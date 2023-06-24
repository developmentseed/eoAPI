"""TiTiler+PgSTAC FastAPI application."""

import logging
from typing import Dict

import pystac
from eoapi.raster import __version__ as eoapi_raster_version
from eoapi.raster.config import ApiSettings
from fastapi import Depends, FastAPI, Query
from psycopg import OperationalError
from psycopg_pool import PoolTimeout
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import AlgorithmFactory, MultiBaseTilerFactory, TMSFactory
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.resources.enums import OptionalHeader
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.pgstac.db import close_db_connection, connect_to_db
from titiler.pgstac.dependencies import ItemPathParams
from titiler.pgstac.factory import MosaicTilerFactory
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


if settings.debug:
    optional_headers = [OptionalHeader.server_timing, OptionalHeader.x_assets]
else:
    optional_headers = []

app = FastAPI(title=settings.name, version=eoapi_raster_version)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

###############################################################################
# MOSAIC Endpoints
mosaic = MosaicTilerFactory(
    optional_headers=optional_headers,
    router_prefix="/mosaic",
    add_statistics=True,
    # add /map viewer
    add_viewer=True,
    # add /mosaic/list endpoint
    add_mosaic_list=True,
)


@mosaic.router.get("/builder", response_class=HTMLResponse)
async def mosaic_builder(request: Request):
    """Mosaic Builder Viewer."""
    return templates.TemplateResponse(
        name="mosaic-builder.html",
        context={
            "request": request,
            "register_endpoint": mosaic.url_for(request, "register_search"),
            "collections_endpoint": str(request.url_for("list_collection")),
        },
        media_type="text/html",
    )


# `Secret` endpoint for mosaic builder. Do not need to be public (in the OpenAPI docs)
@app.get("/collections", include_in_schema=False)
async def list_collection(request: Request):
    """list collections."""
    with request.app.state.dbpool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM collections;")
            return [t[2] for t in cursor.fetchall() if t]


app.include_router(mosaic.router, tags=["Mosaic"], prefix="/mosaic")

###############################################################################
# STAC Item Endpoints
stac = MultiBaseTilerFactory(
    reader=PgSTACReader,
    path_dependency=ItemPathParams,
    optional_headers=optional_headers,
    router_prefix="/collections/{collection_id}/items/{item_id}",
    # add /map viewer
    add_viewer=True,
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
    stac.router, tags=["Item"], prefix="/collections/{collection_id}/items/{item_id}"
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
        "title": "eoAPI-Raster",
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
                "title": "Mosaic List (JSON)",
                "href": mosaic.url_for(request, "list_mosaic"),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "Mosaic Builder",
                "href": mosaic.url_for(request, "mosaic_builder"),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "Mosaic Metadata (template URL)",
                "href": mosaic.url_for(request, "info_search", searchid="{searchid}"),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "Mosaic viewer (template URL)",
                "href": mosaic.url_for(request, "map_viewer", searchid="{searchid}"),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "TiTiler-pgSTAC Documentation (external link)",
                "href": "https://stac-utils.github.io/titiler-pgstac/",
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


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
