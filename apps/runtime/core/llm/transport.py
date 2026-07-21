"""HTTP transport to the LiteLLM proxy (task 2.3).

The proxy exposes an OpenAI-compatible ``/chat/completions`` surface and owns the
retries + fallback chain (§4.4). This transport is a thin async HTTP client over
it — it deliberately does NOT import any provider SDK (CLAUDE.md rule 1); the
proxy is the only thing that talks to providers.

Trace correlation (TRD §6): the caller's ``trace_id`` and agent/user/dept are
forwarded as LiteLLM metadata so the proxy's Langfuse callback tags the trace.
"""

from __future__ import annotations

from typing import Any

import httpx


class ProxyTransport:
    """Async transport that POSTs chat completions to the LiteLLM proxy."""

    def __init__(
        self, *, base_url: str, master_key: str, timeout: float = 60.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._master_key = master_key
        self._timeout = timeout

    async def complete(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> dict[str, Any]:
        """Send a completion; raise for a non-2xx so the client maps it to GatewayError."""
        url = f"{self._base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._master_key}"}

        metadata = {
            k: kwargs[k]
            for k in ("trace_id", "agent_id", "user_id", "dept_id")
            if kwargs.get(k) is not None
        }
        payload: dict[str, Any] = {"model": model, "messages": messages}
        for passthrough in ("max_tokens", "temperature", "tools", "response_format"):
            if passthrough in kwargs:
                payload[passthrough] = kwargs[passthrough]
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            body: dict[str, Any] = resp.json()
            return body
