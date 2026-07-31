"""Reconcile counterparty positions against the Aladdin feed.

This is the control the whole pipeline exists to serve. Two sets of books —
internal (Aladdin) and external (the counterparty statements this package
extracts) — are joined on their natural key and every disagreement is
classified. A disagreement is a **break**, and breaks cost real money:
unclaimed dividends, failed settlements, wrong NAV, audit findings.

Four break classes, and the distinction between them is what an operations
analyst acts on:

``MISSING_EXTERNAL``
    Aladdin holds the position; the counterparty statement does not. Either a
    genuine settlement failure, or — and this is the trap — a position we failed
    to extract. NWD-142 produced exactly this signature, which is why the
    completeness rules in :mod:`core.rules` exist.
``MISSING_INTERNAL``
    The statement holds it; Aladdin does not. Usually an unbooked trade.
``QUANTITY_BREAK``
    Both hold it, the quantities disagree beyond ``QTY_TOLERANCE``.
``VALUE_BREAK``
    Both hold it in the same quantity, but market values disagree by more than
    ``MV_TOLERANCE_PCT``. Usually a pricing source difference rather than an
    error, which is why the tolerance is 50 basis points rather than zero.

**The confidence gate has to sit upstream of this.** A break caused by a bad
extraction and a break caused by a genuine settlement failure look identical in
this output. If low-confidence rows flowed through, the report would fill with
false positives, operations would stop trusting it, and the control would be
worse than the manual process it replaced.

Arithmetic is ``Decimal`` throughout. A 0.0001 quantity tolerance is smaller
than the noise binary floating point introduces on a large position, so a float
comparison would manufacture breaks that do not exist.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

log = logging.getLogger(__name__)

# Below this, a quantity difference is float noise from somebody's export, not a
# real break.
QTY_TOLERANCE = Decimal("0.0001")
# 50 basis points. Aladdin and the counterparty price from different sources at
# different times of day; inside half a percent is agreement, not a discrepancy.
MV_TOLERANCE_PCT = Decimal("0.005")

MATCHED = "MATCHED"
MISSING_EXTERNAL = "MISSING_EXTERNAL"
MISSING_INTERNAL = "MISSING_INTERNAL"
QUANTITY_BREAK = "QUANTITY_BREAK"
VALUE_BREAK = "VALUE_BREAK"

BREAK_TYPES: tuple[str, ...] = (
    MISSING_EXTERNAL,
    MISSING_INTERNAL,
    QUANTITY_BREAK,
    VALUE_BREAK,
)

# The natural key. Account plus security is the grain a position is held at; the
# as-of date is a parameter of the run, not part of the join.
KEY: tuple[str, ...] = ("account_number", "security_id")

# Columns carried onto every break row so the report is actionable without a
# second query. The audit trio (content_hash, bronze_path, min_confidence) comes
# from the counterparty side and is optional — Aladdin-only breaks have none.
_AUDIT_COLUMNS: tuple[str, ...] = ("content_hash", "bronze_path", "min_confidence")


def _dec(value: Any) -> Decimal:
    """Coerce to ``Decimal``, treating absent or unreadable values as zero.

    Zero is the honest default here: on a matched key, a missing quantity means
    one side is asserting nothing where the other asserts something, and that
    difference should surface as a break rather than be quietly skipped.
    """
    if value is None:
        return Decimal("0")
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")
    # An outer join fills the absent side with NaN, and Decimal("nan") is a legal
    # Decimal that poisons every comparison it touches. Treat it as absent.
    return parsed if parsed.is_finite() else Decimal("0")


def classify_break(row: dict[str, Any]) -> str:
    """Classify one joined row. Returns :data:`MATCHED` when the two sides agree.

    Quantity is tested before value on purpose: when the quantity is wrong the
    market value is wrong as a consequence, and reporting both would double-count
    one underlying problem in the analyst's queue.
    """
    merge_side = row.get("_merge")
    match merge_side:
        case "left_only":
            return MISSING_EXTERNAL
        case "right_only":
            return MISSING_INTERNAL

    quantity_difference = abs(_dec(row.get("quantity_aladdin")) - _dec(row.get("quantity_cpty")))
    if quantity_difference > QTY_TOLERANCE:
        return QUANTITY_BREAK

    base = _dec(row.get("market_value_aladdin"))
    external = _dec(row.get("market_value_cpty"))
    if base and abs(base - external) / abs(base) > MV_TOLERANCE_PCT:
        return VALUE_BREAK

    return MATCHED


def reconcile(aladdin, counterparty, as_of: date):
    """Full outer join the two feeds and return only the breaks.

    ``aladdin`` and ``counterparty`` are DataFrames carrying at minimum
    ``account_number``, ``security_id``, ``quantity`` and ``market_value``.
    Matched rows are dropped — an operations analyst works a break list, not a
    holdings list.
    """
    import pandas as pd

    merged = aladdin.merge(
        counterparty,
        on=list(KEY),
        how="outer",
        suffixes=("_aladdin", "_cpty"),
        indicator=True,
    )

    if merged.empty:
        return pd.DataFrame(columns=[*KEY, "break_type", "difference", "as_of_date"])

    merged["break_type"] = [classify_break(record) for record in merged.to_dict("records")]
    merged["difference"] = [
        _difference(record) for record in merged.to_dict("records")
    ]
    merged["as_of_date"] = as_of

    breaks = merged[merged["break_type"] != MATCHED].copy()
    breaks = breaks.drop(columns=["_merge"])

    log.info(
        "reconciliation_completed",
        extra={
            "as_of": as_of.isoformat(),
            "internal_rows": len(aladdin),
            "external_rows": len(counterparty),
            "breaks": len(breaks),
            "by_type": summarise(breaks),
        },
    )
    return breaks


def _difference(row: dict[str, Any]) -> Decimal | None:
    """The signed size of the disagreement, in the unit that caused it.

    Quantity breaks report a quantity difference, value breaks a value
    difference, missing-side breaks the amount that is absent. Analysts triage by
    size, so a break without a number on it is a break nobody prioritises.
    """
    match row.get("break_type"):
        case "QUANTITY_BREAK":
            return _dec(row.get("quantity_aladdin")) - _dec(row.get("quantity_cpty"))
        case "VALUE_BREAK":
            return _dec(row.get("market_value_aladdin")) - _dec(row.get("market_value_cpty"))
        case "MISSING_EXTERNAL":
            return _dec(row.get("quantity_aladdin"))
        case "MISSING_INTERNAL":
            return -_dec(row.get("quantity_cpty"))
        case _:
            return None


def summarise(breaks) -> dict[str, int]:
    """Counts per break class, for the daily reconciliation report.

    This feeds the operational metrics alongside straight-through rate: a jump in
    ``MISSING_EXTERNAL`` on one counterparty is either a settlement problem or an
    extraction problem, and knowing which is a five-minute check rather than an
    afternoon.
    """
    if breaks is None or len(breaks) == 0:
        return {break_type: 0 for break_type in BREAK_TYPES}
    counts = breaks["break_type"].value_counts().to_dict()
    return {break_type: int(counts.get(break_type, 0)) for break_type in BREAK_TYPES}


def audit_columns_present(breaks) -> list[str]:
    """Which audit columns survived the join, for the report writer's benefit."""
    return [column for column in _AUDIT_COLUMNS if column in getattr(breaks, "columns", [])]
