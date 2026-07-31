"""Unit tests for agentic/budget.py — using an injected fake clock so no
test actually sleeps or depends on wall-clock time."""

from __future__ import annotations

import pytest

from aisets.agentic.budget import Budget, BudgetExceeded, BudgetLimits


def make_fake_clock():
    state = {"now": 0.0}

    def clock() -> float:
        return state["now"]

    def advance(seconds: float) -> None:
        state["now"] += seconds

    return clock, advance


def test_budget_allows_steps_under_the_limit() -> None:
    budget = Budget(limits=BudgetLimits(max_steps=3, max_usd=1.0, max_seconds=100.0))
    budget.record_step(cost_usd=0.1)
    budget.record_step(cost_usd=0.1)
    assert budget.steps_used == 2
    assert budget.remaining_steps() == 1


def test_budget_raises_when_step_limit_exceeded() -> None:
    budget = Budget(limits=BudgetLimits(max_steps=2, max_usd=10.0, max_seconds=100.0))
    budget.record_step()
    budget.record_step()
    with pytest.raises(BudgetExceeded, match="step budget exceeded"):
        budget.record_step()


def test_budget_raises_when_cost_limit_exceeded() -> None:
    budget = Budget(limits=BudgetLimits(max_steps=10, max_usd=0.10, max_seconds=100.0))
    budget.record_step(cost_usd=0.06)
    with pytest.raises(BudgetExceeded, match="cost budget exceeded"):
        budget.record_step(cost_usd=0.06)


def test_budget_raises_when_time_limit_exceeded_using_fake_clock() -> None:
    clock, advance = make_fake_clock()
    budget = Budget(limits=BudgetLimits(max_steps=100, max_usd=100.0, max_seconds=10.0), clock=clock)
    budget.start()
    budget.record_step()  # elapsed = 0, fine

    advance(11.0)
    with pytest.raises(BudgetExceeded, match="time budget exceeded"):
        budget.record_step()


def test_budget_without_start_never_checks_time() -> None:
    budget = Budget(limits=BudgetLimits(max_steps=100, max_usd=100.0, max_seconds=0.0))
    # start() was never called -> time check is skipped entirely.
    budget.record_step()
    budget.record_step()
    assert budget.steps_used == 2


def test_remaining_usd_never_goes_negative() -> None:
    budget = Budget(limits=BudgetLimits(max_steps=10, max_usd=0.05, max_seconds=100.0))
    with pytest.raises(BudgetExceeded):
        budget.record_step(cost_usd=0.10)
    assert budget.remaining_usd() == 0.0
