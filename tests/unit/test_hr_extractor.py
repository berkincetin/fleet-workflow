"""agents.hr_agent.extractor: OCR text -> structured CV profile (task 8.1/8.2,
dept scenario 05 "CV -> structured profile" step + protected-attribute
schema-exclusion guardrail).
"""

from __future__ import annotations

import pytest
from agents.hr_agent.extractor import CvProfile, ExtractionParseError, extract_cv_profile


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[list[dict[str, object]]] = []
        self.call_kwargs: list[dict[str, object]] = []

    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        self.calls.append(messages)
        self.call_kwargs.append(kwargs)

        class _Resp:
            content = self.content

        return _Resp()


_VALID_JSON = (
    '{"full_name": "Ayse Yilmaz", "email": "ayse.yilmaz@example.com", '
    '"phone": "+90 555 123 4567", '
    '"education": ["BSc Computer Engineering, ODTU, 2019"], '
    '"experience": ["Software Engineer, Acme A.S., 2019-2022"], '
    '"skills": ["Python", "SQL"]}'
)


async def test_extract_cv_profile_parses_valid_response() -> None:
    llm = _FakeLLM(_VALID_JSON)
    profile = await extract_cv_profile(ocr_text="cv text", llm_client=llm)
    assert profile.full_name == "Ayse Yilmaz"
    assert profile.email == "ayse.yilmaz@example.com"
    assert profile.phone == "+90 555 123 4567"
    assert profile.education == ["BSc Computer Engineering, ODTU, 2019"]
    assert profile.experience == ["Software Engineer, Acme A.S., 2019-2022"]
    assert profile.skills == ["Python", "SQL"]


async def test_extract_cv_profile_always_uses_pii_sensitivity() -> None:
    """CV content must never be routable to a cloud model — the sensitivity
    passed to the gateway client is hardcoded, not caller-overridable, unlike
    invoice_agent's `sensitivity` kwarg."""
    llm = _FakeLLM(_VALID_JSON)
    await extract_cv_profile(ocr_text="x", llm_client=llm)
    assert llm.call_kwargs[0]["sensitivity"] == "pii"


async def test_extract_cv_profile_uses_reasoning_tier() -> None:
    calls = {"reasoning": False}

    class _TierLLM:
        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            calls["reasoning"] = True

            class _Resp:
                content = _VALID_JSON

            return _Resp()

        async def utility(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            raise AssertionError("extractor must not call utility()")

    await extract_cv_profile(ocr_text="x", llm_client=_TierLLM())
    assert calls["reasoning"] is True


async def test_extract_cv_profile_strips_markdown_code_fence() -> None:
    llm = _FakeLLM(f"```json\n{_VALID_JSON}\n```")
    profile = await extract_cv_profile(ocr_text="x", llm_client=llm)
    assert profile.full_name == "Ayse Yilmaz"


async def test_extract_cv_profile_raises_on_malformed_json() -> None:
    llm = _FakeLLM("not json")
    with pytest.raises(ExtractionParseError):
        await extract_cv_profile(ocr_text="x", llm_client=llm)


async def test_extract_cv_profile_raises_on_missing_field() -> None:
    llm = _FakeLLM('{"full_name": "x"}')
    with pytest.raises(ExtractionParseError):
        await extract_cv_profile(ocr_text="x", llm_client=llm)


async def test_extract_cv_profile_prompt_includes_ocr_text() -> None:
    llm = _FakeLLM(_VALID_JSON)
    await extract_cv_profile(ocr_text="CV of Ayse Yilmaz, born 1990-04-12", llm_client=llm)
    user_message = llm.calls[0][-1]["content"]
    assert "born 1990-04-12" in user_message


# --- Protected-attribute schema-exclusion guardrail (dept scenario 05) -----


async def test_cv_profile_dataclass_has_no_protected_attribute_fields() -> None:
    """The schema itself is the guardrail: birthdate/age/gender/photo must
    not exist as fields on CvProfile at all, so no code path can ever
    populate or forward them downstream (e.g. into a shortlist draft)."""
    field_names = {f for f in CvProfile.__dataclass_fields__}
    protected = {"age", "birthdate", "date_of_birth", "gender", "photo", "marital_status"}
    assert field_names.isdisjoint(protected)


async def test_extract_cv_profile_drops_protected_attributes_the_model_still_emits() -> None:
    """A model may see a birthdate on the CV and include it anyway despite
    the prompt's instruction not to — the parser must silently discard any
    extra key rather than surface it, since a prompt is not a guarantee."""
    json_with_extra_fields = (
        '{"full_name": "Ayse Yilmaz", "email": "a@example.com", "phone": "555", '
        '"education": [], "experience": [], "skills": [], '
        '"birthdate": "1990-04-12", "age": 34, "gender": "female", '
        '"photo_description": "smiling"}'
    )
    llm = _FakeLLM(json_with_extra_fields)
    profile = await extract_cv_profile(ocr_text="x", llm_client=llm)
    assert not hasattr(profile, "birthdate")
    assert not hasattr(profile, "age")
    assert not hasattr(profile, "gender")
    assert not hasattr(profile, "photo_description")
    assert profile.full_name == "Ayse Yilmaz"
