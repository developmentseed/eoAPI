"""test EOapi.vector"""

import httpx

vector_endpoint = "http://0.0.0.0:8083"


def test_vector_api():
    """test vector."""
    # landing
    resp = httpx.get(f"{vector_endpoint}/")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["links"]

    # conformance
    resp = httpx.get(f"{vector_endpoint}/conformance")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["conformsTo"]

    # collections
    resp = httpx.get(f"{vector_endpoint}/collections")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    assert list(resp.json()) == [
        "links",
        "numberMatched",
        "numberReturned",
        "collections",
    ]
    assert resp.json()["numberMatched"] == 3
    assert resp.json()["numberReturned"] == 3

    collections = resp.json()["collections"]
    ids = [c["id"] for c in collections]
    # 3 Functions
    assert "pg_temp.pgstac_collections_view" in ids
    assert "pg_temp.pgstac_hash" in ids
    assert "pg_temp.pgstac_hash_count" in ids

    # collection
    resp = httpx.get(f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["links"]
    assert resp.json()["itemType"] == "feature"

    # items
    resp = httpx.get(
        f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view/items"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"
    items = resp.json()["features"]
    assert len(items) == 1

    # limit
    resp = httpx.get(
        f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view/items",
        params={"limit": 1},
    )
    assert resp.status_code == 200
    items = resp.json()["features"]
    assert len(items) == 1

    # intersects
    resp = httpx.get(
        f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view/items",
        params={"bbox": "-180,0,0,90"},
    )
    assert resp.status_code == 200
    items = resp.json()["features"]
    assert len(items) == 1

    # # properties
    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"properties": ""},
    # )
    # assert resp.status_code == 200
    # item = resp.json()["features"][0]
    # assert "properties" not in item

    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"properties": "event"},
    # )
    # assert resp.status_code == 200
    # item = resp.json()["features"][0]
    # assert "datetime" not in item["properties"]

    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"properties": "event,datetime"},
    # )
    # assert resp.status_code == 200
    # item = resp.json()["features"][0]
    # assert "datetime" in item["properties"]
    # assert "event" in item["properties"]

    # # sortby
    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"sortby": "datetime"},
    # )
    # assert resp.status_code == 200
    # item = resp.json()["features"][0]
    # assert item["properties"]["datetime"] == "2020-03-07T00:00:00Z"

    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"sortby": "+datetime"},
    # )
    # assert resp.status_code == 200
    # item = resp.json()["features"][0]
    # assert item["properties"]["datetime"] == "2020-03-07T00:00:00Z"

    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"sortby": "-datetime"},
    # )
    # assert resp.status_code == 200
    # item = resp.json()["features"][0]
    # assert item["properties"]["datetime"] == "2020-03-11T00:00:01Z"

    # # propname
    # resp = httpx.get(
    #     f"{vector_endpoint}/collections/noaa-emergency-response/items",
    #     params={"datetime": "2020-03-07T00:00:00Z", "limit": 200},
    # )
    # assert resp.status_code == 200
    # items = resp.json()["features"]
    # assert len(items) == 38

    # item
    resp = httpx.get(
        f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view/items/noaa-emergency-response"
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == "noaa-emergency-response"
