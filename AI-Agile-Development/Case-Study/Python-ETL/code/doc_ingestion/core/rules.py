"""The rules engine: config-driven validation and normalisation.

The confidence gate answers "was the model sure?". This module answers the
harder question: "is the document *coherent*?" Those are not the same question,
and the difference is what NWD-142 taught the team.

Everything here is driven by the ``rules:`` / ``extra_rules:`` lists in
``config/sources.yaml``. A rule is a ``{id, type, severity, applies_to, params}``
block; ``type`` selects one of the implementations registered below. Adding a
control for a new counterparty is a YAML block, not a branch in Python.

**Two phases, in declared order.** Normalisation rules run first and rewrite
values in place on a copy of the document (trimming, casing, stripping thousands
separators, mapping vocabulary). Validation rules then run against the
normalised document. Running them the other way round means every validator has
to re-implement "well, it might have a space on the end".

**Every rule returns a structured violation, never a bare bool.** A bool tells an
analyst nothing. A :class:`RuleViolation` carries the rule that fired, the field
and row it fired on, what was observed and what was expected — which is exactly
what the exception queue screen renders and what the analyst needs to fix it in
one pass.

-------------------------------------------------------------------------------
NWD-142 — the completeness rules
-------------------------------------------------------------------------------
Divya found that on a Broker Alpha statement whose positions table spanned a page
boundary, the line items on page 2 were silently dropped. The document still
passed the confidence gate, because every field that *was* extracted scored
high. It loaded into Snowflake with half the positions, and reconciliation then
reported MISSING_EXTERNAL breaks that looked exactly like genuine settlement
failures.

The gate could never have caught this. Confidence is a statement about the
values you have; it says nothing about the values you do not. So the fix is a
new class of rule that reasons about what *should* be there:

* :func:`line_item_count` — the document states how many positions it contains.
  Compare that to how many we extracted. Cheap, exact, and it would have caught
  NWD-142 on the first statement.
* :func:`page_continuation` — the layout model reports which pages carry a
  table. Compare that to the pages our line items actually came from. Any page
  with a table but no extracted rows is a dropped continuation page.

Belt and braces on purpose: not every layout declares a count, and not every
model returns table regions. Either rule alone closes the hole for the layouts
it can see; together they close it for all of them.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterator

from config.settings import RuleConfig, SourceConfig
from core import confidence as confidence_gate_module
from core.extract import ExtractedDocument, ExtractedField

log = logging.getLogger(__name__)

# Scope names a rule may target.
SCOPE_HEADER = "header"
SCOPE_LINE_ITEM = "line_item"
SCOPE_ALL = "all"

_WHITESPACE_RUN = re.compile(r"\s+")


# -----------------------------------------------------------------------------
# Result types
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleViolation:
    """One structured reason a document is not fit to load.

    ``observed`` and ``expected`` are what makes this useful in the exception
    queue: the analyst sees "quantity 1,250 x price 48.20 = 60,250.00 but the
    statement says 62,050.00" rather than "value_consistency: failed".
    """

    rule_id: str
    rule_type: str
    severity: str
    message: str
    field: str | None = None
    row: int | None = None
    observed: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Serialisable form, stored in ``etl.extraction_exception.failures_json``."""
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
            "row": self.row,
            "observed": _plain(self.observed),
            "expected": _plain(self.expected),
        }


@dataclass(frozen=True)
class Normalisation:
    """A value the engine rewrote, kept so the change is auditable."""

    rule_id: str
    field: str
    row: int | None
    before: Any
    after: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "field": self.field,
            "row": self.row,
            "before": _plain(self.before),
            "after": _plain(self.after),
        }


@dataclass
class RuleResult:
    """What the engine decided, plus the document it decided it about.

    ``document`` is the *normalised* document — the one the transform should
    consume. Downstream code must use this rather than the input, or the
    normalisation was pointless.
    """

    document: ExtractedDocument
    violations: list[RuleViolation] = dc_field(default_factory=list)
    normalisations: list[Normalisation] = dc_field(default_factory=list)

    @property
    def errors(self) -> list[RuleViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[RuleViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    @property
    def passed(self) -> bool:
        """Warnings load. Errors go to a human."""
        return not self.errors

    @property
    def straight_through(self) -> bool:
        """No error and no warning — zero human touch, the headline metric."""
        return not self.violations

    @property
    def reason(self) -> str:
        """Short reason string for the exception queue row and the log line."""
        if self.passed:
            return "ok"
        ids = sorted({v.rule_id for v in self.errors})
        return f"rule_violation: {', '.join(ids)}"

    def to_failures(self) -> list[dict[str, Any]]:
        """Every violation, serialisable, for ``failures_json``."""
        return [v.to_dict() for v in self.violations]


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

NormaliserFn = Callable[
    [ExtractedDocument, SourceConfig, RuleConfig], list[Normalisation]
]
ValidatorFn = Callable[[ExtractedDocument, SourceConfig, RuleConfig], list[RuleViolation]]

NORMALISERS: dict[str, NormaliserFn] = {}
VALIDATORS: dict[str, ValidatorFn] = {}


def normaliser(name: str) -> Callable[[NormaliserFn], NormaliserFn]:
    """Register a normalisation rule implementation under a YAML ``type``."""

    def wrap(fn: NormaliserFn) -> NormaliserFn:
        NORMALISERS[name] = fn
        return fn

    return wrap


def validator(name: str) -> Callable[[ValidatorFn], ValidatorFn]:
    """Register a validation rule implementation under a YAML ``type``."""

    def wrap(fn: ValidatorFn) -> ValidatorFn:
        VALIDATORS[name] = fn
        return fn

    return wrap


# -----------------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------------


def _plain(value: Any) -> Any:
    """Coerce a value into something ``json.dumps`` will accept."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return value


def _clone(doc: ExtractedDocument) -> ExtractedDocument:
    """Copy a document deeply enough to normalise it without touching the input.

    ``raw_response`` is shared by reference on purpose — it is the immutable
    bronze payload, it can be megabytes, and nothing here writes to it.
    """
    return ExtractedDocument(
        source_key=doc.source_key,
        model_id=doc.model_id,
        page_count=doc.page_count,
        header={k: v.with_value(v.value) for k, v in doc.header.items()},
        line_items=[
            {k: v.with_value(v.value) for k, v in row.items()} for row in doc.line_items
        ],
        raw_response=doc.raw_response,
        table_pages=list(doc.table_pages),
        declared_line_item_count=doc.declared_line_item_count,
    )


def _scope_of(rule: RuleConfig) -> str:
    return str(rule.params.get("scope", SCOPE_ALL))


def _iter_scope(
    doc: ExtractedDocument, scope: str
) -> Iterator[tuple[int | None, dict[str, ExtractedField]]]:
    """Yield ``(row_index, field_mapping)`` for each container the scope selects."""
    if scope in (SCOPE_HEADER, SCOPE_ALL):
        yield None, doc.header
    if scope in (SCOPE_LINE_ITEM, SCOPE_ALL):
        for idx, row in enumerate(doc.line_items):
            yield idx, row


def _as_decimal(value: Any) -> Decimal | None:
    """Best-effort numeric coercion. ``None`` when the value is not a number.

    Handles the currency union Document Intelligence returns (``{"amount": ...,
    "currency": ...}``) and strings that still carry grouping characters, because
    a rule may run before the normaliser that would have stripped them.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, dict):
        return _as_decimal(value.get("amount"))
    if isinstance(value, str):
        cleaned = _strip_grouping(value)
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
    return None


def _strip_grouping(text: str) -> str:
    """Turn ``1,234.56`` or ``1.234,56`` or ``1 234,56`` into ``1234.56``.

    EM counterparties use the European convention; Broker Alpha uses the
    Anglo-American one. Deciding which is which by looking at the *last*
    separator is the only reading that works for both.
    """
    # OCR emits ordinary spaces, non-breaking spaces and apostrophes as
    # digit grouping depending on the counterparty's locale.
    candidate = text.strip()
    for grouping_char in (" ", " ", " ", "'"):
        candidate = candidate.replace(grouping_char, "")
    if not candidate:
        return candidate

    last_comma = candidate.rfind(",")
    last_dot = candidate.rfind(".")

    if last_comma > last_dot:
        # Comma is the decimal separator: 1.234,56
        candidate = candidate.replace(".", "").replace(",", ".")
    else:
        # Dot is the decimal separator (or there is none): 1,234.56
        candidate = candidate.replace(",", "")
    return candidate


def _as_text(value: Any) -> str | None:
    """Textual reading of a value, unwrapping the currency union."""
    if value is None:
        return None
    if isinstance(value, dict):
        code = value.get("currency")
        return str(code) if code is not None else None
    if isinstance(value, str):
        return value
    return str(value)


def _as_date(value: Any) -> date | None:
    """Coerce a value to a ``date``. ``None`` when it is not date-like."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            return None
    return None


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


# -----------------------------------------------------------------------------
# Normalisation rules
# -----------------------------------------------------------------------------


def _selected_names(rule: RuleConfig, mapping: dict[str, ExtractedField]) -> list[str]:
    """Field names a rule targets; an empty ``fields`` list means all of them."""
    names = rule.params.get("fields") or []
    return list(names) if names else list(mapping.keys())


@normaliser("trim_whitespace")
def trim_whitespace(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[Normalisation]:
    """Strip and collapse whitespace on string values.

    OCR routinely returns ``"ACME  CORP \\n"``. Left alone, that string fails an
    exact match against Aladdin's security name and produces a break that is
    nothing but formatting.
    """
    applied: list[Normalisation] = []
    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        for name in _selected_names(rule, mapping):
            f = mapping.get(name)
            if f is None or not isinstance(f.value, str):
                continue
            cleaned = _WHITESPACE_RUN.sub(" ", f.value).strip()
            if cleaned != f.value:
                applied.append(Normalisation(rule.id, name, row_idx, f.value, cleaned))
                mapping[name] = f.with_value(cleaned)
    return applied


@normaliser("upper_case")
def upper_case(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[Normalisation]:
    """Upper-case selected string values — currency codes, tickers, sides."""
    applied: list[Normalisation] = []
    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        for name in rule.params.get("fields") or []:
            f = mapping.get(name)
            if f is None or not isinstance(f.value, str):
                continue
            upper = f.value.upper()
            if upper != f.value:
                applied.append(Normalisation(rule.id, name, row_idx, f.value, upper))
                mapping[name] = f.with_value(upper)
    return applied


@normaliser("strip_thousands_separators")
def strip_thousands_separators(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[Normalisation]:
    """Rewrite grouped numeric strings into a form ``Decimal`` will accept."""
    applied: list[Normalisation] = []
    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        for name in rule.params.get("fields") or []:
            f = mapping.get(name)
            if f is None or not isinstance(f.value, str):
                continue
            cleaned = _strip_grouping(f.value)
            if cleaned != f.value:
                applied.append(Normalisation(rule.id, name, row_idx, f.value, cleaned))
                mapping[name] = f.with_value(cleaned)
    return applied


@normaliser("map_values")
def map_values(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[Normalisation]:
    """Map a controlled vocabulary onto canonical values (COMPRA -> BUY).

    Lookup is case-insensitive because the same broker sends ``Compra`` and
    ``COMPRA`` depending on which template generated the confirmation.
    """
    mapping_table = {
        str(k).upper(): v for k, v in (rule.params.get("mapping") or {}).items()
    }
    name = rule.params.get("field")
    applied: list[Normalisation] = []
    if not name or not mapping_table:
        return applied

    for row_idx, container in _iter_scope(doc, _scope_of(rule)):
        f = container.get(name)
        if f is None or not isinstance(f.value, str):
            continue
        replacement = mapping_table.get(f.value.strip().upper())
        if replacement is not None and replacement != f.value:
            applied.append(Normalisation(rule.id, name, row_idx, f.value, replacement))
            container[name] = f.with_value(replacement)
    return applied


# -----------------------------------------------------------------------------
# Validation rules
# -----------------------------------------------------------------------------


@validator("confidence_gate")
def confidence_gate(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """Fold the pure confidence gate into the rules engine.

    The gate stays in its own module with no Azure dependency and no knowledge
    of rules; this adapter is the only thing that knows both exist. That is why
    ``tests/test_confidence.py`` needs no rules configuration and this file needs
    no threshold logic.
    """
    result = confidence_gate_module.evaluate(doc, source)
    return [
        RuleViolation(
            rule_id=rule.id,
            rule_type="confidence_gate",
            severity=rule.severity,
            message=(
                f"{failure['field']} scored {failure['confidence']} "
                f"against a threshold of {failure['threshold']} ({failure['why']})"
            ),
            field=str(failure["field"]),
            row=failure["row"],
            observed=failure["confidence"],
            expected=failure["threshold"],
        )
        for failure in result.failures
    ]


@validator("required_fields")
def required_fields(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """Named fields must be present and non-empty in the given scope."""
    names = rule.params.get("fields") or []
    violations: list[RuleViolation] = []

    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        for name in names:
            f = mapping.get(name)
            missing = f is None or f.value is None or (
                isinstance(f.value, str) and not f.value.strip()
            )
            if missing:
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        rule_type="required_fields",
                        severity=rule.severity,
                        message=f"required field '{name}' is absent or empty",
                        field=name,
                        row=row_idx,
                        observed=None if f is None else f.value,
                        expected="a non-empty value",
                    )
                )
    return violations


@validator("numeric_range")
def numeric_range(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """A numeric field must parse, and must sit inside a plausible range.

    Range checks catch the decimal-point class of OCR error: a quantity of
    1,250 read as 1250000 clears the confidence gate comfortably because the
    digits themselves were legible.
    """
    name = rule.params.get("field")
    if not name:
        return []

    low = _as_decimal(rule.params.get("min"))
    high = _as_decimal(rule.params.get("max"))
    violations: list[RuleViolation] = []

    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        f = mapping.get(name)
        if f is None or f.value is None:
            continue  # absence is required_fields' business, not ours
        number = _as_decimal(f.value)
        if number is None:
            violations.append(
                RuleViolation(
                    rule_id=rule.id,
                    rule_type="numeric_range",
                    severity=rule.severity,
                    message=f"'{name}' is not numeric",
                    field=name,
                    row=row_idx,
                    observed=f.value,
                    expected="a number",
                )
            )
            continue
        if (low is not None and number < low) or (high is not None and number > high):
            violations.append(
                RuleViolation(
                    rule_id=rule.id,
                    rule_type="numeric_range",
                    severity=rule.severity,
                    message=f"'{name}' of {number} is outside the plausible range",
                    field=name,
                    row=row_idx,
                    observed=number,
                    expected=f"between {low} and {high}",
                )
            )
    return violations


@validator("allowed_values")
def allowed_values(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """A field must hold one of an enumerated set of values."""
    name = rule.params.get("field")
    permitted = {str(v).upper() for v in (rule.params.get("values") or [])}
    allow_missing = bool(rule.params.get("allow_missing", False))
    if not name or not permitted:
        return []

    violations: list[RuleViolation] = []
    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        f = mapping.get(name)
        text = _as_text(None if f is None else f.value)
        if text is None or not text.strip():
            if allow_missing:
                continue
            text = ""
        if text.strip().upper() not in permitted:
            violations.append(
                RuleViolation(
                    rule_id=rule.id,
                    rule_type="allowed_values",
                    severity=rule.severity,
                    message=f"'{name}' value '{text}' is not a recognised code",
                    field=name,
                    row=row_idx,
                    observed=text,
                    expected=sorted(permitted),
                )
            )
    return violations


@validator("date_not_future")
def date_not_future(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """Dates must not be in the future beyond a small grace window.

    A statement dated next month is a misread year, every time. The grace
    window exists because counterparty clocks and time zones genuinely disagree
    by a day at the boundary.
    """
    names = rule.params.get("fields") or []
    grace = int(rule.params.get("grace_days", 0))
    limit = _today_utc() + timedelta(days=grace)
    violations: list[RuleViolation] = []

    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        for name in names:
            f = mapping.get(name)
            if f is None or f.value is None:
                continue
            value = _as_date(f.value)
            if value is None:
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        rule_type="date_not_future",
                        severity=rule.severity,
                        message=f"'{name}' is not a readable date",
                        field=name,
                        row=row_idx,
                        observed=f.value,
                        expected="a date",
                    )
                )
                continue
            if value > limit:
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        rule_type="date_not_future",
                        severity=rule.severity,
                        message=f"'{name}' of {value.isoformat()} is in the future",
                        field=name,
                        row=row_idx,
                        observed=value,
                        expected=f"on or before {limit.isoformat()}",
                    )
                )
    return violations


@validator("date_order")
def date_order(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """One date must not precede another — settlement never precedes trade."""
    earlier_name = rule.params.get("earlier")
    later_name = rule.params.get("later")
    if not earlier_name or not later_name:
        return []

    violations: list[RuleViolation] = []
    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        earlier = _as_date(getattr(mapping.get(earlier_name), "value", None))
        later = _as_date(getattr(mapping.get(later_name), "value", None))
        if earlier is None or later is None:
            continue
        if later < earlier:
            violations.append(
                RuleViolation(
                    rule_id=rule.id,
                    rule_type="date_order",
                    severity=rule.severity,
                    message=(
                        f"'{later_name}' ({later.isoformat()}) precedes "
                        f"'{earlier_name}' ({earlier.isoformat()})"
                    ),
                    field=later_name,
                    row=row_idx,
                    observed=later,
                    expected=f"on or after {earlier.isoformat()}",
                )
            )
    return violations


@validator("cross_field_product")
def cross_field_product(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """``left x right`` must reconcile to ``product`` within a tolerance.

    quantity x price should equal market value. When it does not, one of the
    three numbers was misread even though all three cleared the confidence gate
    individually — the model was confident about a digit it got wrong. This is
    arithmetic the document itself proves, which makes it the cheapest and most
    reliable check in the engine.

    The rule abstains when any operand is absent: that is ``required_fields``'
    job, and firing twice for one cause makes the exception queue harder to read.
    """
    left_name = rule.params.get("left")
    right_name = rule.params.get("right")
    product_name = rule.params.get("product")
    if not (left_name and right_name and product_name):
        return []

    tolerance_pct = _as_decimal(rule.params.get("tolerance_pct", "0.005")) or Decimal("0.005")
    tolerance_abs = _as_decimal(rule.params.get("tolerance_abs", "0.01")) or Decimal("0.01")

    violations: list[RuleViolation] = []
    for row_idx, mapping in _iter_scope(doc, _scope_of(rule)):
        left = _as_decimal(getattr(mapping.get(left_name), "value", None))
        right = _as_decimal(getattr(mapping.get(right_name), "value", None))
        stated = _as_decimal(getattr(mapping.get(product_name), "value", None))
        if left is None or right is None or stated is None:
            continue

        computed = left * right
        difference = abs(computed - stated)
        allowed = abs(computed) * tolerance_pct if computed else tolerance_abs

        if difference > allowed:
            violations.append(
                RuleViolation(
                    rule_id=rule.id,
                    rule_type="cross_field_product",
                    severity=rule.severity,
                    message=(
                        f"{left_name} {left} x {right_name} {right} = {computed}, "
                        f"but {product_name} says {stated}"
                    ),
                    field=product_name,
                    row=row_idx,
                    observed=stated,
                    expected=computed,
                )
            )
    return violations


@validator("min_line_items")
def min_line_items(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """A statement with no line items extracted at all is never correct."""
    minimum = int(rule.params.get("minimum", 1))
    if len(doc.line_items) >= minimum:
        return []
    return [
        RuleViolation(
            rule_id=rule.id,
            rule_type="min_line_items",
            severity=rule.severity,
            message=(
                f"extracted {len(doc.line_items)} line items, expected at least {minimum}"
            ),
            field=None,
            row=None,
            observed=len(doc.line_items),
            expected=minimum,
        )
    ]


# -----------------------------------------------------------------------------
# Completeness rules — the NWD-142 fix
# -----------------------------------------------------------------------------


@validator("line_item_count")
def line_item_count(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """Declared line-item count must equal the number extracted. (NWD-142)

    Broker Alpha's statement header carries ``PositionCount``. When the positions
    table spanned a page boundary the extractor returned the page-1 rows only,
    and every one of them was high confidence — so the gate passed a document
    that was missing half its content.

    Comparing the document's own declared count against what we extracted turns
    that silent data loss into an exception-queue item with an exact number in
    it. The rule abstains, loudly, when the layout does not declare a count;
    :func:`page_continuation` is the cover for those layouts.
    """
    declared = doc.declared_line_item_count
    if declared is None:
        log.info(
            "line_item_count_not_declared",
            extra={"source": source.key, "rule": rule.id, "model": doc.model_id},
        )
        return []

    extracted = len(doc.line_items)
    if declared == extracted:
        return []

    return [
        RuleViolation(
            rule_id=rule.id,
            rule_type="line_item_count",
            severity=rule.severity,
            message=(
                f"document declares {declared} line items but {extracted} were "
                f"extracted across {doc.page_count} pages"
            ),
            field=source.line_item_count_field,
            row=None,
            observed=extracted,
            expected=declared,
        )
    ]


@validator("page_continuation")
def page_continuation(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """Every page carrying a table must have contributed line items. (NWD-142)

    The layout model tells us which pages a table sits on. Our extracted line
    items tell us which pages we actually read rows from. A page in the first set
    and not the second is a continuation page we dropped — the precise shape of
    NWD-142, caught without needing the document to declare a count.

    The rule abstains when the model returned no table regions, because absence
    of evidence is not evidence of completeness and a false error here would send
    healthy documents to an analyst.
    """
    if doc.page_count <= 1:
        return []

    table_pages = set(doc.table_pages)
    if not table_pages:
        log.info(
            "page_continuation_not_evaluable",
            extra={"source": source.key, "rule": rule.id, "pages": doc.page_count},
        )
        return []

    read_pages = set(doc.line_item_pages())
    if not read_pages:
        # No page provenance at all: min_line_items / line_item_count cover this.
        return []

    dropped = sorted(table_pages - read_pages)
    if not dropped:
        return []

    return [
        RuleViolation(
            rule_id=rule.id,
            rule_type="page_continuation",
            severity=rule.severity,
            message=(
                "the positions table continues onto "
                f"page(s) {dropped} but no line items were extracted from them"
            ),
            field=None,
            row=None,
            observed=sorted(read_pages),
            expected=sorted(table_pages),
        )
    ]


# -----------------------------------------------------------------------------
# The engine
# -----------------------------------------------------------------------------


class RulesEngine:
    """Applies an ordered list of configured rules to an extracted document."""

    def __init__(self, rules: list[RuleConfig]) -> None:
        unknown = [
            r.id for r in rules if r.type not in NORMALISERS and r.type not in VALIDATORS
        ]
        if unknown:
            # Fail at construction, not silently at run time. A typo in YAML must
            # not quietly remove a control from a financial pipeline.
            raise ValueError(f"Unknown rule type(s) configured for rules: {unknown}")
        self.rules = rules

    @classmethod
    def for_source(cls, source: SourceConfig) -> "RulesEngine":
        """Build the engine for one counterparty: defaults then its additions."""
        return cls(source.all_rules)

    def run(self, doc: ExtractedDocument, source: SourceConfig) -> RuleResult:
        """Normalise, then validate. Returns the normalised document either way.

        Validation always runs to completion. Short-circuiting on the first error
        would mean an analyst fixes one field, resubmits, and discovers the next
        — which is how a five-minute correction becomes a morning.
        """
        working = _clone(doc)
        applicable = [r for r in self.rules if r.applies(source.doc_type)]

        normalisations: list[Normalisation] = []
        for rule in applicable:
            fn = NORMALISERS.get(rule.type)
            if fn is not None:
                normalisations.extend(fn(working, source, rule))

        violations: list[RuleViolation] = []
        for rule in applicable:
            fn_v = VALIDATORS.get(rule.type)
            if fn_v is not None:
                violations.extend(fn_v(working, source, rule))

        result = RuleResult(
            document=working, violations=violations, normalisations=normalisations
        )

        log.info(
            "rules_evaluated",
            extra={
                "source": source.key,
                "rules_applied": len(applicable),
                "normalisations": len(normalisations),
                "errors": len(result.errors),
                "warnings": len(result.warnings),
                "passed": result.passed,
            },
        )
        return result


def evaluate(doc: ExtractedDocument, source: SourceConfig) -> RuleResult:
    """Convenience entry point: build the engine for a source and run it once."""
    return RulesEngine.for_source(source).run(doc, source)
