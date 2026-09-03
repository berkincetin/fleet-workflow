"""Recipe -> n8n workflow JSON (task 13.4).

The compiler is the security boundary between "a builder typed something into a
form" and "n8n executes it". Three invariants, each enforced here rather than
trusted from the schema alone:

1. **Only five node types are ever emitted** — `scheduleTrigger`, `webhook`,
   `if`, `set` and `httpRequest`. In particular never `code`, which would be
   arbitrary JavaScript inside the n8n runtime.
2. **Every `httpRequest` URL is Fleet's own `/v1/service/*` surface**, chosen
   from `SERVICE_PATHS` by action name. The recipe never carries a URL, and
   `_service_url` re-checks the assembled value against `_FLEET_URL_RE` before
   it goes into a node — so a bug in the action map fails loudly instead of
   pointing n8n at someone else's host.
3. **User text never becomes code.** Parameter strings are emitted as JSON
   string literals (`json.dumps`), and the only interpolation is the
   `{{steps.<id>.<path>}}` form the schema already validated, rewritten here
   into `$('<node>').item.json.<path>`.

Because every external side effect still leaves through `/v1/service/*` — and
therefore through an MCP server with a declared `risk_class` — a compiled
recipe cannot bypass the approval queue: `email.send` is routed at the endpoint
that queues an approval, on both branches of a condition, because the endpoint
decides, not the recipe.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from fleet_api.recipes.schema import (
    STEP_REFERENCE_RE,
    ActionName,
    ActionStep,
    ConditionStep,
    Recipe,
    ScheduleTrigger,
)

#: action -> Fleet service path. The single place a recipe's target is decided.
SERVICE_PATHS: dict[ActionName, str] = {
    ActionName.PG_QUERY: "/v1/service/pg-query",
    ActionName.AGENT_RUN: "/v1/service/agent-run",
    ActionName.SLACK_POST: "/v1/service/slack-post",
    ActionName.EMAIL_SEND: "/v1/service/email-send",
    ActionName.HTTP_NOTIFY: "/v1/service/notify",
}

#: n8n resolves the host from its own environment (same as the hand-written
#: exports in `workflows/`), so the compiled workflow is portable between the
#: host-run API in dev and an in-cluster one later. The compiler still owns the
#: whole path after it.
_URL_BASE = "={{ $env.FLEET_API_BASE_URL }}"
_FLEET_URL_RE = re.compile(r"^=\{\{ \$env\.FLEET_API_BASE_URL \}\}/v1/service/[a-z-]+$")

ALLOWED_NODE_TYPES = frozenset(
    {
        "n8n-nodes-base.scheduleTrigger",
        "n8n-nodes-base.webhook",
        "n8n-nodes-base.if",
        "n8n-nodes-base.set",
        "n8n-nodes-base.httpRequest",
    }
)

#: Recipe operator -> (n8n condition type, n8n operation).
_OPERATORS: dict[str, tuple[str, str]] = {
    "eq": ("string", "equals"),
    "ne": ("string", "notEquals"),
    "contains": ("string", "contains"),
    "gt": ("number", "gt"),
    "gte": ("number", "gte"),
    "lt": ("number", "lt"),
    "lte": ("number", "lte"),
}

WORKFLOW_NAME_PREFIX = "fleet-recipe-"


class RecipeCompileError(ValueError):
    """The recipe cannot be compiled into a safe workflow."""


def workflow_name(recipe_name: str) -> str:
    """n8n workflow name for a recipe — prefixed so the built-in catalog's
    exact-match lookups (`workflows_catalog.py`) can never collide with a
    user-defined one."""
    return f"{WORKFLOW_NAME_PREFIX}{recipe_name}"


def webhook_path(recipe_name: str) -> str:
    return f"recipe-{recipe_name}-run"


def webhook_id(recipe_name: str) -> str:
    """Stable per-recipe UUID for the webhook node.

    n8n registers a production webhook by the node's `webhookId`, not by its
    `path` alone: a webhook node deployed over the REST API without one is
    accepted, the workflow activates, and every call to its production URL then
    answers 404 "not registered" — the failure mode this exists to avoid (the
    hand-written exports in `workflows/` carry a literal UUID for the same
    reason). Derived from the recipe name so redeploying the same recipe keeps
    the same registration instead of orphaning the old one.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"fleet-recipe/{recipe_name}"))


def _service_url(action: ActionName) -> str:
    path = SERVICE_PATHS.get(action)
    if path is None:  # pragma: no cover - unreachable while ActionName is exhaustive
        raise RecipeCompileError(f"no service endpoint for action {action!r}")
    url = f"{_URL_BASE}{path}"
    if not _FLEET_URL_RE.match(url):
        raise RecipeCompileError(f"refusing to emit a non-Fleet URL: {url!r}")
    return url


def _node_name(step: ActionStep | ConditionStep) -> str:
    label = step.action.value if isinstance(step, ActionStep) else "if"
    return f"{label} ({step.id})"


def _js_expression(value: str, node_names: dict[str, str]) -> str:
    """A JS expression producing `value`, with step references resolved.

    Literal segments become JSON string literals; a `{{steps.q1.rows}}`
    reference becomes `$('pg.query (q1)').item.json.rows`. Nothing the user
    typed is ever emitted unquoted.
    """
    parts: list[str] = []
    cursor = 0
    for match in STEP_REFERENCE_RE.finditer(value):
        if match.start() > cursor:
            parts.append(json.dumps(value[cursor : match.start()]))
        target = node_names.get(match.group("step"))
        if target is None:
            raise RecipeCompileError(f"reference to unknown step: {match.group('step')!r}")
        parts.append(f"$({json.dumps(target)}).item.json.{match.group('path')}")
        cursor = match.end()
    if cursor < len(value):
        parts.append(json.dumps(value[cursor:]))
    if not parts:
        return json.dumps("")
    return " + ".join(parts)


def _json_body(params: dict[str, Any], node_names: dict[str, str]) -> str:
    fields = ", ".join(
        f"{json.dumps(key)}: "
        + (_js_expression(value, node_names) if isinstance(value, str) else json.dumps(value))
        for key, value in params.items()
    )
    return f"={{{{ JSON.stringify({{{fields}}}) }}}}"


#: Actions whose endpoint answers with no body (`/v1/service/slack-post` is
#: 204). n8n's JSON response parser errors on an empty body, so those — and
#: only those — are read as text.
_EMPTY_RESPONSE_ACTIONS: frozenset[ActionName] = frozenset({ActionName.SLACK_POST})


def _response_options(action: ActionName) -> dict[str, Any]:
    """How the node should read the endpoint's response.

    This is load-bearing, not cosmetic: forcing `responseFormat: "text"` (as the
    hand-written weekly-summary export does for its Slack step) puts the whole
    body in `json.data` as a *string*, so a later `{{steps.q1.row_count}}`
    reference and every `if` condition reading one silently resolve to
    undefined — a condition then always takes its false branch. Everything with
    a real JSON body is therefore left on n8n's default autodetect.
    """
    if action in _EMPTY_RESPONSE_ACTIONS:
        return {"response": {"response": {"responseFormat": "text"}}}
    return {}


def _http_node(step: ActionStep, node_names: dict[str, str], position: list[int]) -> dict[str, Any]:
    return {
        "parameters": {
            "method": "POST",
            "url": _service_url(step.action),
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "X-Fleet-Api-Key", "value": "={{ $env.FLEET_API_KEY }}"},
                    {"name": "Content-Type", "value": "application/json"},
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": _json_body(step.params, node_names),
            "options": _response_options(step.action),
        },
        "id": f"http-{step.id}",
        "name": _node_name(step),
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": position,
    }


def _if_node(
    step: ConditionStep, node_names: dict[str, str], position: list[int]
) -> dict[str, Any]:
    kind, operation = _OPERATORS[step.operator]

    # A numeric comparison against a plain literal is emitted as a real number
    # rather than a quoted expression — n8n's loose type validation would coerce
    # it either way, but a workflow a human opens in the n8n editor should read
    # as `> 0`, not `> "0"`.
    if kind == "number" and not STEP_REFERENCE_RE.search(step.right):
        try:
            right_value: Any = json.loads(step.right)
        except ValueError:
            right_value = f"={{{{ {_js_expression(step.right, node_names)} }}}}"
        if not isinstance(right_value, int | float):
            right_value = f"={{{{ {_js_expression(step.right, node_names)} }}}}"
    else:
        right_value = f"={{{{ {_js_expression(step.right, node_names)} }}}}"

    return {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    # loose: a pg row count arrives as a string from JSON and
                    # still has to compare as a number.
                    "typeValidation": "loose",
                    "version": 2,
                },
                "conditions": [
                    {
                        "id": f"cond-{step.id}",
                        "leftValue": f"={{{{ {_js_expression(step.left, node_names)} }}}}",
                        "rightValue": right_value,
                        "operator": {"type": kind, "operation": operation},
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        },
        "id": f"if-{step.id}",
        "name": _node_name(step),
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": position,
    }


class _Connections:
    """Accumulates n8n's `connections` map from (source, output) -> target."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, list[list[dict[str, Any]]]]] = {}

    def add(self, source: str, output: int, target: str) -> None:
        main = self._data.setdefault(source, {"main": []})["main"]
        while len(main) <= output:
            main.append([])
        main[output].append({"node": target, "type": "main", "index": 0})

    def as_dict(self) -> dict[str, Any]:
        return self._data


def compile_recipe(recipe: Recipe) -> dict[str, Any]:
    """Render `recipe` as an n8n workflow payload (create/update body)."""
    nodes: list[dict[str, Any]] = []
    connections = _Connections()
    node_names: dict[str, str] = {}
    # Edges waiting for the next node: (source node name, output index).
    pending: list[tuple[str, int]] = []

    column = 0

    if isinstance(recipe.trigger, ScheduleTrigger):
        schedule_name = "Schedule"
        nodes.append(
            {
                "parameters": {
                    "rule": {
                        "interval": [
                            {"field": "cronExpression", "expression": recipe.trigger.cron}
                        ]
                    }
                },
                "id": "trigger-schedule",
                "name": schedule_name,
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [-400, 0],
            }
        )
        pending.append((schedule_name, 0))

    # Every recipe also gets a webhook, so "Run now" in the Fleet UI works for a
    # scheduled recipe too — the same shape the hand-written weekly-summary
    # export uses.
    manual_name = "Manual run (from Fleet)"
    nodes.append(
        {
            "parameters": {
                "httpMethod": "POST",
                "path": webhook_path(recipe.name),
                "responseMode": "onReceived",
                "options": {},
            },
            "id": "trigger-webhook",
            "name": manual_name,
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [-400, 160],
            "webhookId": webhook_id(recipe.name),
        }
    )
    pending.append((manual_name, 0))

    def emit_action(step: ActionStep, row: int) -> str:
        nonlocal column
        name = _node_name(step)
        node_names[step.id] = name
        nodes.append(_http_node(step, node_names, [column * 240, row]))
        return name

    for step in recipe.steps:
        column += 1
        if isinstance(step, ActionStep):
            name = emit_action(step, 0)
            for source, output in pending:
                connections.add(source, output, name)
            pending = [(name, 0)]
            continue

        # ConditionStep
        name = _node_name(step)
        node_names[step.id] = name
        nodes.append(_if_node(step, node_names, [column * 240, 0]))
        for source, output in pending:
            connections.add(source, output, name)

        next_pending: list[tuple[str, int]] = []
        for output, branch in ((0, step.then_steps), (1, step.else_steps)):
            row = -160 if output == 0 else 160
            branch_pending: list[tuple[str, int]] = [(name, output)]
            branch_column = column
            for branch_step in branch:
                branch_column += 1
                saved, column = column, branch_column
                branch_name = emit_action(branch_step, row)
                column = saved
                for source, out in branch_pending:
                    connections.add(source, out, branch_name)
                branch_pending = [(branch_name, 0)]
            next_pending.extend(branch_pending)
        pending = next_pending
        column += max(len(step.then_steps), len(step.else_steps))

    emitted_types = {node["type"] for node in nodes}
    unexpected = emitted_types - ALLOWED_NODE_TYPES
    if unexpected:  # pragma: no cover - a guard against future edits
        raise RecipeCompileError(f"refusing to emit node types: {sorted(unexpected)}")

    return {
        "name": workflow_name(recipe.name),
        "nodes": nodes,
        "connections": connections.as_dict(),
        "settings": {"executionOrder": "v1"},
    }


def describe_recipe(recipe: Recipe) -> list[dict[str, Any]]:
    """Structured plain-language summary of what a recipe will do.

    Returned by the API so the builder's preview and the automation card show
    the *same* description, and so the sentence order can be translated in the
    web app rather than assembled from English fragments here.
    """
    lines: list[dict[str, Any]] = []
    if isinstance(recipe.trigger, ScheduleTrigger):
        lines.append({"kind": "trigger", "trigger": "schedule", "cron": recipe.trigger.cron})
    else:
        lines.append({"kind": "trigger", "trigger": "manual"})

    for step in recipe.steps:
        if isinstance(step, ActionStep):
            lines.append(
                {
                    "kind": "action",
                    "id": step.id,
                    "action": step.action.value,
                    "params": step.params,
                    "write_external": step.is_write_external,
                }
            )
        else:
            lines.append(
                {
                    "kind": "condition",
                    "id": step.id,
                    "left": step.left,
                    "operator": step.operator,
                    "right": step.right,
                    "then": [
                        {
                            "id": s.id,
                            "action": s.action.value,
                            "params": s.params,
                            "write_external": s.is_write_external,
                        }
                        for s in step.then_steps
                    ],
                    "else": [
                        {
                            "id": s.id,
                            "action": s.action.value,
                            "params": s.params,
                            "write_external": s.is_write_external,
                        }
                        for s in step.else_steps
                    ],
                }
            )
    return lines
