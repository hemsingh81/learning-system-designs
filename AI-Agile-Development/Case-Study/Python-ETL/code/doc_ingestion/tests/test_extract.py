"""Tests for the Document Intelligence wrapper, with the Azure calls mocked.

Everything network-facing is replaced with a stub poller returning a recorded
response shape. Two things are being proved:

* the typed-union unwrapping is correct for every field type the models return;
* the document that comes out carries the provenance the completeness rules need
  — page numbers per field, and the pages the layout model saw tables on.

The second point is the extraction half of the NWD-142 fix. The rules engine can
only detect a dropped continuation page if this module records where the rows it
*did* read came from.
"""

from __future__ import annotations

import types
from datetime import date
from decimal import Decimal

import pytest

from config.settings import SourceConfig
from core import extract as extraction


@pytest.fixture
def alpha() -> SourceConfig:
    """Broker Alpha's mapping, restated locally so the test is self-contained."""
    return SourceConfig(
        key="broker_alpha",
        display_name="Broker Alpha",
        container="raw",
        prefix="broker_alpha/",
        model_id="broker-alpha-position-v3",
        doc_type="position_statement",
        field_map={
            "AccountNumber": "account_number",
            "StatementDate": "statement_date",
            "PositionCount": "declared_line_item_count",
            "Positions": "positions",
        },
        line_item_map={
            "SecurityId": "security_id",
            "SecurityName": "security_name",
            "Quantity": "quantity",
            "MarketValue": "market_value",
            "Currency": "currency",
        },
        line_item_count_field="declared_line_item_count",
    )


def _analyze_result(stub_field, *, fields, page_count: int, table_pages: list[int]):
    """Assemble the minimum of an ``AnalyzeResult`` that ``analyze`` reads."""
    document = types.SimpleNamespace(fields=fields)
    tables = [
        types.SimpleNamespace(
            bounding_regions=[types.SimpleNamespace(page_number=page)]
        )
        for page in table_pages
    ]
    return types.SimpleNamespace(
        documents=[document],
        pages=[types.SimpleNamespace(page_number=n) for n in range(1, page_count + 1)],
        tables=tables,
        as_dict=lambda: {"documents": ["<recorded response>"], "pageCount": page_count},
    )


def _install_client(monkeypatch, result) -> dict:
    """Replace the Document Intelligence client with a stub poller.

    Returns a dict the test can inspect to assert what the SDK was asked for.
    """
    seen: dict = {}

    class _Poller:
        def result(self):
            return result

    class _Client:
        def begin_analyze_document(self, model_id, request, **kwargs):
            seen["model_id"] = model_id
            seen["request"] = request
            return _Poller()

    monkeypatch.setattr(extraction, "doc_intel", lambda: _Client())
    return seen


def _line_row(stub_field, *, security_id, name, quantity, market_value, currency, page):
    """One element of the ``Positions`` array field."""
    return stub_field(
        "object",
        page=page,
        value_object={
            "SecurityId": stub_field(
                "string", value_string=security_id, confidence=0.97, page=page
            ),
            "SecurityName": stub_field("string", value_string=name, confidence=0.93, page=page),
            "Quantity": stub_field("number", value_number=quantity, confidence=0.95, page=page),
            "MarketValue": stub_field(
                "currency",
                value_currency=types.SimpleNamespace(
                    amount=market_value, currency_code=currency
                ),
                confidence=0.94,
                page=page,
            ),
            "Currency": stub_field("string", value_string=currency, confidence=0.99, page=page),
            # Not in line_item_map: must be dropped, not carried through.
            "InternalRef": stub_field("string", value_string="ignore-me", confidence=0.99),
        },
    )


@pytest.fixture
def alpha_fields(stub_field, stub_azure_sdk):
    """A two-page Broker Alpha statement with rows on both pages."""
    return {
        "AccountNumber": stub_field(
            "string", value_string="NWD-EQ-0042", confidence=0.99, page=1
        ),
        "StatementDate": stub_field(
            "date", value_date=date(2026, 7, 30), confidence=0.97, page=1
        ),
        "PositionCount": stub_field("integer", value_integer=2, confidence=0.98, page=1),
        "Positions": stub_field(
            "array",
            value_array=[
                _line_row(
                    stub_field,
                    security_id="US0378331005",
                    name="Apple Inc",
                    quantity=1250.0,
                    market_value=60250.5,
                    currency="USD",
                    page=1,
                ),
                _line_row(
                    stub_field,
                    security_id="US5949181045",
                    name="Microsoft Corp",
                    quantity=300.0,
                    market_value=123150.0,
                    currency="USD",
                    page=2,
                ),
            ],
        ),
    }


# -----------------------------------------------------------------------------
# Mapping
# -----------------------------------------------------------------------------


def test_header_and_line_items_are_mapped_to_canonical_names(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    seen = _install_client(monkeypatch, result)

    doc = extraction.analyze(b"%PDF-1.7 ...", alpha)

    assert seen["model_id"] == "broker-alpha-position-v3"
    assert set(doc.header) == {"account_number", "statement_date", "declared_line_item_count"}
    assert doc.header["account_number"].value == "NWD-EQ-0042"
    assert doc.header["statement_date"].value == date(2026, 7, 30)
    assert len(doc.line_items) == 2
    assert doc.line_items[0]["security_id"].value == "US0378331005"


def test_fields_outside_the_line_item_map_are_dropped(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    """The map is an allow-list. An unmapped column never reaches the schema."""
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert "InternalRef" not in doc.line_items[0]


def test_a_field_the_model_did_not_return_is_skipped_not_invented(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    """The gate turns the absence into a failure; extraction must not paper over it."""
    del alpha_fields["StatementDate"]
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert "statement_date" not in doc.header


def test_confidence_is_carried_through_untouched(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.header["account_number"].confidence == 0.99
    assert doc.line_items[1]["quantity"].confidence == 0.95


def test_no_documents_returned_is_an_error(
    monkeypatch, stub_field, stub_azure_sdk, alpha
) -> None:
    empty = types.SimpleNamespace(
        documents=[], pages=[], tables=[], as_dict=lambda: {}
    )
    _install_client(monkeypatch, empty)

    with pytest.raises(ValueError, match="returned no documents"):
        extraction.analyze(b"pdf", alpha)


# -----------------------------------------------------------------------------
# Typed-union unwrapping
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field_type", "kwargs", "expected"),
    [
        ("string", {"value_string": "Acme"}, "Acme"),
        ("countryRegion", {"value_string": "MEX"}, "MEX"),
        ("number", {"value_number": 1250.5}, 1250.5),
        ("integer", {"value_integer": 14}, 14),
        ("date", {"value_date": date(2026, 7, 30)}, date(2026, 7, 30)),
        ("selectionMark", {"value_selection_mark": "selected"}, "selected"),
        # Unknown types fall back to the raw content rather than returning None.
        ("somethingNew", {"content": "raw text"}, "raw text"),
    ],
)
def test_unwrap_handles_every_field_type(stub_field, field_type, kwargs, expected) -> None:
    field = stub_field(field_type, **kwargs)

    assert extraction._unwrap(field) == expected


def test_unwrap_keeps_both_halves_of_a_currency_field(stub_field) -> None:
    """The transform needs the amount; the rules engine needs the code."""
    field = stub_field(
        "currency",
        value_currency=types.SimpleNamespace(amount=60250.5, currency_code="USD"),
    )

    assert extraction._unwrap(field) == {"amount": 60250.5, "currency": "USD"}


def test_unwrap_of_an_absent_currency_is_none(stub_field) -> None:
    assert extraction._unwrap(stub_field("currency", value_currency=None)) is None


# -----------------------------------------------------------------------------
# Provenance — the extraction half of the NWD-142 fix
# -----------------------------------------------------------------------------


def test_page_numbers_are_recorded_per_field(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.line_items[0]["security_id"].page_number == 1
    assert doc.line_items[1]["security_id"].page_number == 2
    assert doc.line_item_pages() == [1, 2]


def test_table_pages_are_recorded_from_the_layout(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=3, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.table_pages == [1, 2]
    assert doc.page_count == 3


def test_a_dropped_continuation_page_is_visible_in_the_extracted_document(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    """NWD-142 as the extractor sees it.

    The model reports a table on pages 1 and 2, but the array field only yielded
    rows from page 1. Extraction records both facts faithfully and does not try
    to guess; ``core.rules.page_continuation`` is what turns the gap into an
    exception-queue item.
    """
    alpha_fields["Positions"].value_array = [alpha_fields["Positions"].value_array[0]]
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.table_pages == [1, 2]
    assert doc.line_item_pages() == [1]
    assert set(doc.table_pages) - set(doc.line_item_pages()) == {2}


def test_the_declared_line_item_count_is_parsed_from_the_header(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.declared_line_item_count == 2


def test_an_unparseable_declared_count_degrades_to_none(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    """A bad count must not crash ingestion; the rule abstains instead."""
    alpha_fields["PositionCount"] = stub_field(
        "string", value_string="fourteen", confidence=0.90, page=1
    )
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.declared_line_item_count is None


# -----------------------------------------------------------------------------
# Bronze
# -----------------------------------------------------------------------------


def test_the_raw_response_is_captured_for_bronze(
    monkeypatch, stub_field, stub_azure_sdk, alpha, alpha_fields
) -> None:
    """Bronze is written from this payload before a single field is parsed."""
    result = _analyze_result(stub_field, fields=alpha_fields, page_count=2, table_pages=[1, 2])
    _install_client(monkeypatch, result)

    doc = extraction.analyze(b"pdf", alpha)

    assert doc.raw_response == {"documents": ["<recorded response>"], "pageCount": 2}


def test_decimal_values_survive_the_currency_union(stub_field) -> None:
    """A counterparty that sends Decimal-typed amounts is not coerced to float."""
    field = stub_field(
        "currency",
        value_currency=types.SimpleNamespace(
            amount=Decimal("60250.5678"), currency_code="USD"
        ),
    )

    assert extraction._unwrap(field)["amount"] == Decimal("60250.5678")
