"""Pricing sync for the LiteLLM proxy config (task 2.1).

Keeps the per-token input/output prices in `gateway/litellm/config.yaml` in step
with LiteLLM's canonical price map (`litellm.model_cost`). The registry (task
2.2) and this config are the two places prices live; this script is the tool that
refreshes the config side so the proxy meters spend at correct rates.

Run as a module against the real price map:

    uv run python -m pricing_sync            # from gateway/litellm/
    python gateway/litellm/pricing_sync.py --check   # CI: fail if drifted

The core (`sync_prices`) is a pure function over dicts so it is unit-testable
without the litellm package or network access.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


class PriceValidationError(Exception):
    """Raised in strict mode when a model's price cannot be resolved or is invalid."""


@dataclass
class SyncReport:
    """Outcome of a sync pass."""

    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unresolved and not self.invalid


def _is_local(model_id: str) -> bool:
    """Local-lane (Ollama/vLLM) models are free and absent from the price map."""
    return model_id.startswith("ollama/") or model_id.startswith("vllm/")


def _valid_price(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def sync_prices(
    config: dict[str, Any],
    prices: dict[str, dict[str, float]],
    *,
    strict: bool = False,
) -> tuple[dict[str, Any], SyncReport]:
    """Return a copy of `config` with per-token prices refreshed from `prices`.

    `prices` maps a litellm model id (e.g. ``anthropic/claude-sonnet-4-5``) to a
    dict with ``input_cost_per_token`` / ``output_cost_per_token`` (the shape of
    ``litellm.model_cost`` entries). Local (Ollama) models are treated as free.

    A cloud model with no source price and a non-positive config price is
    reported as *unresolved*; a source price that is negative/non-numeric is
    *invalid*. In ``strict`` mode either condition raises PriceValidationError.
    """
    import copy

    out = copy.deepcopy(config)
    report = SyncReport()

    for entry in out.get("model_list", []):
        name = entry.get("model_name", "<unnamed>")
        params = entry.setdefault("litellm_params", {})
        model_id = params.get("model", "")
        source = prices.get(model_id)

        if source is not None:
            in_price = source.get("input_cost_per_token")
            out_price = source.get("output_cost_per_token", 0.0)
            if not _valid_price(in_price) or not _valid_price(out_price):
                report.invalid.append(name)
                continue
            changed = (
                params.get("input_cost_per_token") != in_price
                or params.get("output_cost_per_token") != out_price
            )
            params["input_cost_per_token"] = in_price
            params["output_cost_per_token"] = out_price
            (report.updated if changed else report.unchanged).append(name)
            continue

        # No source entry.
        if _is_local(model_id):
            params.setdefault("input_cost_per_token", 0.0)
            params.setdefault("output_cost_per_token", 0.0)
            report.unchanged.append(name)
            continue

        # Cloud model with no source price: valid only if it already carries a
        # positive price (hand-pinned in config); otherwise unresolved.
        existing = params.get("input_cost_per_token")
        if _valid_price(existing) and existing > 0:
            report.unchanged.append(name)
        else:
            report.unresolved.append(name)

    if strict and not report.ok:
        problems = report.unresolved + report.invalid
        raise PriceValidationError(
            "unresolved/invalid prices for: " + ", ".join(sorted(problems))
        )
    return out, report


def _load_litellm_price_map() -> dict[str, dict[str, float]]:
    """Best-effort load of LiteLLM's canonical price map; empty if unavailable."""
    try:
        import litellm  # type: ignore
    except Exception:  # pragma: no cover - litellm not installed in unit env
        return {}
    return dict(getattr(litellm, "model_cost", {}))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync LiteLLM config prices.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit non-zero if the config would change or is invalid",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args(argv)

    import yaml  # local import; only the CLI path needs pyyaml

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    prices = _load_litellm_price_map()
    updated, report = sync_prices(config, prices, strict=args.check)

    if args.check:
        if report.updated or not report.ok:
            print(
                f"pricing drift: updated={report.updated} "
                f"unresolved={report.unresolved} invalid={report.invalid}"
            )
            return 1
        print("pricing in sync")
        return 0

    args.config.write_text(
        yaml.safe_dump(updated, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    print(
        f"synced: updated={len(report.updated)} unchanged={len(report.unchanged)} "
        f"unresolved={report.unresolved} invalid={report.invalid}"
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
