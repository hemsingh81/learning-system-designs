# Chapter 3 — Asynchronous Communication

← [Chapter 2](02-synchronous.md) · [Tutorial index](README.md) · Next: [Chapter 4 — Choosing a broker](04-choosing-a-broker.md)

---

## In one line

The caller hands off the message and leaves. Someone else picks it up later.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Asynchronous** | The caller does not wait for the work to finish. Also called "non-blocking". |
| **Broker** | The middleman that holds messages. RabbitMQ, Kafka, Azure Service Bus. |
| **Producer / publisher** | The service that sends a message. |
| **Consumer / subscriber** | The service that reads a message. |
| **Queue** | One line of messages. Each message goes to **exactly one** consumer. Work distribution. |
| **Topic** | A named channel. Each message goes to **every** subscriber. Fan-out. |
| **Command** | "Do this." Named receiver, expects to happen. |
| **Event** | "This happened." No named receiver, past tense, already true. |
| **Consumer group** | A set of consumer instances that share the work of one subscription. |
| **Competing consumers** | Several instances reading the same queue to go faster. |
| **At-least-once delivery** | The broker guarantees the message arrives. It may arrive more than once. |
| **Eventual consistency** | Different services briefly disagree, then agree. |
| **Poison message** | A message that fails every time it is processed. |
| **Dead-letter queue (DLQ)** | A side queue where failed messages are parked for a human to look at. |
| **Offset** | Kafka's bookmark: how far a consumer has read in the log. |

---

## How it works

```
Ordering ─── publish OrderPlaced ──► Broker
Ordering ◄── "got it" (2ms) ──────── Broker
Ordering returns 202 Accepted to the user.   ← done, user is free

                    Broker ──► Payments      (whenever Payments is ready)
                    Broker ──► Notifications (whenever Notifications is ready)
                    Broker ──► Analytics     (whenever Analytics is ready)
```

Three things changed compared to chapter 2:

1. **The user waited 40 ms instead of 4 seconds.**
2. **`Payments` can be down for a minute** and no order is lost — the message waits in the broker.
3. **Adding a fourth consumer requires zero changes to `Ordering`.** It does not know who listens.

---

## Queues vs topics

This is the first real decision, and it is simple:

### Queue — work distribution

```
                    ┌─► Worker 1   (gets messages 1, 4, 7)
[m1 m2 m3 m4 …] ────┼─► Worker 2   (gets messages 2, 5, 8)
                    └─► Worker 3   (gets messages 3, 6, 9)
```

Each message is processed **once**, by whichever worker is free. Add workers to go faster. This is called **competing consumers**.

Use it for: sending emails, resizing images, generating PDFs, processing payments. Anything where the work must happen exactly once and you want to scale it.

### Topic — fan-out

```
                    ┌─► Payments       (gets m1, m2, m3 …)
[m1 m2 m3 m4 …] ────┼─► Notifications  (gets m1, m2, m3 …)
                    └─► Analytics      (gets m1, m2, m3 …)
```

**Every** subscriber gets **every** message. Each has its own independent position.

Use it for: announcing that something happened, when you do not know or care who is interested.

### They combine

Real systems use both at once: a topic fans out to three subscriptions, and each subscription has 5 competing consumer instances behind it.

```
                     ┌─► [Payments subscription]      ─► 5 instances share the work
OrderPlaced topic ───┼─► [Notifications subscription] ─► 2 instances share the work
                     └─► [Analytics subscription]     ─► 1 instance
```

---

## Commands vs events — the distinction that drives everything

This is the most important idea in the chapter. Get it wrong and every later decision is wrong too.

| | **Command** | **Event** |
|---|---|---|
| Means | "Do this" | "This happened" |
| Name | Imperative verb: `ChargePayment` | Past tense: `PaymentSucceeded` |
| Receiver | One, named, known by the sender | Unknown to the sender, zero to many |
| Can it be rejected? | Yes — it is a request | No — it is already a fact |
| Sender knows the outcome? | Usually expects one | No, and does not care |
| Coupling | Sender knows who acts | Sender knows nothing about listeners |
| Transport | Queue | Topic |

### Why the naming rule matters

```csharp
// A command. Ordering is telling Payments what to do.
public record ChargePayment(Guid OrderId, decimal Amount, string Currency);

// An event. Ordering is announcing a fact. Anyone may listen.
public record OrderPlaced(Guid OrderId, Guid CustomerId, decimal Total, DateTime PlacedAtUtc);
```

If you name an event `ProcessOrder`, you have secretly written a command, and you will find yourself asking "did the consumer succeed?" — which is the wrong question to ask about an event.

If you name a command `OrderNeedsCharging`, you have hidden a real dependency behind vague language, and nobody will know that exactly one service must handle it.

### Test for which one you have

Ask: **"Would it be a bug if nobody handled this message?"**

- **Yes, it would be a bug** → it is a command. Use a queue. Alert if the queue grows.
- **No, that is fine** → it is an event. Use a topic. New listeners can appear any time.

> **Diagram: D3 — Commands vs events**
> [Mermaid source](../diagrams/README.md#d3--commands-vs-events)

---

## Code — publishing an event

```csharp
// Ordering/Domain/Order.cs — the event is part of the domain, not an infrastructure detail
public sealed class Order
{
    public Guid Id { get; private set; }
    public OrderStatus Status { get; private set; }
    private readonly List<object> _events = [];
    public IReadOnlyList<object> Events => _events;

    public static Order Place(Guid customerId, IEnumerable<OrderLine> lines)
    {
        var order = new Order
        {
            Id     = Guid.CreateVersion7(),   // time-ordered ID: good for DB index locality
            Status = OrderStatus.Pending
        };

        order._events.Add(new OrderPlaced(
            OrderId:    order.Id,
            CustomerId: customerId,
            Total:      lines.Sum(l => l.UnitPrice * l.Quantity),
            PlacedAtUtc: DateTime.UtcNow));

        return order;
    }
}
```

```csharp
// Ordering/Api/PlaceOrderEndpoint.cs
app.MapPost("/orders", async (
    PlaceOrderRequest req,
    OrderingDbContext db,
    CancellationToken ct) =>
{
    var order = Order.Place(req.CustomerId, req.Lines);

    db.Orders.Add(order);

    // Do NOT publish to the broker here. Write to the outbox in the same transaction.
    // Chapter 8 explains exactly why. This is the single most common bug in the pattern.
    foreach (var e in order.Events)
        db.OutboxMessages.Add(OutboxMessage.From(e));

    await db.SaveChangesAsync(ct);      // one transaction: order + events, both or neither

    return Results.Accepted($"/orders/{order.Id}", new { order.Id, order.Status });
});
```

Note the response: **`202 Accepted`, not `201 Created`**. You are telling the client "I have taken responsibility for this, it is not finished yet". That honesty matters — see eventual consistency below.

---

## Code — consuming an event

```csharp
// Payments/Consumers/OrderPlacedConsumer.cs
public sealed class OrderPlacedConsumer(
    PaymentsDbContext db,
    IPaymentGateway gateway,
    ILogger<OrderPlacedConsumer> log) : IConsumer<OrderPlaced>
{
    public async Task Consume(ConsumeContext<OrderPlaced> ctx)
    {
        var msg = ctx.Message;

        // Idempotency check FIRST. At-least-once delivery means this WILL run twice
        // for the same message at some point. Chapter 8 covers this properly.
        if (await db.Payments.AnyAsync(p => p.OrderId == msg.OrderId, ctx.CancellationToken))
        {
            log.LogInformation("Payment for order {OrderId} already exists, skipping", msg.OrderId);
            return;                       // not an error. A normal, expected outcome.
        }

        var result = await gateway.ChargeAsync(msg.OrderId, msg.Total, ctx.CancellationToken);

        db.Payments.Add(new Payment(msg.OrderId, msg.Total, result.Status));

        // Announce the outcome as a new event, through our own outbox.
        db.OutboxMessages.Add(OutboxMessage.From(result.Succeeded
            ? new PaymentSucceeded(msg.OrderId, result.TransactionId)
            : new PaymentFailed(msg.OrderId, result.FailureReason)));

        await db.SaveChangesAsync(ctx.CancellationToken);
    }
}
```

Three things to notice, and they are all deliberate:

1. **Idempotency check is the first line.** Not an optimisation — a correctness requirement.
2. **The consumer publishes its own event** rather than calling `Ordering` back over HTTP. `Payments` does not need to know `Ordering` exists.
3. **The outcome event goes through the outbox too.** Same reason as before.

---

## Request-reply over a broker — usually a smell

You can do request-reply asynchronously: send a message, include a `ReplyTo` address, wait for a response message.

This is occasionally right (long-running work with a correlation ID). Usually it is a smell, because you have paid all the costs of async — a broker to run, correlation to manage, duplicate handling, harder debugging — and kept the one cost of sync: **the caller is still waiting**.

If the caller must wait, use HTTP. It is simpler and every tool understands it.

The honest exception: the work takes 30 seconds and you want it to survive a restart. Then a broker is right — but return `202 Accepted` with a status URL, and let the client poll or receive a push. Do not make the original HTTP request wait.

---

## Sharp edges

### Edge 1 — Eventual consistency, in the user's face

This is not a theoretical concern. It is a support ticket.

```
10:00:00.000  User clicks "Place order"
10:00:00.040  Ordering returns 202. Order status = Pending.
10:00:00.041  User is redirected to "My Orders"
10:00:00.045  The page loads... and the order is NOT THERE YET,
              because the read model has not been updated.
10:00:00.900  PaymentSucceeded arrives. Order status = Confirmed.
```

The user saw an empty page and thinks their money vanished. They call support.

**How to handle it — pick one, deliberately:**

| Technique | How it works | Best for |
|---|---|---|
| **Show the pending state** | Return the order immediately with status "Processing". Never hide it. | Almost always the right answer |
| **Read your own writes** | After a write, read from the primary, not a replica, for that user for a few seconds | Lists and dashboards |
| **Push the update** | SignalR / WebSocket tells the browser the moment status changes | Best experience, more moving parts |
| **Optimistic UI** | The client shows the order as if it succeeded, and corrects itself if it did not | Fast-feeling apps; needs care to not lie |

**What never works:** pretending it is not eventually consistent. The gap is real. Design for it in the UI.

### Edge 2 — Ordering is weaker than you think

What you actually get:

| Broker | Ordering guarantee |
|---|---|
| Kafka | Ordered **within one partition**. Nothing across partitions. |
| Azure Service Bus | Ordered only **within a session**. |
| RabbitMQ | Ordered per queue with **one** consumer. Add a second consumer and ordering is gone. |
| SQS standard | No ordering at all. SQS FIFO gives ordering per message group. |

Two consumer instances process in parallel. Message 2 can finish before message 1. Always.

**How to get ordering where you need it:** pick a **partition key** so all related messages take the same path.

```csharp
// All events for one order go to the same partition → processed in order.
// Different orders go to different partitions → still parallel and fast.
await producer.ProduceAsync("orders", new Message<string, string>
{
    Key   = orderId.ToString(),   // ← the partition key. This is the whole trick.
    Value = json
});
```

Choose the key carefully: it decides both ordering and parallelism. Key by `orderId` and you get per-order ordering with high parallelism. Key by a constant and you get total ordering with zero parallelism.

### Edge 3 — Duplicates are normal, not exceptional

At-least-once delivery is what real brokers give you. Exactly-once across a broker and your database does not exist, whatever a vendor's marketing says.

So duplicates happen. Routinely. Causes:

- The consumer processed the message, then crashed before acknowledging it. The broker redelivers.
- The consumer was slow, the broker's lock timed out, and it redelivered while the first attempt was still running.
- The producer's outbox relay crashed after publishing but before marking sent.
- A network blip caused the ack to be lost.

**The fix is not to prevent duplicates. It is to make processing them harmless.** That is idempotency, and it is [chapter 8](08-outbox-and-idempotency.md).

### Edge 4 — Poison messages and the DLQ

One message fails every time. Maybe a null field, maybe a bad JSON shape, maybe a bug in your handler.

Without a dead-letter queue: it is retried forever, blocks the queue behind it, and fills your logs. The queue stops moving. Everything behind that one message is stuck.

With a DLQ: after N attempts the broker moves it to a side queue. The main queue keeps flowing. A human looks at the DLQ later.

```csharp
// MassTransit: 3 immediate retries, then 3 more spaced out, then dead-letter it
cfg.ReceiveEndpoint("payments-order-placed", e =>
{
    e.UseMessageRetry(r =>
    {
        r.Immediate(3);                                        // transient blips
        r.Intervals(TimeSpan.FromSeconds(5),
                    TimeSpan.FromSeconds(30),
                    TimeSpan.FromMinutes(2));                  // slower recovery
    });

    e.ConfigureConsumer<OrderPlacedConsumer>(ctx);
    // After all retries are exhausted → _error queue automatically.
});
```

**Operational rule: an empty DLQ is not the goal. A monitored DLQ is.** Alert on `DLQ depth > 0`. A message sitting there unnoticed for a week is a customer whose order never shipped.

### Edge 5 — Debugging is genuinely harder

With synchronous calls you get a stack trace. With async you get:

- A log line in `Ordering` at 10:00:00
- A log line in `Payments` at 10:00:01
- A log line in `Notifications` at 10:00:01
- No connection between them

You cannot work this way. You need a **correlation ID** flowing through every message, and distributed tracing. This is not optional with async — it is the price of entry. See [chapter 10](10-observability.md).

### Edge 6 — Queue depth is your most important metric

A growing queue means consumers are slower than producers. If nothing changes, it grows until the broker runs out of disk.

Watch these three:

| Metric | What it tells you | Alert when |
|---|---|---|
| **Queue depth / consumer lag** | Are you falling behind? | Growing steadily for 5+ minutes |
| **Message age (oldest unprocessed)** | How stale is your data? | Above your business tolerance |
| **DLQ depth** | Are messages failing permanently? | Above 0 |

---

## When to use asynchronous

| Case | Why |
|---|---|
| The caller does not need the answer to continue | The whole point |
| Several services care about the same fact | One event, many listeners, no code change to add another |
| The work can absorb delay | Emails, indexing, reports, analytics |
| You want independent failure domains | The consumer can be down without failing the caller |
| Traffic is spiky | The queue absorbs the spike; consumers drain it at their own pace |
| The work is slow | Never make a user wait for a 30-second job |

## When not to use it

| Case | Why not |
|---|---|
| The caller needs the answer to respond | You are just adding a broker to a blocking call |
| Strict global ordering across everything | Very hard, kills parallelism; reconsider the design |
| Simple internal read, both services are yours | An HTTP GET is simpler and a broker is real operational cost |
| Your team has never run a broker and the deadline is Friday | Be honest. A broker you cannot operate is a liability. |

---

## Try it yourself

**Build it.** `Ordering` publishes `OrderPlaced` to a topic. `Payments` and `Notifications` both subscribe. Use RabbitMQ via Docker.

**Now break it, in this order:**

1. **Stop `Payments`.** Place 10 orders. All 10 succeed with `202`. Start `Payments` and watch it catch up. *That is the resilience you bought.*
2. **Deliver the same message twice** (comment out the ack, or publish it twice by hand). Watch the card get charged twice. *That is why idempotency is mandatory.*
3. **Add the idempotency check.** Repeat step 2. One charge. *That is chapter 8.*
4. **Run two `Payments` instances.** Publish 100 messages. Log the order in which each instance handles them. Notice ordering is gone.
5. **Add a partition key** on `orderId`. Publish 100 messages across 10 orders. Notice each order's messages are ordered, but different orders still run in parallel.
6. **Throw an exception for one specific message.** Watch it retry, then land in the `_error` queue. Confirm the other messages kept flowing past it.
7. **Publish 100,000 messages with the consumer stopped.** Watch queue depth climb. Now start one consumer, and measure how long it takes to drain. That number is your recovery time after an outage — and it is a number you should actually know.

---

← [Chapter 2](02-synchronous.md) · [Tutorial index](README.md) · Next: [Chapter 4 — Choosing a broker](04-choosing-a-broker.md)
