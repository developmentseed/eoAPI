"""test EOapi."""

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
    assert resp.headers["content-encoding"] == "gzip"

    resp = httpx.get(f"{raster_endpoint}/healthz", headers={"Accept-Encoding": "br"})
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
    assert resp.json()["links"]

    searchid = resp.json()["searchid"]

    resp = httpx.get(f"{raster_endpoint}/mosaic/{searchid}/-85.6358,36.1624/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert list(resp.json()[0]) == ["id", "bbox", "assets", "collection"]
    assert resp.json()[0]["id"] == "20200307aC0853900w361030"

    resp = httpx.get(f"{raster_endpoint}/mosaic/{searchid}/15/8589/12849/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert list(resp.json()[0]) == ["id", "bbox", "assets", "collection"]
    assert resp.json()[0]["id"] == "20200307aC0853900w361030"

    z, x, y = 15, 8589, 12849
    resp = httpx.get(
        f"{raster_endpoint}/mosaic/{searchid}/tiles/{z}/{x}/{y}",
        params={"assets": "cog"},
        headers={"Accept-Encoding": "br, gzip"},
        timeout=10.0,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert "content-encoding" not in resp.headers


def test_mosaic_search():
    """test mosaic."""
    # register some fake mosaic
    searches = [
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection1"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection2"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection3"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection4"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection5"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection6"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection7"]},
            "metadata": {"owner": "vincent"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection8"]},
            "metadata": {"owner": "sean"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection9"]},
            "metadata": {"owner": "sean"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection10"]},
            "metadata": {"owner": "drew"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection11"]},
            "metadata": {"owner": "drew"},
        },
        {
            "filter": {"op": "=", "args": [{"property": "collection"}, "collection12"]},
            "metadata": {"owner": "drew"},
        },
    ]
    for search in searches:
        resp = httpx.post(f"{raster_endpoint}/mosaic/register", json=search)
        assert resp.status_code == 200
        assert resp.json()["searchid"]

    resp = httpx.get(f"{raster_endpoint}/mosaic/list")
    assert resp.headers["content-type"] == "application/json"
    assert resp.status_code == 200
    assert (
        resp.json()["context"]["matched"] > 10
    )  # there should be at least 12 mosaic registered
    assert resp.json()["context"]["returned"] == 10  # default limit is 10

    # Make sure all mosaics returned have
    for mosaic in resp.json()["searches"]:
        assert mosaic["search"]["metadata"]["type"] == "mosaic"

    links = resp.json()["links"]
    assert len(links) == 2
    assert links[0]["rel"] == "self"
    assert links[1]["rel"] == "next"
    assert links[1]["href"] == f"{raster_endpoint}/mosaic/list?limit=10&offset=10"

    resp = httpx.get(f"{raster_endpoint}/mosaic/list", params={"limit": 1, "offset": 1})
    assert resp.status_code == 200
    assert resp.json()["context"]["matched"] > 10
    assert resp.json()["context"]["limit"] == 1
    assert resp.json()["context"]["returned"] == 1

    links = resp.json()["links"]
    assert len(links) == 3
    assert links[0]["rel"] == "self"
    assert links[0]["href"] == f"{raster_endpoint}/mosaic/list?limit=1&offset=1"
    assert links[1]["rel"] == "next"
    assert links[1]["href"] == f"{raster_endpoint}/mosaic/list?limit=1&offset=2"
    assert links[2]["rel"] == "prev"
    assert links[2]["href"] == f"{raster_endpoint}/mosaic/list?limit=1&offset=0"

    # Filter on mosaic metadata
    resp = httpx.get(f"{raster_endpoint}/mosaic/list", params={"owner": "vincent"})
    assert resp.status_code == 200
    assert resp.json()["context"]["matched"] == 7
    assert resp.json()["context"]["limit"] == 10
    assert resp.json()["context"]["returned"] == 7

    # sortBy
    resp = httpx.get(f"{raster_endpoint}/mosaic/list", params={"sortby": "lastused"})
    assert resp.status_code == 200

    resp = httpx.get(f"{raster_endpoint}/mosaic/list", params={"sortby": "usecount"})
    assert resp.status_code == 200

    resp = httpx.get(f"{raster_endpoint}/mosaic/list", params={"sortby": "-owner"})
    assert resp.status_code == 200
    assert (
        "owner" not in resp.json()["searches"][0]["search"]["metadata"]
    )  # some mosaic don't have owners

    resp = httpx.get(f"{raster_endpoint}/mosaic/list", params={"sortby": "owner"})
    assert resp.status_code == 200
    assert "owner" in resp.json()["searches"][0]["search"]["metadata"]


def test_item():
    """test stac endpoints."""
    resp = httpx.get(
        f"{raster_endpoint}/collections/noaa-emergency-response/items/20200307aC0853300w361200/assets",
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["cog"]

    resp = httpx.get(
        f"{raster_endpoint}/collections/noaa-emergency-response/items/20200307aC0853300w361200/tilejson.json",
        params={
            "assets": "cog",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["tilejson"]
    assert "assets=cog" in resp.json()["tiles"][0]
    assert (
        "/collections/noaa-emergency-response/items/20200307aC0853300w361200"
        in resp.json()["tiles"][0]
    )
    assert resp.json()["bounds"] == [-85.5501, 36.1749, -85.5249, 36.2001]
