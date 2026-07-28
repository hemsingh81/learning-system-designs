# Flow Diagram — `kestrel-code-review`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    REQ["\"review this PR\""] --> MATCH{"Matches\nkestrel-code-review\ndescription?"}
    MATCH -->|Yes| LOAD["SKILL.md loads"]
    LOAD --> READPOLICY["Read review-standards.md\nIN FULL first —\nnever from memory"]
    READPOLICY --> CHECK["Check diff against\nevery numbered rule"]
    CHECK --> SEV["Group by severity:\nMUST FIX / SHOULD FIX /\nCONSIDER"]
    SEV --> STALE{"review-standards.md newer\nthan this SKILL.md's\nown version?"}
    STALE -->|Yes| WARN["Warn: standards may\nhave changed since\nlast review"]
    STALE -->|No| REPORT
    WARN --> REPORT["Report findings —\nNEVER approve or merge"]
```

See [SKILL.md](../SKILL.md) (the instructions) and [review-standards.md](../review-standards.md) (the actual policy, kept as a separate file for exactly the reason explained in ["What went wrong the first time"](../README.md#what-went-wrong-the-first-time)).

---

← [Back to case study](../README.md)
