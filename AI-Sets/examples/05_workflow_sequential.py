"""
Example 05 — a full sequential workflow run: classify -> extract ->
score severity -> draft reply, all four steps in the fixed order YOU
wrote in `build_ticket_pipeline`.

Run:
    .\\scripts\\run-example.ps1 05_workflow_sequential
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.workflow.context import WorkflowContext
from aisets.workflow.ticket_pipeline import build_ticket_pipeline

TICKET_TEXT = (
    "The entire dashboard has been down for 20 minutes, we can't log in at all. "
    "This is affecting our whole team, order 8842 is stuck."
)


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        # Queue exactly one scripted response per step, IN THE ORDER the
        # pipeline calls them: classify, extract, severity, draft.
        llm.queue_json({"category": "outage", "confidence": 0.95})
        llm.queue_json({
            "order_id": "8842", "amount_usd": None, "customer_email": None,
            "issue_summary": "Full dashboard outage affecting the whole team.",
        })
        llm.queue_json({"severity": "critical", "score": 10, "reasoning": "Full outage, whole team blocked."})
        llm.queue_json({
            "reply_text": "We're aware of the outage and our team is investigating urgently.",
            "tone": "empathetic", "contains_prohibited_content": False,
        })

    pipeline = build_ticket_pipeline(llm)
    ctx = WorkflowContext()
    ctx.set("ticket_text", TICKET_TEXT)

    outcomes = pipeline.run(ctx)

    console.print("\n[bold]Step-by-step outcomes:[/bold]")
    for outcome in outcomes:
        console.print(f"  {outcome.name:<16} status={outcome.status:<10} attempts={outcome.attempts}")

    console.print(f"\n[bold]Execution trace:[/bold] {ctx.trace}")

    console.print("\n[bold]Final context values:[/bold]")
    console.print(f"  category: {ctx['category_result'].category}")
    console.print(f"  severity: {ctx['severity_result'].severity} (score={ctx['severity_result'].score})")
    console.print(f"  order_id extracted: {ctx['fields_result'].order_id}")
    console.print(f"  drafted reply: {ctx['reply_result'].reply_text!r}")


if __name__ == "__main__":
    main()
