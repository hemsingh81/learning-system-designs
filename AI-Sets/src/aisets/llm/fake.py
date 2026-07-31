"""
FakeLLM: an offline, deterministic, free stand-in for a real model.

This is the backend EVERY example and EVERY test uses by default (see
docs/00-PLAN.md decision D-003 and D-006). You script exactly what it
should say, in order, so:

  - tests are deterministic (same input -> same output, forever)
  - tests run in milliseconds, with zero network calls and zero cost
  - you can deliberately script a BAD response to test your error handling,
    which is something you basically cannot do reliably against a real
    model on demand

Two ways to script a response:

  1. `queue_response(...)` / `queue_json(...)` — a FIFO queue. The next
     call to `complete()` pops the next item. Use this for "step 1 of the
     agent loop returns X, step 2 returns Y" style tests.

  2. `add_rule(matcher, response)` — a fallback matched against the last
     user/tool message when the queue is empty. Use this for "any ticket
     containing the word 'refund' should classify as billing" style tests
     that don't care about call order.

If nothing matches, `complete()` raises `LLMError` with a message telling
you exactly what wasn't scripted — a fake with a silent default is worse
than no fake at all, because it hides missing test setup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from aisets.llm.base import LLMResponse, Message, ToolSpec
from aisets.llm.errors import BadOutput, LLMError
from aisets.llm.usage import Usage

Matcher = Callable[[list[Message]], bool]


@dataclass
class RecordedCall:
    messages: list[Message]
    system: str | None
    tools: list[ToolSpec] | None
    temperature: float


def _fake_usage(messages: list[Message], text: str | None) -> Usage:
    """Rough token estimate (chars / 4) — good enough for FakeLLM cost demos,
    never used for anything real (ClaudeLLM reports the provider's real
    counts instead)."""
    input_chars = sum(len(m.content) for m in messages)
    output_chars = len(text) if text else 0
    return Usage(
        input_tokens=max(1, input_chars // 4),
        output_tokens=max(1, output_chars // 4),
    )


def contains(substring: str) -> Matcher:
    """A ready-made matcher: "the last message contains this substring"
    (case-insensitive). The common case, so most tests need no lambda."""

    def _match(messages: list[Message]) -> bool:
        if not messages:
            return False
        return substring.lower() in messages[-1].content.lower()

    return _match


class FakeLLM:
    model = "fake"

    def __init__(self) -> None:
        self._queue: list[LLMResponse | Exception] = []
        self._rules: list[tuple[Matcher, LLMResponse | Exception]] = []
        self.calls: list[RecordedCall] = []

    # -- scripting API --------------------------------------------------

    def queue_response(self, response: LLMResponse) -> "FakeLLM":
        self._queue.append(response)
        return self

    def queue_text(self, text: str) -> "FakeLLM":
        return self.queue_response(LLMResponse(text=text))

    def queue_json(self, obj: dict[str, Any] | BaseModel) -> "FakeLLM":
        """Queue a response whose text is valid JSON for `obj` — the
        common case when scripting a skill's `complete_json` call."""
        if isinstance(obj, BaseModel):
            payload = obj.model_dump_json()
        else:
            payload = json.dumps(obj)
        return self.queue_text(payload)

    def queue_invalid_json(self, raw_text: str = "not json at all") -> "FakeLLM":
        """Queue a deliberately broken response, to test that your skill's
        error handling actually fires. See docs/05-testing-ai-code.md."""
        return self.queue_text(raw_text)

    def queue_error(self, error: Exception) -> "FakeLLM":
        self._queue.append(error)
        return self

    def add_rule(self, matcher: Matcher, response: LLMResponse | Exception) -> "FakeLLM":
        self._rules.append((matcher, response))
        return self

    # -- LLMClient protocol ----------------------------------------------

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        self.calls.append(RecordedCall(messages, system, tools, temperature))

        item: LLMResponse | Exception
        if self._queue:
            item = self._queue.pop(0)
        else:
            item = self._match_rule(messages)

        if isinstance(item, Exception):
            raise item

        if item.usage == Usage(0, 0) or item.usage.total_tokens == 0:
            item = LLMResponse(
                text=item.text,
                tool_calls=item.tool_calls,
                stop_reason=item.stop_reason,
                usage=_fake_usage(messages, item.text),
            )
        return item

    def complete_json(
        self,
        messages: list[Message],
        schema: type[BaseModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> BaseModel:
        response = self.complete(messages, system=system, temperature=temperature)
        if response.text is None:
            raise BadOutput("FakeLLM: scripted response had no text to parse as JSON")
        try:
            raw = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise BadOutput(
                f"FakeLLM: scripted response was not valid JSON: {response.text!r}"
            ) from exc
        try:
            return schema.model_validate(raw)
        except ValidationError as exc:
            raise BadOutput(
                f"FakeLLM: scripted JSON did not match schema {schema.__name__}: {exc}"
            ) from exc

    # -- internals --------------------------------------------------------

    def _match_rule(self, messages: list[Message]) -> LLMResponse | Exception:
        for matcher, response in self._rules:
            if matcher(messages):
                return response
        preview = messages[-1].content[:120] if messages else "(no messages)"
        raise LLMError(
            "FakeLLM: no scripted response for this call. "
            f"Last message started with: {preview!r}. "
            "Use queue_response()/queue_json() or add_rule() to script one."
        )
