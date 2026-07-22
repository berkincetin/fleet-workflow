"""Analytics agent's semantic layer: view/column glossary the SQL generator
grounds on (task 5.2, dept scenario 02 "data-semantic-layer" knowledge).

Day-0 scope is the two fixture warehouse views seeded in task 1.2
(fixture_sales, fixture_orders, apps/api/fleet_api/seed.py) — small enough to
inline as a static glossary here rather than standing up a real RAG
collection for it. describe() renders the glossary into the system-prompt
block sql_generator.py grounds the SQL generation call on; allowlisted_tables()
is the same table set pg_ro.PgReadOnlyTool is constructed with, so the model's
allowed universe and the tool's enforced universe can never drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewSpec:
    name: str
    description: str
    columns: dict[str, str]


@dataclass(frozen=True)
class SemanticLayer:
    views: list[ViewSpec]

    def allowlisted_tables(self) -> set[str]:
        return {v.name for v in self.views}

    def describe(self) -> str:
        blocks = []
        for view in self.views:
            column_lines = "\n".join(f"  - {col}: {desc}" for col, desc in view.columns.items())
            blocks.append(f"### {view.name}\n{view.description}\nColumns:\n{column_lines}")
        return "\n\n".join(blocks)


DEFAULT_SEMANTIC_LAYER = SemanticLayer(
    views=[
        ViewSpec(
            name="fixture_sales",
            description="One row per sale transaction.",
            columns={
                "id": "surrogate primary key",
                "region": "sale region code (TR, DE, US, FR)",
                "amount_usd": "sale amount in US dollars",
                "sold_on": "date the sale closed",
            },
        ),
        ViewSpec(
            name="fixture_orders",
            description="One row per order line, referencing a sale.",
            columns={
                "id": "surrogate primary key",
                "sale_id": "foreign key into fixture_sales.id",
                "quantity": "units ordered on this line",
                "refunded": "true if this order line was refunded",
            },
        ),
    ]
)
