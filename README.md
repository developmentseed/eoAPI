
<p align="center">
  <img width="700" src="https://user-images.githubusercontent.com/10407788/236044449-f7d21e6c-c196-4f9e-b4b6-59c945e92644.png"/>
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

**Documentation**: <a href="https://developmentseed.org/eoAPI/" target="_blank">https://developmentseed.org/eoAPI/</a>

**Source Code**: <a href="https://github.com/developmentseed/eoAPI" target="_blank">https://github.com/developmentseed/eoAPI</a>

---

## **E**arth **O**bservation **API**

`eoAPI` combines several *state-of-the-art* projects to create a full Earth Observation API. Each service can be used and deployed independently but `eoAPI` creates the interconnections between each service:

- **pgSTAC** database [https://github.com/stac-utils/pgstac](https://github.com/stac-utils/pgstac)

- **STAC API** built on top of [https://github.com/stac-utils/stac-fastapi](https://github.com/stac-utils/stac-fastapi)

- **STAC Items And Mosaic Raster Tiles** API built on top of [https://github.com/stac-utils/titiler-pgstac](https://github.com/stac-utils/titiler-pgstac)

- **OGC Features and Vector Tiles** API built on top of [https://github.com/developmentseed/tipg](https://github.com/developmentseed/tipg)

---

## Why should you use `eoAPI`
- **Focus on your use case:** `eoAPI` is used for large-scale data processing, building geographic information systems (GIS), creating real-time data applications, climate research and environmental monitoring, machine learning model training, and more.
- **Unified Repository:** `eoAPI` provides a single, unified repository to several state-of-the-art Earth Observation (EO) data services, including Metadata search (STAC), Raster, and Vector services. This can simplify the process of accessing and working with these services.
- **Interoperability:** `eoAPI` is designed to enable interoperability among its included services. This can make building complex applications that leverage different types of EO data easier.
- **Open Source and Community Support:** As an open-source project, `eoAPI` allows developers to inspect its code, contribute to its development, and use it as a base for custom solutions. It also benefits from the support and innovation of a community of developers and EO data users.
- **Scalability and Flexibility:** Each service in `eoAPI` can be used or deployed independently, which provides a lot of flexibility. If a developer's application only requires one or two of eoAPI's services, they don't need to deploy the entire suite.
- **Facilitate Earth Observation Tasks:** `eoAPI` includes specialized tools for working with EO data, such as dynamic tiling, metadata searching, and features/vector tiles API. These can significantly facilitate EO data processing, analysis, and visualization.
- **Ease of Deployment:** `eoAPI` supports containerized deployment using Docker, making it easier to set up, scale, and maintain applications built on it. Spin up the demo locally and start experimenting in minutes.

---

## Services Overview


- **STAC Metadata**: Built with [stac-fastapi.pgstac](https://github.com/stac-utils/stac-fastapi) and extended with a custom extension to connect it to **`TiTiler`** and a **[Search Viewer](http://localhost:8081/index.html)**. See [docs](http://localhost:8081/docs) for API details.
- **Raster Tiles**: Built with [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) and [pgstac](https://github.com/stac-utils/pgstac) to enable large scale mosaic based on results of STAC searches queries. See [docs](http://localhost:8082/docs) for API details.
- **OGC Features & Vector Tiles**: Built with [tipg](https://github.com/developmentseed/tipg) to create a lightweight OGC Features and Tiles API with a PostGIS database. See [docs](http://localhost:8083/api.html) for API details.

See [service details](./docs/src/services-details.md) for more information. 

*Note: The documentation links referenced require lauching the application with `docker-compose` or another deployment*.

---

## Getting started

- Clone the repository: `git clone https://github.com/developmentseed/eoAPI.git`
- Navigate to the project: `cd eoAPI`
- Run services with `docker-compose up`
- Follow the [MAXAR open data demo](https://github.com/vincentsarago/MAXAR_opendata_to_pgstac) (or get inspired by the other [demos](./demo/)) to load some data into eoAPI
- Checkout the [Search Viewer](http://localhost:8081/index.html), and the API documentation ([STAC Metadata](http://localhost:8081/docs), [Raster Tiles](http://localhost:8082/docs), [Vector Tiles](http://localhost:8083/api.html))

Alternatively, you may launch the application locally:
```bash
python -m pip install --upgrade virtualenv
virtualenv .venv
source .venv/bin/activate

python -m pip install "psycopg[binary,pool]" uvicorn
python -m pip install runtime/eoapi/raster runtime/eoapi/stac runtime/eoapi/vector

export DATABASE_URL=postgresql://username:password@0.0.0.0:5439/postgis  # Connect to the database of your choice

# OGC Features/Tiles
.venv/bin/uvicorn eoapi.vector.app:app --port 8000 --reload

# Raster
.venv/bin/uvicorn eoapi.raster.app:app --port 8000 --reload

# STAC
.venv/bin/uvicorn eoapi.stac.app:app --port 8000 --reload
```
---
## Deployment

See [DEPLOYMENT.md](https://github.com/developmentseed/eoAPI/blob/main/infrastructure/DEPLOYMENT.md)

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/eoAPI/blob/main/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/eoAPI/blob/main/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

See [contributors](https://github.com/developmentseed/eoAPI/graphs/contributors) for a listing of individual contributors.

## Changes

See [CHANGES.md](https://github.com/developmentseed/eoAPI/blob/main/CHANGES.md).
