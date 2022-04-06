"""TiTiler extension."""

from typing import Optional
from urllib.parse import urlencode

import attr

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from fastapi.responses import RedirectResponse
from stac_fastapi.types.extension import ApiExtension
from starlette.requests import Request

router = APIRouter()

MAX_B64_ITEM_SIZE = 2000


@attr.s
class TiTilerExtension(ApiExtension):
    """TiTiler extension."""

    def register(self, app: FastAPI, titiler_endpoint: str) -> None:
        """Register the extension with a FastAPI application.
        Args:
            app: target FastAPI application.
        Returns:
            None

        """
        router = APIRouter()

        @router.get(
            "/collections/{collectionId}/items/{itemId}/tilejson.json",
        )
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
            assets: Optional[str] = Query(  # noqa
                None,
                description="comma (',') delimited asset names.",
            ),
            expression: Optional[str] = Query(  # noqa
                None,
                description="rio-tiler's band math expression between assets (e.g asset1/asset2)",
            ),
            bidx: Optional[str] = Query(  # noqa
                None,
                description="comma (',') delimited band indexes to apply to each asset",
            ),
            asset_expression: Optional[str] = Query(  # noqa
                None,
                description="rio-tiler's band math expression (e.g b1/b2) to apply to each asset",
            ),
        ):
            """Get items and redirect to stac tiler."""
            if not assets and not expression:
                raise HTTPException(
                    status_code=500,
                    detail="assets must be defined either via expression or assets options.",
                )

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
            qs.append(("item", itemId))
            qs.append(("collection", collectionId))

            return RedirectResponse(
                f"{titiler_endpoint}/stac/tilejson.json?{urlencode(qs)}"
            )

        @router.get(
            "/collections/{collectionId}/items/{itemId}/viewer",
            responses={
                200: {
                    "description": "Redirect to TiTiler STAC viewer.",
                    "content": {"text/html": {}},
                }
            },
        )
        async def stac_viewer(
            request: Request,
            collectionId: str = Path(..., description="Collection ID"),
            itemId: str = Path(..., description="Item ID"),
        ):
            """Get items and redirect to stac tiler."""
            qs = [(key, value) for (key, value) in request.query_params._list]
            qs.append(("item", itemId))
            qs.append(("collection", collectionId))

            return RedirectResponse(f"{titiler_endpoint}/stac/viewer?{urlencode(qs)}")

        app.include_router(router, tags=["TiTiler Extension"])
