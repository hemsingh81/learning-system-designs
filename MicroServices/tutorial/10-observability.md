# Chapter 10 — Making the Invisible Visible

← [Chapter 9](09-resilience.md) · [Tutorial index](README.md) · Next: [Chapter 11 — The decision framework](11-decision-framework.md)

---

## The story so far

The system survives Acme Pay being slow ([chapter 9](09-resilience.md)). Chapter 2's incident is closed.

Then Priya opens a support ticket:

> *"I ordered a mouse on Tuesday. The money left my account but the app says the order was cancelled. What happened?"*

That is a fair question about her ₹49.98. You want to answer it. Here is everything you have:

```
14:32:01  ordering       Order placed
14:32:03  payments       Charge failed
14:32:04  inventory      Reservation released
```

Three services, three log lines, and **nothing connecting them.** There were 1,400 orders that afternoon. You cannot tell whether any of those lines are hers.

This chapter is the price of everything you built in chapters 3 through 9.

---

## In one line

In a distributed system, you cannot debug what you cannot trace.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Correlation ID** | One ID attached to everything caused by a single user action. |
| **Trace** | The full story of one request across every service. |
| **Span** | One unit of work inside a trace — an HTTP call, a DB query, a message handler. |
| **Trace ID / Span ID** | The identifiers. A trace has many spans; each span knows its parent. |
| **Context propagation** | Passing the trace ID from one service to the next, so the story stays joined up. |
| **W3C Trace Context** | The standard header format (`traceparent`) that everyone now agrees on. |
| **Structured logging** | Logging fields, not sentences: `{ orderId: "o-123" }` instead of `"order o-123 failed"`. |
| **OpenTelemetry (OTel)** | The vendor-neutral standard and SDK for traces, metrics, and logs. |
| **Cardinality** | How many distinct values a label can have. High cardinality makes metrics expensive. |
| **The three pillars** | Logs (what happened), metrics (how much), traces (where the time went). |

---

## Why this chapter is not optional

In the old monolith, Priya's ticket took two minutes. One stack trace, one file, one line number.

Now the same question needs an archaeology dig across four log streams — and the honest answer today is *"we do not know"*.

**This is the tax on async.** Chapters 3 through 9 bought speed, resilience, and independence. This chapter pays for them. Skip it and every incident becomes guesswork.

---

## Layer 1 — Correlation IDs

The cheapest thing with the highest payoff. One ID, generated at the edge, carried everywhere.

### Generate it at the gateway

```csharp
// Gateway/Middleware/CorrelationIdMiddleware.cs
public sealed class CorrelationIdMiddleware(RequestDelegate next)
{
    public const string HeaderName = "X-Correlation-Id";

    public async Task InvokeAsync(HttpContext ctx)
    {
        // Reuse the caller's ID if they sent one (mobile apps should), otherwise create one.
        var correlationId = ctx.Request.Headers[HeaderName].FirstOrDefault()
                            ?? Guid.CreateVersion7().ToString("N");

        ctx.Request.Headers[HeaderName]  = correlationId;
        ctx.Response.Headers[HeaderName] = correlationId;   // so Priya can quote it to support
        ctx.Items[HeaderName]            = correlationId;

        // Every log line in this request now carries it, automatically.
        using (LogContext.PushProperty("CorrelationId", correlationId))
            await next(ctx);
    }
}
```

### Forward it on every outgoing call

```csharp
// Infrastructure/Http/CorrelationIdHandler.cs
public sealed class CorrelationIdHandler(IHttpContextAccessor accessor) : DelegatingHandler
{
    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken ct)
    {
        var id = accessor.HttpContext?.Items[CorrelationIdMiddleware.HeaderName] as string;

        if (id is not null && !request.Headers.Contains(CorrelationIdMiddleware.HeaderName))
            request.Headers.Add(CorrelationIdMiddleware.HeaderName, id);

        return base.SendAsync(request, ct);
    }
}

// Registered once, applied to every typed client:
builder.Services.AddHttpClient<InventoryClient>()
       .AddHttpMessageHandler<CorrelationIdHandler>();
```

### Carry it across the broker — the part most teams miss

HTTP headers do not travel through a message queue. **You must put the ID in the message metadata yourself.**

```csharp
// Publishing
await bus.Publish(evt, c => c.Headers.Set("X-Correlation-Id", correlationId));

// Consuming: pull it back out and push it into the log context
public async Task Consume(ConsumeContext<OrderPlaced> ctx)
{
    var correlationId = ctx.Headers.Get<string>("X-Correlation-Id") ?? "unknown";

    using (LogContext.PushProperty("CorrelationId", correlationId))
    {
        // Everything logged in here — and in anything this calls — carries the ID.
        await HandleAsync(ctx.Message, ctx.CancellationToken);
    }
}
```

Remember the outbox stores the correlation ID on the row ([chapter 8](08-outbox-and-idempotency.md)), so the ID survives even when publishing happens seconds later, in a different process.

### The payoff — Priya's ticket, answered

She reads the reference from her order confirmation email. One query:

```
CorrelationId = "0192f3a10000700080000000000001"
```

```
14:32:01.012  ordering       INFO   Order placed              orderId=o-123 total=49.98
14:32:01.045  ordering       INFO   Outbox row written        messageId=m-1
14:32:01.180  payments       INFO   Consuming OrderPlaced     orderId=o-123
14:32:01.190  payments       INFO   Charging Acme Pay         idempotencyKey=order-charge-o-123
14:32:03.851  payments       ERROR  Charge failed: timeout    psp=acme attempt=1
14:32:04.100  payments       INFO   Retry 2 of 3
14:32:06.400  payments       ERROR  Charge failed: declined   code=insufficient_funds
14:32:06.500  inventory      WARN   Reservation released      orderId=o-123
14:32:06.600  notifications  INFO   Sent "payment failed" email
```

**Now you can answer her.** The card was declined for insufficient funds on the second attempt. The money she saw leave was an authorisation hold from the first attempt, which her bank will release in a few days.

That is a real answer, produced in thirty seconds, from one ID.

---

## Layer 2 — Distributed tracing

Correlation IDs tell you **what happened**. Traces tell you **where the time went**.

### The model

```
Trace: 4bf92f3577b34da6                          total 214 ms
├── span: POST /orders            gateway         214 ms
│   ├── span: handle request      ordering         38 ms
│   │   └── span: db write+outbox ordering         22 ms
│   ├── span: publish OrderPlaced ordering          4 ms
│   └── span: OrderPlaced         broker           18 ms
│       ├── span: consume         payments         96 ms
│       │   └── span: POST /charge acme            78 ms  ← there it is
│       └── span: consume         notifications    24 ms
```

One look and you know: **78 of 214 ms are Acme Pay.** No log reading required.

### Setting it up

```csharp
// Program.cs — the same block in every service
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r
        .AddService(serviceName: builder.Environment.ApplicationName,
                    serviceVersion: typeof(Program).Assembly.GetName().Version?.ToString())
        .AddAttributes([new("deployment.environment", builder.Environment.EnvironmentName)]))

    .WithTracing(t => t
        .AddAspNetCoreInstrumentation(o =>
        {
            o.RecordException = true;
            // Do not trace health checks — 90% of your span volume, 0% of the value.
            o.Filter = ctx => !ctx.Request.Path.StartsWithSegments("/health");
        })
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation(o => o.SetDbStatementForText = true)
        .AddSource("MassTransit")                     // broker publish/consume spans
        .AddOtlpExporter())

    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddMeter("Store.Ordering")                   // your own metrics
        .AddOtlpExporter());
```

That is most of the work. The instrumentation libraries create spans for HTTP in, HTTP out, and database calls automatically.

### Context propagation across the broker

Over HTTP, OTel propagates automatically via `traceparent`. Over a broker it must be injected and extracted:

```csharp
// Publishing — inject the current trace context into message headers
Propagators.DefaultTextMapPropagator.Inject(
    new PropagationContext(Activity.Current!.Context, Baggage.Current),
    messageHeaders,
    (headers, key, value) => headers[key] = value);
```

```csharp
// Consuming — extract it and start a CHILD span, not a new trace
var parentContext = Propagators.DefaultTextMapPropagator.Extract(default, messageHeaders,
    (headers, key) => headers.TryGetValue(key, out var v) ? [v] : []);

using var activity = ActivitySource.StartActivity(
    "OrderPlaced consume",
    ActivityKind.Consumer,
    parentContext.ActivityContext);      // ← this line is what joins the two halves
```

> **If you skip the extract step, every consumer starts a brand-new trace** and the graph breaks exactly where async begins — which is exactly where you needed it most. This is the single most common observability bug in message-driven systems.

### Add your own spans for business steps

```csharp
private static readonly ActivitySource Source = new("Store.Ordering");

public async Task<Order> PlaceAsync(PlaceOrderRequest req, CancellationToken ct)
{
    using var activity = Source.StartActivity("place order");

    activity?.SetTag("order.customer_id", req.CustomerId);
    activity?.SetTag("order.line_count",  req.Lines.Count);

    try
    {
        var order = await CreateAsync(req, ct);
        activity?.SetTag("order.id", order.Id);
        activity?.SetStatus(ActivityStatusCode.Ok);
        return order;
    }
    catch (Exception ex)
    {
        activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
        activity?.AddException(ex);
        throw;
    }
}
```

### Sampling

At scale you cannot store every trace. Do not sample randomly — sample intelligently:

| Strategy | Behaviour | Use when |
|---|---|---|
| Always on | Keep everything | Development, low volume |
| Fixed ratio | Keep 10% | High volume, simple |
| **Tail sampling** | Decide *after* the trace finishes: keep all errors, all slow traces, 1% of the rest | Production. Clearly the best |

**Tail sampling is what you want**, because the traces you need are exactly the rare ones. Configure it in the OTel Collector, not the app.

---

> **Diagram: D10 — One trace, five services**
> [Mermaid source](../diagrams/README.md#d10--one-trace-five-services)

---

## Layer 3 — Structured logging

```csharp
// ✗ A sentence. Ungreppable, unfilterable, unaggregatable.
log.LogError($"Failed to charge order {orderId} for customer {customerId}: {ex.Message}");

// ✓ Fields. You can now filter by orderId, group by error type, alert on a count.
log.LogError(ex, "Charge failed for {OrderId} of {CustomerId} via {Provider}",
    orderId, customerId, "acme-pay");
```

The second form produces a searchable record:

```json
{
  "timestamp": "2026-07-25T14:32:06.851Z",
  "level": "Error",
  "message": "Charge failed for o-123 of c-77 via acme-pay",
  "OrderId": "o-123", "CustomerId": "c-77", "Provider": "acme-pay",
  "CorrelationId": "0192f3a1…", "TraceId": "4bf92f35…", "SpanId": "00f067aa…",
  "Service": "payments", "Exception": "System.TimeoutException: …"
}
```

Note `TraceId` and `SpanId` in the log line. **That is the bridge:** from a log entry you jump to the trace, and from a trace span you jump to its logs.

### What to log, and at which level

| Level | Use for | Store example |
|---|---|---|
| **Trace/Debug** | Development only. Off in production | Every variable |
| **Information** | Business events that matter | "Order placed", "Payment captured" |
| **Warning** | Recovered from, but someone should know | "Retry 2 of 3", "Falling back to cache" |
| **Error** | This request failed | "Charge failed after all retries" |
| **Critical** | The service cannot work | "Cannot reach the database" |

**Never log:** card numbers, passwords, tokens, full request bodies with personal data. Redact at the logging layer so nobody has to remember:

```csharp
.Destructure.ByTransforming<PaymentRequest>(p => new
{
    p.OrderId,
    p.Amount,
    Card = $"****{p.CardNumber[^4..]}"      // never the full number
})
```

---

## Layer 4 — Metrics

Traces show one request. Metrics show all of them.

```csharp
// Infrastructure/Telemetry/OrderingMetrics.cs
public sealed class OrderingMetrics
{
    private readonly Counter<long>     _placed;
    private readonly Counter<long>     _failed;
    private readonly Histogram<double> _duration;
    private readonly ObservableGauge<int> _outboxPending;

    public OrderingMetrics(IMeterFactory factory, IOutboxStats outbox)
    {
        var meter = factory.Create("Store.Ordering");

        _placed   = meter.CreateCounter<long>("orders.placed", unit: "{order}");
        _failed   = meter.CreateCounter<long>("orders.failed", unit: "{order}");
        _duration = meter.CreateHistogram<double>("orders.place.duration", unit: "ms");

        // A gauge is read on demand — perfect for queue-style depths.
        _outboxPending = meter.CreateObservableGauge("outbox.pending",
                            () => outbox.PendingCount(), unit: "{message}");
    }

    // Tags must be LOW cardinality. "channel" has 3 values: fine.
    // Adding customerId here would create millions of time series and a very large bill.
    public void Placed(string channel) => _placed.Add(1, new KeyValuePair<string, object?>("channel", channel));
    public void Failed(string reason)  => _failed.Add(1, new KeyValuePair<string, object?>("reason", reason));
}
```

### The metrics that actually matter

**RED, for every service:**

| Metric | Meaning | Alert on |
|---|---|---|
| **Rate** | Requests per second | A sudden drop — often the first sign of an upstream outage |
| **Errors** | Failed requests per second | Error rate above your SLO |
| **Duration** | p50, p95, p99 latency | p99 above your SLO |

**Plus, for a distributed system specifically:**

| Metric | Why it matters for the store |
|---|---|
| Queue depth / consumer lag | Are you falling behind? |
| Oldest unprocessed message age | How stale is your data, in seconds? |
| DLQ depth | Messages failing permanently. **Alert above 0** |
| **Outbox pending count** | If this grows, chapter 8's 47 orders are happening again |
| Circuit breaker state | Which dependencies are currently considered dead |
| Saga instances by state | Sagas stuck in `AwaitingPayment` over an hour = real customers |

**That outbox row is the one the store added after chapter 8.** A single gauge would have caught 47 stuck orders in the first ten minutes instead of three weeks.

**Watch cardinality.** A label with a customer ID creates one time series per customer. A million customers means a million series, and a metrics bill that gets someone's attention. Keep labels to things with tens of values.

---

## Health checks

Covered in [chapter 9](09-resilience.md#health-checks--liveness-vs-readiness) because they are part of resilience — but they are also your simplest observability signal. Liveness checks the process; readiness checks the dependencies. Confusing them causes restart storms.

---

## Sharp edges

**Edge 1 — Trace context lost at the broker.** The single most common mistake. HTTP propagates automatically; messages do not. **Test it:** place an order and confirm the trace spans gateway *through* the broker *into* the consumer. If the consumer starts its own trace, you have this bug.

**Edge 2 — Tracing everything, including health checks.** Health probes every 10 seconds across 30 pods generate more spans than your real traffic. Filter them out.

**Edge 3 — Logging in a tight consumer loop.** One log line per message at 50,000 messages/sec costs more than the processing. Log aggregates, and per-message only on error.

**Edge 4 — High-cardinality metric labels.** The fastest way to a surprise invoice.

**Edge 5 — No correlation ID on the response.** Give the ID back to the client, in a header and on error pages. Then Priya's ticket saying *"reference 0192f3a1"* is a one-second investigation instead of an hour of guessing.

**Edge 6 — Clock skew.** Server A's clock is 3 seconds ahead of B's. Now your logs show the effect before the cause. Run NTP everywhere, and prefer trace span durations over comparing raw timestamps across machines.

**Edge 7 — Observability that only exists in production.** If it is not in local development, developers do not use it, do not understand it, and do not maintain it. Run Jaeger in `docker-compose` so a trace view is one click away on day one.

---

## A practical starting stack

| Need | Free / self-hosted | Managed |
|---|---|---|
| Collect everything | OpenTelemetry Collector | Same, everywhere |
| Traces | Jaeger, Tempo | Honeycomb, Datadog, Application Insights |
| Metrics | Prometheus + Grafana | Datadog, Azure Monitor |
| Logs | Loki, OpenSearch | Datadog, Azure Monitor |
| Dashboards | Grafana | Vendor's own |

**Instrument with OpenTelemetry, always.** It is vendor-neutral, so changing backend is a collector config change, not a code change across 20 services. That single decision will save you a migration.

### Minimal docker-compose to get a trace view today

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    ports:
      - "16686:16686"    # UI → http://localhost:16686
      - "4317:4317"      # OTLP gRPC — point your services here
```

Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` and you have distributed tracing locally in about five minutes.

---

## Try it yourself

**Build it.** Three services and a broker. Add OpenTelemetry to all three, exporting to Jaeger.

**Now break it:**

1. Place an order. Open Jaeger. Confirm you see **one** trace spanning all three services and the broker. If you see three separate traces, fix propagation — **everything else depends on this**.
2. Remove the broker header injection. Look again. Watch the trace end at the publish. *That gap is what most teams have without knowing it.*
3. Make Acme Pay sleep 3 s. Find it in the trace **without reading any logs**. Time yourself. Then try from logs alone and time that too.
4. Log a message without a correlation ID. Try to link it to a request. You cannot.
5. Add a metric label containing the customer ID. Watch your series count explode. Remove it.
6. Create a dashboard with: request rate, error rate, p99 latency, queue depth, DLQ depth, **outbox pending**. That dashboard should answer "is the system healthy?" in under five seconds.
7. Stop one consumer for 10 minutes. Watch queue depth and oldest-message-age climb. **Set your alert threshold from what you observe**, not from a guess.

---

## What is still broken

Nothing, for the first time in ten chapters.

Priya's ticket is answered in thirty seconds. Incidents have traces. The dashboard tells you the system is healthy before anyone asks.

Then the product team walks over with a new feature: **loyalty points.** Customers earn 1 point per ₹100 spent, redeemable at checkout.

Someone asks the question that used to start a week-long argument:

> *"Should Ordering call the Loyalty service, or publish an event? And do we need Kafka for this?"*

But this time you do not argue. You have walked this system from a 4-second checkout that collapsed under load to one that survives a hundredfold spike — and every decision along the way came down to the same handful of questions.

The last chapter writes those questions down.

---

← [Chapter 9](09-resilience.md) · [Tutorial index](README.md) · Next: [Chapter 11 — The decision framework](11-decision-framework.md)
