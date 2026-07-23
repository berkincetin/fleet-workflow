"""fleet_api.n8n_client: async client over n8n's REST API + webhooks (task
6.5.3). Every case is exercised against a fake transport (httpx.MockTransport)
— no real n8n needed. The key contract under test: a connection failure never
raises, it surfaces as N8nResult(reachable=False), because the workflows
router needs a plain-language down-state, not a 500.
"""

from __future__ import annotations

import json

import httpx
import pytest
from fleet_api.n8n_client import N8nClient


def _client_with_transport(transport: httpx.MockTransport) -> N8nClient:
    client = N8nClient(base_url="http://n8n.test", api_key="test-key")

    # Monkeypatch the per-call httpx.AsyncClient construction to use the fake
    # transport — N8nClient builds a fresh AsyncClient per request (see
    # _request), so patch the constructor it calls rather than an instance.
    orig_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["transport"] = transport
        return orig_init(self, *args, **kwargs)

    httpx.AsyncClient.__init__ = patched_init  # type: ignore[method-assign]
    return client


@pytest.fixture(autouse=True)
def _restore_async_client_init():  # type: ignore[no-untyped-def]
    orig_init = httpx.AsyncClient.__init__
    yield
    httpx.AsyncClient.__init__ = orig_init  # type: ignore[method-assign]


def test_list_workflows_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-N8N-API-KEY"] == "test-key"
        return httpx.Response(200, json={"data": [{"id": "1", "name": "Invoice intake"}]})

    client = _client_with_transport(httpx.MockTransport(handler))

    import asyncio

    result = asyncio.run(client.list_workflows())
    assert result.reachable is True
    assert result.auth_error is False
    assert result.data["data"][0]["name"] == "Invoice intake"


def test_connect_error_surfaces_as_unreachable_not_raised() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = _client_with_transport(httpx.MockTransport(handler))

    import asyncio

    result = asyncio.run(client.list_workflows())
    assert result.reachable is False
    assert result.error is not None


def test_401_surfaces_as_auth_error_not_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "unauthorized"})

    client = _client_with_transport(httpx.MockTransport(handler))

    import asyncio

    result = asyncio.run(client.list_workflows())
    assert result.reachable is True
    assert result.auth_error is True


def test_trigger_webhook_json_posts_body() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    client = _client_with_transport(httpx.MockTransport(handler))

    import asyncio

    result = asyncio.run(client.trigger_webhook_json("invoice-intake", {"image_base64": "abc"}))
    assert result.reachable is True
    assert captured["path"] == "/webhook/invoice-intake"
    assert captured["body"] == {"image_base64": "abc"}


def test_set_active_calls_correct_endpoint() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["method"] = request.method
        return httpx.Response(200, json={"active": True})

    client = _client_with_transport(httpx.MockTransport(handler))

    import asyncio

    result = asyncio.run(client.set_active("42", True))
    assert result.reachable is True
    assert captured["path"] == "/api/v1/workflows/42/activate"
    assert captured["method"] == "POST"
