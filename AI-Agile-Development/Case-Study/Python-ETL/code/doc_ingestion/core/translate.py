"""Translate EM counterparty documents to English — descriptive fields only.

Broker Beta send their trade confirmations in Spanish. Downstream matching,
reporting and the analyst UI all expect English, so descriptive text is
normalised here before any of that runs.

-------------------------------------------------------------------------------
NWD-138 — identifiers are never translated
-------------------------------------------------------------------------------
The first version of this module translated every string field on the document.
Divya filed NWD-138 when a Spanish confirmation failed to match: the security
NAME had been translated, and so had the security IDENTIFIER alongside it. An
identifier is an opaque token — ``BONO-MX-2031`` is not Spanish, it is a key.
Translating it produced a value that matched nothing in Aladdin and surfaced as
a MISSING_INTERNAL break that took an analyst an afternoon to explain.

The fix is the allow-list below, driven by
``SourceConfig.is_translatable_field``:

* Only fields whose type is in ``translate_field_types`` (descriptive strings)
  are candidates at all — numbers, dates and currency unions never are.
* Any field named in ``no_translate_fields`` is excluded outright, whatever its
  type: ``account_number``, ``security_id``, ``isin``, ``cusip``, ``sedol``,
  ``ticker``, ``currency``, ``trade_id``.

The rule to carry away: translate prose, never keys. If a downstream join uses
it, it does not get translated.
"""

from __future__ import annotations

import logging

from config.settings import SourceConfig
from core.clients import retry_on_transport_error, translator
from core.extract import ExtractedDocument, ExtractedField

log = logging.getLogger(__name__)


@retry_on_transport_error
def to_english(texts: list[str], from_language: str) -> list[str]:
    """Normalise a batch of strings to English, preserving order and length."""
    if not texts:
        return []

    response = translator().translate(
        body=texts,
        to_language=["en"],
        from_language=from_language,
    )
    return [item.translations[0].text for item in response]


def _translatable(
    doc: ExtractedDocument, source: SourceConfig
) -> list[tuple[dict[str, ExtractedField], str]]:
    """Every field on the document that is safe to send to Translator.

    Safety here means: descriptive, and not something a join keys on. See
    NWD-138 in the module docstring.
    """
    targets: list[tuple[dict[str, ExtractedField], str]] = []
    containers: list[dict[str, ExtractedField]] = [doc.header, *doc.line_items]

    for mapping in containers:
        for name, f in mapping.items():
            if not isinstance(f.value, str) or not f.value.strip():
                continue
            if not source.is_translatable_field(name, f.field_type):
                continue
            targets.append((mapping, name))
    return targets


def translate_document(
    doc: ExtractedDocument, source: SourceConfig
) -> ExtractedDocument:
    """Translate the document's descriptive fields in place, if configured.

    A no-op for English sources. The confidence score on each field is preserved
    unchanged: Translator did not re-read the document, so it has no bearing on
    how sure the extraction model was about what it read.
    """
    if not source.translate_to or source.language == source.translate_to:
        return doc

    targets = _translatable(doc, source)
    total_text_fields = sum(
        1
        for mapping in (doc.header, *doc.line_items)
        for f in mapping.values()
        if isinstance(f.value, str) and f.value.strip()
    )
    skipped = total_text_fields - len(targets)

    if not targets:
        log.info(
            "translation_skipped_no_targets",
            extra={"source": source.key, "language": source.language},
        )
        return doc

    translated = to_english(
        [mapping[name].value for mapping, name in targets],
        from_language=source.language,
    )

    for (mapping, name), new_value in zip(targets, translated):
        mapping[name] = mapping[name].with_value(new_value)

    log.info(
        "translation_completed",
        extra={
            "source": source.key,
            "from_language": source.language,
            "translated_fields": len(targets),
            # Logged deliberately: if this number ever drops to zero on an EM
            # source, NWD-138 has regressed and identifiers are being translated.
            "protected_fields": skipped,
        },
    )
    return doc
