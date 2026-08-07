# 60 · Concept: Most-Used Design Principles & Patterns (30 questions)

[← SOLID Principles](59-concept-solid-principles.md) · [Home](README.md) · [Next → React Performance Tuning](61-concept-react-performance.md)

This file explains the **design principles and patterns I actually use** — beyond SOLID — in simple English and real depth. I answer from projects A–E, where these principles kept the reporting platform (A), RAG framework (B) and microservices (C) simple, reusable and changeable.

> Simple one-liner: *"Principles tell me *why* one design is better; patterns are *named solutions* to problems that keep recurring. I use the few that pay off daily and skip cleverness for its own sake."*

## Concepts first — the whole idea before the questions

**Principles vs patterns.** A **principle** is a rule of thumb about good design (DRY, KISS, YAGNI, separation of concerns). A **pattern** is a *named, reusable solution* to a recurring problem (Strategy, Factory, Repository). Principles guide judgement; patterns give you a proven shape when a familiar problem appears.

**The everyday analogy.** Principles are like healthy-eating rules ("eat your vegetables, don't overeat"). Patterns are like recipes — proven combinations you reach for when you recognise the situation. You don't cook every meal from a recipe, and you don't force a recipe where a sandwich will do.

**The principles I lean on most:**

| Principle | One-line meaning |
|-----------|------------------|
| **DRY** | Don't repeat yourself — one source of truth |
| **KISS** | Keep it simple — the simplest thing that works |
| **YAGNI** | You aren't gonna need it — don't build for imagined futures |
| **Separation of Concerns** | Keep unrelated responsibilities apart |
| **Composition over inheritance** | Build from parts, not deep class trees |
| **Law of Demeter** | Talk to your neighbours, not strangers |
| **Fail fast** | Detect and surface errors early |
| **Convention over configuration** | Sensible defaults over endless setup |

**The pattern families (Gang of Four):** **Creational** (how objects are made — Factory, Builder, Singleton), **Structural** (how objects are composed — Adapter, Decorator, Facade), and **Behavioural** (how objects interact — Strategy, Observer, Command). Plus enterprise patterns I use constantly: **Repository**, **Unit of Work**, **Dependency Injection**, **CQRS**, **Circuit Breaker**.

**The coach's rule:** *reach for a pattern when you recognise its problem — never to look clever.* A pattern used where the problem doesn't exist is just complexity with a fancy name.

**Jump to:** [DP1 Principle vs pattern](#dp1--principle-vs-pattern) · [DP2 DRY](#dp2--dry) · [DP3 KISS](#dp3--kiss) · [DP4 YAGNI](#dp4--yagni) · [DP5 SoC](#dp5--separation-of-concerns) · [DP6 Composition over inheritance](#dp6--composition-over-inheritance) · [DP7 Law of Demeter](#dp7--law-of-demeter) · [DP8 Fail fast](#dp8--fail-fast) · [DP9 Convention over config](#dp9--convention-over-configuration) · [DP10 Pattern families](#dp10--the-three-pattern-families)
> [DP11 Strategy](#dp11--strategy-pattern) · [DP12 Factory](#dp12--factory-pattern) · [DP13 Singleton](#dp13--singleton-pattern) · [DP14 Builder](#dp14--builder-pattern) · [DP15 Adapter](#dp15--adapter-pattern) · [DP16 Decorator](#dp16--decorator-pattern) · [DP17 Facade](#dp17--facade-pattern) · [DP18 Observer](#dp18--observer-pattern) · [DP19 Command](#dp19--command-pattern) · [DP20 Repository](#dp20--repository-pattern)
> [DP21 Unit of Work](#dp21--unit-of-work) · [DP22 DI pattern](#dp22--dependency-injection-pattern) · [DP23 CQRS](#dp23--cqrs) · [DP24 Circuit breaker](#dp24--circuit-breaker) · [DP25 Anti-patterns](#dp25--anti-patterns-to-avoid) · [DP26 Over-using patterns](#dp26--the-danger-of-over-using-patterns) · [DP27 Patterns in microservices](#dp27--patterns-in-microservices) · [DP28 Patterns in front-end](#dp28--patterns-in-front-end) · [DP29 Choosing a pattern](#dp29--how-do-you-choose-a-pattern) · [DP30 My approach](#dp30--my-approach) · [Section index](#section-index)

---

## DP1 · Principle vs pattern

**Simple explanation.** A **principle** is a guideline (DRY, KISS). A **pattern** is a named, reusable solution to a recurring problem (Strategy, Repository). Principles tell me *why*; patterns give me a proven *how* when I recognise the problem.

**Follow-ups**
- *"Which first?"* — Principles — they let you judge when a pattern helps or hurts.
- *"Must I memorise all patterns?"* — No — know the common dozen and *why* they exist.

---

## DP2 · DRY

**Simple explanation.** **DRY (Don't Repeat Yourself):** every piece of knowledge has **one authoritative source**. Duplicated logic means duplicated bugs and drift. I extract shared logic to one place — like the reusable controller+API pattern on TCW (A).

**Follow-ups**
- *"Can DRY go wrong?"* — Yes — coupling unrelated things that merely *look* similar; prefer a little duplication over the wrong abstraction.
- *"DRY vs copy-paste?"* — Copy-paste is fine to *discover* a pattern; extract once it's real.

---

## DP3 · KISS

**Simple explanation.** **KISS (Keep It Simple):** choose the **simplest design that works**. Complexity is a cost paid on every future change. I add structure only when the problem needs it — the "most boring technology that meets the constraint."

**Follow-ups**
- *"Simple vs easy?"* — Simple = few moving parts (aim for this); easy = familiar (not the same).
- *"When add complexity?"* — Only when a real requirement forces it.

---

## DP4 · YAGNI

**Simple explanation.** **YAGNI (You Aren't Gonna Need It):** don't build features or flexibility for an imagined future. Build for today's requirement; add the seam later *if* it's cheap. Speculative generality is a top source of waste.

*"I keep decisions reversible so I can add flexibility when it's actually needed — not before."*

**Follow-ups**
- *"YAGNI vs extensibility?"* — Keep it reversible (interfaces where change is *likely*), but don't pre-build unused features.
- *"Cost of ignoring it?"* — Complexity nobody uses that everyone maintains.

---

## DP5 · Separation of Concerns

**Simple explanation.** **SoC:** keep unrelated responsibilities in separate modules/layers — UI, business logic, data access. It's SRP at the architecture level. My layered APIs (controller → service → repository) are SoC in action.

**Follow-ups**
- *"Benefit?"* — Change one concern without disturbing others; test each in isolation.
- *"Front-end?"* — Separate presentational components from data/logic (hooks/services).

---

## DP6 · Composition over inheritance

**Simple explanation.** Prefer **building behaviour from small parts** (composition) over deep **inheritance** trees. Inheritance is rigid and can break LSP; composition is flexible and swappable. "Has-a" beats "is-a" for most reuse.

**Follow-ups**
- *"Why avoid deep inheritance?"* — Fragile base-class problem; changes ripple down.
- *"React example?"* — Compose components/hooks rather than inheriting.

---

## DP7 · Law of Demeter

**Simple explanation.** **Law of Demeter ("don't talk to strangers"):** a method should call only its own fields, parameters and objects it creates — not reach through chains like `a.b.c.d()`. Long chains couple you to internal structure.

**Follow-ups**
- *"Smell?"* — Train-wreck calls `order.Customer.Address.City`.
- *"Fix?"* — Ask the immediate object for what you need (`order.ShippingCity`).

---

## DP8 · Fail fast

**Simple explanation.** **Fail fast:** detect invalid state/inputs **early** and surface a clear error, rather than limping on and failing confusingly later. Pydantic validation at the ETL boundary (A) and guard clauses are fail-fast in practice.

**Follow-ups**
- *"Where?"* — At boundaries — validate inputs the moment they arrive.
- *"Benefit?"* — Bugs surface near their cause, cheaper to fix.

---

## DP9 · Convention over configuration

**Simple explanation.** **Convention over configuration:** provide sensible **defaults** so developers configure only the exceptions. ASP.NET Core routing and EF Core conventions mean less boilerplate. Less config = fewer mistakes and faster onboarding.

**Follow-ups**
- *"Trade-off?"* — Less explicit; mitigate with clear, documented conventions.
- *"Example?"* — Framework routing/naming defaults you rarely override.

---

## DP10 · The three pattern families

**Simple explanation.** GoF patterns group into **Creational** (making objects — Factory, Builder, Singleton), **Structural** (composing objects — Adapter, Decorator, Facade), and **Behavioural** (object interaction — Strategy, Observer, Command). The family hints at the kind of problem it solves.

**Follow-ups**
- *"Most-used family?"* — Behavioural (Strategy) and enterprise patterns (Repository/DI).
- *"Memorise all 23?"* — No — know the common ones and their intent.

---

## DP11 · Strategy pattern

**Simple explanation.** **Strategy:** define a family of interchangeable algorithms behind an interface and pick one at runtime. It's how I satisfy OCP — a new report generator or pricing rule is a new strategy, no edits to existing code.

```csharp
interface IPricingStrategy { decimal Price(Order o); }
// StandardPricing, PremiumPricing… chosen at runtime
```

**Follow-ups**
- *"Replaces what?"* — A growing `switch` on type.
- *"Links to?"* — OCP ([file 59 SP5](59-concept-solid-principles.md#sp5--openclosed-principle)).

---

## DP12 · Factory pattern

**Simple explanation.** **Factory:** centralise *object creation* so callers ask for what they need by intent, not by `new`-ing a concrete class. It supports DIP and OCP — add a new type in the factory, callers don't change.

**Follow-ups**
- *"Factory vs DI container?"* — A container is a general factory; a custom factory encodes creation logic.
- *"When?"* — When creation is complex or must vary by input.

---

## DP13 · Singleton pattern

**Simple explanation.** **Singleton:** one shared instance for the app (e.g. a config or cache). Useful but often overused and hard to test if it hides global state. In .NET I prefer a **singleton lifetime in the DI container** over a hand-rolled singleton.

**Follow-ups**
- *"Risk?"* — Global state, hidden dependencies, test pain.
- *"Better way?"* — Register as singleton in DI so it's still injectable/testable.

---

## DP14 · Builder pattern

**Simple explanation.** **Builder:** construct a complex object step by step, keeping construction readable and immutable-friendly. Good when an object has many optional parts (e.g. building a complex query or a report config).

**Follow-ups**
- *"Vs big constructor?"* — Avoids telescoping constructors with many params.
- *"Fluent API?"* — Builders often read as fluent chains.

---

## DP15 · Adapter pattern

**Simple explanation.** **Adapter:** wrap an incompatible interface so it fits what your code expects. I use it to put a third party (Aladdin API, a bought product) behind *my* interface — supporting DIP and reversibility.

**Follow-ups**
- *"Real use?"* — Wrapping the Aladdin client behind an `ISource` my ETL understands.
- *"Links to?"* — DIP and the reversible-path filter.

---

## DP16 · Decorator pattern

**Simple explanation.** **Decorator:** add behaviour to an object by wrapping it, without changing the original — e.g. wrap a repository with caching or logging. Pure OCP: new behaviour by composition, not modification.

```csharp
// CachingRepository wraps IRepository, adds caching, same interface
```

**Follow-ups**
- *"Vs inheritance?"* — Composable at runtime; stackable (cache + log + retry).
- *"Example?"* — Cross-cutting concerns like caching/logging/retry.

---

## DP17 · Facade pattern

**Simple explanation.** **Facade:** a simple front door over a complex subsystem. My RAG orchestration exposes one `Ask(question)` method that hides retrieve → re-rank → assemble → generate → validate. Callers get simplicity; complexity stays contained.

**Follow-ups**
- *"Benefit?"* — Simple client API; internals can change freely.
- *"Vs Adapter?"* — Facade simplifies many parts; Adapter converts one interface.

---

## DP18 · Observer pattern

**Simple explanation.** **Observer:** objects subscribe to events and get notified when something changes — decoupling publisher from subscribers. It underlies event-driven systems, UI events, and message/pub-sub (Kafka, Redis pub/sub).

**Follow-ups**
- *"Real-world?"* — Event-driven microservices; C# events; RxJS in Angular.
- *"Benefit?"* — Publisher doesn't know its subscribers — low coupling.

---

## DP19 · Command pattern

**Simple explanation.** **Command:** wrap a request as an object (with its data), so you can queue, log, retry or undo it. It's the shape behind task queues, CQRS commands, and background jobs.

**Follow-ups**
- *"Use?"* — Queued/background work, undo, audit logs.
- *"Links to?"* — CQRS commands ([DP23](#dp23--cqrs)).

---

## DP20 · Repository pattern

**Simple explanation.** **Repository:** an abstraction over data access so business logic works with a collection-like interface, not raw SQL/EF. Supports SRP (data concern isolated), DIP (depend on `IRepository`), and testing (swap a fake).

**Follow-ups**
- *"Over EF Core?"* — EF's DbSet is already a repository; add one only for real abstraction value, not by reflex.
- *"Benefit?"* — Swappable data source; testable logic.

---

## DP21 · Unit of Work

**Simple explanation.** **Unit of Work:** track changes across repositories and commit them as **one transaction**. EF Core's `DbContext` is a Unit of Work — `SaveChanges` commits everything atomically. Keeps data consistent.

**Follow-ups**
- *"EF example?"* — `DbContext` = UoW + repositories.
- *"Why?"* — All-or-nothing writes; consistency ([file 64](64-concept-sql-performance.md)).

---

## DP22 · Dependency Injection pattern

**Simple explanation.** **DI:** supply a class's dependencies from outside (usually constructor) instead of creating them inside. It's the practical way to achieve DIP — decoupled, testable, swappable code. Built into .NET.

**Follow-ups**
- *"Constructor vs property injection?"* — Constructor — dependencies are explicit and required.
- *"Links to?"* — DIP ([file 59 SP13](59-concept-solid-principles.md#sp13--dip-vs-dependency-injection)).

---

## DP23 · CQRS

**Simple explanation.** **CQRS (Command Query Responsibility Segregation):** separate the **write** model (commands) from the **read** model (queries), because they often have different shapes, scale and consistency needs. My SQL/Snowflake split (A) is CQRS-flavoured — writes/operational vs reads/analytical.

**Follow-ups**
- *"Always split storage?"* — No — CQRS can be just separate code paths; separate stores only when justified.
- *"Cost?"* — More moving parts; use when read/write needs truly diverge.

---

## DP24 · Circuit breaker

**Simple explanation.** **Circuit breaker:** after repeated failures calling a dependency, "trip" and fail fast for a while instead of hammering a dead service, then test-recover. It protects against cascading failure — I use Polly in .NET for this.

**Follow-ups**
- *"With retry?"* — Yes — retry with backoff + circuit breaker + timeout together ([file 63](63-concept-webapi-performance.md)).
- *"Where critical?"* — Microservices and third-party calls (Aladdin).

---

## DP25 · Anti-patterns to avoid

**Simple explanation.** Common anti-patterns: **God object** (does everything), **spaghetti code** (no structure), **golden hammer** (one tool for everything), **premature optimisation**, **magic numbers/strings**, and **anemic domain** taken too far. Naming them helps me spot and avoid them.

**Follow-ups**
- *"Most common?"* — God objects and premature optimisation.
- *"Fix a god object?"* — Split by responsibility (SRP), extract collaborators.

---

## DP26 · The danger of over-using patterns

**Simple explanation.** Patterns add indirection. Used where the problem doesn't exist, they're **complexity theatre** — harder to read, not more flexible. I apply a pattern only when I recognise its exact problem and the simpler option would hurt.

*"A factory that makes one thing, an interface with one impl that will never grow — that's cost without benefit."*

**Follow-ups**
- *"How avoid?"* — Start simple (KISS/YAGNI); introduce a pattern when a real pain appears.
- *"Sign of overuse?"* — Ten files to follow one simple call.

---

## DP27 · Patterns in microservices

**Simple explanation.** Microservices have their own patterns: **API Gateway**, **Circuit Breaker**, **Saga** (distributed transactions), **Strangler Fig** (incremental migration), **Sidecar**, **Event Sourcing**, **Database-per-service**. These solve distribution problems, not object problems ([file 65](65-concept-microservices-performance.md)).

**Follow-ups**
- *"Saga?"* — Coordinate a multi-service transaction via events + compensations, since you can't use one DB transaction.
- *"Strangler fig?"* — Migrate a monolith piece by piece behind a facade.

---

## DP28 · Patterns in front-end

**Simple explanation.** Front-end patterns: **Container/Presentational** (logic vs view), **custom hooks** (reusable logic), **provider/context** (DI), **observer** (RxJS/state), **render props/HOC** (composition). Same principles, framework-specific shapes ([file 61](61-concept-react-performance.md), [file 62](62-concept-angular-performance.md)).

**Follow-ups**
- *"React reuse?"* — Custom hooks over inheritance/HOC where possible.
- *"Angular reactivity?"* — RxJS (observer) and signals.

---

## DP29 · How do you choose a pattern?

**Simple explanation.** I start from the **problem**, not the pattern: what varies, what must stay stable, what needs to be swappable/testable. Then I match a pattern whose intent fits — and if none clearly fits, I keep it simple. The problem picks the pattern, never the reverse.

**Follow-ups**
- *"No pattern fits?"* — Write the simple code; a pattern may emerge later.
- *"Deciding factor?"* — What's likely to change — abstract that seam only.

---

## DP30 · My approach

**How I answer (the whole picture).** *"I lead with principles — **DRY, KISS, YAGNI, separation of concerns, composition over inheritance** — because they guide judgement on every line. Patterns I treat as named solutions I reach for when I *recognise the problem*: **Strategy** for growing switches, **Adapter** to wrap a third party behind my interface, **Decorator** for cross-cutting concerns, **Repository/Unit-of-Work** for data, **Circuit Breaker** for resilient calls, and **CQRS** when reads and writes genuinely diverge — which is exactly why I split SQL and Snowflake on TCW. The discipline that matters most is restraint: I keep the design as simple as the problem allows and add a pattern only when the simpler option would cost more later. A pattern used to look clever is just complexity with a nicer name."*

**Follow-ups**
- *"Principle you value most?"* — KISS — most damage comes from unnecessary complexity.
- *"Pattern you use most?"* — Strategy and Repository — plus DI everywhere.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| DP1 | Principle vs pattern | Guideline vs named reusable solution |
| DP2 | DRY | One source of truth; beware wrong abstraction |
| DP3 | KISS | Simplest thing that works |
| DP4 | YAGNI | Don't build imagined futures |
| DP5 | SoC | Keep responsibilities apart (layers) |
| DP6 | Composition | Has-a beats is-a for reuse |
| DP7 | Law of Demeter | Don't reach through object chains |
| DP8 | Fail fast | Validate early at boundaries |
| DP9 | Convention over config | Sensible defaults, configure exceptions |
| DP10 | Pattern families | Creational/Structural/Behavioural |
| DP11 | Strategy | Interchangeable algorithms (OCP) |
| DP12 | Factory | Centralise creation (DIP/OCP) |
| DP13 | Singleton | One instance; prefer DI singleton |
| DP14 | Builder | Step-by-step complex construction |
| DP15 | Adapter | Wrap a third party behind your interface |
| DP16 | Decorator | Add behaviour by wrapping |
| DP17 | Facade | Simple door over complex subsystem |
| DP18 | Observer | Subscribe/notify; event-driven |
| DP19 | Command | Request as object; queue/undo |
| DP20 | Repository | Abstract data access |
| DP21 | Unit of Work | Commit changes as one transaction |
| DP22 | DI | Inject dependencies (achieves DIP) |
| DP23 | CQRS | Separate read and write models |
| DP24 | Circuit breaker | Fail fast on a failing dependency |
| DP25 | Anti-patterns | God object, spaghetti, golden hammer |
| DP26 | Over-using patterns | Patterns add cost; use on real problems |
| DP27 | Microservices patterns | Gateway, Saga, Strangler, Sidecar |
| DP28 | Front-end patterns | Container/presentational, hooks, context |
| DP29 | Choosing a pattern | Problem picks the pattern |
| DP30 | My approach | Principles guide; patterns on recognised problems |

---

[← SOLID Principles](59-concept-solid-principles.md) · [Home](README.md) · [Next → React Performance Tuning](61-concept-react-performance.md)
