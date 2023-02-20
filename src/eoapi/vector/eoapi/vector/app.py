"""tipg app."""

from typing import Any, List

import jinja2
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware
from tipg.db import close_db_connection, connect_to_db, register_collection_catalog
from tipg.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from tipg.factory import Endpoints as TiPgEndpoints
from tipg.middleware import CacheControlMiddleware
from tipg.settings import DatabaseSettings, PostgresSettings

from eoapi.vector import __version__ as eoapi_vector_version
from eoapi.vector.config import ApiSettings

settings = ApiSettings()
postgres_settings = PostgresSettings()
db_settings = DatabaseSettings()

app = FastAPI(
    title=settings.name,
    version=eoapi_vector_version,
    openapi_url="/api",
    docs_url="/api.html",
)

# add eoapi_vector templates and tipg templates
templates = Jinja2Templates(  # type: ignore
    directory="",
    loader=jinja2.ChoiceLoader(
        [
            jinja2.PackageLoader(__package__, "templates"),
            jinja2.PackageLoader("tipg", "templates"),
        ]
    ),
)

# Register TiPg endpoints.
endpoints = TiPgEndpoints(title=settings.name, templates=templates)
app.include_router(endpoints.router, tags=["OGC API"])

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


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(
        app,
        settings=postgres_settings,
        server_settings={"search_path": "pgstac,public", "application_name": "pgstac"},
    )
    await register_collection_catalog(
        app,
        schemas=["public"],
        tables=db_settings.tables,
        function_schemas=["pg_temp"],
        # functions=db_settings.functions,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)


@app.get(
    "/healthz",
    description="Health Check.",
    summary="Health Check.",
    operation_id="healthCheck",
    tags=["Health Check"],
)
def ping():
    """Health check."""
    return {"ping": "pong!"}


if settings.debug:

    @app.get("/rawcatalog")
    async def raw_catalog(request: Request):
        """Return parsed catalog data for testing."""
        return request.app.state.collection_catalog

    @app.get("/refresh")
    async def refresh(request: Request):
        """Return parsed catalog data for testing."""
        await startup_event()
        return request.app.state.collection_catalog
