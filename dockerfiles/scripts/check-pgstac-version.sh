#!/bin/sh
set -eu

until pg_isready -q -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}"; do
    sleep 1
done

actual_version="$(psql -X -q -t -A -v ON_ERROR_STOP=1 -c 'SELECT pgstac.get_version()' 2>/dev/null || true)"

if [ "${actual_version}" = "${PGSTAC_VERSION}" ]; then
    exit 0
fi

if [ -z "${actual_version}" ]; then
    actual_version="unavailable"
fi

printf '%s\n' "PgSTAC schema version ${actual_version} does not match image version ${PGSTAC_VERSION}." >&2
printf '%s\n' 'Run: docker compose run --rm --build pgstac-migrate' >&2
exit 1
