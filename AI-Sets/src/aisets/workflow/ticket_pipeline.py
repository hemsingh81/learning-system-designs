"""
`build_ticket_pipeline` — the concrete example workflow: classify -> extract
-> score severity -> (branch) draft reply.

This wires together the exact same skills from Milestone 2 in a FIXED
order. Notice the branch: `draft_reply` is skipped entirely when severity
is "low" — that's a decision made HERE, by the person building the
pipeline, not by the model. This is the clearest illustration of the
Skill-vs-Workflow line from docs/01-concepts.md.
"""

from __future__ import annotations

from aisets.llm.base import LLMClient
from aisets.skills.classify_ticket import ClassifyTicket
from aisets.skills.draft_reply import DraftReply, DraftReplySkill
from aisets.skills.extract_fields import ExtractFields
from aisets.skills.score_severity import ScoreSeverity
from aisets.workflow.context import WorkflowContext
from aisets.workflow.engine import Pipeline, Step
from aisets.workflow.policies import CircuitBreaker, RetryPolicy


def build_ticket_pipeline(llm: LLMClient) -> Pipeline:
    classify_skill = ClassifyTicket(llm)
    extract_skill = ExtractFields(llm)
    severity_skill = ScoreSeverity(llm)
    reply_skill = DraftReplySkill(llm)

    classify_breaker = CircuitBreaker(failure_threshold=3)

    def do_classify(ctx: WorkflowContext) -> None:
        ctx.set("category_result", classify_skill.run(ctx["ticket_text"]))

    def do_extract(ctx: WorkflowContext) -> None:
        ctx.set("fields_result", extract_skill.run(ctx["ticket_text"]))

    def do_severity(ctx: WorkflowContext) -> None:
        ctx.set("severity_result", severity_skill.run(ctx["ticket_text"]))

    def needs_reply(ctx: WorkflowContext) -> bool:
        severity = ctx.get("severity_result")
        return severity is not None and severity.severity != "low"

    def do_draft(ctx: WorkflowContext) -> None:
        ctx.set("reply_result", reply_skill.run(ctx["ticket_text"]))

    def fallback_draft(ctx: WorkflowContext) -> None:
        ctx.set(
            "reply_result",
            DraftReply(
                reply_text=(
                    "Thanks for contacting us. A team member will follow up with "
                    "you shortly."
                ),
                tone="neutral",
                contains_prohibited_content=False,
            ),
        )

    steps = [
        Step(
            "classify_ticket",
            do_classify,
            retry=RetryPolicy(max_attempts=2, backoff_seconds=(0.0,)),
            breaker=classify_breaker,
        ),
        Step(
            "extract_fields",
            do_extract,
            retry=RetryPolicy(max_attempts=3, backoff_seconds=(0.0, 0.0)),
        ),
        Step(
            "score_severity",
            do_severity,
            retry=RetryPolicy(max_attempts=2, backoff_seconds=(0.0,)),
        ),
        Step(
            "draft_reply",
            do_draft,
            condition=needs_reply,
            retry=RetryPolicy(max_attempts=2, backoff_seconds=(0.0,)),
            fallback=fallback_draft,
        ),
    ]
    return Pipeline("ticket_pipeline", steps)
