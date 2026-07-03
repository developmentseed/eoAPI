#!/bin/sh
set -eu

DEMO_ROOT="${DEMO_ROOT:-/workspace/demo}"
DATABASE_URL="${DATABASE_URL:-postgresql://username:password@database:5432/postgis}"

load_pair() {
    name="$1"
    collection_file="$2"
    items_file="$3"

    if [ ! -f "$collection_file" ]; then
        echo "Skipping $name: missing collection file $collection_file"
        return 0
    fi

    if [ ! -f "$items_file" ]; then
        echo "Skipping $name: missing items file $items_file"
        return 0
    fi

    echo "Loading $name collection from $collection_file"
    pypgstac load collections "$collection_file" --dsn "$DATABASE_URL" --method insert_ignore

    echo "Loading $name items from $items_file"
    pypgstac load items "$items_file" --dsn "$DATABASE_URL" --method insert_ignore
}

load_noaa() {
    load_pair \
        "noaa" \
        "$DEMO_ROOT/noaa/noaa-emergency-response.json" \
        "$DEMO_ROOT/noaa/noaa-eri-nashville2020.json"
}

load_facebook() {
    load_pair \
        "facebook" \
        "$DEMO_ROOT/facebook/facebook_collection.json" \
        "$DEMO_ROOT/facebook/facebook_items.json"
}

load_cmip6() {
    model="${CMIP6_MODEL:-GISS-E2-1-G}"
    variable="${CMIP6_VARIABLE:-tas}"
    prefix="$DEMO_ROOT/cmip6/CMIP6_daily_${model}_${variable}"

    load_pair \
        "cmip6" \
        "${prefix}_collection.json" \
        "${prefix}_stac_items.ndjson"
}

normalize_ndjson() {
    input_file="$1"
    output_file="$2"

    python - "$input_file" "$output_file" <<'PY_NDJSON'
import json
import re
import sys
from pathlib import Path

import orjson

input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
invalid_escape = re.compile(r'\\(?!["\\/bfnrtu])')


def loads_line(line, lineno):
    raw = line.encode("utf-8")
    try:
        return orjson.loads(raw)
    except orjson.JSONDecodeError:
        pass

    try:
        return json.loads(line)
    except json.JSONDecodeError:
        repaired = invalid_escape.sub(r'\\\\', line)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {input_path} at line {lineno}: {exc}") from exc


items = []
with input_path.open("r", encoding="utf-8") as src:
    for lineno, line in enumerate(src, 1):
        if not line.strip():
            continue
        item = loads_line(line, lineno)
        if "collection" not in item:
            raise SystemExit(f"Normalized item from {input_path} at line {lineno} has no collection field")
        items.append(item)

output_path.write_bytes(orjson.dumps(items))
parsed = orjson.loads(output_path.read_bytes())
if not isinstance(parsed, list):
    raise SystemExit(f"Normalized OAM output should be a JSON array, got {type(parsed).__name__}")
if parsed and "collection" not in parsed[0]:
    raise SystemExit("First normalized OAM item has no collection field")
PY_NDJSON
}
load_oam() {
    collection_file="$DEMO_ROOT/oam/oam_collection.json"
    items_file="$DEMO_ROOT/oam/oam_items.njson"
    normalized_items_file="/tmp/oam_items.normalized.json"

    if [ ! -f "$collection_file" ]; then
        echo "Skipping oam: missing collection file $collection_file"
        return 0
    fi

    if [ ! -f "$items_file" ]; then
        echo "Skipping oam: missing items file $items_file"
        return 0
    fi

    normalize_ndjson "$items_file" "$normalized_items_file"
    load_pair "oam" "$collection_file" "$normalized_items_file"
}

if [ "$#" -eq 0 ]; then
    set -- all
fi

for demo_name in "$@"; do
    case "$demo_name" in
        all)
            load_noaa
            load_facebook
            load_cmip6
            load_oam
            ;;
        noaa)
            load_noaa
            ;;
        facebook)
            load_facebook
            ;;
        cmip6)
            load_cmip6
            ;;
        oam)
            load_oam
            ;;
        *)
            echo "Unknown demo '$demo_name'. Expected one of: all, noaa, facebook, cmip6, oam" >&2
            exit 2
            ;;
    esac
done
