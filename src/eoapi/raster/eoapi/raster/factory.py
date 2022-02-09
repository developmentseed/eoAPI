"""Custom MultiBaseTilerFactory."""

from dataclasses import dataclass
from typing import Any

from fastapi import Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from titiler.core import factory

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


@dataclass
class MultiBaseTilerFactory(factory.MultiBaseTilerFactory):
    """Custom endpoints factory."""

    def register_routes(self) -> None:
        """This Method register routes to the router."""
        super().register_routes()

        # Add viewer
        @self.router.get("/viewer", response_class=HTMLResponse)
        def stac_demo(
            request: Request,
            src_path: Any = Depends(self.path_dependency),
        ):
            """STAC Viewer."""
            return templates.TemplateResponse(
                name="stac-viewer.html",
                context={
                    "request": request,
                    "endpoint": request.url.path.replace("/viewer", ""),
                    "stac_url": request.query_params[
                        "url"
                    ],  # Warning: This assume that `self.path_dependency` uses `url=`
                },
                media_type="text/html",
            )
