import yaml
from aws_cdk import App

from config import Config
from eoapi_template import pgStacInfra, vpc

app = App()

try:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
        config = (
            {} if config is None else config
        )  # if config is empty, set it to an empty dict
        config = Config(**config)
except FileNotFoundError:
    # if no config at the expected path, using defaults
    config = Config()

vpc_stack = vpc.VpcStack(
    tags=config.tags,
    scope=app,
    id=config.build_service_name("pgSTAC-vpc"),
    nat_gateway_count=config.nat_gateway_count,
)


pgstac_infra_stack = pgStacInfra.pgStacInfraStack(
    scope=app,
    tags=config.tags,
    id=config.build_service_name("pgSTAC-infra"),
    vpc=vpc_stack.vpc,
    stac_api_lambda_name=config.build_service_name("STAC API"),
    titiler_pgstac_api_lambda_name=config.build_service_name("titiler pgSTAC API"),
    stage=config.stage,
    db_allocated_storage=config.db_allocated_storage,
    public_db_subnet=config.public_db_subnet,
    db_instance_type=config.db_instance_type,
    bastion_host_allow_ip_list=config.bastion_host_allow_ip_list,
    bastion_host_create_elastic_ip=config.bastion_host_create_elastic_ip,
    bastion_host_user_data=yaml.dump(config.bastion_host_user_data),
    titiler_buckets=config.titiler_buckets,
    data_access_role_arn=config.data_access_role_arn,
    auth_provider_jwks_url=config.auth_provider_jwks_url,
)
app.synth()