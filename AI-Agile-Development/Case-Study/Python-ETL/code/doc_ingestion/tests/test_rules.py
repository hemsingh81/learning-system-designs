"""Tests for the rules engine.

Like the gate, the rules engine is pure logic over dataclasses, so these tests
construct documents directly and assert on structured violations.

The block at the bottom is the important one. It covers NWD-142 — the Broker
Alpha statement whose positions table spanned a page boundary and silently lost
the page-2 line items. The confidence gate passed that document because every
field it *did* extract was high confidence. These are the tests that would have
caught it, and the reason the completeness rules exist.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from config.settings import ConfidenceConfig, RuleConfig, SourceConfig
from core import rules
from core.rules import NORMALISERS, VALIDATORS, RulesEngine
# conftest.py sits next to this file; pytest puts tests/ on sys.path.
from conftest import make_document, make_field as _f


def _source(rule_configs: list[RuleConfig], **overrides) -> SourceConfig:
    """A source carrying exactly the rules a test cares about."""
    base = dict(
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
        rules=rule_configs,
    )
    base.update(overrides)
    return SourceConfig(**base)


# -----------------------------------------------------------------------------
# Engine mechanics
# -----------------------------------------------------------------------------


def test_unknown_rule_type_fails_at_construction() -> None:
    """A typo in YAML must not silently remove a control from the pipeline."""
    source = _source([RuleConfig(id="oops", type="not_a_real_rule")])

    with pytest.raises(ValueError, match="Unknown rule type"):
        RulesEngine.for_source(source)


def test_applies_to_restricts_a_rule_to_one_document_type() -> None:
    """`applies_to` is how one default rule set serves several layouts."""
    source = _source(
        [
            RuleConfig(
                id="trades_only",
                type="min_line_items",
                applies_to=["trade_confirmation"],
                params={"minimum": 99},
            )
        ]
    )

    result = rules.evaluate(make_document(), source)

    assert result.passed  # doc_type is position_statement, so the rule sat out


def test_normalisation_does_not_mutate_the_input_document() -> None:
    """The engine returns a normalised copy; bronze-derived input stays as read."""
    source = _source([RuleConfig(id="trim", type="trim_whitespace", params={"fields": []})])
    doc = make_document(header={"security_name": _f("security_name", "  Acme  Corp ", 0.9)})

    result = rules.evaluate(doc, source)

    assert doc.header["security_name"].value == "  Acme  Corp "
    assert result.document.header["security_name"].value == "Acme Corp"


def test_warnings_do_not_block_the_load() -> None:
    """Warnings are recorded and logged; only errors send a document to a human."""
    source = _source(
        [
            RuleConfig(
                id="side_vocab",
                type="map_values",
                severity="warning",
                params={"scope": "line_item", "field": "side", "mapping": {"COMPRA": "BUY"}},
            ),
            RuleConfig(
                id="currency_known",
                type="allowed_values",
                severity="warning",
                params={"scope": "line_item", "field": "currency", "values": ["USD"]},
            ),
        ]
    )
    doc = make_document(line_items=[{"currency": _f("currency", "XXX", 0.99)}])

    result = rules.evaluate(doc, source)

    assert result.passed
    assert not result.straight_through
    assert len(result.warnings) == 1


# -----------------------------------------------------------------------------
# Normalisation
# -----------------------------------------------------------------------------


def test_trim_whitespace_collapses_ocr_noise() -> None:
    source = _source([RuleConfig(id="trim", type="trim_whitespace", params={"fields": []})])
    doc = make_document(header={"security_name": _f("security_name", " ACME\n  CORP ", 0.9)})

    result = rules.evaluate(doc, source)

    assert result.document.header["security_name"].value == "ACME CORP"
    assert result.normalisations[0].before == " ACME\n  CORP "
    assert result.normalisations[0].after == "ACME CORP"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,234.56", "1234.56"),      # Anglo-American: Broker Alpha
        ("1.234,56", "1234.56"),      # European: Broker Beta EM
        ("1 234,56", "1234.56"),      # space-grouped
        ("1234.56", "1234.56"),       # already clean
    ],
)
def test_strip_thousands_separators_handles_both_conventions(raw: str, expected: str) -> None:
    """Deciding by the LAST separator is the only reading that works for both."""
    source = _source(
        [
            RuleConfig(
                id="strip",
                type="strip_thousands_separators",
                params={"scope": "line_item", "fields": ["market_value"]},
            )
        ]
    )
    doc = make_document(line_items=[{"market_value": _f("market_value", raw, 0.95)}])

    result = rules.evaluate(doc, source)

    assert result.document.line_items[0]["market_value"].value == expected


def test_map_values_normalises_spanish_trade_direction() -> None:
    """Broker Beta send COMPRA / VENTA; downstream reasons about BUY / SELL."""
    source = _source(
        [
            RuleConfig(
                id="side_vocab",
                type="map_values",
                severity="warning",
                params={
                    "scope": "line_item",
                    "field": "side",
                    "mapping": {"COMPRA": "BUY", "VENTA": "SELL"},
                },
            )
        ]
    )
    doc = make_document(line_items=[{"side": _f("side", "Compra", 0.95)}])

    result = rules.evaluate(doc, source)

    assert result.document.line_items[0]["side"].value == "BUY"


def test_normalisation_runs_before_validation() -> None:
    """Otherwise every validator has to re-implement the counterparty's vocabulary.

    ``allowed_values`` knows nothing about Spanish. It only passes here because
    ``map_values`` rewrote COMPRA to BUY first — and it does so even though the
    validator is declared ahead of the normaliser in the rule list, because the
    two phases are separate.
    """
    source = _source(
        [
            RuleConfig(
                id="side_known",
                type="allowed_values",
                params={"scope": "line_item", "field": "side", "values": ["BUY", "SELL"]},
            ),
            RuleConfig(
                id="side_vocab",
                type="map_values",
                params={
                    "scope": "line_item",
                    "field": "side",
                    "mapping": {"COMPRA": "BUY", "VENTA": "SELL"},
                },
            ),
        ]
    )
    doc = make_document(line_items=[{"side": _f("side", "COMPRA", 0.99)}])

    result = rules.evaluate(doc, source)

    assert result.passed
    assert result.document.line_items[0]["side"].value == "BUY"


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------


def test_confidence_gate_is_folded_into_the_rules_engine() -> None:
    """The gate keeps its own module; this adapter is the only place both meet."""
    source = _source([RuleConfig(id="confidence_gate", type="confidence_gate")])
    doc = make_document(header={"market_value": _f("market_value", 100, 0.85, "currency")})

    result = rules.evaluate(doc, source)

    assert not result.passed
    violation = result.errors[0]
    assert violation.rule_type == "confidence_gate"
    assert violation.field == "market_value"
    assert violation.observed == 0.85
    assert violation.expected == 0.90


def test_required_line_item_field_reports_the_row() -> None:
    source = _source(
        [
            RuleConfig(
                id="line_required",
                type="required_fields",
                params={"scope": "line_item", "fields": ["security_id"]},
            )
        ]
    )
    doc = make_document(
        line_items=[
            {"security_id": _f("security_id", "US0378331005", 0.99)},
            {"security_id": _f("security_id", "   ", 0.99)},
        ]
    )

    result = rules.evaluate(doc, source)

    assert not result.passed
    assert result.errors[0].row == 1
    assert result.errors[0].field == "security_id"


def test_numeric_range_catches_a_shifted_decimal_point() -> None:
    """A quantity read as 1,250,000 instead of 1,250 is high confidence and wrong."""
    source = _source(
        [
            RuleConfig(
                id="quantity_sane",
                type="numeric_range",
                params={"scope": "line_item", "field": "quantity", "min": 0, "max": 100000},
            )
        ]
    )
    doc = make_document(line_items=[{"quantity": _f("quantity", 1_250_000, 0.99, "number")}])

    result = rules.evaluate(doc, source)

    assert not result.passed
    assert result.errors[0].rule_type == "numeric_range"


def test_allowed_values_rejects_an_unknown_currency() -> None:
    source = _source(
        [
            RuleConfig(
                id="currency_known",
                type="allowed_values",
                params={
                    "scope": "line_item",
                    "field": "currency",
                    "values": ["USD", "EUR"],
                    "allow_missing": True,
                },
            )
        ]
    )
    doc = make_document(
        line_items=[
            {"currency": _f("currency", "usd", 0.99)},   # case-insensitive: fine
            {},                                          # absent: allowed
            {"currency": _f("currency", "XYZ", 0.99)},   # unknown: rejected
        ]
    )

    result = rules.evaluate(doc, source)

    assert [v.row for v in result.errors] == [2]


def test_future_statement_date_is_rejected() -> None:
    """A statement dated next year is a misread year, every time."""
    source = _source(
        [
            RuleConfig(
                id="no_future_dates",
                type="date_not_future",
                params={"scope": "header", "fields": ["statement_date"], "grace_days": 1},
            )
        ]
    )
    doc = make_document(
        header={"statement_date": _f("statement_date", "2099-01-31", 0.99, "date")}
    )

    result = rules.evaluate(doc, source)

    assert not result.passed
    assert result.errors[0].rule_type == "date_not_future"


def test_settlement_may_not_precede_trade() -> None:
    source = _source(
        [
            RuleConfig(
                id="settlement_after_trade",
                type="date_order",
                params={"scope": "header", "earlier": "trade_date", "later": "settlement_date"},
            )
        ]
    )
    doc = make_document(
        header={
            "trade_date": _f("trade_date", "2026-07-30", 0.99, "date"),
            "settlement_date": _f("settlement_date", "2026-07-28", 0.99, "date"),
        }
    )

    assert not rules.evaluate(doc, source).passed


def test_quantity_times_price_must_reconcile_to_market_value() -> None:
    """Arithmetic the document proves about itself — the cheapest check there is."""
    source = _source(
        [
            RuleConfig(
                id="value_consistency",
                type="cross_field_product",
                params={
                    "scope": "line_item",
                    "left": "quantity",
                    "right": "price",
                    "product": "market_value",
                    "tolerance_pct": 0.005,
                },
            )
        ]
    )
    doc = make_document(
        line_items=[
            {   # 1250 x 48.20 = 60,250 — the statement says 62,050. Digits swapped.
                "quantity": _f("quantity", "1250", 0.99, "number"),
                "price": _f("price", "48.20", 0.99, "number"),
                "market_value": _f("market_value", "62050.00", 0.99, "currency"),
            }
        ]
    )

    result = rules.evaluate(doc, source)

    assert not result.passed
    assert result.errors[0].expected == Decimal("60250.00")
    assert result.errors[0].observed == Decimal("62050.00")


def test_cross_field_product_tolerates_rounding_within_50bps() -> None:
    source = _source(
        [
            RuleConfig(
                id="value_consistency",
                type="cross_field_product",
                params={
                    "scope": "line_item",
                    "left": "quantity",
                    "right": "price",
                    "product": "market_value",
                    "tolerance_pct": 0.005,
                },
            )
        ]
    )
    doc = make_document(
        line_items=[
            {
                "quantity": _f("quantity", "1250", 0.99, "number"),
                "price": _f("price", "48.20", 0.99, "number"),
                "market_value": _f("market_value", "60251.00", 0.99, "currency"),
            }
        ]
    )

    assert rules.evaluate(doc, source).passed


def test_a_statement_with_no_line_items_is_never_correct() -> None:
    source = _source([RuleConfig(id="at_least_one_line", type="min_line_items")])

    result = rules.evaluate(make_document(), source)

    assert not result.passed
    assert result.errors[0].rule_type == "min_line_items"


# -----------------------------------------------------------------------------
# NWD-142 — the completeness rules
#
# Divya's bug: a Broker Alpha statement whose positions table spanned a page
# boundary loaded with the page-2 line items missing. Every field that WAS
# extracted scored high, so the confidence gate passed it, and reconciliation
# reported MISSING_EXTERNAL breaks that looked like real settlement failures.
# -----------------------------------------------------------------------------


def test_declared_count_mismatch_is_caught(completeness_source: SourceConfig) -> None:
    """The exact NWD-142 shape: 14 positions declared, 8 extracted."""
    doc = make_document(
        header={"declared_line_item_count": _f("declared_line_item_count", 14, 0.99, "integer")},
        line_items=[{"quantity": _f("quantity", i, 0.99, "number")} for i in range(8)],
        page_count=2,
        declared_line_item_count=14,
    )

    result = rules.evaluate(doc, completeness_source)

    assert not result.passed
    violation = next(v for v in result.errors if v.rule_type == "line_item_count")
    assert violation.expected == 14
    assert violation.observed == 8


def test_declared_count_matching_passes(completeness_source: SourceConfig) -> None:
    doc = make_document(
        line_items=[{"quantity": _f("quantity", i, 0.99, "number")} for i in range(3)],
        declared_line_item_count=3,
    )

    assert rules.evaluate(doc, completeness_source).passed


def test_line_item_count_abstains_when_the_layout_declares_none(
    completeness_source: SourceConfig,
) -> None:
    """Not every counterparty states a count — page_continuation covers those."""
    doc = make_document(
        line_items=[{"quantity": _f("quantity", 1, 0.99, "number")}],
        declared_line_item_count=None,
    )

    assert rules.evaluate(doc, completeness_source).passed


def test_page_continuation_detects_a_dropped_second_page(
    completeness_source: SourceConfig,
) -> None:
    """The layout model saw a table on page 2; no line item came from page 2."""
    doc = make_document(
        line_items=[
            {"quantity": _f("quantity", 100, 0.99, "number", page_number=1)},
            {"quantity": _f("quantity", 200, 0.99, "number", page_number=1)},
        ],
        page_count=2,
        table_pages=[1, 2],
    )

    result = rules.evaluate(doc, completeness_source)

    assert not result.passed
    violation = next(v for v in result.errors if v.rule_type == "page_continuation")
    assert violation.observed == [1]
    assert violation.expected == [1, 2]
    assert "page(s) [2]" in violation.message


def test_page_continuation_passes_when_every_table_page_contributed(
    completeness_source: SourceConfig,
) -> None:
    doc = make_document(
        line_items=[
            {"quantity": _f("quantity", 100, 0.99, "number", page_number=1)},
            {"quantity": _f("quantity", 200, 0.99, "number", page_number=2)},
        ],
        page_count=2,
        table_pages=[1, 2],
    )

    assert rules.evaluate(doc, completeness_source).passed


def test_page_continuation_abstains_without_table_regions(
    completeness_source: SourceConfig,
) -> None:
    """Absence of evidence is not evidence of completeness — do not fail healthy docs."""
    doc = make_document(
        line_items=[{"quantity": _f("quantity", 100, 0.99, "number", page_number=1)}],
        page_count=3,
        table_pages=[],
    )

    assert rules.evaluate(doc, completeness_source).passed


def test_page_continuation_ignores_single_page_documents(
    completeness_source: SourceConfig,
) -> None:
    doc = make_document(
        line_items=[{"quantity": _f("quantity", 100, 0.99, "number", page_number=1)}],
        page_count=1,
        table_pages=[1],
    )

    assert rules.evaluate(doc, completeness_source).passed


def test_the_gate_alone_would_have_missed_nwd_142(
    completeness_source: SourceConfig, source: SourceConfig
) -> None:
    """The teaching point, asserted.

    The same document passes the confidence gate and fails the completeness
    rules. Confidence is a statement about the values you have; it says nothing
    about the values you do not.
    """
    from core.confidence import evaluate as gate

    doc = make_document(
        header={"account_number": _f("account_number", "ACC-1", 0.99)},
        line_items=[{"quantity": _f("quantity", 100, 0.99, "number", page_number=1)}],
        page_count=2,
        table_pages=[1, 2],
        declared_line_item_count=9,
    )

    assert gate(doc, source).passed
    assert not rules.evaluate(doc, completeness_source).passed


# -----------------------------------------------------------------------------
# The shipped configuration
# -----------------------------------------------------------------------------


def test_every_configured_rule_type_is_implemented(settings) -> None:
    """Configuration is code here. A typo in sources.yaml fails the suite."""
    known = set(NORMALISERS) | set(VALIDATORS)
    for source_config in settings.sources.values():
        configured = {rule.type for rule in source_config.all_rules}
        assert configured <= known, f"{source_config.key}: {configured - known}"


def test_shipped_sources_build_a_working_engine(settings) -> None:
    for source_config in settings.sources.values():
        assert RulesEngine.for_source(source_config).rules


def test_broker_alpha_overrides_the_currency_threshold(broker_alpha: SourceConfig) -> None:
    """0.92 rather than 0.90 — their scan quality is weaker, so gate them harder."""
    assert broker_alpha.confidence.threshold_for("currency") == 0.92
    assert broker_alpha.confidence.threshold_for("number") == 0.90
