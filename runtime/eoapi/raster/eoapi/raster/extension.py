"""mosaicViewerExtension for /map endpoint"""
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlencode

from fastapi import Depends, Query
from jinja2 import ChoiceLoader, PackageLoader
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from titiler.core.factory import FactoryExtension
from titiler.pgstac.factory import BaseTilerFactory

templates = Jinja2Templates(  # type: ignore
    directory="",
    loader=ChoiceLoader(
        [
            PackageLoader(__package__, "templates"),
        ]
    ),
)


@dataclass
class mosaicViewerExtension(FactoryExtension):
    """Add /viewer endpoint to the TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/{searchid}/viewer", response_class=HTMLResponse)
        @factory.router.get(
            "/{searchid}/{TileMatrixSetId}/viewer", response_class=HTMLResponse
        )
        def map_viewer(
            request: Request,
            searchid=Depends(factory.path_dependency),
            TileMatrixSetId: Literal["WebMercatorQuad"] = Query(
                "WebMercatorQuad",
                description="TileMatrixSet Name (default: 'WebMercatorQuad')",
            ),  # noqa
        ):
            """Return a simple map viewer."""
            # tilejson url for adding tile layer to slippy map
            tilejson_url = factory.url_for(
                request, "tilejson", searchid=searchid, TileMatrixSetId=TileMatrixSetId
            )

            # assets_url with placeholders for bounding box coordinates
            # TODO: can we recover the bounding box here instead of requesting it in javascript?
            assets_url = factory.url_for(
                request,
                "assets_for_tile",
                searchid=searchid,
                TileMatrixSetId=TileMatrixSetId,
                # parameters to be populated in mosaic-viewer.html
                x="${tileCoordinates.x}",
                y="${tileCoordinates.y}",
                z="${tileCoordinates.z}",
            )

            info_url = factory.url_for(
                request,
                "info_search",
                searchid=searchid,
            )

            if request.query_params._list:
                tilejson_url += f"?{urlencode(request.query_params._list)}"

            tms = factory.supported_tms.get(TileMatrixSetId)
            return templates.TemplateResponse(
                name="mosaic-viewer.html",
                context={
                    "request": request,
                    "tilejson_url": tilejson_url,
                    "assets_url": assets_url,
                    "info_url": info_url,
                    "tms": tms,
                    "resolutions": [tms._resolution(matrix) for matrix in tms],
                },
                media_type="text/html",
            )
