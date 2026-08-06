# 17 · Deep Dive: Python & Data (10 questions)

[← Deep Dive: React & TypeScript](16-deepdive-react-typescript.md) · [Home](README.md) · [Next → Coding-Round Prep](18-coding-round-prep.md)

This is the Python/data-heavy round — where they test the ETL and AI side. I personally built the FastAPI ETL services that ingest BlackRock Aladdin data on TCW (A), the Sculptor/Bain reporting ETL (D), and the firm's first production RAG app (B), so I answer from real ingestion, transformation and data code.

> Opening line for a data-deep panel: *"My Python is production ETL, not notebooks. Validate at the boundary with Pydantic, transform set-based, load idempotently, and reconcile counts — so when the daily reporting deadline hits, the numbers are right and I can prove it."*

**Jump to:** [P1 async Python](#p1--async-python-that-actually-helps) · [P2 Pydantic v2](#p2--pydantic-v2-validation-at-the-boundary) · [P3 Pandas ETL](#p3--pandas-transform-vectorised) · [P4 idempotent load](#p4--idempotent-loads-and-reconciliation) · [P5 SQL tuning](#p5--sql-tuning-and-sargability) · [P6 Snowflake](#p6--snowflake-vs-sql-server) · [P7 orchestration](#p7--orchestration-airflow-adf-tidal) · [P8 RAG code](#p8--rag-the-code-behind-the-4-pillars) · [P9 packaging & quality](#p9--packaging-typing-and-quality) · [P10 testing data](#p10--testing-data-pipelines) · [Section index](#section-index)

---

## P1 · Async Python that actually helps

**What they are testing.** Whether I know when async helps in Python — and the GIL trap.

**How I answer.** Python has the GIL, so threads don't give true CPU parallelism. That shapes the rule:

- **I/O-bound** (API calls, DB, files) → `asyncio` — huge win, one thread handles many waits.
- **CPU-bound** (heavy number-crunching) → `multiprocessing` — separate processes side-step the GIL.

Ingesting many Aladdin entity types is I/O-bound, so async with bounded concurrency (the Python twin of [F2](14-fullstack-hands-on.md#f2--how-do-you-write-correct-async-c)):

```python
import asyncio, httpx

async def fetch_all(entity_types: list[str]) -> list[dict]:
    sem = asyncio.Semaphore(4)  # never more than 4 concurrent calls to a rate-limited API
    async with httpx.AsyncClient(timeout=10) as client:
        async def one(t: str) -> dict:
            async with sem:
                r = await client.get(f"/aladdin/{t}")
                r.raise_for_status()
                return r.json()
        return await asyncio.gather(*(one(t) for t in entity_types))
```

`asyncio.gather` runs them concurrently; the semaphore caps it at 4 so I respect the API's rate limit. This turned a serial ingest that fetched entity types one after another into a concurrent one — material time saved inside the deadline window.

**Lesson.** *"Async Python is for I/O waits, not CPU — the GIL means threads won't parallelise computation. I fetch the Aladdin feeds concurrently with a bounded semaphore, which respects the rate limit and still cuts wall-clock time."*

**Follow-ups**
- *"`asyncio.gather` vs `as_completed`?"* — `gather` waits for all; `as_completed` yields each as it finishes — useful to start loading the first results while others fetch.
- *"Blocking call inside async?"* — It blocks the whole event loop — wrap it in `run_in_executor` or use an async library.
- *"CPU-bound work?"* — `ProcessPoolExecutor` — real parallelism across processes.

---

## P2 · Pydantic v2 validation at the boundary

**What they are testing.** Whether bad data can enter my pipeline — in a regulated firm it must not.

**How I answer.** I validate at the boundary with Pydantic v2, so nothing untyped or malformed gets past the front door. The model *is* the contract:

```python
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

class Position(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)
    quantity: Decimal                       # Decimal, never float, for money
    market_value: Decimal = Field(ge=0)     # non-negative
    as_of: date

    @field_validator("ticker")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.strip().upper()

# one malformed row raises ValidationError with the exact field and reason
positions = [Position(**row) for row in raw_rows]
```

Two things I insist on: **`Decimal` not `float` for money** — floats give rounding errors that are unacceptable in financial reporting; and **validate early** — a bad row fails here with a precise message, not three steps later as a mysterious NaN in a report. Pydantic v2's core is in Rust, so this is fast even at volume.

**Lesson.** *"Pydantic validates at the boundary — the model is the contract, money is `Decimal` not `float`, and a bad row fails immediately with the exact field and reason. Catching it at the door is far cheaper than debugging a wrong number in a report."*

**Follow-ups**
- *"Why Decimal for money?"* — `0.1 + 0.2 != 0.3` in float; in financial reporting that rounding is a defect. `Decimal` is exact.
- *"`model_validate` vs constructor?"* — `model_validate` for dicts/JSON with full validation; both enforce the schema.
- *"Settings?"* — `pydantic-settings` for typed, validated config from env/Key Vault — same discipline as the .NET options pattern ([D10](15-deepdive-dotnet.md#d10--configuration-options-and-secrets)).

---

## P3 · Pandas transform, vectorised

**What they are testing.** Whether I transform data efficiently — or loop row-by-row and time out.

**How I answer.** The cardinal rule: **vectorise, never iterate**. `iterrows()` on a large frame is the Python equivalent of the N+1 — orders of magnitude too slow.

```python
import pandas as pd

# BAD — row-by-row Python loop over a big frame
# for i, row in df.iterrows(): df.at[i, 'weight'] = row.market_value / total

# GOOD — vectorised, runs in C under the hood
df["weight"] = df["market_value"] / df["market_value"].sum()
df["bucket"] = pd.cut(df["weight"], bins=[0, 0.01, 0.05, 1.0], labels=["small", "mid", "large"])

# joins instead of nested lookups
enriched = df.merge(ref_data, on="ticker", how="left", validate="many_to_one")
```

Other things I do at volume: pick **explicit dtypes** (and `category` for repeated strings like ticker) to cut memory; use `validate=` on merges so a bad join key fails loudly instead of silently duplicating rows; and when the data outgrows memory, I don't force Pandas — I push the heavy aggregation **down into SQL/Snowflake** ([P6](#p6--snowflake-vs-sql-server)) where it belongs, and only bring back the result.

**Lesson.** *"Vectorise, never `iterrows` — it's the Pandas N+1. Use explicit dtypes and validated merges, and when the data is too big for memory, push the aggregation into the warehouse instead of pulling it all into Python."*

**Follow-ups**
- *"Chained assignment / `SettingWithCopyWarning`?"* — It means I'm mutating a view; use `.loc` or `.copy()` deliberately.
- *"Pandas vs Polars/DuckDB?"* — For larger-than-comfortable data, Polars (lazy, multi-threaded) or DuckDB (SQL over files) — I choose the tool for the data size.
- *"Memory blow-ups?"* — `category` dtype, chunked reads (`chunksize`), and pushing aggregation to SQL.

---

## P4 · Idempotent loads and reconciliation

**What they are testing.** Whether re-running my pipeline is safe — the single most important property of production ETL.

**How I answer.** A pipeline **will** be re-run — after a failure, a fix, or a late file. If a re-run duplicates data, the report is wrong. So every load is idempotent, keyed by natural key + as-of date, and I reconcile counts after.

```python
def load_positions(conn, positions: list[Position], as_of: date) -> dict:
    with conn.begin():  # one transaction — all or nothing
        # idempotent: delete this as-of slice, then insert — re-run is safe
        conn.execute(text("DELETE FROM positions WHERE as_of = :d"), {"d": as_of})
        conn.execute(insert_stmt, [p.model_dump() for p in positions])

    # reconcile: prove the load is complete and correct
    loaded = conn.execute(text("SELECT COUNT(*) FROM positions WHERE as_of = :d"),
                          {"d": as_of}).scalar()
    if loaded != len(positions):
        raise ReconciliationError(f"expected {len(positions)}, loaded {loaded}")
    return {"as_of": str(as_of), "rows": loaded}
```

The pattern: **transaction** (partial loads are poison), **delete-then-insert by as-of key** (or a MERGE/upsert) so re-running replaces rather than duplicates, and a **reconciliation count** so the pipeline proves it loaded what it fetched. This is exactly what lets me meet the daily deadline with confidence — if step 3 fails, I re-run step 3, and it just works ([S1](07-support-post-delivery.md#s1--how-do-you-run-production-support-for-a-system-with-a-hard-daily-deadline)).

**Lesson.** *"Every load is idempotent — keyed by as-of date, wrapped in a transaction, and reconciled by count. A pipeline that duplicates data on re-run is a landmine; one you can safely re-run is a good night's sleep."*

**Follow-ups**
- *"Upsert vs delete-insert?"* — MERGE/upsert when I need to preserve unchanged rows; delete-insert for a full daily slice replacement. Both idempotent.
- *"Late-arriving / out-of-order data?"* — Key by business date, not load time, so a late file lands in the right slice.
- *"Partial failure mid-load?"* — The transaction rolls back; nothing half-loaded; re-run cleanly.

---

## P5 · SQL tuning and sargability

**What they are testing.** Whether I can make a slow query fast — the deadline often lives in one query ([S4](07-support-post-delivery.md#s4--how-do-you-tune-a-slow-query-in-production)).

**How I answer.** I read the execution plan first, then fix in cheap-to-expensive order. The commonest win is **sargability** — keeping the indexed column bare so the index can be used:

```sql
-- NOT sargable: function on the column disables the index → full scan
WHERE CONVERT(date, trade_time) = @asOf

-- Sargable: range on the bare column → index seek
WHERE trade_time >= @asOf AND trade_time < DATEADD(day, 1, @asOf)
```

My tuning order, said as a list: **measure the plan → sargable predicates → select only needed columns → rewrite set-based (kill row-by-row cursors) → then add indexes deliberately** (they cost on writes) **→ model for growth**. A real rewrite — replacing a self-join-per-row ranking with a window function:

```sql
SELECT ticker, market_value,
       RANK() OVER (PARTITION BY sector ORDER BY market_value DESC) AS rank_in_sector
FROM positions
WHERE as_of = @asOf;   -- one pass, no correlated subquery per row
```

**Lesson.** *"Plan first, then the cheap causes: make predicates sargable, select only what you need, rewrite set-based, and only then add indexes. A function wrapped around an indexed column is the most common reason a query full-scans."*

**Follow-ups**
- *"Covering index?"* — An index that includes all columns the query needs, so it never touches the table.
- *"Window functions?"* — Ranking/running-totals in one pass instead of correlated subqueries — big wins on reporting queries.
- *"Parameter sniffing?"* — A cached plan for one parameter that's bad for another; `OPTION (RECOMPILE)` or `OPTIMIZE FOR` where it bites.

---

## P6 · Snowflake vs SQL Server

**What they are testing.** Whether I understand the operational-vs-analytical split I actually built (A ingests Aladdin into **both** SQL Server and Snowflake).

**How I answer.** They are different tools for different jobs:

- **SQL Server** — the **operational** store: row-based, transactional (OLTP), great for the app's reads/writes and point lookups by key.
- **Snowflake** — the **analytical** store: columnar, massively parallel (OLAP), great for scanning and aggregating large history; compute (warehouses) scales separately from storage.

So on A I ingest Aladdin into SQL Server for the operational reporting app and into Snowflake for heavy analytics — the store-split one-liner: *"operational data serves the app; analytical data serves the questions."* Snowflake specifics I use: **micro-partitions + clustering** for pruning, separate **virtual warehouses** so an analyst's heavy query doesn't slow the load, and **zero-copy clones** for a test dataset without duplicating storage. I don't run OLTP point-writes on Snowflake or giant analytical scans on SQL Server — each does what it's shaped for.

**Lesson.** *"SQL Server is operational and row-based for the app; Snowflake is analytical and columnar for the questions. I ingest Aladdin into both because operational and analytical workloads want different engines — forcing one to do both is where performance dies."*

**Follow-ups**
- *"When does data move between them?"* — Batch loads on the schedule, plus reconciliation so both stores agree.
- *"Snowflake cost control?"* — Auto-suspend warehouses, right-size them, and cluster so queries prune — compute is the bill.
- *"Star schema?"* — Facts + dimensions in the analytical store so reporting queries and BI stay fast and simple.

---

## P7 · Orchestration: Airflow, ADF, Tidal

**What they are testing.** Whether I can make a multi-step pipeline reliable, ordered and observable — I ran exactly this across ADF, Tidal and Airflow on A.

**How I answer.** Orchestration is about **dependencies, retries, idempotency and visibility**. The steps form a DAG: fetch → validate → transform → load → reconcile → publish — each depending on the last, each retryable, each idempotent so a retry is safe.

```python
# Airflow DAG — dependency-aware, retrying, alerting
with DAG("aladdin_daily", schedule="0 3 * * *", catchup=False,
         default_args={"retries": 3, "retry_delay": timedelta(minutes=5),
                       "on_failure_callback": alert_ops}) as dag:
    fetch    = PythonOperator(task_id="fetch",    python_callable=fetch_all)
    validate = PythonOperator(task_id="validate", python_callable=validate_rows)
    load     = PythonOperator(task_id="load",     python_callable=load_positions)
    reconcile= PythonOperator(task_id="reconcile",python_callable=reconcile_counts)
    fetch >> validate >> load >> reconcile   # explicit dependency chain
```

The production properties that matter: **retries with backoff** on transient failures, **failure alerts** to ops so a 3 a.m. break is known before the 6 a.m. deadline, **idempotent tasks** so a retry doesn't duplicate ([P4](#p4--idempotent-loads-and-reconciliation)), and a **reconciliation gate** so nothing publishes unless the counts match. I chose the tool per environment — ADF for Azure-native movement, Airflow for complex Python DAGs, Tidal where enterprise scheduling already lived — and wrapped them in one dependency-aware layer to hit the daily window ([S1](07-support-post-delivery.md#s1--how-do-you-run-production-support-for-a-system-with-a-hard-daily-deadline)).

**Lesson.** *"Orchestration is dependencies, retries, idempotency and alerting in a DAG — fetch, validate, load, reconcile, publish, each retryable and safe to re-run. That dependency-aware layer is what let me guarantee the daily reporting window across three schedulers."*

**Follow-ups**
- *"Backfill?"* — Parameterise by business date so I can re-run any past day idempotently.
- *"Idempotency in orchestration?"* — Each task keyed by business date; a retry replaces its slice, never appends.
- *"Monitoring?"* — SLA on the DAG, alert on miss, and a dashboard of last-success-per-table.

---

## P8 · RAG: the code behind the 4 pillars

**What they are testing.** Whether the "first production RAG app" was real engineering — grounded and evaluated, not a demo.

**How I answer.** RAG in a regulated firm rests on four pillars: **retrieval, grounding, orchestration, evaluation**. The core retrieve-then-generate, grounded so it can't invent:

```python
def answer(question: str) -> Answer:
    # 1. RETRIEVAL — semantic search over embedded, chunked docs
    docs = vector_store.similarity_search(question, k=5)
    if not docs:
        return Answer(text="I don't have information on that.", citations=[])  # refuse, don't guess

    # 2. GROUNDING — answer ONLY from retrieved context, with citations
    context = "\n\n".join(f"[{i}] {d.page_content}" for i, d in enumerate(docs))
    prompt = (f"Answer ONLY from the context. If it's not there, say you don't know. "
              f"Cite sources by number.\n\nContext:\n{context}\n\nQuestion: {question}")
    result = llm.invoke(prompt)  # temperature=0 for determinism
    return Answer(text=result.content, citations=[d.metadata["source"] for d in docs])
```

The non-negotiables: it **grounds** every answer in retrieved context and **cites** sources; it **refuses** when nothing relevant is found (a confident wrong answer is worse than "I don't know" in finance); and it is **evaluated** — I built an eval set (with LangSmith) scoring faithfulness and relevance, so a prompt or model change is measured, not hoped. That evaluation harness is what made it *reusable reference architecture*, not a one-off ([B](01-overview-positioning.md)).

**Lesson.** *"RAG done right is grounded, cited, and evaluated — it answers only from retrieved context, refuses when it has nothing, and is scored on an eval set so changes are measured. In a regulated firm, 'I don't know' beats a confident hallucination every time."*

**Follow-ups**
- *"Chunking strategy?"* — Semantic/section-aware chunks with overlap so retrieval gets coherent context, not sentence fragments.
- *"Hallucination control?"* — Strict grounding prompt, low temperature, citations, and refusal on empty retrieval — plus the eval catching regressions.
- *"Evaluation metrics?"* — Faithfulness (grounded in context), answer relevance, retrieval hit-rate — tracked over time in LangSmith.

---

## P9 · Packaging, typing and quality

**What they are testing.** Whether my Python is engineered like the .NET — typed, tested, linted — or a loose script.

**How I answer.** I treat Python with the same discipline as C#. **Type hints everywhere**, checked in CI:

```python
def transform(rows: list[Position], ref: dict[str, RefData]) -> list[EnrichedPosition]:
    ...
```

The toolchain I standardise: **`ruff`** for lint + format (fast, one tool), **`mypy`** for static type checking (catches the bug before runtime, like TypeScript does for the front end), **`pytest`** for tests, and **`uv`/`poetry`** for reproducible dependency locking. Structure is a proper package (`src/` layout, `pyproject.toml`), not a folder of loose scripts — so it imports cleanly, tests cleanly, and deploys as an artifact. This is the same instinct as the reusable backend patterns: the ETL is a maintainable codebase the team extends, not scripts one person understands.

**Lesson.** *"My Python is engineered, not scripted — type hints checked by mypy, ruff for lint and format, pytest for tests, locked dependencies, proper package layout. The same standards I hold C# to, so the ETL is maintainable by the team, not just runnable by me."*

**Follow-ups**
- *"Why mypy if Python is dynamic?"* — It catches type errors before runtime and documents intent — exactly the value TypeScript adds to JS.
- *"Managing dependencies?"* — A lock file for reproducible builds; pinned versions so "works on my machine" isn't a phrase I say.
- *"Ruff over black+flake8+isort?"* — One fast tool replacing three; less config, faster CI.

---

## P10 · Testing data pipelines

**What they are testing.** Whether I can prove a pipeline is correct — harder than testing a function, because data is the input.

**How I answer.** I test at three levels: **unit** (pure transform logic), **data-quality** (contracts on the data itself), and **reconciliation** (end-to-end counts).

```python
def test_weight_sums_to_one():
    rows = [Position(ticker="A", quantity=1, market_value=Decimal("60"), as_of=date(2026,8,6)),
            Position(ticker="B", quantity=1, market_value=Decimal("40"), as_of=date(2026,8,6))]
    out = compute_weights(rows)
    assert sum(r.weight for r in out) == Decimal("1.0")   # invariant must hold

def test_rejects_negative_market_value():
    with pytest.raises(ValidationError):
        Position(ticker="A", quantity=1, market_value=Decimal("-1"), as_of=date(2026,8,6))
```

Beyond unit tests I add **data-quality checks that run in the pipeline** (Great Expectations / custom asserts): no nulls in key columns, values in expected ranges, referential integrity, and the **reconciliation gate** from [P4](#p4--idempotent-loads-and-reconciliation) that blocks publish if counts don't match. The invariant I always test is the one that matters to the report — e.g. *weights sum to 1*, *totals reconcile to source* — because that's the number a portfolio manager will trust.

**Lesson.** *"I test data pipelines at three levels: unit tests on the transforms, data-quality checks inside the run, and a reconciliation gate that blocks publish if counts don't match. The invariant I always assert is the one the report depends on — weights summing to one, totals matching source."*

**Follow-ups**
- *"Test data without a real feed?"* — Fixtures of representative and edge rows (nulls, extremes, malformed) so I test the failure paths, not just the happy one.
- *"Great Expectations vs custom asserts?"* — GE for a rich, documented suite; custom asserts when a couple of checks is enough — don't over-tool.
- *"Regression on the numbers?"* — Golden-output tests: known input → known report; any drift fails the build.

---

## Section index

| # | Question | Core message |
|---|---|---|
| P1 | Async Python | Async for I/O (GIL blocks CPU threads); bounded semaphore for rate limits |
| P2 | Pydantic v2 | Validate at the boundary; `Decimal` for money; fail early with the field |
| P3 | Pandas transform | Vectorise never `iterrows`; push big aggregation into SQL |
| P4 | Idempotent load | Transaction + delete/insert by as-of + reconcile — re-run must be safe |
| P5 | SQL tuning | Plan first; sargable predicates; set-based rewrite before new indexes |
| P6 | Snowflake vs SQL Server | Operational row-store vs analytical column-store — ingest into both |
| P7 | Orchestration | DAG of dependencies with retries, idempotency, alerts, reconcile gate |
| P8 | RAG code | Grounded, cited, refuses on empty, evaluated on an eval set |
| P9 | Packaging & quality | Typed (mypy), ruff, pytest, locked deps — engineered like the C# |
| P10 | Testing pipelines | Unit + data-quality + reconciliation; assert the report's invariant |

---

[← Deep Dive: React & TypeScript](16-deepdive-react-typescript.md) · [Home](README.md) · [Next → Coding-Round Prep](18-coding-round-prep.md)
