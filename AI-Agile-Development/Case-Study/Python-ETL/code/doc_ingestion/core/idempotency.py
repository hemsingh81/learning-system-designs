"""Content hashing and the processed-document ledger.

Extraction is billed per page. Reprocessing a document because a downstream step
failed, or because a counterparty resent the same statement, is a real cost and
a real data problem — a duplicate statement loaded twice doubles a position.

-------------------------------------------------------------------------------
NWD-140 — the hash is of CONTENT, never the filename
-------------------------------------------------------------------------------
Divya filed NWD-140 when Broker Alpha resent an unchanged statement as
``positions_20260728_RESEND.pdf``. It loaded a second time and produced a
duplicate row. The cause was one code path that had drifted to hashing the blob
name instead of the bytes — it looked equivalent, and for every test fixture it
was.

It is not equivalent. Counterparties rename, re-zip, and resend constantly, and
the filename is metadata they control. The bytes are the document.

:func:`content_hash` is now the only way a digest is produced anywhere in this
codebase, and it takes ``bytes``. There is deliberately no overload that accepts
a path or a name — if you cannot pass the content, you cannot get a hash.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

# Ledger status values. ``skipped`` exists so a duplicate is visible in the
# ledger rather than being invisible by absence.
STATUS_LOADED = "loaded"
STATUS_REVIEW = "review"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


@dataclass(frozen=True)
class LedgerEntry:
    """One row of ``etl.processed_document``."""

    content_hash: str
    blob_path: str
    model_id: str
    page_count: int
    status: str
    reason: str | None = None


def content_hash(content: bytes) -> str:
    """SHA-256 of the document bytes, lower-case hex.

    NWD-140: content, not filename. See the module docstring. The signature only
    accepts bytes so that the mistake cannot be made again by accident.
    """
    if not isinstance(content, (bytes, bytearray, memoryview)):
        raise TypeError(
            "content_hash requires the document bytes. Hashing a filename or a "
            "path is the NWD-140 defect and is not supported."
        )
    return hashlib.sha256(bytes(content)).hexdigest()


def already_processed(conn: Any, digest: str) -> bool:
    """Whether this exact content has already been loaded or is under review.

    ``failed`` is deliberately not in the list: a document that blew up on a
    transient error must be allowed through on a retry. ``review`` is, because
    the analyst already has it and a resend should not create a second queue
    item for the same bytes.
    """
    row = conn.execute(
        """
        SELECT 1
        FROM etl.processed_document
        WHERE content_hash = ? AND status IN ('loaded', 'review')
        """,
        digest,
    ).fetchone()
    return row is not None


def record_processed(
    conn: Any,
    *,
    digest: str,
    blob_path: str,
    model_id: str,
    pages: int,
    status: str,
    reason: str | None = None,
) -> None:
    """Upsert the ledger row for this document.

    MERGE rather than INSERT because a document legitimately transitions
    ``review`` -> ``loaded`` when an analyst corrects it and it is resubmitted,
    and because two Function instances can race on the same blob.
    """
    conn.execute(
        """
        MERGE etl.processed_document AS t
        USING (SELECT ? AS content_hash) AS s
          ON t.content_hash = s.content_hash
        WHEN MATCHED THEN
            UPDATE SET status = ?, reason = ?, model_id = ?, page_count = ?,
                       updated_utc = SYSUTCDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (content_hash, blob_path, model_id, page_count, status, reason, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, SYSUTCDATETIME());
        """,
        digest,
        status,
        reason,
        model_id,
        pages,
        digest,
        blob_path,
        model_id,
        pages,
        status,
        reason,
    )
    conn.commit()

    log.info(
        "ledger_recorded",
        extra={
            "hash": digest,
            "blob_path": blob_path,
            "status": status,
            "pages": pages,
            "reason": reason,
        },
    )
