"""
Example 12 — Critic + re-plan: the agent's own investigation runs, the
Critic checks the result against the ORIGINAL goal, REJECTS it as
incomplete, and the investigation runs again with that feedback folded
in — succeeding on the second attempt.

This wires Milestone 5's AgentLoop + Milestone 6's Planner/Critic
together by hand, in this script, to show how you'd compose the building
blocks yourself for a real use case.

Run:
    .\\scripts\\run-example.ps1 12_agentic_self_correct
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.agent.simple_agent import build_simple_agent
from aisets.agentic.critic import Critic
from aisets.agentic.goal import Goal
from aisets.llm.base import LLMResponse, ToolCall

GOAL = Goal(
    objective="Determine the root cause of order 9002's failure and cite the specific evidence.",
    success_criteria=[
        "States the specific failure reason (not just 'it failed').",
        "Cites at least one concrete piece of evidence (a log line or a metric value).",
    ],
)


def main() -> None:
    settings, llm = setup()
    agent = build_simple_agent(llm, settings)
    critic = Critic(llm)

    if is_fake(llm):
        # --- Attempt 1: a weak, incomplete answer ---
        llm.queue_response(LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="c1", name="query_orders", arguments={"order_id": "9002"})],
            stop_reason="tool_use",
        ))
        llm.queue_response(LLMResponse(text="Order 9002 failed. Not sure why.", stop_reason="end_turn"))
        # Critic rejects: no specific reason, no cited evidence.
        llm.queue_json({
            "goal_met": False,
            "reasoning": "The answer does not state a specific failure reason or cite any evidence.",
            "missing": ["a specific failure reason", "cited evidence (a log line or metric)"],
        })

        # --- Attempt 2: a stronger answer, informed by what was missing ---
        llm.queue_response(LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="c2", name="search_logs", arguments={"query": "payment-gateway timed out", "max_lines": 2})],
            stop_reason="tool_use",
        ))
        llm.queue_response(LLMResponse(
            text=(
                "Order 9002 failed due to a payment-gateway timeout "
                "(fail_reason='payment_gateway_timeout'). Log evidence: "
                "'2026-06-15T02:14:00 ERROR payments upstream call to "
                "payment-gateway timed out after 5000ms'."
            ),
            stop_reason="end_turn",
        ))
        llm.queue_json({
            "goal_met": True,
            "reasoning": "Specific failure reason is stated and a concrete log line is cited.",
            "missing": [],
        })

    console.rule("Attempt 1")
    result1 = agent.run("Why did order 9002 fail?")
    console.print(f"Answer: {result1.final_answer}")
    verdict1 = critic.check(GOAL, result1.final_answer)
    console.print(f"Critic: goal_met={verdict1.goal_met} — {verdict1.reasoning}")
    if verdict1.missing:
        console.print(f"Missing: {verdict1.missing}")

    if not verdict1.goal_met:
        console.rule("Re-planning: attempt 2, informed by what was missing")
        result2 = agent.run(
            "Why did order 9002 fail? Be specific about the failure reason and cite log evidence."
        )
        console.print(f"Answer: {result2.final_answer}")
        verdict2 = critic.check(GOAL, result2.final_answer)
        console.print(f"Critic: goal_met={verdict2.goal_met} — {verdict2.reasoning}")


if __name__ == "__main__":
    main()
