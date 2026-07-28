# Flow Diagram — `chart-overlap-investigator`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    INVOKE["Invoked with goal:\nfind the legend-overlap cause"] --> T1["Turn 1: think()"]
    T1 --> CODE["read_component_code —\nlegend width capped by\nlongest label"]
    CODE --> T2["Turn 2: think()"]
    T2 --> SHAPE["fetch_customer_data_shape —\nfinds a 40-char label,\npast the cap"]
    SHAPE --> T3["Turn 3: think()"]
    T3 --> RENDER["render_with_data —\nconfirms overlap on\nthat exact customer"]
    RENDER --> GROUND{"Real evidence\ncited?"}
    GROUND -->|Yes| DONE["DONE — grounded\nconclusion returned"]
```

A real run resolves in 3 turns when the label-length theory is right on the first try — see [`agent.md`](../agent.md) for the full loop, and [the case study](../README.md#what-went-wrong-the-first-time) for the run that instead ends in an honest `EXHAUSTED` on a cause this agent's tools can't see.

---

← [Back to case study](../README.md)
