"""eoAPI.features FastAPI application."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

from eoapi.features.config import ApiSettings
from eoapi.features.db import close_db_connection, connect_to_db
from eoapi.features.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from eoapi.features.factory import Endpoints
from eoapi.features.middleware import CacheControlMiddleware
from eoapi.features.version import __version__ as eoapi_features_version

settings = ApiSettings()

app = FastAPI(title=settings.name, version=eoapi_features_version, openapi_url="/api")
add_exception_handlers(app, DEFAULT_STATUS_CODES)

features = Endpoints()
app.include_router(features.router)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

app.add_middleware(CacheControlMiddleware, cachecontrol=settings.cachecontrol)
app.add_middleware(CompressionMiddleware)


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
