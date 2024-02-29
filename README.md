<p align="center">
  <img width="700" src="docs/logos/eoAPI.png"/>
  <p align="center">Create a full Earth Observation API with Metadata, Raster, and Vector services.</p>
</p>

<p align="center">
  <a href="https://github.com/developmentseed/eoAPI/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/eoAPI/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://github.com/developmentseed/eoAPI/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/titiler.svg" alt="Downloads">
  </a>
</p>

---

**Documentation**: <a href="https://eoapi.dev" target="_blank">https://eoapi.dev</a>

**Source Code**: <a href="https://github.com/developmentseed/eoAPI" target="_blank">https://github.com/developmentseed/eoAPI</a>

---

## **E**arth **O**bservation **API**

`eoAPI` combines several *state-of-the-art* projects to create a full Earth Observation API. Each service can be used and deployed independently, but `eoAPI` creates the interconnections between each service:

- **pgSTAC** database [https://github.com/stac-utils/pgstac](https://github.com/stac-utils/pgstac)

- **STAC API** built on top of [https://github.com/stac-utils/stac-fastapi](https://github.com/stac-utils/stac-fastapi)

- **STAC Items And Mosaic Raster Tiles** API built on top of [https://github.com/stac-utils/titiler-pgstac](https://github.com/stac-utils/titiler-pgstac)

- **OGC Features and Vector Tiles** API built on top of [https://github.com/developmentseed/tipg](https://github.com/developmentseed/tipg)

- **A STAC Catalog browsing UI** based on the radiant earth browser : [https://github.com/radiantearth/stac-browser](https://github.com/radiantearth/stac-browser)

---

## 🌍 eoAPI: An Open-Source Community Project

`eoAPI` is proudly open-source and driven by a dedicated community of contributors. We believe in the power of open collaboration and welcome anyone to contribute, discuss, and grow this tool. Join the conversations on [GitHub Discussions](https://github.com/developmentseed/eoAPI/discussions) and make a difference in the Earth Observation realm.


---

## Getting started

The easiest way to start exploring the different eoAPI services is with *Docker*. Clone this repository and start the multi-container *Docker* applications using `Compose`:

```
git clone https://github.com/developmentseed/eoAPI.git
cd eoAPI
docker compose up
```

Once the applications are *up*, you'll need to add STAC **Collections** and **Items** to the PgSTAC database. If you don't have these available, you can follow the [MAXAR open data demo](https://github.com/vincentsarago/MAXAR_opendata_to_pgstac) (or get inspired by the other [demos](https://github.com/developmentseed/eoAPI/tree/main/demo)).

Then you can start exploring your dataset with:

  - the STAC Metadata service [http://localhost:8081](http://localhost:8081)
  - the Raster service [http://localhost:8082](http://localhost:8082)
  - the browser UI [http://localhost:8085](http://localhost:8085)

If you've added a vector dataset to the `public` schema in the Postgres database, they will be available through the **Vector** service at [http://localhost:8083](http://localhost:8083).

## Deployment with standard runtimes

This repository has current runtimes that are consistently updated with new functionality.

### Local deployment

The services can be deployed altogether locally with `docker compose up`.

Alternatively, you may install the libraries and launch the applications manually: 

<details>

```bash
python -m pip install --upgrade virtualenv
virtualenv .venv
source .venv/bin/activate

export DATABASE_URL=postgresql://username:password@0.0.0.0:5439/postgis  # Connect to the database of your choice

python -m pip install uvicorn

###############################################################################
# Install and launch the application
# Select one of the following

###############################################################################
# STAC
python -m pip install "psycopg[binary,pool]" stac-fastapi-pgstac
.venv/bin/uvicorn stac_fastapi.pgstac.app:app --port 8081 --reload

###############################################################################
# RASTER
python -m pip install "psycopg[binary,pool]" titiler-pgstac
.venv/bin/uvicorn titiler.pgstac.main:app --port 8082 --reload

###############################################################################
# VECTOR
python -m pip install tipg
.venv/bin/uvicorn tipg.main:app --port 8083 --reload
```

Note: Python libraries might have incompatible dependencies, which you can resolve by using a virtual environment for each one.

</details>

### Deployment on the cloud

#### Kubernetes 

[eoapi-k8s](https://github.com/developmentseed/eoapi-k8s) contains IaC and Helm charts for deploying eoAPI services on AWS and GCP.

#### AWS CDK

[eoapi-cdk](https://github.com/developmentseed/eoapi-cdk) defines a set of AWS CDK constructs that can be used to deploy eoAPI services on AWS. This repository itself makes use of these in `infrastructure/aws`. An official example usage of these constructs can be found at [eoapi-template](https://github.com/developmentseed/eoapi-template).



## Deployment with custom runtimes

The eoAPI repository hosts customized versions of each base service which can work in parallel or in combination with each other.

eoAPI custom runtimes can be launched with docker:

```
docker compose -f docker-compose.custom.yml --profile gunicorn up
```

Alternatively, you may launch the application locally:
```bash
python -m pip install --upgrade virtualenv
virtualenv .venv
source .venv/bin/activate

python -m pip install "psycopg[binary,pool]" uvicorn
python -m pip install runtime/eoapi/{SERVICE}  # SERVICE should be one of `raster, vector, stac.`

export DATABASE_URL=postgresql://username:password@0.0.0.0:5439/postgis  # Connect to the database of your choice

.venv/bin/uvicorn eoapi.{SERVICE}.app:app --port 8000 --reload
```

Note: services might have incompatible dependencies, which you can resolve by using a virtual environment for each service.

## Contribution & Development

We highly value and rely on our community! You can make a difference whether you're an expert or just getting started. Here's how:

- **Contribute**: Check out our [CONTRIBUTING.md](https://github.com/developmentseed/eoAPI/blob/main/CONTRIBUTING.md) guide to understand how you can contribute.
- **Engage in Discussions**: Share your ideas, ask questions, or provide feedback through [GitHub Discussions](https://github.com/developmentseed/eoAPI/discussions). This is where most of our project conversations take place.
- **Report Issues**: Found a bug or have a feature request? Raise it on our [issues page](https://github.com/developmentseed/eoAPI/issues).

---
## License

At Development Seed, we believe in open collaboration and making tools and data more accessible. In line with this ethos, we've explicitly chosen a MIT license for `eoAPI`.

For full license details, see [LICENSE](https://github.com/developmentseed/eoAPI/blob/main/LICENSE).

## Authors

Nurtured by [Development Seed](<http://developmentseed.org>)

See [contributors](https://github.com/developmentseed/eoAPI/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/eoAPI/blob/main/CHANGES.md).
