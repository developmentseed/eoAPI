#!/bin/bash
model="$1"
variable="$2"

collection_json_file="CMIP6_daily_${model}_${variable}_collection.json"
items_json_file="CMIP6_daily_${model}_${variable}_stac_items.ndjson"

if [ -z "$DATABASE_URL" ]; then
    username=postgres
    password=password
    host=localhost
    dbname=postgres
    port=5432
    DATABASE_URL="postgresql://$username:$password@$host:$port/$dbname"
fi

echo $DATABASE_URL
echo "Inserting collection from $collection_json_file"
pypgstac load collections $collection_json_file --dsn $DATABASE_URL --method insert_ignore
echo "Inserting items from $items_json_file"
pypgstac load items $items_json_file --dsn $DATABASE_URL --method insert_ignore
