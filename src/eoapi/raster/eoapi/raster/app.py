"""TiTiler+PgSTAC FastAPI application."""

import logging
from typing import Dict

from starlette_cramjam.middleware import CompressionMiddleware

from eoapi.raster.config import ApiSettings
from eoapi.raster.factory import STACTilerFactory
from eoapi.raster.version import __version__ as eoapi_raster_version
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.resources.enums import OptionalHeader
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.pgstac.db import close_db_connection, connect_to_db
from titiler.pgstac.factory import MosaicTilerFactory

logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("rio-tiler").setLevel(logging.ERROR)

settings = ApiSettings()

app = FastAPI(title=settings.name, version=eoapi_raster_version)

add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

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

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

if settings.debug:
    optional_headers = [OptionalHeader.server_timing]
else:
    optional_headers = []

# PgSTAC mosaic tiler
mosaic = MosaicTilerFactory(router_prefix="mosaic", optional_headers=optional_headers)
app.include_router(mosaic.router, prefix="/mosaic", tags=["PgSTAC Mosaic"])

# Custom STAC titiler endpoint (not added to the openapi docs)
stac = STACTilerFactory(router_prefix="stac", optional_headers=optional_headers)
app.include_router(
    stac.router,
    prefix="/stac",
    tags=["SpatioTemporal Asset Catalog"],
    include_in_schema=False,
)


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping() -> Dict:
    """Health check."""
    return {"ping": "pong!"}


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
