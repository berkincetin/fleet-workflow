"""core.memory: rolling conversation window + LLM-summarized eviction (task 4.1, TRD §5).

Context budgeting for conversations: keep the most recent turns verbatim up to
max_turns; older turns are folded into a running summary via the utility model
(cheap call-site per §5) rather than dropped outright.
"""

from __future__ import annotations

from core.memory import build_context


class _FakeUtilityClient:
    def __init__(self, summary: str) -> None:
        self._summary = summary
        self.calls: list[list[dict]] = []

    async def utility(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(messages)

        class _Resp:
            content = self._summary

        return _Resp()


async def test_build_context_keeps_all_turns_under_window() -> None:
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    client = _FakeUtilityClient("unused")
    result = await build_context(history, max_turns=10, summary_client=client)
    assert result.summary is None
    assert result.recent == history
    assert client.calls == []


async def test_build_context_summarizes_evicted_turns_over_window() -> None:
    history = [{"role": "user", "content": f"turn {i}"} for i in range(10)]
    client = _FakeUtilityClient("User discussed turns 0-6.")
    result = await build_context(history, max_turns=3, summary_client=client)
    assert result.summary == "User discussed turns 0-6."
    assert result.recent == history[-3:]
    assert len(client.calls) == 1


async def test_build_context_empty_history() -> None:
    client = _FakeUtilityClient("unused")
    result = await build_context([], max_turns=5, summary_client=client)
    assert result.summary is None
    assert result.recent == []
