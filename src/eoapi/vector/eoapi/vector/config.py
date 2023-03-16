"""API settings."""

from functools import lru_cache

import pydantic


class ApiSettings(pydantic.BaseSettings):
    """API settings"""

    name: str = "eoAPI-vector"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    debug: bool = False

    @pydantic.validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_prefix = "EOAPI_VECTOR_"
        env_file = ".env"


class TileSettings(pydantic.BaseSettings):
    """MVT settings"""

    resolution: int = 4096
    buffer: int = 256
    max_feature: int = 10000

    class Config:
        """model config"""

        env_prefix = "EOAPI_MVT_"
        env_file = ".env"
