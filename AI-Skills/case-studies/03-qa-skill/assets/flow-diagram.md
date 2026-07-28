# Flow Diagram — `kestrel-test-case-gen`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    REQ["\"write test cases\nfor this story\""] --> MATCH{"Matches\nkestrel-test-case-gen\ndescription?"}
    MATCH -->|Yes| LOAD["SKILL.md loads"]
    LOAD --> GEN["Generate cases across\n5 fixed categories"]
    GEN --> EXP{"Expected result\nspecific enough to\ncheck pass/fail?"}
    EXP -->|No| REJECT["Rewrite until it is —\nnever accept\n'works correctly'"]
    REJECT --> EXP
    EXP -->|Yes| SPEC{"Story specifies\nthis edge case?"}
    SPEC -->|No| FLAG["Flag as OPEN QUESTION —\nnever invent an answer"]
    SPEC -->|Yes| CASE["Add as a real,\ntestable case"]
    FLAG --> OUT["Final list: real cases\n+ open questions"]
    CASE --> OUT
```

The `EXP` and `SPEC` checks are the actual fix from ["What went wrong the first time"](../README.md#what-went-wrong-the-first-time--and-why-it-mattered-more-here) — see [SKILL.md](../SKILL.md) for the instructions that enforce them.

---

← [Back to case study](../README.md)
