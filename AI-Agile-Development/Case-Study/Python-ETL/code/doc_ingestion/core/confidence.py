"""The confidence gate. Pure logic, zero Azure imports, no I/O.

This is the heart of the design, and its isolation is the design decision worth
copying. The gate decides whether a document is trustworthy enough to enter the
warehouse; that decision is the one thing in the pipeline you most need to be
able to test exhaustively and reason about in an audit. So it takes dataclasses
in and returns a dataclass out. There is nothing to mock. ``tests/test_confidence.py``
imports this module and constructs documents by hand.

The three rules it encodes:

* **Per-field-type thresholds.** Money and quantity are gated harder than
  descriptive text, because a wrong number is materially worse than a wrong
  label. A misread security *name* does not break a reconciliation keyed on
  identifier and quantity; a misread *quantity* does.
* **A field the model did not return is a failure, not a pass.** Absence is not
  evidence of correctness.
* **One failing field sends the whole document to review.** Partial ingestion of
  a statement produces a reconciliation break that looks exactly like a real
  settlement failure, and operations cannot tell the two apart. Half a statement
  is worse than none.

The gate sits upstream of reconciliation for the same reason: if low-confidence
rows flowed through, the break report would fill with false positives and
operations would stop trusting the control.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import SourceConfig
from core.extract import ExtractedDocument, ExtractedField

# Why a field failed. Kept as literals rather than an enum so the value survives
# a round trip through the exception queue's JSON column unchanged.
WHY_MISSING = "missing"
WHY_BELOW_THRESHOLD = "below_threshold"
WHY_NO_CONFIDENCE = "no_confidence"


@dataclass
class GateResult:
    """The gate's verdict on one document."""

    passed: bool
    # Each failure: field, row, value, confidence, threshold, why.
    failures: list[dict] = field(default_factory=list)
    # True only if every field cleared its threshold — this is the numerator of
    # the straight-through rate, the single most useful metric in the system.
    straight_through: bool = False

    @property
    def reason(self) -> str:
        """A short human-readable reason, for the exception queue row."""
        if self.passed:
            return "ok"
        names = ", ".join(sorted({str(f["field"]) for f in self.failures}))
        return f"low_confidence: {names}"


def _check(
    f: ExtractedField,
    source: SourceConfig,
    row: int | None = None,
) -> dict | None:
    """Evaluate one field against its type's threshold. ``None`` means it passed."""
    threshold = source.confidence.threshold_for(f.field_type)

    # A field the model did not return at all is a failure, not a pass.
    if f.value is None:
        return {
            "field": f.name,
            "row": row,
            "value": None,
            "confidence": f.confidence,
            "threshold": threshold,
            "why": WHY_MISSING,
        }

    # Custom models return None confidence for some field types — treat as
    # unverified. Auto-accepting a value nobody scored is the exact failure the
    # gate exists to prevent.
    if f.confidence is None:
        return {
            "field": f.name,
            "row": row,
            "value": f.value,
            "confidence": None,
            "threshold": threshold,
            "why": WHY_NO_CONFIDENCE,
        }

    if f.confidence < threshold:
        return {
            "field": f.name,
            "row": row,
            "value": f.value,
            "confidence": f.confidence,
            "threshold": threshold,
            "why": WHY_BELOW_THRESHOLD,
        }

    return None


def evaluate(doc: ExtractedDocument, source: SourceConfig) -> GateResult:
    """Gate every header field and every line-item field in the document.

    Failures are collected rather than short-circuited: the analyst working the
    exception queue needs to see everything wrong with the document at once, not
    fix one field and resubmit to discover the next.
    """
    failures = [c for f in doc.header.values() if (c := _check(f, source)) is not None]

    for idx, row in enumerate(doc.line_items):
        failures.extend(
            c for f in row.values() if (c := _check(f, source, row=idx)) is not None
        )

    return GateResult(
        passed=not failures,
        failures=failures,
        straight_through=not failures,
    )


def min_confidence(doc: ExtractedDocument) -> float:
    """The lowest confidence anywhere in the document.

    Carried onto every warehouse row. When a number in a report is questioned,
    this plus ``bronze_path`` is the answer: here is how sure the model was, and
    here is the original response it came from.

    A field with no reported confidence contributes 0.0 — the honest reading of
    "we do not know". An empty document is 0.0 for the same reason.
    """
    scores = [f.confidence if f.confidence is not None else 0.0 for _, f in doc.all_fields()]
    return min(scores) if scores else 0.0
