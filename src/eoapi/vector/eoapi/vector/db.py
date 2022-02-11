"""Database connection handling."""

from buildpg import asyncpg
from timvt.settings import PostgresSettings

from fastapi import FastAPI

pg_settings = PostgresSettings()


async def connect_to_db(app: FastAPI) -> None:
    """Connect."""
    app.state.pool = await asyncpg.create_pool_b(
        pg_settings.database_url,
        min_size=pg_settings.db_min_conn_size,
        max_size=pg_settings.db_max_conn_size,
        max_queries=pg_settings.db_max_queries,
        max_inactive_connection_lifetime=pg_settings.db_max_inactive_conn_lifetime,
        server_settings={
            "search_path": "pgstac,public",
            "application_name": "pgstac",
        },
    )


async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    await app.state.pool.close()
