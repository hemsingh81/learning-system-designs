"""Unit tests for agentic/orchestrator.py — Specialist/Supervisor,
including the failure-handling paths: a specialist that raises, a
specialist that "stalls" (SpecialistTimeout), and all-specialists-failed."""

from __future__ import annotations

from aisets.agentic.orchestrator import Specialist, SpecialistTimeout, Supervisor


def test_all_specialists_succeed_and_get_synthesized(fake_llm) -> None:
    fake_llm.queue_json({"summary": "Combined finding: X caused Y.", "contradictions": []})

    investigator = Specialist("investigator", lambda task: "Found evidence of X.")
    fixer = Specialist("fixer", lambda task: "Recommend fix Y.")
    supervisor = Supervisor(fake_llm, [investigator, fixer])

    result = supervisor.run("investigate the incident")

    assert result.final_answer == "Combined finding: X caused Y."
    assert result.synthesis_skipped is False
    assert all(r.succeeded for r in result.specialist_results)


def test_one_specialist_fails_others_still_synthesized(fake_llm) -> None:
    fake_llm.queue_json({"summary": "Based on the investigator alone: X.", "contradictions": []})

    def broken_fixer(task: str) -> str:
        raise RuntimeError("fixer crashed")

    investigator = Specialist("investigator", lambda task: "Found evidence of X.")
    fixer = Specialist("fixer", broken_fixer)
    supervisor = Supervisor(fake_llm, [investigator, fixer])

    result = supervisor.run("investigate")

    assert result.synthesis_skipped is False
    assert result.final_answer == "Based on the investigator alone: X."
    failed = [r for r in result.specialist_results if not r.succeeded]
    assert len(failed) == 1
    assert failed[0].name == "fixer"
    assert "fixer crashed" in failed[0].error

    # The failure notice must have reached the synthesis prompt.
    sent_content = fake_llm.calls[0].messages[0].content
    assert "fixer crashed" in sent_content


def test_specialist_that_stalls_is_treated_as_a_failure(fake_llm) -> None:
    fake_llm.queue_json({"summary": "Only the communicator responded.", "contradictions": []})

    def stalling_specialist(task: str) -> str:
        raise SpecialistTimeout("specialist did not respond in time")

    investigator = Specialist("investigator", stalling_specialist)
    communicator = Specialist("communicator", lambda task: "Here is a draft update.")
    supervisor = Supervisor(fake_llm, [investigator, communicator])

    result = supervisor.run("investigate and communicate")

    failed = [r for r in result.specialist_results if not r.succeeded]
    assert len(failed) == 1
    assert "did not respond in time" in failed[0].error


def test_all_specialists_fail_skips_synthesis_entirely(fake_llm) -> None:
    def broken(task: str) -> str:
        raise RuntimeError("broken")

    supervisor = Supervisor(fake_llm, [Specialist("a", broken), Specialist("b", broken)])
    result = supervisor.run("task")

    assert result.synthesis_skipped is True
    assert "All specialists failed" in result.final_answer
    assert len(fake_llm.calls) == 0  # never even attempted a synthesis call


def test_contradictions_are_surfaced_not_silently_resolved(fake_llm) -> None:
    fake_llm.queue_json({
        "summary": "Specialists disagree on the root cause.",
        "contradictions": ["Investigator says gateway timeout; fixer assumed a config error."],
    })

    a = Specialist("investigator", lambda task: "Root cause: gateway timeout.")
    b = Specialist("fixer", lambda task: "Root cause: a bad config change.")
    supervisor = Supervisor(fake_llm, [a, b])

    result = supervisor.run("investigate")

    assert len(result.contradictions) == 1
    assert "gateway timeout" in result.contradictions[0]
