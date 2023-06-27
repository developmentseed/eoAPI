---
hide:
  - navigation
---

The `eoAPI` is composed of four services built on top of `state-of-the-art` projects: [**pgstac**](https://github.com/stac-utils/pgstac), [**stac-fastapi**](https://github.com/stac-utils/stac-fastapi), [**titiler-pgstac**](https://github.com/stac-utils/titiler-pgstac) and [**tipg**](https://github.com/developmentseed/tipg). While those offert a great baseline, we choose to customize them to demo how they could work together, not only be used in parallel.

## Metadata

A custom version of [stac-fastapi.pgstac](https://github.com/stac-utils/stac-fastapi) application, adding a **`TiTilerExtension`** and a simple **`Search Viewer`**.

The service includes:

- Full **stac-fastapi** implementation - see [docs](http://localhost:8081/docs) if using the `docker-compose` configuration.

- Simple STAC Search **viewer** - see [viewer](http://localhost:8081/index.html) if using the `docker-compose` configuration.

- **Proxy** to the Tiler endpoint for STAC Items

  When `TITILER_ENDPOINT` environement is set (pointing the `raster` application), additional endpoints will be added to the stac-fastapi application (see: [stac/extension.py](https://github.com/developmentseed/eoAPI/blob/main/src/eoapi/stac/eoapi/stac/extension.py)):

  - `/collections/{collectionId}/items/{itemId}/tilejson.json`: Return the `raster` tilejson for an item
  - `/collections/{collectionId}/items/{itemId}/viewer`: Redirect to the `raster` viewer

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/146790933-e439893c-ef2e-4d78-a372-f2f18694836c.png"/>
  <p align="center">STAC Search viewer</p>
</p>

Code: [/runtime/eoapi/stac](https://github.com/developmentseed/eoAPI/tree/main/runtime/eoapi/stac)

---

## Raster

The dynamic tiler deployed within eoAPI is built on top of [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) and [pgstac](https://github.com/stac-utils/pgstac). It enables large scale mosaic based on results of STAC searches queries.

The service includes:

- Full **titiler-pgstac** implementation

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/129632282-f71e9f45-264c-4882-af28-7062c4e56f25.png"/>
  <p align="center">TiTiler-PgSTAC workflow</p>
</p>

Code: [/runtime/eoapi/raster](https://github.com/developmentseed/eoAPI/tree/main/runtime/eoapi/raster)

---

## Vector

OGC Features + Tiles API built on top of [tipg](https://github.com/developmentseed/tipg).

By default, the API will look for tables in the `public` schema of the database. We've also added three custom functions which connect to the pgSTAC schema.

- **pg_temp.pgstac_collections_view**: Simple function which return PgSTAC Collections
- **pg_temp.pgstac_hash**: Return features for a specific searchId (hash)
- **pg_temp.pgstac_hash_count**: Return the number of items per geometry for a specific searchId (hash)

Code: [/runtime/eoapi/vector](https://github.com/developmentseed/eoAPI/tree/main/runtime/eoapi/vector)

---
