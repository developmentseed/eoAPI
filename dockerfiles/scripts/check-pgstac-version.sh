#!/bin/sh
set -eu

tries=0
until pg_isready -q -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}"; do
    tries=$((tries + 1))
    if [ "${tries}" -ge 120 ]; then
        printf '%s\n' "PostgreSQL at ${PGHOST}:${PGPORT} did not accept connections within two minutes." >&2
        exit 1
    fi
    sleep 1
done

actual_version="$(psql -X -q -t -A -v ON_ERROR_STOP=1 -c 'SELECT pgstac.get_version()' || true)"

if [ "${actual_version}" = "${PGSTAC_VERSION}" ]; then
    exit 0
fi

if [ -z "${actual_version}" ]; then
    actual_version="unavailable"
fi

printf '%s\n' "PgSTAC schema version ${actual_version} does not match image version ${PGSTAC_VERSION}." >&2
printf '%s\n' 'Run: docker compose run --rm --build pgstac-migrate' >&2
exit 1
