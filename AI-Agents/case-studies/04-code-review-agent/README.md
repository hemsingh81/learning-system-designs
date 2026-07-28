# Case Study 4 — Code Review: A Workflow's Fixed Plan, Made Adaptive

← [Case Study 3 — QA](../03-qa-agent/README.md) · [All case studies](../README.md)

Built by **Rahul**, tech lead at Kestrel. Pattern: **an agent that decides which review angles apply, then reuses the existing workflow to run them.**

---

## The problem

This is the story that's run through all three tutorials. Rahul's original AI-Skills [`/code-review` skill](../../../AI-Skills/case-studies/04-code-review-skill/README.md) does one focused pass. His AI-Workflows [five-angle review workflow](../../../AI-Workflows/case-studies/04-code-review-workflow/README.md) fixed the large-PR problem by always checking security, tests, style, data access, and docs — a fixed, reliable, well-tested plan.

"Always" is doing real work in that sentence, though. A one-line typo fix in a doc comment gets the exact same five angles as a 600-line PR touching authentication. Four of those five checks find nothing on the typo fix, every time, because they were never going to find anything there. The workflow, being a fixed plan, has no way to know that in advance and skip them.

---

## The thought process

This is precisely [Chapter 6](../../tutorial/06-agents-vs-other-tools.md)'s question, answered for real: is "decide which angles apply" itself something you could plan in advance? No — it genuinely depends on what's actually in the diff, which is exactly the shape [Chapter 1](../../tutorial/01-what-is-an-agent.md) calls an agent's job. A typo fix and an auth change need a genuinely different *set* of angles, and that set can't be known until you've actually looked at what changed.

But — and this is the part that answers Goal 3's real question — **the five-angle workflow itself doesn't need to be rebuilt.** It's already tested, already trusted, already correctly runs security/tests/style/data-access/docs checks with verification built in. The agent's job isn't to redo that work. It's to decide *which subset* of it applies, then hand off to the workflow you already have, exactly the way the workflow handed off to the skill it already had.

---

## The agent

The full, ready-to-run definition also lives at [`agent.md`](agent.md) in this folder.

```javascript
meta = {
  name: "adaptive-pr-review-agent",
  version: "1.0.0",
  goal: "Review this PR using only the angles that genuinely apply to " +
    "what it actually changes — grounded in the diff's real content, " +
    "not its file names.",
  tools: [
    { name: "read_full_diff", description: "Read the complete diff, " +
      "not just file names or a summary.", access: "READ_ONLY" },
    { name: "run_five_angle_review", description: "Runs the existing, " +
      "tested five-angle review workflow (security, tests, style, " +
      "data access, docs) for a given SUBSET of angles against the " +
      "diff. This is the same workflow from AI-Workflows Chapter 9 — " +
      "not reimplemented here.", access: "READ_ONLY" }
  ],
  max_iterations: 3
}
```

A real run: turn 1, `read_full_diff` on the typo-fix PR — one line, a doc comment, nothing else touched. `think()` decides, grounded in having actually read the content: only `docs` and `style` genuinely apply; `security`, `tests`, and `data access` have nothing in this diff that could possibly relate to them. Turn 2, `run_five_angle_review` is called with `angles: ["docs", "style"]` — the *same* underlying workflow from AI-Workflows, just invoked with a smaller angle set instead of always all five. `DONE`, with the workflow's own output as the evidence.

On the 600-line auth PR, turn 1's `read_full_diff` shows genuine touches across all five categories. The agent calls `run_five_angle_review` with all five angles — functionally identical to always running the fixed workflow, because for *this* PR, all five genuinely do apply. **The agent didn't change what a large, cross-cutting PR gets. It changed what a narrow, single-purpose PR gets.**

---

## What went wrong the first time

Rahul's first version decided which angles applied by looking at *file names and extensions* — `.css` files skip data-access and security, `.md` files skip everything but docs — without actually reading the diff's content. It worked on most PRs. Then it missed a real issue: a PR that looked frontend-only by its file paths (mostly `.tsx` files) also quietly modified a data-fetching hook to remove an authorization check. That's a genuine security issue, in a file whose extension gave no signal that it needed the security angle.

This is [Chapter 4](../../tutorial/04-tools-and-grounding.md)'s grounding lesson again, in its sharpest form yet: a scope decision based on file extensions is a plausible-sounding shortcut, not a grounded conclusion. The fix was making `read_full_diff` mandatory before any angle-selection decision, and requiring the agent's angle choice to cite *specific lines* of the diff as its reasoning — not the file list.

---

## How it was tested

Per [Chapter 7](../../tutorial/07-testing-and-iterating.md): the exact planted case above — a `.tsx`-only PR with a buried authorization removal — confirmed the fixed, content-grounded version correctly includes the security angle, where the file-extension-based first draft missed it. Also tested: a genuinely narrow PR (the typo fix) correctly runs only 2 of 5 angles, and a genuinely broad PR correctly runs all 5 — confirming the agent adapts in both directions, not just toward doing less.

---

## Where it sits on the sharing ladder

**Level 3 — Company-wide.** Entirely read-only — it decides scope and calls an existing, already-governed workflow, taking no action itself — so it clears [Chapter 9](../../tutorial/09-governance-and-capstone.md)'s approval-gate requirement without needing one. Its real cost is now variable per PR instead of fixed, and that's stated plainly in its own documentation. Small PRs cost a fraction of what the fixed five-angle workflow used to cost every time. Large ones cost exactly the same as before.

---

## References & assets

- **[`agent.md`](agent.md)** — the complete, real definition, including the guard requiring `read_full_diff` before any angle-selection decision. Copy it into your own agent tool, adapting syntax per the repo's [note on accuracy](../../README.md#a-note-on-accuracy).
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, showing the narrow-PR and broad-PR paths side by side.
- **Chapters used:** [Chapter 4](../../tutorial/04-tools-and-grounding.md) (grounding the scope decision in real content, not file names), [Chapter 6](../../tutorial/06-agents-vs-other-tools.md), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **The full thread this closes:** [AI-Skills `/code-review` skill](../../../AI-Skills/case-studies/04-code-review-skill/README.md) → [AI-Workflows five-angle workflow](../../../AI-Workflows/case-studies/04-code-review-workflow/README.md) → this agent. See [`docs/how-the-three-connect.md`](../../../docs/how-the-three-connect.md) for the complete trace.

---

## Where the story goes next

Rahul's skill became a stage in a workflow. That workflow's fixed five angles just became one agent's grounded, adaptive choice — the same underlying review logic, reused at every level, nothing thrown away at any step.

This is the last case study in the series. For the full picture of how Skills, Workflows, and Agents connect — the complete line from a single trigger description to an autonomous, tool-using investigation — see:

**[`docs/how-the-three-connect.md`](../../../docs/how-the-three-connect.md)**

---

← [Case Study 3 — QA](../03-qa-agent/README.md) · [All case studies](../README.md)
