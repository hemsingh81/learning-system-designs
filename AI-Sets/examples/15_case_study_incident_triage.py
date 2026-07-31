"""
Example 15 — the capstone case study: incident triage.

Wires together EVERYTHING from Lessons 01-04: a Goal, a Planner, an
investigating AgentLoop (3 read-only tools), a Critic that can reject an
incomplete answer and trigger a re-plan, and an EscalationGate that
NEVER lets a write action through without a human's sign-off — and, in
the "trap" variant, refuses to guess at all when the evidence is
genuinely insufficient or contradictory.

Three data variants (data/case_study/{easy,ambiguous,trap}/):
  - easy:       clear, consistent evidence -> one investigation pass.
  - ambiguous:  weak evidence at first -> the Critic rejects it, a
                second, broader investigation pass finds the missing
                piece -> succeeds.
  - trap:       genuinely contradictory evidence (the metrics spike
                belongs to a DIFFERENT service than the one being
                investigated) -> the Critic never accepts it -> the
                system ESCALATES instead of guessing. No action is ever
                taken on unconfirmed evidence.

`run_incident_triage` is the reusable piece — imported directly by
tests/integration/test_case_study.py so the exact same code path is
tested, not a re-implementation of it.

Run:
    .\\scripts\\run-example.ps1 15_case_study_incident_triage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from _common import console, is_fake, setup

from aisets.agent.loop import AgentLoop
from aisets.agent.registry import ToolRegistry
from aisets.agentic.critic import Critic
from aisets.agentic.escalation import ApprovalRecord, ApprovalRequest, EscalationGate, EscalationPolicy
from aisets.agentic.goal import Goal
from aisets.agentic.planner import Planner
from aisets.llm.base import LLMResponse, ToolCall
from aisets.tools.logs import make_search_logs_tool
from aisets.tools.metrics import make_get_metrics_tool
from aisets.tools.runbook import make_find_runbook_tool

GOAL = Goal(
    objective="Determine the root cause of the incident reported around 02:14 and recommend a fix, backed by evidence.",
    success_criteria=[
        "States a specific root cause for the PAYMENTS service specifically (not just 'something is wrong', and not a different service).",
        "Cites concrete evidence from a tool (a log line or a metric value), not a guess.",
        "The evidence is not contradicted by a different, more plausible explanation.",
    ],
    hard_constraints=["Never take a write action without explicit human approval."],
    stop_conditions=["Stop once a root cause is confidently supported by consistent evidence, or after the investigation attempt limit is reached."],
)

QUESTION_TEMPLATE = (
    "Investigate the incident reported around 02:14 today for the payments service "
    "and determine the root cause. Suggested approach: {plan_steps}"
)


def build_investigator(llm, variant_dir: Path, runbooks_dir: Path, *, max_steps: int = 6) -> AgentLoop:
    registry = ToolRegistry()
    registry.register(make_search_logs_tool(variant_dir / "app.log"))
    registry.register(make_get_metrics_tool(variant_dir / "metrics.json"))
    registry.register(make_find_runbook_tool(runbooks_dir))
    system_prompt = (
        "You are a backend incident investigator. You can search logs, check "
        "service metrics, and find runbooks. Gather evidence before concluding. "
        "If the evidence points to a DIFFERENT service than the one you were "
        "asked about, or if you cannot find concrete evidence, say so honestly "
        "instead of guessing at a root cause."
    )
    return AgentLoop(llm, registry, system_prompt=system_prompt, max_steps=max_steps, allow_write=False)


@dataclass
class TriageResult:
    variant: str
    critic_met: bool
    escalated: bool
    action_approved: bool
    final_message: str
    attempts: int
    answer: str
    approval_records: list[ApprovalRecord] = field(default_factory=list)


def run_incident_triage(
    llm,
    settings,
    variant: str,
    *,
    human_approve: Callable[[ApprovalRequest], bool],
    max_attempts: int = 2,
) -> TriageResult:
    variant_dir = settings.data_dir / "case_study" / variant
    runbooks_dir = settings.data_dir / "runbooks"

    investigator = build_investigator(llm, variant_dir, runbooks_dir)
    planner = Planner(llm)
    critic = Critic(llm)
    gate = EscalationGate(EscalationPolicy(), human_approve=human_approve)

    evidence_notes = ""
    answer = ""
    verdict = None
    context_notes = ""

    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        plan = planner.make_plan(GOAL, context_notes=context_notes)
        question = QUESTION_TEMPLATE.format(plan_steps="; ".join(plan.steps))

        result = investigator.run(question)
        answer = result.final_answer
        evidence_notes += f"\n--- Attempt {attempt} ---\n{answer}"

        verdict = critic.check(GOAL, answer, evidence_notes)
        if verdict.goal_met:
            break
        context_notes = f"Attempt {attempt} was rejected by the reviewer. Missing: {verdict.missing}. Broaden the investigation."

    if verdict is None or not verdict.goal_met:
        gate.request(
            action="propose_fix",
            arguments={},
            is_write_action=True,
            risk_level="high",
            confidence=0.3,
            reasoning="Evidence remained insufficient or contradictory after investigation — refusing to guess.",
        )
        return TriageResult(
            variant=variant, critic_met=False, escalated=True, action_approved=False,
            final_message="Evidence was insufficient or contradictory — escalated to a human, no action taken.",
            attempts=attempt, answer=answer, approval_records=gate.records,
        )

    record = gate.request(
        action="restart_service",
        arguments={"service_name": "payments"},
        is_write_action=True,
        risk_level="medium",
        confidence=0.85,
        reasoning=f"Root cause identified: {answer}",
    )
    message = answer + (
        " -> Action APPROVED by a human, would now be executed."
        if record.approved
        else " -> Action NOT approved by a human — nothing executed."
    )
    return TriageResult(
        variant=variant, critic_met=True, escalated=False, action_approved=record.approved,
        final_message=message, attempts=attempt, answer=answer, approval_records=gate.records,
    )


# --- Demo scripting (FakeLLM only) ------------------------------------------

def _script_easy(llm) -> None:
    llm.queue_json({"steps": ["check payments logs", "check payments metrics", "conclude"], "reasoning": "start with logs"})
    llm.queue_response(LLMResponse(text=None, tool_calls=[ToolCall(id="c1", name="search_logs", arguments={"query": "ERROR"})], stop_reason="tool_use"))
    llm.queue_response(LLMResponse(
        text="Payments failed due to a payment-gateway timeout: log shows 'upstream call to payment-gateway timed out after 5000ms' at 02:14, with the circuit breaker opening shortly after.",
        stop_reason="end_turn",
    ))
    llm.queue_json({"goal_met": True, "reasoning": "Specific root cause with cited log evidence, consistent, no contradiction.", "missing": []})


def _script_ambiguous(llm) -> None:
    llm.queue_json({"steps": ["check payments metrics"], "reasoning": "start with metrics"})
    llm.queue_response(LLMResponse(text=None, tool_calls=[ToolCall(id="c1", name="get_metrics", arguments={"service": "payments"})], stop_reason="tool_use"))
    llm.queue_response(LLMResponse(
        text="Payments metrics show a mild latency/error-rate increase around 02:14, but no confirmed root cause yet.",
        stop_reason="end_turn",
    ))
    llm.queue_json({"goal_met": False, "reasoning": "An elevated metric alone is not a root cause.", "missing": ["a specific root cause", "supporting log evidence"]})

    llm.queue_json({"steps": ["search logs for connection/pool related warnings", "combine with the metrics spike"], "reasoning": "broaden the search"})
    llm.queue_response(LLMResponse(text=None, tool_calls=[ToolCall(id="c2", name="search_logs", arguments={"query": "connection pool"})], stop_reason="tool_use"))
    llm.queue_response(LLMResponse(
        text="Payments showed a metrics spike (elevated latency/error rate) around 02:14, correlating with a log warning: 'connection pool at 85% utilization (18/20 connections in use)'. Root cause: the connection pool was nearing exhaustion under load.",
        stop_reason="end_turn",
    ))
    llm.queue_json({"goal_met": True, "reasoning": "Root cause now supported by both a metric and a log line, consistent with each other.", "missing": []})


def _script_trap(llm) -> None:
    llm.queue_json({"steps": ["check payments metrics"], "reasoning": "start with metrics"})
    llm.queue_response(LLMResponse(text=None, tool_calls=[ToolCall(id="c1", name="get_metrics", arguments={"service": "payments"})], stop_reason="tool_use"))
    llm.queue_response(LLMResponse(
        text="Payments metrics show no anomaly around 02:14. Unable to identify a root cause for the reported payments incident from this evidence.",
        stop_reason="end_turn",
    ))
    llm.queue_json({"goal_met": False, "reasoning": "No root cause identified.", "missing": ["a concrete root cause", "evidence explaining the incident"]})

    llm.queue_json({"steps": ["check other services in case the incident was misattributed", "re-examine payments logs"], "reasoning": "broaden the search"})
    llm.queue_response(LLMResponse(text=None, tool_calls=[ToolCall(id="c2", name="search_logs", arguments={"query": "ERROR"})], stop_reason="tool_use"))
    llm.queue_response(LLMResponse(
        text=(
            "No payments-specific error evidence was found. The checkout service shows a metrics "
            "spike and errors following a deployment (v42) around 02:09-02:15, but this is a "
            "DIFFERENT service than payments, and it's unclear whether it explains the reported "
            "payments incident. Evidence is inconclusive and possibly contradictory."
        ),
        stop_reason="end_turn",
    ))
    llm.queue_json({
        "goal_met": False,
        "reasoning": "The only concrete evidence found belongs to a different service (checkout), not payments — this does not satisfy 'root cause for the payments service specifically'.",
        "missing": ["a root cause confirmed for the PAYMENTS service, not a different service"],
    })


def main() -> None:
    settings, llm = setup()

    def print_result(result: TriageResult) -> None:
        console.print(f"  attempts: {result.attempts}")
        console.print(f"  critic_met: {result.critic_met}, escalated: {result.escalated}, action_approved: {result.action_approved}")
        console.print(f"  {result.final_message}")

    console.rule("Variant: EASY")
    if is_fake(llm):
        _script_easy(llm)
    result_easy = run_incident_triage(llm, settings, "easy", human_approve=lambda req: True)
    print_result(result_easy)

    console.rule("Variant: AMBIGUOUS (Critic rejects attempt 1, re-plan succeeds on attempt 2)")
    if is_fake(llm):
        _script_ambiguous(llm)
    result_ambiguous = run_incident_triage(llm, settings, "ambiguous", human_approve=lambda req: False)
    print_result(result_ambiguous)

    console.rule("Variant: TRAP (contradictory evidence -> must escalate, never guess)")
    if is_fake(llm):
        _script_trap(llm)
    result_trap = run_incident_triage(llm, settings, "trap", human_approve=lambda req: False)
    print_result(result_trap)

    assert result_trap.escalated and not result_trap.action_approved, "the trap variant must never take an action on unconfirmed evidence"
    console.print("\n[green]Confirmed: the trap variant escalated and took NO action, as required.[/green]")


if __name__ == "__main__":
    main()
