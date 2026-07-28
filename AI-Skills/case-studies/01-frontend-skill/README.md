# Case Study 1 — Frontend: Accessibility Review

← [All case studies](../README.md) · Next: [Backend — API Scaffolding](../02-backend-skill/README.md)

Built by **Divya**, frontend engineer at Kestrel.

---

## The problem

Every new component at Kestrel gets a design review and a code review. Neither one reliably catches accessibility problems — missing alt text, bad colour contrast, form fields with no label, buttons a screen reader can't announce properly.

It's not that nobody cares. It's that accessibility review needs a specific checklist, applied every single time, and checklists that live only in people's heads get skipped when a deadline is close.

Divya has caught the same three or four mistakes, repeatedly, across different components, for months.

---

## The thought process

Divya runs this through [Chapter 6](../../tutorial/06-skills-vs-other-tools.md)'s decision framework before writing anything.

**Does this need to happen every time, with zero exceptions, no judgement call?** Not quite — a hook could run an automated accessibility scanner on every save, and Kestrel already has one for the most mechanical checks (missing `alt` attributes, for instance). But plenty of real accessibility problems need actual judgement — is this color contrast genuinely a problem *in context*, is this label actually clear to someone using a screen reader. A fixed hook can't make that call.

**Does this need a separate workspace?** No. Reviewing a component needs to see the component's actual code, which is already right there.

**Will Divya always remember to type an exact command?** Under deadline pressure, honestly, no — and that's exactly the kind of situation a skill is meant to cover, one that doesn't depend on someone remembering.

**Is it a repeated, recognisable request, phrased differently by different people?** Yes. Sometimes "review this for accessibility," sometimes "can a screen reader use this form," sometimes just "check this component before I open a PR."

Skill, then partly-hook. Divya keeps the existing automated scanner as the hook it already was, and builds a skill for the judgement-based checks the scanner can't make.

---

## The skill

The full file also lives at [`SKILL.md`](SKILL.md) in this folder — copy it directly into your own skills directory to use it as-is.

```markdown
---
name: kestrel-a11y-review
version: 1.0.0
description: Reviews a frontend component for accessibility problems
  that need human judgement — colour contrast in context, label
  clarity, screen reader announcement order, and focus management.
  Use when the user asks to check, review, or verify accessibility
  for a component, or asks if something is screen-reader friendly.
  Does NOT cover automated checks already caught by our lint rules
  (missing alt attributes, missing ARIA roles) — only flag those if
  you notice the automated check was somehow bypassed.
---

You are reviewing a frontend component at Kestrel for accessibility
problems that need real judgement, not just a fixed rule.

Read the component's actual code before saying anything. Do not
review from the component's name or description alone.

Check for, specifically:

1. COLOUR CONTRAST IN CONTEXT — not just "is there enough contrast",
   but "does this specific combination, in this specific component,
   actually read clearly". A technically-passing contrast ratio can
   still be a real problem on a small font or a thin element.

2. LABEL CLARITY — does every form field have a label a screen
   reader user could understand OUT OF CONTEXT, without seeing the
   surrounding layout? "Enter here" next to a visually-obvious field
   is not clear out of context. "Enter your billing postcode" is.

3. ANNOUNCEMENT ORDER — for anything with dynamic content (a modal
   opening, an error appearing), does the actual DOM order match the
   order a sighted user would naturally read it in? Screen readers
   generally follow DOM order, not visual position.

4. FOCUS MANAGEMENT — when a modal opens, does focus move into it?
   When it closes, does focus return to where it was? Missing focus
   management is one of the most common real-world accessibility
   failures, and automated scanners routinely miss it entirely.

For each issue found: quote the exact line, explain why it's a
problem IN PLAIN LANGUAGE (not just citing a WCAG rule number), and
give a specific fix — not just "improve this."

If you find nothing wrong, say so plainly. Do not invent minor
issues to seem thorough.
```

---

## What went wrong the first time

Divya's first draft of the instructions said: *"Check the component follows WCAG guidelines."*

It technically worked — but the output was nearly useless. It cited rule numbers ("fails WCAG 1.4.3") without explaining what that meant for the actual component in front of her, or what to change. She had to look up every rule number herself, which defeated the entire point of automating the review.

The fix was the "explain why it's a problem IN PLAIN LANGUAGE" instruction, plus "give a specific fix — not just 'improve this.'" This is the same lesson from [Chapter 3](../../tutorial/03-your-first-skill.md): vague instructions produce vague output, even when the underlying knowledge is technically correct.

---

## How it was tested

Trigger tests, following [Chapter 7](../../tutorial/07-testing-and-iterating.md)'s method:

| Should trigger | Result |
|---|---|
| "review this for accessibility" | ✅ |
| "can a screen reader use this form?" | ✅ |
| "check this before I open a PR" | ✅ |
| "is this component accessible?" | ✅ |
| "does this need any a11y fixes?" | ✅ |

| Should NOT trigger | Result |
|---|---|
| "why is accessibility important?" (general question, not a real review request) | ✅ correctly ignored |
| "fix the lint errors on this file" (a different, unrelated task) | ✅ correctly ignored |
| "make this button bigger" (a styling request, not a review) | ✅ correctly ignored |

Output testing, on three real components: a login form, a modal dialog, and a data table. The skill correctly found a real focus-management bug in the modal — focus wasn't returning to the trigger button on close — that had passed both a design review and a code review already. That single catch was the moment the rest of the frontend team asked to use it too.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Checked into the frontend repo, so every frontend engineer at Kestrel gets it automatically, the same way they get the lint config. It's specific to Kestrel's own component patterns and doesn't make sense outside this codebase, so it stays at Level 2 rather than becoming a company-wide package.

---

## References & assets

- **[`SKILL.md`](SKILL.md)** — the complete, real file. Copy it into your own skills directory to use it exactly as built here.
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, tracing a real request from trigger match through all four checks to the final report.
- **Chapters used:** [Chapter 3](../../tutorial/03-your-first-skill.md) (the vague-instructions fix), [Chapter 6](../../tutorial/06-skills-vs-other-tools.md) (the skill-vs-hook split), [Chapter 7](../../tutorial/07-testing-and-iterating.md) (trigger + output testing), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md) (what actually happens when this skill runs).
- **Where Divya's work goes next:** the same cross-size checking problem gets a genuinely different tool in [AI-Workflows Case Study 1](../../../AI-Workflows/case-studies/01-frontend-workflow/README.md) (parallel fan-out with a barrier), and an open-ended investigation version in [AI-Agents Case Study 1](../../../AI-Agents/case-studies/01-frontend-agent/README.md) (explore, narrow, confirm).

---

← [All case studies](../README.md) · Next: [Backend — API Scaffolding](../02-backend-skill/README.md)
