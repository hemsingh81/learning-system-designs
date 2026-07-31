# 02 — Sprint 1: Discovery

← [01 — Sprint 0: Foundations](01-sprint-0-foundations.md) · [Case study index](README.md) · Next: [03 — Sprint 1: Design](03-sprint-1-design.md)

> **One line:** Amara turns a rambling email into eight stories, and asks a four-word question that adds a whole screen to the project.

---

## 1. Monday, 09:20

Amara Osei arrives with a printed email, which is unusual enough that Farhan comments on it.

It is two pages from Northwind's head of operations. It arrived three weeks after it was promised, opens with an apology about month-end and two people on leave, and contains — in its most specific paragraph — the entire written requirement for a project Kestrel has already signed a contract for:

> *"we need to stop manually keying broker statements — it's killing our T+1 targets."*

Everything else in the email is background, the apology, and a list of four people who should be on the distribution list.

Amara has seen this before. She spent six years on the operations floor of a custodian bank before moving into product, which means she can read that sentence and immediately produce about forty questions. What counts as a broker statement? All eleven counterparties or the top four? What happens when the PDF is unreadable? Who fixes it? Does "stop manually keying" mean zero human touch, or does it mean a human only touches the hard ones — because those are two different projects with two different budgets and two different go-live dates.

**She is not going to get those answers by emailing the client forty questions.** She is going to get them by writing down her best current understanding in a form specific enough that somebody can point at a sentence and say "no, that's wrong."

That document is a PRD, and by 09:55 she has a draft of one.

---

## 2. The vocabulary, since we're about to use it constantly

Most of this is jargon dressed as ordinary English. None of it is complicated. It's just named.

| Term | What it actually means |
|---|---|
| **Agile** | A family of ways of running projects where you build a small useful thing, show it to somebody, and change your plan based on what they say. The alternative — 200-page spec, disappear for a year, deliver something nobody wants — is what it was a reaction to. |
| **Sprint** | A fixed block of time, usually two weeks, in which the team commits to a specific list. The length never moves; the list does. Northwind runs Sprints 0 to 4. |
| **Backlog** | The ordered list of everything the team might build, most important first. Not a wish list. An ordered queue. |
| **Product Owner** | Owns that ordering and owns what "done" means to the business. Amara. When somebody asks "translation or the review screen first," she answers and her answer is final. |
| **Project Manager** | Owns dates, risk and sequencing. Farhan. Amara owns *what* and *why*; Farhan owns *when* and *what happens if it slips*. |
| **PRD** | Product Requirements Document. One document answering: what problem, for whom, measured how, and what's explicitly out. |
| **User story** | One small unit of work in the backlog, written from the point of view of somebody who wants an outcome. |
| **Acceptance criteria** | The specific, checkable conditions that make one story done. |
| **Discovery** | The phase before you build anything, where you work out what the problem actually is. This chapter. |
| **Story point** | A number expressing how big a story feels relative to other stories. Not hours. Explained properly in §8. |

**One distinction that matters more than the rest.** A PRD says *what problem and why*. A technical spec says *how*. They are different documents, written by different people, for different readers. The Northwind PRD does not contain the words "Azure," "Document Intelligence," "Python" or "0.90," and the moment it does, an architecture decision has been made by a product owner without anybody noticing.

---

## 3. P06 — writing the PRD

Amara runs [P06 — Write a Full PRD](../../AI-Prompts-Library/phase-1-discovery/P06-write-a-full-prd.md) at 09:40, with the operations email open in a second window.

### The two inputs that do all the work

The prompt has a lot of structure, but two blocks at the bottom carry it.

**The source material, pasted verbatim.** The whole email, including the apology and the distribution list. Not tidied. Not summarised.

> **Why verbatim matters.** If you summarise the brief before pasting it, you have already made the interpretation calls the PRD is supposed to surface, and you've made them invisibly. The mess is information. The fact that the head of operations spent a whole paragraph on a failed pilot from two years ago and one sentence on the actual ask tells you which one he cares about.

**What Amara already knows that isn't in the email.** Six lines of domain knowledge from the kickoff call:

```text
- Northwind runs two reporting books: EM (Emerging Markets) and EQ (Equity).
  ~$40bn AUM. Offices in London and Los Angeles.
- Their internal position and trade records come out of BlackRock Aladdin over a
  REST API. That side is structured and reliable. The problem is entirely the
  counterparty side.
- Volume is roughly 200 documents a day, 3 pages average, spiking hard at month-end.
- The named analyst on the client side is Priya Raman. She is currently the person
  doing the keying, and she will be the primary user of whatever we build.
- Their current straight-through rate — documents needing zero human touch — is 61%,
  because 61% is the share that already arrives as machine-readable data feeds
  rather than PDFs. The PDFs are the other 39%.
- Compliance require an audit trail on anything that touches the books of record.
```

It's tempting to leave that block empty and let the assistant ask. Amara doesn't, and the reason is arithmetic: those six lines removed four items from the open-questions list, which meant the client meeting on Wednesday spent its time on the questions that actually needed a client.

### What came back, and the one number that matters

The full PRD is at [`artifacts/prd-counterparty-ingestion.md`](artifacts/prd-counterparty-ingestion.md). Three excerpts, because these three are the ones that get quoted for the next nine weeks.

**The problem statement's third paragraph** — the one that isn't about the current process at all:

```markdown
A previous attempt to automate this step, an OCR pilot two years ago, made the
problem worse for a period. That system supplied values it was not confident in
without indicating uncertainty. The resulting incorrect values produced
discrepancies that were indistinguishable from genuine settlement failures, and
roughly two weeks of analyst time went into chasing them. This history is
directly relevant to how success is defined below.
```

**The goals table:**

```markdown
| # | Goal | Baseline | Target | How it is measured |
|---|---|---|---|---|
| G1 | Reconciliation breaks are detected on T+1 rather than T+2 | T+2 | T+1 | Timestamp of break report generation relative to trade date |
| G2 | Straight-through rate — the share of incoming counterparty documents that reach the reconciliation input with zero human touch | 61% | 85% within one quarter of go-live | Documents processed with no analyst intervention ÷ total documents |
| G3 | Manual keying of counterparty statements is eliminated as a routine daily task | 2 analysts, most of each morning | 0 hours of routine keying; analyst time spent only on flagged exceptions | Analyst time logging, or a count of documents routed to human review |
| G4 | No incorrect value enters the reconciliation input as a result of automated extraction | Unknown — the previous pilot's error rate was never measured | Zero. Any value the system is not sufficiently confident in must be withheld and flagged, never estimated | Sampling audit against the source PDF |
```

**G4 is stated as an absolute, not a percentage, and that is unusual for a goal.** It is correct here, and the reason is in the note underneath it:

```markdown
**Note on G4.** This is stated as an absolute rather than a percentage
deliberately. The source material is explicit that a wrong value is more
damaging than a missing one, because a wrong value produces a discrepancy that
looks genuine and consumes analyst time to disprove. A missing value produces an
explicit flag that costs a few minutes to resolve. These outcomes are not
symmetric and the system's design must reflect that.
```

The whole of that note came from one paragraph of a rambling email about a failed pilot.

**When a client tells you about a previous failure, that story is usually the real requirement.** Amara says a version of this out loud on the Tuesday and it's the most useful sentence anybody says that week.

### Why the goals aren't model metrics

Worth naming, because it's the single most common way this artifact goes wrong.

The obvious version of G2 is *"the extraction model achieves an F1 score of at least 0.94 on the held-out validation set."*

> **F1 score.** One number between 0 and 1 combining how often the model's answers were right with how many of the right answers it found. Data scientists use it because it's one number instead of two. It's a fine internal diagnostic. It's a terrible business goal, because nobody's day gets better when it moves from 0.93 to 0.94.

The version in the PRD is *"straight-through rate rises from 61% to 85% within one quarter."* Both are numbers. Only one of them means anything to Priya.

**The metric shapes the system, and this one shapes it hard.** If success were extraction accuracy, a system that guesses confidently would score well. Because success is straight-through rate *and* T+1 break detection, a system that guesses confidently scores terribly — its wrong guesses create fake breaks, operations stops trusting the break report, and T+1 gets further away rather than closer.

---

## 4. The key scene: "rejected to where?"

**Monday, 11:15.** Amara is reading the draft properly for the first time — not skimming her own output, actually reading it — and she stops at CAP-04.

Here is what the first draft said, in full:

```markdown
**CAP-04 — Report its own certainty and withhold when uncertain.**
For every value it extracts, the system must produce an indication of how
certain it is, and must compare that against a threshold. Values below the
threshold must not reach the reconciliation input. The thresholds must be
different for different kinds of value: a monetary amount that is wrong is
materially worse than a descriptive text field that is wrong.
```

That is a good capability. It's specific, it's checkable, it comes directly from the brief, and it names the asymmetry. Nothing in it is wrong.

Amara reads it twice and then asks, to nobody, because there is nobody else in the room:

> **"Rejected to where?"**

She takes it to Rahul at lunch and says it properly:

> "Rejected to where? Priya still has to do something with it. Right now you've built her a system that does 80% of her job and gives her the other 20% in a worse format than she had before."

### Why this is the pivotal moment of the whole project

Read CAP-04 again with that question in your head.

It says values below the threshold must not reach the reconciliation input. It says nothing about where they *do* go. And the natural reading — the reading an engineer will take, the reading an AI will take, the reading almost every pipeline in the world implements — is **rejected and logged**.

Rejected and logged is perfectly reasonable. It's what a lot of pipelines do. It's also, from Priya's side, a catastrophe, and it's worth being precise about why:

**Before the project**, Priya opens 200 documents and types them. Slow, but she has a complete picture. She knows what's done and what isn't. She has the PDF in front of her.

**After the project, with "rejected and logged"**, Priya gets 170 documents she never sees, and 30 documents that failed — as **log lines**. In an engineer's log. With no PDF beside them, no indication of which field failed, and no way to fix and release. Her working day is now: monitor a log she doesn't have access to, find the failed documents, hunt down the originals in an email folder, open each one, type the whole thing into the spreadsheet again.

**She has lost the batch and kept the work.** The 20% that remains is harder than it was, not easier, because the system has taken away her overview and given her nothing in return.

Amara has personally chased a reconciliation break at 7pm on a settlement date, which is why she reads a capability and instinctively asks what the person on the other end does with it. That instinct is not a product-management technique. It's six years on an operations floor.

### What the question produces

Three things, immediately.

**First, a new capability.** CAP-05 goes into the PRD:

```markdown
**CAP-05 — Route anything uncertain to a human, with the reason.**
When a document is withheld, an analyst must be able to see it, see specifically
which value or values fell below threshold, see the source document alongside,
correct it, and release it. The reason must be specific enough to act on.
"Extraction failed" is not sufficient.
```

The last two sentences are Amara's, written by hand, and they are the sentences Ji-woo builds a screen from six weeks later.

**Second, a change to a non-goal.** The non-goals list gains:

```markdown
4. **This project does not aim for 100% automation.** A defined share of
   documents will be routed to human review by design, and that is a success
   condition, not a failure.
```

Which sounds like a caveat and is actually a design decision. It says out loud that the 15% is planned, so that nobody in Sprint 3 treats an exception as a defect.

**Third, an open question that becomes the most expensive decision in the project.** More on that in §5.

### The thing that makes this scene worth a whole section

**The AI did not do anything wrong.** CAP-04 is a faithful, well-written capability derived from the source material. The email said "I'd rather it told us it didn't know than gave us a number that's wrong," and CAP-04 says exactly that.

What the email did not say, and what the AI therefore had no way to supply, is what happens to the ones it doesn't know. That gap existed in the client's own head — the head of operations knows perfectly well that Priya will deal with the rejects, so obviously he didn't write it down.

**A gap that everyone considers obvious is the gap that survives every review.** It survived the client's email. It survived the first PRD draft. It survives, in [Chapter 3](03-sprint-1-design.md), a second time, in a place where it is considerably more expensive.

---

## 5. Wednesday: the client answers

Amara sends the PRD Tuesday morning with eleven open questions and a note saying she'd like forty-five minutes on four of them.

The call is on Wednesday. Nine of eleven questions get answered, one gets "ask Compliance, they'll be slow," and one — **Q2** — gets a five-minute answer that runs twice as long as it needed to because the head of operations wants to tell the OCR-pilot story again.

Q2, as written:

```markdown
| Q2 | Confirm A6: if a statement's rows cannot all be extracted with confidence,
       is withholding the entire document acceptable, even though it means more
       analyst work? | Head of Operations + Reconciliation owner | The single
       most important design decision in the project |
```

Amara expected the answer to be no. Her working assumption, from the operations floor, was that people want as many rows as they can get and will tolerate gaps.

The answer was the opposite, emphatically:

> "Hold the whole thing. All of it. I'd rather Priya opened forty documents a day than have one half-loaded statement produce a break that looks real. We've done the other version. It cost us a fortnight."

That answer becomes design invariant number two — **one failing field sends the whole document to review** — and it is the rule the whole architecture is built around. It is also the rule that gets argued about in [Chapter 3](03-sprint-1-design.md), challenged again in [Chapter 7](07-sprint-3-verify.md), and violated in [Chapter 8](08-sprint-3-rework.md) by a bug nobody saw coming.

**Notice what made the question askable.** A6 was an *assumption* the prompt was forced to surface rather than a *fact* it quietly encoded. Had the first draft written "the system rejects the whole document when any field fails" as a stated capability, nobody would have asked the client, and the team would have got the right answer by luck and never known it was luck.

---

## 6. P07 — slicing it into stories

Wednesday afternoon, ten minutes after the call ends. Amara runs [P07 — Slice the PRD into Stories](../../AI-Prompts-Library/phase-1-discovery/P07-slice-the-prd-into-stories.md).

### The one rule that makes or breaks this

You have a system with layers: storage, extraction, business rules, database, screen. So you slice by layer.

```text
Story 1: Build the storage layer
Story 2: Build the extraction layer
Story 3: Build the rules engine
Story 4: Build the database schema
Story 5: Build the UI
```

That's **horizontal slicing** and it's very tempting because it matches how the system is drawn and how the team is organised. It's also close to useless, for one reason: **nothing works until all of it works.** You can't demo Story 1. You can't test Story 4 end to end. And you can't learn anything from any of them, because the questions you actually need answered — does the gate reject too much, does the screen make sense to Priya, does translation break the identifier match — all live in the interaction between layers.

**Vertical slicing** cuts the other way. Each slice is thin, but it goes all the way through every layer, and at the end of it something observable is different.

```text
NWD-101: A Broker Alpha PDF that arrives in the landing zone is retained
         unaltered and can be found again by date and counterparty
NWD-102: An arriving PDF is identified as a Broker Alpha position statement,
         or routed to review if we cannot tell
NWD-103: Every extracted value is checked against a confidence threshold, and
         if any value fails, the whole document is held back with the reason
```

**The test: could you show the finished thing to a non-engineer and would they understand what changed?** If the answer is "well, you'd have to look at the database," it's horizontal.

There's an honest complication. Some genuinely necessary work has no user-visible outcome — a storage client, a config loader, a schema. The answer is not to invent a fake user story for it. The answer is to fold it into the first vertical slice that needs it. NWD-101 carries the shared storage client and the content-hash duplicate check, and says so in its notes.

### The eight stories

| ID | Title | Owner |
|---|---|---|
| [NWD-101](artifacts/stories/NWD-101.md) | Land counterparty PDFs immutably in the raw zone | Backend |
| [NWD-102](artifacts/stories/NWD-102.md) | Classify an incoming PDF to its counterparty layout | Backend |
| [NWD-103](artifacts/stories/NWD-103.md) | **Gate every extracted field on its confidence score** | Backend |
| [NWD-104](artifacts/stories/NWD-104.md) | Translate EM documents to English before matching | Backend |
| [NWD-105](artifacts/stories/NWD-105.md) | Redact PII before anything is persisted | Backend |
| [NWD-106](artifacts/stories/NWD-106.md) | Transform extracted fields into the canonical position schema | Backend |
| [NWD-107](artifacts/stories/NWD-107.md) | Load positions into Azure SQL and Snowflake idempotently | Backend |
| [NWD-108](artifacts/stories/NWD-108.md) | Exception queue screen for analyst review | Frontend |

**NWD-108 exists because of a question asked on Monday at 11:15.** Without it there are seven stories, all backend, and Ji-woo has nothing to do until Sprint 4.

Here it is in full, because it's the one this chapter is about:

```markdown
## NWD-108 — Exception queue screen for analyst review

**As an** operations analyst
**I want** a screen listing every document that was held back, showing me exactly
which value failed and why, with the original document alongside it, so I can
correct it and release it
**So that** a held document costs me two minutes instead of being a dead end, and
the work that was automated stays automated

**Delivers:** CAP-05 (fully), and completes the human half of CAP-02 and CAP-04
**Depends on:**
- NWD-102 — needs classification failures to have something to show.
- NWD-103 — needs confidence failures, which are the bulk of the queue.
**Demo:** Show Priya the queue with six held documents. Open one. Show the failing
field highlighted, its score shown as a percentage, and the source PDF page beside
it. Correct the value, release it, and show it appear in staging within seconds.
Show the queue count drop to five.
**Out of scope for this story:**
- Bulk release of multiple documents. Open question Q6 in the PRD; not answered yet.
- Editing a value that passed the gate. Only failing fields are editable.
- Any reporting or analytics over the queue.
**Notes:** The beneficiary here is Priya specifically and the demo should be run
with her in the room, not for her. PRD goal G3 depends on this screen being fast
to use — if clearing an exception takes ten minutes, the 85% straight-through
target is irrelevant because the other 15% eats the day.
```

Two things about that story. **The Demo line names a real person and a real number of documents**, which means when it's demoed in Sprint 2 there's no argument about whether it's finished. And the last note is a warning that turns out to be load-bearing: Ji-woo builds the whole screen around the sentence *"if clearing an exception takes ten minutes, the 85% target is irrelevant."*

### The argument about CAP-08

The output flags one capability as uncovered:

```markdown
| CAP-08 Onboard a counterparty without a release | — | **NOT COVERED** |

**CAP-08 is not covered by any story.** Onboarding a new counterparty without a
software release is a property of how NWD-102 and NWD-103 are built rather than a
separate deliverable, but nothing in the current stories forces it. A Product
Owner decision is needed: either add a story that proves it, or accept that
CAP-08 is a design constraint on other stories and record it as such. Leaving it
as-is means nobody ever verifies it.
```

Rahul's position: adding a counterparty without a release is a property of the design, Sofia will honour it in the architecture, and a story for it is bureaucracy.

Amara's position: **untested properties are not properties.**

They compromise. No new story, but NWD-102's acceptance criteria will include onboarding a ninth counterparty by configuration only. That criterion passes, and in Sprint 4 Northwind adds a counterparty in forty minutes without a deployment.

Rahul was right about the design. Amara was right that nobody would have known.

### The thing nobody caught

The output's dependency diagram put **NWD-105 (redact PII) after NWD-103**. NWD-103 writes to staging. PRD constraint C3 says PII must not be persisted.

So either redaction moves earlier, or NWD-103's staging write isn't really persistence, and one of those is a design change.

Nobody caught it in the story review. It was caught eight days later by Sofia, writing the technical spec, asking her usual question. The fix was cheap because nothing had been built. It would not have been cheap in Sprint 3.

**Why it was missed is worth naming: the model ordered by data flow, and constraints do not respect the data flow diagram.** Everything in that diagram is correct as a description of how a document moves. The constraint cuts across it.

---

## 7. P08 — acceptance criteria, with Ananya in the room

Thursday morning. Amara and Ananya Iyer sit down together and run [P08 — Write Acceptance Criteria](../../AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) on NWD-103.

### Why they do it together

This pairing is the whole point of the prompt and it's easy to skip.

**Criteria written by a Product Owner alone describe what should happen.** They're correct, they're business-relevant, and they are almost entirely happy path, because a product owner thinks in terms of the outcome they want.

**Criteria written with QA in the room describe what happens when it doesn't.** Ananya's contribution to every session she's in is the same shape: *"and what if there isn't one?"*

Amara drafts AC-1 through AC-3 in about ten minutes. Ananya adds AC-4 through AC-8 in twenty, and four of the five are cases where something is absent, null, or malformed.

### The criteria

The full file is [`artifacts/acceptance-criteria-NWD-103.md`](artifacts/acceptance-criteria-NWD-103.md). These are the ones that matter later:

```markdown
**AC-1** — Given a Broker Alpha position statement where every extracted field
scores at or above its threshold, when the document is processed, then every
position row reaches staging and the document does not appear in the exception
queue.

**AC-2** — Given a Broker Alpha statement where the market value on one row
scores 0.91, when the document is processed, then no rows reach staging and the
document appears in the exception queue naming `market_value`, its score of 0.91,
and the threshold of 0.92 that was applied.
  [0.92 not 0.90, because broker_alpha overrides currency. This criterion exists
   to prove the override is real.]

**AC-3** — Given the same value of 0.91 on a Broker Beta EM confirmation, which
has no currency override, when the document is processed, then the document is
accepted.
  [This criterion asserts a NON-effect. It exists so that an implementation with
   a single global currency threshold fails.]

**AC-4** — Given a field the layout defines but the extraction response does not
contain, when the document is processed, then the document is rejected with a
reason naming that field, and the reason is distinguishable from a
below-threshold failure.
  [Ananya. "A missing field is not a low-confidence field and Priya's action is
   different — she is reading a value off the page, not judging one."]

**AC-5** — Given a field that is present with a value and a null confidence, when
the document is processed, then the document is rejected. A null confidence is
never treated as zero and never treated as passing.
  [Ananya. "If the service gives us nothing, we have not measured anything, and
   an unmeasured field is exactly the thing G4 is about."]

**AC-6** — Given a document with three failing fields, when the document is
processed, then all three appear in the exception queue, not just the first.
  [Ananya. "Otherwise the document bounces. Priya fixes one, releases it, it
   fails again on the second. Three trips for one document."]

**AC-8** — Given a new counterparty block added to configuration with a model id
and thresholds, when the pipeline next runs, then documents for that counterparty
are gated using the new thresholds and no Python file has changed.
  [This is the CAP-08 compromise from the story review, made executable.]
```

**AC-3 is the one to look at.** It asserts that something does *not* happen. Criteria that assert a non-effect are the ones people skip, and they're worth more than the happy paths, because without AC-3 an implementation with one global currency threshold passes every other criterion in the list.

**AC-6 is Ananya's best contribution and she got it from imagining a Tuesday**, not from a technique. Priya has forty documents. If each one takes three round trips because failures are reported one at a time, that's a hundred and twenty interactions, and the 85% target becomes irrelevant because the other 15% has eaten the morning.

---

## 8. P09 — estimating, and the failure mode nobody expected

Friday. Farhan and Rahul run [P09 — Estimate and Rank the Backlog](../../AI-Prompts-Library/phase-1-discovery/P09-estimate-and-rank-the-backlog.md).

### What estimating is for

Not accuracy. This is the part everybody gets wrong.

> **A story point** is a relative size. NWD-101 is a 3, NWD-107 is an 8. That doesn't mean 107 takes eight hours or eight days. It means it feels somewhere between two and three times as big as 101.
>
> **Why not hours?** Because humans are demonstrably bad at estimating hours and reasonably good at estimating relative size. Ask "how long will this take?" and you get optimism. Ask "is this bigger or smaller than that thing last month?" and you get something usable.
>
> **The scale** is 1, 2, 3, 5, 8, 13 — roughly Fibonacci, deliberately gappy, so people stop arguing about whether something is a 6 or a 7. Anything above 8 is not an estimate, it's a signal: *we don't understand this well enough yet.*

The output of estimation isn't a schedule. It's an ordering and a set of flags saying where the uncertainty is.

### What came back

```markdown
| ID | Title | Points | Confidence | Note |
|---|---|---|---|---|
| NWD-101 | Land counterparty PDFs immutably | 2 | High | Storage client + content hash. Well-understood shape. |
| NWD-102 | Classify to counterparty layout | 5 | Medium | Unknown: how many labelled samples a classifier needs. Spike first. |
| NWD-103 | **Gate every field on confidence** | **13** | **Low** | See note below. Largest story in the set and the least well understood. |
| NWD-104 | Translate EM documents | 3 | Medium | Translator API is straightforward; deciding WHICH fields to translate is not. |
| NWD-105 | Redact PII before persistence | 5 | Medium | Fail-closed behaviour is the work, not the PII call. |
| NWD-106 | Transform to canonical schema | 3 | High | Mapping code. Boilerplate. |
| NWD-107 | Load to Azure SQL and Snowflake | 5 | Medium | Two sinks, one idempotency rule. Snowflake auth is an external dependency. |
| NWD-108 | Exception queue screen | 8 | Low | Scope depends on PRD Q6 (bulk actions), unanswered. |

**On NWD-103 (13 points, low confidence).**
This story is not large because there is a lot of code in it. Estimated purely on
lines produced, it is smaller than NWD-107. It is large because two of its
decisions cannot be derived from anything currently written down:

  1. What the threshold for a monetary field should be. 0.90 is a starting point,
     not an answer. The right number depends on the observed confidence
     distribution for each counterparty and on how much analyst time an
     additional rejection costs — neither of which is known today.
  2. Whether a low-confidence line item inside a table rejects the whole document
     under the same rule as a header field. The spec does not exist yet and the
     shape of the extraction response for tables is not documented.

Neither is a coding problem. Both are judgement calls that require looking at real
documents and talking to Amara. I cannot size the second one at all and have
included it at the top of the range.
```

### The lesson, which is not the one Farhan expected

Farhan has estimated backlogs for eleven years. He knows his own biases: he is usually 30% under on integration work and usually right on anything he's built before.

**What he'd never had to account for is that a third of the backlog collapsed and a third didn't, for reasons that have nothing to do with complexity.**

Look at the table again with that in mind:

| Story | What Farhan would have said in 2022 | What it came out at | Why |
|---|---|---|---|
| NWD-101 | 5 | **2** | Storage client, content hash, path convention. It's plumbing, the assistant writes it correctly first time, and Sprint 0's context file means it writes it *our way* first time. |
| NWD-106 | 5 | **3** | Field mapping. Pure boilerplate with a schema on both sides. |
| NWD-107 | 8 | **5** | Two sinks and a MERGE. More boilerplate, and an external dependency that no amount of AI touches. |
| NWD-103 | 8 | **13** | Went **up**. |

The three that collapsed are the ones where **the work was typing**. Somebody had to write a hundred lines of correct, conventional, unsurprising Python, and that is now genuinely faster by a large factor.

NWD-103 didn't collapse, and it didn't collapse for a reason worth stating precisely:

> **The hard part of NWD-103 is deciding what number 0.90 should be, and no amount of code generation touches that.**

You can ask an assistant what a good confidence threshold for a currency field is. It will give you an answer. The answer will be plausible, it will probably be 0.90, and it will be **entirely uninformed by the thing that actually determines it** — which is the observed confidence distribution on Broker Alpha's specific scans, weighed against how much of Priya's morning an additional rejection costs.

That is a judgement made by looking at real documents and talking to a product owner. It's not a knowledge gap the model has. It's a gap in *the world*: the information does not exist yet, anywhere, for anybody.

### What Farhan changes about how he estimates

He splits every story into two numbers and stops reporting one.

```text
For each story, estimate separately:
  (a) PRODUCTION — how much correct code has to exist
  (b) JUDGEMENT  — how many decisions have to be made that cannot be derived
                   from the artifacts we already have

Report both. Do not sum them.

A story is fast when (a) is large and (b) is zero.
A story is slow when (b) is non-zero, regardless of (a).
```

Under that split, NWD-101 is `production: medium, judgement: none` and NWD-103 is `production: small, judgement: two open decisions`. And the second number is the one that predicts the calendar.

**Farhan's line at the retro, six weeks later:** *"I used to estimate how much there was to build. Now I estimate how much there is to decide, and the building is a rounding error until it isn't."*

Hold on to the second half of that sentence. It matters in [Chapter 5](05-sprint-2-build-backend.md), where the building really is a rounding error, and in [Chapter 7](07-sprint-3-verify.md), where it turns out not to have been.

---

## 9. What Sprint 1 discovery produced

| Artifact | Path |
|---|---|
| The PRD, agreed with the client | [`artifacts/prd-counterparty-ingestion.md`](artifacts/prd-counterparty-ingestion.md) |
| Eight stories, one file each | [`artifacts/stories/`](artifacts/stories/) |
| Coverage table, INVEST check, dependency diagram | [`artifacts/stories/README.md`](artifacts/stories/README.md) |
| Acceptance criteria for the flagship story | [`artifacts/acceptance-criteria-NWD-103.md`](artifacts/acceptance-criteria-NWD-103.md) |
| The ranked, estimated backlog | appended to [`artifacts/stories/README.md`](artifacts/stories/README.md) |

And one contract, written at the bottom of the PRD, which is the thing [Chapter 3](03-sprint-1-design.md) is about:

```markdown
> **Artifact contract — `artifacts/prd-counterparty-ingestion.md`**
>
> Anyone designing against this PRD can rely on finding:
> - The business problem and why it exists now
> - Success metrics, in operational terms, with current baselines
> - **What must happen when the system is not confident** — including who sees
>   it, in what form, and by when
> - What is explicitly out of scope for v1
> - The named users and what their working day looks like
>
> This PRD does **not** contain: technology choices, data schemas, API shapes, or
> sequencing. If you need those, they are the architect's job.
>
> **If any bullet above is missing or empty, this PRD is not done.**
> Do not design against it.
```

The third bullet is the one Amara added by hand on Monday afternoon, immediately after asking her question. She added it because she'd nearly lost the requirement once and wanted a named guarantee that would make losing it visible.

**It gets lost anyway, four days later, in a completely different way.** That's the next chapter.

---

## 10. The handoff

Sofia Marchetti picks this up. She is the next reader of the PRD and the first person who will design against it.

What she is guaranteed to find: eight capabilities with IDs, each described as an outcome rather than a mechanism, a non-goals list telling her what not to design, and constraints C1 through C5 stated as absolutes. C1 — *a wrong value is worse than a missing value* — is the sentence that produces the confidence gate and the sentence she quotes in [ADR-0001](artifacts/adr/) when she rejects the simpler design.

Farhan takes the open-questions list and nothing else, at first. Eleven questions with named owners is his risk register for the week.

Ananya takes the acceptance criteria and starts thinking about what she'd need to test them, which turns into the E2E harness in Sprint 2 and the bug report in Sprint 3.

Ji-woo takes NWD-108 and the two sentences Amara wrote by hand, and does not start building, because there is nothing to build against yet. She spends a day at Northwind watching Priya work instead, which turns out to be the highest-value day anybody spends in Sprint 1.

---

## 11. What this cost, honestly

The first run of P06 produced a capability called **CAP-09 — Provide a management dashboard showing ingestion volumes and error rates.**

Nobody at Northwind asked for a dashboard. It appeared because dashboards appear in documents shaped like this one. It is a perfectly sensible thing for a document ingestion system to have, and it was entirely invented.

Amara nearly left it in. It seemed harmless and probably useful. She cut it, moved it to open question Q12 — *"does operations want visibility into ingestion volumes, or is that already covered by existing monitoring?"* — and forgot about it.

Six weeks later, in Sprint 3, the client asked for exactly that dashboard. Because it had been sitting in the open-questions list as a **question** rather than in the capabilities list as a **commitment**, it was a scope conversation with a price attached, not a defect and an apology.

**The assumption you write down as a question is the one that does not cost you a sprint.**

The near-miss is the one in §4, and it's worth being blunt about how close it was. CAP-04 was written on Monday at 09:55. Amara read it properly at 11:15. If she had done what almost everybody does with their own AI output — skimmed it, thought "yes, that's what I meant," and sent it — then the PRD would have gone to the client with no exception queue in it, the client would have approved it (because from his side the rejects obviously go to Priya, that's not a thing you write down), and the first person to notice would have been Priya, at a demo, in Sprint 3.

That version costs a new screen, a new table, a new API surface, a change to the gate's output shape, and a conversation about the date.

It didn't happen. But the same gap opens again on Thursday, in the design session, and the second time nobody spots it for four days.

---

**Next:** [Chapter 3 — Sprint 1: Design](03-sprint-1-design.md). Sofia picks the extraction approach, writes three ADRs, has a real argument about one of them, and paraphrases the PRD from memory.

---

← [01 — Sprint 0: Foundations](01-sprint-0-foundations.md) · [Case study index](README.md) · Next: [03 — Sprint 1: Design](03-sprint-1-design.md)
