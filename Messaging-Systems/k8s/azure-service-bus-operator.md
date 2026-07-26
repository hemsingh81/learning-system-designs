# Azure Service Bus on Kubernetes

**There is no broker to deploy.** Service Bus is a PaaS [platform as a service — Microsoft runs the servers, you rent the endpoint]. Nothing about it runs in your cluster. What you deploy is the *plumbing*: identity, network access, and the declaration of queues and topics.

That is the whole trade. You get no cluster to patch, no disk to size, no quorum to lose — and no `kubectl exec` when something is wrong. Every knob below exists because the broker is somebody else's.

---

## 1. Declare the namespace with the Azure Service Operator

The [Azure Service Operator](https://azure.github.io/azure-service-operator/) (ASO) lets you manage Azure resources as Kubernetes objects. Your topics live in the same GitOps repo as your Deployments.

```bash
helm repo add aso2 https://raw.githubusercontent.com/Azure/azure-service-operator/main/v2/charts
helm install aso2 aso2/azure-service-operator \
  -n azureserviceoperator-system --create-namespace \
  --set azureSubscriptionID=$SUB_ID \
  --set azureTenantID=$TENANT_ID \
  --set crdPattern='servicebus.azure.com/*'
```

```yaml
# service-bus-namespace.yaml
apiVersion: servicebus.azure.com/v1api20211101
kind: Namespace
metadata:
  name: orders-sb-eu
  namespace: messaging
spec:
  location: westeurope
  owner:
    name: rg-orders-prod
  sku:
    name: Premium
    tier: Premium
    # Messaging units are the unit of dedicated capacity: 1, 2, 4, 8 or 16.
    # Each is roughly 1000 msg/sec of headroom. This is the ONLY scaling knob
    # on Premium, and it is a step function, not a slider.
    capacity: 4
  zoneRedundant: true          # three availability zones. Premium only.
  disableLocalAuth: true       # kills connection strings. Entra ID or nothing.
  minimumTlsVersion: "1.2"
---
apiVersion: servicebus.azure.com/v1api20211101
kind: NamespacesQueue
metadata:
  name: payment-commands
  namespace: messaging
spec:
  owner:
    name: orders-sb-eu
  requiresSession: true                    # ordering per SessionId
  maxDeliveryCount: 5                      # then automatic dead-letter
  lockDuration: PT1M                       # ISO 8601 — 1 minute
  defaultMessageTimeToLive: P14D           # 14 days
  deadLetteringOnMessageExpiration: true   # expired != silently gone
  requiresDuplicateDetection: true
  duplicateDetectionHistoryTimeWindow: PT10M
  maxSizeInMegabytes: 5120
  enablePartitioning: false                # cannot be changed later; leave off
                                           # on Premium — it conflicts with
                                           # transactions across entities
---
apiVersion: servicebus.azure.com/v1api20211101
kind: NamespacesTopic
metadata:
  name: order-events
  namespace: messaging
spec:
  owner:
    name: orders-sb-eu
  defaultMessageTimeToLive: P7D
  requiresDuplicateDetection: true
  duplicateDetectionHistoryTimeWindow: PT10M
  maxSizeInMegabytes: 5120
  supportOrdering: true
---
apiVersion: servicebus.azure.com/v1api20211101
kind: NamespacesTopicsSubscription
metadata:
  name: payments
  namespace: messaging
spec:
  owner:
    name: order-events
  maxDeliveryCount: 5
  lockDuration: PT1M
  deadLetteringOnMessageExpiration: true
  deadLetteringOnFilterEvaluationExceptions: true
---
apiVersion: servicebus.azure.com/v1api20211101
kind: NamespacesTopicsSubscriptionsRule
metadata:
  name: payments-filter
  namespace: messaging
spec:
  owner:
    name: payments
  filterType: SqlFilter
  sqlFilter:
    expression: "sys.Label = 'OrderPlaced' AND [high-value] = false"
```

> **The `$Default` rule trap.** Every new subscription is born with a rule named `$Default` that matches everything (`1=1`). Adding your own rule does **not** replace it — the two are ORed, and your filter does nothing. ASO handles this when you declare a `Rule`, but if you create subscriptions any other way, delete `$Default` explicitly. This is the most common Service Bus misconfiguration in production.

---

## 2. Workload Identity — how pods authenticate

Connection strings are passwords that never expire and get copied into Slack. Use workload identity [a pod borrows an Azure identity through a short-lived token, with no secret stored anywhere].

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payment-worker
  namespace: orders
  annotations:
    azure.workload.identity/client-id: "00000000-0000-0000-0000-000000000000"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-worker
  namespace: orders
spec:
  replicas: 6
  selector:
    matchLabels: { app: payment-worker }
  template:
    metadata:
      labels:
        app: payment-worker
        azure.workload.identity/use: "true"    # required — the webhook looks for it
    spec:
      serviceAccountName: payment-worker
      containers:
        - name: worker
          image: acr.azurecr.io/payment-worker:1.4.2
          env:
            - name: SERVICEBUS_NAMESPACE
              value: orders-sb-eu.servicebus.windows.net
            # No password. DefaultAzureCredential in the SDK finds the projected
            # token automatically. See ../code/csharp/azure-consumer.cs
          resources:
            requests: { memory: 256Mi, cpu: "200m" }
            limits:   { memory: 512Mi, cpu: "1" }
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 15
          readinessProbe:
            httpGet: { path: /readyz, port: 8080 }
      # Give in-flight messages time to complete before the pod dies. Shorter
      # than this and you abandon messages on every deploy — which is safe, but
      # doubles your duplicate rate for no reason.
      terminationGracePeriodSeconds: 90
```

Grant the identity the least role that works:

```bash
# Send + receive, but NOT manage. The app should never be able to delete a queue.
az role assignment create \
  --role "Azure Service Bus Data Sender" \
  --assignee $CLIENT_ID \
  --scope "$NS_ID/topics/order-events"

az role assignment create \
  --role "Azure Service Bus Data Receiver" \
  --assignee $CLIENT_ID \
  --scope "$NS_ID/queues/payment-commands"
```

The three built-in roles: **Data Sender** (send only), **Data Receiver** (receive and settle), **Data Owner** (both, plus manage). Scope them per entity, not per namespace — a namespace-scoped Data Owner is a blast radius nobody needs.

---

## 3. Scaling workers on queue depth with KEDA

The number of pods should follow the backlog, not CPU. CPU-based autoscaling on a message consumer is close to useless: a worker waiting on a slow payment API uses no CPU while the queue grows to a million.

```yaml
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: sb-auth
  namespace: orders
spec:
  podIdentity:
    provider: azure-workload
    identityId: "00000000-0000-0000-0000-000000000000"
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: payment-worker
  namespace: orders
spec:
  scaleTargetRef:
    name: payment-worker
  minReplicaCount: 3          # never zero on a latency-sensitive path — cold
                              # start is 10-20s and the queue keeps filling
  maxReplicaCount: 60
  pollingInterval: 15
  cooldownPeriod: 300         # wait 5 min before scaling down. Flapping costs
                              # more than the extra pods.
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleUp:
          stabilizationWindowSeconds: 30    # react fast to a backlog
          policies:
            - type: Percent
              value: 100
              periodSeconds: 30
        scaleDown:
          stabilizationWindowSeconds: 300   # leave slowly
          policies:
            - type: Percent
              value: 20
              periodSeconds: 60
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: payment-commands
        namespace: orders-sb-eu
        # Target backlog PER POD. 5 pending messages per pod is a good starting
        # point for sub-second handlers. Raise it if pods are cheap and latency
        # is forgiving; lower it if each message is slow.
        messageCount: "5"
        activationMessageCount: "1"
      authenticationRef:
        name: sb-auth
```

> **Sessions change the maths.** With `requiresSession: true`, concurrency is bounded by the number of *distinct sessions*, not the number of messages. Scaling to 60 pods when only 8 order sessions are active leaves 52 pods idle. Scale on `activeMessageCount` but cap `maxReplicaCount` near your realistic concurrent-session count.

---

## 4. Network isolation

Premium tier supports Private Link [a private IP for the service inside your virtual network, so traffic never crosses the public internet].

```yaml
apiVersion: network.azure.com/v1api20220701
kind: PrivateEndpoint
metadata:
  name: sb-private-endpoint
  namespace: messaging
spec:
  location: westeurope
  owner:
    name: rg-orders-prod
  subnet:
    reference:
      armId: /subscriptions/.../subnets/snet-privatelink
  privateLinkServiceConnections:
    - name: sb-connection
      privateLinkServiceReference:
        armId: /subscriptions/.../namespaces/orders-sb-eu
      groupIds: [namespace]
```

Then set `publicNetworkAccess: Disabled` on the namespace. Do this **after** the private endpoint is confirmed working, or you lock yourself out of your own namespace — including the portal.

Standard tier has no Private Link. It has IP firewall rules, which are weaker and awkward from AKS with dynamic egress IPs. If network isolation is a requirement, Premium is not optional.

---

## 5. Multi-region

Geo-DR pairing replicates **metadata only** — the shape of your queues and topics, not the messages in them.

```yaml
apiVersion: servicebus.azure.com/v1api20211101
kind: NamespacesDisasterRecoveryConfig
metadata:
  name: orders-failover-alias
  namespace: messaging
spec:
  owner:
    name: orders-sb-eu
  partnerNamespace: /subscriptions/.../namespaces/orders-sb-us
  alternateName: orders-sb-alias
```

Apps connect to the **alias** hostname, not the primary. Failover repoints the alias; clients reconnect and find the secondary. What you must accept:

| | Reality |
|---|---|
| Messages in flight at failover | **Lost.** Metadata replicates; message bodies do not. |
| Failover trigger | Manual, or your own automation. There is no automatic failover. |
| Typical RTO | Minutes — the alias repoint is fast, client reconnect is not instant. |
| RPO | Equal to your in-flight queue depth. Keep queues shallow and this is small. |
| After failover | The pairing is **broken**. Re-establish it manually before you can fail back. |

For active-active — which is what a real multi-region system wants — do not use Geo-DR. Deploy an independent namespace per region, route users to the nearest one, and keep state in a globally replicated store. That is the shape in [`../diagrams/case-study-azure.mmd`](../diagrams/case-study-azure.mmd).

---

## 6. Cost control, which is a deployment concern here

Service Bus charges by tier, not by cluster size. The failure mode is different from a self-hosted broker: you cannot accidentally run out of disk, but you *can* accidentally spend a lot.

| Tier | Model | Watch out for |
|---|---|---|
| Basic | Per million operations | Queues only. No topics, no sessions, no DLQ ergonomics. Do not build on it. |
| Standard | Base fee + per million operations | **Every operation counts** — including a peek that returns nothing. An idle receiver polling in a tight loop generates real money. |
| Premium | Flat per messaging unit per hour | Predictable. Operations are free. The floor is the cost even at zero traffic. |

The Standard-tier trap worth naming: a receiver with a short `TryTimeout` in a `while(true)` loop bills millions of empty-receive operations per day. Use long polling (30-second `TryTimeout`, which is the SDK default) or the `ServiceBusProcessor`, which manages this for you.

Rough crossover: above ~10 million operations/month, Premium's flat fee usually beats Standard's metered fee — and it is the only tier with predictable latency, VNet isolation and 100 MB messages. Check current prices before committing; the numbers move.

---

## What this file does not cover

- **Local development.** The Service Bus emulator container handles queues, topics and subscriptions but not sessions, transactions or Geo-DR. See [`../code/csharp/README.md`](../code/csharp/README.md#local-brokers).
- **Event Hubs.** When the requirement is a 100k/sec firehose with replay, Service Bus is the wrong Azure product — Event Hubs is Kafka-compatible and priced for that shape. The case study uses both, deliberately: [`../docs/case-study-ecommerce.md`](../docs/case-study-ecommerce.md).
- **Operations.** Incident response lives in [`../runbooks/azure-runbook.md`](../runbooks/azure-runbook.md).
