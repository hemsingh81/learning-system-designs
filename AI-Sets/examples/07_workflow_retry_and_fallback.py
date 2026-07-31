"""
Example 07 — reliability policies in action: a step that fails twice and
succeeds on its THIRD attempt (retry), and a step that fails every attempt
and falls back to a safe default instead of crashing the whole pipeline.

Run:
    .\\scripts\\run-example.ps1 07_workflow_retry_and_fallback
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.llm.errors import RateLimited
from aisets.workflow.context import WorkflowContext
from aisets.workflow.ticket_pipeline import build_ticket_pipeline

TICKET_TEXT = "The app crashed while I was checking out, I think I was charged but got no confirmation."


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        # classify_ticket: succeeds first try.
        llm.queue_json({"category": "bug", "confidence": 0.8})

        # extract_fields is configured with max_attempts=3 in the pipeline.
        # Fail twice (simulated rate limiting), then succeed on attempt 3.
        llm.queue_error(RateLimited("simulated 429 (attempt 1)"))
        llm.queue_error(RateLimited("simulated 429 (attempt 2)"))
        llm.queue_json({
            "order_id": None, "amount_usd": None, "customer_email": None,
            "issue_summary": "Possible duplicate charge during a checkout crash.",
        })

        # score_severity: succeeds first try.
        llm.queue_json({"severity": "high", "score": 7, "reasoning": "Possible unconfirmed charge."})

        # draft_reply is configured with max_attempts=2 and a fallback.
        # Fail BOTH attempts, forcing the fallback to kick in.
        llm.queue_error(RateLimited("simulated 429 (draft attempt 1)"))
        llm.queue_error(RateLimited("simulated 429 (draft attempt 2)"))

    pipeline = build_ticket_pipeline(llm)
    ctx = WorkflowContext()
    ctx.set("ticket_text", TICKET_TEXT)

    outcomes = pipeline.run(ctx)

    console.print("\n[bold]Step-by-step outcomes:[/bold]")
    for outcome in outcomes:
        console.print(
            f"  {outcome.name:<16} status={outcome.status:<10} attempts={outcome.attempts}"
            + (f"  error={outcome.error}" if outcome.error else "")
        )

    console.print(f"\nextract_fields needed {outcomes[1].attempts} attempts before succeeding.")
    console.print(f"draft_reply status is '{outcomes[3].status}' — it used the FALLBACK reply:")
    console.print(f"  {ctx['reply_result'].reply_text!r}")


if __name__ == "__main__":
    main()
