"""Static catalog of the local stack's services + how to probe each (task 13.3).

The long-deferred System-health screen (TRD §12 Admin CORE, plan task 7.3).
Same split as `workflows_catalog.py`: this module carries only what the API
needs to *find and check* a service — its local URL, the probe that decides
whether it is up, and which environment variables hold its dev credentials.
The friendly title and the one-sentence "what it is for" live in the web app's
i18n messages (keyed by `name`), so they are translated like every other
string rather than hard-coded English here.

Credentials are read from the environment at request time and **never**
committed: this module stores variable *names*, not values, and the router
only ever emits masked forms unless a `platform_admin` explicitly asks for a
reveal.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum


class ProbeKind(StrEnum):
    """How a service's liveness is decided."""

    HTTP = "http"  # GET probe_url, any 2xx/3xx/401/403 counts as "up"
    POSTGRES = "postgres"  # SELECT 1 over the API's own engine
    REDIS = "redis"  # PING
    ARQ = "arq"  # arq worker heartbeat key in Redis


@dataclass(frozen=True)
class ServiceCredential:
    """One dev credential pair for a service.

    `username_env`/`secret_env` name environment variables; `default_username`
    covers the compose defaults (`${POSTGRES_USER:-fleet}`) so the screen still
    shows the value actually in effect when `.env` leaves the var unset.
    """

    label: str
    secret_env: str
    username_env: str | None = None
    default_username: str | None = None
    default_secret: str | None = None

    def username(self) -> str | None:
        if self.username_env:
            return os.environ.get(self.username_env) or self.default_username
        return self.default_username

    def secret(self) -> str | None:
        return os.environ.get(self.secret_env) or self.default_secret


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    group: str  # "core" | "observability" | "automation" | "provider" | "worker"
    probe: ProbeKind
    #: What a human opens in a browser (empty when the service has no UI).
    url: str = ""
    #: What the API actually probes; falls back to `url`.
    probe_url: str = ""
    #: Not part of `make dev`'s default profile (Ollama) or run on the host
    #: (arq) — down is a normal state for these, so they never turn red.
    optional: bool = False
    credentials: tuple[ServiceCredential, ...] = field(default_factory=tuple)

    def effective_probe_url(self) -> str:
        return self.probe_url or self.url


CATALOG: tuple[ServiceSpec, ...] = (
    ServiceSpec(
        name="postgres",
        group="core",
        probe=ProbeKind.POSTGRES,
        url="postgresql://localhost:5432/fleet",
        credentials=(
            ServiceCredential(
                label="database",
                username_env="POSTGRES_USER",
                secret_env="POSTGRES_PASSWORD",
                default_username="fleet",
                default_secret="fleet_dev_pw",
            ),
        ),
    ),
    ServiceSpec(
        name="redis",
        group="core",
        probe=ProbeKind.REDIS,
        url="redis://localhost:6379",
    ),
    ServiceSpec(
        name="qdrant",
        group="core",
        probe=ProbeKind.HTTP,
        url="http://localhost:6333/dashboard",
        probe_url="http://localhost:6333/readyz",
    ),
    ServiceSpec(
        name="minio",
        group="core",
        probe=ProbeKind.HTTP,
        url="http://localhost:9001",
        probe_url="http://localhost:9000/minio/health/live",
        credentials=(
            ServiceCredential(
                label="console",
                username_env="MINIO_ROOT_USER",
                secret_env="MINIO_ROOT_PASSWORD",
                default_username="fleet",
                default_secret="fleet_dev_pw",
            ),
        ),
    ),
    ServiceSpec(
        name="keycloak",
        group="core",
        probe=ProbeKind.HTTP,
        url="http://localhost:8080",
        probe_url="http://localhost:8080/realms/fleet/.well-known/openid-configuration",
        credentials=(
            ServiceCredential(
                label="admin console",
                username_env="KEYCLOAK_ADMIN",
                secret_env="KEYCLOAK_ADMIN_PASSWORD",
                default_username="admin",
                default_secret="admin",
            ),
        ),
    ),
    ServiceSpec(
        name="litellm",
        group="provider",
        probe=ProbeKind.HTTP,
        url="http://localhost:4000",
        probe_url="http://localhost:4000/health/liveliness",
        credentials=(
            ServiceCredential(
                label="master key",
                secret_env="LITELLM_MASTER_KEY",
                default_secret="sk-fleet-dev-master",
            ),
        ),
    ),
    ServiceSpec(
        name="ollama",
        group="provider",
        probe=ProbeKind.HTTP,
        url="http://localhost:11434",
        probe_url="http://localhost:11434/api/tags",
        optional=True,
    ),
    ServiceSpec(
        name="langfuse",
        group="observability",
        probe=ProbeKind.HTTP,
        url="http://localhost:3001",
        probe_url="http://localhost:3001/api/public/health",
        credentials=(
            ServiceCredential(
                label="sign-in",
                username_env="LANGFUSE_INIT_USER_EMAIL",
                secret_env="LANGFUSE_INIT_USER_PASSWORD",
                default_username="admin@fleet.dev",
                default_secret="fleet_dev_pw",
            ),
            ServiceCredential(
                label="project secret key",
                secret_env="LANGFUSE_SECRET_KEY",
                default_secret="sk-lf-fleet-dev",
            ),
        ),
    ),
    ServiceSpec(
        name="prometheus",
        group="observability",
        probe=ProbeKind.HTTP,
        url="http://localhost:9090",
        probe_url="http://localhost:9090/-/healthy",
    ),
    ServiceSpec(
        name="grafana",
        group="observability",
        probe=ProbeKind.HTTP,
        url="http://localhost:3002",
        probe_url="http://localhost:3002/api/health",
        credentials=(
            ServiceCredential(
                label="admin console",
                username_env="GF_SECURITY_ADMIN_USER",
                secret_env="GF_SECURITY_ADMIN_PASSWORD",
                default_username="admin",
                default_secret="admin",
            ),
        ),
    ),
    ServiceSpec(
        name="loki",
        group="observability",
        probe=ProbeKind.HTTP,
        url="http://localhost:3100",
        probe_url="http://localhost:3100/ready",
    ),
    ServiceSpec(
        name="promtail",
        group="observability",
        probe=ProbeKind.HTTP,
        url="http://localhost:9080/targets",
        probe_url="http://localhost:9080/ready",
    ),
    ServiceSpec(
        name="alertmanager",
        group="observability",
        probe=ProbeKind.HTTP,
        url="http://localhost:9093",
        probe_url="http://localhost:9093/-/healthy",
    ),
    ServiceSpec(
        name="mailpit",
        group="core",
        probe=ProbeKind.HTTP,
        url="http://localhost:8025",
        probe_url="http://localhost:8025/readyz",
    ),
    ServiceSpec(
        name="n8n-main",
        group="automation",
        # Humans go through the SSO proxy at :5679; the loopback REST port the
        # Fleet API uses is what we actually probe.
        probe=ProbeKind.HTTP,
        url="http://localhost:5679",
        probe_url="http://localhost:5678/healthz",
    ),
    ServiceSpec(
        name="n8n-worker",
        group="worker",
        probe=ProbeKind.HTTP,
        # QUEUE_HEALTH_CHECK_ACTIVE publishes the worker's own /healthz on a
        # loopback-only port (compose, task 13.3) — without it a queue-mode
        # worker has no health surface at all and "is the worker up?" would be
        # a guess.
        probe_url="http://localhost:5680/healthz",
    ),
    ServiceSpec(
        name="arq",
        group="worker",
        probe=ProbeKind.ARQ,
        # Run on the host (`uv run arq fleet_rag.ingest.worker.WorkerSettings`),
        # not in compose — so "not running" is a normal dev state, not a fault.
        optional=True,
    ),
)

CATALOG_BY_NAME: dict[str, ServiceSpec] = {s.name: s for s in CATALOG}


def mask_secret(value: str | None) -> str | None:
    """Masked form of a secret — enough to recognise it, never enough to use it.

    Short values are fully masked: revealing 2 of 6 characters is a meaningful
    fraction of the search space, revealing 2 of 40 is not.
    """
    if value is None:
        return None
    if len(value) < 10:
        return "•" * 8
    return f"{value[:2]}{'•' * 6}{value[-2:]}"
