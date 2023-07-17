---
hide:
  - navigation
---

The default runtimes are available through separate repositories ([eoapi-cdk](https://github.com/developmentseed/eoapi-cdk) and [eoapi-k8s](https://github.com/developmentseed/eoapi-k8s)). 

A demonstration application is accessible with the repository [eoapi-template](https://github.com/developmentseed/eoapi-template).

## AWS (Lambda)

An example of Cloud Stack is available for AWS (RDS for the database and Lambda for the APIs)

The stack is deployed by the [AWS CDK](https://aws.amazon.com/cdk/) utility. Under the hood, CDK will create the deployment packages required for AWS Lambda, upload it to AWS, and handle the creation of the Lambda and API Gateway resources.

The example commands here will deploy a CloudFormation stack called `eoAPI-staging`.

1. Clone the `eoapi` repo and install dependencies
    ```bash
    # Download eoapi repo
    git clone https://github.com/developmentseed/eoapi.git

    # Create a virtual environment
    python -m pip install --upgrade virtualenv
    virtualenv infrastructure/aws/.venv
    source infrastructure/aws/.venv/bin/activate

    # install cdk dependencies
    python -m pip install -r infrastructure/aws/requirements-cdk.txt
    ```

2. Install node dependency - requires node version 14+
    ```bash
    npm --prefix infrastructure/aws install
    ```

3. Update settings

    Set environment variable or hard code in `infrastructure/aws/.env` file (e.g `CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1`).

    **Important**:

      - `CDK_EOAPI_DB_PGSTAC_VERSION` is a required env (see https://github.com/stac-utils/pgstac/tags for the latest version)

      - You can choose which functions to deploy by setting `CDK_EOAPI_FUNCTIONS` env (e.g `CDK_EOAPI_FUNCTIONS='["stac","raster","vector"]'`)


4. Install CDK and connect to your AWS account. This step is only necessary once per AWS account. The environment variable `CDK_EOAPI_STAGE` determines the name of the stack
(e.g. eoAPI-staging or eoAPI-production)
    ```bash
    # Deploy the CDK toolkit stack into an AWS environment.
    CDK_EOAPI_STAGE=staging \
    CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 \
    npm --prefix infrastructure/aws run cdk -- bootstrap

    # or to a specific region
    AWS_DEFAULT_REGION=us-west-2 \
    AWS_REGION=us-west-2 \
    CDK_EOAPI_STAGE=staging \
    CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 \
    npm --prefix infrastructure/aws run cdk -- bootstrap
    ```

5. Pre-Generate CFN template

    ```bash
    CDK_EOAPI_STAGE=staging \
    CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 \
    npm --prefix infrastructure/aws run cdk -- synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

6. Deploy

    ```bash
    CDK_EOAPI_STAGE=staging \
    CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 \
    npm --prefix infrastructure/aws run cdk -- deploy eoAPI-staging

    # Deploy in specific region
    AWS_DEFAULT_REGION=eu-central-1 \
    AWS_REGION=eu-central-1 \
    CDK_EOAPI_STAGE=staging \
    CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 \
    npm --prefix infrastructure/aws run cdk -- deploy eoapi-staging --profile {my-aws-profile}
    ```

If you get an error saying that the max VPC's has been reached, this means that you have hit the limit for the amount of VPCs per unique AWS account and region combination. You can change the AWS region to a region that has less VPCs and deploy again to fix this.

## K8S

A Kubernetes chart is currently being developed at https://github.com/developmentseed/eoapi-k8s
