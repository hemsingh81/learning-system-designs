# 6 — System Design Scenarios

← [Observability](05-observability.md) · [Interview index](README.md) · Next: [Rapid fire →](07-rapid-fire.md)

8 full "design me X" questions. These run 30–45 minutes in a real interview, so each answer below is a **structure to follow**, not a script to recite.

---

## The structure to use for any of them

Do these in order. Interviewers notice when you jump straight to technology.

| # | Step | Time | What you are doing |
|---|---|---|---|
| 1 | **Clarify the constraint** | 3 min | Find the one thing that must be true. Everything else follows from it |
| 2 | **Scale numbers** | 2 min | Requests/sec, data size, users. Ask if not given |
| 3 | **Draw the services** | 5 min | Boxes and who owns what data |
| 4 | **Mark every arrow sync or async** | 5 min | And say why for each one |
| 5 | **Walk the happy path** | 5 min | One request, end to end |
| 6 | **Walk a failure** | 5 min | What breaks, what the user sees |
| 7 | **Name what you traded away** | 3 min | The part that makes you sound senior |

**Step 1 is the highest-leverage.** "Checkout must stay up during a spike" and "money must never move twice" produce completely different systems from the same starting description.

---

<details id="q1">
<summary><b>Q1 · Design the checkout flow for an e-commerce site.</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>the most common scenario</i></summary>

**1. The constraint**

Ask: *"What matters more — never overselling, or never failing a checkout during a sale?"*

For most retail the answer is **keep selling**. That single answer drives everything below. (If they say "never oversell", you are designing something closer to ticketing, and the answer changes.)

**2. Scale**

Normal 50 orders/min; sale peak 5,000 orders/min — a 100× spike arriving the second a campaign email lands. That spike is the design problem.

**3. Services**

`Catalog` · `Inventory` · `Ordering` · `Payments` · `Notifications` · `Shipping` — each owning its own data, one writer per entity.

**4. Sync or async**

| Call | Choice | Why |
|---|---|---|
| BFF → Catalog | Sync, cached | Cannot render a page without products |
| BFF → Inventory | Sync **with fallback** | Stock badge; hide it rather than fail the page |
| BFF → Ordering | Sync, returns `202` | The user needs an order ID now |
| Ordering → everything else | **Async** | Nothing downstream should be able to fail a sale |

**The decision that defines the system:** payment is asynchronous. Accept the order in 40 ms, charge in the background, push the result. Charging inside the request means the payment provider's latency becomes your checkout latency and their outage becomes yours.

**5. Happy path**

`POST /orders` with an idempotency key → order + outbox row in one transaction → `202 Accepted` in ~15 ms → relay publishes → Inventory reserves → Payments charges → `PaymentSucceeded` → order confirmed → SignalR pushes "Confirmed" to the browser ~1.2 s later.

**6. Failure**

Payment declined → `PaymentFailed` → Inventory releases the reservation → order cancelled → the user is told *why*, with a retry button. Stock is back on sale within 20 ms.

**7. What you traded**

- The user sees "Processing" briefly — so the UI must show it honestly, never claim success early.
- Some orders are cancelled *after* a success page, which needs a clear email.
- A rare oversell is possible, and that must be an agreed business decision, not an engineer's call.

**Things that earn points here:** mentioning the outbox unprompted; a reservation TTL plus a sweeper for lost events; `202` rather than `201`; idempotent compensation.

📖 [Case study 1 — E-commerce checkout](../case-studies/01-ecommerce/README.md)

</details>

---

<details id="q2">
<summary><b>Q2 · Design a money transfer system.</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**1. The constraint**

*"Money must never move twice and never disappear."* Correctness beats availability — the opposite of Q1, and say so explicitly, because the contrast is the insight.

**2. Scale**

A few hundred transfers/sec at peak. **Volume is not the problem here**, which is worth saying — it stops you over-engineering.

**3. Services**

`Accounts` · **`Ledger`** · `Transfers` · `Payments` · `Fraud` · `Notifications`.

**The rule that defines the system: only the Ledger writes balances. Nothing else. Ever.**

**4. The two things to get right**

**(a) Double-entry, not a balance column.** Immutable journal entries in balanced pairs; the balance is *derived*. This buys history, an audit trail, self-checking (debits must equal credits), and reversal without deletion.

**(b) Debit and credit in ONE local transaction, in ONE service.** Not a saga. `Serializable` isolation, or two concurrent transfers both pass a balance check only one should.

If the interviewer pushes you to make the posting a saga, push back — that is the trap in the question.

**5. The saga is around the posting**

`Requested → Screening → Posting → Paying → Completed`, orchestrated, with timeouts on every wait. Orchestration because compliance reviews the flow, support must answer "where is transfer T-123?", and compensation needs to know whether the ledger posted before the payment failed.

**6. Failure**

- Insufficient funds → rejected, nothing posted, **no compensation needed**.
- External payment fails after posting → reverse with a **new opposing journal**; the original is never deleted.
- Payment times out → state = **`Unknown`**. Never guess, never auto-retry. Query the network; escalate if unresolved.

**7. What you traded**

Availability. If Fraud or the Ledger is unavailable, transfers wait. That is the correct answer for a bank and the wrong one for a shop.

**Things that earn points:** idempotency enforced at three levels; strict FIFO per account; nightly reconciliation proving the books balance; `Unknown` as a first-class state.

📖 [Case study 2 — Banking and payments](../case-studies/02-banking-payments/README.md)

</details>

---

<details id="q3">
<summary><b>Q3 · Design a real-time price feed for 5,000 instruments.</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**1. The constraint**

Volume, and replayability. *"A backtest run in 2029 must see exactly what the market looked like in 2026."*

**2. Scale**

200,000 ticks/sec peak, 1.2 billion/day, ~15 consumers. Get these numbers on the board early — they rule out most designs immediately.

**3. Why Kafka, not a queue**

Replay is a product feature (backtesting, rebuilding projections, reprocessing after a bug fix). A queue cannot replay at all, and nothing else handles the rate.

**4. The single most important decision: the partition key**

`Key = symbol`.

- `null` → ordering destroyed, candles built from out-of-order ticks.
- constant → one consumer, no parallelism.
- `symbol` → ordered per instrument, parallel across instruments. ✅

Partition count: 200k ÷ 20k per consumer = 10 minimum, ×3 headroom, round to **64**. Over-provision, because adding partitions later re-hashes keys and breaks ordering.

**5. Pipeline**

`Feed Handler → raw topic → Normaliser → clean topic → {Candle Builder, Store, Distributor, Alerts}`

Two topics because when a candle looks wrong, the first question is "was the raw tick wrong, or did we break it?" — and 24 hours of raw retention answers it in a minute.

**6. Three techniques worth naming**

- **`Acks.Leader`, not `Acks.All`** — durability traded for throughput, made acceptable by gap detection.
- **Gap detection as a feature** — sequence numbers produce a `GapDetected` event, and affected candles are flagged incomplete. Visible loss beats silent loss.
- **Conflation for the display path only** — browsers get 10 snapshots/sec; the candle builder, store, and alert engine see every tick.

**7. What you traded**

A few milliseconds of ticks can be lost if a broker dies at the wrong moment. Acceptable *because* it is detected and marked. In banking the same setting would be indefensible.

**Things that earn points:** batching writes and committing the offset only after a durable write; retention tiers as a budget decision; naming the hot-partition problem before being asked.

📖 [Case study 3 — Stock market data](../case-studies/03-stock-market-data/README.md)

</details>

---

<details id="q4">
<summary><b>Q4 · Design order placement for a trading app.</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**1. The constraint**

Two that fight: **an order must be risk-checked before it leaves**, and **the whole path must complete in under 150 ms**.

The resolution is one sentence, and it is the architecture: **exactly one synchronous gate; everything else async.**

**2. The gate**

`Order API → Risk` is synchronous with an **8 ms budget**. That budget dictates everything about Risk:

- In-memory limits, no database on the hot path.
- Cached positions and buying power, updated by events.
- No network calls — one 20 ms dependency would blow the budget entirely.
- gRPC, not REST, to save 2–4 ms.
- **Fail closed** — if Risk is unavailable, reject. An unchecked order is a regulatory incident.

**3. The problem with a cache, and the fix**

A cached buying power lags by a few hundred milliseconds, so two quick orders could each pass a check only one should.

**Reservations** fix it: approving an order immediately holds its value in memory, before the caller even gets a response. Holds expire, and a reconciler compares cached state against the truth. Fast check in the hot path, exact check behind it.

**4. States**

`Received → Checking → Routed → Working → Filled`, plus `Rejected`, `Cancelled`, and — the important one — **`Unknown`**: we sent it, the broker did not answer, it may or may not be live at the exchange.

**Never auto-retry an order.** A duplicate is a real unwanted position that costs money to unwind while the market moves.

**5. Also worth raising unprompted**

- A **kill switch**: synchronous, in-memory, checked first on every order, with per-user / per-symbol / global scope. It must be milliseconds, not seconds.
- A **price collar** rejecting a limit 10% away from the market — the fat-finger guard, which saves more money than every other rule combined.
- **Event-sourced positions**, so average cost is explainable and P&L bugs can be fixed by recomputing from fills.

**7. What you traded**

Cached risk state can be marginally stale, covered by reservations plus reconciliation. And fail-closed means a Risk outage stops all trading — deliberately.

📖 [Case study 4 — Trading app](../case-studies/04-trading-app/README.md)

</details>

---

<details id="q5">
<summary><b>Q5 · Design live parcel tracking for 12,000 vehicles.</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**1. The constraint**

*"Only the latest position matters for the map. The full history matters for proof of delivery."* Two demands on one stream.

Also worth spotting early: **a lost ping barely matters** — another arrives in 5 seconds. That softer constraint allows a much simpler design than the market-data case, and recognising it is the senior move.

**2. Scale**

12,000 vehicles × one ping / 5 s = 2,400/sec. 30,000 customers watching maps. ~200 million history rows/day.

**3. The central idea: three consumers, three storage models**

| Path | Storage | Why |
|---|---|---|
| Latest position | **Redis**, one key per vehicle | Only ever 12,000 keys. O(1). Overwrite, never append |
| Fence events | Kafka topic | Arrival/departure are facts others react to |
| History | Time-partitioned table | Written once, read rarely, kept for years |

Querying history for "where is vehicle 4471 now?" would be an index seek over 200 million rows, 30,000 times a second, for a single key lookup.

**4. Two details that matter**

- **A TTL on the position key.** A vehicle that stops reporting *disappears* rather than sitting on the map at an hours-old position looking live. Missing is honest; stale-pretending-to-be-live is not.
- **Nothing on the live path reads the history table.** One two-year legal export would lock it and stop the live map for everyone.

**5. The hard part: geo-fencing**

500,000 fences × 2,400 pings/sec = 1.2 billion checks/sec if done naively. Three fixes, all needed:

1. **Spatial index** (geohash) → ~5 candidate fences instead of 500,000.
2. **Previous-state check** → fire on the *transition*, not on being inside. Without it a parked van fires "arrived" every 5 seconds, 17,280 times a day.
3. **Hysteresis** → GPS jitters 10–30 m; enter at the boundary, leave only after boundary + 50 m. Without it, one parked van generates thousands of events an hour.

Point 3 is what teams discover from a notification bill.

**6. Offline vehicles are normal**

Tunnels and basements mean bursts of buffered pings. History accepts all; latest-position ignores older ones; geo-fencing replays them in device-time order.

📖 [Case study 5 — Logistics tracking](../case-studies/05-logistics-tracking/README.md)

</details>

---

<details id="q6">
<summary><b>Q6 · Design a notification service used by every other service.</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**1. The constraint**

*"Never block the caller, never send a duplicate to a human, and never lose an important one."* Those pull in different directions and you should say so.

**2. The interface**

Other services **publish events**; they do not call Notifications. That is the key decision.

If they called synchronously, every service's latency and availability would depend on SMTP. Notifications should subscribe to `OrderPlaced`, `PaymentFailed`, and so on, and decide what to send.

**A useful refinement:** for genuinely notification-specific requests ("send this password reset"), a **command** on a queue is right, because exactly one service must act and it *would* be a bug if nobody did.

**3. Design**

```
Services → outbox → topic → Notifications (inbox for dedupe)
                                 ├─ email  (queue, retried)
                                 ├─ SMS    (queue, retried, costs money)
                                 └─ push   (SignalR, fire and forget)
```

**4. The details that matter**

- **Idempotency via an inbox**, or users get duplicate emails on every redelivery.
- **Per-channel queues**, because SMS costs money and deserves its own retry policy and DLQ.
- **User preferences and quiet hours** — Notifications owns this, not the caller.
- **Rate limiting per user.** A bug upstream should not send someone 400 texts, and this service is the last line of defence.
- **Templates live here**, so wording changes do not require redeploying Ordering.

**5. Failure**

Email provider down → queue grows, drains on recovery. Nothing lost, and the order was never at risk.

**6. What you traded**

Notifications are eventually consistent — a user may act on the app before the email arrives. Almost always fine, and worth stating rather than leaving implicit.

**Things that earn points:** the send is *not* transactional with the inbox row, so a crash between them sends a duplicate — an accepted trade for email, and the wrong trade for money.

📖 [Case study 1 — `OrderEventsConsumer.cs`](../case-studies/01-ecommerce/src/Ecommerce.Notifications/Consumers/OrderEventsConsumer.cs)

</details>

---

<details id="q7">
<summary><b>Q7 · Split this monolith. Where do you start?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**1. Challenge the premise first**

*"What are we trying to buy?"* If the answer is "microservices are best practice", say plainly that a split has real costs and needs a specific reason: independent scaling, independent failure, independent release cadence, team ownership, or compliance isolation.

Interviewers usually respect this. If they insist, proceed — but you have shown judgement.

**2. Find the seams before writing code**

- Where does the **language** change? ("order" = basket vs manufacturing job)
- What **changes together** in the same pull request?
- Which tables does each module actually touch?
- Where is a **second of inconsistency acceptable**? That is a candidate boundary.

**3. Sequence: strangler fig, not big bang**

1. **Modularise inside the monolith first.** Separate projects, no cross-module DB access, communication via interfaces. Most of the value, a fraction of the risk.
2. **Extract the easiest high-value service** — few dependencies, clear ownership, real reason. Notifications is often a good first one.
3. **Route through a facade** so callers do not change.
4. **Move the data last**, and expect this to be the hard part.
5. **Measure**, then decide whether to continue.

**4. The data is the hard part**

Code extraction is a week. Splitting a shared `Customers` table used by nine modules is a quarter. Say this — it is where inexperienced answers underestimate by 10×.

Techniques: dual writes during migration, CDC to sync during transition, a read-only replica for the leaving service, then a cutover with a rollback plan.

**5. What tells you to stop**

If, after two or three services, deploys are not more independent and incidents are not smaller in blast radius, stop and reassess. Ending with 3 services and a well-modularised monolith is a legitimate and often superior outcome.

📖 [Chapter 6 — When to split, when not to](../tutorial/06-boundaries-and-data.md#when-to-split-when-not-to)

</details>

---

<details id="q8">
<summary><b>Q8 · Design an idempotent payment API.</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**1. The constraint**

*"The same logical payment must never execute twice, no matter how many times it is submitted."*

Retries are guaranteed: mobile networks drop responses, users tap twice, clients retry on timeout.

**2. The interface**

```
POST /payments
Idempotency-Key: <client-generated, stable across retries>   ← MANDATORY
```

**Mandatory, not optional, and never server-generated.** A server-generated key is new on every retry, which defeats the mechanism at exactly the moment it is needed. Missing header → 400.

**3. Three levels of defence**

| Level | Guard | Catches |
|---|---|---|
| API | Unique index on `(UserId, IdempotencyKey)` | Client retries |
| Processing | Inbox on `(MessageId, Consumer)` | Broker redeliveries |
| Provider | `Idempotency-Key` header on the outbound call | Our own retries |

Three levels because one missed guard moves real money.

**4. The race**

Two identical requests hit two instances simultaneously. Both pass the "have I seen this key?" check before either commits.

**The unique index is the real guarantee**; the check is only a fast path:

```csharp
catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("IX_Payments_IdempotencyKey"))
{
    var winner = await db.Payments.FirstAsync(p => p.IdempotencyKey == key, ct);
    return Results.Ok(winner);      // a success, not an error
}
```

**5. Edge cases they will probe**

- **Same key, different amount?** → 409. That is a client bug; returning an unrelated payment would be worse.
- **Retry while the first is still processing?** → return the in-flight status, do not start a second.
- **How long do you keep keys?** → longer than any client would sensibly retry; 24 hours minimum, and longer than your broker's retention if messaging is involved.
- **The provider call times out?** → `Unknown`, never a guess. Retry with the same key to learn the truth.

**6. What you traded**

Storage for keys and a slightly more complex API contract. Trivial next to a double charge.

📖 [Chapter 8 — Level 3: idempotency keys at the boundary](../tutorial/08-outbox-and-idempotency.md#level-3--idempotency-keys-at-the-boundary)

</details>

---

## Five phrases that make you sound senior in any of these

1. *"Before I design this, what is the one thing that must never happen?"*
2. *"That call is synchronous because the caller genuinely cannot continue without it — everything else here is async."*
3. *"The failure mode I would worry about is…"*
4. *"I would trade X for Y here, because this business cares more about Y."*
5. *"I would want a job that proves this invariant nightly, because bugs and manual edits corrupt data in ways tests cannot see."*

---

← [Observability](05-observability.md) · [Interview index](README.md) · Next: [Rapid fire →](07-rapid-fire.md)
