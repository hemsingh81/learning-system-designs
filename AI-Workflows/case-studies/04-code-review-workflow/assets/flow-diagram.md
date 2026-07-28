# Flow Diagram — `pr-five-angle-review` v1.1.0

← [Back to case study](../README.md)

```mermaid
flowchart TD
    RUN["Invoked with diff"] --> PH1["phase('Review')"]
    PH1 --> PAR["parallel([...]) —\n5 angles at once"]
    PAR --> SEC["Security"]
    PAR --> TEST["Tests"]
    PAR --> STYLE["Style —\nrun_skill('/code-review')\n(AI-Skills Case Study 4)"]
    PAR --> DATA["Data access"]
    PAR --> DOCS["Docs"]
    SEC --> RAW["BARRIER —\nwait for all 5"]
    TEST --> RAW
    STYLE --> RAW
    DATA --> RAW
    DOCS --> RAW
    RAW --> PH2["phase('Verify')"]
    PH2 --> PIPE["pipeline(findings, verify) —\neach finding checked\nindependently"]
    PIPE --> V{"Fresh agent call:\nfind a reason this\nis WRONG"}
    V -->|CONFIRMED| PR["Reaches the PR"]
    V -->|REJECTED| DROP["Discarded"]

    style STYLE fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
```

The `STYLE` box is the literal, diagrammed proof of this case study's whole point — see [`workflow.md`](../workflow.md) for the real script, and [AI-Skills Case Study 4](../../../../AI-Skills/case-studies/04-code-review-skill/README.md) for the skill it calls.

---

← [Back to case study](../README.md)
