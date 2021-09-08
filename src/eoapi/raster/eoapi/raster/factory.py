"""Custom STACTilerFactory."""

from dataclasses import dataclass
from typing import Dict, Type

from rio_tiler.io import MultiBaseReader
from rio_tiler.models import Info

from eoapi.raster.reader import MyCustomSTACReader
from fastapi import Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from titiler.core.factory import MultiBaseTilerFactory

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))


@dataclass
class STACTilerFactory(MultiBaseTilerFactory):
    """Custom STAC endpoints factory."""

    reader: Type[MultiBaseReader] = MyCustomSTACReader

    def register_routes(self) -> None:
        """This Method register routes to the router."""
        super().register_routes()
        self._viewer_routes()

    def info(self):
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Dict[str, Info],
            response_model_exclude={"minzoom", "maxzoom", "center"},
            response_model_exclude_none=True,
            responses={
                200: {
                    "description": "Return dataset's basic info or the list of available assets."
                }
            },
        )
        def info(src_path=Depends(self.path_dependency)):
            """Return dataset's basic info or the list of available assets."""
            with self.reader(src_path, **self.reader_options) as src_dst:
                return src_dst.info(assets=src_dst.assets)

    def _viewer_routes(self):
        """Register viewer route."""

        @self.router.get("/viewer", response_class=HTMLResponse)
        def stac_demo(
            request: Request, url: str = Depends(self.path_dependency),
        ):
            """STAC Viewer."""
            return templates.TemplateResponse(
                name="stac-viewer.html",
                context={
                    "request": request,
                    "endpoint": request.url.path.replace("/viewer", ""),
                    "stac_url": url,
                },
                media_type="text/html",
            )
