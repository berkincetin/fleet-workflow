"""core.killswitch: per-agent pause + global read-only mode (task 4.2, TRD §9).

Per-agent `status=paused` must be enforced before any graph node runs, checked
against Redis with a 5s cache so a pause takes effect within 5s without a
Redis round-trip on every single call. Global read-only mode blocks all
`write:*` tool risk_classes regardless of per-agent status.
"""

from __future__ import annotations

import datetime as dt

from core.killswitch import KillSwitch


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.get_calls = 0

    async def get(self, key: str) -> str | None:
        self.get_calls += 1
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value


class _Clock:
    def __init__(self, start: dt.datetime) -> None:
        self.now = start

    def __call__(self) -> dt.datetime:
        return self.now


async def test_agent_is_active_when_not_paused_in_redis() -> None:
    redis = _FakeRedis()
    ks = KillSwitch(redis)
    assert await ks.is_agent_paused("support_copilot") is False


async def test_agent_is_paused_when_redis_flag_set() -> None:
    redis = _FakeRedis()
    redis.store["agent:paused:support_copilot"] = "1"
    ks = KillSwitch(redis)
    assert await ks.is_agent_paused("support_copilot") is True


async def test_pause_check_is_cached_for_5s_no_repeat_redis_call() -> None:
    redis = _FakeRedis()
    clock = _Clock(dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    ks = KillSwitch(redis, now=clock)

    await ks.is_agent_paused("support_copilot")
    await ks.is_agent_paused("support_copilot")
    assert redis.get_calls == 1  # second call served from the 5s cache


async def test_pause_check_refetches_after_5s_elapses() -> None:
    redis = _FakeRedis()
    clock = _Clock(dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    ks = KillSwitch(redis, now=clock)

    await ks.is_agent_paused("support_copilot")
    clock.now += dt.timedelta(seconds=6)
    await ks.is_agent_paused("support_copilot")
    assert redis.get_calls == 2


async def test_pause_cache_is_scoped_per_agent() -> None:
    redis = _FakeRedis()
    redis.store["agent:paused:agent_a"] = "1"
    ks = KillSwitch(redis)
    assert await ks.is_agent_paused("agent_a") is True
    assert await ks.is_agent_paused("agent_b") is False


async def test_global_read_only_blocks_write_tool() -> None:
    redis = _FakeRedis()
    redis.store["global:read_only"] = "1"
    ks = KillSwitch(redis)
    assert await ks.blocks_tool(risk_class="write:internal") is True
    assert await ks.blocks_tool(risk_class="write:external") is True


async def test_global_read_only_never_blocks_read_tool() -> None:
    redis = _FakeRedis()
    redis.store["global:read_only"] = "1"
    ks = KillSwitch(redis)
    assert await ks.blocks_tool(risk_class="read") is False


async def test_no_read_only_flag_allows_write_tool() -> None:
    redis = _FakeRedis()
    ks = KillSwitch(redis)
    assert await ks.blocks_tool(risk_class="write:internal") is False


async def test_agent_paused_when_redis_returns_raw_bytes() -> None:
    """redis-py returns bytes unless decode_responses=True was set on the
    client — a real caller that forgot that flag must still be enforced
    correctly rather than silently treating "paused" as "active"."""

    class _BytesRedis(_FakeRedis):
        async def get(self, key: str) -> str | None:  # type: ignore[override]
            value = self.store.get(key)
            return value.encode() if value is not None else None

    redis = _BytesRedis()
    redis.store["agent:paused:support_copilot"] = "1"
    ks = KillSwitch(redis)
    assert await ks.is_agent_paused("support_copilot") is True


async def test_global_read_only_blocks_when_redis_returns_raw_bytes() -> None:
    class _BytesRedis(_FakeRedis):
        async def get(self, key: str) -> str | None:  # type: ignore[override]
            value = self.store.get(key)
            return value.encode() if value is not None else None

    redis = _BytesRedis()
    redis.store["global:read_only"] = "1"
    ks = KillSwitch(redis)
    assert await ks.blocks_tool(risk_class="write:internal") is True
