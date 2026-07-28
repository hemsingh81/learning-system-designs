# Flow Diagram — `flaky-test-triage-agent`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    INVOKE["Invoked with goal:\nfind the real flaky-test cause"] --> T1["Turn 1:\nrun_test_isolated"]
    T1 --> RESULT1{"Still fails\nalone?"}
    RESULT1 -->|Yes| RULEOUT["Rules out BOTH\nordering AND shared-fixture\nin one step"]
    RULEOUT --> T2["Turn 2:\nread_test_code"]
    T2 --> FOUND["Finds a timestamp\nassertion with no\nclock-drift tolerance"]
    FOUND --> T3["Turn 3:\nrun_test_n_times"]
    T3 --> CONFIRM["Failure rate rises\nunder load — confirms\ntiming-sensitivity theory"]
    CONFIRM --> DONE["DONE — root cause +\nproposed fix (human\nreview required)"]
```

See [`agent.md`](../agent.md) for the full loop. Note the agent proposes a fix but never applies one — see [the case study](../README.md#what-went-wrong-the-first-time) for why the first draft's auto-edit tool was removed.

---

← [Back to case study](../README.md)
