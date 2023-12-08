import pystac
import rasterio
from urllib.request import urlopen, urlretrieve
import json
import fsspec
from typing import Any, Dict
from pyproj import CRS, Proj
from shapely.geometry import Polygon, box
from typing import Any, Dict, List, Optional
from datetime import datetime
from shapely.geometry import mapping as geojson_mapping
from pystac.extensions.file import FileExtension
from pystac import Link, Provider, ProviderRole

from pystac.extensions.file import MappingObject
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.label import (
    LabelClasses,
    LabelExtension,
    LabelTask,
    LabelType,
)


def save_rf06():
    # Metadata
    title = "MethaneAIR RF06"
    description = "MethaneAIR Flight RF06"
    properties = {
        "title": title,
        "description": description,
    }
    start_datetime = datetime(2021, 8, 6, 13, 34, 54)
    end_datetime = datetime(2021, 8, 6, 20, 32, 54)

    # geometry
    rf06_cog_href = "http://localhost:8090/cogs/RF06.tif"
    with rasterio.open(rf06_cog_href) as dataset:
        cog_bbox = list(dataset.bounds)
        cog_transform = list(dataset.transform)
        cog_shape = [dataset.height, dataset.width]

        transformer = Proj.from_crs(CRS.from_epsg(3857),
                                    CRS.from_epsg(4326),
                                    always_xy=True)
        bbox = list(
            transformer.transform_bounds(dataset.bounds.left, 
                                         dataset.bounds.bottom, 
                                         dataset.bounds.right, 
                                         dataset.bounds.top))

        geometry = geojson_mapping(box(*bbox, ccw=True))

    # Create item
    item = pystac.Item(
        id="RF06_Level4_GIM_COG",
        geometry=geometry,
        bbox=bbox,
        datetime=start_datetime,
        properties=properties,
        stac_extensions=[],
        collection="MethaneAIR_Level4",
    )

    item.common_metadata.start_datetime = start_datetime
    item.common_metadata.end_datetime = end_datetime

    # Create COG asset
    cog_asset = pystac.Asset(
        href=rf06_cog_href,
        media_type=pystac.MediaType.COG,
        roles=[
            "data",
            "labels",
            "labels-raster",
        ],
        title="RF06 COG",
    )
    item.add_asset('COG', cog_asset)

    item_projection = ProjectionExtension.ext(item, add_if_missing=True)

    item_projection.epsg = 3857
    item_projection.wkt2 = CRS.from_epsg(3857).to_wkt()
    item_projection.bbox = cog_bbox
    item_projection.transform = cog_transform
    item_projection.shape = cog_shape

    cog_asset_file = FileExtension.ext(cog_asset, add_if_missing=True)

    with fsspec.open(rf06_cog_href) as file:
        size = file.size
        cog_asset_file.size = size
    print(item.to_dict())

    # Create collection
    collection = pystac.Collection(
        id="MethaneAIR_Level4",
        title="MethaneAIR Level 4 data",
        description="MethaneAIR level 4 data",
        extent=pystac.Extent(
            pystac.SpatialExtent([bbox]),
            pystac.TemporalExtent([[start_datetime, end_datetime]]),
        ),
    )

    print(collection.to_dict())
    item.set_self_href("rf06.json")
    item.save_object()
    collection.set_self_href("level4.json")
    collection.save_object()


def save_rf08():
    # Metadata
    title = "MethaneAIR RF08"
    description = "MethaneAIR Flight RF08"
    properties = {
        "title": title,
        "description": description,
    }
    start_datetime = datetime(2021, 8, 6, 13, 34, 54)
    end_datetime = datetime(2021, 8, 6, 20, 32, 54)

    # geometry
    rf08_cog_href = "http://localhost:8090/cogs/RF08.tif"
    with rasterio.open(rf08_cog_href) as dataset:
        cog_bbox = list(dataset.bounds)
        cog_transform = list(dataset.transform)
        cog_shape = [dataset.height, dataset.width]

        transformer = Proj.from_crs(CRS.from_epsg(3857),
                                    CRS.from_epsg(4326),
                                    always_xy=True)
        bbox = list(
            transformer.transform_bounds(dataset.bounds.left, 
                                         dataset.bounds.bottom, 
                                         dataset.bounds.right, 
                                         dataset.bounds.top))

        geometry = geojson_mapping(box(*bbox, ccw=True))

    # Create item
    item = pystac.Item(
        id="RF08_Level4_GIM_COG",
        geometry=geometry,
        bbox=bbox,
        datetime=start_datetime,
        properties=properties,
        stac_extensions=[],
        collection="MethaneAIR_Level4",
    )

    item.common_metadata.start_datetime = start_datetime
    item.common_metadata.end_datetime = end_datetime

    # Create COG asset
    cog_asset = pystac.Asset(
        href=rf08_cog_href,
        media_type=pystac.MediaType.COG,
        roles=[
            "data",
            "labels",
            "labels-raster",
        ],
        title="RF08 COG",
    )
    item.add_asset('COG', cog_asset)

    item_projection = ProjectionExtension.ext(item, add_if_missing=True)

    item_projection.epsg = 3857
    item_projection.wkt2 = CRS.from_epsg(3857).to_wkt()
    item_projection.bbox = cog_bbox
    item_projection.transform = cog_transform
    item_projection.shape = cog_shape

    cog_asset_file = FileExtension.ext(cog_asset, add_if_missing=True)

    with fsspec.open(rf08_cog_href) as file:
        size = file.size
        cog_asset_file.size = size
    print(item.to_dict())

    # Create collection
    collection = pystac.Collection(
        id="MethaneAIR_Level4",
        title="MethaneAIR Level 4 data",
        description="MethaneAIR level 4 data",
        extent=pystac.Extent(
            pystac.SpatialExtent([bbox]),
            pystac.TemporalExtent([[start_datetime, end_datetime]]),
        ),
    )

    print(collection.to_dict())
    item.set_self_href("rf08.json")
    item.save_object()
    collection.set_self_href("level4.json")
    collection.save_object()


if __name__ == "__main__":
    save_rf06()
    save_rf08()
