# NWD-141 — A 429 from Document Intelligence kills the run instead of backing off

| | |
|---|---|
| **Raised by** | Ananya Iyer, QA Engineer |
| **Date raised** | 2026-07-24 |
| **Severity** | **Medium** |
| **Priority** | P2 — does not corrupt data, but takes the pipeline down on the day it is needed most |
| **Component** | `core/clients.py` — Azure client factory |
| **Environment** | `dev`, pipeline build `2026.06.22-c`, Document Intelligence S0, model `broker-alpha-position-v3` |
| **Status** | Open → Fixed 2026-06-25 → Verified 2026-07-31 |

---

## 1. Summary

Under a month-end load simulation — 200 documents queued in four minutes — Document Intelligence returns HTTP 429 and the worker raises immediately. The exception propagates out of the queue handler, the Function invocation fails, and every document in that invocation's batch is abandoned.

The service is telling us to slow down. We are treating it as a fatal error.

[Spec §8, case X3](spec-confidence-gate.md#8-error-cases) is unambiguous about the required behaviour:

> **X3** — Extraction returns 429 (throttled). Exponential backoff with jitter, then retry. **Must not fail the run.** Month-end is exactly when this happens and exactly when it matters.

---

## 2. Expected vs actual

Load simulation: 200 documents enqueued over four minutes, S0 tier, default concurrency.

| | Expected | Actual |
|---|---|---|
| Documents processed | 200 | **147** |
| Documents failed | 0 | **53** |
| 429 responses received | some — normal under load | 61 |
| 429 responses retried | 61 | **0** |
| Function invocations failed | 0 | **9** |
| Messages returned to the queue | n/a | 53, then dead-lettered after 5 dequeues |
| Time to process 200 documents | ~14 min | run never completed |

The 53 failures are not spread evenly. They arrive in bursts, because a 429 in one invocation kills every document that invocation was holding.

---

## 3. Steps to reproduce

1. Point `dev` at the S0 Document Intelligence resource.
2. Enqueue the month-end fixture set:
   ```bash
   ./scripts/load_test.sh --count 200 --window 240s --source broker_alpha
   ```
3. Watch the Function logs, or query Application Insights:
   ```kusto
   exceptions
   | where timestamp > ago(30m)
   | where outerMessage has "429"
   | summarize count() by bin(timestamp, 1m), problemId
   ```

Reproduces on every run. It reproduces at 120 documents in the same window too, which is under the volume we have told Northwind we support.

---

## 4. Evidence

### 4.1 The stack trace

From Application Insights, invocation `8f4e2c11-9a03-4d7e-b6a1-0c5518e93d77`:

```
Result: Failure
Exception: azure.core.exceptions.HttpResponseError: (429) Too Many Requests
Stack:   File "/home/site/wwwroot/function_app.py", line 63, in on_document_landed
             result = extract.analyse(client, blob_bytes, source)
           File "/home/site/wwwroot/core/extract.py", line 118, in analyse
             poller = client.begin_analyze_document(
                          model_id=source.model_id,
                          analyze_request=stream,
                          content_type="application/octet-stream",
                      )
           File "/home/site/wwwroot/.python_packages/lib/site-packages/azure/ai/documentintelligence/_operations/_operations.py", line 1204, in begin_analyze_document
             raise map_error(status_code=response.status_code, response=response, error_map=error_map)
           File "/home/site/wwwroot/.python_packages/lib/site-packages/azure/core/exceptions.py", line 163, in map_error
             raise error
         azure.core.exceptions.HttpResponseError: (429) Too Many Requests
         Code: 429
         Message: Requests to the Analyze Document Operation under Document Intelligence
                  have exceeded call rate limit of your current tier. Please retry after 3 seconds.
         Retry-After: 3
```

The response carries `Retry-After: 3`. The service told us how long to wait and the code did not read it.

### 4.2 The client is constructed with retries disabled

`core/clients.py`, the factory every Azure client is built through:

```python
 51	    return DocumentIntelligenceClient(
 52	        endpoint=settings.doc_intel_endpoint,
 53	        credential=_credential(),
 54	        retry_total=0,          # TODO: turn back on before merge - TV 2026-06-09
 55	    )
```

`retry_total=0` disables the azure-core retry policy entirely, including its built-in 429 handling. The SDK would have honoured `Retry-After` on its own. It was switched off.

The comment says what happened. It was a deliberate shortcut, taken so that a failing call during local development would surface immediately instead of being retried five times behind a thirty-second wait, and it was never turned back on.

### 4.3 It is in three places, not one

```bash
$ grep -rn "retry_total" core/
core/clients.py:54:        retry_total=0,          # TODO: turn back on before merge - TV 2026-06-09
core/clients.py:79:        retry_total=0,
core/clients.py:112:       retry_total=0,
```

Document Intelligence at line 54, Azure AI Language (redaction) at line 79, Azure AI Translator at line 112. Only the first carries the TODO. The other two were copied from it.

### 4.4 What the queue does about it

Failed invocations return their messages to the queue, which retries them, which produces another burst of 429s, which fails again. After five dequeues each message dead-letters. So the recovery mechanism makes the throttling worse and then gives up.

---

## 5. Business impact

1. **It fails on the one day it must not.** Month-end is when volume spikes, when the T+1 commitment is under most pressure, and when Northwind's own reporting deadline sits. Every other day of the month this defect is invisible.
2. **53 documents dead-lettered.** They are not lost — bronze is not reached, raw is immutable, and they can be replayed. But somebody has to notice and replay them, and there is currently no alert that would tell them to.
3. **Rate limits get tighter, not looser.** The retry storm in §4.4 means the failure is self-amplifying. The system responds to being told to slow down by speeding up.
4. **Two more services are exposed.** Redaction fails closed by design, so a throttled Language call sends documents to review rather than corrupting anything — an inconvenience. A throttled Translator call on the EM book is the same shape. Neither has been load-tested; I would not assume either is fine.

---

## 6. What I ruled out

| Hypothesis | Ruled out because |
|---|---|
| We are on the free tier (F0, ~1 TPS) | S0. Confirmed on the resource in the portal |
| The rate limit is lower than documented | The 429 body quotes the S0 limit and it matches the published figure |
| The volume is unreasonable | 200 documents in four minutes. The PRD commits to ~200/day with month-end spikes. This is the stated load |
| Only Document Intelligence is affected | Same construction at `core/clients.py:79` and `:112`. Not observed under load yet — not observed is not the same as fine |
| The Function host is timing out | No. The invocation fails in under two seconds with an explicit 429 |
| The retry is happening and failing silently | `retry_total=0`. The azure-core policy is not running at all |

---

## 7. Suggested area to investigate

`core/clients.py`, all three client constructions.

The SDK's own retry policy honours `Retry-After` and applies exponential backoff. This may be entirely a matter of removing the argument rather than writing anything.

What I would want beyond that: **one retry policy, defined once, applied to every client.** Three constructors each carrying their own retry configuration is how one of them ends up different again. That is the shape of NWD-140 as well, and this is the second time in two days the defect has been "two code paths, one correct".

Also worth considering: the SDK's policy handles HTTP responses it can see. A connection reset or a DNS blip is a transport error, not a response, and will not be retried by it.

---

## 8. Note for whoever picks this up

This report has a stack trace and [NWD-142](bug-NWD-142.md) does not. That difference is not an accident of how much effort I put in, and it changes how each one should be worked.

Here, the trace **is** the diagnosis. It names the file, the line, the call, the status code and the service's own instruction, and `grep` finds the cause in one command. Ten minutes from the alert to knowing exactly what to change.

NWD-142 has no trace because **nothing threw**. No exception, no failing test, no log line, a document marked `loaded` and a confidence gate returning `passed = true` and being right to. There is nothing to paste. That report needs numbers, evidence and a ruled-out table precisely because it has no stack trace to hand anyone.

Loud failures are the cheap ones. Debug from the trace when you have it — [P26](../../../AI-Prompts-Library/phase-6-rework/P26-debug-an-error-fast.md) — and understand that the class of bug that costs a sprint is the one that never produces a trace at all.

A regression test needs to assert **behaviour under 429**, not the value of a constructor argument. Mock the transport to return two 429s then a 200, and assert the call succeeds and took the backoff. A test asserting `retry_total == 5` passes forever and proves nothing about what happens when the service throttles.

— Ananya

---

## 9. Resolution

**Fixed** 2026-06-25 by Tomas Vargas. Three commits:

1. `test: reproduce NWD-141 throttling failure under simulated 429`
2. `fix(clients): one shared retry policy across every Azure client`
3. `fix(clients): retry transport errors the HTTP policy cannot see`

**Root cause:** `retry_total=0` on all three Azure client constructions in `core/clients.py`, disabling the azure-core retry policy including its `Retry-After` handling. Committed as a local-development shortcut on 2026-06-09 with a TODO, copied twice without one.

**Fix:**
- One retry configuration, defined once and applied identically to every client: `retry_total=5`, `retry_backoff_factor=2.0`, `retry_backoff_max=60`. Clients are built through a single cached factory; a caller cannot construct one with its own retry settings.
- `retry_on_transport_error` wraps the call sites for connection resets and DNS failures, which the HTTP policy never sees. Ananya's §7 point.
- Each retry emits a structured `azure_transport_retry` log event, so throttling is visible before it is fatal.
- Module docstring states the policy and why it is shared.

**Alerting added:** a 429-rate alert firing before the retry budget is exhausted, and a dead-letter-depth alert. Both have runbook entries — [`runbook-doc-ingestion.md`](runbook-doc-ingestion.md) §5.3.

**Regression tests added:** 6. `test_429_then_success_is_retried` mocks two 429s and a 200 and asserts the call succeeds. `test_retry_after_header_is_honoured` asserts the wait. No test asserts a constructor argument.

**Verified** 2026-07-31 by Ananya Iyer. 200 documents in four minutes: 200 processed, 0 failed, 74 × 429 received and all retried, run completed in 16m 40s. Dead-letter queue empty.

---

> **Artifact contract — `artifacts/bug-NWD-141.md`**
>
> Produced by: Ananya Iyer (QA Engineer), using the bug-report standard in [P22](../../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md)
> Approved by: Rahul Nair, 2026-07-24
>
> Anyone fixing from this report can rely on finding:
> - Exact reproduction steps, including the load-test command and the Application Insights query
> - Expected vs actual as **numbers**, not descriptions
> - The **complete stack trace**, unedited, including the service's own `Retry-After` instruction
> - The offending line quoted with its file and line number, and every other place the same line appears
> - A ruled-out table, so no one repeats an investigation already done
> - Business impact stated in operational terms, including when the defect is invisible
> - A statement of what a regression test must assert, and what it must not
>
> This report does **not** contain: a diagnosis of the root cause, or a proposed fix.
> Those are the engineer's job — see [P26](../../../AI-Prompts-Library/phase-6-rework/P26-debug-an-error-fast.md), which uses this report as its worked example.
>
> **If any guarantee above is missing, this report is not ready to prompt with.** Send it back.
>
> Changing this file: QA only, until Resolution is filled in; then it is closed.
