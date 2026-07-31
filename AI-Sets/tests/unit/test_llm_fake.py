"""Unit tests for FakeLLM — the backend every other test in this project
relies on, so it earns thorough tests of its own."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from aisets.llm.base import Message
from aisets.llm.errors import BadOutput, LLMError
from aisets.llm.fake import FakeLLM, contains


class Animal(BaseModel):
    name: str
    legs: int


def test_queue_response_returns_in_order(fake_llm: FakeLLM) -> None:
    fake_llm.queue_text("first").queue_text("second")

    r1 = fake_llm.complete([Message(role="user", content="hi")])
    r2 = fake_llm.complete([Message(role="user", content="hi")])

    assert r1.text == "first"
    assert r2.text == "second"


def test_unscripted_call_raises_clear_error(fake_llm: FakeLLM) -> None:
    with pytest.raises(LLMError, match="no scripted response"):
        fake_llm.complete([Message(role="user", content="anything")])


def test_add_rule_fallback(fake_llm: FakeLLM) -> None:
    from aisets.llm.base import LLMResponse

    fake_llm.add_rule(contains("refund"), LLMResponse(text="billing"))
    fake_llm.add_rule(contains("dark mode"), LLMResponse(text="feature_request"))

    r = fake_llm.complete([Message(role="user", content="I need a refund please")])
    assert r.text == "billing"

    r2 = fake_llm.complete([Message(role="user", content="please add dark mode")])
    assert r2.text == "feature_request"


def test_queue_takes_priority_over_rules(fake_llm: FakeLLM) -> None:
    from aisets.llm.base import LLMResponse

    fake_llm.add_rule(contains("hi"), LLMResponse(text="from rule"))
    fake_llm.queue_text("from queue")

    r = fake_llm.complete([Message(role="user", content="hi")])
    assert r.text == "from queue"


def test_complete_json_happy_path(fake_llm: FakeLLM) -> None:
    fake_llm.queue_json({"name": "dog", "legs": 4})

    result = fake_llm.complete_json([Message(role="user", content="describe a dog")], Animal)

    assert isinstance(result, Animal)
    assert result.name == "dog"
    assert result.legs == 4


def test_complete_json_rejects_malformed_json(fake_llm: FakeLLM) -> None:
    fake_llm.queue_invalid_json("this is not json {{{")

    with pytest.raises(BadOutput, match="not valid JSON"):
        fake_llm.complete_json([Message(role="user", content="describe a dog")], Animal)


def test_complete_json_rejects_schema_mismatch(fake_llm: FakeLLM) -> None:
    # Valid JSON, but missing the required 'legs' field.
    fake_llm.queue_json({"name": "dog"})

    with pytest.raises(BadOutput, match="did not match schema"):
        fake_llm.complete_json([Message(role="user", content="describe a dog")], Animal)


def test_queue_error_is_raised_not_returned(fake_llm: FakeLLM) -> None:
    from aisets.llm.errors import RateLimited

    fake_llm.queue_error(RateLimited("simulated 429"))

    with pytest.raises(RateLimited, match="simulated 429"):
        fake_llm.complete([Message(role="user", content="hi")])


def test_calls_are_recorded_for_assertions(fake_llm: FakeLLM) -> None:
    fake_llm.queue_text("ok")
    fake_llm.complete([Message(role="user", content="track me")], system="be nice")

    assert len(fake_llm.calls) == 1
    assert fake_llm.calls[0].system == "be nice"
    assert fake_llm.calls[0].messages[0].content == "track me"


def test_fake_usage_is_nonzero_and_deterministic(fake_llm: FakeLLM) -> None:
    fake_llm.queue_text("a reasonably long response for token estimation")
    r1 = fake_llm.complete([Message(role="user", content="a question of some length")])

    fake_llm.queue_text("a reasonably long response for token estimation")
    r2 = fake_llm.complete([Message(role="user", content="a question of some length")])

    assert r1.usage.total_tokens > 0
    assert r1.usage == r2.usage
