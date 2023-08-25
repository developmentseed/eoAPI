
<p align="center">
  <img width="700" src="docs/logos/eoAPI.png"/>
  <p align="center">Create a full Earth Observation API with Metadata, Raster and Vector services.</p>
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

`eoAPI` combines several *state-of-the-art* projects to create a full Earth Observation API. Each service can be used and deployed independently but `eoAPI` creates the interconnections between each service:

- **pgSTAC** database [https://github.com/stac-utils/pgstac](https://github.com/stac-utils/pgstac)

- **STAC API** built on top of [https://github.com/stac-utils/stac-fastapi](https://github.com/stac-utils/stac-fastapi)

- **STAC Items And Mosaic Raster Tiles** API built on top of [https://github.com/stac-utils/titiler-pgstac](https://github.com/stac-utils/titiler-pgstac)

- **OGC Features and Vector Tiles** API built on top of [https://github.com/developmentseed/tipg](https://github.com/developmentseed/tipg)

---

## 🌍 eoAPI: An Open-Source Community Project

`eoAPI` is proudly open-source and driven by a dedicated community of contributors. We believe in the power of open collaboration and welcome anyone to contribute, discuss, and grow this tool with us. Join the conversations on [GitHub Discussions](https://github.com/developmentseed/eoAPI/discussions) and make a difference in the Earth Observation realm.


---

## Getting started

- Clone the repository: `git clone https://github.com/developmentseed/eoAPI.git`
- Navigate to the project: `cd eoAPI`
- Run services with `docker compose up`
- Follow the [MAXAR open data demo](https://github.com/vincentsarago/MAXAR_opendata_to_pgstac) (or get inspired by the other [demos](./demo/)) to load some data into eoAPI
- Check out the [Search Viewer](http://localhost:8081/index.html), and the API documentation ([STAC Metadata](http://localhost:8081/docs), [Raster Tiles](http://localhost:8082/docs), [Vector Tiles](http://localhost:8083/api.html))

Alternatively, you may launch the application locally:
```bash
python -m pip install --upgrade virtualenv
virtualenv .venv
source .venv/bin/activate

python -m pip install "psycopg[binary,pool]" uvicorn
python -m pip install runtime/eoapi/{SERVICE}  # SERVICE should be one of `raster, vector, stac`

export DATABASE_URL=postgresql://username:password@0.0.0.0:5439/postgis  # Connect to the database of your choice

.venv/bin/uvicorn eoapi.{SERVICE}.app:app --port 8000 --reload
```

Note: services might have incompatible dependencies which you can resolve by using a virtual environment for each service

---

## Deployment

This repository has current runtimes that are consistently updated with new functionality. 

The services can be deployed locally via docker with `docker-compose up`. The official runtimes can be launched with `docker-compose -f docker-compose.yml -f docker-compose.official.yml up stac-fastapi titiler-pgstac tipg`. 

Two Infrastructure as Code (IaC) repositories are available:
- [eoapi-cdk](https://github.com/developmentseed/eoapi-cdk): A set of AWS CDK constructs to deploy eoAPI services
- [eoapi-k8s](https://github.com/developmentseed/eoapi-k8s): IaC and Helm charts for deploying eoAPI services on AWS and GCP

Finally, [eoapi-template](https://github.com/developmentseed/eoapi-template) is an AWS CDK app that shows how to configure the eoapi-cdk constructs.

## Contribution & Development

We highly value and rely on our community! Whether you're an expert or just getting started, you can make a difference. Here's how:

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
