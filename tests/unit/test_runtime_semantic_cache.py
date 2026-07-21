"""core.semantic_cache: Redis-backed semantic cache (task 4.2, TRD §5).

Opt-in per agent (only deterministic Q&A agents). Cosine similarity of the
normalized query embedding against cached entries in the same agent+collection
scope; a hit >= threshold serves the cached answer with a "cached" badge.
TTL default 24h; invalidated on KB collection update (bump a per-collection
generation counter rather than scanning/deleting every cached key).
"""

from __future__ import annotations

from core.semantic_cache import SemanticCache


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    async def keys(self, pattern: str) -> list[str]:
        prefix = pattern.rstrip("*")
        return [k for k in self.store if k.startswith(prefix)]

    async def incr(self, key: str) -> int:
        current = int(self.store.get(key, "0")) + 1
        self.store[key] = str(current)
        return current


def _vec(*values: float) -> list[float]:
    return list(values)


async def test_miss_when_cache_empty() -> None:
    cache = SemanticCache(_FakeRedis(), threshold=0.95)
    hit = await cache.lookup(agent_id="support_copilot", collection_id=1, embedding=_vec(1, 0))
    assert hit is None


async def test_hit_on_near_identical_embedding_above_threshold() -> None:
    redis = _FakeRedis()
    cache = SemanticCache(redis, threshold=0.95)
    await cache.store(
        agent_id="support_copilot", collection_id=1, embedding=_vec(1, 0), answer="cached answer"
    )
    hit = await cache.lookup(
        agent_id="support_copilot", collection_id=1, embedding=_vec(0.999, 0.001)
    )
    assert hit is not None
    assert hit.answer == "cached answer"
    assert hit.cached is True


async def test_miss_when_similarity_below_threshold() -> None:
    redis = _FakeRedis()
    cache = SemanticCache(redis, threshold=0.95)
    await cache.store(
        agent_id="support_copilot", collection_id=1, embedding=_vec(1, 0), answer="cached answer"
    )
    hit = await cache.lookup(agent_id="support_copilot", collection_id=1, embedding=_vec(0, 1))
    assert hit is None


async def test_cache_is_scoped_per_agent_and_collection() -> None:
    redis = _FakeRedis()
    cache = SemanticCache(redis, threshold=0.95)
    await cache.store(
        agent_id="support_copilot", collection_id=1, embedding=_vec(1, 0), answer="answer A"
    )
    # Same embedding, different agent -> no cross-agent leakage.
    other_agent = await cache.lookup(agent_id="other_agent", collection_id=1, embedding=_vec(1, 0))
    assert other_agent is None
    # Same embedding, different collection -> no cross-collection leakage.
    other_collection = await cache.lookup(
        agent_id="support_copilot", collection_id=2, embedding=_vec(1, 0)
    )
    assert other_collection is None


async def test_invalidate_collection_bumps_generation_and_misses_old_entries() -> None:
    redis = _FakeRedis()
    cache = SemanticCache(redis, threshold=0.95)
    await cache.store(
        agent_id="support_copilot", collection_id=1, embedding=_vec(1, 0), answer="stale answer"
    )
    await cache.invalidate_collection(collection_id=1)

    hit = await cache.lookup(agent_id="support_copilot", collection_id=1, embedding=_vec(1, 0))
    assert hit is None


async def test_store_defaults_to_24h_ttl() -> None:
    class _RecordingRedis(_FakeRedis):
        def __init__(self) -> None:
            super().__init__()
            self.set_calls: list[tuple[str, str, int | None]] = []

        async def set(self, key: str, value: str, ex: int | None = None) -> None:
            self.set_calls.append((key, value, ex))
            await super().set(key, value, ex=ex)

    redis = _RecordingRedis()
    cache = SemanticCache(redis, threshold=0.95)
    await cache.store(agent_id="a", collection_id=1, embedding=_vec(1, 0), answer="x")
    assert redis.set_calls[-1][2] == 24 * 3600
