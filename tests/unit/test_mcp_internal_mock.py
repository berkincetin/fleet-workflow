"""fleet_mcp.servers.internal_mock: fixture-backed internal API mock (task 5.1).

# INTEGRATION-POINT (CLAUDE.md rule 2): stands in for a real internal system
(e.g. an internal lookup API) that isn't wired yet. Fixture-backed and
read-only so it's safe to expose to any agent under active development.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.internal_mock import InternalMockTool, RecordNotFoundError


def test_lookup_returns_seeded_fixture_record() -> None:
    tool = InternalMockTool(fixtures={"emp-001": {"name": "Ada Lovelace", "dept": "Engineering"}})
    record = tool.lookup(record_id="emp-001")
    assert record == {"name": "Ada Lovelace", "dept": "Engineering"}


def test_lookup_unknown_id_raises_not_found() -> None:
    tool = InternalMockTool(fixtures={})
    with pytest.raises(RecordNotFoundError):
        tool.lookup(record_id="missing")


def test_contract_declares_read_risk_class() -> None:
    tool = InternalMockTool(fixtures={})
    contract = tool.as_contract()
    assert contract.risk_class == "read"
    assert contract.name == "internal.lookup"
