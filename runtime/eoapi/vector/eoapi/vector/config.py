"""API settings."""


import pydantic


class ApiSettings(pydantic.BaseSettings):
    """API settings"""

    name: str = "eoAPI-vector"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    debug: bool = False

    catalog_ttl: int = 300

    @pydantic.validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_prefix = "EOAPI_VECTOR_"
        env_file = ".env"
