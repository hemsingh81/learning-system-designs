# Diagram Set

Ten diagrams, one visual language.

**Three formats, on purpose:**
- **Mermaid** (this file) — GitHub renders it natively, so it stays editable and version-controlled. No build step, no stale exports.
- **SVG** (`../images/svg/`) — hand-authored, dark, high-contrast. Crisp at any zoom, renders inline in the README.
- **PNG** (`../images/png/`) — 1600×900 exports of the SVGs. LinkedIn does not accept SVG uploads, so these are the files you actually post.

All image files live in one place: `MicroServices/images/`. Nothing else in the repo stores an image.

Regenerate the PNGs after editing any SVG. Run this from the `MicroServices` folder:

```bash
pip install cairosvg
python -c "
import cairosvg, glob, os
for f in glob.glob('images/svg/*.svg'):
    cairosvg.svg2png(url=f, write_to='images/png/'+os.path.basename(f)[:-4]+'.png',
                     output_width=1600, output_height=900, background_color='#0F1620')
"
```

## Colour semantics

The palette carries meaning and is identical across every diagram and both formats:

| Colour | Meaning |
|---|---|
| 🟠 Amber `#FF7A45` | **Synchronous** — caller blocked, hot path |
| 🟢 Green `#3DDC97` | **Asynchronous** — decoupled, event-driven |
| 🔵 Blue `#6C8EF5` | **North-south** — edge, external, client-facing |
| 🔴 Red `#F45B69` | **Failure path** — compensation, retry, dead-letter |
| 🟣 Purple `#B980F0` | **Abstraction layer** — Dapr, service mesh, anything sitting over a transport |
| ⚪ Slate `#8FA3B5` | Infrastructure, storage, neutral |

One deliberate exception: **D4** uses tool-identity colours instead, because every option on that diagram is asynchronous — colouring them all green would carry no information. It says so on the diagram itself.

Monospace is reserved for identifiers — service names, message names, topics. Sans-serif for everything a human wrote. Once you know the code, you can read any diagram in the set without a legend.

---

## D1 — The communication landscape
*Section 1. Hero SVG: [`images/svg/d1-landscape.svg`](../images/svg/d1-landscape.svg)*

![The communication landscape](../images/svg/d1-landscape.svg)

*[PNG for LinkedIn](../images/png/d1-landscape.png)*

```mermaid
flowchart LR
    subgraph OUT [" Outside "]
        WEB["Web app"]
        MOB["Mobile app"]
        PTR["Partner system"]
    end

    subgraph SYS [" Your system "]
        GW["API Gateway"]
        ORD["Ordering"]
        INV["Inventory"]
        PAY["Payments"]
        NOT["Notifications"]
        BRK[("Broker")]
    end

    WEB -->|north-south| GW
    MOB -->|north-south| GW
    PTR -->|webhook| GW
    GW --> ORD
    ORD -->|east-west sync| INV
    ORD -->|east-west async| BRK
    BRK --> PAY
    BRK --> NOT
    NOT -.->|push| WEB

    classDef ns fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
    classDef sync fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    classDef async fill:#122B22,stroke:#3DDC97,color:#E8EEF4
    class WEB,MOB,PTR,GW ns
    class ORD,INV sync
    class PAY,NOT,BRK async
```

---

## D2 — Synchronous vs asynchronous
*Section 2. Hero SVG: [`images/svg/d2-sync-vs-async.svg`](../images/svg/d2-sync-vs-async.svg)*

![Synchronous vs asynchronous](../images/svg/d2-sync-vs-async.svg)

*[PNG for LinkedIn](../images/png/d2-sync-vs-async.png)*

**Synchronous — the caller waits, and inherits every downstream delay**

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant O as Ordering
    participant I as Inventory
    participant P as Payments

    C->>O: POST /orders
    activate O
    O->>I: reserve stock
    activate I
    I-->>O: reserved
    deactivate I
    O->>P: charge card
    activate P
    Note over P: 4s under load
    P-->>O: approved
    deactivate P
    O-->>C: 201 Created
    deactivate O
    Note over C,P: Total latency = sum of every hop.<br/>Any hop down = request fails.
```

**Asynchronous — the caller commits and leaves**

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant O as Ordering
    participant B as Broker
    participant P as Payments
    participant N as Notifications

    C->>O: POST /orders
    activate O
    O->>O: persist order (Pending)
    O->>B: publish OrderPlaced
    O-->>C: 202 Accepted
    deactivate O
    B->>P: OrderPlaced
    B->>N: OrderPlaced
    P->>B: publish PaymentSucceeded
    B->>O: PaymentSucceeded
    O->>O: order → Confirmed
    N-->>C: push "order confirmed"
    Note over C,N: Client waits ~40ms.<br/>Payments can be down for a minute<br/>without failing the order.
```

---

## D3 — Commands vs events
*Section 3. The distinction that drives every later decision.*

```mermaid
flowchart TB
    subgraph CMD ["COMMAND — an instruction"]
        direction LR
        C1["Ordering"] -->|"ChargePayment"| C2["Payments"]
        C3["• Names a specific receiver<br/>• Expects it to happen<br/>• Sender knows who acts<br/>• One consumer"]
    end

    subgraph EVT ["EVENT — a statement of fact"]
        direction LR
        E1["Ordering"] -->|"OrderPlaced"| E2[("Topic")]
        E2 --> E3["Payments"]
        E2 --> E4["Inventory"]
        E2 --> E5["Analytics"]
        E6["• Names no receiver<br/>• Already happened, past tense<br/>• Sender does not care who listens<br/>• Zero to many consumers"]
    end

    classDef cmd fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    classDef evt fill:#122B22,stroke:#3DDC97,color:#E8EEF4
    classDef note fill:none,stroke:none,color:#8FA3B5
    class C1,C2 cmd
    class E1,E2,E3,E4,E5 evt
    class C3,E6 note
```

---

## D4 — Choosing a broker
*Section 4. Hero SVG: [`images/svg/d4-broker-decision.svg`](../images/svg/d4-broker-decision.svg) — the most shareable asset in the set.*

![Choosing a broker](../images/svg/d4-broker-decision.svg)

*[PNG for LinkedIn](../images/png/d4-broker-decision.png)*

```mermaid
flowchart TD
    START{"Do consumers need to<br/>re-read old messages?"}
    START -->|Yes, replay matters| REPLAY{"Throughput above<br/>~50k msg/sec?"}
    START -->|No, once is enough| ONCE{"Need per-message ack,<br/>retry and DLQ?"}

    REPLAY -->|Yes| KAFKA["Kafka<br/><i>event log</i>"]
    REPLAY -->|No| KAFKA2["Kafka or ASB Premium<br/><i>still want the log</i>"]

    ONCE -->|Yes| MANAGED{"Want to run<br/>the broker yourself?"}
    ONCE -->|No, simple fan-out| PUBSUB["Any pub/sub<br/><i>pick on ops cost</i>"]

    MANAGED -->|No, managed please| ASB["Azure Service Bus<br/><i>sessions, dedupe, scheduling</i>"]
    MANAGED -->|Yes, full control| RABBIT["RabbitMQ<br/><i>flexible routing, cheap</i>"]

    KAFKA --> PORT{"Must this run on<br/>more than one cloud?"}
    ASB --> PORT
    RABBIT --> PORT
    PORT -->|Yes| DAPR["Wrap in Dapr<br/><i>swap broker by config</i>"]
    PORT -->|No| DONE["Use the native client<br/><i>keep full broker power</i>"]

    classDef q fill:#18222E,stroke:#3A4A5C,color:#E8EEF4
    classDef a fill:#122B22,stroke:#3DDC97,color:#E8EEF4
    classDef d fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
    class START,REPLAY,ONCE,MANAGED,PORT q
    class KAFKA,KAFKA2,ASB,RABBIT,PUBSUB a
    class DAPR,DONE d
```

---

## D5 — Gateway and BFF topology
*Section 5.*

```mermaid
flowchart LR
    WEB["Web SPA"] --> BFFW["BFF — Web<br/><i>wide payloads, few calls</i>"]
    MOB["Mobile"] --> BFFM["BFF — Mobile<br/><i>slim payloads, offline-aware</i>"]
    PTR["Partner"] --> APIM["Public API<br/><i>versioned, rate-limited</i>"]

    BFFW --> GW["Gateway / YARP<br/>auth · routing · rate limit · TLS"]
    BFFM --> GW
    APIM --> GW

    GW --> ORD["Ordering"]
    GW --> INV["Inventory"]
    GW --> CAT["Catalog"]

    classDef ext fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
    classDef svc fill:#18222E,stroke:#3A4A5C,color:#E8EEF4
    class WEB,MOB,PTR,BFFW,BFFM,APIM,GW ext
    class ORD,INV,CAT svc
```

---

## D6 — Bounded contexts and data ownership
*Section 6. "Customer" means four different things here — and that is correct, not a bug.*

```mermaid
flowchart TB
    subgraph ORD ["Ordering context"]
        O1["Customer = <i>who is buying</i><br/>id, shipping address"]
        ODB[("orders db")]
    end
    subgraph PAY ["Payments context"]
        P1["Customer = <i>who is paying</i><br/>id, billing, payment methods"]
        PDB[("payments db")]
    end
    subgraph SUP ["Support context"]
        S1["Customer = <i>who needs help</i><br/>id, tickets, sentiment"]
        SDB[("support db")]
    end
    subgraph LEG ["Legacy CRM"]
        L1["Customer = <i>everything, 180 columns</i>"]
    end

    ACL["Anti-corruption layer<br/><i>translates, never leaks</i>"]
    LEG --> ACL
    ACL --> ORD
    ACL --> SUP

    ORD -.->|"events only,<br/>never direct db access"| PAY
    PAY -.->|events only| SUP

    classDef ctx fill:#18222E,stroke:#3A4A5C,color:#E8EEF4
    classDef acl fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    class O1,P1,S1,L1,ODB,PDB,SDB ctx
    class ACL acl
```

---

## D7 — Saga: choreography vs orchestration
*Section 7a. Hero SVG: [`images/svg/d7-saga.svg`](../images/svg/d7-saga.svg)*

![Saga: choreography vs orchestration](../images/svg/d7-saga.svg)

*[PNG for LinkedIn](../images/png/d7-saga.png)*

**Choreography — no coordinator; each service reacts**

```mermaid
sequenceDiagram
    autonumber
    participant O as Ordering
    participant B as Broker
    participant I as Inventory
    participant P as Payments

    O->>B: OrderPlaced
    B->>I: OrderPlaced
    I->>B: StockReserved
    B->>P: StockReserved
    P->>B: PaymentFailed
    B->>I: PaymentFailed
    I->>I: compensate — release stock
    B->>O: PaymentFailed
    O->>O: compensate — cancel order
    Note over O,P: No single place shows the flow.<br/>Simple at 3 services. Opaque at 10.
```

**Orchestration — one coordinator owns the flow**

```mermaid
sequenceDiagram
    autonumber
    participant O as OrderSaga
    participant I as Inventory
    participant P as Payments
    participant S as Shipping

    O->>I: ReserveStock
    I-->>O: StockReserved
    O->>P: ChargePayment
    P-->>O: PaymentFailed
    Note over O: State machine decides:<br/>failure → compensate backwards
    O->>I: ReleaseStock
    I-->>O: StockReleased
    O->>O: Order → Cancelled
    Note over O,S: Flow is one readable, testable class.<br/>Cost: the coordinator can itself fail.
```

---

## D8 — The dual-write problem and the Outbox
*Section 7b.*

```mermaid
flowchart TB
    subgraph BAD ["✗ Dual write — the bug nearly everyone ships first"]
        direction TB
        B1["BEGIN TX"] --> B2["save order"] --> B3["COMMIT"]
        B3 --> B4["publish OrderPlaced"]
        B4 -.->|"process dies here"| B5["Order exists.<br/>No event. Ever.<br/>Silent, permanent divergence."]
    end

    subgraph GOOD ["✓ Transactional Outbox"]
        direction TB
        G1["BEGIN TX"] --> G2["save order"] --> G3["insert into outbox"] --> G4["COMMIT<br/><i>both, or neither</i>"]
        G4 --> G5["Relay polls outbox"]
        G5 --> G6["publish to broker"]
        G6 --> G7["mark sent"]
        G6 -.->|"crash before mark"| G8["Republished later.<br/>Duplicate — which is fine,<br/>because consumers are idempotent."]
    end

    classDef bad fill:#2E1A1D,stroke:#F45B69,color:#E8EEF4
    classDef good fill:#122B22,stroke:#3DDC97,color:#E8EEF4
    class B1,B2,B3,B4,B5 bad
    class G1,G2,G3,G4,G5,G6,G7,G8 good
```

---

## D9 — Resilience layers
*Section 7c. Order matters — each layer only works because the one outside it exists.*

```mermaid
flowchart LR
    REQ["Request"] --> T["1 · Timeout<br/><i>bound the wait</i>"]
    T --> R["2 · Retry<br/><i>backoff + jitter</i>"]
    R --> CB["3 · Circuit breaker<br/><i>stop hammering a corpse</i>"]
    CB --> BH["4 · Bulkhead<br/><i>contain the blast radius</i>"]
    BH --> FB["5 · Fallback<br/><i>degrade, don't die</i>"]
    FB --> SVC["Downstream service"]

    R -.->|"no jitter =<br/>thundering herd"| WARN1["⚠"]
    CB -.->|"no breaker =<br/>retry storm"| WARN2["⚠"]

    classDef ok fill:#122B22,stroke:#3DDC97,color:#E8EEF4
    classDef warn fill:#2E1A1D,stroke:#F45B69,color:#E8EEF4
    classDef n fill:#18222E,stroke:#3A4A5C,color:#E8EEF4
    class T,R,CB,BH,FB ok
    class WARN1,WARN2 warn
    class REQ,SVC n
```

---

## D10 — One trace, five services
*Section 8. The article's payoff image — context propagating across HTTP **and** the broker.*

```mermaid
gantt
    title trace_id 4bf92f3577b34da6 — total 214ms
    dateFormat SSS
    axisFormat %Lms

    section Gateway
    POST /orders                  :a1, 000, 214ms
    section Ordering
    handle request                :a2, 012, 38ms
    db write + outbox             :a3, 020, 22ms
    section Broker
    OrderPlaced in flight         :crit, a4, 052, 18ms
    section Payments
    consume OrderPlaced           :a5, 070, 96ms
    call PSP (external)           :a6, 082, 78ms
    section Notifications
    consume OrderPlaced           :a7, 070, 24ms
    SignalR push                  :a8, 090, 8ms
```

---

## Production status

| ID | Mermaid | Hero SVG | Carousel slide |
|---|---|---|---|
| D1 | ✅ | ✅ | ✅ |
| D2 | ✅ | ✅ | ✅ |
| D3 | ✅ | — | ✅ |
| D4 | ✅ | ✅ | ✅ |
| D5 | ✅ | — | — |
| D6 | ✅ | — | ✅ |
| D7 | ✅ | ✅ | ✅ |
| D8 | ✅ | — | ✅ |
| D9 | ✅ | — | ✅ |
| D10 | ✅ | — | ✅ |

Any Mermaid diagram can be promoted to a hero SVG on request — say which.
