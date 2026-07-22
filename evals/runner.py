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
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

EVALS_DIR = Path(__file__).resolve().parent

_ENV_LINE_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)=(.*)$")


def _load_dotenv_fallback() -> None:
    """.env is a Docker Compose convention in this repo (see
    apps/api/fleet_api/config.py — no env_file configured, pydantic-settings
    never auto-loads it), so a standalone script like this one needs its own
    fallback to pick up FLEET_GITHUB_SANDBOX_TOKEN etc. for dev_agent evals.
    Same pattern as tests/integration/test_mcp_github_live.py."""
    env_path = EVALS_DIR.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        match = _ENV_LINE_RE.match(line.strip())
        if match and match.group(1) not in os.environ:
            os.environ[match.group(1)] = match.group(2)


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


@dataclass(frozen=True)
class DevAgentCase:
    id: str
    ticket_key: str
    expect_pending_approval: bool = False
    expect_blocked: bool = False
    must_target_path_containing: str | None = None


@dataclass(frozen=True)
class DevAgentAnswer:
    pending_approval: bool = False
    blocked_reason: str | None = None
    branch_name: str | None = None
    target_paths: list[str] = field(default_factory=list)


def load_dev_agent_dataset(path: Path) -> list[DevAgentCase]:
    cases: list[DevAgentCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cases.append(
            DevAgentCase(
                id=row["id"],
                ticket_key=row["ticket_key"],
                expect_pending_approval=row.get("expect_pending_approval", False),
                expect_blocked=row.get("expect_blocked", False),
                must_target_path_containing=row.get("must_target_path_containing"),
            )
        )
    return cases


def evaluate_dev_agent_case(case: DevAgentCase, answer: DevAgentAnswer) -> CaseResult:
    if case.expect_blocked:
        if not answer.blocked_reason:
            return CaseResult(id=case.id, passed=False, reason="expected the run to be blocked")
        return CaseResult(id=case.id, passed=True, reason="ok")

    if case.expect_pending_approval:
        if not answer.pending_approval:
            return CaseResult(
                id=case.id, passed=False, reason="expected the run to reach pending_approval"
            )
        # Branch-name compliance: proven structurally (GitHubTool refuses any
        # non-agent/* name before ever creating a branch, task 5.3), but
        # re-asserted here on the branch a real successful run actually used —
        # a regression in that guard would show up as a failed eval, not just
        # a passing unit test that never exercises the real graph.
        if not (answer.branch_name or "").startswith("agent/"):
            return CaseResult(
                id=case.id, passed=False,
                reason=f"branch name {answer.branch_name!r} does not start with 'agent/'",
            )
        if case.must_target_path_containing is not None:
            if not any(
                case.must_target_path_containing in p for p in answer.target_paths
            ):
                return CaseResult(
                    id=case.id, passed=False,
                    reason=(
                        f"expected a target path containing "
                        f"{case.must_target_path_containing!r}, got {answer.target_paths!r}"
                    ),
                )
        return CaseResult(id=case.id, passed=True, reason="ok")

    return CaseResult(id=case.id, passed=True, reason="ok")


async def _run_dev_agent_case(case: DevAgentCase) -> DevAgentAnswer:
    """Run one case through the real Dev Agent graph (5.5) — real gateway
    client, real fixture Jira backend, real GitHub sandbox (create_branch/
    commit_file only; open_pr is never reached since evals never approve).
    """
    from agents.dev_agent.graph import build_dev_agent_graph
    from core.llm.factory import build_client
    from fleet_mcp.servers.github import GitHubTool
    from fleet_mcp.servers.github import build_default_backend as build_github_backend
    from fleet_mcp.servers.jira import JiraTool
    from fleet_mcp.servers.jira import build_default_backend as build_jira_backend
    from fleet_mcp.servers.slack import SlackPostTool, build_default_sender
    from langgraph.checkpoint.memory import InMemorySaver

    llm_client = await build_client()
    jira = JiraTool(backend=build_jira_backend())
    github = GitHubTool(backend=build_github_backend())
    slack = SlackPostTool(sender=build_default_sender(), allowed_channels={"#dev-agent"})

    graph = build_dev_agent_graph(
        llm_client=llm_client, jira=jira, github=github, slack=slack,
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": f"eval-{case.id}"}}
    result = await graph.ainvoke({"ticket_key": case.ticket_key}, config)

    if result.get("blocked_reason"):
        return DevAgentAnswer(blocked_reason=result["blocked_reason"])
    if "__interrupt__" in result:
        args = result["__interrupt__"][0].value["args"]
        plan_target_paths = result.get("plan", {}).get("target_paths", [])
        return DevAgentAnswer(
            pending_approval=True, branch_name=args["branch_name"],
            target_paths=plan_target_paths,
        )
    return DevAgentAnswer()


async def run_dev_agent_eval() -> tuple[list[CaseResult], float, float]:
    """Returns (results, pass_rate, threshold). Never approves/rejects — each
    case's run stays parked at its interrupt (or blocked earlier), so evals
    never open a real PR on the sandbox repo, only create_branch/commit_file
    (both write:internal, no approval queue side effect to worry about)."""
    config = yaml.safe_load((EVALS_DIR / "config.yaml").read_text(encoding="utf-8"))
    agent_config = config["agents"]["dev_agent"]
    dataset_path = EVALS_DIR / agent_config["dataset"]
    threshold = float(agent_config["threshold"])
    cases = load_dev_agent_dataset(dataset_path)

    results = []
    for case in cases:
        answer = await _run_dev_agent_case(case)
        results.append(evaluate_dev_agent_case(case, answer))

    pass_rate = sum(1 for r in results if r.passed) / len(results) if results else 0.0
    return results, pass_rate, threshold


def main() -> None:
    import asyncio

    _use_utf8_stdout()
    _load_dotenv_fallback()

    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    args = parser.parse_args()

    if args.agent == "analytics":
        results, pass_rate, threshold = asyncio.run(run_analytics_eval())
    elif args.agent == "dev_agent":
        results, pass_rate, threshold = asyncio.run(run_dev_agent_eval())
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
