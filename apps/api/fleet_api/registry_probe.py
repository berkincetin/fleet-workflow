"""Connectivity/capability smoke probe for the model registry (task 2.2).

Runs a real minimal completion against a model *through the LiteLLM proxy* (never
a provider SDK — CLAUDE.md rule 1 applies to the whole platform; the proxy is the
gateway) and reports reachability + whether the declared capabilities held. The
pure fold of this result into a row lives in `registry.py`; this module is the
transport and is exercised in the Docker integration pass.
"""

from __future__ import annotations

import time

import httpx
from fleet_api.registry import ModelDraft, SmokeResult


async def probe_model(
    draft: ModelDraft,
    *,
    proxy_base_url: str,
    master_key: str,
    timeout: float = 30.0,  # noqa: ASYNC109 — passed straight to httpx's own timeout
) -> SmokeResult:
    """Send a 1-token completion to `draft.litellm_model_id` via the proxy.

    Reachable + a well-formed choice back ⇒ reachable=True. If the draft declares
    `tools`/`json`, we only assert the basic round-trip here (deep capability
    assertions are left to per-agent evals); a malformed/empty response marks
    capabilities_ok=False so the row lands `degraded` rather than `active`.
    """
    url = f"{proxy_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {master_key}"}
    payload = {
        "model": draft.name,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        return SmokeResult(
            reachable=False, capabilities_ok=False, detail=f"transport error: {exc}"
        )

    latency_ms = int((time.monotonic() - start) * 1000)
    if resp.status_code != 200:
        return SmokeResult(
            reachable=False,
            capabilities_ok=False,
            detail=f"HTTP {resp.status_code}: {resp.text[:200]}",
            latency_ms=latency_ms,
        )

    try:
        body = resp.json()
        choices = body.get("choices") or []
        capabilities_ok = bool(choices) and "message" in choices[0]
        detail = "ok" if capabilities_ok else "reachable but response had no choices"
    except ValueError:
        capabilities_ok = False
        detail = "reachable but response was not JSON"

    return SmokeResult(
        reachable=True,
        capabilities_ok=capabilities_ok,
        detail=detail,
        latency_ms=latency_ms,
    )
