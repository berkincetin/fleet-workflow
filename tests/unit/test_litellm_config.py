"""Static validation of the pinned LiteLLM config (task 2.1).

Guards the shape LiteLLM requires to boot, so an obviously-broken config is
caught in unit tests rather than only when the container starts: every model has
a name + litellm model id + non-negative prices, every fallback target resolves
to a defined model, and every fleet_role/clearance is from the allowed set.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONFIG = Path(__file__).resolve().parents[2] / "gateway" / "litellm" / "config.yaml"

_ROLES = {"reasoning", "utility", "embeddings", "vision"}
_CLEARANCES = {"public", "internal", "confidential", "pii"}


@pytest.fixture(scope="module")
def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _names(config: dict) -> set[str]:
    return {m["model_name"] for m in config["model_list"]}


def test_every_model_has_name_id_and_valid_prices(config: dict) -> None:
    for entry in config["model_list"]:
        assert entry.get("model_name"), entry
        params = entry["litellm_params"]
        assert params.get("model"), entry["model_name"]
        for key in ("input_cost_per_token", "output_cost_per_token"):
            price = params.get(key)
            assert isinstance(price, (int, float)) and price >= 0, (
                entry["model_name"],
                key,
                price,
            )


def test_model_info_roles_and_clearances_are_known(config: dict) -> None:
    for entry in config["model_list"]:
        info = entry.get("model_info", {})
        assert info.get("fleet_role") in _ROLES, entry["model_name"]
        assert info.get("sensitivity_clearance") in _CLEARANCES, entry["model_name"]


def test_no_cloud_model_is_cleared_for_pii(config: dict) -> None:
    # TRD §4.2: no cloud model is ever cleared for pii — only local (ollama) is.
    for entry in config["model_list"]:
        info = entry.get("model_info", {})
        if info.get("sensitivity_clearance") == "pii":
            assert entry["litellm_params"]["model"].startswith("ollama/"), entry[
                "model_name"
            ]


def test_all_fallback_targets_are_defined_models(config: dict) -> None:
    names = _names(config)
    fallbacks = config["litellm_settings"]["fallbacks"]
    for mapping in fallbacks:
        for primary, chain in mapping.items():
            assert primary in names, primary
            for target in chain:
                assert target in names, (primary, target)


def test_reasoning_and_utility_roles_present(config: dict) -> None:
    roles = {m["model_info"]["fleet_role"] for m in config["model_list"]}
    assert {"reasoning", "utility", "embeddings"} <= roles
