# The Retrospective

← [Previous](09-sprint-4-release.md) · [Case study index](README.md) · Next: [Book README](../../README.md)

> **One line:** the finding is not that Ravi made a mistake — it is that nothing anywhere in the team's process ever asked whether all the data had arrived, and the best control in the system was the reason nobody noticed.

---

## 1. Thursday, 13 August, 10:00

Seven people in a room, or four in a room and three on a call, which is what these things actually look like. Atulhas a laptop and a document with one heading in it.

The retrospective is for Sprint 3, which ended on 31 July. It is two weeks late.

> **A retrospective** is a meeting at the end of a sprint where the team looks at *how* they worked rather than *what* they built. The demo is about the product. The retro is about the process. It is the only ceremony whose entire output is a change to the way the team operates.

Atul opens with the same two sentences he opens every retro with, and he means them:

> "This is about our process, not about any of us. If a finding comes out with a person's name attached, it is not finished yet."

That is not a nicety. A retro that becomes a search for who was responsible produces exactly one outcome, which is that next time nobody mentions anything. **You get one honest retro per team, and then you either keep it honest or you never get another.**

Then he says the second thing, which is less comfortable:

> "And before anything else — this retro was scheduled twice and dropped twice. That is finding number three and we are going to talk about it."

---

## 2. Where Sprint 3 actually went

Atul puts the arithmetic up first, because [P35](../../AI-Prompts-Library/phase-8-improve/P35-run-the-retrospective.md) runs in two passes and the first pass is the timeline, not the opinions. **A room that discusses feelings before facts remembers the sprint it thought it had.**

Sprint 3 was ten working days, 20 to 31 July. Here is where they went, in engineering days across the team:

| Activity | Planned | Actual |
|---|---|---|
| Build — NWD-104, NWD-105, remaining pipeline work | 5 | **4** |
| Test — Pankaj's end-to-end suite against 40 real documents | 3 | **2** |
| Bug fixing | **1** | **6** |
| Slack | 1 | 0 |

Six days of rework against an estimate of one.

Not six days of Ravi. Six days of engineering time across the team: Ravi for a day and three quarters on NWD-142 alone, Hem for most of an afternoon on the specification change, Preetinka on the approval, Pankaj re-testing, Gautam reviewing twice, and then four more defects that were smaller and still not free.

Atul's line, and he says it before anybody else can:

> "That estimate wasn't wrong because I'm bad at estimating. It was wrong because rework wasn't a thing I estimated. It had no line."

**Hold that.** It becomes the third action item and it is the only one that changes how the team is managed rather than how the system is built.

### The one-page timeline

The room agrees this before it interprets anything, which takes eight minutes and saves an hour of people misremembering:

| Date | Event |
|---|---|
| 17 Jul | NWD-103 marked done. Reviewed, merged, accepted by Preetinka |
| 22 Jul | Pankaj begins end-to-end testing against 40 real counterparty documents |
| 29 Jul | She notices `MISSING_EXTERNAL` breaks on a Broker Alpha statement she can see is complete in the PDF |
| 29 Jul | Opens the PDF and counts: 47 positions, table continues onto page 2. Snowflake has 31 |
| 29 Jul, 18:14 | Files NWD-142 with the document, page count, expected and actual row counts, and the break IDs |
| 30 Jul, 08:15 | Ravi reaches for the debugging prompt. Wrong tool. 25 minutes lost |
| 30 Jul, 09:00 | Reproduces offline from the bronze payload, first attempt |
| 30 Jul, 10:15 | Root cause: `core/extract.py:206` took `documents[0]` and discarded every other region |
| 30 Jul, 11:15 | Hem's counter-example kills the obvious fix. It becomes a specification problem |
| 30 Jul, 13:55 | Preetinka approves the spec amendment, with NWD-145 raised and dated |
| 31 Jul, 16:20 | Merged. Straight-through rate drops 61% → 58% |

---

## 3. What went well

The prompt asks for this first and the room usually wants to skip it. Atul does not let them, for a reason that is practical rather than pastoral: **the things that worked are the things you are about to accidentally stop doing.**

1. **Pankaj's bug report was good enough to prompt with directly.** [`bug-NWD-142.md`](artifacts/bug-NWD-142.md) carried the exact statement, the page count, the expected and actual row counts, the break IDs, and — crucially — the words `GUESS, not verified` in capitals in front of her theory. Ravi pasted it in whole and got a working reproduction on the first attempt.
2. **The bronze layer turned a production defect into an offline test in thirty seconds.** Hem argued for storing the raw API response before parsing on cost grounds in Sprint 1. The payoff was debugging, and nobody predicted it.
3. **NWD-139 took twenty minutes**, including the test. A cosmetic defect got a proportionate response. That is worth noting because the opposite is common and exhausting.
4. **Ravi raised NWD-142 as a specification problem rather than patching around it.** The merge was green at 10:52 and he did not ship it. That is not obvious behaviour and it is the reason the spec is not now a lie.
5. **Nobody argued when the ten-day parallel-run clock reset on 21 August.** It reset because of a real defect, everyone knew what the rule was, and the rule held.

---

## 4. Finding 1 — there was no data-completeness check anywhere in our process

This is the finding. Everything else in the document is either supporting it or is smaller than it.

The prompt drives a **why-chain**: keep asking why until the answer stops being about code. The room's temptation, every time, is to stop at level two, because level two feels like a conclusion.

| # | Question | Answer |
|---|---|---|
| 1 | Why were page-2 line items dropped? | `core/extract.py:206` took `result.documents[0]`. Document Intelligence returns one document object per detected *region*, and a table continuing across a page comes back as a second region |
| 2 | Why did no test catch it? | Every fixture in the suite was a single-page statement, because that is what Broker Alpha usually sends and that is what everyone had looked at |
| 3 | Why did nobody think to test a multi-page table? | Nobody knew the service behaved that way, and the spec did not describe multi-page documents at all |
| 4 | Why did the confidence gate not catch it? | **The gate checks confidence. Confidence was high on everything present. A field extracted at 0.97 and a field that never arrived are indistinguishable to a threshold check** |
| 5 | Why did nobody notice the gate had that blind spot? | Because it is the centrepiece of the design and everyone assumed it covered correctness. It covers wrong *values*. It has never covered *missing* values and was never designed to |

**Level two is where a room stops if you let it, and level two produces "write more tests", which is the useless answer.** More tests of the same kind, drawn from the same fixtures, built from the same understanding, catch nothing. The chain has to run to level five before it produces something you can act on.

### The finding, stated plainly

Nowhere in the process — not the PRD, not the stories, not the acceptance criteria, not the spec, not the code, not the tests, not the code review, not the end-to-end suite — did anything ask whether all the expected data had arrived.

Every check the team built verifies that the values present are trustworthy. None asks whether the values are all there.

And the comparison that would have caught it was available the whole time, on the document, in print. A Broker Alpha statement carries a summary line reading `Total positions: 47`, because a statement that does not tell you how many rows it has is a statement no operations team would accept. **The document declares its own row count and nothing in the system read it.** That comparison is one line of Python and no part of the process performed it.

### What else this gap could let through

The room spends fifteen minutes on this list and it is the most productive fifteen minutes of the morning, because it is the moment the finding stops being about PDFs.

- A truncated response from the Aladdin REST API — page one of three returned, no error raised. *(This was live in the dev environment and nobody had reported it, because nobody reports rows that were never there. Found during the sweep, fixed as NWD-146.)*
- Reconciliation running against a partial external side, because a statement is sitting unworked in the exception queue.
- A Snowflake `MERGE` that silently matches zero rows.
- A translated document losing a section.
- Any counterparty whose statement format nobody has yet seen at full length.

**This is not a PDF problem, a table problem or an Azure problem.** It is a class of failure the system had no defence against anywhere, and two instances of it were already running in the dev environment before Pankaj found the third.

---

## 5. Finding 2 — a good control created a blind spot precisely by being good

This is the finding people take away from this book, so it is worth reading slowly.

The confidence gate is well designed. It has its own architecture decision record, its own specification, forty-one tests and a principle repeated in every artifact the project produced: *a wrong number is worse than no number.* It works. It has never let a low-confidence value into the warehouse.

**That is exactly why nobody looked in that direction.**

Hem designed it. Gautam reviewed against it. Pankaj wrote acceptance tests around it. Preetinka wrote acceptance criteria that assumed it. Ravi built it and can explain every line. All five carried the same mental model, in which the confidence gate is *the thing that stops bad data reaching the warehouse*.

It stops bad **values**. The gap between those two statements is where NWD-142 lived for twelve days.

Hem's framing in the room, which Atul writes down verbatim:

> "We never asked what class of error the gate specifically does not see. We asked whether it worked. It does."

And Pankaj's, which is shorter and is the one that ends up in the release pack:

> "The gate isn't broken. The gate answers a question we never should have thought was the only question."

**The uncomfortable part is that the better a control is, the stronger this effect gets.** A weak control makes everyone nervous, and nervous people check the edges. A strong, well-documented, well-tested control is trusted, and trust is precisely the thing that stops you asking what it does not cover. There is no version of "build a better confidence gate" that fixes this. The fix is a question, asked of every design, in writing.

Hem's standing question — *what does this look like when it's wrong?* — turns out not to be quite enough on its own, and she is the one who says so. A wrong value is visible. Missing data is not. The question has to be asked in a form that reaches absence.

---

## 6. Finding 3 — this retro is two weeks late, and that is a finding

Sprint 3's retro was scheduled twice and dropped twice, because the rework consumed the time. The same pressure slipped two of Gautam's code reviews past the one-working-day commitment.

**The ceremony whose job is to improve the process is the first thing cut when the process is under strain.** That is backwards, and stating it plainly is worth more than apologising for it.

The room considers a rule that the retro cannot be moved, and rejects it. A rule nobody can keep under pressure is worse than an honest acknowledgement, because breaking it teaches everyone that the rules are decorative. What Atul does instead is move the retro to the last day of the sprint rather than the first day of the next, so that cutting it is a visible decision rather than a scheduling drift.

Noted. Not an action item, and the document says so, because a retro that turns every observation into a task produces a list nobody completes.

---

## 7. The action items

Three. Each has a named owner, a date, and a "done when" that somebody other than the owner can check.

> **"We'll be more careful" is not an action item.** It has no artifact, no owner, no date and no way of knowing whether it happened. It is a feeling written down. Every action item below was proposed in a vaguer form first.

| # | Action | Owner | Date | Done when |
|---|---|---|---|---|
| 1 | **Row-count reconciliation across every hop of the pipeline.** For each document, the count is asserted at each handover — declared on the statement → extracted → normalised → transformed → written to silver → merged to gold. Any hop where the count changes without an explicit reason fails the document and names both numbers. A daily summary reports every count mismatch across all sources. | **Pankaj ** | 4 Sep | The assertion exists at all five hops with a test each; the 24 July fixture fails at the extract hop; a deliberately truncated silver write fails at the load hop; the daily summary has run for five consecutive days |
| 2 | **Add the question "what does silently-missing data look like here, and what would detect it?" to the spec template**, as a section that cannot be left empty. Backfill an answered section into `spec-confidence-gate.md` and `data-contract-counterparty-position.md`. | **Hem Singh** | 28 Aug | The question is in the template; both existing specs carry an answered section; the next spec written does not pass review without one |
| 3 | **Estimates carry an explicit rework line.** Every sprint plan from Sprint 5 onward states rework as a named allocation with its own number, sized from the previous two sprints' actuals rather than from optimism. | **Atul** | Sprint 5 planning, 17 Aug | `sprint-5-plan.md` contains a rework line with a number and a stated basis; the retro after it compares that number to actual |

Three notes on those, because the shape of them matters more than the content.

**Action 1 is owned by QA, and that is deliberate.** The obvious owner is Ravi — it is pipeline code and he wrote the pipeline. Pankaj asks for it, and her argument wins in about thirty seconds: *the check that proves the data is complete should not be written by the person whose mental model let it be incomplete.* Not because Ravi is careless. Because he built the extractor and the fixtures in the same week from the same understanding of what a statement looks like, and a check built from that same understanding inherits the same blind spot. **A completeness check needs an independent source of truth, and so does the person writing it.**

**Action 1 also deliberately does not stop at extraction.** The NWD-142 fix already added two completeness rules at the extraction layer. Those close the hole where it was found. Action 1 closes it at the other four hops, where nobody has looked, and where the sweep in [Chapter 8](08-sprint-3-rework.md) already found two live instances.

**Action 3 is the only one that changes a person's job rather than the system.** Atul proposed it about himself, unprompted, which is the healthiest thing in the document. Rework was invisible in the plan, so it happened in the gaps, so the sprint was late for reasons nobody could point at.

### Rejected as action items

This table does more work than it looks like it does.

| Proposed | Why rejected | What it became |
|---|---|---|
| "Be more careful with multi-page documents" | Not checkable, relies on memory, asks a human to do a machine's job | Action 1 |
| "Add more edge case tests" | No artifact, no owner, no way to know when it is done | Action 1's per-hop assertions, which name the artifact and the assertion |
| "Hem should review all extraction code" | Creates a bottleneck and puts the fix in a person rather than in a process | Action 2, which puts it in the template |
| "Slow down — we're going too fast" | The speed is the point of the tooling and it is not the cause. The cause is that rework and review capacity did not scale with it | Action 3 |

**Every one of those was said out loud by a real person in the room.** Recording what they had to become is how the standard gets taught: at the next retro somebody proposes something vague, somebody points at this table, and the conversation is thirty seconds instead of ten minutes.

---

## 8. The dead code

Wednesday afternoon, before the retro. Gautam runs [P34](../../AI-Prompts-Library/phase-8-improve/P34-clean-up-dead-code.md), which is a different kind of tidying-up from the one people expect.

> **Dead code** is code that nothing calls and nothing will call. Not code that is ugly, not code you disagree with. Code with no path to it.

The reason it matters is not disk space. It is that every dead function is read by somebody in six months who assumes it does something, and then designs around it. **Dead code is a lie about what your system does, told to whoever reads it next.**

And there is an AI-era version of the problem, which is why this prompt is in the library at all: generated code is generous. Ask for a confidence gate and you may also receive a batch helper, a report class and two convenience wrappers, none of which anything calls. Clause D2 in the [Definition of Done](artifacts/definition-of-done.md) catches most of them at the door. Most is not all.

### Step 0 — is the search even reliable here?

The prompt refuses to classify anything as dead until it has established whether static analysis can be trusted in this repository, and in this one it cannot:

```text
$ rg -n "importlib|__import__|getattr\(|globals\(\)|eval\(" --type py
core/rules.py:41:    mapper = getattr(transform, spec["mapper"])
core/clients.py:88:  cls = getattr(sys.modules[__name__], client_name)
```

`core/rules.py:41` resolves a transform function **by name, from a string in `config/sources.yaml`**. Which means any function in `core/transform.py` may have zero code references and be entirely alive.

That is not an accident, it is invariant 8 working — *adding a counterparty is a YAML change plus a trained model, never a code change* — and it means every tool that reports unused functions will lie to you about this repository. So every candidate carries a full search across code, config, SQL, reconciliation and tests, and nothing is called dead on static analysis alone.

**The one that proves the point:**

```text
$ rg -n "map_beta_isin" --type py
core/transform.py:118:def map_beta_isin(raw: str) -> str:

$ rg -n "map_beta_isin" config/
config/sources.yaml:64:      mapper: map_beta_isin
```

Zero code references and completely alive. Delete it and `broker_beta_em` stops mapping its security identifiers, at runtime, in production, with a `getattr` failure nobody sees in a test.

### The four that are actually dead

**1. An unused dependency, from before the service was renamed.**

```text
$ rg -n "formrecognizer|FormRecognizer" --type py
(no matches)

$ rg -n "formrecognizer" .
requirements.txt:7:azure-ai-formrecognizer==3.3.0
```

Azure's Form Recognizer became Azure AI Document Intelligence, and the Python package became `azure-ai-documentintelligence`, which is the one actually imported in `core/clients.py`. The old line survived the Sprint 2 migration and has been installed into every container image since. Harmless, and it is the sort of thing that has somebody reading two SDKs' documentation in a year's time trying to work out which one the system uses.

**2 and 3. Two extraction helpers from the approach that was rejected in Sprint 1.**

```text
$ rg -n "_ocr_text_blocks" --type py
core/extract.py:214:def _ocr_text_blocks(pdf_bytes: bytes) -> list[TextBlock]:

$ rg -n "_regex_field_scan" --type py
core/extract.py:256:def _regex_field_scan(blocks, pattern_map) -> dict:
core/extract.py:271:        # matches = _regex_field_scan(blocks, PATTERNS)   <- commented out
```

Definition sites, and one commented-out call. `OCR_LINE_PATTERN` is used only by `_regex_field_scan`, which is itself dead, so the three go together as one connected component along with the `TextBlock` type nothing else uses.

**These are the remnants of Option C** — optical character recognition plus regular expressions — which [ADR-0001](artifacts/adr/) rejected in Sprint 1 because it produces no per-field confidence score, and without a per-field confidence score there is no confidence gate and no exception queue and no audit trail. That decision is load-bearing for the entire design.

Gautam writes one sentence into the deletion commit that is worth more than the deletion:

> These are the OCR+regex remnants ADR-0001 rejected. Deleted rather than kept "in case" — the ADR is the record of why we are not doing this, and dead code that contradicts an ADR will eventually be read as an option.

**4. A feature flag stuck permanently on.**

```text
$ rg -n "ENABLE_ROW_COUNT_CHECK" .
config/settings.py:44:    ENABLE_ROW_COUNT_CHECK: bool = True
core/rules.py:781:    if not settings.ENABLE_ROW_COUNT_CHECK:
tests/test_rules.py:203:    monkeypatch.setattr(settings, "ENABLE_ROW_COUNT_CHECK", False)
```

> **A feature flag** is a switch that turns a piece of behaviour on or off without a deploy. Useful when you are not sure something is safe. Dangerous when you forget it.

This one was added with the NWD-142 fix, as a kill switch in case the new completeness rules proved noisy and flooded Preeti's queue. They did not. It defaults to `True`, no environment overrides it, and the Function app's settings do not contain it.

**The dead part is the `False` branch**, and one test exists purely to exercise a code path that has never run in any environment.

Removing it is not tidying. It is a design statement: it makes the completeness check unconditional, which is a thing the specification should say, so the spec is updated in the same commit. Gautam flags that explicitly rather than deleting quietly, and Hem signs it off.

Four commits, least risky first, tests run after each. Twenty-eight lines of Python, one dependency and one flag gone. It takes ninety minutes and none of it is glamorous.

---

## 9. The debt register

Friday. Hem and Gautam run [P36](../../AI-Prompts-Library/phase-8-improve/P36-tech-debt-triage.md), which is a different exercise again and the one most often done badly.

> **Technical debt** is a shortcut you took, or a divergence between what the system does and what it was designed to do, that costs you something *every time you touch it*. The word is a metaphor about interest: you took something now and you are paying for it repeatedly.

The two traps are worth naming, because almost every debt register falls into one of them.

**Debt is not "code I would have written differently."** A 140-line function that is well tested and touched twice a year is style, not debt. If nobody is paying interest on it, it is not a loan.

**Ranking by size is wrong.** The number everyone has is the *principal* — how long it would take to fix. The numbers that matter are the **interest** (what it costs per touch, times how often you touch it) and the **default** (what happens if it fails, and how likely that is in the horizon you care about).

Four items. The horizon is the two quarters to end of March: parallel run through August, cutover in September, a third counterparty likely in the new year, and a possible second reporting book that would roughly multiply volume.

| # | Item | Kind | Cost type | Principal | Verdict |
|---|---|---|---|---|---|
| 1 | Blob trigger processes inline instead of enqueuing | DELIBERATE | Blocks scale + risks correctness | 2 days | **FIX NOW** |
| 2 | No page-level OCR quality pre-check | ACCIDENTAL | Risks correctness | 3 days | **FIX NOW** |
| 3 | The classifier knows only two layouts | ACCIDENTAL | Blocks a specific change | 4 days + labelling | **FIX WHEN TRIGGERED** |
| 4 | Reconciliation is single-threaded pandas | DELIBERATE | Blocks scale | 5 days | **FIX WHEN TRIGGERED** |

### 1 — the blob trigger does the work itself

The architecture has said since Sprint 1 that a PDF arriving in the landing zone enqueues a message, and a separate worker picks that message up and does the analysis. `function_app.py` does not do that. Its trigger calls classification, extraction, the rules engine and the sinks directly, inline.

Ravi shipped it that way in Sprint 2 to get two stories landing in the same week, and recorded it nowhere. **The date pressure that justified the trade is gone; the trade has expired.**

The interest is modest — a few hours a quarter, because every extraction change now has to be reasoned about against the Function's timeout budget. It ranks first anyway, and the reason is the default:

> A thirty-page quarterly statement arrives. The Function is killed mid-run with no exception. The blob trigger fires again, is killed again, five times, and the message lands in the poison queue. **The document is silently absent.** Nothing alerts on the absence of one document.

Probability in the horizon: high, because quarterly statements exist and Q4 statements land in January. And note the second-order effect, which is why Hem puts it first: a silently missing document produces a cluster of `MISSING_EXTERNAL` breaks — the exact symptom the team has just spent a sprint teaching itself to associate with a fixed bug.

**This is the case the ranking rule exists for: low interest, high and imminent default.** Rank by what annoys you and it sits fourth.

### 2 — nothing checks whether a page was legible

The system checks per-field confidence after extraction. It never checks whether a page was readable enough to extract from in the first place, and Document Intelligence returns page-level quality signals nobody reads.

**Why that gap is not obvious:** a badly scanned page can produce a *confident wrong value*. An OCR misread of `1,450` as `1,459` is high confidence and wrong, because the model is confident about the characters it believes it can see. Per-field confidence measures certainty about the reading, not the quality of the source.

Broker Alpha's currency threshold sits at 0.92 rather than 0.90 precisely because their scan quality is poor. **That override is a workaround for this gap, and nobody had named it as one until this session.**

This is Finding 2 wearing different clothes: a control that works well in its domain being assumed to cover a neighbouring one.

It ranks second because it is the only item on the register that directly contradicts the project's first design invariant — a wrong number is worse than no number — and because during the parallel run a divergence on an auto-accepted row is a hard failure that resets the ten-day clock.

### 3 — the classifier knows two layouts

The custom classifier was trained on `broker_alpha` and `broker_beta_em`. A third counterparty requires retraining the classifier itself, not just adding an extraction model, because a layout it has never seen scores below 0.75 and goes to review unclassified.

**Is this even debt?** Borderline, and the register says so. You cannot train a classifier on layouts you do not have. It is on the register because it partially contradicts invariant 8: adding a counterparty is a YAML change plus a trained model, never a code change. That holds for extraction. It does **not** hold for classification.

Verdict is FIX WHEN TRIGGERED, and the reasoning is the useful part:

> The valuable action now is not the fix — it is writing down that invariant 8 has an exception, so nobody at Northwind plans a two-day counterparty onboarding.

**A debt item whose entire payload is "correct someone's mental model before they plan around it" is a legitimate and underrated kind.**

### 4 — reconciliation is a single-threaded pandas job

`recon/reconcile.py` loads both sides into pandas DataFrames and does a full outer join in memory, single-threaded. Chosen deliberately in Sprint 2 because it is readable, testable, and 200 documents a day is nothing.

> **pandas** is a Python library for working with tables of data in memory. **A full outer join** puts two tables side by side and keeps every row from both, matched where they match — which is exactly what a reconciliation is.

It runs in about forty minutes today, comfortably inside the window. Memory and runtime both scale with total positions, not documents. At ten times the volume — a second reporting book, plus growth — it does not fit the window and nobody has measured its memory profile at all.

**The default is the business case.** The entire justification for this project is moving break detection from T+2 to T+1. A reconciliation that misses its window takes that away.

And the verdict shows the middle option people forget. Not "fix it" and not "ignore it" but **measure it**: add runtime and peak-memory logging so the next conversation has a curve instead of two opinions. Two hours, not five days.

### Considered and excluded

| Item | Why excluded |
|---|---|
| `core/rules.py::run()` is long | Long, well tested, touched rarely. Style, not debt |
| Dataclasses in one module, dicts in another | Preference. A competent engineer who did not write it would shrug |
| Test fixtures are large JSON files | Deliberate and correct — they are real captured responses, which is the point |

**The exclusions table earns its place** by recording that somebody considered these and decided. Without it, the same three items get raised at the next triage, discussed for ten minutes, and excluded again.

---

## 10. What each of them would tell a team starting tomorrow

Atul's last question in the retro. One or two lines each, no preparation, going round the room.

**Atul, project manager.**
> "Put rework on the plan as a line with a number on it. If you leave it off, it still happens — it just happens in the gaps, and then the sprint is late and nobody can tell you why."

**Preetinka Sharma, product owner.**
> "Ask 'rejected to where?' about everything the system refuses. Every refusal ends up on a person's desk, and if you haven't decided which person, you've decided it's Preeti."

**Hem Singh, architect.**
> "Ask what the design looks like when it's wrong, and then ask the harder version: what class of error does this control specifically not see? A good control is the one you'll stop checking."

**Gautam , team lead.**
> "You can generate code three times faster. You cannot review it three times faster, and review is the only safeguard newly written code has. Plan the review, not just the build."

**Ravi Mullick, backend engineer.**
> "Say 'I don't understand what this gave me' out loud, at standup, before you merge it. It cost me twenty minutes once. Not saying it costs somebody a night in six months."

**Dzmitry , frontend engineer.**
> "Go and watch the person do the job by hand for a morning. Everything worth knowing about the screen was in the fact that she does it forty times before lunch, and it wasn't in the brief."

**Pankaj , QA.**
> "For every list your system produces, there is a test that the list is complete, or a written note saying why you can't know. Pick one. Silence is not the third option."

---

## 11. The honest close

The system works. It ships on 4 September after a nineteen-day parallel run. Manual keying is gone, breaks surface on T+1 instead of T+2, and Preeti Singh spends her mornings on the documents that are actually hard.

None of that is what this book is about, and the retrospective is a list of things that should have been caught earlier written by the people who did not catch them.

Here is the part that is easiest to get wrong on the way out.

It is tempting to read NWD-142 as a story about an AI writing a bug. It is not. `documents[0]` is what a competent engineer writes when every example they have ever seen has one region in it, and no reviewer on earth flags it without knowing the service returns two. The AI did not introduce the assumption. It inherited it, from the spec, from the fixtures, from the team, and then it built on that assumption faster and more confidently than a human could have.

**That is the actual finding of this whole book, and it is not comforting.** The tooling did not make the team worse at engineering. It made them faster, and speed does not create wrong assumptions — it just gets you to the consequences of the ones you already had, sooner and in better-looking code. Every safeguard that caught something in these ten chapters was a written artifact with a name on it: an ADR that recorded why an option was rejected, a specification that could be found to be silent, a definition of done with a clause somebody owned, a bug report honest enough to label its own guess.

And the one thing that caught NWD-142 was not an artifact at all. It was Pankaj looking at a break report and thinking *that is not the shape settlement failures make*, and then opening the PDF and counting the rows with her finger.

Four years of domain judgement, applied on a Tuesday afternoon, to a system in which every automated check was green.

**Nothing the team builds in Sprint 5 will replicate that, and writing it down is the closest they can get.**

---

← [Previous](09-sprint-4-release.md) · [Case study index](README.md) · Next: [Book README](../../README.md)
