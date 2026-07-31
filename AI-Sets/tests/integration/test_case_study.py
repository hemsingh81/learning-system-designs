"""
Integration test for the Milestone 8 capstone: incident triage across all
three data variants (easy, ambiguous, trap). Imports the exact same
`run_incident_triage` function that examples/15_case_study_incident_triage.py
runs interactively, scripted with the SAME FakeLLM sequences, so this test
proves the actual case-study code path, not a re-implementation of it.

The one property this test file exists to GUARANTEE: the "trap" variant
(genuinely contradictory evidence) must never take an action and must
always escalate — this is the safety property the whole case study is
built to demonstrate.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


@pytest.fixture(scope="module")
def case_study_module():
    sys.path.insert(0, str(EXAMPLES_DIR))
    try:
        yield importlib.import_module("15_case_study_incident_triage")
    finally:
        sys.path.remove(str(EXAMPLES_DIR))


@pytest.fixture
def settings(tmp_path, monkeypatch):
    from aisets.config import load_settings

    monkeypatch.setenv("DATA_DIR", "data")  # use the real seeded case_study data
    return load_settings()


def test_easy_variant_succeeds_on_first_attempt_and_action_is_approved(case_study_module, fake_llm, settings) -> None:
    case_study_module._script_easy(fake_llm)

    result = case_study_module.run_incident_triage(
        fake_llm, settings, "easy", human_approve=lambda req: True
    )

    assert result.attempts == 1
    assert result.critic_met is True
    assert result.escalated is False
    assert result.action_approved is True
    assert "payment-gateway timeout" in result.answer or "payment_gateway" in result.answer.lower() or "gateway" in result.answer.lower()


def test_ambiguous_variant_rejects_first_attempt_then_succeeds_on_second(case_study_module, fake_llm, settings) -> None:
    case_study_module._script_ambiguous(fake_llm)

    result = case_study_module.run_incident_triage(
        fake_llm, settings, "ambiguous", human_approve=lambda req: True
    )

    assert result.attempts == 2  # proves the re-plan actually happened
    assert result.critic_met is True
    assert result.escalated is False
    assert "connection pool" in result.answer.lower()


def test_ambiguous_variant_human_can_decline_even_after_root_cause_is_confirmed(case_study_module, fake_llm, settings) -> None:
    case_study_module._script_ambiguous(fake_llm)

    result = case_study_module.run_incident_triage(
        fake_llm, settings, "ambiguous", human_approve=lambda req: False
    )

    assert result.critic_met is True  # root cause WAS confirmed...
    assert result.action_approved is False  # ...but the human still gets the final say


def test_trap_variant_escalates_and_never_auto_approves_a_fix(case_study_module, fake_llm, settings) -> None:
    case_study_module._script_trap(fake_llm)

    result = case_study_module.run_incident_triage(
        fake_llm, settings, "trap", human_approve=lambda req: False
    )

    # The system never reaches a confirmed root cause, so it must escalate
    # rather than propose or auto-execute any fix.
    assert result.attempts == 2  # exhausted both attempts
    assert result.critic_met is False
    assert result.escalated is True
    assert result.action_approved is False
    assert "insufficient" in result.final_message.lower() or "contradictory" in result.final_message.lower()


def test_trap_variant_never_auto_approves_even_if_a_human_would_say_yes(case_study_module, fake_llm, settings) -> None:
    # This is the key safety property: NOTHING about the escalation path
    # is allowed to short-circuit to "auto" just because risk/confidence
    # inputs happen to look permissive — a human decision is always
    # actually consulted (decided_by == "human"), never skipped.
    case_study_module._script_trap(fake_llm)

    result = case_study_module.run_incident_triage(
        fake_llm, settings, "trap", human_approve=lambda req: True
    )

    assert len(result.approval_records) == 1
    record = result.approval_records[0]
    assert record.request.risk_level == "high"
    assert record.decided_by == "human"  # never "auto" — a human was genuinely consulted
    assert record.approved is True  # reflects the human's actual answer, not a hardcoded denial
