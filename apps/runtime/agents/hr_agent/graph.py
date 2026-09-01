"""HR Agent graph: CV image -> OCR -> structured profile -> role match ->
shortlist draft approval (task 8.5, dept scenario 05 HR Talent & Onboarding).

Node order: killswitch_gate -> ocr (image bytes -> text, `read`, local-only
per task 8.2) -> extract_profile (local Qwen -> CvProfile, protected
attributes excluded by schema) -> match_role (pure scoring, `read`) -> hitl
(interrupt() carrying the draft shortlist entry; `write:internal` per the
department scenario's "shortlist output = draft visible to dept_admin only",
and the rollout note "shortlist = assist only (HR decides)" means autonomy is
never enabled here — every run reaches the approval queue) -> [rejected: END
/ approved: END, since there is no downstream external system this scenario
integrates with — the Approval row's payload IS the shortlist draft].

Same "dedicated graph, not core.graph.build_graph()" reasoning as
invoice_agent/dev_agent: this is a fixed linear pipeline. Tool objects
(OcrLike) referenced only via a local Protocol, matching invoice_agent's
apps/runtime-has-no-fleet-mcp-dependency boundary; the caller in apps/api
passes the real fleet_mcp instance in.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.hr_agent.extractor import CvProfile, ExtractionParseError, extract_cv_profile
from agents.hr_agent.match import score_role_match
from core.hitl import requires_approval
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class OcrLike(Protocol):
    async def extract_text(self, image_base64: str) -> dict[str, Any]: ...


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


class HrAgentState(TypedDict, total=False):
    image_base64: str
    criteria: list[str]
    ocr_text: str
    profile: dict[str, Any]
    match: dict[str, Any]
    blocked_reason: str | None
    rejected: bool
    paused: bool


_SHORTLIST_DRAFT_RISK_CLASS = "write:internal"


def build_hr_agent_graph(
    *,
    llm_client: ReasoningClient,
    ocr: OcrLike,
    checkpointer: Any,
    killswitch: KillSwitch | None = None,
    agent_name: str = "hr_agent",
) -> Any:
    async def killswitch_gate(state: HrAgentState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: HrAgentState) -> str:
        return END if state.get("paused") else "ocr"

    async def ocr_node(state: HrAgentState) -> dict[str, Any]:
        result = await ocr.extract_text(image_base64=state["image_base64"])
        return {"ocr_text": result["text"]}

    async def extract_profile(state: HrAgentState) -> dict[str, Any]:
        try:
            profile: CvProfile = await extract_cv_profile(
                ocr_text=state["ocr_text"], llm_client=llm_client
            )
        except ExtractionParseError as exc:
            return {"blocked_reason": f"profile extraction failed: {exc}"}
        return {
            "profile": {
                "full_name": profile.full_name,
                "email": profile.email,
                "phone": profile.phone,
                "education": profile.education,
                "experience": profile.experience,
                "skills": profile.skills,
            }
        }

    def route_after_extract(state: HrAgentState) -> str:
        return "end" if state.get("blocked_reason") else "match_role"

    async def match_role(state: HrAgentState) -> dict[str, Any]:
        p = state["profile"]
        profile = CvProfile(
            full_name=p["full_name"], email=p["email"], phone=p["phone"],
            education=p["education"], experience=p["experience"], skills=p["skills"],
        )
        result = score_role_match(profile, criteria=state.get("criteria", []))
        return {
            "match": {
                "score": result.score,
                "matched_criteria": result.matched_criteria,
                "missing_criteria": result.missing_criteria,
                "reasoning": result.reasoning,
            }
        }

    async def hitl(state: HrAgentState) -> dict[str, Any]:
        # write:internal + autonomy never enabled (dept scenario 05's rollout
        # note: "shortlist = assist only (HR decides)") -> always approval,
        # same "no autonomy path to short-circuit into" shape as invoice_agent.
        assert requires_approval(
            risk_class=_SHORTLIST_DRAFT_RISK_CLASS, eval_pass_rate=0.0, autonomy_enabled=False,
        )
        decision = interrupt(
            {
                "tool": "hr.shortlist_draft",
                "risk_class": _SHORTLIST_DRAFT_RISK_CLASS,
                "args": state["profile"],
                "match": state["match"],
            }
        )
        if not decision.get("approved"):
            return {"rejected": True}
        return {}

    async def end_node(state: HrAgentState) -> dict[str, Any]:
        return {}

    graph = StateGraph(HrAgentState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("ocr", ocr_node)
    graph.add_node("extract_profile", extract_profile)
    graph.add_node("match_role", match_role)
    graph.add_node("hitl", hitl)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate", route_after_killswitch, {END: END, "ocr": "ocr"}
    )
    graph.add_edge("ocr", "extract_profile")
    graph.add_conditional_edges(
        "extract_profile", route_after_extract, {"match_role": "match_role", "end": "end"}
    )
    graph.add_edge("match_role", "hitl")
    graph.add_edge("hitl", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)
