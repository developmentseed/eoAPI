"""Database connection handling."""

from buildpg import asyncpg

from eoapi.vector.config import PostgresSettings
from fastapi import FastAPI

settings = PostgresSettings()


async def connect_to_db(app: FastAPI) -> None:
    """Connect."""
    app.state.pool = await asyncpg.create_pool(
        settings.reader_connection_string,
        min_size=settings.db_min_conn_size,
        max_size=settings.db_max_conn_size,
        max_queries=settings.db_max_queries,
        max_inactive_connection_lifetime=settings.db_max_inactive_conn_lifetime,
        server_settings={"search_path": "pgstac,public", "application_name": "pgstac"},
    )


async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    await app.state.pool.close()
