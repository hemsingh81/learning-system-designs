# Case Study 2 — Backend: API Endpoint Scaffolding

← [Frontend](../01-frontend-skill/README.md) · [All case studies](../README.md) · Next: [QA — Test Case Generation](../03-qa-skill/README.md)

Built by **Vikram**, senior backend engineer at Kestrel.

---

## The problem

Every new API endpoint at Kestrel follows the same layered structure: a route, a service, a repository, and a test file, each in a specific folder, each following a specific naming pattern. Vikram has explained this structure to every new backend hire, individually, for two years.

New endpoints still show up inconsistent. Someone puts business logic directly in the route handler. Someone forgets the repository layer entirely and queries the database straight from the service. It's not that the convention is unclear once you know it — it's that everyone starts a new endpoint by copying whichever old one happens to be open in their editor, and old endpoints don't all follow the current convention either.

---

## The thought process

Through [Chapter 6](../../tutorial/06-skills-vs-other-tools.md)'s framework:

**Fixed rule, no exceptions?** No — endpoints genuinely vary. A read-only endpoint doesn't need the same shape as one that writes data. Judgement is needed.

**Separate workspace?** No — scaffolding needs to see where similar endpoints already live in the actual repo, which is already visible.

**Vikram typing an exact command every time?** He'd remember. New hires, in their first month, would not — and they're exactly who benefits most from this.

**Repeated, recognisable, phrased differently?** Yes — "add a new endpoint for X," "scaffold the files for Y," "I need to add a route for Z."

Skill.

---

## The skill

The full file also lives at [`SKILL.md`](SKILL.md), with its bundled script at [`scripts/validate-scaffold.sh`](scripts/validate-scaffold.sh) — copy the whole folder into your own skills directory to use it as-is.

```markdown
---
name: kestrel-api-scaffold
version: 1.0.0
description: Scaffolds the files for a new API endpoint following
  Kestrel's layered structure (route, service, repository, test).
  Use when the user asks to add, create, or scaffold a new API
  endpoint or route. Does NOT cover modifying an EXISTING endpoint —
  only creating a new one.
---

You are scaffolding a new API endpoint for Kestrel's backend, which
follows a strict layered structure. Every endpoint needs all four of
these, even for something simple:

1. ROUTE (src/routes/) — HTTP method, path, and validation only.
   NO business logic here. It calls the service and returns the
   result.

2. SERVICE (src/services/) — the actual business logic. This is
   where rules live: what's allowed, what's not, what happens on
   success or failure. It calls the repository for any data access —
   it never touches the database directly.

3. REPOSITORY (src/repositories/) — data access only. Queries,
   inserts, updates. NO business logic here — just "get this data"
   or "save this data."

4. TEST (tests/) — at minimum, one test for the happy path and one
   for the most likely failure case (bad input, not found, or a
   conflict, depending on what the endpoint does).

Before writing anything:
- Look at 2 existing endpoints in the same area of the codebase, to
  match naming conventions and see how similar logic is structured.
- Ask the user what the endpoint should actually do, if it's not
  already clear from their request — do not guess at business rules.

After scaffolding all four files, run
`scripts/validate-scaffold.sh <endpoint-name>` to confirm nothing
was missed, and report its output to the user.
```

```bash
#!/bin/bash
# scripts/validate-scaffold.sh
# Checks that a newly scaffolded endpoint has all four required
# layers. Takes the endpoint name as an argument.

NAME=$1
MISSING=()

[ -f "src/routes/${NAME}.ts" ]      || MISSING+=("route")
[ -f "src/services/${NAME}.ts" ]    || MISSING+=("service")
[ -f "src/repositories/${NAME}.ts" ] || MISSING+=("repository")
[ -f "tests/${NAME}.test.ts" ]      || MISSING+=("test")

if [ ${#MISSING[@]} -eq 0 ]; then
  echo "All 4 layers present for '${NAME}'."
  exit 0
else
  echo "Missing layers for '${NAME}':"
  printf '  - %s\n' "${MISSING[@]}"
  exit 1
fi
```

---

## What went wrong the first time

Vikram's first draft didn't include "look at 2 existing endpoints... to match naming conventions." Without it, the skill produced technically-correct files that used slightly different naming than the rest of the codebase — `getUserById` in one file, `fetchUserById` in the file it called. Functionally fine. Inconsistent in a way that made the codebase harder to search and navigate.

This is the same lesson as Chapter 5's environment check: **don't let the skill work from assumption when it can check the real, current state of the actual codebase instead.** Looking at real neighbouring examples, instead of generating from a general pattern in isolation, fixed it.

He also added the validation script late — his first version just trusted the instructions to produce all four files, which mostly worked, until one test run quietly skipped the repository file because the request had been phrased as "add a quick endpoint for X" and the model treated "quick" as license to skip a layer. The script now catches that every time, instead of relying on the instructions alone to never slip.

---

## How it was tested

| Should trigger | Result |
|---|---|
| "add a new endpoint for fetching order history" | ✅ |
| "scaffold the files for a delete-user route" | ✅ |
| "I need to add a route for updating preferences" | ✅ |
| "create an endpoint that lists active sessions" | ✅ |
| "set up a new API route for password reset" | ✅ |

| Should NOT trigger | Result |
|---|---|
| "why do we split routes and services?" (a question, not a build request) | ✅ correctly ignored |
| "fix the bug in the existing login endpoint" (modifying, not creating) | ✅ correctly ignored |
| "add a new column to the users table" (a schema change, not an endpoint) | ✅ correctly ignored |

Output testing on 3 different endpoint types — a simple read, a write with validation, and one requiring a new database query — confirmed all four layers were generated correctly each time, and `validate-scaffold.sh` correctly caught a missing test file when Vikram deliberately asked for "just the route quickly" as a stress test.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Checked into the backend repo. It encodes Kestrel's own specific layered structure, so it wouldn't transfer meaningfully to a team using a different backend architecture — Level 2 is the right, and final, home for it.

---

## References & assets

- **[`SKILL.md`](SKILL.md)** + **[`scripts/validate-scaffold.sh`](scripts/validate-scaffold.sh)** — the complete, real files. Copy the whole folder into your own skills directory to use it exactly as built here.
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, including the validation-script branch that catches a silently-skipped layer.
- **Chapters used:** [Chapter 5](../../tutorial/05-tools-and-scripts.md) (bundling a real script), [Chapter 6](../../tutorial/06-skills-vs-other-tools.md), [Chapter 7](../../tutorial/07-testing-and-iterating.md), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **Where Vikram's work goes next:** the same layered-structure problem becomes a genuinely different shape in [AI-Workflows Case Study 2](../../../AI-Workflows/case-studies/02-backend-workflow/README.md) (pipeline with overlapping stages, scaffold → test → document), and an open-ended diagnosis in [AI-Agents Case Study 2](../../../AI-Agents/case-studies/02-backend-agent/README.md) (hypothesize, test, revise).

---

← [Frontend](../01-frontend-skill/README.md) · [All case studies](../README.md) · Next: [QA — Test Case Generation](../03-qa-skill/README.md)
