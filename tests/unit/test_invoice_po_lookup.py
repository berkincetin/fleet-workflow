"""agents.invoice_agent.po_lookup: PgPoLookup over a pg_ro-shaped QueryTool
(task 6.3). po_number is LLM-extracted (untrusted, CLAUDE.md rule 4) so this
must never string-interpolate it into SQL — verified by asserting the query
sent to the tool never contains the looked-up value.
"""

from __future__ import annotations

from agents.invoice_agent.po_lookup import PgPoLookup


class _FakeQueryTool:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.queries: list[str] = []

    async def query(self, sql: str) -> list[dict[str, object]]:
        self.queries.append(sql)
        return self.rows


_ROWS = [
    {"po_number": "PO-1001", "vendor": "Acme Tedarik A.S.", "amount": 1250.0, "currency": "TRY"},
    {"po_number": "PO-1002", "vendor": "Bilgi Teknoloji Ltd.", "amount": 4800.5, "currency": "TRY"},
]


async def test_lookup_finds_matching_po() -> None:
    tool = _FakeQueryTool(_ROWS)
    lookup = PgPoLookup(tool=tool)
    po = await lookup.lookup("PO-1002")
    assert po is not None
    assert po.vendor == "Bilgi Teknoloji Ltd."
    assert po.amount == 4800.5


async def test_lookup_returns_none_for_unknown_po() -> None:
    tool = _FakeQueryTool(_ROWS)
    lookup = PgPoLookup(tool=tool)
    po = await lookup.lookup("PO-9999")
    assert po is None


async def test_lookup_never_interpolates_the_untrusted_po_number_into_sql() -> None:
    tool = _FakeQueryTool(_ROWS)
    lookup = PgPoLookup(tool=tool)
    malicious = "PO-1001'; DROP TABLE fixture_purchase_orders; --"
    await lookup.lookup(malicious)
    assert all(malicious not in q for q in tool.queries)
