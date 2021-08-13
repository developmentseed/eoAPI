"""Database connection handling."""

from psycopg2 import pool

from eoapi.tiler.config import PostgresSettings
from fastapi import FastAPI

settings = PostgresSettings()


async def connect_to_db(app: FastAPI) -> None:
    """Connect to Database."""
    app.state.readpool = pool.ThreadedConnectionPool(
        minconn=settings.db_min_conn_size,
        maxconn=settings.db_max_conn_size,
        dsn=settings.reader_connection_string,
        options="-c search_path=pgstac,public -c application_name=pgstac",
    )
    app.state.writepool = pool.ThreadedConnectionPool(
        minconn=settings.db_min_conn_size,
        maxconn=settings.db_max_conn_size,
        dsn=settings.writer_connection_string,
        options="-c search_path=pgstac,public -c application_name=pgstac",
    )


async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    app.state.readpool.closeall()
    app.state.writepool.closeall()
