# How To Read The Sample Code

← [All case studies](README.md) · [Back to the map](../README.md)

Read this **before** opening any `.cs` file. It takes five minutes and will save you an hour of confusion.

---

## First, the honest part

These files are **teaching material shaped like production code**. They are not a solution you can open in Visual Studio and press F5.

| | |
|---|---|
| ✅ Every file is complete and real | You can copy any file into a project and adapt it |
| ✅ The error handling is real | That is usually where the actual lesson lives |
| ❌ There is no `.sln` or `.csproj` | Nothing to build |
| ❌ Some referenced types are missing | **This is the big one — see below** |
| ❌ No `using` statement is guaranteed complete | Your IDE will show red squiggles everywhere |

### The thing that will confuse you first

Open [`OrdersEndpoints.cs`](01-ecommerce/src/Ecommerce.Ordering/Api/OrdersEndpoints.cs) and you will see this:

```csharp
db.OutboxMessages.Add(OutboxMessage.From(domainEvent));
```

Then you will look for `OutboxMessage`, and **it is not in the folder.** Neither is `IMetrics`, `InboxMessage`, `OrderingDbContext`, or about thirty other things.

That is deliberate, and I should have said so up front. Each file shows **one idea**. If every file also carried its DbContext, its EF configuration, its metrics class, and its DI registration, the idea would be buried under 400 lines of plumbing you already know how to write.

**So: when you hit a type that does not exist, do not go looking for it.** Check the table below — it tells you what each one does in one line. That is all you need to keep reading.

---

## The 30 missing pieces, and what each one is

Every symbol below is used in the samples and defined nowhere. Here is what each would be in a real project.

### Infrastructure you would write once and reuse everywhere

| Symbol | What it is | Where it's explained |
|---|---|---|
| `OutboxMessage` | The outbox table row. `.From(evt)` serialises an event into it | **Full implementation** in [chapter 8](../tutorial/08-outbox-and-idempotency.md#code--the-outbox) |
| `db.OutboxMessages` | `DbSet<OutboxMessage>` on the DbContext | [chapter 8](../tutorial/08-outbox-and-idempotency.md) |
| `InboxMessage` | The dedupe table row: `(MessageId, Consumer)` composite key | **Full implementation** in [chapter 8](../tutorial/08-outbox-and-idempotency.md#level-2--the-inbox-works-for-everything) |
| `IInboxStore` | Wrapper over the inbox: `TryClaimAsync(messageId, consumer)` returns false on a duplicate | [chapter 8](../tutorial/08-outbox-and-idempotency.md) |
| `IsUniqueViolationOn(name)` | Your extension on `DbUpdateException` — "was this a duplicate-key error on this index?" | See the snippet below |
| `IsSerializationFailure()` | Same idea, for PostgreSQL error `40001` (serializable conflict) | See the snippet below |
| `IMetrics` | Your metrics facade. Every `metrics.Something()` call is one counter or histogram | [chapter 10](../tutorial/10-observability.md#layer-4--metrics) |
| `IAlertService` | Raises a page/alert to a human. `RaiseAsync(severity, title, detail)` | — |
| `IEmailSender` | Sends an email. Assume SMTP or a provider SDK | — |
| `JsonOptions.Web` | A shared `JsonSerializerOptions` (camelCase, case-insensitive) | — |

The two exception helpers are small enough to give you here:

```csharp
// Infrastructure/Persistence/DbExceptionExtensions.cs
public static class DbExceptionExtensions
{
    // SQL Server: 2601/2627 are duplicate key. PostgreSQL: 23505.
    public static bool IsUniqueViolationOn(this DbUpdateException ex, string indexName) =>
        ex.InnerException switch
        {
            SqlException s     => s.Number is 2601 or 2627 && s.Message.Contains(indexName),
            PostgresException p => p.SqlState == "23505" && p.ConstraintName == indexName,
            _ => false
        };

    // PostgreSQL 40001: serializable transaction conflict. Safe to retry.
    public static bool IsSerializationFailure(this DbUpdateException ex) =>
        ex.InnerException is PostgresException { SqlState: "40001" };
}
```

### DbContexts — one per service, exactly as you'd expect

`OrderingDbContext`, `InventoryDbContext`, `PaymentsDbContext`, `LedgerDbContext`, `TransfersDbContext`

Standard EF Core. Each has `DbSet`s for its own entities plus `OutboxMessages` and `InboxMessages`. Nothing surprising — which is why they're not written out.

### Domain types referenced across files

| Symbol | Case study | What it is |
|---|---|---|
| `Reservation`, `Stock` | E-commerce | Inventory's own entities. `Reservation` has `IsReleased`, `IsCommitted`, `ExpiresAtUtc` |
| `PaymentSucceeded`, `PaymentFailed` | E-commerce | Payment outcome events, same shape as the ones in `OrderEvents.cs` |
| `ManualReviewRequired` | E-commerce | An escalation event for a human |
| `Transfer`, `TransferStatus` | Banking | The transfer aggregate, same shape as `Order` |
| `TransferPosted`, `TransferReversed` | Banking | Ledger outcome events |
| `IBalanceService` | Banking | Derives a balance by summing journal entries |
| `IAccountValidator` | Banking | "Can this account be debited?" — returns validity + whether the beneficiary is external |
| `OrderRequest` | Trading | The risk engine's input: user, symbol, side, quantity, price |
| `UserRiskState` | Trading | Cached per-user state: buying power, positions, limits |
| `PriceSnapshot` | Trading | Last price + `IsStale` |
| `RiskStateCache` | Trading | In-memory store of the two above, updated by events |
| `IKillSwitch` | Trading | `IsActive(userId, symbol, out reason)` |
| `TickSerializer` | Market data | Binary serialise/deserialise for `Tick` |
| `ISubscriptionRegistry` | Market data | Which symbols have live subscribers |
| `VehiclePing` | Logistics | The core position record (vehicle, lat, lon, both timestamps, accuracy) |
| `GeoFenceIndex`, `Geohash` | Logistics | The spatial index — the README explains the algorithm |
| `IFenceStateStore` | Logistics | Which fences each vehicle is currently inside |

**None of these change the lesson.** They're the supporting cast.

---

## How every file is laid out

All 26 files follow the same shape. Once you see it, they all read the same way:

```csharp
using ...;

namespace ...;

// ─────────────────────────────────────────────────────────────
// TITLE IN CAPITALS
//
// ← READ THIS FIRST. This banner explains WHY the file exists,
//   what problem it solves, and what would go wrong without it.
//   It is usually 10–30 lines and it is the actual teaching.
// ─────────────────────────────────────────────────────────────

public sealed class Something
{
    // ── Numbered step comments mark the important moments ──
    // ── 1. Do this first, and here is why ──
    ...
}

// ─────────────────────────────────────────────────────────────
// SOMETIMES: a footer listing the tests this file deserves
// ─────────────────────────────────────────────────────────────
```

**The reading recipe:**

1. **Read the top banner.** If you read nothing else in the file, read this. It's the point.
2. **Skim the method signatures** to see the shape.
3. **Read only the `── numbered ──` sections.** Those are the moments that matter.
4. **Ignore the plumbing** — mapping, DTO shuffling, null checks.
5. **If there's a test-list footer, read it.** It tells you every edge case that matters, which is often clearer than the code.

You can get 80% of the value from steps 1 and 5 alone.

---

## Reading order — by concept, not by case study

This is the part that was missing. Don't read case study by case study; the concepts build on each other across them.

### Level 1 — Start here (about 30 minutes)

| # | File | Why start here | Prerequisite |
|---|---|---|---|
| 1 | [`Ecommerce.Contracts/Events/OrderEvents.cs`](01-ecommerce/src/Ecommerce.Contracts/Events/OrderEvents.cs) | Simplest file in the set. Pure data. Teaches event design and versioning | none |
| 2 | [`Ecommerce.Ordering/Domain/Order.cs`](01-ecommerce/src/Ecommerce.Ordering/Domain/Order.cs) | A pure aggregate — no EF, no broker. Just business rules | none |
| 3 | [`Ecommerce.Ordering/Api/OrdersEndpoints.cs`](01-ecommerce/src/Ecommerce.Ordering/Api/OrdersEndpoints.cs) | Ties 1 and 2 together. Shows the outbox write and `202 Accepted` | [ch. 8](../tutorial/08-outbox-and-idempotency.md) |

After these three you understand: events, aggregates, the outbox write, and idempotency keys. That's most of the foundation.

### Level 2 — Consumers and the awkward bits (about 45 minutes)

| # | File | The one idea | Prerequisite |
|---|---|---|---|
| 4 | [`Ecommerce.Inventory/.../OrderPlacedConsumer.cs`](01-ecommerce/src/Ecommerce.Inventory/Consumers/OrderPlacedConsumer.cs) | The inbox pattern, and why the DB constraint is the real guarantee | [ch. 3](../tutorial/03-asynchronous.md), [ch. 8](../tutorial/08-outbox-and-idempotency.md) |
| 5 | [`Ecommerce.Inventory/.../PaymentFailedConsumer.cs`](01-ecommerce/src/Ecommerce.Inventory/Consumers/PaymentFailedConsumer.cs) | **Compensation, and its three guards.** Read the banner twice | [ch. 7](../tutorial/07-saga.md) |
| 6 | [`Ecommerce.Payments/Gateways/AcmePspGateway.cs`](01-ecommerce/src/Ecommerce.Payments/Gateways/AcmePspGateway.cs) | Idempotency keys against a third party, and the `Unknown` outcome | [ch. 8](../tutorial/08-outbox-and-idempotency.md) |

File 5 is the highest value-per-line in the whole folder. An "undo" that runs twice fails **silently**, and that banner explains exactly why.

### Level 3 — Pure logic, no infrastructure (about 40 minutes)

These are the easiest to read because nothing external is involved — and they're where the expensive bugs actually live.

| # | File | The one idea |
|---|---|---|
| 7 | [`Trading.Positions/Domain/PnlCalculator.cs`](04-trading-app/src/Trading.Positions/Domain/PnlCalculator.cs) | Average cost and P&L. Read the four numbered cases |
| 8 | [`MarketData.CandleBuilder/.../CandleAggregator.cs`](03-stock-market-data/src/MarketData.CandleBuilder/Aggregation/CandleAggregator.cs) | Stateful stream aggregation with boundaries and out-of-order data |
| 9 | [`Logistics.GeoFence/.../TransitionDetector.cs`](05-logistics-tracking/src/Logistics.GeoFence/Detection/TransitionDetector.cs) | Three real bugs and their fixes — especially hysteresis |

All three end with a test list. **Read the test lists.** They're a plain-English specification.

### Level 4 — The hard ones (about an hour)

| # | File | The one idea | Prerequisite |
|---|---|---|---|
| 10 | [`Banking.Ledger/Domain/JournalEntry.cs`](02-banking-payments/src/Banking.Ledger/Domain/JournalEntry.cs) | Double-entry, immutability, and a `Money` type | — |
| 11 | [`Banking.Ledger/Services/PostingService.cs`](02-banking-payments/src/Banking.Ledger/Services/PostingService.cs) | ACID + serializable + idempotent, all at once | file 10 |
| 12 | [`Banking.Transfers/Sagas/TransferSaga.cs`](02-banking-payments/src/Banking.Transfers/Sagas/TransferSaga.cs) | **Orchestration.** The longest file — read it as a flowchart | [ch. 7](../tutorial/07-saga.md) |
| 13 | [`Trading.Risk/Checks/RiskEngine.cs`](04-trading-app/src/Trading.Risk/Checks/RiskEngine.cs) | A latency budget as a design constraint; fail-closed | [ch. 9](../tutorial/09-resilience.md) |
| 14 | [`Trading.Risk/State/ReservationLedger.cs`](04-trading-app/src/Trading.Risk/State/ReservationLedger.cs) | Why a cache alone isn't enough | file 13 |

**On file 12 (`TransferSaga.cs`):** don't read it top to bottom. Read the `State` list first, then the `Event` list, then each `During(...)` block as "when I'm in state X and Y happens, do Z". It's a flowchart written in C#, and reading it linearly makes it much harder than it is.

### Level 5 — High-throughput specifics (about 30 minutes)

Only if this is your world:

| # | File | The one idea |
|---|---|---|
| 15 | [`MarketData.Contracts/Tick.cs`](03-stock-market-data/src/MarketData.Contracts/Tick.cs) | Why a struct, why `decimal` not `double` |
| 16 | [`MarketData.FeedHandler/.../TickProducer.cs`](03-stock-market-data/src/MarketData.FeedHandler/Publishing/TickProducer.cs) | The partition key; fire-and-forget; backpressure |
| 17 | [`MarketData.Store/Writers/BatchTickWriter.cs`](03-stock-market-data/src/MarketData.Store/Writers/BatchTickWriter.cs) | **Commit the offset only after a durable write** |
| 18 | [`Logistics.Tracking/Store/LatestPositionStore.cs`](05-logistics-tracking/src/Logistics.Tracking/Store/LatestPositionStore.cs) | Latest-value-wins, TTL as honesty |

---

## If you only read five files

Short on time? These five carry most of the lessons:

1. [`PaymentFailedConsumer.cs`](01-ecommerce/src/Ecommerce.Inventory/Consumers/PaymentFailedConsumer.cs) — compensation is where the silent bugs are
2. [`OrdersEndpoints.cs`](01-ecommerce/src/Ecommerce.Ordering/Api/OrdersEndpoints.cs) — the outbox write and idempotency, in 60 lines
3. [`PostingService.cs`](02-banking-payments/src/Banking.Ledger/Services/PostingService.cs) — what "correctness first" actually looks like in code
4. [`TransitionDetector.cs`](05-logistics-tracking/src/Logistics.GeoFence/Detection/TransitionDetector.cs) — three bugs, three fixes, very concrete
5. [`BatchTickWriter.cs`](03-stock-market-data/src/MarketData.Store/Writers/BatchTickWriter.cs) — ordering of operations as a correctness property

---

## Libraries you'll see

If a type looks unfamiliar, it's probably from one of these. You don't need to know them to follow the logic.

| Library | What you'll see | What it means |
|---|---|---|
| **MassTransit** | `IConsumer<T>`, `ConsumeContext<T>`, `IBus` | A messaging abstraction over RabbitMQ/ASB. `Consume()` is called when a message arrives. `ConsumeContext.MessageId` is the dedupe key |
| **MassTransit sagas** | `MassTransitStateMachine<T>`, `During`, `When`, `TransitionTo` | A state machine DSL. `During(X, When(Y).Do(Z))` = "in state X, on event Y, do Z" |
| **Confluent.Kafka** | `IProducer<K,V>`, `IConsumer<K,V>`, `Message`, `Commit()` | The Kafka client. `Key` sets the partition. `Commit()` moves the read bookmark |
| **EF Core** | `DbContext`, `DbSet`, `SaveChangesAsync`, `DbUpdateException` | You already know this one |
| **StackExchange.Redis** | `IDatabase`, `StringSetAsync`, `SortedSetAddAsync` | The Redis client |
| **Polly** | `AddResilienceHandler`, `AddRetry`, `AddCircuitBreaker` | Retry/breaker/timeout policies. See [ch. 9](../tutorial/09-resilience.md) |
| **SignalR** | `IHubContext<THub, TClient>`, `Clients.Group(...)` | WebSocket push. `Group` = a set of connections |
| **YARP** | Config only, no code | Reverse proxy. See [ch. 5](../tutorial/05-gateway-and-bff.md) |
| **Npgsql** | `BeginBinaryImportAsync` | PostgreSQL's fast bulk-load (`COPY`) |

---

## C# features you may not have used

The samples use .NET 10 / C# 13. A few things that might look odd:

| Syntax | Meaning |
|---|---|
| `public sealed class Foo(IBar bar)` | **Primary constructor.** `bar` is available in every method — no field declaration, no assignment |
| `record` / `sealed record` | Immutable value type with generated equality. `==` compares contents, not references |
| `readonly record struct` | Same, but on the stack. Used in market data to avoid allocations |
| `required Guid Id { get; init; }` | Compiler error if the caller doesn't set it in the object initialiser |
| `order with { Status = X }` | Copy with one property changed. The original is untouched |
| `private readonly List<X> _items = [];` | **Collection expression** — the new way to write `new List<X>()` |
| `Guid.CreateVersion7()` | Time-ordered GUID. Sequential, so it doesn't fragment a clustered index |
| `file sealed record AcmeResponse` | **`file` scope** — visible only inside this one file. Used to lock a third party's wire model away |
| `void Publish(in Tick tick)` | Pass a struct by reference without copying it |
| `is not (OrderState.Routed or OrderState.Unknown)` | Pattern matching. Reads as English |
| `ex is DbUpdateException { SqlState: "40001" }` | **Property pattern** — type check and property check in one |
| `msg.Detail[..Math.Min(1000, len)]` | **Range operator** — take the first N characters |

---

## Turning reading into running

When you want to actually run something:

1. **Start the infrastructure.** Every case study has a real `docker-compose.yml`:
   ```bash
   docker compose up -d
   ```
2. **Create one project**, not five:
   ```bash
   dotnet new web -n Ecommerce.Ordering
   cd Ecommerce.Ordering
   dotnet add package MassTransit.RabbitMQ
   dotnet add package Microsoft.EntityFrameworkCore.SqlServer
   ```
3. **Copy in one file** — start with `Order.cs`. It has no dependencies at all and will compile immediately.
4. **Add the missing pieces as you need them.** `OutboxMessage` is written out in full in [chapter 8](../tutorial/08-outbox-and-idempotency.md#code--the-outbox); copy it. `IMetrics` can be a no-op class for now.
5. **Do the "Now break it" exercises** in that case study's README. That's where the learning actually happens.

**Suggested first build:** e-commerce `Ordering` + `Inventory`, RabbitMQ, no payments. That's exercises 1–5 of [case study 1](01-ecommerce/#now-break-it) and about an evening's work.

---

## Still stuck on a specific file?

Each file's top banner is the explanation. If it isn't enough, the chapter it links to has the same idea with more words and a diagram:

| If you're reading about… | Go to |
|---|---|
| Outbox, inbox, idempotency | [Chapter 8](../tutorial/08-outbox-and-idempotency.md) |
| Sagas, compensation, orchestration | [Chapter 7](../tutorial/07-saga.md) |
| Events vs commands, queues vs topics | [Chapter 3](../tutorial/03-asynchronous.md) |
| Kafka, partitions, replay | [Chapter 4](../tutorial/04-choosing-a-broker.md) |
| Timeouts, retries, circuit breakers | [Chapter 9](../tutorial/09-resilience.md) |
| Who owns which data | [Chapter 6](../tutorial/06-boundaries-and-data.md) |

---

← [All case studies](README.md) · [Back to the map](../README.md)
