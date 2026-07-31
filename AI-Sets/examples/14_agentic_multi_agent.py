"""
Example 14 — multi-agent orchestration: an investigator, a fixer, and a
communicator, each independently working the SAME incident, combined by a
Supervisor into one synthesis. Compares total model calls against a
single agent covering only the investigation part, to make the cost
tradeoff concrete (docs/01-concepts.md's "centralized vs distributed
agents" tradeoff).

Run:
    .\\scripts\\run-example.ps1 14_agentic_multi_agent
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.agent.simple_agent import build_simple_agent
from aisets.agentic.orchestrator import Specialist, Supervisor
from aisets.llm.base import LLMResponse, Message, ToolCall
from aisets.skills.draft_reply import DraftReplySkill
from aisets.tools.runbook import make_find_runbook_tool

TASK = "The payments service had an incident around 02:14 — investigate, recommend a fix, and draft a customer-facing update."


def make_investigator(llm, settings):
    agent = build_simple_agent(llm, settings)

    def run(task: str) -> str:
        return agent.run("Why did the payments incident happen around 02:14?").final_answer

    return run


def make_fixer(llm, settings):
    find_runbook = make_find_runbook_tool(settings.data_dir / "runbooks")

    def run(task: str) -> str:
        matches = find_runbook(keywords="payments gateway timeout")
        top = matches[0]["filename"] if matches else "no matching runbook"
        response = llm.complete(
            [Message(role="user", content=f"Matching runbook: {top}. Write a one-sentence fix recommendation.")],
            system="You are a fix recommender. Be concise, cite the runbook by name.",
        )
        return response.text or ""

    return run


def make_communicator(llm):
    draft_skill = DraftReplySkill(llm, tone="empathetic")

    def run(task: str) -> str:
        result = draft_skill.run("Customers are asking why payments were failing around 02:14 this morning.")
        return result.reply_text

    return run


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        # Investigator: 1 tool call + 1 final answer = 2 model calls.
        llm.queue_response(LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="c1", name="query_orders", arguments={"service": "payments", "status": "failed", "limit": 5})],
            stop_reason="tool_use",
        ))
        llm.queue_response(LLMResponse(
            text="Multiple payments orders failed around 02:14 due to a payment-gateway timeout.",
            stop_reason="end_turn",
        ))
        # Fixer: 1 model call.
        llm.queue_text("Per payments-gateway-timeout.md, monitor for gateway recovery before considering a restart.")
        # Communicator: 1 model call (draft_reply skill).
        llm.queue_json({
            "reply_text": "We experienced a brief payment processing issue around 02:14 and it has since been resolved.",
            "tone": "empathetic", "contains_prohibited_content": False,
        })
        # Supervisor synthesis: 1 model call.
        llm.queue_json({
            "summary": (
                "Root cause: a payment-gateway timeout caused failed payments around 02:14. "
                "Recommended action: monitor gateway recovery per the runbook before restarting. "
                "A customer-facing update has been drafted acknowledging the brief issue."
            ),
            "contradictions": [],
        })

    investigator = Specialist("investigator", make_investigator(llm, settings))
    fixer = Specialist("fixer", make_fixer(llm, settings))
    communicator = Specialist("communicator", make_communicator(llm))
    supervisor = Supervisor(llm, [investigator, fixer, communicator])

    result = supervisor.run(TASK)

    console.print("\n[bold]Specialist results:[/bold]")
    for r in result.specialist_results:
        status = "[green]ok[/green]" if r.succeeded else f"[red]failed: {r.error}[/red]"
        console.print(f"  {r.name}: {status}")
        if r.succeeded:
            console.print(f"    {r.output}")

    console.print(f"\n[bold]Synthesis:[/bold] {result.final_answer}")
    if result.contradictions:
        console.print(f"[yellow]Contradictions flagged:[/yellow] {result.contradictions}")

    multi_agent_calls = len(llm.calls) if is_fake(llm) else None
    console.print(f"\n[dim]Total model calls for the full 3-specialist team + synthesis: {multi_agent_calls}[/dim]")
    console.print(
        "[dim]A single agent doing ONLY the investigation part would need about 2 calls "
        "(as in example 08) — the multi-agent team costs more in total calls, but covers "
        "3 distinct concerns (investigate, fix, communicate) that one agent's tool set "
        "wasn't built to handle at once. See tutorial/04-agentic/README.md's tradeoff table.[/dim]"
    )


if __name__ == "__main__":
    main()
