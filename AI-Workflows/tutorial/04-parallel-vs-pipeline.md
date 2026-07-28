# Chapter 4 — Parallel vs. Pipeline

← [Chapter 3 — Your First Workflow](03-your-first-workflow.md) · [Learning path](../learning-path.md) · Next: [Chapter 5 — Fan-Out and Verify](05-fan-out-and-verify.md)

---

## Where you left off

Your function-review workflow works, and it earned its overhead. Vikram asks you to help with something bigger: a workflow that reviews five files, one at a time, each going through the same three steps — read it, analyze it, summarize the findings.

You write it the obvious way: `parallel()` around all five files, each one going through all three steps inside its own `agent()` call.

It works. It's also slower than you expected, and you can't immediately say why. This chapter is why — and it's the single most important idea in the whole tutorial.

---

## What you'll learn

1. The real, practical difference between running work in parallel and running it as a pipeline.
2. How to pick correctly between them.
3. What a "barrier" actually costs, and when that cost is genuinely worth paying.

---

## The lesson

### What you actually built

```javascript
results = parallel([
  () => agent("Read, analyze, and summarize file A, all in one pass: " + fileA),
  () => agent("Read, analyze, and summarize file B, all in one pass: " + fileB),
  () => agent("Read, analyze, and summarize file C, all in one pass: " + fileC),
  () => agent("Read, analyze, and summarize file D, all in one pass: " + fileD),
  () => agent("Read, analyze, and summarize file E, all in one pass: " + fileE)
])
```

This genuinely does run all five files at the same time — that part is correct, and it's faster than doing all five one after another. But look closely at what each individual piece of work is actually doing: read, analyze, *and* summarize, all three, back to back, inside one `agent()` call. You've parallelised *across files*, but each file still goes through its three steps as one long, undivided piece of work.

### The problem with a barrier

`parallel([...])` is what's called a **barrier**: it starts everything at once, and — this is the part that matters — it waits for **every single one** to completely finish before anything after it can begin.

Here's what that actually costs. Say four of your five files are short and analyze quickly — a few seconds each. The fifth is a genuinely large, complicated file that takes two full minutes to read, analyze, and summarize.

**Your workflow's total time is two minutes.** Not "a few seconds, since most of them were fast" — two minutes, because the barrier waits for the *slowest* one before it lets anything proceed. The four fast files finished long ago and are just sitting there, done, waiting for the fifth one to catch up before the workflow can report anything at all.

This is the real, practical cost of a barrier: **your wall-clock time becomes the time of your single slowest piece, not the average.** One slow file taxes the entire batch.

### The alternative: a pipeline

A pipeline flows each item through every stage **independently**. There's no barrier between stages — item A can be finishing its third stage while item B is still on its first.

```javascript
results = pipeline(
  [fileA, fileB, fileC, fileD, fileE],
  (file) => agent("Read this file and extract its key structure: " + file),
  (structure, file) => agent("Analyze this structure for issues: " + structure),
  (analysis, file) => agent("Summarize these findings in 2 sentences: " + analysis)
)
```

Now watch what actually happens when you run this. File A starts stage 1 (read). The instant it finishes, it moves to stage 2 (analyze) — it does **not** wait for files B through E to also finish stage 1 first. Meanwhile, file B has *already started* stage 1, right behind A, and file E — your slow one — is still working through stage 1 on its own timeline, not holding anyone else back.

**Your total wall-clock time is now roughly the time of your slowest single chain, not the sum of every stage for every file, and not gated by your slowest file finishing stage 1 before anyone else can move to stage 2.** The four fast files sail through all three stages while file E is still working — instead of sitting idle, waiting for it.

### Why this matters more as things scale

With five files, the difference is noticeable. With fifty files, it's the difference between a workflow that finishes in a couple of minutes and one that takes an hour, purely because of how the stages are wired together — not because the underlying work changed at all.

This is worth repeating because it's easy to forget once you're focused on getting the logic right: **the orchestration shape you choose has a real, measurable cost, completely separate from whether each individual step is written well.**

### So when IS a barrier the right call?

Not never — genuinely, sometimes you need one. The honest test is: **does the next step need *all* the previous results together, at once, before it can do its job correctly?**

A few real cases where the answer is yes:

- **Deduplication across everything.** If two of your five files might report the *same* underlying issue, you need to see all five findings together before you can spot and merge the duplicate. You can't dedupe file A against file C if you haven't looked at file C yet.
- **An early-exit decision.** "If zero issues were found across all five files, skip the expensive verification stage entirely" needs to know the total count *before* deciding whether to proceed — which means waiting for everyone.
- **A genuine comparison between items.** "Which of these five files has the most serious issue?" can't be answered until you've actually seen all five.

None of these are true for your file-review workflow. Nothing about summarizing file A depends on knowing what happened in file C. That's exactly why the barrier there was pure cost with nothing bought.

### The default worth remembering

**Default to a pipeline. Reach for a barrier only when you can name the specific cross-item reason you need one** — deduplication, an early-exit decision, or a real comparison across everything. If you can't name that reason, you almost certainly don't need one, and a pipeline will finish faster for the exact same work.

A useful smell test: if you find yourself writing "first collect everything, *then* process it" and the "then" step doesn't actually look at more than one item at a time — that's not really a reason for a barrier. That work belongs inside the pipeline's own stages instead.

### Fixing your five-file workflow

```javascript
results = pipeline(
  [fileA, fileB, fileC, fileD, fileE],
  (file) => agent("Read this file and extract its key structure: " + file),
  (structure) => agent("Analyze this structure for issues: " + structure),
  (analysis) => agent("Summarize these findings in 2 sentences: " + analysis)
)

// Only add a barrier AFTER the pipeline, and only because you have a real
// cross-item reason: here, deduplicating similar findings across all 5 files.
deduped = agent("Here are 5 summaries — merge any that describe the same underlying issue: " + results)
```

Notice the shape: **pipeline by default for the per-item work, and a barrier only at the one specific point where you actually need everything together** — right at the deduplication step, and nowhere else.

---

## Try it yourself

1. Take a workflow you've built (or the file-review one above). Identify every `parallel([...])` call in it.
2. For each one, ask honestly: does anything AFTER this barrier genuinely need every result together, at once? Name the specific reason if yes.
3. For any barrier that fails that test, rewrite it as a pipeline instead.
4. If you can actually run both versions, time them with a realistic mix of fast and slow items — one item that's clearly slower than the rest is the most revealing test case. Write down the real difference.

---

## What's still missing

You can now build a workflow that's actually fast. Speed alone doesn't make it *trustworthy* — Rahul's five-angle review still has an open problem from Chapter 1: what happens when one of your five focused checks finds something that sounds convincing and turns out to be wrong?

That's the next chapter.

---

← [Chapter 3 — Your First Workflow](03-your-first-workflow.md) · [Learning path](../learning-path.md) · Next: [Chapter 5 — Fan-Out and Verify](05-fan-out-and-verify.md)
