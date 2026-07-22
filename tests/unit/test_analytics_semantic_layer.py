"""agents.analytics.semantic_layer: view/column glossary the SQL generator
grounds on (task 5.2, dept scenario 02 "data-semantic-layer" knowledge).

Day-0 scope is the two fixture warehouse views seeded in task 1.2
(fixture_sales, fixture_orders) — small enough to inline as a static
glossary rather than standing up a RAG collection for it; describe() renders
it into the system-prompt block the SQL generator reads. A future sprint that
adds more governed views could swap this for real RAG retrieval without
changing SemanticLayer's public shape.
"""

from __future__ import annotations

from agents.analytics.semantic_layer import DEFAULT_SEMANTIC_LAYER, SemanticLayer, ViewSpec


def test_allowlisted_tables_match_view_names() -> None:
    layer = SemanticLayer(
        views=[
            ViewSpec(name="fixture_sales", description="Sales", columns={"id": "pk"}),
            ViewSpec(name="fixture_orders", description="Orders", columns={"id": "pk"}),
        ]
    )
    assert layer.allowlisted_tables() == {"fixture_sales", "fixture_orders"}


def test_describe_renders_view_and_column_glossary() -> None:
    layer = SemanticLayer(
        views=[
            ViewSpec(
                name="fixture_sales",
                description="One row per sale.",
                columns={"amount_usd": "sale amount in USD"},
            )
        ]
    )
    rendered = layer.describe()
    assert "fixture_sales" in rendered
    assert "One row per sale." in rendered
    assert "amount_usd" in rendered
    assert "sale amount in USD" in rendered


def test_default_semantic_layer_covers_both_fixture_views() -> None:
    assert DEFAULT_SEMANTIC_LAYER.allowlisted_tables() == {"fixture_sales", "fixture_orders"}
