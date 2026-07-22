"""Real PO lookup over pg_ro (task 6.3, dept scenario 04 "pg_ro.query
purchase-orders view (read)" tool).

Wraps the governed PgReadOnlyTool (Sprint 5.1) rather than querying Postgres
directly — the invoice agent gets the same allowlist/DML-block/row-limit
guarantees any other pg_ro caller gets. Depends on the tool's *shape*
(agents.invoice_agent.validator.GovernedPoLookup Protocol), not the fleet_mcp
package itself, same runtime/mcp boundary agents.analytics.service already
established.

`po_number` here is LLM-extracted from OCR'd invoice text — untrusted data
per CLAUDE.md rule 4 — and PgReadOnlyTool.query() takes a raw SQL string with
no parameter binding (it structurally validates the statement shape, not
literal values), so this module must never string-interpolate it directly
into SQL. Instead of building a WHERE clause at all, every allowlisted PO
number is fetched in one bounded query and matched in Python — the same
"push filtering to the trusted side of the boundary" pattern, just applied
one layer earlier than usual since pg_ro has no parameterized-query surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from agents.invoice_agent.validator import PurchaseOrder


class QueryTool(Protocol):
    async def query(self, sql: str) -> list[dict[str, Any]]: ...


@dataclass
class PgPoLookup:
    tool: QueryTool

    async def lookup(self, po_number: str) -> PurchaseOrder | None:
        rows = await self.tool.query(
            "SELECT po_number, vendor, amount, currency FROM fixture_purchase_orders"
        )
        for row in rows:
            if str(row["po_number"]) == po_number:
                return PurchaseOrder(
                    po_number=str(row["po_number"]),
                    vendor=str(row["vendor"]),
                    amount=float(row["amount"]),
                    currency=str(row["currency"]),
                )
        return None
