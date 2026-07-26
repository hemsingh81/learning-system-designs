# Messaging Cheat Sheet

One page. Print it. The reasoning behind every line is in [`../docs/tutorial.md`](../docs/tutorial.md).

---

## The one-sentence version

| | |
|---|---|
| **Kafka** | A log you can rewind. Many readers, same data, replay any time. |
| **Azure Service Bus** | A managed queue with enterprise manners. The message is a job; it disappears when done. |
| **RabbitMQ** | A smart router. The exchange decides where copies go; rewire without redeploying. |

---

## Vocabulary, decoded

| Term | Plain English |
|---|---|
| **Broker** | The server in the middle that holds messages |
| **Producer / publisher / sender** | Code that puts a message in |
| **Consumer / subscriber / receiver** | Code that takes a message out |
| **Topic** | A named stream. Kafka: a log. Service Bus: a fan-out point. |
| **Partition** | One ordered slice of a Kafka topic. Parallelism unit and ordering unit. |
| **Offset** | A bookmark — "I have read up to here" |
| **Consumer lag** | How far behind a reader is |
| **Consumer group** | A team of readers splitting the partitions between them |
| **Exchange** | RabbitMQ's router. Holds nothing, decides everything. |
| **Binding** | The rule connecting an exchange to a queue |
| **Routing key** | The label on a message that bindings match against |
| **DLQ** | Dead-letter queue — where messages that kept failing go to wait for a human |
| **TTL** | Time to live — delete the message if nobody handled it in time |
| **Backpressure** | The system telling you to slow down |
| **Poison message** | A message that fails every time, forever |
| **Idempotency** | Doing it twice has the same effect as doing it once |
| **Split-brain** | A cluster that split in two and both halves think they are in charge |
| **Prefetch** | How many unacked messages a consumer holds at once |
| **Compaction** | Keep only the newest value per key — turns a log into a table |
| **PeekLock** | Take the message but leave a locked copy until you confirm |
| **Quorum** | A majority; enough replicas to agree on what is true |

---

## Delivery semantics — what you actually get

| Guarantee | How | Cost | Reality |
|---|---|---|---|
| **At-most-once** | Ack before working | Fast | Loses messages. Only for telemetry. |
| **At-least-once** | Work, then ack | Duplicates | **The default everywhere.** Design for it. |
| **Exactly-once** | Broker transactions | Slow, narrow | Kafka: only Kafka→Kafka. Not across a database. |
| **Effectively-once** | At-least-once + idempotency key | One table | **What you actually build.** |

> Anyone who says their system is exactly-once across a network and a database is describing effectively-once and has not noticed.

---

## Ordering — how each one gives it to you

| | Mechanism | Scope | Parallelism cost |
|---|---|---|---|
| **Kafka** | Same key → same partition | Per key | None. Different keys run in parallel. |
| **Service Bus** | `SessionId` | Per session | High. One worker per session at a time. |
| **RabbitMQ** | One queue, one consumer | Per queue | Total. Consumer count = 1. |

Ordering always costs parallelism. Ask whether you need global order (almost never) or per-entity order (usually).

---

## Producer settings that prevent data loss

**Kafka**
```
acks=all                          # wait for all in-sync replicas
enable.idempotence=true           # broker drops duplicate retries
min.insync.replicas=2             # ON THE BROKER — acks=all alone is theatre
unclean.leader.election=false     # never promote an out-of-sync replica
```

**Service Bus**
```csharp
MessageId = $"{orderId}:OrderPlaced"    // deterministic, NOT Guid.NewGuid()
requiresDuplicateDetection = true       // on the queue
disableLocalAuth = true                 // no connection strings
```

**RabbitMQ**
```csharp
publisherConfirmationsEnabled: true     // without this, publish is fire-and-forget
mandatory: true                         // unroutable → callback, not silence
Persistent = true                       // AND declare the queue durable. Both.
x-queue-type: quorum                    // classic mirrored is removed in 4.x
```

---

## Consumer settings that prevent outages

**Kafka**
```
enable.auto.commit=false                     # commit after work, never on a timer
partition.assignment.strategy=CooperativeSticky   # don't stop the group on every deploy
max.poll.interval.ms > worst-case handler    # raise THIS, not session.timeout.ms
```

**Service Bus**
```csharp
ReceiveMode = PeekLock                  // not ReceiveAndDelete
AutoCompleteMessages = false            // settle every message explicitly
PrefetchCount = 0                       // prefetched messages hold their locks
MaxAutoLockRenewalDuration = worst case  // not the p50
```

**RabbitMQ**
```csharp
BasicQos(prefetchCount: 20, global: false)   // default is UNLIMITED. Fix this.
autoAck: false                                // ack after work
BasicNack(requeue: false)                     // requeue:true → infinite poison loop
```

---

## The failure that gets each one

| Broker | The classic outage | The one-line prevention |
|---|---|---|
| **Kafka** | Rebalance loop — handler exceeds `max.poll.interval.ms`, gets evicted mid-work, forever | Raise `max.poll.interval.ms`; use cooperative rebalancing |
| **Service Bus** | Lock expiry storm — slow handler + high prefetch = mass duplicates | `PrefetchCount = 0`, enable auto lock renewal |
| **RabbitMQ** | Publishers blocked — memory watermark hit, every publisher stalls cluster-wide | `x-max-length` + `x-overflow: reject-publish` on every queue |

---

## Metrics that matter

| Metric | Broker | Alert when |
|---|---|---|
| Consumer lag | Kafka | > 5 min of traffic, 10 min |
| Under-replicated partitions | Kafka | > 0 for 5 min |
| Offline partitions | Kafka | > 0 — **page immediately** |
| Rebalance rate | Kafka | > 1/min sustained |
| `connections_blocked` | RabbitMQ | > 0 for 1 min — **page immediately** |
| `messages_ready` | RabbitMQ | > 50k for 10 min |
| `consumer_utilisation` | RabbitMQ | < 0.4 (prefetch too low) |
| `ThrottledRequests` | Service Bus | > 0 for 5 min |
| `activeMessageCount` | Service Bus | > 10 min of traffic |
| `NamespaceCpuUsage` | Service Bus | > 70% |
| **DLQ depth** | **All three** | **> 0. Always. No exceptions.** |

A DLQ nobody reads is a slow-motion data-loss machine.

---

## CLI — the commands you actually type

**Kafka**
```bash
# lag
kafka-consumer-groups.sh --bootstrap-server $BS --describe --group payments-service
# health
kafka-topics.sh --bootstrap-server $BS --describe --under-replicated-partitions
# read a specific record
kafka-console-consumer.sh --bootstrap-server $BS --topic orders.v1 \
  --partition 7 --offset 1044235 --max-messages 1 --property print.headers=true
# replay from a time
kafka-consumer-groups.sh --bootstrap-server $BS --group g --topic t \
  --reset-offsets --to-datetime 2026-07-25T14:00:00.000 --execute   # consumers must be STOPPED
```

**RabbitMQ**
```bash
rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers consumer_utilisation
rabbitmqctl list_connections name state | grep blocked      # the outage check
rabbitmqctl cluster_status                                   # partitions?
rabbitmqctl purge_queue scratch.queue                        # permanent
```

**Service Bus**
```bash
az servicebus queue show -g $RG --namespace-name $NS -n q --query countDetails
az servicebus namespace update -g $RG -n $NS --capacity 8    # 1/2/4/8/16 only
az servicebus topic subscription rule list -g $RG --namespace-name $NS \
  --topic-name t --subscription-name s -o table              # is $Default still there?
```

---

## Retry and DLQ patterns

| | Retry mechanism | DLQ |
|---|---|---|
| **Kafka** | In-process backoff, or a retry topic per delay tier | You build it — a normal topic + reason headers |
| **Service Bus** | `Abandon` + `MaxDeliveryCount`, or `ScheduleMessageAsync` for delay | Built in. `$DeadLetterQueue` sub-queue. |
| **RabbitMQ** | TTL queue with no consumer that dead-letters back to the exchange | Dead-letter exchange + `x-death` header audit trail |

Never retry a business rejection (declined card, invalid SKU). Retry only transient faults. Retrying a decline five times annoys the payment provider and delays the real answer.

---

## Sizing rules of thumb

| Question | Rule |
|---|---|
| Kafka partitions? | Peak throughput ÷ per-consumer throughput, ×2 for headroom. **Cannot be lowered later.** |
| Kafka heap? | 20–25% of container memory. The page cache does the real work. |
| RabbitMQ prefetch? | (messages/sec you handle) × (round-trip seconds) × 2. Start at 20. |
| RabbitMQ memory watermark? | 0.6 of the limit. Lower is tempting; headroom is what prevents the block. |
| Service Bus messaging units? | Start at 4. Scale at 70% CPU. Only 1/2/4/8/16 exist. |
| Consumer replicas? | Kafka: never more than partitions. Rabbit/ASB: no ceiling — downstream is the limit. |

---

## When to use what

**Kafka when** — many independent readers, replay matters, > 50k msg/sec, event sourcing, CDC, a stream feeding analytics.

**Service Bus when** — you are on Azure, you want zero brokers to run, you need sessions / scheduling / per-message TTL, throughput is under ~10k msg/sec.

**RabbitMQ when** — task queues, RPC, complex routing that changes without redeploys, low latency, you need to run it anywhere, and the working set is thousands of messages not millions.

**Hybrid when** — you have both a firehose and a workflow. This is most large systems. Kafka or Event Hubs for the stream, Service Bus or Rabbit for the commands.

**None of them when** — a synchronous call, a database table polled by a worker, or a scheduled batch job would do. A broker you have to operate is not free.

---

## Dapr — one API over all three

Not a broker. A sidecar. Your code says `PublishEventAsync("pubsub", "orders", order)`; a YAML file decides whether that is Kafka, Rabbit or Service Bus.

| Gives you | Takes away |
|---|---|
| Portability — swap brokers by editing YAML | **Kafka: replay and offset control** |
| One API across .NET / Go / Python / Java | **Kafka: transactions** |
| **A DLQ on Kafka** — one line | **Service Bus: sessions, scheduling, defer** |
| Declarative retries + circuit breakers | **RabbitMQ: exchange types, priority** |
| A transactional outbox, implemented | The native error taxonomy |
| Content routing on any broker | ~50–150 MB sidecar per pod |

**The rule:** Dapr fits when you chose your broker for reasons it *preserves*, and not when you chose it for reasons it *hides*. The two strongest single-broker reasons — Kafka replay, Service Bus sessions — are both incompatible with it.

**Use it when:** polyglot estate · multi-cloud is real, not hypothetical · **you genuinely do not know the broker yet** · you were going to build a DLQ and outbox anyway.

**Skip it when:** single-language + single-broker · you need the broker-defining features · latency-critical · small team.

**.NET-only shop? Look at MassTransit first** — same patterns, no sidecar, and you can still reach native config.

**The tell it is costing more than it saves:** you are using Dapr but reaching past it for native broker features. Drop it for that service.

⚠️ **CloudEvents:** Dapr wraps your payload by default, so a non-Dapr consumer on the same topic breaks. Keep your own deterministic id *inside* the payload — the envelope `id` is regenerated on every publish and is useless for deduplication.

Full detail: [`../docs/dapr.md`](../docs/dapr.md)

---

## Five things that are true of all three

1. **At-least-once is the contract.** Build idempotent consumers or accept duplicates in production.
2. **Dual writes do not work.** Saving to a database and publishing a message are two operations that can half-fail. Use the outbox pattern.
3. **The DLQ needs an owner and an alert**, or it is just a place messages go to die quietly.
4. **Ordering costs parallelism.** Always. Decide what actually needs it.
5. **Pick the one your team can debug at 3am.** Operational familiarity beats a 15% benchmark win every single time.
