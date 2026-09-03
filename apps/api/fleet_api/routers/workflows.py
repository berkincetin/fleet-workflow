"""Workflow catalog: run/monitor real n8n automations from the web UI (task
6.5.3, TRD §12 — "Workflow catalog" promoted from P2 to CORE).

The catalog is a friendly proxy over n8n's own REST API + webhooks (n8n_client.py,
workflows_catalog.py): it never re-implements automation logic, it only surfaces
state and forwards trigger requests. When n8n is unreachable (stack not up, or
this specific container down) every endpoint still returns 200 with
`reachable: false` so the UI can render a plain-language down-state rather than
an error page — that down state is an expected, demoable condition here.

RBAC: viewing the catalog is CHAT (any logged-in user); running the
invoice-intake workflow is UPLOAD (the external write it produces is still
HITL-gated by the approval queue, same trust level as a document upload);
running weekly-summary and activate/deactivate are MANAGE_AGENTS (weekly-summary
posts to Slack immediately with no approval gate, and toggling a workflow's
active state is an operational action).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fleet_api.config import Settings, get_settings
from fleet_api.n8n_client import N8nClient, N8nResult
from fleet_api.rbac import Permission, require_permission
from fleet_api.workflows_catalog import CATALOG, WorkflowMeta
from pydantic import BaseModel

router = APIRouter(prefix="/v1/workflows", tags=["workflows"])


def get_n8n_client(settings: Settings = Depends(get_settings)) -> N8nClient:  # noqa: B008
    return N8nClient(base_url=settings.n8n_base_url, api_key=settings.n8n_api_key or None)


class WorkflowOut(BaseModel):
    slug: str
    kind: str
    reachable: bool
    auth_error: bool = False
    active: bool | None = None
    last_run: dict[str, Any] | None = None


def _execution_status(row: dict[str, Any]) -> str:
    """Derive a run's outcome from what n8n 1.71's executions list actually
    carries.

    That list omits `status` on each row and reports only `finished` +
    `stoppedAt`. Passing the missing field straight through rendered every
    completed run as a red "unknown" badge on the Home dashboard (task 13.1).
    The mapping matches what n8n's own `?status=` filter concludes for the same
    rows: finished -> success; not finished but already stopped -> error
    (the run ended at a failing node); not finished and still open -> running.
    """
    status = row.get("status")
    if isinstance(status, str) and status:
        return status
    if row.get("finished"):
        return "success"
    return "error" if row.get("stoppedAt") else "running"


def _find_workflow(data: list[dict[str, Any]], n8n_name: str) -> dict[str, Any] | None:
    for wf in data:
        if wf.get("name") == n8n_name:
            return wf
    return None


async def _catalog_entry(meta: WorkflowMeta, client: N8nClient) -> WorkflowOut:
    listing = await client.list_workflows()
    if not listing.reachable:
        return WorkflowOut(slug=meta.slug, kind=meta.kind, reachable=False)
    if listing.auth_error:
        return WorkflowOut(slug=meta.slug, kind=meta.kind, reachable=True, auth_error=True)

    workflows = listing.data.get("data", []) if isinstance(listing.data, dict) else []
    wf = _find_workflow(workflows, meta.n8n_name)
    if wf is None:
        return WorkflowOut(slug=meta.slug, kind=meta.kind, reachable=True, active=None)

    last_run: dict[str, Any] | None = None
    executions = await client.list_executions(str(wf["id"]), limit=1)
    if executions.reachable and isinstance(executions.data, dict):
        rows = executions.data.get("data", [])
        if rows:
            last_run = {"status": _execution_status(rows[0]), "at": rows[0].get("startedAt")}

    return WorkflowOut(
        slug=meta.slug, kind=meta.kind, reachable=True, active=bool(wf.get("active")),
        last_run=last_run,
    )


@router.get("")
async def list_catalog(
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> list[WorkflowOut]:
    return [await _catalog_entry(meta, client) for meta in CATALOG.values()]


class RunResultOut(BaseModel):
    status: str  # "accepted" | "workflow_inactive" | "n8n_unreachable"
    detail: str | None = None


def _get_meta(slug: str) -> WorkflowMeta:
    meta = CATALOG.get(slug)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"unknown workflow: {slug}")
    return meta


async def _require_active_and_reachable(
    meta: WorkflowMeta, client: N8nClient
) -> RunResultOut | None:
    """Returns a RunResultOut early-exit response, or None if the workflow is
    confirmed active and reachable and the caller should proceed to trigger it."""
    listing = await client.list_workflows()
    if not listing.reachable:
        return RunResultOut(status="n8n_unreachable", detail=listing.error)
    workflows = listing.data.get("data", []) if isinstance(listing.data, dict) else []
    wf = _find_workflow(workflows, meta.n8n_name)
    if wf is None or not wf.get("active"):
        return RunResultOut(
            status="workflow_inactive",
            detail="workflow is not active in n8n — run `make n8n-import` or activate it",
        )
    return None


_MAX_INVOICE_IMAGE_BYTES = 10 * 1024 * 1024
_ALLOWED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}


@router.post("/invoice-intake/run", status_code=202)
async def run_invoice_intake(
    file: UploadFile,
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RunResultOut:
    import base64

    meta = _get_meta("invoice-intake")

    if file.content_type not in _ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"unsupported image type: {file.content_type}",
        )
    data = await file.read()
    if len(data) > _MAX_INVOICE_IMAGE_BYTES:
        raise HTTPException(status_code=422, detail="image too large (max 10MB)")

    early_exit = await _require_active_and_reachable(meta, client)
    if early_exit is not None:
        return early_exit

    result: N8nResult = await client.trigger_webhook_json(
        meta.run_webhook_path, {"image_base64": base64.b64encode(data).decode("ascii")}
    )
    if not result.reachable:
        return RunResultOut(status="n8n_unreachable", detail=result.error)
    return RunResultOut(status="accepted", detail="fatura kuyruğa alındı — Onaylar'ı kontrol edin")


@router.post("/weekly-summary/run", status_code=202)
async def run_weekly_summary(
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RunResultOut:
    meta = _get_meta("weekly-summary")
    early_exit = await _require_active_and_reachable(meta, client)
    if early_exit is not None:
        return early_exit

    result = await client.trigger_webhook_json(meta.run_webhook_path, {})
    if not result.reachable:
        return RunResultOut(status="n8n_unreachable", detail=result.error)
    return RunResultOut(status="accepted")


class ActiveIn(BaseModel):
    active: bool


@router.post("/{slug}/activate")
async def activate_workflow(
    slug: str,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RunResultOut:
    return await _set_active(slug, True, client)


@router.post("/{slug}/deactivate")
async def deactivate_workflow(
    slug: str,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RunResultOut:
    return await _set_active(slug, False, client)


async def _set_active(slug: str, active: bool, client: N8nClient) -> RunResultOut:
    meta = _get_meta(slug)
    listing = await client.list_workflows()
    if not listing.reachable:
        return RunResultOut(status="n8n_unreachable", detail=listing.error)
    workflows = listing.data.get("data", []) if isinstance(listing.data, dict) else []
    wf = _find_workflow(workflows, meta.n8n_name)
    if wf is None:
        raise HTTPException(status_code=404, detail="workflow not found in n8n — import it first")

    result = await client.set_active(str(wf["id"]), active)
    if not result.reachable:
        return RunResultOut(status="n8n_unreachable", detail=result.error)
    return RunResultOut(status="accepted")
