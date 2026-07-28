# Flow Diagram — `adaptive-pr-review-agent`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    INVOKE["Invoked with goal:\nreview using only\napplicable angles"] --> T1["Turn 1:\nread_full_diff\n(mandatory first)"]
    T1 --> SCOPE["think() decides scope,\ngrounded in actual\ndiff content, not\nfile extensions"]
    SCOPE --> NARROW{"Genuinely\nnarrow PR?"}
    NARROW -->|"Yes — typo fix"| SMALL["run_five_angle_review\nwith 2 angles\n(docs, style)"]
    NARROW -->|"No — auth PR"| FULL["run_five_angle_review\nwith all 5 angles"]
    SMALL --> DONE["DONE — workflow's\noutput returned as\nevidence"]
    FULL --> DONE
```

See [`agent.md`](../agent.md) for the full loop, including the guard that rejects any angle-selection decision made before `read_full_diff` actually ran — the direct fix for the file-extension near-miss in ["What went wrong the first time"](../README.md#what-went-wrong-the-first-time).

---

← [Back to case study](../README.md)
