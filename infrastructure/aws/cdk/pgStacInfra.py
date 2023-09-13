import boto3
import yaml
from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_certificatemanager,
    aws_ec2,
    aws_iam,
    aws_rds,
    aws_s3,
    aws_lambda
)
from aws_cdk.aws_apigateway import DomainNameOptions
from aws_cdk.aws_apigatewayv2_alpha import DomainName
from constructs import Construct
from eoapi_cdk import (
    BastionHost,
    PgStacApiLambda,
    PgStacDatabase,
    StacBrowser,
    StacIngestor,
    TiPgApiLambda,
    TitilerPgstacApiLambda,
)

from config import AppConfig

APIS_RUNTIME_DIR = 'runtime'

class pgStacInfraStack(Stack):
    def __init__(
        self,
        scope: Construct,
        vpc: aws_ec2.Vpc,
        app_config: AppConfig,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id=app_config.build_service_name("pgSTAC-infra"),
            tags=app_config.tags,
            **kwargs,
        )

        pgstac_db = PgStacDatabase(
            self,
            "pgstac-db",
            vpc=vpc,
            engine=aws_rds.DatabaseInstanceEngine.postgres(
                version=aws_rds.PostgresEngineVersion.VER_14
            ),
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if app_config.public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_ISOLATED
            ),
            allocated_storage=app_config.db_allocated_storage,
            instance_type=aws_ec2.InstanceType(app_config.db_instance_type),
            api_code={'entry': f'{APIS_RUNTIME_DIR}/db', 'index': 'handler.py', 'handler': 'handler'},
        )

        stac_api_lambda = PgStacApiLambda(
            self,
            "pgstac-api",
            api_env={
                "NAME": app_config.build_service_name("STAC API"),
                "description": f"{app_config.stage} STAC API",
            },
            api_code={'entry': f'{APIS_RUNTIME_DIR}/stac', 'index': 'handler.py', 'handler': 'handler'},
            vpc=vpc,
            db=pgstac_db.db,
            db_secret=pgstac_db.pgstac_secret,
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if app_config.public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            stac_api_domain_name=DomainName(
                self,
                "stac-api-domain-name",
                domain_name=app_config.stac_api_custom_domain,
                certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                    self,
                    "stac-api-cdn-certificate",
                    certificate_arn=app_config.acm_certificate_arn,
                ),
            )
            if app_config.stac_api_custom_domain
            else None,
        )

        TitilerPgstacApiLambda(
            self,
            "titiler-pgstac-api",
            api_env={
                "NAME": app_config.build_service_name("titiler pgSTAC API"),
                "description": f"{app_config.stage} titiler pgstac API",
            },
            python_lambda_options={'runtime':f'{APIS_RUNTIME_DIR}/raster','index':'handler.py', 'handler':'handler','memorySize': 3008, 'architecture': aws_lambda.Architecture.X86_64},
            vpc=vpc,
            db=pgstac_db.db,
            db_secret=pgstac_db.pgstac_secret,
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if app_config.public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            buckets=app_config.titiler_buckets,
            titiler_pgstac_api_domain_name=DomainName(
                self,
                "titiler-pgstac-api-domain-name",
                domain_name=app_config.titiler_pgstac_api_custom_domain,
                certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                    self,
                    "titiler-pgstac-api-cdn-certificate",
                    certificate_arn=app_config.acm_certificate_arn,
                ),
            )
            if app_config.titiler_pgstac_api_custom_domain
            else None,
        )

        TiPgApiLambda(
            self,
            "tipg-api",
            api_env={
                "NAME": app_config.build_service_name("tipg API"),
                "description": f"{app_config.stage} tipg API",
            },
            api_code={'entry': f'{APIS_RUNTIME_DIR}/vector', 'index': 'handler.py', 'handler': 'handler'},
            vpc=vpc,
            db=pgstac_db.db,
            db_secret=pgstac_db.pgstac_secret,
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if app_config.public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            tipg_api_domain_name=DomainName(
                self,
                "tipg-api-domain-name",
                domain_name=app_config.tipg_api_custom_domain,
                certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                    self,
                    "tipg-api-cdn-certificate",
                    certificate_arn=app_config.acm_certificate_arn,
                ),
            )
            if app_config.tipg_api_custom_domain
            else None,
        )

        if app_config.bastion_host:
            BastionHost(
                self,
                "bastion-host",
                vpc=vpc,
                db=pgstac_db.db,
                ipv4_allowlist=app_config.bastion_host_allow_ip_list,
                user_data=aws_ec2.UserData.custom(
                    yaml.dump(app_config.bastion_host_user_data)
                )
                if app_config.bastion_host_user_data is not None
                else aws_ec2.UserData.for_linux(),
                create_elastic_ip=app_config.bastion_host_create_elastic_ip,
            )

        if app_config.data_access_role_arn:
            # importing provided role from arn.
            # the stac ingestor will try to assume it when called,
            # so it must be listed in the data access role trust policy.
            data_access_role = aws_iam.Role.from_role_arn(
                self,
                "data-access-role",
                role_arn=app_config.data_access_role_arn,
            )
        else:
            data_access_role = self._create_data_access_role()

        stac_ingestor_env = {"REQUESTER_PAYS": "True"}

        if app_config.auth_provider_jwks_url:
            stac_ingestor_env["JWKS_URL"] = app_config.auth_provider_jwks_url

        stac_ingestor = StacIngestor(
            self,
            "stac-ingestor",
            stac_url=stac_api_lambda.url,
            stage=app_config.stage,
            vpc=vpc,
            data_access_role=data_access_role,
            stac_db_secret=pgstac_db.pgstac_secret,
            stac_db_security_group=pgstac_db.db.connections.security_groups[0],
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            api_env=stac_ingestor_env,
            api_code={'entry': f'{APIS_RUNTIME_DIR}/ingestor', 'index': 'handler.py', 'handler': 'handler'},
            ingestor_domain_name_options=DomainNameOptions(
                domain_name=app_config.stac_ingestor_api_custom_domain,
                certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                    self,
                    "stac-ingestor-api-cdn-certificate",
                    certificate_arn=app_config.acm_certificate_arn,
                ),
            )
            if app_config.stac_ingestor_api_custom_domain
            else None,
        )

        if app_config.stac_browser_version:
            stac_browser_bucket = aws_s3.Bucket(
                self,
                "stac-browser-bucket",
                bucket_name=app_config.build_service_name("stac-browser"),
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True,
                website_index_document="index.html",
                public_read_access=True,
                block_public_access=aws_s3.BlockPublicAccess(
                    block_public_acls=False,
                    block_public_policy=False,
                    ignore_public_acls=False,
                    restrict_public_buckets=False,
                ),
                object_ownership=aws_s3.ObjectOwnership.OBJECT_WRITER,
            )
            StacBrowser(
                self,
                "stac-browser",
                github_repo_tag=app_config.stac_browser_version,
                stac_catalog_url=f"https://{app_config.stac_api_custom_domain}",
                website_index_document="index.html",
                bucket_arn=stac_browser_bucket.bucket_arn,
            )

        # we can only do that if the role is created here.
        # If injecting a role, that role's trust relationship
        # must be already set up, or set up after this deployment.
        if not app_config.data_access_role_arn:
            data_access_role = self._grant_assume_role_with_principal_pattern(
                data_access_role, stac_ingestor.handler_role.role_name
            )

    def _create_data_access_role(self) -> aws_iam.Role:
        """
        Creates an IAM role with full S3 read access.
        """

        data_access_role = aws_iam.Role(
            self,
            "data-access-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        data_access_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "s3:Get*",
                ],
                resources=["*"],
                effect=aws_iam.Effect.ALLOW,
            )
        )
        return data_access_role

    def _grant_assume_role_with_principal_pattern(
        self,
        role_to_assume: aws_iam.Role,
        principal_pattern: str,
        account_id: str = boto3.client("sts").get_caller_identity().get("Account"),
    ) -> aws_iam.Role:
        """
        Grants assume role permissions to the role of the given
        account with the given name pattern. Default account
        is the current account.
        """

        role_to_assume.assume_role_policy.add_statements(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[aws_iam.AnyPrincipal()],
                actions=["sts:AssumeRole"],
                conditions={
                    "StringLike": {
                        "aws:PrincipalArn": [
                            f"arn:aws:iam::{account_id}:role/{principal_pattern}"
                        ]
                    }
                },
            )
        )

        return role_to_assume
