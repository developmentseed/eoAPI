"""API settings."""

from functools import lru_cache
from typing import Optional

import pydantic
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.extensions.core import (
    ContextExtension,
    FieldsExtension,
    FilterExtension,
    QueryExtension,
    SortExtension,
    TokenPaginationExtension,
)
from stac_fastapi.pgstac.types.search import PgstacSearch


class _ApiSettings(pydantic.BaseSettings):
    """API settings"""

    name: str = "eoAPI-stac"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    debug: bool = False

    @pydantic.validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "EOAPI_STAC_"


@lru_cache()
def ApiSettings() -> _ApiSettings:
    """
    This function returns a cached instance of the APISettings object.
    Caching is used to prevent re-reading the environment every time the API settings are used in an endpoint.
    If you want to change an environment variable and reset the cache (e.g., during testing), this can be done
    using the `lru_cache` instance method `get_api_settings.cache_clear()`.

    From https://github.com/dmontagu/fastapi-utils/blob/af95ff4a8195caaa9edaa3dbd5b6eeb09691d9c7/fastapi_utils/api_settings.py#L60-L69
    """
    return _ApiSettings()


class _TilesApiSettings(pydantic.BaseSettings):
    """Tile API settings"""

    titiler_endpoint: Optional[str]

    class Config:
        """model config"""

        env_file = ".env"


@lru_cache()
def TilesApiSettings() -> _TilesApiSettings:
    """
    This function returns a cached instance of the TilesApiSettings object.
    Caching is used to prevent re-reading the environment every time the API settings are used in an endpoint.

    """
    return _TilesApiSettings()


extensions = [
    FilterExtension(),
    QueryExtension(),
    SortExtension(),
    FieldsExtension(),
    TokenPaginationExtension(),
    ContextExtension(),
]
post_request_model = create_post_request_model(extensions, base_model=PgstacSearch)
get_request_model = create_get_request_model(extensions)
