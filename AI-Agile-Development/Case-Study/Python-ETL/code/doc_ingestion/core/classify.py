"""Route a PDF to the right extraction model — or to a human.

The classifier runs before extraction and answers one question: which
counterparty layout is this? Blob path prefix already suggests an answer, but
paths are set by whoever dropped the file and counterparties change their
templates without telling anyone. The classifier is the independent check.

The threshold is the whole point. Below ``min_confidence`` (0.75) the document
is not guessed at — it goes to the exception queue with the classifier's own
uncertainty recorded. Guessing the layout means running the wrong extraction
model, which produces confidently wrong fields: the single worst outcome this
pipeline can have.

A drop in classification confidence across a day's documents is also the
earliest signal that a counterparty changed their template, which is why the
confidence is logged on every document, not just the failures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from config.settings import SourceConfig
from core.clients import doc_intel, retry_on_transport_error

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Classification:
    """What the classifier decided about a document."""

    doc_type: str | None
    confidence: float
    accepted: bool

    @property
    def reason(self) -> str:
        if self.accepted:
            return "ok"
        if self.doc_type is None:
            return "unclassified: no document type returned"
        return f"classification_below_threshold: {self.doc_type} at {self.confidence:.2f}"


@retry_on_transport_error
def classify(content: bytes, source: SourceConfig) -> Classification:
    """Identify which counterparty layout this document is.

    Returns an unaccepted :class:`Classification` rather than raising when the
    model is unsure — an unrecognised layout is an ordinary business outcome
    that belongs in the exception queue, not an exception in the code.
    """
    from azure.ai.documentintelligence.models import ClassifyDocumentRequest

    cfg = source.classifier
    poller = doc_intel().begin_classify_document(
        cfg.classifier_id,
        ClassifyDocumentRequest(bytes_source=content),
    )
    result = poller.result()

    if not result.documents:
        log.warning(
            "classification_empty",
            extra={"classifier": cfg.classifier_id, "source": source.key},
        )
        return Classification(doc_type=None, confidence=0.0, accepted=False)

    top = max(result.documents, key=lambda d: d.confidence or 0.0)
    confidence = top.confidence or 0.0
    doc_type = top.doc_type

    if confidence < cfg.min_confidence:
        log.warning(
            "classification_below_threshold",
            extra={
                "doc_type": doc_type,
                "confidence": confidence,
                "threshold": cfg.min_confidence,
                "source": source.key,
            },
        )
        return Classification(doc_type=doc_type, confidence=confidence, accepted=False)

    log.info(
        "classification_accepted",
        extra={"doc_type": doc_type, "confidence": confidence, "source": source.key},
    )
    return Classification(doc_type=doc_type, confidence=confidence, accepted=True)


def matches_expected(classification: Classification, source: SourceConfig) -> bool:
    """Whether the classifier agrees with the path-based routing.

    Disagreement means the file landed under the wrong prefix or the
    counterparty changed their template. Either way a human decides, because
    extracting with the wrong model is worse than extracting nothing.
    """
    if not classification.accepted or classification.doc_type is None:
        return False
    return classification.doc_type == source.doc_type
