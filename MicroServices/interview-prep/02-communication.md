# 2 — Communication

← [Fundamentals](01-fundamentals.md) · [Interview index](README.md) · Next: [Boundaries and edges →](03-boundaries-and-edges.md)

20 questions. This section and [Reliability](04-reliability.md) are where most interviews actually live.

---

<details id="q1">
<summary><b>Q1 · Synchronous or asynchronous — how do you decide?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

One question decides it: **can the caller continue without the answer?**

- **No** — it cannot produce a response without this → synchronous.
- **Yes** — it can respond now and let the rest happen later → asynchronous.

And it is a *business* question, not a technical one. The way to ask it: *"If this step took 30 seconds, would we still accept the order?"*

**If they dig deeper**

Watch for the false "no". "The user needs to see the payment confirmed" usually means "the user needs to know we received their order" — which is `202 Accepted` plus a push update, not a blocking card charge.

That reframing is exactly what the e-commerce case study does, and it is the difference between a checkout that survives a traffic spike and one that collapses.

**Follow-up to expect:** *"Give me an example where you changed a sync call to async."* → Charging a card during checkout. Sync means the payment provider's latency becomes your checkout latency and their downtime becomes your outage. Async means accept the order, charge in the background, push the result.

📖 [Chapter 11 — Q1: Can the caller continue?](../tutorial/11-decision-framework.md#q1-can-the-caller-continue-without-the-answer)

</details>

---

<details id="q2">
<summary><b>Q2 · REST or gRPC?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

gRPC inside, REST at the edge.

gRPC is 5–10× smaller on the wire, contract-first so a breaking change fails the build instead of production, and gives you streaming. But browsers cannot call it directly and you cannot debug it with `curl`.

**If they dig deeper**

| | REST | gRPC |
|---|---|---|
| Readable on the wire | ✅ | ❌ |
| Cacheable | ✅ | ❌ |
| Enforced contract | ❌ | ✅ |
| Browser support | ✅ | Needs gRPC-Web + a proxy |
| Wire size | Verbose | 5–10× smaller |
| Streaming | Awkward | Built in |

The place gRPC genuinely earns its keep is a **latency-critical internal hop**. In the trading case study the risk check has an 8 ms budget, and gRPC saves 2–4 ms versus JSON over HTTP/1.1 — a meaningful share of it.

**Follow-up to expect:** *"What breaks when you adopt gRPC?"* → Your existing tooling. Load balancers, API gateways, logging, and debugging all understand HTTP/JSON and need work to understand gRPC. That cost is real and worth naming.

📖 [Chapter 2 — Option B: gRPC](../tutorial/02-synchronous.md#option-b--grpc)

</details>

---

<details id="q3">
<summary><b>Q3 · What is the difference between a command and an event?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐⭐ <i>asked constantly, answered poorly</i></summary>

**The 30-second answer**

A **command** says *do this*. It names one receiver, expects it to happen, and can be rejected. `ChargePayment`.

An **event** says *this happened*. It names no receiver, is past tense, is already true, and can have zero to many listeners. `PaymentSucceeded`.

**If they dig deeper**

| | Command | Event |
|---|---|---|
| Name | Imperative: `ChargePayment` | Past tense: `PaymentSucceeded` |
| Receivers | One, known to the sender | Unknown, zero to many |
| Can be rejected? | Yes — it is a request | No — it is a fact |
| Transport | Queue | Topic |
| Coupling | Sender knows who acts | Sender knows nothing |

**The test that settles it:** *"Would it be a bug if nobody handled this message?"*

- Yes → command. Use a queue. Alert if the queue grows.
- No → event. Use a topic. New listeners can appear any time.

**Why the naming rule matters:** if you name an event `ProcessOrder`, you have secretly written a command, and you will start asking "did the consumer succeed?" — which is the wrong question to ask about a fact.

**Follow-up to expect:** *"Which should you default to?"* → Events. Adding a consumer to a topic costs nothing. Turning a command into an event later means changing the producer.

📖 [Chapter 3 — Commands vs events](../tutorial/03-asynchronous.md#commands-vs-events--the-distinction-that-drives-everything)

</details>

---

<details id="q4">
<summary><b>Q4 · Queue or topic?</b> &nbsp;·&nbsp; <code>Junior</code></summary>

**The 30-second answer**

- **Queue** — each message goes to exactly **one** consumer. Work distribution. Add workers to go faster.
- **Topic** — each message goes to **every** subscriber. Fan-out. Each subscriber has its own position.

**If they dig deeper**

Real systems use both at once: a topic fans out to three subscriptions, and each subscription has several competing consumer instances behind it.

```
                     ┌─► [Payments subscription]      ─► 5 instances share the work
OrderPlaced topic ───┼─► [Notifications subscription] ─► 2 instances share the work
                     └─► [Analytics subscription]     ─► 1 instance
```

Queue for: sending emails, resizing images, processing payments — work that must happen exactly once and that you want to scale.

Topic for: announcing that something happened, when you do not know or care who is interested.

**Follow-up to expect:** *"What happens if you add a second consumer to a queue?"* → They compete: each message goes to one of them. Which is what you want for throughput, and which silently destroys ordering if your code depended on it.

📖 [Chapter 3 — Queues vs topics](../tutorial/03-asynchronous.md#queues-vs-topics)

</details>

---

<details id="q5">
<summary><b>Q5 · Explain eventual consistency to a product manager.</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

"For a short time — usually under a second — different parts of the system have different answers, and then they agree. The order exists, but the invoice screen has not caught up yet."

The key point for a PM is that **it becomes a UI decision**, not just a technical one.

**If they dig deeper**

This is not theoretical. It is a support ticket:

```
10:00:00.040  Checkout returns 202. Order status = Pending.
10:00:00.045  User lands on "My Orders"… and the order is NOT THERE YET.
              They think their money vanished. They call support.
10:00:00.900  PaymentSucceeded arrives. Status = Confirmed.
```

Four ways to handle it, and you should pick one deliberately:

| Technique | Best for |
|---|---|
| **Show the pending state** — never hide it | Almost always the right answer |
| **Read your own writes** — read from primary for a few seconds after a write | Lists and dashboards |
| **Push the update** — SignalR/WebSocket tells the browser | Best experience, more moving parts |
| **Optimistic UI** — show it as done, correct if it fails | Fast-feeling apps; needs care not to lie |

What never works is pretending the gap is not there.

**Follow-up to expect:** *"How long is 'eventually'?"* → Measure it, do not guess. It is your outbox relay interval plus broker latency plus consumer processing. Typically 200 ms–2 s. And you should have a metric for it, because when it becomes 5 minutes you want to know.

📖 [Chapter 3 — Edge 1: eventual consistency in the user's face](../tutorial/03-asynchronous.md#edge-1--eventual-consistency-in-the-users-face)

</details>

---

<details id="q6">
<summary><b>Q6 · What ordering guarantees do you actually get?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Much weaker than people assume:

| Broker | Ordering |
|---|---|
| Kafka | Within one **partition** only |
| Azure Service Bus | Within one **session** only |
| RabbitMQ | Per queue, with **one** consumer. Add a second and it is gone |
| SQS standard | None at all |

Two consumer instances processing in parallel means message 2 can finish before message 1. Always.

**If they dig deeper**

The fix is a **partition key**, so all related messages take the same path:

```csharp
await producer.ProduceAsync("orders", new Message<string, string>
{
    Key   = orderId.ToString(),   // ← ordering AND parallelism, in one line
    Value = json
});
```

Choose the key carefully, because it sets both properties at once:

| Key | Ordering | Parallelism |
|---|---|---|
| `null` | none | maximum |
| constant | total | **one consumer** |
| `orderId` / `symbol` / `vehicleId` | per entity | high |

**Follow-up to expect:** *"What if you need global ordering?"* → You get one consumer and no parallelism. That is almost always the wrong trade — go back and check whether you truly need global ordering, or just ordering per entity. It is nearly always the latter.

📖 [Chapter 3 — Edge 2: ordering is weaker than you think](../tutorial/03-asynchronous.md#edge-2--ordering-is-weaker-than-you-think)

</details>

---

<details id="q7">
<summary><b>Q7 · RabbitMQ or Kafka?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

One question decides it: **does anyone need to re-read old messages?**

- **Yes** → Kafka. It is an append-only log; consumers track their own position and can rewind.
- **No** → RabbitMQ. It is a post office; once a message is acked it is gone, and you get per-message retry and dead-lettering for free.

**If they dig deeper**

The mental models are the thing to remember:

- **RabbitMQ — smart broker, dumb consumer.** Routing lives in the broker. Per-message ack. Like a post office: it delivers and keeps no copy.
- **Kafka — dumb broker, smart consumer.** It is a log. The consumer tracks its offset. Like a DVR: everything is on the tape, any viewer can rewind.

That difference produces everything else. Kafka gives replay and huge throughput; it cannot give you per-message ack, so "message 5 of 100 failed" is your problem to solve. Rabbit gives per-message ack and DLQ; it can never give you replay.

**Follow-up to expect:** *"When have you seen someone choose wrong?"* → Kafka used purely as a work queue with no replay — paying cluster operations for a feature never used. Or someone trying to replay a RabbitMQ queue to rebuild a read model, which is simply not possible.

📖 [Chapter 4 — The four options and their mental models](../tutorial/04-choosing-a-broker.md#the-four-options-and-their-mental-models)

</details>

---

<details id="q8">
<summary><b>Q8 · What are Kafka partitions and why do they matter?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

A partition is a slice of a topic. The message key decides which partition a message goes to, and that decides two things at once: **ordering is guaranteed within a partition**, and **the partition count caps your consumer count**.

Three partitions means at most three consumers in a group, no matter how far behind you are.

**If they dig deeper**

Sizing, using the market-data case study's numbers:

```
peak rate                200,000 ticks/sec
one consumer handles     ~20,000/sec
minimum partitions       10
3× headroom              30
round up                 64
```

**Over-provision deliberately.** Adding partitions later re-hashes keys, so existing keys move to different partitions and your ordering guarantee breaks for in-flight entities. 64 partitions on a topic doing 40k/sec costs almost nothing and saves a painful migration.

**The hot-partition problem:** keys are not equal. One symbol can be 15% of all traffic, so its partition lags while 63 others idle. Fixes, in order: more partitions, a dedicated topic for the top keys, or sub-keying — but never sub-key a consumer that needs per-entity ordering.

**Follow-up to expect:** *"What happens during a rebalance?"* → Partitions are reassigned and consumers briefly stop. If your consumer holds a buffer, flush and commit in the revoked handler or that work is re-done by whoever gets the partition next.

📖 [Case study 3 — Partitioning](../case-studies/03-stock-market-data/README.md#partitioning--the-most-important-design-decision-here)

</details>

---

<details id="q9">
<summary><b>Q9 · What is at-least-once delivery, and what does it mean for your code?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐⭐ <i>the real test</i></summary>

**The 30-second answer**

It means the broker guarantees your message arrives, and accepts that it may arrive **more than once**. Duplicates are normal operation, not an error condition.

Which means every consumer must be idempotent. There is no broker setting, cloud tier, or vendor feature that removes this requirement.

**If they dig deeper**

Where duplicates actually come from — and note that most of these happen on *every deploy*:

- The consumer processed the message, then crashed before acknowledging it.
- The consumer was slow, the broker's lock expired, and it redelivered while the first attempt was still running.
- The outbox relay crashed after publishing but before marking the row sent.
- A network blip lost the ack.
- Someone replayed a Kafka topic to fix a bug.

**The fix is not to prevent duplicates. It is to make processing one harmless.**

**Follow-up to expect:** *"What about exactly-once?"* → Kafka has exactly-once *within Kafka* — read a topic, process, write a topic, transactionally. The moment your side effect is a database write, a card charge, or an email, you are back to at-least-once. Do not let a feature list talk you out of idempotency.

📖 [Chapter 3 — Edge 3: duplicates are normal](../tutorial/03-asynchronous.md#edge-3--duplicates-are-normal-not-exceptional)

</details>

---

<details id="q10">
<summary><b>Q10 · What is a dead-letter queue and when does a message land there?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A side queue for messages that failed every retry. It exists so one bad message does not block the queue behind it.

Without a DLQ, a poison message is retried forever, blocks everything behind it, and fills your logs. The queue stops moving.

**If they dig deeper**

A sensible retry ladder before dead-lettering:

```csharp
e.UseMessageRetry(r =>
{
    r.Immediate(3);                                     // transient blips
    r.Intervals(TimeSpan.FromSeconds(5),
                TimeSpan.FromSeconds(30),
                TimeSpan.FromMinutes(2));               // slower recovery
});
// exhausted → _error queue automatically
```

**The operational rule that matters:** an empty DLQ is not the goal, a **monitored** DLQ is. Alert on `DLQ depth > 0`. A message sitting there unnoticed for a week is a customer whose order never shipped.

**Follow-up to expect:** *"What do you do with the messages in it?"* → Look at them, fix the bug, then replay them. Which means your DLQ needs a replay path — a tool or endpoint that re-publishes to the original queue. Teams routinely build the DLQ and forget the way out of it.

📖 [Chapter 3 — Edge 4: poison messages and the DLQ](../tutorial/03-asynchronous.md#edge-4--poison-messages-and-the-dlq)

</details>

---

<details id="q11">
<summary><b>Q11 · Why is request-reply over a message broker usually a smell?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Because you pay every cost of async — a broker to run, correlation to manage, duplicates to handle, harder debugging — and keep the one cost of sync: **the caller is still waiting**.

If the caller must wait, use HTTP. It is simpler and every tool understands it.

**If they dig deeper**

The honest exception: the work takes 30 seconds and you want it to survive a restart. A broker is genuinely right there — but return `202 Accepted` with a status URL and let the client poll or receive a push. Do not make the original HTTP request wait.

The tell that you have this smell: your code has a correlation ID, a reply queue, and a `TaskCompletionSource` waiting on it. That is a synchronous call with extra infrastructure.

**Follow-up to expect:** *"So how do you return a result from async work?"* → Three options: the client polls a status endpoint; you push over WebSocket/SignalR; or you publish a result event and whoever cares subscribes. The e-commerce case study uses the push option, which is why the checkout page updates itself about a second after `202`.

📖 [Chapter 3 — Request-reply over a broker](../tutorial/03-asynchronous.md#request-reply-over-a-broker--usually-a-smell)

</details>

---

<details id="q12">
<summary><b>Q12 · What is backpressure and how do you handle it?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Backpressure is telling the caller to slow down instead of accepting work you cannot do.

The wrong response to overload is accepting it anyway: queues grow, latency climbs, memory fills, and you fail *everything* instead of *most things*. **Refusing work is a feature.**

**If they dig deeper**

For synchronous traffic, shed load early and cheaply:

```csharp
o.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(ctx =>
    RateLimitPartition.GetConcurrencyLimiter("global", _ => new ConcurrencyLimiterOptions
    {
        PermitLimit = 500,
        QueueLimit  = 0      // do not queue. Queuing is just slow rejection.
    }));
```

A fast `429` with `Retry-After` is a good outcome — the caller can back off or degrade. A 30-second timeout gives them nothing and costs you a thread.

**Shed by priority.** Under load, reject analytics writes before checkout requests.

For async consumers, backpressure is mostly built in: the queue absorbs the spike and consumers drain at their own pace. What you must do is *watch queue depth*, so you notice when "absorbing a spike" has become "falling behind permanently".

**Follow-up to expect:** *"How do you decide what to shed?"* → Write the list before the incident, not during it. Checkout must work; recommendations may fail. That list is an architectural artefact.

📖 [Chapter 9 — Backpressure and load shedding](../tutorial/09-resilience.md#backpressure-and-load-shedding)

</details>

---

<details id="q13">
<summary><b>Q13 · Kafka retention is set to 7 days. What is the risk?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

On day 8 your "replayable log" is empty.

If the log is your audit trail or the source you rebuild projections from, seven days means you can only rebuild the last seven days. Teams discover this during an incident, which is the worst possible time.

**If they dig deeper**

Retention is a **budget decision** you should make deliberately per topic. From the market-data case study:

| Topic | Retention | Why |
|---|---|---|
| `market.ticks.raw` | 24 hours | Debugging only, huge volume |
| `market.ticks.clean` | 7 days | Consumer recovery |
| `market.candles` | 90 days | Charts and analysis |
| Database | Forever | The real archive |

Kafka is the **transport and short-term buffer**. The database is the archive. Keeping 1.2 billion ticks a day in Kafka forever would cost more than the business.

The exception is banking, where the ledger event log is set to `-1` (infinite) because a regulator can ask about any period, years later.

**Follow-up to expect:** *"What is log compaction?"* → Instead of deleting by age, Kafka keeps the *latest* message per key forever. Right for "current state of every entity" topics; wrong for an event history, because intermediate events are discarded.

📖 [Chapter 4 — Sharp edges](../tutorial/04-choosing-a-broker.md#sharp-edges)

</details>

---

<details id="q14">
<summary><b>Q14 · What is a consumer group?</b> &nbsp;·&nbsp; <code>Junior</code></summary>

**The 30-second answer**

A set of consumer instances that share the work of one subscription. Kafka gives each partition to exactly one instance in the group, so the group as a whole sees every message once.

Two *different* groups reading the same topic each get a full copy — that is how fan-out works in Kafka.

**If they dig deeper**

The consequence people miss: **instances in a group cannot exceed partitions.** Ten instances on a three-partition topic means seven do nothing. Adding instances to clear a backlog then achieves nothing, which is a genuinely confusing incident to debug at 2 a.m.

The group also owns the committed offset. Start a new group with `AutoOffsetReset.Earliest` and it reads the whole retained log from the beginning — which is exactly how you onboard a new service with full history.

**Follow-up to expect:** *"How do you reprocess from the start?"* → Either reset the existing group's offsets, or just create a new group ID. The second is safer: the original group is untouched, so a mistake does not disturb the live consumer.

📖 [Chapter 4 — Kafka](../tutorial/04-choosing-a-broker.md#kafka--dumb-broker-smart-consumer)

</details>

---

<details id="q15">
<summary><b>Q15 · When would you use Dapr?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

When portability is a real requirement, not a hypothetical one — you must run on more than one cloud, or you have many services in different languages that should all message the same way.

Dapr is not a broker. It is a sidecar giving you one API for pub/sub, with the actual broker chosen in a YAML file.

**If they dig deeper**

The genuine win is that swapping RabbitMQ for Kafka is a config change:

```yaml
spec:
  type: pubsub.rabbitmq        # → pubsub.kafka, no code change
```

The costs, which you should name unprompted:

- A sidecar per pod — memory, another failure point, another version to upgrade.
- **The abstraction hides broker-specific power.** You get the common subset: no Kafka transactions, no ASB sessions, no Rabbit priority queues.
- One more debugging step: is it my code, Dapr, or the broker?

**The tell that it is costing you more than it saves:** you are using Dapr but reaching past it for native broker features. At that point drop it and use the native client.

**Follow-up to expect:** *"What would you use instead?"* → MassTransit, if you are .NET-only. You get the outbox, retry policies, and idempotency helpers, and swapping transport is still a config change — without a sidecar in your latency path.

📖 [Chapter 4 — Dapr](../tutorial/04-choosing-a-broker.md#dapr--a-portability-layer-over-any-of-the-above)

</details>

---

<details id="q16">
<summary><b>Q16 · How do you version an event without breaking consumers?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Never edit the old event. Publish a new version alongside it and run both until nobody consumes v1.

```csharp
public record OrderPlaced(Guid OrderId, Guid CustomerId, decimal Total);          // keep
public record OrderPlacedV2(Guid OrderId, Guid CustomerId,
                            decimal Subtotal, decimal Tax, string Currency);      // add
```

**If they dig deeper**

The migration, in order:

1. **Publish both** for every order.
2. **Consumers migrate one at a time**, on their own schedule — no coordination meeting.
3. **Measure** who still consumes v1. Wait until that is zero, for real, for a week.
4. **Then** stop publishing v1 and delete it.

This takes weeks, and that is correct. The alternative is a big-bang coordinated deploy, which is how outages happen.

What is safe versus breaking:

| Change | Safe? |
|---|---|
| Add an optional field | ✅ |
| Add a new event type | ✅ |
| Rename or remove a field | ❌ |
| Change a type | ❌ |
| **Change the meaning of a field** | ❌❌ **Worst of all** — nothing fails, numbers are just wrong |

**Follow-up to expect:** *"How do you know when v1 is unused?"* → Instrument it. Emit a metric tagged by consumer on every v1 deserialisation. "Nobody has complained" is not evidence.

📖 [Chapter 6 — How to make a breaking change safely](../tutorial/06-boundaries-and-data.md#how-to-make-a-breaking-change-safely)

</details>

---

<details id="q17">
<summary><b>Q17 · Should an event carry all the data, or just an ID?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Carry the data consumers need. If an event only carries an ID, every consumer must call back to the producer — which recreates the synchronous coupling you removed by going async.

**If they dig deeper**

The two styles, and when each is right:

| Style | Event contains | Good | Bad |
|---|---|---|---|
| **Event-carried state transfer** | Everything needed | No callbacks; consumers work when the producer is down | Bigger messages; some duplicated data |
| **Notification** | Just the ID | Tiny messages; always fresh | Every consumer calls back — a thundering herd on the producer, and you are coupled again |

Default to carrying the data. Denormalise deliberately — the e-commerce `OrderPlaced` includes `CustomerEmail` precisely so `Notifications` never has to call `Customers`.

Use the ID-only style when the payload is large (do not put a 5 MB document in an event) or the data is highly sensitive.

**Follow-up to expect:** *"What if the data changes after the event is published?"* → The event is a snapshot of a fact at a point in time, and that is usually correct — the order was placed at *that* address. If you truly need current data, that is a lookup, and you should be explicit about which one you want.

📖 [Case study 1 — `OrderEvents.cs`](../case-studies/01-ecommerce/src/Ecommerce.Contracts/Events/OrderEvents.cs)

</details>

---

<details id="q18">
<summary><b>Q18 · A consumer is falling behind. Walk me through it.</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

First look at **consumer lag per partition**, not overall. That immediately tells you which of two problems you have:

- **All partitions lagging** → the consumer is genuinely too slow. Scale out or make it faster.
- **One partition lagging** → a hot key. Adding instances will not help at all.

**If they dig deeper**

The diagnosis order I would follow:

1. **Lag per partition** — even or skewed?
2. **Processing time per message** — has it changed? Usually a downstream dependency got slower.
3. **Instance count versus partition count** — if instances ≥ partitions, scaling out does nothing.
4. **Errors and retries** — a message retrying 5 times consumes 5× the capacity.
5. **Batch size** — per-message database writes are the classic cause; batching often gives 10×.

The fixes, matched to cause: scale out (if partitions allow), increase partitions (plan carefully — it re-hashes keys), batch the writes, remove a synchronous call from the consumer, or split hot keys.

**Follow-up to expect:** *"How long until you catch up?"* → You should be able to answer this: `lag ÷ (processing rate − arrival rate)`. If arrival exceeds processing, the answer is "never" and you need a different fix. Knowing this number before an incident is the difference between a plan and a panic.

📖 [Chapter 3 — Edge 6: queue depth](../tutorial/03-asynchronous.md#edge-6--queue-depth-is-your-most-important-metric)

</details>

---

<details id="q19">
<summary><b>Q19 · What is conflation and when is it appropriate?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**The 30-second answer**

Keeping only the latest value per key and dropping the intermediate ones, deliberately.

It is right when the consumer is a **human eye** — nobody can read 200 price updates a second. It is wrong for anything computing an aggregate.

**If they dig deeper**

The boundary is the whole point, and it is the part people get wrong:

| Consumer | Conflate? | Why |
|---|---|---|
| Browser price display | ✅ | A human cannot read them all |
| Candle builder | ❌ | High, low, and volume would be wrong |
| Storage / archive | ❌ | It is the permanent record |
| Alert engine | ❌ | "Price touched 2850" would be missed |
| Risk engine | ❌ | Must see every tick |

This only works because Kafka lets **each consumer read the full log at its own pace**. With a queue, conflating for one consumer would drop the message for all of them.

**Follow-up to expect:** *"How do you implement it?"* → A dictionary keyed by symbol holding the latest value, plus a dirty set, flushed on a timer. Memory is bounded by the number of keys, not the message rate. In the market-data case the ratio is around 50:1, so 98% of display traffic never leaves the server.

📖 [Case study 3 — `ConflationBuffer.cs`](../case-studies/03-stock-market-data/src/MarketData.Distributor/Conflation/ConflationBuffer.cs)

</details>

---

<details id="q20">
<summary><b>Q20 · Design the messaging for "send a confirmation email when an order is placed".</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

Run the five questions:

1. **Can the caller continue?** Yes — nobody waits for SMTP → **async**.
2. **Replay needed?** No → **queue**, not Kafka.
3. **One consumer or many?** Notifications, Analytics, and Loyalty all care → **event on a topic**.
4. **Safe if delivered twice?** No — a duplicate email is embarrassing → **inbox table**.
5. **Who owns the data?** Notifications owns delivery; Ordering owns the order → clean.

**Design:** `OrderPlaced` event → topic → Notifications subscription with an inbox for dedupe.

**If they dig deeper**

Two details that show experience:

- The event must be published through an **outbox**, in the same transaction as the order insert. Otherwise a crash between the commit and the publish loses the email forever, silently.
- The email send itself is *not* in the inbox transaction. If the process dies between sending and recording, a retry sends a second email. That is an accepted trade — one duplicate email is cheaper than the machinery to prevent it. **Money would deserve the opposite call.**

**Follow-up to expect:** *"What if the email service is down for an hour?"* → Messages queue up and drain when it recovers. Which is exactly what you wanted: the order was never at risk. Watch queue depth so you know it is happening.

📖 [Chapter 11 — Worked example 1](../tutorial/11-decision-framework.md#example-1--send-a-confirmation-email-when-an-order-is-placed)

</details>

---

← [Fundamentals](01-fundamentals.md) · [Interview index](README.md) · Next: [Boundaries and edges →](03-boundaries-and-edges.md)
