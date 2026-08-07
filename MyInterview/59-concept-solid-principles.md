# 59 · Concept: SOLID Principles (30 questions)

[← Cross-cutting Decision-Making](58-case-study-decision-making.md) · [Home](README.md) · [Next → Design Principles & Patterns](60-concept-design-principles.md)

This file explains **SOLID** — the five object-oriented design principles that keep code easy to change — in simple English and real depth. I answer from projects A–E, where SOLID kept the TCW reporting APIs (A), the RAG framework (B) and the completion microservices (C) maintainable as teams and requirements grew.

> Simple one-liner: *"SOLID is five rules that make code easy to change without breaking. The goal isn't 'clean code' for its own sake — it's that the next change is cheap and safe."*

## Concepts first — the whole idea before the questions

**Why SOLID exists.** Software doesn't fail because it was written; it fails because it can't be *changed* cheaply. Requirements shift, teams grow, and rigid code turns every small change into a risky, expensive one. SOLID is five principles (Robert C. Martin) that fight that rot by controlling **dependencies** and **responsibilities**.

**The everyday analogy.** Think of a well-organised kitchen. Each tool does one job (S), you can add new gadgets without rewiring the room (O), any brand of blender fits the same socket (L), you don't force a coffee machine to also toast bread (I), and appliances plug into the wall — not hard-wired to each other (D). A messy kitchen where everything is glued together is code without SOLID.

**The five, in one line each:**

| Letter | Principle | One-line meaning |
|--------|-----------|------------------|
| **S** | Single Responsibility | A class should have one reason to change |
| **O** | Open/Closed | Open to extension, closed to modification |
| **L** | Liskov Substitution | A subtype must be usable wherever its base is |
| **I** | Interface Segregation | Many small interfaces beat one fat one |
| **D** | Dependency Inversion | Depend on abstractions, not concrete classes |

**The thread that ties them together:** *manage dependencies so change stays local.* S keeps a class focused; O/L/I/D make sure adding or swapping behaviour doesn't ripple across the codebase. Used together they give **low coupling** and **high cohesion** — the two words that describe changeable software.

**A word of balance (the coach's warning).** SOLID is a *guide, not a religion*. Applied blindly it produces a maze of tiny classes and interfaces (over-engineering). I apply it where change is likely and keep simple things simple — YAGNI wins ties.

**Jump to:** [SP1 What is SOLID](#sp1--what-is-solid) · [SP2 Why it matters](#sp2--why-does-solid-matter) · [SP3 SRP](#sp3--single-responsibility-principle) · [SP4 SRP example](#sp4--srp-a-real-example) · [SP5 OCP](#sp5--openclosed-principle) · [SP6 OCP example](#sp6--ocp-a-real-example) · [SP7 LSP](#sp7--liskov-substitution-principle) · [SP8 LSP example](#sp8--lsp-a-real-example) · [SP9 ISP](#sp9--interface-segregation-principle) · [SP10 ISP example](#sp10--isp-a-real-example)
> [SP11 DIP](#sp11--dependency-inversion-principle) · [SP12 DIP example](#sp12--dip-a-real-example) · [SP13 DIP vs DI](#sp13--dip-vs-dependency-injection) · [SP14 Coupling/cohesion](#sp14--coupling-and-cohesion) · [SP15 SOLID & DI containers](#sp15--solid-and-di-containers) · [SP16 SOLID & testing](#sp16--solid-and-testability) · [SP17 SRP smell](#sp17--how-to-spot-an-srp-violation) · [SP18 OCP smell](#sp18--how-to-spot-an-ocp-violation) · [SP19 Over-engineering](#sp19--can-solid-be-overdone) · [SP20 SOLID in microservices](#sp20--solid-in-microservices)
> [SP21 SOLID in React/TS](#sp21--solid-in-front-end-reacttypescript) · [SP22 SOLID in Python](#sp22--solid-in-python) · [SP23 SOLID vs DRY/KISS](#sp23--solid-vs-dry-kiss-yagni) · [SP24 Strategy & OCP](#sp24--which-patterns-support-solid) · [SP25 Refactor to SOLID](#sp25--how-do-you-refactor-toward-solid) · [SP26 SOLID & legacy](#sp26--applying-solid-to-legacy-code) · [SP27 Interview trap](#sp27--the-common-interview-trap) · [SP28 SOLID in a code review](#sp28--using-solid-in-code-review) · [SP29 Beyond SOLID](#sp29--principles-beyond-solid) · [SP30 My approach](#sp30--my-approach) · [Section index](#section-index)

---

## SP1 · What is SOLID?

**Simple explanation.** **SOLID** is an acronym for five object-oriented design principles — **S**ingle Responsibility, **O**pen/Closed, **L**iskov Substitution, **I**nterface Segregation, **D**ependency Inversion. Together they make code **easier to change, test and extend** by keeping responsibilities focused and dependencies pointing at abstractions.

**Architect's view:** SOLID is my vocabulary for *why* one design is better than another. When I review a design, I'm often really asking "does this violate S or D?"

**Follow-ups**
- *"Who coined it?"* — Robert C. Martin ("Uncle Bob"); the acronym is Michael Feathers'.
- *"One goal?"* — Cheap, safe change — low coupling, high cohesion.

---

## SP2 · Why does SOLID matter?

**Simple explanation.** Because most software cost is **change**, not first build. SOLID code isolates change: a new report type, a new payment provider, a new data source slots in without editing (and risking) code that already works. That means fewer bugs, faster delivery, and easier testing.

*"On the TCW reporting platform, SOLID is why adding a new report reuses the pattern instead of touching the working ones."*

**Follow-ups**
- *"Business value?"* — Faster, safer changes = lower cost and risk over the product's life.
- *"What if I skip it?"* — Code rots: every change becomes risky and slow ("rigid, fragile" code).

---

## SP3 · Single Responsibility Principle

**Simple explanation.** **SRP:** a class (or module/function) should have **one reason to change** — one job, one owner of that job. If a class both formats a report *and* saves it to the database *and* emails it, three different reasons can force it to change.

**Architect's view:** SRP is the most-used and most-violated principle. "One reason to change" is more precise than "one job" — it's about *who* asks for the change.

**Follow-ups**
- *"How do I know?"* — If you use "and" to describe a class, it probably has >1 responsibility.
- *"Too small?"* — Yes, SRP taken to extremes fragments code — balance with cohesion.

---

## SP4 · SRP — a real example

**Simple explanation.** A `ReportService` that pulls data, calculates, formats, and emails violates SRP. I split it: a **repository** (data), a **calculator** (logic), a **formatter** (presentation), a **notifier** (email). Now a change to the email provider touches only the notifier.

```csharp
// Before: one class, four reasons to change
class ReportService { /* fetch + calculate + format + email */ }
// After: each has one reason to change
class ReportRepository { }   // data changes
class ReportCalculator { }   // business-rule changes
class ReportFormatter { }    // layout changes
class EmailNotifier { }      // delivery changes
```

**Follow-ups**
- *"Benefit?"* — Each part is independently testable and changeable.
- *"Risk?"* — Over-splitting; group by *reason to change*, not by line count.

---

## SP5 · Open/Closed Principle

**Simple explanation.** **OCP:** software should be **open for extension, closed for modification**. I add new behaviour by adding new code (a new class/strategy), not by editing existing, tested code. A big `switch` I keep editing for each new case is the classic OCP smell.

**Follow-ups**
- *"How do I extend without editing?"* — Program to an interface; add a new implementation.
- *"Why closed?"* — Editing working code risks breaking it; adding new code doesn't.

---

## SP6 · OCP — a real example

**Simple explanation.** Instead of a `switch` on report type, I define an `IReportGenerator` interface and one implementation per report. Adding a new report means adding a new class — the existing ones and the dispatcher never change.

```csharp
interface IReportGenerator { Report Build(Data d); }
class EquityReport : IReportGenerator { }
class EmergingMarketsReport : IReportGenerator { }
// New report? Add a class. No edits to existing code.
```

**Follow-ups**
- *"Pattern behind it?"* — Strategy/polymorphism ([SP24](#sp24--which-patterns-support-solid)).
- *"Always?"* — Only where variation is expected — don't abstract a switch that never grows.

---

## SP7 · Liskov Substitution Principle

**Simple explanation.** **LSP:** any subtype must be **usable anywhere its base type is expected**, without surprises. A subclass must honour the base class's contract — same expected inputs/outputs, no throwing where the base wouldn't. Breaking LSP breaks polymorphism.

**Follow-ups**
- *"Classic violation?"* — `Square extends Rectangle` where setting width also changes height — breaks callers' expectations.
- *"Rule of thumb?"* — A subtype should require no more and promise no less than its base.

---

## SP8 · LSP — a real example

**Simple explanation.** If `IReportGenerator.Build` is expected to return a report, a subtype that instead throws for "unsupported" breaks callers relying on the contract. I fix it by not forcing that subtype into the hierarchy, or by making the contract honest (e.g. a capability check).

**Follow-ups**
- *"Symptom in code?"* — Callers doing `if (x is SpecialType)` special-casing — the abstraction is leaking.
- *"Fix?"* — Redesign the hierarchy so every subtype truly *is-a* base type.

---

## SP9 · Interface Segregation Principle

**Simple explanation.** **ISP:** clients shouldn't be forced to depend on methods they don't use. Prefer **several small, focused interfaces** over one **fat** interface. A class implementing a huge interface it only half-needs has to stub the rest — a smell.

**Follow-ups**
- *"Symptom?"* — Methods that throw `NotImplementedException`.
- *"Benefit?"* — Implementers depend only on what they use; changes ripple less.

---

## SP10 · ISP — a real example

**Simple explanation.** A fat `IRepository` with `Read`, `Write`, `Bulk`, `Archive` forces a read-only consumer to know about writes. I split into `IReadRepository` and `IWriteRepository`; a query screen depends only on reads.

```csharp
interface IReadRepository<T>  { T? Get(int id); }
interface IWriteRepository<T> { void Add(T item); }
// A report screen takes IReadRepository only — no write surface.
```

**Follow-ups**
- *"Link to CQRS?"* — Same instinct — separate read and write concerns.
- *"Over-split?"* — Don't make an interface per method blindly; split by client need.

---

## SP11 · Dependency Inversion Principle

**Simple explanation.** **DIP:** high-level modules shouldn't depend on low-level modules — **both depend on abstractions**. My business logic depends on an `IEmailSender` interface, not on `SmtpEmailSender`. This lets me swap implementations (SMTP → SendGrid) and test with a fake.

**Follow-ups**
- *"Direction of dependency?"* — Point it at an interface owned by the high-level code.
- *"Payoff?"* — Swappable, testable, decoupled — the reversible-path filter in code form.

---

## SP12 · DIP — a real example

**Simple explanation.** My RAG orchestration (B) depends on `IVectorStore`, not on Chroma directly. Swapping Chroma for Azure AI Search is a new implementation of the interface — the orchestration code never changes. That's DIP protecting a real decision.

```csharp
interface IVectorStore { IReadOnlyList<Chunk> Search(float[] q, int k); }
class ChromaStore : IVectorStore { }
class AzureAiSearchStore : IVectorStore { }
```

**Follow-ups**
- *"Cross-link?"* — This is why [CB3/DM4](58-case-study-decision-making.md#dm4--how-do-you-make-a-decision-reversible) reversibility works.
- *"Who creates the concrete class?"* — The DI container at composition root ([SP15](#sp15--solid-and-di-containers)).

---

## SP13 · DIP vs Dependency Injection

**Simple explanation.** **DIP** is the *principle* (depend on abstractions). **Dependency Injection (DI)** is one *technique* to achieve it — passing dependencies in (via constructor) instead of `new`-ing them inside. DIP is the goal; DI is a common way to get there.

**Follow-ups**
- *"Same thing?"* — No — DIP is the principle, DI (and IoC containers) are how you implement it.
- *"Constructor injection?"* — My default — dependencies are explicit and testable.

---

## SP14 · Coupling and cohesion

**Simple explanation.** **Coupling** = how much modules depend on each other (want it *low*). **Cohesion** = how focused a module is on one job (want it *high*). SOLID is really a toolkit for **low coupling, high cohesion** — the two properties of changeable code.

**Follow-ups**
- *"Which principle helps which?"* — SRP/ISP raise cohesion; OCP/DIP lower coupling.
- *"Measure it?"* — Ask "if I change X, what else must change?" — a lot means high coupling.

---

## SP15 · SOLID and DI containers

**Simple explanation.** A **DI container** (built into .NET) wires abstractions to concrete classes at the **composition root**, so my code only sees interfaces (DIP). I register `IVectorStore → ChromaStore` in one place; everything else depends on the interface.

**Follow-ups**
- *"Lifetimes?"* — Singleton/scoped/transient — match to the dependency ([file 51 DN9](51-concept-dotnet-core.md#dn9--service-lifetimes)).
- *"Container required for DIP?"* — No — you can inject manually; the container just automates it.

---

## SP16 · SOLID and testability

**Simple explanation.** SOLID code is easy to unit-test: DIP lets me inject **fakes/mocks**, SRP keeps units small and focused, ISP means I mock only what's used. Hard-to-test code is usually a SOLID violation in disguise.

*"When a class is painful to test, I don't fight the test — I fix the design; the pain is pointing at a coupling problem."*

**Follow-ups**
- *"Sign of bad design?"* — Needing a database or network to unit-test business logic.
- *"Fix?"* — Inject an abstraction; test the logic in isolation.

---

## SP17 · How to spot an SRP violation

**Simple explanation.** Signs: a class name with "And"/"Manager"/"Helper", methods touching unrelated concerns (DB + UI + email), a file that changes for many different reasons, and huge classes ("god objects"). Each is a cue to split by *reason to change*.

**Follow-ups**
- *"Quick test?"* — Describe the class in one sentence; if you need "and", split it.
- *"Danger of god objects?"* — Every change risks everything they touch.

---

## SP18 · How to spot an OCP violation

**Simple explanation.** The tell-tale sign is **editing the same file every time a new case appears** — a growing `switch`/`if-else` on a type, repeated across the codebase. That's a cue to introduce an interface + strategy so new cases are new classes.

**Follow-ups**
- *"Is every switch bad?"* — No — only ones that keep growing with new business cases.
- *"Fix?"* — Polymorphism/Strategy; register implementations by key.

---

## SP19 · Can SOLID be overdone?

**Simple explanation.** Yes. Blindly applied, SOLID creates a **maze of tiny classes and interfaces** for code that never changes — accidental complexity. I apply it where **variation or change is likely**, and keep stable, simple code simple. YAGNI and KISS are the counterweights.

*"An interface with one implementation that will never have a second is often just noise — I add the seam when the second reason appears, if it's cheap to do then."*

**Follow-ups**
- *"How decide?"* — Is change likely here? Is the abstraction cheap to add later? If "no, yes" — wait.
- *"Balance principle?"* — SOLID for changeable areas; KISS/YAGNI everywhere else.

---

## SP20 · SOLID in microservices

**Simple explanation.** SOLID scales up: a **service** should have a single responsibility (SRP at service level = bounded context), depend on other services via **contracts/abstractions** (DIP), and be extendable without editing others (OCP). The completion platform (C) split by business capability is SRP for services.

**Follow-ups**
- *"SRP for a service?"* — One business capability per service — the bounded context.
- *"DIP across services?"* — Depend on a versioned contract, not another service's internals ([file 65](65-concept-microservices-performance.md)).

---

## SP21 · SOLID in front-end (React/TypeScript)

**Simple explanation.** SOLID applies beyond OOP. In React: a component with one job (SRP), extend via **composition/props** not editing (OCP), small focused prop/interface types (ISP), and depend on abstractions like hooks/context (DIP) rather than hard-wiring a data source into a component.

**Follow-ups**
- *"SRP in React?"* — Split a component doing fetch + layout + logic into a hook + presentational component.
- *"DIP in React?"* — Inject data via props/context so the component is reusable and testable.

---

## SP22 · SOLID in Python

**Simple explanation.** Python is duck-typed, so DIP/ISP use **protocols/ABCs** and just passing the right shape. My FastAPI ETL (A) depends on an abstract `Source`/`Sink`, so a new data source is a new class — OCP — without touching the pipeline.

**Follow-ups**
- *"Interfaces in Python?"* — `typing.Protocol` or `abc.ABC` for explicit contracts.
- *"Still worth it?"* — Yes — the principles are language-agnostic; the mechanism differs.

---

## SP23 · SOLID vs DRY, KISS, YAGNI

**Simple explanation.** They're complementary. **DRY** (don't repeat yourself), **KISS** (keep it simple), **YAGNI** (don't build what you don't need) guard against complexity; **SOLID** structures the complexity you *do* need. When they conflict, I favour KISS/YAGNI for stable code and SOLID for changeable code.

**Follow-ups**
- *"DRY vs SRP tension?"* — Over-DRYing can couple unrelated things; a little duplication beats the wrong abstraction.
- *"Priority?"* — Simplicity first; add SOLID seams when change demands them.

---

## SP24 · Which patterns support SOLID?

**Simple explanation.** Many GoF patterns are SOLID in action: **Strategy** (OCP), **Factory** (DIP/OCP), **Adapter** (DIP), **Decorator** (OCP), **Repository** (SRP/DIP). Patterns are named solutions that happen to satisfy the principles ([file 60](60-concept-design-principles.md)).

**Follow-ups**
- *"Learn patterns or principles first?"* — Principles — patterns make sense once you know *why*.
- *"Most useful for OCP?"* — Strategy and Decorator.

---

## SP25 · How do you refactor toward SOLID?

**Simple explanation.** Incrementally and behind tests: (1) add characterisation tests, (2) extract the responsibility that changes most (SRP), (3) introduce an interface at the painful seam (DIP), (4) replace a growing switch with strategies (OCP). Small steps, green tests each time.

**Follow-ups**
- *"Big-bang rewrite?"* — Avoid — refactor in safe steps with tests as a net.
- *"Where to start?"* — The class that hurts most to change — highest ROI.

---

## SP26 · Applying SOLID to legacy code

**Simple explanation.** In legacy code I don't apply all five everywhere; I create a **seam** (an interface) around the part I need to change or test, inject it (DIP), and improve just that area. Over time the SOLID islands grow. This is the strangler approach at the class level.

**Follow-ups**
- *"First move on untested legacy?"* — Get a test around it via a seam, then refactor safely.
- *"Realistic goal?"* — Improve where you touch; don't boil the ocean.

---

## SP27 · The common interview trap

**Simple explanation.** The trap is reciting the acronym without **examples or trade-offs**. I always pair each letter with a concrete example and note that SOLID can be over-applied. Showing judgement (when *not* to) scores higher than perfect definitions.

**Follow-ups**
- *"What impresses?"* — A real refactor story and knowing the cost of over-abstraction.
- *"Most violated?"* — SRP (and DIP by `new`-ing dependencies inside classes).

---

## SP28 · Using SOLID in code review

**Simple explanation.** SOLID gives review a shared language: "this class has two reasons to change (SRP)", "this switch will grow — extract a strategy (OCP)", "inject this dependency (DIP)". It turns opinion into principle, which makes reviews objective and teachable.

**Follow-ups**
- *"Nit or principle?"* — Tie feedback to a principle and its cost, not personal style.
- *"Teaching juniors?"* — Point at the exact letter and show the cheaper future change.

---

## SP29 · Principles beyond SOLID

**Simple explanation.** SOLID isn't everything. I also use **DRY, KISS, YAGNI**, **Law of Demeter** (don't reach through objects), **Composition over inheritance**, and **Separation of Concerns**. SOLID is the OO core; these round it out ([file 60](60-concept-design-principles.md)).

**Follow-ups**
- *"Composition over inheritance?"* — Prefer building from parts over deep class trees — more flexible, avoids LSP traps.
- *"Law of Demeter?"* — Talk to friends, not strangers — reduces coupling.

---

## SP30 · My approach

**How I answer (the whole picture).** *"I treat SOLID as five tools for one goal: cheap, safe change. **SRP** keeps each class focused on one reason to change; **OCP** lets me add behaviour (a new report, a new source) without editing tested code; **LSP** keeps my polymorphism honest; **ISP** keeps interfaces small so clients depend only on what they use; and **DIP** points my business logic at abstractions so I can swap Chroma for Azure AI Search, or SMTP for SendGrid, and still test with fakes. I apply them where change is likely — on the TCW APIs and the RAG framework — and I deliberately *don't* over-apply them to stable, simple code, where KISS and YAGNI win. The measure of success is simple: when the next change lands, it touches one place, and the tests stay green."*

**Follow-ups**
- *"One principle if forced?"* — SRP — it prevents the god objects that cause most pain.
- *"Biggest mistake teams make?"* — Either ignoring SOLID (rigid code) or worshipping it (maze of abstractions) — judgement is the skill.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| SP1 | What is SOLID | Five OO principles for changeable code |
| SP2 | Why it matters | Change is the real cost; SOLID isolates it |
| SP3 | SRP | One reason to change per class |
| SP4 | SRP example | Split data/logic/format/notify |
| SP5 | OCP | Extend by adding, not editing |
| SP6 | OCP example | Interface + one class per report |
| SP7 | LSP | Subtypes usable as their base |
| SP8 | LSP example | No special-casing subtypes |
| SP9 | ISP | Small interfaces over fat ones |
| SP10 | ISP example | Split read/write repositories |
| SP11 | DIP | Depend on abstractions |
| SP12 | DIP example | IVectorStore → swap Chroma/AI Search |
| SP13 | DIP vs DI | Principle vs technique |
| SP14 | Coupling/cohesion | SOLID = low coupling, high cohesion |
| SP15 | DI containers | Wire abstractions at composition root |
| SP16 | Testability | SOLID code is easy to mock/test |
| SP17 | SRP smell | "And" names, god objects |
| SP18 | OCP smell | A switch you keep editing |
| SP19 | Over-engineering | Don't over-apply; YAGNI/KISS balance |
| SP20 | Microservices | SRP = bounded context; DIP = contracts |
| SP21 | React/TS | Composition, hooks, small prop types |
| SP22 | Python | Protocols/ABCs for DIP/ISP |
| SP23 | vs DRY/KISS/YAGNI | Complementary; simplicity first |
| SP24 | Patterns | Strategy/Factory/Adapter enact SOLID |
| SP25 | Refactoring | Small steps behind tests |
| SP26 | Legacy | Create seams; grow SOLID islands |
| SP27 | Interview trap | Pair each letter with an example + trade-off |
| SP28 | Code review | Shared language, objective feedback |
| SP29 | Beyond SOLID | DRY, KISS, YAGNI, Demeter, composition |
| SP30 | My approach | Five tools for cheap, safe change |

---

[← Cross-cutting Decision-Making](58-case-study-decision-making.md) · [Home](README.md) · [Next → Design Principles & Patterns](60-concept-design-principles.md)
