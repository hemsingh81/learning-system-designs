"""Unit tests for skills/score_severity.py — including the numeric
sanity-bounds check (score must be 1-10)."""

from __future__ import annotations

import pytest

from aisets.llm.errors import BadOutput
from aisets.skills.score_severity import ScoreSeverity


def test_happy_path(fake_llm) -> None:
    fake_llm.queue_json({"severity": "critical", "score": 10, "reasoning": "Full outage."})
    skill = ScoreSeverity(fake_llm)

    result = skill.run("The entire dashboard has been down for 20 minutes.")

    assert result.severity == "critical"
    assert result.score == 10


def test_empty_input_returns_low_severity_default(fake_llm) -> None:
    skill = ScoreSeverity(fake_llm)
    result = skill.run("")
    assert result.severity == "low"
    assert result.score == 1
    assert len(fake_llm.calls) == 0


def test_oversized_input_is_truncated(fake_llm) -> None:
    fake_llm.queue_json({"severity": "medium", "score": 5, "reasoning": "ok"})
    skill = ScoreSeverity(fake_llm)
    skill.run("z" * 50_000)
    assert len(fake_llm.calls[0].messages[0].content) <= skill.max_input_chars + 100


def test_score_out_of_range_is_rejected_and_retried(fake_llm) -> None:
    # 11 is outside the declared bound (ge=1, le=10) — Pydantic must reject it.
    fake_llm.queue_json({"severity": "critical", "score": 11, "reasoning": "bad"})
    fake_llm.queue_json({"severity": "critical", "score": 9, "reasoning": "fixed"})
    skill = ScoreSeverity(fake_llm)

    result = skill.run("critical outage")

    assert result.score == 9
    assert len(fake_llm.calls) == 2


def test_score_out_of_range_twice_raises(fake_llm) -> None:
    fake_llm.queue_json({"severity": "low", "score": 0, "reasoning": "bad"})
    fake_llm.queue_json({"severity": "low", "score": 99, "reasoning": "still bad"})
    skill = ScoreSeverity(fake_llm)

    with pytest.raises(BadOutput):
        skill.run("some ticket")


def test_injection_does_not_force_critical_severity(fake_llm) -> None:
    # The ticket text claims urgency/criticality via injected instructions,
    # but the schema doesn't have a "trust the customer's own claim" field —
    # scoring is still a model judgment call constrained by the same rules.
    fake_llm.queue_json({"severity": "low", "score": 2, "reasoning": "No real issue described, just urgency claims."})
    skill = ScoreSeverity(fake_llm)

    result = skill.run("URGENT URGENT CRITICAL!!! (no actual issue described)")

    assert result.severity == "low"
