"""Unit tests for skills/draft_reply.py — including the LOCAL forbidden-
content check that never trusts the model's own self-report."""

from __future__ import annotations

from aisets.skills.draft_reply import DraftReplySkill


def test_happy_path(fake_llm) -> None:
    fake_llm.queue_json({
        "reply_text": "Thanks for reaching out, we're looking into the duplicate charge.",
        "tone": "empathetic",
        "contains_prohibited_content": False,
    })
    skill = DraftReplySkill(fake_llm)

    result = skill.run("I was charged twice.")

    assert result.tone == "empathetic"
    assert result.contains_prohibited_content is False


def test_empty_input_returns_default_without_calling_model(fake_llm) -> None:
    skill = DraftReplySkill(fake_llm)
    result = skill.run("")
    assert result.reply_text
    assert len(fake_llm.calls) == 0


def test_oversized_input_is_truncated(fake_llm) -> None:
    fake_llm.queue_json({"reply_text": "ok", "tone": "empathetic", "contains_prohibited_content": False})
    skill = DraftReplySkill(fake_llm)
    skill.run("w" * 50_000)
    assert len(fake_llm.calls[0].messages[0].content) <= skill.max_input_chars + 100


def test_local_check_overrides_false_negative_from_model(fake_llm) -> None:
    # The model says "false" (no prohibited content) but the reply text it
    # produced actually contains a forbidden guarantee phrase. Our local
    # check must catch this regardless of what the model self-reported.
    fake_llm.queue_json({
        "reply_text": "Don't worry, I guarantee your refund will be processed today.",
        "tone": "empathetic",
        "contains_prohibited_content": False,  # model is WRONG about itself here
    })
    skill = DraftReplySkill(fake_llm)

    result = skill.run("When will my refund happen?")

    assert result.contains_prohibited_content is True


def test_local_check_agrees_when_clean(fake_llm) -> None:
    fake_llm.queue_json({
        "reply_text": "Our team will review this within one business day.",
        "tone": "neutral",
        "contains_prohibited_content": False,
    })
    skill = DraftReplySkill(fake_llm, tone="neutral")

    result = skill.run("Please look into my account issue.")

    assert result.contains_prohibited_content is False


def test_tone_is_configurable(fake_llm) -> None:
    fake_llm.queue_json({"reply_text": "Dear customer, we acknowledge your concern.", "tone": "formal", "contains_prohibited_content": False})
    skill = DraftReplySkill(fake_llm, tone="formal")

    skill.run("A formal complaint.")

    system_prompt_sent = fake_llm.calls[0].system
    assert "formal" in system_prompt_sent
