"""Custom Reader.

This is based on an original idea from Daniel J. Dufour, ref: https://github.com/cogeotiff/rio-tiler/issues/408
"""

import json
from base64 import b64decode

import attr
import pystac
from rio_tiler.io import stac


@attr.s
class STACReader(stac.STACReader):
    """Custom STACReader.

    This reader allows input to be in form of `stac://{base64 encoded STAC items}

    """

    def __attrs_post_init__(self):
        """Decode data: urls."""
        if self.input and self.input.startswith("stac://"):
            self.item = pystac.Item.from_dict(
                json.loads(b64decode(self.input.replace("stac://", "")))
            )
            self.input = None

        super().__attrs_post_init__()
