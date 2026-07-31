"""Azure Function entry points for the counterparty ingestion pipeline.

Three triggers, and the split between the first two is the important part.

``on_statement_landed`` (blob trigger)
    Fires when a PDF lands in ``raw/``. It does almost nothing: hashes the
    content, checks the ledger, and enqueues a message. It does **not** analyse
    the document. The Consumption plan caps execution at 5 minutes (10 if
    configured) and a 50-page scanned statement can outrun that; a trigger that
    times out mid-analysis leaves a half-processed document and a retry storm.
    Enqueue and return.

``analyse_statement`` (queue trigger)
    Does the real work, with a queue's retry and poison handling underneath it.
    A corrupt PDF that throws every time is capped by ``host.json`` and lands in
    the poison queue with the exception recorded, instead of retrying forever.

``daily_reconciliation`` (timer trigger)
    Pulls the Aladdin feed and joins it against the silver rows that cleared the
    gate. This is the control the whole pipeline serves, and running it on a
    schedule immediately after the ingestion window is what moves break detection
    from T+2 to T+1.

The pipeline order inside the worker is deliberate and each step earns its place:

    read -> classify -> extract -> BRONZE -> translate -> rules -> redact
         -> transform -> silver -> gold -> ledger

Bronze before parsing, so a parsing bug is reprocessed for free. Translate before
the rules, so normalisation and validation see English. Rules before redaction,
so validation sees real values. Redaction before persistence, always.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

import azure.functions as func

from config.settings import SourceConfig, get_settings
from core import classify, idempotency, redact, rules, translate
from core import extract as extraction
from core.logging_config import configure_logging, correlation_scope, new_correlation_id
from recon import reconcile
from sinks import blob_sink, snowflake_sink, sql_sink
from sources.aladdin_api import AladdinClient

configure_logging()
log = logging.getLogger(__name__)

app = func.FunctionApp()


# -----------------------------------------------------------------------------
# 1. Land -> enqueue
# -----------------------------------------------------------------------------


@app.blob_trigger(arg_name="blob", path="raw/{name}", connection="StatementsStorage")
@app.queue_output(
    arg_name="analysis_queue", queue_name="doc-analysis", connection="StatementsStorage"
)
def on_statement_landed(blob: func.InputStream, analysis_queue: func.Out[str]) -> None:
    """Hash the arriving document and enqueue it for analysis.

    The duplicate check happens here rather than in the worker so a resent
    statement never costs a queue round trip — or, more importantly, a per-page
    extraction charge.
    """
    correlation_id = new_correlation_id()
    with correlation_scope(correlation_id):
        settings = get_settings()
        blob_path = blob.name or ""
        content = blob.read()

        # NWD-140: the digest is of the CONTENT. Counterparties resend the same
        # statement under a new filename constantly; the bytes are the identity.
        digest = idempotency.content_hash(content)

        log.info(
            "ingest_landed",
            extra={"blob_path": blob_path, "bytes": len(content), "hash": digest},
        )

        with sql_sink.connection() as conn:
            if idempotency.already_processed(conn, digest):
                log.info("skipped_duplicate", extra={"blob_path": blob_path, "hash": digest})
                return

        analysis_queue.set(
            json.dumps(
                {
                    "correlation_id": correlation_id,
                    "blob_path": blob_path,
                    "content_hash": digest,
                    "container": settings.raw_container,
                }
            )
        )
        log.info("analysis_enqueued", extra={"blob_path": blob_path, "hash": digest})


# -----------------------------------------------------------------------------
# 2. Analyse
# -----------------------------------------------------------------------------


@app.queue_trigger(
    arg_name="msg", queue_name="doc-analysis", connection="StatementsStorage"
)
def analyse_statement(msg: func.QueueMessage) -> None:
    """Classify, extract, gate, validate, redact, transform and load one document."""
    message = json.loads(msg.get_body().decode("utf-8"))
    blob_path: str = message["blob_path"]
    expected_hash: str = message["content_hash"]

    with correlation_scope(message.get("correlation_id")):
        settings = get_settings()
        content = blob_sink.read_raw(blob_path)

        # Re-hash rather than trusting the message: the queue is at-least-once,
        # and a message could in principle outlive an overwritten blob.
        digest = idempotency.content_hash(content)
        if digest != expected_hash:
            log.warning(
                "content_changed_since_enqueue",
                extra={"blob_path": blob_path, "expected": expected_hash, "actual": digest},
            )

        relative = blob_sink.relative_path(blob_path, settings.raw_container)

        with sql_sink.connection() as conn:
            if idempotency.already_processed(conn, digest):
                log.info("skipped_duplicate", extra={"blob_path": blob_path, "hash": digest})
                return

            try:
                source = settings.source_for_blob(relative)
            except ValueError as exc:
                _to_exception_queue(
                    conn,
                    digest=digest,
                    blob_path=blob_path,
                    bronze_path=None,
                    source_key="unknown",
                    reason=str(exc),
                    model_id="unknown",
                    pages=0,
                )
                return

            try:
                _process(conn, content, digest, blob_path, source)
            except Exception as exc:  # noqa: BLE001 - recorded, then re-raised
                log.exception(
                    "ingest_failed", extra={"blob_path": blob_path, "error": str(exc)}
                )
                idempotency.record_processed(
                    conn,
                    digest=digest,
                    blob_path=blob_path,
                    model_id=source.model_id,
                    pages=0,
                    status=idempotency.STATUS_FAILED,
                    reason=str(exc)[:400],
                )
                # Let the Function runtime retry, then poison-queue. The ledger
                # row above means the failure is visible either way.
                raise


def _process(
    conn,
    content: bytes,
    digest: str,
    blob_path: str,
    source: SourceConfig,
) -> None:
    """The pipeline proper, for one document. Ordering is load-bearing."""

    # -- classify: confirm the layout matches the path-based routing ----------
    classification = classify.classify(content, source)
    if not classify.matches_expected(classification, source):
        _to_exception_queue(
            conn,
            digest=digest,
            blob_path=blob_path,
            bronze_path=None,
            source_key=source.key,
            reason=(
                f"layout_mismatch: expected {source.doc_type}, "
                f"classifier said {classification.doc_type} "
                f"({classification.confidence:.2f})"
            ),
            model_id=source.model_id,
            pages=0,
        )
        return

    # -- extract --------------------------------------------------------------
    extracted = extraction.analyze(content, source)

    # -- bronze: persist the full response BEFORE parsing anything ------------
    bronze_path = blob_sink.write_bronze(
        digest=digest, source_key=source.key, payload=extracted.raw_response
    )

    if extracted.page_count > source.max_pages:
        _to_exception_queue(
            conn,
            digest=digest,
            blob_path=blob_path,
            bronze_path=bronze_path,
            source_key=source.key,
            reason=f"page_limit_exceeded: {extracted.page_count} > {source.max_pages}",
            model_id=source.model_id,
            pages=extracted.page_count,
        )
        return

    # -- translate EM documents before anything reasons about the text --------
    extracted = translate.translate_document(extracted, source)

    # -- rules engine: confidence gate + validation + normalisation ----------
    result = rules.evaluate(extracted, source)
    if not result.passed:
        _to_exception_queue(
            conn,
            digest=digest,
            blob_path=blob_path,
            bronze_path=bronze_path,
            source_key=source.key,
            reason=result.reason,
            model_id=source.model_id,
            pages=extracted.page_count,
            failures=result.to_failures(),
        )
        return

    # From here on, use the NORMALISED document the engine returned.
    document = result.document

    # -- redact PII before anything is persisted downstream -------------------
    document = redact.redact_document(document, source)

    # -- transform and load ---------------------------------------------------
    rows = sql_sink.to_rows(
        document, source, digest=digest, bronze_path=bronze_path, blob_path=blob_path
    )
    sql_sink.upsert_positions(conn, rows)
    snowflake_sink.load_positions(rows)

    idempotency.record_processed(
        conn,
        digest=digest,
        blob_path=blob_path,
        model_id=source.model_id,
        pages=extracted.page_count,
        status=idempotency.STATUS_LOADED,
        reason=None if result.straight_through else "loaded_with_warnings",
    )

    log.info(
        "ingest_completed",
        extra={
            "blob_path": blob_path,
            "hash": digest,
            "source": source.key,
            "rows": len(rows),
            "pages": extracted.page_count,
            "warnings": len(result.warnings),
            # The straight-through rate is the headline metric: the proportion of
            # documents that needed zero human touch. 61% at go-live, 85% target.
            "straight_through": result.straight_through,
        },
    )


def _to_exception_queue(
    conn,
    *,
    digest: str,
    blob_path: str,
    bronze_path: str | None,
    source_key: str,
    reason: str,
    model_id: str,
    pages: int,
    failures: list[dict] | None = None,
) -> None:
    """Route a refused document to the analyst queue and mark the ledger.

    Both writes happen inside the caller's transaction, so a document is never
    marked reviewed without a queue item for an analyst to actually work.
    """
    review_path = blob_sink.copy_to_review(blob_path, digest)
    sql_sink.write_exception(
        conn,
        digest=digest,
        blob_path=blob_path,
        bronze_path=bronze_path,
        source_key=source_key,
        reason=reason,
        failures=failures,
        review_path=review_path,
    )
    idempotency.record_processed(
        conn,
        digest=digest,
        blob_path=blob_path,
        model_id=model_id,
        pages=pages,
        status=idempotency.STATUS_REVIEW,
        reason=reason,
    )


# -----------------------------------------------------------------------------
# 3. Reconcile
# -----------------------------------------------------------------------------


@app.timer_trigger(
    arg_name="timer",
    # 06:30 UTC, after the overnight counterparty drop and before London opens.
    schedule="0 30 6 * * *",
    run_on_startup=False,
)
def daily_reconciliation(timer: func.TimerRequest) -> None:
    """Join yesterday's Aladdin positions against the extracted statements.

    Only rows that cleared the confidence gate exist in silver, which is what
    keeps this report free of extraction-noise false positives.
    """
    with correlation_scope():
        as_of = date.today() - timedelta(days=1)
        client = AladdinClient.from_environment()
        internal = client.positions_frame(as_of)

        with sql_sink.connection() as conn:
            external = sql_sink.fetch_positions_for_recon(conn, as_of.isoformat())

        breaks = reconcile.reconcile(internal, external, as_of)

        log.info(
            "reconciliation_report",
            extra={
                "as_of": as_of.isoformat(),
                "breaks": len(breaks),
                "by_type": reconcile.summarise(breaks),
            },
        )
