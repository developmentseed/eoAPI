#!/bin/bash
MANIFEST=./tmp/eoapi-manfests.yaml
echo "" > $MANIFEST
MANIFESTS=$(find ./templates/* -name "manifest.yaml")
while read MFILE; do
  path_without_dot_prefix=$(echo "$MFILE" | sed 's/^\.\///g')
  printf "[ RENDERING ]: %s\n" "$path_without_dot_prefix"
  helm template . -s $path_without_dot_prefix --set gitSha=$(git rev-parse HEAD | cut -c1-10) -f values.yaml >> $MANIFEST
done < <(echo "$MANIFESTS")

