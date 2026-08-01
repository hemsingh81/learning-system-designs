# The Prompt Analysis

← [Learning path](learning-path.md) · [README](README.md) · Next: [The prompts library](AI-Prompts-Library/README.md)

> **One line:** what was wrong with the fifteen prompts this book started from, and exactly what happened to each one.

This book didn't start from nothing. It started from a set of fifteen development-workflow prompts — good ones, better than most of what circulates — and a question about what was missing.

This page is the honest answer. It's blunt, because a diplomatic version would be useless.

If you arrived with your own prompt library, read this first. The five gaps below are almost certainly in yours too, because they're structural — they come from the fact that nearly every prompt library on the internet is written by one person working alone, and a software project is not one person working alone.

---

## 1. What the original fifteen got right

Worth saying properly before the criticism, because these are not small things.

### Imperative voice with real specificity

> *"Read the stack trace, open the exact files involved."*

Not "analyse the error." **Read the stack trace. Open the files.** Verbs the AI can't wriggle out of. Most prompt libraries are full of soft nouns — "provide analysis of", "consider the implications" — and soft nouns produce soft output.

### Explicit stop gates

Three of the fifteen — the plan-mode prompt, the implementation-plan prompt, and the commit prompt — end with some version of *"then stop and wait for my approval."*

That is the single most valuable habit in the whole set, and it's the one thing that separates AI-assisted work from AI-generated mess. It's kept and strengthened throughout this library.

### Evidence over vibes

> *"Prove or kill each one with logs or a tiny test — evidence, not vibes."*

That line is doing real work. An AI asked to debug will happily produce three plausible hypotheses and then confidently assert the first one, with no check. Demanding proof for each is the difference between debugging and guessing eloquently. It survives verbatim into [P26](AI-Prompts-Library/phase-6-rework/P26-debug-an-error-fast.md).

### Bracket placeholders

`[DESCRIBE FEATURE]`, `[YOUR STACK]`, `[PROTECTED PATHS]`. Simple, obvious, and it forces you to actually think about the input rather than letting the AI infer it. Kept — and every placeholder in this library now gets an explanation table, because "what do I put in `[YOUR NON-NEGOTIABLES]`?" turned out to be a real question people asked.

---

## 2. The five gaps

### Gap 1 — No role owns anything

All fifteen prompts read as though one person is doing everything.

Take the PRD prompt. Who runs it? On a real team the answer is the product owner, and that matters enormously — because the prompt assumes the runner can judge what ships in v1 and what doesn't. A product owner can make that call. A backend engineer four days into the project cannot, and if they run it anyway, the AI fills the gap by **inventing business priorities that sound completely reasonable** and nobody catches it until the demo.

That's not a bad prompt. That's a good prompt pointed at the wrong person.

**The fix:** every prompt in this library declares who runs it, and the four-field header (`Who runs it` / `Takes in` / `Produces` / `Hands off to`) is mandatory. See [the cast](the-cast.md) for why role assignment is load-bearing rather than decorative.

---

### Gap 2 — No handoff contract

This is the big one.

The original PRD prompt ends well: *"Save it as docs/prd-[feature].md so every later prompt can reference it."* Good instinct. But then three later prompts say some version of "reference the PRD" — and **nothing anywhere defines what the next person is guaranteed to find in it.**

So here's what actually happens on a real team. Preetinka writes a PRD. Hem needs it. Hem opens it, skims it, and then describes the problem to her own AI **in her own words**, because that's faster than pasting six pages. Her words are 90% the same as Preetinka's. The missing 10% is the part about what happens when the extraction is uncertain.

Two weeks later there's a design that has no concept of an exception queue.

Nobody prompted badly. The seam leaked.

> **The thing that makes this specific to AI work:** when a human receives an incomplete handoff, they ask a question. They say "wait, what about the uncertain ones?" An AI does not. An AI takes what you give it and produces something confident and complete-looking on top of it, gap and all. **The AI will never tell you that you handed it the wrong thing.**

**The fix:** [the handoff contract](AI-Prompts-Library/02-the-handoff-contract.md), and a contract block at the end of every prompt file stating exactly what its artifact guarantees.

---

### Gap 3 — No rework loop

The fifteen describe a straight line: PRD → plan → spec → implement → test → commit.

Real work is a loop, and the loop is most of the sprint:

```
build → test → wrong → understand why → fix → test → still wrong →
oh, the spec was wrong → update spec → fix → review → three comments →
two are fair, one isn't → fix → test → ship
```

The original set has a debug prompt, which handles exactly one entry point into that loop: **something threw an exception and there's a stack trace.**

It has nothing for the far more common case — and the one the author actually asked about:

> *"Suppose Dev A is working on a story which is code generated. Now after doing some testing there are some issues. For that, what kind of prompt do we have to use?"*

The code runs. Nothing throws. The tests pass. QA says it's wrong. **That is a completely different problem from debugging an error**, and the debug prompt actively misfires on it, because step 1 is "read the stack trace" and there isn't one.

**The fix:** [Phase 6](AI-Prompts-Library/03-the-rework-loop.md), five prompts, the longest phase in the book. [P27 — Fix from a QA bug report](AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md) is the flagship and the single most important file here.

---

### Gap 4 — No ceremonies, so no team rhythm

Nothing in the original fifteen covers: story slicing, acceptance criteria, estimation, sprint planning, standup, definition of done, release readiness, or retrospective.

That's understandable — none of them feel like "prompts." They feel like meetings.

But they're precisely where an AI-assisted team either converges or diverges, and they're where the AI-specific failure modes surface. Standup is where somebody finally says *"the AI produced something I don't fully understand and I'm not comfortable merging it"* — which is a legitimate, common, and completely new category of blocker that didn't exist five years ago.

**The fix:** seven new ceremony prompts, each of which explains the ceremony itself from scratch for readers who've never worked in scrum.

---

### Gap 5 — No prompt knows when it's finished

Not one of the fifteen says "you are done with me when X."

So you never know whether to re-prompt or move on. And in practice people re-prompt, because there's always something that could be a bit better — which is how you end up with a PRD that's been polished four times and still doesn't say what happens when the extraction is uncertain. **The AI will happily improve the prose forever and never notice the missing section.**

**The fix:** every prompt file has §7 *Why this is the final prompt* — with a tickable checklist and an explicit warning about the over-prompting failure mode for that specific artifact — feeding straight into §8 *When it is not done*.

---

## 3. What happened to each of the fifteen

Nothing was deleted outright. Five were re-scoped to a role, two pairs were split apart because they were doing two jobs each, and everything got the eleven-section treatment.

| # | Original | Verdict | Becomes | What changed |
|---|---|---|---|---|
| 01 | Write a Full PRD | **Re-scope** | [P06](AI-Prompts-Library/phase-1-discovery/P06-write-a-full-prd.md) | Assigned to the Product Owner. Success metrics must be operational (T+2→T+1), never model metrics. Gains an explicit contract for what the architect will find in it. |
| 02 | Create Your CLAUDE.md | **Re-scope + promote** | [P01](AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md) | Promoted to the first prompt in the book. Everything downstream depends on it existing, so it earns Sprint 0 position rather than being an afterthought. |
| 03 | Ultra Plan Mode | **Split** | [P10](AI-Prompts-Library/phase-2-design/P10-ultra-plan-mode.md) | Was doing two jobs: *choose an approach* and *sequence the build*. Now it does only the first, as the Architect. The stop gate moves to the top of the prompt where it can't be skimmed past. |
| 04 | Spec-Driven Development | **Re-scope** | [P11](AI-Prompts-Library/phase-2-design/P11-write-the-technical-spec.md) | Overlapped heavily with the PRD prompt. Now clearly the Architect's behaviour contract, distinct from the PO's business document, with the difference explained rather than assumed. |
| 05 | Full UI & UX Design Brief | **Re-scope** | [P14](AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md) | Now anchored to a real user's working day (Preeti, forty exceptions a morning) rather than a component inventory. |
| 06 | Implementation Plan | **Split (other half)** | [P15](AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md) | The sequencing half of the old #03. Team Lead's job. The "compiles and runs after every step" rule gets a full explanation of why it matters more with AI. |
| 07 | Wire Up an MCP Server | **Regroup** | [P03](AI-Prompts-Library/phase-0-foundation/P03-wire-up-an-mcp-server.md) | Not a lifecycle prompt — it's environment setup. Moved to Sprint 0. Now explains what MCP actually is before using the acronym. |
| 08 | Connect Your Database | **Regroup** | [P02](AI-Prompts-Library/phase-0-foundation/P02-connect-the-database.md) | Same — Sprint 0. Extended for the two-warehouse reality (Azure SQL silver, Snowflake gold) and serverless connection pooling. |
| 09 | Find Security Gaps | **Keep, re-home** | [P24](AI-Prompts-Library/phase-5-verify/P24-find-security-gaps.md) | Strong prompt, kept nearly intact. Moved into Verify where it belongs, jointly owned by QA and the Architect. |
| 10 | Debug an Error Fast | **Keep, narrow** | [P26](AI-Prompts-Library/phase-6-rework/P26-debug-an-error-fast.md) | Kept almost verbatim — it's the best of the fifteen. But now explicitly scoped: *this is for when something threw*. If the code runs and the answer is wrong, you want P27. That fork was the missing signpost. |
| 11 | E2E Test Your Application | **Keep, extend** | [P22](AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md) | Extended for pipeline testing — an E2E test here spans blob → function → warehouse, not just a browser. |
| 12 | Clean Up Dead Code | **Keep, re-home** | [P34](AI-Prompts-Library/phase-8-improve/P34-clean-up-dead-code.md) | Moved to Improve. Gains the AI-era observation: AI-assisted work generates dead code faster, because abandoned approaches leave their helpers behind and nobody remembers they were speculative. |
| 13 | Write Clean Git Commits | **Keep, strengthen** | [P31](AI-Prompts-Library/phase-7-release/P31-write-clean-git-commits.md) | The *splitting* step gets much more weight: an AI session routinely touches eight files for three unrelated reasons, which was rare when a human made every edit deliberately. |
| 14 | Hooks as Guardrails | **Regroup** | [P04](AI-Prompts-Library/phase-0-foundation/P04-hooks-as-guardrails.md) | Sprint 0. Now leads with the actual point: a hook is the only way to guarantee something happens *every* time, because it's run by the harness, not chosen by the AI. |
| 15 | Turn a Task Into a Skill | **Regroup** | [P05](AI-Prompts-Library/phase-0-foundation/P05-turn-a-repeated-task-into-a-skill.md) | Sprint 0, and now connected back to [AI-Skills](../AI-Skills/README.md) where Gautam built his first one. |

---

## 4. The twenty-one new prompts

Grouped by which gap they close.

### Handoff and definition (Gap 1, 2, 5)

| | | |
|---|---|---|
| [P08](AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) | Write Acceptance Criteria | The missing link between a story and a test |
| [P13](AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md) | Design the Data Contract | The single most important artifact on an ETL project, absent from every prompt library we could find |
| [P17](AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md) | Definition of Done | The team-wide contract, distinct from per-story criteria |
| [P12](AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) | Record an Architecture Decision | So the *reason* survives the person who decided |

### The rework loop (Gap 3)

| | | |
|---|---|---|
| [P27](AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md) | **Fix From a QA Bug Report** | **The flagship.** The exact scenario that prompted this book |
| [P28](AI-Prompts-Library/phase-6-rework/P28-respond-to-code-review-feedback.md) | Respond to Code Review Feedback | Because "address this review" makes an AI change code for comments that weren't defects |
| [P29](AI-Prompts-Library/phase-6-rework/P29-the-spec-was-wrong.md) | The Spec Was Wrong | The escape hatch. Without it, devs fix specs silently in code and the document becomes a lie |
| [P30](AI-Prompts-Library/phase-6-rework/P30-when-the-ai-is-stuck.md) | When the AI Is Stuck | Circling, confident falsehoods, and the sunk-cost problem |

### Ceremonies (Gap 4)

| | | |
|---|---|---|
| [P07](AI-Prompts-Library/phase-1-discovery/P07-slice-the-prd-into-stories.md) | Slice the PRD into Stories | Vertical slicing, and why slicing by layer is the classic failure |
| [P09](AI-Prompts-Library/phase-1-discovery/P09-estimate-and-rank-the-backlog.md) | Estimate and Rank the Backlog | And why AI changes the estimate for some story shapes and not others |
| [P16](AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md) | Sprint Plan and Assignment | Capacity, goals, and the dependency Atul spots three weeks early |
| [P21](AI-Prompts-Library/phase-4-build/P21-daily-standup-summary.md) | Daily Standup Summary | Where seven private AI sessions get reconciled |
| [P32](AI-Prompts-Library/phase-7-release/P32-release-readiness-check.md) | Release Readiness Check | Parallel run — the gate that tests alone can't replace |
| [P35](AI-Prompts-Library/phase-8-improve/P35-run-the-retrospective.md) | Run the Retrospective | And why "we'll be more careful" is not an action item |

### Build and verify depth

| | | |
|---|---|---|
| [P18](AI-Prompts-Library/phase-4-build/P18-implement-a-story.md) | Implement a Story | The central build prompt. Somehow absent from the original set |
| [P19](AI-Prompts-Library/phase-4-build/P19-build-the-ui-from-the-brief.md) | Build the UI from the Brief | States before happy path |
| [P20](AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) | Write Tests Alongside the Code | Behaviour tests vs tests that restate the implementation |
| [P23](AI-Prompts-Library/phase-5-verify/P23-review-someone-elses-code.md) | Review Someone Else's Code | AI code is syntactically fine, so the classic checklist finds nothing |
| [P25](AI-Prompts-Library/phase-5-verify/P25-data-quality-validation.md) | Data Quality Validation | "The code works" ≠ "the data is right". **This is the prompt that would have caught NWD-142** |
| [P33](AI-Prompts-Library/phase-7-release/P33-write-the-runbook.md) | Write the Runbook | For the person on call at 3am who didn't build it |
| [P36](AI-Prompts-Library/phase-8-improve/P36-tech-debt-triage.md) | Tech Debt Triage | Interest rate, not just principal |

---

## 5. Three prompt-craft changes applied to all thirty-six

Beyond restructuring, three things changed in how the prompts themselves are written.

### The stop gate moves to the top

The original plan-mode prompt buries `Then stop. Show me the plan and wait` after seven numbered instructions. Anything at position eight gets skimmed — by humans reading it and, in a longer context, by the model too.

Every prompt with a gate now states it in the first two lines.

### Every prompt gets a "Do not" list

This is the single highest-leverage change, and it's the one most often missing.

An AI told what to do will also do adjacent things it considers helpful. Told to fix a bug, it renames three variables. Told to add a test, it refactors the function under test. The result looks like a bigger, better change and is much harder to review.

Naming the boundary is what prevents it:

```text
Do not:
* Change any behaviour beyond the defect described
* Rename, reformat or reorganise anything you were not asked to touch
* Modify an existing test to make it pass
* Add a dependency
```

### Every prompt declares its own exit criteria

One line, inside the prompt: **"You are done when..."**

That line is what makes §7 of every file answerable, and it's what stops the reader from re-prompting a finished artifact into mush.

---

## 6. If you want the short version

Your prompts were fine. What was missing wasn't better wording — it was:

1. **Who runs this** (role)
2. **What it's guaranteed to hand over** (contract)
3. **What to do when it's wrong** (the loop)
4. **When to stop** (exit criteria)

Everything in this library is one of those four things, applied thirty-six times.

---

← [Learning path](learning-path.md) · [README](README.md) · Next: [The prompts library](AI-Prompts-Library/README.md)
