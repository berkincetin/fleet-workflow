"""Push a feedback score onto a Langfuse trace (TRD §6, task 4.3 AC: "👍/👎
lands in Langfuse").

Thin HTTP client over Langfuse's public /api/public/scores endpoint, using the
same public/secret keypair LiteLLM's Langfuse callback authenticates with
(§6 — this repo's dev default is pk-lf-fleet-dev/sk-lf-fleet-dev, baked into
compose). The trace_id must be the SAME id the gateway client forwarded as
`metadata.trace_id` on the original call (core.llm.client) — that's what lets
a score land on the exact trace the message came from rather than one
Langfuse auto-generated.
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
