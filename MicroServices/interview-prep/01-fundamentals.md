# 1 — Fundamentals

← [Interview index](README.md) · Next: [Communication →](02-communication.md)

12 questions. Answer in your head first, then expand.

---

<details id="q1">
<summary><b>Q1 · What is a microservice?</b> &nbsp;·&nbsp; <code>Junior</code></summary>

**The 30-second answer**

A service you can deploy on its own, that owns its own data, and that does one job for the business.

The important word is **own**. If it shares a database with another service, it is not a microservice — it is a module with a network call in front of it.

**If they dig deeper**

Three properties, and all three must hold:

1. **Independently deployable** — you can ship it on a Tuesday without coordinating with another team.
2. **Owns its data** — no other service reads or writes its tables.
3. **A business capability, not a technical layer** — `Ordering`, not `DataAccessService`.

Size is not one of the properties. "Micro" is misleading — a service should be as big as the business capability it owns. Some are 500 lines, some are 50,000.

**Follow-up to expect:** *"So how small should a service be?"* → Small enough that one team owns it comfortably, big enough that it does not need a synchronous call to another service to answer a normal request.

📖 [Chapter 1 — The three axes](../tutorial/01-three-axes.md)

</details>

---

<details id="q2">
<summary><b>Q2 · When would you NOT use microservices?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

Most of the time, honestly. Specifically when:

- You cannot clearly say where the boundaries are yet.
- The team is small — 4 people with 12 services spend their lives on operations, not features.
- The data needs to be strongly consistent across the split. You would be choosing a distributed transaction over a local one, for nothing.
- You only want to reuse code. That is a library, not a service.

**If they dig deeper**

The honest framing: microservices are a **trade**, not an upgrade. You buy independent deployment, independent scaling, and independent failure. You pay with network latency, eventual consistency, distributed debugging, and operational overhead.

If you cannot name what you are buying, you are only paying.

The default I would recommend: **start with a modular monolith.** Keep clean module boundaries inside one deployable. Extract a service when you can point at a specific reason — this module needs to scale differently, or fail differently, or be owned by a different team.

**Follow-up to expect:** *"But isn't it harder to split later?"* → Somewhat, yes. But splitting on the wrong boundary is much more expensive than splitting late, because undoing it is a data migration plus a code change plus a coordinated deploy. You learn the real seams by operating the system.

📖 [Chapter 6 — When to split, when not to](../tutorial/06-boundaries-and-data.md#when-to-split-when-not-to)

</details>

---

<details id="q3">
<summary><b>Q3 · What is a distributed monolith, and how do you know you have one?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A system with all the operational cost of microservices and none of the benefit. Many deployables that still have to change and deploy together.

You get one by splitting the code without splitting the ownership.

**If they dig deeper**

Six symptoms. Three or more and you have one:

1. Services must deploy together to work.
2. Two services write to the same table.
3. One team's schema change breaks another team's build.
4. A single request fans out through six synchronous hops.
5. Nobody can name who owns a given entity.
6. Local development requires running the entire system.

**Symptom 6 is the best early warning.** If a new developer cannot run one service alone and do useful work, the boundaries are wrong — and you will feel it in every deploy afterwards.

**Follow-up to expect:** *"How would you fix one?"* → Not by adding more services. Start with the ownership table: one row per entity, one owning service, and "who else writes this" must be *nobody*. Fix those rows first, because shared writes are the root of most of the other symptoms.

📖 [Chapter 6 — The distributed monolith checklist](../tutorial/06-boundaries-and-data.md#the-distributed-monolith-checklist)

</details>

---

<details id="q4">
<summary><b>Q4 · What are the three axes of microservice communication?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

- **East-west** — your service calling your service, inside the trust boundary.
- **North-south** — the outside world talking to your system, crossing the trust boundary.
- **The boundary itself** — where you drew the lines and who owns which data.

Most teams obsess over the first, under-invest in the second, and skip the third. Skipping the third is what produces a distributed monolith.

**If they dig deeper**

North-south differs from east-west in every way that matters: you cannot trust the caller, you cannot change the caller (an old mobile app is in someone's pocket for two years), the network is slow and unreliable, and the contract is effectively permanent.

The third axis is not a network call at all — it is a modelling decision, and it is the most expensive one to change later.

**Follow-up to expect:** *"Why is the boundary the hardest?"* → Because moving it is a data migration, not a refactor. Code you can change on a Tuesday; changing which service owns a table is a project.

📖 [Chapter 1 — The three axes](../tutorial/01-three-axes.md#the-three-axes)

</details>

---

<details id="q5">
<summary><b>Q5 · How do you decide where to draw service boundaries?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Not by drawing boxes on a whiteboard. By asking four questions:

1. **Where does the language change?** If "order" means a basket to one team and a manufacturing job to another, that is a boundary.
2. **What changes together?** Things that always change in the same pull request belong together.
3. **Who owns the decision?** If one team decides the rules for something, it belongs to their service.
4. **What can be inconsistent for a second?** If two things must agree *instantly*, they probably belong in one service and one transaction.

**If they dig deeper**

Question 4 is the most practical, because it converts a fuzzy architecture argument into a business question you can actually ask a product owner: *"If the stock count and the order disagreed for two seconds, would that be a problem?"*

The answer tells you whether you have one service or two.

The classic mistake is splitting by **technical layer** — a "database service", an "API service", a "business logic service". Every feature then touches all three, so nothing deploys independently. Split **vertically**, by business capability.

**Follow-up to expect:** *"What if you get it wrong?"* → You will, somewhere. Merging two services back together is a legitimate and underused fix. It is usually cheaper than building a saga to paper over a bad boundary.

📖 [Chapter 6 — How to find your boundaries](../tutorial/06-boundaries-and-data.md#how-to-find-your-boundaries)

</details>

---

<details id="q6">
<summary><b>Q6 · What does "independently deployable" actually require?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Four things, and most teams have only the first:

1. Its own deployment pipeline.
2. Its own database — no shared schema.
3. **Backwards-compatible contracts** — you can deploy version N+1 while consumers still run N.
4. No shared library that forces a coordinated release.

**If they dig deeper**

Point 3 is where most teams fail. "Independently deployable" means the *old* version of every consumer must keep working after you deploy. That requires additive-only changes, or running two contract versions side by side.

Point 4 is the quiet one. A `Common.Models` NuGet package that every service depends on has recreated the monolith — changing it means redeploying everything. Share *contracts* (events and DTOs). Never share domain models.

**Follow-up to expect:** *"How do you prove it works?"* → Consumer-driven contract tests. The consumer writes a test asserting what it needs; the test runs in the *producer's* CI. A breaking change then fails the producer's build rather than production.

📖 [Chapter 6 — Contracts and versioning](../tutorial/06-boundaries-and-data.md#contracts-and-versioning)

</details>

---

<details id="q7">
<summary><b>Q7 · Monolith first, or microservices from day one?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Modular monolith first, in almost every case. You do not know where the boundaries are until you have operated the system, and a wrong boundary is far more expensive than a late split.

The exception: when a boundary is already obvious and non-negotiable — a different compliance scope, a different team with its own roadmap, or a component with wildly different scaling needs.

**If they dig deeper**

The crucial detail is **modular**. "Monolith first" fails when people hear it as "one big ball of mud first, tidy it later". If the modules inside the monolith are tangled, extracting a service is just as hard as it would have been.

Enforce module boundaries inside the monolith — separate projects, no cross-module database access, communication through interfaces. Then extraction is mostly mechanical.

**Follow-up to expect:** *"When do you extract the first one?"* → When you can name the reason in one sentence: this needs to scale separately, fail separately, deploy separately, or be owned by a different team. "It feels too big" is not a reason.

📖 [Chapter 6 — When to split, when not to](../tutorial/06-boundaries-and-data.md#when-to-split-when-not-to)

</details>

---

<details id="q8">
<summary><b>Q8 · Two services need the same data. What do you do?</b> &nbsp;·&nbsp; <code>Mid</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

First, work out whether both **write** it or only one writes and the other reads.

- **One writer, one reader** → the owner exposes an API and publishes events. The reader keeps a local read-only copy if it needs speed.
- **Both write it** → the boundary is wrong. Merge the services, or split the data so each part has exactly one owner.

**If they dig deeper**

The rule is **one writer, many readers**. A local copy is fine — it is not a normalisation violation, because normalisation is a rule for one database, not across services.

What makes the copy safe is that it is updated *only* by the owner's events, never by a user action in the consuming service:

```csharp
// Ordering keeps a read-only snapshot, written ONLY by CustomerChanged events
public sealed class CustomerSnapshot
{
    public Guid CustomerId { get; init; }
    public string Name { get; init; } = "";
    public DateTime UpdatedAtUtc { get; init; }   // so you can see how stale it is
}
```

**Follow-up to expect:** *"Isn't that duplicated data?"* → Yes, deliberately. You trade a copy for independence: `Ordering` keeps working when `Customers` is down. The alternative is a synchronous call that makes your uptime depend on theirs.

📖 [Chapter 6 — The three honest questions this raises](../tutorial/06-boundaries-and-data.md#the-three-honest-questions-this-raises)

</details>

---

<details id="q9">
<summary><b>Q9 · What did you actually gain by splitting into microservices?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

If you cannot name it specifically, you gained nothing. Legitimate answers:

| Gained | Example |
|---|---|
| Independent scaling | Search gets 1000× the traffic of checkout |
| Independent failure | Checkout must stay up; recommendations may not |
| Independent release cadence | Pricing ships hourly; the ledger ships monthly with sign-off |
| Team autonomy | A separate team with its own roadmap and on-call rota |
| Compliance isolation | Card data in one small service, so the PCI audit scope is small |
| Technology fit | Market-data ingestion in Rust, the rest in C# |

**If they dig deeper**

Notice what is *not* on that list: "cleaner code", "modern architecture", "easier to understand". Those are properties of good modularity, and you can have them in a monolith for free.

This question is often a trap to see whether you will oversell. The strong answer names the cost too: network latency, eventual consistency, distributed debugging, and roughly N times the operational surface.

**Follow-up to expect:** *"Was it worth it on your last project?"* → Answer honestly. "For two of the six services, clearly yes. The other four should probably have stayed in the monolith" is a much stronger answer than uniform enthusiasm.

📖 [Chapter 6 — When to split, when not to](../tutorial/06-boundaries-and-data.md#when-to-split-when-not-to)

</details>

---

<details id="q10">
<summary><b>Q10 · How does availability change when you add synchronous dependencies?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

It multiplies, and it gets worse fast.

Four synchronous dependencies at 99.9% each:

```
0.999⁴ = 0.996  →  about 3.5 hours of downtime a month,
                   caused entirely by other people's services
```

Latency behaves the same way, but it **adds**: five hops at 50 ms is a 250 ms floor before any real work happens.

**If they dig deeper**

The one-line version worth memorising:

> In a synchronous chain, latency is the **sum** and availability is the **product**. Both get worse with every hop.

Which is why the fix is usually not "make each hop faster" but "make the hop asynchronous, or remove it". An async hop takes your dependency's uptime out of your own availability calculation entirely.

**Follow-up to expect:** *"So how do you avoid the multiplication?"* → Three ways: make the call async so the dependency being down does not fail you; add a fallback so a failure is degraded rather than fatal; or merge the services if they genuinely cannot function apart.

📖 [Chapter 2 — Edge 2: latency compounds](../tutorial/02-synchronous.md#edge-2--latency-compounds)

</details>

---

<details id="q11">
<summary><b>Q11 · What is a bounded context?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A part of the business where a word has exactly one meaning.

"Customer" means four different things to four teams — who is buying, who is paying, who needs help, who might buy again. Each of those is a bounded context, and each should have its own customer model with only the fields it needs.

**If they dig deeper**

The instinct to build one `Customer` table with every field produces a table with 180 columns where each service uses 12 and nobody can safely change any of them.

The right answer is three small models joined by a shared `CustomerId`:

```csharp
// Ordering — who is buying
public sealed record Customer(Guid Id, string Name, Address ShippingAddress);

// Payments — who is paying. Different name on purpose.
public sealed record Payer(Guid CustomerId, Address BillingAddress, IReadOnlyList<PaymentMethod> Methods);

// Support — who needs help
public sealed record Contact(Guid CustomerId, string Email, int OpenTickets);
```

**Follow-up to expect:** *"How do you keep them in sync?"* → You mostly do not, and that is the point. Each context owns its own fields. Anything genuinely shared is published as an event by its one owner.

📖 [Chapter 6 — Bounded contexts explained with one word](../tutorial/06-boundaries-and-data.md#bounded-contexts-explained-with-one-word)

</details>

---

<details id="q12">
<summary><b>Q12 · Your team of five owns fifteen services and struggles to keep up. What do you do?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**The 30-second answer**

Merge some. Fifteen services for five people is roughly three services per person of deployment pipelines, dashboards, alerts, dependency upgrades, and on-call surface.

I would find the services that always change together and combine them, because that pairing is direct evidence the boundary was wrong.

**If they dig deeper**

Merging services is treated as an admission of failure, which is why teams keep suffering instead. It is a legitimate refactor and usually the cheapest available fix.

How I would pick candidates, in order:

1. **Services that always deploy together** — the boundary is not real.
2. **Services with a single synchronous consumer** and no independent scaling need — that is a library in disguise.
3. **Services with no independent failure requirement** — if A is useless when B is down, they can be one thing.

What I would *not* do is add a platform team to manage the overhead. That treats the symptom and makes the headcount problem worse.

**Follow-up to expect:** *"How do you convince the team?"* → Measure it. Count hours spent on operations versus features for a month. The number is usually persuasive on its own, and it turns an architectural taste argument into a cost conversation.

📖 [Chapter 6 — Sharp edges](../tutorial/06-boundaries-and-data.md#sharp-edges)

</details>

---

← [Interview index](README.md) · Next: [Communication →](02-communication.md)
