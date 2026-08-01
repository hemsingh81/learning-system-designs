# Runbook — counterparty document ingestion

| | |
|---|---|
| **Produced by** | Ravi Mullick, Backend Engineer |
| **Using** | [P33 — Write the Runbook](../../../AI-Prompts-Library/phase-7-release/P33-write-the-runbook.md) |
| **Date** | 2026-07-19 |
| **Status** | Live · walked through end to end by Dzmitry , who did not build this system, 2026-07-19 |
| **Version** | 1.0 |
| **Audience** | Whoever is on call. Assumes you have never seen this code. |

---

## 0. Read this first

You are reading this at 3am because something paged you. Start at §2, decide whether the system is healthy, then go to §5 for your alert.

**Nothing here is urgent enough to skip §1.** Two rules, and both of them are about not making it worse.

**You will not lose data by waiting.** Every document is immutable in `raw/`, and its raw extraction response is immutable in `bronze/`. Reprocessing costs nothing and re-extracting is free from bronze. Doing nothing until morning is almost always safe. Deleting something is almost never.

**Never write to the warehouse by hand.** If a row is wrong, fix the pipeline and reprocess. A manual UPDATE breaks the audit trail, and the audit trail is what this system is for.

---

## 1. What this system does

Counterparty statements and trade confirmations arrive as PDFs, in every layout imaginable, some scanned, some in Spanish. This pipeline reads them, checks how confident the model was in every number, and loads only the documents it can stand behind — everything else goes to a human.

The output is one side of a daily reconciliation. The other side comes from Aladdin. Where they disagree, that is a break, and an analyst investigates it.

```
raw/ (blob)  →  classify  →  translate  →  extract  →  bronze/ (blob)
                                                          ↓
                                                       redact
                                                          ↓
                                                    rules engine
                                                    ┌─────┴─────┐
                                                  pass        fail
                                                    ↓           ↓
                                            Azure SQL      exception
                                             (silver)        queue
                                                    ↓
                                              Snowflake (gold)
```

| Thing | Where |
|---|---|
| Function app | `func-northwind-ingest-prod`, resource group `rg-northwind-recon-prod` |
| Raw / bronze | Storage account `stnorthwindrecon`, containers `raw`, `bronze` |
| Queue | `doc-landed`, dead-letter `doc-landed-poison` |
| Silver | Azure SQL `sql-northwind-recon`, database `recon`, schema `silver` + `etl` |
| Gold | Snowflake `NORTHWIND.GOLD.COUNTERPARTY_POSITION` |
| Telemetry | Application Insights `appi-northwind-recon-prod` |
| Exception queue UI | `https://recon.northwind.internal/exceptions` |
| Config | `config/sources.yaml` in the deployed package |

---

## 2. Is it healthy?

### 2.1 The one number

**The straight-through rate.** The percentage of documents that needed no human touch. Today it should be around 85%.

If you check one thing, check this. It is three things at once:

- **A business metric.** It is what Northwind is paying for. The whole case rests on it.
- **A model-health metric.** It falls when extraction confidence falls, which is what a degrading model looks like from the outside.
- **An early warning that a counterparty changed their template.** This is the one nobody expects. When a broker moves a column or renames a header, nothing errors. Extraction still runs, confidence on the fields it can still find is still high, and documents quietly start failing a required-field or completeness rule instead of loading. The rate drops for **that counterparty only**, usually by ten or twenty points, usually overnight, usually with no alert firing anywhere else.

So: always read it **per counterparty**, never only in aggregate. A single broker collapsing from 88% to 20% barely moves a blended number, and it is the most important thing that happened yesterday.

```kusto
customEvents
| where name == "document_processed"
| where timestamp > ago(24h)
| extend source_key = tostring(customDimensions.source_key),
         st = tobool(customDimensions.straight_through)
| summarize total = count(), straight = countif(st) by source_key
| extend rate = round(100.0 * straight / total, 1)
| order by rate asc
```

Expected: `broker_alpha` around 85%, `broker_beta_em` around 82%, on roughly 200 documents a day total. A drop of more than 15 points for one counterparty is §5.1.

### 2.2 The other four checks, in order

```kusto
// 1. Are documents arriving at all? Expect ~200/day, spiking at month-end.
customEvents | where name == "document_processed" | where timestamp > ago(24h) | count
```

```kusto
// 2. Is anything failing loudly?
exceptions | where timestamp > ago(24h) | summarize count() by problemId | order by count_ desc
```

```bash
# 3. Is the poison queue empty? It should be.
az storage queue metadata show --name doc-landed-poison \
  --account-name stnorthwindrecon --auth-mode login --query approximateMessageCount
```

```sql
-- 4. Is the exception queue being worked, or growing?
SELECT CAST(created_utc AS date) AS day, COUNT(*) AS raised
FROM   etl.extraction_exception
WHERE  created_utc > DATEADD(day, -7, SYSUTCDATETIME())
GROUP  BY CAST(created_utc AS date) ORDER BY day;
```

Roughly 30 a day is normal. A hundred is §5.1. Zero for a whole day is not good news either — it usually means nothing is arriving.

### 2.3 Healthy looks like

| Signal | Healthy |
|---|---|
| Straight-through rate, per counterparty | 80–90%, stable day to day |
| Documents processed | ~200/day, 400+ at month-end |
| Exceptions raised | ~30/day |
| Poison queue depth | 0 |
| Exception-to-queue latency | under 15 minutes (a PRD commitment) |
| 429 rate | non-zero at month-end and retried; never fatal |
| Azure AI spend | ~$420/month at ~12,600 pages |

---

## 3. Alerts

Every alert links to the section that fixes it. An alert without a section here is a bug in this runbook — file it.

| Alert | Fires when | Severity | Go to |
|---|---|---|---|
| `ST-RATE-DROP` | Straight-through rate for one counterparty falls >15 points vs its 7-day mean | **Sev 2** | [§5.1](#51-a-counterparty-changed-their-template) |
| `POISON-DEPTH` | `doc-landed-poison` depth > 0 for 15 minutes | **Sev 2** | [§5.2](#52-a-poison-blob) |
| `THROTTLE-RATE` | 429 responses > 50 in 5 minutes | **Sev 3** | [§5.3](#53-429-throttling-at-month-end) |
| `REDACT-FAIL` | Any redaction failure | **Sev 1** | [§5.4](#54-redaction-api-failure) |
| `FUNC-TIMEOUT` | Function invocation exceeds 9 minutes | **Sev 3** | [§5.5](#55-function-timeout-on-a-large-document) |
| `NO-DOCS` | Zero documents processed in 4 hours during business hours | **Sev 2** | [§5.6](#56-nothing-is-arriving) |
| `EXC-LATENCY` | Exception row not visible within 15 minutes of landing | **Sev 2** | [§5.6](#56-nothing-is-arriving) |
| `SQL-WRITE-FAIL` | Exception row could not be written | **Sev 1** | [§5.7](#57-cannot-write-the-exception-row) |

**Sev 1 wakes you.** Sev 2 is looked at within the hour during business hours. Sev 3 waits until morning unless it is month-end.

`REDACT-FAIL` is Sev 1 because redaction fails closed: nothing downstream is at risk, but every affected document stops. It is safe and it is blocking, which is the worst combination for a backlog.

---

## 4. Reprocessing and draining

You will need one of these two in most of §5. They are here so you are not scrolling.

### 4.1 Reprocess one document from bronze

Free. No Azure AI charge — the extraction response is already stored. This is what bronze is for.

```bash
# 1. Find the document.
az storage blob list --container-name bronze --account-name stnorthwindrecon \
  --prefix "broker_alpha/2026-07-19/" --auth-mode login --output table

# 2. Reprocess by content hash. Re-runs redaction, rules, transform, load.
python -m tools.reprocess --content-hash 9f2c…a41b --from bronze

# 3. Confirm.
```
```sql
SELECT status, reason, page_count FROM etl.processed_document WHERE content_hash = '9f2c…a41b';
SELECT COUNT(*) FROM silver.counterparty_position WHERE content_hash = '9f2c…a41b';
```

Reprocess a whole day:

```bash
python -m tools.reprocess --source broker_alpha --date 2026-07-19 --from bronze
```

Re-extract from `raw/` instead — **this costs money**, ~$0.03/page. Only when the bronze response itself is the problem, e.g. after a model redeploy:

```bash
python -m tools.reprocess --content-hash 9f2c…a41b --from raw --confirm-cost
```

The MERGE is keyed on `(content_hash, line_no)`, so reprocessing updates in place. It never duplicates. That is [NWD-140](bug-NWD-140.md) and it is enforced now.

### 4.2 Drain the exception queue

"Draining" means getting rejected documents resolved, not deleting them.

```sql
-- What is in there and why.
SELECT source_key, LEFT(reason, 60) AS reason, COUNT(*) AS n
FROM   etl.extraction_exception
WHERE  resolved_utc IS NULL
GROUP  BY source_key, LEFT(reason, 60)
ORDER  BY n DESC;
```

Group by reason first. Thirty exceptions with the same reason are one problem, not thirty.

- **Genuinely low confidence** — Preeti's job, in the UI. Not yours.
- **All the same reason, all one counterparty** — §5.1. Do not ask an analyst to hand-key thirty documents that a config change fixes.
- **A bug we have now fixed** — reprocess in bulk after the deploy:
  ```bash
  python -m tools.reprocess --exceptions-since 2026-07-18 --reason-like 'page_continuation%' --from bronze
  ```
  Resolved documents clear from the queue automatically when they load.
- **Never** `DELETE FROM etl.extraction_exception`. A rejected document that never reached a human is the worst outcome this system has.

---

## 5. Failure modes

### 5.1 A counterparty changed their template

**Symptom.** `ST-RATE-DROP`. One counterparty's straight-through rate collapses overnight. No exceptions in Application Insights. Nothing is erroring. Exception-queue volume for that counterparty jumps, all with similar reasons.

**Why.** They moved a column, renamed a header, added a summary row. Extraction still runs. The classifier still recognises the layout. Fields it can still find still score highly. Fields it cannot find come back `missing`, or the line-item count stops matching. Nothing throws, because nothing is broken — the document is just not the document we trained on.

**Diagnose.**

```sql
-- What is the actual reason? This is the whole diagnosis.
SELECT LEFT(reason, 80) AS reason, COUNT(*) AS n
FROM   etl.extraction_exception
WHERE  source_key = 'broker_alpha' AND created_utc > DATEADD(day, -2, SYSUTCDATETIME())
GROUP  BY LEFT(reason, 80) ORDER BY n DESC;
```

Then open one document side by side with a known-good one from last week:

```bash
az storage blob download --container-name raw --account-name stnorthwindrecon \
  --name "broker_alpha/2026-07-19/BA-POS-20260719.pdf" --file ./today.pdf --auth-mode login
az storage blob download --container-name raw --account-name stnorthwindrecon \
  --name "broker_alpha/2026-07-12/BA-POS-20260712.pdf" --file ./lastweek.pdf --auth-mode login
```

**Remediate.** Three cases.

*A field was renamed and we can map it.* Config only:
```yaml
# config/sources.yaml, under sources.broker_alpha.field_map
    PositionQty: quantity        # was "Quantity" until 2026-07-19
```
```bash
git commit -am "config(broker_alpha): map renamed PositionQty field" && ./deploy.sh prod
python -m tools.reprocess --source broker_alpha --since 2026-07-19 --from bronze
```

*The layout changed enough that the model must be retrained.* Not a 3am job. Raise it, tell Preetinka and Preeti the exceptions will be hand-worked meanwhile, and note that training is free — you pay only for analysis, and reprocessing from bronze after a retrain re-runs mapping without re-extracting.

*It is one bad batch, not a change.* Reprocess and watch tomorrow.

**Escalate** if the rate has not recovered within one business day. This is the failure mode most likely to be a real change on their side, and the person who fixes it is at the counterparty.

---

### 5.2 A poison blob

**Symptom.** `POISON-DEPTH`. One or more messages in `doc-landed-poison`. Each has failed five dequeues.

**Why.** Usually a corrupt, encrypted or zero-byte PDF that should have been caught as `unreadable_document` and was not. Occasionally a transient failure that happened five times.

**Diagnose.**

```bash
az storage message peek --queue-name doc-landed-poison \
  --account-name stnorthwindrecon --num-messages 10 --auth-mode login
```

The message body carries the blob path. Then:

```kusto
exceptions
| where timestamp > ago(6h)
| where customDimensions.blob_path has "BA-POS-20260719"
| project timestamp, problemId, outerMessage
```

**Remediate.**

*Genuinely unreadable document.* Record it and tell the counterparty. Do not delete the raw blob.
```bash
python -m tools.mark_unreadable --blob "broker_alpha/2026-07-19/BA-POS-20260719.pdf" \
  --reason "PDF is password-protected"
az storage message clear --queue-name doc-landed-poison --account-name stnorthwindrecon --auth-mode login
```
That writes an exception row so the document is visible to a human, then clears the queue. **Clear the queue only after the exception row exists.** Check it:
```sql
SELECT content_hash, reason FROM etl.extraction_exception WHERE blob_path LIKE '%BA-POS-20260719%';
```

*Transient — a downstream service was down.* Replay it:
```bash
python -m tools.requeue --from-poison --blob "broker_alpha/2026-07-19/BA-POS-20260719.pdf"
```

*More than about ten poison messages at once.* That is not a bad document, that is a downstream outage. Check §5.4 and §5.7 first, fix the cause, then requeue the lot:
```bash
python -m tools.requeue --from-poison --all
```

---

### 5.3 429 throttling at month-end

**Symptom.** `THROTTLE-RATE`. High 429 counts against Document Intelligence. Processing slows. Under normal operation **this is not an incident** — retries are working and the run completes.

**Why.** Month-end doubles volume. The S0 tier rate-limits. The client retries with exponential backoff and honours `Retry-After`. That is [NWD-141](bug-NWD-141.md) and it is fixed; before the fix a 429 killed the run.

**Diagnose — is it retrying, or failing?**

```kusto
customEvents | where name == "azure_transport_retry" | where timestamp > ago(1h)
| summarize retries = count() by bin(timestamp, 5m), tostring(customDimensions.service)
```
```kusto
exceptions | where timestamp > ago(1h) | where outerMessage has "429" | count
```

Retries climbing and exceptions at zero: **the system is working.** Do nothing. Note it and go back to bed.

**Remediate**, only if exceptions are non-zero — the retry budget is exhausted.

```bash
# 1. Reduce concurrency so we stop asking for what we cannot have.
az functionapp config appsettings set --name func-northwind-ingest-prod \
  --resource-group rg-northwind-recon-prod \
  --settings PYTHON_THREADPOOL_THREAD_COUNT=2 FUNCTIONS_WORKER_PROCESS_COUNT=1

# 2. Confirm the retry budget is what we think it is.
grep -n "retry_total\|retry_backoff" core/clients.py
```
Expect `retry_total=5`, `retry_backoff_factor=2.0`, `retry_backoff_max=60`. If you ever see `retry_total=0`, that is NWD-141 back from the dead — stop and escalate.

Anything dead-lettered goes through §5.2. Nothing is lost: raw is immutable and the extraction was never charged for.

Restore concurrency after month-end:
```bash
az functionapp config appsettings set --name func-northwind-ingest-prod \
  --resource-group rg-northwind-recon-prod \
  --settings PYTHON_THREADPOOL_THREAD_COUNT=8 FUNCTIONS_WORKER_PROCESS_COUNT=4
```

**Escalate to a tier increase** if this recurs outside month-end. That is a capacity conversation, not an incident.

---

### 5.4 Redaction API failure

**Symptom.** `REDACT-FAIL`, Sev 1. Documents stop loading. Exception rows appear with a redaction marker.

**Why.** Azure AI Language is unavailable or erroring. **Redaction fails closed by design** — if PII detection cannot run, the raw text is not persisted anywhere downstream and a marker is written instead. Nothing leaks. Everything stops.

Sev 1 not because data is at risk — it is not — but because every affected document is blocked and the backlog grows at ~200/day.

**Diagnose.**

```kusto
exceptions | where timestamp > ago(2h)
| where operation_Name has "redact" or outerMessage has "TextAnalytics"
| project timestamp, problemId, outerMessage | take 20
```
```bash
az cognitiveservices account show --name cog-northwind-language \
  --resource-group rg-northwind-recon-prod --query "properties.provisioningState"
```
Check the Azure status page for the region.

**Remediate.**

*Service outage.* Wait it out. Do not disable redaction — there is no supported way to and there should not be. When the service returns:
```bash
python -m tools.reprocess --exceptions-since 2026-07-19 --reason-like 'redaction%' --from bronze
```

*Auth failure — 401 or 403.* Managed identity has lost its role assignment:
```bash
az role assignment list --assignee <function-managed-identity-object-id> --output table
# Expect: Cognitive Services User on cog-northwind-language
az role assignment create --assignee <object-id> --role "Cognitive Services User" \
  --scope /subscriptions/<sub>/resourceGroups/rg-northwind-recon-prod/providers/Microsoft.CognitiveServices/accounts/cog-northwind-language
```

*Throttling.* §5.3 applies; same shared retry policy.

**Escalate** to Hem if anyone suggests bypassing redaction to clear a backlog. The answer is no, and it is not a 3am decision.

---

### 5.5 Function timeout on a large document

**Symptom.** `FUNC-TIMEOUT`. An invocation exceeds nine minutes and is killed. Usually a month-end statement of 40+ pages.

**Why.** Extraction time scales with pages. The Function's timeout is ten minutes on the Premium plan. A 50-page document with a slow poller can reach it.

**Diagnose.**

```kusto
requests | where timestamp > ago(24h) | where duration > 300000
| project timestamp, name, duration, success, customDimensions.blob_path
| order by duration desc
```
```sql
SELECT blob_path, page_count, status FROM etl.processed_document
WHERE created_utc > DATEADD(day, -1, SYSUTCDATETIME()) AND page_count > 30
ORDER BY page_count DESC;
```

**Remediate.**

*One-off.* Reprocess it on its own, off the hot path:
```bash
python -m tools.reprocess --blob "broker_alpha/2026-07-31/BA-POS-MONTHEND.pdf" --from raw --confirm-cost --timeout 1800
```

*Recurring at month-end.* Confirm the page cap is sane and raise the host timeout:
```bash
grep -n "max_pages" config/sources.yaml     # expect 50
az functionapp config appsettings set --name func-northwind-ingest-prod \
  --resource-group rg-northwind-recon-prod --settings functionTimeout=00:10:00
```
Ten minutes is the Premium-plan maximum. Past that the answer is architectural — split extraction from post-processing — and it is a ticket, not a fix.

*A document over `max_pages`.* It is rejected as oversized, not timed out, and appears in the exception queue. That is correct behaviour. Raise the cap deliberately or hand the document to Preeti.

**Do not** retry a timing-out document repeatedly. You pay per page each time it re-extracts from raw.

---

### 5.6 Nothing is arriving

**Symptom.** `NO-DOCS` or `EXC-LATENCY`. Zero documents in four business hours. Everything looks healthy because nothing is happening.

**Diagnose, in this order.** Work backwards from the blob.

```bash
# 1. Are files landing in raw at all?
az storage blob list --container-name raw --account-name stnorthwindrecon \
  --prefix "broker_alpha/$(date +%Y-%m-%d)/" --auth-mode login --output table
```
If empty, the problem is upstream — email/SFTP delivery, not this pipeline. Contact Northwind ops. Nothing here to fix.

```bash
# 2. Files landing but nothing queued? The blob trigger is not firing.
az storage queue metadata show --name doc-landed \
  --account-name stnorthwindrecon --auth-mode login --query approximateMessageCount

# 3. Is the Function running?
az functionapp show --name func-northwind-ingest-prod \
  --resource-group rg-northwind-recon-prod --query "state"
az functionapp restart --name func-northwind-ingest-prod --resource-group rg-northwind-recon-prod
```

```bash
# 4. Messages queued but not consumed after a restart — replay the day's blobs.
python -m tools.requeue --source broker_alpha --date 2026-07-19
```

Requeueing is safe. The content-hash ledger means an already-processed document is recognised and skipped.

---

### 5.7 Cannot write the exception row

**Symptom.** `SQL-WRITE-FAIL`, Sev 1. Azure SQL is unavailable or rejecting writes to `etl.extraction_exception`.

**Why this is Sev 1.** A rejected document that never reaches the queue is the worst outcome this system has — spec error case X9. The document is not loaded and nobody knows it exists. The pipeline is built to refuse to report success in this case, so it will fail loudly rather than lose the document, and that is what you are seeing.

**Diagnose.**

```bash
az sql db show --name recon --server sql-northwind-recon \
  --resource-group rg-northwind-recon-prod --query "status"
```
```sql
SELECT TOP 5 start_time, end_time, error_code FROM sys.dm_exec_requests_history ORDER BY start_time DESC;
```
Check for a failover, a DTU cap, or a firewall change.

**Remediate.** Restore SQL availability, then replay:

```bash
python -m tools.requeue --failed-since 2026-07-19T02:00:00
```

Documents that failed here were never marked processed, so replay is clean. Confirm the queue caught up:

```sql
SELECT COUNT(*) FROM etl.extraction_exception WHERE created_utc > '2026-07-19T02:00:00';
```

---

## 6. Escalation

Try §5 first. If the alert is Sev 1, or you have been on it for 30 minutes without progress, escalate — nobody on this list minds being called.

| Order | Who | For | Contact |
|---|---|---|---|
| 1 | On-call engineer (rota) | Everything, first | PagerDuty `northwind-recon` |
| 2 | Ravi Mullick — Backend | Pipeline, extraction, rules engine, sinks | Teams · mobile in PagerDuty |
| 3 | Gautam  — Team Lead | Anything unresolved after 30 minutes; any deploy to prod out of hours | Teams · mobile in PagerDuty |
| 4 | Hem Singh — Architect | Anything touching redaction, audit trail, or a proposal to bypass a control | Teams |
| 5 | Dzmitry  — Frontend | Exception queue UI only | Teams |
| 6 | Pankaj  — QA | Suspected data correctness issue, before anyone touches the warehouse | Teams |
| 7 | Preetinka Sharma — Product Owner | Anything a business decision depends on; any backlog Preeti will feel | Teams |
| 8 | Atul— PM | Client communication. **Northwind hears from Atul, not from you.** | Teams · mobile |
| — | Preeti Singh — Northwind ops | The person who works the exception queue. Tell her before she finds out. | Northwind Teams |

**Two standing rules.**

Pankaj is consulted before anyone modifies data in silver or gold. Always. Even when it is obviously fine.

Any proposal to disable a control — redaction, the confidence gate, a completeness rule — goes to Hem, in daylight, with a written reason. There is no 3am version of that conversation.

---

## 7. Routine

| Task | Frequency | Command |
|---|---|---|
| Straight-through rate per counterparty | Daily | §2.1 query |
| Exception queue age — anything older than 2 days | Daily | `SELECT * FROM etl.extraction_exception WHERE resolved_utc IS NULL AND created_utc < DATEADD(day,-2,SYSUTCDATETIME())` |
| Azure AI spend vs the ~$420/month estimate | Monthly | Cost Management, filter to Cognitive Services |
| Snowflake key rotation | Quarterly | `docs/ops/snowflake-key-rotation.md` |
| Restore a document from bronze, as a drill | Monthly | §4.1 on any document. If it does not work, you need to know before you need it |
| Review this runbook against reality | Per release | Any new failure mode needs a §5 entry before it ships — [`definition-of-done.md`](definition-of-done.md) §4.3 |

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/runbook-doc-ingestion.md`**
>
> Produced by: Backend Engineer (Ravi Mullick) using P33 — Write the Runbook
> Validated by: Dzmitry , 2026-07-19 — walked every section without help from the author, which is the only test of a runbook that counts
>
> Anyone consuming this file can rely on finding:
> - What the system does, in two lines, before any procedure
> - How to tell whether it is healthy, with runnable queries and the expected numbers
> - The single most useful number in the system, and why one number carries three meanings
> - An alert table where every alert links to the section that resolves it
> - A failure-mode section per alert: symptom, why, how to diagnose, exact remediation commands
> - How to reprocess a document from bronze, and how to drain the exception queue without deleting anything
> - Named escalation contacts in order, with what each is for
>
> This file does **not** contain: the design reasoning, the deployment procedure, or the release gate.
> Those live in: `spec-confidence-gate.md` (P11), the ADRs (P12), the deploy pipeline, and `release-readiness-v1.0.md` (P32).
>
> **If any guarantee above is missing, this runbook is not ready to be on call with.** Send it back.
>
> Changing this file: whoever is on call may add a failure mode they hit, immediately and without approval — a runbook that is hard to update stops being true. Removing a section needs Ravi Mullick or Gautam .
