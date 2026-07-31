"""
Example 08 — the first agent: watch it decide, step by step, which tool
to call next, instead of following a path you wrote in advance.

Question: "Why did order 9002 fail?" — order 9002 is part of the seeded
payments incident (see data/seed_data.py): a cluster of orders that
failed with `payment_gateway_timeout` around 02:14.

Run:
    .\\scripts\\run-example.ps1 08_agent_first_loop
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.agent.simple_agent import build_simple_agent
from aisets.llm.base import LLMResponse, ToolCall

QUESTION = "Why did order 9002 fail?"


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        # Turn 1: the model decides to look up the order itself.
        llm.queue_response(LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="call_1", name="query_orders", arguments={"order_id": "9002"})],
            stop_reason="tool_use",
        ))
        # Turn 2: having seen the failure reason, it searches logs for context.
        llm.queue_response(LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="call_2", name="search_logs", arguments={"query": "payment-gateway timed out", "max_lines": 3})],
            stop_reason="tool_use",
        ))
        # Turn 3: enough evidence gathered — final answer.
        llm.queue_response(LLMResponse(
            text=(
                "Order 9002 failed because of a payment-gateway timeout "
                "(fail_reason='payment_gateway_timeout'). This lines up with a "
                "broader incident in the logs around 02:14, where the payments "
                "service repeatedly timed out calling the upstream gateway."
            ),
            stop_reason="end_turn",
        ))

    agent = build_simple_agent(llm, settings)
    result = agent.run(QUESTION)

    console.print(f"\n[bold]Question:[/bold] {QUESTION}\n")
    for step in result.steps:
        if step.action == "tool_call":
            console.print(f"[cyan]Step {step.step}:[/cyan] called [bold]{step.tool_name}[/bold]({step.tool_arguments})")
            console.print(f"          -> {step.tool_result[:200]}")
        elif step.action == "final_answer":
            console.print(f"[cyan]Step {step.step}:[/cyan] [green]final answer[/green]")

    console.print(f"\n[bold]Answer:[/bold] {result.final_answer}")
    console.print(f"\n[dim]Stopped because: {result.stopped_reason} (used {len(result.steps)} of {agent.max_steps} steps)[/dim]")


if __name__ == "__main__":
    main()
