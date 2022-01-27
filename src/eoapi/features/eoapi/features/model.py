"""eoAPI.features models."""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.types import BBox
from pydantic import BaseModel


class MediaType(str, Enum):
    """Responses Media types formerly known as MIME types."""

    xml = "application/xml"
    json = "application/json"
    geojson = "application/geo+json"
    html = "text/html"
    text = "text/plain"


class Link(BaseModel):
    """Link model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/link.yaml

    """

    rel: Optional[str]
    title: Optional[str]
    type: Optional[MediaType]
    href: str
    hreflang: Optional[str]
    length: Optional[int]

    class Config:
        """Link model configuration."""

        use_enum_values = True


class Spatial(BaseModel):
    """Spatial Extent model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/extent.yaml

    """

    bbox: List[BBox]
    crs: str = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"


class Temporal(BaseModel):
    """Temporal Extent model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/extent.yaml

    """

    interval: List[Tuple[Optional[str], Optional[str]]]
    trs: str = "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"


class Extent(BaseModel):
    """Extent model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/extent.yaml

    """

    spatial: Optional[Spatial]
    temporal: Optional[Temporal]


class Collection(BaseModel):
    """Collection model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/collection.yaml

    """

    id: str
    title: Optional[str]
    description: Optional[str]
    links: List[Link]
    extent: Optional[Extent]
    itemType: str = "feature"
    crs: str = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"

    class Config:
        """Collection model configuration."""

        extra = "ignore"


class Collections(BaseModel):
    """
    Collections model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/collections.yaml

    """

    collections: List[Collection]
    links: List[Link]


class Item(Feature):
    """Item model

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/featureGeoJSON.yaml

    """

    assets: Dict[str, Any]
    links: Optional[List[Link]]


class Items(FeatureCollection):
    """Items model

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/featureCollectionGeoJSON.yaml

    """

    features: List[Item]  # type: ignore
    links: Optional[List[Link]]
    timeStamp: Optional[str]
    numberMatched: Optional[int]
    numberReturned: Optional[int]


class Conformance(BaseModel):
    """Conformance model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/confClasses.yaml

    """

    conformsTo: List[str]


class Landing(BaseModel):
    """Landing page model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/landingPage.yaml

    """

    title: Optional[str]
    description: Optional[str]
    links: List[Link]
