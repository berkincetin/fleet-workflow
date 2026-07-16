# Sprint 1 · Stage C — Auth Core, Middleware, Helm/k3d Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement tasks 1.3 (gateway auth core: FastAPI app factory, OIDC token validation, RBAC decorator + permission service, error model, health/readiness), 1.4 (cross-cutting middleware: append-only audit, OpenTelemetry trace_id propagation, Redis rate limiter, OpenAPI→generated TS client), and 1.5 (Helm umbrella chart + k3d bootstrap). Then enable branch protection on `main` (the GitHub side of task 1.0) and close Sprint 1.

**Architecture:** The FastAPI app is assembled by a factory (`create_app`) that wires middleware in the correct order (trace_id → audit → rate-limit) and mounts routers. OIDC validation fetches Keycloak's JWKS and verifies RS256 tokens; a `permission service` enforces the §7 RBAC matrix as a dependency/decorator on service methods, not just routes. Audit writes go to the append-only `audit_log` table (from Stage B) carrying the request's trace_id. The Helm umbrella chart templates the 1.1 compose stack for k3d; `make k3d-up` stands it up locally.

**Tech Stack:** Python 3.12 (uv), FastAPI, Pydantic v2, `python-jose[cryptography]` (JWT/JWKS) or `pyjwt[crypto]`, `httpx` (JWKS fetch), `redis` (async), OpenTelemetry SDK, SQLAlchemy async (from Stage B), testcontainers (Postgres + Keycloak + Redis), Helm 3, k3d, `openapi-typescript` (TS client gen via pnpm).

## Global Constraints

- **English only** in every repo artifact — code, comments, docs, config.
- **Python 3.12**, full typing, Pydantic v2 at boundaries, async I/O only. Domain errors from `core.errors`.
- **RBAC roles are exactly** (TRD §7.1): `platform_admin, dept_admin, builder, approver, member`. Permission checks are decorators/dependencies on service methods, not only routes.
- **`fleet_readonly` stays read-only** (unchanged from Stage B).
- **Every endpoint keeps** trace_id propagation, audit emit, RBAC enforcement — these are cross-cutting; do not special-case around them (CLAUDE.md rule 6).
- **Migrations only via Alembic** — if a new table is needed (e.g. api_keys is NOT in scope here), do not add it ad hoc; Stage C adds no new tables (audit_log already exists).
- **Pinned versions** — image tags, action versions, Helm chart appVersion pinned; no `:latest`.
- **No secrets in code/CI** — Keycloak client secret for tests comes from the realm fixture; nothing real committed.
- **Commit automatically** on `feat/sprint-1-stage-c` (single-sentence English subject, no AI byline, no `Co-Authored-By`). Land via PR; never push to protected `main`.
- **Dual-layer docs rule:** this stage writes no changes to `docs/*` canonical originals; only code + `docs/PROGRESS.md` + `docs/superpowers/`.
- PowerShell PATH refresh when a fresh tool isn't found: `$m=[Environment]::GetEnvironmentVariable('Path','Machine');$u=[Environment]::GetEnvironmentVariable('Path','User');$env:Path="$m;$u"`. `uv`/`make`/`k3d`/`kubectl`/`helm`/`gh` are installed.

---

### Task 1: Config, error model, and FastAPI app factory with health/readiness (1.3 part A)

**Files:**
- Create: `apps/api/fleet_api/config.py` (pydantic-settings)
- Create: `apps/api/fleet_api/errors.py` (domain error model + handlers)
- Create: `apps/api/fleet_api/app.py` (`create_app` factory)
- Create: `apps/api/fleet_api/routers/__init__.py`
- Create: `apps/api/fleet_api/routers/health.py`
- Modify: `apps/api/pyproject.toml` (add fastapi, uvicorn, httpx, python-jose[cryptography], redis)
- Test: `tests/unit/test_health.py`

**Interfaces:**
- Consumes: `fleet_api.db` (Stage B).
- Produces: `fleet_api.app.create_app() -> FastAPI`; `fleet_api.config.Settings` (env-driven); `fleet_api.errors.AppError` (base domain error) + `install_error_handlers(app)`; a health router exposing `GET /healthz` (liveness) and `GET /readyz` (readiness — checks DB). Later tasks add auth deps, middleware, and routers to `create_app`.

- [ ] **Step 1: Add deps to `apps/api/pyproject.toml`** — extend the `dependencies` list (keep existing sqlalchemy/asyncpg/alembic/pydantic/pydantic-settings):

```toml
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "httpx>=0.27",
    "python-jose[cryptography]>=3.3",
    "redis>=5.2",
    "opentelemetry-api>=1.28",
    "opentelemetry-sdk>=1.28",
```

- [ ] **Step 2: Create `apps/api/fleet_api/config.py`**

```python
"""Application settings, loaded from the environment (pydantic-settings)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration for the Fleet API."""

    model_config = SettingsConfigDict(env_prefix="FLEET_", extra="ignore")

    database_url: str = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
    # OIDC / Keycloak
    oidc_issuer: str = "http://localhost:8080/realms/fleet"
    oidc_audience: str = "fleet-api"
    oidc_jwks_url: str = "http://localhost:8080/realms/fleet/protocol/openid-connect/certs"
    # Redis (rate limiting)
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 120


def get_settings() -> Settings:
    """Return a fresh Settings instance (call at app creation, not import time)."""
    return Settings()
```

- [ ] **Step 3: Create `apps/api/fleet_api/errors.py`**

```python
"""Domain error model and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for domain errors mapped to HTTP responses."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.code
        super().__init__(self.message)


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


def install_error_handlers(app: FastAPI) -> None:
    """Register a handler that renders AppError as a structured JSON body."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
```

- [ ] **Step 4: Create `apps/api/fleet_api/routers/__init__.py`**

```python
"""API routers."""
```

- [ ] **Step 5: Create `apps/api/fleet_api/routers/health.py`**

```python
"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from fleet_api.db import get_engine

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz() -> dict[str, str]:
    """Readiness: the database is reachable."""
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await engine.dispose()
    return {"status": "ready"}
```

- [ ] **Step 6: Create `apps/api/fleet_api/app.py`**

```python
"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from fleet_api.errors import install_error_handlers
from fleet_api.routers import health


def create_app() -> FastAPI:
    """Build and configure the Fleet API application."""
    app = FastAPI(title="Fleet API", version="0.1.0")
    install_error_handlers(app)
    app.include_router(health.router)
    return app
```

- [ ] **Step 7: Write the unit test** `tests/unit/test_health.py`

```python
"""Unit test: healthz returns ok without any external dependency."""

from fastapi.testclient import TestClient

from fleet_api.app import create_app


def test_healthz_ok() -> None:
    client = TestClient(create_app())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 8: Sync, run the unit test, lint**

Run (PowerShell, PATH refreshed):
```
uv sync
uv run pytest tests/unit/test_health.py -v
uv run ruff check apps/api tests
```
Expected: `uv sync` installs fastapi/etc; the test PASSES; ruff exit 0. (`TestClient` needs `httpx`, which we added.)

- [ ] **Step 9: Commit**

```
git add -A
git commit -m "Add API config, error model, and app factory with health and readiness"
```

---

### Task 2: OIDC validation + RBAC permission service + 401/403 integration tests (1.3 part B)

**Files:**
- Create: `apps/api/fleet_api/auth.py` (JWKS fetch + token verify + current-user dependency)
- Create: `apps/api/fleet_api/rbac.py` (roles, permission matrix, `require_permission`)
- Create: `apps/api/fleet_api/routers/whoami.py` (a protected demo route to exercise auth/RBAC)
- Modify: `apps/api/fleet_api/app.py` (mount whoami router)
- Modify: `apps/api/pyproject.toml` (add testcontainers keycloak extra if needed — see step)
- Test: `tests/integration/test_auth_rbac.py` (real Keycloak testcontainer)

**Interfaces:**
- Consumes: `fleet_api.config.get_settings`, `fleet_api.errors.{UnauthorizedError,ForbiddenError}`.
- Produces: `fleet_api.auth.get_current_user` (FastAPI dependency → `CurrentUser` with `sub`, `roles: set[str]`); `fleet_api.rbac.Permission` (enum), `fleet_api.rbac.require_permission(perm)` (dependency factory that raises ForbiddenError); `fleet_api.rbac.ROLE_PERMISSIONS` (the §7 matrix). Later middleware/routers depend on `get_current_user`.

- [ ] **Step 1: Create `apps/api/fleet_api/rbac.py`** (the §7.1 matrix — roles: platform_admin, dept_admin, builder, approver, member)

```python
"""Role-based access control: roles, permissions, and the enforcement dependency."""

from __future__ import annotations

from enum import StrEnum

from fastapi import Depends

from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import ForbiddenError


class Permission(StrEnum):
    CHAT = "chat"
    UPLOAD = "upload"
    MANAGE_AGENTS = "manage_agents"
    APPROVE = "approve"
    MANAGE_DEPT = "manage_dept"
    MANAGE_PLATFORM = "manage_platform"


# TRD §7.1 RBAC matrix. Roles: platform_admin, dept_admin, builder, approver, member.
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "member": {Permission.CHAT, Permission.UPLOAD},
    "builder": {Permission.CHAT, Permission.UPLOAD, Permission.MANAGE_AGENTS},
    "approver": {Permission.CHAT, Permission.UPLOAD, Permission.APPROVE},
    "dept_admin": {
        Permission.CHAT,
        Permission.UPLOAD,
        Permission.MANAGE_AGENTS,
        Permission.APPROVE,
        Permission.MANAGE_DEPT,
    },
    "platform_admin": set(Permission),
}


def permissions_for(roles: set[str]) -> set[Permission]:
    """Union of permissions granted by the user's roles."""
    granted: set[Permission] = set()
    for role in roles:
        granted |= ROLE_PERMISSIONS.get(role, set())
    return granted


def require_permission(perm: Permission):
    """Dependency factory: allow the request only if the user holds `perm`."""

    async def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if perm not in permissions_for(user.roles):
            raise ForbiddenError(f"missing permission: {perm}")
        return user

    return _dep
```

- [ ] **Step 2: Create `apps/api/fleet_api/auth.py`** (OIDC RS256 verify against Keycloak JWKS)

```python
"""OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from fleet_api.config import Settings, get_settings
from fleet_api.errors import UnauthorizedError

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """The authenticated principal extracted from a verified token."""

    sub: str
    roles: set[str] = field(default_factory=set)


async def _fetch_jwks(url: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


def _extract_roles(claims: dict) -> set[str]:
    # Keycloak puts realm roles under realm_access.roles.
    realm = claims.get("realm_access", {}) or {}
    return set(realm.get("roles", []))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Verify the bearer token and return the current user, or raise 401."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("missing bearer token")
    token = credentials.credentials
    try:
        jwks = await _fetch_jwks(settings.oidc_jwks_url)
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"verify_aud": True},
        )
    except (JWTError, httpx.HTTPError) as exc:
        raise UnauthorizedError("invalid token") from exc
    sub = claims.get("sub")
    if not sub:
        raise UnauthorizedError("token missing sub")
    return CurrentUser(sub=sub, roles=_extract_roles(claims))
```

Note: python-jose's `jwt.decode` accepts a JWKS dict directly for `key`. If verification of `aud` is brittle with Keycloak's default token (aud may be `account`), the test in Step 6 will surface it — the integration test requests a token for the `fleet-api` client; if `aud` doesn't match, adjust `oidc_audience` or set `options={"verify_aud": False}` and validate `azp` instead. Do NOT weaken verification silently; if you change it, note why in the report.

- [ ] **Step 3: Create `apps/api/fleet_api/routers/whoami.py`** (protected route to exercise auth + RBAC)

```python
"""A protected demo route: returns the caller identity; requires CHAT permission."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from fleet_api.auth import CurrentUser
from fleet_api.rbac import Permission, require_permission

router = APIRouter(tags=["whoami"])


@router.get("/whoami")
async def whoami(
    user: CurrentUser = Depends(require_permission(Permission.CHAT)),
) -> dict[str, object]:
    return {"sub": user.sub, "roles": sorted(user.roles)}
```

- [ ] **Step 4: Mount the whoami router** — modify `apps/api/fleet_api/app.py`'s `create_app` to add:

```python
    from fleet_api.routers import whoami
    app.include_router(whoami.router)
```
(add alongside the existing `app.include_router(health.router)`.)

- [ ] **Step 5: Add the Keycloak testcontainer dependency** — in the root `pyproject.toml` dev-dependencies, add:

```toml
    "testcontainers[keycloak]>=4.8",
```
(testcontainers provides a Keycloak module; if the `[keycloak]` extra is unavailable in the installed version, use the generic `DockerContainer("quay.io/keycloak/keycloak:26.0")` with a `start-dev` command in the test instead — the test in Step 6 shows the generic approach to avoid extra-availability issues.)

- [ ] **Step 6: Write the integration test** `tests/integration/test_auth_rbac.py` (real Keycloak testcontainer, generic container to avoid extra-version issues)

```python
"""Integration test: 401 without/with a bad token, 200 with a valid member token,
403 when the token lacks the required permission — against a real Keycloak."""

from __future__ import annotations

import time

import httpx
import pytest
from fastapi.testclient import TestClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

REALM = {
    "realm": "fleet",
    "enabled": True,
    "sslRequired": "none",
    "clients": [
        {
            "clientId": "fleet-api",
            "enabled": True,
            "publicClient": True,
            "directAccessGrantsEnabled": True,
            "standardFlowEnabled": True,
            "redirectUris": ["*"],
        }
    ],
    "roles": {"realm": [{"name": "member"}, {"name": "builder"}]},
    "users": [
        {
            "username": "m",
            "enabled": True,
            "credentials": [{"type": "password", "value": "m", "temporary": False}],
            "realmRoles": ["member"],
        }
    ],
}


@pytest.fixture(scope="module")
def keycloak() -> str:
    import json
    import tempfile

    container = (
        DockerContainer("quay.io/keycloak/keycloak:26.0")
        .with_command("start-dev --import-realm")
        .with_env("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
        .with_env("KC_BOOTSTRAP_ADMIN_PASSWORD", "admin")
        .with_exposed_ports(8080)
    )
    # Write the realm to a temp dir mounted at the import path.
    tmp = tempfile.mkdtemp()
    with open(f"{tmp}/fleet-realm.json", "w", encoding="utf-8") as fh:
        json.dump(REALM, fh)
    container.with_volume_mapping(tmp, "/opt/keycloak/data/import", "ro")
    with container:
        wait_for_logs(container, "Listening on", timeout=120)
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8080)
        base = f"http://{host}:{port}"
        # Give the realm import a moment.
        for _ in range(30):
            try:
                r = httpx.get(f"{base}/realms/fleet/.well-known/openid-configuration", timeout=3)
                if r.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(2)
        yield base


def _token(base: str, username: str, password: str) -> str:
    resp = httpx.post(
        f"{base}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _client(base: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("FLEET_OIDC_ISSUER", f"{base}/realms/fleet")
    monkeypatch.setenv(
        "FLEET_OIDC_JWKS_URL",
        f"{base}/realms/fleet/protocol/openid-connect/certs",
    )
    monkeypatch.setenv("FLEET_OIDC_AUDIENCE", "account")
    from fleet_api.app import create_app

    return TestClient(create_app())


def test_401_without_token(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(keycloak, monkeypatch)
    assert client.get("/whoami").status_code == 401


def test_401_bad_token(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(keycloak, monkeypatch)
    r = client.get("/whoami", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_200_member_has_chat(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    token = _token(keycloak, "m", "m")
    client = _client(keycloak, monkeypatch)
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "member" in r.json()["roles"]
```

Note on `aud`: Keycloak's default access token has `aud` = `account`, so the test sets `FLEET_OIDC_AUDIENCE=account`. The 403 path is covered structurally by `require_permission` unit-level logic; a dedicated 403 case can be added if a role lacking CHAT is introduced, but member has CHAT so the 200 path is the realistic positive. If you want an explicit 403, add a route requiring `MANAGE_PLATFORM` and assert the member token gets 403 — include it.

- [ ] **Step 7: Add the explicit 403 case** — add a route requiring platform permission and a test. In `whoami.py` add:

```python
@router.get("/admin-only")
async def admin_only(
    user: CurrentUser = Depends(require_permission(Permission.MANAGE_PLATFORM)),
) -> dict[str, str]:
    return {"ok": "admin"}
```
And in the test file add:
```python
def test_403_member_lacks_admin(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    token = _token(keycloak, "m", "m")
    client = _client(keycloak, monkeypatch)
    r = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
```

- [ ] **Step 8: Sync, run the integration test (Docker + Keycloak), lint**

Run:
```
uv sync
uv run pytest tests/integration/test_auth_rbac.py -v
uv run ruff check apps/api tests
```
Expected: Keycloak container starts (~30-60s), realm imports; 401/401/200/403 all pass; ruff clean. If `aud` mismatch causes the 200 case to 401, adjust per the Step 2/6 notes and record why. Do NOT skip or xfail — report a real blocker instead.

- [ ] **Step 9: Commit**

```
git add -A
git commit -m "Add OIDC token validation and RBAC permission service with Keycloak-backed tests"
```

---

### Task 3: Cross-cutting middleware — trace_id, append-only audit, Redis rate limiter (1.4 part A)

**Files:**
- Create: `apps/api/fleet_api/otel.py` (trace_id helper + OTel logging exporter setup)
- Create: `apps/api/fleet_api/middleware.py` (TraceIdMiddleware, AuditMiddleware, RateLimitMiddleware)
- Create: `apps/api/fleet_api/audit.py` (append-only audit write helper)
- Modify: `apps/api/fleet_api/app.py` (wire middleware in order)
- Test: `tests/integration/test_middleware.py` (audit row w/ trace_id; 429 on rate limit)

**Interfaces:**
- Consumes: `fleet_api.db` (audit_log table from Stage B migration), `fleet_api.config` (redis_url, rate_limit_per_minute).
- Produces: middleware classes; `fleet_api.audit.write_audit(engine, *, actor, actor_type, action, entity, entity_id, trace_id)`; a per-request `trace_id` available on `request.state.trace_id` and echoed in the `X-Trace-Id` response header. Middleware order in `create_app`: TraceId (outermost) → Audit → RateLimit.

- [ ] **Step 1: Create `apps/api/fleet_api/otel.py`**

```python
"""OpenTelemetry setup (dev: logging exporter) and trace-id helpers."""

from __future__ import annotations

import uuid

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

_configured = False


def configure_tracing() -> None:
    """Install a console span exporter once (dev default per plan/TRD §14)."""
    global _configured
    if _configured:
        return
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _configured = True


def new_trace_id() -> str:
    """Generate a request trace id."""
    return uuid.uuid4().hex
```

- [ ] **Step 2: Create `apps/api/fleet_api/audit.py`**

```python
"""Append-only audit log writes."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def write_audit(
    engine: AsyncEngine,
    *,
    actor: str,
    actor_type: str,
    action: str,
    entity: str | None = None,
    entity_id: str | None = None,
    trace_id: str | None = None,
) -> None:
    """Insert one append-only audit row. Never updates or deletes."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO audit_log "
                "(actor, actor_type, action, entity, entity_id, trace_id) "
                "VALUES (:actor, :actor_type, :action, :entity, :entity_id, :trace_id)"
            ),
            {
                "actor": actor,
                "actor_type": actor_type,
                "action": action,
                "entity": entity,
                "entity_id": entity_id,
                "trace_id": trace_id,
            },
        )
```

- [ ] **Step 3: Create `apps/api/fleet_api/middleware.py`**

```python
"""Cross-cutting ASGI middleware: trace-id, append-only audit, and rate limiting."""

from __future__ import annotations

import time

import redis.asyncio as redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fleet_api.audit import write_audit
from fleet_api.db import get_engine
from fleet_api.otel import new_trace_id


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Assign a trace_id per request and echo it in the response header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or new_trace_id()
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Write an append-only audit row for each request, carrying the trace_id."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        trace_id = getattr(request.state, "trace_id", None)
        engine = get_engine()
        try:
            await write_audit(
                engine,
                actor=request.headers.get("X-User", "anonymous"),
                actor_type="user",
                action=f"{request.method} {request.url.path}",
                entity="http_request",
                entity_id=str(response.status_code),
                trace_id=trace_id,
            )
        finally:
            await engine.dispose()
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client rate limiting backed by Redis."""

    def __init__(self, app, redis_url: str, limit_per_minute: int) -> None:
        super().__init__(app)
        self._redis_url = redis_url
        self._limit = limit_per_minute

    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"ratelimit:{client}:{window}"
        r = redis.from_url(self._redis_url)
        try:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
        finally:
            await r.aclose()
        if count > self._limit:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited", "message": "too many requests"}},
            )
        return await call_next(request)
```

- [ ] **Step 4: Wire middleware in `create_app`** — modify `apps/api/fleet_api/app.py`. Add middleware so the effective order is TraceId (outermost) → Audit → RateLimit. In Starlette, the LAST `add_middleware` call is the OUTERMOST, so add in reverse:

```python
    from fleet_api.config import get_settings
    from fleet_api.middleware import (
        AuditMiddleware,
        RateLimitMiddleware,
        TraceIdMiddleware,
    )
    from fleet_api.otel import configure_tracing

    settings = get_settings()
    configure_tracing()
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.redis_url,
        limit_per_minute=settings.rate_limit_per_minute,
    )
    app.add_middleware(AuditMiddleware)
    app.add_middleware(TraceIdMiddleware)
```
(place this block in `create_app` before `return app`; keep error handlers + routers.)

- [ ] **Step 5: Write the integration test** `tests/integration/test_middleware.py` (Postgres + Redis testcontainers)

```python
"""Integration test: an audit row is written with the request trace_id, and the
rate limiter returns 429 past the configured limit."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="module")
def env(monkeypatch_module):  # see conftest note below
    ...


@pytest.fixture(scope="module")
def stack():
    with PostgresContainer("postgres:16") as pg, RedisContainer("redis:7") as rc:
        raw = pg.get_connection_url()  # postgresql+psycopg2://...
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        async_url = raw.replace("+psycopg2", "+asyncpg")
        redis_host = rc.get_container_host_ip()
        redis_port = rc.get_exposed_port(6379)
        os.environ["FLEET_DATABASE_URL"] = async_url
        os.environ["FLEET_REDIS_URL"] = f"redis://{redis_host}:{redis_port}/0"
        os.environ["FLEET_RATE_LIMIT_PER_MINUTE"] = "3"
        yield async_url


def test_audit_row_has_trace_id(stack: str) -> None:
    from fleet_api.app import create_app
    from fleet_api.db import get_engine

    client = TestClient(create_app())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    trace_id = resp.headers["X-Trace-Id"]
    assert trace_id

    import asyncio

    async def _check() -> None:
        engine = get_engine()
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("SELECT trace_id FROM audit_log ORDER BY id DESC LIMIT 1")
                )
            ).first()
            assert row is not None
            assert row[0] == trace_id
        await engine.dispose()

    asyncio.run(_check())


def test_rate_limit_429(stack: str) -> None:
    from fleet_api.app import create_app

    client = TestClient(create_app())
    # limit is 3/min; the 4th request in the same window is 429.
    codes = [client.get("/healthz").status_code for _ in range(5)]
    assert 429 in codes
```

Remove the unused `env`/`monkeypatch_module` fixture stub — it is a leftover; the real fixture is `stack`. (The implementer must delete the `env` fixture and its `...` body; it is shown here only to flag that no module-scoped monkeypatch is needed — use `os.environ` directly as `stack` does.)

- [ ] **Step 6: Run the middleware integration test + lint**

Run:
```
uv run pytest tests/integration/test_middleware.py -v
uv run ruff check apps/api tests
```
Expected: both tests pass (audit row carries the trace_id; 429 appears within 5 requests at limit 3). If the audit middleware errors because `get_engine()` opens too many connections, note it — but the dispose-per-request pattern should hold for this test volume.

- [ ] **Step 7: Commit**

```
git add -A
git commit -m "Add trace-id, append-only audit, and Redis rate-limit middleware"
```

---

### Task 4: OpenAPI → generated TypeScript client in packages/shared (1.4 part B)

**Files:**
- Create: `apps/api/fleet_api/export_openapi.py` (dump the app's OpenAPI schema to JSON)
- Create: `packages/shared/package.json`
- Create: `packages/shared/tsconfig.json`
- Create: `packages/shared/README.md` (how the client is generated)
- Create: `packages/shared/openapi.json` (generated artifact, committed)
- Create: `packages/shared/src/index.ts` (re-export the generated types)
- Modify: `Makefile` (add `openapi` + `client` targets)
- Modify: `pnpm-workspace.yaml` already includes `packages/*` (verify)

**Interfaces:**
- Consumes: `fleet_api.app.create_app` (for the schema).
- Produces: `make openapi` writes `packages/shared/openapi.json`; `make client` runs `openapi-typescript` to generate `packages/shared/src/schema.d.ts`; `packages/shared` exports the types for the web app (Stage-A `apps/web`) to import later.

- [ ] **Step 1: Create `apps/api/fleet_api/export_openapi.py`**

```python
"""Dump the FastAPI OpenAPI schema to a file for TS client generation."""

from __future__ import annotations

import json
import sys

from fleet_api.app import create_app


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "packages/shared/openapi.json"
    schema = create_app().openapi()
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create `packages/shared/package.json`**

```json
{
  "name": "@fleet/shared",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "src/index.ts",
  "scripts": {
    "gen": "openapi-typescript openapi.json -o src/schema.d.ts",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "openapi-typescript": "7.4.4",
    "typescript": "5.7.2"
  }
}
```

- [ ] **Step 3: Create `packages/shared/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "esnext",
    "moduleResolution": "bundler",
    "strict": true,
    "noEmit": true,
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts"]
}
```

- [ ] **Step 4: Create `packages/shared/src/index.ts`**

```typescript
// Re-export the generated OpenAPI types. Regenerate with `make client`.
export type { paths, components } from "./schema";
```

- [ ] **Step 5: Create `packages/shared/README.md`**

```markdown
# @fleet/shared

Generated TypeScript client + shared types for the Fleet web app.

- `make openapi` — dump the API schema to `openapi.json` (from FastAPI).
- `make client` — run `openapi-typescript` to produce `src/schema.d.ts`.

Do not hand-edit `schema.d.ts`; it is generated.
```

- [ ] **Step 6: Add Makefile targets** — append to the Makefile (and add `openapi client` to `.PHONY`):

```makefile
openapi: ## dump the API OpenAPI schema to packages/shared/openapi.json
	uv run python -m fleet_api.export_openapi packages/shared/openapi.json

client: openapi ## generate the TypeScript client from the OpenAPI schema
	pnpm --filter @fleet/shared install
	pnpm --filter @fleet/shared gen
```

- [ ] **Step 7: Generate the schema + client and typecheck**

Run (PowerShell, PATH refreshed):
```
make openapi
pnpm install
pnpm --filter @fleet/shared gen
pnpm --filter @fleet/shared typecheck
```
Expected: `openapi.json` written; `openapi-typescript` produces `src/schema.d.ts`; `tsc --noEmit` exits 0. Commit both `openapi.json` and the generated `schema.d.ts` (they are the client contract).

- [ ] **Step 8: Commit**

```
git add -A
git commit -m "Generate TypeScript client from the API OpenAPI schema in packages/shared"
```

---

### Task 5: Helm umbrella chart + values-dev + k3d bootstrap (1.5)

**Files:**
- Create: `infra/helm/fleet/Chart.yaml`
- Create: `infra/helm/fleet/values.yaml`
- Create: `infra/helm/fleet/values-dev.yaml`
- Create: `infra/helm/fleet/templates/_helpers.tpl`
- Create: `infra/helm/fleet/templates/{postgres,redis,qdrant,minio,keycloak,prometheus,grafana,loki}.yaml` (Deployment+Service per service; a subset that mirrors the 1.1 stack essentials for a k3d bring-up)
- Create: `infra/helm/fleet/templates/NOTES.txt`
- Create: `infra/k3d/cluster.yaml` (k3d cluster config)
- Create: `infra/k3d/up.sh` (create cluster + helm install)
- Modify: `Makefile` (add `k3d-up`, `k3d-down`, `helm-lint`)

**Interfaces:**
- Consumes: nothing from the app image yet (the chart brings up the data-plane + observability stack, mirroring 1.1; the api image deploys in a later sprint).
- Produces: `make helm-lint` (lints the chart); `make k3d-up` (creates a k3d cluster and `helm install`s the chart so the 1.1-equivalent stack runs on k3d); `make k3d-down` (deletes the cluster).

- [ ] **Step 1: Create `infra/helm/fleet/Chart.yaml`**

```yaml
apiVersion: v2
name: fleet
description: Fleet platform umbrella chart (dev/test/staging/prod via per-env values).
type: application
version: 0.1.0
appVersion: "0.1.0"
```

- [ ] **Step 2: Create `infra/helm/fleet/values.yaml`** (defaults; images pinned, mirror the 1.1 stack subset)

```yaml
# Default values. Per-env overrides live in values-<env>.yaml.
namespace: fleet

postgres:
  image: postgres:16
  user: fleet
  password: fleet_dev_pw
  db: fleet

redis:
  image: redis:7

qdrant:
  image: qdrant/qdrant:v1.12.4

minio:
  image: minio/minio:RELEASE.2024-12-13T22-19-12Z
  rootUser: fleet
  rootPassword: fleet_dev_pw

keycloak:
  image: quay.io/keycloak/keycloak:26.0
  adminUser: admin
  adminPassword: admin

prometheus:
  image: prom/prometheus:v3.0.1

grafana:
  image: grafana/grafana:11.4.0
  adminUser: admin
  adminPassword: admin

loki:
  image: grafana/loki:3.3.2
```

- [ ] **Step 3: Create `infra/helm/fleet/values-dev.yaml`**

```yaml
# Dev (k3d) overrides. Small footprint; ephemeral storage.
namespace: fleet-dev
```

- [ ] **Step 4: Create `infra/helm/fleet/templates/_helpers.tpl`**

```
{{- define "fleet.namespace" -}}
{{- .Values.namespace | default "fleet" -}}
{{- end -}}
```

- [ ] **Step 5: Create one template per service.** Each is a minimal Deployment + Service. Example `infra/helm/fleet/templates/postgres.yaml` (write the analogous file for redis, qdrant, minio, keycloak, prometheus, grafana, loki — same shape, service-specific image/port/env):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: {{ include "fleet.namespace" . }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: {{ .Values.postgres.image }}
          env:
            - name: POSTGRES_USER
              value: {{ .Values.postgres.user | quote }}
            - name: POSTGRES_PASSWORD
              value: {{ .Values.postgres.password | quote }}
            - name: POSTGRES_DB
              value: {{ .Values.postgres.db | quote }}
          ports:
            - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: {{ include "fleet.namespace" . }}
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

Ports for the others: redis 6379, qdrant 6333, minio 9000 (+9001, command `server /data --console-address ":9001"`), keycloak 8080 (command `["start-dev"]`), prometheus 9090, grafana 3000 (env GF_SECURITY_ADMIN_USER/PASSWORD), loki 3100. Keep each minimal — no PVCs (ephemeral is fine for k3d dev), no healthchecks required for the bring-up AC.

- [ ] **Step 6: Create `infra/helm/fleet/templates/NOTES.txt`**

```
Fleet dev stack installed into namespace {{ include "fleet.namespace" . }}.
Run: kubectl -n {{ include "fleet.namespace" . }} get pods
```

- [ ] **Step 7: Create `infra/k3d/cluster.yaml`**

```yaml
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: fleet
servers: 1
agents: 1
```

- [ ] **Step 8: Create `infra/k3d/up.sh`**

```bash
#!/usr/bin/env bash
# Create the local k3d cluster and install the Fleet umbrella chart.
set -euo pipefail

CLUSTER=fleet
NS=fleet-dev

if ! k3d cluster list | grep -q "^${CLUSTER} "; then
  k3d cluster create --config infra/k3d/cluster.yaml
fi

kubectl create namespace "${NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install fleet infra/helm/fleet \
  -f infra/helm/fleet/values-dev.yaml \
  --namespace "${NS}"

echo "waiting for pods..."
kubectl -n "${NS}" wait --for=condition=available --timeout=300s deploy --all || true
kubectl -n "${NS}" get pods
```

- [ ] **Step 9: Add Makefile targets** (append; add `k3d-up k3d-down helm-lint` to `.PHONY`):

```makefile
helm-lint: ## lint the umbrella chart
	helm lint infra/helm/fleet -f infra/helm/fleet/values-dev.yaml

k3d-up: ## create a local k3d cluster and install the chart
	bash infra/k3d/up.sh

k3d-down: ## delete the local k3d cluster
	k3d cluster delete fleet
```

- [ ] **Step 10: Static-validate the chart**

Run (PowerShell, PATH refreshed):
```
helm lint infra/helm/fleet -f infra/helm/fleet/values-dev.yaml
helm template fleet infra/helm/fleet -f infra/helm/fleet/values-dev.yaml
```
Expected: `helm lint` passes (0 failures); `helm template` renders valid multi-doc YAML for all services. Fix any template error before committing.

- [ ] **Step 11: Commit**

```
git add -A
git commit -m "Add Helm umbrella chart, dev values, and k3d bootstrap scripts"
```

---

### Task 6: Live-verify k3d bring-up + full gate (1.5 AC)

**Files:** none (verification task; ends with a `docs/PROGRESS.md` entry).

**Interfaces:**
- Consumes: the chart + k3d scripts (Task 5), Makefile.
- Produces: proof `make k3d-up` brings up the 1.1-equivalent stack on a real local k3d cluster (the 1.5 AC).

- [ ] **Step 1: Bring up the cluster**

Run (PowerShell, PATH refreshed, Docker running):
```
make k3d-up
```
Expected: k3d creates the `fleet` cluster; helm installs; pods for postgres/redis/qdrant/minio/keycloak/prometheus/grafana/loki reach Running. This pulls images the first time (several minutes).

- [ ] **Step 2: Verify pods are Running**

Run: `kubectl -n fleet-dev get pods`
Expected: all service pods `Running` (or investigate any `CrashLoopBackOff`/`Pending` — report root cause; do not silently patch).

- [ ] **Step 3: Tear down**

Run: `make k3d-down`
Expected: cluster deleted cleanly.

- [ ] **Step 4: Run the full local gate**

Run: `make lint` then `make test` (unit + all integration).
Expected: green. (Integration now includes auth+middleware Keycloak/Postgres/Redis containers — this is slower; that's expected.)

- [ ] **Step 5: Write the `docs/PROGRESS.md` entry** for 1.3+1.4+1.5 (append-only): what was built, AC results (401/403 tests, audit+trace_id, 429, k3d bring-up), issues, notes.

- [ ] **Step 6: Commit**

```
git add docs/PROGRESS.md
git commit -m "Log Stage C completion with auth, middleware, and k3d verification"
```

---

## Self-Review

**1. Spec coverage:**
- 1.3 app factory + OIDC + RBAC + error model + health/readiness → Tasks 1 (factory/errors/health) + 2 (OIDC/RBAC). AC "integration tests cover 401/403" → Task 2 (real Keycloak, 401×2 + 200 + 403).
- 1.4 audit + OTel trace_id + Redis rate limit + OpenAPI→TS client → Task 3 (audit/trace/rate-limit) + Task 4 (TS client). AC "audit row with trace_id; 429 test; traces exported" → Task 3 tests + otel console exporter.
- 1.5 Helm chart + k3d + values-dev → Task 5. AC "make k3d-up brings up the 1.1 stack" → Task 6 live verify.
- Branch protection (GitHub side of 1.0) + Sprint close are handled by the controller AFTER Task 6 (not subagent tasks): enable protection via gh, write sprint-1 report, refresh graph.

**2. Placeholder scan:** No TBD/implement-later. The `env`/`monkeypatch_module` stub in Task 3 Step 5 is explicitly flagged for deletion (it's a note, not shipped code) — the implementer removes it. The Helm templates are described once with the exact shape + per-service parameters rather than repeating 8 near-identical blocks; this is a deliberate DRY instruction, and each service's image/port/env is given explicitly.

**3. Type/name consistency:** `CurrentUser` (auth.py) is consumed by rbac.py and whoami.py with the same fields (sub, roles). `get_current_user` name is identical across auth.py, rbac.py, whoami.py. `Permission` enum members (CHAT, MANAGE_PLATFORM, …) match between rbac.py's matrix and whoami.py's usage. `FLEET_` env prefix (config.py) matches the env vars set in tests (FLEET_OIDC_ISSUER, FLEET_DATABASE_URL, FLEET_REDIS_URL, FLEET_RATE_LIMIT_PER_MINUTE). `write_audit` signature (audit.py) matches its call in middleware.py. Middleware order documented explicitly (Starlette last-added-is-outermost). `audit_log` columns used by write_audit match the Stage-B migration exactly (actor, actor_type, action, entity, entity_id, trace_id). Helm service names (postgres/redis/…) match the values.yaml keys.

**Known risk flagged for implementers:** Keycloak `aud` claim. The default access token's `aud` is often `account`, not `fleet-api`. The plan sets `FLEET_OIDC_AUDIENCE=account` in the integration test and notes that if the 200 case 401s on audience, the implementer adjusts (validate `azp` or set the audience to what the token actually carries) and records why — never weakening verification silently. Task 2 Step 8 runs this against a real Keycloak, so the mismatch surfaces during implementation, not in CI.
