"""eoAPI Configs."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic_settings import BaseSettings


class functionName(str, Enum):
    """Function names."""

    stac = "stac"
    raster = "raster"
    vector = "vector"


class eoAPISettings(BaseSettings):
    """Application settings"""

    name: str = "eoapi"
    stage: str = "production"
    owner: Optional[str] = None
    client: Optional[str] = None
    functions: List[functionName] = [functionName.stac, functionName.raster]

    model_config = {
        "env_prefix": "CDK_EOAPI_",
        "env_file": ".env",
        "extra": "ignore",
        "use_enum_values": True,
    }


class eoDBSettings(BaseSettings):
    """Application settings"""

    dbname: str = "eoapi"
    user: str = "eouser"

    # Define PGSTAC VERSION
    pgstac_version: str
    instance_size: str = "SMALL"
    context: bool = True
    mosaic_index: bool = True
    allocated_storage: int = 20
    model_config = {
        "env_prefix": "CDK_EOAPI_DB_",
        "env_file": ".env",
    }


class eoSTACSettings(BaseSettings):
    """Application settings"""

    env: Dict = {}

    timeout: int = 10
    memory: int = 256

    model_config = {
        "env_prefix": "CDK_EOAPI_STAC_",
        "env_file": ".env",
    }


class eoRasterSettings(BaseSettings):
    """Application settings"""

    # Default options are optimized for CloudOptimized GeoTIFF
    # For more information on GDAL env see: https://gdal.org/user/configoptions.html
    # or https://developmentseed.org/titiler/advanced/performance_tuning/
    env: Dict = {
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF,.tiff",
        "GDAL_CACHEMAX": "200",  # 200 mb
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "GDAL_INGESTED_BYTES_AT_OPEN": "32768",
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
        "GDAL_HTTP_MULTIPLEX": "YES",
        "GDAL_HTTP_VERSION": "2",
        "PYTHONWARNINGS": "ignore",
        "VSI_CACHE": "TRUE",
        "VSI_CACHE_SIZE": "5000000",  # 5 MB (per file-handle)
        "DB_MIN_CONN_SIZE": "1",
        "DB_MAX_CONN_SIZE": "1",
    }

    # S3 bucket names where TiTiler could do HEAD and GET Requests
    # specific private and public buckets MUST be added if you want to use s3:// urls
    # You can whitelist all bucket by setting `*`.
    # ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-arn-format.html
    buckets: List = ["*"]

    timeout: int = 10
    memory: int = 3008

    model_config = {
        "env_prefix": "CDK_EOAPI_RASTER_",
        "env_file": ".env",
    }


class eoVectorSettings(BaseSettings):
    """Application settings"""

    env: Dict = {}

    timeout: int = 10
    memory: int = 512

    model_config = {
        "env_prefix": "CDK_EOAPI_VECTOR_",
        "env_file": ".env",
    }
