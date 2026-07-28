# Flow Diagram — `endpoint-scaffold-test-document`

← [Back to case study](../README.md)

```mermaid
flowchart LR
    subgraph E1 ["Endpoint 1"]
        S1["Scaffold"] --> T1["Test"] --> D1["Document"]
    end
    subgraph E2 ["Endpoint 2"]
        S2["Scaffold"] --> T2["Test"] --> D2["Document"]
    end
    subgraph E3 ["Endpoint 3 (slow)"]
        S3["Scaffold"] --> T3["Test"] --> D3["Document"]
    end
```

No barrier anywhere in this diagram — endpoint 1 can reach `Document` while endpoint 3 is still on `Scaffold`. See [`workflow.md`](../workflow.md) for the real script, and compare this shape directly against [Case Study 1's](../../01-frontend-workflow/assets/flow-diagram.md) barrier to see [Chapter 4](../../../tutorial/04-parallel-vs-pipeline.md)'s core distinction in two real diagrams.

---

← [Back to case study](../README.md)
