"""eoapi.features middlewares."""

import re
from typing import Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


class CacheControlMiddleware(BaseHTTPMiddleware):
    """MiddleWare to add CacheControl in response headers."""

    def __init__(
        self,
        app: ASGIApp,
        cachecontrol: Optional[str] = None,
        exclude_path: Optional[Set[str]] = None,
    ) -> None:
        """Init Middleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.
            cachecontrol (str): Cache-Control string to add to the response.
            exclude_path (set): Set of regex expression to use to filter the path.

        """
        super().__init__(app)
        self.cachecontrol = cachecontrol
        self.exclude_path = exclude_path or set()

    async def dispatch(self, request: Request, call_next):
        """Add cache-control."""
        response = await call_next(request)
        if self.cachecontrol and not response.headers.get("Cache-Control"):
            for path in self.exclude_path:
                if re.match(path, request.url.path):
                    return response

            if request.method in ["HEAD", "GET"] and response.status_code < 500:
                response.headers["Cache-Control"] = self.cachecontrol

        return response
