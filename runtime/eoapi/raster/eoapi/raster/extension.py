"""mosaicViewerExtension for /map endpoint"""
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple
from urllib.parse import urlencode

from fastapi import Depends, Query
from jinja2 import ChoiceLoader, PackageLoader
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from titiler.core.dependencies import AssetsBidxExprParamsOptional, RescalingParams
from titiler.core.factory import FactoryExtension
from titiler.core.resources.enums import ImageType
from titiler.mosaic.resources.enums import PixelSelectionMethod
from titiler.pgstac.dependencies import PgSTACParams
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
    """Add /map endpoint to the TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/{searchid}/map", response_class=HTMLResponse)
        @factory.router.get(
            "/{searchid}/{TileMatrixSetId}/map", response_class=HTMLResponse
        )
        def map_viewer(
            request: Request,
            searchid=Depends(factory.path_dependency),
            TileMatrixSetId: Literal["WebMercatorQuad"] = Query(
                "WebMercatorQuad",
                description="TileMatrixSet Name (default: 'WebMercatorQuad')",
            ),  # noqa
            tile_format: Optional[ImageType] = Query(
                None, description="Output image type. Default is auto."
            ),  # noqa
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),  # noqa
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),  # noqa
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),  # noqa
            layer_params=AssetsBidxExprParamsOptional,  # noqa
            dataset_params=Depends(factory.dataset_dependency),  # noqa
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
            buffer: Optional[float] = Query(
                None,
                gt=0,
                alias="buffer",
                title="Tile buffer.",
                description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
            ),  # noqa
            post_process=Depends(factory.process_dependency),  # noqa
            rescale: Optional[List[Tuple[float, ...]]] = Depends(
                RescalingParams
            ),  # noqa
            color_formula: Optional[str] = Query(
                None,
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),  # noqa
            colormap=Depends(factory.colormap_dependency),  # noqa
            render_params=Depends(factory.render_dependency),  # noqa
            pgstac_params: PgSTACParams = Depends(),  # noqa
            backend_params=Depends(factory.backend_dependency),  # noqa
            reader_params=Depends(factory.reader_dependency),  # noqa
            env=Depends(factory.environment_dependency),  # noqa
        ):
            """Return a simple map viewer."""
            tilejson_url = factory.url_for(
                request, "tilejson", searchid=searchid, TileMatrixSetId=TileMatrixSetId
            )

            # TODO: use assets_for_bbox to avoid needing the zoom level?
            assets_url = factory.url_for(
                request,
                "assets_for_tile",
                searchid=searchid,
                TileMatrixSetId=TileMatrixSetId,
                x="{x}",
                y="{y}",
                z="{z}",
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
                name="mosaic-browser.html",
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
