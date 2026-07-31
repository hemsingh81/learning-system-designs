"""
Token and cost accounting.

Why this exists: cost is invisible until you measure it. Every LLMClient
call returns a `Usage` so that skills, workflows, and (later) the agent's
budget can add these up and answer "how much did this run cost?" the same
way you'd track DB round-trips or external API calls in normal backend
observability.

Prices below are ILLUSTRATIVE per-million-token list prices, kept in one
place so updating them updates every cost estimate in the project at once.
Check https://www.anthropic.com/pricing for current numbers before relying
on this for a real budget decision — see docs/07-cost-and-latency.md.
"""

from __future__ import annotations

from dataclasses import dataclass

# USD per 1,000,000 tokens. (input, output)
_PRICING_PER_MILLION_USD: dict[str, tuple[float, float]] = {
    "claude-3-5-haiku-latest": (0.80, 4.00),
    "claude-3-5-sonnet-latest": (3.00, 15.00),
    "fake": (0.0, 0.0),
}
_DEFAULT_PRICING = (1.00, 5.00)  # used for any model not in the table above


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


ZERO_USAGE = Usage(input_tokens=0, output_tokens=0)


def estimate_cost_usd(model: str, usage: Usage) -> float:
    """Rough dollar estimate for one call. Good enough to catch a budget
    problem before it becomes a real bill — not good enough for accounting."""
    input_price, output_price = _PRICING_PER_MILLION_USD.get(model, _DEFAULT_PRICING)
    cost = (usage.input_tokens / 1_000_000) * input_price
    cost += (usage.output_tokens / 1_000_000) * output_price
    return round(cost, 6)


class UsageTracker:
    """Accumulates usage/cost across many calls in one run. Used by the
    Agentic budget module (Milestone 6) and by any example that wants to
    print "this run cost $X" at the end."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.total_usage = ZERO_USAGE
        self.call_count = 0

    def record(self, usage: Usage) -> None:
        self.total_usage = self.total_usage + usage
        self.call_count += 1

    @property
    def total_cost_usd(self) -> float:
        return estimate_cost_usd(self.model, self.total_usage)

    def summary(self) -> str:
        return (
            f"{self.call_count} call(s), "
            f"{self.total_usage.total_tokens} tokens "
            f"({self.total_usage.input_tokens} in / {self.total_usage.output_tokens} out), "
            f"~${self.total_cost_usd:.4f}"
        )
