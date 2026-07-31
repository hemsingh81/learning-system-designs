"""Map extracted fields onto the canonical ``counterparty_position`` schema.

This is the boundary between "what the model saw" and "what the warehouse
holds". Everything upstream of here is shaped by the counterparty; everything
downstream is shaped by Northwind's data contract. One document type in, one row
type out.

Three decisions in this module are non-negotiable and are worth stating.

**Money and quantity are ``Decimal``, never ``float``.** ``0.1 + 0.2`` is not
``0.3`` in binary floating point, and a reconciliation whose tolerance is 0.0001
cannot afford representation noise. Values arrive from the SDK as floats or
strings; they are converted through ``str`` so the decimal digits the model
actually read are the digits stored.

**Timestamps are timezone-aware UTC.** Northwind runs London and Los Angeles.
A naive datetime is a bug waiting for a daylight-saving boundary; the moment a
break report is generated in one office about a row written in the other, an
ambiguous timestamp becomes an argument nobody can settle.

**Every row carries ``content_hash``, ``bronze_path`` and ``min_confidence``.**
That is the audit story in three columns: for any number in any report, produce
the original PDF, the raw extraction response, and how sure the model was. If
those columns are ever dropped to "tidy up the schema", the pipeline stops being
auditable and the control stops being defensible.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from config.settings import SourceConfig
from core import confidence as confidence_module
from core.extract import ExtractedDocument, ExtractedField

log = logging.getLogger(__name__)

# Precision the warehouse stores. Quantities carry eight places because EM funds
# deal in fractional units; money carries four because that is what the
# statements state and rounding earlier throws away information reconciliation
# needs.
QUANTITY_DP = Decimal("0.00000001")
MONEY_DP = Decimal("0.0001")
CONFIDENCE_DP = Decimal("0.0001")

# The canonical column order. Both sinks and ``sql/schema.sql`` follow this list;
# it exists so a schema change is one edit rather than four that drift apart.
COLUMNS: tuple[str, ...] = (
    "content_hash",
    "source_key",
    "doc_type",
    "account_number",
    "security_id",
    "security_name",
    "statement_date",
    "trade_date",
    "settlement_date",
    "line_no",
    "side",
    "quantity",
    "price",
    "market_value",
    "currency",
    "min_confidence",
    "model_id",
    "bronze_path",
    "blob_path",
    "extracted_utc",
)


class TransformError(ValueError):
    """A document reached the transform without a field the schema requires.

    In practice the rules engine catches these first; this is the backstop that
    keeps a malformed row out of the warehouse if a rule is ever misconfigured.
    """


@dataclass(frozen=True)
class CounterpartyPosition:
    """One canonical row. Column names match ``sql/schema.sql`` exactly.

    A trade confirmation and a position statement both land here. They differ in
    which date columns are populated, not in shape — one target table means one
    reconciliation, which is the entire reason the schema is canonical.
    """

    content_hash: str
    source_key: str
    doc_type: str
    account_number: str
    security_id: str
    security_name: str | None
    statement_date: date
    trade_date: date | None
    settlement_date: date | None
    line_no: int
    side: str | None
    quantity: Decimal
    price: Decimal | None
    market_value: Decimal | None
    currency: str | None
    min_confidence: Decimal
    model_id: str
    bronze_path: str
    blob_path: str
    extracted_utc: datetime

    def as_tuple(self) -> tuple[Any, ...]:
        """Values in :data:`COLUMNS` order, for a parameterised insert."""
        data = asdict(self)
        return tuple(data[name] for name in COLUMNS)

    def as_dict(self) -> dict[str, Any]:
        """Values keyed by canonical column name."""
        return {name: getattr(self, name) for name in COLUMNS}


# -----------------------------------------------------------------------------
# Coercion helpers
# -----------------------------------------------------------------------------


def _value(mapping: dict[str, ExtractedField], name: str) -> Any:
    f = mapping.get(name)
    return None if f is None else f.value


def _decimal(value: Any, places: Decimal, *, field_name: str) -> Decimal | None:
    """Coerce to ``Decimal`` at a fixed precision. ``None`` stays ``None``.

    Conversion goes via ``str`` deliberately: ``Decimal(0.1)`` captures the
    binary approximation, ``Decimal(str(0.1))`` captures the decimal the model
    reported.
    """
    if value is None:
        return None
    if isinstance(value, dict):  # the currency union: {"amount", "currency"}
        return _decimal(value.get("amount"), places, field_name=field_name)
    if isinstance(value, bool):
        raise TransformError(f"'{field_name}' is a boolean, not a number")
    try:
        return Decimal(str(value)).quantize(places)
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        raise TransformError(f"'{field_name}' value {value!r} is not numeric") from exc


def _currency_code(mapping: dict[str, ExtractedField], name: str) -> str | None:
    """Read an ISO currency code from either a plain string or the currency union."""
    value = _value(mapping, name)
    if value is None:
        return None
    if isinstance(value, dict):
        code = value.get("currency")
        return str(code).upper()[:3] if code else None
    text = str(value).strip().upper()
    return text[:3] or None


def _date(value: Any, *, field_name: str) -> date | None:
    """Coerce to a ``date``. Strings are read as ISO, which is what the SDK emits."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).strip()).date()
    except ValueError as exc:
        raise TransformError(f"'{field_name}' value {value!r} is not a date") from exc


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(value: Any, *, field_name: str) -> str:
    text = _text(value)
    if text is None:
        raise TransformError(f"required field '{field_name}' is empty")
    return text


def _as_of_date(doc: ExtractedDocument, source: SourceConfig) -> date:
    """The date the row is 'as of'.

    A position statement states one directly. A trade confirmation does not — the
    trade date is the equivalent anchor, and using it keeps a single non-null
    column in the natural key that both document types populate. Without that,
    the warehouse MERGE key contains a NULL and stops matching.
    """
    match source.doc_type:
        case "position_statement":
            value = _value(doc.header, "statement_date")
            field_name = "statement_date"
        case "trade_confirmation":
            value = _value(doc.header, "trade_date")
            field_name = "trade_date"
        case _:
            value = _value(doc.header, "statement_date") or _value(doc.header, "trade_date")
            field_name = "statement_date/trade_date"

    resolved = _date(value, field_name=field_name)
    if resolved is None:
        raise TransformError(
            f"cannot resolve an as-of date for {source.key}: '{field_name}' is absent"
        )
    return resolved


# -----------------------------------------------------------------------------
# The transform
# -----------------------------------------------------------------------------


def to_positions(
    doc: ExtractedDocument,
    source: SourceConfig,
    *,
    content_hash: str,
    bronze_path: str,
    blob_path: str,
    extracted_utc: datetime | None = None,
) -> list[CounterpartyPosition]:
    """Turn one extracted document into canonical rows, one per line item.

    ``doc`` must be the *normalised* document the rules engine returned, not the
    raw extraction — the values here are the ones that reach the warehouse, and
    normalisation is what makes them comparable to Aladdin's.
    """
    as_of = _as_of_date(doc, source)
    account_number = _required_text(
        _value(doc.header, "account_number"), field_name="account_number"
    )
    trade_date = _date(_value(doc.header, "trade_date"), field_name="trade_date")
    settlement_date = _date(
        _value(doc.header, "settlement_date"), field_name="settlement_date"
    )

    # One min_confidence for the whole document, not per row. A document is
    # accepted or rejected as a unit, so the weakest field in it is the honest
    # confidence for every row it produced.
    lowest = _decimal(
        confidence_module.min_confidence(doc), CONFIDENCE_DP, field_name="min_confidence"
    )
    assert lowest is not None  # min_confidence always returns a float

    now = extracted_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise TransformError("extracted_utc must be timezone-aware")
    now = now.astimezone(timezone.utc)

    rows: list[CounterpartyPosition] = []
    for line_no, item in enumerate(doc.line_items, start=1):
        quantity = _decimal(_value(item, "quantity"), QUANTITY_DP, field_name="quantity")
        if quantity is None:
            raise TransformError(f"line {line_no}: quantity is required")

        rows.append(
            CounterpartyPosition(
                content_hash=content_hash,
                source_key=source.key,
                doc_type=source.doc_type,
                account_number=account_number,
                security_id=_required_text(
                    _value(item, "security_id"), field_name="security_id"
                ),
                security_name=_text(_value(item, "security_name")),
                statement_date=as_of,
                trade_date=trade_date,
                settlement_date=settlement_date,
                line_no=line_no,
                side=_text(_value(item, "side")),
                quantity=quantity,
                price=_decimal(_value(item, "price"), MONEY_DP, field_name="price"),
                market_value=_decimal(
                    _value(item, "market_value"), MONEY_DP, field_name="market_value"
                ),
                currency=_currency_code(item, "currency"),
                min_confidence=lowest,
                model_id=doc.model_id,
                bronze_path=bronze_path,
                blob_path=blob_path,
                extracted_utc=now,
            )
        )

    log.info(
        "transform_completed",
        extra={
            "source": source.key,
            "rows": len(rows),
            "as_of": as_of.isoformat(),
            "min_confidence": str(lowest),
            "bronze_path": bronze_path,
        },
    )
    return rows
