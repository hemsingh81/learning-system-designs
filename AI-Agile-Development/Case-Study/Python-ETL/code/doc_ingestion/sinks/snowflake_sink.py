"""Snowflake gold load: stage, then MERGE. Never INSERT into the target.

Gold is what the EM and EQ reporting modules read. Two properties matter more
than throughput.

**Idempotent at the row level.** The load stages into
``GOLD.STG_COUNTERPARTY_POSITION`` and MERGEs from there. A re-run — after a
transient failure, after an analyst correction, after a reprocess from bronze —
converges on the same target rows instead of accumulating duplicates. A direct
INSERT would make every retry a data quality incident.

**Audit columns travel with the data.** ``MIN_CONFIDENCE`` and ``BRONZE_PATH``
are carried into the warehouse row on purpose. When somebody queries a number in
a report, those two columns answer "how sure was the model, and where is the
original?" without leaving SQL. They are the reason this pipeline can be
defended in an audit rather than merely explained.

Authentication is key-pair (JWT), not a password. The private key is held in Key
Vault and read with the Function's managed identity.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from core.transform import COLUMNS, CounterpartyPosition

log = logging.getLogger(__name__)

TARGET_TABLE = "GOLD.COUNTERPARTY_POSITION"
STAGING_TABLE = "GOLD.STG_COUNTERPARTY_POSITION"

# Snowflake identifiers are upper-case by convention; the canonical column list
# in core.transform stays the single source of truth for what those columns are.
SNOWFLAKE_COLUMNS: tuple[str, ...] = tuple(c.upper() for c in COLUMNS)

# The natural key. Content hash pins the document, line number pins the position
# within it; account, security and date are included so a human reading the
# MERGE can see what identity means here.
_MERGE_KEY = ("CONTENT_HASH", "LINE_NO", "ACCOUNT_NUMBER", "SECURITY_ID", "STATEMENT_DATE")
_UPDATABLE = tuple(c for c in SNOWFLAKE_COLUMNS if c not in _MERGE_KEY)


@contextmanager
def connection() -> Iterator[Any]:
    """A Snowflake connection using key-pair auth."""
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="SNOWFLAKE_JWT",
        # Key-pair auth, not a password. The key file is mounted from Key Vault.
        private_key_file=os.environ["SNOWFLAKE_KEY_PATH"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ.get("SNOWFLAKE_DATABASE", "NORTHWIND_ANALYTICS"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "GOLD"),
    )
    try:
        yield conn
    finally:
        conn.close()


def rows_to_frame(rows: Sequence[CounterpartyPosition]):
    """Build the staging DataFrame with upper-case canonical columns.

    ``Decimal`` values are left as ``Decimal`` objects rather than being cast to
    float. ``write_pandas`` writes them to a NUMBER column without going through
    binary floating point, which is the whole reason the transform produced
    Decimals in the first place.
    """
    import pandas as pd

    frame = pd.DataFrame(
        [row.as_dict() for row in rows],
        columns=list(COLUMNS),
        dtype=object,
    )
    frame.columns = list(SNOWFLAKE_COLUMNS)
    return frame


def _merge_statement() -> str:
    on_clause = "\n      AND ".join(f"t.{c} = s.{c}" for c in _MERGE_KEY)
    set_clause = ",\n        ".join(f"t.{c} = s.{c}" for c in _UPDATABLE)
    insert_cols = ", ".join(SNOWFLAKE_COLUMNS)
    insert_vals = ", ".join(f"s.{c}" for c in SNOWFLAKE_COLUMNS)
    return f"""
MERGE INTO {TARGET_TABLE} AS t
USING {STAGING_TABLE} AS s
  ON  {on_clause}
WHEN MATCHED THEN UPDATE SET
        {set_clause},
        t.UPDATED_UTC = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT
    ({insert_cols}, CREATED_UTC)
    VALUES ({insert_vals}, CURRENT_TIMESTAMP());
"""


def load_positions(rows: Sequence[CounterpartyPosition]) -> int:
    """Stage then MERGE. Returns the number of rows the MERGE touched.

    ``overwrite=True`` on the staging write is safe and deliberate: staging is a
    scratch table, and truncating it per load stops a failed previous run from
    replaying rows nobody asked for.
    """
    if not rows:
        return 0

    from snowflake.connector.pandas_tools import write_pandas

    frame = rows_to_frame(rows)

    with connection() as conn:
        write_pandas(
            conn,
            frame,
            "STG_COUNTERPARTY_POSITION",
            schema="GOLD",
            auto_create_table=False,
            overwrite=True,
            quote_identifiers=False,
        )
        cursor = conn.cursor()
        try:
            cursor.execute(_merge_statement())
            affected = cursor.rowcount or 0
        finally:
            cursor.close()
        conn.commit()

    log.info(
        "gold_merged",
        extra={
            "rows_staged": len(rows),
            "rows_merged": affected,
            "content_hash": rows[0].content_hash,
        },
    )
    return affected
