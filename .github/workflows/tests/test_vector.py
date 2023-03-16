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
    assert resp.json()["numberMatched"] == 4  # one public table + 3 functions
    assert resp.json()["numberReturned"] == 4

    collections = resp.json()["collections"]
    ids = [c["id"] for c in collections]
    # 3 Functions
    assert "pg_temp.pgstac_collections_view" in ids
    assert "pg_temp.pgstac_hash" in ids
    assert "pg_temp.pgstac_hash_count" in ids
    # 1 public table
    assert "public.my_data" in ids

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

    # item
    resp = httpx.get(
        f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view/items/noaa-emergency-response"
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == "noaa-emergency-response"

    # OGC Tiles
    resp = httpx.get(f"{vector_endpoint}/collections/public.my_data/tiles/0/0/0")
    assert resp.status_code == 200

    resp = httpx.get(
        f"{vector_endpoint}/collections/pg_temp.pgstac_collections_view/tilejson.json"
    )
    assert resp.status_code == 200

    resp = httpx.get(f"{vector_endpoint}/tileMatrixSets")
    assert resp.status_code == 200

    resp = httpx.get(f"{vector_endpoint}/tileMatrixSets/WebMercatorQuad")
    assert resp.status_code == 200
