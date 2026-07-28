# Flow Diagram — `multi-angle-test-case-generation`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    RUN["Invoked with\nfeature_spec"] --> PH1["phase('Generate')"]
    PH1 --> PAR["parallel([...]) —\n4 angles at once"]
    PAR --> B["Boundary"]
    PAR --> I["Invalid input"]
    PAR --> C["Concurrency"]
    PAR --> P["Permissions"]
    B --> RAW["raw_cases —\nBARRIER, wait for all 4"]
    I --> RAW
    C --> RAW
    P --> RAW
    RAW --> PH2["phase('Verify')"]
    PH2 --> PIPE["pipeline(cases, verify) —\neach case verified\nindependently, no barrier"]
    PIPE --> V{"Fresh agent call:\nfind a reason this is\nSHALLOW"}
    V -->|GENUINE| KEEP["Kept in final suite"]
    V -->|SHALLOW| DROP["Discarded"]
```

See [`workflow.md`](../workflow.md) for the real script, and [the case study](../README.md#what-went-wrong-the-first-time) for why the `V` step's exact wording — "find a reason this is SHALLOW," not "confirm this is good" — is what actually catches the false-coverage risk.

---

← [Back to case study](../README.md)
