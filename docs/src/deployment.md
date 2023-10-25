---
hide:
  - navigation
---


## Via [eoapi-cdk](https://github.com/developmentseed/eoapi-cdk)


[eoapi-cdk](https://github.com/developmentseed/eoapi-cdk) is a set of AWS CDK constructs to deploy eoAPI services.

[eoapi-template](https://github.com/developmentseed/eoapi-template) is an AWS CDK app that shows how to configure the [eoapi-cdk](https://github.com/developmentseed/eoapi-cdk) constructs.

An example of Cloud Stack is available for AWS (RDS for the database and Lambda for the APIs).

The stack is deployed by the [AWS CDK](https://aws.amazon.com/cdk/) utility. Under the hood, CDK will create the deployment packages required for AWS Lambda, upload them to AWS, and handle the creation of the Lambda and API Gateway resources.

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

    Set environment variable or complex code in the `infrastructure/aws/.env` file (e.g., `CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1`).

    To modify the size of the burstable database instance, modify `CDK_EOAPI_DB_INSTANCE_SIZE` to one of the values of [`aws_cdk.aws_ec2.InstanceSize`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceSize.html#instancesize).
    The default size is `SMALL`.

    **Important**:

      - `CDK_EOAPI_DB_PGSTAC_VERSION` is a required env (see https://github.com/stac-utils/pgstac/tags for the latest version)

      - You can choose which functions to deploy by setting `CDK_EOAPI_FUNCTIONS` env (e.g., `CDK_EOAPI_FUNCTIONS='["stac","raster","vector"]'`)


4. Install CDK and connect to your AWS account. This step is only necessary once per AWS account. The environment variable `CDK_EOAPI_STAGE` determines the name of the stack
(e.g., eoAPI-staging or eoAPI-production)
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

    # Deploy in a specific region
    AWS_DEFAULT_REGION=eu-central-1 \
    AWS_REGION=eu-central-1 \
    CDK_EOAPI_STAGE=staging \
    CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 \
    npm --prefix infrastructure/aws run cdk -- deploy eoapi-staging --profile {my-aws-profile}
    ```

If you get an error saying that the max VPCs have been reached, you have hit the limit for the number of VPCs per unique AWS account and region combination. You can change the AWS region to a region with fewer VPCs and deploy again to fix this.

## Via [eoapi-k8s](https://github.com/developmentseed/eoapi-k8s)

[eoapi-k8s](https://github.com/developmentseed/eoapi-k8s) has the IaC and Helm charts for deploying eoAPI services on AWS and GCP.

**Getting started**

If you still need to set up a k8s cluster on AWS or GCP, then follow an IaC guide below that is relevant to you.

> &#9432; The helm chart in this repo assumes your cluster has a few third-party add-ons and controllers installed. So
> It's in your best interest to read through the IaC guides to understand what those defaults are

* :octicons-link-external-16: [AWS EKS Cluster Setup](https://github.com/developmentseed/eoapi-k8s/blob/main/docs/aws-eks.md)

* :octicons-link-external-16: [TBD: GCP GKE Cluster Setup](https://github.com/developmentseed/eoapi-k8s/blob/main/docs/gcp-gke.md)

**Helm Installation**

Once you have a k8s cluster set up, you can `helm install` eoAPI as follows

1. `helm install` from this repo's `helm-chart/` folder:

    ```python
      ######################################################
      # create os environment variables for required secrets
      ######################################################
      $ export GITSHA=$(git rev-parse HEAD | cut -c1-10)
      $ export PGUSER=s00pers3cr3t
      $ export POSTGRES_USER=s00pers3cr3t
      $ export POSTGRES_PASSWORD=superuserfoobar
      $ export PGPASSWORD=foobar

      $ cd ./helm-chart

      $ helm install \
          --namespace eoapi \
          --create-namespace \
          --set gitSha=$GITSHA \
          --set db.settings.secrets.PGUSER=$PGUSER \
          --set db.settings.secrets.POSTGRES_USER=$POSTGRES_USER \
          --set db.settings.secrets.PGPASSWORD=$PGPASSWORD \
          --set db.settings.secrets.POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
          eoapi \
          ./eoapi
    ```

2. or `helm install` from https://devseed.com/eoapi-k8s/:

    ```python
      # add the eoapi helm repo locally
      $ helm repo add eoapi https://devseed.com/eoapi-k8s/

      # List out the eoapi chart versions
      $ helm search repo eoapi
      NAME            CHART VERSION   APP VERSION     DESCRIPTION
      eoapi/eoapi     0.1.1           0.1.0           Create a full Earth Observation API with Metada...
      eoapi/eoapi     0.1.2           0.1.0           Create a full Earth Observation API with Metada...

      # add the required secret overrides to an arbitrarily named `.yaml` file (`config.yaml` below)
      $ cat config.yaml
      db:
        settings:
          secrets:
            PGUSER: "username"
            POSTGRES_USER: "username"
            PGPASSWORD: "password"
            POSTGRES_PASSWORD: "password"

      # then run `helm install` with those overrides
      helm install eoapi eoapi/eoapi --version 0.1.1 -f config.yaml
    ```