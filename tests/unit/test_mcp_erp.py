"""fleet_mcp.servers.erp: mock ERP create_draft_entry (task 6.3, dept scenario 04).

# INTEGRATION-POINT (CLAUDE.md rule 2): no real ERP wired this environment —
in-memory draft records stand in for it. Always write:external (§9): a draft
accounting entry must never execute without human approval, unconditionally.
"""

from __future__ import annotations

from fleet_mcp.servers.erp import ErpTool


async def test_create_draft_entry_records_and_returns_a_draft() -> None:
    tool = ErpTool()
    entry = await tool.create_draft_entry(
        vendor="Acme Tedarik A.S.", po_number="PO-1001", amount=1250.0, currency="TRY"
    )
    assert entry["status"] == "draft"
    assert entry["vendor"] == "Acme Tedarik A.S."
    assert entry["po_number"] == "PO-1001"
    assert entry["amount"] == 1250.0
    assert entry["entry_id"].startswith("DRAFT-")
    assert tool.created_entries == [entry]


async def test_each_draft_entry_gets_a_unique_id() -> None:
    tool = ErpTool()
    first = await tool.create_draft_entry(
        vendor="Acme", po_number="PO-1001", amount=100.0, currency="TRY"
    )
    second = await tool.create_draft_entry(
        vendor="Acme", po_number="PO-1001", amount=100.0, currency="TRY"
    )
    assert first["entry_id"] != second["entry_id"]
    assert len(tool.created_entries) == 2


def test_contract_declares_write_external() -> None:
    tool = ErpTool()
    contract = tool.as_contract()
    assert contract.risk_class == "write:external"
    assert contract.name == "erp.create_draft_entry"
