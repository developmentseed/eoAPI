"""Custom Models."""

from enum import Enum
from typing import Optional

from pydantic import Field, validator

from stac_fastapi.pgstac.types import search


# HOT Patch before next stac-fastapi release
class FilterLang(str, Enum):
    """filter language.

    ref: https://github.com/radiantearth/stac-api-spec/tree/master/fragments/filter#get-query-parameters-and-post-json-fields
    """

    cql_json = "cql-json"
    cql_text = "cql-text"
    cql2_json = "cql2-json"


class PgstacSearch(search.PgstacSearch):
    """Extent PgSTAC Search."""

    filter_lang: Optional[FilterLang] = Field(None, alias="filter-lang")

    class Config:
        """Config for model."""

        use_enum_values = True

    @validator("filter_lang", pre=False, check_fields=False, always=True)
    def validate_query_uses_cql(cls, v, values):
        """If using query syntax, forces cql-json."""
        retval = v
        if values.get("query", None) is not None:
            retval = "cql-json"
        if values.get("collections", None) is not None:
            retval = "cql-json"
        if values.get("ids", None) is not None:
            retval = "cql-json"
        if values.get("datetime", None) is not None:
            retval = "cql-json"
        if values.get("bbox", None) is not None:
            retval = "cql-json"
        if v == "cql2-json" and retval == "cql-json":
            raise ValueError(
                "query, collections, ids, datetime, and bbox"
                "parameters are not available in cql2-json"
            )
        return retval
