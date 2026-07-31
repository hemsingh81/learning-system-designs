"""
`Budget` — hard caps on steps, money, and wall-clock time for one Agentic
run. Milestone 5's `AgentLoop` already caps STEPS for a single question;
this extends the same idea across an entire multi-phase investigation
(plan -> act -> critic -> maybe re-plan -> act again...), where the
overall cost could otherwise be unbounded even if each individual agent
call is well-behaved.

A `clock` parameter is injected (defaults to `time.monotonic`) so tests
can supply a fake, controllable clock instead of actually sleeping —
see docs/00-PLAN.md's rule that unit tests must stay fast and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class BudgetExceeded(Exception):
    """Raised the moment ANY limit (steps, dollars, seconds) is crossed."""


@dataclass(frozen=True)
class BudgetLimits:
    max_steps: int = 10
    max_usd: float = 0.50
    max_seconds: float = 60.0


@dataclass
class Budget:
    limits: BudgetLimits
    clock: Callable[[], float] = field(default=None)  # type: ignore[assignment]
    steps_used: int = 0
    usd_spent: float = 0.0
    _start_time: float | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.clock is None:
            import time
            self.clock = time.monotonic

    def start(self) -> None:
        self._start_time = self.clock()

    def record_step(self, cost_usd: float = 0.0) -> None:
        self.steps_used += 1
        self.usd_spent += cost_usd
        self._check()

    def remaining_steps(self) -> int:
        return max(0, self.limits.max_steps - self.steps_used)

    def remaining_usd(self) -> float:
        return max(0.0, self.limits.max_usd - self.usd_spent)

    def _check(self) -> None:
        if self.steps_used > self.limits.max_steps:
            raise BudgetExceeded(
                f"step budget exceeded: used {self.steps_used}, limit {self.limits.max_steps}"
            )
        if self.usd_spent > self.limits.max_usd:
            raise BudgetExceeded(
                f"cost budget exceeded: spent ${self.usd_spent:.4f}, limit ${self.limits.max_usd:.4f}"
            )
        if self._start_time is not None:
            elapsed = self.clock() - self._start_time
            if elapsed > self.limits.max_seconds:
                raise BudgetExceeded(
                    f"time budget exceeded: elapsed {elapsed:.1f}s, limit {self.limits.max_seconds:.1f}s"
                )
