# Case Study 4 — Trading App

← [Market data](../03-stock-market-data/) · [All case studies](../README.md) · Next: [Logistics tracking](../05-logistics-tracking/)

---

## The business

A retail trading app. Users see live prices, place buy and sell orders, and watch their positions and profit-and-loss update in real time. Orders go to a broker, which sends them to the exchange.

| Measure | Value |
|---|---|
| Active users at market open | ~80,000 |
| Orders per second at peak | ~2,000 |
| Order-to-exchange latency budget | **under 150 ms end to end** |
| Price updates consumed | the full feed from [case study 3](../03-stock-market-data/) |

---

## The constraint

> **An order must be risk-checked before it leaves the building — and the whole path must still complete in under 150 milliseconds.**

Two demands that fight each other. Banking chose correctness over speed. Market data chose speed over durability. This system has to do both, so it draws a sharp line:

> **Exactly one synchronous gate. Everything else is asynchronous.**

That single sentence is the architecture.

---

## Why one sync gate, and only one

You cannot send an order you are not allowed to send. Sending first and checking later means:

- The user trades money they do not have.
- You breach a regulatory position limit.
- A bug in a trading algorithm sends 10,000 orders before anyone notices.

None of these can be fixed by an apology email. The check must happen **before** the order leaves.

But every extra synchronous hop costs latency and availability ([chapter 2](../../tutorial/02-synchronous.md)). So the design allows exactly one:

```
Client ─► Gateway ─► Order API ─► [ RISK CHECK — synchronous, 8ms ] ─► accept
                                                                         │
                                                                    (async from here)
                                                                         ▼
                                                            Execution ─► Broker ─► Exchange
                                                                         │
                                            Positions ◄── Fills ◄────────┘
                                                │
                                                ▼
                                            push to the client
```

Everything after the risk check is asynchronous, because once the order is accepted, the user does not need to wait to hear what the exchange said — they will be told.

---

## The services

| Service | Owns | Latency budget |
|---|---|---|
| **Order API** | Order records, order state | 20 ms |
| **Risk** | Limits, buying power, position caps, the kill switch | **8 ms — the tightest in the system** |
| **Execution** | Broker connection, order routing, fills | 40 ms to the broker |
| **Positions** | Holdings, average cost, realised and unrealised P&L | async |
| **Market Data** | Live prices (consumes case study 3's feed) | async |
| **Push** | WebSocket to the client | async |
| **Ledger** | Cash balances, settlement | async |

### The ownership table

| Entity | Owner | Readers |
|---|---|---|
| Order | Order API | Execution, Positions, Push |
| Fill | Execution | Positions, Ledger |
| Position | Positions | Risk (via cache), Push |
| BuyingPower | Ledger | Risk (via cache) |
| Price | Market Data | everyone |
| RiskLimit | Risk | nobody |

**Risk reads a cached copy of positions and buying power.** It does not call Positions or Ledger synchronously — that would put two more hops inside the 8 ms budget. See "Decision 2".

---

## Order states — the heart of the system

An order is a state machine, and getting the states right matters more than any other modelling decision here.

```
                  ┌──────────┐
                  │ Received │  order API accepted the request
                  └────┬─────┘
                       ▼
                  ┌──────────┐   risk said no
                  │ Checking │──────────────────► Rejected
                  └────┬─────┘
                       │ risk said yes
                       ▼
                  ┌──────────┐   broker rejected
                  │  Routed  │──────────────────► Rejected
                  └────┬─────┘
                       │ broker acknowledged
                       ▼
                  ┌──────────┐
       ┌──────────│  Working │──────────┐
       │          └────┬─────┘          │
       │ partial fill  │ full fill      │ user cancels
       ▼               ▼                ▼
┌──────────────┐  ┌──────────┐   ┌───────────┐
│PartiallyFilled│─►│  Filled  │   │ Cancelled │
└──────────────┘  └──────────┘   └───────────┘
```

Plus one more, and it is the important one:

```
                  ┌──────────┐
                  │ Unknown  │  we sent it, the broker did not answer.
                  └──────────┘  It may or may not be live at the exchange.
```

**`Unknown` is a real state, exactly as in [banking](../02-banking-payments/).** A trading system that only models success and failure will eventually tell a user their order was rejected while it is quietly live at the exchange — and that is how someone loses a lot of money.

---

## Walkthrough: buying 100 shares

```
t=0ms      Client        POST /orders  { RELIANCE, BUY, 100, LIMIT 2841.00 }
                         Client-Order-Id: c7f2a9  (the idempotency key)

t=2ms      Gateway       validate JWT, rate limit (per user, not per IP)
t=4ms      Order API     client order ID not seen → create Order (Received)

t=5ms      Order API     ─────► Risk.Check()  [SYNCHRONOUS — the only one]
t=6ms      Risk            buying power from cache:  ₹450,000 ≥ ₹284,100  ✓
t=7ms      Risk            position limit:  100 ≤ 5,000 cap                ✓
t=7ms      Risk            per-order value cap: ₹284,100 ≤ ₹1,000,000      ✓
t=8ms      Risk            kill switch: off                                ✓
t=9ms      Risk          ◄───── Approved (reservation held for 30s)

t=11ms     Order API     status = Checking → Routed
t=13ms     Order API     INSERT order + INSERT outbox   ← one transaction
t=15ms     Order API     202 Accepted { orderId, status: "Routed" }
t=17ms     Client        shows the order as "Sending…"

           ── everything below is asynchronous ──

t=40ms     Execution     consume OrderRouted → send to broker (FIX / REST)
t=95ms     Broker        acknowledged, exchange order ID 4471829
t=97ms     Execution     publish OrderAcknowledged
t=99ms     Push          → client: "Working"

t=340ms    Broker        FILL: 100 @ 2840.75
t=345ms    Execution     publish OrderFilled
t=350ms    Positions     consume → position 100 @ 2840.75, recalc average cost
t=352ms    Ledger        consume → debit cash ₹284,075 + charges
t=355ms    Risk          consume → release the reservation, update the cached position
t=358ms    Push          → client: "Filled 100 @ 2840.75"
```

**15 ms to a response. 358 ms to a confirmed fill.** The user saw feedback three times without refreshing.

---

## Key decisions

### Decision 1 — Risk is synchronous, and its budget is 8 ms

Everything about the Risk service is shaped by that number:

| Technique | Why |
|---|---|
| **In-memory limits** | Loaded at startup, refreshed on events. Zero database reads on the hot path |
| **Cached positions and buying power** | Updated by events, never fetched synchronously |
| **No network calls at all** | A single 20 ms dependency would blow the entire budget |
| **Single-digit-millisecond datastore** | If state must be shared, Redis — never a relational query |
| **Fail closed** | If Risk is unavailable, **reject the order.** Never "allow and check later" |

**Fail closed is the opposite of [case study 1](../01-ecommerce/).** E-commerce keeps selling when Inventory is down. A trading system that keeps accepting orders when Risk is down is one bug away from a regulatory incident.

### Decision 2 — Risk reads cached state, and that is a deliberate risk

Risk needs buying power (owned by Ledger) and positions (owned by Positions). Calling them synchronously would add 30–60 ms and two more failure points.

So Risk keeps a **local cache**, updated by events:

```csharp
// Risk/Consumers/PositionChangedConsumer.cs
public async Task Consume(ConsumeContext<PositionChanged> ctx)
{
    _cache.UpdatePosition(ctx.Message.UserId, ctx.Message.Symbol, ctx.Message.Quantity);
}
```

**The cost, stated plainly:** the cache can be a few hundred milliseconds stale. A user could, in theory, place two orders quickly enough that the second is checked against a position the first has already changed.

**How that is handled — reservations, not just reads:**

```csharp
// The approval RESERVES buying power immediately, in memory.
// The next check sees the reduced amount, even before the fill event arrives.
// This closes the gap that a plain cache read would leave open.
_reservations.Hold(userId, amount, TimeSpan.FromSeconds(30));
```

Reservations expire, so a rejected or lost order cannot hold buying power forever — the same safety-net pattern as the e-commerce reservation sweeper.

**And a slower, exact check runs behind it.** A background reconciler compares cached positions against the real ones every few seconds and alerts on drift. Fast check in the hot path, exact check behind it. This is a common and honest shape for latency-critical systems.

### Decision 3 — The client order ID is the idempotency key

The client generates it, and it is unique per user:

```
Unique index on (UserId, ClientOrderId)
```

**Why it must come from the client:** a mobile app on a bad connection retries. Without a stable key, one tap becomes two orders — and unlike a duplicate e-commerce order, this one cannot be refunded. The market moved.

This also matches the FIX protocol, where `ClOrdID` is exactly this concept. Aligning with the protocol you already speak is free correctness.

### Decision 4 — The kill switch is synchronous, global, and instant

Every trading system needs one control: **stop everything, now.**

```csharp
// Checked on every single order. It must be the cheapest check in the system.
if (_killSwitch.IsActive(userId, symbol))
    return RiskDecision.Rejected(RiskRejectionReason.TradingHalted, _killSwitch.Reason);
```

Scopes, from narrowest to widest:

| Scope | Used when |
|---|---|
| Per user | A suspected compromised account |
| Per symbol | An exchange halts a stock |
| Per strategy | An algorithm is behaving badly |
| **Global** | Something is very wrong and you need everything to stop |

**It must be synchronous and in-memory.** A kill switch that takes 5 seconds to propagate is 10,000 orders too late. Push the change to every Risk instance immediately, and have each instance re-check a shared flag on a short interval as a backstop.

### Decision 5 — Never auto-retry an order to the broker

The broker times out. Did the order reach the exchange?

```csharp
catch (TimeoutException)
{
    // NEVER resend. A duplicate order is a real, unwanted position that
    // costs real money to unwind, and the market moves while you find out.
    order.MarkUnknown("broker timeout — status unverified");

    // Ask the broker what actually happened, using our client order ID.
    await scheduler.Schedule(TimeSpan.FromSeconds(2),
        new QueryOrderStatus(order.Id, order.ClientOrderId));
}
```

Same principle as [banking](../02-banking-payments/): **when the outcome is unknown, find out — do not guess.** A retry is a guess with money attached.

### Decision 6 — Positions are event-sourced

Position state is derived from an append-only stream of fills:

```
Fill: +100 @ 2840.75    → position 100, avg 2840.75
Fill: +50  @ 2845.00    → position 150, avg 2842.17
Fill: -75  @ 2850.00    → position 75,  avg 2842.17, realised P&L +₹587.25
```

**Why:**
- "How did I get this average cost?" is answerable, exactly, years later.
- Tax reporting needs every lot.
- A bug in the P&L calculation can be fixed and the position **recomputed from the fills**.
- Disputes are settled with data, not with an apology.

**The cost:** you must keep a snapshot for speed, and prove the snapshot matches the recomputed value — the same reconciliation duty as the [banking ledger](../02-banking-payments/).

---

## Folder structure

`src/` sits alongside a real [`docker-compose.yml`](docker-compose.yml) — Redis for the risk hot path, Kafka for the order/fill audit log, RabbitMQ for commands, PostgreSQL, Jaeger, and a broker mock you can configure to time out (the "now break it" exercises need that).

```
src/
├── Trading.Contracts/
│   ├── Commands/   PlaceOrder.cs, CancelOrder.cs
│   └── Events/     OrderEvents.cs, FillEvents.cs, PositionEvents.cs
│
├── Trading.OrderApi/
│   ├── Api/        OrdersEndpoints.cs
│   ├── Domain/
│   │   ├── Order.cs              ← the state machine, pure and fully tested
│   │   ├── OrderState.cs
│   │   └── OrderType.cs          ← Market, Limit, StopLoss, StopLimit
│   ├── Consumers/  ExecutionEventsConsumer.cs
│   └── Infrastructure/
│
├── Trading.Risk/                            ← the latency-critical service
│   ├── Checks/
│   │   ├── IRiskCheck.cs
│   │   ├── BuyingPowerCheck.cs
│   │   ├── PositionLimitCheck.cs
│   │   ├── OrderValueCheck.cs
│   │   ├── PriceCollarCheck.cs   ← rejects a "fat finger" price
│   │   └── KillSwitchCheck.cs
│   ├── State/
│   │   ├── RiskStateCache.cs     ← in-memory. NO database on the hot path
│   │   └── ReservationLedger.cs  ← holds buying power between check and fill
│   ├── Consumers/                ← the ONLY way the cache is updated
│   ├── Jobs/       CacheReconciler.cs   ← slow exact check behind the fast one
│   └── Api/        RiskEndpoints.cs     ← gRPC, not REST. See below.
│
├── Trading.Execution/
│   ├── Brokers/    IBrokerClient.cs, FixBrokerClient.cs, RestBrokerClient.cs
│   ├── Routing/    OrderRouter.cs
│   ├── Consumers/  OrderRoutedConsumer.cs
│   └── Jobs/       OrderStatusReconciler.cs   ← resolves Unknown orders
│
├── Trading.Positions/
│   ├── Domain/     Position.cs, Lot.cs, PnlCalculator.cs   ← pure maths
│   ├── Consumers/  FillConsumer.cs
│   └── Snapshots/  PositionSnapshotStore.cs
│
└── Trading.Push/
    ├── Hubs/       TradingHub.cs
    └── Consumers/  OrderEventsConsumer.cs, PriceConsumer.cs
```

### Why this layout

**`Risk/Checks/` is one file per rule.** Rules change constantly, regulators ask what each one does, and each must be independently testable. A single 800-line `RiskService.Check()` cannot answer "show me the position-limit rule" — a folder of small files can.

**`Risk/Api/` uses gRPC, not REST.** This is the one call inside the 8 ms budget. gRPC's binary encoding and HTTP/2 multiplexing save 2–4 ms versus JSON over HTTP/1.1 — a meaningful share of the budget ([chapter 2](../../tutorial/02-synchronous.md)).

**`Positions/Domain/PnlCalculator.cs` is pure.** Average cost with partial fills, short positions, and corporate actions is genuinely hard maths that users check against their own spreadsheets. It must be unit-testable with no infrastructure.

**`Execution/Brokers/` is an ACL.** FIX is a 1990s protocol with its own vocabulary. It stops at that folder.

---

## The code

> Read [HOW-TO-READ-THE-CODE.md](../HOW-TO-READ-THE-CODE.md) first. `PnlCalculator.cs` is pure maths with no dependencies — the easiest file here to read cold. `RiskEngine.cs` and `ReservationLedger.cs` are a pair; read them in that order.

| File | Shows |
|---|---|
| [`Trading.Risk/Checks/RiskEngine.cs`](src/Trading.Risk/Checks/RiskEngine.cs) | The 8 ms sync gate: in-memory, fail-closed, composable rules |
| [`Trading.Risk/State/ReservationLedger.cs`](src/Trading.Risk/State/ReservationLedger.cs) | Closing the cache-staleness gap with expiring holds |
| [`Trading.OrderApi/Domain/Order.cs`](src/Trading.OrderApi/Domain/Order.cs) | The order state machine, including `Unknown` |
| [`Trading.Positions/Domain/PnlCalculator.cs`](src/Trading.Positions/Domain/PnlCalculator.cs) | Average cost and realised P&L, pure and testable |

---

## Failure modes

| What fails | What happens | User sees |
|---|---|---|
| **Risk down** | **All orders rejected.** Fail closed | "Trading temporarily unavailable" |
| **Risk cache stale** | Reservations cover the gap; reconciler alerts on drift | Nothing |
| **Order API down** | No new orders. Existing ones continue | Cannot place orders; positions still update |
| **Execution down** | Orders queue as `Routed`, sent when it recovers | "Sending…" for longer |
| **Broker times out** | Order → `Unknown`; reconciler queries the broker | "Checking status…" — never a guess |
| **Positions down** | Fills queue; P&L is stale | Orders fill; position updates late |
| **Push down** | Client polls as a fallback | Slower updates, nothing lost |
| **Market data lags** | Prices go stale | Stale-price warning; **risk collar uses the last good price** |

**Two rows deserve emphasis.** "Risk down → reject everything" is the constraint holding. And "broker timeout → Unknown, never a retry" is the single most valuable line in the whole system.

---

## Now break it

1. **Stop Risk.** Confirm every order is rejected, not accepted. If any order gets through, you have failed open — fix it before anything else.
2. **Measure the risk check's p99** under 2,000 orders/sec. If it is over 8 ms, find out why. Usually it is a database call that crept into the hot path.
3. **Add a synchronous call from Risk to Positions.** Measure again. Watch the budget disappear. Remove it. That measurement is why the cache exists.
4. **Send the same `Client-Order-Id` twice.** One order. If you get two, a user just doubled their position by tapping twice.
5. **Place two orders quickly** that together exceed buying power. Without reservations, both pass. With them, the second is rejected. Try it both ways.
6. **Make the broker time out.** Confirm the order goes to `Unknown` and the reconciler resolves it. If your code retries automatically, you have just built a duplicate-position generator.
7. **Activate the kill switch** while 1,000 orders/sec are flowing. Measure how long until the last order is rejected. It should be milliseconds. If it is seconds, that is thousands of orders you did not stop.
8. **Fill an order in three partial fills.** Check the average cost after each. Then compute it by hand. They must agree exactly — users check this with a calculator, and they are not forgiving about it.
9. **Recompute a position from its fill history** and compare it with the snapshot. Any drift means your event sourcing and your snapshot have already diverged.
10. **Send a limit order at 10× the market price** (a fat finger). The price collar must reject it. If it does not, you have no protection against the most common expensive mistake in retail trading.
11. **Stop the market-data feed.** Confirm the risk collar uses the last good price and flags it, rather than dividing by a null price or waving the order through.

---

## What this case study teaches

- **You can have one synchronous gate.** Name it, budget it in milliseconds, and defend that budget against every future addition.
- **Fail closed when the check protects against harm you cannot undo.** The opposite of e-commerce, on purpose.
- **A cache plus reservations beats a synchronous read** when latency is the constraint — provided reservations expire and a reconciler watches for drift.
- **`Unknown` is a state, in every system that talks to an external one.**
- **Never auto-retry an order.** A retry is a guess, and here a guess costs money.
- **Event sourcing earns its cost** when "how did we get this number?" is a question users actually ask.
- **A kill switch is a feature, not an operations tool.** Design it in from day one.

---

← [Market data](../03-stock-market-data/) · [All case studies](../README.md) · Next: [Logistics tracking](../05-logistics-tracking/)
