# Kafka Runbook

Operational procedures for a Strimzi-managed Kafka cluster. Written to be read at 3am by someone who did not build it.

**Conventions.** `$NS` = namespace (`kafka`). `$CLUSTER` = cluster name (`orders-kafka`). `$BS` = bootstrap servers. Commands assume you can `kubectl exec` into a broker pod:

```bash
alias kx='kubectl -n kafka exec -it orders-kafka-broker-0 --'
export BS=orders-kafka-kafka-bootstrap:9092
```

---

## Quick triage — first 90 seconds

Run these three, in order, before forming a theory.

```bash
# 1. Is the cluster whole? Under-replicated partitions is THE health metric.
kx bin/kafka-topics.sh --bootstrap-server $BS --describe --under-replicated-partitions

# 2. Who is behind, and by how much?
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS --describe --all-groups \
  | awk 'NR==1 || $6 > 10000'

# 3. Are the brokers up and is anything offline?
kubectl -n kafka get pods -l strimzi.io/cluster=orders-kafka
kx bin/kafka-topics.sh --bootstrap-server $BS --describe --unavailable-partitions
```

| Output | Means | Go to |
|---|---|---|
| Under-replicated > 0, stable | A broker is down or a follower is slow | [Broker down](#incident-1--broker-down) |
| Under-replicated > 0, climbing | Replication cannot keep up with writes | [Replication lag](#incident-6--replication-cannot-keep-up) |
| Unavailable partitions > 0 | **Data is offline.** Below min.insync.replicas | [Quorum loss](#incident-7--partitions-offline--quorum-lost) |
| Lag high on one group only | A consumer problem, not a broker problem | [Consumer lag](#incident-2--consumer-lag-climbing) |
| Lag high on all groups | A broker problem | [Broker down](#incident-1--broker-down) |
| Everything clean, users complaining | Look at producer-side latency and the app | [Producer stalls](#incident-4--producers-timing-out) |

---

## Incident 1 — Broker down

**Symptoms.** `UnderReplicatedPartitions > 0`. Producer latency up. One pod in `CrashLoopBackOff` or `Pending`.

**Impact.** With RF=3 and `min.insync.replicas=2`, losing one broker is survivable — writes continue. Losing a second on the same partitions stops writes.

**Diagnose.**

```bash
kubectl -n kafka describe pod orders-kafka-broker-2
kubectl -n kafka logs orders-kafka-broker-2 --tail=200
kubectl -n kafka get pvc -l strimzi.io/cluster=orders-kafka   # disk full?
```

Three usual causes, in order of frequency:

1. **Disk full.** Log segments filled the PVC. Check `kubectl exec ... -- df -h /var/lib/kafka/data`.
2. **OOMKilled.** Check `kubectl describe pod` for `Last State: Terminated, Reason: OOMKilled`. Usually a heap set too high relative to the container limit — Kafka wants a *small* heap and a *large* page cache.
3. **Node lost.** Pod is `Pending` with no node to schedule on.

**Fix — disk full.** Do not delete files by hand. Reduce retention, let the broker clean up, then expand:

```bash
# Temporary relief: cut retention on the biggest topic
kx bin/kafka-configs.sh --bootstrap-server $BS --alter \
  --entity-type topics --entity-name orders.v1 \
  --add-config retention.ms=86400000      # 1 day, from 7

# Then expand the volume (requires a storage class with allowVolumeExpansion)
kubectl -n kafka patch pvc data-0-orders-kafka-broker-2 \
  -p '{"spec":{"resources":{"requests":{"storage":"1500Gi"}}}}'

# Restore retention once headroom is back
kx bin/kafka-configs.sh --bootstrap-server $BS --alter \
  --entity-type topics --entity-name orders.v1 \
  --delete-config retention.ms
```

**Fix — OOMKilled.** Lower the heap, not raise it. In [`../k8s/kafka-helm-values.yaml`](../k8s/kafka-helm-values.yaml), `-Xmx` should be roughly 20–25% of the container memory limit. A 6 GB heap in a 32 GB container is right; a 24 GB heap in a 32 GB container will thrash.

**Verify.** Under-replicated returns to 0 and stays there for 10 minutes.

**Do not** delete the PVC to "start fresh". That destroys the replica and forces a full re-sync of every partition it held, which is hours of network saturation and makes the incident worse.

---

## Incident 2 — Consumer lag climbing

**Symptoms.** `kafka_consumergroup_lag` rising steadily. Downstream data is stale. No broker alarms.

**First question: is it throughput or is it stuck?** These look identical on a lag graph and have opposite fixes.

```bash
# Run twice, 30 seconds apart. Compare CURRENT-OFFSET.
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS \
  --describe --group payments-service
```

| CURRENT-OFFSET between runs | Diagnosis |
|---|---|
| Not moving at all | **Stuck.** A poison message, a deadlock, or a rebalance loop. |
| Moving, slower than LOG-END-OFFSET grows | **Too slow.** Scale up or speed up. |
| Moving, but only on some partitions | **Skewed keys.** One partition is hot. |

**If stuck — check for a rebalance loop first.** This is the most common cause and the least obvious:

```bash
kubectl -n orders logs deploy/payment-worker --tail=500 | grep -iE "rebalanc|revoked|assigned"
```

Seeing "Revoked / Assigned" repeatedly, every few seconds, means the group cannot settle. The consumer is exceeding `max.poll.interval.ms` — processing takes longer than the group's patience, so it gets evicted mid-work, which triggers a rebalance, which restarts the work, forever. Fix: raise `MaxPollIntervalMs`, or process fewer records per poll. Raising `SessionTimeoutMs` does **not** help and is the usual wrong turn.

**If stuck — find the poison message:**

```bash
# What offset is it wedged on?
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group payments-service

# Read that exact record without joining the group
kx bin/kafka-console-consumer.sh --bootstrap-server $BS \
  --topic orders.v1 --partition 7 --offset 1044235 --max-messages 1 \
  --property print.headers=true
```

Skipping past it — **only** after you have captured the message and understand what it is:

```bash
kubectl -n orders scale deploy/payment-worker --replicas=0     # must be stopped

kx bin/kafka-consumer-groups.sh --bootstrap-server $BS \
  --group payments-service --topic orders.v1:7 \
  --reset-offsets --to-offset 1044236 --execute

kubectl -n orders scale deploy/payment-worker --replicas=6
```

> Offset reset requires the group to have **no active members**. If it refuses, something is still connected.

**If too slow — scale, within limits:**

```bash
# You cannot have more useful consumers than partitions.
kx bin/kafka-topics.sh --bootstrap-server $BS --describe --topic orders.v1 | head -1

kubectl -n orders scale deploy/payment-worker --replicas=12
```

If replicas already equal partition count, more pods do nothing. Either make the handler faster, or add partitions — and note that **adding partitions changes key-to-partition mapping**, so ordering across the boundary is broken for in-flight keys. Do it during a quiet window, and never on a compacted topic.

**Emergency: skip to now.** Data loss, deliberate. Only when a stale backlog is worthless — for example, live inventory:

```bash
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS \
  --group payments-service --all-topics --reset-offsets --to-latest --execute
```

---

## Incident 3 — Consumer group rebalancing constantly

**Symptoms.** Throughput sawtooths. Logs full of partition assignment churn. Lag oscillates.

**Causes, in order of likelihood:**

1. **Processing exceeds `max.poll.interval.ms`.** See Incident 2.
2. **Eager rebalancing on a rolling deploy.** Every pod restart stops the entire group. Fix permanently by switching to `CooperativeSticky` — see [`../code/csharp/kafka-consumer.cs`](../code/csharp/kafka-consumer.cs).
3. **Liveness probe killing healthy pods.** A pod busy processing does not answer `/healthz` fast enough, Kubernetes kills it, the group rebalances, the next pod inherits more work and is slower still. Check `kubectl get pods` for climbing RESTARTS.
4. **`session.timeout.ms` shorter than a GC pause.** Rare with modern GCs, but real on heap-heavy consumers.

**Confirm which:**

```bash
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group payments-service --state
kubectl -n orders get pods -l app=payment-worker    # RESTARTS column
```

`STATE: PreparingRebalance` for more than ~30 seconds means a member is not responding to the join request — usually one stuck instance holding the whole group hostage. Find it and kill it:

```bash
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group payments-service --members
kubectl -n orders delete pod <the-stuck-one>
```

---

## Incident 4 — Producers timing out

**Symptoms.** `Local: Message timed out` or `NOT_ENOUGH_REPLICAS` in application logs. Order submissions failing.

```bash
# Is the cluster accepting writes at all?
kx bin/kafka-topics.sh --bootstrap-server $BS --describe --topic orders.v1
```

Look at the `Isr:` field. If it lists fewer brokers than `min.insync.replicas`, **writes are rejected by design** — this is the durability guarantee working, not a bug. The fix is to restore the missing replica, not to lower the setting.

Under sustained pressure, resist this:

```bash
# DO NOT DO THIS to make an alert go away.
kx bin/kafka-configs.sh --bootstrap-server $BS --alter \
  --entity-type topics --entity-name orders.v1 --add-config min.insync.replicas=1
```

It converts "writes are failing loudly" into "writes may be silently lost". If you do it under extreme duress, write down the time, set a reminder, and revert within the hour.

**Other causes:**

| Error | Cause | Fix |
|---|---|---|
| `Local: Queue full` | Producer's in-memory buffer is full — broker slower than the app | Raise `QueueBufferingMaxMessages`, or apply backpressure upstream |
| `REQUEST_TIMED_OUT` | Broker is up but slow | Check broker CPU and disk latency |
| `TOPIC_AUTHORIZATION_FAILED` | ACL missing after a deploy | Check the `KafkaUser` resource |
| `RecordTooLargeException` | Message over `message.max.bytes` | Put the payload in blob storage, send a pointer |

---

## Incident 5 — Disk filling fast

```bash
kx df -h /var/lib/kafka/data

# Which topic is eating the space?
kx du -sh /var/lib/kafka/data/*/  | sort -rh | head -20
```

**Immediate relief**, in order of preference:

1. Cut retention on the largest topic (see Incident 1).
2. Enable tiered storage if licensed — old segments move to object storage.
3. Expand the PVC.
4. Add brokers and rebalance — slowest, but the real fix if this is growth, not a leak.

**The trap:** deleting `.log` files by hand while the broker runs. The broker holds open file handles and tracks segment metadata; removing files underneath it corrupts the partition and can lose committed data. Always go through retention config.

---

## Incident 6 — Replication cannot keep up

**Symptoms.** Under-replicated partitions climbing during normal operation, no broker down.

```bash
# Replication throughput per broker
kubectl -n kafka exec orders-kafka-broker-0 -- \
  curl -s localhost:9404/metrics | grep -E 'kafka_server_replicafetchermanager_maxlag'
```

**Fixes:**

```bash
# More fetcher threads (needs a rolling restart)
# In the Kafka CR: num.replica.fetchers: 8

# If a rebalance is saturating the network, throttle it
kx bin/kafka-configs.sh --bootstrap-server $BS --alter \
  --entity-type brokers --entity-default \
  --add-config leader.replication.throttled.rate=50000000,follower.replication.throttled.rate=50000000
```

Remember to **remove the throttle** when the rebalance finishes. A forgotten throttle is a slow-burning incident that surfaces weeks later as mysterious replication lag.

---

## Incident 7 — Partitions offline / quorum lost

**This is the serious one.** Unavailable partitions means data is not readable or writable.

```bash
kx bin/kafka-topics.sh --bootstrap-server $BS --describe --unavailable-partitions
kubectl -n kafka get pods -l strimzi.io/cluster=orders-kafka
kubectl -n kafka logs orders-kafka-controller-0 --tail=100
```

**Decision point.** You have two options and they are not equivalent:

**Option A — restore the brokers.** Correct, and always the first choice. Bring the down brokers back; partitions recover automatically. Time: however long the brokers take.

**Option B — unclean leader election.** Promotes an out-of-sync replica to leader. Availability returns **immediately** and you **silently lose** every record the new leader had not yet replicated.

```bash
# LAST RESORT. This loses data. Get explicit sign-off. Write down the time.
kx bin/kafka-leader-election.sh --bootstrap-server $BS \
  --election-type UNCLEAN --all-topic-partitions
```

Only choose B when the brokers are genuinely unrecoverable **and** the business has decided availability outranks completeness for this data. Then reconcile from the source system afterwards — the outbox table, the upstream database, whatever produced the events.

---

## Routine procedures

### Create a topic

Prefer the `KafkaTopic` custom resource in [`../k8s/kafka-helm-values.yaml`](../k8s/kafka-helm-values.yaml) so the definition is in git. CLI is for emergencies:

```bash
kx bin/kafka-topics.sh --bootstrap-server $BS --create \
  --topic orders.v2 --partitions 60 --replication-factor 3 \
  --config min.insync.replicas=2 --config retention.ms=604800000
```

### Inspect lag for one group

```bash
kx bin/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group payments-service
```

Columns that matter: `CURRENT-OFFSET` (where the group is), `LOG-END-OFFSET` (where the topic is), `LAG` (the gap), `CONSUMER-ID` (empty means **no active consumer** — the group is dead, not slow).

### Read the dead-letter topic

```bash
kx bin/kafka-console-consumer.sh --bootstrap-server $BS \
  --topic orders.v1.dlq --from-beginning --max-messages 20 \
  --property print.headers=true --property print.key=true
```

Group failures by the `dlq-reason` header before fixing anything — a hundred dead letters are usually one bug.

### Replay a time range

```bash
kubectl -n orders scale deploy/payment-worker --replicas=0

kx bin/kafka-consumer-groups.sh --bootstrap-server $BS \
  --group payments-service --topic orders.v1 \
  --reset-offsets --to-datetime 2026-07-25T14:00:00.000 --execute

kubectl -n orders scale deploy/payment-worker --replicas=6
```

Replay only works if consumers are idempotent. Verify that before you press it, not after — see [`../docs/tutorial.md`](../docs/tutorial.md#19-idempotency--the-pattern-that-makes-everything-else-safe).

### Purge a topic

```bash
# Set retention to 1ms, wait for the cleaner, restore.
kx bin/kafka-configs.sh --bootstrap-server $BS --alter \
  --entity-type topics --entity-name scratch.topic --add-config retention.ms=1000
sleep 120
kx bin/kafka-configs.sh --bootstrap-server $BS --alter \
  --entity-type topics --entity-name scratch.topic --delete-config retention.ms
```

### Rolling restart

```bash
kubectl -n kafka annotate pod orders-kafka-broker-0 strimzi.io/manual-rolling-update=true
```

Strimzi restarts one broker at a time and waits for in-sync replicas to recover between each. Never restart brokers in parallel.

---

## Escalation

| Situation | Action |
|---|---|
| Unavailable partitions, brokers recoverable | Restore brokers. Page the messaging on-call. |
| Unavailable partitions, brokers lost | Page the messaging lead **and** a business decision-maker before unclean election. |
| Lag > 1 hour on a payment path | Page the owning service team. Kafka is probably not the problem. |
| Disk > 90% on any broker | Page. You have hours, not days. |
| KRaft controller quorum lost | Page the messaging lead. Do not restart controllers randomly. |
