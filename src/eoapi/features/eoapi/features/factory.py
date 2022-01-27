"""eoapi.features.factory: router factories."""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from buildpg import render
from geojson_pydantic.geometries import Polygon

from eoapi.features import model
from eoapi.features.errors import NotFoundError
from eoapi.features.model import MediaType
from eoapi.features.response import GeoJSONResponse
from fastapi import APIRouter, Depends, Path, Query
from starlette.datastructures import QueryParams
from starlette.requests import Request


def queryparams_to_kwargs(q: QueryParams, ignore_keys: List = []) -> Dict:
    """Convert query params to dict."""
    keys = list(q.keys())
    values = {}
    for k in keys:
        if k in ignore_keys:
            continue

        v = q.getlist(k)
        values[k] = v if len(v) > 1 else v[0]

    return values


@dataclass
class Endpoints:
    """Endpoints Factory."""

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Router Prefix is needed to find the path for routes when prefixed
    # e.g if you mount the route with `/foo` prefix, set router_prefix to foo
    router_prefix: str = ""

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        self.register_routes()

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        """Return full url (with prefix) for a specific handler."""
        url_path = self.router.url_path_for(name, **path_params)

        base_url = str(request.base_url)
        if self.router_prefix:
            base_url += self.router_prefix.lstrip("/")

        return url_path.make_absolute_url(base_url=base_url)

    def register_routes(self):  # noqa
        """Register Routes."""

        @self.router.get(
            "/",
            response_model=model.Landing,
            response_model_exclude_none=True,
        )
        def landing(request: Request):
            """Get landing."""
            return model.Landing(
                title="eoAPI Features",
                links=[
                    model.Link(
                        title="Landing Page",
                        href=self.url_for(request, "landing"),
                        type=MediaType.json,
                    ),
                    model.Link(
                        title="Conformance",
                        href=self.url_for(request, "conformance"),
                        type=MediaType.json,
                    ),
                    model.Link(
                        title="List of Collections",
                        href=self.url_for(request, "collections"),
                        type=MediaType.json,
                    ),
                    model.Link(
                        title="Collection metadata",
                        href=self.url_for(
                            request, "collection", collectionId="{collectionId}"
                        ),
                        type=MediaType.json,
                    ),
                    model.Link(
                        title="Collection Features",
                        href=self.url_for(
                            request, "items", collectionId="{collectionId}"
                        ),
                        type=MediaType.geojson,
                    ),
                    model.Link(
                        title="Collection Feature",
                        href=self.url_for(
                            request,
                            "item",
                            collectionId="{collectionId}",
                            itemId="{itemId}",
                        ),
                        type=MediaType.geojson,
                    ),
                ],
            )

        @self.router.get(
            "/conformance",
            response_model=model.Conformance,
            response_model_exclude_none=True,
        )
        def conformance(request: Request):
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

        @self.router.get(
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
                        href=self.url_for(request, "landing"),
                        rel="parent",
                        type=MediaType.json,
                    ),
                    model.Link(
                        href=self.url_for(request, "collections"),
                        rel="self",
                        type=MediaType.json,
                    ),
                ],
                collections=[
                    model.Collection(
                        **{
                            **collection,
                            "links": [
                                model.Link(
                                    href=self.url_for(
                                        request,
                                        "collection",
                                        collectionId=collection["id"],
                                    ),
                                    rel="collection",
                                    type=MediaType.json,
                                ),
                                model.Link(
                                    href=self.url_for(
                                        request, "items", collectionId=collection["id"]
                                    ),
                                    rel="items",
                                    type=MediaType.geojson,
                                ),
                            ],
                        }
                    )
                    for collection in collections
                ],
            )

        @self.router.get(
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
                            href=self.url_for(
                                request, "collection", collectionId=collection["id"]
                            ),
                            rel="self",
                            type=MediaType.json,
                        ),
                        model.Link(
                            href=self.url_for(
                                request, "items", collectionId=collection["id"]
                            ),
                            rel="items",
                            type=MediaType.geojson,
                        ),
                    ],
                }
            )

        def bbox_query(
            bbox: Optional[str] = Query(
                None,
                description="Filter features in response to ones intersecting a bounding box",
            )
        ) -> Optional[Polygon]:
            """BBox query dependency."""
            if bbox:
                split_bbox = bbox.split(",")
                if len(split_bbox) not in [4, 6]:
                    raise Exception("Invalid BBOX.")

                bounds = tuple(map(float, split_bbox))
                return Polygon.from_bounds(*bounds)

            return None

        @self.router.get(
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
            intersects: Optional[Polygon] = Depends(bbox_query),
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

            if intersects:
                req["filter"]["args"].append(
                    {
                        "op": "s_intersects",
                        "args": [{"property": "geometry"}, intersects.dict()],
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

            qs = f"?{request.query_params}" if request.query_params else ""

            links = [
                model.Link(
                    href=self.url_for(request, "collection", collectionId=collectionId),
                    rel="collection",
                    type=MediaType.json,
                ),
                model.Link(
                    href=self.url_for(request, "items", collectionId=collectionId) + qs,
                    rel="self",
                    type=MediaType.geojson,
                ),
            ]
            next_token = items.get("next")
            if next_token:
                qs = QueryParams({**request.query_params, "offset": next_token})
                links.append(
                    model.Link(
                        href=self.url_for(request, "items", collectionId=collectionId)
                        + f"?{qs}",
                        rel="next",
                        type=MediaType.geojson,
                    ),
                )

            prev_token = items.get("prev")
            if prev_token:
                qs = QueryParams({**request.query_params, "offset": prev_token})
                links.append(
                    model.Link(
                        href=self.url_for(request, "items", collectionId=collectionId)
                        + f"?{qs}",
                        rel="prev",
                        type=MediaType.geojson,
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
                                    href=self.url_for(
                                        request, "collection", collectionId=collectionId
                                    ),
                                    rel="collection",
                                    type=MediaType.json,
                                ),
                                model.Link(
                                    href=self.url_for(
                                        request,
                                        "item",
                                        collectionId=collectionId,
                                        itemId=item["id"],
                                    ),
                                    rel="item",
                                    type=MediaType.geojson,
                                ),
                            ],
                        }
                    )
                    for item in items["features"]
                ],
            )

        @self.router.get(
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
                        href=self.url_for(
                            request, "collection", collectionId=collectionId
                        ),
                        rel="collection",
                        type=MediaType.json,
                    ),
                    model.Link(
                        href=self.url_for(
                            request, "item", collectionId=collectionId, itemId=itemId
                        ),
                        rel="self",
                        type=MediaType.geojson,
                    ),
                ],
            )
