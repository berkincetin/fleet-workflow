"""agents.dev_agent.graph: ticket -> plan -> branch -> PR -> Slack, with a
single HITL interrupt on PR creation (task 5.5, dept scenario 03).

A dedicated LangGraph graph, not core.graph.build_graph() — the Dev Agent's
flow is a fixed linear pipeline (not a general single-tool-call ReAct loop
core.graph is built for), same reasoning that kept Support Copilot (4.4) off
core.graph too. github.open_pr is write:external, so core.hitl.requires_approval
always returns True for it (TRD §9 "no exception") — proven here by the
interrupt firing unconditionally, not by eval_pass_rate/autonomy plumbing this
graph doesn't even have.

Guardrail failures (missing agent-ok label, protected path, oversized diff)
short-circuit to END before ever calling create_branch — proven by asserting
the fake GitHub backend's create_branch was never invoked. The graph accepts
real fleet_mcp Tool wrappers (JiraTool/GitHubTool/SlackPostTool), not raw
backends, so it inherits their own guardrails (agent/* pattern, channel
allowlist) for free rather than re-implementing them.
"""

from __future__ import annotations

from typing import Any

from agents.dev_agent.graph import build_dev_agent_graph
from fleet_mcp.servers.github import GitHubTool
from fleet_mcp.servers.jira import JiraTool
from fleet_mcp.servers.slack import SlackPostTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class _FakeJiraBackend:
    def __init__(self, ticket: dict[str, Any]) -> None:
        self.ticket = ticket

    async def search(self, jql: str) -> list[dict[str, Any]]:
        return [self.ticket]

    async def get_issue(self, key: str) -> dict[str, Any]:
        return self.ticket


class _FakeGitHubBackend:
    def __init__(self) -> None:
        self.branches_created: list[str] = []
        self.files_committed: list[str] = []
        self.prs_opened: list[dict[str, str]] = []

    async def read_repo(self) -> dict[str, Any]:
        return {"default_branch": "main", "full_name": "org/repo"}

    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, Any]:
        self.branches_created.append(branch_name)
        return {"ref": f"refs/heads/{branch_name}"}

    async def commit_file(
        self, *, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, Any]:
        self.files_committed.append(branch_name)
        return {"commit": {"sha": "abc123"}}

    async def open_pr(self, *, branch_name: str, title: str, body: str) -> dict[str, Any]:
        self.prs_opened.append({"branch": branch_name, "title": title, "body": body})
        return {"number": 1, "html_url": "https://github.com/org/repo/pull/1"}


class _FakeSlackSender:
    def __init__(self) -> None:
        self.posted: list[dict[str, str]] = []

    async def post(self, *, channel: str, text: str) -> None:
        self.posted.append({"channel": channel, "text": text})


def _tools(
    ticket: dict[str, Any],
) -> tuple[JiraTool, GitHubTool, SlackPostTool, _FakeGitHubBackend, _FakeSlackSender]:
    github_backend = _FakeGitHubBackend()
    slack_sender = _FakeSlackSender()
    jira = JiraTool(backend=_FakeJiraBackend(ticket))
    github = GitHubTool(backend=github_backend)
    slack = SlackPostTool(sender=slack_sender, allowed_channels={"#dev-agent"})
    return jira, github, slack, github_backend, slack_sender


_VALID_PLAN_JSON = (
    '{"branch_suffix": "fix-typo", "pr_title": "Fix typo", "pr_body": "Closes DEV-1", '
    '"target_paths": ["README.md"], "diff_line_estimate": 3}'
)


class _FakeLLM:
    def __init__(self, content: str = _VALID_PLAN_JSON) -> None:
        self.content = content

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        class _Resp:
            content = self.content

        return _Resp()

    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        raise AssertionError("dev_agent graph must not call utility() for planning")


def _labeled_ticket(key: str = "DEV-1") -> dict[str, Any]:
    return {"key": key, "summary": "Fix typo", "labels": ["agent-ok"]}


async def test_run_reaches_interrupt_before_opening_pr() -> None:
    jira, github, slack, github_backend, _ = _tools(_labeled_ticket())
    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=slack,
        checkpointer=InMemorySaver(), slack_channel="#dev-agent",
    )
    config = {"configurable": {"thread_id": "t1"}}
    result = await graph.ainvoke({"ticket_key": "DEV-1"}, config)

    assert "__interrupt__" in result
    assert len(github_backend.branches_created) == 1
    assert github_backend.branches_created[0].startswith("agent/fix-typo-")
    assert github_backend.files_committed == github_backend.branches_created
    assert github_backend.prs_opened == []  # not yet — waiting on approval


async def test_approve_resumes_and_opens_pr_and_notifies_slack() -> None:
    jira, github, slack, github_backend, slack_sender = _tools(_labeled_ticket())
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "t2"}}

    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=slack,
        checkpointer=checkpointer, slack_channel="#dev-agent",
    )
    await graph.ainvoke({"ticket_key": "DEV-1"}, config)

    graph2 = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=slack,
        checkpointer=checkpointer, slack_channel="#dev-agent",
    )
    result = await graph2.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in result
    assert len(github_backend.prs_opened) == 1
    opened = github_backend.prs_opened[0]
    assert opened["branch"].startswith("agent/fix-typo-")
    assert opened["title"] == "Fix typo"
    assert opened["body"] == "Closes DEV-1"
    assert len(slack_sender.posted) == 1
    posted_text = slack_sender.posted[0]["text"]
    assert "Fix typo" in posted_text or "DEV-1" in posted_text


async def test_reject_cancels_cleanly_without_opening_pr() -> None:
    jira, github, slack, github_backend, slack_sender = _tools(_labeled_ticket())
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "t3"}}

    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=slack,
        checkpointer=checkpointer, slack_channel="#dev-agent",
    )
    await graph.ainvoke({"ticket_key": "DEV-1"}, config)

    graph2 = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=slack,
        checkpointer=checkpointer, slack_channel="#dev-agent",
    )
    result = await graph2.ainvoke(Command(resume={"approved": False}), config)

    assert "__interrupt__" not in result
    assert result["rejected"] is True
    assert github_backend.prs_opened == []
    assert slack_sender.posted == []


async def test_slack_notify_failure_does_not_fail_the_whole_run() -> None:
    """Caught before shipping: a raised slack.post() (e.g. an unset/invalid
    webhook URL) must not crash the resume call after the PR has already been
    opened successfully — best-effort notify, not a hard dependency."""

    class _FailingSlackSender:
        async def post(self, *, channel: str, text: str) -> None:
            raise RuntimeError("webhook unreachable")

    jira, github, _, github_backend, _ = _tools(_labeled_ticket())
    failing_slack = SlackPostTool(sender=_FailingSlackSender(), allowed_channels={"#dev-agent"})
    checkpointer = InMemorySaver()
    config = {"configurable": {"thread_id": "t-slack-fail"}}

    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=failing_slack,
        checkpointer=checkpointer, slack_channel="#dev-agent",
    )
    await graph.ainvoke({"ticket_key": "DEV-1"}, config)

    graph2 = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=failing_slack,
        checkpointer=checkpointer, slack_channel="#dev-agent",
    )
    result = await graph2.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in result
    assert github_backend.prs_opened  # the PR still opened successfully
    assert result.get("slack_notify_error") is not None


async def test_ticket_without_agent_ok_label_never_creates_branch() -> None:
    unlabeled = {"key": "DEV-2", "summary": "x", "labels": []}
    jira, github, slack, github_backend, _ = _tools(unlabeled)
    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(), jira=jira, github=github, slack=slack,
        checkpointer=InMemorySaver(), slack_channel="#dev-agent",
    )
    config = {"configurable": {"thread_id": "t4"}}
    result = await graph.ainvoke({"ticket_key": "DEV-2"}, config)

    assert "__interrupt__" not in result
    assert result.get("blocked_reason") is not None
    assert github_backend.branches_created == []


async def test_plan_touching_protected_path_never_creates_branch() -> None:
    plan_json = (
        '{"branch_suffix": "x", "pr_title": "x", "pr_body": "x", '
        '"target_paths": ["infra/compose/docker-compose.dev.yml"], "diff_line_estimate": 3}'
    )
    jira, github, slack, github_backend, _ = _tools(_labeled_ticket())
    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(plan_json), jira=jira, github=github, slack=slack,
        checkpointer=InMemorySaver(), slack_channel="#dev-agent",
    )
    config = {"configurable": {"thread_id": "t5"}}
    result = await graph.ainvoke({"ticket_key": "DEV-1"}, config)

    assert "__interrupt__" not in result
    assert result.get("blocked_reason") is not None
    assert github_backend.branches_created == []


async def test_oversized_diff_never_creates_branch() -> None:
    plan_json = (
        '{"branch_suffix": "x", "pr_title": "x", "pr_body": "x", '
        '"target_paths": ["a.py"], "diff_line_estimate": 999}'
    )
    jira, github, slack, github_backend, _ = _tools(_labeled_ticket())
    graph = build_dev_agent_graph(
        llm_client=_FakeLLM(plan_json), jira=jira, github=github, slack=slack,
        checkpointer=InMemorySaver(), slack_channel="#dev-agent",
    )
    config = {"configurable": {"thread_id": "t6"}}
    result = await graph.ainvoke({"ticket_key": "DEV-1"}, config)

    assert "__interrupt__" not in result
    assert result.get("blocked_reason") is not None
    assert github_backend.branches_created == []
