# Chapter 5 — Fan-Out and Verify

← [Chapter 4 — Parallel vs. Pipeline](04-parallel-vs-pipeline.md) · [Learning path](../learning-path.md) · Next: [Chapter 6 — Workflows vs. Other Tools](06-workflows-vs-other-tools.md)

---

## Where you left off

Time to build the thing that started this whole tutorial: Rahul's five-angle PR review. Security, tests, style, data access, docs — five focused checks, running in parallel, on the same diff.

You build it. It's fast, thanks to Chapter 4. You run it on a real PR, and the security reviewer reports: *"Line 84 stores the session token without encryption — this is a real vulnerability."*

It sounds completely convincing. Confident, specific, cites a line number. You almost put it straight on the PR.

Then you actually check line 84 yourself. The token isn't stored there at all — it's a different variable, that happens to have a similar name, three lines away. The finding was fluent, specific-sounding, and wrong.

---

## What you'll learn

1. Why an independent check can sound completely confident and still be incorrect.
2. How to design a real verification step that catches this.
3. How to build the full "fan out, then verify" pattern properly.

---

## The lesson

### Why a confident-sounding finding can still be wrong

This isn't really a workflow problem — it's the same thing you already learned to watch for with a single skill: fluent output isn't the same thing as correct output. A focused reviewer doing exactly what it was asked — "look for security issues" — will find something that *pattern-matches* to a security issue even when the actual details don't quite hold up. It's not being careless. It's doing exactly the job it was given, and that job doesn't include double-checking itself.

**One pass, however focused, is still just one pass.** The fix isn't "ask it to be more careful" — you already tried something like that with skills, and it helps a little, not enough. The real fix is a second, genuinely independent check.

### What makes a verification step genuinely independent

Here's the part that's easy to get wrong: if you ask the *same* reviewer, in the *same* context, "are you sure about that finding?" — it will very often just confirm itself. It already committed to the answer. Asking it to double-check its own homework, in the same breath, mostly just gets you a more confident version of the same mistake.

**A real verification step needs fresh eyes** — a separate `agent()` call, with no memory of how the original finding was reached, given only the specific claim and told to try to disprove it.

```javascript
verified = agent(
  "A reviewer claims: 'Line 84 stores the session token without encryption.' " +
  "Here is the actual code around line 84: " + code_snippet + ". " +
  "Try to find a reason this claim might be WRONG. Check the exact line " +
  "number and exact variable referenced. Report: is this claim accurate, " +
  "or not?"
)
```

Notice the instruction: **"try to find a reason this claim might be wrong,"** not "check if this is right." That single wording choice matters more than it looks like it should. Asking a verifier to *confirm* something tends to produce confirmation — the same agreeable instinct you saw with skills, back in AI-Skills. Asking it to actively look for a reason the claim fails changes its whole posture, and that posture change is what actually catches mistakes like your line-84 example.

### The full fan-out-and-verify shape

```javascript
meta = {
  name: "pr-five-angle-review",
  description: "Reviews a PR from 5 angles, then verifies each finding",
  phases: [
    { title: "Review" },
    { title: "Verify" }
  ]
}

phase("Review")

findings = parallel([
  () => agent("Review this diff for SECURITY issues only: " + diff),
  () => agent("Review this diff for missing TEST coverage only: " + diff),
  () => agent("Review this diff for STYLE issues only, against our style guide: " + diff),
  () => agent("Review this diff for DATA ACCESS pattern issues only: " + diff),
  () => agent("Review this diff for missing or outdated DOCS only: " + diff)
])

phase("Verify")

// Each finding gets checked independently, by a fresh agent, with the
// instruction to actively look for a reason it might be wrong.
verified_findings = pipeline(
  flatten(findings),
  (finding) => agent(
    "A reviewer claims: '" + finding + "'. Here is the actual diff: " + diff +
    ". Try to find a reason this claim might be WRONG — check exact line " +
    "numbers, exact variable names, and whether the described problem " +
    "genuinely exists. Report: CONFIRMED (the claim holds up) or " +
    "REJECTED (the claim doesn't hold up), with a one-line reason."
  )
)

confirmed_only = filter(verified_findings, (f) => f.status == "CONFIRMED")

return confirmed_only
```

Notice this uses a **pipeline**, not a barrier, for the verification stage — exactly the Chapter 4 lesson, applied here. Each finding's verification is completely independent of every other finding's verification. Nothing about checking whether the security claim holds up needs to wait for the style claim's check to finish first.

### One finding, verified twice, for anything genuinely high-stakes

For a normal PR review, one independent verifier is usually enough — it catches the plausible-but-wrong mistakes without adding much cost. But for something higher-stakes — a finding that would block a release, say — you can go one step further: verify the same finding with **two separate, independent checks**, and only trust it if both agree.

```javascript
double_checked = parallel([
  () => agent("Try to find a reason this claim might be WRONG: " + finding + diff),
  () => agent("Try to find a reason this claim might be WRONG: " + finding + diff)
])

// Only trust it if BOTH independent checks agree it holds up.
is_real = double_checked[0].status == "CONFIRMED" && double_checked[1].status == "CONFIRMED"
```

This is a genuine, deliberate use of `parallel()` as a real barrier — and it passes Chapter 4's test cleanly: the next step (deciding `is_real`) truly does need both results together before it can make its call. Don't reach for this everywhere; it roughly doubles your cost for that finding. Save it for findings where being wrong is genuinely expensive.

### What this actually bought you

Go back to your line-84 mistake. With verification in place, here's what would have happened instead:

```
Security reviewer:  "Line 84 stores the session token without encryption."
Verifier:            "REJECTED — the actual variable at line 84 is
                      `displayName`, not the session token. The token
                      handling is at line 91 and is correctly encrypted."
```

The false finding never reaches the PR at all. Rahul never sees it, never has to spend time investigating it, and never has his trust in the whole review eroded by one confident-sounding mistake. That last part matters more than it sounds — **the first time a team catches an automated review being wrong, they start double-checking everything it says, and you've lost most of the value the automation was supposed to provide.** Verification isn't just about catching individual mistakes. It's what keeps people actually trusting the output at all.

---

## Try it yourself

1. Take a fan-out check you've built — or the security-finding example above.
2. Write a verification step using the "try to find a reason this might be wrong" wording, not "confirm this is right."
3. Deliberately feed it a plausible-but-wrong finding — invent one, the way your security reviewer did with line 84. Confirm your verifier actually rejects it.
4. Now feed it a genuinely correct finding. Confirm it doesn't over-correct and reject things that are actually true. A verifier that rejects everything is just as useless as one that confirms everything.

---

## What's still missing

You now have a fast, trustworthy workflow. Rahul looks at it and asks a fair question: "Couldn't I have just built five separate skills, and run each one myself, one at a time?"

You need a real answer, not just "this feels more organised." That's the next chapter — and it's also where you'll first hear about the tool that comes after workflows.

---

← [Chapter 4 — Parallel vs. Pipeline](04-parallel-vs-pipeline.md) · [Learning path](../learning-path.md) · Next: [Chapter 6 — Workflows vs. Other Tools](06-workflows-vs-other-tools.md)
