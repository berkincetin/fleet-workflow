"""Automation-recipe CRUD + deploy (task 13.4, TRD §12).

Fleet stores the recipe; n8n executes the workflow compiled from it. Every
write here does both, in that order — the row is the source of truth, and the
n8n deploy is a projection of it that can be rebuilt at any time by saving the
recipe again.

RBAC is MANAGE_AGENTS (builder and up), the same tier as defining an agent:
both are "someone configures what the platform does on its own". Reading the
list is CHAT, so an ordinary member can see the automations that exist without
being able to change one.

n8n being down is a first-class state, not an error: the recipe still saves and
the response says `deployed: false` with the reason, matching how the built-in
workflow catalog reports its own down-state.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import AutomationRecipe
from fleet_api.n8n_client import N8nClient
from fleet_api.rbac import Permission, require_permission
from fleet_api.recipes.compiler import (
    RecipeCompileError,
    compile_recipe,
    describe_recipe,
    webhook_path,
    workflow_name,
)
from fleet_api.recipes.schema import Recipe, RecipeValidationError
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/recipes", tags=["recipes"])


def get_n8n_client(settings: Settings = Depends(get_settings)) -> N8nClient:  # noqa: B008
    return N8nClient(base_url=settings.n8n_base_url, api_key=settings.n8n_api_key or None)


class RecipeOut(BaseModel):
    id: int
    name: str
    description: str
    definition: dict[str, Any]
    n8n_workflow_id: str | None
    active: bool
    created_by: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    #: Plain-language rendering of the steps, so the card and the builder
    #: preview describe the recipe identically.
    summary: list[dict[str, Any]] = []
    #: True if any step (on either branch) leaves the company — the UI shows
    #: the "this will need approval" note from this, not from its own guess.
    has_write_external: bool = False
    #: Set when the last deploy attempt did not reach n8n.
    deploy_error: str | None = None


class RecipeIn(BaseModel):
    """The recipe as the builder posts it — validated by `Recipe` itself."""

    model_config = {"extra": "forbid"}

    name: str
    description: str = ""
    trigger: dict[str, Any]
    steps: list[dict[str, Any]]


def _parse(body: RecipeIn) -> Recipe:
    try:
        return Recipe.model_validate(body.model_dump())
    except (ValidationError, RecipeValidationError) as exc:
        raise HTTPException(status_code=422, detail=f"invalid recipe: {exc}") from exc


def _to_out(row: AutomationRecipe, *, deploy_error: str | None = None) -> RecipeOut:
    recipe = Recipe.model_validate(row.definition)
    return RecipeOut(
        id=row.id,
        name=row.name,
        description=row.description,
        definition=row.definition,
        n8n_workflow_id=row.n8n_workflow_id,
        active=row.active,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
        summary=describe_recipe(recipe),
        has_write_external=recipe.has_write_external,
        deploy_error=deploy_error,
    )


async def _deploy(
    recipe: Recipe, row: AutomationRecipe, client: N8nClient
) -> str | None:
    """Create or update the recipe's n8n workflow. Returns an error string when
    n8n could not be reached, or None on success."""
    try:
        payload = compile_recipe(recipe)
    except RecipeCompileError as exc:
        # A compile refusal is the caller's fault (a crafted recipe), not an
        # outage — surface it as a 422 rather than a soft "not deployed".
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if row.n8n_workflow_id:
        result = await client.update_workflow(row.n8n_workflow_id, payload)
        if result.reachable and result.data:
            return None
        if result.reachable and result.error and "404" in str(result.error):
            # The workflow was deleted in n8n behind our back — recreate it.
            row.n8n_workflow_id = None
        else:
            return result.error or "n8n unreachable"

    result = await client.create_workflow(payload)
    if not result.reachable or not isinstance(result.data, dict):
        return result.error or "n8n unreachable"
    row.n8n_workflow_id = str(result.data.get("id"))
    return None


@router.get("")
async def list_recipes(
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[RecipeOut]:
    rows = (
        await session.execute(select(AutomationRecipe).order_by(AutomationRecipe.id))
    ).scalars().all()
    return [_to_out(row) for row in rows]


@router.get("/{recipe_id}")
async def get_recipe(
    recipe_id: int,
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RecipeOut:
    row = await session.get(AutomationRecipe, recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    return _to_out(row)


class PreviewOut(BaseModel):
    summary: list[dict[str, Any]]
    has_write_external: bool
    workflow: dict[str, Any]


@router.post("/preview")
async def preview_recipe(
    body: RecipeIn,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
) -> PreviewOut:
    """Validate + compile without saving or deploying — what the builder's
    last wizard step shows before the user commits."""
    recipe = _parse(body)
    try:
        workflow = compile_recipe(recipe)
    except RecipeCompileError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PreviewOut(
        summary=describe_recipe(recipe),
        has_write_external=recipe.has_write_external,
        workflow=workflow,
    )


@router.post("", status_code=201)
async def create_recipe(
    body: RecipeIn,
    current: CurrentUser = Depends(get_current_user),  # noqa: B008
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RecipeOut:
    recipe = _parse(body)

    existing = (
        await session.execute(
            select(AutomationRecipe).where(AutomationRecipe.name == recipe.name)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"recipe already exists: {recipe.name}")

    row = AutomationRecipe(
        name=recipe.name,
        description=recipe.description,
        definition=recipe.model_dump(mode="json"),
        created_by=current.sub,
    )
    session.add(row)
    await session.flush()

    deploy_error = await _deploy(recipe, row, client)
    await session.commit()
    await session.refresh(row)
    return _to_out(row, deploy_error=deploy_error)


@router.put("/{recipe_id}")
async def update_recipe(
    recipe_id: int,
    body: RecipeIn,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RecipeOut:
    row = await session.get(AutomationRecipe, recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="recipe not found")

    recipe = _parse(body)
    if recipe.name != row.name:
        raise HTTPException(
            status_code=422,
            detail="a recipe's name is its n8n workflow identity and cannot be changed",
        )

    row.description = recipe.description
    row.definition = recipe.model_dump(mode="json")
    deploy_error = await _deploy(recipe, row, client)
    await session.commit()
    await session.refresh(row)
    return _to_out(row, deploy_error=deploy_error)


class RecipeActionOut(BaseModel):
    status: str  # "ok" | "n8n_unreachable" | "not_deployed" | "trigger_failed"
    detail: str | None = None


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RecipeActionOut:
    row = await session.get(AutomationRecipe, recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="recipe not found")

    detail = None
    if row.n8n_workflow_id:
        result = await client.delete_workflow(row.n8n_workflow_id)
        if not result.reachable:
            # The row still goes, so the UI does not strand a recipe the user
            # asked to remove; the orphan workflow is named in the response.
            detail = f"n8n unreachable — workflow {workflow_name(row.name)} may still exist"

    await session.delete(row)
    await session.commit()
    return RecipeActionOut(status="ok", detail=detail)


@router.post("/{recipe_id}/activate")
async def activate_recipe(
    recipe_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RecipeActionOut:
    return await _set_active(recipe_id, True, session, client)


@router.post("/{recipe_id}/deactivate")
async def deactivate_recipe(
    recipe_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RecipeActionOut:
    return await _set_active(recipe_id, False, session, client)


async def _set_active(
    recipe_id: int, active: bool, session: AsyncSession, client: N8nClient
) -> RecipeActionOut:
    row = await session.get(AutomationRecipe, recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    if not row.n8n_workflow_id:
        return RecipeActionOut(status="not_deployed", detail="recipe was never deployed to n8n")

    result = await client.set_active(row.n8n_workflow_id, active)
    if not result.reachable:
        return RecipeActionOut(status="n8n_unreachable", detail=result.error)
    if result.error:
        return RecipeActionOut(status="trigger_failed", detail=result.error)
    row.active = active
    await session.commit()
    return RecipeActionOut(status="ok")


@router.post("/{recipe_id}/run", status_code=202)
async def run_recipe(
    recipe_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    client: N8nClient = Depends(get_n8n_client),  # noqa: B008
) -> RecipeActionOut:
    """Trigger the recipe's manual webhook. Every compiled recipe carries one,
    scheduled ones included, so "Run now" works without waiting for the cron."""
    row = await session.get(AutomationRecipe, recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    if not row.active:
        return RecipeActionOut(
            status="not_deployed", detail="activate the recipe before running it"
        )

    result = await client.trigger_webhook_json(webhook_path(row.name), {})
    if not result.reachable:
        return RecipeActionOut(status="n8n_unreachable", detail=result.error)
    if result.error:
        # `reachable` only means n8n answered. A 404 here means the production
        # webhook is not registered even though the workflow is active — real
        # enough to have shipped a green "accepted" over a run that never
        # happened, so a non-2xx is reported as a failure, not a success.
        return RecipeActionOut(status="trigger_failed", detail=result.error)
    return RecipeActionOut(status="ok")
