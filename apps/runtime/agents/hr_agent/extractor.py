"""CV text -> structured profile (task 8.1/8.2, dept scenario 05 "CV -> structured
profile" step, TRD §8 pii lane).

Mirrors agents.invoice_agent.extractor's shape (system prompt -> JSON ->
dataclass, same markdown-code-fence defense) with one deliberate difference:
`CvProfile` has NO fields for age, gender, photo, or birthdate. The department
scenario's guardrail — "protected-attribute fields (age, gender, photo)
excluded from the structured profile at extraction — enforced by schema" — is
implemented literally here: even if the model includes those keys in its JSON
response (it may see a birthdate on the CV and try to be "helpful"), `_parse`
only reads the allowed fields, so a protected attribute can never reach the
returned CvProfile no matter what the model outputs. This is stronger than a
prompt instruction alone (which a model can ignore or a prompt-injection in
the CV text could try to override).

The reasoning call always uses sensitivity="pii" (TRD §8 pii lane, dept
scenario 05: "pii lane: local Qwen (parse/extract)... reasoning stays local
for CV content") — never overridable by the caller, unlike invoice_agent's
`sensitivity` parameter, because CV content must never be eligible for cloud
routing under any circumstance.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

_SYSTEM_PROMPT = """You are a CV/resume field extraction assistant. Given OCR'd \
CV text (which may contain OCR noise/errors), extract the following fields.

Respond with exactly one JSON object and nothing else — no markdown code fences, no commentary:
{
  "full_name": "<candidate's full name as written on the CV>",
  "email": "<email address, or empty string if none>",
  "phone": "<phone number, or empty string if none>",
  "education": ["<one string per degree/school entry, e.g. 'BSc Computer Science, ODTU, 2019'>"],
  "experience": ["<one string per role, e.g. 'Software Engineer, Acme A.S., 2019-2022'>"],
  "skills": ["<skill1>", "<skill2>", "..."]
}

Do not include age, date of birth, gender, marital status, or any photo/appearance
description in your response, even if present in the CV text — these fields are not
part of the schema and must be omitted entirely.
If a field cannot be determined from the text, use an empty string (or empty list).
"""

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


class ExtractionParseError(Exception):
    """The model's CV-extraction response was malformed or missing a field."""


class ReasoningClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


# The complete, exhaustive set of fields a CvProfile may ever carry — this
# dataclass IS the schema-enforced protected-attribute exclusion; there is no
# age/gender/photo/birthdate field to accidentally populate.
@dataclass(frozen=True)
class CvProfile:
    full_name: str
    email: str
    phone: str
    education: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)


_REQUIRED_FIELDS = ("full_name", "email", "phone", "education", "experience", "skills")


async def extract_cv_profile(
    *, ocr_text: str, llm_client: ReasoningClient, **meta: Any
) -> CvProfile:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": ocr_text},
    ]
    response = await llm_client.reasoning(messages, sensitivity="pii", **meta)

    try:
        parsed = json.loads(_strip_code_fence(response.content))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(
            f"model did not return valid JSON: {response.content!r}"
        ) from exc

    missing = [f for f in _REQUIRED_FIELDS if f not in parsed]
    if missing:
        raise ExtractionParseError(f"extraction response missing field(s): {missing}")

    def _str_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ExtractionParseError(f"expected a list, got {value!r}")
        return [str(v) for v in value]

    # Reading only the six allowed keys below is the enforcement mechanism:
    # any other key the model emitted (age, gender, photo, birthdate, ...) is
    # silently dropped here, never reaching the returned CvProfile.
    return CvProfile(
        full_name=str(parsed["full_name"]),
        email=str(parsed["email"]),
        phone=str(parsed["phone"]),
        education=_str_list(parsed["education"]),
        experience=_str_list(parsed["experience"]),
        skills=_str_list(parsed["skills"]),
    )
