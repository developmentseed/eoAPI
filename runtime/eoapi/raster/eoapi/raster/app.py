"""TiTiler+PgSTAC FastAPI application."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple
from urllib.parse import urlencode

import pystac
from eoapi.raster import __version__ as eoapi_raster_version
from eoapi.raster.config import ApiSettings
from fastapi import Depends, FastAPI, Query
from jinja2 import ChoiceLoader, PackageLoader
from psycopg import OperationalError
from psycopg_pool import PoolTimeout
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.core.dependencies import AssetsBidxExprParamsOptional, RescalingParams
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import (
    AlgorithmFactory,
    FactoryExtension,
    MultiBaseTilerFactory,
    TMSFactory,
)
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.resources.enums import ImageType, OptionalHeader
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.mosaic.resources.enums import PixelSelectionMethod
from titiler.pgstac.db import close_db_connection, connect_to_db
from titiler.pgstac.dependencies import ItemPathParams, PgSTACParams
from titiler.pgstac.factory import BaseTilerFactory, MosaicTilerFactory
from titiler.pgstac.reader import PgSTACReader

try:
    pass  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    pass  # type: ignore

logging.getLogger("botocore.credentials").disabled = True
logging.getLogger("botocore.utils").disabled = True
logging.getLogger("rio-tiler").setLevel(logging.ERROR)

settings = ApiSettings()

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(  # type: ignore
    directory="",
    loader=ChoiceLoader(
        [
            PackageLoader(__package__, "templates"),
        ]
    ),
)


if settings.debug:
    optional_headers = [OptionalHeader.server_timing, OptionalHeader.x_assets]
else:
    optional_headers = []

app = FastAPI(title=settings.name, version=eoapi_raster_version)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)


###############################################################################
# MOSAIC Endpoints
# https://github.com/developmentseed/titiler/blob/main/src/titiler/extensions/titiler/extensions/viewer.py#LL21C1-L42C1
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
            layer_params=Depends(factory.layer_dependency),  # noqa
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


###############################################################################
# MOSAIC Endpoints
# https://github.com/developmentseed/eoAPI/blob/main/runtime/eoapi/raster/eoapi/raster/app.py
mosaic = MosaicTilerFactory(
    optional_headers=optional_headers,
    router_prefix="/mosaic",
    add_statistics=True,
    add_map_viewer=False,
    add_mosaic_list=True,
    extensions=[
        mosaicViewerExtension(),
    ],
    layer_dependency=AssetsBidxExprParamsOptional,
)


@mosaic.router.get("/builder", response_class=HTMLResponse)
async def mosaic_builder(request: Request):
    """Mosaic Builder Viewer."""
    return templates.TemplateResponse(
        name="mosaic-builder.html",
        context={
            "request": request,
            "register_endpoint": mosaic.url_for(request, "register_search"),
            "collections_endpoint": str(request.url_for("list_collection")),
        },
        media_type="text/html",
    )


# `Secret` endpoint for mosaic builder. Do not need to be public (in the OpenAPI docs)
@app.get("/collections", include_in_schema=False)
async def list_collection(request: Request):
    """list collections."""
    with request.app.state.dbpool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM collections;")
            return [t[2] for t in cursor.fetchall() if t]


app.include_router(mosaic.router, tags=["Mosaic"], prefix="/mosaic")

###############################################################################
# STAC Item Endpoints
stac = MultiBaseTilerFactory(
    reader=PgSTACReader,
    path_dependency=ItemPathParams,
    optional_headers=optional_headers,
    router_prefix="/collections/{collection_id}/items/{item_id}",
    # add /map viewer
    add_viewer=True,
)


@stac.router.get("/viewer", response_class=HTMLResponse)
def viewer(request: Request, item: pystac.Item = Depends(stac.path_dependency)):
    """STAC Viewer

    Simplified version of https://github.com/developmentseed/titiler/blob/main/src/titiler/extensions/titiler/extensions/templates/stac_viewer.html
    """
    return templates.TemplateResponse(
        name="stac-viewer.html",
        context={
            "request": request,
            "endpoint": request.url.path.replace("/viewer", ""),
        },
        media_type="text/html",
    )


app.include_router(
    stac.router, tags=["Item"], prefix="/collections/{collection_id}/items/{item_id}"
)

###############################################################################
# Tiling Schemes Endpoints
tms = TMSFactory()
app.include_router(tms.router, tags=["Tiling Schemes"])

###############################################################################
# Algorithms Endpoints
algorithms = AlgorithmFactory()
app.include_router(algorithms.router, tags=["Algorithms"])


###############################################################################
# Health Check Endpoint
@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping(
    timeout: int = Query(1, description="Timeout getting SQL connection from the pool.")
) -> Dict:
    """Health check."""
    try:
        with app.state.dbpool.connection(timeout) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version from pgstac.migrations;")
                version = cursor.fetchone()
        return {"database_online": True, "pgstac_version": version}
    except (OperationalError, PoolTimeout):
        return {"database_online": False}


###############################################################################
# Landing page Endpoint
@app.get(
    "/",
    response_class=HTMLResponse,
)
def landing(request: Request):
    """Get landing page."""
    data = {
        "title": "eoAPI-Raster",
        "links": [
            {
                "title": "Landing page",
                "href": str(request.url_for("landing")),
                "type": "text/html",
                "rel": "self",
            },
            {
                "title": "the API definition (JSON)",
                "href": str(request.url_for("openapi")),
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "rel": "service-desc",
            },
            {
                "title": "the API documentation",
                "href": str(request.url_for("swagger_ui_html")),
                "type": "text/html",
                "rel": "service-doc",
            },
            {
                "title": "Mosaic List (JSON)",
                "href": mosaic.url_for(request, "list_mosaic"),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "Mosaic Builder",
                "href": mosaic.url_for(request, "mosaic_builder"),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "Mosaic Metadata (template URL)",
                "href": mosaic.url_for(request, "info_search", searchid="{searchid}"),
                "type": "application/json",
                "rel": "data",
            },
            {
                "title": "Mosaic viewer (template URL)",
                "href": mosaic.url_for(request, "map_viewer", searchid="{searchid}"),
                "type": "text/html",
                "rel": "data",
            },
            {
                "title": "TiTiler-pgSTAC Documentation (external link)",
                "href": "https://stac-utils.github.io/titiler-pgstac/",
                "type": "text/html",
                "rel": "doc",
            },
        ],
    }

    urlpath = request.url.path
    crumbs = []
    baseurl = str(request.base_url).rstrip("/")

    crumbpath = str(baseurl)
    for crumb in urlpath.split("/"):
        crumbpath = crumbpath.rstrip("/")
        part = crumb
        if part is None or part == "":
            part = "Home"
        crumbpath += f"/{crumb}"
        crumbs.append({"url": crumbpath.rstrip("/"), "part": part.capitalize()})

    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "response": data,
            "template": {
                "api_root": baseurl,
                "params": request.query_params,
                "title": "",
            },
            "crumbs": crumbs,
            "url": str(request.url),
            "baseurl": baseurl,
            "urlpath": str(request.url.path),
            "urlparams": str(request.url.query),
        },
    )


if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol=settings.cachecontrol,
    exclude_path={r"/healthz"},
)
app.add_middleware(
    CompressionMiddleware,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
)


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
