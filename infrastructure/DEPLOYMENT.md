
## AWS

An example of Cloud Stack is available for AWS (RDS for the database and Lambda for the APIs)

The stack is deployed by the [AWS CDK](https://aws.amazon.com/cdk/) utility. Under the hood, CDK will create the deployment packages required for AWS Lambda, upload it to AWS, and handle the creation of the Lambda and API Gateway resources.

1. Install CDK and connect to your AWS account. This step is only necessary once per AWS account.

    ```bash
    # Download titiler repo
    git clone https://github.com/developmentseed/eoapi.git

    # Create a virtual environment
    python -m pip install --upgrade virtualenv
    virtualenv infrastructure/aws/.venv
    source infrastructure/aws/.venv/bin/activate

    # install cdk dependencies
    python -m pip install -r infrastructure/aws/requirements-cdk.txt

    # Install node dependency
    npm --prefix infrastructure/aws install

    # Deploys the CDK toolkit stack into an AWS environment
    npm --prefix infrastructure/aws run cdk -- bootstrap
    # or to a specific region
    AWS_DEFAULT_REGION=us-west-2 AWS_REGION=us-west-2 npm --prefix infrastructure/aws run cdk -- bootstrap
    ```

2. Update settings

    Set environment variable or hard code in `infrastructure/aws/.env` file (e.g `CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1`).

    **Important**:
      - `CDK_EOAPI_DB_PGSTAC_VERSION` is a required env
      - You can choose which functions to deploy by setting `CDK_EOAPI_FUNCTIONS` env (e.g `CDK_EOAPI_FUNCTIONS='["stac","raster","vector"]'`)

3. Pre-Generate CFN template

    ```bash
    npm --prefix infrastructure/aws run cdk -- synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

4. Deploy

    ```bash
    CDK_EOAPI_STAGE=staging CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 npm --prefix infrastructure/aws run cdk -- deploy eoapi-staging

    # Deploy in specific region
    AWS_DEFAULT_REGION=eu-central-1 AWS_REGION=eu-central-1 CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 npm --prefix infrastructure/aws run cdk -- deploy eoapi-production --profile {my-aws-profile}
    ```

If you get an error saying that the max VPC's has been reached, this means that you have hit the limit for the amount of VPCs per unique AWS account and region combination. You can change the AWS region to a region that has less VPCs and deploy again to fix this.
