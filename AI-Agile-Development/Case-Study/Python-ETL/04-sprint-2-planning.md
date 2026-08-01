# Sprint 2 — Planning the Build

← [Previous](03-sprint-1-design.md) · [Case study index](README.md) · Next: [Sprint 2 — Backend](05-sprint-2-build-backend.md)

> **One line:** a build sequence written ninety minutes after the spec it depends on, a dependency caught three weeks before it could hurt anyone, and a Definition of Done that grows three clauses which would have made no sense two years ago.

---

## 1. Monday, 6 July, 08:15

Atulis in the office ninety minutes before anyone else, which is not unusual, and he is doing arithmetic, which is.

On his screen is a document that does not exist yet: `artifacts/sprint-2-plan.md`. Beside it, in a text file, are the answers people gave him in Slack on Friday afternoon to a question he asks every fortnight and never gets a straight answer to the first time — *how many days are you actually available?*

Ravi Mullick: ten, minus a day's leave on Thursday, minus finishing the bronze persistence review with Hem. Dzmitry : ten, minus a day at Northwind with Preeti Singh.

**Sprint 2 is the first sprint where anybody writes code that ships.** Sprint 0 built the scaffolding, Sprint 1 designed the thing, and both of them produced documents. This one produces a pipeline. That means it is also the first sprint where being wrong about the plan costs money rather than embarrassment.

Three things happen today, in this order, and the order is deliberate:

1. **Gautam ** turns Hem's spec into a numbered build sequence for NWD-103 — [P15](../../AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md). He actually did this on Friday at half past four, for reasons [Chapter 3](03-sprint-1-design.md) explains, and this morning he does the thing he should have done then.
2. **Atul** plans the sprint around it — [P16](../../AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md).
3. **Gautam and Pankaj ** write down what "done" means, once, for every story — [P17](../../AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md).

Nobody writes a line of Python until tomorrow. That is not a delay. It is the day that makes the next nine survivable.

---

## 2. The plan written ninety minutes after the spec

### What an implementation plan actually is

> **An implementation plan** is an ordered list of steps that turns one story into working code, where after every single step the application still runs.

That last clause is the whole idea and it is worth being slow about.

The obvious way to build the confidence gate is: write the gate, write the config loader, write the exception table, wire it all up, run it, fix what breaks. Four days of work with one moment of truth at the end. Engineers have built software that way forever and it mostly works, because the person doing it holds the whole thing in their head while they build it.

**That approach stops working when a machine writes the code, and it stops working for a specific reason.** Four hundred lines arrive in about nine minutes. They import cleanly. They are internally consistent. And nobody — not the person who prompted for them, not the reviewer — has any way to tell which parts they understand and which parts they merely recognise.

Gautam's framing at standup, which is the sentence Ravi remembers all sprint:

> "Forty lines with a command that proves it works is readable. Four hundred lines with nothing you can run is a thing you agree with."

So the plan's job is not to describe the design. Hem's spec does that. The plan's job is to **cut the design into pieces small enough that a human can honestly say they read one.**

### The green command

Every step in the plan is checked against one literal command:

```bash
pytest -q && python -c "import doc_ingestion.function_app"
```

> **The green command** is the command that proves the application still compiles and still starts. Not "the feature works" — just "the thing is not broken."

Two halves, and the second one is the one people leave out. `pytest -q` runs the test suite quietly. `python -c "import doc_ingestion.function_app"` imports the Azure Functions entry point, which catches the whole family of mistakes where the tests pass beautifully and the application will not start — a circular import, a module-level line that needs an environment variable, a typo in a name that only the entry point references.

> **Azure Functions** is the service that runs your Python without you managing a server. You write a function, tag it with a trigger — "run this when a blob lands" — and Azure runs it. `function_app.py` is the file it looks at.

**If the "Verify" line on a step is weaker than the green command, the step is not verified.** That single check is how Gautam reads a plan in thirty seconds.

### Riskiest first, not bottom-up

The natural order to build anything is bottom-up: types, then logic, then wiring, then persistence. It is tidy and it is wrong here.

Gautam tells the prompt to **order by risk**, where risk means *the thing that, if the answer surprises us, throws away work already done*. And he names what he thinks the riskiest thing is, so the model has something to disagree with:

```text
**Identify the risky unknowns first.**
I believe the riskiest is:
Whether Azure AI Document Intelligence returns a per-cell confidence score for
line items inside a table, or only for top-level document fields. The entire
story assumes per-cell confidence on the positions table.
Tell me if you think something else is riskier.
```

This is not a small question. A **line item** is one row of the positions table on a statement — one security, one quantity, one market value. If the extraction service scores the whole table with a single number rather than scoring each cell, then the gate cannot be per-field below the header, the spec's section 3 is wrong, the exception queue cannot point Preeti at row 34, and the design changes shape. It would be a bad thing to discover on day four.

### The risk register that comes back

| # | Unknown | Why it could change the design | Time to answer |
|---|---|---|---|
| R1 | Does Document Intelligence return a confidence per cell for line items inside a table, or only for top-level fields? | If line-item cells have no confidence, the gate cannot be per-field below the header and spec §3 is wrong. Everything downstream changes. | ~40 min with one real `broker_alpha` PDF from `bronze/` |
| R2 | Do all Broker Alpha statements use the same field names across model versions v2 and v3? | If not, the `field_map` needs versioning and `config/sources.yaml` grows a dimension. | ~20 min, compare two bronze responses |
| R3 | Is there an existing exceptions table anywhere, or does this story create it? | `sql/schema.sql` has only `positions_staging`. If NWD-108 assumes a table shape, we must agree it before Step 5. | Ask Dzmitry — 5 min |

And the line under it, which is the model doing the useful half of its job:

> I agree R1 is the riskiest. R3 is not technically risky but it is a cross-person dependency and it blocks Dzmitry, so it is answered before Step 5.

**R3 is the sentence that makes Atul's morning easier three hours later.** A plan for one engineer's story noticed that a different engineer is blocked by it, because it was told to read all the artifacts rather than just the one it was planning.

---

## 3. The real build sequence

Eight steps. Here are the first four in full, because the format is the point, and the rest compressed.

### Step 0 — Prove line items carry per-cell confidence (SPIKE)

- **Why now:** If this is false, Steps 1–7 are the wrong shape. Nothing else should be written until it is answered.
- **Files:** `scratch/spike_lineitem_confidence.py` — created (throwaway)
- **Change:** Load one already-persisted `broker_alpha` response from `bronze/`, walk the positions table, and print the confidence attached to each cell of the first three rows. No new Azure call — bronze already has the JSON, which is exactly why bronze exists.
- **Verify:** `python scratch/spike_lineitem_confidence.py` → prints three rows, each with a float confidence per cell, none of them `None`
- **Not working yet:** Everything. No production code exists.
- **Undo:** Delete `scratch/`. Nothing else imports it.
- **Size:** ~25 lines, deleted at Step 1

> **A spike** is deliberately throwaway code written to answer a question. It is not a prototype and it is not the first draft of the real thing. The plan says what deletes it, in writing, on the day it is created, because a spike nobody deleted is how a codebase gets a second implementation of something.

Step 0 costs forty minutes and it makes no Azure call at all. That is [ADR-0002](artifacts/adr/) — persist the full API response to bronze before parsing — paying rent on the first morning of the build. Hem argued for bronze on cost grounds. Here it is buying speed instead, and it will buy debugging in [Chapter 8](08-sprint-3-rework.md).

### Step 1 — Pure confidence module with the default thresholds

- **Why now:** R1 is retired. This is the smallest piece of real behaviour and it has no dependencies at all.
- **Files:** `core/confidence.py` — created · `tests/test_confidence.py` — created
- **Change:** Add the default threshold table, an `ExtractedField` value type and a `GateResult` value type carrying `passed`, `failures` and `straight_through`. Add the document evaluation handling top-level fields only. No Azure imports, no I/O, no config reading — this module takes everything it needs as arguments. That is deliberate; see "Where a human must look".
- **Verify:** `pytest -q tests/test_confidence.py` → 4 passed
- **Not working yet:** Nothing calls the gate. Line items are ignored. Counterparty overrides are ignored.
- **Undo:** Delete both files. No other module imports them.
- **Size:** ~90 lines plus ~60 lines of tests

### Step 2 — Per-counterparty threshold overrides from YAML

- **Why now:** Broker Alpha's 0.92 currency override is in the acceptance criteria and it is the reason thresholds are data rather than constants.
- **Files:** `core/confidence.py` — edited · `config/sources.yaml` — edited · `tests/test_confidence.py` — edited
- **Change:** Add a `confidence:` block under `broker_alpha` in `sources.yaml` setting `currency: 0.92`. Resolve the threshold for a field from the counterparty's config, falling back to the type default. The module still does not read the file itself — the caller passes the resolved config in.
- **Verify:** `pytest -q tests/test_confidence.py` → 7 passed, including one asserting 0.91 currency fails for `broker_alpha` and passes for `broker_beta_em`
- **Not working yet:** Still nothing calls the gate.
- **Undo:** Revert the three files; the YAML block is additive and ignored if left.
- **Size:** ~30 lines plus ~25 lines of tests

### Step 3 — Gate line items, one bad row fails the document

- **Why now:** This is invariant 2 from the spec and the single behaviour most likely to be got subtly wrong.
- **Files:** `core/confidence.py` — edited · `tests/test_confidence.py` — edited
- **Change:** Accept an ordered sequence of line items alongside the header fields. Evaluate every cell of every row. Record the row index on each failure so the exception queue can point Preeti at row 34 rather than "somewhere in the table". Any single failure sets `passed = False` for the whole document.
- **Verify:** `pytest -q tests/test_confidence.py` → 11 passed, including one with 40 good rows and 1 bad row asserting the document fails
- **Not working yet:** Still nothing calls the gate. Nothing is persisted.
- **Undo:** Revert both files.
- **Size:** ~40 lines plus ~40 lines of tests

### And the rest

| Step | Goal | Files | Not working yet |
|---|---|---|---|
| **4** | Call the gate from the rules engine | `core/rules.py`, `tests/test_rules.py` | A rejected document stops silently. Nothing reaches Preeti |
| **5** | The exceptions table | `sql/schema.sql` | The table is empty. Nothing writes to it |
| **6** | Persist rejections to the exception queue | `sinks/sql_sink.py`, `core/rules.py`, `tests/test_rules.py` | No metric is emitted. The straight-through rate is not measurable |
| **7** | Emit the straight-through metric | `core/logging_config.py`, `core/rules.py` | Nothing. The story is complete |

> **The straight-through rate** is the percentage of documents that need zero human touch. It is the headline number for the whole project: it starts at 61% and the target is 85%. Step 7 is one call to Application Insights, and it is in the plan as a numbered step precisely because "we'll add the metric later" means there is no metric in November.

### Where a human must look

The plan ends with three named steps rather than a general instruction to review carefully:

> - **Step 1** — the shape of `GateResult` is the contract three other pieces of work depend on: the exception queue UI, the Snowflake `MIN_CONFIDENCE` column, and the metric. Getting the field names wrong here is cheap now and expensive in two weeks. Read this one properly.
> - **Step 3** — the line-item loop is where an off-by-one on the row index will send Preeti to the wrong row, and she will not be able to tell that it is wrong.
> - **Step 4** — the only step that changes the behaviour of the running pipeline. Everything before it is additive.

**Step 3's reason is the best sentence in the document.** Not "this is complex" but *she will not be able to tell that it is wrong*. A bug an analyst can catch is an annoyance. A bug that quietly sends her to the wrong row on a screen she trusts is something else, and naming which is which is what turns "review carefully" into an instruction somebody can follow.

The plan is saved to [`artifacts/implementation-plan-NWD-103.md`](artifacts/implementation-plan-NWD-103.md), in the repository, where Atul can read it before the planning session. That matters in about forty minutes.

---

## 4. Atul's sprint plan

### The goal, and the two candidates

Atul asks for two candidate sprint goals and a recommendation, which is a small trick that gets a much better first one.

> **Recommended:**
> A Broker Alpha position statement lands in the raw zone, is classified, is gated on confidence, and reaches Azure SQL — and anything the gate rejects is visible to Preeti in a browser.
>
> **Alternative considered:**
> The full ingestion pipeline works end to end for both counterparties, in both languages, loading to Snowflake.

The reasoning underneath is the part worth stealing:

> The alternative is worse for one reason: nothing can be dropped from it. It requires NWD-104 (translation) and NWD-107 (Snowflake load) to be complete, which means on day eight there is no principled way to descope.

> **A sprint goal is a sentence describing what the sprint achieves, in terms someone non-technical would recognise.** Not "finish NWD-101 to NWD-108."

Here is why that distinction earns its place, and it has nothing to do with motivation.

On day eight of a two-week sprint you discover you cannot finish everything. With a ticket list, you now have a negotiation: the project manager wants the story with the client's name on it, the engineer wants the one that is nearly done, the architect wants the foundational one. There is no principle to appeal to, so it takes an hour you do not have.

With a goal, you ask one question of each remaining story: *does the goal survive without this?* NWD-104 translates EM documents to Spanish and Portuguese. The goal says Broker Alpha, which is English. The goal survives. NWD-104 slips. Forty seconds, nobody's feelings involved.

**The sprint goal is the thing that tells you what to drop.** A ticket list can only tell you what you did not do.

The recommended goal also names Preeti, and Atul says so out loud in the room: it is the only version Preetinka Sharma can judge without an engineer translating it for her.

### Capacity, with the arithmetic shown

| Person | Working days | Leave | Ceremonies | Carry-over | Available |
|---|---|---|---|---|---|
| Ravi Mullick | 10.0 | −1.0 | −0.5 | −0.5 | **8.0** |
| Dzmitry  | 10.0 | 0 | −0.5 | −1.0 | **8.5** |
| | | | | | **16.5 days** |

Two things people consistently get wrong, both visible in that table.

**Ceremonies are not free.** Planning is ninety minutes. Standup is fifteen minutes a day, which is closer to two and a half hours a sprint once you count the context switch on either side. Demo and retro are another two hours. That is the better part of a day per person, every sprint. Pretending otherwise is how sprints finish 10% short and nobody can point at why.

**Capacity is not a target to fill.** Atul commits to 75% of 16.5, which is **12.4 days of planned work**, and he writes down what the remaining 4.1 days are reserved for rather than leaving it as a vague cushion: Azure service surprises, the labelled-document set needing correction, and rework arising from Gautam's reviews.

Gautam, Pankaj, Hem and Preetinka are not counted as build capacity at all. Gautam is reserving half a day a day for review, pairing and unblocking. Atul's note in the plan:

> Counting a reviewer's time as build capacity is how review becomes the thing that gets skipped.

### Velocity honesty

> **Velocity** is how many story points a team completed in recent sprints. You use it to forecast the next one.

Atul has none, and the plan says so in a sentence he could easily have softened and did not:

> **There is no velocity for this team on this project.** Sprints 0 and 1 produced foundations and design documents, not application code. Any points-per-sprint number quoted now would be invented.
>
> Consequence: this plan is a forecast, not a commitment.

What he uses instead is Gautam's implementation plan: eight steps, roughly 350 lines of production code plus tests, which reads bottom-up as about two and a half days for NWD-103 including review and rework.

**Hold on to that two and a half days.** It is the most interesting number in this chapter and nobody notices it until the next one.

### The stories

| ID | Title | Pts | Owner | Goal survives without it? |
|---|---|---|---|---|
| NWD-101 | Land counterparty PDFs immutably in the raw zone | 3 | Ravi | **No** — nothing works without the landing zone |
| NWD-102 | Classify an incoming PDF to its counterparty layout | 5 | Ravi | **No** — the gate needs to know which thresholds apply |
| NWD-103 | Gate every extracted field on its confidence score | 5 | Ravi | **No** — this is the sprint |
| NWD-104 | Translate EM documents to English before matching | 3 | Ravi | **Yes** — the goal says Broker Alpha, which is English |
| NWD-105 | Redact PII before anything is persisted | 5 | Ravi | **Yes** for the goal, **no** for go-live |
| NWD-106 | Transform extracted fields into the canonical position schema | 5 | Ravi | **No** — nothing reaches SQL without it |
| NWD-107 | Load positions into Azure SQL and Snowflake idempotently | 8 | Ravi | **Partly** — Azure SQL half required, Snowflake half not |
| NWD-108 | Exception queue screen for analyst review | 8 | Dzmitry | **No** — "visible to Preeti" is half the goal |

Ravi carries 34 points. Dzmitry carries 8. Atul writes the uncomfortable line rather than shuffling the numbers to hide it:

> That imbalance is real and it is not solved by moving points around — Dzmitry cannot write the Python and Ravi is not building React this sprint.

---

## 5. The dependency, found three weeks early

This is the section the sprint turns on, and it is section 5 of the plan because Atul told the prompt to treat dependencies as the most important part of the document.

> **A dependency** is when one piece of work cannot finish until something in another piece of work exists.

Here is this one, in plain terms. **NWD-108 is Dzmitry's exception queue: the screen where Preeti fixes a document the pipeline refused.** It shows a list of refused documents and, for each one, which field failed and why. **NWD-103 is the confidence gate: the thing that does the refusing.**

Until NWD-103 exists and has decided what a refusal looks like — the column names, the types, whether `line_item_index` can be null — Dzmitry has a screen with nothing to put on it. Not "not much". Nothing.

Atul's plan states it as a fact with a date on it:

> **D1 — NWD-108 needs NWD-103 (critical)**
>
> - **What is needed:** exception rows to display. Specifically the shape of an exception record — field names and types — and an endpoint that returns a list of them.
> - **From:** Ravi · **To:** Dzmitry · **Needed by:** end of day 5
> - **Why it is critical:** NWD-108 is Dzmitry's entire sprint. Blocked, she has nothing else assigned.

### The four options, and why three of them are bad

| Option | Assessment |
|---|---|
| (a) Wait | Dzmitry does nothing until NWD-103 lands. Costs four to five days of a frontend engineer. Obviously bad, extremely common. Rejected. |
| (b) Reorder | Do NWD-103 first, then start NWD-108. Does not help — the backend takes the same number of days either way, so she waits at the front instead of the back. Rejected. |
| (c) **Agreed fixture** | **Recommended.** |
| (d) Descope NWD-108 | Fails half the sprint goal. Rejected. |

Option (c) is the one that works, and it works for a reason worth stating precisely.

> **A fixture** is a fixed, fake piece of data you develop against so you do not need the real system running. Dzmitry's is a JSON file with six invented exception rows in it.

**The expensive part of a dependency is not the code. It is the agreement.** Once Ravi and Dzmitry have agreed exactly what an exception row looks like, the two sides are genuinely independent — she builds against a file, he builds against a database, and on day six they swap the file for the real endpoint and nothing needs rewriting. Until they have agreed, no amount of scheduling helps, because whatever she builds is a guess that gets rewritten in the last three days of the sprint.

The plan does not say "coordinate with Dzmitry." It specifies the meeting and the artifact:

> Day 1, before either of them writes anything: Ravi and Dzmitry agree the exception record shape against `data-contract-counterparty-position.md` §4 and `implementation-plan-NWD-103.md` Step 5. Forty minutes, both present, Gautam in the room. Output is a committed `exceptions.sample.json` fixture containing six rows and covering, at minimum:
>
> - a document with three separate field failures sharing one document hash
> - a failure on a line item (non-null row index) and a failure on a header field (null row index)
> - one `BELOW_THRESHOLD`, one `MISSING_VALUE`, one `NULL_CONFIDENCE` reason code
> - one row where confidence is null, so the UI has to decide what to render
>
> **If the shape changes after day 1**, it is a change both of them attend, and it is raised at standup, not fixed silently.

**Those four bullets are the whole value of the section.** A fixture that only contains tidy rows produces a screen that only handles tidy rows, and the awkward cases arrive in production. A null `line_item_index` is exactly the sort of thing that gets designed out of a fixture on Monday and turns up in front of Preeti in October.

The other three dependencies are shorter and one of them is not about software at all:

- **D2 — NWD-103 needs NWD-102.** The gate resolves per-counterparty thresholds, so it needs to know the counterparty. Both stories are Ravi's, in sequence. A sequencing note, not a coordination risk.
- **D3 — Pankaj needs a working exception queue by day 8.** Not a story dependency, a people one. She cannot start the end-to-end test harness against a screen that does not render. Flag at standup on day 6 if it looks tight.
- **D4 — the Snowflake half of NWD-107 needs key-pair authentication provisioned by Northwind IT.** Outside the team's control. Requested, not confirmed. **Chase on day 3, not day 7.**

### The day-level shape

```text
Day  1   2   3   4   5   6   7   8   9  10
Ravi
     [--101--][----102----][------103------][--106--][----107----]
                                        ^Step 5/6 land (D1)
     Thu wk1 = leave (day 4)
Dzmitry
     [D1 agree][------108 against fixture------][real API][--polish/a11y--]
                                        ^swap day 6
Reserve (4.1 days, unallocated): 104, 105, Snowflake half of 107
```

This sketch is wrong by Wednesday, and Atul says so when he puts it up. It is drawn from point estimates that are guesses on a team with no velocity. **The only load-bearing thing in it is the arrow, because the arrow is D1's deadline.**

---

## 6. "What happens if that takes twice as long?"

Atul asks this in every planning session anybody has ever attended with him, and most of the time it is a mild irritant. People have learned to answer it quickly so the meeting can continue.

Today it lands, and it lands on the arrow.

> **Atul:** "Step 5 is the exceptions table. Your plan says day five. What happens if that takes twice as long?"
>
> **Ravi:** "It won't. It's a `CREATE TABLE`. Twenty-five lines of DDL."
>
> **Atul:** "I believe you. What happens if it does?"
>
> **Ravi:** *(pause)* "Then Dzmitry swaps the fixture on day eight instead of day six."
>
> **Dzmitry:** "No, then I swap it on day eight and find out on day eight whether I guessed the shape right. If I guessed wrong I've got two days to rewrite a screen and Pankaj's got nothing to test."
>
> **Gautam:** "So the risk isn't Step 5 being late."
>
> **Dzmitry:** "The risk is the *shape* being late. The table can be Thursday. The column names have to be Monday."

That exchange takes about ninety seconds and it changes the plan in one specific way. The dependency stops being "NWD-103 by day 5" and becomes two things with different deadlines:

| What Dzmitry needs | When | Why that date |
|---|---|---|
| The **shape** of an exception record — names, types, nullability | End of **day 1** | Everything she builds is bound to it. Late here means a rewrite, not a wait |
| A **working endpoint** returning real rows | End of **day 5** | Late here means she keeps using the fixture for another day or two. Annoying, not expensive |

**Splitting one deadline into two is the entire output of the question, and it is worth more than the rest of the session.** The forty-minute conversation moves to nine o'clock on the Monday morning, before either of them opens an editor, and it happens before Ravi has any code that might make him defensive about the shape.

Atul's question is not a challenge to the estimate. It never is. It is a request for the **failure shape** — *what specifically goes wrong, and to whom* — and the useful answer almost never comes from the person being asked. It came from Dzmitry, who was not being asked at all.

> **Ask "what happens if that takes twice as long" of the person who is waiting, not the person who is building.** The builder answers about their own schedule. The waiter answers about the consequence.

For the record, Step 5 took forty minutes.

---

## 7. The Definition of Done

Monday afternoon. Gautam and Pankaj at one desk with [P17](../../AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md), an hour before they take it to the team at four o'clock.

### The two lists people confuse

This trips up almost every team once, so it is worth being blunt about it.

> **Acceptance criteria** are per-story. They say whether you built **the right thing**. "A currency field at 0.89 is rejected for `broker_alpha`" is an acceptance criterion for NWD-103 and it means nothing on any other story.
>
> **The Definition of Done** is one list that applies to **every** story, forever. It says whether you built it in a way you can **safely live with**. "One other person approved the change" applies to NWD-101 and NWD-108 and every story anyone writes next year.

You need both. The second one is the one that quietly disappears under deadline pressure, which is exactly why it is written down, owned by name, and costed.

### The three clauses that only exist because a machine writes the code

Most Definition of Done templates you can find online were written before four hundred correct-looking lines could arrive in ten seconds. They cover tests, review and deployment, and they are fine as far as they go. Gautam and Pankaj add three that those templates do not have.

Here they are as they ship, from [`artifacts/definition-of-done.md`](artifacts/definition-of-done.md):

```markdown
## AI-assisted work

**D7 — A human has read every line the AI wrote, and can explain what it does.**
"Read" means: you can say what each function does without re-reading it, you can
name one input that would break it, and you noticed at least one thing you would
have done differently. Reading a file and having no reaction to it means you
skimmed it.
- Check: the author states in the pull request description "I have read every
  line" and answers one question from the reviewer about a specific line the
  reviewer picks.
- Owner: author, confirmed by reviewer
- Cost: 20 min

**D8 — No test was modified in order to make it pass.**
If a test file changed in the same pull request as the code that made it green,
the description must contain one sentence saying why the *old* assertion was
wrong. "It was failing" is not that sentence. Skipping, deleting or loosening a
test counts as modifying it.
- Check: reviewer looks at the test diff first, before the code diff. If any
  assertion weakened, the sentence must be there.
- Owner: reviewer
- Cost: 5 min

**D9 — If behaviour diverged from the spec, the spec was updated in the same
pull request.**
Covers the small case: the spec was silent and the code had to decide. For the
large case — the spec was actively wrong — raise it with the architect and follow
the spec-change route instead of editing quietly.
- Check: reviewer asks "does the spec describe what this does?" and the answer is
  yes, or the same pull request contains the spec edit.
- Owner: Hem Singh for the rules engine and data contract; Gautam otherwise
- Cost: 10 min
```

Each of them is worth a paragraph.

**D7 gets pushback, in the room, from Ravi, and the objection is reasonable:** *we do not read every line of the libraries we import, so why this?*

The answer is that a library has a public interface, a version number, a maintainer, a test suite and a hundred thousand other users who would have found the bug. Freshly generated code in your repository has exactly one safeguard and it is you.

The clever part is not the clause, it is **the check**. Not "the author confirms they read it" — a box anybody will tick on a Friday. It is *the reviewer picks a line and asks about it*. Ten seconds of Gautam's time, and it converts a promise into a test.

Be honest about what it costs: twenty minutes a story, and there is no way around it. What you are buying is the absence of **comprehension debt** — code in production nobody on the team can explain — and that debt gets called in during an incident, at night, by the person who understands it least.

**D8 is the sharpest one and it needs the situation spelled out.** Ravi has a failing test. He asks the AI to fix it. There are two ways to make the suite green: change the code so the behaviour is right, or change the test so it agrees with the current behaviour. Both look like a fix in the diff. The second is far easier, so by default it is what happens a distressing proportion of the time.

And the change is nearly invisible in review. An assertion moves from `assert result.passed is False` to `assert result.passed is not None`. A threshold in the test goes from 0.92 to 0.90. A case acquires `@pytest.mark.skip` with a plausible comment.

The clause is not "never change a test." Tests change constantly and legitimately. The clause is: **if a test changed in the same commit that made it pass, one sentence says why the old assertion was wrong.** If that sentence is *"the old assertion checked 0.90, but Broker Alpha's currency threshold is 0.92 in `sources.yaml`, so the test was wrong"* — good, that is a real fix. If the only available sentence is *"it was failing"*, the code is wrong and the test was right.

Gautam's version, which is the one people remember:

> **The test is the requirement written in code. You do not get to edit the requirement to pass the exam.**

Pankaj adds the check herself, and it is about ordering rather than wording: **read the test diff first, before the code diff.** Once you have read and approved the code, a weakened assertion reads as consistent rather than as suspicious. Look at the tests cold.

**D9 exists because documents now move slower than code by a much wider margin than they used to.** A story that took three days takes one. The spec that took a week to write is a day behind after every story.

The specific failure it catches: Ravi implements the gate, discovers at Step 3 that the spec never said what happens when a field is *absent* rather than low-confidence, sensibly decides absence is a failure, and implements it. The spec still does not mention it. Six weeks later somebody reads the spec, believes it, and builds something that assumes absent fields pass.

Usually the fix is one sentence and a date. The harder version — where the code revealed the spec was actively **wrong** rather than merely silent — is a different route entirely and involves the architect. That route gets used, hard, in [Chapter 8](08-sprint-3-rework.md).

### The fourth one, which is easy to miss

There is a fourth clause that lives under `Code` rather than under `AI-assisted work`, and it is there for the same reason:

```markdown
**D2 — No code in the change is unreachable or uncalled.**
Every function, class, config key and constant added is called by something, or
is a documented public entry point. Applies with force to AI-generated code,
which offers helpers nobody asked for.
- Check: reviewer greps each new public name for a call site during review.
- Owner: reviewer
- Cost: 5 min
```

Ask for a confidence gate and you may also receive a batch helper, a report class and two convenience wrappers, none of which anything calls. Every one of those is code somebody will read, maintain and be confused by in a year. Catching them at the door costs five minutes. Catching them later is [Chapter 10](10-retrospective.md).

### What it costs, and the honest section

Fifteen clauses. Total added cost, stated at the top of the document rather than buried: **roughly ninety minutes per story.**

Putting the number at the top does something important. It turns the Definition of Done from a moral document into an operational one. Ninety minutes a story is either planned for in the sprint, or it is paid out of the last two days, which is where it gets skipped.

And there is a section called **Blocked on tooling**, which is the part that makes the rest of the document trustworthy:

```markdown
These would be clauses if the tooling existed. They are not clauses today, and
nobody should pretend otherwise.

- **E2E in CI.** Playwright runs manually. Until it runs on every merge, E2E
  passing cannot be a done condition. Tracked; Pankaj owns it, Sprint 3.
- **Automated diff-coverage gate.** Coverage is reported but not enforced per
  file. Today D6 relies on the reviewer reading the report.
- **Automated dead-code detection.** D2 is a human grep. `vulture` was trialled
  and produced too many false positives on the Azure Functions decorators.
```

Most Definitions of Done claim end-to-end coverage the team does not have. This one says the tests run manually and therefore cannot be a done condition. **That is uncomfortable to write and it is why the other fourteen clauses can be believed.**

---

## 8. What Monday produced, and what it missed

By six o'clock there are three documents in the repository that did not exist on Friday: a build sequence, a sprint plan, and a definition of done. Tomorrow Ravi starts Step 0.

The handoff is clean:

| Artifact | Goes to | For |
|---|---|---|
| [`implementation-plan-NWD-103.md`](artifacts/implementation-plan-NWD-103.md) | Ravi | One step at a time, with [P18](../../AI-Prompts-Library/phase-4-build/P18-implement-a-story.md) |
| `sprint-2-plan.md` | Everyone | The goal, and the drop order for day eight |
| [`definition-of-done.md`](artifacts/definition-of-done.md) | Everyone | What "done" means, before anybody claims it |
| `exceptions.sample.json` | Dzmitry | Six rows, four of them awkward |

**And now the honest part, because a chapter about planning that ends with everything going well is not worth reading.**

The plan is good. It is risk-ordered, every step has a command you can type, the riskiest unknown is retired in forty minutes, and the dependency that would have cost Dzmitry half her sprint was caught on day one instead of day seven.

It also has a shape to it that nobody remarked on at the time, and it is the same shape as the spec it was built from.

Every step in the sequence is about whether a value can be **trusted**. Thresholds, overrides, per-row failures, reason codes, the minimum confidence carried into the warehouse. Step 3 is the only step that reasons about line items as a *collection* at all, and what it reasons about is whether one bad row spoils the set.

Nothing in eight steps asks whether the set is **complete**. There is no step that compares the number of rows extracted against anything at all, because there is nothing in the spec to compare against, because the spec is a specification of confidence and nobody has the other concept yet.

Gautam reads the plan twice on Monday morning against Hem's spec, running the contract check he instituted in [Chapter 3](03-sprint-1-design.md) — *check the artifact against its own contract before you build on it.* It comes back clean. Every guarantee the spec makes is honoured by a step, and every step traces to a rule.

**The check works exactly as designed. It compares the plan to the spec, and the spec is the thing with the hole in it.**

Two open questions from the Friday of Sprint 1 are still sitting on the spec, unowned, carried forward a second time: Hem's one about line items inside tables, and Pankaj's one about what the extraction response looks like when a table spans a page boundary. Nobody opens either of them on Monday. There is a plan to write, a sprint to shape, and a definition of done to argue about, and open questions with no owner do not compete well with a room full of people who have somewhere to be at four o'clock.

They are both the same question, and the answer is three weeks away.

---

**Next:** [Chapter 5 — Sprint 2: Build, backend](05-sprint-2-build-backend.md). Ravi builds in three days something that was estimated at two weeks, it genuinely works, and the most interesting thing he says all sprint is that he does not understand a piece of code that passes all its tests.

---

← [Previous](03-sprint-1-design.md) · [Case study index](README.md) · Next: [Sprint 2 — Backend](05-sprint-2-build-backend.md)
