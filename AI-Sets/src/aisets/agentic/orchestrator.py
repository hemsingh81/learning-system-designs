"""
Multi-agent orchestration: a `Supervisor` dispatches ONE task to several
independent `Specialist`s, collects their results — CONTINUING even if
one fails or times out — and synthesizes a final answer from whichever
specialists succeeded, flagging any contradictions between them.

This is the "several agents, each with a different job" pattern from
docs/01-concepts.md's Level 4 diagram, generalized: investigator, fixer,
and communicator (used in example 14) are just three named `Specialist`
instances — nothing here is hard-coded to those roles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pydantic import BaseModel

from aisets.llm.base import LLMClient, Message

_SYNTHESIS_SYSTEM = (
    "You are combining the findings of several independent specialists "
    "who each investigated the SAME task from a different angle. Write a "
    "short synthesis that reflects what they collectively found. If two "
    "specialists say something that conflicts, list it under "
    "contradictions instead of silently picking one — a human should "
    "resolve genuine contradictions, not the synthesis step.\n\n"
    "Respond ONLY by calling the provided tool."
)


class SpecialistTimeout(Exception):
    """A specialist took too long / stalled. Distinct from a plain
    failure so the orchestrator's log can tell the two apart."""


@dataclass
class SpecialistResult:
    name: str
    output: str
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class Specialist:
    def __init__(self, name: str, run_fn: Callable[[str], str]) -> None:
        self.name = name
        self.run_fn = run_fn

    def run(self, task: str) -> SpecialistResult:
        try:
            output = self.run_fn(task)
            return SpecialistResult(name=self.name, output=output)
        except Exception as exc:  # noqa: BLE001 - a specialist's own failure must never crash the whole orchestration
            return SpecialistResult(name=self.name, output="", error=str(exc))


class Synthesis(BaseModel):
    summary: str
    contradictions: list[str] = []


@dataclass
class OrchestrationResult:
    final_answer: str
    specialist_results: list[SpecialistResult] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    synthesis_skipped: bool = False


class Supervisor:
    def __init__(self, llm: LLMClient, specialists: list[Specialist]) -> None:
        self.llm = llm
        self.specialists = specialists

    def run(self, task: str) -> OrchestrationResult:
        results = [specialist.run(task) for specialist in self.specialists]
        succeeded = [r for r in results if r.succeeded]
        failed = [r for r in results if not r.succeeded]

        if not succeeded:
            return OrchestrationResult(
                final_answer=(
                    "All specialists failed — cannot synthesize an answer. "
                    f"Failures: {', '.join(f'{r.name} ({r.error})' for r in failed)}"
                ),
                specialist_results=results,
                synthesis_skipped=True,
            )

        parts = [f"[{r.name}]\n{r.output}" for r in succeeded]
        if failed:
            parts.append(
                "[NOTE] The following specialists failed and are excluded from "
                f"this synthesis: {', '.join(f'{r.name} ({r.error})' for r in failed)}"
            )
        content = "\n\n".join(parts)

        synthesis = self.llm.complete_json([Message(role="user", content=content)], Synthesis, system=_SYNTHESIS_SYSTEM)

        return OrchestrationResult(
            final_answer=synthesis.summary,
            specialist_results=results,
            contradictions=synthesis.contradictions,
            synthesis_skipped=False,
        )
