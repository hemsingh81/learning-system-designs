# 52 · Case Studies & Architectural Decision-Making — Hub

[← .NET Core](51-concept-dotnet-core.md) · [Home](README.md) · [Next → Case Study A: Investment Reporting](53-case-study-a-investment-reporting.md)

This is the **hub** for my case studies. The other concept files (28–51) teach a topic; these files tell my **real projects as full case studies** — *how the project started, why we chose each technology, the benefits, who was involved, and my involvement from start to end (architecture through development to production and support)*. Each case study lives in its own file so I can go deep, and each ends with **interview questions, full answers and follow-up questions** so I can defend every decision I made.

> Simple one-liner: *"A good architect can tell you not just what they built, but why they built it that way, what they rejected, who they built it with, and what it cost. These files are my decision story for each project."*

---

## The five case studies (one file each)

![Four anchor projects with their stacks and headline results](assets/anchor-projects.svg)

*Figure 52.1 — My story bank. Each case study below expands one of these anchor projects into a full decision narrative.*

| File | Case study | Client(s) | Lead theme | Headline number |
|------|-----------|-----------|-----------|-----------------|
| [53](53-case-study-a-investment-reporting.md) | **A — Investment Reporting Platform** | TCW Group, Los Angeles | Deadline-driven data platform; SQL + Snowflake split; FastAPI ETL; dependency-aware orchestration | Reports land **inside the pre-market window** daily |
| [54](54-case-study-b-ai-rag-assistant.md) | **B — AI/LLM Framework & RAG Assistant** | TCW Group | Reference architecture first; RAG over fine-tuning; Chroma/LangChain/LangGraph/LangSmith | TCW's **first production RAG app** |
| [55](55-case-study-c-completion-platform.md) | **C — Construction Completion Platform** | TengizChevroil, Kazakhstan | Microservices per process; managed Azure; adoption as architecture | **60%** less manual effort, **50%** shorter release cycle |
| [56](56-case-study-d-asset-management-reporting.md) | **D — Asset-Management Reporting** | Sculptor Capital · Bain Capital | ADF ETL + BI; velocity from cutting rework; Agile delivery | **+20%** velocity, **−15%** defects |
| [57](57-case-study-e-uk-web-platforms.md) | **E — UK Enterprise Web Platforms** | Bupa · NHS · Unilever | PoC-led direction; owned code standards; regulated discipline | Decisions **shaped by evidence** before build |
| [58](58-case-study-decision-making.md) | **Cross-cutting Decision-Making** | All projects | *How* I decide, not just what I built | The reusable decision playbook |

---

## The case-study template (the 8 beats)

When I tell any project as a case study, I keep the same eight beats. It stops me rambling and it makes the **decision** — not just the tech — the hero of the story. Every case-study file below follows this exact order.

| Beat | What I answer | Why it matters in an interview |
|---|---|---|
| **1. How it started** | The business trigger. A deadline, a paper process, a compliance gap, a cost problem. | Shows I start from the business, not the tech. |
| **2. The problem / constraints** | The non-functionals: time window, correctness, scale, cost, regulation. | Architects are hired to own constraints. |
| **3. Options I considered** | The real alternatives, with the trade-off of each. | This is what separates an architect from a builder. |
| **4. The decision & why** | What I picked, and the one reason that settled it. | A decision without a reason is just a preference. |
| **5. What I built** | The concrete components, patterns and data flow. | Proves I can go from decision to working system. |
| **6. Who was involved** | Business analysts, stakeholders, engineers, data, QA, ops — and my role among them. | Architecture is a team sport; shows leadership. |
| **7. The result** | A number. Always a number. | Outcome, not activity. |
| **8. The lesson** | What I would do differently, or the rule I now carry. | Shows growth; juniors leave this out. |

These map to my two answer frameworks — **C-QUAD** for design questions and **STAR-D** for behavioural ones (see [01 Overview](01-overview-positioning.md#14-frameworks-i-use-to-answer-so-i-never-ramble)).

---

## The decision lens — how I choose technology

Before every case study, here is the lens I use to choose any technology. I never pick a tool because it is new. I run the choice through five filters, in order.

1. **The dominant constraint first.** I name the one quality that must not break — a deadline, correctness on money, adoption on a shop floor, or cost. The technology serves that, not the other way round.
2. **Fit to the operating model.** Who runs this at 3 a.m.? I bias to the most-managed option that meets the need (App Service over AKS, a managed queue over self-hosted) so the client's team can actually operate it.
3. **Reuse and skills in the team.** A slightly less perfect tool the team already knows beats a perfect tool nobody can maintain.
4. **Cost over the lifecycle, not day one.** Licence, compute, and the human cost of operating it. Snowflake compute is not free; neither is a cluster nobody patches.
5. **A reversible path.** I prefer decisions I can undo. Contracts and interfaces at the boundaries so I can swap an implementation later without a rewrite.

> The phrase I use out loud: *"I choose the most boring technology that meets the hardest constraint, behind an interface I can change my mind about later."*

---

## How each case-study file is laid out

So I always know where to look under pressure, every file (53–57) has the same sections:

- **The story** — the 8 beats above, told in depth.
- **Architecture at a glance** — the components and the data flow, with a diagram where one exists.
- **Decision log** — an ADR-style table: the decision, the options, the choice, and the trade-off I accepted.
- **Q&As** — interviewer-style questions with full answers and follow-ups.
- **Section index** — a one-line summary of every Q&A.

File [58](58-case-study-decision-making.md) is different: it is the **cross-cutting decision-making** playbook that pulls the *how-I-decide* lessons out of all five projects.

---

## Fast recall — the one-line decision per project

If I only have a sentence per project in the room, these are the lines I land:

| Project | The decision in one line |
|---------|--------------------------|
| **A** | *"I split the data tier by workload — SQL Server for operational, Snowflake for analytical — because a shared engine would let heavy analytics starve my pre-market deadline."* |
| **B** | *"I built the safe reusable AI pattern first — retrieval, grounding, orchestration, evaluation — then proved it with the firm's first RAG app; RAG over fine-tuning because the knowledge changes and must be cited."* |
| **C** | *"I split four business processes into microservices on managed Azure because they have independent lifecycles — and I treated shop-floor adoption as an architecture requirement, not training."* |
| **D** | *"I attacked rework, not effort — automation plus review gates — so velocity and quality rose together, +20% and −15%."* |
| **E** | *"I led with a cheap PoC to de-risk the client's direction before funding a build, and owned code standards so quality stayed consistent in regulated delivery."* |

---

[← .NET Core](51-concept-dotnet-core.md) · [Home](README.md) · [Next → Case Study A: Investment Reporting](53-case-study-a-investment-reporting.md)
