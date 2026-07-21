"""Kill switches: per-agent pause + global read-only mode (TRD §9).

Per-agent `status=paused` must take effect within 5s without hitting Redis on
every single call, so a positive/negative pause lookup is cached in-process
for 5s per agent_id. Global read-only mode has no such cache — it's a rare,
deliberate admin action and every `write:*` tool call must see it immediately.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Protocol

_PAUSE_CACHE_TTL = dt.timedelta(seconds=5)
_GLOBAL_READ_ONLY_KEY = "global:read_only"


class RedisLike(Protocol):
    # redis-py returns bytes unless the client is built with
    # decode_responses=True — callers may or may not have set that, so every
    # read here treats the value as str | bytes | None rather than assuming.
    async def get(self, key: str) -> str | bytes | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> None: ...


def _is_flag_set(value: str | bytes | None) -> bool:
    if value is None:
        return False
    if isinstance(value, bytes):
        return value == b"1"
    return value == "1"


def _pause_key(agent_id: str) -> str:
    return f"agent:paused:{agent_id}"


def _default_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class KillSwitch:
    """Runtime-side enforcement, checked before any graph node runs a step."""

    def __init__(
        self, redis: RedisLike, *, now: Callable[[], dt.datetime] = _default_now
    ) -> None:
        self._redis = redis
        self._now = now
        self._pause_cache: dict[str, tuple[bool, dt.datetime]] = {}

    async def is_agent_paused(self, agent_id: str) -> bool:
        cached = self._pause_cache.get(agent_id)
        current_time = self._now()
        if cached is not None and current_time - cached[1] < _PAUSE_CACHE_TTL:
            return cached[0]

        value = await self._redis.get(_pause_key(agent_id))
        paused = _is_flag_set(value)
        self._pause_cache[agent_id] = (paused, current_time)
        return paused

    async def blocks_tool(self, *, risk_class: str) -> bool:
        if not risk_class.startswith("write:"):
            return False
        value = await self._redis.get(_GLOBAL_READ_ONLY_KEY)
        return _is_flag_set(value)

    async def pause_agent(self, agent_id: str) -> None:
        await self._redis.set(_pause_key(agent_id), "1")

    async def resume_agent(self, agent_id: str) -> None:
        await self._redis.set(_pause_key(agent_id), "0")

    async def set_global_read_only(self, enabled: bool) -> None:
        await self._redis.set(_GLOBAL_READ_ONLY_KEY, "1" if enabled else "0")
