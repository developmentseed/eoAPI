from aws_cdk import App

from config import build_app_config
import pgStacInfra, vpc

app = App()

app_config = build_app_config()

vpc_stack = vpc.VpcStack(scope=app, app_config=app_config)

pgstac_infra_stack = pgStacInfra.pgStacInfraStack(
    scope=app,
    vpc=vpc_stack.vpc,
    app_config=app_config,
)
app.synth()
