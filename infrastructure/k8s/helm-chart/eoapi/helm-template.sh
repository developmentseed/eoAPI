#!/bin/bash
MANIFEST=/tmp/eoapi-manfests.yaml
echo "" > $MANIFEST
helm template . -s templates/vector/deployment.yaml --set gitSha=$(git rev-parse HEAD | cut -c1-10) -f values.yaml >> $MANIFEST
helm template . -s templates/vector/configmap.yaml --set gitSha=$(git rev-parse HEAD | cut -c1-10) -f values.yaml >> $MANIFEST
helm template . -s templates/vector/service.yaml --set gitSha=$(git rev-parse HEAD | cut -c1-10) -f values.yaml >> $MANIFEST
helm template . -s templates/db/postgres.yaml --set gitSha=$(git rev-parse HEAD | cut -c1-10) -f values.yaml >> $MANIFEST
