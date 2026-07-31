"""
The one interface every LLM backend implements: `LLMClient`.

This is the seam of the whole project. Every skill, workflow step, and
agent talks to `LLMClient`, never to `FakeLLM` or `ClaudeLLM` directly by
name. That is exactly the "program to an interface, not an implementation"
rule you already use for a `IPaymentGateway` or `IEmailSender` in normal
backend code — and it is what lets every example run against `FakeLLM` in
tests and `ClaudeLLM` in real life with NO code changes, only a config flip
(`LLM_BACKEND`, see src/aisets/config.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TypeVar

from pydantic import BaseModel

from aisets.llm.usage import Usage, ZERO_USAGE

Role = Literal["system", "user", "assistant", "tool"]

TModel = TypeVar("TModel", bound=BaseModel)


@dataclass(frozen=True)
class Message:
    """One turn in a conversation.

    `tool_call_id`/`name` are only used when `role == "tool"` (a tool's
    result being reported back to the model).

    `tool_calls` is only used when `role == "assistant"` AND that turn was
    the model asking to call tools rather than answering directly — the
    agent loop (Milestone 5) stores this so the full conversation, tool
    calls included, can be replayed back to the model on the next turn.
    """

    role: Role
    content: str
    tool_call_id: str | None = None
    name: str | None = None
    tool_calls: list["ToolCall"] | None = None


@dataclass(frozen=True)
class ToolSpec:
    """Describes one tool the model is allowed to call. `parameters` is a
    JSON Schema object (see agent/tools.py for how we generate this from a
    plain Python function's type hints + docstring in Milestone 4)."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """One tool invocation the model asked for."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    """What every `complete()` call returns, regardless of backend.

    Exactly one of `text` or `tool_calls` is meaningful at a time:
      - `stop_reason == "end_turn"` -> read `text`, this is the final answer.
      - `stop_reason == "tool_use"` -> read `tool_calls`, run them, and send
        the results back as new `Message(role="tool", ...)` entries.
    """

    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: Literal["end_turn", "tool_use", "max_tokens"] = "end_turn"
    usage: Usage = ZERO_USAGE

    @property
    def is_final_answer(self) -> bool:
        return self.stop_reason != "tool_use"


class LLMClient(Protocol):
    """Every backend (FakeLLM, ClaudeLLM) implements this shape."""

    model: str

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Free-form text or tool-call completion."""
        ...

    def complete_json(
        self,
        messages: list[Message],
        schema: type[TModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> TModel:
        """Ask for output matching a Pydantic model, and return a validated
        instance of it. Raises `aisets.llm.errors.BadOutput` if the model's
        output cannot be validated against `schema`, even after one retry.
        """
        ...
