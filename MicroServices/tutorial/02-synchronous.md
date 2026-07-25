# Chapter 2 — Synchronous Communication

← [Chapter 1](01-three-axes.md) · [Tutorial index](README.md) · Next: [Chapter 3 — Asynchronous](03-asynchronous.md)

---

## The story so far

You have drawn the map ([chapter 1](01-three-axes.md)). It showed six services and one arrow that looked risky: `Ordering` calls `Payments` and waits for an answer.

Tonight is the Diwali sale. The campaign email goes out at 00:00. This chapter is what happens next.

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
| **Thread** | A worker inside your process. Each waiting request usually holds one. You have a limited number. |
| **Connection pool** | A fixed set of reusable network connections. When it is empty, new calls queue up. |
| **Idempotent** | Doing it twice has the same effect as doing it once. `GET` is idempotent. Charging a card is not, unless you make it so. |

---

## How it works

The whole idea in one picture. `Ordering` needs stock, so it asks `Inventory` and waits:

```
Ordering ──── GET /stock/SKU-88 ────► Inventory
   (waiting…)                            (looks up DB, 12 ms)
Ordering ◄─── 200 { available: 42 } ──── Inventory
   (continues)
```

**Think of it like a phone call.** You dial, you wait, they pick up, you get your answer, you hang up. While the phone is ringing you cannot do anything else — you are holding the line.

That is it. The mechanism is simple. All the difficulty is in what happens when the other end is slow or does not pick up.

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

- Human-readable. You can debug it with `curl` at 2 a.m. — and tonight, you will.
- Cacheable. `GET` responses can be cached by the browser, a CDN, or your gateway.
- Universally supported by proxies, load balancers, and logging tools.

**What it costs:** JSON is verbose, parsing it takes CPU, and there is no enforced contract — the Inventory team can rename `available` to `qty` and you find out in production.

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

**What it costs:** not readable on the wire without tooling; browsers cannot call it directly (you need gRPC-Web or a translating gateway); another build step.

**Rule of thumb: gRPC inside, REST at the edge.**

---

### Service discovery

Never write this:

```csharp
c.BaseAddress = new Uri("http://10.4.22.17:8080");  // ✗ dies the moment a pod moves
```

Use a logical name the platform resolves:

| Platform | What you use |
|---|---|
| Kubernetes | DNS name of the Service: `http://inventory.default.svc.cluster.local` |
| Docker Compose | The service name: `http://inventory:8080` |
| Consul / Eureka | A registry lookup by name |
| Azure Container Apps | The app name: `https://inventory.internal.<env>.azurecontainerapps.io` |

In every case, the address lives in **configuration**, not code.

---

> **Diagram: D2 — Synchronous vs asynchronous**
> [`images/svg/d2-sync-vs-async.svg`](../images/svg/d2-sync-vs-async.svg) · [Mermaid source](../diagrams/README.md#d2--synchronous-vs-asynchronous)

![Synchronous vs asynchronous](../images/svg/d2-sync-vs-async.svg)

---

## The store's checkout, version 1

Here is how checkout works tonight. Everything is synchronous — the simplest thing that works, and it has worked fine for a year.

```
Priya taps "Buy now"
   │
   ▼
POST /orders
   │
   ├─► Inventory: reserve 2 × SKU-88     (12 ms)
   ├─► Payments:  charge ₹49.98          (800 ms)
   ├─► Ordering:  save order             (8 ms)
   └─► Notifications: send email         (150 ms)
   │
   ▼
201 Created — "Order confirmed!"          total: ~970 ms
```

Just under a second. Priya sees her confirmation. Everyone is happy.

At 50 orders per minute, this is completely fine. **The design is not wrong — it is untested at scale.**

---

## The 2 a.m. incident

The campaign email lands at 00:00. Traffic goes from 50 orders/minute to 5,000 orders/minute in about ninety seconds.

Here is exactly what happens, step by step.

### 00:02 — Acme Pay gets slow

Not down. **Slow.** Their systems are handling every retailer's Diwali sale at once. Response time drifts from 800 ms to 4 seconds.

Nothing in your system has failed yet. No errors. No alerts.

### 00:03 — Requests start piling up

Every checkout now takes about 4.2 seconds instead of 970 ms. Each one holds a thread while it waits.

Do the arithmetic:

```
5,000 orders/min  =  83 orders/second
each holds a thread for 4.2 seconds
83 × 4.2  =  349 threads needed, all the time
```

`Ordering` is configured with 200 threads.

### 00:04 — Ordering stops responding to everything

The thread pool is exhausted. The connection pool is exhausted. New requests queue up behind the ones already waiting.

**And here is the part that surprises people:** requests that have nothing to do with payments are now also failing. `GET /orders/o-123` — just reading a row from a database — cannot get a thread. Priya cannot even look at her order history.

> **One slow dependency has taken down the entire service, including the parts that never touch it.**

### 00:05 — The gateway starts timing out

The gateway waits 5 seconds for `Ordering`, gives up, and returns `504 Gateway Timeout`.

### 00:06 — Retries make it much worse

The gateway is configured to retry failed requests 3 times. It seems sensible. Tonight it is the thing that finishes you off.

```
83 real orders/second
    × 4 attempts (1 original + 3 retries)
    = 332 requests/second hitting a system that is already drowning
```

Traffic to `Payments` has **quadrupled**. Acme Pay goes from slow to refusing connections entirely.

### 00:08 — Total collapse

Checkout is fully down. The error log is 10,000 timeout exceptions per minute. The original cause — one dependency drifting from 800 ms to 4 s — is completely invisible underneath them.

Someone wakes you up.

### What actually went wrong

Read the timeline again and notice: **the payment provider never went down.** It got slower. Everything else was your own system amplifying a small problem into an outage.

| Step | What made it worse |
|---|---|
| 00:03 | No timeout tuned for this — threads held for 4 s each |
| 00:04 | No isolation — one dependency consumed every thread |
| 00:06 | **Retries with no circuit breaker — you attacked yourself** |

Those three lines become chapter 9. But first, chapter 3 removes the reason you were waiting at all.

---

## Sharp edges

### Edge 1 — Temporal coupling

For the work to happen, `Payments` must be alive **right now**, this exact millisecond. If it is restarting for a 20-second deploy, your checkout fails for 20 seconds.

You have tied your uptime to someone else's uptime. And it compounds:

```
Ordering depends on Inventory, Payments, Catalog, Notifications
Each is up 99.9% of the time

Your real availability = 0.999 × 0.999 × 0.999 × 0.999
                       = 0.996
                       = about 3.5 hours of downtime per month,
                         caused entirely by other people's services
```

### Edge 2 — Latency compounds

Every hop adds its own time. They add up; they do not overlap:

```
Gateway → Ordering → Inventory → Pricing → Tax → Ordering → Gateway
   10ms  +   15ms   +   12ms    +  35ms   + 60ms +  10ms   +  10ms   = 152ms
```

That 152 ms is your **floor**. It is what Priya pays before any useful work happens. And it is the *good* case — the average. Your 99th percentile is far worse, because the slowest hop dominates.

> **The rule worth memorising:** in a synchronous chain, latency is the **sum**, and availability is the **product**. Both get worse with every hop you add.

### Edge 3 — Cascading failure

This is the 2 a.m. incident above. The general shape:

```
one service gets slow
   → its callers hold threads waiting
      → its callers get slow for ALL requests
         → their callers time out
            → retries multiply the load
               → the original slow service dies completely
```

Each arrow is your own system making the problem worse.

### Edge 4 — "Just add a retry" without a circuit breaker

Retries are correct **only** when combined with:

- A **timeout**, so you fail fast instead of holding a thread.
- **Exponential backoff with jitter**, so retries spread out instead of arriving together.
- A **circuit breaker**, so once the downstream is clearly dead, you stop calling it at all.

Retry alone turns a slowdown into an outage. That is [chapter 9](09-resilience.md).

### Edge 5 — Chatty calls in a loop

Priya's order has 2 lines. A bulk business order has 200.

```csharp
// ✗ 200 lines → 200 HTTP calls → 200 × 12ms = 2.4 seconds
foreach (var line in order.Lines)
    var stock = await inventory.GetStockAsync(line.Sku, ct);
```

```csharp
// ✓ one call, one round trip
var stock = await inventory.GetStockBatchAsync(order.Lines.Select(l => l.Sku), ct);
```

This is the N+1 query problem moved to the network, where each "query" costs 100× more. **Always give your internal APIs a batch endpoint.**

---

## When to use synchronous

Use it when **both** are true:

1. The caller genuinely cannot continue without the answer.
2. The answer is fast and the data must be fresh.

Good fits in the store:

| Case | Why |
|---|---|
| Loading a product page | You need the price now, to render now |
| Validating Priya's login token | The decision blocks everything after it |
| Looking up a tax rate | Cheap, fast, and it changes the total |

## When not to use it

| Case | Use instead |
|---|---|
| Sending Priya's confirmation email | Async — she does not wait for SMTP |
| Updating the search index | Async — a few seconds of staleness is fine |
| **Charging the card during checkout** | **Async — this is tonight's lesson** |
| Writing to the analytics warehouse | Async — never let reporting slow the hot path |
| Anything where the callee being down should not fail the caller | Async |

---

## Try it yourself

**Build it.** Two Minimal API services. `Ordering` calls `Inventory` over HTTP with a 2-second timeout.

**Now break it** — this reproduces tonight, in miniature:

1. Add `await Task.Delay(5000)` in `Inventory`'s handler. Your timeout fires. Good — that is the timeout working.
2. Remove the timeout (`c.Timeout = Timeout.InfiniteTimeSpan`). Send 200 concurrent requests. Watch `Ordering` stop responding to *everything*, including endpoints that never call `Inventory`. **That is 00:04.**
3. Put the timeout back. Add 3 retries with no delay. Count requests arriving at `Inventory` — you just tripled load on a struggling service. **That is 00:06.**
4. Add exponential backoff with jitter. Count again. The requests now spread out over time instead of arriving in a burst.
5. Stop `Inventory` completely. Notice `Ordering` still burns the full 2-second timeout on every request before failing. Add a circuit breaker and watch it fail in under a millisecond instead.

Steps 4 and 5 are [chapter 9](09-resilience.md). Steps 2 and 3 are the reason chapter 9 exists.

---

## What is still broken

You now understand why checkout died: **Priya's order waited for a card charge that had nothing to do with whether her order was valid.**

She does not need the card charged before she gets a confirmation. She needs to know you have her order. The charge can happen a second later.

That single realisation is the fix — and the next chapter builds it. Checkout goes from **4 seconds to 40 milliseconds**, and Acme Pay can be down for a full minute without losing a single order.

It also creates three new problems you have never had before.

---

← [Chapter 1](01-three-axes.md) · [Tutorial index](README.md) · Next: [Chapter 3 — Asynchronous communication](03-asynchronous.md)
