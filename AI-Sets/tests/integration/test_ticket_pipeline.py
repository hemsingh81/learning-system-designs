"""
Integration test: the full `build_ticket_pipeline` against `FakeLLM`,
covering the sequential happy path, branching, retry, and fallback — the
same scenarios examples 05-07 demonstrate interactively.
"""

from __future__ import annotations

from aisets.llm.errors import RateLimited
from aisets.workflow.context import WorkflowContext
from aisets.workflow.ticket_pipeline import build_ticket_pipeline


def _run(llm, ticket_text: str):
    pipeline = build_ticket_pipeline(llm)
    ctx = WorkflowContext()
    ctx.set("ticket_text", ticket_text)
    outcomes = pipeline.run(ctx)
    return outcomes, ctx


def test_full_sequential_run_all_steps_succeed(fake_llm) -> None:
    fake_llm.queue_json({"category": "outage", "confidence": 0.95})
    fake_llm.queue_json({"order_id": "8842", "amount_usd": None, "customer_email": None, "issue_summary": "Outage."})
    fake_llm.queue_json({"severity": "critical", "score": 10, "reasoning": "Full outage."})
    fake_llm.queue_json({"reply_text": "We are investigating.", "tone": "empathetic", "contains_prohibited_content": False})

    outcomes, ctx = _run(fake_llm, "The dashboard is completely down for everyone, order 8842.")

    assert [o.status for o in outcomes] == ["ok", "ok", "ok", "ok"]
    assert ctx["category_result"].category == "outage"
    assert ctx["fields_result"].order_id == "8842"
    assert ctx["severity_result"].severity == "critical"
    assert ctx["reply_result"].reply_text == "We are investigating."


def test_low_severity_skips_draft_reply(fake_llm) -> None:
    fake_llm.queue_json({"category": "how_to", "confidence": 0.9})
    fake_llm.queue_json({"order_id": None, "amount_usd": None, "customer_email": None, "issue_summary": "Wants invoice PDF."})
    fake_llm.queue_json({"severity": "low", "score": 1, "reasoning": "Simple question."})
    # No fourth response queued — draft_reply must not be called at all.

    outcomes, ctx = _run(fake_llm, "How do I download my invoice as a PDF?")

    assert outcomes[3].status == "skipped"
    assert ctx.get("reply_result") is None
    assert len(fake_llm.calls) == 3


def test_extract_retries_then_succeeds(fake_llm) -> None:
    fake_llm.queue_json({"category": "bug", "confidence": 0.8})
    fake_llm.queue_error(RateLimited("429 #1"))
    fake_llm.queue_error(RateLimited("429 #2"))
    fake_llm.queue_json({"order_id": None, "amount_usd": None, "customer_email": None, "issue_summary": "A bug."})
    fake_llm.queue_json({"severity": "medium", "score": 4, "reasoning": "Minor bug."})
    # severity "medium" != "low" so draft_reply runs too.
    fake_llm.queue_json({"reply_text": "Thanks, we're looking into it.", "tone": "neutral", "contains_prohibited_content": False})

    outcomes, ctx = _run(fake_llm, "Something is broken.")

    assert outcomes[1].status == "ok"
    assert outcomes[1].attempts == 3
    assert ctx["fields_result"].issue_summary == "A bug."


def test_draft_reply_exhausts_retries_and_falls_back(fake_llm) -> None:
    fake_llm.queue_json({"category": "billing", "confidence": 0.9})
    fake_llm.queue_json({"order_id": None, "amount_usd": 200.0, "customer_email": None, "issue_summary": "Overcharged."})
    fake_llm.queue_json({"severity": "high", "score": 7, "reasoning": "Money involved."})
    fake_llm.queue_error(RateLimited("429 draft #1"))
    fake_llm.queue_error(RateLimited("429 draft #2"))

    outcomes, ctx = _run(fake_llm, "I was overcharged $200.")

    assert outcomes[3].status == "fallback"
    assert "follow up" in ctx["reply_result"].reply_text
