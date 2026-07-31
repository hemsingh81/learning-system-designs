"""Tests for the confidence gate.

Not one mock in this file. The gate is pure logic in its own module with no
Azure dependency, so it is unit tested directly — that separation was a
deliberate design choice, and this file is the evidence that it paid off.

The four tests below are the four the gate has to get right. Everything else the
pipeline does is downstream of them being true.
"""

from __future__ import annotations

import pytest

from config.settings import ConfidenceConfig, SourceConfig
from core.confidence import evaluate, min_confidence
# conftest.py sits next to this file; pytest puts tests/ on sys.path.
from conftest import make_document, make_field as _f


@pytest.fixture
def source() -> SourceConfig:
    return SourceConfig(
        key="test",
        display_name="t",
        container="raw",
        prefix="test/",
        model_id="m",
        doc_type="position_statement",
        confidence=ConfidenceConfig(
            default=0.80,
            by_field_type={"currency": 0.90, "number": 0.90, "date": 0.85, "string": 0.75},
        ),
    )


def test_money_field_gated_harder_than_text(source: SourceConfig) -> None:
    """0.82 passes for a name and 0.85 fails for a value. That asymmetry is the point."""
    doc = make_document(
        header={
            # 0.82 clears the 0.75 string threshold
            "security_name": _f("security_name", "Acme Corp", 0.82, "string"),
            # 0.85 does NOT clear the 0.90 currency threshold
            "market_value": _f("market_value", 1_000_000, 0.85, "currency"),
        }
    )

    result = evaluate(doc, source)

    assert not result.passed
    assert {f["field"] for f in result.failures} == {"market_value"}


def test_missing_value_is_a_failure_not_a_pass(source: SourceConfig) -> None:
    """A field the model did not return is a failure, however sure it claims to be."""
    doc = make_document(header={"quantity": _f("quantity", None, 0.99, "number")})

    assert evaluate(doc, source).failures[0]["why"] == "missing"


def test_null_confidence_never_auto_accepts(source: SourceConfig) -> None:
    """No score means unverified. Unverified never loads."""
    doc = make_document(header={"quantity": _f("quantity", 100, None, "number")})

    assert not evaluate(doc, source).passed


def test_one_bad_line_item_fails_whole_document(source: SourceConfig) -> None:
    """Partial ingestion of a statement produces a break that looks real.

    So one bad row rejects the document, not the row.
    """
    doc = make_document(
        header={"account_number": _f("account_number", "ACC-1", 0.99)},
        line_items=[
            {"quantity": _f("quantity", 100, 0.99, "number")},
            {"quantity": _f("quantity", 200, 0.60, "number")},  # bad row
        ],
    )

    result = evaluate(doc, source)

    assert not result.passed
    assert result.failures[0]["row"] == 1


# -----------------------------------------------------------------------------
# Supporting behaviour
# -----------------------------------------------------------------------------


def test_clean_document_is_straight_through(source: SourceConfig) -> None:
    """The straight-through flag is the numerator of the headline metric."""
    doc = make_document(
        header={"account_number": _f("account_number", "ACC-1", 0.99)},
        line_items=[
            {
                "security_id": _f("security_id", "US0378331005", 0.97),
                "quantity": _f("quantity", 100, 0.96, "number"),
            }
        ],
    )

    result = evaluate(doc, source)

    assert result.passed
    assert result.straight_through
    assert result.reason == "ok"


def test_integer_fields_are_gated_as_numbers(source: SourceConfig) -> None:
    """`integer` is an alias for `number`; it must not fall back to the 0.80 default."""
    doc = make_document(header={"lots": _f("lots", 12, 0.85, "integer")})

    assert not evaluate(doc, source).passed


def test_failure_reason_names_every_bad_field(source: SourceConfig) -> None:
    """The analyst gets the whole list at once, not one field per resubmission."""
    doc = make_document(
        header={
            "market_value": _f("market_value", 10, 0.10, "currency"),
            "statement_date": _f("statement_date", "2026-07-31", 0.20, "date"),
        }
    )

    reason = evaluate(doc, source).reason

    assert reason.startswith("low_confidence:")
    assert "market_value" in reason and "statement_date" in reason


def test_min_confidence_is_the_weakest_field(source: SourceConfig) -> None:
    """This value is carried onto every warehouse row as the audit signal."""
    doc = make_document(
        header={"account_number": _f("account_number", "ACC-1", 0.99)},
        line_items=[{"quantity": _f("quantity", 100, 0.91, "number")}],
    )

    assert min_confidence(doc) == pytest.approx(0.91)


def test_min_confidence_treats_unscored_as_zero(source: SourceConfig) -> None:
    """An unscored field means 'we do not know', which is not 'we are certain'."""
    doc = make_document(header={"quantity": _f("quantity", 100, None, "number")})

    assert min_confidence(doc) == 0.0
