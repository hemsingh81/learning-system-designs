# Chapter 8 — The Outbox and Idempotent Consumers

← [Chapter 7](07-saga.md) · [Tutorial index](README.md) · Next: [Chapter 9 — Resilience](09-resilience.md)

---

## In one line

Writing to your database and publishing to a broker are two separate acts, and the gap between them is where data goes wrong forever.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Dual write** | Writing the same fact to two places (your DB and the broker) without a shared transaction. |
| **Outbox** | A table in **your own** database where you save outgoing messages inside the same transaction as your data. |
| **Relay / dispatcher** | A background worker that reads the outbox and publishes to the broker. |
| **Inbox** | A table recording which incoming message IDs you have already processed. |
| **Idempotent** | Doing it twice has the same effect as doing it once. |
| **Natural idempotency** | The operation is already safe to repeat: `SET status = 'Confirmed'`. |
| **CDC (Change Data Capture)** | Reading the database's own transaction log to detect changes. |
| **Divergence** | Two systems that should agree, and no longer do. |

---

## The bug almost everyone ships first

This code looks completely reasonable. It is in production in thousands of companies. It is broken.

```csharp
// ✗ THE DUAL-WRITE BUG
app.MapPost("/orders", async (PlaceOrderRequest req, OrderingDbContext db, IBus bus) =>
{
    var order = Order.Place(req.CustomerId, req.Lines);

    db.Orders.Add(order);
    await db.SaveChangesAsync();                                    // ① commits

    await bus.Publish(new OrderPlaced(order.Id, order.Total));      // ② separate act

    return Results.Accepted();
});
```

There is a gap between ① and ②. Anything can happen in that gap:

- The process is killed (deploy, pod eviction, OOM, scale-down).
- The broker is unreachable for 30 seconds.
- The network drops the publish.
- The machine loses power.

### What the failures actually look like

**Failure A — crash between ① and ②:**
```
Order o-123 exists in the database.  Status: Pending.
OrderPlaced was never published.
Payments never charges. Notifications never emails.
The order sits at Pending. Forever.
Nothing in any log says "error", because nothing errored.
```
The customer's order silently disappears into a state nobody monitors. You find out from a support ticket three days later.

**Failure B — swap the order to publish first:**
```csharp
await bus.Publish(new OrderPlaced(order.Id, order.Total));   // ② first
await db.SaveChangesAsync();                                 // ① crashes here
```
```
OrderPlaced was published. Payments CHARGED THE CARD.
The order does not exist in the database.
The customer has been billed for an order you have no record of.
```
That is worse. There is no ordering of these two lines that is safe.

**Failure C — the "clever" fix:**
```csharp
using var tx = await db.Database.BeginTransactionAsync();
db.Orders.Add(order);
await db.SaveChangesAsync();
await bus.Publish(evt);      // if this throws, we roll back. Clever?
await tx.CommitAsync();
```
Still broken. The publish succeeded and the message is *already gone* to the broker. If `CommitAsync` then fails, you have rolled back the order but the event is out in the world. You cannot un-publish.

> **The core truth:** a database transaction cannot include a network call to a different system. Every attempt to make it look like it can is a bug with better camouflage.

---

## The fix: the transactional outbox

Stop trying to do two things atomically. Do **one** thing: write to your own database.

```
BEGIN TRANSACTION
   INSERT INTO orders  (…)          ← the business fact
   INSERT INTO outbox  (…)          ← the intention to publish
COMMIT                              ← both, or neither. One database. Real atomicity.

   … later, a separate background worker …

   SELECT * FROM outbox WHERE processed_at IS NULL
   publish each to the broker
   UPDATE outbox SET processed_at = now()
```

Now the gap has moved somewhere harmless. If the relay crashes before marking a row sent, it republishes on restart. That produces a **duplicate**, not a **loss** — and duplicates are solvable (second half of this chapter). Loss is not.

> **Outbox turns an unsolvable problem (loss) into a solvable one (duplication).** That is the whole trick.

---

> **Diagram: D8 — The dual-write problem and the Outbox**
> [Mermaid source](../diagrams/README.md#d8--the-dual-write-problem-and-the-outbox)

---

## Code — the outbox

### The table

```csharp
// Infrastructure/Outbox/OutboxMessage.cs
public sealed class OutboxMessage
{
    public long      Id          { get; private set; }        // identity, gives us ordering
    public Guid      MessageId   { get; private set; }        // stable ID for consumer dedupe
    public string    Type        { get; private set; } = "";  // assembly-qualified event type
    public string    Payload     { get; private set; } = "";  // JSON
    public string?   CorrelationId { get; private set; }      // for tracing (chapter 10)
    public DateTime  OccurredAtUtc { get; private set; }
    public DateTime? ProcessedAtUtc { get; private set; }
    public int       Attempts    { get; private set; }
    public string?   LastError   { get; private set; }

    public static OutboxMessage From(object evt, string? correlationId = null) => new()
    {
        MessageId     = Guid.CreateVersion7(),
        Type          = evt.GetType().AssemblyQualifiedName!,
        Payload       = JsonSerializer.Serialize(evt, evt.GetType(), JsonOptions.Web),
        CorrelationId = correlationId ?? Activity.Current?.TraceId.ToString(),
        OccurredAtUtc = DateTime.UtcNow
    };

    public void MarkProcessed()          => ProcessedAtUtc = DateTime.UtcNow;
    public void MarkFailed(string error) { Attempts++; LastError = error[..Math.Min(1000, error.Length)]; }
}
```

```csharp
// Infrastructure/Configurations/OutboxMessageConfiguration.cs
public sealed class OutboxMessageConfiguration : IEntityTypeConfiguration<OutboxMessage>
{
    public void Configure(EntityTypeBuilder<OutboxMessage> b)
    {
        b.ToTable("OutboxMessages");
        b.HasKey(x => x.Id);

        // THE index that matters. The relay's only query is
        // "unprocessed rows, oldest first" — this makes it a cheap ranged scan.
        b.HasIndex(x => new { x.ProcessedAtUtc, x.Id })
         .HasFilter("[ProcessedAtUtc] IS NULL")
         .HasDatabaseName("IX_Outbox_Pending");

        b.Property(x => x.Payload).HasColumnType("nvarchar(max)");
        b.Property(x => x.Type).HasMaxLength(500);
    }
}
```

### Writing to it — one transaction

```csharp
// ✓ CORRECT
app.MapPost("/orders", async (
    PlaceOrderRequest req,
    OrderingDbContext db,
    CancellationToken ct) =>
{
    var order = Order.Place(req.CustomerId, req.Lines);

    db.Orders.Add(order);

    foreach (var e in order.Events)
        db.OutboxMessages.Add(OutboxMessage.From(e));

    await db.SaveChangesAsync(ct);   // ← ONE transaction. Order + events. Both, or neither.

    return Results.Accepted($"/orders/{order.Id}", new { order.Id, order.Status });
});
```

No `IBus` in the endpoint at all. That absence is the point.

### The relay

```csharp
// Infrastructure/Outbox/OutboxRelay.cs
public sealed class OutboxRelay(
    IServiceScopeFactory scopes,
    IBus bus,
    ILogger<OutboxRelay> log) : BackgroundService
{
    private const int BatchSize = 100;
    private static readonly TimeSpan Idle = TimeSpan.FromMilliseconds(500);

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                var published = await PublishBatchAsync(ct);

                // Busy? Loop again immediately. Idle? Back off so we are not hammering the DB.
                if (published == 0) await Task.Delay(Idle, ct);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                log.LogError(ex, "Outbox relay pass failed; retrying");
                await Task.Delay(TimeSpan.FromSeconds(5), ct);
            }
        }
    }

    private async Task<int> PublishBatchAsync(CancellationToken ct)
    {
        using var scope = scopes.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<OrderingDbContext>();

        // Ordering by Id preserves publish order. If two instances run this, use
        // a row lock (SQL Server: UPDLOCK, READPAST) or SELECT … FOR UPDATE SKIP LOCKED.
        var batch = await db.OutboxMessages
            .Where(m => m.ProcessedAtUtc == null)
            .OrderBy(m => m.Id)
            .Take(BatchSize)
            .ToListAsync(ct);

        if (batch.Count == 0) return 0;

        foreach (var msg in batch)
        {
            try
            {
                var type = Type.GetType(msg.Type)
                           ?? throw new InvalidOperationException($"Unknown type {msg.Type}");
                var evt  = JsonSerializer.Deserialize(msg.Payload, type, JsonOptions.Web)!;

                await bus.Publish(evt, type, c =>
                {
                    // The SAME MessageId every time this row is published.
                    // This is what lets consumers detect a redelivery. Critical.
                    c.MessageId = msg.MessageId;
                    if (msg.CorrelationId is not null)
                        c.Headers.Set("X-Correlation-Id", msg.CorrelationId);
                }, ct);

                msg.MarkProcessed();
            }
            catch (Exception ex)
            {
                // Leave it unprocessed. Next pass retries it. Do not lose it.
                msg.MarkFailed(ex.ToString());
                log.LogWarning(ex, "Outbox message {MessageId} failed (attempt {Attempts})",
                    msg.MessageId, msg.Attempts);
            }
        }

        await db.SaveChangesAsync(ct);
        return batch.Count;
    }
}
```

**The critical line is `c.MessageId = msg.MessageId`.** Because the row keeps the same `MessageId` across republishes, the consumer can recognise a redelivery. If you generated a fresh ID on each publish attempt, every retry would look like a brand-new message and dedupe would be impossible.

### Two ways to get messages out of the outbox

| Approach | How | Pros | Cons |
|---|---|---|---|
| **Polling** (above) | Background worker queries every 500 ms | Simple, no extra infrastructure, works anywhere | Small latency; constant light DB load |
| **CDC** (Debezium) | Read the database transaction log | No polling, very low latency, no app code | Extra infrastructure; DB-specific setup; another thing to operate |

Start with polling. A 500 ms delay is invisible next to the eventual consistency you already have. Move to CDC only when you can measure that polling is a problem.

**Or use a library.** MassTransit has this built in and it is well tested:

```csharp
builder.Services.AddMassTransit(x =>
{
    x.AddEntityFrameworkOutbox<OrderingDbContext>(o =>
    {
        o.QueryDelay = TimeSpan.FromMilliseconds(500);
        o.UseSqlServer();
        o.UseBusOutbox();       // bus.Publish() inside a DbContext transaction → goes to the outbox
    });
});
```

With this on, `await bus.Publish(evt)` before `SaveChangesAsync` writes to the outbox instead of the broker. Same guarantee, less code you maintain.

---

## The other half: idempotent consumers

The outbox guarantees **at-least-once**. So you will process duplicates. This is not an edge case — it is normal operation.

### Where duplicates come from

| Cause | Frequency |
|---|---|
| Relay crashed after publishing, before marking sent | Every deploy, potentially |
| Broker redelivered because the ack was lost | Regularly |
| Consumer's lock expired while it was still working | Under load, often |
| Consumer processed the message, then crashed before acking | Every deploy |
| Someone replayed a Kafka topic to fix a bug | Whenever you fix a bug |
| Producer retried a publish that had actually succeeded | Occasionally |

### Level 1 — Natural idempotency (best, if you can get it)

Some operations are already safe to repeat. Prefer these:

```csharp
// ✓ Safe to run 100 times. The end state is identical.
order.Status = OrderStatus.Confirmed;

// ✗ NOT safe. Run it twice and the number is wrong.
account.Balance -= amount;
```

The rule: **set absolute values, do not apply deltas.** When you must apply a delta, you need level 2 or 3.

### Level 2 — The inbox (works for everything)

Record every message ID you have processed, in the same transaction as the work.

```csharp
// Infrastructure/Inbox/InboxMessage.cs
public sealed class InboxMessage
{
    public Guid     MessageId    { get; init; }        // primary key
    public string   Consumer     { get; init; } = "";  // same message, different consumers
    public DateTime ProcessedAtUtc { get; init; }
}
```

```csharp
// Infrastructure/Inbox/InboxMessageConfiguration.cs
b.HasKey(x => new { x.MessageId, x.Consumer });
// Composite key: OrderPlaced can be processed once by Payments AND once by Notifications.
// A single-column key would make the second consumer silently skip every message.
```

```csharp
// Payments/Consumers/OrderPlacedConsumer.cs
public sealed class OrderPlacedConsumer(
    PaymentsDbContext db,
    IPaymentGateway gateway) : IConsumer<OrderPlaced>
{
    private const string ConsumerName = nameof(OrderPlacedConsumer);

    public async Task Consume(ConsumeContext<OrderPlaced> ctx)
    {
        var messageId = ctx.MessageId
            ?? throw new InvalidOperationException("MessageId is required for idempotency");

        // 1. Have we seen it?
        var seen = await db.InboxMessages
            .AnyAsync(x => x.MessageId == messageId && x.Consumer == ConsumerName,
                      ctx.CancellationToken);

        if (seen) return;                    // duplicate. Normal. Not an error.

        // 2. Do the work
        var result = await gateway.ChargeAsync(
            ctx.Message.OrderId, ctx.Message.Total, ctx.CancellationToken);

        // 3. Record the work, the outcome event, AND the inbox row — one transaction.
        //    If the process dies before this commit, nothing happened and we retry cleanly.
        db.Payments.Add(new Payment(ctx.Message.OrderId, ctx.Message.Total, result.Status));

        db.OutboxMessages.Add(OutboxMessage.From(result.Succeeded
            ? new PaymentSucceeded(ctx.Message.OrderId, result.TransactionId)
            : new PaymentFailed(ctx.Message.OrderId, result.FailureReason)));

        db.InboxMessages.Add(new InboxMessage
        {
            MessageId      = messageId,
            Consumer       = ConsumerName,
            ProcessedAtUtc = DateTime.UtcNow
        });

        await db.SaveChangesAsync(ctx.CancellationToken);
    }
}
```

**Note the race.** Two instances can both pass the check at step 1 before either commits. The primary key on `(MessageId, Consumer)` is your real defence — the second commit fails with a duplicate-key error. Handle it as success:

```csharp
try
{
    await db.SaveChangesAsync(ctx.CancellationToken);
}
catch (DbUpdateException ex) when (ex.IsUniqueConstraintViolation())
{
    // Another instance won the race and did the same work. Nothing to do.
    // Do NOT rethrow — rethrowing causes a broker retry, and a third attempt.
    return;
}
```

The check at step 1 is the cheap fast path. The primary key is the correctness guarantee. You need both.

### Level 3 — Idempotency keys at the boundary

When the side effect is in **someone else's** system, your inbox cannot help — the charge already happened over there. Instead, make *their* API idempotent by sending a key.

```csharp
// Infrastructure/Payments/StripeLikeGateway.cs
public async Task<ChargeResult> ChargeAsync(Guid orderId, decimal amount, CancellationToken ct)
{
    var request = new HttpRequestMessage(HttpMethod.Post, "/v1/charges")
    {
        Content = JsonContent.Create(new { amount = (long)(amount * 100), currency = "inr" })
    };

    // Derived from the order, so it is IDENTICAL on every retry.
    // The provider returns the original charge instead of creating a second one.
    // Never use Guid.NewGuid() here — that defeats the entire mechanism.
    request.Headers.Add("Idempotency-Key", $"order-charge-{orderId}");

    using var res = await http.SendAsync(request, ct);
    return await res.Content.ReadFromJsonAsync<ChargeResult>(cancellationToken: ct)
           ?? throw new InvalidOperationException("empty gateway response");
}
```

Every serious payment provider supports this header. Use it. It is the difference between "we might double-charge" and "we cannot double-charge".

### Also expose idempotency on your own write APIs

```csharp
app.MapPost("/orders", async (
    PlaceOrderRequest req,
    [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey,
    OrderingDbContext db,
    CancellationToken ct) =>
{
    if (string.IsNullOrWhiteSpace(idempotencyKey))
        return Results.BadRequest("Idempotency-Key header is required");

    // Retry from a flaky mobile network? Return the SAME order, not a second one.
    var existing = await db.Orders
        .FirstOrDefaultAsync(o => o.IdempotencyKey == idempotencyKey, ct);

    if (existing is not null)
        return Results.Accepted($"/orders/{existing.Id}", new { existing.Id, existing.Status });

    // … create, outbox, save …
});
```

This single header removes an entire class of "the customer tapped Pay twice on a bad connection" bugs.

---

## Sharp edges

**Edge 1 — The outbox table grows without limit.** At 1,000 orders/minute you add ~1.4 million rows a day. Every relay query gets slower. **Fix:** delete processed rows older than a few days, on a schedule:

```csharp
// Keep a short window for debugging, then delete. Batch it so you do not lock the table.
var cutoff = DateTime.UtcNow.AddDays(-3);
int deleted;
do
{
    deleted = await db.OutboxMessages
        .Where(m => m.ProcessedAtUtc != null && m.ProcessedAtUtc < cutoff)
        .Take(5_000)
        .ExecuteDeleteAsync(ct);

    await Task.Delay(100, ct);   // be kind to the database
} while (deleted > 0);
```

Same for the inbox — but keep the inbox window **longer than your broker's maximum retention/retry window**, or a very late redelivery will be treated as new. If Kafka retains 7 days, keep inbox rows for at least 8.

**Edge 2 — Two relay instances publishing the same row twice.** Both read the same batch. Fix with a row lock:

```sql
-- SQL Server
SELECT TOP (100) * FROM OutboxMessages WITH (UPDLOCK, READPAST)
WHERE ProcessedAtUtc IS NULL ORDER BY Id;

-- PostgreSQL
SELECT * FROM outbox_messages
WHERE processed_at IS NULL ORDER BY id LIMIT 100
FOR UPDATE SKIP LOCKED;
```

Or run a single relay instance and accept that it is a small, restartable single point of failure. Or use a library that already handles it.

**Edge 3 — Outbox ordering is not guaranteed end to end.** Rows are published in `Id` order, but if the relay publishes 100 messages and consumers process them in parallel, order is lost after the broker. If you need ordering, set a partition key ([chapter 3](03-asynchronous.md)) — the outbox alone does not give you ordering.

**Edge 4 — A poison outbox row blocks everything behind it.** A row whose type no longer exists (you deleted the event class) fails forever. Because the relay processes in `Id` order, everything behind it may stall. Fix: cap attempts, then move the row to a `dead` state and alert — the same shape as a DLQ, but for outgoing messages.

**Edge 5 — Forgetting `MessageId` breaks consumer dedupe silently.** If your publish path does not carry a stable `MessageId`, the inbox check never matches and every duplicate is processed. Nothing errors. You just double-charge people. Assert it in a test.

**Edge 6 — The inbox check without the primary key is a race, not a fix.** A `SELECT` then `INSERT` with no unique constraint will let two concurrent instances both do the work. The constraint is the guarantee; the `SELECT` is just an optimisation.

**Edge 7 — Non-transactional side effects inside the consumer.** If your handler sends an email *and* writes the inbox row, the email is not in the transaction. A crash between them means a duplicate email on retry. Either accept it (an extra email is survivable), or publish an `EmailRequested` event through your outbox and let a dedicated consumer send it — moving the problem to a place where a duplicate is cheap.

---

## When you need this

**You need the outbox whenever you publish a message about a state change you just persisted.** That is nearly every event in nearly every system.

You can skip it when:

| Situation | Why it is safe |
|---|---|
| The message is pure telemetry and loss is acceptable | Losing a metric is not a data-integrity bug |
| The broker **is** your database (event sourcing on Kafka) | There is only one write; no dual write exists |
| You publish nothing and only expose HTTP reads | No messages, no problem |

**You need idempotent consumers always.** There is no configuration, broker, or cloud tier that removes this requirement. At-least-once is the ground truth.

---

## Try it yourself

**Build the bug first.** Write the dual-write version. Then, in `Payments`, kill the process between `SaveChangesAsync` and `Publish`:

```csharp
db.Orders.Add(order);
await db.SaveChangesAsync();
Environment.FailFast("simulating a pod eviction");   // ← right in the gap
await bus.Publish(evt);
```

Look at your database. The order is `Pending`. No event was ever sent. Nothing is in the error log. **Sit with that for a moment** — this is the failure you almost certainly have in production right now, and it makes no noise at all.

**Now fix it and break it again:**

1. Add the outbox. Repeat the `FailFast` test. Restart. Watch the relay publish the event that was waiting. Nothing lost.
2. Kill the relay *after* `bus.Publish` but *before* `SaveChangesAsync`. Restart. Watch the same message publish twice. That duplicate is the price of the fix.
3. Confirm the duplicate causes a double charge. Now add the inbox. Repeat. One charge.
4. Remove `c.MessageId = msg.MessageId` from the relay. Repeat step 3. Watch dedupe stop working with no error anywhere. Put it back.
5. Run two consumer instances and deliver the same message to both at the same instant. Without the composite primary key, both do the work. Add the key, catch the duplicate-key error, treat it as success.
6. Add a second consumer for the same event. If your inbox key is only `MessageId`, the second consumer silently processes nothing. Change it to `(MessageId, Consumer)`.
7. Insert 5 million processed outbox rows. Measure the relay query. Add the filtered index. Measure again. Add the cleanup job.
8. Send the same `POST /orders` twice with the same `Idempotency-Key`. Confirm you get one order and the same ID both times.

---

← [Chapter 7](07-saga.md) · [Tutorial index](README.md) · Next: [Chapter 9 — Resilience](09-resilience.md)
