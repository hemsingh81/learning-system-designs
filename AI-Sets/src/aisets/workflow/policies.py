"""
Reliability policies a workflow step can be wrapped with: retry with
backoff, and a circuit breaker. These live at the WORKFLOW level, not
inside a skill — see tutorial/02-workflows/DECISIONS.md for why "retry
the whole step" and "retry inside the skill" (Milestone 2's one retry on
bad output) are two different, both-correct decisions at two different
layers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryPolicy:
    """Retry a step up to `max_attempts` times, sleeping `backoff_seconds[i]`
    between attempt i and i+1. An empty `backoff_seconds` means no sleep
    (useful in tests, so they don't burn wall-clock time)."""

    max_attempts: int = 1
    backoff_seconds: tuple[float, ...] = ()

    def sleep_before_retry(self, attempt_index: int) -> None:
        if attempt_index < len(self.backoff_seconds):
            time.sleep(self.backoff_seconds[attempt_index])


NO_RETRY = RetryPolicy(max_attempts=1)


class CircuitBreaker:
    """After `failure_threshold` consecutive failures, the breaker OPENS:
    further calls are refused immediately (routed to the step's fallback,
    if any) instead of trying the real action again. This protects a
    struggling dependency (or a burning API budget) from being hammered
    by every subsequent pipeline run.

    A production version would also auto-CLOSE after a cooldown window;
    this teaching version stays open until `reset()` is called explicitly,
    to keep the behavior simple to reason about and test.
    """

    def __init__(self, failure_threshold: int = 3) -> None:
        self.failure_threshold = failure_threshold
        self._consecutive_failures = 0
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._open = False

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._open = True

    def reset(self) -> None:
        self._consecutive_failures = 0
        self._open = False
