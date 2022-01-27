"""test EOapi."""

import httpx

features_endpoint = "http://0.0.0.0:8085"


def test_features_api():
    """test features."""
    # landing
    resp = httpx.get(f"{features_endpoint}/")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["links"]

    # conformance
    resp = httpx.get(f"{features_endpoint}/conformance")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["conformsTo"]

    # collections
    resp = httpx.get(f"{features_endpoint}/collections")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    assert list(resp.json()) == ["collections", "links"]
    collections = resp.json()["collections"]
    assert len(collections) > 0
    ids = [c["id"] for c in collections]
    assert "noaa-emergency-response" in ids

    # collection
    resp = httpx.get(f"{features_endpoint}/collections/noaa-emergency-response")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["links"]
    assert resp.json()["itemType"] == "feature"

    # items
    resp = httpx.get(f"{features_endpoint}/collections/noaa-emergency-response/items")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"
    items = resp.json()["features"]
    assert len(items) == 10

    # limit
    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"limit": 1},
    )
    assert resp.status_code == 200
    items = resp.json()["features"]
    assert len(items) == 1

    # intersects
    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"bbox": "-180,0,0,90"},
    )
    assert resp.status_code == 200
    items = resp.json()["features"]
    assert len(items) == 10

    # properties
    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"properties": ""},
    )
    assert resp.status_code == 200
    item = resp.json()["features"][0]
    assert "properties" not in item

    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"properties": "event"},
    )
    assert resp.status_code == 200
    item = resp.json()["features"][0]
    assert "datetime" not in item["properties"]

    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"properties": "event,datetime"},
    )
    assert resp.status_code == 200
    item = resp.json()["features"][0]
    assert "datetime" in item["properties"]
    assert "event" in item["properties"]

    # sortby
    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"sortby": "datetime"},
    )
    assert resp.status_code == 200
    item = resp.json()["features"][0]
    assert item["properties"]["datetime"] == "2020-03-07T00:00:00Z"

    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"sortby": "+datetime"},
    )
    assert resp.status_code == 200
    item = resp.json()["features"][0]
    assert item["properties"]["datetime"] == "2020-03-07T00:00:00Z"

    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"sortby": "-datetime"},
    )
    assert resp.status_code == 200
    item = resp.json()["features"][0]
    assert item["properties"]["datetime"] == "2020-03-11T00:00:01Z"

    # propname
    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items",
        params={"datetime": "2020-03-07T00:00:00Z", "limit": 200},
    )
    assert resp.status_code == 200
    items = resp.json()["features"]
    assert len(items) == 38

    # item
    resp = httpx.get(
        f"{features_endpoint}/collections/noaa-emergency-response/items/20200307aC0853300w361200"
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == "20200307aC0853300w361200"
