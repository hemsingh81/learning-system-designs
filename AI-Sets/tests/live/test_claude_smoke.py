"""
Live smoke tests — these hit the REAL Anthropic API and cost real (tiny)
money. They are excluded by default (see pyproject.toml `addopts`).

Run them deliberately with:
    .\\scripts\\test.ps1 -Live

They need ANTHROPIC_API_KEY set in .env. If it's missing, they are skipped
with a clear reason rather than failing, so CI without a key stays green.

Assertions here are deliberately LOOSE (non-empty text, valid JSON shape) —
never assert exact model wording, because that will change between model
versions and turn this into a flaky test for no real benefit.
"""

from __future__ import annotations

import os

import pytest
from pydantic import BaseModel

from aisets.llm.base import Message
from aisets.llm.claude import ClaudeLLM

pytestmark = pytest.mark.live


def _make_client() -> ClaudeLLM:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set — skipping live test.")
    model = os.environ.get("CLAUDE_MODEL", "claude-3-5-haiku-latest")
    return ClaudeLLM(model=model, api_key=api_key)


class Greeting(BaseModel):
    language: str
    greeting: str


def test_complete_returns_nonempty_text() -> None:
    client = _make_client()
    response = client.complete(
        [Message(role="user", content="Say hello in one short sentence.")]
    )
    assert response.is_final_answer
    assert response.text
    assert len(response.text.strip()) > 0
    assert response.usage.total_tokens > 0


def test_complete_json_returns_valid_schema() -> None:
    client = _make_client()
    result = client.complete_json(
        [Message(role="user", content="Give me a greeting in French.")],
        Greeting,
    )
    assert isinstance(result, Greeting)
    assert result.language
    assert result.greeting
