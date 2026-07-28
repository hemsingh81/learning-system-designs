# Kestrel Code Review Standards

The real policy `kestrel-code-review` reads before every review. Owned by the
tech-lead group, not by whoever maintains the skill — see the case study's
["What went wrong the first time"](README.md#what-went-wrong-the-first-time)
for why that separation matters.

---

## 1. Error handling
Every external call (database, API, file system) must be wrapped with
explicit error handling. Silent failures are not acceptable — every caught
error must be logged or surfaced, not swallowed.

## 2. Documentation
Every exported function needs a doc comment stating what it does, its
parameters, and what it returns. Internal (non-exported) functions do not
require this.

## 3. Data access
Database queries must go through the repository layer. Never query the
database directly from a route handler or a frontend component. **Exception**
(added after the caching-layer incident in "What went wrong the first time"):
a read-through cache wrapper may query the database directly, provided it
lives in `src/cache/` and exposes only a repository-shaped interface to
everything else.

## 4. Testing
Every new function with a conditional (an if/else, a switch) needs at least
one test per branch. A function with no conditionals needs at least one
happy-path test.

## 5. Naming
Boolean variables and functions start with is/has/can/should (`isValid`,
`hasPermission`) — never a bare noun or verb.

## 6. Secrets
No credential, API key, or token may appear as a literal string anywhere in
a diff, including in a test fixture or a commented-out line. Use the secrets
manager, always.

## 7. Logging
Never log a full request or response body for an endpoint that handles
payment or authentication data. Log identifiers (user ID, order ID) instead
of the payload itself.

## 8. Migrations
A database migration that changes an existing column's type or drops a
column needs a written rollback plan in the PR description, not just the
migration file itself.

## 9. Dependencies
A new third-party package needs a one-line justification in the PR
description: what it does, and why an existing dependency couldn't do it.

## 10. Feature flags
Code behind a feature flag must have the flag's default state (on/off)
stated explicitly in the PR description — "flag defaults to off in
production" or equivalent. A PR that adds a flag with no stated default is a
MUST FIX, not a CONSIDER, because it's exactly the kind of thing that causes
an accidental production rollout.
