"""Tests for the canonical schema mapping.

Three properties are asserted here over and over, because they are the ones that
cost money when they break: money and quantity are ``Decimal``, timestamps are
timezone-aware UTC, and every row carries the audit trio (``content_hash``,
``bronze_path``, ``min_confidence``).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from config.settings import SourceConfig
from core.transform import COLUMNS, CounterpartyPosition, TransformError, to_positions
# conftest.py sits next to this file; pytest puts tests/ on sys.path.
from conftest import make_document, make_field as _f

BRONZE = "bronze/broker_alpha/2026/07/31/abc.json"
BLOB = "raw/broker_alpha/2026-07-31/statement.pdf"
DIGEST = "a" * 64


@pytest.fixture
def statement_source() -> SourceConfig:
    return SourceConfig(
        key="broker_alpha",
        display_name="Broker Alpha",
        container="raw",
        prefix="broker_alpha/",
        model_id="broker-alpha-position-v3",
        doc_type="position_statement",
    )


@pytest.fixture
def confirm_source() -> SourceConfig:
    return SourceConfig(
        key="broker_beta_em",
        display_name="Broker Beta EM",
        container="raw",
        prefix="broker_beta/",
        model_id="broker-beta-confirm-v1",
        doc_type="trade_confirmation",
        language="es",
        translate_to="en",
    )


def _statement_document():
    return make_document(
        header={
            "account_number": _f("account_number", "NWD-EQ-0042", 0.99),
            "statement_date": _f("statement_date", date(2026, 7, 30), 0.97, "date"),
        },
        line_items=[
            {
                "security_id": _f("security_id", "US0378331005", 0.96),
                "security_name": _f("security_name", "Apple Inc", 0.93),
                "quantity": _f("quantity", "1250.12345678", 0.95, "number"),
                "price": _f("price", "48.20", 0.94, "number"),
                "market_value": _f("market_value", "60250.5678", 0.92, "currency"),
                "currency": _f("currency", "usd", 0.99),
            },
            {
                "security_id": _f("security_id", "US5949181045", 0.96),
                "security_name": _f("security_name", "Microsoft Corp", 0.91),
                "quantity": _f("quantity", 300, 0.95, "number"),
                "price": _f("price", 410.5, 0.94, "number"),
                "market_value": _f("market_value", 123150.0, 0.92, "currency"),
                "currency": _f("currency", "USD", 0.99),
            },
        ],
        model_id="broker-alpha-position-v3",
        page_count=2,
    )


def _rows(source: SourceConfig, doc=None) -> list[CounterpartyPosition]:
    return to_positions(
        doc if doc is not None else _statement_document(),
        source,
        content_hash=DIGEST,
        bronze_path=BRONZE,
        blob_path=BLOB,
    )


# -----------------------------------------------------------------------------
# Schema mapping
# -----------------------------------------------------------------------------


def test_one_row_per_line_item(statement_source: SourceConfig) -> None:
    rows = _rows(statement_source)

    assert len(rows) == 2
    assert [row.line_no for row in rows] == [1, 2]
    assert [row.security_id for row in rows] == ["US0378331005", "US5949181045"]


def test_header_fields_are_copied_onto_every_row(statement_source: SourceConfig) -> None:
    """The statement's header is denormalised onto each position deliberately.

    Reconciliation joins at position grain; a row that cannot state its own
    account number is not reconcilable.
    """
    rows = _rows(statement_source)

    assert all(row.account_number == "NWD-EQ-0042" for row in rows)
    assert all(row.statement_date == date(2026, 7, 30) for row in rows)
    assert all(row.source_key == "broker_alpha" for row in rows)
    assert all(row.doc_type == "position_statement" for row in rows)
    assert all(row.model_id == "broker-alpha-position-v3" for row in rows)


def test_as_tuple_follows_the_canonical_column_order(statement_source: SourceConfig) -> None:
    """The sinks build parameterised statements from COLUMNS; order must agree."""
    row = _rows(statement_source)[0]
    values = row.as_tuple()

    assert len(values) == len(COLUMNS)
    assert values[COLUMNS.index("content_hash")] == DIGEST
    assert values[COLUMNS.index("security_id")] == "US0378331005"
    assert values[COLUMNS.index("line_no")] == 1


def test_currency_codes_are_upper_case_and_three_characters(
    statement_source: SourceConfig,
) -> None:
    assert [row.currency for row in _rows(statement_source)] == ["USD", "USD"]


def test_a_trade_confirmation_anchors_on_trade_date(confirm_source: SourceConfig) -> None:
    """Both document types land in one table, so both must populate the key date."""
    doc = make_document(
        header={
            "account_number": _f("account_number", "NWD-EM-0007", 0.99),
            "trade_date": _f("trade_date", date(2026, 7, 29), 0.97, "date"),
            "settlement_date": _f("settlement_date", date(2026, 7, 31), 0.97, "date"),
        },
        line_items=[
            {
                "security_id": _f("security_id", "BONO-MX-2031", 0.96),
                "quantity": _f("quantity", "5000", 0.95, "number"),
                "price": _f("price", "99.8125", 0.95, "number"),
                "side": _f("side", "BUY", 0.98),
                "currency": _f("currency", "MXN", 0.99),
            }
        ],
        model_id="broker-beta-confirm-v1",
    )

    row = _rows(confirm_source, doc)[0]

    assert row.statement_date == date(2026, 7, 29)
    assert row.trade_date == date(2026, 7, 29)
    assert row.settlement_date == date(2026, 7, 31)
    assert row.side == "BUY"
    assert row.market_value is None


def test_currency_union_is_unwrapped_to_its_amount(statement_source: SourceConfig) -> None:
    """Document Intelligence returns {'amount', 'currency'} for currency fields."""
    doc = make_document(
        header={
            "account_number": _f("account_number", "NWD-EQ-0042", 0.99),
            "statement_date": _f("statement_date", date(2026, 7, 30), 0.97, "date"),
        },
        line_items=[
            {
                "security_id": _f("security_id", "US0378331005", 0.96),
                "quantity": _f("quantity", 100, 0.95, "number"),
                "market_value": _f(
                    "market_value", {"amount": 60250.5, "currency": "USD"}, 0.92, "currency"
                ),
                "currency": _f(
                    "currency", {"amount": 60250.5, "currency": "eur"}, 0.92, "currency"
                ),
            }
        ],
    )

    row = _rows(statement_source, doc)[0]

    assert row.market_value == Decimal("60250.5000")
    assert row.currency == "EUR"


# -----------------------------------------------------------------------------
# Decimal precision
# -----------------------------------------------------------------------------


def test_money_and_quantity_are_decimal_never_float(statement_source: SourceConfig) -> None:
    row = _rows(statement_source)[0]

    for value in (row.quantity, row.price, row.market_value, row.min_confidence):
        assert isinstance(value, Decimal)
        assert not isinstance(value, float)


def test_quantity_keeps_eight_decimal_places(statement_source: SourceConfig) -> None:
    """EM funds deal in fractional units; rounding earlier throws away a position."""
    row = _rows(statement_source)[0]

    assert row.quantity == Decimal("1250.12345678")
    assert row.quantity.as_tuple().exponent == -8


def test_money_is_quantised_to_four_places(statement_source: SourceConfig) -> None:
    row = _rows(statement_source)[0]

    assert row.market_value == Decimal("60250.5678")
    assert row.market_value.as_tuple().exponent == -4


def test_float_input_does_not_carry_binary_noise(statement_source: SourceConfig) -> None:
    """Conversion goes via str(), so 410.5 stays 410.5 rather than 410.50000000001."""
    row = _rows(statement_source)[1]

    assert row.price == Decimal("410.5")
    assert row.quantity == Decimal("300")


def test_a_non_numeric_quantity_is_refused(statement_source: SourceConfig) -> None:
    doc = make_document(
        header={
            "account_number": _f("account_number", "A", 0.99),
            "statement_date": _f("statement_date", date(2026, 7, 30), 0.99, "date"),
        },
        line_items=[
            {
                "security_id": _f("security_id", "X", 0.99),
                "quantity": _f("quantity", "not a number", 0.99, "number"),
            }
        ],
    )

    with pytest.raises(TransformError, match="quantity"):
        _rows(statement_source, doc)


# -----------------------------------------------------------------------------
# Timezone handling
# -----------------------------------------------------------------------------


def test_extracted_utc_is_timezone_aware_utc(statement_source: SourceConfig) -> None:
    """Northwind runs London and Los Angeles. A naive timestamp is an argument."""
    row = _rows(statement_source)[0]

    assert row.extracted_utc.tzinfo is not None
    assert row.extracted_utc.utcoffset() == timezone.utc.utcoffset(None)


def test_an_aware_timestamp_is_converted_to_utc(statement_source: SourceConfig) -> None:
    from datetime import timedelta

    los_angeles = timezone(timedelta(hours=-7))
    supplied = datetime(2026, 7, 30, 17, 0, 0, tzinfo=los_angeles)

    rows = to_positions(
        _statement_document(),
        statement_source,
        content_hash=DIGEST,
        bronze_path=BRONZE,
        blob_path=BLOB,
        extracted_utc=supplied,
    )

    assert rows[0].extracted_utc == datetime(2026, 7, 31, 0, 0, 0, tzinfo=timezone.utc)


def test_a_naive_timestamp_is_refused(statement_source: SourceConfig) -> None:
    with pytest.raises(TransformError, match="timezone-aware"):
        to_positions(
            _statement_document(),
            statement_source,
            content_hash=DIGEST,
            bronze_path=BRONZE,
            blob_path=BLOB,
            extracted_utc=datetime(2026, 7, 30, 12, 0, 0),
        )


# -----------------------------------------------------------------------------
# The audit story
# -----------------------------------------------------------------------------


def test_every_row_carries_the_audit_trio(statement_source: SourceConfig) -> None:
    """content_hash + bronze_path + min_confidence. Do not drop these."""
    for row in _rows(statement_source):
        assert row.content_hash == DIGEST
        assert row.bronze_path == BRONZE
        assert row.blob_path == BLOB
        assert row.min_confidence == Decimal("0.91")


def test_min_confidence_is_document_wide_not_per_row(statement_source: SourceConfig) -> None:
    """A document is accepted or rejected as a unit, so its weakest field governs."""
    rows = _rows(statement_source)

    assert len({row.min_confidence for row in rows}) == 1


def test_a_document_without_an_account_number_is_refused(
    statement_source: SourceConfig,
) -> None:
    doc = make_document(
        header={"statement_date": _f("statement_date", date(2026, 7, 30), 0.99, "date")},
        line_items=[
            {
                "security_id": _f("security_id", "X", 0.99),
                "quantity": _f("quantity", 1, 0.99, "number"),
            }
        ],
    )

    with pytest.raises(TransformError, match="account_number"):
        _rows(statement_source, doc)


def test_a_document_without_an_as_of_date_is_refused(statement_source: SourceConfig) -> None:
    doc = make_document(
        header={"account_number": _f("account_number", "A", 0.99)},
        line_items=[
            {
                "security_id": _f("security_id", "X", 0.99),
                "quantity": _f("quantity", 1, 0.99, "number"),
            }
        ],
    )

    with pytest.raises(TransformError, match="as-of date"):
        _rows(statement_source, doc)
