# Production Incidents

Thirty incident shapes — ten per broker. Each one: **symptoms**, **root cause**, **how it was detected**, **mitigation**, **long-term fix**.

These are the failures that recur. If you have run any of these systems for a year, you have met several. If you are about to run one, these are what to build alarms for.

**Sections:** [Apache Kafka](#apache-kafka) · [Azure Service Bus](#azure-service-bus) · [RabbitMQ](#rabbitmq) · [Patterns across all three](#what-repeats-across-all-thirty)

---

## Apache Kafka

### K1 — The rebalance loop

| | |
|---|---|
| **Symptoms** | Throughput sawtooths between full speed and zero. Lag oscillates. Consumer logs full of "Revoked / Assigned" every few seconds. No broker alarms. |
| **Root cause** | Handler took longer than `max.poll.interval.ms` (default 5 min). The group evicted the consumer mid-work, which triggered a rebalance, which restarted the work, which took too long again. |
| **Detection** | Rebalance rate metric > 1/min. Usually reported by a downstream team as "data is stale", not by monitoring. |
| **Mitigation** | Raise `max.poll.interval.ms` above the realistic worst case. Reduce `max.poll.records` so each batch is smaller. |
| **Long-term** | Cooperative sticky assignment. Alert on rebalance rate. Move genuinely long work off the consumer thread and into a job queue. |

**The trap:** almost everyone reaches for `session.timeout.ms` first. It does nothing here. Heartbeats run on a background thread and are healthy; it is the *processing* that is too slow.

---

### K2 — Disk full, broker down

| | |
|---|---|
| **Symptoms** | One broker in `CrashLoopBackOff`. Under-replicated partitions climbing. Producer latency up. |
| **Root cause** | Retention set to 30 days when the cluster was quiet. Traffic tripled over eight months. Nobody watched the disk graph. |
| **Detection** | Pod crash alert — i.e. **after** the failure, not before. Disk trending was not alerted on. |
| **Mitigation** | Cut retention on the largest topic temporarily, let the cleaner run, then expand the PVC. |
| **Long-term** | Alert at 75%. Tiered storage. Capacity review quarterly with actual growth rates. |

**Never delete `.log` files by hand.** The broker holds open handles and tracks segment metadata; removing files underneath it corrupts the partition and can lose committed data.

---

### K3 — `acks=all` that guaranteed nothing

| | |
|---|---|
| **Symptoms** | After a broker failure, ~4,000 acknowledged orders were missing downstream. Producers had logged success for every one. |
| **Root cause** | `acks=all` was set. `min.insync.replicas` was left at **1**. The in-sync set had silently shrunk to one replica; "all" meant "one". That replica died. |
| **Detection** | A finance reconciliation three days later. Not by monitoring at all. |
| **Mitigation** | Replay from the outbox table — which existed, which is the only reason this was recoverable. |
| **Long-term** | `min.insync.replicas=2` on every topic. A config audit in CI that fails the build on `min.insync.replicas=1` with `acks=all`. Alert on ISR shrink. |

**The single most common Kafka misconfiguration.** `acks=all` alone is theatre.

---

### K4 — Partition skew from one large customer

| | |
|---|---|
| **Symptoms** | Lag on partition 7 only. Every other partition at zero. Consumer CPU low across the fleet. Adding replicas changed nothing. |
| **Root cause** | Keyed by `customerId`. One enterprise customer generated 40× the traffic of the next largest and hashed to one partition. |
| **Detection** | Per-partition lag dashboard. Aggregate lag looked fine — this is why per-partition matters. |
| **Mitigation** | Composite key with sub-sharding for that customer: `customerId:hash(orderId) % 16`. |
| **Long-term** | Confirm the real ordering unit before choosing a key. It was per-*order*, not per-*customer* — the whole problem was self-inflicted. |

---

### K5 — Consumer group reset to the beginning after a holiday

| | |
|---|---|
| **Symptoms** | Tuesday morning after a long weekend: a consumer group started reprocessing 7 days of history. 40 million duplicate messages. |
| **Root cause** | `offsets.retention.minutes` default is 7 days. The group had been idle over the break, its committed offsets were expired, and `auto.offset.reset=earliest` did exactly what it was told. |
| **Detection** | Lag spiked to the full topic size. Downstream systems flooded. |
| **Mitigation** | Stopped consumers, reset offsets to a timestamp, restarted. **Idempotency absorbed the duplicates that had already been processed** — without it this would have been a data corruption incident. |
| **Long-term** | `offsets.retention.minutes` to 14 days minimum. Alert on any group whose committed offset disappears. |

---

### K6 — Poison message wedging a partition

| | |
|---|---|
| **Symptoms** | One partition's lag climbing linearly. Others fine. Consumer logs the same exception every 200 ms. |
| **Root cause** | An upstream deploy emitted a message with a null field the consumer dereferenced. Unbounded retry on the main path. |
| **Detection** | Per-partition lag plus a spike in the error rate. |
| **Mitigation** | Captured the message, dead-lettered it manually, reset the offset past it — with consumers stopped, since offset reset requires an empty group. |
| **Long-term** | Bounded retry then dead-letter then commit past. Schema validation at the producer. |

---

### K7 — Liveness probes killing healthy consumers

| | |
|---|---|
| **Symptoms** | Consumer pods restarting every few minutes. Constant rebalancing. Throughput a fraction of expected. |
| **Root cause** | The liveness probe hit an HTTP endpoint on the same thread pool as message processing. Under load the probe timed out. Kubernetes killed a perfectly healthy pod, which triggered a rebalance, which increased load on the survivors, which slowed their probes. |
| **Detection** | Climbing RESTARTS in `kubectl get pods` — correlated with rebalances only after someone looked at both. |
| **Mitigation** | Raised probe timeout and failure threshold. |
| **Long-term** | Probe endpoint on a dedicated thread pool. Liveness checks broker connectivity, not processing health. **Readiness and liveness should not measure the same thing.** |

---

### K8 — Cross-region replication silently stopped

| | |
|---|---|
| **Symptoms** | DR drill discovered the standby region was 11 days behind. No alerts had fired. |
| **Root cause** | MirrorMaker 2 connector had failed after a certificate rotation and stayed in FAILED state. Nobody monitored the connector, only the clusters. |
| **Detection** | A scheduled DR drill. **Otherwise this would have been discovered during a real failover.** |
| **Mitigation** | Restarted the connector, waited 6 hours for the backlog. |
| **Long-term** | Alert on replication lag, not connector state — a connector can be RUNNING and doing nothing. Automated monthly DR drills. |

**The lesson generalises:** monitor the *outcome* (is data arriving?), not the *component* (is the process up?).

---

### K9 — Rebalance storm during a rolling deploy

| | |
|---|---|
| **Symptoms** | Every deploy of a 20-instance consumer caused a 4-minute processing gap. |
| **Root cause** | Eager rebalancing. Each pod restart stopped the *entire* group and reassigned everything. Twenty pods meant twenty full rebalances. |
| **Detection** | Lag sawtooth aligned exactly with deploy times. |
| **Mitigation** | Slowed the rollout so rebalances did not overlap — a workaround, not a fix. |
| **Long-term** | `CooperativeSticky` assignment. **Static membership** (`group.instance.id`) with a StatefulSet: a pod that restarts within the session timeout reclaims its exact partitions with **no rebalance at all**. Deploy gap went from 4 minutes to under 10 seconds. |

---

### K10 — Increasing partitions broke ordering

| | |
|---|---|
| **Symptoms** | Two days after scaling a topic from 60 to 120 partitions, support reported orders showing a "shipped" status before "paid". |
| **Root cause** | Increasing partitions changes the key-to-partition mapping. Keys moved partitions; in-flight messages for the same order were then processed concurrently from two partitions by two consumers. |
| **Detection** | Customer complaints. No alert existed for out-of-order processing. |
| **Mitigation** | Drained in-flight work, paused producers briefly, resumed. Damage was limited to a two-hour window. |
| **Long-term** | Size partitions for peak parallelism up front. If you must expand, drain in-flight keys first. Add a sequence number per key and assert monotonicity in the consumer — the check that would have caught this in minutes. |

---

## Azure Service Bus

### A1 — Lock expiry storm

| | |
|---|---|
| **Symptoms** | Duplicate payment captures. `DeliveryCount` climbing on messages that eventually succeeded. Downstream complaining about repeats. |
| **Root cause** | `PrefetchCount = 100` with a handler averaging 2 seconds. Prefetched messages hold their lock from the moment they arrive in the client buffer, so messages 50–100 sat locked for minutes, expired, and were redelivered to other workers — which were equally slow. |
| **Detection** | Payment provider flagged duplicate charge attempts. **Idempotency prevented actual double charges**; without it this would have been a refund exercise. |
| **Mitigation** | `PrefetchCount = 0`, `MaxConcurrentCalls` reduced from 64 to 16. |
| **Long-term** | Auto lock renewal set to the realistic worst case. Alert on the `DeliveryCount` distribution — a rising tail means locks are expiring. |

---

### A2 — The `$Default` rule

| | |
|---|---|
| **Symptoms** | A new "high-value orders" subscription received *every* order, not just high-value ones. The filter looked correct in the portal. |
| **Root cause** | Every new subscription is created with a rule named `$Default` matching `1=1`. Adding a filter does not replace it — rules are ORed, so the catch-all won. |
| **Detection** | The fraud team noticed volume 50× higher than expected. |
| **Mitigation** | Deleted `$Default`. |
| **Long-term** | Provisioning code deletes `$Default` before adding any rule. A test asserts the rule count per subscription. |

**The most common Service Bus misconfiguration in production**, and it fails in the direction of "too much data", which is quieter than failing loudly.

---

### A3 — Sessions capping concurrency

| | |
|---|---|
| **Symptoms** | Backlog growing during a load test. KEDA scaled to 60 pods. Throughput did not improve. Most pods idle. |
| **Root cause** | The queue had `requiresSession: true`. Concurrency is bounded by the number of *distinct active sessions*, not messages. The test used 8 test orders, so only 8 sessions existed and 52 pods had nothing to do. |
| **Detection** | Load test. **Fortunately** — this would have been a bad discovery on Black Friday. |
| **Mitigation** | Test data changed to use realistic session cardinality. |
| **Long-term** | Cap `maxReplicaCount` near the realistic concurrent-session count. Document that sessions bound concurrency — it is not obvious from the API. |

---

### A4 — The silent Standard-tier bill

| | |
|---|---|
| **Symptoms** | Monthly Azure bill up $6,700 with no traffic change. Constant throttling. |
| **Root cause** | A clickstream on Standard tier: 8,000 events/sec into a topic with six subscriptions. Each event = 1 send + 6 deliveries + 6 completions = **13 operations**. About 8.4 billion operations/month. |
| **Detection** | Finance, during a cost review. Three months late. |
| **Mitigation** | Moved the clickstream to Event Hubs — approximately $400/month at the same volume. |
| **Long-term** | Cost alerts per resource. **Model operations, not messages** — the team had modelled 8,000/sec and budgeted for 8,000 operations/sec, off by 13×. |

---

### A5 — Empty receives billing millions of operations

| | |
|---|---|
| **Symptoms** | Standard tier operation count 20× the message count on a low-traffic queue. |
| **Root cause** | A custom receive loop with `TryTimeout` of 1 second in a `while(true)`. Every empty receive is a billed operation. An idle queue generated ~2.6 million operations/month doing nothing. |
| **Detection** | Cost analysis after A4 prompted a wider audit. |
| **Mitigation** | `TryTimeout` raised to 30 seconds (the SDK default, which had been overridden for no recorded reason). |
| **Long-term** | Use `ServiceBusProcessor` rather than hand-rolled receive loops. It handles long polling correctly. |

---

### A6 — Throttling on Premium at peak

| | |
|---|---|
| **Symptoms** | `ServiceBusException` with `Reason = ServiceBusy` during a sale. Sends failing intermittently. |
| **Root cause** | 4 messaging units provisioned for average load. Peak was 5× average. |
| **Detection** | `ThrottledRequests` alert fired — correctly and on time. |
| **Mitigation** | Scaled to 8 MU. Took 90 seconds, no downtime. |
| **Long-term** | Pre-scale before known peak events. Alert on `NamespaceCpuUsage > 70%` as a leading indicator rather than on throttling as a lagging one. |

**Note the step function:** 4 → 8 doubles both capacity and cost. There is no 6.

---

### A7 — DLQ filling silently for three weeks

| | |
|---|---|
| **Symptoms** | A customer asked why their order from three weeks earlier had never shipped. Investigation found 12,000 messages in a dead-letter queue. |
| **Root cause** | A downstream API changed a response shape. The consumer threw, abandoned five times, and the broker dead-lettered — exactly as designed. **No alert existed on DLQ depth.** |
| **Detection** | A customer. Three weeks late. |
| **Mitigation** | Fixed the deserialisation, replayed the DLQ with original message ids preserved. |
| **Long-term** | **Alert on DLQ depth > 0. Not > 100. Zero.** A named owner per DLQ. A scheduled drain job. |

The most preventable incident in this document, and one of the most common.

---

### A8 — Geo-DR failover lost in-flight messages

| | |
|---|---|
| **Symptoms** | A DR drill failed over to the paired region. ~3,000 in-flight messages vanished. |
| **Root cause** | Geo-DR replicates **metadata only** — queue and topic definitions, not message bodies. This is documented; the team had assumed message replication. |
| **Detection** | The drill. As intended. |
| **Mitigation** | Replayed from the source system, which was possible only because an outbox existed. |
| **Long-term** | Architecture changed to independent namespaces per region with global routing. Geo-DR retained only for metadata convenience. **RPO documented explicitly** as "in-flight message count at failover". |

---

### A9 — Filter exception dead-lettering everything

| | |
|---|---|
| **Symptoms** | A subscription's DLQ filling rapidly with `FilterEvaluationExceptionOccurred`. |
| **Root cause** | A SQL filter referenced `[customer-tier]`. A producer deploy renamed it to `[customerTier]`. The filter threw on every message. |
| **Detection** | The DLQ alert added after A7 fired within minutes. **The fix from one incident caught the next one.** |
| **Mitigation** | Corrected the filter, replayed. |
| **Long-term** | Property names in a shared contract package. `deadLetteringOnFilterEvaluationExceptions` kept enabled — it turned silent misrouting into a visible failure. |

---

### A10 — `ReceiveAndDelete` losing messages on a restart

| | |
|---|---|
| **Symptoms** | After a routine deploy, ~200 notifications were never sent. No errors anywhere. |
| **Root cause** | The consumer used `ReceiveAndDelete` mode. Messages are deleted at the moment of delivery. Pods terminated mid-batch; the messages had already been deleted server-side and had never been processed. |
| **Detection** | A customer complaint about a missing email. There was no trace on the system side at all. |
| **Mitigation** | Switched to PeekLock. |
| **Long-term** | A code review rule: `ReceiveAndDelete` requires written justification. `terminationGracePeriodSeconds` raised so in-flight work completes on shutdown. |

---

## RabbitMQ

### R1 — Blocked publishers cluster-wide

| | |
|---|---|
| **Symptoms** | Every publisher across every queue hung simultaneously. Consumers kept working normally. Looked exactly like a total broker failure. |
| **Root cause** | A telemetry queue grew to 12 million messages after its consumer was accidentally scaled to zero. Memory crossed `vm_memory_high_watermark`. RabbitMQ blocks **all** publishers cluster-wide when that happens. |
| **Detection** | Every service alerted at once on publish timeouts. The broker's own health checks reported healthy — because it was. |
| **Mitigation** | Scaled the telemetry consumer back up, raised the watermark to 0.75 temporarily, drained. |
| **Long-term** | `x-max-length` + `x-overflow: reject-publish` on **every** queue. One workload's growth now rejects into one queue instead of blocking the cluster. Alert on `connections_blocked > 0`. |

**A GPS telemetry backlog took down checkout.** That sentence is the reason to bound every queue.

---

### R2 — Unlimited prefetch starving the fleet

| | |
|---|---|
| **Symptoms** | 20 consumers deployed; throughput identical to 1 consumer. One pod at 100% CPU, nineteen idle. |
| **Root cause** | Prefetch left at the default, which is **unlimited**. The first consumer to connect claimed the entire queue into its own memory. |
| **Detection** | `rabbitmqctl list_consumers` showed one channel with an enormous unacked count. Aggregate throughput metrics looked merely "disappointing". |
| **Mitigation** | `BasicQos(prefetchCount: 20, global: false)` and a restart. |
| **Long-term** | Prefetch in the shared client library, not per service. Alert on `consumer_utilisation < 0.4`. |

---

### R3 — The requeue poison loop

| | |
|---|---|
| **Symptoms** | One consumer at 100% CPU, throughput zero, log growing at 200 MB/minute. |
| **Root cause** | The handler called `BasicNack(requeue: true)` on any exception. A message with malformed JSON was returned to the **head** of the queue and redelivered instantly, forever. |
| **Detection** | Disk alert from the log volume. |
| **Mitigation** | Purged the message via the management UI. |
| **Long-term** | `requeue: false` plus a dead-letter exchange. `x-delivery-limit: 5` on quorum queues as a broker-side backstop. |

---

### R4 — Network partition with classic mirrored queues

| | |
|---|---|
| **Symptoms** | A brief network blip split a 5-node cluster 3–2. On heal, ~8,000 messages had vanished. |
| **Root cause** | Classic mirrored queues. During a partition both sides accepted writes; on heal, the minority side's messages were discarded — documented behaviour, and the reason mirrored queues were deprecated. |
| **Detection** | `cluster_status` showed partitions. The message loss was found by reconciliation. |
| **Mitigation** | Replayed from the upstream system. |
| **Long-term** | Migrated every durable queue to **quorum queues**. Raft means the majority side keeps working and the minority rejects — a degradation, not divergence. |

---

### R5 — Unroutable messages disappearing

| | |
|---|---|
| **Symptoms** | A new consumer received nothing. Publishers reported success. No errors anywhere. |
| **Root cause** | A typo in the binding key: `order.eu.place` instead of `order.eu.placed`. An exchange with no matching queue **silently drops** the message. |
| **Detection** | Manual investigation after the consumer team escalated. Roughly six hours of messages were gone. |
| **Mitigation** | Corrected the binding. The lost messages were unrecoverable — they had never been stored. |
| **Long-term** | `mandatory: true` on every publish with a `BasicReturn` handler that logs and alerts. Topology declared in code and tested, never typed into the management UI. |

---

### R6 — Consumers cancelled by `consumer_timeout`

| | |
|---|---|
| **Symptoms** | Queue depth growing with `consumers = 0`, while worker pods appeared healthy and showed no errors. |
| **Root cause** | A batch job held an unacked message for over 30 minutes. The broker's `consumer_timeout` cancelled the consumer. The client did not surface the cancellation, so the pod sat there consuming nothing. |
| **Detection** | Queue depth alert. The pods looked fine on every other signal. |
| **Mitigation** | Restarted the workers. |
| **Long-term** | `consumer_timeout` raised to match the real worst case. A consumer-cancel handler that logs and exits so Kubernetes restarts the pod. Alert on `consumers == 0` for any queue that should have consumers. |

---

### R7 — Queue as an archive

| | |
|---|---|
| **Symptoms** | Cluster memory at 90%. Publish latency up 10×. Management UI timing out. |
| **Root cause** | A requirement to "keep 30 days of events for replay" was implemented as a queue with no consumer. It reached 40 million messages. |
| **Detection** | Memory alert. |
| **Mitigation** | Shovelled the backlog to a separate cluster and drained it there — decoupling backlog recovery from live traffic. |
| **Long-term** | The workload moved to Kafka. **A queue is a working set, not an archive.** Stream queues would have been the RabbitMQ-native option and were not known about at the time. |

---

### R8 — Split channel across threads corrupting acks

| | |
|---|---|
| **Symptoms** | Intermittent "unknown delivery tag" errors. Occasional messages acked without being processed. |
| **Root cause** | One `IChannel` shared across a thread pool. **Channels are not thread-safe.** Concurrent use corrupted the delivery-tag sequence, so acks landed on the wrong messages. |
| **Detection** | Sporadic errors dismissed as noise for weeks. Confirmed only when a specific order was found acked but unprocessed. |
| **Mitigation** | One channel per worker thread. |
| **Long-term** | Channel pool in the shared library with the thread-safety constraint enforced by the API shape rather than by documentation. |

---

### R9 — Rolling restart losing quorum

| | |
|---|---|
| **Symptoms** | A cluster upgrade made every quorum queue unavailable for 8 minutes. |
| **Root cause** | The StatefulSet used `podManagementPolicy: Parallel`. All 5 nodes restarted at once. Quorum queues need a majority; with all nodes down there was no majority. |
| **Detection** | Total unavailability, immediately. |
| **Mitigation** | Waited for the nodes to return and re-elect. |
| **Long-term** | `podManagementPolicy: OrderedReady`, a PodDisruptionBudget with `maxUnavailable: 1`, and a readiness probe that only reports ready once the node has fully rejoined the cluster. |

---

### R10 — The management UI as a production dependency

| | |
|---|---|
| **Symptoms** | Broker CPU spiking to 100% every minute on a cluster with 40,000 queues. |
| **Root cause** | A monitoring script polled the management HTTP API for all queue stats every 60 seconds. That endpoint aggregates across every queue and is expensive — it was consuming more CPU than the actual message traffic. |
| **Detection** | CPU profiling during an unrelated performance investigation. |
| **Mitigation** | Reduced the polling interval and scoped the query to specific queues. |
| **Long-term** | Switched to the `rabbitmq_prometheus` plugin, which is designed for scraping. **The management API is for humans; the Prometheus endpoint is for machines.** |

---

## What repeats across all thirty

### Five root causes account for most of them

| Pattern | Incidents |
|---|---|
| **A default that is wrong for production** | K1, K5, R2, R3, A1 — unlimited prefetch, 7-day offset retention, 5-minute poll interval |
| **A guarantee that was not what it looked like** | K3, A8, R4 — `acks=all` without min.insync, Geo-DR replicating metadata only, mirrored queues diverging |
| **Silence instead of failure** | R5, A2, A7, A9 — unroutable messages dropped, `$Default` matching everything, DLQ filling unwatched |
| **Using a broker as something it is not** | R7, A4, K1 — a queue as an archive, a queue as a firehose, a log as a job queue |
| **Monitoring the component, not the outcome** | K8, R6 — a running connector doing nothing, a healthy pod consuming nothing |

### Detected too late in eight of thirty

K3, K10, A4, A5, A7, A10, R5, R8 were all found by a customer, by finance, or by a scheduled drill — not by monitoring. In every case the alert that would have caught it was cheap:

- DLQ depth > 0
- ISR shrink
- `consumers == 0` on a queue that should have consumers
- Replication **lag**, not connector state
- Cost per resource
- Out-of-order sequence numbers per key

### The five alerts to add today

1. **DLQ depth > 0** — every broker, every queue, named owner. Catches A7, A9, and half of everything else.
2. **Publishers blocked / offline partitions / throttled requests** — the "everything is stopped" signal per broker.
3. **`consumers == 0`** on any queue that should have them. Catches R6 and the silent scale-to-zero in R1.
4. **Replication lag**, measured as data arriving — not as "is the connector running". Catches K8.
5. **Config assertions in CI** — `min.insync.replicas >= 2` where `acks=all`, prefetch set explicitly, `$Default` deleted. Catches K3, R2, A2 before they ship.

### The one architectural lesson

The most expensive incidents — K3, K10, R1, R7, A4 — were not operational mistakes. They were **the wrong system for the workload**, discovered late:

- A queue used as an archive (R1, R7)
- A firehose on per-operation billing (A4)
- A durability guarantee assumed rather than verified (K3)
- An ordering guarantee broken by a scaling operation nobody realised was breaking (K10)

Configuration fixes the operational ones. Only design fixes these. That is what [the decision checklist](../cheatsheet/decision-checklist.md) is for, and why its last question is "what did we give up?"

---

*Response procedures: [`../runbooks/`](../runbooks/) · Alert definitions: [`monitoring.md`](monitoring.md) · Concepts: [`tutorial.md`](tutorial.md)*
