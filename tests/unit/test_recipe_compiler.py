"""fleet_api.recipes.compiler: recipe -> n8n workflow JSON (task 13.4).

Pins the shape n8n actually accepts (compared against the hand-written
`workflows/weekly-summary.json` export, which is known to import and run) and
the compiler's own invariants: five node types, Fleet-only URLs, no user text
emitted as code.
"""

from __future__ import annotations

import json

from fleet_api.recipes.compiler import (
    ALLOWED_NODE_TYPES,
    SERVICE_PATHS,
    compile_recipe,
    describe_recipe,
    webhook_path,
    workflow_name,
)
from fleet_api.recipes.schema import ActionName, Recipe


def _recipe(**overrides: object) -> Recipe:
    base: dict[str, object] = {
        "name": "sales-check",
        "trigger": {"type": "schedule", "cron": "0 9 * * 1"},
        "steps": [
            {
                "type": "action",
                "id": "q1",
                "action": "pg.query",
                "params": {"sql": "SELECT COUNT(*) AS n FROM fixture_sales"},
            }
        ],
    }
    base.update(overrides)
    return Recipe.model_validate(base)


def _nodes_by_type(workflow: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for node in workflow["nodes"]:
        out.setdefault(node["type"], []).append(node)
    return out


def test_schedule_recipe_emits_trigger_plus_manual_webhook() -> None:
    workflow = compile_recipe(_recipe())
    by_type = _nodes_by_type(workflow)
    assert len(by_type["n8n-nodes-base.scheduleTrigger"]) == 1
    # Every recipe also gets a webhook so "Run now" works without the cron.
    assert by_type["n8n-nodes-base.webhook"][0]["parameters"]["path"] == webhook_path(
        "sales-check"
    )
    assert workflow["name"] == workflow_name("sales-check")


def test_manual_recipe_has_no_schedule_node() -> None:
    workflow = compile_recipe(_recipe(trigger={"type": "manual"}))
    assert "n8n-nodes-base.scheduleTrigger" not in _nodes_by_type(workflow)


def test_only_allowlisted_node_types_are_emitted() -> None:
    workflow = compile_recipe(
        _recipe(
            steps=[
                {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}},
                {
                    "type": "condition",
                    "id": "c1",
                    "left": "{{steps.q1.row_count}}",
                    "operator": "gt",
                    "right": "0",
                    "then_steps": [
                        {
                            "type": "action",
                            "id": "n1",
                            "action": "http.notify",
                            "params": {"title": "t", "message": "m"},
                        }
                    ],
                    "else_steps": [],
                },
            ]
        )
    )
    assert {node["type"] for node in workflow["nodes"]} <= ALLOWED_NODE_TYPES
    assert "n8n-nodes-base.code" not in {node["type"] for node in workflow["nodes"]}


def test_every_http_node_targets_a_fleet_service_path() -> None:
    steps = [
        {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}},
        {
            "type": "action",
            "id": "a1",
            "action": "agent.run",
            "params": {"agent": "support_copilot", "question": "hi"},
        },
        {
            "type": "action",
            "id": "e1",
            "action": "email.send",
            "params": {"to": "a@fleet.local", "subject": "s", "body": "b"},
        },
    ]
    workflow = compile_recipe(_recipe(steps=steps))
    urls = [
        node["parameters"]["url"]
        for node in workflow["nodes"]
        if node["type"] == "n8n-nodes-base.httpRequest"
    ]
    assert urls == [
        "={{ $env.FLEET_API_BASE_URL }}/v1/service/pg-query",
        "={{ $env.FLEET_API_BASE_URL }}/v1/service/agent-run",
        "={{ $env.FLEET_API_BASE_URL }}/v1/service/email-send",
    ]


def test_service_paths_cover_every_action() -> None:
    assert set(SERVICE_PATHS) == set(ActionName)


def test_api_key_is_taken_from_n8n_env_never_from_the_recipe() -> None:
    workflow = compile_recipe(_recipe())
    node = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.httpRequest")
    headers = node["parameters"]["headerParameters"]["parameters"]
    assert {"name": "X-Fleet-Api-Key", "value": "={{ $env.FLEET_API_KEY }}"} in headers


def test_user_text_is_emitted_as_a_json_string_literal() -> None:
    """A quote in user text must be escaped, not close the literal."""
    workflow = compile_recipe(
        _recipe(
            steps=[
                {
                    "type": "action",
                    "id": "n1",
                    "action": "http.notify",
                    "params": {"title": 'he said "hi"', "message": "m"},
                }
            ]
        )
    )
    node = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.httpRequest")
    body = node["parameters"]["jsonBody"]
    assert json.dumps('he said "hi"') in body


def test_step_reference_becomes_a_node_reference() -> None:
    workflow = compile_recipe(
        _recipe(
            steps=[
                {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}},
                {
                    "type": "action",
                    "id": "s1",
                    "action": "slack.post",
                    "params": {
                        "channel": "#weekly-summary",
                        "text": "rows: {{steps.q1.row_count}}",
                    },
                },
            ]
        )
    )
    slack = next(n for n in workflow["nodes"] if n["name"] == "slack.post (s1)")
    assert '$("pg.query (q1)").item.json.row_count' in slack["parameters"]["jsonBody"]


def test_condition_wires_both_branches_to_the_if_outputs() -> None:
    workflow = compile_recipe(
        _recipe(
            steps=[
                {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}},
                {
                    "type": "condition",
                    "id": "c1",
                    "left": "{{steps.q1.row_count}}",
                    "operator": "gt",
                    "right": "0",
                    "then_steps": [
                        {
                            "type": "action",
                            "id": "n1",
                            "action": "http.notify",
                            "params": {"title": "t", "message": "m"},
                        }
                    ],
                    "else_steps": [
                        {
                            "type": "action",
                            "id": "e1",
                            "action": "email.send",
                            "params": {"to": "a@fleet.local", "subject": "s", "body": "b"},
                        }
                    ],
                },
            ]
        )
    )
    outputs = workflow["connections"]["if (c1)"]["main"]
    assert outputs[0] == [{"node": "http.notify (n1)", "type": "main", "index": 0}]
    assert outputs[1] == [{"node": "email.send (e1)", "type": "main", "index": 0}]


def test_numeric_comparison_against_a_literal_emits_a_number() -> None:
    workflow = compile_recipe(
        _recipe(
            steps=[
                {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}},
                {
                    "type": "condition",
                    "id": "c1",
                    "left": "{{steps.q1.row_count}}",
                    "operator": "gte",
                    "right": "3",
                    "then_steps": [
                        {
                            "type": "action",
                            "id": "n1",
                            "action": "http.notify",
                            "params": {"title": "t", "message": "m"},
                        }
                    ],
                    "else_steps": [],
                },
            ]
        )
    )
    if_node = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.if")
    condition = if_node["parameters"]["conditions"]["conditions"][0]
    assert condition["rightValue"] == 3
    assert condition["operator"] == {"type": "number", "operation": "gte"}


def test_json_responses_are_left_parseable_and_only_slack_reads_as_text() -> None:
    """Regression for the branch-always-false bug: forcing responseFormat
    "text" hides the body inside `json.data` as a string, so `{{steps.q1.
    row_count}}` and every condition reading one resolve to undefined."""
    workflow = compile_recipe(
        _recipe(
            steps=[
                {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}},
                {
                    "type": "action",
                    "id": "s1",
                    "action": "slack.post",
                    "params": {"channel": "#weekly-summary", "text": "t"},
                },
            ]
        )
    )
    pg = next(n for n in workflow["nodes"] if n["name"] == "pg.query (q1)")
    slack = next(n for n in workflow["nodes"] if n["name"] == "slack.post (s1)")
    assert pg["parameters"]["options"] == {}
    # slack-post is 204 with no body — n8n's JSON parser errors on that.
    assert slack["parameters"]["options"]["response"]["response"]["responseFormat"] == "text"


def test_webhook_node_carries_a_stable_webhook_id() -> None:
    """n8n registers a production webhook by the node's `webhookId`; without
    one an activated workflow answers 404 on its own production URL."""
    first = compile_recipe(_recipe())
    second = compile_recipe(_recipe())
    webhook = next(n for n in first["nodes"] if n["type"] == "n8n-nodes-base.webhook")
    again = next(n for n in second["nodes"] if n["type"] == "n8n-nodes-base.webhook")
    assert webhook["webhookId"]
    assert webhook["webhookId"] == again["webhookId"]
    assert webhook["webhookId"] != compile_recipe(_recipe(name="other-name"))["nodes"][1][
        "webhookId"
    ]


def test_describe_recipe_marks_write_external_steps() -> None:
    summary = describe_recipe(
        _recipe(
            steps=[
                {
                    "type": "action",
                    "id": "e1",
                    "action": "email.send",
                    "params": {"to": "a@fleet.local", "subject": "s", "body": "b"},
                }
            ]
        )
    )
    assert summary[0]["kind"] == "trigger"
    assert summary[1]["write_external"] is True
