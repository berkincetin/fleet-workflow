"""Automation-recipe schema (task 13.4).

A recipe is what a builder defines in Fleet's own UI; it is stored here as the
source of truth and *compiled* into an n8n workflow (see `compiler.py`). n8n
stays the executor — the recipe is not a second workflow engine.

The whole point of this schema is that it is small enough to be safe. Actions
come from a fixed allowlist, each one backed by a Fleet `/v1/service/*`
endpoint the compiler picks itself, so no recipe can name a URL. Parameters are
typed per action with `extra="forbid"`, so no recipe can smuggle an extra field
into an n8n node. Strings are checked against `_TEXT_RE` so no recipe can carry
an n8n expression (`={{ $env.OPENAI_API_KEY }}`) into the generated workflow;
the only templating allowed is a `{{steps.<id>.<path>}}` reference to an earlier
step's output, which the compiler rewrites itself.

Together those three rules are what keeps Non-Negotiable Rule 3 intact: the
only external side effects a recipe can reach are the MCP-backed service
endpoints, with their `risk_class` and HITL gating unchanged.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ActionName(StrEnum):
    """The fixed action allowlist. Anything not here fails validation."""

    PG_QUERY = "pg.query"
    AGENT_RUN = "agent.run"
    SLACK_POST = "slack.post"
    EMAIL_SEND = "email.send"
    HTTP_NOTIFY = "http.notify"


#: Actions whose effect leaves the company. The compiler routes these at
#: endpoints that queue an approval instead of executing (TRD §9); listed here
#: so the API and the UI can say so *before* the recipe is saved.
WRITE_EXTERNAL_ACTIONS: frozenset[ActionName] = frozenset({ActionName.EMAIL_SEND})

#: `{{steps.<step_id>.<dotted.path>}}` — the only templating a recipe may use.
STEP_REFERENCE_RE = re.compile(
    r"\{\{\s*steps\.(?P<step>[a-z0-9_]{1,64})\.(?P<path>[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*)\s*\}\}"
)

_STEP_ID_RE = re.compile(r"^[a-z0-9_]{1,64}$")
_RECIPE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
#: 5-field cron, the only form n8n's scheduleTrigger cronExpression is fed here.
_CRON_RE = re.compile(r"^[\d*,\-/]+(\s+[\d*,\-/A-Za-z]+){4}$")


class RecipeValidationError(ValueError):
    """A recipe that cannot be represented safely."""


def check_text(value: str, *, field: str) -> str:
    """Reject anything that could become an n8n expression.

    n8n evaluates a parameter whose value starts with `=`, and `{{ … }}` inside
    such a value is arbitrary JavaScript with `$env` in scope. So: no leading
    `=`, and once the legal step references are removed nothing bracey may
    remain.
    """
    if value.startswith("="):
        raise RecipeValidationError(f"{field}: a value may not start with '=' (n8n expression)")
    residue = STEP_REFERENCE_RE.sub("", value)
    if "{" in residue or "}" in residue:
        raise RecipeValidationError(
            f"{field}: only {{{{steps.<id>.<field>}}}} references are allowed, got {value!r}"
        )
    return value


class _Params(BaseModel):
    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _no_expressions(self) -> _Params:
        for name, value in self.__dict__.items():
            if isinstance(value, str):
                check_text(value, field=name)
        return self


class PgQueryParams(_Params):
    """Read-only SQL through the same governed `PgReadOnlyTool` the Analytics
    agent uses — allowlist, DML block, row limit and timeout all still apply on
    the service side, so this schema does not re-validate SQL."""

    sql: str = Field(min_length=1, max_length=4000)


class AgentRunParams(_Params):
    agent: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=4000)


class SlackPostParams(_Params):
    channel: str = Field(min_length=2, max_length=80)
    text: str = Field(min_length=1, max_length=4000)


class EmailSendParams(_Params):
    to: str = Field(min_length=3, max_length=254)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8000)


class HttpNotifyParams(_Params):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)


PARAMS_BY_ACTION: dict[ActionName, type[_Params]] = {
    ActionName.PG_QUERY: PgQueryParams,
    ActionName.AGENT_RUN: AgentRunParams,
    ActionName.SLACK_POST: SlackPostParams,
    ActionName.EMAIL_SEND: EmailSendParams,
    ActionName.HTTP_NOTIFY: HttpNotifyParams,
}


class ScheduleTrigger(BaseModel):
    model_config = {"extra": "forbid"}

    type: Literal["schedule"] = "schedule"
    cron: str

    @field_validator("cron")
    @classmethod
    def _valid_cron(cls, value: str) -> str:
        if not _CRON_RE.match(value.strip()):
            raise RecipeValidationError(f"not a 5-field cron expression: {value!r}")
        return value.strip()


class ManualTrigger(BaseModel):
    model_config = {"extra": "forbid"}

    type: Literal["manual"] = "manual"


Trigger = Annotated[ScheduleTrigger | ManualTrigger, Field(discriminator="type")]


class ActionStep(BaseModel):
    model_config = {"extra": "forbid"}

    type: Literal["action"] = "action"
    id: str
    action: ActionName
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _valid_id(cls, value: str) -> str:
        if not _STEP_ID_RE.match(value):
            raise RecipeValidationError(f"step id must be lowercase a-z0-9_: {value!r}")
        return value

    @model_validator(mode="after")
    def _validate_params(self) -> ActionStep:
        model = PARAMS_BY_ACTION[self.action]
        # Round-tripping through the typed model is what enforces
        # extra="forbid" and the no-expression rule on every string.
        self.params = model(**self.params).model_dump()
        return self

    @property
    def is_write_external(self) -> bool:
        return self.action in WRITE_EXTERNAL_ACTIONS


class ConditionStep(BaseModel):
    """One level of branching: `if <left> <op> <right> then … else …`.

    Deliberately not nestable. A recipe builder that can express arbitrary
    nesting is a programming language, and every rule above would then need to
    hold recursively; one level covers "post to Slack only when the query
    returned something", which is what the builder is for.
    """

    model_config = {"extra": "forbid"}

    type: Literal["condition"] = "condition"
    id: str
    left: str = Field(min_length=1, max_length=500)
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "contains"]
    right: str = Field(max_length=500)
    then_steps: list[ActionStep] = Field(default_factory=list)
    else_steps: list[ActionStep] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _valid_id(cls, value: str) -> str:
        if not _STEP_ID_RE.match(value):
            raise RecipeValidationError(f"step id must be lowercase a-z0-9_: {value!r}")
        return value

    @model_validator(mode="after")
    def _validate(self) -> ConditionStep:
        check_text(self.left, field="left")
        check_text(self.right, field="right")
        if not self.then_steps and not self.else_steps:
            raise RecipeValidationError("a condition needs at least one step on a branch")
        return self

    @property
    def is_write_external(self) -> bool:
        return any(s.is_write_external for s in (*self.then_steps, *self.else_steps))


Step = Annotated[ActionStep | ConditionStep, Field(discriminator="type")]


class Recipe(BaseModel):
    """The stored, canonical form of a user-defined automation."""

    model_config = {"extra": "forbid"}

    name: str
    description: str = Field(default="", max_length=500)
    trigger: Trigger
    steps: list[Step] = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        if not _RECIPE_NAME_RE.match(value):
            raise RecipeValidationError(
                f"name must be a lowercase kebab-case slug (3-64 chars): {value!r}"
            )
        return value

    @model_validator(mode="after")
    def _unique_ids_and_ordered_refs(self) -> Recipe:
        seen: set[str] = set()
        for step in self.steps:
            if step.id in seen:
                raise RecipeValidationError(f"duplicate step id: {step.id!r}")
            seen.add(step.id)
            for referenced in self._references(step):
                if referenced not in seen or referenced == step.id:
                    raise RecipeValidationError(
                        f"step {step.id!r} references {referenced!r}, which does not run before it"
                    )
            if isinstance(step, ConditionStep):
                for branch_step in (*step.then_steps, *step.else_steps):
                    if branch_step.id in seen:
                        raise RecipeValidationError(f"duplicate step id: {branch_step.id!r}")
                    seen.add(branch_step.id)
        return self

    @staticmethod
    def _references(step: ActionStep | ConditionStep) -> list[str]:
        texts: list[str] = []
        if isinstance(step, ActionStep):
            texts = [v for v in step.params.values() if isinstance(v, str)]
        else:
            texts = [step.left, step.right]
            for branch_step in (*step.then_steps, *step.else_steps):
                texts.extend(v for v in branch_step.params.values() if isinstance(v, str))
        return [m.group("step") for text in texts for m in STEP_REFERENCE_RE.finditer(text)]

    @property
    def has_write_external(self) -> bool:
        return any(step.is_write_external for step in self.steps)
