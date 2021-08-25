"""AWS Lambda handler."""

import logging

from mangum import Mangum

from eoapi.raster.app import app

logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)

handler = Mangum(app, lifespan="auto", log_level="error")
