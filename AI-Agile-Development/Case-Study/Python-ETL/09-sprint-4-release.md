# Sprint 4 — Release, and the Argument About the Parallel Run

← [Previous](08-sprint-3-rework.md) · [Case study index](README.md) · Next: [Retrospective](10-retrospective.md)

> **One line:** three commits, a readiness pack, a runbook, and a fight about whether a system that passes all its own tests is allowed to replace a human control.

---

## 1. Monday, 3 August — what "done" costs

Sprint 4 is the release sprint. Everything is built, everything is fixed, everything is green. On paper this is the easy fortnight.

Farhan opens standup by reading out the state of things, which takes forty seconds:

- 203 tests passing. Five E2E scenarios green.
- NWD-138 through NWD-142 closed. Two security findings closed.
- 58% straight-through, honestly measured, target 85%.
- NWD-145 — retrain the Broker Alpha model for multi-page statements — open, with a date.
- Northwind wants to go live on the 17th.

And then the thing that turns the sprint into a real one, which is a message from the client relationship lead: *Northwind's operations director has asked whether we can skip the parallel run, since everything passes.*

Hold that. It comes back in section 5, and it is the most important argument in this chapter.

First, three prompts.

---

## 2. P31 — three commits out of one afternoon

Tomas's NWD-142 branch is a working tree with about four hundred lines of change in six files. It merged on Friday afternoon as one commit called `fix NWD-142`, which Rahul let through because it was Friday afternoon and it was blocking the release branch.

On Monday he asks Tomas to redo it before it goes into `release/1.0.0`.

> **Rahul:** "In four months somebody's going to `git blame` line 780 of `rules.py` and get a commit called `fix NWD-142` with a four-hundred-line diff. What are they going to learn?"

This is not tidiness. **A commit is the smallest unit of explanation your codebase can produce automatically, and it is the only documentation that is guaranteed to still be attached to the code.** Design documents drift. Tickets get archived when the tracker migrates. `git log` survives everything.

[P31](../../AI-Prompts-Library/phase-7-release/P31-write-clean-git-commits.md) is not "write me a commit message." It is: *here is a pile of changes, split it into commits that each make sense on their own.*

```text
You are preparing a change for review in the Northwind counterparty ingestion
pipeline. I have one working tree containing the whole of NWD-142's fix.

## The change

[OUTPUT OF `git diff --stat` AND THE FULL `git diff`]

## The context

Bug NWD-142: a positions table spanning a page boundary lost the rows on page 2
silently. Root cause was in extraction; the shipped fix is detection, not
recovery — see artifacts/spec-confidence-gate.md §7, added as part of this work.

## Split it

Propose a sequence of commits where:
* Each commit builds and each commit's tests pass at that commit. Not just the
  last one.
* The FIRST commit is the failing test, committed while it still fails, so the
  history contains proof the defect was real.
* Spec and configuration changes are separate from code changes.
* No commit mixes a behaviour change with a rename or a reformat.

For each commit give me: the files, the `git add` commands, and the message.

## Message format

Subject: <=72 chars, imperative mood, ticket ID in brackets at the end.
Body: what the reader needs that the diff cannot tell them — WHY, and what was
considered and rejected. Not a restatement of the diff.
Trailer: any ticket the commit closes or raises.

## Do not
* Do not squash the test into the fix.
* Do not write a message that describes the code. The diff does that.
* Do not invent a rationale. If you do not know why something was done, say so
  and I will tell you.
```

That last `Do not` earns its place. An AI asked to write a commit message will happily invent a plausible reason for a change, and a plausible-but-wrong rationale in `git log` is worse than none, because the next person believes it.

### What shipped

Four commits, not three — the model correctly split the configuration out from the code.

```text
commit 1/4
─────────────────────────────────────────────────────────────────────────────
    Add failing test for page-boundary line-item loss [NWD-142]

    A Broker Alpha statement whose positions table crosses a page boundary
    loads only the page-1 rows. 14 positions on the statement, 9 rows in
    silver, no exception, min_confidence 0.94.

    Fixture is the verbatim bronze payload from
    bronze/broker_alpha/2026-07-24/BA_POS_20260724.json, so the reproduction
    is offline and deterministic. This is the bronze layer (ADR-0001) paying
    for itself in a way we did not plan: the exact API response that produced
    the wrong answer is already on disk.

    This commit is expected to FAIL. It is committed red on purpose, so the
    history contains proof the defect existed before the fix claimed to
    remove it.

    Refs: NWD-142

  A  tests/fixtures/broker_alpha_2page_14_items.json
  A  tests/fixtures/broker_alpha_2page_full.json
  M  tests/test_extract.py
```

```text
commit 2/4
─────────────────────────────────────────────────────────────────────────────
    Record page provenance on extracted fields and documents [NWD-142]

    Every ExtractedField now carries the page it was read from, and every
    ExtractedDocument carries the pages the LAYOUT model reported a table on,
    plus the line-item count the document declares about itself.

    None of this changes behaviour. It exists because you cannot check that
    page 2 contributed rows unless you know which page each row came from,
    and we were discarding that.

    Splitting `analyze()` into a fetch half and a `build_document(payload,
    source)` half is part of this: the mapping was untestable without a
    network call.

    Refs: NWD-142

  M  core/extract.py
  M  tests/test_extract.py
```

```text
commit 3/4
─────────────────────────────────────────────────────────────────────────────
    Add completeness rules: declared count and page continuation [NWD-142]

    The confidence gate answers "can this value be trusted". It has no way to
    answer "is this value present". NWD-142 is the second question and every
    one of our six controls behaved correctly while a third of a statement
    went missing.

    Two rules, deliberately overlapping, because not every layout declares a
    count and not every model returns table regions:

      line_item_count   — declared count must equal extracted count
      page_continuation — every page carrying a table must contribute a row

    Both are errors, not warnings. A short document goes to the exception
    queue and no rows load.

    CONSIDERED AND REJECTED: merging the AnalyzedDocument regions so the
    continuation's rows are recovered automatically. It makes this test pass
    and it is the wrong fix — nothing in the response distinguishes "a table
    continuing" from "a second, unrelated document in the same file", so the
    merge would silently combine two accounts' positions under one account
    number. That trades visible data loss for invisible data invention, which
    is the wrong direction for this system. Recovering multi-page tables
    properly requires the extraction model to return one region, tracked as
    NWD-145.

    This lowers the straight-through rate from 61% to 58%. Three of those
    points were documents that loaded incomplete.

    Refs: NWD-142, NWD-145
    Spec: artifacts/spec-confidence-gate.md §7

  M  core/rules.py
  M  tests/test_rules.py
```

```text
commit 4/4
─────────────────────────────────────────────────────────────────────────────
    Configure completeness rules for both counterparties [NWD-142]

    Adding a control is a YAML block, not a branch. Broker Alpha declares
    PositionCount, Broker Beta declares TradeCount; both map to
    declared_line_item_count and both name it as line_item_count_field.

    Refs: NWD-142

  M  config/sources.yaml
```

Three things in that history are worth stealing.

**The first commit is red on purpose, and says so.** Anyone reading this history in a year can check out commit 1, run the test, and watch it fail. That is proof the defect was real, preserved forever, at a cost of one sentence.

**Commit 3 records what was rejected and why.** That paragraph is the single most valuable thing in the whole history. In six months somebody will look at `page_continuation`, think *why don't we just merge the regions and recover the rows*, and the answer will be sitting right there instead of being rediscovered in a two-day argument.

**Commit 3 also records that the metric got worse.** A commit message that admits it made a number go down is unusual and it is the honest thing. When someone runs a regression analysis on the straight-through rate next quarter and finds a step change on 31 July, `git log` explains it.

The sweep fixes from [chapter 8](08-sprint-3-rework.md) — Aladdin paging and the reconciliation readiness check — go on their own branch as **NWD-146**, with their own commits, because they are a different defect that happens to have been found by the same investigation. **One pull request per reason, not one per session.**

---

## 3. P33 — the runbook, written by the person who will not be on call

Tomas writes the runbook on Tuesday with [P33](../../AI-Prompts-Library/phase-7-release/P33-write-the-runbook.md), and the framing Rahul gives him is the reason it comes out useful:

> "Write it for someone who has never seen this code, at three in the morning, on a phone, when the person who wrote it has left the company."

A runbook is the document an on-call engineer reads when something breaks. Its whole value is that it lets a person who does not understand the system take a correct action anyway.

The part that matters most is the failure-mode table. Here it is as it ships, in `artifacts/runbook-doc-ingestion.md`:

| What you see | What it means | What to do | What NOT to do |
|---|---|---|---|
| Alert `poison_queue_depth > 0` | A document failed processing five times and gave up. The blob is still in `raw/`; nothing was written to silver. | Read the exception in App Insights, keyed by the queue message's blob path. Requeue with `scripts/requeue.py <blob-path>` once the cause is fixed. | Do not delete the poison message. It is the only record that the document exists and was not processed. |
| Alert `documents_processed == 0` for 90 min during a business day | Either nothing arrived, or the trigger is not firing. Those look identical from the metric. | Check `raw/` for today's date first. If files are there, the trigger is the problem — restart the Function app. If `raw/` is empty, it is an SFTP/email delivery problem, which is Northwind's side. | Do not restart the Function app before checking `raw/`. It cures nothing and it resets the metric you are diagnosing with. |
| Alert `exception_queue_depth > 40` | More documents than Priya can clear in a morning are waiting. Usually one counterparty changed a layout overnight. | Group `etl.extraction_exception` by `source_key` and `reason`. If one reason dominates, it is a layout change, not forty separate problems. Tell Amara before you tell Priya. | Do not raise thresholds to clear the queue. That is switching off the control to make its alarm stop. |
| Reason `page_continuation` on many documents from one counterparty | That counterparty has started sending multi-page tables the model was not trained on. The system is working correctly and refusing to guess. | Confirm against the PDF, then raise a model retraining ticket with ~50 labelled examples. Documents keep going to review until then. This is expected behaviour, not an incident. | Do not disable the rule. This is the exact control that exists because of NWD-142. |
| Reason `low_confidence: quantity` spiking on one counterparty | Scan quality dropped — a new scanner, a fax, a different template. | Compare against last week's documents for the same source. If the PDFs genuinely look worse, tell the counterparty. Threshold changes go through Sofia, never on call. | Do not lower the threshold. £-denominated quantities are gated at 0.90 for a reason and it is written down in spec §3. |
| `429 Too Many Requests` in logs, no failures | Backoff is working. Month-end. | Nothing. Watch it. If documents start hitting the poison queue, raise the Document Intelligence tier for the month. | Do not increase parallelism to "catch up". You will make it worse. |
| Reconciliation refuses to run: "external side incomplete" | Documents for that date are still in the exception queue. This is deliberate. | Clear the queue for that date, or run with `--allow-partial` **and** state on the report which sources are missing. | Do not run with `--allow-partial` silently. Every position in a missing statement becomes a false `MISSING_EXTERNAL` break, which is what NWD-142 taught us. |
| Redaction call fails | PII detection errored. The pipeline stores a marker instead of the text and refuses the document. | Nothing urgent. Check the Language service health. Documents will queue up until it recovers, then reprocess from bronze at no extra cost. | Do not add a fallback that persists unredacted text. Redaction fails closed on purpose. |

Look at the right-hand column. **Every row in "what NOT to do" is a plausible, well-intentioned action that makes things worse**, and four of the eight are some version of "switch off the control so the alarm stops."

That column is the part of a runbook people leave out, and it is the part that saves you at 3am, because at 3am the thing a tired person most wants is for the noise to stop.

The runbook also carries the thing that makes it survivable — an "if you are unsure" section with two lines in it:

> **If you are unsure, the safe action is always to let documents queue.** Nothing is lost. `raw/` is immutable, bronze is immutable, and reprocessing costs nothing because the API response is already stored. The system is designed so that doing nothing is safe and guessing is not.
>
> **Never make a threshold, rule or configuration change while on call.** Wake Sofia instead. She has agreed to this in writing.

---

## 4. P32 — the readiness pack

Wednesday. Farhan and Rahul run [P32](../../AI-Prompts-Library/phase-7-release/P32-release-readiness-check.md) together. The output is `artifacts/release-readiness-v1.0.md`, and the useful thing about it is that it is not a checklist of green ticks — the prompt forces every item to have evidence and an owner, and forces an explicit list of what is knowingly not ready.

```text
Produce a release readiness assessment for v1.0 of the Northwind counterparty
document ingestion pipeline.

For every item: state PASS, FAIL or ACCEPTED RISK. Every PASS must cite
evidence — a test name, a run ID, a document, a metric with a date. "It works"
is not evidence.

Assess:
1. Functional — every acceptance criterion on NWD-101..108, by ID.
2. Defects — every bug raised in Sprint 3, its state, and if closed, the test
   that proves it.
3. Data quality — the P25 check set, with results and dates.
4. Security — the P24 findings, their fixes, and anything accepted.
5. Operational — alerts, runbook, on-call rota, rollback procedure.
6. Cost — projected monthly spend against the estimate in the PRD.
7. What we know is not ready. Be specific. This section is mandatory and it
   may not be empty.

Do not mark anything PASS on the strength of a passing test suite alone where
the risk is about data correctness rather than code correctness. Say what
independent evidence exists.
```

The abridged result:

| Area | State | Evidence |
|---|---|---|
| NWD-101 landing zone | PASS | `test_raw_blob_is_immutable`, E2E scenario 1, 142 documents landed 16 Jul – 3 Aug with zero overwrites |
| NWD-102 classification | PASS | `test_classifier_below_threshold_goes_to_review`; 0 documents guessed below 0.75 in 19 days |
| NWD-103 confidence gate | PASS | 41 tests in `test_confidence.py`; 0 rows in silver below threshold across 2,240 rows |
| NWD-104 translation | PASS | NWD-138 closed; `no_translate_fields` covered by `test_translate_skips_identifier_fields` |
| NWD-105 redaction | PASS | Fails-closed path tested; SEC-02 closed 27 Jul |
| NWD-106 transform | PASS | Parity tests against the data contract |
| NWD-107 idempotent load | PASS | NWD-140 closed; resend E2E scenario green |
| NWD-108 exception queue | PASS | NWD-139 closed; Priya signed off on the demo 17 Jul |
| Completeness (spec §7) | PASS | NWD-142 closed; 6 regression tests; 4 previously-silent documents now correctly refused |
| Security | PASS | SEC-01, SEC-02 closed. Managed identity throughout, no keys in configuration |
| Cost | PASS | 12,600 pages/month projected → ~$378 extraction + ~$38 classification = **~$420/month**, against a PRD estimate of $500 |
| Rollback | PASS | Feature-flag off at the trigger; `raw/` and bronze retained; nothing to unwind |
| **Straight-through rate** | **ACCEPTED RISK** | **58% against a target of 85%. Multi-page statements are refused rather than recovered until NWD-145 lands. Priya's workload increases in the interim, agreed by Amara 30 Jul** |
| **Parallel run** | **FAIL — blocking** | **Not started. See §5** |

Two things about that table.

**Every PASS cites something you can go and look at.** Not "tested" — a test name, a count, a date, a person who signed off. That constraint is what makes the readiness pack a document rather than a mood.

**The ACCEPTED RISK row is written as plainly as the failures.** It says the number is bad, why it is bad, and who agreed. When Northwind's audit function reads this in November, the worst possible answer is one they have to reconstruct.

And then there is the last row.

---

## 5. Thursday — the argument

Northwind's operations director puts it reasonably, which is what makes it hard:

> "Everything passes. Your tests pass, your data quality checks pass, you've found and fixed five defects, and you've been running against real files for three weeks. Priya is spending four hours a day on something the system now does. Why are we asking her to do it for another month?"

**A parallel run means running the new automated process and the old manual process side by side, on the same documents, every day, and comparing the two outputs.** Priya keeps typing PDFs into her spreadsheet. The pipeline keeps loading them into Snowflake. Every morning someone compares.

It is expensive. It is dull. It is the thing everyone wants to skip and it is where the argument lands.

Amara says no. Sofia says no. They give completely different reasons and both reasons are correct.

### Sofia's reason: a control cannot validate itself

> "Everything that passes is something we wrote. The tests, the data quality checks, the confidence thresholds, the completeness rules — all of it is Kestrel asserting that Kestrel's code does what Kestrel thought it should. That's not validation. That's a closed loop.
>
> Six weeks ago every one of those checks was green while a third of a statement went missing. Not because the checks were badly written — because none of us had the concept the checks needed to cover. We fixed the one we found. I have no way of proving there isn't a second one, and neither does anybody in this room, because if there were, it would look exactly like this: quiet, green, and confident.
>
> The only thing that can tell us about a mistake we haven't imagined is a **different process, arriving at the same numbers independently.** Priya's spreadsheet is that process. It's been running for four years and everybody trusts it. Comparing against it is the only evidence we can produce that isn't circular."

That is her recurring question — *what does this look like when it's wrong?* — applied to the release itself. The answer for NWD-142 was: it looks like everything passing. So "everything passes" cannot be the gate.

There is a regulatory version of the same argument, and Sofia makes it second because it is the weaker one: this pipeline is a **control** in the accounting sense. It sits between a counterparty's statement and a number that reaches a valuation. Replacing a manual control with an automated one is a change an auditor will ask about, and the evidence they will ask for is a period of parallel operation with documented comparison. Not a test report.

### Amara's reason: she has been the analyst

Amara's reason takes twenty seconds and lands harder, because she does not argue about controls at all.

> "I spent six years on an operations floor. Twice in that time a number went into a report wrong and came out the other end as a client query, and both times the conversation started with someone asking me why *I'd* got it wrong. Not the system. Me. I was the last human who touched it.
>
> If we cut this over on the 17th and something we haven't thought of goes wrong in week three, the person sitting in that conversation is Priya. She'll be defending numbers she didn't produce, from a system she was told to trust, and she'll have no way to show it wasn't her.
>
> A parallel run is four weeks of her being able to say *I checked, and they matched.* That's not process. That's the only thing that protects her."

Nobody argues after that.

**Notice that neither of them argued about the software.** Sofia argued about epistemology — what can count as evidence — and Amara argued about who carries the blame. The engineers in the room, who knew the code best, had the least useful things to say, and that is normal and worth noticing.

### What they actually agree

Farhan writes it up as the cutover gate, and the specificity is the point — "run in parallel for a while and see how it goes" is a plan that never ends.

> **Cutover gate — v1.0 counterparty ingestion**
>
> **Duration.** Minimum two weeks. Maximum four. Must include one month-end.
>
> **What runs.** Both processes, on every counterparty document, every business day. Priya keys documents as she does today. The pipeline processes the same documents independently. Neither sees the other's output.
>
> **The comparison.** A daily automated diff of Priya's spreadsheet against `silver.counterparty_position`, on account number, security identifier, quantity and market value. Produced by 09:30, reviewed by Priya and one of Tomas or Ananya, signed by both.
>
> **The gate.** Cutover is approved when **all** of these hold:
>
> 1. **Zero divergence on auto-accepted rows for ten consecutive business days.** Not "low divergence". Zero. A row the pipeline accepted without human touch must match Priya's keying exactly, within the reconciliation tolerances (0.0001 quantity, 0.005 market value).
> 2. **Every document Priya keyed is accounted for** — either loaded, or in the exception queue with a reason. No document is unexplained.
> 3. **At least one month-end** in the window, because volume spikes and month-end is when both people and systems make different mistakes.
> 4. **Every divergence investigated to a root cause** and written down, including the ones where Priya was wrong. Especially those.
>
> **What resets the clock.** Any divergence on an auto-accepted row resets the ten-day count to zero. Any code change to the extraction, rules or transform layers resets it to zero.
>
> **What does not reset it.** Divergences on rows the pipeline sent to the exception queue. That is the system working.
>
> **Who signs.** Amara for the business, Sofia for the architecture, Northwind's operations director for the client.

Clause 1 is the one people push back on, and Sofia holds the line on it for a specific reason worth spelling out:

**An auto-accepted row is a row no human looked at.** A one-percent tolerance on those is not a tolerance, it is a decision to let one document in a hundred be wrong forever, with nobody watching. Rows that went to the exception queue can diverge freely — that is a human and a machine disagreeing, which is what the queue is for. Rows nobody looked at have to be exactly right or the whole design is a bluff.

Clause 4's last sentence — *especially the ones where Priya was wrong* — is Amara's. She knows the parallel run will find transcription errors in the manual process, because the manual process is a person reading a scanned fax at 8:40 in the morning. Those divergences are the ones that prove the system is worth building, and they are also the ones nobody would write down unless you told them to in advance.

---

## 6. What actually happened in the parallel run

For completeness, since the book would be dishonest without it.

The parallel run started Monday 10 August and ran nineteen business days, through month-end.

**Eleven divergences in total.**

- **Six** were Priya. Transposed digits, mostly, on scanned Broker Alpha statements. One was a whole line skipped on a two-page statement, which is the manual-process version of NWD-142 and got a wry note in the retro.
- **Three** were rows the pipeline had sent to the exception queue, where Priya's correction differed from what the model extracted. Not gate failures. The gate working.
- **One** was a genuine defect: a Broker Beta EM confirmation with a negative quantity — a short position — where the transform dropped the minus sign because the model returned it as a separate `selectionMark` field. Filed as **NWD-149**. Two days to fix. **The ten-day count reset to zero on 21 August, and nobody argued about it.**
- **One** was a currency-rounding difference in Priya's spreadsheet formula that had been there since 2023 and had never been noticed.

That eleventh one is the argument in a sentence. **The parallel run found a four-year-old error in the process it was validating against.** You do not get that from a test suite, because a test suite compares your system to your own expectations, and the whole problem is that your expectations are the thing under test.

Cutover was signed on 4 September. Three weeks later than the client wanted, and NWD-149 alone justified every day of it.

---

## 7. What Sprint 4 hands over

| Artifact | Where | Who reads it next |
|---|---|---|
| Four commits per fix, red test first | `git log` on `release/1.0.0` | Whoever runs `git blame` in four months |
| Release readiness pack | `artifacts/release-readiness-v1.0.md` | Northwind's audit function, in November |
| Runbook with the failure-mode table | `artifacts/runbook-doc-ingestion.md` | Whoever is on call |
| Cutover gate | Signed by three people | Everyone, weekly, for a month |
| NWD-145, NWD-146, NWD-149 | Backlog with dates | Sprint 5 |

And one thing that is not an artifact: Farhan has now watched a sprint estimated at one day of bug fixing consume six days of rework, and he has a retrospective to run about it.

He moves it to Thursday of the following week, on purpose. His reasoning, which is good enough to steal:

> "If we retro on the Friday everyone talks about how they felt. If we retro after the release pack is written, everyone talks about what happened, because it's all written down and none of us can misremember it."

---

← [Previous](08-sprint-3-rework.md) · [Case study index](README.md) · Next: [Retrospective](10-retrospective.md)
