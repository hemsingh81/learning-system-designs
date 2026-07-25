# Chapter 2 — Synchronous Communication

← [Chapter 1](01-three-axes.md) · [Tutorial index](README.md) · Next: [Chapter 3 — Asynchronous](03-asynchronous.md)

---

## In one line

The caller waits for the answer, and while it waits it can do nothing else.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Synchronous** | The caller stops and waits for a reply. Also called "blocking". |
| **Request-response** | One message out, one message back. |
| **REST** | A style of HTTP API. Resources have URLs; verbs (`GET`, `POST`) say what to do. |
| **gRPC** | A fast binary way to call another service. You define the contract in a file, and tooling generates the client and server code. |
| **Protobuf** | The compact binary format gRPC uses instead of JSON. |
| **Service discovery** | How a service finds another service's address without hardcoding an IP. |
| **Temporal coupling** | Two services must be alive at the same moment for the work to happen. |
| **Idempotent** | Doing it twice has the same effect as doing it once. `GET` is idempotent. Charging a card is not, unless you make it so. |

---

## How it works

The whole idea in one sequence: `Ordering` needs stock, so it asks `Inventory` and waits.

```
Ordering ──── GET /stock/SKU-88 ────► Inventory
   (waiting...)                          (looks up DB, 12ms)
Ordering ◄─── 200 { available: 42 } ──── Inventory
   (continues)
```

That is it. The complexity is not in the mechanism — it is in what happens when the reply is slow or never comes.

---

### Option A — HTTP / REST

The default. Every language, every tool, every proxy, every debugger speaks it.

```csharp
// Ordering/Clients/InventoryClient.cs
public sealed class InventoryClient(HttpClient http)
{
    public async Task<StockLevel?> GetStockAsync(string sku, CancellationToken ct)
    {
        // Relative URL only. The base address comes from config, never hardcoded here.
        using var res = await http.GetAsync($"/stock/{sku}", ct);

        if (res.StatusCode == HttpStatusCode.NotFound) return null;

        res.EnsureSuccessStatusCode();
        return await res.Content.ReadFromJsonAsync<StockLevel>(cancellationToken: ct);
    }
}

public record StockLevel(string Sku, int Available);
```

Registered with a timeout — never rely on the default, which is 100 seconds and far too long:

```csharp
// Ordering/Program.cs
builder.Services.AddHttpClient<InventoryClient>(c =>
{
    c.BaseAddress = new Uri(builder.Configuration["Services:Inventory"]!);
    c.Timeout     = TimeSpan.FromSeconds(2);   // bound the wait. Always.
});
```

**Why REST is a good default:**
- Human-readable. You can debug it with `curl` at 2 a.m.
- Cacheable. `GET` responses can be cached by the browser, a CDN, or your gateway.
- Universally supported by proxies, gateways, load balancers, and logging tools.

**What it costs:** JSON is verbose, parsing it takes CPU, and there is no enforced contract — the other team can rename a field and you find out in production.

---

### Option B — gRPC

For calls **inside** your system, where both sides are yours and you care about speed.

You write the contract first, in a `.proto` file:

```protobuf
// contracts/inventory.proto
syntax = "proto3";
package inventory.v1;

service InventoryService {
  rpc GetStock (GetStockRequest) returns (GetStockReply);
}

message GetStockRequest { string sku = 1; }
message GetStockReply   { string sku = 1; int32 available = 2; }
```

Tooling generates the client and the server base class. Calling it looks like a local method call:

```csharp
// Ordering/Clients/InventoryGrpcClient.cs
public sealed class InventoryGrpcClient(InventoryService.InventoryServiceClient client)
{
    public async Task<int> GetAvailableAsync(string sku, CancellationToken ct)
    {
        var reply = await client.GetStockAsync(
            new GetStockRequest { Sku = sku },
            deadline: DateTime.UtcNow.AddSeconds(2),   // gRPC calls it a deadline, not a timeout
            cancellationToken: ct);

        return reply.Available;
    }
}
```

**Why gRPC:**
- 5–10× smaller on the wire than JSON, and faster to parse.
- The contract is a real file in source control. Breaking it fails the build, not production.
- HTTP/2 multiplexing: many calls share one connection.
- Streaming in both directions is built in.

**What it costs:**
- Not readable by a human on the wire without tooling.
- Browsers cannot call it directly (you need gRPC-Web or a gateway to translate).
- Another build step and another set of generated files.

**Rule of thumb:** gRPC inside, REST at the edge.

---

### Service discovery

Never write this:

```csharp
c.BaseAddress = new Uri("http://10.4.22.17:8080");  // ✗ dies the moment a pod moves
```

Instead, use a logical name that the platform resolves:

| Platform | What you use |
|---|---|
| Kubernetes | DNS name of the Service: `http://inventory.default.svc.cluster.local` |
| Docker Compose | The service name: `http://inventory:8080` |
| Consul / Eureka | A registry lookup by name |
| Azure Container Apps | The app name: `https://inventory.internal.<env>.azurecontainerapps.io` |

In every case, the address goes in **configuration**, not code.

---

> **Diagram: D2 — Synchronous vs asynchronous**
> [`images/svg/d2-sync-vs-async.svg`](../images/svg/d2-sync-vs-async.svg) · [Mermaid source](../diagrams/README.md#d2--synchronous-vs-asynchronous)

![Synchronous vs asynchronous](../images/svg/d2-sync-vs-async.svg)

---

## Sharp edges

### Edge 1 — Temporal coupling

For the work to happen, `Inventory` must be alive **right now**, at this exact millisecond. If it is restarting, your request fails. You have tied your uptime to someone else's uptime.

If your service depends on 4 services synchronously, and each has 99.9% uptime, your effective uptime is:

```
0.999 ⁴ = 0.996  →  about 3.5 hours of downtime per month, caused entirely by other people
```

### Edge 2 — Latency compounds

Every hop adds its own time. They add up, they do not overlap:

```
Gateway → Ordering → Inventory → Pricing → Tax → Ordering → Gateway
   10ms  +   15ms   +   40ms    +  35ms   + 60ms +  10ms   +  10ms   = 180ms
```

That 180 ms is your **floor**. It is what the user pays before any useful work is done. And it is the *good* case — the average. Your 99th percentile will be far worse, because the slowest hop dominates.

> **The rule:** in a synchronous chain, your latency is the **sum**, and your availability is the **product**. Both get worse with every hop you add.

### Edge 3 — Cascading failure

This is the 2 a.m. incident, step by step:

1. `Payments` gets slow — from 200 ms to 4 s. It is not down. It is just slow.
2. `Ordering` calls `Payments` and waits 4 s per request.
3. Each waiting request holds a thread and a connection. `Ordering`'s connection pool fills up.
4. Now `Ordering` is slow for **every** request, including ones that never touch payments.
5. The gateway's calls to `Ordering` start timing out.
6. Retries kick in. Every timed-out request is now sent 3 times.
7. Traffic to `Payments` has tripled. It goes from slow to dead.
8. Checkout is fully down. The original cause — a slow query in `Payments` — is now invisible under 10,000 timeout errors.

The killer detail: **step 6 made it worse.** A retry against an overloaded service is an attack on your own system.

### Edge 4 — "Just add a retry" without a circuit breaker

Retries are correct **only** when combined with:

- A **timeout**, so you fail fast instead of holding a thread.
- **Exponential backoff with jitter**, so retries spread out instead of arriving together.
- A **circuit breaker**, so once the downstream is clearly dead, you stop calling it at all.

Retry alone turns a slowdown into an outage. This is all of [chapter 9](09-resilience.md).

### Edge 5 — Chatty calls in a loop

```csharp
// ✗ 200 orders → 200 HTTP calls → 200 × 40ms = 8 seconds
foreach (var line in order.Lines)
    var stock = await inventory.GetStockAsync(line.Sku, ct);
```

```csharp
// ✓ one call, one round trip
var stock = await inventory.GetStockBatchAsync(order.Lines.Select(l => l.Sku), ct);
```

This is the N+1 query problem, moved to the network where each "query" costs 100× more. Always give your internal APIs a batch endpoint.

---

## When to use synchronous

Use it when **both** are true:

1. The caller genuinely cannot continue without the answer.
2. The answer is fast and the data is fresh-critical.

Good fits:

| Case | Why |
|---|---|
| Reading data to render a page | You need it now, to return a response now |
| Validating a token or permission | The decision blocks everything after it |
| Looking up a price or a tax rate | Cheap, fast, and the result changes the outcome |
| A risk check before accepting an order | Legally you may not proceed without it ([case study 4](../case-studies/04-trading-app/)) |

## When not to use it

| Case | Use instead |
|---|---|
| Sending a confirmation email | Async event — the user does not wait for SMTP |
| Updating a search index | Async event — seconds of staleness is fine |
| Charging a card during checkout | Async — accept the order, charge in the background ([case study 1](../case-studies/01-ecommerce/)) |
| Writing to an analytics warehouse | Async — never let reporting slow down the hot path |
| Anything where the callee being down should not fail the caller | Async |

---

## Try it yourself

**Build it.** Two Minimal API services. `Ordering` calls `Inventory` over HTTP with a 2-second timeout.

**Now break it.** In order, and observe what happens each time:

1. Add `await Task.Delay(5000)` in `Inventory`'s handler. Your timeout fires. Good — that is the timeout working.
2. Remove the timeout (`c.Timeout = Timeout.InfiniteTimeSpan`). Send 200 concurrent requests. Watch `Ordering` stop responding to *everything*. That is thread and connection exhaustion — edge 3, step 4.
3. Put the timeout back. Add 3 retries with no delay between them. Count the requests arriving at `Inventory`. You just tripled the load on a service that was already struggling — edge 4.
4. Add exponential backoff with jitter. Count again. Notice the requests now spread out over time instead of arriving in a burst.
5. Stop `Inventory` completely. Notice that `Ordering` still spends the full timeout on every request before failing. Now add a circuit breaker and watch it fail in under a millisecond instead.

Steps 4 and 5 are [chapter 9](09-resilience.md). Steps 2 and 3 are the reason chapter 9 exists.

---

← [Chapter 1](01-three-axes.md) · [Tutorial index](README.md) · Next: [Chapter 3 — Asynchronous communication](03-asynchronous.md)
