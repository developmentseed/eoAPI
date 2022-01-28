"""eoAPI.vector FastAPI application."""

from typing import Dict

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from eoapi.vector.config import ApiSettings
from eoapi.vector.db import close_db_connection, connect_to_db
from eoapi.vector.factory import MVTilerFactory
from eoapi.vector.version import __version__

settings = ApiSettings()

app = FastAPI(title=settings.name, version=__version__)

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


mvt = MVTilerFactory()
app.include_router(mvt.router)


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping() -> Dict:
    """Health check."""
    return {"ping": "pong!"}


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)
