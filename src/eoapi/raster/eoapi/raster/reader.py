"""Custom STAC reader."""

from typing import Dict, Optional, Set, Type, Union

import attr
import pystac
from morecantile import TileMatrixSet
from rasterio.crs import CRS
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import MissingAssets
from rio_tiler.io import BaseReader, COGReader, stac


@attr.s
class STACReader(stac.STACReader):
    """Custom STAC Reader."""

    input: Union[str, Dict] = attr.ib()  # Input can be of type String or Dict
    item: pystac.Item = attr.ib(init=False)

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib(default=None)
    maxzoom: int = attr.ib(default=None)

    geographic_crs: CRS = attr.ib(default=WGS84_CRS)

    include_assets: Optional[Set[str]] = attr.ib(default=None)
    exclude_assets: Optional[Set[str]] = attr.ib(default=None)

    include_asset_types: Set[str] = attr.ib(default=stac.DEFAULT_VALID_TYPE)
    exclude_asset_types: Optional[Set[str]] = attr.ib(default=None)

    reader: Type[BaseReader] = attr.ib(default=COGReader)
    reader_options: Dict = attr.ib(factory=dict)

    fetch_options: Dict = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        """Fetch STAC Item and get list of valid assets."""
        if isinstance(self.input, (Dict, pystac.Item)):
            self.item = stac._to_pystac_item(self.input)
        else:
            self.item = pystac.Item.from_dict(
                stac.fetch(self.input, **self.fetch_options), self.input
            )

        # TODO: get bounds/crs using PROJ extension if available
        self.bounds = self.item.bbox
        self.crs = WGS84_CRS

        self.assets = list(
            stac._get_assets(
                self.item,
                include=self.include_assets,
                exclude=self.exclude_assets,
                include_asset_types=self.include_asset_types,
                exclude_asset_types=self.exclude_asset_types,
            )
        )
        if not self.assets:
            raise MissingAssets("No valid asset found")

        if self.minzoom is None:
            # TODO get minzoom from PROJ extension
            self.minzoom = self.tms.minzoom

        if self.maxzoom is None:
            # TODO get maxzoom from PROJ extension
            self.maxzoom = self.tms.maxzoom
