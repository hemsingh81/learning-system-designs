# 03 — Sprint 1: Design

← [02 — Sprint 1: Discovery](02-sprint-1-discovery.md) · [Case study index](README.md) · Next: [04 — Sprint 2: Planning](04-sprint-2-planning.md)

> **One line:** Hem makes three decisions that are expensive to reverse, has a real argument about one of them, and loses a requirement for six days by describing a document instead of pasting it.

---

## 1. Thursday evening, week one

Hem Singh reads the PRD at about six on the Thursday, at home, on a tablet, which is a detail that matters later.

It's a good PRD. Eight capabilities, four goals with baselines, five constraints stated as absolutes, and a section on assumptions that is longer than she expected and more honest than most. She reads it once, closes it, and opens an AI session because she wants to see the shape of the thing before Tuesday.

What she types is this:

> *"We're building a pipeline that reads broker statement PDFs and extracts positions into our warehouse. It needs to handle multiple layouts per counterparty and it can't put bad data in the warehouse. Design me the ingestion architecture."*

Every word of that is true. It is an accurate summary. It is roughly 90% of the PRD.

What comes back is genuinely excellent. Blob landing zone with an immutable raw path. A classifier step that routes uncertain documents away rather than guessing. Custom extraction models per layout family. A confidence gate with per-type thresholds. A bronze layer holding the raw response before anything is parsed, so a parsing bug next month costs nothing. And — because she said *"can't put bad data in the warehouse"* — documents below threshold are **rejected and logged**.

Rejected and logged.

She reads it twice, thinks *yes, that's it*, and goes to bed. **It is the best forty minutes of design work anybody does in Sprint 1 and it quietly deletes the one thing the PRD was most careful about.**

We'll come back to that in §7. First, Tuesday.

---

## 2. Tuesday morning: the branch

Hem opens Slack at 08:50 and finds a branch notification. Ravi has pushed `spike/extract-poc`.

It is forty lines of Python. It sends a page of a Broker Alpha statement to a large language model with the prompt *"extract the positions as JSON."* It works. On the one PDF he tried, it works beautifully — clean JSON, sensible field names, correct numbers.

**This is the exact moment the project can go wrong quietly for six weeks.**

Ravi's forty lines are not wrong. They are *plausible*. If you squint at the output you'd sign it off. What the output does not contain is any way of knowing which of those numbers the model was sure about and which it guessed, and Northwind's entire reason for buying this system is that a wrong number is worse than no number.

Hem does not tell Ravi he's wrong, because she does not yet know that he is. What she knows is that a decision which touches the rules engine, the exception queue, the audit trail and the monthly bill is currently being made by whoever pushed a branch first.

So she opens a fresh session and runs [P10 — Ultra Plan Mode](../../AI-Prompts-Library/phase-2-design/P10-ultra-plan-mode.md). Not to get an answer. To get **three answers, honestly compared, and then a hard stop before anybody writes code.**

---

## 3. What plan mode is, and why the stop gate exists

> **Plan mode** is a way of running an AI session where it is allowed to read, think and write a proposal, and is forbidden to change anything. No files created, no files edited, no commands that alter state.

Some tools have this as a switch. It doesn't matter much, because plan mode is really a prompt discipline: you tell the assistant in the first three lines what it may and may not do, and you tell it to stop at a specific point and wait for a human.

> **A stop gate** is a point where work halts and does not resume until a named human says so.

You might reasonably ask why that needs saying. Humans plan and check with each other all the time without ceremony.

The reason is speed and plausibility, and it's worth being precise about it.

When a **human** takes a wrong design and starts building, they build slowly. Day three, somebody notices. The wrongness surfaces because effort creates friction and friction creates conversation.

When an **AI** takes a wrong design and starts building, it produces four files, a config schema, tests that pass and a README, in about nine minutes. There is no friction. Every artifact looks exactly like the artifacts a correct design would produce.

> **Plausible-wrong is far more expensive than obviously-wrong, because obviously-wrong gets caught in an hour and plausible-wrong gets caught in a sprint.**

That asymmetry is the whole justification for the stop gate. You are deliberately reinserting the friction the AI removed.

There's a second reason for the structure of this prompt, which is that **if you name a technology in your question, you get that technology in the answer.** Ask "how should we use an LLM to extract these fields" and you will never hear about Document Intelligence. So Hem's decision statement names nothing:

```text
**The decision I need made:**
How do we turn a counterparty PDF into typed rows, given that every extracted
field must carry a confidence score we can trust and defend to an auditor?
```

And her criteria are in priority order, which is the part that does the work:

```text
**How I will judge the options — weight them in this order:**
1. Produces a genuine per-field confidence score.
2. Auditable and reproducible — the same input gives the same output, and I can
   show an auditor why.
3. Onboarding a new counterparty requires no code change.
4. Monthly cost at 12,600 pages.
```

---

## 4. The three options, explained from scratch

The plan came back with three, and the rest of this book assumes you know all three, so here they are properly.

### Option A — Azure AI Document Intelligence, custom extraction models

**What it is.** A managed service you post a PDF to and get named fields back — "this is the quantity, this is the settlement date" — rather than a wall of text. You train a **custom model** by labelling around fifty documents from one counterparty: you draw boxes saying "this box is the quantity," and it learns that layout family. Training is free; you pay per page analysed.

**The number, with the arithmetic shown:**

```text
200 docs/day × 3 pages × 21 business days = 12,600 pages/month
Custom extraction ≈ $30 per 1,000 pages → 12.6 × $30 = $378/month
Custom classifier  ≈ $3  per 1,000 pages → 12.6 × $3  =  $38/month
                                                       ───────────
                                                       ≈ $416/month
```

Labelling effort: about 50 documents per layout for production, four hours for a first pass. **Fifteen documents is enough to prove the approach** before committing to fifty, which is the sort of distinction a good plan surfaces and a bad one glosses over.

**How it fails.** A counterparty changes their layout materially and the model's confidence drops across the affected fields. That is a **loud** failure: the documents go to the exception queue rather than loading wrong. You notice it as a spike in Preeti's queue on the day it happens, not as a break report three weeks later.

**What you give up.** Day-one support for a brand new counterparty. You cannot onboard a broker in an afternoon; you need documents to label first.

**The part that decides everything.** Every field comes back with a **confidence score** — a number between 0 and 1 saying how sure the model is that it read that field correctly.

### Option B — a large language model

**What it is.** Send the page text or the page image to a general-purpose language model with an instruction describing the fields you want, and parse the JSON it writes back. Ravi's spike.

**Why it's tempting, genuinely.** Zero training data. No labelling. It handles a brand new broker layout on day one because it is reading the document the way a person would. It is the fastest path to a first result and it is not close.

**The number:** roughly 2,500 input tokens per page plus ~600 output. At 12,600 pages, about 39 million tokens a month. Cost is model-dependent and the plan wrote `UNKNOWN — verify`, which is the correct behaviour and which we come back to in §12.

### Option C — OCR plus regular expressions

**What it is.** **OCR** — optical character recognition — turns the pixels of a scanned page into characters. You then use **regular expressions** (small pattern-matching rules: "a run of digits, a comma, two more digits") to pull values out of that text by position or by nearby labels.

**Why it's here and why people underrate it.** It costs almost nothing per page, it is completely deterministic, and every rule is readable by a human. For a fixed-layout document from a cooperative counterparty this is a genuinely fine answer.

**How it fails.** A pattern matches the wrong thing. If Broker Alpha inserts an "Accrued Interest" column before "Market Value," a positional rule now reads accrued interest as market value, with total success and no complaint. Silent, and worse than option B's failure because it is **systematic** — every row on every document is wrong the same way.

**What you give up.** Confidence entirely, since a regex matches or it doesn't. And the no-code-change onboarding rule, since every new counterparty is a Python change, a review and a deploy. That's constraint C2, and it is disqualifying.

---

## 5. Why Hem rejects the LLM

This is the argument the book turns on, so it gets its own section. There are three reasons and they are not equally weighted.

### Reason one — there is no calibrated per-field confidence to gate on

This is the disqualifying one and everything else is supporting material.

> **Calibrated** means: when the model says 0.90, it is right about nine times out of ten. The number corresponds to something in the world. You can compare it to a threshold and the comparison means something.

Document Intelligence produces a calibrated confidence per field because that's what it was built to do — it's an extraction service whose output is fields-plus-scores, and the score is derived from the model's own measurement of how well the region matched.

You can, of course, ask a language model how confident it is. It will tell you. It will say `0.94`. And that number is worthless for gating, for a reason worth stating slowly:

> **The self-reported score comes from the same process that produced the value.** It is not an independent measurement of the answer. It is a second output of the same generation, produced by the same weights, under the same misreading. If the model has misread a smudged `14,500` as `14,600`, it does not know it has misread it — that's what misreading is — so it reports high confidence on the wrong number.
>
> **A confidence score that is correlated with the error rather than independent of it is not a confidence score.** It's a second opinion from the same source, which is not an opinion at all.

The consequence is not that the confidence gate would be weaker. It's that **NWD-103 as specified cannot be built on this approach.** There is no number to compare to a threshold. The story, the exception queue, the `MIN_CONFIDENCE` column carried into Snowflake, and G4 in the PRD all consume that number, and exactly one of the three options produces one.

Hem's line in the plan review, which Gautam writes down:

> "We are not choosing an extraction technology. We are choosing whether the invariant is enforceable or aspirational."

### Reason two — non-deterministic output is hard to defend in an audit

> **Deterministic** means the same input always produces the same output. Send the same PDF twice, get the same numbers twice.

Document Intelligence is deterministic in this sense for a given model version. A language model is not, or at least not reliably: the same page can produce a marginally different answer on a different day, and even at the lowest temperature settings the guarantee is weaker than "identical."

For most systems this is a shrug. For this one it isn't, and the reason is constraint C2 from the PRD:

```markdown
**C2 — Anything touching the books of record must be auditable.** Compliance
requirement, non-negotiable. Every persisted value traces to a source document.
```

> **An audit trail**, in this context, means: somebody can point at a row in the warehouse and ask "why does this say 40,000?" — and you can answer with evidence rather than with a description of your process.

With Document Intelligence, the answer is: here is the exact JSON the service returned, stored in `bronze/broker_alpha/2026-03-11/{sha256}.json` before we parsed a single field. Here is the confidence it reported. Here is the threshold in force that day, in `config/sources.yaml`, in version control. Here is the original PDF. Reprocess it yourself and you'll get the same thing.

With a language model, the honest answer is: here is what it said at the time. Run it again and you may get something slightly different, and that is a property of the tool rather than a fault.

Hem's recurring question — **"what does this look like when it's wrong?"** — has a concrete answer here, and it isn't about the model at all. It's about the conversation eighteen months later when somebody from compliance asks why a position was booked at a value nobody can reproduce.

### Reason three — token pricing is harder to forecast than per-page pricing

The weakest of the three, and Hem says so, and it still matters because of constraint C5.

C5 is not "cost must be low." It is **"cost must be predictable."**

- Document Intelligence bills **per page**. Northwind already forecasts document volume, because operations plan headcount against it. A per-page price is a number finance can put in a budget line and not revisit.
- A language model bills **per token**, and token count depends on how much text is on the page, which depends on the broker's layout, whether it's a scan, how many positions the fund held that day, and whether it's month-end. All of those move together in the same direction at exactly the wrong time.

The absolute figures are probably comparable. That was never the point. **The point is which one you can put in a budget for a year, and the answer is the one whose driver is a number the business already tracks.**

Atul's contribution to this part of the argument is one sentence and it settles it: *"I can defend a number that goes up when volume goes up. I cannot defend a number that goes up and nobody can tell me why."*

### Why the answer turns out to be A

Everything else about the three options is arguable. Cost is comparable at this volume. Effort is comparable over a quarter. What is not arguable is that **the confidence gate, the exception queue and the audit trail all consume a per-field confidence number, and exactly one of the three options produces one.**

That single sentence is the ADR.

---

## 6. The three ADRs

### What an ADR is

> **ADR** — Architecture Decision Record. A short numbered document capturing exactly one decision, at the moment it's made, so nobody has to reconstruct the reasoning later.
>
> **Short** — one to two pages. Longer and it becomes a design document and stops being read.
> **Numbered** — `0001`, `0002`, in the order made. The number is the citable name.
> **One decision** — if you write "and we also decided," you have two ADRs.
> **A record** — past tense, permanent, never quietly edited. When a decision changes you write a new ADR that supersedes the old one, and the old one stays with a status of `Superseded by 0011`.

The section people skip is **Consequences**, and it's the section that makes the document worth writing. An ADR listing only benefits is a sales pitch.

Three documents, three questions, and it's worth having the distinction:

```text
PRD   → why does the business want this?      (Preetinka, living)
ADR   → why did we choose this over that?     (Hem, frozen)
Spec  → what exactly does the system do?      (Hem, living)
```

Hem writes all three ADRs with [P12](../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md), on the days the decisions were made, which is the rule that matters most and the one most often broken.

> **If you cannot write the ADR in twenty minutes, you have not actually made the decision yet.** Hem uses this deliberately: when a decision feels agreed but the ADR won't come out, she goes back to the room.

### ADR-0001 — Use Document Intelligence custom models, not an LLM

Written Tuesday afternoon, straight out of the plan. [`artifacts/adr/0001-extraction-approach.md`](artifacts/adr/).

The deciding factor is one sentence, and P12 forces it to be one rather than five:

```markdown
## Decision

We will extract fields using Azure AI Document Intelligence custom extraction
models, one per layout family, with a custom classifier in front.

**The deciding factor:** it is the only option that produces a per-field
confidence score from the extraction step itself, and every downstream component
— the confidence gate in NWD-103, the exception queue in NWD-108, and the
MIN_CONFIDENCE column carried into Snowflake — consumes that number. A
self-reported score from a generative model is produced by the same process that
produced the error, so it is correlated with the mistake rather than independent
of it.
```

And the reversal trigger, which is what turns a decision into something you can monitor:

```markdown
## Reversal trigger

If Northwind's counterparty list turns over faster than we can label it — more
than two new layouts per month for two consecutive months — labelling cost
dominates and a hybrid becomes worth building: a generative model for unseen
layouts, routed straight to review rather than to silver. At the current rate of
roughly one new counterparty a quarter this is not the case.

The observable signal is the count of new `model_id` entries added to
config/sources.yaml per month.
```

### ADR-0002 — Persist the full API response to bronze before parsing

Written Wednesday, two days after the decision, and the ADR says so at the top — *"written 2 April from Tuesday's notes; the option list may be incomplete."* That line costs nothing and preserves trust, and Hem writes it every time she's late.

> **Bronze, silver, gold** is a naming convention for three stages data passes through. **Bronze** is exactly what arrived, untouched. **Silver** is cleaned and typed but still per-source. **Gold** is modelled and joined for consumption.

The decision is that the complete JSON response from Document Intelligence is written to `bronze/{broker}/{yyyy-mm-dd}/{sha256}.json` **before a single field is read out of it.**

The cost is storage, which is negligible. The benefit has two halves:

```markdown
## Consequences

**What this makes easier**
- A parsing defect found next month is fixed by reprocessing files we already
  have. We do not re-upload 12,600 pages and pay $378 again.
- An auditor asking why a row has its value gets the actual bytes the decision
  was made from, not a description of the process.
- A spike can be run against real responses with no Azure call at all, which is
  why Step 0 of the implementation plan costs forty minutes instead of a day.

**What this makes harder**
- Bronze is PII-bearing until redaction runs. Retention and access control on
  the bronze container are now a real problem rather than a theoretical one, and
  the answer is not yet written down. Raised as an open question.
- Every schema change to the extraction response is now something we have
  historical data in the old shape for. Reprocessing is not automatically
  backwards-compatible.
```

**That second "makes harder" bullet is the honest one**, and it's the kind of thing that only appears because P12 demands the list be non-empty and demands the middle list be the longest.

There's a line in the notes worth quoting, because it's the sort of reason teams hide:

```markdown
Storage was chosen partly because Northwind's platform team had already approved
ADLS Gen2 and approving anything new takes six weeks. That is a real reason and
recording it means nobody spends a day in eight months wondering why we did not
use something more suitable.
```

### ADR-0003 — One failing field sends the whole document to review

Thursday morning, in the spec review, and this one causes a real argument.

Rule R3 in the draft spec says: the document decision is ACCEPT only when every field passes. One failure sends the whole document to review, with no rows written.

**Ravi objects**, and his objection is completely reasonable:

> "A Broker Alpha statement has fourteen positions. If one settlement date scores 0.83, we're throwing away thirteen perfectly good rows and giving Preeti a whole document to re-key. That's going to tank the straight-through rate and she's going to hate us."

Gautam thinks partial ingestion sounds sensible too. Preetinka is not sure.

Hem's answer is her recurring question, pointed at Ravi's proposal rather than at her own:

> **"What does this look like when it's wrong?"**

And then she walks it through. Thirteen rows load. The statement *looks* complete. The missing fourteenth position appears in the reconciliation report as `MISSING_EXTERNAL`, which is exactly the signal a genuine failed settlement produces. An operations analyst cannot tell the two apart from the report, so they investigate — email the broker, check the custodian — for a position that was simply never loaded.

Preetinka, who came off an operations floor and has personally chased that ghost, agrees immediately. Her framing, which goes into the ADR's notes verbatim because Hem wrote it down in the room:

> **"A break I have to chase and then find out was never real costs me more than a document I have to key."**

Decision made. Meeting moves on. Everyone satisfied.

**Why this needs the strongest ADR of the three** is that the reasoning is *non-local*. The cost of partial ingestion does not appear in the ingestion code at all. It appears two systems away, in the reconciliation report. You cannot see it from `core/rules.py`, which means anybody reading that file in isolation will correctly conclude the rule is wasteful and try to improve it.

Hem predicts this, in writing, in the Notes section:

```markdown
## Notes

Ravi raised the obvious objection at the time — thirteen good rows should not be
thrown away — and it is the right instinct. The counter is that the cost of the
fourteenth row is not paid in the ingestion pipeline; it is paid two systems
downstream, by a different team, in a form that looks like a real problem. Expect
this decision to be challenged again by anyone reading core/rules.py in
isolation, because from inside that file the choice looks purely wasteful. That
is the nature of a decision whose justification lives elsewhere.
```

She is right within nine weeks. In [Chapter 7](07-sprint-3-verify.md) a code reviewer reads `core/rules.py` and writes almost exactly Ravi's sentence. Gautam replies with a single line — the path to ADR-0003 — and the thread closes in one exchange.

And the consequences section contains the number that hurts:

```markdown
**What this makes harder**
- The straight-through rate is directly suppressed. One weak field on a
  twenty-position statement costs a whole document. At launch this will read
  materially below the 85% target and the number will understate actual
  extraction quality. **Accepted knowingly.**
- Preeti re-checks fields that were fine, because the queue presents the whole
  document. The UI must make the failing field obvious and everything else fast
  to skim, or this becomes forty minutes of wasted attention a morning.
```

**That second bullet is a design requirement for a screen that has not been briefed yet**, and Dzmitry picks it up directly. She never attended the spec review. She read one ADR.

---

## 7. The handoff failure

Now back to Thursday evening of week one, and the forty minutes of excellent design work.

### What happened

Hem's mental model of this system was set on that Thursday evening, and in that model, **documents below threshold are rejected and logged.**

Everything after it was built on top of that model, correctly and competently:

- **Tuesday**, P10 runs properly. It reads the PRD, the story and the acceptance criteria, and its read log is accurate. But P10's scope is the *extraction approach* — options A, B and C — and it never touches routing. The plan does not re-surface the exception queue because the plan was never asked about it.
- **Wednesday**, Hem drafts the spec with [P11](../../AI-Prompts-Library/phase-2-design/P11-write-the-technical-spec.md). Section 4, rule R3, says the document is rejected. Section 7 lists the reason codes. And the failure output shape says the gate returns a `GateResult` with a decision and a list of failures, which the rules engine **logs**.
- **Thursday**, the spec review happens. Four people read R3 carefully enough to have a twenty-minute argument about it. Nobody notices that the destination is a log file, because the argument was about *whether* to reject, not about *where the rejection goes*.

### The catch

**Friday morning, day 10.** Preetinka reads the draft spec, because Hem sent it round on Thursday night and Preetinka reads things.

She gets to section 7, the error-cases table, and asks the question for the second time in eight days:

> "Rejected to where?"

There is a pause on the call that Atul describes afterwards as the longest four seconds of Sprint 1.

Then Hem goes and looks, and finds that the spec she wrote has no exception record in it. Not a weak one. **None.** The word "queue" appears twice, both times in the out-of-scope list, pointing at NWD-108 as somebody else's problem.

NWD-108 existed the whole time. It was in the backlog, with acceptance criteria, owned by Dzmitry. What did not exist was anything on the backend that would ever produce a row for it to display.

### Why it happened, precisely

Not because anybody was careless. Three specific things, and they're the three ways every handoff gap gets created:

| How | What it looked like here |
|---|---|
| **Summarising from memory** | Hem typed a paragraph instead of pasting six pages. It was faster, and the summary felt complete because *she* remembered the rest. |
| **Paraphrasing into your own frame** | *"It can't put bad data in the warehouse"* instead of *"must reach a human, in a form they can act on, the same day."* An architect re-frames a problem in architecture vocabulary, and the re-framing drops what doesn't fit the frame. |
| **Assuming the artifact says something it doesn't** | Everybody in the spec review assumed the routing was covered somewhere, because NWD-108 existed and had a name. |

The second row is the one worth sitting with. Hem's paraphrase is not a bad summary. It is an *architect's* summary — it keeps the properties of the system and drops the properties of the working day. "Can't put bad data in the warehouse" is a statement about the warehouse. "Must reach a human in a form they can act on" is a statement about Preeti, and Preeti is not an architectural concern, which is exactly why an architect's paraphrase loses her.

### Why an AI makes this worse rather than better

Hand an incomplete brief to a **human** engineer and something specific happens: they get confused. They frown. They say *"wait — what am I supposed to do with the ones it can't read?"* Their confusion is a **signal** and it travels back to you.

Hand the same incomplete brief to an **AI** and you get a complete, confident, well-structured design that closes the gap by making something up that sounds sensible. Reject and log. Perfectly reasonable! It's what a lot of pipelines do!

> **The AI will never tell you that you handed it the wrong thing.** It has no way to know it's missing. It produces the best possible output for the input it was given, and the output looks *exactly as good* as it would have looked if the input had been complete.

The traditional early-warning system for a bad handoff was a confused colleague. The AI has removed it while making everything downstream faster.

### What it cost

Six working days between the paraphrase and the catch, and the cost lands entirely on one Friday.

| What had to change | Cost |
|---|---|
| Spec sections 5, 6 and 7 — the `GateResult` shape, four new scenarios, the exception record columns | 3 hours |
| The data contract, which had been drafted with no exception record at all | Rewritten Friday afternoon, finished Monday morning of Sprint 2 |
| Dzmitry's UI brief, which had been scoped as a "rejections log viewer" | Rewritten Friday evening, with Dzmitry staying late |
| Gautam's implementation plan for NWD-103, which he had scheduled for Friday morning | Written Friday at 16:30, against a spec that had been finished ninety minutes earlier |

That last row is the one that matters, because an implementation plan written ninety minutes after the spec it depends on is a plan written by somebody who has not slept on it. It is fine. It is also the reason the Sprint 2 planning session on Monday has a dependency in it that nobody has thought through, which is the subject of the next chapter.

### The version where nobody catches it

It's worth being honest about how this story is told elsewhere in the book.

[The handoff contract](../../AI-Prompts-Library/02-the-handoff-contract.md) tells this as the version where nobody catches it — where the design ships without an exception queue, Ravi builds it, and Preetinka discovers it at a demo in week six. That version has the gap costing a new screen, a new table, a new API surface and a conversation about the date.

**That is not a hypothetical.** It is the shape of the failure, told as the retro told it, compressed. In the retro Atul says there was never a story for the exception queue, and that is how it *felt* from where he was sitting, and it is not literally true — NWD-108 sat in the backlog the whole time with nothing on the backend to feed it. The distinction matters a great deal when you are working out what to fix, and it matters not at all when you are the person discovering it.

The honest summary: it was caught on the last day of the sprint, by the same person who caught it the first time, asking the same four words, and every day between Thursday and Friday was a day the team was designing the wrong system confidently.

### The habit that comes out of it

Gautam institutes one rule on the Monday and it takes ninety seconds per artifact.

**Before you build on somebody else's artifact, check it against its own contract.**

The PRD has a contract block, added by Preetinka at the end of [Chapter 2](02-sprint-1-discovery.md). So the first move in any session that consumes it is:

```text
Here is the approved PRD. Read it completely before responding.

<paste the entire contents of artifacts/prd-counterparty-ingestion.md>

Here is the contract this PRD guarantees:

<paste the contract block>

**First task, before any design work:** check the PRD against its own contract.
For each guaranteed item, quote the section that satisfies it, or state that it
is missing. List anything the PRD leaves ambiguous that a design would have to
invent.

Then stop. Do not design anything yet.
```

Gautam runs it retrospectively on every artifact produced so far, on the Monday of Sprint 2. It takes twenty minutes and it finds one more instance: the draft data contract had no exception record either, for the same reason, from the same source.

**The rule, in one line:** *paste the artifact, do not describe it.* It costs one extra paste and about ninety seconds of reading. It would have caught this on the Thursday evening.

---

## 8. P11 — the technical spec

The rewritten spec is at [`artifacts/spec-confidence-gate.md`](artifacts/spec-confidence-gate.md). It runs to 230 lines. Four parts are worth showing.

### The rules

```markdown
**R1** — A field passes when `confidence >= threshold`. Equality passes.
Comparison is on the float value as returned; no rounding before comparison.

**R2** — The threshold for a field resolves in this order, first match wins:
  1. a field-name override for this counterparty (`fields.<name>.min_confidence`)
  2. a type override for this counterparty (`thresholds.<type>`)
  3. the type default (currency 0.90, number 0.90, date 0.85, string 0.75)
  4. the hard default 0.90
Resolution never falls through to a lower value silently.

**R3** — The document decision is ACCEPT only when **every** field passes. One
failure produces REVIEW for the whole document, with no rows written to silver.
(ADR-0003.)

**R4** — A field named in the layout definition but absent from the extraction
response is a failure with `confidence = null` and `reason = FIELD_MISSING`.

**R5** — A field present with `confidence = null` is a failure with
`reason = CONFIDENCE_ABSENT`. It is **not** treated as 0.0 and it is **not**
treated as passing.

**R7** — The classifier is checked before extraction. Below 0.75, extraction is
not attempted at all, and the result is REVIEW with
`reason = CLASSIFIER_BELOW_THRESHOLD`. No extraction cost is incurred.

**R8** — A counterparty with no entry in `config/sources.yaml` is a configuration
error, not a document error. The gate raises `UnknownCounterpartyError`; the
document remains unprocessed in the raw zone. It does **not** land in the
exception queue, because the exception queue is for documents an analyst can fix
and this is not one.

**R9** — All failing fields are reported, not just the first. Preeti needs to see
every problem in one pass; returning only the first means a document bounces
through review repeatedly.

**R10** — The gate performs no I/O. It receives fields and a policy and returns a
result. Persisting the decision is the rules engine's job.
```

**R2 is the load-bearing rule in the whole document.** Threshold resolution order is exactly the kind of thing that gets decided by accident in code — whichever `if` happens to be checked first — and then differs between the gate, the exception queue and the report, and nobody notices for a quarter. Four numbered lines, first match wins, done.

**R8 is the one that took the longest to write** and it is the direct product of Hem's question. An unknown counterparty is not something Preeti can fix. Putting it in her queue would be putting an engineer's problem in an analyst's inbox, which is the exact inverse of the mistake this chapter is about.

**R10 exists because of testability.** A function that takes data and returns data can be tested without Azure, without a database, and without a network. Every scenario in section 6 is a unit test that runs in milliseconds, and that is why Ravi has 22 of them by the end of the next chapter.

### The interface

```python
def evaluate_confidence(
    fields: list[ExtractedField],
    policy: ConfidencePolicy,
) -> GateResult: ...

def load_policy(counterparty_id: str, config: dict) -> ConfidencePolicy: ...
    # raises UnknownCounterpartyError when counterparty_id is absent from config
```

`GateResult`:

| Field | Type | Null? | Meaning |
|---|---|---|---|
| `decision` | `"ACCEPT" \| "REVIEW"` | no | The document-level outcome |
| `min_confidence` | float | yes | Lowest confidence across fields that had one; null when none did |
| `failures` | list[FieldFailure] | no | Empty on ACCEPT; one entry per failing field on REVIEW |

### The scenario that asserts a non-effect

```markdown
**S2 — One currency field below the counterparty override**
Given counterparty `broker_alpha` with `thresholds.currency = 0.92`
And `market_value` has confidence 0.91 and every other field is above 0.95
When the gate evaluates the document
Then decision is REVIEW
And `failures` contains exactly one entry with `field_name = "market_value"`,
    `threshold = 0.92`, `reason = BELOW_THRESHOLD`

**S3 — The same value passes for a different counterparty**
Given counterparty `broker_beta_em` with no currency override (default 0.90)
And `market_value` has confidence 0.91
When the gate evaluates the document
Then decision is ACCEPT
[This scenario exists to prove R2 resolves per counterparty, not globally.]
```

**S3 exists only to prove S2 wasn't a global rule.** Without it, an implementation with a single global currency threshold passes every other scenario in the list.

### The open questions

Five of them, and one is a time bomb.

```markdown
- **Preetinka** — when Preeti corrects a field in the exception queue, is the corrected
  value re-gated, or is a human edit trusted by definition?
- **Preetinka** — does a document rejected purely on CLASSIFIER_BELOW_THRESHOLD go to
  the same queue as a field failure? Preeti's action is different — she is picking
  a counterparty, not fixing a number.
- **Ravi** — does the Document Intelligence response ever return a confidence of
  exactly 0.0, or is absence the only signal?
- **Hem** — line items are a repeating structure with per-item confidence. This
  spec treats fields as flat. Does a low-confidence line item reject the document
  under the same rule? ASSUMED: yes, same rule. **This needs its own spec section
  before NWD-106.**
- **Pankaj** — do we need a scenario for a document whose table spans a page
  boundary? The extraction response shape for that case is not documented
  anywhere I can find.
```

Read the last two again.

The fourth is Hem noting that the spec treats fields as flat when real responses have a repeating table structure, writing `ASSUMED: yes, same rule`, and moving on.

The fifth is Pankaj asking, on the Friday of Sprint 1, whether anybody knows what happens when a table crosses a page.

Nobody answers either of them. The Friday is the Friday described in §7, everything is compressed, and open questions that nobody owns on the last day of a sprint do not get chased. Hem marks both as carried to Sprint 2 and they are not looked at again.

**Five open questions on a first draft is healthy. Two carried into a build sprint unanswered is not, and the team knows it, and does it anyway.**

---

## 9. P13 — the data contract

Friday afternoon, rewritten from a version that had no exception record in it. Hem and Ravi together, running [P13](../../AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md).

> **A data contract** is the agreed shape of data crossing a boundary between two things that are built separately. Column names, types, nullability, units, and what happens when a value is missing. It exists because the two sides will be built by different people at different times, and "we'll sort it out at integration" means sorting it out on day eight of a ten-day sprint.

Two tables come out of it. The position row that reaches Snowflake:

| Column | Type | Null? | Notes |
|---|---|---|---|
| `CONTENT_HASH` | char(64) | no | SHA-256 of the source PDF. The idempotency key. |
| `COUNTERPARTY_ID` | varchar(32) | no | `broker_alpha`, `broker_beta_em` |
| `AS_OF_DATE` | date | no | Statement date, not receipt date |
| `INSTRUMENT_ID` | varchar(32) | no | The identifier used to match against Aladdin. **Never translated.** |
| `INSTRUMENT_NAME` | varchar(256) | yes | Descriptive. May be translated. |
| `QUANTITY` | decimal(28,8) | no | |
| `MARKET_VALUE` | decimal(28,4) | no | |
| `CURRENCY` | char(3) | no | ISO 4217 |
| `MIN_CONFIDENCE` | decimal(5,4) | no | Lowest confidence across every field on the document |
| `BRONZE_PATH` | varchar(512) | no | Where the raw response is stored. The audit link. |

And the exception record, the one that did not exist on Thursday:

| Column | Type | Meaning |
|---|---|---|
| `EXCEPTION_ID` | uuid | Surrogate key |
| `CONTENT_HASH` | char(64) | SHA-256 of the source document — groups all failures on one document |
| `BRONZE_PATH` | varchar(512) | Where the raw response is stored |
| `COUNTERPARTY_ID` | varchar(32) | |
| `FAILING_FIELD` | varchar(64) | One row per failing field |
| `FIELD_CONFIDENCE` | decimal(5,4) | Null where the reason is `FIELD_MISSING` |
| `THRESHOLD_APPLIED` | decimal(5,4) | The resolved threshold, so the analyst sees the bar |
| `REASON_CODE` | varchar(32) | From `ReasonCode` |
| `SOURCE_PAGE` | int | 1-based; null where unknown |
| `LINE_ITEM_INDEX` | int | Null for a header field; the row number for a line item |
| `CREATED_AT_UTC` | timestamp | UTC, no local time anywhere |

Two things in there are worth naming.

**`INSTRUMENT_ID` carries the note "never translated" and `INSTRUMENT_NAME` does not.** That distinction is written down on the Friday of Sprint 1 and it is violated in Sprint 2 anyway, which becomes bug NWD-138.

**`THRESHOLD_APPLIED` is there because of Preeti.** It would be entirely possible to store the confidence and not the threshold — the threshold is in config, after all. Storing it means the screen can show her `0.91 against a bar of 0.92` instead of `0.91`, which is the difference between "this number is bad" and "this number is nearly fine and here's why we stopped." Hem's argument for the column takes about ninety seconds and it is the single most user-facing decision an architect makes on this project.

---

## 10. P14 — the UI brief

Friday evening. Dzmitry has spent a day at Northwind watching Preeti work, and comes back with three observations that shape the whole screen:

1. **Preeti does not use a mouse for anything she does forty times.** She uses it for the PDF and nothing else.
2. **She reads the PDF first and the extracted values second**, every time, without exception. Not the other way round. Any layout that puts the form on the left and the document on the right is fighting her.
3. **She keeps a paper notebook** of counterparty quirks. Broker Alpha's dates are DD/MM. One custodian puts the currency in the header rather than per row. That notebook is the thing the system should eventually replace and definitely should not contradict.

The brief they write with [P14](../../AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md) is at [`artifacts/ui-brief-exception-queue.md`](artifacts/ui-brief-exception-queue.md). Its opening constraint is a direct quotation from ADR-0003:

```markdown
## The constraint this screen exists under

From ADR-0003: "Preeti re-checks fields that were fine, because the queue presents
the whole document. The UI must make the failing field obvious and everything
else fast to skim, or this becomes forty minutes of wasted attention a morning."

Therefore, two hard requirements, both testable:

**H1** — From opening a document, the failing field must be findable in under two
seconds without scrolling and without reading anything else. Measured by watching
five people who have not seen the screen before.

**H2** — A single-field correction must be completable with the keyboard alone,
in under four keystrokes from the point of arriving on the document.

Everything else in this brief is negotiable. These two are not.
```

**Dzmitry's framing, which she says at least twice a sprint:** *Preeti clears around forty exceptions in a morning, so every extra click is not one click, it is forty. Every time the PDF viewer loses its scroll position, that's forty times she has to find her place again.*

The brief also carries the sentence that becomes the smallest bug in this book:

```markdown
Confidence is shown to the analyst as a percentage — `82%` — never as a raw
float. The raw value is stored; it is not displayed. A number like 0.8234567 on
screen is noise that costs a fraction of a second of attention forty times a
morning, and it makes the screen look like a debugging tool rather than a
workspace.
```

It ships as `0.8234567` anyway. That's [NWD-139](artifacts/), it's one line, and it is in this book deliberately: not everything is a crisis, and a bug report that takes four minutes to fix is still a bug report.

---

## 11. The handoff

The design goes to two people.

**Gautam** takes the spec and the data contract into [P15 — Implementation Plan](../../AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md) at 16:30 on the Friday. What he is guaranteed to find: ten numbered rules, twelve scenarios covering every rule, a fixed set of reason codes, and an interface with types on both sides. What he is *not* guaranteed to find — and this is the part that matters in [Chapter 8](08-sprint-3-rework.md) — is anything about completeness. The spec's contract guarantees the thresholds, the per-field rules, the failure output shape and the exception routing. It guarantees nothing about whether all the data that should have been extracted actually was.

Nobody thought to ask, because the whole mental model was *"is this number trustworthy"* rather than *"is this number here."*

**Dzmitry** takes the UI brief and the exception record shape into Sprint 2 with nothing on the backend to call, which is the dependency Atul is about to find on Monday.

**Ravi** gets the steps table from the plan and a closed branch. `spike/extract-poc` is deleted rather than merged, and Hem makes a point of saying in standup that the spike did its job, because a spike that gets deleted after informing a decision is a success and it should not feel like one being thrown away.

Ravi asks why it's being deleted when it worked. Hem's answer:

> "It worked at the only thing we asked it to do, which was tell us what we lose."

---

## 12. What this cost, honestly

Two things, and the smaller one first.

**Hem's first run of P10 did not have the `Do not invent numbers` instruction in it.** The plan came back with an LLM cost of "approximately $95/month" against Document Intelligence's $378. No arithmetic. On those figures, the recommendation should have been the language model, and the plan said so.

Hem caught it because $95 for 39 million tokens felt low, and checking took four minutes.

The interesting part is that the corrected plan reached the *same conclusion the first one had been about to reject* — Document Intelligence — but for an entirely different reason. Cost was never the deciding factor. The confidence score was. The first plan had buried that under a cost comparison that turned out to be fictional, **which is a very good illustration of the fact that a plan can be wrong in its reasoning and right in its conclusion, and that those are not the same thing.**

**The larger cost is §7, and the honest accounting of it is this.**

The exception queue was lost for six working days by an architect who had read the document, agreed with it, and cared about it more than anybody except Preetinka. It was not lost through carelessness or through disagreement. It was lost because describing a document to an AI feels exactly like briefing a colleague, and briefing a colleague works, because the colleague asks questions.

The fix costs one extra paste.

What it actually cost was one compressed Friday, a data contract finished on a Monday morning it should have been finished on the Friday, a UI brief written by two tired people at seven in the evening, and an implementation plan written ninety minutes after the spec it depends on.

And one more thing, which nobody counted at the time. In the compression of that Friday, two open questions on the spec went unowned: the one about line items inside tables, and Pankaj's one about a table that spans a page boundary.

Both of them are the same bug.

---

**Next:** [Chapter 4 — Sprint 2: Planning](04-sprint-2-planning.md). Gautam turns the spec into a build sequence, Atul finds a dependency three weeks before it becomes a problem, and the Definition of Done grows three clauses that only exist because an AI writes the code.

---

← [02 — Sprint 1: Discovery](02-sprint-1-discovery.md) · [Case study index](README.md) · Next: [04 — Sprint 2: Planning](04-sprint-2-planning.md)
