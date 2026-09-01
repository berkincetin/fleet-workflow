"""Push a feedback score onto a Langfuse trace (TRD §6, task 4.3 AC: "👍/👎
lands in Langfuse"); post-hoc redact a trace's content (task 8.4 AC:
"detected identifiers appear masked in ... Langfuse for a seeded PII
conversation").

Thin HTTP client over Langfuse's public /api/public/scores endpoint, using the
same public/secret keypair LiteLLM's Langfuse callback authenticates with
(§6 — this repo's dev default is pk-lf-fleet-dev/sk-lf-fleet-dev, baked into
compose). The trace_id must be the SAME id the gateway client forwarded as
`metadata.trace_id` on the original call (core.llm.client) — that's what lets
a score land on the exact trace the message came from rather than one
Langfuse auto-generated.

`LangfuseRedactor` exists because litellm's own per-request redaction switch
(the `litellm-enable-message-redaction` header/metadata field documented in
litellm/litellm_core_utils/redact_messages.py) was verified NOT to suppress
Langfuse's GENERATION-observation content on this proxy version (v1.53.7) —
the flag genuinely reaches the proxy (visible in the observation's own
`requester_metadata`), but the raw prompt/response are still written. Rather
than depend on that undocumented, version-specific internal mechanism, this
overwrites the trace after the fact via Langfuse's own ingestion API, which
upserts by id (empirically verified: a `trace-create`/`generation-update`
event with an existing id overwrites that record's input/output).
"""

from __future__ import annotations

import httpx


class LangfuseScorer:
    def __init__(
        self,
        *,
        base_url: str,
        public_key: str,
        secret_key: str,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = (public_key, secret_key)
        self._transport = transport
        self._timeout = timeout

    async def push_score(
        self, *, trace_id: str, score: int, reason: str | None = None
    ) -> None:
        """score is +1 (thumbs up) or -1 (thumbs down); Langfuse NUMERIC score."""
        body: dict[str, object] = {
            "traceId": trace_id,
            "name": "user-feedback",
            "value": score,
        }
        if reason is not None:
            body["comment"] = reason

        async with httpx.AsyncClient(
            transport=self._transport, timeout=self._timeout
        ) as client:
            resp = await client.post(
                f"{self._base_url}/api/public/scores", json=body, auth=self._auth
            )
            resp.raise_for_status()


_REDACTED_CONTENT = "[REDACTED — PII detected at ingest, TRD §8]"


class LangfuseRedactor:
    """Best-effort, never-raising: overwrites a trace's (and its generation
    observations') input/output after the fact. Call sites treat this as
    fire-and-forget (e.g. `asyncio.create_task(...)`, never awaited inline)
    since Langfuse ingestion is asynchronous and must never add latency to
    the chat response it's redacting."""

    def __init__(
        self,
        *,
        base_url: str,
        public_key: str,
        secret_key: str,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = (public_key, secret_key)
        self._transport = transport
        self._timeout = timeout

    async def redact_trace(self, *, trace_id: str) -> None:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self._timeout
            ) as client:
                await self._patch_trace(client, trace_id=trace_id)
                await self._patch_observations(client, trace_id=trace_id)
        except Exception:  # noqa: BLE001 — tracing must never raise into the caller
            pass

    async def _patch_trace(self, client: httpx.AsyncClient, *, trace_id: str) -> None:
        await client.post(
            f"{self._base_url}/api/public/ingestion",
            auth=self._auth,
            json={
                "batch": [
                    {
                        "id": f"redact-trace-{trace_id}",
                        "type": "trace-create",
                        "timestamp": _now_iso(),
                        "body": {
                            "id": trace_id,
                            "input": _REDACTED_CONTENT,
                            "output": _REDACTED_CONTENT,
                        },
                    }
                ]
            },
        )

    async def _patch_observations(self, client: httpx.AsyncClient, *, trace_id: str) -> None:
        # A couple of short retries: litellm's own callback may not have
        # finished writing the trace/observation yet when this runs.
        observation_ids: list[str] = []
        for _ in range(3):
            resp = await client.get(
                f"{self._base_url}/api/public/traces/{trace_id}", auth=self._auth
            )
            if resp.status_code == 200:
                observations = resp.json().get("observations") or []
                observation_ids = [
                    o["id"] if isinstance(o, dict) else o for o in observations
                ]
                if observation_ids:
                    break
            import asyncio

            await asyncio.sleep(1.5)

        if not observation_ids:
            return

        batch = [
            {
                "id": f"redact-obs-{obs_id}",
                "type": "generation-update",
                "timestamp": _now_iso(),
                "body": {
                    "id": obs_id,
                    "traceId": trace_id,
                    "input": _REDACTED_CONTENT,
                    "output": _REDACTED_CONTENT,
                },
            }
            for obs_id in observation_ids
        ]
        await client.post(
            f"{self._base_url}/api/public/ingestion", auth=self._auth, json={"batch": batch}
        )


def _now_iso() -> str:
    import datetime as dt

    return dt.datetime.now(dt.UTC).isoformat()
