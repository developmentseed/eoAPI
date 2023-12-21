"""TiTiler extension."""

from typing import Optional
from urllib.parse import urlencode

import attr
import pydantic
from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from fastapi.responses import ORJSONResponse, RedirectResponse
from stac_fastapi.extensions.core import (
    ContextExtension,
    FieldsExtension,
    FilterExtension,
    QueryExtension,
    SortExtension,
    TokenPaginationExtension,
    TransactionExtension,
)
from stac_fastapi.extensions.third_party import BulkTransactionExtension
from stac_fastapi.pgstac.extensions.filter import FiltersClient
from stac_fastapi.pgstac.transactions import BulkTransactionsClient, TransactionsClient
from stac_fastapi.types.extension import ApiExtension
from starlette.requests import Request

router = APIRouter()


class TransactionSettings(pydantic.BaseSettings):
    """Simple API settings from stac-fastapi-pgstac Transaction Client.

    ref: https://github.com/stac-utils/stac-fastapi/blob/09dac221d86fe70035aa6cddbc9a3f0de304aff5/stac_fastapi/types/stac_fastapi/types/config.py#L7-L37
    """

    enable_response_models: bool = False

    class Config:
        """Model config (https://pydantic-docs.helpmanual.io/usage/model_config/)."""

        extra = "allow"
        env_file = ".env"


extensions_map = {
    "query": QueryExtension(),
    "sort": SortExtension(),
    "fields": FieldsExtension(),
    "pagination": TokenPaginationExtension(),
    "context": ContextExtension(),
    "filter": FilterExtension(client=FiltersClient()),
    "transaction": TransactionExtension(
        client=TransactionsClient(),
        settings=TransactionSettings(),
        response_class=ORJSONResponse,
    ),
    "bulk_transactions": BulkTransactionExtension(client=BulkTransactionsClient()),
}


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
            return RedirectResponse(
                f"{titiler_endpoint}/collections/{collectionId}/items/{itemId}/tilejson.json?{urlencode(qs)}"
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
            url = f"{titiler_endpoint}/collections/{collectionId}/items/{itemId}/viewer"
            if qs:
                url += f"?{urlencode(qs)}"

            return RedirectResponse(url)

        app.include_router(router, tags=["TiTiler Extension"])
