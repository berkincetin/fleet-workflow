"""fleet_mcp.servers.github: read_repo/create_branch/open_pr (task 5.3, dept
scenario 03 Dev Agent).

GitHubTool wraps an injected GitHubBackend Protocol (a real REST-backed
implementation is exercised live in tests/integration against the sandbox
repo). Guardrails tested here: create_branch enforces the `agent/*` branch
name pattern (dept scenario 03's explicit guardrail) before ever calling the
backend; open_pr is always write:external (TRD §9 "PR creation classified
write:external => approval, always" — task 5.5's wording), no exception path.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.github import BranchNamePatternError, GitHubTool


class _FakeBackend:
    def __init__(self) -> None:
        self.created_branches: list[tuple[str, str]] = []
        self.opened_prs: list[dict[str, str]] = []
        self.committed_files: list[tuple[str, str, str]] = []
        self.repo_info = {"default_branch": "main", "full_name": "org/repo"}

    async def read_repo(self) -> dict[str, object]:
        return self.repo_info

    async def create_branch(self, branch_name: str, from_ref: str) -> dict[str, object]:
        self.created_branches.append((branch_name, from_ref))
        return {"ref": f"refs/heads/{branch_name}"}

    async def commit_file(
        self, *, branch_name: str, path: str, content: str, message: str
    ) -> dict[str, object]:
        self.committed_files.append((branch_name, path, content))
        return {"content": {"path": path}, "commit": {"sha": "abc123"}}

    async def open_pr(self, *, branch_name: str, title: str, body: str) -> dict[str, object]:
        self.opened_prs.append({"branch": branch_name, "title": title, "body": body})
        return {"number": 1, "html_url": "https://github.com/org/repo/pull/1"}


def _tool() -> tuple[GitHubTool, _FakeBackend]:
    backend = _FakeBackend()
    return GitHubTool(backend=backend), backend


async def test_read_repo_returns_backend_info() -> None:
    tool, _ = _tool()
    info = await tool.read_repo()
    assert info["full_name"] == "org/repo"


async def test_create_branch_with_agent_prefix_succeeds() -> None:
    tool, backend = _tool()
    result = await tool.create_branch(branch_name="agent/dev-1-fix-typo", from_ref="main")
    assert result["ref"] == "refs/heads/agent/dev-1-fix-typo"
    assert backend.created_branches == [("agent/dev-1-fix-typo", "main")]


async def test_create_branch_without_agent_prefix_is_rejected() -> None:
    tool, backend = _tool()
    with pytest.raises(BranchNamePatternError):
        await tool.create_branch(branch_name="feature/whatever", from_ref="main")
    assert backend.created_branches == []


async def test_open_pr_always_dispatches_regardless_of_content() -> None:
    tool, backend = _tool()
    result = await tool.open_pr(
        branch_name="agent/dev-1-fix-typo", title="Fix typo", body="Closes DEV-1"
    )
    assert result["number"] == 1
    assert backend.opened_prs == [
        {"branch": "agent/dev-1-fix-typo", "title": "Fix typo", "body": "Closes DEV-1"}
    ]


async def test_commit_file_with_agent_prefix_succeeds() -> None:
    tool, backend = _tool()
    result = await tool.commit_file(
        branch_name="agent/dev-1-fix-typo", path="NOTES.md", content="fix", message="Fix typo"
    )
    assert result["commit"]["sha"] == "abc123"
    assert backend.committed_files == [("agent/dev-1-fix-typo", "NOTES.md", "fix")]


async def test_commit_file_without_agent_prefix_is_rejected() -> None:
    tool, backend = _tool()
    with pytest.raises(BranchNamePatternError):
        await tool.commit_file(
            branch_name="main", path="NOTES.md", content="fix", message="Fix typo"
        )
    assert backend.committed_files == []


def test_contracts_declare_correct_risk_classes() -> None:
    tool, _ = _tool()
    contracts = {c.name: c.risk_class for c in tool.as_contracts()}
    assert contracts == {
        "github.read_repo": "read",
        "github.create_branch": "write:internal",
        "github.commit_file": "write:internal",
        "github.open_pr": "write:external",
    }
