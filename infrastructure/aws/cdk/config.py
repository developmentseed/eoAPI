"""eoAPI Configs."""

from enum import Enum
from typing import Dict, List, Optional

import pydantic


class functionName(str, Enum):
    """Function names."""

    stac = "stac"
    raster = "raster"
    vector = "vector"


class eoAPISettings(pydantic.BaseSettings):
    """Application settings"""

    name: str = "eoapi"
    stage: str = "production"
    owner: Optional[str]
    client: Optional[str]
    functions: List[functionName] = [functionName.stac, functionName.raster]

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CDK_EOAPI_"
        use_enum_values = True


class eoDBSettings(pydantic.BaseSettings):
    """Application settings"""

    dbname: str = "eoapi"
    user: str = "eouser"

    # Define PGSTAC VERSION
    pgstac_version: str
    context: bool = True
    mosaic_index: bool = True

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CDK_EOAPI_DB_"


class eoSTACSettings(pydantic.BaseSettings):
    """Application settings"""

    env: Dict = {}

    timeout: int = 10
    memory: int = 256

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CDK_EOAPI_STAC_"


class eoRasterSettings(pydantic.BaseSettings):
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

    # S3 key pattern to limit the access to specific items (e.g: "my_data/*.tif")
    key: str = "*"

    timeout: int = 10
    memory: int = 3008

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CDK_EOAPI_RASTER_"


class eoVectorSettings(pydantic.BaseSettings):
    """Application settings"""

    env: Dict = {}

    timeout: int = 10
    memory: int = 512

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CDK_EOAPI_VECTOR_"
