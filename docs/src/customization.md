The **eoapi-devseed** repository (https://github.com/developmentseed/eoapi-devseed) hosts customized versions of each base service. The documentation below demonstrates how each service can be customized. The eoAPI services can work in parallel or in combination with each other.

---
## eoapi.stac

Built on [stac-fastapi.pgstac](https://github.com/stac-utils/stac-fastapi-pgstac) application, adding a **`TiTilerExtension`** and a simple **`Search Viewer`**.

The service includes:

- Full **stac-fastapi** implementation - see [docs](http://localhost:8081/docs) if using the `docker-compose` configuration.
- Simple STAC Search **viewer** - see [viewer](http://localhost:8081/index.html) if using the `docker-compose` configuration.
- **Proxy** to the tiler endpoint for STAC Items.

When the `TITILER_ENDPOINT` environment variable is set (pointing to the `raster` application), additional endpoints will be added to the stac-fastapi application (see: [stac/extension.py](https://github.com/developmentseed/eoapi-devseed/blob/main/runtimes/eoapi/stac/eoapi/stac/extension.py)):

- `/collections/{collectionId}/items/{itemId}/tilejson.json`: Return the `raster` tilejson for an item
- `/collections/{collectionId}/items/{itemId}/viewer`: Redirect to the `raster` viewer

<p align="center">
<img  alt="eoapi.stac OpenAPI documentation"src="https://github.com/developmentseed/eoAPI/assets/10407788/f7fc4e7f-079a-4007-8c4c-74ff9ca7b012">
<img alt="Metadata STAC search viewer" src="https://github.com/developmentseed/eoAPI/assets/10407788/b1fd6aa8-aab9-4d58-9ad4-6e1069ed9473"/>
</p>

Code: [/runtimes/eoapi/stac](https://github.com/developmentseed/eoapi-devseed/tree/main/runtimes/eoapi/stac)

---
## eoapi.raster

The dynamic tiler deployed within `eoapi-devseed` is built on top of [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) and [pgstac](https://github.com/stac-utils/pgstac). It enables large-scale mosaic based on the results of STAC search queries.

The service includes all the default endpoints from **titiler-pgstac** application and:

- `/`: a custom landing page with links to the different endpoints

- `/mosaic/builder`: a virtual mosaic builder UI, which helps create and register STAC Search queries

- `/collections`: a *secret* (not in OpenAPI documentation) endpoint used in the mosaic-builder page

- `/collections/{collection_id}/items/{item_id}/viewer`: a simple STAC Item viewer

<p align="center">
<img alt="eoapi.stac OpenAPI documentation" src="https://github.com/developmentseed/eoAPI/assets/10407788/aa08d796-f3b1-4f43-8021-cbddfff95d26">
<img alt="Raster mosaic builder" src="https://github.com/developmentseed/eoAPI/assets/10407788/8f0c96e6-d80a-46ef-a34f-66e59c64a027"/>
<img alt="STAC Item viewer" src="https://github.com/developmentseed/eoAPI/assets/10407788/be86f07e-4b05-4c78-87bf-8738daf1ee20">
</p>


Code: [/runtimes/eoapi/raster](https://github.com/developmentseed/eoapi-devseed/tree/main/runtimes/eoapi/raster)

---
## eoapi.vector

OGC Features and Tiles API built on top of [tipg](https://github.com/developmentseed/tipg).

By default, the API will look for tables in the `public` schema of the database. We've also added three functions that connect to the pgSTAC schema:

- **pg_temp.pgstac_collections_view**: Simple function which returns PgSTAC Collections
- **pg_temp.pgstac_hash**: Return features for a specific `searchId` (hash)
- **pg_temp.pgstac_hash_count**: Return the number of items per geometry for a specific `searchId` (hash)

<p align="center">
<img alt="eoapi.vector OpenAPI documentation" src="https://github.com/developmentseed/eoAPI/assets/10407788/80ff9659-bc07-4238-a94a-7cab0a2af380">
<img alt="eoapi.vector landing page" src="https://github.com/developmentseed/eoAPI/assets/10407788/b2a8a8d4-d3a1-464a-8b1a-166499ee4abd">
</p>

Code: [/runtimes/eoapi/vector](https://github.com/developmentseed/eoapi-devseed/tree/main/runtimes/eoapi/vector)

--
# STAC browser

The custom browser configuration can be modified using the config located in [/dockerfiles/browser_config.js](https://github.com/developmentseed/eoapi-devseed/blob/main/dockerfiles/browser_config.js). For more information about available configurations, see the [Radiant Earth repository](https://github.com/radiantearth/stac-browser).
