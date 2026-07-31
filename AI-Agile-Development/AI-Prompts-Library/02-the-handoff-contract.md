# The Handoff Contract

← [Anatomy of a good prompt](01-anatomy-of-a-good-prompt.md) · [Library index](README.md) · Next: [The rework loop](03-the-rework-loop.md)

> **One line:** the gap between one person's output and the next person's input is where AI-assisted teams break — and a contract is what closes it.

This is the most important idea in the book. If you read one file in this library and nothing else, read this one.

---

## 1. The failure, in full

Week six at Northwind. Nothing is obviously on fire. Everyone is producing good work quickly. And the project is in trouble.

Here's the exact sequence.

**Monday, week two.** Amara — the product owner — writes the PRD for counterparty document ingestion. It's a good PRD. Six pages. She's careful about one section in particular, because it comes from her years on an operations floor: *what happens when the machine isn't sure.* She writes about half a page on it, including the line **"a document the system cannot read confidently must reach a human, in a form they can act on, the same day."**

She saves it to `docs/prd-counterparty-ingestion.md` and tells the team it's ready.

**Thursday, week two.** Sofia — the architect — starts design. She's read the PRD. She opens a session with her AI and types, from memory:

> *"We're building a pipeline that reads broker statement PDFs and extracts positions into our warehouse. It needs to handle multiple layouts per counterparty and it can't put bad data in the warehouse. Design me the ingestion architecture."*

Everything in that sentence is true. It's an accurate summary. It is roughly 90% of the PRD.

The missing 10% is *"in a form they can act on."*

**What the AI produces** is genuinely excellent: blob landing zone, classifier, custom extraction models per layout, confidence gate, bronze layer for audit, and — because Sofia said "can't put bad data in the warehouse" — documents below threshold are **rejected and logged**.

Rejected and logged. Not routed to a human with the failing field highlighted. Rejected. Logged.

**Week four.** Tomas has built it. It works. The tests pass.

**Week six.** Amara sees a demo and asks where the exception queue is.

There isn't one. There was never a story for it. It wasn't in the design, so it wasn't in the plan, so it wasn't in the sprint. Two people, two AI sessions, both excellent, and the thing the PRD was most careful about **evaporated in the gap between them.**

Adding it now means a new screen, a new table, a new API surface, a change to the gate's output shape, and a conversation with the client about the date.

---

## 2. Why an AI makes this worse, not better

Here's the part that matters, and it's not obvious.

Hand an incomplete brief to a **human** engineer and something specific happens: they get confused. They frown at it. They say *"wait — what am I supposed to do with the ones it can't read?"* Their confusion is a **signal**, and the signal travels back to you.

Hand the same incomplete brief to an **AI** and you get a complete, confident, well-structured design that closes the gap by **making something up that sounds sensible.** Reject and log. Perfectly reasonable! It's what a lot of pipelines do!

> **The AI will never tell you that you handed it the wrong thing.** It has no way to know it's missing. It produces the best possible output for the input it was given, and the output *looks exactly as good* as it would have looked if the input had been complete.

That's the whole problem in one sentence. The traditional early-warning system for a bad handoff was a confused colleague, and the AI has removed it while making everything downstream faster.

Faster, in the wrong direction, with no confusion to slow you down.

### The three ways the gap gets created

| How | What it looks like | Why it happens |
|---|---|---|
| **Summarising from memory** | Sofia types a paragraph instead of pasting six pages | It's faster, and the summary feels complete because *she* remembers the rest |
| **Paraphrasing into your own frame** | "It can't put bad data in the warehouse" instead of "must reach a human, same day" | Each role re-frames the problem in their own vocabulary. The re-framing drops what doesn't fit the frame |
| **Assuming the artifact says something it doesn't** | Tomas assumes the spec covers page boundaries | Nobody ever verified what the spec *guarantees* to cover |

All three are invisible at the moment they happen. All three are expensive weeks later.

---

## 3. What a handoff contract actually is

A handoff contract is a short, explicit statement — written into the artifact itself — of **what the next person is guaranteed to find, and what they are guaranteed not to.**

That's it. It's not a process. It's a block of text at the end of a document.

Here's the one that would have saved Northwind six weeks:

> **Artifact contract — `docs/prd-counterparty-ingestion.md`**
>
> Anyone designing against this PRD can rely on finding:
> - The business problem and why it exists now
> - Success metrics, in operational terms, with current baselines
> - **What must happen when the system is not confident** — including who sees it, in what form, and by when
> - What is explicitly out of scope for v1
> - The named users and what their working day looks like
>
> This PRD does **not** contain: technology choices, data schemas, API shapes, or sequencing.
> If you need those, they are the architect's job — see [P11](phase-2-design/P11-write-the-technical-spec.md).
>
> **If any bullet above is missing or empty, this PRD is not done.** Do not design against it.

Now read Sofia's paraphrase again against that contract. `must reach a human, in what form, by when` is a **named guarantee**. Her one-line summary drops it visibly. She'd have caught it — or her AI would have, if she'd pasted the contract along with the summary and asked it to check.

### The contract is a checklist in both directions

That's the part people miss. It works two ways:

**For the producer:** it's your definition of done. Amara can't call the PRD finished while a guaranteed bullet is empty.

**For the consumer:** it's your input validation. Sofia's first move should be to check the artifact against its own contract before she designs anything. Ten seconds. Catches a six-week problem.

---

## 4. The four fields every prompt declares

Every prompt file in this library opens with the same four-row table. They exist for exactly this reason.

| Field | What it does |
|---|---|
| **Who runs it** | Names the role whose knowledge the prompt assumes. Run by the wrong role, the AI invents the missing knowledge |
| **Takes in** | Names the artifacts that must **already exist**, at real paths. Not "context" — files |
| **Produces** | Names the one artifact created, at a real path. One prompt, one artifact |
| **Hands off to** | Names the next role and the exact prompt they'll run |

Chain those together and you get something you can actually look at:

```mermaid
flowchart LR
    A["P06 PRD<br/>Amara"] -->|prd-counterparty-ingestion.md| B["P07 Stories<br/>Amara"]
    B -->|stories/NWD-1xx.md| C["P08 Acceptance criteria<br/>Amara + Ananya"]
    C -->|acceptance-criteria-NWD-103.md| D["P10 Plan mode<br/>Sofia"]
    D -->|ADR-0001| E["P11 Spec<br/>Sofia"]
    E -->|spec-confidence-gate.md| F["P15 Impl plan<br/>Rahul"]
    F -->|implementation-plan-NWD-103.md| G["P18 Implement<br/>Tomas"]
    G -->|core/confidence.py| H["P22 P25 Test<br/>Ananya"]

    style A fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
    style E fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    style H fill:#122B22,stroke:#3DDC97,color:#E8EEF4
```

Every arrow is a file with a contract on it. Every arrow is a place the project can quietly break.

---

## 5. The rule that fixes 80% of it

One rule. It's almost too simple to write down, and it's the highest-value habit in this entire book.

> ### Paste the artifact. Do not describe it.

When you start a session that depends on someone else's work, **give the AI the file** — the actual file, whole — and the contract block that goes with it. Do not summarise it. Do not paraphrase it into your own framing. Do not tell the AI what's in it.

Sofia's session should have opened:

```text
Here is the approved PRD. Read it completely before responding.

<paste the entire contents of docs/prd-counterparty-ingestion.md>

Here is the contract this PRD guarantees:

<paste the contract block>

**First task, before any design work:** check the PRD against its own contract.
For each guaranteed item, quote the section that satisfies it, or state that it is missing.
List anything the PRD leaves ambiguous that a design would have to invent.

Then stop. Do not design anything yet.
```

That's it. That's the fix. It costs one extra paste and about ninety seconds of reading, and it would have caught the missing exception queue on the Thursday of week two instead of the Wednesday of week six.

**Why does describing feel more natural?** Because it's how you'd brief a colleague, and briefing a colleague *works* — because the colleague asks questions. You've imported a habit that depended on a feedback loop into a situation that doesn't have one.

### The check-the-artifact-against-its-contract move

That middle instruction is worth isolating, because it's useful on its own:

```text
**Before doing anything else:** here is an artifact and the contract it is supposed to satisfy.
For each guaranteed item in the contract, either quote the passage that satisfies it or say
"MISSING". Then list every place a downstream reader would have to guess.

Do not fix anything. Do not design anything. Report only.
```

An AI is genuinely good at this — better than a human skimming, because it doesn't fill gaps from memory the way a person who was in the meeting does. Run it on every artifact you receive. It takes thirty seconds and it is the cheapest insurance in the book.

---

## 6. When the contract itself is wrong

Sometimes you'll check an artifact against its contract, find everything present, and *still* discover downstream that something essential was missing.

That means the **contract** was incomplete, not the artifact. It's a different problem and it has a different fix: update the contract in the prompt file, and — this is the part teams skip — **go back and re-check every artifact already produced under the old contract.**

Northwind hit this. The original spec contract for `spec-confidence-gate.md` guaranteed: the thresholds, the per-field-type rules, the failure output shape, and the exception routing. All present. All correct.

It did not guarantee anything about **completeness** — about whether all the data that should have been extracted actually was. Nobody thought to ask, because the whole mental model was "is this number trustworthy", not "is this number *here*".

Bug [NWD-142](../Case-Study/Python-ETL/artifacts/bug-NWD-142.md) is what that missing guarantee cost: a positions table spanning a page boundary, nine rows loaded where fourteen existed, every one of them high-confidence and correct. The gate was working perfectly. It was answering a question nobody had noticed was the wrong question.

The fix wasn't only in code. It was a new guaranteed line in the spec contract:

> - **What "complete" means for this document type**, and how the system detects incompleteness

And then a sweep back through every spec written under the old contract to see what else had the same hole.

That's [P29 — The spec was wrong](phase-6-rework/P29-the-spec-was-wrong.md), and the fact that it needs to exist at all is the honest admission this book is built on.

---

## 7. The contract block template

Paste this at the end of any artifact you produce.

```markdown
> **Artifact contract — `<path/to/this/file>`**
>
> Produced by: <role> using <prompt ID>
> Approved by: <role, date>
>
> Anyone consuming this file can rely on finding:
> - <guarantee 1 — be specific enough to check>
> - <guarantee 2>
> - <guarantee 3>
>
> This file does **not** contain: <the adjacent things people will assume are here>.
> Those live in: <path>, produced by <prompt ID>.
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: <who must approve, and what downstream artifacts must be re-checked>
```

Three notes on filling it in.

**Guarantees must be checkable.** "Covers error handling" is not a guarantee — two people will disagree about whether it's satisfied. "States what happens to a document when every field fails the gate, including who is notified" is checkable.

**The "does not contain" line is doing real work.** It's what stops the next person assuming this document covers something it doesn't. At Northwind the PRD's "does not contain: technology choices" line is what stopped a genuinely good argument about Document Intelligence versus an LLM from happening two weeks before it should have.

**The last line prevents silent divergence.** If changing the data contract requires re-checking the transform, the sinks and the reconciliation, write that down — because the person changing it in four months will not know.

---

## 8. What this looks like on a real team

Not a process. Four habits.

| Habit | Cost | What it prevents |
|---|---|---|
| Every artifact ends with a contract block | 5 minutes when you write it | The producer calling something done when a guarantee is empty |
| Every session opens by pasting the artifact whole, never a summary | 30 seconds | 90% of everything in this file |
| Every consumer runs the check-against-contract prompt before building | 30 seconds | The one guarantee that got dropped in paraphrase |
| Changing a contract triggers a re-check of everything produced under the old one | An hour, rarely | The NWD-142 class of problem — a hole replicated across six documents |

None of that is heavy. Total cost is maybe twenty minutes a sprint. Northwind lost four weeks to not doing it.

---

## 9. The one thing to remember

If everything else in this file falls out of your head, keep this:

> **When you hand work to a human, their confusion is your error-checking. An AI has no confusion. So the checking has to be written down.**

That's the whole idea. The contract is just where you write it down.

---

← [Anatomy of a good prompt](01-anatomy-of-a-good-prompt.md) · [Library index](README.md) · Next: [The rework loop](03-the-rework-loop.md)
