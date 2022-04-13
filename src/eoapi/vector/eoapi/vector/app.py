"""eoAPI.vector FastAPI application."""

from typing import Dict

from timvt.factory import VectorTilerFactory
from timvt.layer import Function, FunctionRegistry

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

from eoapi.vector.config import ApiSettings
from eoapi.vector.db import close_db_connection, connect_to_db
from eoapi.vector.dependencies import LayerParams, TileMatrixSetParams
from eoapi.vector.middleware import CacheControlMiddleware
from eoapi.vector.version import __version__

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

settings = ApiSettings()

app = FastAPI(title=settings.name, version=__version__)

vector = VectorTilerFactory(
    layer_dependency=LayerParams,
    with_tables_metadata=False,  # We are not using table
    with_functions_metadata=True,
    with_viewer=True,
    tms_dependency=TileMatrixSetParams,
)
app.include_router(vector.router)

app.state.function_catalog = FunctionRegistry()
app.state.function_catalog.register(
    Function.from_file(
        id="search",
        infile=str(resources_files("eoapi.vector").joinpath("sql/search.sql")),  # type: ignore
        function_name="search_mvt",
    )
)

app.state.function_catalog.register(
    Function.from_file(
        id="mercator",
        infile=str(resources_files("eoapi.vector").joinpath("sql/mercator.sql")),  # type: ignore
        function_name="mercator",
    )
)

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
app.add_middleware(CompressionMiddleware, minimum_size=0)


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
