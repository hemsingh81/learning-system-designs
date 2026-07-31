"""Unit tests for agent/loop.py — the think/act/observe loop, in isolation
from any real skill or tool, using small dummy tools registered directly."""

from __future__ import annotations

from aisets.agent.loop import AgentLoop
from aisets.agent.registry import ToolRegistry
from aisets.agent.tools import tool
from aisets.llm.base import LLMResponse, ToolCall


@tool(permission="read", name="lookup")
def lookup(key: str) -> str:
    """Look up a value by key, for testing."""
    if key == "boom":
        raise RuntimeError("simulated tool failure")
    return f"value-for-{key}"


@tool(permission="write", name="dangerous_action")
def dangerous_action(target: str) -> str:
    """A write tool that should never be reachable from a read-only agent."""
    return f"did something to {target}"


def _build_agent(fake_llm, *, max_steps: int = 5, allow_write: bool = False) -> AgentLoop:
    registry = ToolRegistry().register_all([lookup, dangerous_action])
    return AgentLoop(fake_llm, registry, system_prompt="test system prompt", max_steps=max_steps, allow_write=allow_write)


def test_immediate_final_answer_no_tool_calls(fake_llm) -> None:
    fake_llm.queue_text("The answer is 42.")
    agent = _build_agent(fake_llm)

    result = agent.run("what is the answer?")

    assert result.stopped_reason == "answered"
    assert result.final_answer == "The answer is 42."
    assert len(result.steps) == 1
    assert result.steps[0].action == "final_answer"


def test_one_tool_call_then_final_answer(fake_llm) -> None:
    fake_llm.queue_response(LLMResponse(
        text=None,
        tool_calls=[ToolCall(id="c1", name="lookup", arguments={"key": "alpha"})],
        stop_reason="tool_use",
    ))
    fake_llm.queue_text("Found it: value-for-alpha.")

    agent = _build_agent(fake_llm)
    result = agent.run("look up alpha")

    assert result.stopped_reason == "answered"
    assert result.final_answer == "Found it: value-for-alpha."
    assert len(result.steps) == 2
    assert result.steps[0].action == "tool_call"
    assert result.steps[0].tool_name == "lookup"
    assert "value-for-alpha" in result.steps[0].tool_result


def test_tool_error_is_fed_back_not_raised(fake_llm) -> None:
    fake_llm.queue_response(LLMResponse(
        text=None,
        tool_calls=[ToolCall(id="c1", name="lookup", arguments={"key": "boom"})],
        stop_reason="tool_use",
    ))
    fake_llm.queue_text("That lookup failed, so I can't determine the value.")

    agent = _build_agent(fake_llm)
    result = agent.run("look up boom")

    assert result.stopped_reason == "answered"
    assert "error:" in result.steps[0].tool_result
    # The error text was appended to conversation history and the model
    # still got to answer normally afterward.
    assert result.final_answer == "That lookup failed, so I can't determine the value."


def test_loop_detection_stops_on_repeated_identical_call(fake_llm) -> None:
    same_call = ToolCall(id="c1", name="lookup", arguments={"key": "alpha"})
    fake_llm.queue_response(LLMResponse(text=None, tool_calls=[same_call], stop_reason="tool_use"))
    fake_llm.queue_response(LLMResponse(text=None, tool_calls=[same_call], stop_reason="tool_use"))

    agent = _build_agent(fake_llm, max_steps=5)
    result = agent.run("look up alpha repeatedly")

    assert result.stopped_reason == "loop_detected"
    assert len(result.steps) == 2  # stopped on the SECOND occurrence, not after using the full budget


def test_budget_exhausted_after_max_steps(fake_llm) -> None:
    for i in range(3):
        fake_llm.queue_response(LLMResponse(
            text=None,
            tool_calls=[ToolCall(id=f"c{i}", name="lookup", arguments={"key": f"key{i}"})],
            stop_reason="tool_use",
        ))

    agent = _build_agent(fake_llm, max_steps=3)
    result = agent.run("never-ending investigation")

    assert result.stopped_reason == "budget_exhausted"
    tool_call_steps = [s for s in result.steps if s.action == "tool_call"]
    assert len(tool_call_steps) == 3


def test_write_tool_is_not_offered_when_allow_write_false(fake_llm) -> None:
    fake_llm.queue_text("done")
    agent = _build_agent(fake_llm, allow_write=False)
    agent.run("do something")

    call = fake_llm.calls[0]
    tool_names = {t.name for t in (call.tools or [])}
    assert "dangerous_action" not in tool_names
    assert "lookup" in tool_names


def test_write_tool_is_offered_when_allow_write_true(fake_llm) -> None:
    fake_llm.queue_text("done")
    agent = _build_agent(fake_llm, allow_write=True)
    agent.run("do something")

    call = fake_llm.calls[0]
    tool_names = {t.name for t in (call.tools or [])}
    assert "dangerous_action" in tool_names
