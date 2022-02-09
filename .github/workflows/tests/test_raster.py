"""test EOapi."""

import json
from base64 import b64encode

import httpx

raster_endpoint = "http://0.0.0.0:8082"


def test_raster_api():
    """test api."""
    # health
    resp = httpx.get(
        f"{raster_endpoint}/healthz", headers={"Accept-Encoding": "br, gzip"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.headers["content-encoding"] == "br"


def test_mosaic_api():
    """test mosaic."""
    query = {"collections": ["noaa-emergency-response"], "filter-lang": "cql-json"}
    resp = httpx.post(f"{raster_endpoint}/mosaic/register", json=query)
    assert resp.headers["content-type"] == "application/json"
    assert resp.status_code == 200
    assert resp.json()["searchid"]
    assert resp.json()["metadata"]

    searchid = resp.json()["searchid"]

    resp = httpx.get(f"{raster_endpoint}/mosaic/{searchid}/-85.6358,36.1624/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert list(resp.json()[0]) == ["id", "bbox", "assets"]
    assert resp.json()[0]["id"] == "20200307aC0853900w361030"

    resp = httpx.get(f"{raster_endpoint}/mosaic/{searchid}/15/8589/12849/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert list(resp.json()[0]) == ["id", "bbox", "assets"]
    assert resp.json()[0]["id"] == "20200307aC0853900w361030"

    z, x, y = 15, 8589, 12849
    resp = httpx.get(
        f"{raster_endpoint}/mosaic/tiles/{searchid}/{z}/{x}/{y}",
        params={"assets": "cog"},
        headers={"Accept-Encoding": "br, gzip"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert "content-encoding" not in resp.headers


def test_stac_api():
    """test stac proxy."""
    item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "20200307aC0853300w361200",
        "properties": {
            "event": "Nashville Tornado",
            "datetime": "2020-03-07T00:00:00Z",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-85.5501, 36.2001],
                    [-85.5501, 36.1749],
                    [-85.5249, 36.1749],
                    [-85.5249, 36.2001],
                    [-85.5501, 36.2001],
                ]
            ],
        },
        "links": [
            {
                "rel": "collection",
                "href": "noaa-emergency-response",
                "type": "application/json",
            }
        ],
        "assets": {
            "cog": {
                "href": "https://noaa-eri-pds.s3.us-east-1.amazonaws.com/2020_Nashville_Tornado/20200307a_RGB/20200307aC0853300w361200n.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            }
        },
        "bbox": [-85.5501, 36.1749, -85.5249, 36.2001],
        "stac_extensions": [],
        "collection": "noaa-emergency-response",
    }
    itemb64 = b64encode(json.dumps(item).encode()).decode()

    # stac://
    resp = httpx.get(
        f"{raster_endpoint}/stac/assets", params={"url": f"stac://{itemb64}"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["cog"]

    resp = httpx.get(
        f"{raster_endpoint}/stac/tilejson.json",
        params={"url": f"stac://{itemb64}", "assets": "cog"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["tilejson"]
    assert "assets=cog" in resp.json()["tiles"][0]
    assert resp.json()["bounds"] == [-85.5501, 36.1749, -85.5249, 36.2001]

    # pgstac://
    resp = httpx.get(
        f"{raster_endpoint}/stac/assets",
        params={"url": "pgstac://noaa-emergency-response/20200307aC0853300w361200"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["cog"]

    resp = httpx.get(
        f"{raster_endpoint}/stac/tilejson.json",
        params={
            "url": "pgstac://noaa-emergency-response/20200307aC0853300w361200",
            "assets": "cog",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["tilejson"]
    assert "assets=cog" in resp.json()["tiles"][0]
    assert resp.json()["bounds"] == [-85.5501, 36.1749, -85.5249, 36.2001]
