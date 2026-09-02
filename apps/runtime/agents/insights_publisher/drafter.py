"""Draft a monthly price-index report in brand voice (task 11.3, dept scenario
08 Insights Publisher).

The reasoning model is given (1) the month's index data as explicit rows and
(2) brand-voice guidance retrieved from the `mkt-brand` collection, and must
write a short TR report + a social variant. It is instructed to use ONLY the
numbers in the provided data — the numbers-match guardrail
(agents.insights_publisher.grounding) then verifies this deterministically
after generation, so a drifted number is caught even if the model ignores the
instruction.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from core.guardrails import wrap_untrusted

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


_SYSTEM_PROMPT = """Sen bir pazarlama içerik yazarısın. Sana bir aylık fiyat \
endeksi verisi (satırlar) ve marka sesi rehberi verilecek. Türkçe, kısa bir \
rapor ve bir sosyal medya varyantı yaz.

SAYILARLA İLGİLİ KESİN KURALLAR:
- Sadece veri satırlarında AÇIKÇA bulunan sayıları kullan.
- Sayıları verideki haliyle, birebir yaz (örn. 500000 yaz; "500 bin" YAZMA).
- Yeni sayı, yüzde, artış/azalış oranı veya değişim HESAPLAMA ve UYDURMA. \
Veride bir yüzde yoksa metinde yüzde kullanma.

Marka sesi rehberine dikkatle uy: rehberde istenen ton, cümle uzunluğu ve \
hitap şeklini uygula.

Yanıtı tam olarak tek bir JSON nesnesi olarak ver, başka hiçbir şey yazma:
{
  "report": "<kısa rapor metni>",
  "social": "<sosyal medya gönderisi>"
}"""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


class DraftParseError(Exception):
    """The model's draft response was malformed."""


@dataclass(frozen=True)
class Draft:
    report: str
    social: str


def _format_data(rows: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)


async def draft_report(
    *,
    data_rows: list[dict[str, Any]],
    brand_voice: str,
    llm_client: ReasoningClient,
    sensitivity: str = "internal",
    **meta: Any,
) -> Draft:
    # Brand-voice text is retrieved KB content -> untrusted, wrapped in a
    # quarantine block (CLAUDE.md rule 4) like any RAG context.
    user = (
        f"Veri satırları:\n{_format_data(data_rows)}\n\n"
        f"Marka sesi rehberi:\n{wrap_untrusted(brand_voice)}"
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
    response = await llm_client.reasoning(messages, sensitivity=sensitivity, **meta)

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise DraftParseError(f"model did not return valid JSON: {response.content!r}") from exc

    if "report" not in parsed or "social" not in parsed:
        raise DraftParseError(f"draft missing report/social: {parsed!r}")
    return Draft(report=str(parsed["report"]), social=str(parsed["social"]))
