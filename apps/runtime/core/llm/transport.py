"""HTTP transport to the LiteLLM proxy (task 2.3).

The proxy exposes an OpenAI-compatible ``/chat/completions`` surface and owns the
retries + fallback chain (§4.4). This transport is a thin async HTTP client over
it — it deliberately does NOT import any provider SDK (CLAUDE.md rule 1); the
proxy is the only thing that talks to providers.

Trace correlation (TRD §6): the caller's ``trace_id`` and agent/user/dept are
forwarded as LiteLLM metadata so the proxy's Langfuse callback tags the trace.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx


def _build_metadata(kwargs: dict[str, Any]) -> dict[str, Any]:
    """trace_id/agent_id/user_id/dept_id passthrough (TRD §6 trace correlation)
    plus, when `redact_langfuse` is set, litellm's own per-request redaction
    switch (TRD §8: "detected identifiers masked in logs/traces always").
    This is read from `litellm_params.metadata.headers` server-side (see
    litellm/litellm_core_utils/redact_messages.py) — a JSON-body convention
    litellm uses to mimic a header, NOT an actual HTTP request header (real
    header forwarding is a separate, disabled-by-default proxy setting that
    populates a different field entirely — confirmed against the proxy's own
    source rather than assumed, task 8.4)."""
    metadata = {
        k: kwargs[k]
        for k in ("trace_id", "agent_id", "user_id", "dept_id")
        if kwargs.get(k) is not None
    }
    if kwargs.pop("redact_langfuse", False):
        # litellm's check is `is not True` (identity, not truthy) — a JSON
        # string "true" would NOT satisfy it; must be the real boolean.
        metadata["headers"] = {"litellm-enable-message-redaction": True}
    return metadata


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
        metadata = _build_metadata(kwargs)
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

    async def embed(
        self, *, model: str, input: list[str], **kwargs: Any
    ) -> dict[str, Any]:
        """Send an embeddings request; raise for non-2xx (mapped to GatewayError)."""
        url = f"{self._base_url}/embeddings"
        headers = {"Authorization": f"Bearer {self._master_key}"}
        payload: dict[str, Any] = {"model": model, "input": input}

        metadata = _build_metadata(kwargs)
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            body: dict[str, Any] = resp.json()
            return body

    async def stream_complete(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a completion (TRD §5 "streaming everywhere"). Yields one dict
        per SSE chunk: `{"model": ..., "delta": <text>, "usage": <final usage
        block, only on the last chunk>}`. `stream_options.include_usage` asks
        the (OpenAI-compatible) proxy for that final usage-only chunk."""
        url = f"{self._base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._master_key}"}

        metadata = _build_metadata(kwargs)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        for passthrough in ("max_tokens", "temperature", "tools", "response_format"):
            if passthrough in kwargs:
                payload[passthrough] = kwargs[passthrough]
        if metadata:
            payload["metadata"] = metadata

        async def _iter() -> AsyncIterator[dict[str, Any]]:
            async with httpx.AsyncClient(timeout=self._timeout) as client, client.stream(
                "POST", url, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[len("data:") :].strip()
                    if raw == "[DONE]":
                        break
                    event = json.loads(raw)
                    choices = event.get("choices") or [{}]
                    delta_text = choices[0].get("delta", {}).get("content", "") or ""
                    yield {
                        "model": event.get("model", model),
                        "delta": delta_text,
                        "usage": event.get("usage"),
                    }

        return _iter()
