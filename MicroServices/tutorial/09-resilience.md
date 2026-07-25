# Chapter 9 — Resilience

← [Chapter 8](08-outbox-and-idempotency.md) · [Tutorial index](README.md) · Next: [Chapter 10 — Observability](10-observability.md)

---

## In one line

Five layers, in a fixed order, and each one only works because the one outside it exists.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Timeout** | Give up waiting after N seconds. |
| **Retry** | Try again after a failure. |
| **Backoff** | Wait longer before each retry. |
| **Jitter** | Add a small random amount to the wait, so retries do not all fire together. |
| **Circuit breaker** | After too many failures, stop calling at all for a while. |
| **Bulkhead** | Limit how many calls to one dependency can be in flight, so it cannot use all your resources. |
| **Fallback** | A degraded but useful answer when the real one is unavailable. |
| **Backpressure** | Telling the caller to slow down, instead of accepting work you cannot do. |
| **Load shedding** | Deliberately rejecting some requests to keep the rest healthy. |
| **Thundering herd** | Many clients retrying at the same instant, creating a spike that repeats the failure. |
| **Cascading failure** | One slow service making its callers slow, and so on up the chain. |

---

## The order matters

```
Request ─► ① Timeout ─► ② Retry ─► ③ Circuit breaker ─► ④ Bulkhead ─► ⑤ Fallback ─► Service
```

Read it as: bound the wait, then try again sensibly, then stop trying when it is clearly dead, then contain the damage, then degrade gracefully.

**Why the order is not arbitrary:**

- **Retry without timeout** = you retry after 100 seconds. Useless.
- **Retry without a circuit breaker** = you attack a struggling service and finish it off.
- **Circuit breaker without a bulkhead** = one slow dependency still consumes all your threads before the breaker notices.
- **Bulkhead without a fallback** = you correctly reject the call, and then return a 500 anyway.

> **Diagram: D9 — Resilience layers**
> [Mermaid source](../diagrams/README.md#d9--resilience-layers)

---

## Layer 1 — Timeout

**The rule: every call over a network has a timeout. No exceptions.**

Defaults are dangerous. `HttpClient`'s default is 100 seconds. No user waits 100 seconds; they refresh, and now you have two hung requests instead of one.

```csharp
builder.Services.AddHttpClient<InventoryClient>(c =>
{
    c.BaseAddress = new Uri(config["Services:Inventory"]!);
    c.Timeout     = TimeSpan.FromSeconds(2);
});
```

### How to choose the number

Not by guessing. Measure, then decide:

1. Look at the dependency's **p99 latency** (the slowest 1% of successful calls).
2. Set the timeout to roughly **2–3× p99**.
3. Sanity check it against your own SLA. If you must answer in 500 ms, a 2-second timeout on a dependency is already a lie.

| Dependency p99 | Timeout |
|---|---|
| 50 ms | 150 ms |
| 200 ms | 500 ms |
| 1 s | 3 s |

**Timeouts must shrink as you go deeper.** If the gateway allows 5 s, the service must allow less, and its dependency less again. Otherwise the outer layer gives up while inner work continues — burning resources on a result nobody will read.

```
Gateway 5s  →  BFF 4s  →  Ordering 3s  →  Inventory 1s
```

Pass the remaining budget down explicitly where you can:

```csharp
// Use the caller's cancellation token so a client disconnect stops all downstream work.
public async Task<Order> GetAsync(string id, CancellationToken ct)
{
    using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
    cts.CancelAfter(TimeSpan.FromSeconds(1));          // my own budget, on top of theirs

    return await inventory.GetStockAsync(id, cts.Token);
}
```

---

## Layer 2 — Retry, with backoff and jitter

Retry helps with **transient** failures: a dropped packet, a pod restarting, a brief lock. It does not help with a bug, a 400, or an overloaded service.

### What to retry, and what not to

| Situation | Retry? |
|---|---|
| Network timeout, connection refused | ✓ Yes |
| HTTP 503, 502, 504 | ✓ Yes |
| HTTP 429 (too many requests) | ✓ Yes, but honour `Retry-After` |
| HTTP 500 | ⚠️ Maybe once. It is often a bug that will fail again. |
| HTTP 400, 401, 403, 404, 422 | ✗ Never. The answer will not change. |
| A non-idempotent write with no idempotency key | ✗ Never — you may do it twice |

### Why jitter is not optional

Without jitter, 1,000 clients that failed at the same moment retry at the same moment:

```
t=0.0s   1000 requests fail (service restarts)
t=1.0s   1000 retries arrive together  ← spike, service falls over again
t=3.0s   1000 retries arrive together  ← again
t=7.0s   1000 retries arrive together  ← the service never gets a quiet moment to recover
```

With jitter, the same 1,000 retries spread across the window, and the service recovers.

```csharp
// Program.cs — Polly v8 resilience pipeline on a typed client
builder.Services.AddHttpClient<InventoryClient>(c =>
{
    c.BaseAddress = new Uri(config["Services:Inventory"]!);
    c.Timeout     = TimeSpan.FromSeconds(2);          // layer 1
})
.AddResilienceHandler("inventory", (pipeline, _) =>
{
    pipeline.AddRetry(new HttpRetryStrategyOptions          // layer 2
    {
        MaxRetryAttempts = 3,
        BackoffType      = DelayBackoffType.Exponential,
        UseJitter        = true,                      // ← the important line
        Delay            = TimeSpan.FromMilliseconds(200),
        ShouldHandle     = new PredicateBuilder<HttpResponseMessage>()
            .Handle<HttpRequestException>()
            .Handle<TimeoutRejectedException>()
            .HandleResult(r => r.StatusCode is HttpStatusCode.ServiceUnavailable
                                            or HttpStatusCode.BadGateway
                                            or HttpStatusCode.GatewayTimeout
                                            or HttpStatusCode.TooManyRequests)
    });

    pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions   // layer 3
    {
        FailureRatio     = 0.5,                       // 50% of calls failing…
        MinimumThroughput = 20,                       // …out of at least 20 samples
        SamplingDuration = TimeSpan.FromSeconds(30),
        BreakDuration    = TimeSpan.FromSeconds(15)
    });

    pipeline.AddTimeout(TimeSpan.FromSeconds(1));     // per-attempt timeout
});
```

Note there are **two** timeouts: 1 second per attempt, and 2 seconds total on the client. Worst case is bounded — this is what stops "3 retries × 2 s = 6 s" surprises.

### Retries multiply load — do the arithmetic

3 retries means 4× traffic when things go wrong. If your service is failing because it is overloaded, you have just made it 4× more overloaded.

**Retry budgets** fix this: allow retries only up to a fraction of total traffic (say 10%). Service meshes (Envoy, Linkerd) support this directly. Without a mesh, the circuit breaker is your protection — which is why layer 3 exists.

---

## Layer 3 — Circuit breaker

A breaker has three states:

```
        failures exceed threshold
CLOSED ─────────────────────────► OPEN
  ▲                                 │  after break duration
  │                                 ▼
  └────── test call succeeds ──── HALF-OPEN
                 ▲                  │
                 └── test fails ────┘
```

| State | Behaviour |
|---|---|
| **Closed** | Normal. Calls go through. Failures are counted. |
| **Open** | All calls fail **immediately**, without touching the network. |
| **Half-open** | After the break, let one call through. Success → closed. Failure → open again. |

### Why it matters

Without a breaker, when `Payments` is dead:

```
Every request waits 2s for the timeout, then fails.
1000 requests/sec × 2s = 2000 threads and connections held.
Ordering falls over — including for requests that never needed Payments.
```

With a breaker:

```
First 20 requests fail slowly (2s). Breaker opens.
Every request after that fails in <1ms.
Ordering stays healthy and can still serve everything else.
Payments gets zero traffic and a chance to recover.
```

**The breaker protects you twice:** it stops you wasting your own resources, and it stops you hammering a service that is trying to come back.

### Tuning

| Setting | Typical | What happens if wrong |
|---|---|---|
| `FailureRatio` | 0.5 | Too low → opens on normal noise. Too high → never opens. |
| `MinimumThroughput` | 20 | Too low → 2 failures at 3 a.m. open the breaker unnecessarily. |
| `SamplingDuration` | 30 s | Too short → jumpy. Too long → slow to react. |
| `BreakDuration` | 15–30 s | Too short → keeps hammering. Too long → slow recovery after a blip. |

**One breaker per dependency, never one global breaker.** A shared breaker means a failure in the recommendations service stops your payment calls.

---

## Layer 4 — Bulkhead

Named after a ship's watertight compartments: a hole in one does not sink the vessel.

**The problem it solves:** even with a breaker, before it opens, a slow dependency can consume every thread and connection you have.

```
Payments is slow (4s). Ordering has 200 threads.
50 requests/sec × 4s = 200 threads all waiting on Payments.
Requests for GET /orders — which do not touch Payments — have no thread left.
Your entire service is down because ONE dependency is slow.
```

**The fix:** cap concurrent calls per dependency.

```csharp
pipeline.AddConcurrencyLimiter(new ConcurrencyLimiterOptions
{
    PermitLimit = 20,        // at most 20 concurrent calls to Payments…
    QueueLimit  = 10         // …plus 10 waiting. Number 31 fails instantly.
});
```

Now a slow `Payments` can occupy at most 30 of your resources. The other 170 keep serving everything else. You are degraded, not down.

Give each dependency its own limit, sized by its importance and its normal concurrency.

---

## Layer 5 — Fallback

When everything above has failed, answer the question: **what is the best thing I can still do?**

| Fallback | Example | Good for |
|---|---|---|
| **Cached value** | Last known price, marked "as of 10:42" | Data that changes slowly |
| **Default value** | Show generic products instead of personalised ones | Enhancement features |
| **Partial response** | Order page without the tracking number | Composite pages |
| **Queue it for later** | Accept the order, charge asynchronously | Writes that can be deferred |
| **Honest failure** | "Payments are temporarily unavailable, your basket is saved" | When you genuinely cannot proceed |

```csharp
// Bff.Web/Services/RecommendationService.cs
public async Task<IReadOnlyList<Product>> GetForUserAsync(Guid userId, CancellationToken ct)
{
    try
    {
        return await recommendations.GetAsync(userId, ct);
    }
    catch (Exception ex) when (ex is BrokenCircuitException
                                  or TimeoutRejectedException
                                  or HttpRequestException)
    {
        // Personalised recommendations are a nice-to-have. Never fail a page for them.
        log.LogWarning(ex, "Recommendations unavailable for {UserId}, using best sellers", userId);
        return await cache.GetBestSellersAsync(ct);
    }
}
```

**The most important fallback decision is which features are allowed to fail.** Write that list down before an incident, not during one:

| Feature | If its dependency is down |
|---|---|
| Checkout | **Must work.** Degrade to async payment. |
| Product page | **Must work.** Serve from cache. |
| Recommendations | Show best sellers. |
| Reviews | Hide the section. |
| Live inventory count | Show "In stock" without a number. |
| Loyalty points preview | Hide it. |

---

## Backpressure and load shedding

Everything above is about **you calling someone else**. This is about **someone calling you** faster than you can cope.

**The wrong response to overload is to accept the work anyway.** Your queues grow, latency climbs, memory fills, and you fail everything instead of most things.

**Refusing work is a feature.** A fast `429` is a good outcome: the caller can retry, back off, or degrade. A 30-second timeout gives them nothing and costs you a thread.

```csharp
// Reject early and cheaply when you are already at capacity.
builder.Services.AddRateLimiter(o =>
{
    o.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(ctx =>
        RateLimitPartition.GetConcurrencyLimiter("global", _ => new ConcurrencyLimiterOptions
        {
            PermitLimit = 500,
            QueueLimit  = 0            // do not queue. Queuing is just slow rejection.
        }));

    o.OnRejected = async (ctx, ct) =>
    {
        ctx.HttpContext.Response.Headers.RetryAfter = "2";   // tell them when to come back
        await ctx.HttpContext.Response.WriteAsync("Server busy, retry shortly", ct);
    };
});
```

**Shed by priority when you can.** Under load, reject analytics writes before checkout requests. A simple tier header or route-based policy is enough:

```csharp
// Checkout keeps 80% of capacity; everything else shares the rest.
o.AddPolicy("critical", _ => RateLimitPartition.GetConcurrencyLimiter("c",
    _ => new ConcurrencyLimiterOptions { PermitLimit = 400, QueueLimit = 50 }));

o.AddPolicy("standard", _ => RateLimitPartition.GetConcurrencyLimiter("s",
    _ => new ConcurrencyLimiterOptions { PermitLimit = 100, QueueLimit = 0 }));
```

**For async consumers, backpressure is built in.** A queue absorbs the spike; your consumers drain it at their own speed. Just watch queue depth so you know when "absorbing a spike" has become "falling behind permanently".

---

## Health checks — liveness vs readiness

Getting these two confused causes restart loops that turn a small problem into an outage.

| Check | Question | If it fails |
|---|---|---|
| **Liveness** | "Is this process broken beyond repair?" | The platform **kills and restarts** the pod |
| **Readiness** | "Should I receive traffic right now?" | The platform **stops sending traffic**, but does not restart |

```csharp
builder.Services.AddHealthChecks()
    // Liveness: only things a RESTART would fix. Keep this almost empty.
    .AddCheck("self", () => HealthCheckResult.Healthy(), tags: ["live"])

    // Readiness: everything you need to serve a request properly.
    .AddDbContextCheck<OrderingDbContext>("database",   tags: ["ready"])
    .AddCheck<BrokerHealthCheck>("broker",              tags: ["ready"]);

app.MapHealthChecks("/health/live",  new() { Predicate = h => h.Tags.Contains("live")  });
app.MapHealthChecks("/health/ready", new() { Predicate = h => h.Tags.Contains("ready") });
```

**The classic mistake:** putting the database check in the liveness probe.

```
Database has a 30-second blip.
Liveness fails on every pod.
Kubernetes restarts every pod, all at once.
All pods start cold, with empty caches, and all reconnect to the database at the same instant.
The database, already struggling, now falls over completely.
A 30-second blip has become a 20-minute outage — caused entirely by the health check.
```

**Rule: liveness checks only the process. Readiness checks the dependencies.**

Also consider a **degraded** state: if the recommendation service is down but you can still take orders, stay ready. Reserve "not ready" for "I genuinely cannot serve a correct response".

---

## Sharp edges

**Edge 1 — Resilience for a non-idempotent write is a double-write bug.** Retrying `POST /charge` may charge twice, because the first attempt might have succeeded before the timeout. Never retry a write without an idempotency key ([chapter 8](08-outbox-and-idempotency.md)).

**Edge 2 — Nested retries multiply.** Gateway retries 3× → BFF retries 3× → Service retries 3× = **27 requests** for one user click. Retry at **one** layer, as close to the failure as sensible. Everywhere else, fail fast.

**Edge 3 — A circuit breaker that never opens is decoration.** If `MinimumThroughput` is 100 and you get 5 requests a minute, the breaker will never trip. Test it: stop the dependency, and assert the breaker opens.

**Edge 4 — Fallbacks that hide real failures.** If you always serve stale cache when the price service is down, nobody notices it has been down for a week. Every fallback must emit a metric and, past a threshold, an alert. Degraded must be visible.

**Edge 5 — Timeouts that are longer than the client's patience.** A user gives up at ~3 seconds. A 30-second timeout means you spend 27 seconds computing a response nobody is waiting for. Cancel work when the client disconnects — pass `HttpContext.RequestAborted` all the way down.

**Edge 6 — Retrying a `429`.** If a service says "too many requests" and you retry immediately, you are ignoring the only useful thing it told you. Honour `Retry-After`.

**Edge 7 — Untested resilience is not resilience.** Nearly every one of these settings looks fine and is wrong until you test it. This is why chaos testing exists.

---

## What to do where

| Layer | Sync HTTP/gRPC | Async consumer |
|---|---|---|
| Timeout | ✓ Always | ✓ On calls the consumer makes |
| Retry | ✓ Transient failures only | ✓ Broker retry policy + DLQ |
| Circuit breaker | ✓ Per dependency | ✓ For external calls in the handler |
| Bulkhead | ✓ Per dependency | ✓ Cap consumer concurrency |
| Fallback | ✓ For non-critical data | ⚠️ Usually not — dead-letter instead |
| Backpressure | ✓ Rate limit + shed | ✓ The queue is the buffer; watch depth |

**A useful asymmetry:** synchronous calls need all five layers because the user is waiting. Asynchronous consumers need fewer, because the queue itself absorbs failure and time. This is another argument for async where you can use it.

---

## Try it yourself

**Build it.** `Ordering` calls `Inventory` through a Polly pipeline with all five layers.

**Now break it, and watch each layer do its job:**

1. **No timeout.** Make `Inventory` sleep 60 s. Send 100 concurrent requests. Watch `Ordering` stop responding to everything. Add the timeout. Repeat. Requests now fail in 2 s and the service stays alive.
2. **Retry without jitter.** Make `Inventory` fail for 10 s, and send 500 requests. Plot the arrival times at `Inventory`. You will see spikes. Turn jitter on, plot again, see it smooth out.
3. **No circuit breaker.** Stop `Inventory` completely. Note that every request still burns the full 2 s timeout. Add the breaker. Note requests now fail in under 1 ms after the breaker opens.
4. **No bulkhead.** Make `Inventory` slow (4 s), then call `GET /orders`, which does not use `Inventory` at all. Watch it fail anyway. Add the bulkhead. Watch it succeed while `Inventory` calls are being rejected.
5. **Fallback.** Stop the recommendation service. The page should still render, with best sellers. Confirm a metric was emitted — if not, edge 4 applies to you.
6. **Load shedding.** Send 10× your capacity. You should see fast `429`s, and your p99 for accepted requests should stay flat. If instead everything gets slow, you are queuing when you should be shedding.
7. **Health checks.** Put the database check in the **liveness** probe. Stop the database for 30 s. Watch every pod restart at once. Move it to readiness. Repeat. Watch pods stay up and simply stop taking traffic. This one exercise will save you a real outage.
8. **Nested retries.** Turn retries on at gateway, BFF, and service. Count actual requests reaching the service for one client call. Find your 27.

---

← [Chapter 8](08-outbox-and-idempotency.md) · [Tutorial index](README.md) · Next: [Chapter 10 — Observability](10-observability.md)
