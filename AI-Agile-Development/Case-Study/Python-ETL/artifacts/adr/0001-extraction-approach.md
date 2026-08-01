# 0001 — Use Document Intelligence custom models, not an LLM, for extraction

| | |
|---|---|
| **Produced by** | Hem Singh, Architect |
| **Using** | [P12 — Record an Architecture Decision](../../../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) |
| **Date** | 2026-06-15 |
| **Status** | Accepted |
| **Version** | 1.0 |
| **In the room** | Hem Singh (Architect), Gautam  (Team Lead), Ravi Mullick (Backend), Preetinka Sharma (PO), Atul(PM) |

---

## Context

Northwind receives roughly **200 counterparty documents a day, averaging 3 pages**, spiking at month-end. That is **12,600 pages a month**. Each document has to become typed rows in a warehouse: account number, security identifier, quantity, price, market value, currency, dates.

The layouts are not consistent. Two counterparties are in scope for v1 — Broker Alpha's daily position statement in English, Broker Beta's EM trade confirmations in Spanish — and the roadmap adds one per fortnight after that. Some documents are native PDF, some are scans of a printout.

The constraint that makes this a decision rather than a default is in the PRD, §7: **a value the system is not confident about must reach a human rather than the warehouse.** That requires a per-field confidence score we can threshold, defend in an audit, and reproduce.

There is a second constraint that shapes everything: this is a **financial control**. The output of this pipeline feeds a reconciliation whose breaks are investigated by people and reported to clients. Northwind's internal audit will ask, at some point, "how did this number get here and how sure were you?" We must be able to answer with a stored artefact, not a recollection.

## Options considered

### Option A — Azure AI Document Intelligence, custom extraction models per layout family

**What it is.** A service you send a PDF to and get structured fields back — "this is the account number, this is the quantity, here is a table of positions" — rather than a wall of text. You train it by labelling a set of example documents for each layout. Training is free; you pay per page analysed.

**For.**
- Returns a **calibrated confidence score per field**, between 0 and 1. This is not a nice-to-have. It is the input to the entire design.
- Output is deterministic for a pinned model version. The same PDF analysed twice returns the same fields.
- Model versions are ours. `broker-alpha-position-v3` is a thing we trained, pinned, and can re-run against a document from March.
- Table extraction with per-cell provenance, including which page a value came from.
- Pricing is simple and predictable: ~$30 per 1,000 pages for custom extraction, ~$3 per 1,000 for the classifier. At our volume that is ~$378 + ~$38, roughly **$420 a month**.
- ~50 labelled documents per layout for production quality; 15 is enough to prove the approach before committing.

**Against.**
- Labelling is genuinely tedious. Somebody sits and draws boxes for a couple of days per layout. There is no way around it and pretending otherwise is how projects slip.
- A layout change means retraining. Free, but it is an operational task somebody has to notice is needed.
- The free tier (F0) has traps that will waste a day if you do not know about them: it only analyses the **first two pages**, caps files at **4 MB**, and throttles to roughly one transaction per second. It does not warn you that it truncated your document. We use S0 from day one.

### Option B — A large language model with a vision input and a prompt per layout

**What it is.** Send the page image and a prompt — "extract the account number, statement date, and the positions table as JSON" — and parse the reply.

**For.**
- No labelling. You could have something working the same afternoon.
- Handles a layout it has never seen, which is genuinely attractive given a counterparty-per-fortnight roadmap.
- Handles Spanish without a separate translation step.
- Copes with messy, irregular documents that would need several trained layouts.

**Against.** (See Decision, reasons 1–3. This is the option we spent the most time on and it is the one we rejected.)

### Option C — Template-based parsing: `pdfplumber` plus per-layout coordinate rules and regex

**What it is.** Our own Python. Open the PDF, read text at known positions, pull values with regular expressions written per counterparty.

**For.**
- No per-page cost at all. Free to run.
- Fully deterministic and fully inspectable. Every decision is a line of our code.
- No external dependency in the critical path.

**Against.**
- Does not work on scans. A meaningful share of Broker Alpha's statements are scanned, which would mean bolting OCR on and then owning the OCR quality problem too.
- **No confidence score exists.** A regex either matches or it does not. There is no "I found something that might be the quantity, 71% sure". The PRD's central requirement cannot be implemented on top of this without inventing a confidence proxy, and an invented confidence is worse than none.
- Onboarding a counterparty becomes a code change, which contradicts the v1 requirement that it be a config change.
- Every layout tweak by a counterparty breaks it silently. This is the failure mode Northwind already lives with in an older spreadsheet-macro process and specifically asked us not to recreate.

### Option D — Outsource keying to a BPO

**What it is.** Pay people offshore to type the documents.

**For.** Works today. No build. Handles any layout.

**Against.** Does not achieve T+1 — a keying vendor's SLA is overnight at best. Does not remove the analyst review step, it relocates it. Introduces a third party into a flow carrying account-level position data. Costs more than $420 a month by two orders of magnitude. Recorded because Atul asked and it deserved a real answer, not because it was close.

## Decision

**We use Azure AI Document Intelligence with custom extraction models, one per layout family, fronted by a custom classifier.** Option A.

We explicitly reject Option B — LLM-based extraction — for three reasons:

**Reason 1. There is no calibrated per-field confidence score.**
The design in the PRD rests on a number between 0 and 1, per field, that means "how sure was the reader". An LLM does not give you that. You can ask it to self-report a confidence and it will produce one, and that number is not calibrated against anything — it is generated text about a value, produced by the same process that produced the value. Thresholding it would give us a control that looks exactly like a real control and is not one. Given that this pipeline exists specifically to stop untrustworthy numbers reaching the warehouse, building it on an uncalibrated trust signal is self-defeating.

**Reason 2. The output is not reproducible, so there is no audit trail.**
The same page, the same prompt, two runs, and the output can differ. Worse, the underlying model is updated by the vendor on their schedule: a document that extracted one way in June extracts a different way in September with no change on our side and no version we pinned. When Northwind's audit function asks how a number in a Q2 report was derived, "we sent the page to a model, and that model no longer exists in the form that produced this" is not an answer. Document Intelligence gives us `broker-alpha-position-v3` — a specific artefact, pinned, re-runnable.

**Reason 3. The failure mode is confident fabrication rather than a low score.**
When a trained extraction model cannot find the quantity, it returns nothing or returns it with a low confidence, and our gate catches it. When an LLM cannot find the quantity, it very often returns a plausible number — one that is on the page somewhere, or one that makes the arithmetic work. That failure is invisible downstream, arrives with no signal attached, and lands in a reconciliation as a number nobody can distinguish from a correct one. This is the single worst outcome the system can produce, and Option B makes it more likely, not less.

Cost was not a deciding reason and should not be recorded as one. At our volume both options are affordable.

## Consequences

### What this gives us

- A per-field confidence score that the confidence gate ([NWD-103](../stories/NWD-103.md)) can threshold, and that is carried into the warehouse as `MIN_CONFIDENCE`.
- Deterministic, version-pinned extraction. A document can be re-analysed in a year against the model that originally read it.
- Page provenance per field, which turned out later to matter more than we expected — see [ADR-0003](0003-one-failing-field-rejects-the-document.md) and [NWD-142](../bug-NWD-142.md).
- Predictable spend: ~$420/month at 12,600 pages, with the classifier billed separately so we can see it.
- Onboarding a counterparty is a YAML block plus a trained model, with no Python change.

### What this costs us

- Two days of labelling per new layout, done by a person, before that counterparty can be onboarded. This is the boring part and there is no way around it.
- A model registry to manage: which model version is live for which counterparty, and who retrains when a layout drifts.
- A hard dependency on one Azure service in the critical path. If Document Intelligence is down, nothing ingests. Mitigated by the raw landing zone — documents queue rather than being lost.
- Documents from an unseen layout cannot be processed at all until somebody labels them. Option B would have made a guess. We would rather have a queue than a guess.

### What we have accepted that we do not like

- **A counterparty who changes their layout breaks us quietly.** Confidence scores fall across the board, the straight-through rate drops, and the exception queue fills. Nothing errors. We have made that detectable — it is the runbook's first diagnostic and the reason M2 is monitored daily — but we have not made it impossible.
- **We are slower to onboard than Option B would have been.** A fortnight per counterparty rather than an afternoon. Atul flagged this against the roadmap and it stands as a known cost.
- **We may be wrong in eighteen months.** Calibrated per-field confidence from language models is an active area, and if it arrives, reason 1 disappears. Reasons 2 and 3 do not, but they are more arguable.

### Objections on the record

- **Ravi Mullick, 2026-06-15:** argued that a hybrid was worth prototyping — Document Intelligence for the two known layouts, an LLM as a fallback for unrecognised documents, with the LLM's output routed straight to the exception queue rather than to the warehouse. **Not accepted for v1**, on the grounds that a second extraction path doubles the surface a reviewer has to check and the exception queue already handles unknown layouts adequately. Recorded as a genuine option for v2 and logged in the tech debt register. Hem's note: this is the strongest argument against the decision and it was not a bad idea.

## Revisit when

- A calibrated, vendor-pinned, per-field confidence signal becomes available from a language model — at which point reason 1 no longer holds and this should be reopened properly.
- Onboarding cadence exceeds one counterparty per week, at which point the labelling cost becomes the bottleneck rather than an annoyance.
- Not on a date. Dates make people re-litigate decisions that are still correct.

## References

- [PRD §7 — What happens when the system is not confident](../prd-counterparty-ingestion.md#7-what-happens-when-the-system-is-not-confident)
- [ADR-0002 — Persist bronze before parsing](0002-persist-bronze-before-parsing.md)
- [ADR-0003 — One failing field rejects the document](0003-one-failing-field-rejects-the-document.md)
- Threshold sweep, 60 labelled documents, 2026-06-16 — the measurement behind the numbers in [`spec-confidence-gate.md`](../spec-confidence-gate.md)

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/adr/0001-extraction-approach.md`**
>
> Produced by: Architect (Hem Singh) using P12 — Record an Architecture Decision
> Approved by: Gautam  (Team Lead) 2026-06-15 · Atul(PM) 2026-06-16
>
> Anyone consuming this file can rely on finding:
> - The context and the two constraints that made this a decision rather than a default, with volumes and costs stated
> - Four options with honest arguments for and against, including the one nobody was going to pick
> - The decision with three numbered reasons for rejecting LLM-based extraction
> - Consequences in three parts, including what we accepted and dislike
> - Ravi Mullick's objection, attributed and dated, with the reason it was not accepted
> - A revisit trigger, not a revisit date
>
> This file does **not** contain: the threshold values, the extraction implementation, model training procedure, or the schema.
> Those live in: `spec-confidence-gate.md` (P11), `core/extract.py`, `data-contract-counterparty-position.md` (P13).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: never edit the Decision section. Supersede with a new ADR and set this one's status to "Superseded by NNNN". Doing so requires re-checking `spec-confidence-gate.md`, `core/extract.py`, `core/classify.py`, and the cost model in `release-readiness-v1.0.md`.
