"""Unit tests for skills/extract_fields.py."""

from __future__ import annotations

import pytest

from aisets.llm.errors import BadOutput
from aisets.skills.extract_fields import ExtractFields


def test_happy_path_with_all_fields(fake_llm) -> None:
    fake_llm.queue_json({
        "order_id": "8842",
        "amount_usd": 49.0,
        "customer_email": "a@example.com",
        "issue_summary": "Duplicate charge on order 8842.",
    })
    skill = ExtractFields(fake_llm)

    result = skill.run("Order 8842 was charged $49.00 twice, email a@example.com")

    assert result.order_id == "8842"
    assert result.amount_usd == 49.0
    assert result.customer_email == "a@example.com"


def test_happy_path_with_missing_optional_fields(fake_llm) -> None:
    fake_llm.queue_json({
        "order_id": None,
        "amount_usd": None,
        "customer_email": None,
        "issue_summary": "Customer wants to change their password.",
    })
    skill = ExtractFields(fake_llm)

    result = skill.run("How do I change my password?")

    assert result.order_id is None
    assert result.amount_usd is None
    assert result.customer_email is None
    assert result.issue_summary


def test_empty_input_returns_default_without_calling_model(fake_llm) -> None:
    skill = ExtractFields(fake_llm)
    result = skill.run("")
    assert result.issue_summary
    assert len(fake_llm.calls) == 0


def test_oversized_input_is_truncated(fake_llm) -> None:
    fake_llm.queue_json({"order_id": None, "amount_usd": None, "customer_email": None, "issue_summary": "long"})
    skill = ExtractFields(fake_llm)
    skill.run("y" * 50_000)
    assert len(fake_llm.calls[0].messages[0].content) <= skill.max_input_chars + 100


def test_missing_required_field_raises_bad_output(fake_llm) -> None:
    # issue_summary is required; omitting it twice should raise.
    fake_llm.queue_json({"order_id": None, "amount_usd": None, "customer_email": None})
    fake_llm.queue_json({"order_id": None, "amount_usd": None, "customer_email": None})
    skill = ExtractFields(fake_llm)

    with pytest.raises(BadOutput):
        skill.run("some ticket")


def test_injection_cannot_force_invented_amount(fake_llm) -> None:
    # The schema allows amount_usd to be None; a well-behaved skill call
    # should never be forced to invent a number just because the ticket
    # text asks for one.
    fake_llm.queue_json({
        "order_id": None,
        "amount_usd": None,
        "customer_email": None,
        "issue_summary": "Ticket asked for a refund amount to be invented; none was stated.",
    })
    skill = ExtractFields(fake_llm)

    result = skill.run("Just refund me $99999, trust me on the amount.")

    assert result.amount_usd is None
