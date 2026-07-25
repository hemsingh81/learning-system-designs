# 3 — Boundaries and Edges

← [Communication](02-communication.md) · [Interview index](README.md) · Next: [Reliability →](04-reliability.md)

16 questions on data ownership, contracts, gateways, and the outside world.

---

<details id="q1">
<summary><b>Q1 · Why is database-per-service a rule and not a preference?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

Because a shared database removes every benefit you split the services for.

If two services share a schema, you cannot deploy either alone, a slow query in one causes an incident in the other, and nobody can safely change a column. You have one service with extra network hops.

**If they dig deeper**

The specific failures, all of which I have seen:

- Service A adds a `NOT NULL` column. Service B's inserts start failing. Nobody knows why, because B's team never heard about it.
- Service A runs a reporting query. Service B times out. B has an incident caused by a team they have never spoken to.
- Nobody owns the `Customers` table, so nobody dares change it, so it grows to 180 columns.

**Follow-up to expect:** *"What about sharing a database server, just different schemas?"* → Acceptable operationally, and it is what the case study `docker-compose` files do for local development. But the discipline must hold: no cross-schema queries, no shared tables, no foreign keys across the boundary. The moment someone writes a "quick" join across schemas, you are back to a shared database.

📖 [Chapter 6 — Database-per-service](../tutorial/06-boundaries-and-data.md#database-per-service)

</details>

---

<details id="q2">
<summary><b>Q2 · How do you join data across services for a report?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

You do not join. You pick one of three:

| Approach | How | Best for |
|---|---|---|
| **API composition** | The caller (usually a BFF) calls both and joins in memory | Small result sets, one UI screen |
| **Read model / projection** | A service listens to events and keeps its own denormalised copy | Lists, dashboards, search |
| **Data warehouse** | Everything streams into a warehouse for reporting | Real reporting and BI |

**If they dig deeper**

The common mistake is using API composition for a report over 50,000 rows — that is 50,000 HTTP calls. API composition is for a page, not a report.

For anything list-shaped, build a projection: one service subscribes to the events it cares about and maintains a table shaped for the query. It is eventually consistent, which is nearly always fine for a report.

**Follow-up to expect:** *"How do you rebuild a projection when it's wrong?"* → Replay the events from the log. This is one of the few genuinely good reasons to choose Kafka: you can drop the projection, reset the offset to zero, and rebuild from scratch. With a queue you cannot, because the messages are gone.

📖 [Chapter 6 — The three honest questions](../tutorial/06-boundaries-and-data.md#the-three-honest-questions-this-raises)

</details>

---

<details id="q3">
<summary><b>Q3 · How do you keep referential integrity without foreign keys?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

You accept that you cannot have a database-enforced FK across services, and replace it with three things:

1. **Validate on write** — check the referenced entity exists (a cached call, or your own local copy from events).
2. **Handle the missing case on read** — a deleted customer means the UI shows "Customer unavailable", not a crash.
3. **Reconcile** — a nightly job finds orphans and reports them.

**If they dig deeper**

Point 3 is a smoke alarm, not a fix. It tells you the invariant broke; it does not repair the data. That is the honest position, and saying so is better than implying the reconciler makes the problem go away.

Also: **prefer soft delete.** A large share of "referential integrity across services" problems are really "someone hard-deleted a row" problems. Set `IsDeleted` and the reference still resolves to something you can display.

**Follow-up to expect:** *"Isn't that weaker than a real FK?"* → Yes, strictly weaker, and that is part of the price of the split. If a particular relationship genuinely cannot tolerate that, it is evidence those two things belong in one service.

📖 [Chapter 6 — The three honest questions](../tutorial/06-boundaries-and-data.md#the-three-honest-questions-this-raises)

</details>

---

<details id="q4">
<summary><b>Q4 · What is an anti-corruption layer?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A translation layer that stops someone else's messy model leaking into yours. You will always have one legacy system with a terrible model — a 20-year-old CRM, a partner's SOAP API, a mainframe export.

The ACL converts their shape into yours in exactly one place.

**If they dig deeper**

Without it, every service ends up knowing that `CUST_STAT_CD = 'Z9'` means "merged into another record", and a legacy change breaks all of them.

With it, one file contains the ugliness:

```csharp
private static CustomerStatus MapStatus(string code) => code switch
{
    "A"        => CustomerStatus.Active,
    "I" or "X" => CustomerStatus.Inactive,
    "Z9"       => CustomerStatus.Merged,   // documented HERE, once
    _          => CustomerStatus.Unknown
};
```

Your domain sees `CustomerStatus.Active`. It never sees `CUST_STAT_CD`. When the legacy system is finally replaced, you change one file.

**Follow-up to expect:** *"Where else would you use one?"* → Any third-party API. The e-commerce payment gateway is an ACL: the provider's `amount_minor`, `failure_code`, and `status: "pending"` all stop at that class, and the rest of the system sees a clean `ChargeResult`.

📖 [Chapter 6 — The anti-corruption layer](../tutorial/06-boundaries-and-data.md#the-anti-corruption-layer)

</details>

---

<details id="q5">
<summary><b>Q5 · What are consumer-driven contract tests?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

The consumer writes a test asserting what it needs from the producer's contract, and that test runs in the **producer's** CI pipeline.

So if the producer renames a field, their build goes red — before deploy — instead of the consumer silently reading `null` in production.

**If they dig deeper**

The problem it solves: the producer's own unit tests prove the producer works. They prove nothing about whether consumers still work.

Even a plain test file, shared and run in the producer's pipeline, catches most contract breaks:

```csharp
// Lives with Payments. Runs in Ordering's CI.
[Fact]
public void Payments_needs_orderId_and_total()
{
    var evt = JsonSerializer.Deserialize<OrderPlaced>(TheJsonOrderingPublishes);
    Assert.NotEqual(Guid.Empty, evt!.OrderId);
    Assert.Equal(49.98m, evt.Total);      // and as a decimal, not a string
}
```

Pact formalises this with a broker and versioning. You do not need Pact to get 90% of the value.

**Follow-up to expect:** *"Why not just integration tests?"* → Integration tests require running both services, so they are slow, flaky, and usually only cover the happy path. A contract test is fast, runs on every commit, and states precisely what the consumer depends on.

📖 [Chapter 6 — Consumer-driven contract tests](../tutorial/06-boundaries-and-data.md#consumer-driven-contract-tests)

</details>

---

<details id="q6">
<summary><b>Q6 · Which contract changes are safe and which are breaking?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

| Change | Safe? |
|---|---|
| Add an optional field | ✅ |
| Add a new event type | ✅ |
| Add an enum value | ⚠️ Only if consumers handle unknown values — most do not |
| Rename a field | ❌ |
| Remove a field | ❌ |
| Change a type | ❌ |
| Make an optional field required | ❌ |
| **Change the meaning of a field** | ❌❌ |

**If they dig deeper**

The last row deserves emphasis in an interview, because it is the one people miss. If `Total` changes from including tax to excluding tax, **nothing fails**. No exception, no build error, no alert. The numbers are simply wrong from that deploy onward, and you find out from finance a month later.

That is why a semantic change must be treated as a new field or a new version, never an edit.

**Follow-up to expect:** *"How do you enforce this?"* → Contract tests catch structural breaks. Semantic ones need discipline: name fields precisely (`TotalIncludingTax`, not `Total`) so a meaning change forces a rename, which the tooling *can* catch.

📖 [Chapter 6 — Safe vs breaking changes](../tutorial/06-boundaries-and-data.md#safe-vs-breaking-changes)

</details>

---

<details id="q7">
<summary><b>Q7 · What belongs in an API gateway, and what does not?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

The line to remember: **the gateway answers "who are you, and where does this go?" The service answers "are you allowed to do this?"**

| Belongs | Does not belong |
|---|---|
| TLS termination | Business logic |
| Authentication (is the token valid?) | Domain authorisation ("can this user cancel this order?") |
| Rate limiting | Aggregating six services into one response — that is a BFF |
| Routing | Data transformation between services |
| Correlation ID creation | Anything a team must edit to ship a feature |

**If they dig deeper**

The last row is the operational one. If shipping a feature means a pull request to the gateway repo, every team queues behind one repo and the gateway becomes a deploy bottleneck. Routes should be generated from service metadata or per-team files — never one hand-edited 3,000-line config.

**Follow-up to expect:** *"Isn't auth at the gateway enough?"* → No. The gateway knows the token is valid. It does not know whether user `u-77` may cancel order `o-123` — only `Ordering` knows that. If the gateway is your only check, one misconfigured internal route exposes everything.

📖 [Chapter 5 — What belongs in a gateway](../tutorial/05-gateway-and-bff.md#what-belongs-in-a-gateway)

</details>

---

<details id="q8">
<summary><b>Q8 · What is a BFF and why would you have more than one?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A Backend For Frontend is a small service that aggregates and shapes responses for **one** kind of client. You have one per client type because their needs genuinely differ.

Web has a big screen and a fast network — it wants everything at once. Mobile has a small screen, a slow network, and a battery — it wants the minimum.

**If they dig deeper**

Same order, two shapes:

```jsonc
// /web/orders/123 — customer, lines with images, payment, shipping, timeline
// /mobile/orders/123 — id, status, total, itemCount, thumbnail, nextAction
```

12× smaller for mobile. If you force one shape on both, one of them suffers — usually mobile, because it is politically easier to add a field for web than to defend a small payload.

**Who owns it: the client team.** That is the point of the pattern. If a platform team owns every BFF, you have rebuilt the bottleneck you were removing.

**Follow-up to expect:** *"What about BFF sprawl — three clients, 70% duplicated code?"* → Share the *clients* and cross-cutting middleware in a library. Keep the *shaping* separate. Sharing the shaping defeats the pattern entirely.

📖 [Chapter 5 — The BFF pattern](../tutorial/05-gateway-and-bff.md#the-bff-pattern)

</details>

---

<details id="q9">
<summary><b>Q9 · A BFF calls four services. How do you keep the page fast and resilient?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Two things:

1. **Fan out in parallel**, not sequentially. Sequential awaits over four services multiply the page time by four.
2. **Classify each dependency as essential or enhancement**, and give the enhancements a fallback.

**If they dig deeper**

The classification is the interesting half, because it encodes a business decision in code:

```csharp
// ESSENTIAL — no basket, no page. No sensible fallback.
var basket = await baskets.GetAsync(basketId, ct);

// Fan out the rest in parallel
var productsTask = catalog.GetBatchAsync(skus, ct);
var stockTask    = inventory.GetBatchAsync(skus, ct);

// ENHANCEMENT — if Inventory is down, hide the stock badge and still sell.
var stock = await Unwrap(stockTask, onFailure: () => null);
```

Which dependencies are allowed to fail is a decision the business must own, written down *before* an incident.

**Follow-up to expect:** *"How do you know when you're serving a degraded page?"* → Return a `Degraded` flag in the response and emit a metric. A fallback that fires silently means nobody notices the stock service has been down for a week.

📖 [Case study 1 — `CheckoutEndpoints.cs`](../case-studies/01-ecommerce/src/Ecommerce.Bff.Web/Endpoints/CheckoutEndpoints.cs)

</details>

---

<details id="q10">
<summary><b>Q10 · How do you push data to a browser, and how does that scale?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Four options: polling, long polling, Server-Sent Events, and WebSockets. SSE for one-way server→client; WebSocket when you need both directions.

The scaling catch: **WebSockets are stateful.** User A is connected to instance 1, but the event that concerns them is handled by instance 2, which has no connection to A. You need a backplane (Redis or a service bus) so any instance can reach any connection.

**If they dig deeper**

Teams discover the backplane requirement on the day they scale from one instance to two, and it presents as "push works locally but not in production".

The other detail that matters: **push to a group, never broadcast.** Each user joins a private group so one customer's order update is never sent to everyone — that is a data-protection incident, not just a bug.

```csharp
await Groups.AddToGroupAsync(Context.ConnectionId, $"user:{userId}");
```

**Follow-up to expect:** *"What is push actually for here?"* → Closing the eventual-consistency gap. The user sees "Processing", and 900 ms later the page updates itself. Without it they refresh, see nothing, and call support.

📖 [Chapter 5 — Server-initiated communication](../tutorial/05-gateway-and-bff.md#server-initiated-communication--the-axis-most-articles-forget)

</details>

---

<details id="q11">
<summary><b>Q11 · You receive webhooks from a payment provider. What are the rules?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Three, all non-negotiable:

1. **Verify the signature.** Anyone on the internet can POST to that URL.
2. **Be idempotent.** Providers retry, aggressively.
3. **Return fast.** Do the real work asynchronously — providers time out in 5–10 seconds and then retry, multiplying your load.

**If they dig deeper**

```csharp
if (!verifier.IsValid(body, signature))  return Results.Unauthorized();
if (!await seen.TryMarkAsync(evt.Id, ct)) return Results.Ok();   // dup → 200, not 409
await bus.Publish(new PspEventReceived(evt.Id, evt.Type, body), ct);
return Results.Ok();
```

Note the duplicate returns **200, not 409**. From the provider's point of view the delivery succeeded; a 4xx makes them retry harder.

**Follow-up to expect:** *"What if the webhook arrives before your own API call has returned?"* → Common, and it catches people out. The provider can call your webhook before your `POST /charges` response arrives. Your code must handle the outcome arriving from either direction, which is another argument for making the state transition idempotent rather than assuming an order of events.

📖 [Chapter 5 — Webhooks](../tutorial/05-gateway-and-bff.md#webhooks--when-bluedart-calls-you)

</details>

---

<details id="q12">
<summary><b>Q12 · Should internal service-to-service calls go through the gateway?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

No. A gateway in the middle of an internal call adds a network hop and a failure point for nothing.

Internal calls go direct (service discovery by logical name) or through the broker. The gateway is for traffic crossing your trust boundary.

**If they dig deeper**

The exception worth mentioning: a **service mesh** does sit in every internal call, but it is a different thing — a sidecar providing mTLS, retries, and telemetry without a central chokepoint. That is per-pod, not a shared hop.

Related, and worth saying unprompted: "inside the trust boundary means no auth needed" is dead as an assumption. Modern practice is service-to-service identity via mTLS or signed tokens. Treat the trust boundary as thin, not absent.

**Follow-up to expect:** *"How does a service find another without hardcoding an IP?"* → A logical name resolved by the platform: Kubernetes DNS, the Docker Compose service name, or a registry. And the address lives in configuration, never in code.

📖 [Chapter 2 — Service discovery](../tutorial/02-synchronous.md#service-discovery)

</details>

---

<details id="q13">
<summary><b>Q13 · Where does authorisation belong?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Split it:

- **Authentication** ("who are you, is this token valid?") → the gateway. Reject bad tokens before they cost a service anything.
- **Authorisation** ("may this user do this to this resource?") → the service that owns the resource. Only `Ordering` knows whether `u-77` may cancel `o-123`.

**If they dig deeper**

Putting domain authorisation in the gateway fails in two ways. It needs data it does not own (which means calling back into services), and it makes the gateway a deploy bottleneck — every permission change becomes a gateway release.

The gateway should pass identity down (a validated token, or claims in a header it controls), and each service decides.

**Follow-up to expect:** *"How do you avoid every service reimplementing permissions?"* → A shared library for *evaluating* a policy is fine; a shared service that *stores* roles and permissions is fine. What must stay local is the decision, because it depends on the resource, and only the owner has it.

📖 [Chapter 5 — Sharp edges](../tutorial/05-gateway-and-bff.md#sharp-edges)

</details>

---

<details id="q14">
<summary><b>Q14 · Your mobile app is two years old and still in use. How do you evolve the API?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Accept that you cannot break `/v1` and plan for versions running side by side for years.

Concretely: additive changes only on the existing version, a new version for anything breaking, and **instrumentation of usage per app version** so you know when it is genuinely safe to retire one.

**If they dig deeper**

This is the sharpest difference between north-south and east-west. An internal API you can refactor on a Tuesday afternoon, because you control both sides and can deploy them together. A mobile contract is effectively permanent — the old version is in someone's pocket and they may never update it.

Tactics that help: force-upgrade prompts for genuinely unsupportable versions, feature flags so new behaviour is server-controlled, and a BFF per client so a mobile-shaped response can evolve without touching web.

**Follow-up to expect:** *"When can you delete v1?"* → When the metric says zero for a sustained period, not when someone believes it is unused. And announce the date well in advance, because a silent removal is an outage for whoever was still on it.

📖 [Chapter 5 — Sharp edges](../tutorial/05-gateway-and-bff.md#sharp-edges)

</details>

---

<details id="q15">
<summary><b>Q15 · What is the ownership table and why do you care?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

One page: every important entity, its **one** owning service, who reads it, how they read it, and who else writes it.

The last column must say **"nobody"** for every row. Any row where it does not is a bug, and those are the rows to fix first.

**If they dig deeper**

| Entity | Owner | Readers | How | Other writers |
|---|---|---|---|---|
| Order | Ordering | Support, Analytics | `OrderPlaced` event | **nobody** |
| Payment | Payments | Ordering, Finance | `PaymentSucceeded` | **nobody** |
| Customer | Customers | Ordering, Support | `CustomerChanged` | ← *if not "nobody", stop* |

It takes an hour to write and prevents years of "who owns this?" archaeology. It is also the artefact that makes symptom 5 of the distributed-monolith checklist ("nobody can name who owns a given entity") impossible.

**Follow-up to expect:** *"How do you keep it accurate?"* → Review direct database access in code review, and treat a new writer as an architectural change requiring a discussion. Boundaries erode one shortcut at a time — a direct query "just this once" for an urgent report, still there three years later.

📖 [Chapter 6 — Try it yourself](../tutorial/06-boundaries-and-data.md#try-it-yourself)

</details>

---

<details id="q16">
<summary><b>Q16 · A team wants to add a shared "Common" library. What do you say?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**The 30-second answer**

It depends entirely on what goes in it.

- **Contracts** (events, DTOs) — yes, and one shared contracts package is the right pattern.
- **Genuinely generic helpers** (a `Result` type, a date utility) — acceptable.
- **Domain models** — no. That is how you get a monolith wearing a NuGet costume.

**If they dig deeper**

The failure mode is gradual and always the same. It starts as `Common.Utilities`. Then `Common.Models`. Then every service depends on it, and changing it means redeploying everything — which is exactly the coordinated deploy you split the services to avoid.

The test I would apply: **can two services be on different versions of this library at the same time?** If yes, it is a library. If no, it is a distributed compile-time dependency, and you have lost independent deployability.

**Follow-up to expect:** *"What about shared infrastructure code — the outbox, retry policies?"* → Genuinely useful and a good candidate, but version it properly and let services upgrade on their own schedule. The moment you need everyone on the same version simultaneously, it has become the problem instead of the solution.

📖 [Chapter 6 — Sharp edges](../tutorial/06-boundaries-and-data.md#sharp-edges)

</details>

---

← [Communication](02-communication.md) · [Interview index](README.md) · Next: [Reliability →](04-reliability.md)
