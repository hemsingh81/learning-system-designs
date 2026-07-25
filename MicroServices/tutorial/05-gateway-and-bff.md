# Chapter 5 — Gateway and BFF: Talking to the Outside World

← [Chapter 4](04-choosing-a-broker.md) · [Tutorial index](README.md) · Next: [Chapter 6 — Boundaries](06-boundaries-and-data.md)

---

## In one line

Your system needs one front door, not fifty.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **North-south traffic** | Traffic between the outside world and your system. |
| **API Gateway** | One entry point that all outside traffic goes through. It handles auth, routing, rate limiting, TLS. |
| **BFF (Backend For Frontend)** | A small service built for **one** kind of client. The web BFF and the mobile BFF are different services. |
| **TLS termination** | The gateway decrypts HTTPS so services behind it can speak plain HTTP internally. |
| **Rate limiting** | Refusing requests from a caller who sends too many. |
| **Reverse proxy** | A server that forwards requests to other servers. A gateway is a reverse proxy with extra features. |
| **Server-Sent Events (SSE)** | A long-lived HTTP response the server keeps writing to. One direction: server → client. |
| **WebSocket** | A two-way connection that stays open. Both sides can send at any time. |
| **Webhook** | The reverse of an API call: *they* call *you* when something happens. |
| **Long polling** | The client asks, and the server holds the request open until it has something to say. |

---

## Why a gateway

Without one, every client must know about every service:

```
Mobile app ──► Ordering    (needs its URL, its auth, its version)
           ──► Catalog
           ──► Inventory
           ──► Payments
```

Problems this creates, all real:

1. **Every service must implement auth.** Five services, five chances to get it wrong.
2. **The client knows your internal layout.** Split `Catalog` into two services and every client must be updated — including the app version already on people's phones.
3. **CORS everywhere.** Every service must allow your web origin.
4. **No single place for rate limiting**, so an abusive caller must be blocked five times.
5. **Every service needs a public TLS certificate.**
6. **Chatty mobile clients.** A phone on 4G making 6 calls to render one screen is a slow app and a hot battery.

With a gateway:

```
Mobile app ──► Gateway ──► Ordering
                       ──► Catalog
                       ──► Inventory
                       ──► Payments
```

The client knows one address. The gateway knows the map.

---

## What belongs in a gateway

**Yes — these belong:**

| Concern | Why the gateway |
|---|---|
| TLS termination | One certificate to renew |
| Authentication (is this token valid?) | Reject bad tokens before they cost a service anything |
| Rate limiting / throttling | One place to protect everything behind it |
| Routing | `/orders/*` → Ordering. The client never learns the internal name |
| Request/response logging + correlation ID | The first place a trace is born |
| CORS | One policy |
| Response compression | One setting |
| API versioning at the edge | `/v1/*` and `/v2/*` can route to different services |

**No — these do not belong:**

| Anti-pattern | Why it hurts |
|---|---|
| Business logic ("if order total > 1000 then...") | Now business rules live in infrastructure, owned by nobody, tested by no one |
| Data transformation between services | Hides real contract mismatches; the gateway becomes a translation layer nobody understands |
| Aggregating 6 services into one response | That is a BFF's job, not the gateway's |
| Authorisation of domain rules ("can this user cancel this order?") | Only the service knows. The gateway knows *who you are*, the service knows *what you may do* |
| Anything one team must edit to ship a feature | The gateway becomes a deploy bottleneck and a source of cross-team conflict |

> **The line to remember:** the gateway answers *"who are you, and where does this go?"* A service answers *"are you allowed to do this?"*

---

## Code — a gateway with YARP

YARP is Microsoft's reverse proxy library. It is configuration first, code second.

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
        "Transforms": [
          { "PathRemovePrefix": "/api" },
          { "RequestHeader": "X-Forwarded-For", "Append": "{RemoteIpAddress}" }
        ]
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
      },
      "catalog": {
        "Destinations": { "d1": { "Address": "http://catalog:8080" } }
      }
    }
  }
}
```

```csharp
// Gateway/Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));

builder.Services.AddAuthentication().AddJwtBearer();
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("authenticated", p => p.RequireAuthenticatedUser())
    .AddPolicy("anonymous",     p => p.RequireAssertion(_ => true));

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

// Correlation ID is born here, at the edge, and flows to everything behind it.
app.Use(async (ctx, next) =>
{
    var correlationId = ctx.Request.Headers["X-Correlation-Id"].FirstOrDefault()
                        ?? Guid.CreateVersion7().ToString();

    ctx.Request.Headers["X-Correlation-Id"]  = correlationId;
    ctx.Response.Headers["X-Correlation-Id"] = correlationId;

    using (Serilog.Context.LogContext.PushProperty("CorrelationId", correlationId))
        await next();
});

app.UseRateLimiter();
app.UseAuthentication();
app.UseAuthorization();
app.MapReverseProxy();

app.Run();
```

Notice: **no business logic**. Routing, identity, limits, correlation. That is the whole job.

---

## The BFF pattern

A gateway routes. A **BFF aggregates and shapes** — and there is one per client type.

### Why the web app and mobile app should not share a response

**Web** — big screen, fast network. It wants everything at once:

```json
GET /web/orders/123
{
  "id": "123", "status": "Confirmed", "placedAt": "2026-07-25T10:00:00Z",
  "customer":  { "id": "c1", "name": "Priya Sharma", "email": "p@example.com", "tier": "Gold" },
  "lines": [
    { "sku": "SKU-88", "name": "Wireless Mouse", "qty": 2, "unitPrice": 24.99,
      "imageUrl": "https://cdn/…", "inStock": true, "estimatedDelivery": "2026-07-28" }
  ],
  "payment":  { "method": "Visa ****4242", "status": "Captured", "capturedAt": "…" },
  "shipping": { "address": "…", "carrier": "BlueDart", "trackingNumber": "BD123456789" },
  "timeline": [ { "at": "…", "event": "Placed" }, { "at": "…", "event": "Payment captured" } ]
}
```

**Mobile** — small screen, slow network, battery matters. It wants the minimum:

```json
GET /mobile/orders/123
{
  "id": "123", "status": "Confirmed", "total": 49.98, "itemCount": 2,
  "thumbnailUrl": "https://cdn/…?w=120",
  "nextAction": { "label": "Track parcel", "deepLink": "app://track/BD123456789" }
}
```

Same order. 12× smaller payload. Different shape, chosen for a different client.

If you force one response shape on both, one of them suffers — usually mobile, because it is easier to add a field for web than to defend a small payload.

### Code — a BFF that fans out in parallel

```csharp
// Bff.Web/Endpoints/OrderDetailsEndpoint.cs
app.MapGet("/web/orders/{id}", async (
    string id,
    OrderingClient orders,
    CustomerClient customers,
    ShippingClient shipping,
    CancellationToken ct) =>
{
    // The order first — everything else needs its IDs.
    var order = await orders.GetAsync(id, ct);
    if (order is null) return Results.NotFound();

    // Then fan out IN PARALLEL. Sequential awaits here would be three times slower —
    // this is the difference between a 60ms and a 180ms page.
    var customerTask = customers.GetAsync(order.CustomerId, ct);
    var shippingTask = shipping.GetAsync(id, ct);

    await Task.WhenAll(customerTask, shippingTask);

    return Results.Ok(new WebOrderDetails
    {
        Id       = order.Id,
        Status   = order.Status,
        Customer = customerTask.Result,
        Shipping = shippingTask.Result,
        Lines    = order.Lines.Select(l => new WebLine(l.Sku, l.Name, l.Quantity, l.UnitPrice)).ToList()
    });
});
```

**And handle partial failure.** If `Shipping` is down, do you fail the whole page? Usually no:

```csharp
// A missing tracking number should not hide the order.
var shipping = await shippingTask.ContinueWith(t =>
    t.IsCompletedSuccessfully ? t.Result : ShippingInfo.Unavailable, ct);
```

This is a **fallback**, and it is [chapter 9](09-resilience.md).

### Who owns a BFF?

**The client team.** This is the point of the pattern. The web team owns the web BFF and can reshape a response without asking anyone. If a platform team owns all BFFs, you have rebuilt the deploy bottleneck you were trying to remove.

---

> **Diagram: D5 — Gateway and BFF topology**
> [Mermaid source](../diagrams/README.md#d5--gateway-and-bff-topology)

---

## Protocol choice at the edge

| Protocol | Optimises for | Use when | Watch out for |
|---|---|---|---|
| **REST/JSON** | Simplicity, caching, tooling | Default for public and web APIs | Over-fetching; many round trips |
| **GraphQL** | The client picks exactly the fields it wants | Many clients with very different needs; deeply nested data | N+1 resolvers; hard to cache; a single query can be a denial-of-service |
| **gRPC-Web** | Speed and a strict contract | You control the client and want typed calls | Needs a proxy to translate; poor browser debuggability |
| **SSE** | Simple server → client streaming | Live prices, progress bars, notification feeds | One direction only |
| **WebSocket** | Two-way, low latency | Chat, collaborative editing, trading | Stateful connections complicate scaling and load balancing |

**Practical advice:** REST for the public API, gRPC internally, and one push channel (SSE or WebSocket) for live updates. Add GraphQL only when you can name the client whose life it improves.

---

## Server-initiated communication — the axis most articles forget

Everything so far assumes the client asks first. But your system often needs to tell the client something: your order shipped, your price moved, your report is ready.

### The four ways

| Way | How | Good | Bad |
|---|---|---|---|
| **Polling** | Client asks every N seconds | Trivial, works everywhere | Wasteful; latency = interval |
| **Long polling** | Server holds the request until it has news | Works through any proxy | Ties up a connection per client |
| **SSE** | One long-lived HTTP response, server keeps writing | Simple, auto-reconnects, plain HTTP | Server → client only |
| **WebSocket** | Two-way persistent connection | Lowest latency, both directions | Stateful; scaling needs a backplane |

### Code — pushing an update with SignalR

```csharp
// Notifications/Hubs/OrderHub.cs
public sealed class OrderHub : Hub
{
    // Each user joins a private group, so we never broadcast one user's order to everyone.
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

This closes the eventual-consistency gap from [chapter 3](03-asynchronous.md): the user sees "Processing", and 900 ms later the page updates itself. No polling, no refresh, no support ticket.

### Webhooks — when they call you

A payment provider tells you a charge succeeded by calling **your** endpoint. Three rules, all non-negotiable:

```csharp
// Api/Webhooks/PspWebhookEndpoint.cs
app.MapPost("/webhooks/psp", async (
    HttpRequest req,
    IWebhookVerifier verifier,
    IProcessedWebhookStore seen,
    IBus bus,
    CancellationToken ct) =>
{
    var body      = await new StreamReader(req.Body).ReadToEndAsync(ct);
    var signature = req.Headers["X-PSP-Signature"].FirstOrDefault();

    // RULE 1 — verify the signature. Anyone on the internet can POST to this URL.
    if (!verifier.IsValid(body, signature))
        return Results.Unauthorized();

    var evt = JsonSerializer.Deserialize<PspEvent>(body)!;

    // RULE 2 — be idempotent. Providers retry, and they retry aggressively.
    if (!await seen.TryMarkAsync(evt.Id, ct))
        return Results.Ok();                      // already handled. Say 200, not 409.

    // RULE 3 — return fast. Do the real work asynchronously.
    // Providers time out in 5–10 seconds and then retry, which multiplies your load.
    await bus.Publish(new PspEventReceived(evt.Id, evt.Type, body), ct);

    return Results.Ok();
});
```

---

## Sharp edges

**Edge 1 — The gateway becomes a deploy bottleneck.** If shipping a feature means a pull request to the gateway repo, every team is queued behind one repo. Fix: routes generated from service metadata, or per-team route files, or an operator that reads Kubernetes annotations. Never a hand-edited 3,000-line config.

**Edge 2 — The gateway is a single point of failure.** Everything goes through it, so it must be boring, stateless, and horizontally scaled — at least 3 instances behind a load balancer. Deploy it more carefully than anything else you own.

**Edge 3 — Auth at the gateway only is not enough.** The gateway validates the token. It does not know whether user `u-77` may cancel order `o-123`. Only `Ordering` knows. Services must still authorise. If the gateway is your only check, one misconfigured internal route exposes everything.

**Edge 4 — BFF sprawl.** Three clients, three BFFs, and 70% of the code is copy-pasted. Fix: share the *clients* and cross-cutting middleware in a library; keep the *shaping* separate. Sharing the shaping defeats the pattern.

**Edge 5 — WebSocket scaling needs a backplane.** User A connects to instance 1. The event that concerns them is handled by instance 2. Instance 2 has no connection to A. You need Redis (or ASB) as a SignalR backplane so any instance can reach any connection. Teams discover this on the day they scale from one instance to two.

**Edge 6 — Mobile clients live forever.** An app version from two years ago is still installed on real phones. You cannot break `/v1`. Plan for versions running side by side for years, and instrument usage per version so you know when it is genuinely safe to remove one.

---

## When to use what

| Situation | Answer |
|---|---|
| Any traffic from outside your network | Gateway. Always. |
| One client type, simple needs | Gateway only. No BFF. |
| Web + mobile with genuinely different needs | Gateway + one BFF per client |
| Partner or public API | Gateway + a separately versioned public API surface |
| Client needs live updates | SSE for one-way; WebSocket/SignalR for two-way |
| An external system must notify you | Webhook: verify, dedupe, return fast |
| Internal service-to-service | **No gateway.** Call directly, or use the broker. A gateway in the middle adds a hop and a failure point for nothing. |

---

## Try it yourself

**Build it.** A YARP gateway in front of two services. Add JWT auth and a per-user rate limit. Then a web BFF that fans out to both in parallel.

**Now break it:**

1. Send 200 requests in a second from one user. Confirm you get `429`, and confirm the limit is per user — a second user should be unaffected.
2. Stop one of the two services. Does your BFF return a partial page, or a 500? Make it return a partial page with a fallback.
3. In the BFF, replace `Task.WhenAll` with sequential `await`s. Measure the page time. Put it back. Measure again. That gap is why parallel fan-out matters.
4. Delete the correlation ID middleware. Now try to trace one request across gateway, BFF, and both services using logs only. Give up after five minutes. Put it back. That five minutes is why [chapter 10](10-observability.md) exists.
5. Run two instances of your SignalR service behind the gateway. Connect a browser and push an event from the *other* instance. Notice the browser gets nothing. Add a Redis backplane. Notice it now works.
6. POST to your webhook endpoint with `curl` and no signature. If it does something, you have a security bug — fix it, then try again.

---

← [Chapter 4](04-choosing-a-broker.md) · [Tutorial index](README.md) · Next: [Chapter 6 — Boundaries and data ownership](06-boundaries-and-data.md)
