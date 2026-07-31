# Postmortem exercise — write it up like a real incident

You've now run all three variants of the incident-triage capstone. This
exercise asks you to write a POSTMORTEM the way a backend team would
after a real incident — using the case study's own output as your source
material. This is the "for real, describe it" step; nothing here is
graded automatically, so be honest with yourself about the gaps.

## Step 1 — run all three variants and capture the output

```powershell
.\scripts\run-example.ps1 15_case_study_incident_triage
```

Save the full console output (or re-run inside PowerShell and copy it) —
you'll quote from it in your writeup.

## Step 2 — write a one-page postmortem for the `easy` variant

Structure it like a real incident report:
- **Summary**: one sentence, what happened and what was concluded.
- **Timeline**: when the anomaly started (`02:14`), when it was detected
  (attempt 1), when it was resolved (approved for restart).
- **Root cause**: quote the exact evidence cited (the log line).
- **Action taken**: quote the escalation outcome (`action_approved`).
- **What went well**: (hint — one investigation pass was enough; why?)

## Step 3 — write a one-page postmortem for the `ambiguous` variant

Same structure, but add a **What required a second look** section:
- What did attempt 1 conclude, and why did the Critic reject it? Quote
  `verdict.missing` from `_script_ambiguous`.
- What changed in attempt 2 (the broader `search_logs` query) that
  produced a satisfying answer?
- If this had been a REAL model instead of scripted, what tells you the
  broader search was the right move rather than luck? (Hint: look at
  `context_notes` passed into the second `Planner.make_plan` call.)

## Step 4 — write a one-page postmortem for the `trap` variant, as a NEAR-MISS report

This is the important one. A near-miss report documents something that
did NOT go wrong, on purpose, because a safeguard caught it. Structure:
- **What could have gone wrong**: describe the tempting-but-wrong
  conclusion (checkout's deploy caused a payments incident) that the
  system did NOT commit to.
- **What safeguard caught it**: name it specifically — the Critic's
  `success_criteria` checking "for the PAYMENTS service specifically",
  and the escalation gate refusing to auto-approve any action.
- **What would have happened WITHOUT that safeguard**: if the Critic had
  accepted the checkout-based explanation, what real-world action might
  have been taken on the WRONG service? (Hint: `restart_service` on
  `checkout` would do nothing for a real payments incident, and might
  even cause a second, unrelated outage.)

## Step 5 — the hard question

In your own words (3-5 sentences): **is two investigation attempts
(`max_attempts=2`) the right number for a real production system?** Argue
both sides — what breaks if it's too few, what breaks if it's too many —
referencing `tutorial/05-case-study/DECISIONS.md`'s D-504. There's no
single correct answer here; the point is to practice the same tradeoff
reasoning this whole project has modeled in every `DECISIONS.md` file.

## Checkpoint

You're done when you have three short postmortems and one paragraph
answering Step 5. If you can write these without re-reading the source
code, you've genuinely internalized what Goal → Plan → Critic → Escalation
does and why — which is the actual goal of Milestone 8.
