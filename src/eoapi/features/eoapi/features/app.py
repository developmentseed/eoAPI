"""eoAPI.features FastAPI application."""

import json
import re
from typing import Any, Dict, Optional, Union

from buildpg import render
from geojson_pydantic.geometries import Polygon
from geojson_pydantic.types import BBox

from eoapi.features import model
from eoapi.features.config import ApiSettings
from eoapi.features.db import close_db_connection, connect_to_db
from eoapi.features.errors import (
    DEFAULT_STATUS_CODES,
    NotFoundError,
    add_exception_handlers,
)
from eoapi.features.response import GeoJSONResponse
from eoapi.features.version import __version__
from fastapi import Depends, FastAPI, Path, Query
from starlette.datastructures import URL, QueryParams
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette_cramjam.middleware import CompressionMiddleware

settings = ApiSettings()

app = FastAPI(title=settings.name, version=__version__, openapi_url="/api")

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(CompressionMiddleware)
add_exception_handlers(app, DEFAULT_STATUS_CODES)


def make_url(
    name: str,
    base_url: Union[str, URL],
    path_params: Optional[Dict] = None,
    query_params: Optional[str] = None,
) -> str:
    """find Url for endpoint."""
    path_params = path_params or {}

    url = app.url_path_for(name, **path_params).make_absolute_url(base_url=base_url)
    if query_params:
        url += f"?{query_params}"
    return url


@app.get(
    "/",
    response_model=model.Landing,
    response_model_exclude_none=True,
)
async def landing(request: Request):
    """Get conformance."""
    return model.Landing(
        title="eoAPI Features",
        links=[
            model.Link(
                title="Landing Page",
                href=make_url("landing", request.base_url),
                type=model.MediaType.json,
            ),
            model.Link(
                title="Conformance",
                href=make_url("conformance", request.base_url),
                type=model.MediaType.json,
            ),
            model.Link(
                title="List of Collections",
                href=make_url("collections", request.base_url),
                type=model.MediaType.json,
            ),
            model.Link(
                title="Collection metadata",
                href=make_url(
                    "collection", request.base_url, {"collectionId": "{collectionId}"}
                ),
                type=model.MediaType.json,
            ),
            model.Link(
                title="Collection Features",
                href=make_url(
                    "items", request.base_url, {"collectionId": "{collectionId}"}
                ),
                type=model.MediaType.json,
            ),
            model.Link(
                title="Collection Feature",
                href=make_url(
                    "item",
                    request.base_url,
                    {"collectionId": "{collectionId}", "itemId": "{itemId}"},
                ),
                type=model.MediaType.json,
            ),
        ],
    )


@app.get(
    "/conformance",
    response_model=model.Conformance,
    response_model_exclude_none=True,
)
async def conformance(request: Request):
    """Get conformance."""
    return model.Conformance(
        conformsTo=[
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas3",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
            "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/simple-query",
        ]
    )


@app.get(
    "/collections",
    response_model=model.Collections,
    response_model_exclude_none=True,
)
async def collections(request: Request):
    """List of feature collections."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        collections = (
            await conn.fetchval(
                """
            SELECT * FROM all_collections();
            """
            )
            or []
        )

    return model.Collections(
        links=[
            model.Link(
                href=make_url("landing", request.base_url),
                rel="parent",
                type=model.MediaType.json,
            ),
            model.Link(
                href=make_url("collections", request.base_url),
                rel="self",
                type=model.MediaType.json,
            ),
        ],
        collections=[
            model.Collection(
                **{
                    **collection,
                    "links": [
                        model.Link(
                            href=make_url(
                                "collection",
                                request.base_url,
                                {"collectionId": collection["id"]},
                            ),
                            rel="collection",
                            type=model.MediaType.json,
                        ),
                        model.Link(
                            href=make_url(
                                "items",
                                request.base_url,
                                {"collectionId": collection["id"]},
                            ),
                            rel="items",
                            type=model.MediaType.geojson,
                        ),
                    ],
                }
            )
            for collection in collections
        ],
    )


@app.get(
    "/collections/{collectionId}",
    response_model=model.Collection,
    response_model_exclude_none=True,
)
async def collection(
    request: Request,
    collectionId: str = Path(..., description="Collection identifier"),
):
    """Metadata for a feature collection."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        q, p = render(
            """
            SELECT * FROM get_collection(:id::text);
            """,
            id=collectionId,
        )
        collection = await conn.fetchval(q, *p)

    if collection is None:
        raise NotFoundError(f"Collection {collectionId} does not exist.")

    return model.Collection(
        **{
            **collection,
            "links": [
                model.Link(
                    href=make_url(
                        "collection",
                        request.base_url,
                        {"collectionId": collection["id"]},
                    ),
                    rel="self",
                    type=model.MediaType.json,
                ),
                model.Link(
                    href=make_url(
                        "items", request.base_url, {"collectionId": collection["id"]}
                    ),
                    rel="items",
                    type=model.MediaType.geojson,
                ),
            ],
        }
    )


def bbox_query(
    bbox: Optional[str] = Query(
        None,
        description="filter features in response to ones intersecting a bounding box",
    )
) -> Optional[BBox]:
    """BBox dependency."""
    if bbox:
        split_bbox = bbox.split(",")
        if len(split_bbox) not in [4, 6]:
            raise Exception("Invalid BBOX.")
        return tuple(map(float, split_bbox))  # type: ignore

    return bbox  # type: ignore


@app.get(
    "/collections/{collectionId}/items",
    response_model=model.Items,
    response_model_exclude_none=True,
    response_class=GeoJSONResponse,
)
async def items(
    request: Request,
    collectionId: str = Path(..., description="Collection identifier"),
    limit: int = Query(
        10, description="Limits the number of features in the response."
    ),
    offset: Optional[str] = Query(
        None, description="Starts the response at an offset."
    ),
    bbox: Optional[BBox] = Depends(bbox_query),
    properties: Optional[str] = Query(
        None,
        description="Return only specific properties (comma-separated). If PROP-LIST is empty, no properties are returned. If not present, all properties are returned.",
    ),
    sortby: Optional[str] = Query(
        None,
        description="Sort the response items by a property (ascending (default) or descending).",
    ),
):
    """Data set of features from a feature collection."""
    pool = request.app.state.pool

    req: Dict[str, Any] = {
        "fields": {
            "exclude": ["links"],
        },
        "filter": {
            "op": "and",
            "args": [
                {
                    "op": "eq",
                    "args": [{"property": "collection"}, collectionId],
                },
            ],
        },
        "limit": limit,
    }

    if bbox:
        req["filter"]["args"].append(
            {
                "op": "s_intersects",
                "args": [{"property": "geometry"}, Polygon.from_bounds(*bbox).dict()],
            }
        )

    # # <propname>=val - filter features for a property having a value. Multiple property filters are ANDed together.
    qs_key_to_remove = ["limit", "offset", "bbox", "properties", "sortby"]
    propname = [
        {"op": "eq", "args": [{"property": key}, value]}
        for (key, value) in request.query_params.items()
        if key.lower() not in qs_key_to_remove
    ]
    if propname:
        req["filter"]["args"].append(*propname)

    # sortby=[+|-]PROP - sort the response items by a property (ascending (default) or descending).
    if sortby:
        sort_expr = []
        for s in sortby.split(","):
            parts = re.match(
                "^(?P<dir>[+-]?)(?P<prop>.*)$", s
            ).groupdict()  # type:ignore
            sort_expr.append(
                {
                    "field": f"properties.{parts['prop']}",
                    "direction": "desc" if parts["dir"] == "-" else "asc",
                }
            )

        req["sortby"] = sort_expr

    # properties=PROP-LIST- return only specific properties (comma-separated). If PROP-LIST is empty, no properties are returned. If not present, all properties are returned.
    if properties is not None:
        if properties == "":
            req["fields"]["exclude"].append("properties")
        else:
            required_props = ["type", "geometry", "id", "bbox", "assets"]
            req["fields"].update(
                {
                    "include": required_props
                    + [f"properties.{p}" for p in properties.split(",")]
                }
            )

    if offset:
        req["token"] = offset

    async with pool.acquire() as conn:
        q, p = render(
            """
            SELECT * FROM search(:req::text::jsonb);
            """,
            req=json.dumps(req),
        )
        items = await conn.fetchval(q, *p)

    links = [
        model.Link(
            href=make_url("collection", request.base_url, request.path_params),
            rel="collection",
            type=model.MediaType.json,
        ),
        model.Link(
            href=make_url(
                "items",
                request.base_url,
                request.path_params,
                str(request.query_params),
            ),
            rel="self",
            type=model.MediaType.json,
        ),
    ]
    next_token = items.get("next")
    if next_token:
        new_qr = QueryParams({**request.query_params, "offset": next_token})
        links.append(
            model.Link(
                href=make_url(
                    "items", request.base_url, request.path_params, str(new_qr)
                ),
                rel="next",
                type=model.MediaType.json,
            ),
        )

    prev_token = items.get("prev")
    if prev_token:
        new_qr = QueryParams({**request.query_params, "offset": prev_token})
        links.append(
            model.Link(
                href=make_url(
                    "items", request.base_url, request.path_params, str(new_qr)
                ),
                rel="prev",
                type=model.MediaType.json,
            ),
        )

    return model.Items(
        numberReturned=items["context"]["returned"],
        links=links,
        features=[
            model.Item(
                **{
                    **item,
                    "links": [
                        model.Link(
                            href=make_url(
                                "collection",
                                request.base_url,
                                {"collectionId": collectionId},
                            ),
                            rel="collection",
                            type=model.MediaType.json,
                        ),
                        model.Link(
                            href=make_url(
                                "item",
                                request.base_url,
                                {"collectionId": collectionId, "itemId": item["id"]},
                            ),
                            rel="item",
                            type=model.MediaType.json,
                        ),
                    ],
                }
            )
            for item in items["features"]
        ],
    )


@app.get(
    "/collections/{collectionId}/items/{itemId}",
    response_model=model.Item,
    response_model_exclude_none=True,
    response_class=GeoJSONResponse,
)
async def item(
    request: Request,
    collectionId: str = Path(..., description="Collection identifier"),
    itemId: str = Path(..., description="Item identifier"),
):
    """Data for a specific feature."""
    pool = request.app.state.pool

    req = json.dumps(
        {
            "fields": {
                "exclude": ["links"],
            },
            "filter": {
                "op": "and",
                "args": [
                    {
                        "op": "eq",
                        "args": [{"property": "collection"}, collectionId],
                    },
                    {"op": "eq", "args": [{"property": "id"}, itemId]},
                ],
            },
        }
    )

    async with pool.acquire() as conn:
        q, p = render(
            """
            SELECT * FROM search(:req::text::jsonb);
            """,
            req=req,
        )
        items = await conn.fetchval(q, *p)

    if not items["features"]:
        raise NotFoundError(
            f"Item {itemId} in Collection {collectionId} does not exist."
        )

    return model.Item(
        **items["features"][0],
        links=[
            model.Link(
                href=make_url(
                    "collection", request.base_url, {"collectionId": collectionId}
                ),
                rel="collection",
                type=model.MediaType.json,
            ),
            model.Link(
                href=make_url("collection", request.base_url, request.path_params),
                rel="self",
                type=model.MediaType.json,
            ),
        ],
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
