"""Unit tests for the usage/cost accounting helpers (llm/usage.py)."""

from __future__ import annotations

from aisets.llm.usage import Usage, UsageTracker, estimate_cost_usd


def test_usage_add() -> None:
    a = Usage(input_tokens=10, output_tokens=5)
    b = Usage(input_tokens=3, output_tokens=1)
    total = a + b
    assert total.input_tokens == 13
    assert total.output_tokens == 6
    assert total.total_tokens == 19


def test_estimate_cost_usd_known_model() -> None:
    usage = Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    cost = estimate_cost_usd("claude-3-5-haiku-latest", usage)
    assert cost == 0.80 + 4.00


def test_estimate_cost_usd_unknown_model_uses_default_pricing() -> None:
    usage = Usage(input_tokens=1_000_000, output_tokens=0)
    cost = estimate_cost_usd("some-future-model", usage)
    assert cost == 1.00


def test_estimate_cost_usd_fake_model_is_free() -> None:
    usage = Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    assert estimate_cost_usd("fake", usage) == 0.0


def test_usage_tracker_accumulates() -> None:
    tracker = UsageTracker(model="fake")
    tracker.record(Usage(input_tokens=10, output_tokens=5))
    tracker.record(Usage(input_tokens=20, output_tokens=10))

    assert tracker.call_count == 2
    assert tracker.total_usage.total_tokens == 45
    assert "2 call(s)" in tracker.summary()
