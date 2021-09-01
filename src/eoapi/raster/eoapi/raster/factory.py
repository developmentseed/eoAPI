"""Custom MosaicTiler Factory for PgSTAC Mosaic Backend."""

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type
from urllib.parse import urlencode

import rasterio
from cogeo_mosaic.backends import BaseBackend
from morecantile import TileMatrixSet
from pydantic import BaseModel, root_validator, validator
from rio_tiler.constants import MAX_THREADS
from rio_tiler.models import Info
from stac_pydantic.api.extensions.query import Operator
from stac_pydantic.api.extensions.sort import SortExtension

from eoapi.raster.mosaic import PGSTACBackend
from eoapi.raster.reader import MyCustomSTACReader
from fastapi import Depends, Path, Query
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates
from titiler.core.dependencies import AssetsBidxExprParams, DefaultDependency
from titiler.core.factory import (
    BaseTilerFactory,
    MultiBaseTilerFactory,
    img_endpoint_params,
)
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType, OptionalHeader
from titiler.core.utils import Timer
from titiler.mosaic.resources.enums import PixelSelectionMethod

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))


class MosaicCreate(BaseModel):
    """Create Mosaic model.

    Simplified version of the `search` model
    """

    datetime: Optional[str]
    collections: Optional[List[str]] = None
    query: Optional[Dict[str, Dict[Operator, Any]]]
    sortby: Optional[List[SortExtension]]

    @root_validator(pre=True)
    def validate_query_fields(cls, values: Dict) -> Dict:
        """Pgstac does not require the base validator for query fields."""
        return values

    @validator("datetime")
    def validate_datetime(cls, v: str) -> str:
        """Pgstac does not require the base validator for datetime."""
        return v


def MosaicPathParams(searchid: str = Path(..., description="search id")) -> str:
    """Mosaic ID"""
    return searchid


@dataclass
class MosaicTilerFactory(BaseTilerFactory):
    """Custom MosaicTiler for PgSTAC Mosaic Backend."""

    reader: BaseBackend = PGSTACBackend
    path_dependency: Callable[..., str] = MosaicPathParams
    layer_dependency: Type[DefaultDependency] = AssetsBidxExprParams

    backend_options: Dict = field(default_factory=dict)

    def register_routes(self) -> None:
        """This Method register routes to the router."""
        self._search_routes()
        self._tiles_routes()
        self._assets_routes()

    def _search_routes(self) -> None:
        """Register search routes."""

        @self.router.post(
            "/register",
            responses={200: {"description": "Register a Search."}},
            response_model=TileJSON,
            response_model_exclude_none=True,
        )
        def register_search(
            request: Request,
            body: MosaicCreate,
            tms: TileMatrixSet = Depends(self.tms_dependency),
            tile_format: Optional[ImageType] = Query(
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
            bounds: Optional[str] = Query(
                None, description="Overwrite default bounding box."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
            kwargs: Dict = Depends(self.additional_dependency),  # noqa
        ):
            pool = request.app.state.writepool
            conn = pool.getconn()

            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT * FROM search_query(%s);",
                            (body.json(exclude_none=True),),
                        )
                        r = cursor.fetchone()
                        fields = [
                            "id",
                            "search",
                            "where_tag",
                            "orderby_tag",
                            "lastused",
                            "usecount",
                            "statslastupdated",
                            "estimated_count",
                            "total_count",
                        ]
                        mosaic_info = dict(zip(fields, r))
            finally:
                pool.putconn(conn)

            searchid = mosaic_info["id"]
            route_params = {
                "searchid": searchid,
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
            }
            if tile_format:
                route_params["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "searchid",
                "bounds",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            bbox = (
                tuple(map(float, bounds.split(","))) if bounds else (-180, -90, 180, 90)
            )
            with self.reader(
                searchid,
                pool=request.app.state.readpool,
                bounds=bbox,
                **self.backend_options,
            ) as src_dst:
                center = list(src_dst.center)
                if minzoom is not None:
                    center[-1] = minzoom
                return {
                    "bounds": src_dst.bounds,
                    "center": tuple(center),
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "name": searchid,
                    "tiles": [tiles_url],
                }

    def _tiles_routes(self) -> None:
        """Register tiles routes."""

        @self.router.get("/tiles/{searchid}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            "/tiles/{searchid}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            "/tiles/{searchid}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            "/tiles/{searchid}/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params
        )
        @self.router.get(
            "/tiles/{searchid}/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params
        )
        @self.router.get(
            "/tiles/{searchid}/{TileMatrixSetId}/{z}/{x}/{y}.{format}",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{searchid}/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x",
            **img_endpoint_params,
        )
        @self.router.get(
            "/tiles/{searchid}/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        # TODO add cache
        def tile(
            request: Request,
            searchid=Depends(self.path_dependency),
            z: int = Path(..., ge=0, le=30, description="Tile's zoom level"),
            x: int = Path(..., description="Tile's column"),
            y: int = Path(..., description="Tile's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            colormap=Depends(self.colormap_dependency),
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
            kwargs: Dict = Depends(self.additional_dependency),
        ):
            """Create map tile."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        searchid,
                        pool=request.app.state.readpool,
                        **self.backend_options,
                    ) as src_dst:
                        mosaic_read = t.from_start
                        timings.append(("mosaicread", round(mosaic_read * 1000, 2)))

                        data, _ = src_dst.tile(
                            x,
                            y,
                            z,
                            pixel_selection=pixel_selection.method(),
                            threads=threads,
                            tilesize=tilesize,
                            **layer_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            if OptionalHeader.x_assets in self.optional_headers:
                ids = [x["id"] for x in data.assets]
                headers["X-Assets"] = ",".join(ids)

            return Response(content, media_type=format.mediatype, headers=headers)

        @self.router.get(
            "/{searchid}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{searchid}/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        def tilejson(
            request: Request,
            searchid=Depends(self.path_dependency),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            tile_format: Optional[ImageType] = Query(
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
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),  # noqa
            kwargs: Dict = Depends(self.additional_dependency),  # noqa
        ):
            """Return TileJSON document for a COG."""
            route_params = {
                "searchid": searchid,
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
            }
            if tile_format:
                route_params["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "searchid",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            with self.reader(
                searchid, pool=request.app.state.readpool, **self.backend_options,
            ) as src_dst:
                center = list(src_dst.center)
                if minzoom:
                    center[-1] = minzoom
                return {
                    "bounds": src_dst.bounds,
                    "center": tuple(center),
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "name": searchid,
                    "tiles": [tiles_url],
                }

    def _assets_routes(self):
        """Register assets routes."""

        @self.router.get(
            "/{searchid}/{z}/{x}/{y}/assets",
            responses={200: {"description": "Return list of assets"}},
        )
        @self.router.get(
            "/{searchid}/{TileMatrixSetId}/{z}/{x}/{y}/assets",
            responses={200: {"description": "Return list of assets"}},
        )
        def assets_for_tile(
            request: Request,
            searchid=Depends(self.path_dependency),
            z: int = Path(..., ge=0, le=30, description="Tiles's zoom level"),
            x: int = Path(..., description="Tiles's column"),
            y: int = Path(..., description="Tiles's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
        ):
            """Return a list of assets which overlap a given tile"""
            with self.reader(
                searchid,
                pool=request.app.state.readpool,
                tms=tms,
                **self.backend_options,
            ) as src_dst:
                return src_dst.assets_for_tile(x, y, z)


@dataclass
class STACTilerFactory(MultiBaseTilerFactory):
    """Custom STAC endpoints factory."""

    reader: BaseBackend = MyCustomSTACReader

    def register_routes(self) -> None:
        """This Method register routes to the router."""
        super().register_routes()
        self._viewer_routes()

    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Dict[str, Info],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={
                200: {
                    "description": "Return dataset's basic info or the list of available assets."
                }
            },
        )
        def info(src_path=Depends(self.path_dependency)):
            """Return dataset's basic info or the list of available assets."""
            with self.reader(src_path, **self.reader_options) as src_dst:
                return src_dst.info(assets=src_dst.assets)

    def _viewer_routes(self):
        """Register viewer route."""

        @self.router.get("/viewer", response_class=HTMLResponse)
        def stac_demo(
            request: Request, url: str = Depends(self.path_dependency),
        ):
            """STAC Viewer."""
            return templates.TemplateResponse(
                name="stac-viewer.html",
                context={
                    "request": request,
                    "endpoint": request.url.path.replace("/viewer", ""),
                    "stac_url": url,
                },
                media_type="text/html",
            )
