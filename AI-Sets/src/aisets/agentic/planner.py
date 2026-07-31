"""
`Planner` — turns a `Goal` into an ordered list of INTENDED investigation
steps, in plain English (not tool calls — the agent loop, Milestone 5,
still decides the actual tool calls; the plan is a higher-level map of
intent, the same way a human on-call engineer might jot "1. check
metrics, 2. check logs, 3. check runbook" before touching a keyboard).

Re-planning: when the Critic (critic.py) rejects a result, call
`make_plan` again, passing what was tried and why it fell short as
`context_notes` — this is "re-plan when reality surprises you", not a
separate code path.
"""

from __future__ import annotations

from pydantic import BaseModel

from aisets.agentic.goal import Goal
from aisets.llm.base import LLMClient, Message

_SYSTEM_TEMPLATE = (
    "You are planning how to achieve a goal for a backend incident "
    "investigation. You do NOT execute anything yourself — you only "
    "produce a short, ordered list of investigation steps in plain "
    "English (e.g. 'check payments service metrics', not a tool call).\n\n"
    "{goal_description}\n\n"
    "Rules:\n"
    "- 3-6 steps, each one short sentence.\n"
    "- Steps should progress from gathering evidence to forming a "
    "hypothesis to proposing a fix.\n"
    "- Never include a step that itself takes a destructive action "
    "(restarting/scaling/paging) — those are proposed as a RECOMMENDATION "
    "in the final answer, not as a planning step.\n"
    "- Respond ONLY by calling the provided tool."
)


class Plan(BaseModel):
    steps: list[str]
    reasoning: str


class Planner:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def make_plan(self, goal: Goal, context_notes: str = "") -> Plan:
        system = _SYSTEM_TEMPLATE.format(goal_description=goal.describe())
        content = f"Context so far:\n{context_notes}" if context_notes else "Context so far: (nothing yet — this is the first plan)"
        messages = [Message(role="user", content=content)]
        return self.llm.complete_json(messages, Plan, system=system)
