## eoAPI

STAC and Tiler API


### Deployment

The stack is deployed by the [AWS CDK](https://aws.amazon.com/cdk/) utility. Under the hood, CDK will create the deployment packages required for AWS Lambda, upload it to AWS, and handle the creation of the Lambda and API Gateway resources.

1. Install CDK and connect to your AWS account. This step is only necessary once per AWS account.

    ```bash
    # Download titiler repo
    $ git clone https://github.com/developmentseed/eoapi.git

    # install cdk dependencies
    $ pip install -r deployment/requirements.txt
    $ npm install

    $ npm run cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment

    # in specific region
    $ npm run cdk bootstrap aws://${AWS_ACCOUNT_ID}/eu-central-1
    ```

2. Pre-Generate CFN template

    ```bash
    $ npm run cdk synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

3. Update settings

    Using environment variable or editing `deployment/cdk/config.py`

4. Deploy

    ```bash
    $ EOAPI_STAGE=staging npm run cdk deploy eoapi-staging --profile {my-aws-profile}

    # Deploy in specific region
    $ AWS_DEFAULT_REGION=eu-central-1 AWS_REGION=eu-central-1 npm run cdk deploy eoapi-production --profile {my-aws-profile}
    ```
