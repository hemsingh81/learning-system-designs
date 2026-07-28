# Chapter 2 — Anatomy of a Workflow

← [Chapter 1 — What Is a Workflow?](01-what-is-a-workflow.md) · [Learning path](../learning-path.md) · Next: [Chapter 3 — Your First Workflow](03-your-first-workflow.md)

---

## Where you left off

You understand *why* Rahul's review needs to become a workflow. He sends you a real one — a much simpler example from another team, a "pre-release check" that looks at three independent things and combines them.

You open it expecting something like a skill file. It isn't. It's an actual script — real code, with function calls, not prose instructions.

You read it top to bottom and understand maybe a third of it. This chapter is the rest.

---

## What you'll learn

1. The real shape a workflow script has.
2. What a "phase" is, and why workflows are organised into them.
3. The difference between the workflow's *plan* and the actual work each stage does.

---

## The lesson

### Why a workflow is code, not prose

Think back to what made a skill work: instructions, written in plain language, followed by one continuous line of reasoning. That's exactly right for one flow of judgement.

A workflow's whole job is different: it has to **guarantee** a specific structure — these three things happen at the same time, this one waits for those to finish, this check runs before anything gets reported. A guarantee like that needs something more precise than prose. It needs an actual plan, written the way you'd write any other script: in order, with real function calls, that runs the same way every single time.

That's the honest reason a workflow looks like code and a skill looks like a paragraph. They're solving genuinely different problems.

### The pieces, one at a time

Here's a small, real workflow — the "pre-release check" Rahul showed you, simplified. Read it once, then we'll go through it piece by piece.

```javascript
// pre-release-check.workflow

meta = {
  name: "pre-release-check",
  description: "Checks tests, changelog, and docs before a release",
  phases: [
    { title: "Check" },
    { title: "Report" }
  ]
}

phase("Check")

results = parallel([
  () => agent("Do all tests pass on the release branch? Report pass/fail and any failing test names."),
  () => agent("Is there a changelog entry for every merged PR since the last release? List any missing."),
  () => agent("Are the docs for any new public API endpoints up to date? List any that are missing or stale.")
])

phase("Report")

report = agent(
  "Combine these three findings into one release-readiness report: " + results
)

return report
```

**`meta`** — the workflow's own name plate. A name, a one-line description, and the list of phases it's organised into. This is mostly here so a human — or a system listing available workflows — can tell what this does before running it, the same spirit as a skill's description, but there's no automatic triggering here. Workflows are run on purpose. You'll see exactly why in [Chapter 8](08-packaging-and-sharing.md).

**`phase(...)`** — a label marking where one stage of work begins. Nothing magic happens here — it's mostly for humans and for progress tracking, so when this workflow is running, you can see "it's in the Check phase" instead of a black box. Group related work under the same phase name.

**`agent(...)`** — one real, focused piece of work. Each call is like handing one task to one focused specialist — check *this one thing*, and report back. This is the workflow's equivalent of a skill being triggered for one specific job: each `agent()` call can, in fact, use a skill internally if one exists for that exact task. You'll see this directly in the [code review case study](../case-studies/04-code-review-workflow/README.md).

**`parallel([...])`** — run several `agent()` calls **at the same time**, and wait for **all of them** to finish before moving on. This is the "five specialists, all looking at the same thing right now" pattern from Chapter 1. The waiting-for-all-of-them part is called a **barrier**, and it's the whole subject of [Chapter 4](04-parallel-vs-pipeline.md) — it sounds simple here and it has real, non-obvious costs.

**The return value** — what the workflow actually produces. Here it's a combined report, but it could be structured data, a list of findings, anything the next thing in line needs.

### The plan vs. the work

This is the distinction that took you longest to actually see, so slow down here.

**The workflow script is the plan.** It says: run these three things at once, then combine them. That plan is fixed. It doesn't change from run to run.

**Each `agent(...)` call is where real judgement happens.** "Do all tests pass" isn't a fixed, mechanical check — the agent handling it has to actually look at test output, understand what "passing" means here, and report clearly. That's exactly the kind of reasoning a skill is good at. In fact, it very often *is* a skill, called from inside the workflow.

So a workflow isn't a replacement for judgement-based work. **It's a fixed, reliable container that decides when and how several pieces of judgement-based work happen together.** The container is deterministic. What happens inside each box in the container can be just as flexible and judgement-driven as any skill you've already built.

### Reading a workflow you didn't write

Same three-step habit you built for skills in AI-Skills, adapted:

1. **Read `meta` first.** What's this for, and how many phases does it have?
2. **Trace the shape, not the details.** Which calls are inside a `parallel(...)`? Which run one after another? Draw it as boxes and arrows if that helps — you're building a mental map of the *structure* before you worry about what each `agent()` call actually says.
3. **Check what depends on what.** Does a later stage actually need the earlier stage's real output, or could it have run at the same time? This question is the seed of [Chapter 4](04-parallel-vs-pipeline.md), and it's worth asking about every workflow you read, including ones you didn't write.

---

## Try it yourself

Here's a real, small workflow. Read it using the three-step habit above, before scrolling to the questions.

```javascript
meta = {
  name: "onboarding-doc-check",
  description: "Checks a new engineer's setup doc is accurate",
  phases: [
    { title: "Verify" },
    { title: "Summarize" }
  ]
}

phase("Verify")

steps_result = agent("Follow the steps in docs/local-setup.md exactly as written. Report which steps worked and which failed.")

phase("Summarize")

summary = agent(
  "Given this result: " + steps_result + ", write a short summary: is this doc accurate, and what needs fixing?"
)

return summary
```

1. Draw the shape — is anything here running in parallel, or is it all one after another?
2. Does the "Summarize" phase genuinely need the "Verify" phase's real output before it can start? Or could you have run them at the same time?
3. Is there anything here a plain skill could have done just as well, without needing a workflow at all? Be honest — not everything needs to be a workflow, and this example is deliberately a borderline case.

---

## What's still missing

You can read a workflow now. You still haven't built one — and the honest exercise question above is a preview of the next chapter's actual lesson: your first attempt is going to look like this simple two-step example, and it's going to teach you something uncomfortable about when a workflow is worth the trouble at all.

---

← [Chapter 1 — What Is a Workflow?](01-what-is-a-workflow.md) · [Learning path](../learning-path.md) · Next: [Chapter 3 — Your First Workflow](03-your-first-workflow.md)
