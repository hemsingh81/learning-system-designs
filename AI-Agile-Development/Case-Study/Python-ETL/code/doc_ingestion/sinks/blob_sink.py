"""Bronze persistence: the full extraction response, written before parsing.

Bronze is the cheapest insurance in the pipeline. The complete Document
Intelligence response is written to blob storage *before* a single field is
mapped, and it is never modified afterwards.

Two things fall out of that:

* **A parsing bug costs nothing to fix.** NWD-142 was a mapping bug. Because the
  raw responses were already in bronze, the affected statements were reprocessed
  from stored JSON rather than re-analysed — no second per-page charge, and no
  asking Broker Alpha to resend a month of statements.
* **Auditability.** Every warehouse row carries ``bronze_path``. Given a number
  in a report, you can produce the exact API response it was derived from and
  the PDF that produced that.

Bronze is also the only place unredacted content exists. The container is
access-restricted and lifecycle-managed to cool/archive; silver and gold see
redacted values only.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import get_settings
from core.clients import blobs

log = logging.getLogger(__name__)


def bronze_path_for(digest: str, source_key: str, when: datetime | None = None) -> str:
    """Deterministic bronze path for a document.

    Keyed on the content hash, so the same bytes always land in the same place —
    reprocessing overwrites rather than accumulating near-duplicates. Partitioned
    by date so the lifecycle policy can age whole days out to archive.
    """
    stamp = (when or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return (
        f"{source_key}/{stamp:%Y}/{stamp:%m}/{stamp:%d}/{digest}.json"
    )


def write_bronze(*, digest: str, source_key: str, payload: dict[str, Any] | None) -> str:
    """Persist the raw analysis response. Returns the full container-qualified path.

    Overwrite is intentional: the path is content-addressed, so an overwrite can
    only ever be the identical document being re-analysed.
    """
    settings = get_settings()
    relative = bronze_path_for(digest, source_key)

    client = blobs().get_blob_client(container=settings.bronze_container, blob=relative)
    body = json.dumps(payload or {}, default=str, separators=(",", ":")).encode("utf-8")
    client.upload_blob(body, overwrite=True)

    full_path = f"{settings.bronze_container}/{relative}"
    log.info(
        "bronze_written",
        extra={"bronze_path": full_path, "bytes": len(body), "source": source_key},
    )
    return full_path


def read_bronze(bronze_path: str) -> dict[str, Any]:
    """Read a stored response back. This is what makes reprocessing free."""
    container, _, relative = bronze_path.partition("/")
    client = blobs().get_blob_client(container=container, blob=relative)
    return json.loads(client.download_blob().readall())


def read_raw(blob_path: str) -> bytes:
    """Fetch the original PDF bytes.

    ``blob_path`` is container-qualified (``raw/broker_alpha/2026-07-31/x.pdf``),
    which is the form the blob trigger reports and the form stored on the ledger.
    """
    container, _, relative = blob_path.partition("/")
    client = blobs().get_blob_client(container=container, blob=relative)
    return client.download_blob().readall()


def relative_path(blob_name: str, container: str) -> str:
    """Strip the leading container segment from a blob name.

    ``source_for_blob`` matches on the path *inside* the raw container, because
    the prefix in ``sources.yaml`` is what the counterparty's SFTP drop writes,
    not the container it happens to live in.
    """
    prefix = f"{container}/"
    return blob_name[len(prefix) :] if blob_name.startswith(prefix) else blob_name


def copy_to_review(blob_path: str, digest: str) -> str:
    """Place a copy of the source PDF where the analyst UI can render it.

    The raw container is immutable and audit-scoped; the review container is the
    working copy the exception queue screen links to, and it can be cleaned up
    once the item is resolved.
    """
    settings = get_settings()
    content = read_raw(blob_path)
    relative = f"{digest}.pdf"

    client = blobs().get_blob_client(container=settings.review_container, blob=relative)
    client.upload_blob(content, overwrite=True)

    full_path = f"{settings.review_container}/{relative}"
    log.info("review_copy_written", extra={"review_path": full_path, "hash": digest})
    return full_path
