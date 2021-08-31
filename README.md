## Earth Observation API

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/129632832-fe6f7d80-4d87-463a-b0cc-305423a8489e.png"/>
  <p align="center">Deploy a STAC API and a dynamic mosaic tiler API using AWS CDK.</p>
</p>

<p align="center">
  <!-- <a href="https://github.com/developmentseed/eoAPI/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/eoAPI/workflows/CI/badge.svg" alt="Test">
  </a> -->
  <a href="https://github.com/developmentseed/eoAPI/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler.svg" alt="Downloads">
  </a>
</p>

---

**Source Code**: <a href="https://github.com/developmentseed/eoAPI" target="_blank">https://github.com/developmentseed/eoAPI</a>

---


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


## STAC + PgSTAC + TiTiler

The dyanic tiler deployed within eoAPI is built on top of [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) and [pgstac](https://github.com/stac-utils/pgstac). It enables large scale mosaic based on results of STAC searches queries:

![](https://user-images.githubusercontent.com/10407788/129632282-f71e9f45-264c-4882-af28-7062c4e56f25.png)

## Local

You can launch the APIs locally using docker. This will start 3 services: database, eoapi.stac, eoapi.raster
```
$ git clone https://github.com/developmentseed/eoAPI.git
$ cd eoAPI
$ docker-compose build
$ docker-compose up
```

## Project structure

```
 ├──demo/                  - items/collections and notebook
 ├──deployment/            - AWS CDK code
 └──src/eoapi/
    ├── raster/            - eoAPI raster Application package
    ├── stac/              - eoAPI stac Application package
    └── vector/            - eoAPI vector Application package [EXPERIMENTAL]
```

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/eoAPI/blob/master/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/eoAPI/blob/master/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

See [contributors](https://github.com/developmentseed/eoAPI/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/eoAPI/blob/master/CHANGES.md).
