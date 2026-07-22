"""Integration: GitHub MCP tool against the real sandbox repo (task 5.3 AC:
"GitHub sandbox smoke (branch create) works with PAT").

FLEET_GITHUB_SANDBOX_REPO/FLEET_GITHUB_SANDBOX_TOKEN are read from the
process environment or, if unset there, parsed directly out of the repo's
.env (Docker Compose's own convention for this repo — not auto-loaded by
pydantic-settings, see apps/api/fleet_api/config.py) since this is the only
test needing them and doesn't warrant a new python-dotenv dependency.
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest
from fleet_mcp.servers.github import GitHubTool, RestGitHubBackend

_ENV_LINE_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)=(.*)$")


def _load_dotenv_fallback() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        match = _ENV_LINE_RE.match(line.strip())
        if match and match.group(1) not in os.environ:
            os.environ[match.group(1)] = match.group(2)


_load_dotenv_fallback()

SANDBOX_REPO = os.environ.get("FLEET_GITHUB_SANDBOX_REPO", "")
SANDBOX_TOKEN = os.environ.get("FLEET_GITHUB_SANDBOX_TOKEN", "")

pytestmark = pytest.mark.skipif(
    not (SANDBOX_REPO and SANDBOX_TOKEN),
    reason="FLEET_GITHUB_SANDBOX_REPO/TOKEN not set — see .env",
)


async def test_read_repo_returns_real_metadata() -> None:
    tool = GitHubTool(backend=RestGitHubBackend(repo=SANDBOX_REPO, token=SANDBOX_TOKEN))
    info = await tool.read_repo()
    assert info["full_name"] == SANDBOX_REPO


async def test_create_branch_smoke() -> None:
    """The literal AC: branch create works with a PAT against a real sandbox repo."""
    tool = GitHubTool(backend=RestGitHubBackend(repo=SANDBOX_REPO, token=SANDBOX_TOKEN))
    repo_info = await tool.read_repo()
    default_branch = repo_info["default_branch"]

    branch_name = f"agent/mcp-smoke-{uuid.uuid4().hex[:8]}"
    result = await tool.create_branch(branch_name=branch_name, from_ref=default_branch)
    assert result["ref"] == f"refs/heads/{branch_name}"


async def test_create_branch_rejects_non_agent_prefix_before_any_api_call() -> None:
    tool = GitHubTool(
        backend=RestGitHubBackend(repo=SANDBOX_REPO, token="deliberately-invalid-token")
    )
    from fleet_mcp.servers.github import BranchNamePatternError

    with pytest.raises(BranchNamePatternError):
        # An invalid token would 401 if this ever reached the backend — the
        # branch-name guard must fire first, so this proves the guard runs
        # before any network call, not just that the sandbox rejects it too.
        await tool.create_branch(branch_name="not-agent-prefixed", from_ref="main")
