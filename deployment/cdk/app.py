"""
CDK Stack definition code for EOAPI
"""
import json
import os
from typing import Any

import aws_cdk.aws_logs as logs
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_integrations as apigw_integrations
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import core
from config import (
    eoAPISettings,
    eoDBSettings,
    eoFeaturesSettings,
    eoRasterSettings,
    eoSTACSettings,
    eoVectorSettings,
)

eoapi_settings = eoAPISettings()


class BootstrappedDb(core.Construct):
    """
    Given an RDS database, connect to DB and create a database, user, and
    password
    """

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        db: rds.DatabaseInstance,
        new_dbname: str,
        new_username: str,
        pgstac_version: str,
        secrets_prefix: str,
    ) -> None:
        """Update RDS database."""
        super().__init__(scope, id)

        # TODO: Utilize a singleton function.
        handler = aws_lambda.Function(
            self,
            "DatabaseBootstrapper",
            handler="handler.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_docker_build(
                path=os.path.abspath("./"),
                file="deployment/dockerfiles/Dockerfile.db",
                build_args={"PGSTAC_VERSION": pgstac_version},
                platform="linux/amd64",
            ),
            timeout=core.Duration.minutes(5),
            vpc=db.vpc,
            allow_public_subnet=True,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        self.secret = secretsmanager.Secret(
            self,
            id,
            secret_name=os.path.join(
                secrets_prefix, id.replace(" ", "_"), self.node.unique_id[-8:]
            ),
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {
                        "dbname": new_dbname,
                        "engine": "postgres",
                        "port": 5432,
                        "host": db.instance_endpoint.hostname,
                        "username": new_username,
                    },
                ),
                generate_string_key="password",
                exclude_punctuation=True,
            ),
            description=f"Deployed by {core.Stack.of(self).stack_name}",
        )

        self.resource = core.CustomResource(
            scope=scope,
            id="BootstrappedDbResource",
            service_token=handler.function_arn,
            properties={
                # By setting pgstac_version in the properties assures
                # that Create/Update events will be passed to the service token
                "pgstac_version": pgstac_version,
                "conn_secret_arn": db.secret.secret_arn,
                "new_user_secret_arn": self.secret.secret_arn,
            },
            # We do not need to run the custom resource on STAC Delete
            # Custom Resource are not physical resources so it's OK to `Retain` it
            removal_policy=core.RemovalPolicy.RETAIN,
        )

        # Allow lambda to...
        # read new user secret
        self.secret.grant_read(handler)
        # read database secret
        db.secret.grant_read(handler)
        # connect to database
        db.connections.allow_from(handler, port_range=ec2.Port.tcp(5432))

    def is_required_by(self, construct: core.Construct):
        """Register required services."""
        return construct.node.add_dependency(self.resource)


class eoAPIconstruct(core.Stack):
    """Earth Observation API CDK application"""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        stage: str,
        name: str,
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, f"{id}-vpc", nat_gateways=0)

        interface_endpoints = [
            (
                "SecretsManager Endpoint",
                ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            ),
            (
                "CloudWatch Logs Endpoint",
                ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            ),
        ]
        for (id, service) in interface_endpoints:
            vpc.add_interface_endpoint(id, service=service)

        gateway_endpoints = [("S3", ec2.GatewayVpcEndpointAwsService.S3)]
        for (id, service) in gateway_endpoints:
            vpc.add_gateway_endpoint(id, service=service)

        eodb_settings = eoDBSettings()
        db = rds.DatabaseInstance(
            self,
            f"{id}-postgres-db",
            vpc=vpc,
            engine=rds.DatabaseInstanceEngine.POSTGRES,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL
            ),
            database_name=eodb_settings.dbname,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            backup_retention=core.Duration.days(7),
            deletion_protection=eoapi_settings.stage.lower() == "production",
            removal_policy=core.RemovalPolicy.SNAPSHOT
            if eoapi_settings.stage.lower() == "production"
            else core.RemovalPolicy.DESTROY,
        )

        setup_db = BootstrappedDb(
            self,
            "STAC DB for eoapi",
            db=db,
            new_dbname=eodb_settings.dbname,
            new_username=eodb_settings.user,
            pgstac_version=eodb_settings.pgstac_version,
            secrets_prefix=os.path.join(stage, name),
        )

        core.CfnOutput(
            self,
            f"{id}-database-secret-arn",
            value=db.secret.secret_arn,
            description="Arn of the SecretsManager instance holding the connection info for Postgres DB",
        )

        # eoapi.raster
        if "raster" in eoapi_settings.functions:
            db_secrets = {
                "POSTGRES_HOST": setup_db.secret.secret_value_from_json(
                    "host"
                ).to_string(),
                "POSTGRES_DBNAME": setup_db.secret.secret_value_from_json(
                    "dbname"
                ).to_string(),
                "POSTGRES_USER": setup_db.secret.secret_value_from_json(
                    "username"
                ).to_string(),
                "POSTGRES_PASS": setup_db.secret.secret_value_from_json(
                    "password"
                ).to_string(),
                "POSTGRES_PORT": setup_db.secret.secret_value_from_json(
                    "port"
                ).to_string(),
            }
            eoraster_settings = eoRasterSettings()
            eoraster_function = aws_lambda.Function(
                self,
                f"{id}-raster-lambda",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                code=aws_lambda.Code.from_docker_build(
                    path=os.path.abspath(code_dir),
                    file="deployment/dockerfiles/Dockerfile.raster",
                    platform="linux/amd64",
                ),
                vpc=vpc,
                allow_public_subnet=True,
                handler="handler.handler",
                memory_size=eoraster_settings.memory,
                timeout=core.Duration.seconds(eoraster_settings.timeout),
                environment=eoraster_settings.env or {},
                log_retention=logs.RetentionDays.ONE_WEEK,
            )
            for k, v in db_secrets.items():
                eoraster_function.add_environment(key=k, value=str(v))

            eoraster_function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[
                        f"arn:aws:s3:::{bucket}/{eoraster_settings.key}"
                        for bucket in eoraster_settings.buckets
                    ],
                )
            )

            db.connections.allow_from(eoraster_function, port_range=ec2.Port.tcp(5432))
            raster_api = apigw.HttpApi(
                self,
                f"{id}-raster-endpoint",
                default_integration=apigw_integrations.HttpLambdaIntegration(
                    f"{id}-raster-integration",
                    handler=eoraster_function,
                ),
            )
            core.CfnOutput(self, "eoAPI-raster", value=raster_api.url)

            setup_db.is_required_by(eoraster_function)

        # eoapi.stac
        if "stac" in eoapi_settings.functions:
            db_secrets = {
                "POSTGRES_HOST_READER": setup_db.secret.secret_value_from_json(
                    "host"
                ).to_string(),
                "POSTGRES_HOST_WRITER": setup_db.secret.secret_value_from_json(
                    "host"
                ).to_string(),
                "POSTGRES_DBNAME": setup_db.secret.secret_value_from_json(
                    "dbname"
                ).to_string(),
                "POSTGRES_USER": setup_db.secret.secret_value_from_json(
                    "username"
                ).to_string(),
                "POSTGRES_PASS": setup_db.secret.secret_value_from_json(
                    "password"
                ).to_string(),
                "POSTGRES_PORT": setup_db.secret.secret_value_from_json(
                    "port"
                ).to_string(),
            }

            eostac_settings = eoSTACSettings()
            eostac_function = aws_lambda.Function(
                self,
                f"{id}-stac-lambda",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                code=aws_lambda.Code.from_docker_build(
                    path=os.path.abspath(code_dir),
                    file="deployment/dockerfiles/Dockerfile.stac",
                    platform="linux/amd64",
                ),
                vpc=vpc,
                allow_public_subnet=True,
                handler="handler.handler",
                memory_size=eostac_settings.memory,
                timeout=core.Duration.seconds(eostac_settings.timeout),
                environment=eostac_settings.env or {},
                log_retention=logs.RetentionDays.ONE_WEEK,
            )
            for k, v in db_secrets.items():
                eostac_function.add_environment(key=k, value=str(v))

            # If raster is deployed we had the TITILER_ENDPOINT env to add the Proxy extension
            if "raster" in eoapi_settings.functions:
                eostac_function.add_environment(
                    key="TITILER_ENDPOINT", value=raster_api.url
                )

            db.connections.allow_from(eostac_function, port_range=ec2.Port.tcp(5432))

            stac_api = apigw.HttpApi(
                self,
                f"{id}-stac-endpoint",
                default_integration=apigw_integrations.HttpLambdaIntegration(
                    f"{id}-stac-integration",
                    handler=eostac_function,
                ),
            )
            core.CfnOutput(self, "eoAPI-stac", value=stac_api.url)

            setup_db.is_required_by(eostac_function)

        # eoapi.vector
        if "vector" in eoapi_settings.functions:
            db_secrets = {
                "POSTGRES_HOST": setup_db.secret.secret_value_from_json(
                    "host"
                ).to_string(),
                "POSTGRES_DBNAME": setup_db.secret.secret_value_from_json(
                    "dbname"
                ).to_string(),
                "POSTGRES_USER": setup_db.secret.secret_value_from_json(
                    "username"
                ).to_string(),
                "POSTGRES_PASS": setup_db.secret.secret_value_from_json(
                    "password"
                ).to_string(),
                "POSTGRES_PORT": setup_db.secret.secret_value_from_json(
                    "port"
                ).to_string(),
            }

            eovector_settings = eoVectorSettings()
            eovector_function = aws_lambda.Function(
                self,
                f"{id}-vector-lambda",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                code=aws_lambda.Code.from_docker_build(
                    path=os.path.abspath(code_dir),
                    file="deployment/dockerfiles/Dockerfile.vector",
                    platform="linux/amd64",
                ),
                vpc=vpc,
                allow_public_subnet=True,
                handler="handler.handler",
                memory_size=eovector_settings.memory,
                timeout=core.Duration.seconds(eovector_settings.timeout),
                environment=eovector_settings.env or {},
                log_retention=logs.RetentionDays.ONE_WEEK,
            )
            for k, v in db_secrets.items():
                eovector_function.add_environment(key=k, value=str(v))

            db.connections.allow_from(eovector_function, port_range=ec2.Port.tcp(5432))

            vector_api = apigw.HttpApi(
                self,
                f"{id}-vector-endpoint",
                default_integration=apigw_integrations.HttpLambdaIntegration(
                    f"{id}-vector-integration",
                    handler=eovector_function,
                ),
            )
            core.CfnOutput(self, "eoAPI-vector", value=vector_api.url)

            setup_db.is_required_by(eovector_function)

        # eoapi.feature
        if "features" in eoapi_settings.functions:
            db_secrets = {
                "POSTGRES_HOST": setup_db.secret.secret_value_from_json(
                    "host"
                ).to_string(),
                "POSTGRES_DBNAME": setup_db.secret.secret_value_from_json(
                    "dbname"
                ).to_string(),
                "POSTGRES_USER": setup_db.secret.secret_value_from_json(
                    "username"
                ).to_string(),
                "POSTGRES_PASS": setup_db.secret.secret_value_from_json(
                    "password"
                ).to_string(),
                "POSTGRES_PORT": setup_db.secret.secret_value_from_json(
                    "port"
                ).to_string(),
            }
            eofeatures_settings = eoFeaturesSettings()
            eofeatures_function = aws_lambda.Function(
                self,
                f"{id}-features-lambda",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                code=aws_lambda.Code.from_docker_build(
                    path=os.path.abspath(code_dir),
                    file="deployment/dockerfiles/Dockerfile.features",
                    platform="linux/amd64",
                ),
                vpc=vpc,
                allow_public_subnet=True,
                handler="handler.handler",
                memory_size=eofeatures_settings.memory,
                timeout=core.Duration.seconds(eofeatures_settings.timeout),
                environment=eofeatures_settings.env or {},
                log_retention=logs.RetentionDays.ONE_WEEK,
            )
            for k, v in db_secrets.items():
                eofeatures_function.add_environment(key=k, value=str(v))

            db.connections.allow_from(
                eofeatures_function, port_range=ec2.Port.tcp(5432)
            )

            features_api = apigw.HttpApi(
                self,
                f"{id}-features-endpoint",
                default_integration=apigw_integrations.HttpLambdaIntegration(
                    f"{id}-features-integration",
                    handler=eofeatures_function,
                ),
            )
            core.CfnOutput(self, "eoAPI-features", value=features_api.url)

            setup_db.is_required_by(eofeatures_function)


app = core.App()

# Tag infrastructure
for key, value in {
    "Project": eoapi_settings.name,
    "Stack": eoapi_settings.stage,
    "Owner": eoapi_settings.owner,
    "Client": eoapi_settings.client,
}.items():
    if value:
        core.Tag.add(app, key, value)


stackname = f"{eoapi_settings.name}-{eoapi_settings.stage}"
eoAPIconstruct(
    app,
    stackname,
    eoapi_settings.name,
    eoapi_settings.stage,
    env={
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
        "region": os.environ["CDK_DEFAULT_REGION"],
    },
)
app.synth()
