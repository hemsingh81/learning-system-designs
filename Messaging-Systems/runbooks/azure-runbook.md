# Azure Service Bus Runbook

Operational procedures for Service Bus Premium. Written to be read at 3am by someone who did not build it.

**The defining difference from the other two runbooks:** you cannot log into the broker. There is no `kubectl exec`, no broker log, no thread dump. Every diagnostic here goes through the Azure control plane, and every fix is either a config change, a client change, or a support ticket. Plan your observability accordingly — by the time you need it, you cannot add it.

**Conventions.**

```bash
export NS=orders-sb-eu
export RG=rg-orders-prod
az extension add --name servicebus       # once
```

---

## Quick triage — first 90 seconds

```bash
# 1. Is the namespace healthy and are we being throttled?
az monitor metrics list --resource "$NS_ID" \
  --metric ThrottledRequests ServerErrors UserErrors \
  --interval PT1M --start-time $(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --output table

# 2. What is the backlog and is anything dead-lettered?
az servicebus queue show -g $RG --namespace-name $NS -n payment-commands \
  --query "countDetails" -o json

# 3. CPU and memory on the messaging units
az monitor metrics list --resource "$NS_ID" \
  --metric NamespaceCpuUsage NamespaceMemoryUsage \
  --interval PT1M --output table
```

`countDetails` is the object to read:

```json
{
  "activeMessageCount": 142000,      // waiting to be picked up
  "deadLetterMessageCount": 37,      // parked, needs a human
  "scheduledMessageCount": 400,      // future delivery
  "transferMessageCount": 0,         // in transit to another entity
  "transferDeadLetterMessageCount": 0
}
```

| Signal | Means | Go to |
|---|---|---|
| `ThrottledRequests > 0` | Over capacity for the tier | [Throttling](#incident-1--throttling) |
| `activeMessageCount` climbing | Consumers too slow or absent | [Backlog](#incident-2--backlog-growing) |
| `deadLetterMessageCount > 0` | Poison messages | [Dead letters](#incident-3--dead-letter-queue-filling) |
| `NamespaceCpuUsage > 70%` | Need more messaging units | [Capacity](#incident-4--messaging-unit-saturation) |
| High redelivery, low completion | Locks expiring | [Lock expiry](#incident-5--lock-expiry-and-duplicate-processing) |
| `ServerErrors > 0` | Azure-side problem | [Azure-side faults](#incident-7--azure-side-faults) |

---

## Incident 1 — Throttling

**Symptoms.** `ServiceBusException` with `Reason = ServiceBusy`. `ThrottledRequests` metric non-zero. Sends and receives intermittently failing.

**What it means by tier — these are different problems:**

| Tier | Cause | Fix |
|---|---|---|
| **Standard** | Shared capacity, credit-based throttling. You are competing with other tenants. | Move to Premium. There is no reliable tuning fix. |
| **Premium** | You have exceeded your messaging units. | Add messaging units. |

```bash
# Current capacity
az servicebus namespace show -g $RG -n $NS --query "sku" -o json

# Scale up — takes 1-2 minutes, no downtime, only 1/2/4/8/16 are valid
az servicebus namespace update -g $RG -n $NS --capacity 8
```

**Client-side check.** The SDK retries `ServiceBusy` automatically with exponential backoff. If your application is surfacing these as errors, someone has disabled retries or wrapped the call in a shorter timeout than the retry policy needs. Confirm the retry configuration matches [`../code/csharp/azure-producer.cs`](../code/csharp/azure-producer.cs).

**The Standard-tier billing trap.** On Standard, *every* operation is billed — including a receive that returns nothing. A receiver with a short `TryTimeout` in a tight loop generates millions of empty operations per day. Symptom: an unexpectedly large bill alongside throttling. Fix: use `ServiceBusProcessor`, or set `TryTimeout` to 30 seconds so the call long-polls.

---

## Incident 2 — Backlog growing

**Symptoms.** `activeMessageCount` climbing. Orders taking minutes instead of seconds.

```bash
# Is anything actually connected?
az monitor metrics list --resource "$NS_ID" \
  --metric ActiveConnections --interval PT1M --output table

# Rate in vs rate out — this is the whole diagnosis
az monitor metrics list --resource "$NS_ID" \
  --metric IncomingMessages OutgoingMessages \
  --interval PT1M --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --output table
```

If `IncomingMessages` exceeds `OutgoingMessages` consistently, you are under-provisioned on consumers, full stop.

**Scale consumers.** With KEDA configured (see [`../k8s/azure-service-bus-operator.md`](../k8s/azure-service-bus-operator.md)) this should be automatic. When it is not:

```bash
kubectl -n orders scale deploy/payment-worker --replicas=40
kubectl -n orders get scaledobject payment-worker -o yaml | grep -A5 status
```

**The sessions ceiling.** If the queue has `requiresSession: true`, concurrency is bounded by the number of *distinct active sessions*, not by message count. Forty pods against eight active order sessions leaves thirty-two pods idle while the backlog grows. Check:

```bash
az servicebus queue show -g $RG --namespace-name $NS -n payment-commands \
  --query "requiresSession"
```

If sessions are the bottleneck and ordering is not actually required for that message type, moving it to a non-session queue is the real fix. That is a design change, not a 3am change — note it and route around it for now.

**Emergency drain.** When a stale backlog is genuinely worthless (expired promotional notifications, for example), there is no offset reset like Kafka's. You delete messages:

```bash
# Receive-and-delete in bulk. Destructive. Be certain.
az servicebus queue delete -g $RG --namespace-name $NS -n low-priority-notifications
az servicebus queue create -g $RG --namespace-name $NS -n low-priority-notifications \
  --max-delivery-count 5 --lock-duration PT1M --enable-dead-lettering-on-message-expiration true
```

Recreating the queue is the fastest purge. It also drops the DLQ and any scheduled messages, so confirm those are expendable first.

---

## Incident 3 — Dead-letter queue filling

```bash
az servicebus queue show -g $RG --namespace-name $NS -n payment-commands \
  --query "countDetails.deadLetterMessageCount"
```

**Read the reason before acting.** The broker writes `DeadLetterReason` and `DeadLetterErrorDescription` on every message. Peek with the Service Bus Explorer in the portal, or with the drain code in [`../code/csharp/azure-consumer.cs`](../code/csharp/azure-consumer.cs).

| `DeadLetterReason` | Written by | Meaning |
|---|---|---|
| `MaxDeliveryCountExceeded` | Broker | Abandoned 5 times. Transient fault that never cleared, or a poison message. |
| `TTLExpiredException` | Broker | Message outlived its TTL before anyone processed it. Backlog problem. |
| `HeaderSizeExceeded` | Broker | Too many application properties. A producer bug. |
| `FilterEvaluationExceptionOccurred` | Broker | A subscription filter threw — usually a SQL filter referencing a property that is absent. |
| Anything else | **Your code** | Whatever string you passed to `DeadLetterMessageAsync`. |

That last row is why explicit dead-lettering with a meaningful reason (as in the sample) pays for itself the first time you triage.

**Replay.** Fix the cause first, then run the drain job. It resubmits with the original `MessageId` preserved so downstream idempotency still recognises the message. Never replay into an unfixed consumer.

**The transfer DLQ.** `transferDeadLetterMessageCount` is a separate, easily missed queue. Messages land there when forwarding between entities fails — for example a subscription with auto-forward whose target is full or deleted. Check it explicitly:

```bash
az servicebus queue show -g $RG --namespace-name $NS -n payment-commands \
  --query "countDetails.transferDeadLetterMessageCount"
```

---

## Incident 4 — Messaging unit saturation

**Symptoms.** `NamespaceCpuUsage` above 70%. Latency climbing. Intermittent throttling.

```bash
az monitor metrics list --resource "$NS_ID" \
  --metric NamespaceCpuUsage NamespaceMemoryUsage \
  --interval PT5M --start-time $(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --output table
```

```bash
az servicebus namespace update -g $RG -n $NS --capacity 8
```

Scaling is a **step function**: 1, 2, 4, 8, 16 messaging units. There is no 6. Doubling is the only move available, and it doubles the bill. Takes 1–2 minutes with no downtime.

**Above 16 MU** you have hit the ceiling of a single namespace. Options, in order of preference:

1. **Split by domain.** Separate namespaces for orders, notifications and telemetry. Usually the right answer — it also isolates blast radius.
2. **Move the firehose to Event Hubs.** If the volume is telemetry or events rather than commands, Service Bus is the wrong product for it. See the case study.
3. **Shard by key across namespaces.** Works, adds routing complexity you now own.

---

## Incident 5 — Lock expiry and duplicate processing

**Symptoms.** Same message processed twice. `DeliveryCount` climbing on messages that eventually succeed. Downstream duplicate side effects.

**Cause.** PeekLock gives you a lock with a deadline (60 seconds by default). Exceed it without completing, and the broker assumes you died and redelivers to someone else — while your original handler is still running.

**Diagnose.** Compare handler duration against lock duration:

```bash
az servicebus queue show -g $RG --namespace-name $NS -n payment-commands \
  --query "{lock:lockDuration, maxDelivery:maxDeliveryCount}"
```

**Fixes, in order:**

1. **Enable auto lock renewal** in the client. `MaxAutoLockRenewalDuration` should cover your realistic worst case, not your p50. See [`../code/csharp/azure-consumer.cs`](../code/csharp/azure-consumer.cs).

2. **Lower prefetch.** Prefetched messages hold their locks from the moment they land in your client buffer. A prefetch of 100 with a 2-second handler means messages 50–100 sit locked for over a minute doing nothing. `PrefetchCount = 0` is the safe default.

3. **Raise the lock duration** — capped at 5 minutes:

   ```bash
   az servicebus queue update -g $RG --namespace-name $NS -n payment-commands \
     --lock-duration PT5M
   ```

4. **Make the handler faster**, or split slow work into a second message.

**Duplicates will still happen.** Lock expiry is one cause among several; at-least-once delivery is the contract. The consumer must be idempotent — that is not a mitigation, it is the design. See [`../docs/tutorial.md`](../docs/tutorial.md#19-idempotency--the-pattern-that-makes-everything-else-safe).

---

## Incident 6 — Subscription receiving wrong messages

**Symptoms.** A subscription gets messages it should have filtered out, or gets nothing at all.

```bash
az servicebus topic subscription rule list \
  -g $RG --namespace-name $NS --topic-name order-events \
  --subscription-name payments -o table
```

**If a rule named `$Default` appears in that list alongside your rule, that is the bug.** Every new subscription is created with `$Default` matching everything (`1=1`). Adding your own rule does not replace it — the rules are ORed, so the catch-all wins and your filter does nothing.

```bash
az servicebus topic subscription rule delete \
  -g $RG --namespace-name $NS --topic-name order-events \
  --subscription-name payments --name '$Default'
```

**If the subscription receives nothing**, the filter references a property that does not exist. SQL filters on absent properties evaluate to false silently. Verify the producer actually sets it:

```bash
# The filter says: [region] = 'eu'
# Does the producer set ApplicationProperties["region"]? Check the code, not the docs.
```

Turn on `deadLetteringOnFilterEvaluationExceptions` so filter errors become visible dead letters instead of silence.

---

## Incident 7 — Azure-side faults

**Symptoms.** `ServerErrors` non-zero. Failures across multiple entities at once. Nothing changed on your side.

```bash
az monitor metrics list --resource "$NS_ID" --metric ServerErrors \
  --interval PT1M --output table

# Is Azure already reporting it?
az rest --method get \
  --url "https://management.azure.com/subscriptions/$SUB_ID/providers/Microsoft.ResourceHealth/events?api-version=2022-10-01&\$filter=eventType eq 'ServiceIssue'"
```

Also check [Azure Service Health](https://portal.azure.com/#blade/Microsoft_Azure_Health/AzureHealthBrowseBlade) in the portal, filtered to your region.

**What you can do:**

1. **Confirm the SDK is retrying.** Transient faults are the SDK's job; make sure nothing is short-circuiting it.
2. **Fail over**, if you have a Geo-DR alias and the outage is regional. Understand the cost first:

   ```bash
   az servicebus georecovery-alias fail-over -g $RG --namespace-name $NS --alias orders-sb-alias
   ```

   **Messages in flight are lost.** Geo-DR replicates metadata only. The pairing is also broken afterwards and must be re-established manually before you can fail back.

3. **Open a support ticket** with the correlation IDs from your exception logs. For a Premium namespace this is a legitimate path — you are paying for it.

There is no equivalent of "restart the broker". Accept that and design the client for it.

---

## Routine procedures

### Create a queue

Prefer the ASO custom resource in [`../k8s/azure-service-bus-operator.md`](../k8s/azure-service-bus-operator.md). CLI for emergencies:

```bash
az servicebus queue create -g $RG --namespace-name $NS -n payment-commands \
  --enable-session true \
  --max-delivery-count 5 \
  --lock-duration PT1M \
  --default-message-time-to-live P14D \
  --enable-dead-lettering-on-message-expiration true \
  --enable-duplicate-detection true \
  --duplicate-detection-history-time-window PT10M \
  --max-size 5120
```

### Create a topic with a filtered subscription

```bash
az servicebus topic create -g $RG --namespace-name $NS -n order-events \
  --enable-duplicate-detection true --max-size 5120

az servicebus topic subscription create -g $RG --namespace-name $NS \
  --topic-name order-events -n payments \
  --max-delivery-count 5 --lock-duration PT1M

# Delete the catch-all FIRST
az servicebus topic subscription rule delete -g $RG --namespace-name $NS \
  --topic-name order-events --subscription-name payments --name '$Default'

az servicebus topic subscription rule create -g $RG --namespace-name $NS \
  --topic-name order-events --subscription-name payments --name primary \
  --filter-sql-expression "sys.Label = 'OrderPlaced' AND [high-value] = false"
```

### Check depth across all queues

```bash
az servicebus queue list -g $RG --namespace-name $NS \
  --query "[].{name:name, active:countDetails.activeMessageCount, dlq:countDetails.deadLetterMessageCount}" \
  -o table
```

### Scale messaging units

```bash
az servicebus namespace update -g $RG -n $NS --capacity 8
```

### Test failover (do this in a drill, not in an incident)

```bash
az servicebus georecovery-alias show -g $RG --namespace-name $NS --alias orders-sb-alias
az servicebus georecovery-alias fail-over -g $RG --namespace-name $NS --alias orders-sb-alias
# Then re-pair manually. There is no automatic fail-back.
```

---

## What you cannot do — know this before the incident

| Wish | Reality |
|---|---|
| Read broker logs | Not available. Only metrics and diagnostic settings you enabled **in advance**. |
| Restart the broker | Not available. Scale the namespace or fail over. |
| Replay processed messages | Gone. Completed means deleted. If replay matters, use Event Hubs or Kafka. |
| Inspect a message without receiving it | `PeekMessagesAsync` — read-only, does not lock or count as a delivery. Use it. |
| See per-consumer detail | Not available. Instrument the client side; the broker will not tell you. |
| Move a message between queues | No server-side shovel. Receive and resend from your own code. |

Turn on diagnostic settings **now**, before you need them:

```bash
az monitor diagnostic-settings create --name sb-diagnostics \
  --resource "$NS_ID" \
  --workspace "$LOG_ANALYTICS_ID" \
  --logs '[{"category":"OperationalLogs","enabled":true},
           {"category":"RuntimeAuditLogs","enabled":true},
           {"category":"ApplicationMetricsLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

---

## Escalation

| Situation | Action |
|---|---|
| `ServerErrors` sustained, Service Health shows an incident | Open a Sev A support ticket. Escalate internally to whoever owns the Azure relationship. |
| Throttling on Premium at 16 MU | Page the messaging lead — this is an architecture problem, not an ops problem. |
| DLQ growing on a payment path | Page the owning service team. |
| Considering Geo-DR failover | Page the messaging lead **and** a business decision-maker. In-flight messages will be lost. |
| Backlog > 30 minutes on order intake | Page. Check whether sessions are the ceiling before scaling further. |
