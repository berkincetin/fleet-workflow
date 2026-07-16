"""Append-only audit log writes."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def write_audit(
    engine: AsyncEngine,
    *,
    actor: str,
    actor_type: str,
    action: str,
    entity: str | None = None,
    entity_id: str | None = None,
    trace_id: str | None = None,
) -> None:
    """Insert one append-only audit row. Never updates or deletes."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO audit_log "
                "(actor, actor_type, action, entity, entity_id, trace_id) "
                "VALUES (:actor, :actor_type, :action, :entity, :entity_id, :trace_id)"
            ),
            {
                "actor": actor,
                "actor_type": actor_type,
                "action": action,
                "entity": entity,
                "entity_id": entity_id,
                "trace_id": trace_id,
            },
        )
