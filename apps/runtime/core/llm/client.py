"""LLM gateway client — the only place provider LLM calls are made (CLAUDE.md rule 1).

Responsibilities (TRD §4.3, §5, §8):
- tiering helpers ``reasoning()`` / ``utility()`` that choose a model per call-site;
- sensitivity routing enforcement (via ``core.llm.routing``) applied BEFORE any
  transport call — a refused request never leaves the process;
- delegate retries + fallback chains to the LiteLLM proxy (configured in
  gateway/litellm/config.yaml, §4.4); surface a clean ``GatewayError`` if the
  chain is still exhausted;
- capture token usage + cost and append a ``spend_ledger`` row (§5).

Transport and ledger are injected behind small protocols so the orchestration is
unit-testable without network or DB; the concrete implementations live in
``core.llm.transport`` and ``core.llm.ledger``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.llm.budget import BudgetStatus
from core.llm.cost import compute_cost, parse_usage
from core.llm.routing import Sensitivity, select_model


class Transport(Protocol):
    """Sends a chat completion to the proxy and returns the raw response body."""

    async def complete(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> dict[str, Any]: ...

    async def embed(
        self, *, model: str, input: list[str], **kwargs: Any
    ) -> dict[str, Any]: ...

    async def stream_complete(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]: ...


class Ledger(Protocol):
    """Persists a spend_ledger row."""

    async def record(self, row: dict[str, Any]) -> None: ...


class BudgetChecker(Protocol):
    """Evaluates the request's budget scope; raises BudgetExceeded on hard stop."""

    async def __call__(self, meta: dict[str, Any]) -> BudgetStatus: ...


class GatewayError(Exception):
    """The proxy call failed after its retries + fallback chain (§4.4)."""


@dataclass
class EmbeddingResponse:
    """A completed embeddings call: the served model, vectors, usage, cost."""

    model: str
    vectors: list[list[float]]
    tok_in: int
    cost_usd: float
    raw: dict[str, Any]


@dataclass
class LLMResponse:
    """A completed LLM call: the served model, text, token usage, and cost."""

    model: str
    content: str
    tok_in: int
    tok_out: int
    tok_cached: int
    cost_usd: float
    raw: dict[str, Any]
    # §5 budget: True when the request's scope is at/over its soft limit (80%).
    budget_soft_exceeded: bool = False
    budget: BudgetStatus | None = field(default=None, repr=False)


def _first_content(body: dict[str, Any]) -> str:
    choices = body.get("choices") or []
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "") or ""


class LLMClient:
    """Governed entry point for LLM calls. Construct once per process with the
    model registry rows, a transport, and a ledger sink."""

    def __init__(
        self,
        *,
        models: list[dict[str, Any]],
        transport: Transport,
        ledger: Ledger,
        budget_checker: BudgetChecker | None = None,
    ) -> None:
        self._models = models
        self._transport = transport
        self._ledger = ledger
        self._budget_checker = budget_checker

    async def reasoning(
        self,
        messages: list[dict[str, Any]],
        *,
        sensitivity: str | Sensitivity = "internal",
        redacted: bool = False,
        **meta: Any,
    ) -> LLMResponse:
        """Planning / generation / judgment call-sites (§4.3)."""
        return await self._call("reasoning", messages, sensitivity, redacted, meta)

    async def utility(
        self,
        messages: list[dict[str, Any]],
        *,
        sensitivity: str | Sensitivity = "internal",
        redacted: bool = False,
        **meta: Any,
    ) -> LLMResponse:
        """Classification / extraction / routing / summarization call-sites (§4.3)."""
        return await self._call("utility", messages, sensitivity, redacted, meta)

    async def reasoning_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        sensitivity: str | Sensitivity = "internal",
        redacted: bool = False,
        **meta: Any,
    ) -> AsyncIterator[str]:
        """Streaming variant of reasoning() for SSE chat (§4.3, TRD §5 "streaming
        everywhere"). Sensitivity + budget are enforced before the first chunk is
        requested, same as the non-streaming call; the spend row is recorded once
        the stream is exhausted and usage is known."""
        # 1/2. Same enforcement as _call, before any transport call.
        model = select_model(
            self._models, role="reasoning", sensitivity=sensitivity, redacted=redacted
        )
        name = model["name"]

        budget: BudgetStatus | None = None
        if self._budget_checker is not None:
            budget = await self._budget_checker(meta)
            budget.raise_if_exceeded()

        try:
            chunks = await self._transport.stream_complete(model=name, messages=messages, **meta)
        except GatewayError:
            raise
        except Exception as exc:
            raise GatewayError(f"gateway stream call failed for model {name!r}: {exc}") from exc

        served = name
        usage_body: dict[str, Any] = {}
        try:
            async for chunk in chunks:
                served = chunk.get("model", served)
                if chunk.get("usage"):
                    usage_body = chunk
                delta = chunk.get("delta", "")
                if delta:
                    yield delta
        except GatewayError:
            raise
        except Exception as exc:
            raise GatewayError(f"gateway stream call failed for model {name!r}: {exc}") from exc

        priced = self._price_for(served, fallback=model)
        usage = parse_usage(usage_body)
        cost = compute_cost(
            usage,
            input_price_per_1k=float(priced.get("input_price_per_1k", 0.0)),
            output_price_per_1k=float(priced.get("output_price_per_1k", 0.0)),
            cached_input_price_per_1k=_opt_float(priced.get("cached_input_price")),
        )
        await self._ledger.record(
            {
                "model": served,
                "agent_id": meta.get("agent_id"),
                "user_id": meta.get("user_id"),
                "dept_id": meta.get("dept_id"),
                "tok_in": usage.tok_in,
                "tok_out": usage.tok_out,
                "tok_cached": usage.tok_cached,
                "cost_usd": cost,
                "trace_id": meta.get("trace_id"),
            }
        )

    async def embeddings(
        self,
        texts: list[str],
        *,
        sensitivity: str | Sensitivity = "internal",
        redacted: bool = False,
        **meta: Any,
    ) -> EmbeddingResponse:
        """RAG ingestion/query embedding call-sites (§3.1, §3.3)."""
        model = select_model(
            self._models, role="embeddings", sensitivity=sensitivity, redacted=redacted
        )
        name = model["name"]

        budget: BudgetStatus | None = None
        if self._budget_checker is not None:
            budget = await self._budget_checker(meta)
            budget.raise_if_exceeded()

        try:
            body = await self._transport.embed(model=name, input=texts, **meta)
        except GatewayError:
            raise
        except Exception as exc:
            raise GatewayError(f"gateway embed call failed for model {name!r}: {exc}") from exc

        served = body.get("model", name)
        priced = self._price_for(served, fallback=model)
        usage = parse_usage(body)
        cost = compute_cost(
            usage,
            input_price_per_1k=float(priced.get("input_price_per_1k", 0.0)),
            output_price_per_1k=float(priced.get("output_price_per_1k", 0.0)),
        )

        await self._ledger.record(
            {
                "model": served,
                "agent_id": meta.get("agent_id"),
                "user_id": meta.get("user_id"),
                "dept_id": meta.get("dept_id"),
                "tok_in": usage.tok_in,
                "tok_out": 0,
                "tok_cached": 0,
                "cost_usd": cost,
                "trace_id": meta.get("trace_id"),
            }
        )

        data = sorted(body.get("data") or [], key=lambda d: d.get("index", 0))
        vectors = [d["embedding"] for d in data]

        return EmbeddingResponse(
            model=served, vectors=vectors, tok_in=usage.tok_in, cost_usd=cost, raw=body
        )

    async def _call(
        self,
        role: str,
        messages: list[dict[str, Any]],
        sensitivity: str | Sensitivity,
        redacted: bool,
        meta: dict[str, Any],
    ) -> LLMResponse:
        # 1. Enforce sensitivity FIRST — a refusal must never reach the transport.
        model = select_model(
            self._models, role=role, sensitivity=sensitivity, redacted=redacted
        )
        name = model["name"]

        # 2. Budget pre-check (CLAUDE.md rule 6). A hard stop (100%) raises
        #    BudgetExceeded before any call; a soft limit (80%) is flagged on the
        #    response. No checker → no enforcement.
        budget: BudgetStatus | None = None
        if self._budget_checker is not None:
            budget = await self._budget_checker(meta)
            budget.raise_if_exceeded()

        # 3. Call the proxy (it owns retries + the fallback chain, §4.4). Forward
        #    trace_id/agent_id/user_id/dept_id so the proxy's Langfuse callback
        #    (§6) tags the trace with the SAME id spend_ledger.trace_id records —
        #    otherwise Langfuse mints its own random trace id and the two never
        #    correlate (caught while wiring 4.3's feedback→Langfuse score path).
        try:
            body = await self._transport.complete(model=name, messages=messages, **meta)
        except GatewayError:
            raise
        except Exception as exc:  # transport/provider error after fallbacks
            raise GatewayError(f"gateway call failed for model {name!r}: {exc}") from exc

        # 4. Meter usage + cost. The served model may differ from the requested
        #    one when the proxy fell back; bill the model it actually reports.
        served = body.get("model", name)
        priced = self._price_for(served, fallback=model)
        usage = parse_usage(body)
        cost = compute_cost(
            usage,
            input_price_per_1k=float(priced.get("input_price_per_1k", 0.0)),
            output_price_per_1k=float(priced.get("output_price_per_1k", 0.0)),
            cached_input_price_per_1k=_opt_float(priced.get("cached_input_price")),
        )

        # 5. Append the spend row (§5 spend ledger).
        await self._ledger.record(
            {
                "model": served,
                "agent_id": meta.get("agent_id"),
                "user_id": meta.get("user_id"),
                "dept_id": meta.get("dept_id"),
                "tok_in": usage.tok_in,
                "tok_out": usage.tok_out,
                "tok_cached": usage.tok_cached,
                "cost_usd": cost,
                "trace_id": meta.get("trace_id"),
            }
        )

        return LLMResponse(
            model=served,
            content=_first_content(body),
            tok_in=usage.tok_in,
            tok_out=usage.tok_out,
            tok_cached=usage.tok_cached,
            cost_usd=cost,
            raw=body,
            budget_soft_exceeded=bool(budget and budget.soft_exceeded),
            budget=budget,
        )

    def _price_for(
        self, model_name: str, *, fallback: dict[str, Any]
    ) -> dict[str, Any]:
        for m in self._models:
            if m["name"] == model_name or m.get("litellm_model_id") == model_name:
                return m
        return fallback


def _opt_float(value: Any) -> float | None:
    return float(value) if value is not None else None
