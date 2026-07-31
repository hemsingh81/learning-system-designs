"""
`Critic` — checks a proposed answer against the ORIGINAL goal before
declaring success. This is cheap insurance: one extra model call that
asks, skeptically, "does this actually satisfy what we set out to do?"

Why a separate call instead of trusting the investigating agent's own
"I'm done" signal: the same reason a code reviewer is a different person
(or at least a different pass) than the author — a fresh, skeptical look
catches things the original reasoning missed, especially "I answered A
when the goal asked for A AND B".
"""

from __future__ import annotations

from pydantic import BaseModel

from aisets.agentic.goal import Goal
from aisets.llm.base import LLMClient, Message

_SYSTEM = (
    "You are a strict, skeptical reviewer. You will be given a goal and a "
    "proposed final answer from an investigation. Decide whether the "
    "answer ACTUALLY satisfies every success criterion — do not be "
    "generous. If any criterion is not clearly met by the answer, mark "
    "goal_met=false and list exactly what's missing.\n\n"
    "Respond ONLY by calling the provided tool."
)


class CriticVerdict(BaseModel):
    goal_met: bool
    reasoning: str
    missing: list[str] = []


class Critic:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def check(self, goal: Goal, proposed_answer: str, evidence_notes: str = "") -> CriticVerdict:
        content = (
            f"{goal.describe()}\n\n"
            f"Proposed final answer:\n{proposed_answer}\n\n"
            f"Evidence gathered along the way:\n{evidence_notes or '(none recorded)'}"
        )
        messages = [Message(role="user", content=content)]
        return self.llm.complete_json(messages, CriticVerdict, system=_SYSTEM)
