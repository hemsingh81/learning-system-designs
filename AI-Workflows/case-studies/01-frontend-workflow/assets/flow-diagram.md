# Flow Diagram — `cross-size-component-check`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    RUN["Deliberately invoked\nwith component_code"] --> PH1["phase('Check')"]
    PH1 --> PAR["parallel([...]) —\n3 renders START\nat the same instant"]
    PAR --> D["desktop 1440px"]
    PAR --> T["tablet 768px"]
    PAR --> M["mobile 375px\n(+ below-fold check)"]
    D --> BAR["BARRIER —\nwait for all 3"]
    T --> BAR
    M --> BAR
    BAR --> PH2["phase('Combine')"]
    PH2 --> REPORT["One combined report —\nno size's issue hidden\nunder general commentary"]
```

See [`workflow.md`](../workflow.md) for the real script this diagram traces, and [AI-Workflows Chapter 10](../../../tutorial/10-lifecycle-of-execution.md) for how the barrier step actually behaves at runtime.

---

← [Back to case study](../README.md)
