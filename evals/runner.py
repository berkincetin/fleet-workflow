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
import difflib
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


# Turkish characters have no accent-only Unicode decomposition for _fold()'s
# NFD-strip trick to bridge (ı is its own base letter, not "i" + a combining
# mark) — a real transliteration table is needed for vendor fuzzy-matching to
# treat "Yildiz"/"Yıldız" as the same word rather than 1/6 characters apart.
_TR_ASCII_MAP = str.maketrans("ıİşŞçÇğĞöÖüÜ", "iIsScCgGoOuU")


def _tr_ascii_fold(text: str) -> str:
    return _fold(text.translate(_TR_ASCII_MAP))


def _vendor_reasonably_matches(extracted: str, expected: str, *, threshold: float = 0.8) -> bool:
    """Word-for-word fuzzy match, tolerant of OCR-level diacritic noise (ı/i,
    ş/s, ç/c, ğ/g) a small local vision model reading rendered text realistically
    produces — a byte-identical string match is the wrong bar for "field
    extraction accuracy" here (dept scenario 04). Same word count required
    (an extraction that drops/adds a word is a real miss, not OCR noise);
    each corresponding word must be at least `threshold` similar per
    difflib.SequenceMatcher on the ASCII-transliterated form.
    """
    extracted_words = _tr_ascii_fold(extracted).split()
    expected_words = _tr_ascii_fold(expected).split()
    if len(extracted_words) != len(expected_words):
        return False
    return all(
        difflib.SequenceMatcher(None, e, x).ratio() >= threshold
        for e, x in zip(extracted_words, expected_words, strict=True)
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


@dataclass(frozen=True)
class InvoiceCase:
    """One synthetic invoice (task 6.3, dept scenario 04 evals: field
    extraction accuracy >=95%; mismatch fixture must flag, never auto-draft
    as clean; duplicate invoice fixture must flag). The invoice image is
    rendered at run time from vendor/po_number/amount, not stored as a
    pre-baked file — same "exercise the real image->text pipeline, don't
    fake around it" spirit as tests/integration/test_invoice_agent_e2e_live.py.
    """

    id: str
    vendor: str
    po_number: str
    amount: str  # as written on the rendered invoice, e.g. "1250.00"
    expect_vendor: str
    expect_po_number: str
    expect_amount: float
    expect_validation_ok: bool
    expect_reason_contains: str | None = None


@dataclass(frozen=True)
class InvoiceAnswer:
    pending_approval: bool = False
    blocked_reason: str | None = None
    extracted_vendor: str | None = None
    extracted_po_number: str | None = None
    extracted_amount: float | None = None
    validation_ok: bool | None = None
    validation_reasons: list[str] = field(default_factory=list)


def load_invoice_dataset(path: Path) -> list[InvoiceCase]:
    cases: list[InvoiceCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cases.append(
            InvoiceCase(
                id=row["id"],
                vendor=row["vendor"],
                po_number=row["po_number"],
                amount=row["amount"],
                expect_vendor=row["expect_vendor"],
                expect_po_number=row["expect_po_number"],
                expect_amount=float(row["expect_amount"]),
                expect_validation_ok=row["expect_validation_ok"],
                expect_reason_contains=row.get("expect_reason_contains"),
            )
        )
    return cases


def evaluate_invoice_case(case: InvoiceCase, answer: InvoiceAnswer) -> CaseResult:
    if not answer.pending_approval:
        return CaseResult(
            id=case.id, passed=False,
            reason=f"expected the run to reach pending_approval, got blocked_reason="
            f"{answer.blocked_reason!r}",
        )

    # Field extraction accuracy (dept scenario 04: ">= 95% on synthetic invoice set").
    # Vendor names are OCR'd/transcribed by a small local vision model reading
    # rendered Turkish text — minor diacritic slips (ı/i, ş/s, ç/c) are real
    # OCR noise, not extraction failures, so vendor comparison tolerates small
    # per-word edit distance rather than requiring byte-identical spelling.
    # po_number/amount stay exact-match — those are unambiguous, no OCR-noise
    # tolerance is appropriate for a number the model either got right or not.
    if not _vendor_reasonably_matches(answer.extracted_vendor or "", case.expect_vendor):
        return CaseResult(
            id=case.id, passed=False,
            reason=f"vendor extraction mismatch: got {answer.extracted_vendor!r}, "
            f"expected {case.expect_vendor!r}",
        )
    if answer.extracted_po_number != case.expect_po_number:
        return CaseResult(
            id=case.id, passed=False,
            reason=f"po_number extraction mismatch: got {answer.extracted_po_number!r}, "
            f"expected {case.expect_po_number!r}",
        )
    if answer.extracted_amount is None or abs(answer.extracted_amount - case.expect_amount) > 0.01:
        return CaseResult(
            id=case.id, passed=False,
            reason=f"amount extraction mismatch: got {answer.extracted_amount!r}, "
            f"expected {case.expect_amount!r}",
        )

    # Validation outcome: mismatch/duplicate/unknown-PO fixtures must flag
    # (never silently validate as clean); a genuinely matching invoice must
    # validate ok (never a false-positive flag either).
    if answer.validation_ok != case.expect_validation_ok:
        return CaseResult(
            id=case.id, passed=False,
            reason=f"expected validation_ok={case.expect_validation_ok}, "
            f"got {answer.validation_ok} (reasons={answer.validation_reasons!r})",
        )
    if case.expect_reason_contains is not None:
        wanted = _fold(case.expect_reason_contains)
        if not any(wanted in _fold(r) for r in answer.validation_reasons):
            return CaseResult(
                id=case.id, passed=False,
                reason=f"expected a validation reason containing "
                f"{case.expect_reason_contains!r}, got {answer.validation_reasons!r}",
            )

    return CaseResult(id=case.id, passed=True, reason="ok")


def _render_invoice_image_base64(*, vendor: str, po_number: str, amount: str) -> str:
    import base64
    import io

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (500, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Vendor: {vendor}", fill="black")
    draw.text((10, 50), f"PO Number: {po_number}", fill="black")
    draw.text((10, 90), f"Total Amount: {amount} TRY", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


async def _run_invoice_case(case: InvoiceCase, *, seen_po_numbers: set[str]) -> InvoiceAnswer:
    """Run one case through the real Invoice Agent graph (6.3) — real
    gateway client (vision OCR + reasoning extraction), real pg_ro-backed PO
    lookup against the seeded fixture_purchase_orders view, real mock ERP
    tool. Never approves, same "stays parked at its interrupt" pattern as
    Dev Agent evals — no real draft entries created by the eval suite."""
    from agents.invoice_agent.graph import build_invoice_agent_graph
    from agents.invoice_agent.po_lookup import PgPoLookup
    from core.llm.factory import build_client
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.erp import ErpTool
    from fleet_mcp.servers.ocr import build_ocr_tool
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool
    from langgraph.checkpoint.memory import InMemorySaver

    class _OcrAdapter:
        def __init__(self, fn: object) -> None:
            self._fn = fn

        async def extract_text(self, image_base64: str) -> dict[str, str]:
            return await self._fn(image_base64=image_base64)  # type: ignore[operator]

    llm_client = await build_client()
    ocr = _OcrAdapter(build_ocr_tool(vision_client=llm_client, tesseract_fn=lambda b: ""))
    erp = ErpTool()
    po_lookup = PgPoLookup(
        tool=PgReadOnlyTool(
            runner=build_default_runner(), allowlisted_tables={"fixture_purchase_orders"}
        )
    )

    graph = build_invoice_agent_graph(
        llm_client=llm_client, ocr=ocr, erp=erp, po_lookup=po_lookup,
        checkpointer=InMemorySaver(), seen_po_numbers=seen_po_numbers,
    )
    image_b64 = _render_invoice_image_base64(
        vendor=case.vendor, po_number=case.po_number, amount=case.amount
    )
    config = {"configurable": {"thread_id": f"eval-{case.id}"}}
    result = await graph.ainvoke({"image_base64": image_b64}, config)

    if result.get("blocked_reason"):
        return InvoiceAnswer(blocked_reason=result["blocked_reason"])
    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        fields = payload["args"]
        validation = payload["validation"]
        return InvoiceAnswer(
            pending_approval=True,
            extracted_vendor=fields.get("vendor"),
            extracted_po_number=fields.get("po_number"),
            extracted_amount=fields.get("amount"),
            validation_ok=validation.get("ok"),
            validation_reasons=validation.get("reasons", []),
        )
    return InvoiceAnswer()


async def run_invoice_agent_eval() -> tuple[list[CaseResult], float, float]:
    """Returns (results, pass_rate, threshold). Cases run in dataset order
    sharing one `seen_po_numbers` set across the whole batch — the
    "duplicate invoice fixture" cases are deliberately ordered right after
    the clean case using the same PO number (see the dataset's
    `duplicate_of` field, informational only / not read by the runner)."""
    config = yaml.safe_load((EVALS_DIR / "config.yaml").read_text(encoding="utf-8"))
    agent_config = config["agents"]["invoice_agent"]
    dataset_path = EVALS_DIR / agent_config["dataset"]
    threshold = float(agent_config["threshold"])
    cases = load_invoice_dataset(dataset_path)

    seen_po_numbers: set[str] = set()
    results = []
    for case in cases:
        answer = await _run_invoice_case(case, seen_po_numbers=seen_po_numbers)
        results.append(evaluate_invoice_case(case, answer))

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
    elif args.agent == "invoice_agent":
        results, pass_rate, threshold = asyncio.run(run_invoice_agent_eval())
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
