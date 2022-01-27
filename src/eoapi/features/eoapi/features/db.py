"""Database connection handling."""

from functools import lru_cache

import orjson
from buildpg import asyncpg
from pydantic import BaseSettings

from fastapi import FastAPI


class _PostgresSettings(BaseSettings):
    """Postgres-specific API settings.

    Attributes:
        postgres_user: postgres username.
        postgres_pass: postgres password.
        postgres_host: hostname for the connection.
        postgres_port: database port.
        postgres_dbname: database name.
    """

    postgres_user: str
    postgres_pass: str
    postgres_host: str
    postgres_port: str
    postgres_dbname: str

    db_min_conn_size: int = 1
    db_max_conn_size: int = 10
    db_max_queries: int = 50000
    db_max_inactive_conn_lifetime: float = 300

    class Config:
        """model config"""

        env_file = ".env"

    @property
    def dsn(self):
        """Create reader psql connection string."""
        return f"postgresql://{self.postgres_user}:{self.postgres_pass}@{self.postgres_host}:{self.postgres_port}/{self.postgres_dbname}"


@lru_cache()
def PostgresSettings() -> _PostgresSettings:
    """This function returns a cached instance of the PostgresSettings object."""
    return _PostgresSettings()


settings = PostgresSettings()


async def con_init(conn):
    """Use orjson for json returns."""
    await conn.set_type_codec(
        "json",
        encoder=orjson.dumps,
        decoder=orjson.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=orjson.dumps,
        decoder=orjson.loads,
        schema="pg_catalog",
    )


async def connect_to_db(app: FastAPI) -> None:
    """Create connection pool."""
    app.state.pool = await asyncpg.create_pool_b(
        settings.dsn,
        min_size=settings.db_min_conn_size,
        max_size=settings.db_max_conn_size,
        max_queries=settings.db_max_queries,
        max_inactive_connection_lifetime=settings.db_max_inactive_conn_lifetime,
        init=con_init,
        server_settings={
            "search_path": "pgstac,public",
            "application_name": "pgstac",
        },
    )


async def close_db_connection(app: FastAPI) -> None:
    """Close connection pool."""
    await app.state.pool.close()
