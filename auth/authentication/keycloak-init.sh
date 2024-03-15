#!/bin/bash

# Keycloak admin credentials
KC_USER=admin
KC_PASSWORD=admin
KC_AUTH_URL=http://localhost:a8080/auth

# New realm details
NEW_REALM=eoapi

# Login
kcadm.sh config credentials --server $KC_AUTH_URL --realm master --user $KC_USER --password $KC_PASSWORD

# Create new realm
kcadm.sh create realms -s realm=$NEW_REALM -s enabled=true -s displayName="My Custom Realm"

# Create stac-api client in the new realm
kcadm.sh create clients -r $NEW_REALM -s clientId=stac-api -s publicClient=true -s directAccessGrantsEnabled=true -s rootUrl=http://localhost:3000 -s 'redirectUris=["*"]'

# Create user Alice in the new realm
kcadm.sh create users -r $NEW_REALM -s username=Alice -s enabled=true
# Set Alice's password
kcadm.sh set-password -r $NEW_REALM --username Alice --new-password Alice

# Create user Bob in the new realm
kcadm.sh create users -r $NEW_REALM -s username=Bob -s enabled=true
# Set Bob's password
kcadm.sh set-password -r $NEW_REALM --username Bob --new-password Bob

echo "Initialization completed for realm $NEW_REALM."
