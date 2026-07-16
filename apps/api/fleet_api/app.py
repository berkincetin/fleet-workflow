"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fleet_api.errors import install_error_handlers
from fleet_api.routers import health, whoami


def create_app() -> FastAPI:
    """Build and configure the Fleet API application."""
    app = FastAPI(title="Fleet API", version="0.1.0")
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(whoami.router)
    return app
