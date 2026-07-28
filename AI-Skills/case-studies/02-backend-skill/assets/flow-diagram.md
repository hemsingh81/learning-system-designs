# Flow Diagram — `kestrel-api-scaffold`

← [Back to case study](../README.md)

```mermaid
flowchart TD
    REQ["\"scaffold a new endpoint\nfor X\""] --> MATCH{"Matches\nkestrel-api-scaffold\ndescription?"}
    MATCH -->|Yes| LOAD["SKILL.md loads"]
    LOAD --> LOOK["Look at 2 existing\nendpoints for naming\nconventions"]
    LOOK --> ASK{"Business rules\nclear from request?"}
    ASK -->|No| CLARIFY["Ask the user —\nnever guess"]
    ASK -->|Yes| WRITE
    CLARIFY --> WRITE["Write all 4 layers:\nroute, service,\nrepository, test"]
    WRITE --> VALIDATE["Run\nscripts/validate-scaffold.sh"]
    VALIDATE --> CHECK{"All 4 files\npresent?"}
    CHECK -->|Yes| PASS["Report: all 4\nlayers present"]
    CHECK -->|No| FAIL["Report: which\nlayer(s) missing"]
```

See [SKILL.md](../SKILL.md) and [scripts/validate-scaffold.sh](../scripts/validate-scaffold.sh) for the real files this diagram traces.

---

← [Back to case study](../README.md)
