# NWD-142 — Line items on page 2+ of a multi-page positions table are silently dropped

| | |
|---|---|
| **Raised by** | Ananya Iyer, QA Engineer |
| **Date raised** | 2026-07-24 |
| **Severity** | **Critical** |
| **Priority** | P1 — blocks release |
| **Component** | `core/extract.py` — counterparty document ingestion |
| **Affects story** | [NWD-103](stories/NWD-103.md) (confidence gate), [NWD-106](stories/NWD-106.md) (transform) |
| **Environment** | `dev`, pipeline build `2026.07.23-a`, Document Intelligence model `broker-alpha-position-v3` |
| **Status** | Open → Fixed 2026-07-31 → Verified 2026-08-03 |

---

## 1. Summary

When a Broker Alpha daily position statement contains a positions table that **continues across a page boundary**, only the line items on the first page are extracted. Line items on subsequent pages are dropped.

**Nothing fails.** No exception is raised. No test fails. The confidence gate passes the document, because every field that *was* extracted carries a genuinely high confidence score. The document is recorded as `status = loaded` in `etl.processed_document` and a partial set of positions is merged into `GOLD.COUNTERPARTY_POSITION`.

The missing rows then appear in the daily break report as `MISSING_EXTERNAL` — **indistinguishable from a genuine settlement failure.**

---

## 2. Expected vs actual

Test document: `broker_alpha/2026-07-24/BA-POS-20260724.pdf` (2 pages, 14 positions — 9 on page 1, 5 on page 2).

| | Expected | Actual |
|---|---|---|
| Line items extracted | 14 | **9** |
| Document status | `loaded` | `loaded` |
| Gate result | pass | pass |
| `min_confidence` on loaded rows | ≥ 0.90 | 0.94 |
| Rows in `GOLD.COUNTERPARTY_POSITION` | 14 | **9** |
| Errors / warnings in logs | — | **none** |
| Breaks raised by reconciliation | 0 | **5 × `MISSING_EXTERNAL`** |

---

## 3. Steps to reproduce

1. Upload the fixture to the raw container:
   ```bash
   az storage blob upload \
     --container-name raw \
     --name "broker_alpha/2026-07-24/BA-POS-20260724.pdf" \
     --file ./fixtures/BA-POS-20260724.pdf \
     --auth-mode login
   ```
2. Wait for the queue-triggered worker to complete (~40s). Confirm it did:
   ```sql
   SELECT content_hash, status, page_count, reason
   FROM   etl.processed_document
   WHERE  blob_path LIKE '%BA-POS-20260724%';
   ```
   Returns `status = 'loaded'`, `page_count = 2`, `reason = NULL`.
3. Open the source PDF and count the rows in the positions table by hand. **14.**
4. Count the loaded rows:
   ```sql
   SELECT COUNT(*) AS loaded_rows, MIN(MIN_CONFIDENCE) AS worst_confidence
   FROM   GOLD.COUNTERPARTY_POSITION
   WHERE  CONTENT_HASH = '9f2c…a41b';
   ```

**Result:**

```
LOADED_ROWS   WORST_CONFIDENCE
-----------   ----------------
          9             0.9412
```

Nine rows. Worst confidence 0.9412 — comfortably above the 0.90 gate. As far as every control in the system is concerned, this document was processed perfectly.

---

## 4. Evidence

### 4.1 The bronze response contains both tables

The raw Document Intelligence response persisted at
`bronze/broker_alpha/2026-07-24/9f2c…a41b.json` shows the layout model **did** find both tables:

```json
{
  "pages": [ { "pageNumber": 1 }, { "pageNumber": 2 } ],
  "tables": [
    { "rowCount": 10, "boundingRegions": [ { "pageNumber": 1 } ] },
    { "rowCount":  6, "boundingRegions": [ { "pageNumber": 2 } ] }
  ],
  "documents": [
    {
      "docType": "broker_alpha:position_statement",
      "fields": {
        "AccountNumber":  { "type": "string", "confidence": 0.981 },
        "StatementDate":  { "type": "date",   "confidence": 0.977 },
        "Positions": {
          "type": "array",
          "valueArray": [ "… 9 entries …" ]
        }
      }
    }
  ]
}
```

Two tables in `tables` (10 rows and 6 rows, one header row each → 9 + 5 = 14 positions).
**Nine entries in `Positions`.** The data is present in the response and lost during mapping.

### 4.2 The extraction is not aware anything is missing

`ExtractedDocument.line_items` has length 9. There is no field, counter, or flag anywhere in the object that records how many line items the document *claimed* to contain, so nothing downstream can detect the shortfall.

### 4.3 The confidence gate cannot see it

`core/confidence.evaluate()` iterates `doc.header` and `doc.line_items` and checks each field it finds against its threshold. Every field present passes. A row that was never extracted has no field to check.

> The gate answers **"can I trust this number?"**
> The failure here is **"is this number even here?"**
> Those are different questions and we only ever implemented the first one.

### 4.4 What it looks like downstream

```sql
SELECT break_type, COUNT(*)
FROM   recon.break_report
WHERE  as_of_date = '2026-07-24' AND account_number = 'ACC-40118'
GROUP  BY break_type;
```

```
BREAK_TYPE          COUNT
-----------------   -----
MISSING_EXTERNAL        5
```

Five breaks. Aladdin holds the position, the counterparty statement appears not to. That is exactly what a genuine failed settlement looks like, and an analyst investigating it would go to the counterparty and ask about five trades that settled perfectly well.

---

## 5. Business impact

1. **Wrong data in the warehouse, marked as trustworthy.** The loaded rows carry `MIN_CONFIDENCE = 0.9412` and a `BRONZE_PATH`. Every audit signal says this row is good. The audit trail is intact and the data is still incomplete.
2. **False breaks that consume analyst time.** Five fabricated `MISSING_EXTERNAL` breaks per affected document. Priya investigates them as real.
3. **It erodes the control.** The break report only works if operations trust it. A report that regularly contains fabricated breaks gets ignored, and then a real one gets ignored too. This is the failure mode we were most trying to avoid.
4. **Scope is not one broker.** Any counterparty whose statement runs past one page is affected. On a spot check of last month's volume that is roughly **31% of Broker Alpha documents**, and effectively **all month-end statements**.

---

## 6. What I ruled out

| Hypothesis | Ruled out because |
|---|---|
| The model failed to read page 2 | `pages` shows 2 pages; `tables` shows a 6-row table on page 2 with normal confidence |
| Free-tier 2-page truncation | This is the S0 resource, not F0. And page 2 *is* in the response |
| The PDF itself is malformed | Opens correctly; text is selectable on both pages; 14 rows visible |
| Confidence gate rejected 5 rows | `etl.extraction_exception` is empty for this `content_hash`. Nothing was rejected — the rows never existed |
| Snowflake MERGE deduplicated them | All 14 have distinct `SECURITY_ID`. Silver staging also has 9 |
| A transform-stage filter dropped them | `core/transform.py` received 9 items. The loss is upstream of transform |

---

## 7. Suggested area to investigate

`core/extract.py`, the mapping loop that walks `source.field_map`:

```python
doc = result.documents[0]
```

`result.documents` is a list. A statement whose positions table spans pages appears to produce a document whose `Positions` array covers only the first table, with the continuation carried in `result.tables` and not folded back into the array. Whatever the precise mechanism, **the mapping takes the first thing it finds and never checks whether there was more.**

---

## 8. Note for whoever picks this up

Two things I would push on beyond the immediate fix.

**This is not only a code defect.** I have read [`spec-confidence-gate.md`](spec-confidence-gate.md) twice. The implementation does exactly what the spec says. The spec has no concept of a document being *incomplete* — only of a field being *untrustworthy*. Fixing this in code without changing the spec leaves the next person reading a document that describes a control we do not have.

**The same assumption is probably elsewhere.** Anywhere we take "the first result" or read a paged response, the identical mistake is available. I would look at the Aladdin REST pull in particular, where paging could truncate in exactly this way.

A regression test needs to assert the **count**, not the content. Every existing test in `tests/test_confidence.py` asserts things about rows that are present. None of them could ever have caught this, including the one I would have bet on — `test_one_bad_line_item_fails_whole_document` checks that a *present* bad row is caught, and says nothing about an *absent* row.

— Ananya

---

## 9. Resolution

**Fixed** 2026-07-31 by Tomas Vargas. Merged in three commits (see [P31](../../../AI-Prompts-Library/phase-7-release/P31-write-clean-git-commits.md) for the split):

1. `test: reproduce NWD-142 line-item loss on multi-page tables` — the failing test first
2. `fix(extract): fold continuation tables into the line-item array`
3. `docs(spec): add completeness rules to the confidence gate spec`

**Root cause:** `core/extract.py` mapped only `result.documents[0]` and treated each page's table as independent, so a table continuing onto page 2 was never folded into the `Positions` array. No completeness check existed anywhere to notice the shortfall.

**Fix:**
- `core/extract.py` now stitches continuation tables and records per-field `page_number` plus a document-level `table_pages` provenance.
- `core/rules.py` gains two completeness rules — `line_item_count` (declared vs extracted) and `page_continuation` (layout table pages vs pages line items actually came from). A shortfall now routes the document to the exception queue rather than loading it.
- [`spec-confidence-gate.md`](spec-confidence-gate.md) **Revision 2** adds the completeness section. This was the real gap — see [P29](../../../AI-Prompts-Library/phase-6-rework/P29-the-spec-was-wrong.md).
- [`acceptance-criteria-NWD-103.md`](acceptance-criteria-NWD-103.md) **Revision 2** adds the missing criterion.

**Same pattern found and fixed in two other places**, as flagged in §8:
- `sources/aladdin_api.py` — the positions pull stopped at the first page of a paged REST response.
- `recon/reconcile.py` — the input path assumed the extracted set was complete.

**Regression tests added:** 8, including `test_the_gate_alone_would_have_missed_nwd_142`, which asserts that this exact document **passes the confidence gate and fails the completeness rules** — pinning the distinction the bug was made of.

**Verified** 2026-08-03 by Ananya Iyer. 14 positions in, 14 rows out. Fixture retained as `tests/fixtures/broker_alpha_2page.json`.

---

> **Artifact contract — `artifacts/bug-NWD-142.md`**
>
> Produced by: Ananya Iyer (QA Engineer), using the bug-report standard in [P22](../../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md)
> Approved by: Rahul Nair, 2026-07-24
>
> Anyone fixing from this report can rely on finding:
> - Exact reproduction steps, including the fixture and the commands to run it
> - Expected vs actual as **numbers**, not descriptions
> - Raw evidence — the bronze JSON, the SQL and its real output
> - A ruled-out table, so no one repeats an investigation already done
> - Business impact stated in operational terms
> - Whether the reporter believes the spec is implicated
>
> This report does **not** contain: a diagnosis of the root cause, or a proposed fix.
> Those are the engineer's job — see [P27](../../../AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md).
>
> **If any guarantee above is missing, this report is not ready to prompt with.** Send it back.
>
> Changing this file: QA only, until Resolution is filled in; then it is closed.
