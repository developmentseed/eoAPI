## Earth Observation API

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/129632832-fe6f7d80-4d87-463a-b0cc-305423a8489e.png"/>
  <p align="center">Deploy a STAC API and a dynamic mosaic tiler API using AWS CDK.</p>
</p>

<p align="center">
  <a href="https://github.com/developmentseed/eoAPI/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/eoAPI/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://github.com/developmentseed/eoAPI/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler.svg" alt="Downloads">
  </a>
</p>

---

**Source Code**: <a href="https://github.com/developmentseed/eoAPI" target="_blank">https://github.com/developmentseed/eoAPI</a>

---

# The Earth Observation API

`EOapi` is a combination of multiple elements:
- [PgSTAC](https://github.com/stac-utils/pgstac) database
- **STAC** API built on top of [stac-fastapi](https://github.com/stac-utils/stac-fastapi)
- **STAC And Mosaic Raster Tiles** API built on top of [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac)
- **OGC Features and Vector Tiles** API built on top of [tipg](https://github.com/developmentseed/tipg)

The project's goal is to enable a full, but easy to deploy, Earth Observation API for Metadata search (STAC), Raster and Vector services.

## STAC -> [/src/eoapi/stac](/src/eoapi/stac)

A custom version of [stac-fastapi](https://github.com/stac-utils/stac-fastapi), adding a `TiTilerExtension` and a simple `Search Viewer`.

#### Features

- Full **stac-fastapi** implementation
- Simple STAC Search **viewer**
- **Proxy** to the Tiler endpoint for STAC Items

  When `TITILER_ENDPOINT` environement is set (pointing the `raster` application), additional endpoints will be added to the stac-fastapi application (see: [stac/extension.py](https://github.com/developmentseed/eoAPI/blob/master/src/eoapi/stac/eoapi/stac/extension.py)):

  - `/collections/{collectionId}/items/{itemId}/tilejson.json`: Return the `raster` tilejson for an item
  - `/collections/{collectionId}/items/{itemId}/viewer`: Redirect to the `raster` viewer

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/146790933-e439893c-ef2e-4d78-a372-f2f18694836c.png"/>
  <p align="center">STAC Search viewer</p>
</p>


## Raster -> [/src/eoapi/raster](/src/eoapi/raster)

The dynamic tiler deployed within eoAPI is built on top of [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) and [pgstac](https://github.com/stac-utils/pgstac). It enables large scale mosaic based on results of STAC searches queries:

- Full **titiler-pgstac** implementation

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/129632282-f71e9f45-264c-4882-af28-7062c4e56f25.png"/>
  <p align="center">TiTiler-PgSTAC workflow</p>
</p>

## Features/Vector Tiles (Optional) [-> /src/eoapi/features](/src/eoapi/features)

OGC Features + Tiles API (https://github.com/developmentseed/tipg)

By default, the API will look for tables in the `public` schema of the database. We've also added three custom functions which connect to the PgSTAC schema:

- **pg_temp.pgstac_collections_view**: Simple function which return PgSTAC Collections
- **pg_temp.pgstac_hash**: Return features for a specific searchId (hash)
- **pg_temp.pgstac_hash_count**: Return the number of items per geometry for a specific searchId (hash)

## Local

You can launch the APIs locally using docker. This will start 3 services: database, eoapi.stac, eoapi.raster
```
git clone https://github.com/developmentseed/eoAPI.git
cd eoAPI
docker-compose build
docker-compose up stac raster
```

## Project structure

```
 ├──demo/                  - items/collections and notebook
 ├──stack/                 - AWS CDK code
 └──src/eoapi/
    ├── raster/            - eoAPI raster Application package
    ├── stac/              - eoAPI stac Application package
    └── vector/            - eoAPI features+tiles Application package
```

## Deployment

An example of Cloud Stack is available for AWS (RDS for the database and Lambda for the APIs)

The stack is deployed by the [AWS CDK](https://aws.amazon.com/cdk/) utility. Under the hood, CDK will create the deployment packages required for AWS Lambda, upload it to AWS, and handle the creation of the Lambda and API Gateway resources.

1. Install CDK and connect to your AWS account. This step is only necessary once per AWS account.

    ```bash
    # Download titiler repo
    git clone https://github.com/developmentseed/eoapi.git

    # Create a virtual environment
    python -m pip install --upgrade virtualenv
    virtualenv .venv
    source .venv/bin/activate

    # install cdk dependencies
    python -m pip install -r requirements-cdk.txt

    # Install node dependency
    npm install

    # Deploys the CDK toolkit stack into an AWS environment
    npm run cdk -- bootstrap
    # or to a specific region
    AWS_DEFAULT_REGION=us-west-2 AWS_REGION=us-west-2 npm run cdk -- bootstrap
    ```

2. Pre-Generate CFN template

    ```bash
    npm run cdk -- synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

3. Update settings

    Set environment variable or hard code in `stack/.env` file (e.g `CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1`).

    **Important**:
      - `CDK_EOAPI_DB_PGSTAC_VERSION` is a required env
      - You can choose which functions to deploy by setting `CDK_EOAPI_FUNCTIONS` env (e.g `CDK_EOAPI_FUNCTIONS='["stac","raster","vector"]'`)

4. Deploy

    ```bash
    CDK_EOAPI_STAGE=staging CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 npm run cdk -- deploy eoapi-staging

    # Deploy in specific region
    AWS_DEFAULT_REGION=eu-central-1 AWS_REGION=eu-central-1 CDK_EOAPI_DB_PGSTAC_VERSION=0.7.1 npm run cdk -- deploy eoapi-production --profile {my-aws-profile}
    ```

If you get an error saying that the max VPC's has been reached, this means that you have hit the limit for the amount of VPCs per unique AWS account and region combination. You can change the AWS region to a region that has less VPCs and deploy again to fix this.

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/eoAPI/blob/master/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/eoAPI/blob/master/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

See [contributors](https://github.com/developmentseed/eoAPI/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/eoAPI/blob/master/CHANGES.md).
