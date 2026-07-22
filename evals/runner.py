"""Eval runner (task 4.4, TRD §13.4): `make eval AGENT=x`.

Loads evals/datasets/<agent>.jsonl, runs each case through the real Support
Copilot RAG pipeline (fleet_rag.query.service.answer_query against the live
gateway/Qdrant, same as the chat endpoint's RAG path), checks assertions, and
exits non-zero if the pass rate is below the agent's threshold in
evals/config.yaml. Results are also written back to the `eval_datasets`/
`eval_runs` table shape (TRD §11) is deferred — CLAUDE.md rule 5 only requires
pasting the pass rate in the PR for prompt changes, which the console summary
below already provides.

evaluate_case()/load_dataset() are pure and unit-tested without any network
call (tests/unit/test_eval_runner.py); only main()/run_agent_eval() do I/O.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

EVALS_DIR = Path(__file__).resolve().parent


def _use_utf8_stdout() -> None:
    """Windows' console defaults to cp1252, which can't encode Turkish
    characters (ş, ı, ğ, ...) in eval questions/answers — force UTF-8 stdout
    so `make eval` doesn't crash mid-run on a case that happens to fail.
    Only called from main(), never at import time: reassigning sys.stdout on
    import breaks pytest's output capture for the whole session when this
    module is imported by a test."""
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    must_contain: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)
    must_cite: bool = False
    must_refuse: bool = False


@dataclass(frozen=True)
class RagAnswer:
    text: str
    citation_count: int
    degraded: bool


@dataclass(frozen=True)
class CaseResult:
    id: str
    passed: bool
    reason: str


def load_dataset(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cases.append(
            EvalCase(
                id=row["id"],
                question=row["question"],
                must_contain=row.get("must_contain", []),
                must_not_contain=row.get("must_not_contain", []),
                must_cite=row.get("must_cite", False),
                must_refuse=row.get("must_refuse", False),
            )
        )
    return cases


def _fold(text: str) -> str:
    """Case-fold for substring matching, Turkish-safe: plain str.lower() turns
    'İ' into 'i' + a combining dot (U+0307), which then fails to match a plain
    ASCII 'i' in the dataset's must_contain/must_not_contain phrases. Stripping
    combining marks after lowering avoids that."""
    lowered = text.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", lowered) if unicodedata.category(c) != "Mn"
    )


def evaluate_case(case: EvalCase, answer: RagAnswer) -> CaseResult:
    text_lower = _fold(answer.text)

    for phrase in case.must_contain:
        if _fold(phrase) not in text_lower:
            return CaseResult(
                id=case.id, passed=False,
                reason=f"expected answer to contain {phrase!r}",
            )

    for phrase in case.must_not_contain:
        if _fold(phrase) in text_lower:
            return CaseResult(
                id=case.id, passed=False,
                reason=f"answer must not contain {phrase!r} but did",
            )

    if case.must_cite and answer.citation_count < 1:
        return CaseResult(id=case.id, passed=False, reason="expected >=1 citation, got 0")

    if case.must_refuse and not answer.degraded:
        return CaseResult(
            id=case.id, passed=False, reason="expected a degraded/refused answer"
        )

    return CaseResult(id=case.id, passed=True, reason="ok")


async def _run_case(case: EvalCase, *, agent_id: int, collection_ids: list[int]) -> RagAnswer:
    """Run one case through the real Support Copilot RAG pipeline."""
    from core.llm.factory import build_client
    from fleet_rag.query.retrieve import Hit
    from fleet_rag.query.service import AgentQueryConfig, answer_query
    from fleet_rag.store.qdrant_store import collection_name, qdrant_client_from_env, search_hybrid

    llm_client = await build_client()
    qdrant = qdrant_client_from_env()
    collection_names = [collection_name(cid) for cid in collection_ids]

    def _searcher(
        *, query_vector: list[float], top_k: int, keyword: str | None = None
    ) -> list[Hit]:
        hits: list[Hit] = []
        for qname in collection_names:
            points = search_hybrid(
                qdrant, qname, query_vector=query_vector, top_k=top_k, keyword=keyword
            )
            hits.extend(
                Hit(
                    id=str(p.id), score=p.score, document_id=p.payload["document_id"],
                    chunk_ref=p.payload["content_sha256"], content=p.payload["content"],
                    redacted=p.payload.get("redacted", False),
                )
                for p in points
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    answer = await answer_query(
        question=case.question,
        searcher=_searcher,
        embed_client=llm_client,
        reasoning_client=llm_client,
        config=AgentQueryConfig(top_k=5),
        sensitivity="internal",
        agent_id=str(agent_id),
    )
    return RagAnswer(
        text=answer.text, citation_count=len(answer.citations), degraded=answer.degraded
    )


async def run_agent_eval(agent_name: str) -> tuple[list[CaseResult], float, float]:
    """Returns (results, pass_rate, threshold)."""
    import os

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    config = yaml.safe_load((EVALS_DIR / "config.yaml").read_text(encoding="utf-8"))
    agent_config = config["agents"][agent_name]
    dataset_path = EVALS_DIR / agent_config["dataset"]
    threshold = float(agent_config["threshold"])
    cases = load_dataset(dataset_path)

    database_url = os.environ.get(
        "FLEET_DATABASE_URL", "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
    )
    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT id, collection_ids FROM agents WHERE name = :n"), {"n": agent_name}
            )
        ).first()
    await engine.dispose()
    if row is None:
        raise RuntimeError(f"agent {agent_name!r} not seeded — run `make seed` first")
    agent_id, collection_ids = int(row[0]), list(row[1])

    results = []
    for case in cases:
        answer = await _run_case(case, agent_id=agent_id, collection_ids=collection_ids)
        results.append(evaluate_case(case, answer))

    pass_rate = sum(1 for r in results if r.passed) / len(results) if results else 0.0
    return results, pass_rate, threshold


@dataclass(frozen=True)
class AnalyticsCase:
    id: str
    question: str
    expect_row_count: int | None = None
    sql_must_reference_table: str | None = None
    must_refuse: bool = False
    must_clarify: bool = False
    must_refuse_or_clarify: bool = False


@dataclass(frozen=True)
class AnalyticsAnswer:
    sql: str | None = None
    row_count: int | None = None
    refused: bool = False
    clarification: str | None = None


def load_analytics_dataset(path: Path) -> list[AnalyticsCase]:
    cases: list[AnalyticsCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cases.append(
            AnalyticsCase(
                id=row["id"],
                question=row["question"],
                expect_row_count=row.get("expect_row_count"),
                sql_must_reference_table=row.get("sql_must_reference_table"),
                must_refuse=row.get("must_refuse", False),
                must_clarify=row.get("must_clarify", False),
                must_refuse_or_clarify=row.get("must_refuse_or_clarify", False),
            )
        )
    return cases


def evaluate_analytics_case(case: AnalyticsCase, answer: AnalyticsAnswer) -> CaseResult:
    if case.must_refuse:
        if not answer.refused:
            return CaseResult(id=case.id, passed=False, reason="expected the query to be refused")
        return CaseResult(id=case.id, passed=True, reason="ok")

    if case.must_clarify:
        if not answer.clarification:
            return CaseResult(
                id=case.id, passed=False, reason="expected a clarifying question, got SQL"
            )
        return CaseResult(id=case.id, passed=True, reason="ok")

    if case.must_refuse_or_clarify:
        # A question naming a non-allowlisted table may be intercepted at
        # either layer: the SQL generator itself declines to guess a table
        # outside its semantic-layer glossary (clarification), or pg_ro's
        # allowlist refuses SQL that did get generated (refusal) — both are
        # correct outcomes of the guardrail (never a guessed/hallucinated
        # query over a forbidden table), so either satisfies this case.
        if not (answer.refused or answer.clarification):
            return CaseResult(
                id=case.id, passed=False,
                reason="expected a refusal or a clarifying question, got SQL",
            )
        return CaseResult(id=case.id, passed=True, reason="ok")

    if case.expect_row_count is not None and answer.row_count != case.expect_row_count:
        return CaseResult(
            id=case.id, passed=False,
            reason=f"expected {case.expect_row_count} rows, got {answer.row_count}",
        )

    if case.sql_must_reference_table is not None:
        sql = answer.sql or ""
        if case.sql_must_reference_table not in sql:
            return CaseResult(
                id=case.id, passed=False,
                reason=f"expected SQL to reference {case.sql_must_reference_table!r}",
            )

    return CaseResult(id=case.id, passed=True, reason="ok")


async def _run_analytics_case(case: AnalyticsCase) -> AnalyticsAnswer:
    """Run one case through the real Analytics agent pipeline (5.2)."""
    from agents.analytics.semantic_layer import DEFAULT_SEMANTIC_LAYER
    from agents.analytics.service import AnalyticsClarification, AnalyticsRefusal, ask_analytics
    from core.llm.factory import build_client
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool

    llm_client = await build_client()
    pg_tool = PgReadOnlyTool(
        runner=build_default_runner(),
        allowlisted_tables=DEFAULT_SEMANTIC_LAYER.allowlisted_tables(),
    )
    try:
        result = await ask_analytics(
            question=case.question,
            semantic_layer=DEFAULT_SEMANTIC_LAYER,
            llm_client=llm_client,
            pg_tool=pg_tool,
        )
    except AnalyticsClarification as exc:
        return AnalyticsAnswer(clarification=str(exc))
    except AnalyticsRefusal:
        return AnalyticsAnswer(refused=True)

    return AnalyticsAnswer(sql=result.sql, row_count=len(result.rows))


async def run_analytics_eval() -> tuple[list[CaseResult], float, float]:
    """Returns (results, pass_rate, threshold). Same shape as run_agent_eval()
    but over AnalyticsCase/AnalyticsAnswer instead of the RAG-specific types —
    Analytics has no collection_ids and doesn't need the agents-table lookup
    run_agent_eval() does for RAG agents."""
    config = yaml.safe_load((EVALS_DIR / "config.yaml").read_text(encoding="utf-8"))
    agent_config = config["agents"]["analytics"]
    dataset_path = EVALS_DIR / agent_config["dataset"]
    threshold = float(agent_config["threshold"])
    cases = load_analytics_dataset(dataset_path)

    results = []
    for case in cases:
        answer = await _run_analytics_case(case)
        results.append(evaluate_analytics_case(case, answer))

    pass_rate = sum(1 for r in results if r.passed) / len(results) if results else 0.0
    return results, pass_rate, threshold


def main() -> None:
    import asyncio

    _use_utf8_stdout()

    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    args = parser.parse_args()

    if args.agent == "analytics":
        results, pass_rate, threshold = asyncio.run(run_analytics_eval())
    else:
        results, pass_rate, threshold = asyncio.run(run_agent_eval(args.agent))

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.id}: {r.reason}")

    print(f"\n{args.agent}: {pass_rate:.0%} pass rate ({threshold:.0%} required)")
    if pass_rate < threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
