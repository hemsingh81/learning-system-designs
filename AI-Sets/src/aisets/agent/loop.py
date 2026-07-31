"""
`AgentLoop` — the think -> choose a tool -> run it -> observe -> repeat
loop. See docs/diagrams/agent-loop.md for the pseudocode this file
implements almost line for line.

Three safety limits live here, all load-bearing:
  1. `max_steps` — a hard cap on think/act/observe cycles (docs/01-concepts.md's
     "step budget"). Without this, a confused model can call tools forever.
  2. Loop detection — the SAME tool called with the SAME arguments twice
     stops the run immediately. A model re-trying an unhelpful call
     usually won't get a different answer the second time either.
  3. Every tool error is caught and fed back to the model as a normal
     observation (not raised) — the model gets a chance to try something
     else, exactly like a human investigator seeing a command fail and
     trying a different one next.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from aisets.agent.registry import ToolRegistry
from aisets.agent.tools import ToolError, ToolPermissionError
from aisets.llm.base import LLMClient, Message

logger = logging.getLogger(__name__)

StepAction = Literal["tool_call", "final_answer", "loop_detected", "budget_exhausted"]


@dataclass
class AgentStepLog:
    step: int
    action: StepAction
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: str | None = None
    text: str | None = None


@dataclass
class AgentResult:
    final_answer: str
    steps: list[AgentStepLog] = field(default_factory=list)
    stopped_reason: Literal["answered", "loop_detected", "budget_exhausted"] = "answered"


class AgentLoop:
    def __init__(
        self,
        llm: LLMClient,
        registry: ToolRegistry,
        *,
        system_prompt: str,
        max_steps: int = 5,
        allow_write: bool = False,
    ) -> None:
        self.llm = llm
        self.registry = registry
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.allow_write = allow_write

    def run(self, question: str) -> AgentResult:
        history: list[Message] = [Message(role="user", content=question)]
        steps: list[AgentStepLog] = []
        seen_calls: set[tuple[str, str]] = set()
        tool_specs = self.registry.specs(allow_write=self.allow_write)

        for step_index in range(1, self.max_steps + 1):
            response = self.llm.complete(history, system=self.system_prompt, tools=tool_specs)

            if response.is_final_answer:
                steps.append(AgentStepLog(step=step_index, action="final_answer", text=response.text))
                return AgentResult(final_answer=response.text or "", steps=steps, stopped_reason="answered")

            tool_call = response.tool_calls[0]
            call_key = (tool_call.name, json.dumps(tool_call.arguments, sort_keys=True, default=str))

            if call_key in seen_calls:
                msg = (
                    f"I called '{tool_call.name}' with the same arguments again — "
                    "stopping here to avoid an infinite loop."
                )
                logger.warning("agent loop_detected on step %d: %s", step_index, tool_call.name)
                steps.append(AgentStepLog(
                    step=step_index, action="loop_detected",
                    tool_name=tool_call.name, tool_arguments=tool_call.arguments, text=msg,
                ))
                return AgentResult(final_answer=msg, steps=steps, stopped_reason="loop_detected")
            seen_calls.add(call_key)

            try:
                result = self.registry.invoke(tool_call.name, tool_call.arguments, allow_write=self.allow_write)
                result_text = json.dumps(result, default=str)
            except (ToolError, ToolPermissionError) as exc:
                result_text = f"error: {exc}"
                logger.warning("agent tool call failed on step %d: %s", step_index, exc)

            steps.append(AgentStepLog(
                step=step_index, action="tool_call",
                tool_name=tool_call.name, tool_arguments=tool_call.arguments, tool_result=result_text,
            ))

            history.append(Message(role="assistant", content=response.text or "", tool_calls=response.tool_calls))
            history.append(Message(role="tool", content=result_text, tool_call_id=tool_call.id))

        msg = f"I could not finish within my step budget ({self.max_steps} steps) — stopping here."
        logger.warning("agent budget_exhausted after %d steps", self.max_steps)
        steps.append(AgentStepLog(step=self.max_steps, action="budget_exhausted", text=msg))
        return AgentResult(final_answer=msg, steps=steps, stopped_reason="budget_exhausted")
