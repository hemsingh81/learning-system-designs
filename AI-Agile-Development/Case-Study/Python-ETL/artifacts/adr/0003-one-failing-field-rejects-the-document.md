# 0003 — One failing field rejects the whole document

| | |
|---|---|
| **Produced by** | Sofia Marchetti, Architect |
| **Using** | [P12 — Record an Architecture Decision](../../../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) |
| **Date** | 2026-06-17 |
| **Status** | **Accepted, contested** |
| **Version** | 1.0 |
| **In the room** | Sofia Marchetti (Architect), Tomas Vargas (Backend), Amara Osei (PO), Rahul Nair (Team Lead), Ananya Iyer (QA) |

---

## Context

The confidence gate ([NWD-103](../stories/NWD-103.md)) evaluates every extracted field against a threshold chosen by field type. A Broker Alpha position statement has around six header fields and six fields per line item; a fourteen-position statement is therefore roughly ninety scored values.

The question this ADR answers: **when three of those ninety fail, what happens to the other eighty-seven?**

The options are not symmetric, and the asymmetry is the whole argument. This is not a question about data engineering. It is a question about what the recs team sees at eight the next morning.

A **reconciliation** compares Northwind's internal Aladdin positions against the counterparty's statement. Where a position exists on one side and not the other, the reconciliation raises a **break** classified `MISSING_EXTERNAL` — we hold it, the counterparty does not appear to. That is a serious break. It can mean a failed settlement, a wrongly booked trade, or a genuine dispute with a broker. Somebody picks up a phone.

So: if we load eleven of a statement's fourteen positions and drop three, the reconciliation produces three `MISSING_EXTERNAL` breaks. Those breaks are **indistinguishable from real ones**. Not "similar to". Indistinguishable — same classification, same shape, same urgency, same investigation.

## Options considered

### Option A — Row-level rejection. Load the good line items, quarantine the bad ones.

**What it is.** Each line item is gated independently. Line items that pass load into silver; line items that fail go to the exception queue individually.

**For.**
- Higher straight-through rate on the headline metric, immediately and substantially. On the 60-document sample, row-level rejection would have loaded 94% of line items automatically against 61% of documents.
- Less analyst work per document — Priya fixes three fields, not a whole statement.
- Intuitively "wasting less". Eighty-seven good values are eighty-seven good values.

**Against.**
- Produces exactly the break class described above. This is not a hypothetical: it is what the 2024 spreadsheet-macro process at Northwind did, and the recs team's stated reason for distrusting it.
- The straight-through metric becomes dishonest. A document 80% loaded is not 80% done; it is a document that has generated work in a different team.
- Partial state is hard to correct. When Priya fixes line 7, the document is now half-loaded and half-queued, and "release" has to mean "merge the fix into a document that is already partly in the warehouse".

### Option B — Document-level rejection. One failing field sends the whole document to review.

**What it is.** The gate collects every failure and returns one verdict for the document. Pass loads everything; fail loads nothing.

**For.**
- The warehouse contains only complete documents. A break in the report is a real break.
- The unit of correction matches the unit of work: Priya opens a document, fixes it, releases it, and it is done.
- Correction is simple — nothing was loaded, so releasing is a first load, not a reconciliation of partial state.
- The straight-through rate measures something true.

**Against.**
- A single misread security *name* — a descriptive field, threshold 0.75, which no reconciliation keys on — sends an otherwise perfect fourteen-position statement to a human. That is real waste and it is not a small amount of it.
- Depresses the headline metric, which the client is watching.
- Feels wrong to engineers, for good reasons. See the objection below.

### Option C — Hybrid. Document-level for material fields, row-level for descriptive ones.

**What it is.** Fields are tagged material (quantity, price, market value, identifiers, dates) or descriptive (security name, notes). A material failure rejects the document; a descriptive failure loads the row with the field null and a flag.

**For.**
- Recovers most of Option A's efficiency without the break-report problem, since a null security name does not create a `MISSING_EXTERNAL`.
- Directly addresses the strongest objection to Option B.

**Against.**
- Requires a materiality classification per field per counterparty, maintained forever, and wrong the first time somebody onboards a counterparty whose "notes" field carries the settlement instruction.
- Introduces a second kind of row in the warehouse — complete and partially-complete — which every downstream consumer must now understand. Reporting queries silently include them.
- Two rejection paths means two behaviours to test, two to document, and two for a future engineer to confuse.

## Decision

**One failing field rejects the whole document.** Option B.

1. **A wrong number is worse than no number, and a missing row is a wrong number in disguise.** A partially ingested statement does not present as incomplete data. It presents as a counterparty disagreeing with us, which is the most expensive false alarm this system can generate.
2. **The gate sits upstream of reconciliation precisely so the break report stays trustworthy.** If low-confidence or partial data flows through, the break report fills with false positives, and a control that operations stops trusting is a control that does not exist. That is the failure Northwind hired us to fix, not one to reproduce more efficiently.
3. **The unit of human work is the document.** Priya opens a PDF. She does not open a line item. Making the system's unit of decision match the analyst's unit of work is what makes one-pass correction possible, and one-pass correction is what makes forty documents a morning feasible.
4. **One behaviour is testable; two are arguable.** The gate returns one verdict. There is no partial state anywhere in the pipeline, which removes an entire class of bug we would otherwise have found in production.

We accept the cost in reason-form: a descriptive-field failure on an otherwise clean document sends it to review. Mitigation is the threshold, not the rule — descriptive strings are gated at 0.75, the loosest threshold in the system, precisely because they are the fields we least want to reject a document over.

## Consequences

### What this gives us

- The break report contains real breaks. This is the property everything else is in service of.
- No partial state anywhere: not in silver, not in gold, not in the exception queue.
- The straight-through rate (PRD metric M2) measures a true thing — documents needing zero human touch — and can be quoted to the client without an asterisk.
- Correction is a single flow. Fix, re-run the rules, load. No merge of half-loaded documents.
- The gate implementation is genuinely small: collect failures, return one verdict. `core/confidence.py` is under 140 lines including the docstring, and can be tested exhaustively without a mock.

### What this costs us

- A materially lower straight-through rate than Option A would report. Measured on the 60-document ground-truth set: 61% document-level against 94% line-item-level. Farhan raised this with Northwind before the parallel run so the number was expected rather than explained afterwards.
- More analyst work per rejected document, since the analyst reviews the whole statement rather than the failing field. Mitigated by the exception queue showing **every** failure at once and opening the PDF at the failing page ([NWD-108](../stories/NWD-108.md), criteria 3 and 5).
- Genuine waste on descriptive-field-only failures. Roughly a fifth of the rejections in the first parallel-run week were a security name and nothing else.

### What we have accepted that we do not like

- **We are throwing away correct work.** Eighty-seven good values discarded because three were not. Everyone in the room found this uncomfortable and nobody produced an argument that survived reason 1.
- **The metric we report is the harsher of the two available.** We could have quoted 94% to the client on the same pipeline by choosing Option A. Choosing the number that is true rather than the number that is flattering is a decision we will have to defend again, probably at a steering meeting, probably more than once.
- **This rule is what makes [NWD-142](../bug-NWD-142.md) so damaging.** The whole point of Option B is "no partial documents in the warehouse", and NWD-142 put a partial document in the warehouse anyway — not by violating this rule, but by going around it, because a line item that was never extracted has no field to fail. The rule was correct and it was not sufficient. That is recorded honestly here because a reader arriving at this ADR after reading the bug report deserves to see the connection stated, not implied.

### Objections on the record

- **Tomas Vargas, 2026-06-17.** Objected, on the record, and asked for it to be minuted.

  His argument, in summary: *"We are choosing to throw away eighty-seven correct values because three were uncertain, and we are doing it to protect a downstream report from a problem that report could solve itself. Reconciliation already classifies breaks. It could carry a `PARTIAL_SOURCE` classification and filter those breaks out — that's a one-line change in `recon/reconcile.py`. Instead we are paying for it forever, in every document, with analyst time. And the number we'll report to the client is a third lower than the number the same pipeline could report."*

  **Not accepted.** The counter-argument, and Sofia's reasoning as recorded: a `PARTIAL_SOURCE` classification requires the reconciliation to know which rows were dropped, and it cannot know that — the dropped rows are precisely the ones no data exists for. It would have to infer partiality from the document-level record, which means the pipeline must reliably know it dropped something, which is the assumption that [NWD-142](../bug-NWD-142.md) later demonstrated we could not make. The objection was reasonable on the information available in June, and the July evidence went against it.

  Tomas's second point — that the reported metric is a third lower for the same underlying quality — was accepted as true and is recorded above under costs. It is not a reason to change the decision.

  **Status:** Tomas implemented Option B as specified and raised no further objection. Ananya's note in the same meeting: *"If we do this, the exception queue has to be genuinely good, or we've just moved the cost onto Priya."* That became [NWD-108](../stories/NWD-108.md) criteria 3, 5, and 11.

## Revisit when

- The exception queue's median handling time exceeds three minutes for documents whose only failure is a descriptive field. That would mean the mitigation is not working and Option C deserves a real hearing.
- A counterparty's descriptive-field confidence is chronically poor enough that they alone account for more than a quarter of rejections. That is a model retraining problem first, and only a rule problem if retraining does not fix it.

## References

- [PRD §7.4](../prd-counterparty-ingestion.md#74-what-must-not-happen) — "a document must never be partially ingested"
- [`spec-confidence-gate.md`](../spec-confidence-gate.md) — the behaviour this decision governs
- [`acceptance-criteria-NWD-103.md`](../acceptance-criteria-NWD-103.md) AC-08, AC-14
- [NWD-142](../bug-NWD-142.md) — the defect that went around this rule rather than through it
- Threshold sweep and straight-through comparison, 60 documents, 2026-06-16

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/adr/0003-one-failing-field-rejects-the-document.md`**
>
> Produced by: Architect (Sofia Marchetti) using P12 — Record an Architecture Decision
> Approved by: Amara Osei (PO) 2026-06-17 · Rahul Nair (Team Lead) 2026-06-17
>
> Anyone consuming this file can rely on finding:
> - Why partial ingestion is dangerous, explained in terms of what the recs team sees, not in terms of data
> - Three options with honest arguments for and against, including the hybrid nobody wanted to rule out
> - The decision with four numbered reasons
> - Consequences in three parts, with the measured straight-through cost stated numerically (61% vs 94%)
> - **Tomas Vargas's objection in full, attributed and dated, with the counter-argument and its outcome**
> - The connection to NWD-142, stated rather than implied
> - A revisit trigger
>
> This file does **not** contain: the threshold values, the failure output shape, or the exception queue design.
> Those live in: `spec-confidence-gate.md` (P11) and `ui-brief-exception-queue.md` (P14).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: never edit the Decision section. Supersede with a new ADR, approved by Sofia Marchetti and Amara Osei jointly. Reversing this decision requires re-checking `core/confidence.py`, `core/rules.py`, `acceptance-criteria-NWD-103.md` (AC-08, AC-14), `ui-brief-exception-queue.md`, and `recon/reconcile.py`.
