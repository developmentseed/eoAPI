"""TiTiler+PgSTAC FastAPI application."""

import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.resources.enums import OptionalHeader
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.pgstac.db import close_db_connection, connect_to_db
from titiler.pgstac.dependencies import ItemPathParams
from titiler.pgstac.reader import PgSTACReader

from eoapi.raster.config import ApiSettings
from eoapi.raster.factory import MosaicTilerFactory, MultiBaseTilerFactory
from eoapi.raster.version import __version__ as eoapi_raster_version

logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("rio-tiler").setLevel(logging.ERROR)

settings = ApiSettings()

if settings.debug:
    optional_headers = [OptionalHeader.server_timing, OptionalHeader.x_assets]
else:
    optional_headers = []

app = FastAPI(title=settings.name, version=eoapi_raster_version)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

# Custom PgSTAC mosaic tiler
mosaic = MosaicTilerFactory(
    router_prefix="/mosaic",
    enable_mosaic_search=settings.enable_mosaic_search,
    optional_headers=optional_headers,
)
app.include_router(mosaic.router, prefix="/mosaic", tags=["Mosaic"])

stac = MultiBaseTilerFactory(
    reader=PgSTACReader,
    path_dependency=ItemPathParams,
    optional_headers=optional_headers,
    router_prefix="/stac",
)
app.include_router(stac.router, tags=["Items"], prefix="/stac")


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


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
