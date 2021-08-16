"""TiTiler extension."""

import json
from base64 import b64encode
from typing import Optional
from urllib.parse import urlencode

import attr
from buildpg import render

from fastapi import APIRouter, FastAPI, Path, Query
from fastapi.responses import RedirectResponse
from stac_fastapi.pgstac.types.search import PgstacSearch
from stac_fastapi.types.errors import NotFoundError
from stac_fastapi.types.extension import ApiExtension
from starlette.requests import Request

router = APIRouter()


@attr.s
class TilesExtension(ApiExtension):
    """TiTiler extension."""

    def register(self, app: FastAPI, titiler_endpoint: str) -> None:
        """Register the extension with a FastAPI application.
        Args:
            app: target FastAPI application.
        Returns:
            None

        """
        router = APIRouter()

        @router.get("/collections/{collectionId}/items/{itemId}/tilejson.json",)
        async def tilejson(
            request: Request,
            collectionId: str = Path(..., description="Collection ID"),
            itemId: str = Path(..., description="Item ID"),
            tile_format: Optional[str] = Query(
                None, description="Output image type. Default is auto."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
        ):
            """Get items and redirect to stac tiler."""
            pool = request.app.state.readpool

            req = PgstacSearch(collections=[collectionId], ids=[itemId], limit=1).json(
                exclude_none=True
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
                raise NotFoundError("No features found")

            item = json.dumps(items["features"][0])
            itemb64 = b64encode(item.encode())

            qs_key_to_remove = [
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            qs.append(("url", f"stac://{itemb64.decode()}"))

            return RedirectResponse(
                titiler_endpoint + f"/stac/tilejson.json?{urlencode(qs)}"
            )

        app.include_router(router)
