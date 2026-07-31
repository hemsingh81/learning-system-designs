"""Unit tests for agentic/goal.py — Goal.describe()."""

from __future__ import annotations

from aisets.agentic.goal import Goal


def test_describe_includes_all_sections() -> None:
    goal = Goal(
        objective="find root cause",
        success_criteria=["cite evidence"],
        hard_constraints=["never restart without approval"],
        stop_conditions=["stop once confirmed"],
    )
    text = goal.describe()
    assert "find root cause" in text
    assert "cite evidence" in text
    assert "never restart without approval" in text
    assert "stop once confirmed" in text


def test_describe_omits_empty_sections() -> None:
    goal = Goal(objective="find root cause")
    text = goal.describe()
    assert "Success criteria" not in text
    assert "Hard constraints" not in text
    assert "Stop conditions" not in text
