"""TiTiler+PgSTAC FastAPI application."""

import logging
from typing import Dict

import pystac
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

from eoapi.raster.config import ApiSettings
from eoapi.raster.version import __version__ as eoapi_raster_version

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
    add_map_viewer=True,
    add_mosaic_list=True,
)
app.include_router(mosaic.router, tags=["Mosaic"], prefix="/mosaic")

###############################################################################
# STAC Item Endpoints
stac = MultiBaseTilerFactory(
    reader=PgSTACReader,
    path_dependency=ItemPathParams,
    optional_headers=optional_headers,
    router_prefix="/collections/{collection_id}/items/{item_id}",
)


@stac.router.get("/viewer", response_class=HTMLResponse)
def viewer(request: Request, item: pystac.Item = Depends(stac.path_dependency)):
    """STAC Viewer."""
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
