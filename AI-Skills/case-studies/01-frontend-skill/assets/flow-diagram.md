# Flow Diagram — `kestrel-a11y-review`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    REQ["\"review this for accessibility\""] --> MATCH{"Matches\nkestrel-a11y-review\ndescription?"}
    MATCH -->|Yes| LOAD["SKILL.md loads"]
    LOAD --> READ["Read the component's\nactual code"]
    READ --> C1["Check 1:\nColour contrast\nIN CONTEXT"]
    READ --> C2["Check 2:\nLabel clarity\nout of context"]
    READ --> C3["Check 3:\nAnnouncement order\nvs. DOM order"]
    READ --> C4["Check 4:\nFocus management\non open/close"]
    C1 --> REPORT["For each issue:\nquote line + plain-language\nreason + specific fix"]
    C2 --> REPORT
    C3 --> REPORT
    C4 --> REPORT
    REPORT --> CLEAN{"Nothing found?"}
    CLEAN -->|Yes| SAYSO["Say so plainly —\nno invented issues"]
    CLEAN -->|No| DONE["Findings returned"]
```

See [SKILL.md](../SKILL.md) for the real instructions this diagram traces, and [the full lifecycle chapter](../../../tutorial/10-lifecycle-of-execution.md) for how the MATCH step works underneath.

---

← [Back to case study](../README.md)
