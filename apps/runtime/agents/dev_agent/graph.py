"""Dev Agent graph: ticket -> plan -> branch -> PR -> Slack, single HITL
interrupt on PR creation (task 5.5, dept scenario 03).

A dedicated LangGraph graph rather than core.graph.build_graph() — the Dev
Agent's flow is a fixed linear pipeline (fetch ticket, plan, create branch,
open PR, notify Slack), not the general single-tool-call ReAct loop
core.graph is built for. Support Copilot (4.4) made the same call for the
same reason.

Node order: killswitch_gate -> fetch_ticket -> guardrails (label, protected
paths, diff size — any failure short-circuits to END with `blocked_reason`
set, never touching GitHub) -> plan -> create_branch -> hitl (interrupt()
carrying the PR payload; github.open_pr is always write:external per TRD §9,
so this fires unconditionally — no eval_pass_rate/autonomy branch exists in
this graph at all) -> [rejected: END] / [approved: open_pr -> slack_notify].

Tool objects (JiraTool/GitHubTool/SlackPostTool) are referenced here only via
local Protocols, not imported from fleet_mcp — apps/runtime has no fleet-mcp
workspace dependency (fleet-mcp -> fleet-rag -> fleet-runtime already; a
runtime -> mcp edge would cycle), same boundary agents.analytics.service
already established. The caller in apps/api, which does depend on both,
passes the real fleet_mcp Tool instances in.
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol, TypedDict

from agents.dev_agent.guardrails import (
    DiffTooLargeError,
    ProtectedPathError,
    TicketNotLabeledError,
    assert_diff_size_ok,
    assert_no_protected_paths,
    assert_ticket_labeled,
)
from agents.dev_agent.planner import PlanParseError, ReasoningClient, plan_ticket
from core.hitl import requires_approval
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class JiraLike(Protocol):
    async def get_issue(self, key: str) -> dict[str, Any]: ...


class GitHubLike(Protocol):
    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, Any]: ...
    async def commit_file(
        self, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, Any]: ...
    async def open_pr(self, branch_name: str, title: str, body: str) -> dict[str, Any]: ...


class SlackLike(Protocol):
    async def post(self, channel: str, text: str) -> None: ...


class DevAgentState(TypedDict, total=False):
    ticket_key: str
    ticket: dict[str, Any]
    blocked_reason: str | None
    plan: dict[str, Any]
    branch_name: str
    pr_result: dict[str, Any]
    rejected: bool
    paused: bool
    slack_notify_error: str | None


_GITHUB_OPEN_PR_RISK_CLASS = "write:external"


def build_dev_agent_graph(
    *,
    llm_client: ReasoningClient,
    jira: JiraLike,
    github: GitHubLike,
    slack: SlackLike,
    checkpointer: Any,
    slack_channel: str = "#dev-agent",
    killswitch: KillSwitch | None = None,
    agent_name: str = "dev_agent",
    base_ref: str = "main",
) -> Any:
    async def killswitch_gate(state: DevAgentState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: DevAgentState) -> str:
        return END if state.get("paused") else "fetch_ticket"

    async def fetch_ticket(state: DevAgentState) -> dict[str, Any]:
        ticket = await jira.get_issue(key=state["ticket_key"])
        return {"ticket": ticket}

    async def check_guardrails(state: DevAgentState) -> dict[str, Any]:
        try:
            assert_ticket_labeled(state["ticket"])
        except TicketNotLabeledError as exc:
            return {"blocked_reason": str(exc)}
        return {}

    def route_after_ticket_guardrail(state: DevAgentState) -> str:
        return "citation_end" if state.get("blocked_reason") else "plan"

    async def plan(state: DevAgentState) -> dict[str, Any]:
        try:
            plan_result = await plan_ticket(ticket=state["ticket"], llm_client=llm_client)
        except PlanParseError as exc:
            return {"blocked_reason": f"plan generation failed: {exc}"}

        try:
            assert_no_protected_paths(plan_result.target_paths)
            assert_diff_size_ok(plan_result.diff_line_estimate)
        except (ProtectedPathError, DiffTooLargeError) as exc:
            return {"blocked_reason": str(exc)}

        return {
            "plan": {
                "branch_suffix": plan_result.branch_suffix,
                "pr_title": plan_result.pr_title,
                "pr_body": plan_result.pr_body,
                "target_paths": plan_result.target_paths,
                "diff_line_estimate": plan_result.diff_line_estimate,
            }
        }

    def route_after_plan(state: DevAgentState) -> str:
        return "citation_end" if state.get("blocked_reason") else "create_branch"

    async def create_branch(state: DevAgentState) -> dict[str, Any]:
        # Suffix with a short run-unique token: the LLM's branch_suffix alone
        # collides across repeated runs of the same ticket (same wording ->
        # same/similar suggested name) — caught live against the sandbox
        # repo (GitHub 422 "Reference already exists" on a second real run).
        run_token = uuid.uuid4().hex[:8]
        branch_name = f"agent/{state['plan']['branch_suffix']}-{run_token}"
        await github.create_branch(branch_name=branch_name, from_ref=base_ref)
        # A PR against a branch with zero commits ahead of its base is
        # rejected by GitHub (422 "no commits between ... and ...") — commit
        # a minimal real note here so open_pr has an actual diff to open
        # against. This is the "implementation draft" step; a full patch
        # apply engine is out of scope for this sprint.
        note = (
            f"Dev Agent draft for {state['ticket_key']}: {state['plan']['pr_title']}\n\n"
            f"Ticket: {state['ticket'].get('summary', '')}\n"
            f"Target paths (proposed): {', '.join(state['plan']['target_paths'])}\n"
        )
        await github.commit_file(
            branch_name=branch_name,
            path="AGENT_DRAFT_NOTES.md",
            content=note,
            message=f"Dev Agent draft notes for {state['ticket_key']}",
        )
        return {"branch_name": branch_name}

    async def hitl(state: DevAgentState) -> dict[str, Any]:
        # github.open_pr is always write:external (TRD §9) — requires_approval
        # is called for symmetry/auditability with the rest of the codebase's
        # HITL decision points, but for this risk_class it can only ever
        # return True; there is no autonomy path to short-circuit into.
        assert requires_approval(
            risk_class=_GITHUB_OPEN_PR_RISK_CLASS, eval_pass_rate=0.0, autonomy_enabled=False
        )
        decision = interrupt(
            {
                "tool": "github.open_pr",
                "risk_class": _GITHUB_OPEN_PR_RISK_CLASS,
                "args": {
                    "branch_name": state["branch_name"],
                    "title": state["plan"]["pr_title"],
                    "body": state["plan"]["pr_body"],
                },
            }
        )
        if not decision.get("approved"):
            return {"rejected": True}
        return {}

    def route_after_hitl(state: DevAgentState) -> str:
        return "citation_end" if state.get("rejected") else "open_pr"

    async def open_pr(state: DevAgentState) -> dict[str, Any]:
        result = await github.open_pr(
            branch_name=state["branch_name"],
            title=state["plan"]["pr_title"],
            body=state["plan"]["pr_body"],
        )
        return {"pr_result": result}

    async def slack_notify(state: DevAgentState) -> dict[str, Any]:
        # Best-effort: the PR is already open by this point (open_pr already
        # ran and succeeded) — a notification failure (unset webhook, Slack
        # outage) must not surface as a failure of the whole resume call and
        # must never look like the PR itself failed to open.
        pr_url = state["pr_result"].get("html_url", "")
        title = state["plan"]["pr_title"]
        text = f"Dev Agent opened PR for {state['ticket_key']}: {title} {pr_url}"
        try:
            await slack.post(channel=slack_channel, text=text)
        except Exception as exc:
            return {"slack_notify_error": str(exc)}
        return {}

    async def citation_end(state: DevAgentState) -> dict[str, Any]:
        return {}

    graph = StateGraph(DevAgentState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("fetch_ticket", fetch_ticket)
    graph.add_node("check_guardrails", check_guardrails)
    graph.add_node("plan", plan)
    graph.add_node("create_branch", create_branch)
    graph.add_node("hitl", hitl)
    graph.add_node("open_pr", open_pr)
    graph.add_node("slack_notify", slack_notify)
    graph.add_node("citation_end", citation_end)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate", route_after_killswitch, {END: END, "fetch_ticket": "fetch_ticket"}
    )
    graph.add_edge("fetch_ticket", "check_guardrails")
    graph.add_conditional_edges(
        "check_guardrails",
        route_after_ticket_guardrail,
        {"plan": "plan", "citation_end": "citation_end"},
    )
    graph.add_conditional_edges(
        "plan", route_after_plan, {"create_branch": "create_branch", "citation_end": "citation_end"}
    )
    graph.add_edge("create_branch", "hitl")
    graph.add_conditional_edges(
        "hitl", route_after_hitl, {"open_pr": "open_pr", "citation_end": "citation_end"}
    )
    graph.add_edge("open_pr", "slack_notify")
    graph.add_edge("slack_notify", "citation_end")
    graph.add_edge("citation_end", END)

    return graph.compile(checkpointer=checkpointer)
