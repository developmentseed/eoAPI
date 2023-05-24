#!/bin/bash
export PGUSER=username
export POSTGRES_USER=username
export PGPASSWORD=password
export POSTGRES_PASSWORD=password
export GITSHA=$(git rev-parse HEAD | cut -c1-10)

MANIFEST=./tmp/eoapi-manfests.yaml

echo "" > $MANIFEST
MANIFESTS=$(find ./templates/* -name "*.yaml")
while read MFILE; do
  path_without_dot_prefix=$(echo "$MFILE" | sed 's/^\.\///g')
  printf "[ RENDERING ]: %s\n" "$path_without_dot_prefix"
  helm template . \
    -s $path_without_dot_prefix \
    --set gitSha=$GITSHA \
    --set db.settings.secrets.PGUSER=$PGUSER \
    --set db.settings.secrets.POSTGRES_USER=$POSTGRES_USER \
    --set db.settings.secrets.PGPASSWORD=$PGPASSWORD \
    --set db.settings.secrets.POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -f values.yaml >> $MANIFEST
done < <(echo "$MANIFESTS")

