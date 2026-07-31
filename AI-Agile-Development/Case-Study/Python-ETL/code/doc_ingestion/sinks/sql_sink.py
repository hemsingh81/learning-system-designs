"""Azure SQL: the silver staging table and the analyst exception queue.

Silver is typed, validated rows derived from bronze. Gold (Snowflake) is loaded
from here. Two habits govern every write in this module.

**MERGE, never INSERT.** Document-level idempotency (the content-hash ledger)
stops the same statement being processed twice; row-level idempotency stops a
partial failure and retry from duplicating positions. You need both, because the
failure can happen between the two.

**Rejections are data, not exceptions.** Anything the confidence gate or the
rules engine refused is written to ``etl.extraction_exception`` with the reason
and the structured violations attached. That table is Ji-woo's exception queue
screen, and it is where Priya spends her morning — so the row has to carry
enough to fix the document without opening the PDF blind.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from config.settings import SourceConfig
from core import transform
from core.extract import ExtractedDocument
from core.transform import COLUMNS, CounterpartyPosition

log = logging.getLogger(__name__)

SILVER_TABLE = "silver.counterparty_position"
EXCEPTION_TABLE = "etl.extraction_exception"


def _connection_string() -> str:
    """ODBC connection string.

    Authentication is ``ActiveDirectoryMsi`` — the Function's managed identity,
    mapped to a contained database user. No SQL password exists to leak.
    """
    return os.environ["SQL_CONNECTION_STRING"]


@contextmanager
def connection() -> Iterator[Any]:
    """A committed-or-rolled-back connection scope.

    ``autocommit=False`` so a document's silver rows and its ledger entry either
    both land or neither does. A half-written document is the exact condition
    that produces a phantom reconciliation break.
    """
    import pyodbc

    conn = pyodbc.connect(_connection_string(), autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def to_rows(
    doc: ExtractedDocument,
    source: SourceConfig,
    *,
    digest: str,
    bronze_path: str,
    blob_path: str,
) -> list[CounterpartyPosition]:
    """Adapter onto :func:`core.transform.to_positions`.

    The sink owns no mapping logic — it exists so the orchestrator has one
    obvious call site and the transform stays free of storage concerns.
    """
    return transform.to_positions(
        doc,
        source,
        content_hash=digest,
        bronze_path=bronze_path,
        blob_path=blob_path,
    )


_MERGE_POSITIONS = f"""
MERGE {SILVER_TABLE} AS t
USING (SELECT
        ? AS content_hash, ? AS source_key, ? AS doc_type, ? AS account_number,
        ? AS security_id, ? AS security_name, ? AS statement_date, ? AS trade_date,
        ? AS settlement_date, ? AS line_no, ? AS side, ? AS quantity, ? AS price,
        ? AS market_value, ? AS currency, ? AS min_confidence, ? AS model_id,
        ? AS bronze_path, ? AS blob_path, ? AS extracted_utc) AS s
  ON  t.content_hash = s.content_hash
  AND t.line_no      = s.line_no
WHEN MATCHED THEN UPDATE SET
    t.source_key      = s.source_key,
    t.doc_type        = s.doc_type,
    t.account_number  = s.account_number,
    t.security_id     = s.security_id,
    t.security_name   = s.security_name,
    t.statement_date  = s.statement_date,
    t.trade_date      = s.trade_date,
    t.settlement_date = s.settlement_date,
    t.side            = s.side,
    t.quantity        = s.quantity,
    t.price           = s.price,
    t.market_value    = s.market_value,
    t.currency        = s.currency,
    t.min_confidence  = s.min_confidence,
    t.model_id        = s.model_id,
    t.bronze_path     = s.bronze_path,
    t.blob_path       = s.blob_path,
    t.extracted_utc   = s.extracted_utc,
    t.updated_utc     = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
    ({", ".join(COLUMNS)}, created_utc)
    VALUES ({", ".join("s." + c for c in COLUMNS)}, SYSUTCDATETIME());
"""


def upsert_positions(conn: Any, rows: Sequence[CounterpartyPosition]) -> int:
    """MERGE canonical rows into silver. Returns the number written.

    The natural key is ``(content_hash, line_no)``. Content hash identifies the
    document uniquely and line number identifies the position within it — the
    same security can legitimately appear twice on one statement across two
    settlement dates, so security id alone is not a key.
    """
    if not rows:
        return 0

    cursor = conn.cursor()
    try:
        cursor.fast_executemany = True
        cursor.executemany(_MERGE_POSITIONS, [row.as_tuple() for row in rows])
    finally:
        cursor.close()

    log.info(
        "silver_upserted",
        extra={
            "rows": len(rows),
            "content_hash": rows[0].content_hash,
            "source": rows[0].source_key,
        },
    )
    return len(rows)


def write_exception(
    conn: Any,
    *,
    digest: str,
    blob_path: str,
    bronze_path: str | None,
    source_key: str,
    reason: str,
    failures: Sequence[dict[str, Any]] | None = None,
    review_path: str | None = None,
) -> None:
    """Queue a document for analyst review with the reason it was refused.

    ``failures_json`` carries the structured violations — field, row, observed,
    expected. The UI renders those directly, which is what lets Priya correct a
    document in one pass instead of guessing which of forty numbers was wrong.
    """
    conn.execute(
        f"""
        INSERT INTO {EXCEPTION_TABLE}
            (content_hash, blob_path, bronze_path, review_path, source_key,
             reason, failures_json, created_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME());
        """,
        digest,
        blob_path,
        bronze_path,
        review_path,
        source_key,
        reason[:400],
        json.dumps(list(failures or []), default=str),
    )

    log.warning(
        "exception_queued",
        extra={
            "hash": digest,
            "blob_path": blob_path,
            "source": source_key,
            "reason": reason,
            "failure_count": len(failures or []),
        },
    )


def fetch_positions_for_recon(conn: Any, as_of: str, account_number: str | None = None):
    """Read silver rows for a reconciliation run, as a DataFrame.

    Only rows that cleared the gate exist in this table, which is what keeps the
    break report free of false positives.
    """
    import pandas as pd

    sql = f"""
        SELECT account_number, security_id, security_name, quantity, market_value,
               currency, min_confidence, bronze_path, content_hash
        FROM {SILVER_TABLE}
        WHERE statement_date = ?
    """
    params: list[Any] = [as_of]
    if account_number:
        sql += " AND account_number = ?"
        params.append(account_number)

    return pd.read_sql(sql, conn, params=params)
