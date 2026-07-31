"""
The workflow engine: `Step` and `Pipeline`.

A pipeline is a FIXED, ordered list of steps — the order is decided by
whoever calls `Pipeline(...)`, not by the model (that's what makes this a
Workflow and not an Agent — see docs/01-concepts.md). Each step can be
skipped by a condition (branching you control), retried with backoff, and
given a fallback if it ultimately fails.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Literal

from aisets.workflow.context import WorkflowContext
from aisets.workflow.policies import NO_RETRY, CircuitBreaker, RetryPolicy

logger = logging.getLogger(__name__)

StepStatus = Literal["ok", "skipped", "fallback", "failed"]


class WorkflowError(Exception):
    """Raised when a step configuration itself is invalid (e.g. a circuit
    breaker is open and there's no fallback to fall back to)."""


@dataclass
class StepOutcome:
    name: str
    status: StepStatus
    attempts: int = 1
    error: str | None = None


class Step:
    def __init__(
        self,
        name: str,
        action: Callable[[WorkflowContext], None],
        *,
        condition: Callable[[WorkflowContext], bool] | None = None,
        retry: RetryPolicy | None = None,
        fallback: Callable[[WorkflowContext], None] | None = None,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self.name = name
        self.action = action
        self.condition = condition
        self.retry = retry or NO_RETRY
        self.fallback = fallback
        self.breaker = breaker

    def run(self, ctx: WorkflowContext) -> StepOutcome:
        if self.condition is not None and not self.condition(ctx):
            logger.info("step '%s' skipped (condition was false)", self.name)
            ctx.record(f"{self.name}:skipped")
            return StepOutcome(self.name, "skipped")

        if self.breaker is not None and self.breaker.is_open:
            if self.fallback is not None:
                self.fallback(ctx)
                logger.warning("step '%s' breaker OPEN, used fallback", self.name)
                ctx.record(f"{self.name}:fallback(breaker-open)")
                return StepOutcome(self.name, "fallback", error="circuit breaker open")
            raise WorkflowError(
                f"step '{self.name}': circuit breaker is open and no fallback is configured"
            )

        last_exc: Exception | None = None
        for attempt in range(self.retry.max_attempts):
            try:
                self.action(ctx)
            except Exception as exc:  # noqa: BLE001 - deliberately broad: any failure counts
                last_exc = exc
                if self.breaker is not None:
                    self.breaker.record_failure()
                logger.warning(
                    "step '%s' attempt %d/%d failed: %s",
                    self.name, attempt + 1, self.retry.max_attempts, exc,
                )
                if attempt < self.retry.max_attempts - 1:
                    self.retry.sleep_before_retry(attempt)
                continue
            else:
                if self.breaker is not None:
                    self.breaker.record_success()
                ctx.record(self.name)
                return StepOutcome(self.name, "ok", attempts=attempt + 1)

        # Every attempt failed.
        if self.fallback is not None:
            self.fallback(ctx)
            ctx.record(f"{self.name}:fallback")
            return StepOutcome(
                self.name, "fallback", attempts=self.retry.max_attempts, error=str(last_exc)
            )

        ctx.record(f"{self.name}:failed")
        return StepOutcome(
            self.name, "failed", attempts=self.retry.max_attempts, error=str(last_exc)
        )


class Pipeline:
    def __init__(self, name: str, steps: list[Step]) -> None:
        self.name = name
        self.steps = steps

    def run(self, ctx: WorkflowContext) -> list[StepOutcome]:
        outcomes: list[StepOutcome] = []
        for step in self.steps:
            outcome = step.run(ctx)
            outcomes.append(outcome)
            if outcome.status == "failed":
                logger.error(
                    "pipeline '%s' stopped: step '%s' failed with no fallback",
                    self.name, step.name,
                )
                break
        return outcomes
