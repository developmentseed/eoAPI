

1. Create list of items (using rio-stac)

```bash
$ aws s3 ls noaa-eri-pds/2020_Nashville_Tornado/20200307a_RGB/ \
    | awk '{print "s3://noaa-eri-pds/2020_Nashville_Tornado/20200307a_RGB/"$NF}' \
    | grep ".tif" | head -n 3 \
    | while read line; do rio stac $line -c "noaa-emergency-response" -p "event"="Nashville Tornado"  -d "2020-03-07" --without-raster --without-proj --asset-mediatype COG -n cog; done \
    > noaa-eri-nashville2020_2.json
```

2. Create collection.json
```json
{
    "id": "noaa-emergency-response",
    "title": "NOAA Emergency Response Imagery",
    "description": "NOAA Emergency Response Imagery hosted on AWS Public Dataset.",
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
                    "2005-01-01T00:00:00Z",
                    "null"
                ]
            ]
        }
    }
}
```

3. upload collection and items to the RDS postgres instance (using pypgstac)

```bash
$ pypgstac load collections noaa-emergency-response.json --dsn postgresql://{db-user}:{db-password}@{db-host}:{db-port}/{db-name}

$ pypgstac load items noaa-eri-nashville2020.json --dsn postgresql://{db-user}:{db-password}@{db-host}:{db-port}/{db-name}
```

Note:

- You may have to add you address IP to the VPC inbounds rules to be able to connect to the RDS instance.
- You can find the database info in your AWS Lambda configuration (host, user, password, post)
