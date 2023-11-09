"""TiTiler+PgSTAC FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import Dict

import pystac
from eoapi.raster import __version__ as eoapi_raster_version
from eoapi.raster.config import ApiSettings
from fastapi import Depends, FastAPI, Query
from psycopg import OperationalError
from psycopg.rows import dict_row
from psycopg_pool import PoolTimeout
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import AlgorithmFactory, MultiBaseTilerFactory, TMSFactory
from titiler.core.middleware import CacheControlMiddleware
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.pgstac.db import close_db_connection, connect_to_db
from titiler.pgstac.dependencies import CollectionIdParams, ItemIdParams, SearchIdParams
from titiler.pgstac.extensions import searchInfoExtension
from titiler.pgstac.factory import (
    MosaicTilerFactory,
    add_search_list_route,
    add_search_register_route,
)
from titiler.pgstac.reader import PgSTACReader

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("rio-tiler").setLevel(logging.ERROR)

settings = ApiSettings()

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan."""
    # Create Connection Pool
    await connect_to_db(app)
    yield
    # Close the Connection Pool
    await close_db_connection(app)


app = FastAPI(
    title=settings.name,
    version=eoapi_raster_version,
    root_path=settings.root_path,
    lifespan=lifespan,
)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol=settings.cachecontrol,
    exclude_path={r"/healthz"},
)
app.add_middleware(
    CompressionMiddleware,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
)

###############################################################################
# `Secret` endpoint for mosaic builder. Do not need to be public (in the OpenAPI docs)
@app.get("/collections", include_in_schema=False)
async def list_collection(request: Request):
    """list collections."""
    with request.app.state.dbpool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM pgstac.all_collections();")
            r = cursor.fetchone()
            return r.get("all_collections", [])


###############################################################################
# STAC Search Endpoints
searches = MosaicTilerFactory(
    path_dependency=SearchIdParams,
    router_prefix="/searches/{search_id}",
    add_statistics=True,
    add_viewer=True,
    add_part=True,
    extensions=[
        searchInfoExtension(),
    ],
)
app.include_router(
    searches.router, tags=["STAC Search"], prefix="/searches/{search_id}"
)

add_search_register_route(
    app,
    prefix="/searches",
    tile_dependencies=[
        searches.layer_dependency,
        searches.dataset_dependency,
        searches.pixel_selection_dependency,
        searches.tile_dependency,
        searches.process_dependency,
        searches.rescale_dependency,
        searches.colormap_dependency,
        searches.render_dependency,
        searches.pgstac_dependency,
        searches.reader_dependency,
        searches.backend_dependency,
    ],
    tags=["STAC Search"],
)
add_search_list_route(app, prefix="/searches", tags=["STAC Search"])


@app.get("/searches/builder", response_class=HTMLResponse, tags=["STAC Search"])
async def virtual_mosaic_builder(request: Request):
    """Mosaic Builder Viewer."""
    base_url = str(request.base_url)
    return templates.TemplateResponse(
        name="mosaic-builder.html",
        context={
            "request": request,
            "register_endpoint": str(
                app.url_path_for("register_search").make_absolute_url(base_url=base_url)
            ),
            "collections_endpoint": str(
                app.url_path_for("list_collection").make_absolute_url(base_url=base_url)
            ),
        },
        media_type="text/html",
    )


###############################################################################
# STAC COLLECTION Endpoints
collection = MosaicTilerFactory(
    path_dependency=CollectionIdParams,
    router_prefix="/collections/{collection_id}",
    add_statistics=True,
    add_viewer=True,
    add_part=True,
)
app.include_router(
    collection.router, tags=["STAC Collection"], prefix="/collections/{collection_id}"
)


###############################################################################
# STAC Item Endpoints
stac = MultiBaseTilerFactory(
    reader=PgSTACReader,
    path_dependency=ItemIdParams,
    router_prefix="/collections/{collection_id}/items/{item_id}",
    add_viewer=True,
)
app.include_router(
    stac.router,
    tags=["STAC Item"],
    prefix="/collections/{collection_id}/items/{item_id}",
)


@stac.router.get("/viewer", response_class=HTMLResponse)
def viewer(request: Request, item: pystac.Item = Depends(stac.path_dependency)):
    """STAC Viewer

    Simplified version of https://github.com/developmentseed/titiler/blob/main/src/titiler/extensions/titiler/extensions/templates/stac_viewer.html
    """
    return templates.TemplateResponse(
        name="stac-viewer.html",
        context={
            "request": request,
            "endpoint": request.url.path.replace("/viewer", ""),
        },
        media_type="text/html",
    )


app.include_router(
    stac.router,
    tags=["STAC Item"],
    prefix="/collections/{collection_id}/items/{item_id}",
)


###############################################################################
# Tiling Schemes Endpoints
tms = TMSFactory()
app.include_router(tms.router, tags=["Tiling Schemes"])

###############################################################################
# Algorithms Endpoints
algorithms = AlgorithmFactory()
app.include_router(algorithms.router, tags=["Algorithms"])


###############################################################################
# Health Check Endpoint
@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping(
    timeout: int = Query(1, description="Timeout getting SQL connection from the pool.")
) -> Dict:
    """Health check."""
    try:
        with app.state.dbpool.connection(timeout) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version from pgstac.migrations;")
                version = cursor.fetchone()
        return {"database_online": True, "pgstac_version": version}
    except (OperationalError, PoolTimeout):
        return {"database_online": False}


###############################################################################
# Landing page Endpoint
@app.get(
    "/",
    response_class=HTMLResponse,
)
def landing(request: Request):
    """Get landing page."""
    data = {
        "title": settings.name or "eoAPI-raster",
        "links": [
            {
                "title": "Landing page",
                "href": str(request.url_for("landing")),
                "type": "text/html",
                "rel": "self",
            },
            {
                "title": "the API definition (JSON)",
                "href": str(request.url_for("openapi")),
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "rel": "service-desc",
            },
            {
                "title": "the API documentation",
                "href": str(request.url_for("swagger_ui_html")),
                "type": "text/html",
                "rel": "service-doc",
            },
            {
                "title": "PgSTAC Virtual Mosaic list (JSON)",
                "href": str(app.url_path_for("list_searches")),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "PgSTAC Virtual Mosaic builder",
                "href": str(app.url_path_for("virtual_mosaic_builder")),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "PgSTAC Virtual Mosaic viewer (template URL)",
                "href": str(app.url_path_for("map_viewer", search_id="{search_id}")),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "PgSTAC Collection viewer (template URL)",
                "href": str(
                    app.url_path_for("map_viewer", collection_id="{collection_id}")
                ),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "PgSTAC Item viewer (template URL)",
                "href": str(
                    app.url_path_for(
                        "map_viewer",
                        collection_id="{collection_id}",
                        item_id="{item_id}",
                    )
                ),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "TiTiler-PgSTAC Documentation (external link)",
                "href": "https://stac-utils.github.io/titiler-pgstac/",
                "type": "text/html",
                "rel": "doc",
            },
            {
                "title": "TiTiler-PgSTAC source code (external link)",
                "href": "https://github.com/stac-utils/titiler-pgstac",
                "type": "text/html",
                "rel": "doc",
            },
        ],
    }

    urlpath = request.url.path
    crumbs = []
    baseurl = str(request.base_url).rstrip("/")

    crumbpath = str(baseurl)
    for crumb in urlpath.split("/"):
        crumbpath = crumbpath.rstrip("/")
        part = crumb
        if part is None or part == "":
            part = "Home"
        crumbpath += f"/{crumb}"
        crumbs.append({"url": crumbpath.rstrip("/"), "part": part.capitalize()})

    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "response": data,
            "template": {
                "api_root": baseurl,
                "params": request.query_params,
                "title": "",
            },
            "crumbs": crumbs,
            "url": str(request.url),
            "baseurl": baseurl,
            "urlpath": str(request.url.path),
            "urlparams": str(request.url.query),
        },
    )
