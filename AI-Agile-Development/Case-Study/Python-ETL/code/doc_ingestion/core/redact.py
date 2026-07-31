"""PII redaction with Azure AI Language. Fails closed.

Northwind's counterparty statements carry client names, account numbers and
occasionally an adviser's contact details. None of that belongs in silver or
gold. It is detected and masked here, before anything is persisted downstream.
Unredacted content exists in exactly one place — the access-restricted bronze
container, retained for audit.

**Fail closed is the whole design.** If the Language call errors, this module
does not fall back to the original text. It writes a marker. A missing value
creates a visible gap that an analyst resolves; a leaked account number creates
a compliance incident that nobody notices until an audit. Given the choice, take
the gap.

Only descriptive free-text is sent for redaction. Identifiers the pipeline keys
on are excluded by the same configuration that excludes them from translation,
because a masked security identifier would break reconciliation just as surely
as a translated one.
"""

from __future__ import annotations

import logging
from typing import Iterator, Sequence

from config.settings import SourceConfig
from core.clients import language, retry_on_transport_error
from core.extract import ExtractedDocument

log = logging.getLogger(__name__)

# The Language API accepts a limited number of documents per request.
MAX_BATCH = 5

# The marker persisted when redaction could not be completed. Chosen to be
# obviously non-data so it can never be mistaken for a real value, and so the
# exception queue can search for it.
REDACTION_FAILED = "[REDACTION_FAILED]"

SENSITIVE: frozenset[str] = frozenset(
    {
        "Person",
        "PersonType",
        "PhoneNumber",
        "Email",
        "Address",
        "USBankAccountNumber",
        "USSocialSecurityNumber",
        "CreditCardNumber",
        "InternationalBankingAccountNumber",
        "SWIFTCode",
        "EUPassportNumber",
    }
)


def _chunks(items: Sequence[str], size: int) -> Iterator[Sequence[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


@retry_on_transport_error
def redact(texts: list[str], language_code: str = "en") -> list[str]:
    """Redact PII from free-text values, returning one result per input.

    The output list is always the same length and order as the input, so callers
    can zip it back onto the fields it came from. Failures appear in position as
    :data:`REDACTION_FAILED` rather than shortening the list.
    """
    if not texts:
        return []

    client = language()
    out: list[str] = []

    for batch in _chunks(texts, MAX_BATCH):
        results = client.recognize_pii_entities(
            documents=list(batch),
            language=language_code,
            categories_filter=list(SENSITIVE),
        )
        for original, result in zip(batch, results):
            if result.is_error:
                # Fail closed: if redaction fails, do not persist the raw text.
                log.error(
                    "pii_redaction_failed",
                    extra={
                        "code": getattr(result.error, "code", "unknown"),
                        "chars": len(original),
                    },
                )
                out.append(REDACTION_FAILED)
            else:
                out.append(result.redacted_text)

    return out


def redact_document(doc: ExtractedDocument, source: SourceConfig) -> ExtractedDocument:
    """Redact every free-text field on a document, in place.

    Which fields count as free-text is the source's decision, and it is the same
    decision that governs translation: descriptive fields yes, identifiers never.
    Redacting ``security_id`` would produce a row that reconciles against
    nothing.
    """
    if not source.redact_pii:
        return doc

    targets: list[tuple[dict, str, str]] = []
    for row_idx, mapping in _containers(doc):
        for name, f in mapping.items():
            if not isinstance(f.value, str) or not f.value.strip():
                continue
            if not source.is_translatable_field(name, f.field_type):
                # Same allow-list as translation: identifiers are left alone.
                continue
            targets.append((mapping, name, f.value))

    if not targets:
        return doc

    redacted = redact([text for _, _, text in targets], language_code="en")

    failures = 0
    for (mapping, name, _), new_value in zip(targets, redacted):
        if new_value == REDACTION_FAILED:
            failures += 1
        mapping[name] = mapping[name].with_value(new_value)

    log.info(
        "pii_redaction_completed",
        extra={
            "source": source.key,
            "fields": len(targets),
            "failed": failures,
        },
    )
    return doc


def _containers(doc: ExtractedDocument):
    """Header first, then each line item, tagged with its row index."""
    yield None, doc.header
    for idx, row in enumerate(doc.line_items):
        yield idx, row
