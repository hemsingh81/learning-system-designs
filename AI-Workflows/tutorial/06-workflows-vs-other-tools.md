# Chapter 6 — Workflows vs. Other Tools

← [Chapter 5 — Fan-Out and Verify](05-fan-out-and-verify.md) · [Learning path](../learning-path.md) · Next: [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md)

---

## Where you left off

Rahul asked a fair question about your five-angle review workflow: "Couldn't I have just built five separate skills, and run each one myself, one at a time?"

You have a real answer this time — not "this feels more organised," an actual one.

---

## What you'll learn

1. A precise answer to Rahul's question.
2. Where a workflow fits in the full toolkit, alongside skills, subagents, and hooks.
3. What a workflow still can't do — and why that's exactly where the next tool picks up.

---

## The lesson

### Answering Rahul, properly

**"Couldn't you have just run five skills yourself, one at a time?"**

Technically, yes — and here's exactly what you'd lose by doing it that way.

**You'd lose real parallel time.** Running five skills one after another means paying the full time cost of each one, added up. `parallel()` genuinely runs them at once — this isn't a small difference. Go back to Chapter 4's numbers: five checks, one of them slow, run sequentially costs you the sum of all five. Run correctly, it costs you roughly the time of the single slowest one.

**You'd lose the guarantee.** If a human has to remember to run all five skills, then remember to run the verification step, then remember to combine the results — some day, under deadline pressure, a step gets skipped. A workflow's plan is fixed. It runs the same five checks, followed by the same verification, every single time, whether the person running it remembers the full process or not.

**You'd lose the verification step entirely, in practice.** Nothing stops a human from manually asking a follow-up "are you sure?" question after each skill runs — but in practice, under time pressure, that extra step is exactly the one that gets skipped. Building it into the workflow's fixed structure means it can't be skipped, because it isn't a choice made fresh each time — it's just what happens.

None of this is about the skills being wrong. Your five skills — if you'd built this as five separate skills — would each do their one job well. **The value a workflow adds is entirely in the coordination**: guaranteed parallelism, a guaranteed second check, and a guaranteed shape that doesn't depend on anyone remembering the full process correctly, every time, under pressure.

### Updating the full toolkit

You already built this table once, in AI-Skills. Here it is again, with workflow added.

| | Skill | Workflow | Subagent | Hook | Slash command |
|---|---|---|---|---|---|
| Who decides to use it? | The assistant, automatically | You, on purpose | The assistant, or you, delegating one task | Nobody — configured to always fire | You, by typing it |
| What does it coordinate? | Nothing — one flow of reasoning | Several pieces of work, on a fixed plan | Itself — it's one piece of work | Nothing — one fixed action | Nothing — one flow of reasoning |
| Guarantees structure (parallel, staged, verified)? | No | **Yes — this is its whole job** | No | No — it's a single trigger, not orchestration | No |
| Best for | A repeated, recognisable request, followed in one pass | A task with genuinely separate parts, stages, or that needs a real second opinion | One focused, possibly big or independent piece of work | A fixed rule that must hold every time | A task you always want to run yourself, on demand |

**A subagent is one piece of delegated work.** A workflow is the **plan that coordinates several** — and each piece inside that plan can itself be a subagent doing focused work, exactly like each `agent()` call in your review workflow. They're not competitors. A workflow is often built *out of* several subagent-style calls, arranged deliberately.

### The decision framework, extended

Same shape as AI-Skills' framework, one new first question added.

**1. Does this task have genuinely separate parts, real stages, or need an independent second check?**
→ **Workflow.** This is everything you've built in this tutorial.
→ No separate parts? Continue to the questions you already know:

**2. Does this need to happen every single time, with zero exceptions, no judgement call?**
→ **Hook.**

**3. Is it one focused, possibly big or independent piece of work — no coordination between multiple pieces needed?**
→ **Subagent**, used on its own.

**4. Will you personally always remember exactly when you want this, and are happy to type its name?**
→ **Slash command.**

**5. Otherwise — a repeated, recognisable request, followed in one continuous pass?**
→ **Skill.** Genuinely most of your day-to-day work still lives here — workflows are for the specific, less-frequent cases where coordination itself is the hard part.

Run your five-angle review through this: genuinely separate parts (five different concerns), each needing its own focus, plus an independent verification step. Question 1 fits immediately. Workflow is correct — and notably, it wasn't correct back when this whole tutorial started with your two-question PR-description check in Chapter 3, which failed this exact test.

### What a workflow still can't do

Here's the honest limit, and it's worth sitting with before you close this chapter.

**A workflow follows a fixed plan.** You wrote it in advance: these things happen in parallel, this happens after, this gets verified. That plan doesn't change once the workflow starts running — even if, partway through, something is discovered that would genuinely call for a different next step than the one you planned for.

Imagine your five-angle review's security check finds something so serious that, honestly, the *right* next move isn't "continue to the verification stage as planned" — it's "stop everything, and go investigate this one thing more deeply before doing anything else." Your workflow, as written, can't decide that. It follows its fixed phases regardless of what any individual stage discovers, because that's exactly what makes it reliable and predictable in the first place — the same fixed-ness that makes it trustworthy is also what makes it unable to genuinely adapt its own plan mid-run.

**That's not a flaw to fix. It's the actual, precise boundary of what a workflow is for.** A workflow gives you guaranteed structure, at the cost of that structure being fixed in advance.

The next tool up — an **agent** — trades some of that guarantee for real flexibility: something that can decide its own next steps as it goes, based on what it actually finds, rather than following a plan you wrote before it started. You'll learn exactly when that trade is worth making in the companion [AI-Agents](../../AI-Agents/README.md) tutorial, once you've finished this one.

For now: not every task needs that flexibility, and a workflow's guaranteed structure is very often exactly what you want. Keep building with what you have — you're not done with workflows yet.

---

## Try it yourself

Take the three tasks you assigned to a tool back in AI-Skills' equivalent exercise. Run each one through this chapter's extended framework.

1. Did any of them actually belong at "workflow" instead of where you originally put them? If so, what specifically about them did you miss the first time?
2. Pick one real task from your own team that clearly needs a workflow — genuinely separate parts, or a real need for verification. Sketch its phases, the way Chapter 2 taught you to read one.
3. Now try to imagine a version of that same task where, partway through, something is discovered that would call for a genuinely different next step than your fixed plan allows. Don't solve it — just notice it. That's the shape of an agent problem, and it's fine to leave it unsolved for now.

---

## What's still missing

You now know precisely when to reach for a workflow, and precisely where its limit is. What you haven't done yet is prove any of your workflows actually hold up under real conditions — different input sizes, edge cases, the kind of scale that only shows up once real people start relying on this.

That's the next chapter.

---

← [Chapter 5 — Fan-Out and Verify](05-fan-out-and-verify.md) · [Learning path](../learning-path.md) · Next: [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md)
