"""Unit tests for workflow/engine.py — Step and Pipeline mechanics, in
isolation from any real skill or LLM call."""

from __future__ import annotations

import pytest

from aisets.workflow.context import WorkflowContext
from aisets.workflow.engine import Pipeline, Step, WorkflowError
from aisets.workflow.policies import CircuitBreaker, RetryPolicy


def test_step_runs_and_records_trace() -> None:
    ctx = WorkflowContext()
    step = Step("say_hi", lambda c: c.set("greeted", True))

    outcome = step.run(ctx)

    assert outcome.status == "ok"
    assert outcome.attempts == 1
    assert ctx["greeted"] is True
    assert ctx.trace == ["say_hi"]


def test_step_skipped_by_condition_does_not_run_action() -> None:
    ctx = WorkflowContext()
    ran = {"value": False}

    def action(c: WorkflowContext) -> None:
        ran["value"] = True

    step = Step("maybe", action, condition=lambda c: False)
    outcome = step.run(ctx)

    assert outcome.status == "skipped"
    assert ran["value"] is False


def test_step_retries_on_failure_then_succeeds() -> None:
    ctx = WorkflowContext()
    attempts = {"count": 0}

    def flaky(c: WorkflowContext) -> None:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient failure")

    step = Step("flaky", flaky, retry=RetryPolicy(max_attempts=3))
    outcome = step.run(ctx)

    assert outcome.status == "ok"
    assert outcome.attempts == 3


def test_step_exhausts_retries_and_uses_fallback() -> None:
    ctx = WorkflowContext()

    def always_fails(c: WorkflowContext) -> None:
        raise RuntimeError("permanent failure")

    def fallback(c: WorkflowContext) -> None:
        c.set("used_fallback", True)

    step = Step("broken", always_fails, retry=RetryPolicy(max_attempts=2), fallback=fallback)
    outcome = step.run(ctx)

    assert outcome.status == "fallback"
    assert outcome.attempts == 2
    assert ctx["used_fallback"] is True


def test_step_exhausts_retries_with_no_fallback_reports_failed() -> None:
    ctx = WorkflowContext()

    def always_fails(c: WorkflowContext) -> None:
        raise RuntimeError("permanent failure")

    step = Step("broken", always_fails, retry=RetryPolicy(max_attempts=2))
    outcome = step.run(ctx)

    assert outcome.status == "failed"
    assert "permanent failure" in outcome.error


def test_circuit_breaker_opens_after_threshold_and_uses_fallback() -> None:
    ctx = WorkflowContext()
    breaker = CircuitBreaker(failure_threshold=2)

    def always_fails(c: WorkflowContext) -> None:
        raise RuntimeError("dependency down")

    def fallback(c: WorkflowContext) -> None:
        c.set("fell_back", True)

    step = Step("dep_call", always_fails, retry=RetryPolicy(max_attempts=1), breaker=breaker, fallback=fallback)

    step.run(ctx)  # failure 1
    step.run(ctx)  # failure 2 -> breaker opens
    assert breaker.is_open

    outcome = step.run(ctx)  # breaker now open, should short-circuit to fallback
    assert outcome.status == "fallback"
    assert outcome.error == "circuit breaker open"
    assert ctx["fell_back"] is True


def test_circuit_breaker_open_with_no_fallback_raises() -> None:
    ctx = WorkflowContext()
    breaker = CircuitBreaker(failure_threshold=1)

    def always_fails(c: WorkflowContext) -> None:
        raise RuntimeError("dependency down")

    step = Step("dep_call", always_fails, retry=RetryPolicy(max_attempts=1), breaker=breaker)
    step.run(ctx)  # opens the breaker
    assert breaker.is_open

    with pytest.raises(WorkflowError, match="circuit breaker is open"):
        step.run(ctx)


def test_pipeline_runs_all_steps_in_order() -> None:
    ctx = WorkflowContext()
    pipeline = Pipeline("demo", [
        Step("a", lambda c: c.set("a", 1)),
        Step("b", lambda c: c.set("b", 2)),
        Step("c", lambda c: c.set("c", 3)),
    ])

    outcomes = pipeline.run(ctx)

    assert [o.name for o in outcomes] == ["a", "b", "c"]
    assert all(o.status == "ok" for o in outcomes)
    assert ctx["a"] == 1 and ctx["b"] == 2 and ctx["c"] == 3


def test_pipeline_stops_after_a_failed_step_with_no_fallback() -> None:
    ctx = WorkflowContext()

    def boom(c: WorkflowContext) -> None:
        raise RuntimeError("stop here")

    ran_after = {"value": False}

    pipeline = Pipeline("demo", [
        Step("a", lambda c: c.set("a", 1)),
        Step("b", boom),
        Step("c", lambda c: ran_after.__setitem__("value", True)),
    ])

    outcomes = pipeline.run(ctx)

    assert [o.name for o in outcomes] == ["a", "b"]  # step "c" never ran
    assert outcomes[-1].status == "failed"
    assert ran_after["value"] is False
