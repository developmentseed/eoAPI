"""FastAPI application using PGStac."""

from eoapi.stac.config import ApiSettings, TilesApiSettings
from eoapi.stac.extension import TilesExtension
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from stac_fastapi.api.app import StacApi
from stac_fastapi.extensions.core import FieldsExtension, QueryExtension, SortExtension
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from stac_fastapi.pgstac.types.search import PgstacSearch
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))

api_settings = ApiSettings()
tiles_settings = TilesApiSettings()
settings = Settings()


api = StacApi(
    app=FastAPI(title=api_settings.name),
    settings=settings,
    extensions=[QueryExtension(), SortExtension(), FieldsExtension()],
    client=CoreCrudClient(),
    search_request_model=PgstacSearch,
    response_class=ORJSONResponse,
)
app = api.app


# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

if tiles_settings.titiler_endpoint:
    # Register to the tiles extension to the api
    extension = TilesExtension()
    extension.register(api.app, tiles_settings.titiler_endpoint)


@app.get("/index.html", response_class=HTMLResponse)
async def viewer_page(request: Request):
    """Search viewer."""
    print(request.url)
    return templates.TemplateResponse(
        "stac-viewer.html",
        {
            "request": request,
            "endpoint": str(request.url).replace("/index.html", ""),
            "mapbox_token": api_settings.mapbox_token,
        },
        media_type="text/html",
    )


@app.on_event("startup")
async def startup_event():
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection."""
    await close_db_connection(app)
