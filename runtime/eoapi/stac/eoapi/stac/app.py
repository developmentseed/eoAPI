"""FastAPI application using PGStac."""

from contextlib import asynccontextmanager
from typing import Annotated, Any, Dict

from eoapi.stac.config import ApiSettings, TilesApiSettings
from eoapi.stac.extension import TiTilerExtension
from eoapi.stac.extension import extensions_map as PgStacExtensions
from fastapi import FastAPI, Security
from fastapi.responses import ORJSONResponse
from stac_fastapi.api.app import StacApi
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from stac_fastapi.pgstac.types.search import PgstacSearch
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette_cramjam.middleware import CompressionMiddleware

from .auth import KeycloakAuth

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore

api_settings = ApiSettings()
tiles_settings = TilesApiSettings()
settings = Settings()

keycloak = KeycloakAuth()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan."""
    # Create Connection Pool
    await connect_to_db(app)
    yield
    # Close the Connection Pool
    await close_db_connection(app)


if enabled_extensions := api_settings.extensions:
    extensions = [
        PgStacExtensions[extension_name] for extension_name in enabled_extensions
    ]
else:
    extensions = list(PgStacExtensions.values())

POSTModel = create_post_request_model(extensions, base_model=PgstacSearch)
GETModel = create_get_request_model(extensions)

api = StacApi(
    app=FastAPI(
        title=api_settings.name,
        lifespan=lifespan,
        swagger_ui_init_oauth={
            "appName": "eoAPI",
            "clientId": keycloak.client_id,
            "usePkceWithAuthorizationCodeGrant": True,
        },
    ),
    title=api_settings.name,
    description=api_settings.name,
    settings=settings,
    extensions=extensions,
    client=CoreCrudClient(post_request_model=POSTModel),
    search_get_request_model=GETModel,
    search_post_request_model=POSTModel,
    response_class=ORJSONResponse,
    middlewares=[CompressionMiddleware],
)
app = api.app

# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=api_settings.cors_methods,
        allow_headers=["*"],
    )

if tiles_settings.titiler_endpoint:
    # Register to the TiTiler extension to the api
    extension = TiTilerExtension()
    extension.register(api.app, tiles_settings.titiler_endpoint)

for (method, path), scopes in {
    ("POST", "/collections"): ["stac:collection:create"],
    ("PUT", "/collections"): ["stac:collection:update"],
    ("DELETE", "/collections/{collection_id}"): ["stac:collection:delete"],
    ("POST", "/collections/{collection_id}/items"): ["stac:item:create"],
    ("PUT", "/collections/{collection_id}/items/{item_id}"): ["stac:item:update"],
    ("DELETE", "/collections/{collection_id}/items/{item_id}"): ["stac:item:delete"],
}.items():
    api.add_route_dependencies(
        [
            {
                "path": app.router.prefix + path,
                "method": method,
                "type": "http",
            },
        ],
        [Security(keycloak.scheme, scopes=scopes)],
    )


@app.get("/index.html", response_class=HTMLResponse)
async def viewer_page(request: Request):
    """Search viewer."""
    return templates.TemplateResponse(
        "stac-viewer.html",
        {"request": request, "endpoint": str(request.url).replace("/index.html", "")},
        media_type="text/html",
    )


@app.get("/user", tags=["auth"])
def get_user(user_token: Annotated[Dict[Any, Any], Security(keycloak.user_validator)]):
    """View auth token."""
    return user_token
