# Chapter 4 — Choosing a Broker Without Copying Someone Else's Homework

← [Chapter 3](03-asynchronous.md) · [Tutorial index](README.md) · Next: [Chapter 5 — Gateway and BFF](05-gateway-and-bff.md)

---

## In one line

Four tools, four different mental models — pick the one whose model matches your problem, not the one your favourite tech blog used.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Ack (acknowledge)** | The consumer tells the broker "I finished this one, delete it." |
| **Replay** | Reading old messages again, from the past. Only possible if the broker kept them. |
| **Retention** | How long the broker keeps a message after it was read. |
| **Partition** | A slice of a Kafka topic. Ordering is guaranteed inside one partition only. |
| **Session (Azure Service Bus)** | A group of related messages that one consumer handles in order. |
| **Sidecar** | A small helper process running next to your service, handling infrastructure for it. |
| **Smart broker** | The broker does routing and retry logic. The consumer stays simple. |
| **Dumb broker** | The broker just stores an ordered log. The consumer tracks its own position. |

---

## The four options, and their mental models

The mental model is the thing to remember. Everything else follows from it.

### RabbitMQ — "smart broker, dumb consumer"

The broker holds the intelligence. You describe your routing in the broker (exchanges, bindings, routing keys), and it decides where each message goes. Each message is acknowledged individually. Once acked, it is **gone**.

Think of it as a **post office**. It sorts and delivers. Once delivered, it does not keep a copy.

```csharp
// Per-message ack is the core of the model
var consumer = new AsyncEventingBasicConsumer(channel);
consumer.ReceivedAsync += async (_, ea) =>
{
    try
    {
        await HandleAsync(ea.Body.ToArray());
        await channel.BasicAckAsync(ea.DeliveryTag, multiple: false);       // done, delete it
    }
    catch (TransientException)
    {
        await channel.BasicNackAsync(ea.DeliveryTag, false, requeue: true);  // try again later
    }
    catch (PermanentException)
    {
        await channel.BasicNackAsync(ea.DeliveryTag, false, requeue: false); // → dead-letter
    }
};

await channel.BasicConsumeAsync("payments", autoAck: false, consumer);
```

**Shines when:** you are distributing tasks. Per-message retry, per-message dead-lettering, priority queues, complex routing rules, message TTL.

**Costs you:** no replay — an acked message is gone forever. Routing logic lives in broker config, so it is not in your source control unless you are disciplined about infrastructure-as-code. Throughput ceiling is lower than Kafka (tens of thousands/sec, not millions).

---

### Kafka — "dumb broker, smart consumer"

The broker is an **append-only log**. It does not track who read what — the consumer tracks its own position (the offset). Messages stay for the retention period whether or not anyone read them.

Think of it as a **DVR recording a channel**. Everything is on the tape. Any viewer can rewind to any point.

```csharp
// The consumer owns its position. Committing an offset is not the same as acking a message.
var config = new ConsumerConfig
{
    BootstrapServers = "kafka:9092",
    GroupId          = "payments-service",
    AutoOffsetReset  = AutoOffsetReset.Earliest,   // new group: start from the beginning
    EnableAutoCommit = false                       // commit manually, after real work
};

using var consumer = new ConsumerBuilder<string, string>(config).Build();
consumer.Subscribe("orders");

while (!ct.IsCancellationRequested)
{
    var result = consumer.Consume(ct);
    await HandleAsync(result.Message.Key, result.Message.Value);
    consumer.Commit(result);      // move my bookmark forward
}
```

Because the log is kept, you can do things that are impossible with a queue:

```csharp
// Rebuild a broken read model by replaying 30 days of history
consumer.Assign(new TopicPartitionOffset("orders", new Partition(0), new Offset(0)));
```

**Shines when:** you need replay (rebuild a projection, onboard a new consumer with full history, fix a bug and reprocess), many independent consumers of the same stream, ordering per key, very high throughput (millions/sec), and stream processing.

**Costs you:** real operational weight (brokers, coordination, partition rebalancing, retention tuning). No per-message ack — if message 5 of 100 fails, you cannot "nack just that one"; you must decide to skip it, retry it in place, or route it to an error topic yourself. Consumer count is capped by partition count.

---

### Azure Service Bus — "managed enterprise messaging"

RabbitMQ's model, plus enterprise features, minus the operations. You do not run a server.

Think of it as a **courier company with a signed contract**. Guaranteed FIFO on request, scheduled delivery, duplicate detection — and someone else's staff keep the trucks running.

```csharp
// Sessions give you ordered processing per key, which is genuinely hard to build yourself
var processor = client.CreateSessionProcessor("orders", "payments", new ServiceBusSessionProcessorOptions
{
    MaxConcurrentSessions = 20,       // 20 orders in parallel...
    SessionIdleTimeout    = TimeSpan.FromSeconds(30)
});                                   // ...but strictly in order within each order

processor.ProcessMessageAsync += async args =>
{
    await HandleAsync(args.Message.Body.ToString());
    await args.CompleteMessageAsync(args.Message);        // ack
};

// Built-in duplicate detection: the broker drops a repeat MessageId inside a time window
await sender.SendMessageAsync(new ServiceBusMessage(json)
{
    MessageId = $"order-placed-{orderId}",   // broker-level dedupe key
    SessionId = orderId.ToString()           // ordering key
});
```

**Shines when:** you are on Azure, you want FIFO per key without building it, you need scheduled delivery ("run this in 3 days"), broker-level duplicate detection, transactions across queues, and you have no platform team to run a broker.

**Costs you:** cloud lock-in (the API is not portable). Cost grows with volume. Throughput ceiling well below Kafka. Premium tier needed for the good features.

---

### Dapr — "a portability layer over any of the above"

Dapr is not a broker. It is a **sidecar** that gives you one HTTP/gRPC API for pub/sub, and the actual broker is a config file.

Think of it as a **universal power adapter**. Your device has one plug; the adapter handles the country.

```csharp
// Your code. Notice: no broker name, no broker SDK, no broker types.
app.MapPost("/orders", async (PlaceOrderRequest req, DaprClient dapr) =>
{
    var order = Order.Place(req.CustomerId, req.Lines);
    await dapr.PublishEventAsync("pubsub", "orders", new OrderPlaced(order.Id, /* … */));
    return Results.Accepted();
});

// Subscribing is an attribute
[Topic("pubsub", "orders")]
app.MapPost("/on-order-placed", async (OrderPlaced e, IPaymentService payments) =>
{
    await payments.ChargeAsync(e.OrderId, e.Total);
    return Results.Ok();
});
```

```yaml
# components/pubsub.yaml — swap RabbitMQ for Kafka by editing this file. Zero code change.
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.rabbitmq        # ← change to pubsub.kafka or pubsub.azure.servicebus
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef: { name: rabbit-secret, key: connectionString }
```

**Shines when:** you must run on more than one cloud, you have many services in different languages that should all message the same way, you are tired of writing the same retry/DLQ/outbox plumbing in every service, or you want to start on RabbitMQ and move to Kafka later without a rewrite.

**Costs you:** a sidecar per pod (memory, one more thing to fail, one more version to upgrade). The abstraction hides broker-specific power — you get the common subset, so no Kafka transactions, no ASB sessions, no Rabbit priority queues. And a debugging step: "is it my code, or Dapr, or the broker?"

---

## The comparison table

| | **RabbitMQ** | **Kafka** | **Azure Service Bus** | **Dapr** |
|---|---|---|---|---|
| Mental model | Post office | DVR / tape | Contracted courier | Power adapter |
| Replay old messages | ✗ | ✓ | ✗ | Depends on the broker under it |
| Per-message ack | ✓ | ✗ | ✓ | ✓ |
| Per-message DLQ | ✓ | Build it yourself | ✓ | ✓ |
| Ordering | Per queue, 1 consumer | Per partition | Per session | Common subset only |
| Throughput | 10k–50k/sec | Millions/sec | 1k–10k/sec (Premium higher) | Broker's, minus sidecar |
| Ops burden | Medium (you run it) | High (you run a cluster) | None (managed) | Medium (sidecars) |
| Portable across clouds | ✓ (self-hosted) | ✓ | ✗ | ✓ (the point) |
| Scheduled delivery | Via plugin | Build it yourself | ✓ Built in | Via broker |
| Duplicate detection | Build it yourself | Build it yourself | ✓ Built in | Build it yourself |
| Cost shape | Servers | Servers + storage + people | Per message + tier | Broker + sidecar overhead |

---

> **Diagram: D4 — Choosing a broker (decision flowchart)**
> [`images/svg/d4-broker-decision.svg`](../images/svg/d4-broker-decision.svg) · [Mermaid source](../diagrams/README.md#d4--choosing-a-broker)

![Choosing a broker](../images/svg/d4-broker-decision.svg)

---

## The decision, as questions

Ask in this order. Stop at the first clear answer.

**Q1. Do consumers need to re-read old messages?**
Reasons you would: rebuild a read model after a bug, onboard a new service that needs history, reprocess after fixing a calculation, or the event log *is* your audit trail.
→ **Yes: Kafka.** This single capability is the biggest fork in the road, and only a log gives it to you.
→ No: continue.

**Q2. Do you need per-message ack, retry and dead-lettering?**
→ **Yes: RabbitMQ or Azure Service Bus.** Continue to Q3.
→ No, it is simple fan-out: any pub/sub will do. Pick on operational cost.

**Q3. Do you want to run the broker yourself?**
→ **No, managed please: Azure Service Bus** (or SNS+SQS, or Google Pub/Sub).
→ **Yes, full control: RabbitMQ.** Cheaper at volume, more flexible routing.

**Q4. Must this run on more than one cloud, or do you want to defer the choice?**
→ **Yes: wrap it in Dapr.** Start on RabbitMQ locally, deploy on ASB in Azure, move to Kafka if throughput demands it — by changing a YAML file.
→ No: **use the native client.** You keep the full power of the broker and one less moving part.

---

## Signals you chose wrong

These are the honest tells. Each one has a specific fix.

| Symptom | What it means | Fix |
|---|---|---|
| Using Kafka purely as a work queue, never replaying | You are paying cluster ops for a feature you do not use | You wanted RabbitMQ or SQS |
| Trying to replay a RabbitMQ queue to rebuild state | You need a log, not a queue | You wanted Kafka |
| You wrote your own retry / DLQ / outbox plumbing three times | Missing an abstraction | You wanted MassTransit or Dapr |
| Using Dapr but reaching past it for native broker features | The abstraction costs more than it saves | Drop Dapr, use the native client |
| Kafka consumer lag grows and you cannot add consumers | Consumer count is capped by partition count | Increase partitions (plan this up front — it is disruptive) |
| Azure Service Bus bill is your biggest cloud line item | Per-message pricing at high volume | Move the high-volume topic to Kafka; keep ASB for low-volume, high-value flows |
| "We use Kafka because it is web-scale" and you do 40 messages/sec | Copying someone else's constraints | Almost anything else, and reclaim the ops time |

---

## Sharp edges

**Edge 1 — Kafka partition count is close to permanent.** Consumers in a group cannot exceed partitions; 3 partitions means at most 3 consumers, no matter how far behind you are. You *can* add partitions, but existing keys then hash to different partitions, which breaks your ordering guarantee for in-flight keys. Decide early, and over-provision: 12 partitions on a topic doing 100 msg/sec costs almost nothing and saves you a painful migration later.

**Edge 2 — Kafka retention is a real deletion.** `retention.ms=604800000` (7 days) means on day 8 your "replayable log" is empty. If the log is your audit trail or your source of truth, set retention to `-1` (forever) or use compaction, and budget for the disk. People discover this during an incident, which is the worst time.

**Edge 3 — RabbitMQ ordering dies the moment you scale out.** One queue, one consumer = ordered. One queue, two consumers = unordered. Teams add an instance to clear a backlog and silently break an ordering assumption their code depended on.

**Edge 4 — Azure Service Bus sessions serialise your throughput.** A session is processed by one consumer at a time. If you set `SessionId` to something coarse (like a tenant ID), you have accidentally made all of that tenant's work single-threaded.

**Edge 5 — Dapr's sidecar is in your latency path and your failure path.** Every publish is a local HTTP call to the sidecar. Usually sub-millisecond, but if the sidecar is not ready when your app starts, your first publishes fail. Handle sidecar readiness explicitly.

**Edge 6 — "Exactly-once" is marketing.** Kafka has exactly-once *within* Kafka (read topic → process → write topic, transactionally). The moment your side effect is a database write, a card charge, or an email, you are back to at-least-once, and you need idempotency. Do not let a feature list talk you out of [chapter 8](08-outbox-and-idempotency.md).

---

## A pragmatic default

If you have no strong constraint and want a recommendation rather than a decision tree:

**Start with RabbitMQ behind MassTransit** (or Dapr, if multi-cloud is a real requirement).

Why: RabbitMQ is easy to run, easy to reason about, and gives you retry and DLQ for free. MassTransit gives you the outbox, idempotency helpers, and retry policies as configuration. If you later need replay or 100× throughput, you swap the transport — and because your handlers are written against MassTransit's `IConsumer<T>`, not RabbitMQ's channel API, that swap is a config change and a test run.

**Add Kafka when — and only when — you can name the consumer that needs replay.** "We might need it one day" is not that consumer.

---

## Try it yourself

Implement the **same** flow — `OrderPlaced` → charge payment → `PaymentSucceeded` — four times. This is the single most valuable exercise in the tutorial, because it teaches you the models by contrast.

1. **RabbitMQ.** Ack after processing. Then throw an exception and watch the message requeue, then dead-letter after N attempts.
2. **Kafka.** Commit the offset after processing. Then reset the offset to 0 and watch the whole history reprocess. *This is the thing Rabbit cannot do.*
3. **Azure Service Bus.** Use a `SessionId` of `orderId`. Send 3 events for the same order out of order, and watch them arrive in order. Then send the same `MessageId` twice and watch duplicate detection drop it.
4. **Dapr.** Write it once. Run it against RabbitMQ locally. Change one line of YAML to point at Kafka. Run it again with no code change.

Then answer for yourself: **which one felt like the least work for the problem in front of you?** That is your answer, and it is more trustworthy than any blog post.

---

← [Chapter 3](03-asynchronous.md) · [Tutorial index](README.md) · Next: [Chapter 5 — Gateway and BFF](05-gateway-and-bff.md)
