"""FastAPI application using PGStac."""

from eoapi.stac.config import ApiSettings, TilesApiSettings
from eoapi.stac.extension import TilesExtension
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from stac_fastapi.api.app import StacApi
from stac_fastapi.extensions.core import (
    FieldsExtension,
    QueryExtension,
    SortExtension,
    TransactionExtension,
)
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from stac_fastapi.pgstac.transactions import TransactionsClient
from stac_fastapi.pgstac.types.search import PgstacSearch
from starlette.middleware.cors import CORSMiddleware

api_settings = ApiSettings()
tiles_settings = TilesApiSettings()
settings = Settings()


api = StacApi(
    app=FastAPI(title=api_settings.name),
    settings=settings,
    extensions=[
        TransactionExtension(
            client=TransactionsClient(),
            settings=settings,
            response_class=ORJSONResponse,
        ),
        QueryExtension(),
        SortExtension(),
        FieldsExtension(),
    ],
    client=CoreCrudClient(),
    search_request_model=PgstacSearch,
    response_class=ORJSONResponse,
)
app = api.app


# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

if tiles_settings.titiler_endpoint:
    # Register to the tiles extension to the api
    extension = TilesExtension()
    extension.register(api.app, tiles_settings.titiler_endpoint)


@app.on_event("startup")
async def startup_event():
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection."""
    await close_db_connection(app)
