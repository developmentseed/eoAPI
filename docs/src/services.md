---

hide:

- navigation

---

eoAPI combines several state-of-the-art projects to create a full Earth Observation API. Each service can be used and deployed independently but eoAPI creates the interconnections between each service:

- pgSTAC database https://github.com/stac-utils/pgstac
- STAC API built on top of https://github.com/stac-utils/stac-fastapi
- STAC Items And Mosaic Raster Tiles API built on top of https://github.com/stac-utils/titiler-pgstac
- OGC Features and Vector Tiles API built on top of https://github.com/developmentseed/tipg

## Metadata

A custom version of [stac-fastapi.pgstac](https://github.com/stac-utils/stac-fastapi) application, adding a **`TiTilerExtension`** and a simple **`Search Viewer`**.

The service includes:

- Full **stac-fastapi** implementation - see [docs](http://localhost:8081/docs) if using the `docker-compose` configuration.
- Simple STAC Search **viewer** - see [viewer](http://localhost:8081/index.html) if using the `docker-compose` configuration.
- **Proxy** to the tiler endpoint for STAC Items.
    
When the `TITILER_ENDPOINT` environment variable is set (pointing to the `raster` application), additional endpoints will be added to the stac-fastapi application (see: [stac/extension.py](https://github.com/developmentseed/eoAPI/blob/main/src/eoapi/stac/eoapi/stac/extension.py)):

- `/collections/{collectionId}/items/{itemId}/tilejson.json`: Return the `raster` tilejson for an item
- `/collections/{collectionId}/items/{itemId}/viewer`: Redirect to the `raster` viewer

<p align="center">
<img src="https://user-images.githubusercontent.com/10407788/146790933-e439893c-ef2e-4d78-a372-f2f18694836c.png"/>
<p align="center">STAC Search viewer</p>
</p>

Code: [/runtime/eoapi/stac](https://github.com/developmentseed/eoAPI/tree/main/runtime/eoapi/stac)

---

## Raster

The dynamic tiler deployed within `eoAPI` is built on top of [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) and [pgstac](https://github.com/stac-utils/pgstac). It enables large-scale mosaic based on the results of STAC search queries.

The service includes:

- Full **titiler-pgstac** implementation.

<p align="center">
<img src="https://user-images.githubusercontent.com/10407788/129632282-f71e9f45-264c-4882-af28-7062c4e56f25.png"/>
<p align="center">TiTiler-PgSTAC workflow</p>
</p>

Code: [/runtime/eoapi/raster](https://github.com/developmentseed/eoAPI/tree/main/runtime/eoapi/raster)

---

## Vector

OGC Features and Tiles API built on top of [tipg](https://github.com/developmentseed/tipg).

By default, the API will look for tables in the `public` schema of the database. We've also added three custom functions that connect to the pgSTAC schema.

- **pg_temp.pgstac_collections_view**: Simple function which returns PgSTAC Collections
- **pg_temp.pgstac_hash**: Return features for a specific `searchId` (hash)
- **pg_temp.pgstac_hash_count**: Return the number of items per geometry for a specific `searchId` (hash)

Code: [/runtime/eoapi/vector](https://github.com/developmentseed/eoAPI/tree/main/runtime/eoapi/vector)