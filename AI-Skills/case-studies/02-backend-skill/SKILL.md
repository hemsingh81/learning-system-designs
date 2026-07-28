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
