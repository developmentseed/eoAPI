"""eoapi.features custom responses."""

from starlette import responses


class GeoJSONResponse(responses.JSONResponse):
    """GeoJSON Response"""

    media_type = "application/geo+json"
