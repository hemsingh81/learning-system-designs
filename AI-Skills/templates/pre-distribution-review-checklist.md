# Pre-Distribution Review Checklist

← [Back to README](../README.md) · See it explained: [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md)

Run this before any skill moves beyond Level 1 (personal) sharing — see [Chapter 8](../tutorial/08-packaging-and-sharing.md) for the three levels. Ten minutes, every time, no exceptions. Skipping it "just this once" is exactly how the near-miss in Chapter 9 almost happened.

---

## Part 1 — What kind of risk does this skill carry?

Answer these first. They decide how strict the rest of the review needs to be.

- [ ] **Can this skill only produce text, or can it actually take an action?**
  - Text only → lower risk, move through the rest of this checklist quickly.
  - Can act (write, delete, send, call an external service) → every remaining box matters more. Slow down.

- [ ] **If it acts, is that action reversible?**
  - Reversible (e.g., writing a file you can edit again) → real risk, but recoverable.
  - Not reversible (e.g., deleting something, sending a message externally) → this skill **must** have a human-confirmation step before the irreversible part happens. No exceptions.

- [ ] **Does it ever touch secrets, credentials, or personal data?**
  - If yes: confirm it only checks *whether* something exists or is valid — never reports the actual value. (See `check-env.sh` in [Chapter 5](../tutorial/05-tools-and-scripts.md) for the correct pattern.)

---

## Part 2 — Has it actually been checked, not just built?

- [ ] **Has someone other than the author read the full instructions?** Not skimmed — actually read, the way a code reviewer reads a diff.
- [ ] **Does the description honestly match what the instructions do?** Read the description alone, predict what it does, then check the instructions against that prediction. (The three-step habit from [Chapter 2](../tutorial/02-anatomy-of-a-skill.md).)
- [ ] **Has it been through trigger testing** — 5 "should trigger" and 3 "should not trigger" phrasings, run more than once each? ([Chapter 4](../tutorial/04-writing-trigger-descriptions.md) and [Chapter 7](../tutorial/07-testing-and-iterating.md))
- [ ] **Has it been through output testing** on at least 3 different real inputs, checked line-by-line against the actual rules — not just "it looked right"? ([Chapter 7](../tutorial/07-testing-and-iterating.md))

---

## Part 3 — Is it packaged properly?

- [ ] **Does it have a real version number**, following the MAJOR.MINOR.PATCH idea from [Chapter 8](../tutorial/08-packaging-and-sharing.md)?
- [ ] **Is there a changelog entry** explaining what changed and why — not just what?
- [ ] **Have you honestly picked the right sharing level** for what this skill actually is — not further than the evidence supports?

---

## Part 4 — For anything that acts and can't be undone

If you checked "not reversible" in Part 1, these are not optional.

- [ ] **Is there an explicit instruction telling the skill NOT to act automatically** on the irreversible step — to list candidates and wait for confirmation instead?
- [ ] **Does the confirmation step show the human real evidence**, not just "trust me" — the actual data the decision is based on?
- [ ] **Has at least one reviewer tried to think of a case where the skill's judgement could reasonably go wrong** — not just confirmed it works on the obvious case?

---

## The honest outcome

If anything in Part 1 or Part 4 is unresolved, **this skill is not ready for Level 2 or Level 3 sharing.** Fix it, then run the checklist again from the top — don't just re-check the box that failed.

If everything passes: you have real evidence, not a feeling, that this skill is ready. Move it to the sharing level from [Chapter 8](../tutorial/08-packaging-and-sharing.md) that actually fits.

---

← [Back to README](../README.md) · Full context: [Chapter 9](../tutorial/09-governance-and-capstone.md)
