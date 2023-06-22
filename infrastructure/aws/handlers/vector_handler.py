"""AWS Lambda handler."""

import asyncio
import logging
import os

from eoapi.vector.app import app
from mangum import Mangum
from tipg.collections import register_collection_catalog
from tipg.database import connect_to_db
from tipg.settings import PostgresSettings

logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)

postgres_settings = PostgresSettings()

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


CUSTOM_SQL_DIRECTORY = resources_files("eoapi.vector") / "sql"
sql_files = list(CUSTOM_SQL_DIRECTORY.glob("*.sql"))  # type: ignore


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(
        app,
        settings=postgres_settings,
        # We enable both pgstac and public schemas (pgstac will be used by custom functions)
        schemas=["pgstac", "public"],
        user_sql_files=sql_files,
    )
    await register_collection_catalog(
        app,
        # For the Tables' Catalog we only use the `public` schema
        schemas=["public"],
        # We exclude public functions
        exclude_function_schemas=["public"],
        # We allow non-spatial tables
        spatial=False,
    )


handler = Mangum(app, lifespan="off")

if "AWS_EXECUTION_ENV" in os.environ:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.router.startup())
