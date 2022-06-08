"""eoAPI.vector dependencies."""

from enum import Enum

import morecantile
from timvt.layer import Layer

from fastapi import HTTPException, Path, Query
from starlette.requests import Request


def LayerParams(
    request: Request,
    layer: str = Path(..., description="Layer Name"),
) -> Layer:
    """Return Layer Object."""
    func = request.app.state.function_catalog.get(layer)
    if func:
        return func

    raise HTTPException(status_code=404, detail=f"Layer '{layer}' not found.")


TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [("WebMercatorQuad", "WebMercatorQuad")]
)


def TileMatrixSetParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
) -> morecantile.TileMatrixSet:
    """TileMatrixSet parameters."""
    return morecantile.tms.get(TileMatrixSetId.name)
