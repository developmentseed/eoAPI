"""eoapi.raster.dependencies."""

import json
from base64 import b64decode
from typing import Dict, Union
from urllib.parse import urlparse

from cachetools import LRUCache, cached
from cachetools.keys import hashkey

from fastapi import Query
from starlette.requests import Request


@cached(
    LRUCache(maxsize=512),
    key=lambda pool, collection_id, item_id: hashkey(collection_id, item_id),
)
def get_item(pool, collection_id, item_id):
    """Get STAC Item from PGStac."""
    req = dict(
        filter={
            "op": "and",
            "args": [
                {
                    "op": "eq",
                    "args": [{"property": "collection"}, collection_id],
                },
                {"op": "eq", "args": [{"property": "id"}, item_id]},
            ],
        },
    )
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM search(%s);",
                (json.dumps(req),),
            )
            resp = cursor.fetchone()[0]
            features = resp.get("features", [])
            if not len(features):
                raise Exception(
                    "No item '{item_id}' found in '{collection_id}' collection"
                )

            return features[0]


def DatasetPathParams(
    request: Request, url: str = Query(..., description="Dataset URL")
) -> Union[str, Dict]:
    """Custom Dataset Param for the custom STAC Reader"""
    parsed = urlparse(url)

    # stac://{base 64 encoded item}
    if parsed.scheme == "stac":
        return json.loads(b64decode(url.replace("stac://", "")))

    # pgstac://{collectionId}/{itemId}
    elif parsed.scheme == "pgstac":
        collection_id = parsed.netloc
        item_id = parsed.path.strip("/")
        return get_item(
            request.app.state.dbpool,
            collection_id,
            item_id,
        )

    # Default to passing the URL
    else:
        return url
