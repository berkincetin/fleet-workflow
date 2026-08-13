"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fleet_api.config import get_settings
from fleet_api.errors import install_error_handlers
from fleet_api.middleware import (
    AuditMiddleware,
    RateLimitMiddleware,
    TraceIdMiddleware,
)
from fleet_api.otel import configure_tracing
from fleet_api.routers import (
    agents_admin,
    api_keys_admin,
    approvals,
    chat,
    collections,
    dev_agent,
    documents,
    examples,
    health,
    invoice_agent,
    models_admin,
    rag_query,
    service,
    users_admin,
    whoami,
    workflows,
)


def create_app(*, with_middleware: bool = True) -> FastAPI:
    """Build and configure the Fleet API application.

    Set with_middleware=False for lightweight unit tests that must not touch
    Redis/Postgres. Production keeps the default (middleware on).
    """
    app = FastAPI(title="Fleet API", version="0.1.0")
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(whoami.router)
    app.include_router(models_admin.router)
    app.include_router(agents_admin.router)
    app.include_router(collections.router)
    app.include_router(documents.router)
    app.include_router(rag_query.router)
    app.include_router(chat.router)
    app.include_router(approvals.router)
    app.include_router(dev_agent.router)
    app.include_router(api_keys_admin.router)
    app.include_router(service.router)
    app.include_router(invoice_agent.router)
    app.include_router(examples.router)
    app.include_router(workflows.router)
    app.include_router(users_admin.router)
    app.include_router(users_admin.departments_router)

    if with_middleware:
        settings = get_settings()
        configure_tracing()
        # Starlette wraps middleware in reverse add-order (last added = outermost),
        # and the CORS preflight (OPTIONS) must be handled before anything else
        # runs — so CORSMiddleware is added last.
        app.add_middleware(
            RateLimitMiddleware,
            redis_url=settings.redis_url,
            limit_per_minute=settings.rate_limit_per_minute,
        )
        app.add_middleware(AuditMiddleware)
        app.add_middleware(TraceIdMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[settings.web_origin],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app
