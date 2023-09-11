from typing import Any, Dict, List, Optional, Union

import pydantic
from aws_cdk import aws_ec2
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings

DEFAULT_PROJECT_ID = "eoapi"
DEFAULT_STAGE = "staging"
DEFAULT_NAT_GATEWAY_COUNT = 1


class Config(BaseSettings):
    project_id: Optional[str] = pydantic.Field(
        description="Project ID", default=DEFAULT_PROJECT_ID
    )
    stage: Optional[str] = pydantic.Field(
        description="Stage of deployment", default=DEFAULT_STAGE
    )
    tags: Optional[Dict[str, str]] = pydantic.Field(
        description="""Tags to apply to resources. If none provided, 
        will default to the defaults defined in `default_tags`.
        Note that if tags are passed to the CDK CLI via `--tags`, 
        they will override any tags defined here.""",
        default=None,
    )
    auth_provider_jwks_url: Optional[str] = pydantic.Field(
        description="""Auth Provider JSON Web Key Set URL for
        ingestion authentication. If not provided, 
        no authentication will be required.""",
        default=None,
    )
    data_access_role_arn: Optional[str] = pydantic.Field(
        description="""Role ARN for data access, that will be
        used by the STAC ingestor for validation of assets
        located in S3 and for the tiler application to access
        assets located in S3. If none, the role will be
        created at runtime with full S3 read access. If
        provided, the existing role must be configured to
        allow the tiler and STAC ingestor lambda roles to
        assume it. See https://github.com/developmentseed/eoapi-cdk""",
        default=None,
    )
    db_instance_type: Optional[str] = pydantic.Field(
        description="Database instance type", default="t3.micro"
    )
    db_allocated_storage: Optional[int] = pydantic.Field(
        description="Allocated storage for the database", default=5
    )
    public_db_subnet: Optional[bool] = pydantic.Field(
        description="Whether to put the database in a public subnet", default=False
    )
    nat_gateway_count: Optional[int] = pydantic.Field(
        description="Number of NAT gateways to create",
        default=DEFAULT_NAT_GATEWAY_COUNT,
    )
    bastion_host_create_elastic_ip: Optional[bool] = pydantic.Field(
        description="Whether to create an elastic IP for the bastion host",
        default=False,
    )
    bastion_host_allow_ip_list: Optional[List[str]] = pydantic.Field(
        description="""YAML file containing list of IP addresses to 
        allow SSH access to the bastion host""",
        default=[],
    )
    bastion_host_user_data: Optional[
        Union[Dict[str, Any], aws_ec2.UserData]
    ] = pydantic.Field(
        description="Path to file containing user data for the bastion host",
        default=aws_ec2.UserData.for_linux(),
    )
    titiler_buckets: Optional[List[str]] = pydantic.Field(
        description="""Path to YAML file containing list of
        buckets to grant access to the titiler API""",
        default=[],
    )

    @pydantic.field_validator("tags")
    def default_tags(cls, v, info: FieldValidationInfo):
        return v or {"project_id": info.data["project_id"], "stage": info.data["stage"]}

    @pydantic.field_validator("nat_gateway_count")
    def validate_nat_gateway_count(cls, v, info: FieldValidationInfo):
        if not info.data["public_db_subnet"] and v <= 0:
            raise ValueError(
                """if the database and its associated services instances
                             are to be located in the private subnet of the VPC, NAT
                             gateways are needed to allow egress from the services
                             and therefore `nat_gateway_count` has to be > 0."""
            )
        else:
            return v

    def build_service_name(self, service_id: str) -> str:
        return f"{self.project_id}-{self.stage}-{service_id}"