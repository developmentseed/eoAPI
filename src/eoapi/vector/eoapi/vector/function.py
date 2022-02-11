"""eoapi.vector custom SQLfunctions."""
import os

from timvt.layer import Function, FunctionRegistry

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

sql_dir = str(resources_files(__package__))  # type: ignore


function_registry = FunctionRegistry()
function_registry.register(
    Function.from_file(
        id="search",
        infile=os.path.join(sql_dir, "sql", "search.sql"),
        function_name="search_mvt",
    )
)

function_registry.register(
    Function.from_file(
        id="mercator",
        infile=os.path.join(sql_dir, "sql", "mercator.sql"),
        function_name="mercator",
    )
)
