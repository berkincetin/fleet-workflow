"""Unit tests for the LiteLLM pricing sync (task 2.1).

The sync's job: for every model in the LiteLLM config, resolve its canonical
per-token input/output price from a price source (LiteLLM's model_cost map) and
write it back into the config, reporting any model whose price could not be
resolved or is invalid. The core is a pure function so it runs without network
or the litellm package installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

_GATEWAY = Path(__file__).resolve().parents[2] / "gateway" / "litellm"
if str(_GATEWAY) not in sys.path:
    sys.path.insert(0, str(_GATEWAY))

from pricing_sync import PriceValidationError, sync_prices  # noqa: E402


def _cfg() -> dict:
    return {
        "model_list": [
            {
                "model_name": "reasoning",
                "litellm_params": {
                    "model": "anthropic/claude-sonnet-4-5",
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                },
            },
            {
                "model_name": "local-reasoning",
                "litellm_params": {
                    "model": "ollama/qwen2.5:7b-instruct-q4_K_M",
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                },
            },
        ]
    }


def test_sync_writes_prices_from_source() -> None:
    prices = {
        "anthropic/claude-sonnet-4-5": {
            "input_cost_per_token": 0.000003,
            "output_cost_per_token": 0.000015,
        },
    }
    updated, report = sync_prices(_cfg(), prices)

    reasoning = updated["model_list"][0]["litellm_params"]
    assert reasoning["input_cost_per_token"] == 0.000003
    assert reasoning["output_cost_per_token"] == 0.000015
    assert report.updated == ["reasoning"]


def test_local_models_are_free_and_valid_without_a_source_entry() -> None:
    # Ollama models cost nothing and are not in LiteLLM's price map; a 0.0 price
    # for them is valid, not a failure.
    updated, report = sync_prices(_cfg(), prices={})

    local = updated["model_list"][1]["litellm_params"]
    assert local["input_cost_per_token"] == 0.0
    assert local["output_cost_per_token"] == 0.0
    assert "local-reasoning" not in report.unresolved


def test_unresolved_cloud_model_is_reported() -> None:
    # A cloud (non-ollama) model with no price in the source and a 0.0 config
    # price is unresolved — a real price is required.
    updated, report = sync_prices(_cfg(), prices={})
    assert "reasoning" in report.unresolved


def test_strict_raises_on_unresolved_cloud_price() -> None:
    try:
        sync_prices(_cfg(), prices={}, strict=True)
    except PriceValidationError as exc:
        assert "reasoning" in str(exc)
    else:  # pragma: no cover - the call must raise
        raise AssertionError("expected PriceValidationError")


def test_negative_price_in_source_is_invalid() -> None:
    prices = {
        "anthropic/claude-sonnet-4-5": {
            "input_cost_per_token": -1.0,
            "output_cost_per_token": 0.000015,
        },
    }
    try:
        sync_prices(_cfg(), prices, strict=True)
    except PriceValidationError as exc:
        assert "reasoning" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected PriceValidationError on negative price")
