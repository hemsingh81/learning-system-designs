# Case Study 1 — Frontend: Cross-Size Component Check

← [All case studies](../README.md) · Next: [Backend — Scaffold, Test, Document](../02-backend-workflow/README.md)

Built by **Divya**, frontend engineer at Kestrel. Pattern: **parallel fan-out with a barrier.**

---

## The problem

Divya's accessibility skill (from [AI-Skills](../../../AI-Skills/case-studies/01-frontend-skill/README.md)) catches real problems, but only at one screen size at a time. A component that looks fine on desktop can genuinely break on mobile — text overlapping, a button pushed off-screen, a modal that no longer fits.

Checking all three sizes — desktop, tablet, mobile — one at a time, in sequence, works, but takes three separate passes and three separate waits.

---

## The thought process

Run Chapter 3's honest test first: **would one focused piece of work do just as well as three separate ones?** No. A genuinely different rendering happens at each size. Checking all three properly needs to actually look at each one, not reason about "how this would probably look" from a single pass.

These three checks are also **genuinely independent** — nothing about how the component renders on mobile depends on what was found on desktop. That's exactly the shape [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md) calls a clean parallel case: no reason for one to wait for another.

The barrier — waiting for all three before writing one combined report — is genuinely earned here too. You can't write "this component has issues on 2 of 3 sizes" until you've actually seen results from all three.

---

## The workflow

```javascript
meta = {
  name: "cross-size-component-check",
  version: "1.0.0",
  description: "Checks a component's rendering at desktop, tablet, and " +
    "mobile widths, and combines findings into one report.",
  phases: [
    { title: "Check" },
    { title: "Combine" }
  ]
}

phase("Check")

// Genuinely independent — nothing here needs to run in order.
results = parallel([
  () => agent("Render this component at 1440px width (desktop). Check " +
    "for layout issues: overlapping elements, overflow, misalignment. " +
    "Component: " + component_code),
  () => agent("Render this component at 768px width (tablet). Check for " +
    "the same layout issues. Component: " + component_code),
  () => agent("Render this component at 375px width (mobile). Check for " +
    "the same layout issues, plus: is anything critical pushed below " +
    "the visible fold? Component: " + component_code)
])

phase("Combine")

// A real barrier — this step genuinely needs all three results together
// to say anything meaningful about the component as a whole.
report = agent(
  "Combine these 3 findings (desktop, tablet, mobile) into one report. " +
  "State clearly which sizes have issues and which don't — don't bury " +
  "a mobile-only issue under general commentary. " + results
)

return report
```

---

## What went wrong the first time

Divya's first draft ran the three checks with a pipeline instead of `parallel()` — desktop, then tablet, then mobile, one after another, each waiting for the last to finish. It worked. It also took three times as long as it needed to, for no reason at all: nothing about the mobile check depends on the desktop check finishing first.

This is the mirror image of the mistake in [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md) — there, the mistake was an unearned barrier. Here, it was the opposite: **stages that were genuinely independent, run as if they weren't.** The fix was simply changing `pipeline` to `parallel` around the three checks. Nothing else about the workflow needed to change, because the three checks never depended on each other's output in the first place.

---

## How it was tested

Structural test, per [Chapter 7](../../tutorial/07-testing-and-iterating.md): run the three checks and confirm they genuinely start at the same time, rather than one after another. Divya used a component deliberately slow to analyze at one size — a very deep nested structure at mobile width, where wrapping behaviour is genuinely more complex to reason about. The other two sizes' results were ready well before the slow one finished. That's proof it was really parallel, not a pipeline wearing parallel's syntax.

Output testing on 3 real components: a product card, a navigation bar, and a checkout form. The workflow correctly caught a real mobile-only issue — the checkout form's submit button was pushed below the fold at 375px — that had passed review because nobody had actually checked it at that specific width.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Checked into the frontend repo. The pattern (three independent size checks, one combined report) is common enough that other teams *might* want it, but the specific sizes and the specific rendering setup are Kestrel-specific for now.

---

← [All case studies](../README.md) · Next: [Backend — Scaffold, Test, Document](../02-backend-workflow/README.md)
