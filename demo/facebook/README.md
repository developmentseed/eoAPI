

1. Create list of items (using rio-stac)

```bash
$ aws s3 ls s3://dataforgood-fb-data/hrsl-cogs/hrsl_general/v1.5/ \
    | grep -E ".tif$" \
    | awk '{print "s3://dataforgood-fb-data/hrsl-cogs/hrsl_general/v1.5/"$NF}' \
    | while read line; do rio stac $line -c "facebook-population-density" -p version=v1.5 -d"2016-01-01" --without-raster --without-proj --asset-mediatype COG -n cog; done \
    > facebook_items.json
```
Note: we need to do some manual editing here. Some files are duplicated (version 1.5.1 and 1.5.2) and we need to keep only one. We also recommand to use simpler item ID than the basename.

2. Create collection.json
```json
{
    "id": "facebook-population-density",
    "title": "High Resolution Population Density Maps",
    "description": "Population data for a selection of countries, allocated to 1 arcsecond blocks and provided in a combination of CSV and Cloud-optimized GeoTIFF files. This refines CIESIN’s Gridded Population of the World using machine learning models on high-resolution worldwide Digital Globe satellite imagery. CIESIN population counts aggregated from worldwide census data are allocated to blocks where imagery appears to contain buildings.",
    "stac_version": "1.0.0",
    "license": "public-domain",
    "links": [],
    "extent": {
        "spatial": {
            "bbox": [
                [
                    -180,
                    -90,
                    180,
                    90
                ]
            ]
        },
        "temporal": {
            "interval": [
                [
                    "2016-01-01T00:00:00Z",
                    "null"
                ]
            ]
        }
    }
}
```

3. upload collection and items to the RDS postgres instance (using pypgstac)

```bash
$ pypgstac load collections facebook_collection.json --dsn postgresql://{db-user}:{db-password}@{db-host}:{db-port}/{db-name} --method insert

$ pypgstac load items facebook_items.json --dsn postgresql://{db-user}:{db-password}@{db-host}:{db-port}/{db-name} --method insert
```

Note:

- You may have to add you address IP to the VPC inbounds rules to be able to connect to the RDS instance.
- You can find the database info in your AWS Lambda configuration (host, user, password, post)
