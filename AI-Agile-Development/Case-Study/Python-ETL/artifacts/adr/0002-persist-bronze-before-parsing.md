# 0002 — Persist the raw extraction response before parsing it

| | |
|---|---|
| **Produced by** | Hem Singh, Architect |
| **Using** | [P12 — Record an Architecture Decision](../../../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) |
| **Date** | 2026-06-16 |
| **Status** | Accepted |
| **Version** | 1.0 |
| **In the room** | Hem Singh (Architect), Ravi Mullick (Backend), Gautam  (Team Lead) |

---

## Context

Analysis costs money per page. Roughly $30 per 1,000 pages of custom extraction, against **12,600 pages a month**. Re-analysing a month of documents costs about $378 and, more importantly, takes hours and hits the same service the live pipeline depends on.

Parsing costs nothing and is where the bugs are. The extraction response is a nested structure — header fields, arrays of line items, bounding regions, per-field confidences — and every mapping from it to our schema is code we wrote and can get wrong. We will get some of it wrong.

Those two facts point in the same direction, and the design question is where exactly the durability boundary sits: do we persist the PDF and re-analyse when parsing changes, or do we persist the analysis output too?

There is a second force. Northwind's audit requirement is not "show me the PDF". It is "show me how this number was derived". The PDF alone does not answer that; the extraction response does, because it contains what the model actually read and how sure it was, field by field.

## Options considered

### Option A — Persist the raw PDF only. Re-analyse when parsing changes.

**What it is.** `raw/{broker}/{yyyy-mm-dd}/{file}.pdf` is the only durable artefact. A parsing fix means re-sending the PDFs to Document Intelligence.

**For.**
- Simplest possible storage story. One immutable container.
- No question about what the response format is or how to version it.
- Storage footprint is minimal.

**Against.**
- Reprocessing a month of documents costs ~$378 and several hours of service throughput, competing with live traffic.
- A model that has since been retrained will not reproduce the original response. `broker-alpha-position-v3` today is not necessarily deployed in eighteen months. Re-analysis is not replay; it is a fresh reading.
- The audit answer degrades to "here is the PDF and here is our current code", which is a re-derivation rather than a record.

### Option B — Persist the parsed canonical rows only. Treat silver as the record.

**What it is.** Skip an intermediate layer. The typed rows in silver are the durable artefact.

**For.**
- One fewer container and one fewer path to manage.
- Silver is already immutable-ish by MERGE semantics.

**Against.**
- Everything the parser dropped is gone. This option is exactly the one that would have made [NWD-142](../bug-NWD-142.md) unrecoverable — the five missing line items were present in the extraction response and absent from silver, and being able to open the bronze JSON and see them is what turned a three-day investigation into a two-hour one.
- Confidence scores per field are lost; only the aggregate `MIN_CONFIDENCE` survives.
- A parsing bug is unrecoverable without paying for re-analysis, which is Option A's problem plus data loss.

### Option C — Persist the raw extraction response as JSON, before any parsing, alongside the raw PDF.

**What it is.** Two immutable layers. `raw/` holds the PDF exactly as it arrived. `bronze/` holds the complete Document Intelligence response, serialised, before a single line of our mapping code touches it. Parsing reads from bronze.

**For.**
- A parsing bug next month is reprocessed for free.
- The response is a record of what the model read, not a re-derivation of it. That is the audit answer.
- Per-field confidence and page provenance survive, which the canonical row does not fully carry.
- Decouples the cost of fixing our code from the cost of the vendor's service.

**Against.**
- A second container, a second path convention, and a second retention policy.
- The response format is the vendor's, and it changes across API versions. Stored JSON from an older API version needs a parser that still understands it.
- Storage cost, though at this volume it is negligible — a few gigabytes a year.

## Decision

**We persist the complete raw extraction response to `bronze/` before any parsing, and the raw PDF to `raw/` before any analysis. Both are immutable. Parsing reads bronze, never the live service.** Option C.

The reasons, in order of weight:

1. **A parsing bug must be cheap to fix.** We will find parsing bugs. Making the fix cost $378 and a service window means we will batch them, defer them, and eventually stop reprocessing at all.
2. **The audit answer must be a stored record, not a re-derivation.** `BRONZE_PATH` is carried onto every warehouse row for exactly this. Any number in any report resolves to a file containing what the model read and how sure it was.
3. **Re-analysis is not replay.** Models get retrained. The bronze response is tied to the model version that produced it; a re-analysis is not.
4. **The response contains information the canonical row does not.** Page provenance, per-field confidence, bounding regions, and the model's own table structure. All of that is discarded by the transform and all of it has turned out to matter.

`bronze/` is written **before** the confidence gate runs, not after. A document that fails the gate has a bronze record too — otherwise the documents we most need to investigate are the ones we have least evidence about.

## Consequences

### What this gives us

- Reprocessing is free and fast. During the [NWD-142](../bug-NWD-142.md) fix, Ravi replayed 340 stored Broker Alpha responses through the corrected parser in under four minutes at zero cost, and confirmed the fix against real documents rather than fixtures.
- `MIN_CONFIDENCE` plus `BRONZE_PATH` on a warehouse row is a complete audit chain: how sure the model was, and the original response it came from, without leaving SQL.
- Rejected documents are as well evidenced as accepted ones.
- The parser can be rewritten with confidence, because its input is a stored corpus we can regression-test against.

### What this costs us

- Two immutable containers with two lifecycle policies and two retention conversations with compliance. Resolved 2026-07-06: seven years, cool at 90 days, archive at 365, for both.
- Bronze is stored **unredacted**. It is the original response and redacting it would destroy the thing it exists to be. That required an explicit sign-off from Northwind compliance (2026-06-25) and access is restricted to the pipeline's managed identity plus a named break-glass role. This is a real security consequence and is written down here so nobody discovers it in an audit.
- We own a compatibility problem: bronze JSON written under an older Document Intelligence API version must remain parseable. The API version is recorded in the bronze envelope so the parser can branch if it ever has to.

### What we have accepted that we do not like

- **There is now a place in the system where full, unredacted document content sits for seven years.** It is the right decision and it is not a comfortable one. Mitigation is access control and lifecycle, not deletion, because deletion would defeat the purpose.
- **Bronze can drift from raw.** If somebody re-analyses a PDF and writes a second bronze file, there are now two responses for one document. The naming convention keys bronze on the content hash plus model version to make this visible rather than silent, but nothing prevents it.

### Objections on the record

- **Ravi Mullick, 2026-06-16:** none on the decision. Raised that storing the SDK's response objects requires an explicit serialisation step because they are not plain JSON, and that a naive `str()` would produce something unparseable later. Accepted and built as `sinks/blob_sink.py`'s bronze writer, with the API version recorded in the envelope.

## Revisit when

- Storage cost for `bronze/` exceeds the monthly analysis spend of ~$420. At current volumes that is many years away.
- Document Intelligence introduces a breaking response-format change we cannot parse from stored history, at which point we need a migration rather than a decision.

## References

- [ADR-0001 — Extraction approach](0001-extraction-approach.md), for why the response is version-pinned in the first place
- [NWD-142](../bug-NWD-142.md) — the defect whose investigation this decision made cheap
- [`data-contract-counterparty-position.md`](../data-contract-counterparty-position.md), audit columns section
- [NWD-105](../stories/NWD-105.md), criterion 4 — the redaction exemption for raw and bronze

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/adr/0002-persist-bronze-before-parsing.md`**
>
> Produced by: Architect (Hem Singh) using P12 — Record an Architecture Decision
> Approved by: Gautam  (Team Lead) 2026-06-16 · Northwind compliance for the unredacted-bronze consequence 2026-06-25
>
> Anyone consuming this file can rely on finding:
> - The context, with per-page cost and monthly volume stated
> - Three options with honest arguments for and against
> - The decision with numbered reasons, and an explicit statement of where in the pipeline bronze is written
> - Consequences in three parts, including the unredacted-storage consequence and its sign-off
> - Any objection raised, attributed and dated
> - A revisit trigger
>
> This file does **not** contain: blob path conventions, retention policy detail, serialisation format, or access control configuration.
> Those live in: `sinks/blob_sink.py`, `runbook-doc-ingestion.md` (P33), and Northwind's data classification standard.
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: never edit the Decision section. Supersede with a new ADR. Any change requires re-checking `sinks/blob_sink.py`, `data-contract-counterparty-position.md`, and the compliance sign-off on unredacted bronze storage.
