"""test EOapi."""

import httpx

stac_endpoint = "http://0.0.0.0:8081"


def test_stac_api():
    """test stac."""
    # Ping
    assert httpx.get(f"{stac_endpoint}/_mgmt/ping").status_code == 200

    # viewer
    assert httpx.get(f"{stac_endpoint}/index.html").status_code == 200

    # Collections
    resp = httpx.get(f"{stac_endpoint}/collections")
    assert resp.status_code == 200
    collections = resp.json()["collections"]
    assert len(collections) > 0
    ids = [c["id"] for c in collections]
    assert "noaa-emergency-response" in ids

    # items
    resp = httpx.get(f"{stac_endpoint}/collections/noaa-emergency-response/items")
    assert resp.status_code == 200
    items = resp.json()["features"]
    assert len(items) == 10

    # item
    resp = httpx.get(
        f"{stac_endpoint}/collections/noaa-emergency-response/items/20200307aC0853300w361200"
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == "20200307aC0853300w361200"


def test_stac_to_raster():
    """test link to raster api."""
    # tilejson
    resp = httpx.get(
        f"{stac_endpoint}/collections/noaa-emergency-response/items/20200307aC0853300w361200/tilejson.json",
        params={"assets": "cog"},
    )
    assert resp.status_code == 307

    # viewer
    resp = httpx.get(
        f"{stac_endpoint}/collections/noaa-emergency-response/items/20200307aC0853300w361200/viewer",
        params={"assets": "cog"},
    )
    assert resp.status_code == 307
