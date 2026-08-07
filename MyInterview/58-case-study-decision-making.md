# 58 · Cross-cutting Architectural Decision-Making (7 questions + follow-ups)

[← Case Study E: UK Web Platforms](57-case-study-e-uk-web-platforms.md) · [Home](README.md) · [Next → SOLID Principles](59-concept-solid-principles.md)

The case-study files (53–57) tell *what* I built on each project. This file is the **playbook underneath all of them** — *how* I make architectural decisions, told as reusable principles with evidence from projects A–E. When an interviewer asks *"how do you make decisions?"* rather than *"what did you build?"*, this is where I answer. It closes the case-study chapter and leads into the **principles & performance deep-dives** (files 59–65).

> One-line: *"I choose the most boring technology that meets the hardest constraint, behind an interface I can change my mind about later — and I write down why."*

**Jump to:** [The decision lens](#the-decision-lens-five-filters) · [The ADR habit](#the-adr-habit) · [DM1](#dm1--whats-your-process-for-making-a-big-architecture-decision) · [DM2](#dm2--how-do-you-choose-a-technology-without-chasing-hype) · [DM3](#dm3--how-do-you-decide-between-two-good-options) · [DM4](#dm4--how-do-you-make-a-decision-reversible) · [DM5](#dm5--how-do-you-get-buy-in-for-an-architecture-decision-from-stakeholders) · [DM6](#dm6--how-do-you-decide-when-good-enough-is-actually-enough) · [DM7](#dm7--how-do-you-handle-a-decision-that-turned-out-wrong) · [Section index](#section-index)

---

## The decision lens (five filters)

I run every significant choice through these five filters, in order. The projects show them in action.

| # | Filter | The question | Seen in |
|---|--------|--------------|---------|
| 1 | **Dominant constraint** | What one quality must not break? | A: the pre-market deadline drove the SQL/Snowflake split |
| 2 | **Fit to operating model** | Who runs this at 3 a.m.? Bias to most-managed. | C: managed Azure over AKS |
| 3 | **Reuse & team skills** | Can the team maintain it? | A: FastAPI/Python because the team had the skill |
| 4 | **Lifecycle cost** | What's the real cost to build *and operate*? | B: RAG over fine-tuning (cheaper to update) |
| 5 | **Reversible path** | Can I undo this behind an interface? | B: vector store behind an interface; E: bought products behind adapters |

> Said out loud: *"Name the constraint that must hold, pick the most-managed option the team can run, prefer what they already know, cost it over its life, and keep an exit."*

---

## The ADR habit

Every significant decision gets a short **Architecture Decision Record**: the context, the options weighed, the choice, and **the trade-off I accepted**. You can see the ADR-style tables in every case-study file (A-1..A-6, B-1..B-6, C-1..C-6, D-1..D-4, E-1..E-4). The value isn't bureaucracy — it's that *a decision without a written reason becomes an argument later*, and a written trade-off protects the team when someone questions the choice a year on.

---

### DM1 · What's your process for making a big architecture decision?

**My answer.** I use **C-QUAD**: **C**larify the constraint, weigh **QU**alities/options, **A**rrive at a decision, then state the **D**ownside. Concretely: (1) name the **dominant constraint**; (2) list the **real options** with trade-offs; (3) run them through the **five filters**; (4) **decide** and name the one reason that settled it; (5) **record it** as an ADR with the trade-off I accepted; (6) keep it **reversible** where I can.

**Evidence.** In Project A, the constraint (pre-market deadline) drove the SQL/Snowflake split; I recorded it, and I kept the stores behind a shared data-access pattern so the design can evolve.

**Lesson.** *"A decision is: constraint → options → choice → stated downside, written down. If I can't name the downside, I haven't finished deciding."*

**Follow-up: How long do you spend deciding before you just commit?**
> Proportional to reversibility and cost. Cheap, reversible calls I make fast and adjust. Expensive, hard-to-reverse calls get a PoC or a spike to buy evidence (Project E). I never let analysis-paralysis stall a reversible decision.

**Follow-up: What if you don't have time to weigh options fully?**
> I make the smallest reversible decision that unblocks progress, mark it as provisional in the ADR, and revisit with evidence. Motion beats a perfect decision made too late — as long as it's reversible.

---

### DM2 · How do you choose a technology without chasing hype?

**My answer.** I start from the **constraint, not the tool**, and bias to the **most boring option that meets it**. New tech has to earn its place against the five filters — especially *fit to operating model* and *team skills*. Fashion is not a filter.

**Evidence.** Project C: I chose **managed App Services and Functions over AKS** because the client's team could run them — Kubernetes would have been a trophy, not a fit. Project B: I chose **RAG over fine-tuning** on cost and auditability, not because fine-tuning sounded advanced.

**Lesson.** *"Boring technology is a feature. The exciting part should be the business outcome, not the stack."*

**Follow-up: But you *did* use cutting-edge AI (Project B) — isn't that hype?**
> The *use case* was real (a governance gap plus support pain), and I made the *architecture* boring and safe — grounding, evaluation, reversibility, least-privilege. I adopt new tech when it solves a real constraint and I can operate it safely, not because it's new.

**Follow-up: How do you keep up without chasing every new tool?**
> I learn deeply, adopt slowly. I understand new tools enough to know *when* they'd fit a constraint, but I only bring one into a client system when it clearly beats the boring option on the filters.

---

### DM3 · How do you decide between two good options?

**My answer.** When both pass the filters, I decide on the **dominant constraint** and the **reversibility**. Which one better protects the one quality that must not break? And which one is easier to undo if I'm wrong? If still tied, I pick the one the **team knows best**, because maintainability breaks ties.

**Evidence.** Project A: .NET vs FastAPI for ETL were both viable; team skill and data-native fit settled it. Project E: close build-vs-buy calls I settle with a PoC that tests the real fit.

**Lesson.** *"When options tie on merit, break the tie on the dominant constraint, then on reversibility, then on team skill — never on my personal taste."*

**Follow-up: What if the team and you disagree on the tie-break?**
> I listen — they operate it, so their maintainability view is weighty. If it's genuinely a tie on constraints, I'll often defer to the team's preference because their buy-in makes the system healthier. See DM5.

---

### DM4 · How do you make a decision reversible?

**My answer.** **Interfaces and contracts at the boundaries.** I put anything I might change — a vector store, a bought product, a scheduler — behind an interface so swapping the implementation is a contained change, not a rewrite. I prefer additive, versioned changes over breaking ones, and I keep data export paths open.

**Evidence.** Project B: retrieval sits behind an interface, so Chroma can become Azure AI Search without a rewrite. Project C: services integrate through **versioned REST contracts**, so one system can change without breaking others. Project E: bought products sit behind adapters to avoid lock-in.

**Lesson.** *"Reversibility is bought with interfaces. The boundary is the promise; everything behind it is mine to change my mind about."*

**Follow-up: Doesn't all that abstraction add cost?**
> A little, and I apply it where change is *likely*, not everywhere — that would be over-engineering (YAGNI). I put interfaces around the third parties and the fast-moving choices, and keep stable internals simple.

**Follow-up: What's a decision you deliberately made *ir*reversible?**
> Core data-correctness rules — reconciliation on money data (Projects A, D). Some things *should* be hard to bypass. Reversibility is for technology choices, not for the guarantees the business depends on.

---

### DM5 · How do you get buy-in for an architecture decision from stakeholders?

**My answer.** I **present the decision as a trade-off, not a verdict**: here's the constraint, here are the options I weighed, here's my recommendation, and here's what I'd give up. Inviting refinement instead of demanding sign-off turns stakeholders into co-owners of the decision.

**Evidence.** Project C: I **presented architecture decisions to stakeholders for refinement** on site — that co-ownership is what drove adoption. Most disagreement dissolves once people see the options you already considered.

**Lesson.** *"Show your working. People back decisions they helped shape, and disagreement usually means they can see an option you haven't shown them yet."*

**Follow-up: What if you're overruled on a decision you believe in?**
> I make my case with the trade-off clearly, and if I'm overruled after a fair hearing, I **document the risk** in the ADR and commit fully — no passive resistance. Disagree and commit. If the risk later materialises, the record makes the conversation a learning one, not a blame one.

**Follow-up: How do you present to a non-technical stakeholder?**
> In the language of the constraint they care about — the deadline, the cost, the risk, the user — not the tech. "This choice protects your pre-market deadline" lands; "we chose Snowflake" doesn't.

---

### DM6 · How do you decide when 'good enough' is actually enough?

**My answer.** I anchor on the **dominant constraint and the NFRs the business actually needs** — not on perfection. Once the design meets the constraint with sensible headroom and is reversible, more polish is usually gold-plating. **YAGNI**: I don't build for scale or flexibility the business hasn't asked for and can't yet justify.

**Evidence.** Project C: microservices *per real business process* (four), not fragmented further — stopping at the boundary that mattered. Project E: a PoC tests the riskiest assumption and stops, rather than trying to prove everything.

**Lesson.** *"Enough is when the dominant constraint is safely met and the decision is reversible. Past that, polish is cost without value."*

**Follow-up: How do you resist over-engineering?**
> I ask "what breaks if I *don't* build this now, and can I add it later behind an interface?" If the answer is "nothing breaks and yes I can add it later," I don't build it now. Reversibility lets me defer safely.

---

### DM7 · How do you handle a decision that turned out wrong?

**My answer.** I **surface it early, own it, and use the reversibility I designed in**. I go back to the ADR — the recorded trade-off tells me *why* I chose it and what changed — and I make the smallest correcting change, usually swapping the implementation behind the interface. No ego, no hiding; a wrong decision caught early and reversed cheaply is a normal part of the job.

**Evidence.** The whole reversibility discipline (DM4) exists *for this moment*. Because Project B's store and Project E's bought products sit behind interfaces, being wrong about them is a contained fix, not a crisis.

**Lesson.** *"You will be wrong sometimes. The skill is designing so that being wrong is cheap, catching it early, and owning it without drama."*

**Follow-up: How do you know a decision is going wrong before it's a crisis?**
> Observability and the evaluation loops — the dashboards (A), the LangSmith scores (B), the defect/velocity metrics (D). I instrument decisions so I *see* them degrading rather than discovering it from an outage. Measured decisions fail loudly and early, not silently and late.

**Follow-up: How do you talk about a past mistake in an interview?**
> Honestly, as a lesson: the decision, why it was reasonable at the time, what changed, how I caught it, how I fixed it cheaply, and the rule I now carry. Owning a reversed decision shows more seniority than pretending I've never been wrong.

---

## Section index

| ID | Topic | One-line summary |
|----|-------|------------------|
| — | Decision lens | Five filters: constraint, operating model, skills, lifecycle cost, reversibility |
| — | ADR habit | Record context/options/choice/trade-off for every big decision |
| DM1 | Decision process | C-QUAD: constraint → options → choice → stated downside, written down |
| DM2 | Avoiding hype | Start from the constraint; boring tech is a feature |
| DM3 | Two good options | Break ties on constraint, then reversibility, then team skill |
| DM4 | Reversibility | Interfaces & versioned contracts at the boundaries |
| DM5 | Stakeholder buy-in | Present trade-offs for refinement; disagree and commit |
| DM6 | Good enough | Meet the constraint with headroom; resist gold-plating (YAGNI) |
| DM7 | Wrong decisions | Design so being wrong is cheap; catch early, own it |

---

[← Case Study E: UK Web Platforms](57-case-study-e-uk-web-platforms.md) · [Home](README.md) · [Next → SOLID Principles](59-concept-solid-principles.md)
