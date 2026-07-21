"""core.langfuse_client: push a feedback score onto a Langfuse trace (task 4.3, TRD §6).

Thin HTTP client over Langfuse's public /api/public/scores endpoint (Basic
auth with the same public/secret keypair LiteLLM's callback uses, TRD §6).
Score value is +1/-1 for thumbs up/down (Langfuse's NUMERIC score type).
"""

from __future__ import annotations

import httpx
import pytest
from core.langfuse_client import LangfuseScorer


class _RecordingTransport(httpx.MockTransport):
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return httpx.Response(200, json={"id": "score-1"})

        super().__init__(handler)


async def test_push_score_posts_to_scores_endpoint_with_basic_auth() -> None:
    transport = _RecordingTransport()
    scorer = LangfuseScorer(
        base_url="http://langfuse.test",
        public_key="pk-test",
        secret_key="sk-test",
        transport=transport,
    )
    await scorer.push_score(trace_id="trace-1", score=1, reason="helpful")

    assert len(transport.requests) == 1
    req = transport.requests[0]
    assert req.url == "http://langfuse.test/api/public/scores"
    assert req.headers["authorization"].startswith("Basic ")


async def test_push_score_body_carries_trace_id_and_value() -> None:
    transport = _RecordingTransport()
    scorer = LangfuseScorer(
        base_url="http://langfuse.test", public_key="pk-test", secret_key="sk-test",
        transport=transport,
    )
    await scorer.push_score(trace_id="trace-1", score=-1, reason="wrong answer")

    import json

    body = json.loads(transport.requests[0].content)
    assert body["traceId"] == "trace-1"
    assert body["value"] == -1
    assert body["comment"] == "wrong answer"
    assert body["name"] == "user-feedback"


async def test_push_score_without_reason_omits_comment() -> None:
    transport = _RecordingTransport()
    scorer = LangfuseScorer(
        base_url="http://langfuse.test", public_key="pk-test", secret_key="sk-test",
        transport=transport,
    )
    await scorer.push_score(trace_id="trace-1", score=1)

    import json

    body = json.loads(transport.requests[0].content)
    assert "comment" not in body


async def test_push_score_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    scorer = LangfuseScorer(
        base_url="http://langfuse.test", public_key="pk-bad", secret_key="sk-bad",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(httpx.HTTPStatusError):
        await scorer.push_score(trace_id="trace-1", score=1)
