"""Unit tests for agentic/planner.py."""

from __future__ import annotations

from aisets.agentic.goal import Goal
from aisets.agentic.planner import Planner


def test_make_plan_happy_path(fake_llm) -> None:
    fake_llm.queue_json({
        "steps": ["check metrics", "check logs", "propose a fix"],
        "reasoning": "standard investigation order",
    })
    goal = Goal(objective="find the root cause")
    planner = Planner(fake_llm)

    plan = planner.make_plan(goal)

    assert plan.steps == ["check metrics", "check logs", "propose a fix"]
    assert plan.reasoning


def test_make_plan_includes_goal_in_system_prompt(fake_llm) -> None:
    fake_llm.queue_json({"steps": ["a"], "reasoning": "r"})
    goal = Goal(objective="find the root cause of X", success_criteria=["cite evidence"])
    planner = Planner(fake_llm)

    planner.make_plan(goal)

    system_sent = fake_llm.calls[0].system
    assert "find the root cause of X" in system_sent
    assert "cite evidence" in system_sent


def test_make_plan_with_context_notes_included_in_user_message(fake_llm) -> None:
    fake_llm.queue_json({"steps": ["a"], "reasoning": "r"})
    goal = Goal(objective="x")
    planner = Planner(fake_llm)

    planner.make_plan(goal, context_notes="Attempt 1 failed because X was missing.")

    user_content = fake_llm.calls[0].messages[0].content
    assert "Attempt 1 failed because X was missing." in user_content
