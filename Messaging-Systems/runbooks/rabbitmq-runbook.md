# RabbitMQ Runbook

Operational procedures for a 5-node RabbitMQ cluster with quorum queues. Written to be read at 3am by someone who did not build it.

**Conventions.**

```bash
alias rx='kubectl -n messaging exec -it orders-rabbit-0 --'
# Management UI: kubectl -n messaging port-forward svc/orders-rabbit 15672:15672
```

---

## Quick triage — first 90 seconds

```bash
# 1. Are publishers blocked? This is the RabbitMQ equivalent of "everything is down".
rx rabbitmqctl list_connections name state | grep -c blocked

# 2. Cluster whole? Any partitions?
rx rabbitmqctl cluster_status

# 3. What is backing up?
rx rabbitmqctl list_queues name messages messages_ready messages_unacknowledged consumers \
  | sort -k2 -rn | head -20
```

| Output | Means | Go to |
|---|---|---|
| Any connection `blocked` | Memory or disk watermark hit | [Publishers blocked](#incident-1--publishers-blocked) |
| `partitions` non-empty | Network split | [Network partition](#incident-4--network-partition-split-brain) |
| High `messages_ready`, consumers > 0 | Consumers too slow | [Queue backlog](#incident-2--queue-backlog-growing) |
| High `messages_ready`, consumers = 0 | Nobody is listening | [No consumers](#incident-3--no-consumers-attached) |
| High `messages_unacknowledged`, flat | Consumers holding without acking | [Unacked pile-up](#incident-5--unacked-messages-piling-up) |
| `orders.parked` non-zero | Poison messages | [Dead letters](#incident-6--dead-letter-queue-filling) |

---

## Incident 1 — Publishers blocked

**The signature RabbitMQ outage.** Every publisher stalls at once. From the application side it looks like a total broker failure; the broker is actually fine and deliberately applying the brakes.

**Symptoms.** Publishes hang. `rabbitmq_connections_blocked > 0`. Consumers still working normally.

**Why it happens.** RabbitMQ blocks all publishers when memory crosses `vm_memory_high_watermark` or free disk drops below `disk_free_limit`. It is back-pressure, not a crash.

**Diagnose:**

```bash
rx rabbitmqctl status | grep -A5 -E 'memory|disk_free'
rx rabbitmqctl list_connections name state user | grep blocked | head
rx rabbitmqctl list_queues name messages memory | sort -k3 -rn | head -10
```

That last command names the culprit: the queue holding the memory.

**Fix, in order:**

1. **Drain the big queue.** Scale up its consumers. This is the real fix — the queue is deep because nobody is emptying it.

   ```bash
   kubectl -n orders scale deploy/payment-worker --replicas=30
   ```

2. **Buy headroom temporarily.** Raises the ceiling; does not fix the cause.

   ```bash
   rx rabbitmqctl set_vm_memory_high_watermark 0.75    # from 0.6
   ```

   Set a reminder to put it back. A permanently raised watermark means the next incident is an OOMKill instead of a block, which is strictly worse.

3. **Free disk**, if the trigger was disk rather than memory:

   ```bash
   rx rabbitmqctl set_disk_free_limit "4GB"    # temporarily lower the floor
   kubectl -n messaging patch pvc data-orders-rabbit-0 \
     -p '{"spec":{"resources":{"requests":{"storage":"400Gi"}}}}'
   ```

4. **Last resort — purge a non-critical queue.** Deletes messages permanently:

   ```bash
   rx rabbitmqctl purge_queue telemetry.firehose
   ```

**Prevent.** Set `x-max-length` with `x-overflow: reject-publish` on every queue, as in [`../code/csharp/rabbitmq-producer.cs`](../code/csharp/rabbitmq-producer.cs). A bounded queue rejects publishes to *one* queue instead of blocking publishers to *all* of them. The blast radius difference is enormous.

---

## Incident 2 — Queue backlog growing

**Symptoms.** `messages_ready` climbing. Consumers attached and working.

```bash
rx rabbitmqctl list_queues name messages_ready messages_unacknowledged \
   consumers consumer_utilisation message_stats.deliver_get_details.rate
```

**`consumer_utilisation` is the number to read.** It is the fraction of time consumers were able to receive. Interpretation:

| Value | Meaning | Action |
|---|---|---|
| ~1.0 | Consumers are saturated — genuinely too slow | Scale out, or speed up the handler |
| ~0.3 | Consumers are idle waiting for messages | Prefetch is too low — raise it |
| ~0.0 | Consumers are attached but not consuming | Blocked in the handler; take a thread dump |

**The prefetch mistake, in both directions.** Prefetch too low starves consumers between round trips. Prefetch unlimited (the default) lets the first consumer to connect claim the whole queue while everyone else idles — and that memory counts toward the watermark in Incident 1.

```bash
# See how work is actually distributed
rx rabbitmqctl list_consumers queue_name channel_pid prefetch_count
```

If one consumer shows a huge prefetch and the others near zero, that is the bug. Set an explicit prefetch — 20 is a sane starting point for sub-second handlers.

**Scale out:**

```bash
kubectl -n orders scale deploy/payment-worker --replicas=40
```

Unlike Kafka, RabbitMQ has no partition ceiling — any number of consumers can share one queue. The limit is the broker's dispatch rate and your downstream dependencies.

---

## Incident 3 — No consumers attached

**Symptoms.** `messages_ready` growing, `consumers = 0`.

```bash
rx rabbitmqctl list_queues name consumers | awk '$2 == 0'
rx rabbitmqctl list_connections name user peer_host state
kubectl -n orders get pods -l app=payment-worker
```

Causes, in order:

1. **Workers are down or crash-looping.** Check pods and logs.
2. **Consumers were cancelled by `consumer_timeout`.** The broker cancels a consumer that holds an unacked message longer than `consumer_timeout` (30 minutes by default). The application often does not notice.

   ```bash
   rx rabbitmqctl environment | grep consumer_timeout
   kubectl -n orders logs deploy/payment-worker | grep -i "consumer.*cancel"
   ```

   If handlers legitimately run long, raise it in [`../k8s/rabbitmq-helm-values.yaml`](../k8s/rabbitmq-helm-values.yaml). If they do not, find out why one is hanging.

3. **Connections blocked** — a blocked connection cannot consume either. See Incident 1.
4. **Wrong vhost or credentials after a deploy.** Check `rabbitmqctl list_permissions -p /orders`.

---

## Incident 4 — Network partition (split-brain)

**Symptoms.** `rabbitmqctl cluster_status` shows a non-empty `partitions` section. Nodes disagree about who is in the cluster.

```bash
rx rabbitmqctl cluster_status
```

```
Network Partitions
  node rabbit@orders-rabbit-0: [rabbit@orders-rabbit-3, rabbit@orders-rabbit-4]
```

**What this means by queue type — the distinction matters:**

| Queue type | Behaviour during a partition |
|---|---|
| **Quorum** | Raft handles it. The majority side keeps working; the minority side rejects operations. No data divergence. |
| **Classic mirrored** | Both sides may accept writes. On heal, one side's messages are **discarded**. This is why they are deprecated. |
| **Streams** | Like quorum — Raft-based. |

If you are on quorum queues, a partition is a degradation, not a data-loss event. That is the single best reason to migrate off classic mirrored queues.

**Fix.**

```bash
# 1. Find the real cause first — this is almost always the network or a
#    long GC pause, not RabbitMQ.
kubectl -n messaging get events --sort-by=.lastTimestamp | tail -30
kubectl -n messaging logs orders-rabbit-3 | grep -iE 'partition|net_tick|rabbit_node_monitor'

# 2. With autoheal (our config), the losing side restarts itself once
#    connectivity returns. Verify:
rx rabbitmqctl cluster_status

# 3. If a node stays stuck, restart it manually.
kubectl -n messaging delete pod orders-rabbit-3
```

**If autoheal did not trigger**, force it by restarting the minority-side nodes one at a time. Never restart the majority side — that is how you turn a degradation into an outage.

**Prevent.** `net_ticktime` defaults to 60 seconds; a GC pause or a slow node can exceed it and trigger a false partition. Our config sets `heartbeat = 30`. If false partitions recur, the answer is fixing node latency, not raising the timeout further.

---

## Incident 5 — Unacked messages piling up

**Symptoms.** `messages_unacknowledged` high and flat. Consumers connected. Throughput near zero.

This means consumers have taken messages and never settled them. The messages are invisible to other consumers and will redeliver only when the connection drops.

```bash
rx rabbitmqctl list_queues name messages_unacknowledged consumers
rx rabbitmqctl list_channels connection name prefetch_count messages_unacknowledged
```

**Causes:**

1. **Handler deadlock.** Take a thread dump from the worker. Common with a synchronous call to a hung dependency inside the message handler.
2. **Missing ack path.** A code path that returns without calling ack, nack or reject. Read the handler and confirm every branch settles the message.
3. **Sharing a channel across threads.** A channel is not thread-safe; concurrent use corrupts the delivery-tag sequence and acks land on the wrong message.

**Immediate relief** — dropping the connection returns unacked messages to the queue:

```bash
rx rabbitmqctl close_connection "<connection-name>" "clearing stuck consumer"
# or just restart the workers
kubectl -n orders rollout restart deploy/payment-worker
```

Those messages redeliver with `redelivered=true`. Idempotent consumers handle that without issue — which is the point of building them that way.

---

## Incident 6 — Dead-letter queue filling

```bash
rx rabbitmqctl list_queues name messages | grep parked
```

**Read before you act.** The `x-death` header carries the full audit trail: original queue, reason, count, timestamp. Pull one message through the management API and look:

```bash
curl -su admin:$PASS -X POST \
  http://localhost:15672/api/queues/%2Forders/orders.parked/get \
  -H 'content-type: application/json' \
  -d '{"count":5,"ackmode":"ack_requeue_true","encoding":"auto"}' | jq '.[].properties.headers'
```

`ackmode: ack_requeue_true` peeks without consuming. Use it every time you inspect.

**Group by reason before fixing anything.** A thousand dead letters is usually one bug.

| `x-death` reason | Meaning | Typical fix |
|---|---|---|
| `rejected` | Consumer called `basicNack(requeue: false)` | Read the consumer logs for the exception |
| `expired` | Message TTL elapsed | Consumers too slow, or TTL too aggressive |
| `maxlen` | Queue hit `x-max-length` | Backlog — see Incident 2 |
| `delivery_limit` | Quorum queue redelivery cap hit | A poison message that kept failing |

**Replay** using the triage code in [`../code/csharp/rabbitmq-consumer.cs`](../code/csharp/rabbitmq-consumer.cs), or with a shovel for bulk:

```bash
rx rabbitmqctl set_parameter shovel replay-parked \
  '{"src-uri":"amqp:///orders","src-queue":"orders.parked",
    "dest-uri":"amqp:///orders","dest-exchange":"orders",
    "dest-add-forward-headers":true,"ack-mode":"on-confirm",
    "src-delete-after":"queue-length"}'
```

`src-delete-after: queue-length` stops the shovel once it has moved what was there when it started — without it, a message that fails again loops forever between the queues.

Remove the shovel when done:

```bash
rx rabbitmqctl clear_parameter shovel replay-parked
```

**Fix the cause before replaying.** Replaying into an unfixed consumer just refills the parked queue and burns an hour.

---

## Incident 7 — Quorum queue lost quorum

**Symptoms.** Operations on one queue fail while others work. Logs show `ra` (the Raft library) errors.

```bash
rx rabbitmqctl quorum_status payment.work
rx rabbitmqctl list_queues name type members leader
```

A quorum queue with 3 replicas needs 2 alive. Lost 2 of 3 and the queue is unavailable — reads and writes both.

```bash
# Restore the down nodes. This is the correct fix.
kubectl -n messaging get pods -l app.kubernetes.io/name=rabbitmq

# If a node is permanently gone, remove it from the queue's membership
# and add a healthy one.
rx rabbitmqctl delete_member payment.work rabbit@orders-rabbit-3
rx rabbitmqctl add_member payment.work rabbit@orders-rabbit-4
```

**Last resort** — force a single surviving replica to become the leader. **This loses any messages the survivor did not have:**

```bash
rx rabbitmqctl force_shrink_member_to_current_member payment.work
```

Same rule as Kafka's unclean leader election: get sign-off, note the time, reconcile from the source afterwards.

---

## Routine procedures

### Create a queue and binding

Prefer definitions loaded from the `rabbit-definitions` secret so topology lives in git. Manually:

```bash
rx rabbitmqadmin declare queue name=payment.work durable=true \
  arguments='{"x-queue-type":"quorum","x-dead-letter-exchange":"orders.dlx","x-delivery-limit":5}'

rx rabbitmqadmin declare binding source=orders destination=payment.work \
  routing_key="order.*.placed"
```

### Inspect a queue

```bash
rx rabbitmqctl list_queues name type durable messages messages_ready \
   messages_unacknowledged consumers consumer_utilisation memory state
```

### Purge

```bash
rx rabbitmqctl purge_queue telemetry.firehose    # permanent
```

### Move messages between queues

```bash
rx rabbitmqctl set_parameter shovel drain-old \
  '{"src-uri":"amqp:///orders","src-queue":"old.queue",
    "dest-uri":"amqp:///orders","dest-queue":"new.queue",
    "ack-mode":"on-confirm","src-delete-after":"queue-length"}'
```

### Rolling restart

```bash
kubectl -n messaging rollout restart statefulset/orders-rabbit
```

One pod at a time (`podManagementPolicy: OrderedReady`). Watch `rabbitmqctl cluster_status` between pods. A parallel restart loses quorum on every queue at once.

### Check for classic mirrored queues (migrate these)

```bash
rx rabbitmqctl list_queues name type | grep -v quorum | grep -v stream
```

Classic mirrored queues are removed in RabbitMQ 4.x. Anything on that list is a migration item, not a preference.

---

## Escalation

| Situation | Action |
|---|---|
| Publishers blocked > 5 minutes | Page immediately. This is a full outage from the app's view. |
| Network partition with classic mirrored queues | Page the messaging lead. Data divergence is possible. |
| Quorum lost on a payment queue | Page the messaging lead **and** a business decision-maker before force-shrink. |
| Disk > 85% on any node | Page. The block threshold is close. |
| Parked queue growing steadily | Page the owning service team. It is their bug, not the broker's. |
