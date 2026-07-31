"""Unit tests for agentic/critic.py."""

from __future__ import annotations

from aisets.agentic.critic import Critic
from aisets.agentic.goal import Goal


def test_critic_accepts_a_good_answer(fake_llm) -> None:
    fake_llm.queue_json({"goal_met": True, "reasoning": "meets all criteria", "missing": []})
    goal = Goal(objective="x", success_criteria=["cite evidence"])
    critic = Critic(fake_llm)

    verdict = critic.check(goal, "Here is the answer with evidence: log line X.")

    assert verdict.goal_met is True
    assert verdict.missing == []


def test_critic_rejects_and_lists_whats_missing(fake_llm) -> None:
    fake_llm.queue_json({
        "goal_met": False,
        "reasoning": "no evidence cited",
        "missing": ["a cited log line or metric"],
    })
    goal = Goal(objective="x", success_criteria=["cite evidence"])
    critic = Critic(fake_llm)

    verdict = critic.check(goal, "It probably failed for some reason.")

    assert verdict.goal_met is False
    assert "a cited log line or metric" in verdict.missing


def test_critic_includes_evidence_notes_in_prompt(fake_llm) -> None:
    fake_llm.queue_json({"goal_met": True, "reasoning": "ok", "missing": []})
    goal = Goal(objective="x")
    critic = Critic(fake_llm)

    critic.check(goal, "answer", evidence_notes="log line: ERROR payments timeout")

    sent_content = fake_llm.calls[0].messages[0].content
    assert "ERROR payments timeout" in sent_content
