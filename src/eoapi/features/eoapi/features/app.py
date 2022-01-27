"""eoAPI.features FastAPI application."""

from eoapi.features.config import ApiSettings
from eoapi.features.db import close_db_connection, connect_to_db
from eoapi.features.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from eoapi.features.factory import Endpoints
from eoapi.features.middleware import CacheControlMiddleware
from eoapi.features.version import __version__
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

settings = ApiSettings()

app = FastAPI(title=settings.name, version=__version__, openapi_url="/api")

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(CacheControlMiddleware, cachecontrol=settings.cachecontrol)
app.add_middleware(CompressionMiddleware)
add_exception_handlers(app, DEFAULT_STATUS_CODES)

app.include_router(Endpoints().router)


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
