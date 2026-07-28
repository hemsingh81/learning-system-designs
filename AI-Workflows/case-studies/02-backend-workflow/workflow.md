# `endpoint-scaffold-test-document` — real, runnable workflow

← [Back to case study](README.md)

Copy the script below into your own workflow tool, adapting syntax as needed per the [note on accuracy](../../README.md#a-note-on-accuracy). The pipeline shape — one endpoint flowing through all three stages independently — is ready to use as-is.

**Inputs this workflow expects:** `new_endpoints` (an array of `{ spec }` objects, one per endpoint to scaffold).
**Typical cost:** 3 pipeline stages × however many endpoints — no barrier, so cost scales linearly, not by the slowest endpoint.

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

---

← [Back to case study](README.md)
