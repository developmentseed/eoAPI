from aws_cdk import Stack, aws_ec2
from constructs import Construct

from config import AppConfig


class VpcStack(Stack):
    def __init__(self, scope: Construct, app_config: AppConfig, **kwargs) -> None:
        super().__init__(
            scope,
            id=app_config.build_service_name("pgSTAC-vpc"),
            tags=app_config.tags,
            **kwargs
        )

        self.vpc = aws_ec2.Vpc(
            self,
            "vpc",
            subnet_configuration=[
                aws_ec2.SubnetConfiguration(
                    name="ingress", subnet_type=aws_ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                aws_ec2.SubnetConfiguration(
                    name="application",
                    subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                aws_ec2.SubnetConfiguration(
                    name="rds",
                    subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            nat_gateways=app_config.nat_gateway_count,
        )

        self.vpc.add_gateway_endpoint(
            "DynamoDbEndpoint", service=aws_ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )

        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=aws_ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        )

        self.export_value(
            self.vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC)
            .subnets[0]
            .subnet_id
        )
        self.export_value(
            self.vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC)
            .subnets[1]
            .subnet_id
        )
