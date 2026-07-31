"""Tests for the reconciliation engine.

Four break classes and two tolerances. The tolerances are the interesting part:
they exist so the report contains disagreements a human should look at, and not
the arithmetic noise of two systems exporting the same number through different
float paths.

The last test in this file is the one that connects the whole case study
together — it shows that a break caused by a bad extraction is indistinguishable
from a break caused by a genuine settlement failure, which is precisely why the
confidence gate and the completeness rules have to sit upstream of here.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from recon.reconcile import (
    MISSING_EXTERNAL,
    MISSING_INTERNAL,
    MV_TOLERANCE_PCT,
    QTY_TOLERANCE,
    QUANTITY_BREAK,
    VALUE_BREAK,
    reconcile,
    summarise,
)

AS_OF = date(2026, 7, 30)


def _frame(rows: list[dict], *, audit: bool = False) -> pd.DataFrame:
    columns = ["account_number", "security_id", "quantity", "market_value", "currency"]
    if audit:
        columns += ["content_hash", "bronze_path", "min_confidence"]
    return pd.DataFrame(rows, columns=columns, dtype=object)


def _position(
    security_id: str,
    quantity: str,
    market_value: str,
    *,
    account: str = "NWD-EQ-0042",
    **audit,
) -> dict:
    return {
        "account_number": account,
        "security_id": security_id,
        "quantity": Decimal(quantity),
        "market_value": Decimal(market_value),
        "currency": "USD",
        **audit,
    }


# -----------------------------------------------------------------------------
# The four break classes
# -----------------------------------------------------------------------------


def test_missing_external_when_aladdin_holds_it_and_the_statement_does_not() -> None:
    """Either a settlement failure — or a position we failed to extract."""
    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [MISSING_EXTERNAL]
    assert breaks.iloc[0]["security_id"] == "US0378331005"
    assert breaks.iloc[0]["difference"] == Decimal("1250")


def test_missing_internal_when_the_statement_holds_it_and_aladdin_does_not() -> None:
    """Usually an unbooked trade."""
    internal = _frame([])
    external = _frame([_position("BONO-MX-2031", "5000", "499062.50")])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [MISSING_INTERNAL]
    assert breaks.iloc[0]["difference"] == Decimal("-5000")


def test_quantity_break_when_the_two_sides_disagree() -> None:
    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([_position("US0378331005", "1200", "57840.00")])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [QUANTITY_BREAK]
    assert breaks.iloc[0]["difference"] == Decimal("50")


def test_value_break_when_quantities_agree_but_values_do_not() -> None:
    """Same holding, materially different valuation."""
    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([_position("US0378331005", "1250", "62050.00")])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [VALUE_BREAK]
    assert breaks.iloc[0]["difference"] == Decimal("-1800.00")


# -----------------------------------------------------------------------------
# Tolerances
# -----------------------------------------------------------------------------


def test_quantity_noise_inside_the_tolerance_is_not_a_break() -> None:
    """0.0001 is somebody's export precision, not a position discrepancy."""
    assert QTY_TOLERANCE == Decimal("0.0001")

    internal = _frame([_position("US0378331005", "1250.00005", "60250.00")])
    external = _frame([_position("US0378331005", "1250.00000", "60250.00")])

    assert reconcile(internal, external, AS_OF).empty


def test_quantity_difference_just_past_the_tolerance_is_a_break() -> None:
    internal = _frame([_position("US0378331005", "1250.0002", "60250.00")])
    external = _frame([_position("US0378331005", "1250.0000", "60250.00")])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [QUANTITY_BREAK]


def test_value_difference_inside_50bps_is_a_pricing_source_difference() -> None:
    """Aladdin and the counterparty price from different sources at different times."""
    assert MV_TOLERANCE_PCT == Decimal("0.005")

    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([_position("US0378331005", "1250", "60400.00")])  # ~25bps

    assert reconcile(internal, external, AS_OF).empty


def test_value_difference_beyond_50bps_is_a_break() -> None:
    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([_position("US0378331005", "1250", "60700.00")])  # ~75bps

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [VALUE_BREAK]


def test_quantity_is_classified_before_value() -> None:
    """When the quantity is wrong the value is wrong as a consequence.

    Reporting both would double-count one underlying problem in the queue.
    """
    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([_position("US0378331005", "600", "28920.00")])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [QUANTITY_BREAK]


# -----------------------------------------------------------------------------
# Output shape
# -----------------------------------------------------------------------------


def test_matched_rows_are_not_in_the_report() -> None:
    """An analyst works a break list, not a holdings list."""
    internal = _frame(
        [
            _position("US0378331005", "1250", "60250.00"),
            _position("US5949181045", "300", "123150.00"),
        ]
    )
    external = _frame(
        [
            _position("US0378331005", "1250", "60250.00"),
            _position("US5949181045", "300", "123150.00"),
        ]
    )

    assert reconcile(internal, external, AS_OF).empty


def test_every_break_row_carries_the_as_of_date() -> None:
    internal = _frame([_position("US0378331005", "1250", "60250.00")])
    external = _frame([])

    breaks = reconcile(internal, external, AS_OF)

    assert set(breaks["as_of_date"]) == {AS_OF}


def test_audit_columns_survive_the_join() -> None:
    """min_confidence and bronze_path on a break row answer 'was this us?'."""
    internal = _frame([])
    external = _frame(
        [
            _position(
                "US0378331005",
                "1250",
                "60250.00",
                content_hash="a" * 64,
                bronze_path="bronze/broker_alpha/2026/07/30/a.json",
                min_confidence=Decimal("0.93"),
            )
        ],
        audit=True,
    )

    breaks = reconcile(internal, external, AS_OF)

    assert breaks.iloc[0]["bronze_path"] == "bronze/broker_alpha/2026/07/30/a.json"
    assert breaks.iloc[0]["min_confidence"] == Decimal("0.93")


def test_summarise_counts_every_class_including_the_zeroes() -> None:
    """The daily report needs a zero, not a missing key, when a class is clean."""
    internal = _frame(
        [
            _position("US0378331005", "1250", "60250.00"),
            _position("US5949181045", "300", "123150.00"),
        ]
    )
    external = _frame([_position("US0378331005", "1200", "57840.00")])

    counts = summarise(reconcile(internal, external, AS_OF))

    assert counts == {
        MISSING_EXTERNAL: 1,
        MISSING_INTERNAL: 0,
        QUANTITY_BREAK: 1,
        VALUE_BREAK: 0,
    }


def test_summarise_of_an_empty_report_is_all_zeroes() -> None:
    assert summarise(pd.DataFrame()) == {
        MISSING_EXTERNAL: 0,
        MISSING_INTERNAL: 0,
        QUANTITY_BREAK: 0,
        VALUE_BREAK: 0,
    }


def test_two_empty_feeds_produce_an_empty_report() -> None:
    assert reconcile(_frame([]), _frame([]), AS_OF).empty


# -----------------------------------------------------------------------------
# Why the gate sits upstream — NWD-142 seen from the other end
# -----------------------------------------------------------------------------


def test_dropped_line_items_are_indistinguishable_from_a_settlement_failure() -> None:
    """The point of the whole design, asserted in one test.

    Here Broker Alpha's statement genuinely lost its page-2 positions (NWD-142)
    while an unrelated security genuinely failed to settle. Reconciliation
    reports both as MISSING_EXTERNAL and cannot tell them apart — nothing in this
    output distinguishes 'we mis-extracted' from 'the trade did not settle'.

    That is why correctness has to be enforced upstream: by the confidence gate
    for values that are present, and by the completeness rules for values that
    are not.
    """
    internal = _frame(
        [
            _position("US0378331005", "1250", "60250.00"),   # extracted fine
            _position("US5949181045", "300", "123150.00"),   # lost on page 2
            _position("US88160R1014", "80", "20000.00"),     # genuinely unsettled
        ]
    )
    external = _frame([_position("US0378331005", "1250", "60250.00")])

    breaks = reconcile(internal, external, AS_OF)

    assert list(breaks["break_type"]) == [MISSING_EXTERNAL, MISSING_EXTERNAL]
    assert set(breaks["security_id"]) == {"US5949181045", "US88160R1014"}
    # Nothing in the report tells the two causes apart.
    assert breaks["break_type"].nunique() == 1


@pytest.mark.parametrize("empty_side", ["internal", "external"])
def test_a_one_sided_feed_still_produces_a_usable_report(empty_side: str) -> None:
    """A counterparty that sends nothing must not silently reconcile clean."""
    holding = _frame([_position("US0378331005", "1250", "60250.00")])
    empty = _frame([])

    internal, external = (empty, holding) if empty_side == "internal" else (holding, empty)
    breaks = reconcile(internal, external, AS_OF)

    assert len(breaks) == 1
