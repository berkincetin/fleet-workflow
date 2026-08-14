"""Task 8.2 AC: "integration test proves a pii request never reaches a cloud
provider (recorded gateway targets) — runs on hosted CI without GPU."

Exercises the real call sites an HR CV goes through (OCR -> embeddings ->
structured extraction) with a real `core.llm.client.LLMClient` wired to the
real default model matrix + real `core.llm.routing.select_model`, but a fake
`Transport` that only *records* which model name each call targeted — no
network, no Ollama, no GPU, so this runs unmodified on GitHub-hosted CI
runners (the CI note in docs/split/implementation-plan/sprint-8-kvkk-lane.md
task 8.2 is explicit that this class of assertion must never need a GPU
runner). A live extraction accuracy check against the real Ollama/GPU lane is
a separate `@pytest.mark.gpu` test (tests/integration/test_hr_cv_pipeline_gpu_live.py).

Fails loudly (not skips) if any recorded target is a cloud model — this is
the regression guard for the ocr.py bug this task fixed (vision-LLM OCR was
previously hardcoded to sensitivity="internal", which would have routed a raw
CV image to a cloud vision model before any PII redaction could happen).
"""

from __future__ import annotations

from typing import Any

import pytest
from agents.hr_agent.extractor import extract_cv_profile
from core.llm.client import LLMClient
from fleet_rag.ingest.ocr import ocr_image, tesseract_ocr
from fleet_rag.ingest.pipeline import run_ingestion

# Mirrors gateway/litellm/config.yaml's default matrix shape (task 2.2/2.3).
_DEFAULT_MATRIX: list[dict[str, Any]] = [
    {"name": "reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.003, "output_price_per_1k": 0.015},
    {"name": "utility", "fleet_role": "utility", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.000075, "output_price_per_1k": 0.0003},
    {"name": "embeddings", "fleet_role": "embeddings", "sensitivity_clearance": "internal",
     "input_price_per_1k": 0.00002, "output_price_per_1k": 0.0},
    {"name": "local-reasoning", "fleet_role": "reasoning", "sensitivity_clearance": "pii",
     "input_price_per_1k": 0.0, "output_price_per_1k": 0.0},
    {"name": "local-embeddings", "fleet_role": "embeddings", "sensitivity_clearance": "pii",
     "input_price_per_1k": 0.0, "output_price_per_1k": 0.0},
]


class _RecordingTransport:
    """Records every model name each call targeted; never touches the network.
    A cloud-model target here would mean a real HTTP call would have gone to
    a cloud-cleared model — this is the "recorded gateway targets" proof."""

    def __init__(self) -> None:
        self.complete_calls: list[str] = []
        self.embed_calls: list[str] = []

    async def complete(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> dict[str, Any]:
        self.complete_calls.append(model)
        content = (
            '{"full_name": "x", "email": "", "phone": "", '
            '"education": [], "experience": [], "skills": []}'
        )
        return {
            "model": model,
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5},
        }

    async def embed(self, *, model: str, input: list[str], **kwargs: Any) -> dict[str, Any]:
        self.embed_calls.append(model)
        return {
            "model": model,
            "data": [{"index": i, "embedding": [0.0] * 8} for i in range(len(input))],
            "usage": {"prompt_tokens": 5},
        }

    async def stream_complete(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ):  # pragma: no cover
        raise NotImplementedError


class _NullLedger:
    async def record(self, row: dict[str, Any]) -> None:
        pass


class _FakeQdrantSink:
    def ensure_collection(self, name: str, *, vector_size: int) -> None:
        pass

    def upsert(self, name: str, *, points: list[dict[str, Any]]) -> None:
        pass


CLOUD_MODEL_NAMES = {"reasoning", "utility", "embeddings"}


@pytest.fixture()
def llm_client() -> tuple[LLMClient, _RecordingTransport]:
    transport = _RecordingTransport()
    client = LLMClient(models=_DEFAULT_MATRIX, transport=transport, ledger=_NullLedger())
    return client, transport


async def test_cv_ocr_never_calls_the_gateway_at_all(
    llm_client: tuple[LLMClient, _RecordingTransport],
) -> None:
    """A raw CV scan (pii) must be OCR'd purely locally — not even a routed
    local-model call, since no vision-capable local model is registered
    (task 8.2's fix: confidential/pii OCR skips the vision-LLM step entirely)."""
    client, transport = llm_client
    result = await ocr_image(
        b"\x89PNG fake cv image bytes",
        vision_client=client,
        tesseract_fn=lambda _b: "Ayse Yilmaz\nayse.yilmaz@example.com",
        sensitivity="pii",
    )
    assert result.source == "tesseract"
    assert transport.complete_calls == [], (
        f"OCR must never call the gateway for pii content; got {transport.complete_calls!r}"
    )


async def test_cv_extraction_targets_local_reasoning_never_cloud(
    llm_client: tuple[LLMClient, _RecordingTransport]
) -> None:
    client, transport = llm_client
    await extract_cv_profile(ocr_text="Ayse Yilmaz, ayse.yilmaz@example.com", llm_client=client)
    assert transport.complete_calls, "expected extract_cv_profile to call the gateway"
    for target in transport.complete_calls:
        assert target not in CLOUD_MODEL_NAMES, f"CV extraction routed to cloud model {target!r}"
    assert transport.complete_calls == ["local-reasoning"]


async def test_cv_ingestion_pipeline_embeddings_target_local_never_cloud(
    llm_client: tuple[LLMClient, _RecordingTransport]
) -> None:
    """The hr-cvs collection (task 8.2/8.5) is sensitivity=pii,
    pii_policy=allow-local-only — the full run_ingestion() pipeline (real
    orchestration from task 3.1, unchanged here) must resolve its embedding
    call to local-embeddings, never a cloud embeddings model."""
    client, transport = llm_client
    outcome = await run_ingestion(
        data=b"Ayse Yilmaz CV content, ayse.yilmaz@example.com, +90 555 111 2233",
        filename="cv.txt",
        collection_id=1,
        sensitivity="pii",
        pii_policy="allow-local-only",
        llm_client=client,
        qdrant=_FakeQdrantSink(),
        existing_hashes=set(),
    )
    assert outcome.chunks_embedded >= 1
    assert transport.embed_calls, "expected the pipeline to call embeddings"
    for target in transport.embed_calls:
        assert target not in CLOUD_MODEL_NAMES, f"CV embedding routed to cloud model {target!r}"
    assert transport.embed_calls == ["local-embeddings"]


async def test_cv_ocr_confidential_also_never_calls_gateway(
    llm_client: tuple[LLMClient, _RecordingTransport]
) -> None:
    """Same guarantee at the confidential floor (dept scenario 04 invoices —
    the shared ocr_image() fix this task made, not HR-specific)."""
    client, transport = llm_client
    await ocr_image(
        b"\x89PNG fake invoice bytes",
        vision_client=client,
        tesseract_fn=tesseract_ocr,
        sensitivity="confidential",
    )
    assert transport.complete_calls == []
