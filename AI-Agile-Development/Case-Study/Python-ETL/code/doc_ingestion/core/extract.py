"""Document Intelligence extraction, and the shape everything downstream reads.

Two responsibilities live here.

1. :class:`ExtractedField` / :class:`ExtractedDocument` — the pipeline's internal
   representation of an analysed document. Deliberately plain dataclasses with
   no Azure types in them, so every module after this point (the confidence
   gate, the rules engine, the transform) is testable with hand-built objects
   and no mocking.
2. :func:`analyze` — the wrapper around the counterparty's custom extraction
   model that produces one of those documents.

**Why the Azure imports are inside the functions.** ``core/confidence.py`` is
required to be pure logic with no Azure dependency, and it imports the
dataclasses from this module. If this module imported the SDK at the top, that
purity would be a fiction — importing the gate would drag in the whole SDK. The
SDK is imported at the point of use instead, and the type names are resolved
under ``TYPE_CHECKING`` for annotations only.

**Page provenance is captured on purpose.** Every field records the page it came
from, and the document records which pages the model reported a table on. That
data is what the ``page_continuation`` completeness rule needs; without it,
NWD-142 (line items on page 2 silently dropped) is invisible.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Iterator

from config.settings import SourceConfig
from core.clients import doc_intel, retry_on_transport_error

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    from azure.ai.documentintelligence.models import AnalyzeResult, DocumentField

log = logging.getLogger(__name__)


@dataclass
class ExtractedField:
    """One field the model returned, with the certainty it had.

    ``confidence`` is ``None`` when the model did not report one. That is not
    "fine" — the gate treats it as unverified and fails it. See
    :mod:`core.confidence`.
    """

    name: str
    value: Any
    confidence: float | None
    field_type: str
    raw_content: str | None = None
    page_number: int | None = None

    def with_value(self, value: Any) -> "ExtractedField":
        """A copy carrying a new value, keeping provenance intact.

        Normalisation and translation both produce new values; neither may
        discard the confidence or the page the value came from.
        """
        return replace(self, value=value)


@dataclass
class ExtractedDocument:
    """A whole analysed document: header fields plus repeating line items."""

    source_key: str
    model_id: str
    page_count: int
    header: dict[str, ExtractedField] = field(default_factory=dict)
    line_items: list[dict[str, ExtractedField]] = field(default_factory=list)
    raw_response: dict[str, Any] | None = None

    # Pages on which the model reported a table. Compare against the pages the
    # line items actually came from to detect a dropped continuation page.
    table_pages: list[int] = field(default_factory=list)
    # The count the document states for itself, when the layout carries one.
    declared_line_item_count: int | None = None

    def all_fields(self) -> Iterator[tuple[int | None, ExtractedField]]:
        """Every field in the document, tagged with its line-item row index."""
        for f in self.header.values():
            yield None, f
        for idx, row in enumerate(self.line_items):
            for f in row.values():
                yield idx, f

    def line_item_pages(self) -> list[int]:
        """Sorted distinct pages that contributed at least one line item."""
        pages = {
            f.page_number
            for row in self.line_items
            for f in row.values()
            if f.page_number is not None
        }
        return sorted(pages)


def _unwrap(f: "DocumentField") -> Any:
    """Document Intelligence returns a typed union; normalise it to a Python value."""
    match f.type:
        case "string" | "countryRegion" | "phoneNumber" | "address":
            return f.value_string
        case "number":
            return f.value_number
        case "integer":
            return f.value_integer
        case "date":
            return f.value_date
        case "time":
            return f.value_time
        case "currency":
            # value_currency has .amount and .currency_code — keep both, because
            # the transform needs the amount and the rules engine needs the code.
            return (
                None
                if f.value_currency is None
                else {
                    "amount": f.value_currency.amount,
                    "currency": f.value_currency.currency_code,
                }
            )
        case "selectionMark":
            return f.value_selection_mark
        case _:
            return f.content


def _page_of(f: "DocumentField") -> int | None:
    """The page a field was read from, via its first bounding region."""
    regions = getattr(f, "bounding_regions", None) or []
    if not regions:
        return None
    return getattr(regions[0], "page_number", None)


def _to_extracted(name: str, f: "DocumentField") -> ExtractedField:
    return ExtractedField(
        name=name,
        value=_unwrap(f),
        confidence=f.confidence,
        field_type=f.type or "string",
        raw_content=f.content,
        page_number=_page_of(f),
    )


def _table_pages(result: "AnalyzeResult") -> list[int]:
    """Pages the layout model found a table on.

    This is the ground truth the ``page_continuation`` rule compares line-item
    provenance against. If the model saw a table on page 2 and no line item came
    from page 2, rows were lost between layout and field extraction.
    """
    pages: set[int] = set()
    for table in getattr(result, "tables", None) or []:
        for region in getattr(table, "bounding_regions", None) or []:
            page = getattr(region, "page_number", None)
            if page is not None:
                pages.add(page)
    return sorted(pages)


def _declared_count(header: dict[str, ExtractedField], source: SourceConfig) -> int | None:
    """The line-item count the document claims, if the layout states one."""
    if not source.line_item_count_field:
        return None
    f = header.get(source.line_item_count_field)
    if f is None or f.value is None:
        return None
    try:
        return int(f.value)
    except (TypeError, ValueError):
        log.warning(
            "declared_count_unparseable",
            extra={"source": source.key, "value": f.value},
        )
        return None


@retry_on_transport_error
def analyze(content: bytes, source: SourceConfig) -> ExtractedDocument:
    """Run a document through its counterparty-specific extraction model.

    ``begin_analyze_document`` starts a long-running operation. The poller must
    be awaited with ``.result()`` — this is the single most common integration
    mistake with this SDK, and it is why the blob trigger enqueues rather than
    analysing inline: a 50-page scanned statement can outrun the Function
    execution timeout.
    """
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    client = doc_intel()
    poller = client.begin_analyze_document(
        source.model_id,
        AnalyzeDocumentRequest(bytes_source=content),
    )
    result = poller.result()

    if not result.documents:
        raise ValueError(f"Model {source.model_id} returned no documents")

    doc = result.documents[0]
    page_count = len(result.pages or [])

    header: dict[str, ExtractedField] = {}
    line_items: list[dict[str, ExtractedField]] = []

    for api_name, target_name in source.field_map.items():
        f = (doc.fields or {}).get(api_name)
        if f is None:
            log.warning(
                "field_missing",
                extra={"field": api_name, "model": source.model_id, "source": source.key},
            )
            continue

        # Array fields hold repeating line items (positions, trades).
        if f.type == "array":
            for row in f.value_array or []:
                mapped = {
                    source.line_item_map.get(k, k): _to_extracted(
                        source.line_item_map.get(k, k), v
                    )
                    for k, v in (row.value_object or {}).items()
                    if k in source.line_item_map
                }
                if mapped:
                    line_items.append(mapped)
        else:
            header[target_name] = _to_extracted(target_name, f)

    extracted = ExtractedDocument(
        source_key=source.key,
        model_id=source.model_id,
        page_count=page_count,
        header=header,
        line_items=line_items,
        raw_response=result.as_dict(),
        table_pages=_table_pages(result),
    )
    extracted.declared_line_item_count = _declared_count(header, source)

    log.info(
        "extraction_completed",
        extra={
            "source": source.key,
            "model": source.model_id,
            "pages": page_count,
            "header_fields": len(header),
            "line_items": len(line_items),
            "table_pages": extracted.table_pages,
            "declared_line_items": extracted.declared_line_item_count,
        },
    )
    return extracted
