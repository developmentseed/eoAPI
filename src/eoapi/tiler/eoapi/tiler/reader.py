"""Custom Reader.

This is based on an original idea from Daniel J. Dufour, ref: https://github.com/cogeotiff/rio-tiler/issues/408
"""

import json
from base64 import b64decode

import attr
import pystac
from rio_tiler.io import STACReader


@attr.s
class MyCustomSTACReader(STACReader):
    """Custom STACReader."""

    def __attrs_post_init__(self):
        """Decode data: urls."""
        if self.filepath and self.filepath.startswith("stac://"):
            self.item = pystac.Item.from_dict(
                json.loads(b64decode(self.filepath.replace("stac://", "")))
            )
            self.filepath = None

        super().__attrs_post_init__()
