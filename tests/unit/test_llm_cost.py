"""Token usage parsing + cost computation for the gateway client (task 2.3).

The proxy returns an OpenAI-style response with a `usage` block; the client
computes cost from token counts and the model's per-1k prices, metering cached
input tokens at the cached price (TRD §5 prompt caching). Pure functions, so no
network needed.
"""

from __future__ import annotations

from core.llm.cost import Usage, compute_cost, parse_usage


def test_parse_usage_reads_openai_style_block() -> None:
    body = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 40,
            "prompt_tokens_details": {"cached_tokens": 25},
        }
    }
    usage = parse_usage(body)
    assert usage.tok_in == 100
    assert usage.tok_out == 40
    assert usage.tok_cached == 25


def test_parse_usage_defaults_to_zero_when_absent() -> None:
    usage = parse_usage({})
    assert usage == Usage(tok_in=0, tok_out=0, tok_cached=0)


def test_compute_cost_uses_per_1k_prices() -> None:
    usage = Usage(tok_in=1000, tok_out=500, tok_cached=0)
    # in: 1000/1000 * 0.003 = 0.003 ; out: 500/1000 * 0.015 = 0.0075
    cost = compute_cost(usage, input_price_per_1k=0.003, output_price_per_1k=0.015)
    assert round(cost, 6) == round(0.003 + 0.0075, 6)


def test_cached_tokens_billed_at_cached_price_not_full_input() -> None:
    usage = Usage(tok_in=1000, tok_out=0, tok_cached=800)
    # 200 uncached in @0.003/1k + 800 cached @0.0003/1k
    cost = compute_cost(
        usage,
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        cached_input_price_per_1k=0.0003,
    )
    expected = (200 / 1000) * 0.003 + (800 / 1000) * 0.0003
    assert round(cost, 8) == round(expected, 8)


def test_cost_is_zero_for_free_local_model() -> None:
    usage = Usage(tok_in=5000, tok_out=2000, tok_cached=0)
    cost = compute_cost(usage, input_price_per_1k=0.0, output_price_per_1k=0.0)
    assert cost == 0.0
