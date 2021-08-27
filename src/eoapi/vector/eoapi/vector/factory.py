"""MVTilerFactory."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from buildpg import render
from morecantile import Tile, TileMatrixSet, tms
from pydantic import BaseModel, Field, root_validator, validator
from stac_pydantic.api.extensions.query import Operator
from stac_pydantic.api.extensions.sort import SortExtension

from eoapi.vector.config import TileSettings
from fastapi import APIRouter, Depends, Path, Query
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates

mvt_settings = TileSettings()

TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [(a, a) for a in sorted(tms.list())]
)

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))


class TileJSON(BaseModel):
    """
    TileJSON model.

    Based on https://github.com/mapbox/tilejson-spec/tree/master/2.2.0

    """

    tilejson: str = "2.2.0"
    name: Optional[str]
    description: Optional[str]
    version: str = "1.0.0"
    attribution: Optional[str]
    template: Optional[str]
    legend: Optional[str]
    scheme: str = "xyz"
    tiles: List[str]
    grids: List[str] = []
    data: List[str] = []
    minzoom: int = Field(0, ge=0, le=30)
    maxzoom: int = Field(22, ge=0, le=30)
    bounds: List[float] = [-180, -90, 180, 90]
    center: Optional[Tuple[float, float, int]]

    @root_validator
    def compute_center(cls, values):
        """Compute center if it does not exist."""
        bounds = values["bounds"]
        if not values.get("center"):
            values["center"] = (
                (bounds[0] + bounds[2]) / 2,
                (bounds[1] + bounds[3]) / 2,
                values["minzoom"],
            )
        return values


class SearchCreate(BaseModel):
    """Search model.

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


def TileMatrixSetParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    ),
) -> TileMatrixSet:
    """TileMatrixSet parameters."""
    return tms.get(TileMatrixSetId.name)


@dataclass
class MVTilerFactory:
    """Mapbox Vector Tile endpoint factory."""

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        self.register_routes()

    def register_routes(self):
        """Register Tiler Routes."""
        self._search_mvt()
        self._mercator_agg_grid()

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        """Return full url (with prefix) for a specific endpoint."""
        url_path = self.router.url_path_for(name, **path_params)
        base_url = str(request.base_url)
        if self.router_prefix:
            base_url += self.router_prefix.lstrip("/")
        return url_path.make_absolute_url(base_url=base_url)

    def _search_mvt(self):
        """register search VectorTiles."""

        @self.router.post(
            "/register", responses={200: {"description": "Register Search request."}},
        )
        async def register_search(request: Request, body: SearchCreate):
            """Register Search requests."""
            pool = request.app.state.pool
            async with pool.acquire() as conn:
                q, p = render(
                    """
                    SELECT * FROM search_query(:req);
                    """,
                    req=body.json(exclude_none=True),
                )
                searchid = await conn.fetchval(q, *p)

            return {
                "searchid": searchid,
                "url": self.url_for(request, "search_tilejson", searchid=searchid),
            }

        @self.router.get(
            "/tiles/{searchid}/{z}/{x}/{y}.pbf",
            responses={200: {"content": {"application/x-protobuf": {}}}},
            response_class=Response,
        )
        @self.router.get(
            "/tiles/{TileMatrixSetId}/{searchid}/{z}/{x}/{y}.pbf",
            responses={200: {"content": {"application/x-protobuf": {}}}},
            response_class=Response,
        )
        async def search_tiles(
            request: Request,
            searchid: str = Path(..., description="search id"),
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            tms: TileMatrixSet = Depends(TileMatrixSetParams),
        ):
            """Return vector tile."""
            pool = request.app.state.pool

            bbox = tms.xy_bounds(Tile(x, y, z))
            epsg = tms.crs.to_epsg()

            async with pool.acquire() as conn:
                transaction = conn.transaction()
                await transaction.start()
                await conn.execute(
                    """
                    CREATE OR REPLACE FUNCTION search_items(
                        IN geom geometry,
                        IN queryhash text,
                        IN epsg int,
                        IN items_limit int DEFAULT 10000,
                        IN tile_resolution int DEFAULT 4096,
                        IN tile_buffer int DEFAULT 256,
                        IN _scanlimit int DEFAULT 10000,
                        IN _timelimit interval DEFAULT '5 seconds'::interval,
                        OUT mvtgeom geometry,
                        OUT id text
                    ) RETURNS setof RECORD AS $$
                    DECLARE
                        search searches%ROWTYPE;
                        curs refcursor;
                        _where text;
                        query text;
                        iter_record items%ROWTYPE;
                        exit_flag boolean := FALSE;
                        counter int := 1;
                        scancounter int := 1;
                        remaining_limit int := _scanlimit;
                    BEGIN
                        SELECT * INTO search FROM searches WHERE hash=queryhash;

                        IF NOT FOUND THEN
                            RAISE EXCEPTION 'Search with Query Hash % Not Found', queryhash;
                        END IF;

                        _where := format('%s AND ST_Intersects(geometry, %L::geometry)', search._where, ST_Transform(geom, 4326));

                        FOR query IN SELECT * FROM partition_queries(_where, search.orderby) LOOP
                            query := format('%s LIMIT %L', query, remaining_limit);
                            curs = create_cursor(query);
                            LOOP
                                FETCH curs INTO iter_record;
                                EXIT WHEN NOT FOUND;

                                mvtgeom := ST_ASMVTGeom(
                                    ST_Transform(iter_record.geometry, epsg),
                                    geom,
                                    tile_resolution,
                                    tile_buffer
                                );

                                id := iter_record.id;

                                RETURN NEXT;

                                IF counter >= items_limit
                                    OR scancounter > _scanlimit
                                    OR ftime() > _timelimit
                                THEN
                                    exit_flag := TRUE;
                                    EXIT;
                                END IF;
                                counter := counter + 1;
                                scancounter := scancounter + 1;

                            END LOOP;
                            EXIT WHEN exit_flag;
                            remaining_limit := _scanlimit - scancounter;
                        END LOOP;
                        RETURN;
                    END;
                    $$ LANGUAGE PLPGSQL;
                """
                )

                query, args = render(
                    """
                    SELECT ST_AsMVT(mvtgeom.*) FROM search_items(
                        st_segmentize(
                            st_makeenvelope(
                                :xmin,
                                :ymin,
                                :xmax,
                                :ymax,
                                :epsg
                            ),
                            :seg_size
                        ),
                        :queryhash,
                        :epsg,
                        :limit,
                        :tile_resolution,
                        :tile_buffer
                    ) as mvtgeom;
                    """,
                    xmin=bbox.left,
                    ymin=bbox.bottom,
                    xmax=bbox.right,
                    ymax=bbox.top,
                    epsg=epsg,
                    seg_size=bbox.right - bbox.left,
                    queryhash=searchid,
                    tile_resolution=mvt_settings.resolution,
                    tile_buffer=mvt_settings.buffer,
                    limit=mvt_settings.max_feature,
                )
                content = await conn.fetchval(query, *args)
                await transaction.rollback()

            return Response(content, media_type="application/x-protobuf")

        @self.router.get(
            "/{searchid}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{TileMatrixSetId}/{searchid}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        async def search_tilejson(
            request: Request,
            searchid: str = Path(..., description="search id"),
            tms: TileMatrixSet = Depends(TileMatrixSetParams),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            bounds: Optional[str] = Query(
                None, description="Overwrite default bounding box."
            ),
        ):
            """return TileJSON for a searchid."""
            route_params = {
                "TileMatrixSetId": tms.identifier,
                "searchid": searchid,
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
            }

            tiles_endpoint = self.url_for(request, "search_tiles", **route_params)

            bbox = (
                tuple(map(float, bounds.split(","))) if bounds else (-180, -90, 180, 90)
            )

            return {
                "bounds": bbox,
                "minzoom": minzoom if minzoom is not None else tms.minzoom,
                "maxzoom": maxzoom if maxzoom is not None else tms.maxzoom,
                "name": searchid,
                "tiles": [tiles_endpoint],
            }

        @self.router.get(
            "/{searchid}/index.html", response_class=HTMLResponse,
        )
        async def search_page(
            request: Request, searchid: str = Path(..., description="search id"),
        ):
            """Search viewer."""
            route_params = {
                "searchid": searchid,
            }

            return templates.TemplateResponse(
                "index_vector.html",
                {
                    "request": request,
                    "tilejson_endpoint": self.url_for(
                        request, "search_tilejson", **route_params
                    ),
                },
                media_type="text/html",
            )

    def _mercator_agg_grid(self):
        """register Mercator Aggregation grid endpoints."""

        @self.router.get(
            "/grid/mercator/{searchid}/{z}/{x}/{y}.pbf",
            responses={200: {"content": {"application/x-protobuf": {}}}},
            response_class=Response,
        )
        async def mercator_grid_tiles(
            request: Request,
            searchid: str = Path(..., description="search id"),
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            depth: int = Query(2),
        ):
            """Return vector tile."""
            pool = request.app.state.pool
            async with pool.acquire() as conn:
                transaction = conn.transaction()
                await transaction.start()
                await conn.execute(
                    """
                    CREATE OR REPLACE FUNCTION find_items(
                        IN geom geometry,
                        IN queryhash text,
                        IN items_limit int DEFAULT 10000,
                        IN _scanlimit int DEFAULT 10000,
                        IN _timelimit interval DEFAULT '5 seconds'::interval,
                        OUT id text
                    ) RETURNS setof text AS $$
                    DECLARE
                        search searches%ROWTYPE;
                        curs refcursor;
                        _where text;
                        query text;
                        iter_record items%ROWTYPE;
                        exit_flag boolean := FALSE;
                        counter int := 1;
                        scancounter int := 1;
                        remaining_limit int := _scanlimit;
                    BEGIN
                        SELECT * INTO search FROM searches WHERE hash=queryhash;

                        IF NOT FOUND THEN
                            RAISE EXCEPTION 'Search with Query Hash % Not Found', queryhash;
                        END IF;

                        _where := format('%s AND ST_Intersects(geometry, %L::geometry)', search._where, ST_Transform(geom, 4326));

                        FOR query IN SELECT * FROM partition_queries(_where, search.orderby) LOOP
                            query := format('%s LIMIT %L', query, remaining_limit);
                            curs = create_cursor(query);
                            LOOP
                                FETCH curs INTO iter_record;
                                EXIT WHEN NOT FOUND;

                                id := iter_record.id;
                                RETURN NEXT;

                                IF counter >= items_limit
                                    OR scancounter > _scanlimit
                                    OR ftime() > _timelimit
                                THEN
                                    exit_flag := TRUE;
                                    EXIT;
                                END IF;
                                counter := counter + 1;
                                scancounter := scancounter + 1;
                            END LOOP;
                            EXIT WHEN exit_flag;
                            remaining_limit := _scanlimit - scancounter;
                        END LOOP;
                        RETURN;
                    END;
                    $$ LANGUAGE PLPGSQL;

                    CREATE OR REPLACE FUNCTION mercgrid(
                        z integer,
                        x integer,
                        y integer,
                        queryhash text,
                        depth integer default 2
                    )
                    RETURNS bytea AS $$
                    DECLARE
                        tile geometry;
                        result bytea;
                        sq_width float8;
                        tile_xmin float8;
                        tile_ymin float8;
                        bounds geometry;
                    BEGIN
                        -- Find the tile bounds
                        SELECT ST_TileEnvelope(z, x, y) AS geom INTO bounds;

                        -- Find the bottom corner of the bounds
                        tile_xmin := ST_XMin(bounds);
                        tile_ymin := ST_YMin(bounds);

                        -- We want tile divided up into depth*depth squares per tile,
                        -- so what is the width of a square?
                        sq_width := (ST_XMax(bounds) - ST_XMin(bounds)) / depth;

                        WITH mvtgeom AS (
                            SELECT ST_AsMVTGeom(
                                ST_MakeEnvelope(
                                    tile_xmin + sq_width * (a-1),
                                    tile_ymin + sq_width * (b-1),
                                    tile_xmin + sq_width * a,
                                    tile_ymin + sq_width * b,
                                    3857
                                ),
                                bounds
                            ),
                            (
                                SELECT COUNT(*) FROM find_items(
                                    ST_MakeEnvelope(
                                        tile_xmin + sq_width * (a-1),
                                        tile_ymin + sq_width * (b-1),
                                        tile_xmin + sq_width * a,
                                        tile_ymin + sq_width * b,
                                        3857
                                    ),
                                    queryhash
                                )
                            ) AS count

                            -- Drive the square generator with a two-dimensional
                            -- generate_series setup
                            FROM generate_series(1, depth) a, generate_series(1, depth) b
                        )
                        SELECT ST_AsMVT(mvtgeom.*)

                        -- Put the query result into the result variale.
                        INTO result FROM mvtgeom;

                        -- Return the answer
                        RETURN result;
                    END;
                    $$
                    LANGUAGE 'plpgsql'
                    """
                )

                query, args = render(
                    """
                    SELECT * FROM mercgrid(
                        :z,
                        :x,
                        :y,
                        :searchid,
                        :depth
                    );
                    """,
                    z=z,
                    x=x,
                    y=y,
                    depth=depth,
                    searchid=searchid,
                )
                content = await conn.fetchval(query, *args)
                await transaction.rollback()

            return Response(content, media_type="application/x-protobuf")

        @self.router.get(
            "/grid/mercator/{searchid}/index.html", response_class=HTMLResponse,
        )
        async def grid_page(
            request: Request, searchid: str = Path(..., description="search id"),
        ):
            """Search viewer."""
            return templates.TemplateResponse(
                "index_grid_count.html",
                {
                    "request": request,
                    "tiles_endpoint": self.url_for(
                        request,
                        "mercator_grid_tiles",
                        searchid=searchid,
                        z="{z}",
                        x="{x}",
                        y="{y}",
                    ),
                },
                media_type="text/html",
            )
