"""API settings."""

import pydantic


class ApiSettings(pydantic.BaseSettings):
    """API settings"""

    name: str = "eoAPI-raster"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    debug: bool = False
    root_path: str = ""

    @pydantic.validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "EOAPI_RASTER_"
