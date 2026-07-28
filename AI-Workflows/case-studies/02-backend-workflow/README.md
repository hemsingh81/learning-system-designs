# Case Study 2 — Backend: Scaffold, Test, Document

← [Case Study 1 — Frontend](../01-frontend-workflow/README.md) · [All case studies](../README.md) · Next: [QA — Fan-Out and Verify](../03-qa-workflow/README.md)

Built by **Vikram**, backend engineer at Kestrel. Pattern: **pipeline with overlapping stages.**

---

## The problem

Vikram's team ships new API endpoints in batches — a sprint might add 6 new endpoints to the orders service. Each endpoint needs three things done to it. A scaffold (route, handler stub, request/response types). A test file (happy path plus at least 2 edge cases). A docs entry (the internal API reference).

Doing this one endpoint at a time, start to finish, before moving to the next, is correct but slow. Endpoint 2 sits completely idle while endpoint 1 is being documented, even though nothing about endpoint 2's scaffold depends on endpoint 1 finishing anything.

---

## The thought process

This is the textbook shape from [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md): three real stages (scaffold → test → document), each one needing the previous stage's *own* output. But there's **no reason for endpoint 2 to wait for endpoint 1 to clear all three stages** before starting its own scaffold.

Vikram checked Step 2 of the [phase-planning checklist](../../templates/phase-planning-checklist.md) honestly: does the document stage need ALL endpoints' test results together before it can start? No — each endpoint's docs entry only needs *that endpoint's* own test results, nothing from the others. That's a clean pipeline, not a barrier.

---

## The workflow

```javascript
meta = {
  name: "endpoint-scaffold-test-document",
  version: "1.0.0",
  description: "Pipelines new endpoints through scaffold, test, and " +
    "documentation stages, letting different endpoints be at different " +
    "stages at the same time.",
  phases: [
    { title: "Scaffold" },
    { title: "Test" },
    { title: "Document" }
  ]
}

// Each endpoint flows through all 3 stages independently — no barrier
// between stages. Endpoint 3 can be scaffolding while endpoint 1 is
// already being documented.
results = pipeline(
  new_endpoints,

  (endpoint) => {
    phase("Scaffold")
    return agent("Scaffold a route, handler stub, and request/response " +
      "types for: " + endpoint.spec)
  },

  (scaffold, endpoint) => {
    phase("Test")
    return agent("Write a test file for this scaffold: " + scaffold +
      ". Cover the happy path plus at least 2 edge cases. " +
      "Spec: " + endpoint.spec)
  },

  (tests, endpoint) => {
    phase("Document")
    return agent("Write an internal API reference entry for this " +
      "endpoint, using the scaffold and its tests as the source of " +
      "truth for request/response shape: " + endpoint.spec)
  }
)

return results
```

Notice each stage callback receives `(previousResult, endpoint, index)`. That second argument, per [Chapter 2](../../tutorial/02-anatomy-of-a-workflow.md), is how the document stage still knows which endpoint's spec it's writing about — without needing the scaffold stage to carry that information forward by hand.

---

## What went wrong the first time

Vikram's first draft used `parallel()` around each stage instead of `pipeline()`. Run all 6 scaffolds, wait for all 6. Run all 6 tests, wait for all 6. Then run all 6 docs. It worked, but every endpoint's test stage was blocked waiting on the *slowest* endpoint's scaffold, even though nothing about it actually needed to wait.

This is the exact **unearned barrier** mistake from [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md) — three genuinely separate stages, run with a barrier between them that nothing in the task actually required. Switching to `pipeline()` let fast endpoints reach the document stage while slow ones were still being scaffolded, with zero change to what each stage actually does.

---

## How it was tested

Structural test: 6 endpoints, one deliberately given a large, slow-to-scaffold spec. Confirmed the other 5 reached their document stage well before the slow one finished its scaffold — proof the pipeline genuinely overlaps, per [Chapter 7](../../tutorial/07-testing-and-iterating.md).

Output testing on a real sprint batch of 6 endpoints. One real gap surfaced. The docs stage, for one endpoint, wrote a request shape that didn't match what the test file actually exercised — a genuine bug in the docs stage's instructions, not the pipeline shape. Vikram fixed it by telling the docs stage explicitly to use the test file's actual request payloads as its source, rather than re-describing the scaffold from memory.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Checked into the backend repo. Vikram's team runs this every time a sprint adds new endpoints in a batch.

---

← [Case Study 1 — Frontend](../01-frontend-workflow/README.md) · [All case studies](../README.md) · Next: [QA — Fan-Out and Verify](../03-qa-workflow/README.md)
