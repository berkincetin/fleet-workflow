"""fleet_api.recipes.schema: the validation half of the automation builder
(task 13.4).

The schema is a security boundary, not just a shape check — these tests pin the
three rules the compiler relies on: the action allowlist, `extra="forbid"` on
every action's params, and the "no n8n expression may be smuggled through a
string" rule.
"""

from __future__ import annotations

import pytest
from fleet_api.recipes.schema import (
    ActionName,
    ActionStep,
    ConditionStep,
    Recipe,
    RecipeValidationError,
    check_text,
)
from pydantic import ValidationError


def _minimal(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "nightly-check",
        "trigger": {"type": "manual"},
        "steps": [
            {
                "type": "action",
                "id": "q1",
                "action": "pg.query",
                "params": {"sql": "SELECT 1 AS n"},
            }
        ],
    }
    base.update(overrides)
    return base


def test_minimal_recipe_validates() -> None:
    recipe = Recipe.model_validate(_minimal())
    assert recipe.name == "nightly-check"
    assert isinstance(recipe.steps[0], ActionStep)
    assert recipe.steps[0].action is ActionName.PG_QUERY


def test_unknown_action_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate(
            _minimal(
                steps=[
                    {"type": "action", "id": "x", "action": "shell.exec", "params": {"cmd": "ls"}}
                ]
            )
        )


def test_extra_param_is_rejected() -> None:
    """`extra="forbid"` is what stops a recipe from smuggling a field (a URL,
    a header) into the node the compiler builds."""
    with pytest.raises(ValidationError):
        Recipe.model_validate(
            _minimal(
                steps=[
                    {
                        "type": "action",
                        "id": "q1",
                        "action": "pg.query",
                        "params": {"sql": "SELECT 1", "url": "http://evil.example"},
                    }
                ]
            )
        )


@pytest.mark.parametrize(
    "value",
    [
        "={{ $env.OPENAI_API_KEY }}",
        "hello {{ $env.FLEET_API_KEY }}",
        "{{ $json.secret }}",
        "}} injected {{",
    ],
)
def test_expression_smuggling_is_rejected(value: str) -> None:
    with pytest.raises(RecipeValidationError):
        check_text(value, field="text")


def test_step_reference_is_the_one_allowed_template() -> None:
    assert check_text("rows: {{steps.q1.row_count}}", field="text")


def test_reference_to_a_later_step_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate(
            _minimal(
                steps=[
                    {
                        "type": "action",
                        "id": "n1",
                        "action": "http.notify",
                        "params": {"title": "t", "message": "{{steps.q9.x}}"},
                    }
                ]
            )
        )


def test_duplicate_step_ids_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate(
            _minimal(
                steps=[
                    {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "S"}},
                    {"type": "action", "id": "q1", "action": "pg.query", "params": {"sql": "S"}},
                ]
            )
        )


def test_bad_cron_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate(_minimal(trigger={"type": "schedule", "cron": "every monday"}))


def test_good_cron_is_accepted() -> None:
    recipe = Recipe.model_validate(_minimal(trigger={"type": "schedule", "cron": "0 8 * * 1"}))
    assert recipe.trigger.type == "schedule"


def test_condition_needs_at_least_one_branch_step() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate(
            _minimal(
                steps=[
                    {
                        "type": "condition",
                        "id": "c1",
                        "left": "1",
                        "operator": "eq",
                        "right": "1",
                        "then_steps": [],
                        "else_steps": [],
                    }
                ]
            )
        )


def test_write_external_is_detected_on_both_branches() -> None:
    recipe = Recipe.model_validate(
        _minimal(
            steps=[
                {
                    "type": "condition",
                    "id": "c1",
                    "left": "1",
                    "operator": "eq",
                    "right": "1",
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
                }
            ]
        )
    )
    assert recipe.has_write_external is True
    condition = recipe.steps[0]
    assert isinstance(condition, ConditionStep)
    assert condition.is_write_external is True


def test_name_must_be_a_slug() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate(_minimal(name="Nightly Check!"))
