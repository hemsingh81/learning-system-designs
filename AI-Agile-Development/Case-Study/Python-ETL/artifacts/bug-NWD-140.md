# NWD-140 — A resent statement under a new filename loads a second time, duplicating every position

| | |
|---|---|
| **Raised by** | Pankaj , QA Engineer |
| **Date raised** | 2026-07-24 |
| **Severity** | **High** |
| **Priority** | P1 — blocks release |
| **Component** | `sinks/sql_sink.py` / `core/idempotency.py` — counterparty document ingestion |
| **Affects story** | [NWD-107](stories/NWD-107.md) (load idempotently) |
| **Environment** | `dev`, pipeline build `2026.06.22-c`, Document Intelligence model `broker-alpha-position-v3` |
| **Status** | Open → Fixed 2026-06-25 → Verified 2026-07-31 |

---

## 1. Summary

Counterparties resend the same statement under a new filename constantly — `BA-POS-20260619.pdf`, then `BA-POS-20260619_RESEND.pdf`, then `BA-POS-20260619 (1).pdf` when someone drags it out of Outlook a second time. [Design invariant 4](../00-the-brief.md) says idempotency is by SHA-256 of **content**, never filename, for exactly this reason.

One code path does not honour it. The ingestion ledger check in `core/idempotency.py` correctly hashes content and correctly says "already processed". The silver MERGE in `sinks/sql_sink.py` derives its key from a digest computed over the **blob path**, so the two arrivals produce two different keys and the second one inserts rather than matching.

Result: fourteen positions become twenty-eight. The account's market value doubles.

---

## 2. Expected vs actual

Test document: `broker_alpha/2026-06-19/BA-POS-20260619.pdf`, 14 positions, account `ACC-40118`, uploaded twice under two names.

| | Expected | Actual |
|---|---|---|
| Rows in `etl.processed_document` | 1 | 1 ✓ |
| Rows in `silver.counterparty_position` | 14 | **28** |
| Rows in `GOLD.COUNTERPARTY_POSITION` | 14 | **28** |
| Total market value, `ACC-40118` | 4,182,340.00 | **8,364,680.00** |
| Distinct `content_hash` in silver | 1 | **2** |
| Errors / warnings in logs | — | **none** |
| Breaks raised by reconciliation | 0 | **14 × `QUANTITY_MISMATCH`** |

The ledger says the document was processed once. Silver holds it twice. The two controls disagree and neither of them notices.

---

## 3. Steps to reproduce

1. Upload the statement:
   ```bash
   az storage blob upload \
     --container-name raw \
     --name "broker_alpha/2026-06-19/BA-POS-20260619.pdf" \
     --file ./fixtures/BA-POS-20260619.pdf \
     --auth-mode login
   ```
2. Wait for the worker (~40s).
3. Upload the **identical bytes** under a different name:
   ```bash
   az storage blob upload \
     --container-name raw \
     --name "broker_alpha/2026-06-19/BA-POS-20260619_RESEND.pdf" \
     --file ./fixtures/BA-POS-20260619.pdf \
     --auth-mode login
   ```
4. Count what landed:
   ```sql
   SELECT content_hash, COUNT(*) AS rows_loaded
   FROM   silver.counterparty_position
   WHERE  account_number = 'ACC-40118' AND statement_date = '2026-06-19'
   GROUP  BY content_hash;
   ```

**Result:**

```
CONTENT_HASH                            ROWS_LOADED
--------------------------------------  -----------
9f2c…a41b                                        14
d70e…31c8                                        14
```

Two hashes. The file is byte-identical — `certutil -hashfile` on both local copies returns the same SHA-256. Neither of the values above is that hash.

---

## 4. Evidence

### 4.1 The ledger got it right

```sql
SELECT content_hash, blob_path, status
FROM   etl.processed_document
WHERE  blob_path LIKE '%BA-POS-20260619%';
```

```
CONTENT_HASH   BLOB_PATH                                              STATUS
------------   ----------------------------------------------------   ------
9f2c…a41b      broker_alpha/2026-06-19/BA-POS-20260619.pdf             loaded
```

One row. The second arrival was recognised as a duplicate at the ledger. `core/idempotency.py` is correct.

### 4.2 The silver rows carry two different hashes for one document

Both silver groups above have identical `security_id`, `quantity`, `price` and `market_value` values, line for line. They differ only in `content_hash` and `blob_path`. That is one document written twice under two identities.

### 4.3 The second hash is a hash of the path

`d70e…31c8` reproduces exactly from the blob path:

```bash
printf 'broker_alpha/2026-06-19/BA-POS-20260619_RESEND.pdf' | sha256sum
```

Same value. The digest reaching the MERGE is computed over the path string, not the bytes.

### 4.4 Downstream

```sql
SELECT break_type, COUNT(*)
FROM   recon.break_report
WHERE  as_of_date = '2026-06-19' AND account_number = 'ACC-40118'
GROUP  BY break_type;
```

```
BREAK_TYPE          COUNT
-----------------   -----
QUANTITY_MISMATCH      14
```

Every position in the account breaks on quantity, because the counterparty side is exactly double. On a real book that is a phone call to the counterparty about fourteen trades that are all fine.

---

## 5. Business impact

1. **Silently doubled holdings in the warehouse.** Every duplicated row carries a valid `min_confidence` and `bronze_path`. Every audit signal says both copies are good.
2. **Resends are not an edge case.** Broker Alpha resent 23 statements last month, roughly 11% of their volume, and month-end is worse — a corrected statement is always a resend.
3. **It breaks the one control operations is being asked to trust.** Fourteen `QUANTITY_MISMATCH` breaks on an account with nothing wrong with it. This is the second time this sprint a defect has manufactured breaks that look genuine, and the pattern matters more than either instance.
4. **It is not self-correcting.** Reprocessing does not clear it. The duplicate row has a key nothing will ever MERGE onto again, so it stays until someone deletes it by hand.

---

## 6. What I ruled out

| Hypothesis | Ruled out because |
|---|---|
| The two files differ | Byte-identical. Same local SHA-256, same size, same page count |
| Two Function instances raced on one blob | Two separate uploads, forty seconds apart. Ledger shows one insert |
| The MERGE predicate is wrong | The predicate `content_hash + line_no` is right. It is being handed the wrong `content_hash` |
| The ledger check is broken | It is not. It correctly identified the second arrival as a duplicate |
| Snowflake duplicated on load | Silver already holds 28. Gold is faithfully reproducing silver |
| Extraction ran twice and produced different content | Both bronze responses are present and identical apart from the path they were written under |

---

## 7. Suggested area to investigate

`sinks/sql_sink.py`, the digest passed into `to_rows(...)` and on into the MERGE. Whatever computes it is being given a path where it should be given bytes.

The ledger path in `core/idempotency.py` is the correct implementation. Whatever the sink is calling is a second one.

---

## 8. Note for whoever picks this up

Two things beyond the fix.

**One correct implementation is not enough if a second one exists.** `core/idempotency.py` does this properly and has a good docstring explaining why. It did not stop the sink from doing it differently, because nothing forced the sink to go through it. I would make the function signature refuse a `str` outright rather than hashing whatever it is handed — a function that will happily hash a filename is a function that will eventually be handed one.

**Grep for the pattern before closing.** Anywhere a digest is computed, check what it is computed over. I would look at `sinks/blob_sink.py` and the bronze write path in particular, since both deal in paths and bytes in the same breath.

A regression test needs to upload the **same bytes twice under different names** and assert a row count. Every existing idempotency test uploads the same path twice, which the ledger already handles and which could never have caught this.

— Pankaj

---

## 9. Resolution

**Fixed** 2026-06-25 by Ravi Mullick. Three commits:

1. `test: reproduce NWD-140 duplicate rows on filename resend`
2. `fix(sinks): hash document content, never the blob path`
3. `refactor(idempotency): make content_hash reject non-bytes input`

**Root cause:** `sinks/sql_sink.py` computed its own digest from the blob path instead of calling `core.idempotency.content_hash` over the document bytes. Two code paths, one correct, one drifted.

**Fix:**
- The sink no longer computes a digest at all. The content hash is computed once, at ingest, and passed down.
- `core.idempotency.content_hash(content: bytes)` now raises on anything that is not `bytes`, with the message *"content_hash requires the document bytes. Hashing a filename or a path is the NWD-140 defect."* A comment can be ignored; a `TypeError` cannot.
- Module docstring records the defect so the next reader learns it without finding this file.

**Same pattern checked in three other places**, per §8. `sinks/blob_sink.py` and the bronze write path were already correct and now go through the same function. `recon/reconcile.py` does not hash.

**Regression tests added:** 4, including `test_same_bytes_different_filename_loads_once`, which is the report reproduced.

**Verified** 2026-07-31 by Pankaj . Uploaded under three filenames; 14 rows, one `content_hash`, zero breaks. Duplicate rows from the `dev` run cleaned out by hand.

---

> **Artifact contract — `artifacts/bug-NWD-140.md`**
>
> Produced by: Pankaj  (QA Engineer), using the bug-report standard in [P22](../../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md)
> Approved by: Gautam , 2026-07-24
>
> Anyone fixing from this report can rely on finding:
> - Exact reproduction steps, including both uploads and the commands to run them
> - Expected vs actual as **numbers**, not descriptions
> - Raw evidence — the SQL, its real output, and the command that proves which value was hashed
> - A ruled-out table, so no one repeats an investigation already done
> - Business impact stated in operational terms, including whether the damage self-corrects
> - Where the reporter believes the same mistake is available elsewhere
>
> This report does **not** contain: a diagnosis of the root cause, or a proposed fix.
> Those are the engineer's job — see [P27](../../../AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md).
>
> **If any guarantee above is missing, this report is not ready to prompt with.** Send it back.
>
> Changing this file: QA only, until Resolution is filled in; then it is closed.
