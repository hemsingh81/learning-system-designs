"""
`Skill` — the base class every Level-1 skill in this project extends.

A skill is: validate input -> build a prompt -> ask the model for
STRUCTURED output -> (if the model got the shape wrong) retry once ->
return a typed, validated object. Nothing more. No memory of previous
calls, no decision about what happens next — that's what a Workflow
(Milestone 3) or an Agent (Milestone 5) adds on top.

Why "retry once on bad output" is baked in here (see docs/00-PLAN.md,
and DECISIONS.md in tutorial/01-skills/):
    Models occasionally produce output that doesn't match the schema —
    a missing field, a value outside the allowed set. A SINGLE retry
    with an explicit "you got the shape wrong, try again" nudge fixes
    most of these cheaply. If the second attempt also fails, we raise
    `BadOutput` rather than retrying forever — see docs/00-PLAN.md D-006
    and the workflow-level retry policy (Milestone 3) for the difference
    between "retry within a skill" and "retry a whole pipeline step".
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from aisets.llm.base import LLMClient, Message
from aisets.llm.errors import BadOutput

TOutput = TypeVar("TOutput", bound=BaseModel)

_RETRY_NUDGE = (
    "Your previous answer did not match the required schema exactly. "
    "Call the tool again, following the schema exactly this time."
)


class Skill(ABC, Generic[TOutput]):
    name: str
    output_schema: type[TOutput]
    max_input_chars: int = 20_000

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, text: str) -> TOutput:
        """The one public method every skill exposes. Handles empty input,
        oversized input, and the single retry-on-bad-output — subclasses
        only implement `build_messages`, `system_prompt`, and (optionally)
        `empty_input_result`."""
        if not text or not text.strip():
            return self.empty_input_result()

        clean_text = self._truncate_if_needed(text)
        messages = self.build_messages(clean_text)
        system = self.system_prompt()

        try:
            return self.llm.complete_json(messages, self.output_schema, system=system)
        except BadOutput:
            retry_messages = messages + [Message(role="user", content=_RETRY_NUDGE)]
            try:
                return self.llm.complete_json(retry_messages, self.output_schema, system=system)
            except BadOutput as exc:
                raise BadOutput(
                    f"{self.name}: model output did not match {self.output_schema.__name__} "
                    f"even after one retry: {exc}"
                ) from exc

    # -- subclasses implement these ----------------------------------------

    @abstractmethod
    def system_prompt(self) -> str:
        """The fixed system instructions for this skill (role, rules,
        escape hatches — see docs/04-prompting-guide.md)."""

    @abstractmethod
    def build_messages(self, text: str) -> list[Message]:
        """Turn the (already validated/truncated) input text into the
        message list sent to the model."""

    def empty_input_result(self) -> TOutput:
        """Called instead of the model when input is empty/whitespace-only
        — we already KNOW the answer in that case, so don't spend a model
        call on it. Override in subclasses that have a sensible default;
        the base implementation refuses, because guessing a wrong default
        silently is worse than failing loudly."""
        raise ValueError(
            f"{self.name}: input text is empty and this skill has no default "
            "for empty input — override empty_input_result() if one makes sense."
        )

    # -- internals ----------------------------------------------------------

    def _truncate_if_needed(self, text: str) -> str:
        if len(text) <= self.max_input_chars:
            return text
        return text[: self.max_input_chars] + "\n...[truncated, input exceeded max_input_chars]"
