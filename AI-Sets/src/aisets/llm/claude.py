"""
ClaudeLLM: the real backend, talking to the Anthropic API.

This file is the ONLY place in the whole project that imports the
`anthropic` package or knows about Anthropic's wire format. Everything
else — skills, workflows, the agent loop — only ever sees the generic
`LLMClient` shape from `base.py`. That is deliberate: if you ever wanted
to add a second real provider, this is the only file's shape you'd need
to copy, and nothing else in the codebase would need to change.

Retry policy: rate limits and timeouts are retried with exponential
backoff (1s, 2s, 4s), because they are usually transient. A bad-request
error (e.g. a malformed schema) is NOT retried, because retrying an
error that will always happen just wastes time and money.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ValidationError

from aisets.llm.base import LLMResponse, Message, ToolCall, ToolSpec
from aisets.llm.errors import BadOutput, LLMError, RateLimited, Refused, Timeout
from aisets.llm.usage import Usage

_MAX_RETRIES = 3
_BACKOFF_SECONDS = (1, 2, 4)
_DEFAULT_MAX_TOKENS = 1024
_STRUCTURED_OUTPUT_TOOL_NAME = "emit_result"


def _require_anthropic():
    try:
        import anthropic  # noqa: F401
    except ImportError as exc:  # pragma: no cover - anthropic is a hard dependency
        raise LLMError(
            "The 'anthropic' package is not installed. Run "
            "'pip install -e .[dev]' (see docs/02-setup-windows.md), "
            "or set LLM_BACKEND=fake in .env to skip real API calls entirely."
        ) from exc
    return anthropic


def _to_anthropic_messages(messages: list[Message]) -> list[dict[str, Any]]:
    """Convert our generic Message list into Anthropic's wire format.
    System messages are NOT included here — Anthropic takes `system` as
    its own top-level parameter, so the caller pulls those out separately.
    """
    out: list[dict[str, Any]] = []
    for m in messages:
        if m.role == "system":
            continue
        if m.role == "tool":
            out.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.tool_call_id,
                    "content": m.content,
                }],
            })
        elif m.role == "assistant" and m.tool_calls:
            content: list[dict[str, Any]] = []
            if m.content:
                content.append({"type": "text", "text": m.content})
            for tc in m.tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            out.append({"role": "assistant", "content": content})
        else:
            out.append({"role": m.role, "content": m.content})
    return out


def _merge_system(messages: list[Message], system: str | None) -> str | None:
    parts = [m.content for m in messages if m.role == "system"]
    if system:
        parts.append(system)
    return "\n\n".join(parts) if parts else None


class ClaudeLLM:
    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        anthropic = _require_anthropic()
        self._client = anthropic.Anthropic(api_key=api_key)
        self._anthropic = anthropic

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        anthropic_messages = _to_anthropic_messages(messages)
        merged_system = _merge_system(messages, system)
        anthropic_tools = (
            [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools]
            if tools
            else None
        )

        raw = self._call_with_retry(
            messages=anthropic_messages,
            system=merged_system,
            tools=anthropic_tools,
            temperature=temperature,
        )
        return self._to_llm_response(raw)

    def complete_json(
        self,
        messages: list[Message],
        schema: type[BaseModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> BaseModel:
        """Force structured output by giving the model exactly ONE tool
        (matching `schema`'s JSON Schema) and requiring it to call that
        tool. This is more reliable than asking nicely for JSON in prose,
        because the API-level tool-calling machinery guarantees valid JSON
        syntax — we still validate it against the Pydantic schema ourselves,
        because "valid JSON" and "the RIGHT JSON" are different guarantees.
        """
        tool = ToolSpec(
            name=_STRUCTURED_OUTPUT_TOOL_NAME,
            description=f"Return the result as {schema.__name__}.",
            parameters=schema.model_json_schema(),
        )
        anthropic_messages = _to_anthropic_messages(messages)
        merged_system = _merge_system(messages, system)

        raw = self._call_with_retry(
            messages=anthropic_messages,
            system=merged_system,
            tools=[{"name": tool.name, "description": tool.description, "input_schema": tool.parameters}],
            tool_choice={"type": "tool", "name": _STRUCTURED_OUTPUT_TOOL_NAME},
            temperature=temperature,
        )
        response = self._to_llm_response(raw)
        if not response.tool_calls:
            raise BadOutput(
                f"ClaudeLLM: expected a '{_STRUCTURED_OUTPUT_TOOL_NAME}' tool call but got none. "
                f"stop_reason={response.stop_reason}"
            )
        arguments = response.tool_calls[0].arguments
        try:
            return schema.model_validate(arguments)
        except ValidationError as exc:
            raise BadOutput(
                f"ClaudeLLM: model's structured output did not match {schema.__name__}: {exc}"
            ) from exc

    # -- internals ---------------------------------------------------------

    def _call_with_retry(self, **kwargs: Any):
        anthropic = self._anthropic
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                return self._client.messages.create(
                    model=self.model,
                    max_tokens=_DEFAULT_MAX_TOKENS,
                    **kwargs,
                )
            except anthropic.RateLimitError as exc:
                last_exc = RateLimited(str(exc))
            except anthropic.APITimeoutError as exc:
                last_exc = Timeout(str(exc))
            except anthropic.APIStatusError as exc:
                # Not retryable (bad request, auth failure, etc.) — fail fast.
                raise LLMError(f"ClaudeLLM: API error {exc.status_code}: {exc}") from exc

            if attempt < _MAX_RETRIES - 1:
                time.sleep(_BACKOFF_SECONDS[attempt])
        assert last_exc is not None
        raise last_exc

    def _to_llm_response(self, raw: Any) -> LLMResponse:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in raw.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input))

        stop_reason = "tool_use" if raw.stop_reason == "tool_use" else (
            "max_tokens" if raw.stop_reason == "max_tokens" else "end_turn"
        )
        if raw.stop_reason == "refusal":
            raise Refused("ClaudeLLM: the model refused to answer this request.")

        return LLMResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            stop_reason=stop_reason,  # type: ignore[arg-type]
            usage=Usage(
                input_tokens=raw.usage.input_tokens,
                output_tokens=raw.usage.output_tokens,
            ),
        )
