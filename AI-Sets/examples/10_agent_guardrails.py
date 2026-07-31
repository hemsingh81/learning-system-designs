"""
Example 10 — the two safety limits an agent MUST have: loop detection
and a step budget. Without these, a confused model can call tools forever,
burning time and money for no result.

Run:
    .\\scripts\\run-example.ps1 10_agent_guardrails
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.agent.simple_agent import build_simple_agent
from aisets.llm.base import LLMResponse, ToolCall


def demo_loop_detection(settings, llm) -> None:
    console.rule("1. Loop detection: the same tool call twice in a row stops the run")
    if is_fake(llm):
        same_call = ToolCall(id="call_1", name="query_orders", arguments={"order_id": "9002"})
        # Queue the SAME call twice — the agent must stop on the second one.
        llm.queue_response(LLMResponse(text=None, tool_calls=[same_call], stop_reason="tool_use"))
        llm.queue_response(LLMResponse(text=None, tool_calls=[same_call], stop_reason="tool_use"))

    agent = build_simple_agent(llm, settings)
    result = agent.run("Why did order 9002 fail?")

    console.print(f"Stopped because: [bold]{result.stopped_reason}[/bold] after {len(result.steps)} step(s)")
    console.print(f"Final message: {result.final_answer}")


def demo_budget_exhausted(settings, llm) -> None:
    console.rule(f"2. Step budget: stops after max_steps ({settings.max_agent_steps}) with no answer")
    if is_fake(llm):
        # A confused model keeps calling a DIFFERENT order_id every time,
        # never repeating (so loop detection never fires) and never
        # answering — this should burn through the entire step budget.
        for i in range(settings.max_agent_steps):
            llm.queue_response(LLMResponse(
                text=None,
                tool_calls=[ToolCall(id=f"call_{i}", name="query_orders", arguments={"order_id": str(9000 + i)})],
                stop_reason="tool_use",
            ))

    agent = build_simple_agent(llm, settings)
    result = agent.run("Investigate all recent payment failures exhaustively.")

    console.print(f"Stopped because: [bold]{result.stopped_reason}[/bold] after {len(result.steps)} step(s)")
    console.print(f"Final message: {result.final_answer}")
    tool_call_steps = [s for s in result.steps if s.action == "tool_call"]
    console.print(f"Tool calls made before stopping: {len(tool_call_steps)} (== max_steps, none wasted on a repeat)")


def main() -> None:
    settings, llm = setup()
    demo_loop_detection(settings, llm)
    demo_budget_exhausted(settings, llm)


if __name__ == "__main__":
    main()
