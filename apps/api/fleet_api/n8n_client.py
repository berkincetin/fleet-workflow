"""Thin async client over the n8n REST + webhook surfaces (task 6.5.3).

Reached over the loopback port added in 6.5.4 (compose `n8n-main` publishes
127.0.0.1:5678) — the Fleet API talks to n8n directly, never through the
oauth2-proxy SSO gate at :5679 which is for human editor access only.

This client never raises on a connection failure: every method returns an
`N8nResult` with `reachable=False` instead, because the workflows router
(routers/workflows.py) needs to render a plain-language "otomasyon şu an
kapalı" state rather than a 500 when n8n (or the whole compose stack) isn't
running — the down-state is an expected, demoable condition, not an error.
Auth failures (bad/missing N8N_API_KEY) are distinguished from a plain
connection failure so an admin can tell "n8n is down" from "n8n is up but
misconfigured".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class N8nResult:
    reachable: bool
    auth_error: bool = False
    data: Any = None
    error: str | None = None


@dataclass
class N8nClient:
    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 5.0

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> N8nResult:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, headers=self._headers(), timeout=self.timeout_seconds
            ) as client:
                resp = await client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            return N8nResult(reachable=False, error=str(exc))

        if resp.status_code in (401, 403):
            return N8nResult(reachable=True, auth_error=True, error=resp.text)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return N8nResult(reachable=True, error=str(exc))

        data = None
        if resp.content:
            try:
                data = resp.json()
            except ValueError:
                data = resp.text
        return N8nResult(reachable=True, data=data)

    async def list_workflows(self) -> N8nResult:
        return await self._request("GET", "/api/v1/workflows")

    async def get_workflow(self, workflow_id: str) -> N8nResult:
        return await self._request("GET", f"/api/v1/workflows/{workflow_id}")

    async def set_active(self, workflow_id: str, active: bool) -> N8nResult:
        suffix = "activate" if active else "deactivate"
        return await self._request("POST", f"/api/v1/workflows/{workflow_id}/{suffix}")

    async def list_executions(self, workflow_id: str, *, limit: int = 1) -> N8nResult:
        return await self._request(
            "GET", "/api/v1/executions", params={"workflowId": workflow_id, "limit": limit}
        )

    async def trigger_webhook_json(self, path: str, body: dict[str, Any]) -> N8nResult:
        return await self._request("POST", f"/webhook/{path}", json=body)

    async def trigger_webhook_multipart(
        self, path: str, files: dict[str, tuple[str, bytes, str]]
    ) -> N8nResult:
        return await self._request("POST", f"/webhook/{path}", files=files)
