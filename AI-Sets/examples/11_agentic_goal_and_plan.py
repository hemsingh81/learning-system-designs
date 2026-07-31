"""
Example 11 — Goal + Planner: the first Agentic building block. Notice
the plan is plain-English INTENT ("check payments metrics"), not a tool
call — the agent loop (Milestone 5) still decides the actual tool calls
when it's time to act.

Run:
    .\\scripts\\run-example.ps1 11_agentic_goal_and_plan
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.agentic.goal import Goal
from aisets.agentic.planner import Planner

GOAL = Goal(
    objective="Determine the root cause of the payments service incident and recommend a fix.",
    success_criteria=[
        "Identify which service is affected and the specific failure mode.",
        "Cite concrete evidence (log lines and/or metrics) supporting the conclusion.",
        "Recommend an action, backed by a runbook, without actually taking it.",
    ],
    hard_constraints=[
        "Never take a write action (restart/scale/page) without human approval.",
    ],
    stop_conditions=[
        "Stop once a root cause is identified and a runbook-backed recommendation is made.",
    ],
)


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        llm.queue_json({
            "steps": [
                "Check payments service metrics for latency and error-rate spikes.",
                "Search logs around the spike window for error patterns.",
                "Query the orders database for failed payments during that window.",
                "Find a runbook matching the observed failure mode.",
                "Summarize the root cause and the runbook's recommended fix.",
            ],
            "reasoning": "Metrics narrow down WHEN/HOW BAD, logs and orders confirm WHY, "
            "and a runbook grounds the recommendation instead of guessing.",
        })

    planner = Planner(llm)
    plan = planner.make_plan(GOAL)

    console.print(f"\n[bold]Goal:[/bold]\n{GOAL.describe()}\n")
    console.print("[bold]Plan:[/bold]")
    for i, step in enumerate(plan.steps, start=1):
        console.print(f"  {i}. {step}")
    console.print(f"\n[dim]Reasoning: {plan.reasoning}[/dim]")


if __name__ == "__main__":
    main()
