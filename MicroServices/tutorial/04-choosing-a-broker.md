# Chapter 4 — Choosing a Broker Without Copying Someone Else's Homework

← [Chapter 3](03-asynchronous.md) · [Tutorial index](README.md) · Next: [Chapter 5 — Gateway and BFF](05-gateway-and-bff.md)

---

## The story so far

Checkout is asynchronous now ([chapter 3](03-asynchronous.md)) and survives the sale. But every design document says "publish to the broker" without saying which broker.

The team has been arguing for a week:

> **Arjun:** "Kafka. It's what every scaling article uses."
> **Meera:** "Kafka is four servers to babysit. RabbitMQ does everything we need."
> **Sam:** "Azure Service Bus. We're on Azure, and nobody has to run it."
> **Arjun:** "But what if we need to scale later?"

Nobody has asked what the store actually needs. This chapter does that, and the argument ends in about ten minutes.

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

**The mental model is the thing to remember.** Everything else follows from it.

### RabbitMQ — "smart broker, dumb consumer"

The broker holds the intelligence. You describe your routing in the broker (exchanges, bindings, routing keys) and it decides where each message goes. Each message is acknowledged individually. Once acked, it is **gone**.

> **Think of it as a post office.** It sorts and delivers. Once delivered, it does not keep a copy.

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

**Shines when:** you are distributing tasks. Per-message retry, per-message dead-lettering, priority queues, complex routing, message TTL.

**Costs you:** no replay — an acked message is gone forever. Routing lives in broker config, so it is not in source control unless you are disciplined about infrastructure-as-code. Throughput ceiling is lower than Kafka (tens of thousands/sec, not millions).

---

### Kafka — "dumb broker, smart consumer"

The broker is an **append-only log**. It does not track who read what — the consumer tracks its own position (the offset). Messages stay for the retention period whether or not anyone read them.

> **Think of it as a DVR recording a channel.** Everything is on the tape. Any viewer can rewind to any point.

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

**Shines when:** you need replay (rebuild a projection, onboard a new consumer with full history, fix a bug and reprocess), many independent consumers of one stream, ordering per key, very high throughput, stream processing.

**Costs you:** real operational weight (brokers, coordination, partition rebalancing, retention tuning). No per-message ack — if message 5 of 100 fails, you cannot "nack just that one"; you must decide to skip it, retry in place, or route it to an error topic yourself. Consumer count is capped by partition count.

---

### Azure Service Bus — "managed enterprise messaging"

RabbitMQ's model, plus enterprise features, minus the operations. You do not run a server.

> **Think of it as a courier company with a signed contract.** Guaranteed FIFO on request, scheduled delivery, duplicate detection — and someone else's staff keep the trucks running.

```csharp
// Sessions give you ordered processing per key, which is genuinely hard to build yourself
var processor = client.CreateSessionProcessor("orders", "payments", new ServiceBusSessionProcessorOptions
{
    MaxConcurrentSessions = 20,       // 20 orders in parallel…
    SessionIdleTimeout    = TimeSpan.FromSeconds(30)
});                                   // …but strictly in order within each order

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

**Shines when:** you are on Azure, you want FIFO per key without building it, you need scheduled delivery ("run this in 3 days"), broker-level duplicate detection, and you have no platform team to run a broker.

**Costs you:** cloud lock-in (the API is not portable). Cost grows with volume. Throughput ceiling well below Kafka. Premium tier needed for the good features.

---

### Dapr — "a portability layer over any of the above"

#### First, the problem it solves

Pick any broker above and write the code for it. Here is publishing an order to **Azure Service Bus**:

```csharp
// Azure-specific. Every line of this is Azure.
using Azure.Messaging.ServiceBus;                      // ← Azure SDK

var client = new ServiceBusClient(connectionString);   // ← Azure connection string
var sender = client.CreateSender("orders");            // ← Azure type
var message = new ServiceBusMessage(                   // ← Azure type
    JsonSerializer.Serialize(orderPlaced))
{
    SessionId = order.Id,                              // ← Azure concept
    MessageId = $"{order.Id}:placed",
};
await sender.SendMessageAsync(message);
```

Now your boss says: *we are moving to Kafka.*

You delete the `Azure.Messaging.ServiceBus` package. You add `Confluent.Kafka`. `ServiceBusMessage` becomes `Message<string, byte[]>`. `SessionId` does not exist in Kafka — it becomes a partition key. `CreateSender` becomes a `ProducerBuilder`. The connection string becomes bootstrap servers plus SASL config.

**You rewrite every file that publishes or consumes a message.** In a system with forty services, that is a quarter's work.

That rewrite is what Dapr exists to prevent.

#### What Dapr actually is

Dapr runs as a **sidecar** [a second container that runs beside your app in the same pod, like a co-worker at the next desk]. Your app never talks to a broker. It talks to the sidecar over plain HTTP on `localhost`, and the sidecar talks to the broker.

```
BEFORE                              AFTER
┌──────────────┐                    ┌──────────────┬──────────────┐
│  Your app    │                    │  Your app    │ daprd sidecar│
│  + Azure SDK │───► Service Bus    │  (no SDK)    │  + all SDKs  │───► any broker
└──────────────┘                    └──────────────┴──────────────┘
                                           localhost:3500
 SDK is IN your code.                 SDK is in the SIDECAR.
 Change broker = rewrite.             Change broker = edit YAML.
```

> **The universal power adapter.** Map it piece by piece:
>
> | Travel | Dapr |
> |---|---|
> | Your laptop, with one fixed plug shape | **Your code** — it only knows `PublishEventAsync` |
> | The wall socket, different in every country | **The broker** — Kafka, Rabbit, Service Bus all differ |
> | The adapter, reshaping pins to fit | **The Dapr sidecar** — translates your call into that broker's protocol |
> | Choosing which adapter head to click on | **The YAML file** — one line names the broker |
>
> Your laptop never changes. You change the head on the adapter.

#### The same publish, through Dapr

```csharp
// Notice what is NOT here: no broker name, no broker SDK, no broker types,
// no connection string.
app.MapPost("/orders", async (PlaceOrderRequest req, DaprClient dapr) =>
{
    var order = Order.Place(req.CustomerId, req.Lines);
    await dapr.PublishEventAsync("pubsub", "orders", new OrderPlaced(order.Id, /* … */));
    return Results.Accepted();
});
```

Two strings do the work, and **the first one is the whole trick**:

| Argument | What it is |
|---|---|
| `"pubsub"` | **A nickname you invented.** It is not a broker, a protocol, or a keyword. It is a label that points at a config file. |
| `"orders"` | The topic name — the same idea as in any broker |

Now the config file. Watch the `name` field:

```yaml
# components/pubsub.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub                 # ← MUST match the first argument in the C# above.
                               #   This is the join. Your code says "pubsub";
                               #   Dapr looks here to find out what that means.
spec:
  type: pubsub.rabbitmq        # ← THIS is the only line that names a broker.
                               #   Change it to pubsub.kafka and you are on Kafka.
  version: v1
```

**That is the entire mechanism.** Your code refers to a nickname. A YAML file says what the nickname points at. Change the YAML, restart the pod, and the same compiled binary now publishes to a different broker.

Run RabbitMQ in Docker on your laptop, and Azure Service Bus in production — with **one** codebase and **two** config files.

#### Shines when

- **You must run on more than one cloud.** Same code deploys to AWS with SQS and Azure with Service Bus.
- **You have services in several languages.** A .NET service, a Go service and a Python service all use the identical Dapr API. Without it, three teams each learn a different SDK and each implement retries slightly differently.
- **You want to start small and grow.** Begin on free RabbitMQ; move to Kafka when volume demands it, by editing config rather than rewriting code.

#### Costs you — three separate problems

**1. A sidecar per pod.** Not one sidecar for the cluster — **one for every single pod**. Forty services × five replicas = 200 extra containers, each using 50–150 MB. That is roughly 10–30 GB of memory doing nothing but translation, plus 200 more things to patch and upgrade.

**2. The lowest-common-denominator problem.** Dapr offers one API that must work across *every* broker it supports. So it can only expose what they all share. Anything special to one broker is invisible:

| You picked | For this feature | Under Dapr |
|---|---|---|
| Kafka | Transactions, replay from an old offset | ❌ Gone |
| Service Bus | Sessions, scheduled delivery | ❌ Gone |
| RabbitMQ | Priority queues, custom exchange routing | ❌ Gone |

**The sting:** these are usually the exact reasons you picked that broker. You trade a deep, specific tool for a shallow, portable one.

**3. A third place to look when something breaks.** Before Dapr there were two suspects: your code, or the broker. Now there are three:

- Did my code send a malformed request to `localhost:3500`?
- Did the sidecar crash, or load its component config wrong?
- Did the broker reject the message?

Component load failures are the nasty ones — a typo in the YAML means the sidecar starts fine and pub/sub silently does nothing.

> **Sharp edge — the sidecar is in your latency path *and* your failure path.** Every publish is a local HTTP call: usually sub-millisecond, but never zero. And if the sidecar is not ready when your app starts, your first publishes fail. Wait for it explicitly on startup rather than assuming it is there.

#### The one-line test

> **Dapr is worth it when you chose your broker for reasons Dapr keeps, and a mistake when you chose it for reasons Dapr hides.**

If you picked Kafka for replay, or Service Bus for sessions — the two most common reasons for picking either — Dapr removes the thing you wanted. Use the native client instead.

📖 **Much more detail**, including component config for all three brokers, the CloudEvents envelope surprise, and how Dapr compares to MassTransit: [`../../Messaging-Systems/docs/dapr.md`](../../Messaging-Systems/docs/dapr.md)

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
→ **Yes: wrap it in Dapr.**
→ No: **use the native client.** You keep the full power of the broker and one less moving part.

---

## The store answers the questions

The team stops arguing and answers them out loud.

**Q1 — Does anyone need to replay orders?**

Arjun says yes, for analytics. Meera asks him to name the consumer that would replay, and what it would do with the data.

He thinks about it. Analytics reads `OrderPlaced` and writes a daily total. If it breaks, they re-run the daily job from the orders table in the database — they do not need the message log.

**Answer: no.** Nobody replays orders. → **Not Kafka.**

**Q2 — Per-message ack, retry and DLQ?**

Yes, clearly. When `ChargePayment` fails for Priya's order, they need *that one message* retried and eventually dead-lettered so someone can look at it. They do not want to stall every other order behind it.

**Answer: yes.** → **RabbitMQ or Azure Service Bus.**

**Q3 — Do you want to run the broker?**

Six engineers, no platform team, and a Diwali sale to survive. Nobody wants to be on call for a broker cluster.

**Answer: no, managed.** → **Azure Service Bus.**

**Q4 — Multi-cloud?**

No. They are on Azure and have no plan to leave.

**Answer: no.** → **Use the native client. No Dapr.**

**The decision: Azure Service Bus, native client.** Ten minutes, after a week of arguing.

### The part that matters more than the answer

Notice what settled it: **"name the consumer that would replay."**

Arjun's "but what if we need to scale later?" is not a requirement — it is anxiety. It cannot be designed for because it does not say anything specific. "Analytics needs to rebuild six months of funnel data" *is* a requirement, and it would have flipped the answer to Kafka immediately.

**When someone argues for a tool, ask them to name the concrete thing it does for you.** If they cannot, the argument is about fashion.

---

## Signals you chose wrong

Honest tells, each with a specific fix:

| Symptom | What it means | Fix |
|---|---|---|
| Using Kafka purely as a work queue, never replaying | Paying cluster ops for an unused feature | You wanted RabbitMQ or SQS |
| Trying to replay a RabbitMQ queue to rebuild state | You need a log, not a queue | You wanted Kafka |
| You wrote your own retry / DLQ / outbox plumbing three times | Missing an abstraction | You wanted MassTransit or Dapr |
| Using Dapr but reaching past it for native features | The abstraction costs more than it saves | Drop Dapr, use the native client |
| Kafka consumer lag grows and you cannot add consumers | Consumer count capped by partition count | Increase partitions (plan this up front — it is disruptive) |
| Azure Service Bus is your biggest cloud line item | Per-message pricing at high volume | Move the high-volume topic to Kafka; keep ASB for low-volume, high-value flows |
| "We use Kafka because it is web-scale" and you do 40 msg/sec | Copying someone else's constraints | Almost anything else, and reclaim the ops time |

---

## Sharp edges

**Edge 1 — Kafka partition count is close to permanent.** Consumers in a group cannot exceed partitions; 3 partitions means at most 3 consumers, however far behind you are. You *can* add partitions, but existing keys then hash to different partitions, breaking ordering for in-flight keys. Decide early and over-provision: 12 partitions on a topic doing 100 msg/sec costs almost nothing and saves a painful migration.

**Edge 2 — Kafka retention is a real deletion.** `retention.ms=604800000` (7 days) means on day 8 your "replayable log" is empty. If the log is your audit trail, set retention to `-1` or use compaction, and budget for the disk. People discover this during an incident.

**Edge 3 — RabbitMQ ordering dies the moment you scale out.** One queue, one consumer = ordered. One queue, two consumers = unordered. Teams add an instance to clear a backlog and silently break an ordering assumption their code relied on.

**Edge 4 — Azure Service Bus sessions serialise your throughput.** A session is processed by one consumer at a time. Set `SessionId` to something coarse (a tenant ID) and you have accidentally made all of that tenant's work single-threaded.

**Edge 5 — Dapr's sidecar is in your latency path and your failure path.** Every publish is a local HTTP call. Usually sub-millisecond, but if the sidecar is not ready when your app starts, your first publishes fail.

**Edge 6 — "Exactly-once" is marketing.** Kafka has exactly-once *within* Kafka. The moment your side effect is a database write, a card charge, or an email, you are back to at-least-once and you need idempotency. Do not let a feature list talk you out of [chapter 8](08-outbox-and-idempotency.md).

---

## A pragmatic default

If you have no strong constraint and want a recommendation rather than a decision tree:

**Start with RabbitMQ behind MassTransit** (or Dapr, if multi-cloud is genuinely required).

Why: RabbitMQ is easy to run and reason about, and gives you retry and DLQ for free. MassTransit gives you the outbox, idempotency helpers, and retry policies as configuration. If you later need replay or 100× throughput, you swap the transport — and because your handlers are written against `IConsumer<T>` rather than RabbitMQ's channel API, that swap is a config change and a test run.

**Add Kafka when — and only when — you can name the consumer that needs replay.** "We might need it one day" is not that consumer.

---

## Try it yourself

Implement the **same** flow — `OrderPlaced` → charge payment → `PaymentSucceeded` — four times. This is the single most valuable exercise in the tutorial, because it teaches the models by contrast.

1. **RabbitMQ.** Ack after processing. Then throw an exception and watch the message requeue, then dead-letter after N attempts.
2. **Kafka.** Commit the offset after processing. Then reset the offset to 0 and watch the whole history reprocess. *This is the thing Rabbit cannot do.*
3. **Azure Service Bus.** Use `SessionId = orderId`. Send 3 events for one order out of order and watch them arrive in order. Then send the same `MessageId` twice and watch duplicate detection drop it.
4. **Dapr.** Write it once. Run against RabbitMQ locally. Change one line of YAML to point at Kafka. Run again with no code change.

Then answer for yourself: **which felt like the least work for the problem in front of you?** That answer is more trustworthy than any blog post.

---

## What is still broken

The store has a broker and checkout is fast and durable. Backend problems, for the moment, are handled.

Then the product team ships the **mobile app**, and the complaints start:

- Opening the order screen makes **six separate API calls** — one to `Ordering`, one to `Catalog`, one to `Shipping`, and three more for details.
- On 4G that is 2.5 seconds and a visible battery drain.
- Every one of those six services now needs its own authentication, its own rate limiting, and its own public TLS certificate.
- BlueDart wants to send you a webhook when a parcel is scanned, and nobody can agree which service should receive it.

Six services with six front doors is not a system — it is a hallway full of doors. Next chapter builds one front door, and a backend shaped for each kind of client.

---

← [Chapter 3](03-asynchronous.md) · [Tutorial index](README.md) · Next: [Chapter 5 — Gateway and BFF](05-gateway-and-bff.md)
