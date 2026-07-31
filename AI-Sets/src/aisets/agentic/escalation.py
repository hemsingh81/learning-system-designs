"""
Escalation — the policy that decides whether a proposed action can run
automatically, needs a human to confirm it, or must be decided by a human
outright (with no automatic path at all). This is the concrete mechanism
behind docs/01-concepts.md's "knows when to stop and ask a human".

Design point: escalation is a PRODUCT/POLICY decision, not something the
model gets to decide about itself. `EscalationPolicy.decide` is plain,
auditable Python — you can point at the exact rule that produced a given
decision, the same way you'd point at an authorization rule in an access-
control system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

RiskLevel = Literal["low", "medium", "high"]
DecisionAction = Literal["auto", "confirm", "human_only"]
DecidedBy = Literal["auto", "human", "no_human_available"]


@dataclass(frozen=True)
class EscalationDecision:
    action: DecisionAction
    reason: str


@dataclass(frozen=True)
class ApprovalRequest:
    action: str
    arguments: dict
    risk_level: RiskLevel
    reasoning: str


@dataclass(frozen=True)
class ApprovalRecord:
    request: ApprovalRequest
    approved: bool
    decided_by: DecidedBy


class EscalationPolicy:
    """The RULE. Any write action always requires at least a human
    confirmation, regardless of confidence — see DECISIONS.md D-403.
    A read action escalates to human_only only if risk is high or
    confidence is low; otherwise it proceeds automatically."""

    def __init__(self, *, always_confirm_write: bool = True, min_auto_confidence: float = 0.6) -> None:
        self.always_confirm_write = always_confirm_write
        self.min_auto_confidence = min_auto_confidence

    def decide(self, *, is_write_action: bool, risk_level: RiskLevel, confidence: float) -> EscalationDecision:
        if is_write_action and self.always_confirm_write:
            return EscalationDecision(
                action="confirm",
                reason="Write actions always require human confirmation, regardless of confidence.",
            )
        if risk_level == "high":
            return EscalationDecision(
                action="human_only",
                reason="Risk level is high — no automatic path, a human must decide.",
            )
        if confidence < self.min_auto_confidence:
            return EscalationDecision(
                action="human_only",
                reason=f"Confidence {confidence:.2f} is below the minimum for automatic action "
                f"({self.min_auto_confidence:.2f}).",
            )
        return EscalationDecision(
            action="auto",
            reason=f"Risk level '{risk_level}' with confidence {confidence:.2f} — safe to proceed automatically.",
        )


class EscalationGate:
    """Wires `EscalationPolicy` to an actual human-approval callback and
    keeps an audit trail (`records`) of every decision made, approved or
    not — the same shape as `tools/actions.py`'s `AuditLog`, applied one
    layer up (BEFORE the action even reaches a tool call)."""

    def __init__(self, policy: EscalationPolicy, human_approve: Callable[[ApprovalRequest], bool] | None = None) -> None:
        self.policy = policy
        self.human_approve = human_approve
        self.records: list[ApprovalRecord] = []

    def request(
        self,
        *,
        action: str,
        arguments: dict,
        is_write_action: bool,
        risk_level: RiskLevel,
        confidence: float,
        reasoning: str,
    ) -> ApprovalRecord:
        decision = self.policy.decide(is_write_action=is_write_action, risk_level=risk_level, confidence=confidence)
        request = ApprovalRequest(action=action, arguments=arguments, risk_level=risk_level, reasoning=reasoning)

        if decision.action == "auto":
            record = ApprovalRecord(request=request, approved=True, decided_by="auto")
        elif self.human_approve is None:
            # No human available to ask, and the policy required one —
            # the SAFE default is to deny, never to silently proceed.
            record = ApprovalRecord(request=request, approved=False, decided_by="no_human_available")
        else:
            approved = self.human_approve(request)
            record = ApprovalRecord(request=request, approved=approved, decided_by="human")

        self.records.append(record)
        return record
