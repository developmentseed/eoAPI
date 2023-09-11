from typing import Optional, Union

import boto3
from aws_cdk import Stack, aws_ec2, aws_iam, aws_rds
from constructs import Construct
from eoapi_cdk import (
    BastionHost,
    PgStacApiLambda,
    PgStacDatabase,
    StacIngestor,
    TitilerPgstacApiLambda,
)


class pgStacInfraStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        stage: str,
        db_allocated_storage: int,
        public_db_subnet: bool,
        db_instance_type: str,
        stac_api_lambda_name: str,
        titiler_pgstac_api_lambda_name: str,
        bastion_host_allow_ip_list: list,
        bastion_host_create_elastic_ip: bool,
        titiler_buckets: list,
        data_access_role_arn: Optional[str],
        auth_provider_jwks_url: Optional[str],
        bastion_host_user_data: Union[str, aws_ec2.UserData],
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        pgstac_db = PgStacDatabase(
            self,
            "pgstac-db",
            vpc=vpc,
            engine=aws_rds.DatabaseInstanceEngine.postgres(
                version=aws_rds.PostgresEngineVersion.VER_14
            ),
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_ISOLATED
            ),
            allocated_storage=db_allocated_storage,
            instance_type=aws_ec2.InstanceType(db_instance_type),
        )

        stac_api_lambda = PgStacApiLambda(
            self,
            "pgstac-api",
            api_env={"NAME": stac_api_lambda_name, "description": f"{stage} STAC API"},
            vpc=vpc,
            db=pgstac_db.db,
            db_secret=pgstac_db.pgstac_secret,
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        TitilerPgstacApiLambda(
            self,
            "titiler-pgstac-api",
            api_env={
                "NAME": titiler_pgstac_api_lambda_name,
                "description": f"{stage} titiler pgstac API",
            },
            vpc=vpc,
            db=pgstac_db.db,
            db_secret=pgstac_db.pgstac_secret,
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PUBLIC
                if public_db_subnet
                else aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            buckets=titiler_buckets,
        )

        BastionHost(
            self,
            "bastion-host",
            vpc=vpc,
            db=pgstac_db.db,
            ipv4_allowlist=bastion_host_allow_ip_list,
            user_data=aws_ec2.UserData.custom(bastion_host_user_data)
            if bastion_host_user_data
            else aws_ec2.UserData.for_linux(),
            create_elastic_ip=bastion_host_create_elastic_ip,
        )

        if data_access_role_arn:
            # importing provided role from arn.
            # the stac ingestor will try to assume it when called,
            # so it must be listed in the data access role trust policy.
            data_access_role = aws_iam.Role.from_role_arn(
                self,
                "data-access-role",
                role_arn=data_access_role_arn,
            )
        else:
            data_access_role = self._create_data_access_role()

        stac_ingestor_env = {"REQUESTER_PAYS": "True"}

        if auth_provider_jwks_url:
            stac_ingestor_env["JWKS_URL"] = auth_provider_jwks_url

        stac_ingestor = StacIngestor(
            self,
            "stac-ingestor",
            stac_url=stac_api_lambda.url,
            stage=stage,
            vpc=vpc,
            data_access_role=data_access_role,
            stac_db_secret=pgstac_db.pgstac_secret,
            stac_db_security_group=pgstac_db.db.connections.security_groups[0],
            subnet_selection=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            api_env=stac_ingestor_env,
        )

        # we can only do that if the role is created here.
        # If injecting a role, that role's trust relationship
        # must be already set up, or set up after this deployment.
        if not data_access_role_arn:
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