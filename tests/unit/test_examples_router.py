"""fleet_api.routers.examples: examples gallery CRUD (task 6.5.2). A fake
in-memory session stands in for Postgres — no DB needed for the routing/
validation/RBAC-shape logic; the seed idempotency and jsonl-count match are
covered separately (tests/unit/test_eval_cases_seed.py) and the live DB round
trip is exercised in tests/integration.
"""

from __future__ import annotations

import datetime as dt

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.models import EvalCase
from fleet_api.routers import examples as examples_router


class _FakeResult:
    def __init__(self, rows: list[EvalCase]) -> None:
        self._rows = rows

    def scalars(self) -> _FakeResult:
        return self

    def all(self) -> list[EvalCase]:
        return self._rows

    def scalar_one_or_none(self) -> EvalCase | None:
        return self._rows[0] if self._rows else None


class _FakeSession:
    def __init__(self) -> None:
        self.rows: list[EvalCase] = []
        self._next_id = 1

    async def execute(self, stmt: object) -> _FakeResult:
        # Only two query shapes are ever built by this router: a plain
        # ordered list (optionally agent-filtered) and an existence check by
        # (agent_name, case_id) — both are satisfied by returning self.rows
        # filtered in Python, since this fake never actually compiles SQL.
        return _FakeResult(list(self.rows))

    def add(self, row: EvalCase) -> None:
        row.id = self._next_id
        row.created_at = dt.datetime.now(dt.UTC)
        self._next_id += 1
        self.rows.append(row)

    async def commit(self) -> None:
        pass

    async def refresh(self, row: EvalCase) -> None:
        pass


def _build_app(*, session: _FakeSession, user: CurrentUser) -> FastAPI:
    """Overrides get_current_user (not require_permission's per-call-site
    closures, which don't share identity across decorator call sites) so the
    router's real require_permission(Permission.CHAT) checks run against the
    fake user."""
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(examples_router.router)

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield session

    async def fake_current_user() -> CurrentUser:
        return user

    app.dependency_overrides[examples_router.get_session] = fake_get_session
    app.dependency_overrides[get_current_user] = fake_current_user
    return app


def test_create_example_requires_known_agent() -> None:
    session = _FakeSession()
    app = _build_app(session=session, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/examples",
        json={"agent_name": "not_a_real_agent", "payload": {"id": "x1", "question": "hi"}},
    )
    assert resp.status_code == 422


def test_create_example_requires_agent_specific_fields() -> None:
    session = _FakeSession()
    app = _build_app(session=session, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/examples",
        json={"agent_name": "invoice_agent", "payload": {"id": "x1"}},
    )
    assert resp.status_code == 422


def test_create_example_persists_with_user_source() -> None:
    session = _FakeSession()
    app = _build_app(session=session, user=CurrentUser(sub="builder-1", roles={"builder"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/examples",
        json={
            "agent_name": "support_copilot",
            "payload": {"id": "custom-1", "question": "Trink sat nasıl çalışır?"},
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source"] == "user"
    assert body["created_by"] == "builder-1"
    assert body["agent_name"] == "support_copilot"


def test_list_examples_filters_by_agent() -> None:
    session = _FakeSession()
    session.add(
        EvalCase(agent_name="support_copilot", case_id="a", payload={"id": "a"}, source="seed")
    )
    session.add(EvalCase(agent_name="analytics", case_id="b", payload={"id": "b"}, source="seed"))
    app = _build_app(session=session, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/examples")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_duplicate_case_id_for_same_agent_is_rejected() -> None:
    session = _FakeSession()
    session.add(
        EvalCase(
            agent_name="dev_agent", case_id="dup-1",
            payload={"id": "dup-1", "ticket_key": "DEV-1"}, source="seed",
        )
    )
    app = _build_app(session=session, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/examples",
        json={"agent_name": "dev_agent", "payload": {"id": "dup-1", "ticket_key": "DEV-2"}},
    )
    assert resp.status_code == 409
