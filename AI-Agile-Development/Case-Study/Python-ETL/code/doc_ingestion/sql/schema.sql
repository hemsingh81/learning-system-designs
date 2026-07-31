-- =============================================================================
-- Northwind counterparty ingestion — supporting schema
--
-- Two engines, deliberately:
--   * Azure SQL holds the operational tables — the idempotency ledger, the
--     analyst exception queue, and the silver staging rows.
--   * Snowflake holds gold, which the EM and EQ reporting modules read.
--
-- Column names here match `core/transform.py::COLUMNS` exactly. If you change
-- one, change both — the sinks build their statements from that tuple, so a
-- drift is a runtime error rather than a silent mismatch, but it is still an
-- error somebody has to debug at 07:00.
--
-- Numeric columns are DECIMAL/NUMBER, never FLOAT. The reconciliation tolerance
-- is 0.0001 on quantity; binary floating point cannot honour that.
-- =============================================================================


-- =============================================================================
-- PART 1 — Azure SQL
-- =============================================================================

IF SCHEMA_ID('etl') IS NULL EXEC('CREATE SCHEMA etl');
GO
IF SCHEMA_ID('silver') IS NULL EXEC('CREATE SCHEMA silver');
GO


-- -----------------------------------------------------------------------------
-- The processed-document ledger. This is what makes ingestion idempotent.
--
-- NWD-140: the primary key is the SHA-256 of the document CONTENT, not the
-- filename. Counterparties resend the same statement under new names constantly;
-- hashing the name let a resend load twice.
-- -----------------------------------------------------------------------------
CREATE TABLE etl.processed_document (
    content_hash   CHAR(64)       NOT NULL PRIMARY KEY,
    blob_path      NVARCHAR(1024) NOT NULL,
    model_id       NVARCHAR(128)  NOT NULL,
    page_count     INT            NOT NULL,
    status         VARCHAR(16)    NOT NULL,   -- loaded | review | failed | skipped
    reason         NVARCHAR(400)  NULL,
    created_utc    DATETIME2(3)   NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_utc    DATETIME2(3)   NULL
);
GO

CREATE INDEX ix_processed_status
    ON etl.processed_document (status, created_utc);
GO


-- -----------------------------------------------------------------------------
-- The exception queue the analysts work from. This table IS the UI's backing
-- store — Ji-woo's screen renders `failures_json` directly, which is why the
-- rules engine emits structured violations rather than a reason string alone.
--
-- `resolution` closes the loop: rows marked `model_error` are exactly the
-- training set for the next model version.
-- -----------------------------------------------------------------------------
CREATE TABLE etl.extraction_exception (
    exception_id   BIGINT IDENTITY(1,1) PRIMARY KEY,
    content_hash   CHAR(64)       NOT NULL,
    blob_path      NVARCHAR(1024) NOT NULL,
    bronze_path    NVARCHAR(1024) NULL,
    review_path    NVARCHAR(1024) NULL,
    source_key     NVARCHAR(64)   NOT NULL,
    reason         NVARCHAR(400)  NOT NULL,
    -- [{rule_id, rule_type, severity, message, field, row, observed, expected}]
    failures_json  NVARCHAR(MAX)  NULL,
    assigned_to    NVARCHAR(128)  NULL,
    resolved_utc   DATETIME2(3)   NULL,
    resolution     VARCHAR(32)    NULL,       -- corrected | rejected | model_error
    created_utc    DATETIME2(3)   NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX ix_exception_open
    ON etl.extraction_exception (resolved_utc, created_utc)
    INCLUDE (source_key, reason);
GO

CREATE INDEX ix_exception_hash
    ON etl.extraction_exception (content_hash);
GO


-- -----------------------------------------------------------------------------
-- Silver: typed, gated, validated rows. Only documents that cleared the
-- confidence gate AND the rules engine appear here. That is the invariant that
-- keeps the break report free of extraction noise.
--
-- Natural key is (content_hash, line_no): the hash identifies the document, the
-- line number the position within it. The same security can legitimately appear
-- twice on one statement, so security_id alone is not a key.
-- -----------------------------------------------------------------------------
CREATE TABLE silver.counterparty_position (
    content_hash     CHAR(64)        NOT NULL,
    source_key       NVARCHAR(64)    NOT NULL,
    doc_type         NVARCHAR(64)    NOT NULL,
    account_number   NVARCHAR(64)    NOT NULL,
    security_id      NVARCHAR(64)    NOT NULL,
    security_name    NVARCHAR(256)   NULL,
    statement_date   DATE            NOT NULL,
    trade_date       DATE            NULL,
    settlement_date  DATE            NULL,
    line_no          INT             NOT NULL,
    side             VARCHAR(8)      NULL,       -- BUY | SELL, normalised
    quantity         DECIMAL(28, 8)  NOT NULL,
    price            DECIMAL(28, 8)  NULL,
    market_value     DECIMAL(28, 4)  NULL,
    currency         CHAR(3)         NULL,
    -- The audit trio. Do not drop these to "tidy up the schema": together with
    -- bronze they are how any number in a report is traced back to a PDF.
    min_confidence   DECIMAL(5, 4)   NOT NULL,
    model_id         NVARCHAR(128)   NOT NULL,
    bronze_path      NVARCHAR(1024)  NOT NULL,
    blob_path        NVARCHAR(1024)  NOT NULL,
    extracted_utc    DATETIME2(3)    NOT NULL,
    created_utc      DATETIME2(3)    NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_utc      DATETIME2(3)    NULL,
    CONSTRAINT pk_counterparty_position PRIMARY KEY (content_hash, line_no)
);
GO

-- The reconciliation join. account_number + security_id is the grain a position
-- is held at; statement_date scopes the run.
CREATE INDEX ix_position_recon
    ON silver.counterparty_position (statement_date, account_number, security_id)
    INCLUDE (quantity, market_value, currency, min_confidence);
GO

CREATE INDEX ix_position_source
    ON silver.counterparty_position (source_key, statement_date);
GO


-- -----------------------------------------------------------------------------
-- Operational views. Straight-through rate is the single most useful number in
-- the system: it is simultaneously the business metric (manual work removed),
-- the model health metric, and the early warning that a counterparty changed
-- their template.
-- -----------------------------------------------------------------------------
CREATE VIEW etl.vw_straight_through_rate AS
SELECT
    CAST(created_utc AS DATE)                                    AS processing_date,
    COUNT(*)                                                     AS documents,
    SUM(CASE WHEN status = 'loaded' THEN 1 ELSE 0 END)           AS loaded,
    SUM(CASE WHEN status = 'review' THEN 1 ELSE 0 END)           AS sent_to_review,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)           AS failed,
    CAST(SUM(CASE WHEN status = 'loaded' AND reason IS NULL THEN 1.0 ELSE 0 END)
         / NULLIF(COUNT(*), 0) AS DECIMAL(5, 4))                 AS straight_through_rate
FROM etl.processed_document
GROUP BY CAST(created_utc AS DATE);
GO

CREATE VIEW etl.vw_open_exceptions AS
SELECT
    e.exception_id,
    e.content_hash,
    e.source_key,
    e.reason,
    e.blob_path,
    e.bronze_path,
    e.review_path,
    e.failures_json,
    e.assigned_to,
    e.created_utc,
    DATEDIFF(HOUR, e.created_utc, SYSUTCDATETIME()) AS age_hours
FROM etl.extraction_exception AS e
WHERE e.resolved_utc IS NULL;
GO


-- =============================================================================
-- PART 2 — Snowflake (gold)
--
-- Run this against NORTHWIND_ANALYTICS. Loads stage into STG_ and MERGE into the
-- target; nothing ever INSERTs into COUNTERPARTY_POSITION directly, so a re-run
-- converges instead of duplicating.
-- =============================================================================

/*
CREATE SCHEMA IF NOT EXISTS GOLD;

CREATE TABLE IF NOT EXISTS GOLD.COUNTERPARTY_POSITION (
    CONTENT_HASH     VARCHAR(64)    NOT NULL,
    SOURCE_KEY       VARCHAR(64)    NOT NULL,
    DOC_TYPE         VARCHAR(64)    NOT NULL,
    ACCOUNT_NUMBER   VARCHAR(64)    NOT NULL,
    SECURITY_ID      VARCHAR(64)    NOT NULL,
    SECURITY_NAME    VARCHAR(256),
    STATEMENT_DATE   DATE           NOT NULL,
    TRADE_DATE       DATE,
    SETTLEMENT_DATE  DATE,
    LINE_NO          NUMBER(9, 0)   NOT NULL,
    SIDE             VARCHAR(8),
    QUANTITY         NUMBER(28, 8)  NOT NULL,
    PRICE            NUMBER(28, 8),
    MARKET_VALUE     NUMBER(28, 4),
    CURRENCY         VARCHAR(3),
    -- Carried into the warehouse so an audit question is answerable in SQL.
    MIN_CONFIDENCE   NUMBER(5, 4)   NOT NULL,
    MODEL_ID         VARCHAR(128)   NOT NULL,
    BRONZE_PATH      VARCHAR(1024)  NOT NULL,
    BLOB_PATH        VARCHAR(1024)  NOT NULL,
    EXTRACTED_UTC    TIMESTAMP_NTZ  NOT NULL,
    CREATED_UTC      TIMESTAMP_NTZ  NOT NULL,
    UPDATED_UTC      TIMESTAMP_NTZ,
    CONSTRAINT PK_COUNTERPARTY_POSITION PRIMARY KEY (CONTENT_HASH, LINE_NO)
);

-- Staging is a scratch table: every load truncates and rewrites it.
CREATE TABLE IF NOT EXISTS GOLD.STG_COUNTERPARTY_POSITION LIKE GOLD.COUNTERPARTY_POSITION;

ALTER TABLE GOLD.STG_COUNTERPARTY_POSITION DROP COLUMN CREATED_UTC;
ALTER TABLE GOLD.STG_COUNTERPARTY_POSITION DROP COLUMN UPDATED_UTC;

-- The break report the EM / EQ modules read alongside the positions.
CREATE TABLE IF NOT EXISTS GOLD.RECONCILIATION_BREAK (
    AS_OF_DATE           DATE           NOT NULL,
    ACCOUNT_NUMBER       VARCHAR(64)    NOT NULL,
    SECURITY_ID          VARCHAR(64)    NOT NULL,
    BREAK_TYPE           VARCHAR(32)    NOT NULL,  -- MISSING_EXTERNAL | MISSING_INTERNAL
                                                   -- | QUANTITY_BREAK | VALUE_BREAK
    QUANTITY_ALADDIN     NUMBER(28, 8),
    QUANTITY_CPTY        NUMBER(28, 8),
    MARKET_VALUE_ALADDIN NUMBER(28, 4),
    MARKET_VALUE_CPTY    NUMBER(28, 4),
    DIFFERENCE           NUMBER(28, 8),
    CONTENT_HASH         VARCHAR(64),
    BRONZE_PATH          VARCHAR(1024),
    MIN_CONFIDENCE       NUMBER(5, 4),
    CREATED_UTC          TIMESTAMP_NTZ  NOT NULL
);
*/
