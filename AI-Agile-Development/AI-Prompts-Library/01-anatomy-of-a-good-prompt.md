# Anatomy of a Good Prompt

← [How to use this library](00-how-to-use-this-library.md) · [Library index](README.md) · Next: [The handoff contract](02-the-handoff-contract.md)

> **One line:** the seven parts every prompt in this library has, and why the one everybody leaves out is the most important.

You can use this library without reading this file. But if you ever want to write your own prompt — or work out why one of yours isn't behaving — this is the file that explains the machinery.

---

## 1. Why prompts fail, in one paragraph

A prompt fails for one of three reasons, and only one of them is about wording.

**It was pointed at the wrong person.** The prompt assumed knowledge the runner didn't have, so the AI invented it. Covered in [the handoff contract](02-the-handoff-contract.md).

**It didn't say where to stop.** So the AI kept going — into adjacent files, into a refactor, into a redesign — and produced something much larger than you asked for, which now needs reviewing in full.

**It didn't say what "done" looks like.** So neither of you knows whether to run it again.

Notice that none of those three is "the wording wasn't clever enough." Prompt quality is mostly about **boundaries and inputs**, not phrasing. That's good news, because boundaries are easy to write and cleverness is not.

---

## 2. The seven parts

Every prompt in this library has these, in this order. Not all seven every time — but when one is missing, it's missing deliberately.

```text
1. ROLE + GOAL      Who the AI is being, and what job it's doing.        One line.
2. STOP GATE        Where it must halt and wait for a human.             Early, not buried.
3. INPUTS           The artifacts it must read, pasted in full.          Files, not summaries.
4. INSTRUCTIONS     What to do, as imperatives.                          Numbered or bulleted.
5. DO NOT           The boundary. What it must not touch.                The highest-leverage part.
6. DONE WHEN        The exit criterion, stated inside the prompt.        One sentence.
7. OUTPUT           Where to save it, in what shape.                     A real path.
```

Let's take them properly.

---

### Part 1 — Role and goal

One line at the top. Who the AI is being, and what the job is.

```text
You are the architect on this project. Choose the extraction approach for counterparty PDFs.
```

**Why it's first:** it sets the frame for everything after. "You are the architect" gets you tradeoff analysis. "You are a Python developer" gets you code, immediately, whether or not you wanted it yet.

**The common mistake** is over-writing this. `You are a world-class senior staff principal architect with 20 years of experience in distributed systems` does not measurably outperform `You are the architect on this project.` The long version costs you tokens and adds nothing. Say the role and move on.

---

### Part 2 — The stop gate

If the prompt has a point where a human must approve before anything continues, **say so in the first two lines.**

```text
You are the architect. Choose the extraction approach for counterparty PDFs.

**Do not write any code. Produce a recommendation, then stop and wait for my approval.**
```

**Why position matters.** The original version of this prompt that Kestrel started with buried `Then stop. Show me the plan and wait for my approval` after seven numbered instructions. It got skimmed by humans reading it, and in a long session it got deprioritised by the model too — instructions near the end of a long block compete with everything above them.

Top of the prompt. Bold. Before the detail.

**When you need one:** any prompt whose output is expensive to be wrong about. Design decisions, anything touching production config, anything irreversible, and anything where the AI would otherwise start implementing before you've agreed what to implement.

---

### Part 3 — Inputs

The artifacts the prompt depends on, **pasted in whole.**

```text
Here is the approved spec. Read it completely before responding.

<paste the entire contents of docs/spec-confidence-gate.md>

Here is the story and its acceptance criteria.

<paste stories/NWD-103.md and acceptance-criteria-NWD-103.md>
```

This is the part covered at length in [the handoff contract](02-the-handoff-contract.md), so briefly: **paste the artifact, don't describe it.** Your summary is 90% complete and feels 100% complete, and the AI will fill the missing 10% with something plausible and never mention it.

---

### Part 4 — Instructions

Imperative verbs, numbered when order matters.

```text
1. **Read** every file this change touches. List them with one line on what each does today.
2. **State** the expected behaviour and the actual behaviour, one line each.
3. **Write** a failing test that demonstrates the defect before writing any fix.
4. **Fix** the root cause, not the symptom.
5. **Search** the repository for the same pattern elsewhere.
```

Two rules.

**Verbs, not nouns.** `Read the stack trace` beats `analysis of the error should be performed`. Soft nouns produce soft output — "considerations", "an overview of", "thoughts on". You want the AI doing things, not producing a document about things.

**Number them when order is load-bearing.** In the list above, step 3 before step 4 is the entire point. If it fixes first and tests after, the test is written to match the fix rather than the defect, and you've lost your proof.

---

### Part 5 — The "Do not" list

**This is the part almost everybody leaves out, and it's the one that changes results most.**

Here's the failure mode it prevents. You ask an AI to fix a bug. It fixes the bug — and also renames two variables it found unclear, extracts a helper it thought was duplicated, reformats a function, and adds a docstring to the function next door.

Every one of those is defensible in isolation. Together they turn a four-line fix into a 180-line diff, and now your reviewer can't see the fix inside the noise. So they approve it, because it all looks reasonable, and one of those "improvements" quietly changed a behaviour nobody was watching.

An AI has no instinct for scope. It has an instinct for *helpfulness*, and unbounded helpfulness looks exactly like scope creep.

```text
Do not:
* Change any behaviour beyond the defect described
* Rename, reformat or reorganise anything you were not asked to touch
* Modify an existing test to make it pass
* Add a dependency without telling me first
* Create a new file when an existing one is the right home
```

**That third line is the important one.** An AI will edit a test until it passes, sincerely believing that's the job. It's one of the most dangerous things in AI-assisted development, because it silently converts your safety net into an agreement with your bug. Put it in every build and rework prompt. Put it in your [Definition of Done](phase-3-planning/P17-definition-of-done.md) as well, because a prompt can be forgotten and a DoD is checked.

---

### Part 6 — Done when

One sentence, inside the prompt, stating the exit criterion.

```text
You are done when every acceptance criterion in NWD-103 has a passing test that maps to it by name,
and no existing test was modified.
```

**Why this matters more than it looks.** Without an exit criterion, neither you nor the AI knows whether to stop. And in practice people keep prompting, because there's always something that could be slightly better.

That's how you end up with a PRD polished four times over — better prose, tighter structure, cleaner headings — that still doesn't say what happens when the extraction is uncertain. **The AI will improve the writing forever and never notice the missing section**, because "make this better" has no definition and "does this contain X" does.

An explicit exit criterion converts an open-ended improvement task into a closed question with an answer.

---

### Part 7 — Output

Where it goes, in what shape.

```text
Save the result as `docs/adr/0001-extraction-approach.md`, following the ADR template in `docs/adr/TEMPLATE.md`.
End the file with the artifact contract block.
```

**Why the path matters.** An artifact that lives only in a chat session cannot be handed to anybody. Half the value of this library is that each prompt produces a **file**, at a **known location**, that the next prompt consumes.

---

## 3. Two prompts, before and after

Same job. First version is the sort of thing that circulates. Second is the same thing with the seven parts.

### Before

```text
Fix the bug where positions are missing from multi-page statements.
Make sure the tests pass.
```

Twenty words. Reasonable-sounding. Here's what you'll actually get: the AI reads a plausible file, forms a theory about page handling, changes the extraction loop, and — because you said *make sure the tests pass* — if a test fails, it may well adjust the test.

You now have a change you can't verify, for a defect you never located, with a weakened test suite.

### After

```text
You are the backend engineer fixing a defect in the document ingestion pipeline.

Here is the bug report. Read it completely before responding.

<paste artifacts/bug-NWD-142.md>

Here is the current extraction module.

<paste core/extract.py>

Here is the spec the module was built from.

<paste artifacts/spec-confidence-gate.md>

1. **Reproduce first.** Write a failing test using the two-page fixture in
   `tests/fixtures/broker_alpha_2page.json` that asserts 14 line items are extracted.
   Run it. Show me it failing before you change any production code.
2. **State** the root cause in two sentences. Not the symptom — the cause.
3. **Check the spec.** Does `core/extract.py` disagree with the spec, or does the spec
   fail to cover this case? Say which. If it is the spec, stop and tell me — do not fix it in code.
4. **Fix** the root cause only.
5. **Search** the repository for every other place the same assumption is made.
   Report the hits. Do not change them yet.

Do not:
* Change any behaviour beyond the defect in NWD-142
* Rename, reformat or reorganise anything you were not asked to touch
* Modify an existing test to make it pass
* Add a dependency

You are done when the new test passes, every existing test still passes unmodified,
and you have reported the other places the same assumption appears.
```

Longer, obviously. But look at what each addition buys:

| Addition | What it prevents |
|---|---|
| Pasting the bug report, code and spec | Fixing a bug the AI inferred rather than the one that exists |
| "Reproduce first, show me it failing" | A fix for a guessed defect |
| "Check the spec — if it's the spec, stop" | Silently turning the spec into a lie ([P29](phase-6-rework/P29-the-spec-was-wrong.md)) |
| "Search for the same pattern" | Fixing one of three instances |
| The Do not list | A 180-line diff and a weakened test suite |
| "You are done when" | Four more rounds of polish on a finished fix |

That's [P27](phase-6-rework/P27-fix-from-a-qa-bug-report.md), roughly, and the difference between the two versions is most of what this library is.

---

## 4. Five habits worth stealing

### Ask for assumptions before action

```text
Before changing anything, state what you believe to be true about this code and how you know it.
```

Cheap, fast, and it surfaces the false belief before it becomes a change. Especially good when a session has gone on a while and the AI may be reasoning about a version of the file that no longer exists.

### Make it quote, not summarise

```text
For each requirement, quote the passage that satisfies it, or write MISSING.
```

An AI summarising is an AI paraphrasing, and paraphrasing is where things quietly disappear. Requiring a quote makes the absence visible.

### Ask for the failure mode

Hem's habit, applied to prompts:

```text
Before you recommend this, describe what it looks like when it goes wrong in production,
and how we would find out.
```

Anything that can't answer that isn't ready.

### Ask what it did NOT do

```text
List anything you chose not to do, and why.
```

Surfaces the silent scope decisions — the case it decided was out of scope, the edge it assumed wouldn't happen. Those are usually where the next bug is.

### One prompt, one artifact

Resist combining. "Write the spec and then implement it" gets you a spec written to justify an implementation the AI had already decided on. Two prompts, two artifacts, one human decision in between.

---

## 5. What doesn't help

Honesty about things that circulate widely and don't earn their space:

| | |
|---|---|
| **Elaborate role-play** | `You are a world-class 10x principal engineer...` measurably does nothing over `You are the backend engineer on this project.` |
| **Threats and bribes** | `This is very important to my career` — no. |
| **ALL CAPS everywhere** | Emphasis works by contrast. Capitalise everything and nothing is emphasised. |
| **"Think step by step"** | Current models already do. What helps is telling it *which* steps, in what order. |
| **Very long preambles** | Every token of throat-clearing competes with your actual instructions. |

What does help: **the right inputs, a clear boundary, and a stated exit criterion.** Which is the boring answer, and it's the one that survives contact with real projects.

---

## 6. The checklist

Writing your own prompt, run it against this:

- [ ] Does it say **who** is running it, in one line?
- [ ] If it needs a **stop gate**, is that in the first two lines?
- [ ] Are the **inputs pasted whole**, not described?
- [ ] Are the instructions **imperative verbs**, numbered if order matters?
- [ ] Is there a **Do not** list? (If not, add one. This is the most common omission.)
- [ ] Does it state **"you are done when..."**?
- [ ] Does it say **where to save** the output?
- [ ] Could someone who wasn't in the room run it and get the same thing?

That last one is the real test. A prompt that only works because you happen to know the context isn't a prompt — it's a conversation, and it can't be handed to anyone.

---

← [How to use this library](00-how-to-use-this-library.md) · [Library index](README.md) · Next: [The handoff contract](02-the-handoff-contract.md)
