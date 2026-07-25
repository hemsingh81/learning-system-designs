# 5 — Observability and Operations

← [Reliability](04-reliability.md) · [Interview index](README.md) · Next: [System design scenarios →](06-system-design-scenarios.md)

12 questions. Short section, but a reliable place to sound experienced — most candidates can define tracing and very few can say what breaks.

---

<details id="q1">
<summary><b>Q1 · A user reports a failed order. Walk me through finding out why.</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

Ask them for the reference on the error page — that is the **correlation ID**. One query on it returns the whole story across every service, in order.

Without that ID, you are searching five log streams by timestamp and guessing which of the 400 orders that second was theirs.

**If they dig deeper**

What the answer looks like when it is set up properly:

```
CorrelationId = "0192f3a1…"

10:00:00.012  ordering       INFO   Order placed              orderId=o-123
10:00:00.180  payments       INFO   Consuming OrderPlaced     orderId=o-123
10:00:00.851  payments       ERROR  Charge failed: timeout    psp=acme
10:00:01.410  inventory      WARN   Reservation released      orderId=o-123
```

Then open the trace to see *where the time went* — logs tell you what happened, traces tell you which hop was slow.

**Follow-up to expect:** *"What if the correlation ID doesn't cross the broker?"* → Then the story stops at the publish, which is the single most common gap. HTTP propagates automatically; messages do not. You must inject the ID into message headers and extract it on the consuming side.

📖 [Chapter 10 — Layer 1: correlation IDs](../tutorial/10-observability.md#layer-1--correlation-ids)

</details>

---

<details id="q2">
<summary><b>Q2 · What is the difference between logs, metrics, and traces?</b> &nbsp;·&nbsp; <code>Junior</code></summary>

**The 30-second answer**

- **Logs** — what happened, for one request. Detailed, expensive to store, searched after the fact.
- **Metrics** — how much, aggregated across all requests. Cheap, always on, what you alert from.
- **Traces** — where the time went, across services, for one request.

**If they dig deeper**

They answer different questions and you need all three:

| Question | Tool |
|---|---|
| "Is the system healthy?" | Metrics |
| "Why was this request slow?" | Traces |
| "What exactly happened to order o-123?" | Logs |
| "How many orders failed in the last hour?" | Metrics |
| "Which service caused the 2-second delay?" | Traces |

The one that ties them together: log lines should carry `TraceId` and `SpanId`, so you can jump from a log line to the trace and back.

**Follow-up to expect:** *"Which would you add first to an unmonitored system?"* → Metrics for RED (rate, errors, duration), because they tell you *that* something is wrong. Then traces, to tell you *where*. Logs are usually already there in some form.

📖 [Chapter 10 — Why this chapter is not optional](../tutorial/10-observability.md#why-this-chapter-is-not-optional)

</details>

---

<details id="q3">
<summary><b>Q3 · How does a trace survive crossing a message broker?</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐ <i>the one most people miss</i></summary>

**The 30-second answer**

You inject the trace context into the message headers when publishing, and extract it when consuming — then start a **child** span, not a new trace.

HTTP does this automatically via the `traceparent` header. Messaging does not. If you skip the extract step, **every consumer starts a brand-new trace** and your graph breaks exactly where async begins, which is where you needed it most.

**If they dig deeper**

```csharp
// Consuming — the line that joins the two halves
using var activity = ActivitySource.StartActivity(
    "OrderPlaced consume",
    ActivityKind.Consumer,
    parentContext.ActivityContext);   // ← without this, a new trace starts here
```

And the outbox complicates it: the publish happens later, in a different process. That is why the outbox row stores the correlation ID — the context has to survive the gap.

**Follow-up to expect:** *"How do you test it?"* → Place an order and confirm Jaeger shows **one** trace spanning gateway → service → broker → consumer. Three separate traces means you have this bug. It is a 30-second check that most teams never do.

📖 [Chapter 10 — Context propagation across the broker](../tutorial/10-observability.md#context-propagation-across-the-broker)

</details>

---

<details id="q4">
<summary><b>Q4 · What metrics would you put on a dashboard for a microservice?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

**RED**, for every service: **R**ate (requests/sec), **E**rrors (failures/sec), **D**uration (p50/p95/p99).

Plus, for a distributed system specifically:

| Metric | Why |
|---|---|
| Queue depth / consumer lag | Are you falling behind? |
| Oldest unprocessed message age | How stale is your data, in seconds? |
| DLQ depth | Alert above 0 |
| Outbox pending count | If this grows, events are not going out |
| Circuit breaker state | Which dependencies are considered dead |
| Saga instances by state | Sagas stuck for an hour are real customer problems |

**If they dig deeper**

The last one is underrated. A count of sagas by state over time tells you more about system health than CPU ever will.

And **alert on a sudden drop in rate**, not just a spike in errors. Traffic going to zero is often the first sign of an upstream outage, and an errors-only alert will not fire.

**Follow-up to expect:** *"What would you alert on versus just graph?"* → Alert on what needs a human now: error rate above SLO, DLQ above 0, consumer lag growing steadily, outbox pending growing. Graph the rest. An alert nobody acts on trains people to ignore alerts.

📖 [Chapter 10 — The metrics that actually matter](../tutorial/10-observability.md#the-metrics-that-actually-matter)

</details>

---

<details id="q5">
<summary><b>Q5 · What is metric cardinality and why should you care?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Cardinality is how many distinct values a label can have. Each combination creates a separate time series.

A label containing a user ID means one series per user. A million users means a million series, and a metrics bill that gets someone's attention.

**If they dig deeper**

```csharp
// ✅ "channel" has 3 values. Fine.
_placed.Add(1, new KeyValuePair<string, object?>("channel", channel));

// ❌ one series per customer. Millions of series.
_placed.Add(1, new KeyValuePair<string, object?>("customerId", id));
```

Keep metric labels to things with tens of values: service, endpoint, status code, region, channel.

**High-cardinality data belongs in traces and logs, not metrics.** A trace can carry `order.id` as a tag with no aggregation cost, because it is one record rather than a time series.

**Follow-up to expect:** *"So how do you find one customer's problem?"* → Traces and logs, joined by the correlation ID. That is the division of labour: metrics for aggregate health, traces and logs for individual cases.

📖 [Chapter 10 — Layer 4: metrics](../tutorial/10-observability.md#layer-4--metrics)

</details>

---

<details id="q6">
<summary><b>Q6 · Structured logging — what and why?</b> &nbsp;·&nbsp; <code>Junior</code></summary>

**The 30-second answer**

Log fields, not sentences.

```csharp
// ❌ ungreppable, unfilterable, unaggregatable
log.LogError($"Failed to charge order {orderId} for {customerId}: {ex.Message}");

// ✅ now you can filter by orderId, group by error type, alert on a count
log.LogError(ex, "Charge failed for {OrderId} of {CustomerId} via {Provider}",
    orderId, customerId, "acme-psp");
```

**If they dig deeper**

The second form produces a searchable record with `OrderId`, `CustomerId`, `Provider`, plus `CorrelationId`, `TraceId`, and `SpanId` — which is what lets you jump from a log line straight to the trace.

Also worth stating unprompted: **never log card numbers, passwords, tokens, or personal data.** Redact at the logging layer with a destructuring policy, so nobody has to remember at each call site.

**Follow-up to expect:** *"What log level for what?"* → Information for business events that matter; Warning for recovered-but-notable ("falling back to cache"); Error for a failed request; Critical for "the service cannot work". Debug off in production.

📖 [Chapter 10 — Layer 3: structured logging](../tutorial/10-observability.md#layer-3--structured-logging)

</details>

---

<details id="q7">
<summary><b>Q7 · Your tracing bill is too high. What do you do?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Sample — but not randomly. Use **tail sampling**: decide *after* the trace finishes, keep every error, every slow trace, and about 1% of the rest.

The traces you need are exactly the rare ones, so head-based random sampling throws away the interesting data.

**If they dig deeper**

Before sampling, check the cheap wins:

- **Filter out health checks.** Probes every 10 seconds across 30 pods generate more spans than your real traffic, and none of them are useful.
- **Do not trace every database call** in a tight loop — instrument the operation, not each row.

Configure tail sampling in the OTel Collector, not the app. That way the policy changes without a redeploy of twenty services.

**Follow-up to expect:** *"What do you lose with sampling?"* → The ability to find a specific successful request's trace. That is usually acceptable, because you keep all the failures. If a particular flow matters (payments, say), sample it at 100% and everything else at 1%.

📖 [Chapter 10 — Sampling](../tutorial/10-observability.md#sampling)

</details>

---

<details id="q8">
<summary><b>Q8 · Why OpenTelemetry rather than a vendor SDK?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

Because it is vendor-neutral. Instrument once with OTel, and changing backend — Jaeger to Datadog, Datadog to Honeycomb — is a **collector config change**, not a code change across twenty services.

**If they dig deeper**

The migration you avoid is real: replacing a vendor SDK means touching every service, redeploying all of them, and running both in parallel during the switch. With OTel the app keeps exporting OTLP and the collector routes it wherever you like.

It has also effectively won — every major vendor now ingests OTLP natively, so this is no longer a bet.

**Follow-up to expect:** *"What does OTel not give you?"* → Storage, querying, dashboards, and alerting. It is the instrumentation and transport layer. You still choose a backend, and that is where the real cost and the real feature differences are.

📖 [Chapter 10 — A practical starting stack](../tutorial/10-observability.md#a-practical-starting-stack)

</details>

---

<details id="q9">
<summary><b>Q9 · How do you debug something that only happens in production?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Start from the trace, not the logs. Find one failing request, look at where the time went and which span errored, then read that span's logs via the trace ID.

If you cannot do that, fix the observability first — you will otherwise spend the whole incident guessing.

**If they dig deeper**

The order I would work in:

1. **Metrics** — when did it start, what is the blast radius, is it one endpoint or all?
2. **Traces** — one failing example, and which hop is at fault.
3. **Logs for that span** — the exception and the parameters.
4. **Compare with a successful trace** — what is different?

The comparison in step 4 is the most underused technique. A slow trace next to a fast one usually makes the cause obvious in seconds.

**Follow-up to expect:** *"What if it's intermittent — 1 in 10,000?"* → Tail sampling that keeps all errors means you have those traces. Then look for what the failures share: one pod, one partition, one customer, one code path. Intermittent bugs are usually not random — they are correlated with something you have not looked at yet.

📖 [Chapter 10 — Layer 2: distributed tracing](../tutorial/10-observability.md#layer-2--distributed-tracing)

</details>

---

<details id="q10">
<summary><b>Q10 · What is clock skew and when does it bite?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Two servers' clocks disagree. Server A is 3 seconds ahead of B, so your logs show the effect before the cause and you waste an hour on an impossible timeline.

Run NTP everywhere, and prefer **trace span durations** over comparing raw timestamps across machines.

**If they dig deeper**

Where it genuinely matters beyond debugging:

- **Ordering by timestamp** across services — do not. Use sequence numbers or a partition key.
- **Token expiry** — this is why JWT validation usually allows a small clock-skew tolerance.
- **"Latest wins" logic** — the logistics case study compares the *device's* clock, and stores both device and server time precisely because the gap matters in a dispute.

**Follow-up to expect:** *"How do you order events reliably then?"* → A monotonic sequence per entity from a single writer (the exchange's sequence number, a database identity, or a Kafka offset). Wall-clock time across machines is not an ordering mechanism.

📖 [Chapter 10 — Sharp edges](../tutorial/10-observability.md#sharp-edges)

</details>

---

<details id="q11">
<summary><b>Q11 · What would you check first when paged at 3 a.m.?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

One dashboard answering "is the system healthy?" in under five seconds: request rate, error rate, p99 latency, queue depth, DLQ depth, outbox pending.

Then: **what changed?** Most incidents follow a deploy, a config change, or a traffic change. Checking recent deploys is often faster than any amount of log reading.

**If they dig deeper**

The sequence I would follow:

1. **Is it us or a dependency?** Error rate on our endpoints versus latency on our outbound calls.
2. **What changed in the last hour?** Deploys, feature flags, config, traffic.
3. **Blast radius** — one endpoint, one region, one customer, or everything?
4. **Mitigate before diagnosing.** Roll back, flip the flag, open the kill switch. Understanding can wait; the outage cannot.

Point 4 is the one people get wrong under pressure — they try to understand the bug while it is still burning.

**Follow-up to expect:** *"What if the dashboard shows everything is fine but users are complaining?"* → Then you are measuring the wrong thing. Usually you are watching server-side success while the failure is at the edge — the CDN, DNS, the mobile client, or a partial page failure your BFF is swallowing as a "successful" degraded response.

📖 [Chapter 10 — The metrics that actually matter](../tutorial/10-observability.md#the-metrics-that-actually-matter)

</details>

---

<details id="q12">
<summary><b>Q12 · Should observability run in local development?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**The 30-second answer**

Yes, and skipping it is why observability rots.

If a developer has never seen a trace of their own code, they will not notice when their new consumer breaks propagation, and they will not maintain instrumentation they have never used.

**If they dig deeper**

The cost is one container:

```yaml
jaeger:
  image: jaegertracing/all-in-one:latest
  environment: { COLLECTOR_OTLP_ENABLED: "true" }
  ports: ["16686:16686", "4317:4317"]
```

Set `OTEL_EXPORTER_OTLP_ENDPOINT` and you have distributed tracing locally in about five minutes. Every case study's `docker-compose.yml` in this repo includes it for exactly this reason.

**Follow-up to expect:** *"What else belongs in local dev?"* → The broker and the real database engine. Substituting an in-memory bus or SQLite hides precisely the problems this material is about — ordering, duplicates, transaction isolation. Local should be small, not different.

📖 [Chapter 10 — Sharp edges](../tutorial/10-observability.md#sharp-edges)

</details>

---

← [Reliability](04-reliability.md) · [Interview index](README.md) · Next: [System design scenarios →](06-system-design-scenarios.md)
