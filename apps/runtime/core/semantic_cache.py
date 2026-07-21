"""Redis-backed semantic cache (TRD §5).

Opt-in per agent (deterministic Q&A agents only, per AgentSpec). A lookup
computes cosine similarity between the query's embedding and cached entries
scoped to the same (agent_id, collection_id, generation); a hit at or above
`threshold` serves the cached answer with `cached=True`. Entries default to a
24h TTL. `invalidate_collection` bumps a per-collection generation counter so
every prior entry for that collection stops matching on the next lookup,
without needing to enumerate and delete each key.

Similarity is computed by scanning cached entries in the current generation —
fine at demo/dev scale (a handful of collections, hundreds of cached answers);
a production-scale cache would back this with a vector index instead of
Redis KEYS + Python-side cosine.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from typing import Protocol

_DEFAULT_TTL_SECONDS = 24 * 3600


class RedisLike(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> None: ...
    async def keys(self, pattern: str) -> list[str]: ...
    async def incr(self, key: str) -> int: ...


@dataclass(frozen=True)
class CacheHit:
    answer: str
    cached: bool = True


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    def __init__(self, redis: RedisLike, *, threshold: float = 0.95) -> None:
        self._redis = redis
        self._threshold = threshold

    def _generation_key(self, collection_id: int) -> str:
        return f"semcache:gen:{collection_id}"

    async def _generation(self, collection_id: int) -> int:
        raw = await self._redis.get(self._generation_key(collection_id))
        return int(raw) if raw is not None else 0

    def _prefix(self, agent_id: str, collection_id: int, generation: int) -> str:
        return f"semcache:{agent_id}:{collection_id}:{generation}:"

    async def lookup(
        self, *, agent_id: str, collection_id: int, embedding: list[float]
    ) -> CacheHit | None:
        generation = await self._generation(collection_id)
        prefix = self._prefix(agent_id, collection_id, generation)
        keys = await self._redis.keys(f"{prefix}*")

        best_score = -1.0
        best_answer: str | None = None
        for key in keys:
            raw = await self._redis.get(key)
            if raw is None:
                continue
            entry = json.loads(raw)
            score = _cosine(embedding, entry["embedding"])
            if score > best_score:
                best_score = score
                best_answer = entry["answer"]

        if best_answer is not None and best_score >= self._threshold:
            return CacheHit(answer=best_answer)
        return None

    async def store(
        self,
        *,
        agent_id: str,
        collection_id: int,
        embedding: list[float],
        answer: str,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        generation = await self._generation(collection_id)
        prefix = self._prefix(agent_id, collection_id, generation)
        key = f"{prefix}{uuid.uuid4()}"
        payload = json.dumps({"embedding": embedding, "answer": answer})
        await self._redis.set(key, payload, ex=ttl_seconds)

    async def invalidate_collection(self, *, collection_id: int) -> None:
        await self._redis.incr(self._generation_key(collection_id))
