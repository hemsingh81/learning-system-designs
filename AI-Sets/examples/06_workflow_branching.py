"""
Example 06 — branching: the `draft_reply` step is SKIPPED for a low-severity
ticket, and RUN for a higher-severity one. The branch condition lives in
`build_ticket_pipeline` (a human decision), not inside any skill.

Run:
    .\\scripts\\run-example.ps1 06_workflow_branching
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.workflow.context import WorkflowContext
from aisets.workflow.ticket_pipeline import build_ticket_pipeline

LOW_SEVERITY_TICKET = "How do I download my past invoices as PDF?"
HIGH_SEVERITY_TICKET = "My payment failed three times and I was still charged $200 each time!"


def run_one(llm, label: str, ticket_text: str, script) -> None:
    console.rule(label)
    if script:
        script(llm)

    pipeline = build_ticket_pipeline(llm)
    ctx = WorkflowContext()
    ctx.set("ticket_text", ticket_text)
    outcomes = pipeline.run(ctx)

    for outcome in outcomes:
        console.print(f"  {outcome.name:<16} status={outcome.status}")
    severity = ctx.get("severity_result")
    console.print(f"  severity = {severity.severity if severity else '?'}")
    if ctx.get("reply_result"):
        console.print(f"  reply drafted: {ctx['reply_result'].reply_text!r}")
    else:
        console.print("  reply drafted: (none — draft_reply was skipped)")


def main() -> None:
    settings, llm = setup()

    def script_low(llm) -> None:
        llm.queue_json({"category": "how_to", "confidence": 0.9})
        llm.queue_json({"order_id": None, "amount_usd": None, "customer_email": None, "issue_summary": "Wants past invoices as PDF."})
        llm.queue_json({"severity": "low", "score": 1, "reasoning": "Simple how-to question, no urgency."})
        # NOTE: no draft_reply response queued — it must not be called at all.

    def script_high(llm) -> None:
        llm.queue_json({"category": "billing", "confidence": 0.9})
        llm.queue_json({"order_id": None, "amount_usd": 200.0, "customer_email": None, "issue_summary": "Repeated failed payments still charged $200 each time."})
        llm.queue_json({"severity": "high", "score": 7, "reasoning": "Repeated incorrect charges, financial impact."})
        llm.queue_json({"reply_text": "We're sorry about the repeated charges — our billing team will investigate and follow up shortly.", "tone": "empathetic", "contains_prohibited_content": False})

    run_one(llm, "Ticket A (low severity — draft_reply should be SKIPPED)", LOW_SEVERITY_TICKET, script_low if is_fake(llm) else None)
    run_one(llm, "Ticket B (high severity — draft_reply should RUN)", HIGH_SEVERITY_TICKET, script_high if is_fake(llm) else None)


if __name__ == "__main__":
    main()
