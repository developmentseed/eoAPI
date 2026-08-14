#!/usr/bin/env python3
"""Wait for PostgreSQL, then migrate its PgSTAC schema."""

import logging
import os
import time

from psycopg import OperationalError, connect

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def wait_for_database() -> None:
    """Wait up to two minutes for PostgreSQL to accept connections."""
    for _ in range(120):
        try:
            with connect(""):
                return
        except OperationalError:
            time.sleep(1)

    msg = "PostgreSQL did not accept connections within two minutes."
    raise RuntimeError(msg)


if __name__ == "__main__":
    wait_for_database()
    LOGGER.info("Migrating PgSTAC to %s", os.environ["PGSTAC_VERSION"])
    os.execvp("pypgstac", ["pypgstac", "migrate"])
