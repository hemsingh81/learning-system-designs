# Monitoring and Alerting

Prometheus queries, Grafana panels and alert rules for all three brokers. Every threshold has a reason next to it — copy the queries, but read the reasoning before copying the numbers.

**Sections:** [Principles](#principles) · [Kafka](#apache-kafka) · [Azure Service Bus](#azure-service-bus) · [RabbitMQ](#rabbitmq) · [Cross-broker dashboard](#the-dashboard-that-goes-on-the-wall)

---

## Principles

### 1. Alert on the trend, not the level

Lag of 50,000 that is falling is fine. Lag of 5,000 that is climbing is an incident. Alerting on raw depth pages someone for every traffic spike, which trains people to ignore the alert.

```promql
# Bad — fires on every legitimate spike
kafka_consumergroup_lag > 100000

# Good — fires when we will NOT catch up
(kafka_consumergroup_lag / rate(kafka_consumergroup_current_offset[5m])) > 900
```

That second query is **estimated seconds to drain**. It is the number to put in front of an incident commander: "lag is 400,000" means nothing to them; "we will be caught up in 12 minutes" is a decision they can act on.

### 2. Monitor the outcome, not the component

A replication connector can be `RUNNING` and copying nothing. A consumer pod can be `Ready` and consuming nothing. Alert on *is data arriving*, not *is the process up*. This is [incident K8](production-incidents.md#k8--cross-region-replication-silently-stopped) and [R6](production-incidents.md#r6--consumers-cancelled-by-consumer_timeout).

### 3. Every paging alert needs a runbook link

An alert without a documented response is a notification. If nobody knows what to do, it will be acknowledged and ignored.

### 4. DLQ depth > 0 is never acceptable

Not `> 100`. Zero is the correct steady state. This one alert would have caught [A7](production-incidents.md#a7--dlq-filling-silently-for-three-weeks) three weeks earlier and [A9](production-incidents.md#a9--filter-exception-dead-lettering-everything) within minutes.

---

## Apache Kafka

### Exporters

| Exporter | Provides | Notes |
|---|---|---|
| **JMX Exporter** (on each broker) | Broker internals: ISR, partitions, request handlers | Strimzi wires this up — see [`../k8s/kafka-helm-values.yaml`](../k8s/kafka-helm-values.yaml) |
| **kafka-exporter** | Consumer group lag per partition | The one that matters most for application health |
| **kafka-lag-exporter** | Lag in **time**, not just messages | Worth running alongside; time-based lag is far more actionable |

### The queries

**Consumer lag — per group, per partition**

```promql
# Total lag by group
sum by (consumergroup) (kafka_consumergroup_lag)

# Per partition — catches skew that aggregate lag hides (incident K4)
max by (consumergroup, topic, partition) (kafka_consumergroup_lag)

# Estimated seconds to drain — THE number for an incident
sum by (consumergroup) (kafka_consumergroup_lag)
  / clamp_min(sum by (consumergroup) (rate(kafka_consumergroup_current_offset[5m])), 1)

# Skew ratio: is one partition doing all the suffering?
max by (consumergroup) (kafka_consumergroup_lag)
  / clamp_min(avg by (consumergroup) (kafka_consumergroup_lag), 1)
```

That last query is the one that finds partition skew. A ratio above ~5 means one partition is far behind the others, and scaling consumers will not help.

**Cluster health**

```promql
# The single best health signal
sum(kafka_server_replicamanager_underreplicatedpartitions)

# Data is unavailable — this is the page-immediately metric
sum(kafka_controller_kafkacontroller_offlinepartitionscount)

# Must be exactly 1 across the cluster
sum(kafka_controller_kafkacontroller_activecontrollercount)

# Broker saturation. Below 20% means the broker is struggling.
avg by (instance) (kafka_server_kafkarequesthandlerpool_requesthandleravgidlepercent)

# ISR shrinking — the early warning for incident K3
sum(rate(kafka_server_replicamanager_isrshrinkspersec[5m]))
```

**Throughput and latency**

```promql
sum by (topic) (rate(kafka_server_brokertopicmetrics_messagesinpersec[5m]))
sum by (topic) (rate(kafka_server_brokertopicmetrics_bytesinpersec[5m]))

# Produce latency p99
histogram_quantile(0.99,
  sum by (le) (rate(kafka_network_requestmetrics_totaltimems_bucket{request="Produce"}[5m])))
```

**Storage**

```promql
# Disk usage per broker
100 * (1 - kubelet_volume_stats_available_bytes{persistentvolumeclaim=~"data-.*-kafka-.*"}
         / kubelet_volume_stats_capacity_bytes{persistentvolumeclaim=~"data-.*-kafka-.*"})

# Days until full at the current growth rate — the number that prevents incident K2
kubelet_volume_stats_available_bytes{persistentvolumeclaim=~"data-.*-kafka-.*"}
  / clamp_min(deriv(kubelet_volume_stats_used_bytes{persistentvolumeclaim=~"data-.*-kafka-.*"}[6h]), 1)
  / 86400
```

**Rebalancing** — catches incidents K1 and K9

```promql
sum by (consumergroup) (rate(kafka_consumer_coordinator_rebalance_total[10m])) * 60
```

### Alert rules

```yaml
groups:
- name: kafka-critical
  rules:
  - alert: KafkaOfflinePartitions
    expr: sum(kafka_controller_kafkacontroller_offlinepartitionscount) > 0
    for: 1m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "{{ $value }} Kafka partitions are OFFLINE"
      description: "Data is unreadable and unwritable on these partitions."
      runbook: "https://…/runbooks/kafka-runbook.md#incident-7--partitions-offline--quorum-lost"

  - alert: KafkaNoActiveController
    expr: sum(kafka_controller_kafkacontroller_activecontrollercount) != 1
    for: 1m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Kafka has {{ $value }} active controllers (must be exactly 1)"

  - alert: KafkaUnderReplicated
    # 5m, not 1m: a rolling restart legitimately causes brief under-replication.
    expr: sum(kafka_server_replicamanager_underreplicatedpartitions) > 0
    for: 5m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "{{ $value }} under-replicated partitions"
      runbook: "https://…/runbooks/kafka-runbook.md#incident-1--broker-down"

  - alert: KafkaDiskFillingFast
    # Leading indicator. Catches incident K2 days before it happens.
    expr: |
      kubelet_volume_stats_available_bytes{persistentvolumeclaim=~"data-.*-kafka-.*"}
        / clamp_min(deriv(kubelet_volume_stats_used_bytes{persistentvolumeclaim=~"data-.*-kafka-.*"}[6h]), 1)
        / 86400 < 7
    for: 30m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Broker disk full in under 7 days at the current rate"

- name: kafka-warning
  rules:
  - alert: KafkaConsumerLagNotDraining
    # Time-to-drain, not raw lag. 15 min of backlog that is not shrinking.
    expr: |
      sum by (consumergroup) (kafka_consumergroup_lag)
        / clamp_min(sum by (consumergroup) (rate(kafka_consumergroup_current_offset[5m])), 1) > 900
    for: 10m
    labels: { severity: warning, page: "true" }
    annotations:
      summary: "Group {{ $labels.consumergroup }} needs {{ $value | humanizeDuration }} to catch up"
      runbook: "https://…/runbooks/kafka-runbook.md#incident-2--consumer-lag-climbing"

  - alert: KafkaConsumerGroupDead
    # No members at all. The group is stopped, not slow — a different problem.
    expr: kafka_consumergroup_members == 0 and on(consumergroup) kafka_consumergroup_lag > 0
    for: 5m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Group {{ $labels.consumergroup }} has NO members but has lag"

  - alert: KafkaRebalanceLoop
    expr: sum by (consumergroup) (rate(kafka_consumer_coordinator_rebalance_total[10m])) * 60 > 1
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Group {{ $labels.consumergroup }} rebalancing {{ $value }}/min"
      description: "Likely max.poll.interval.ms exceeded. Do NOT raise session.timeout.ms."
      runbook: "https://…/runbooks/kafka-runbook.md#incident-3--consumer-group-rebalancing-constantly"

  - alert: KafkaPartitionSkew
    expr: |
      max by (consumergroup) (kafka_consumergroup_lag)
        / clamp_min(avg by (consumergroup) (kafka_consumergroup_lag), 1) > 5
    for: 15m
    labels: { severity: warning }
    annotations:
      summary: "Partition skew on {{ $labels.consumergroup }} — scaling consumers will not help"

  - alert: KafkaIsrShrinking
    expr: sum(rate(kafka_server_replicamanager_isrshrinkspersec[5m])) > 0
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "ISR shrinking — durability guarantees are degrading"
      description: "With min.insync.replicas=2, a further shrink will reject writes."

  - alert: KafkaDeadLetterTopicActive
    expr: sum(rate(kafka_server_brokertopicmetrics_messagesinpersec{topic=~".*\\.dlq"}[15m])) > 0
    for: 5m
    labels: { severity: warning }
    annotations:
      summary: "Messages arriving in {{ $labels.topic }}"
```

### Grafana panels

| Panel | Query | Type |
|---|---|---|
| Time to drain, by group | The drain query above | Stat, thresholds at 300s / 900s |
| Lag heatmap by partition | `kafka_consumergroup_lag` | Heatmap — skew is visible instantly |
| Under-replicated partitions | `sum(...underreplicatedpartitions)` | Stat, red if > 0 |
| Messages in/out per topic | `rate(...messagesinpersec[5m])` | Time series |
| Disk days remaining | The days-until-full query | Gauge |
| Rebalance rate | `rate(...rebalance_total[10m])*60` | Time series |
| Request handler idle % | `...requesthandleravgidlepercent` | Time series, red below 20 |

---

## Azure Service Bus

### The constraint

**You cannot look inside the broker.** No logs, no exec, no thread dumps. Only Azure Monitor metrics and diagnostics you enabled **in advance**.

Turn on diagnostic settings before you need them — they are not retroactive:

```bash
az monitor diagnostic-settings create --name sb-diagnostics \
  --resource "$NS_ID" --workspace "$LOG_ANALYTICS_ID" \
  --logs '[{"category":"OperationalLogs","enabled":true},
           {"category":"RuntimeAuditLogs","enabled":true},
           {"category":"ApplicationMetricsLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

To get Service Bus metrics into Prometheus, use the **azure-metrics-exporter** or Azure Monitor managed Prometheus.

### Metrics that matter

| Metric | Meaning | Alert |
|---|---|---|
| `ActiveMessages` | Backlog per entity | > 10 min of traffic |
| `DeadletteredMessages` | Poison messages | **> 0** |
| `ScheduledMessages` | Future deliveries pending | Unexpected growth |
| `ThrottledRequests` | Over tier capacity | > 0 for 5 min |
| `ServerErrors` | Azure-side fault | > 0 for 5 min |
| `UserErrors` | Your bug — auth, missing entity, bad filter | > 10/min |
| `NamespaceCpuUsage` | Premium headroom | > 70% |
| `NamespaceMemoryUsage` | Premium headroom | > 75% |
| `ActiveConnections` | Consumers attached | Sudden drop |
| `Size` | Approaching the entity cap | > 80% of max |

### KQL for what metrics do not cover

```kusto
// Dead-letter reasons, grouped. Run this BEFORE fixing anything —
// a thousand dead letters is usually one bug.
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.SERVICEBUS"
| where Category == "OperationalLogs" and OperationName == "DeadLetter"
| summarize count() by DeadLetterReason = tostring(parse_json(Properties).reason), EntityName
| order by count_ desc
```

```kusto
// Throttling by entity — which queue is over capacity?
AzureMetrics
| where ResourceProvider == "MICROSOFT.SERVICEBUS" and MetricName == "ThrottledRequests"
| where Total > 0
| summarize sum(Total) by bin(TimeGenerated, 5m), Resource
| render timechart
```

```kusto
// Operation count, for cost. Catches incidents A4 and A5 —
// both were found by finance months late.
AzureMetrics
| where ResourceProvider == "MICROSOFT.SERVICEBUS"
| where MetricName in ("IncomingMessages", "OutgoingMessages")
| summarize Operations = sum(Total) by bin(TimeGenerated, 1d), MetricName
| render columnchart
```

### Client-side instrumentation — carries more weight here

Because you cannot see inside the broker, the client is your only real observability. Emit these:

| Metric | Why | Catches |
|---|---|---|
| Handler duration histogram | Compare against lock duration | A1 — lock expiry |
| `DeliveryCount` distribution | A rising tail means locks expiring | A1 |
| Settlement outcomes (complete/abandon/deadletter/defer) | The shape of your failure handling | A7, A10 |
| Lock renewal count | Renewals happening means handlers are slow | A1 |
| Active session count | The real concurrency ceiling | A3 |

```csharp
_metrics.CreateHistogram<double>("sb.handler.duration").Record(sw.Elapsed.TotalSeconds,
    new("entity", queueName), new("outcome", outcome));
_metrics.CreateHistogram<int>("sb.delivery.count").Record(message.DeliveryCount,
    new("entity", queueName));
```

### Alert rules

```yaml
groups:
- name: servicebus
  rules:
  - alert: ServiceBusDeadLetterNonZero
    # Zero is the correct steady state. This alert would have caught A7 three weeks earlier.
    expr: azure_servicebus_deadletteredmessages > 0
    for: 15m
    labels: { severity: warning, page: "true" }
    annotations:
      summary: "{{ $value }} dead-lettered messages on {{ $labels.entity }}"
      runbook: "https://…/runbooks/azure-runbook.md#incident-3--dead-letter-queue-filling"

  - alert: ServiceBusThrottled
    expr: rate(azure_servicebus_throttledrequests[5m]) > 0
    for: 5m
    labels: { severity: warning, page: "true" }
    annotations:
      summary: "Service Bus throttling on {{ $labels.namespace }}"
      runbook: "https://…/runbooks/azure-runbook.md#incident-1--throttling"

  - alert: ServiceBusCpuHigh
    # Leading indicator — scale before throttling starts, not after.
    expr: azure_servicebus_namespacecpuusage > 70
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Namespace CPU at {{ $value }}% — consider scaling messaging units"

  - alert: ServiceBusServerErrors
    expr: rate(azure_servicebus_servererrors[5m]) > 0
    for: 5m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Azure-side errors — check Service Health"

  - alert: ServiceBusNoConsumers
    expr: azure_servicebus_activeconnections == 0 and azure_servicebus_activemessages > 0
    for: 5m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Messages waiting on {{ $labels.entity }} with no consumers attached"

  - alert: ServiceBusLockExpiryHigh
    # Client-side metric. p95 delivery count above 2 means locks are expiring.
    expr: histogram_quantile(0.95, rate(sb_delivery_count_bucket[10m])) > 2
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "High redelivery on {{ $labels.entity }} — check prefetch and lock renewal"
      runbook: "https://…/runbooks/azure-runbook.md#incident-5--lock-expiry-and-duplicate-processing"
```

---

## RabbitMQ

### Exporter

Use the built-in `rabbitmq_prometheus` plugin on port 15692. **Do not scrape the management HTTP API** — that endpoint aggregates across every queue and is expensive. On a cluster with many queues it consumes more CPU than the message traffic itself. That is [incident R10](production-incidents.md#r10--the-management-ui-as-a-production-dependency).

### The queries

**The outage signal**

```promql
# Publishers blocked. This is "everything is stopped".
sum(rabbitmq_connections_blocked)

# How close is memory to the watermark that causes it?
100 * rabbitmq_process_resident_memory_bytes / rabbitmq_resident_memory_limit_bytes

# Disk headroom before the disk-based block
rabbitmq_disk_space_available_bytes / rabbitmq_disk_space_available_limit_bytes
```

**Queue health**

```promql
sum by (queue) (rabbitmq_queue_messages_ready)
sum by (queue) (rabbitmq_queue_messages_unacked)

# consumer_utilisation — the most useful and least-known RabbitMQ metric.
#   ~1.0 = saturated, scale out
#   ~0.3 = starved, prefetch too low
#   ~0.0 = attached but stuck, take a thread dump
avg by (queue) (rabbitmq_queue_consumer_utilisation)

# Queues that should have consumers but do not — catches incident R6
rabbitmq_queue_consumers{queue=~".*\\.work"} == 0

# Queue growth rate: positive and sustained means you will not catch up
deriv(rabbitmq_queue_messages_ready[10m])
```

**Cluster health**

```promql
# Network partitions — non-zero means split brain
sum(rabbitmq_cluster_partition_count)

# Node count. Alerts on a node that left and never came back.
count(rabbitmq_build_info)

# File descriptors — a quiet killer at high connection counts
100 * rabbitmq_process_open_fds / rabbitmq_process_max_fds
```

**Quorum queue health**

```promql
# Raft members per queue. Below the majority and the queue is unavailable.
rabbitmq_raft_log_last_applied_index - rabbitmq_raft_log_last_written_index
```

### Alert rules

```yaml
groups:
- name: rabbitmq-critical
  rules:
  - alert: RabbitMQPublishersBlocked
    # From the application's view this is a total outage. Page immediately.
    expr: sum(rabbitmq_connections_blocked) > 0
    for: 1m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "RabbitMQ is BLOCKING publishers"
      description: "Memory or disk watermark hit. Every publisher cluster-wide is stalled."
      runbook: "https://…/runbooks/rabbitmq-runbook.md#incident-1--publishers-blocked"

  - alert: RabbitMQNetworkPartition
    expr: sum(rabbitmq_cluster_partition_count) > 0
    for: 2m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "RabbitMQ network partition detected"
      description: "Quorum queues degrade safely; classic mirrored queues may DIVERGE."
      runbook: "https://…/runbooks/rabbitmq-runbook.md#incident-4--network-partition-split-brain"

  - alert: RabbitMQMemoryNearWatermark
    # Leading indicator for the alert above. This is the one you want to fire first.
    expr: 100 * rabbitmq_process_resident_memory_bytes / rabbitmq_resident_memory_limit_bytes > 70
    for: 5m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Node at {{ $value }}% of the memory watermark — publishers block at 100%"

  - alert: RabbitMQNodeDown
    expr: count(rabbitmq_build_info) < 5
    for: 2m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Only {{ $value }} of 5 RabbitMQ nodes are up"

- name: rabbitmq-warning
  rules:
  - alert: RabbitMQQueueNotDraining
    expr: deriv(rabbitmq_queue_messages_ready[15m]) > 0 and rabbitmq_queue_messages_ready > 10000
    for: 15m
    labels: { severity: warning, page: "true" }
    annotations:
      summary: "Queue {{ $labels.queue }} is growing and will not catch up"
      runbook: "https://…/runbooks/rabbitmq-runbook.md#incident-2--queue-backlog-growing"

  - alert: RabbitMQNoConsumers
    # Catches R6 — pods look healthy, broker cancelled the consumer.
    expr: rabbitmq_queue_consumers{queue=~".*\\.work"} == 0
          and rabbitmq_queue_messages_ready{queue=~".*\\.work"} > 0
    for: 5m
    labels: { severity: critical, page: "true" }
    annotations:
      summary: "Queue {{ $labels.queue }} has messages but NO consumers"

  - alert: RabbitMQConsumerStarved
    # Prefetch too low — consumers idle waiting for work. Catches R2.
    expr: avg by (queue) (rabbitmq_queue_consumer_utilisation) < 0.4
          and rabbitmq_queue_messages_ready > 1000
    for: 15m
    labels: { severity: warning }
    annotations:
      summary: "Consumers on {{ $labels.queue }} are starved — raise prefetch"

  - alert: RabbitMQDeadLetterNonZero
    expr: rabbitmq_queue_messages_ready{queue=~".*parked|.*dlq"} > 0
    for: 15m
    labels: { severity: warning, page: "true" }
    annotations:
      summary: "{{ $value }} messages parked in {{ $labels.queue }}"

  - alert: RabbitMQUnackedStuck
    # High and FLAT unacked = consumers holding without settling. Catches R8.
    expr: rabbitmq_queue_messages_unacked > 1000
          and abs(deriv(rabbitmq_queue_messages_unacked[15m])) < 1
    for: 15m
    labels: { severity: warning }
    annotations:
      summary: "Unacked messages stuck on {{ $labels.queue }}"
      runbook: "https://…/runbooks/rabbitmq-runbook.md#incident-5--unacked-messages-piling-up"

  - alert: RabbitMQClassicMirroredQueues
    # Not an incident — a migration item. Removed in RabbitMQ 4.x.
    expr: rabbitmq_queue_messages{queue_type="classic"} > 0
    for: 1h
    labels: { severity: info }
    annotations:
      summary: "Classic queue {{ $labels.queue }} still in use — migrate to quorum"
```

---

## The dashboard that goes on the wall

One dashboard, four rows. Anyone walking past should be able to tell whether the system is healthy.

**Row 1 — Business (the only row most people need)**

| Panel | What it shows |
|---|---|
| Orders/min vs same day last week | The real health signal. A drop here matters; a broker metric might not. |
| End-to-end p50 / p99 | Order accepted → payment authorised |
| Failed orders (rate) | Should be flat at zero |
| **DLQ depth, all brokers** | Single stat, red if > 0 |

**Row 2 — Am I keeping up?**

| Panel | Query |
|---|---|
| Time to drain, per consumer group | The Kafka drain query |
| Queue depth, per queue | `rabbitmq_queue_messages_ready`, `azure_servicebus_activemessages` |
| Lag heatmap by partition | Makes skew visible instantly |
| Consumer count per queue/group | Zero is an alert, not a curiosity |

**Row 3 — Is the infrastructure healthy?**

| Panel | Threshold |
|---|---|
| Kafka under-replicated / offline partitions | Red if > 0 |
| RabbitMQ blocked connections | Red if > 0 |
| RabbitMQ memory % of watermark | Amber 70, red 90 |
| Service Bus CPU % | Amber 70 |
| Disk days remaining | Amber 14, red 7 |

**Row 4 — What will this cost?**

| Panel | Why |
|---|---|
| Service Bus operations/month | Catches incidents A4 and A5 |
| Kafka storage growth | 7-year retention compounds |
| Cross-region transfer | Billed, and routinely forgotten |
| Messaging units in use | Step-function cost |

### The three numbers for an incident commander

When someone asks "how bad is it?", these are the answers:

1. **Time to drain** — "12 minutes" not "400,000 messages"
2. **Failed orders per minute** — is the business actually affected?
3. **DLQ depth delta** — is data being lost, or just delayed?

Everything else is for the engineers fixing it.

---

## Getting started — the minimum viable setup

If you do nothing else, do these five, in this order:

1. **DLQ depth > 0** on every queue and topic, with a named owner. Cheapest, catches the most.
2. **The "everything is stopped" alert** per broker: offline partitions (Kafka), blocked publishers (RabbitMQ), throttled requests (Service Bus).
3. **`consumers == 0`** on any queue that should have them.
4. **Time to drain** > 15 minutes, per consumer group.
5. **Disk days remaining** < 7 (Kafka), memory % of watermark > 70 (RabbitMQ), CPU > 70% (Service Bus).

Those five would have caught 19 of the [30 incidents](production-incidents.md) before a customer did.

---

*Incidents these alerts catch: [`production-incidents.md`](production-incidents.md) · Response procedures: [`../runbooks/`](../runbooks/) · Concepts: [`tutorial.md`](tutorial.md)*
