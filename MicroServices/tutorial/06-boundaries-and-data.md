# Chapter 6 — Boundaries and Data Ownership

← [Chapter 5](05-gateway-and-bff.md) · [Tutorial index](README.md) · Next: [Chapter 7 — Sagas](07-saga.md)

---

## The story so far

The edge is sorted ([chapter 5](05-gateway-and-bff.md)). Then, on an ordinary Tuesday:

```
14:02  Inventory team deploys. Adds a NOT NULL column to a table. Deploy succeeds.
14:21  Ordering starts failing on every insert.
       The Ordering team has not deployed for three days.
14:25  Ordering team is paged. They check their own repo. Nothing changed.
18:40  Four hours later, someone finds it: both services write to the same database.
```

Nobody wrote that down. It worked fine for a year. This chapter is about the axis everyone skips until it does this to them.

---

## In one line

If two services share a database, you have one service with extra network calls.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Bounded context** | A part of the business where words have one clear meaning. |
| **Ubiquitous language** | The exact words the business uses, used in the code too, without translation. |
| **Aggregate** | A cluster of objects saved and changed as one unit. An `Order` with its lines is one aggregate. |
| **Database-per-service** | Each service has its own database. No other service may touch it. |
| **Anti-corruption layer (ACL)** | A translation layer that stops someone else's messy model leaking into yours. |
| **Contract** | The promise your API or event makes about its shape. |
| **Consumer-driven contract test** | The consumer writes a test proving the producer still meets its needs. The producer runs it in CI. |
| **Distributed monolith** | Many deployables that must all change and deploy together. |
| **Read model / projection** | A copy of data, shaped for reading, built from events. |
| **CQRS** | Separating the write path from the read path so each can be shaped for its job. |

---

## Bounded contexts, explained with one word

Take the word **"customer"**. Ask four teams at the store what it means:

| Team | "Customer" means | Fields they care about |
|---|---|---|
| **Ordering** | Who is buying | id, name, shipping address |
| **Payments** | Who is paying | id, billing address, saved cards, currency |
| **Support** | Who needs help | id, ticket history, sentiment, contact preference |
| **Marketing** | Who might buy again | id, segment, campaign history, consent flags |

Here is the important part: **they are all correct.**

The instinct of most developers is to build one `Customer` table with every field and have every service use it. That instinct produces a table with 180 columns where each service uses 12 of them and no team can safely change any of them.

The right answer is that each context has its **own** customer model, with only what it needs, joined by a shared `CustomerId`.

```csharp
// Ordering/Domain/Customer.cs — who is buying
public sealed record Customer(Guid Id, string Name, Address ShippingAddress);

// Payments/Domain/Payer.cs — who is paying. Different name on purpose.
public sealed record Payer(Guid CustomerId, Address BillingAddress,
                           IReadOnlyList<PaymentMethod> Methods, string Currency);

// Support/Domain/Contact.cs — who needs help
public sealed record Contact(Guid CustomerId, string Email, ContactPreference Preference,
                            int OpenTickets, Sentiment LastSentiment);
```

Three models. One shared ID (`c-77` for Priya). Zero coupling. `Payments` can add a payment method type without a meeting.

### How to find your boundaries

Not by drawing boxes on a whiteboard. By asking four questions:

1. **Where does the language change?** If "order" means a shopping basket to one team and a manufacturing job to another, that is a boundary.
2. **What changes together?** Things that always change in the same pull request belong in the same service.
3. **Who owns the decision?** If one team decides the rules for something, that something belongs to their service.
4. **What can be inconsistent for a second?** If two pieces of data must always agree *instantly*, they probably belong in the same service and the same transaction.

**Question 4 is the most practical one.** It converts a fuzzy architecture argument into a business question you can actually ask a product owner:

> *"If the stock count and the order disagreed for two seconds, would that be a problem?"*

At the store the answer was no — a two-second gap is fine, and they apologise for the rare oversell. That single answer told them `Ordering` and `Inventory` are genuinely two services. Had the answer been *"no, they must never disagree"*, they would be one.

---

> **Diagram: D6 — Bounded contexts and data ownership**
> [Mermaid source](../diagrams/README.md#d6--bounded-contexts-and-data-ownership)

---

## Database-per-service

The rule: **one service owns its data. No other service reads or writes it directly. Ever.**

```
✓ CORRECT                              ✗ WHAT THE STORE ACTUALLY HAD
Ordering ──► orders-db                 Ordering ──┐
Inventory ─► inventory-db                         ├──► shared-db
Payments ──► payments-db               Inventory ─┘
```

The wrong version fails in specific, predictable ways — and the store hit every one:

| Failure | What happened on Tuesday |
|---|---|
| A `NOT NULL` column is added | `Ordering`'s inserts start failing. Nobody knows why |
| A slow report query runs | `Inventory` times out. An incident caused by a team they never spoke to |
| Neither can deploy alone | So they deploy together. So they have a monolith |
| Nobody owns the shared tables | So nobody dares change them, so they grow to 180 columns |

### The three honest questions this raises

Every developer asks these. They have real answers.

**Q1. "How do I join across services for a report?"**

You do not join. Pick one:

| Approach | How it works | Best when |
|---|---|---|
| **API composition** | The caller (usually a BFF) calls both and joins in memory | Small result sets, a UI screen |
| **Read model / projection** | A service listens to events and keeps its own denormalised copy | Lists, dashboards, search |
| **Data warehouse** | Everything streams into a warehouse for reporting | Real reporting and BI |

The common mistake is API composition for a report over 50,000 rows — that is 50,000 HTTP calls. **API composition is for a page, not a report.**

**Q2. "How do I keep referential integrity without a foreign key?"**

You accept you cannot have a database-enforced FK across services, and replace it with three things:

1. **Validate on write.** When `Ordering` receives `c-77`, it checks the customer exists (a cached call, or its own local copy).
2. **Handle the missing case at read time.** A deleted customer shows "Customer unavailable", not a crash.
3. **Reconcile.** A nightly job finds orphans and reports them. Not a fix — a smoke alarm.

Also: **prefer soft delete.** Most "referential integrity across services" problems are really "someone hard-deleted a row" problems.

**Q3. "Isn't duplicating data wrong? I was taught normalisation."**

Normalisation is a rule for **one** database, to prevent update anomalies. Across services the trade is different: you accept a copy in exchange for independence.

The rule that keeps it safe: **one writer, many readers.**

```csharp
// Ordering keeps a local, read-only copy of just the fields it needs.
// It NEVER writes this from a user action — only from Customers' events.
public sealed class CustomerSnapshot
{
    public Guid   CustomerId { get; init; }
    public string Name       { get; init; } = "";
    public Address ShippingAddress { get; init; } = null!;
    public DateTime UpdatedAtUtc { get; init; }   // so you can see how stale it is
}

// Updated only by an event. This is the single source of change.
public sealed class CustomerChangedConsumer(OrderingDbContext db) : IConsumer<CustomerDetailsChanged>
{
    public async Task Consume(ConsumeContext<CustomerDetailsChanged> ctx)
    {
        var m  = ctx.Message;
        var it = await db.CustomerSnapshots.FindAsync([m.CustomerId], ctx.CancellationToken);

        if (it is null)
        {
            db.CustomerSnapshots.Add(new CustomerSnapshot
            {
                CustomerId = m.CustomerId, Name = m.Name,
                ShippingAddress = m.ShippingAddress, UpdatedAtUtc = m.OccurredAtUtc
            });
        }
        else if (m.OccurredAtUtc > it.UpdatedAtUtc)   // ignore out-of-order/older events
        {
            db.Entry(it).CurrentValues.SetValues(new
            {
                m.Name, m.ShippingAddress, UpdatedAtUtc = m.OccurredAtUtc
            });
        }

        await db.SaveChangesAsync(ctx.CancellationToken);
    }
}
```

The duplicate is safe because there is exactly one writer (`Customers`, via events) and the local copy is explicitly read-only.

**And the payoff:** `Customers` can be down for an hour and `Ordering` keeps taking orders with slightly stale names. A synchronous call would have made your uptime depend on theirs.

---

## The anti-corruption layer

The store still has a 20-year-old CRM that Marketing refuses to retire. Its model is horrifying.

Do not let its shape into your code.

```csharp
// ✗ WRONG — the legacy model has leaked everywhere.
// Now every service knows CUST_STAT_CD = 'A', and a legacy change breaks all of them.
public class LegacyCustomerRecord
{
    public string CUST_ID      { get; set; }
    public string CUST_NM_1    { get; set; }
    public string CUST_NM_2    { get; set; }
    public string CUST_STAT_CD { get; set; }   // 'A' | 'I' | 'P' | 'X' | 'Z9'
    // …174 more fields
}
```

```csharp
// ✓ CORRECT — one translation layer. The ugliness stops here.
// Infrastructure/Legacy/LegacyCustomerAdapter.cs
public sealed class LegacyCustomerAdapter(ILegacyCrmClient crm) : ICustomerLookup
{
    public async Task<Customer?> FindAsync(Guid customerId, CancellationToken ct)
    {
        var record = await crm.GetCustomerAsync(customerId.ToString("N"), ct);
        if (record is null) return null;

        // Every legacy quirk is explained and contained in this method.
        return new Customer(
            Id:     customerId,
            Name:   Join(record.CUST_NM_1, record.CUST_NM_2),
            Status: MapStatus(record.CUST_STAT_CD),
            ShippingAddress: new Address(record.ADDR_LN_1, record.CITY_NM, record.PSTL_CD));
    }

    private static string Join(string? a, string? b) => $"{a?.Trim()} {b?.Trim()}".Trim();

    // 'Z9' means "merged into another record" — a fact only the legacy team knows.
    // It is documented HERE, once, instead of being rediscovered by five teams.
    private static CustomerStatus MapStatus(string code) => code switch
    {
        "A"        => CustomerStatus.Active,
        "I" or "X" => CustomerStatus.Inactive,
        "P"        => CustomerStatus.PendingVerification,
        "Z9"       => CustomerStatus.Merged,
        _          => CustomerStatus.Unknown
    };
}
```

Your domain sees `Customer` and `CustomerStatus.Active`. It never sees `CUST_STAT_CD`. When the CRM is finally replaced, you change one file.

---

## Contracts and versioning

A contract is the shape you promised. Breaking it is **a production incident with a delay fuse** — it does not fail when you deploy, it fails when a consumer next runs.

### Safe vs breaking changes

| Change | Safe? | Why |
|---|---|---|
| Add an optional field | ✓ | Old consumers ignore it |
| Add a new event type | ✓ | Nobody is subscribed yet |
| Add a value to an enum | ⚠️ | Safe only if consumers handle unknown values. Most do not |
| Rename a field | ✗ | Old consumers read null |
| Remove a field | ✗ | Old consumers read null |
| Change a type (`string` → `int`) | ✗ | Deserialisation fails |
| Make an optional field required | ✗ | Old producers now send invalid messages |
| **Change the meaning of a field** | ✗✗ | **Worst of all.** Nothing fails. Numbers are just wrong from now on |

That last row deserves a store example. Suppose `OrderPlaced.Total` changes from *including* tax to *excluding* tax.

Nothing throws. No build fails. No alert fires. Analytics quietly under-reports revenue by 18% until someone in finance notices a month later.

### How to make a breaking change safely

Never edit the old contract. Add a new version and run both.

```csharp
// Contracts/Events/OrderPlaced.cs — the old one. Leave it alone.
public record OrderPlaced(Guid OrderId, Guid CustomerId, decimal Total);

// Contracts/Events/OrderPlacedV2.cs — the new shape.
// Total is now split, because finance needed tax visible separately.
public record OrderPlacedV2(Guid OrderId, Guid CustomerId,
                            decimal Subtotal, decimal Tax, string Currency);
```

The migration, in order:

1. **Publish both.** The producer emits `OrderPlaced` and `OrderPlacedV2` for every order.
2. **Consumers migrate one by one**, on their own schedule. No coordination meeting.
3. **Measure.** Instrument who still consumes v1. Wait until the count is zero, for real, for a week.
4. **Then** stop publishing v1, and delete it.

This takes weeks. **That is correct.** The alternative is a coordinated big-bang deploy, which is how outages happen.

### Consumer-driven contract tests

The producer's unit tests prove the producer works. They prove nothing about whether consumers still work. So let the consumer write the test:

```csharp
// Payments.Tests/Contracts/OrderPlacedContractTests.cs
// This test lives with the CONSUMER but runs in the PRODUCER's CI pipeline.
// If Ordering renames Total, this fails in Ordering's build — before deploy.
public class OrderPlacedContractTests
{
    [Fact]
    public void Payments_needs_orderId_customerId_and_total()
    {
        // The exact JSON Ordering publishes today
        const string json = """
        {
          "orderId":     "0192f3a1-0000-7000-8000-000000000001",
          "customerId":  "0192f3a1-0000-7000-8000-000000000002",
          "total":       49.98,
          "placedAtUtc": "2026-07-25T10:00:00Z"
        }
        """;

        var evt = JsonSerializer.Deserialize<OrderPlaced>(json, JsonOptions.Web);

        Assert.NotNull(evt);
        Assert.NotEqual(Guid.Empty, evt!.OrderId);      // I need this
        Assert.NotEqual(Guid.Empty, evt.CustomerId);    // and this
        Assert.Equal(49.98m, evt.Total);                // and this, as a decimal
    }
}
```

Tools like Pact formalise this. But even a plain test file, shared and run in the producer's CI, catches 90% of contract breaks for almost no effort.

---

## The distributed monolith checklist

Six symptoms. Three or more and you have one — and adding services will make it worse, not better.

1. **Services must deploy together to work.**
2. **Two services write to the same table.**
3. **One team's schema change breaks another team's build.**
4. **A single user request fans out through six synchronous hops.**
5. **Nobody can name who owns a given entity.**
6. **Local development requires running the entire system.**

The store scored **four out of six** on Tuesday. Symptoms 2, 3, 5, and — once they looked — 1.

### What each one costs, and how to fix it

| # | What it really costs | The fix |
|---|---|---|
| 1 | Deploy risk of a monolith plus complexity of a distributed system | Version your contracts; support N-1 |
| 2 | Silent data corruption, and incidents caused by strangers | One writer. Others read via API or events |
| 3 | Cross-team blocking, and fear of change | Database-per-service; contract tests |
| 4 | Latency = sum of hops; availability = product of hops | Make hops async, or merge the services |
| 5 | Every change needs an archaeology session | Write an ownership table. One page. Today |
| 6 | 30-minute onboarding becomes 3 days | Contract tests + stubs, so one service runs alone |

**Symptom 6 is the best early warning.** If a new developer cannot run one service alone and do useful work, your boundaries are wrong — and you will feel it in every deploy afterwards.

---

## Sharp edges

**Edge 1 — Splitting too early.** A monolith with clear internal modules is much better than five services with tangled boundaries. You learn where the real seams are by *operating* the system. Start with a modular monolith and extract the service you can prove needs to scale, deploy, or fail independently.

**Edge 2 — Splitting by technical layer instead of business capability.** A "database service", an "API service", and a "business logic service" is the worst possible split: every feature touches all three, so nothing deploys independently. Split **vertically**, by capability.

**Edge 3 — The shared "Common" library that eats everything.** It starts as `Common.Utilities`. Then `Common.Models`. Then every service depends on it, and changing it means redeploying everything. **You have recreated the monolith as a NuGet package.** Share *contracts* (events, DTOs) and genuinely generic helpers. Never share domain models.

**Edge 4 — Nobody owns the boundary.** Boundaries erode one shortcut at a time — a direct query "just this once" for an urgent report, still there three years later. Make the ownership table a real document, and review direct-database access in code review.

**Edge 5 — Events that are really just table rows.** Publishing `CustomerRowChanged { …all 180 columns… }` is database replication with extra steps, and consumers now depend on your schema. Publish *business* events — `CustomerMovedHome`, `CustomerUpgradedToGold` — that say what happened, in business language.

---

## When to split, when not to

**Split when you can name the reason:**

| Reason | Store example |
|---|---|
| Different scaling needs | Product search gets 1000× the traffic of order placement |
| Different failure tolerance | Checkout must stay up; recommendations may not |
| Different release cadence | Pricing ships hourly; the ledger ships monthly with sign-off |
| Different team ownership | A separate team with its own roadmap and on-call rota |
| Different compliance scope | Card data isolated so the PCI audit covers one small service |

**Do not split when:**

| Reason not to | Why |
|---|---|
| "Microservices are best practice" | Not a reason. Name what you are buying |
| The boundary is unclear | You will get it wrong and pay a data migration to undo it |
| Data must be strongly consistent across both halves | You are choosing a distributed transaction over a local one, for nothing |
| Your team is 4 people with 12 services | You will spend your life on operations, not features |
| Only to reuse code | That is a library, not a service |

---

## Try it yourself

**The ownership table.** For your system, fill this in — one row per important entity. It takes an hour and prevents years of confusion:

| Entity | Owning service | Who else reads it | How they read it | Who else *writes* it |
|---|---|---|---|---|
| Order | Ordering | Support, Analytics, Shipping | `OrderPlaced` event | **nobody** |
| StockLevel | Inventory | BFF (display only) | `GET /stock` | **nobody** |
| Payment | Payments | Ordering, Finance | `PaymentSucceeded` event | **nobody** |
| Customer | Customers | Ordering, Support, Marketing | `CustomerChanged` event | ← *if this is not "nobody", stop and fix it* |

**Any row where the last column is not "nobody" is a bug.** Fix those first.

**Now break it:**

1. Try to add a foreign key from `Orders.CustomerId` to a table in another service's database. You cannot — different database. **That constraint is the pattern working as intended.**
2. Make `Customers` publish an event on change and `Ordering` keep a local snapshot. Now stop `Customers` entirely. Notice `Ordering` still works with slightly stale data. *That is the independence you paid for.*
3. Rename a field in an event without versioning it. Watch the consumer silently read `null`, and note that **nothing throws**. That silence is why breaking changes are dangerous.
4. Write a consumer-driven contract test. Rename the field again. Watch the producer's build go red before deploy. *That is the safety net.*
5. Try to run **one** service locally, alone, and do something useful. If you cannot, list what stopped you. **That list is your boundary backlog.**

---

## What is still broken

The store splits the database. Each service gets its own. Contract tests go into CI. The ownership table goes on the wall.

Then a subtler bug appears — one that has probably been happening for months without anyone noticing.

Priya orders 2 mice. `Inventory` reserves them. `Payments` tries her card, and it **declines** — she has hit her credit limit.

The order is marked failed. Priya gets an email. Everything looks handled.

But nobody told `Inventory`. **Those 2 mice are still reserved.** They are not on sale, and they are not sold. They are simply gone.

Multiply by every declined card, every day. Someone in the warehouse eventually asks why the system says 0 in stock when there are 340 on the shelf.

You cannot roll back across services. So what *do* you do? That is the next chapter.

---

← [Chapter 5](05-gateway-and-bff.md) · [Tutorial index](README.md) · Next: [Chapter 7 — Sagas](07-saga.md)
