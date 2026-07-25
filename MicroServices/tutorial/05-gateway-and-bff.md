# Chapter 5 — Gateway and BFF: Talking to the Outside World

← [Chapter 4](04-choosing-a-broker.md) · [Tutorial index](README.md) · Next: [Chapter 6 — Boundaries](06-boundaries-and-data.md)

---

## The story so far

The backend is in good shape. Checkout is async ([chapter 3](03-asynchronous.md)) and running on Azure Service Bus ([chapter 4](04-choosing-a-broker.md)).

Then the store ships a **mobile app**, and the support inbox fills up:

> *"The orders screen takes forever on mobile data."*
> *"This app kills my battery."*

You open the network trace for one screen. Six API calls, 2.5 seconds on 4G. Meanwhile BlueDart, the shipping partner, wants to send you a webhook when a parcel is scanned — and nobody can agree which service should receive it.

This chapter is about everything crossing your trust boundary: **axis 2** from [chapter 1](01-three-axes.md).

---

## In one line

Your system needs one front door, not fifty.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **North-south traffic** | Traffic between the outside world and your system. |
| **API Gateway** | One entry point all outside traffic goes through. Handles auth, routing, rate limiting, TLS. |
| **BFF (Backend For Frontend)** | A small service built for **one** kind of client. The web BFF and the mobile BFF are different services. |
| **TLS termination** | The gateway decrypts HTTPS so services behind it can speak plain HTTP internally. |
| **Rate limiting** | Refusing requests from a caller who sends too many. |
| **Reverse proxy** | A server that forwards requests to other servers. A gateway is a reverse proxy with extra features. |
| **Server-Sent Events (SSE)** | A long-lived HTTP response the server keeps writing to. One direction: server → client. |
| **WebSocket** | A two-way connection that stays open. Both sides can send at any time. |
| **Webhook** | The reverse of an API call: *they* call *you* when something happens. |
| **Backplane** | Shared storage (usually Redis) that lets several server instances reach each other's WebSocket connections. |

---

## Why a gateway

Right now, Priya's phone must know about every service:

```
Priya's phone ──► Ordering      (needs its URL, its auth, its version)
              ──► Catalog
              ──► Inventory
              ──► Shipping
```

Six problems, all of them real, all of them happening to the store today:

| # | Problem | What it costs the store |
|---|---|---|
| 1 | Every service implements auth | Six services, six chances to get it wrong |
| 2 | The client knows your internal layout | Split `Catalog` in two and every app on every phone breaks |
| 3 | CORS everywhere | Every service must allow your web origin |
| 4 | No single place for rate limiting | An abusive caller must be blocked six times |
| 5 | Six public TLS certificates | Six things to renew, six ways to have an outage |
| 6 | **Chatty mobile clients** | 6 calls × 400 ms on 4G = 2.4 seconds, and a hot battery |

With a gateway:

```
Priya's phone ──► Gateway ──► Ordering
                          ──► Catalog
                          ──► Inventory
                          ──► Shipping
```

The client knows **one** address. The gateway knows the map.

---

## What belongs in a gateway

> **The line to remember: the gateway answers *"who are you, and where does this go?"* A service answers *"are you allowed to do this?"***

**Yes — these belong:**

| Concern | Why the gateway |
|---|---|
| TLS termination | One certificate to renew |
| Authentication (is this token valid?) | Reject bad tokens before they cost a service anything |
| Rate limiting / throttling | One place to protect everything behind it |
| Routing | `/orders/*` → Ordering. The client never learns the internal name |
| Correlation ID creation | The first place a trace is born ([chapter 10](10-observability.md)) |
| CORS | One policy |
| API versioning at the edge | `/v1/*` and `/v2/*` can route to different services |

**No — these do not belong:**

| Anti-pattern | Why it hurts |
|---|---|
| Business logic (`if order.total > 1000 then…`) | Business rules in infrastructure, owned by nobody, tested by no one |
| Data transformation between services | Hides real contract mismatches |
| Aggregating 6 services into one response | That is a BFF's job, not the gateway's |
| Domain authorisation ("can Priya cancel order `o-123`?") | Only `Ordering` knows. The gateway knows *who she is*; the service knows *what she may do* |
| Anything one team must edit to ship a feature | The gateway becomes a deploy bottleneck for everyone |

---

## Code — a gateway with YARP

YARP is Microsoft's reverse proxy library. Configuration first, code second.

```jsonc
// Gateway/appsettings.json
{
  "ReverseProxy": {
    "Routes": {
      "orders": {
        "ClusterId": "ordering",
        "Match": { "Path": "/api/orders/{**catch-all}" },
        "AuthorizationPolicy": "authenticated",
        "RateLimiterPolicy": "per-user",
        "Transforms": [ { "PathRemovePrefix": "/api" } ]
      },
      "catalog": {
        "ClusterId": "catalog",
        "Match": { "Path": "/api/catalog/{**catch-all}" },
        "AuthorizationPolicy": "anonymous",          // browsing is public
        "RateLimiterPolicy": "per-ip"
      }
    },
    "Clusters": {
      "ordering": {
        "LoadBalancingPolicy": "PowerOfTwoChoices",
        "HealthCheck": {
          "Active": { "Enabled": true, "Path": "/health/ready", "Interval": "00:00:10" }
        },
        "Destinations": {
          "d1": { "Address": "http://ordering-1:8080" },
          "d2": { "Address": "http://ordering-2:8080" }
        }
      }
    }
  }
}
```

```csharp
// Gateway/Program.cs
builder.Services
    .AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));

builder.Services.AddRateLimiter(o =>
{
    o.AddPolicy("per-user", ctx => RateLimitPartition.GetTokenBucketLimiter(
        partitionKey: ctx.User.FindFirst("sub")?.Value ?? ctx.Connection.RemoteIpAddress!.ToString(),
        _ => new TokenBucketRateLimiterOptions
        {
            TokenLimit          = 100,
            TokensPerPeriod     = 20,
            ReplenishmentPeriod = TimeSpan.FromSeconds(1),
            QueueLimit          = 0                    // reject immediately, do not queue
        }));

    o.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
});

var app = builder.Build();

// The correlation ID is born here, at the edge, and flows to everything behind it.
app.Use(async (ctx, next) =>
{
    var correlationId = ctx.Request.Headers["X-Correlation-Id"].FirstOrDefault()
                        ?? Guid.CreateVersion7().ToString();

    ctx.Request.Headers["X-Correlation-Id"]  = correlationId;
    ctx.Response.Headers["X-Correlation-Id"] = correlationId;   // so Priya can quote it to support

    using (Serilog.Context.LogContext.PushProperty("CorrelationId", correlationId))
        await next();
});

app.UseRateLimiter();
app.UseAuthentication();
app.UseAuthorization();
app.MapReverseProxy();
```

Notice: **no business logic.** Routing, identity, limits, correlation. That is the whole job.

---

## The BFF pattern

A gateway **routes**. A BFF **aggregates and shapes** — and there is one per client type.

### Why Priya's phone and Priya's laptop need different responses

**Web** — big screen, fast network. It wants everything at once:

```jsonc
GET /web/orders/o-123
{
  "id": "o-123", "status": "Confirmed", "placedAt": "2026-07-25T10:00:00Z",
  "customer":  { "id": "c-77", "name": "Priya Sharma", "email": "…", "tier": "Gold" },
  "lines": [
    { "sku": "SKU-88", "name": "Wireless Mouse", "qty": 2, "unitPrice": 24.99,
      "imageUrl": "https://cdn/…", "inStock": true, "estimatedDelivery": "2026-07-28" }
  ],
  "payment":  { "method": "Visa ****4242", "status": "Captured" },
  "shipping": { "address": "…", "carrier": "BlueDart", "trackingNumber": "BD123456789" },
  "timeline": [ { "at": "…", "event": "Placed" }, { "at": "…", "event": "Payment captured" } ]
}
```

**Mobile** — small screen, slow network, battery matters. It wants the minimum:

```jsonc
GET /mobile/orders/o-123
{
  "id": "o-123", "status": "Confirmed", "total": 49.98, "itemCount": 2,
  "thumbnailUrl": "https://cdn/…?w=120",
  "nextAction": { "label": "Track parcel", "deepLink": "app://track/BD123456789" }
}
```

Same order. **12× smaller payload.** Different shape, chosen for a different client.

Force one shape on both and one of them suffers — usually mobile, because it is politically easier to add a field for web than to defend a small payload.

### Code — a BFF that fans out in parallel

This is the fix for the six-calls-on-4G problem. **One call from the phone; the fan-out happens inside your data centre**, where a hop costs 1 ms instead of 400 ms.

```csharp
// Bff.Mobile/Endpoints/OrderDetailsEndpoint.cs
app.MapGet("/mobile/orders/{id}", async (
    string id,
    OrderingClient orders,
    ShippingClient shipping,
    CancellationToken ct) =>
{
    // The order first — everything else needs its IDs.
    var order = await orders.GetAsync(id, ct);
    if (order is null) return Results.NotFound();

    // Then fan out IN PARALLEL. Sequential awaits here would be three times slower —
    // this is the difference between a 60 ms and a 180 ms screen.
    var shippingTask = shipping.GetAsync(id, ct);
    var thumbTask    = catalog.GetThumbnailAsync(order.Lines[0].Sku, ct);

    await Task.WhenAll(shippingTask, thumbTask);

    return Results.Ok(new MobileOrder
    {
        Id        = order.Id,
        Status    = order.Status,
        Total     = order.Total,
        ItemCount = order.Lines.Sum(l => l.Quantity),
        Thumbnail = thumbTask.Result,
        NextAction = shippingTask.Result is { TrackingNumber: not null } s
            ? new Action("Track parcel", $"app://track/{s.TrackingNumber}")
            : null
    });
});
```

**Result for the store:** 6 calls over 4G → **1 call**. 2.5 seconds → about 300 ms. The battery complaint disappears.

### And handle partial failure

If `Shipping` is down, do you fail Priya's whole order screen? No:

```csharp
// A missing tracking number should not hide the order.
var shipping = await shippingTask.ContinueWith(t =>
    t.IsCompletedSuccessfully ? t.Result : ShippingInfo.Unavailable, ct);
```

That is a **fallback**, and it is [chapter 9](09-resilience.md).

### Who owns a BFF?

**The client team.** That is the point of the pattern. The mobile team owns the mobile BFF and can reshape a response without asking anyone. If a platform team owns all BFFs, you have rebuilt the deploy bottleneck you were removing.

---

> **Diagram: D5 — Gateway and BFF topology**
> [Mermaid source](../diagrams/README.md#d5--gateway-and-bff-topology)

---

## Protocol choice at the edge

| Protocol | Optimises for | Use when | Watch out for |
|---|---|---|---|
| **REST/JSON** | Simplicity, caching, tooling | Default for public and web APIs | Over-fetching; many round trips |
| **GraphQL** | The client picks exactly the fields it wants | Many clients with very different needs | N+1 resolvers; hard to cache; one query can be a denial-of-service |
| **gRPC-Web** | Speed and a strict contract | You control the client | Needs a proxy; poor browser debuggability |
| **SSE** | Simple server → client streaming | Live status, progress bars, feeds | One direction only |
| **WebSocket** | Two-way, low latency | Chat, collaborative editing, trading | Stateful; scaling needs a backplane |

**Practical advice:** REST for the public API, gRPC internally, one push channel for live updates. Add GraphQL only when you can name the client whose life it improves.

---

## Server-initiated communication — the axis most articles forget

Everything so far assumes the client asks first. But the store often needs to tell Priya something: *your order is confirmed*, *your parcel is out for delivery*.

### The four ways

| Way | How | Good | Bad |
|---|---|---|---|
| **Polling** | Client asks every N seconds | Trivial, works everywhere | Wasteful; latency = interval |
| **Long polling** | Server holds the request until it has news | Works through any proxy | Ties up a connection per client |
| **SSE** | One long-lived HTTP response | Simple, auto-reconnects, plain HTTP | Server → client only |
| **WebSocket** | Two-way persistent connection | Lowest latency, both directions | Stateful; scaling needs a backplane |

### Code — closing the gap from chapter 3

Remember Priya's support ticket in [chapter 3](03-asynchronous.md)? She bought a mouse, got `202 Accepted`, and her order was not on the page yet.

This is the fix:

```csharp
// Notifications/Hubs/OrderHub.cs
public sealed class OrderHub : Hub
{
    // Each user joins a private group, so we never broadcast one customer's
    // order to everyone. That would be a data-protection incident, not a bug.
    public override async Task OnConnectedAsync()
    {
        var userId = Context.User!.FindFirst("sub")!.Value;
        await Groups.AddToGroupAsync(Context.ConnectionId, $"user:{userId}");
        await base.OnConnectedAsync();
    }
}
```

```csharp
// Notifications/Consumers/PaymentSucceededConsumer.cs
// An event from the broker becomes a push to the browser. This is the bridge
// between east-west (async) and north-south (push).
public sealed class PaymentSucceededConsumer(IHubContext<OrderHub> hub) : IConsumer<PaymentSucceeded>
{
    public async Task Consume(ConsumeContext<PaymentSucceeded> ctx)
    {
        await hub.Clients
            .Group($"user:{ctx.Message.CustomerId}")
            .SendAsync("OrderConfirmed", new
            {
                orderId = ctx.Message.OrderId,
                status  = "Confirmed"
            }, ctx.CancellationToken);
    }
}
```

**What Priya now sees:**

```
10:00:00.040   "Processing your order…"     ← 202 Accepted
10:00:00.900   "Order confirmed ✓"          ← pushed, no refresh
```

No polling. No refresh. No support ticket.

### Webhooks — when BlueDart calls you

BlueDart tells you a parcel was scanned by calling **your** endpoint. Three rules, all non-negotiable:

```csharp
// Api/Webhooks/CarrierWebhookEndpoint.cs
app.MapPost("/webhooks/bluedart", async (
    HttpRequest req,
    IWebhookVerifier verifier,
    IProcessedWebhookStore seen,
    IBus bus,
    CancellationToken ct) =>
{
    var body      = await new StreamReader(req.Body).ReadToEndAsync(ct);
    var signature = req.Headers["X-BlueDart-Signature"].FirstOrDefault();

    // RULE 1 — verify the signature. Anyone on the internet can POST to this URL.
    if (!verifier.IsValid(body, signature))
        return Results.Unauthorized();

    var evt = JsonSerializer.Deserialize<CarrierEvent>(body)!;

    // RULE 2 — be idempotent. Carriers retry, and they retry aggressively.
    if (!await seen.TryMarkAsync(evt.Id, ct))
        return Results.Ok();                      // already handled. Say 200, not 409.

    // RULE 3 — return fast. Do the real work asynchronously.
    // Carriers time out in 5–10 seconds and then retry, multiplying your load.
    await bus.Publish(new ParcelScanned(evt.TrackingNumber, evt.Status), ct);

    return Results.Ok();
});
```

Note rule 2 returns **200, not 409**. From BlueDart's point of view the delivery succeeded; a 4xx makes them retry harder.

---

## Sharp edges

**Edge 1 — The gateway becomes a deploy bottleneck.** If shipping a feature means a pull request to the gateway repo, every team queues behind one repo. Fix: routes generated from service metadata, or per-team route files. Never a hand-edited 3,000-line config.

**Edge 2 — The gateway is a single point of failure.** Everything goes through it, so it must be boring, stateless, and horizontally scaled — at least 3 instances. Deploy it more carefully than anything else you own.

**Edge 3 — Auth at the gateway only is not enough.** The gateway validates Priya's token. It does not know whether she may cancel order `o-123` — only `Ordering` knows. If the gateway is your only check, one misconfigured internal route exposes everything.

**Edge 4 — BFF sprawl.** Three clients, three BFFs, 70% copy-pasted. Fix: share the *clients* and cross-cutting middleware in a library; keep the *shaping* separate. Sharing the shaping defeats the pattern.

**Edge 5 — WebSocket scaling needs a backplane.** Priya connects to instance 1. The `PaymentSucceeded` event is handled by instance 2, which has no connection to her. You need Redis as a SignalR backplane so any instance can reach any connection. Teams discover this the day they scale from one instance to two — it presents as *"push works locally but not in production"*.

**Edge 6 — Mobile clients live forever.** An app version from two years ago is on real phones. You cannot break `/v1`. Plan for versions running side by side for years, and instrument usage per version so you know when it is genuinely safe to remove one.

---

## When to use what

| Situation | Answer |
|---|---|
| Any traffic from outside your network | Gateway. Always |
| One client type, simple needs | Gateway only. No BFF |
| Web + mobile with genuinely different needs | Gateway + one BFF per client |
| Partner or public API | Gateway + a separately versioned public surface |
| Client needs live updates | SSE for one-way; WebSocket/SignalR for two-way |
| An external system must notify you | Webhook: verify, dedupe, return fast |
| **Internal service-to-service** | **No gateway.** Call directly or use the broker. A gateway in the middle adds a hop and a failure point for nothing |

---

## Try it yourself

**Build it.** A YARP gateway in front of two services. Add JWT auth and a per-user rate limit. Then a BFF that fans out to both in parallel.

**Now break it:**

1. Send 200 requests in a second from one user. Confirm you get `429`, and confirm the limit is **per user** — a second user should be unaffected.
2. Stop one of the two services. Does your BFF return a partial screen, or a 500? Make it return a partial screen with a fallback.
3. In the BFF, replace `Task.WhenAll` with sequential `await`s. Measure. Put it back. Measure again. **That gap is why parallel fan-out matters.**
4. Delete the correlation ID middleware. Now try to trace one request across gateway, BFF, and both services using logs only. Give up after five minutes. Put it back. *That five minutes is why [chapter 10](10-observability.md) exists.*
5. Run two SignalR instances behind the gateway. Connect a browser and push an event from the *other* instance. Notice the browser gets nothing. Add a Redis backplane. Notice it now works.
6. POST to your webhook endpoint with `curl` and no signature. If it does something, you have a security bug.

---

## What is still broken

The edge is solved. Priya's app is fast, there is one front door, and BlueDart's webhooks work.

Then, on a normal Tuesday, something strange happens.

The Inventory team adds a `NOT NULL` column to a table. Their deploy succeeds. Twenty minutes later, **`Ordering` starts throwing database errors on every insert** — and the Ordering team has not deployed anything for three days.

It takes four hours to work out why. When they do, the answer is uncomfortable: both services have been writing to the same database since the split. Nobody wrote it down. It "worked fine" for a year.

That is [chapter 1's axis 3](01-three-axes.md#axis-3--the-boundary-itself-who-owns-what) coming due — and it is the next chapter.

---

← [Chapter 4](04-choosing-a-broker.md) · [Tutorial index](README.md) · Next: [Chapter 6 — Boundaries and data ownership](06-boundaries-and-data.md)
