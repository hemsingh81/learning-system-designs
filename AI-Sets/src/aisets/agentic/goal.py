"""
`Goal` — what turns an agent (Milestone 5, answers ONE question) into
Agentic AI (owns a standing objective across a longer investigation).

A goal is plain data, not behavior — the Planner, Critic, and Escalation
modules all read it, but none of them mutate it. Think of it like an
immutable ticket/work-item description: everyone downstream refers back
to the SAME stated objective, success criteria, and hard constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Goal:
    objective: str
    success_criteria: list[str] = field(default_factory=list)
    hard_constraints: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)

    def describe(self) -> str:
        """A plain-text rendering used inside prompts (Planner, Critic).
        Kept in ONE place so every prompt describes the goal identically."""
        lines = [f"Objective: {self.objective}"]
        if self.success_criteria:
            lines.append("Success criteria:")
            lines.extend(f"  - {c}" for c in self.success_criteria)
        if self.hard_constraints:
            lines.append("Hard constraints (must never be violated):")
            lines.extend(f"  - {c}" for c in self.hard_constraints)
        if self.stop_conditions:
            lines.append("Stop conditions:")
            lines.extend(f"  - {c}" for c in self.stop_conditions)
        return "\n".join(lines)
