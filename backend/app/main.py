"""FastAPI application entrypoint for the Latoun configurator backend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_database
from .errors import ConfiguratorError
from .routes import catalog_routes, configuration_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist even if the seed script has not been run yet.
    init_database()
    yield


app = FastAPI(title="Latoun Local Configurator", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConfiguratorError)
async def configurator_error_handler(
    _request: Request, exc: ConfiguratorError
) -> JSONResponse:
    """Surface domain errors as JSON with a clear message; never fail silently."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message},
    )


app.include_router(catalog_routes.router)
app.include_router(configuration_routes.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "latoun-configurator", "docs": "/docs"}
