# Flow Diagram — `discount-combination-explorer`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    INVOKE["Invoked with goal +\nboundary: staging only"] --> T1["think() picks a\ncombination to try"]
    T1 --> SIM["simulate_checkout —\nreal computed total"]
    SIM --> T2["think()"]
    T2 --> EXP["compute_expected_total —\nINDEPENDENT calculation,\nnot the same code path"]
    EXP --> CMP{"Do they\nagree?"}
    CMP -->|Yes| CONTINUE["No finding — try\nanother combination"]
    CMP -->|No| GROUNDCHECK{"BOTH tools\nactually called?"}
    GROUNDCHECK -->|No| REJECT["Rejected — need both\nbefore it counts"]
    GROUNDCHECK -->|Yes| DONE["DONE — genuine\nfinding, reproduced"]
```

See [`agent.md`](../agent.md) for the full loop, including the stricter grounding check requiring both tools before a finding counts — the direct fix for ["What went wrong the first time"](../README.md#what-went-wrong-the-first-time).

---

← [Back to case study](../README.md)
