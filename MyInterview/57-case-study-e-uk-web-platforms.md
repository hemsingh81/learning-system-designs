# 57 · Case Study E — UK Enterprise Web Platforms (Bupa · NHS · Unilever) (5 questions + follow-ups)

[← Case Study D: Asset-Management Reporting](56-case-study-d-asset-management-reporting.md) · [Home](README.md) · [Next → Cross-cutting Decision-Making](58-case-study-decision-making.md)

This is my **enterprise web, regulated-delivery and PoC-led** case study: large web platforms for **Bupa, the NHS and Unilever** in the UK. I reach for it on *"how do you de-risk a big decision?"*, *"how do you keep quality consistent across a large team?"* and *"how do you deliver in a regulated environment?"* For theory, see [30 ASP.NET Core](30-concept-aspnet-core.md), [31 Web API](31-concept-aspnet-webapi.md), [47 System Design](47-concept-system-design.md) and [06 Quality](06-quality-engineering.md).

> One-line decision: *"I led with a cheap PoC to de-risk the client's direction before funding a build, and owned code standards so quality stayed consistent in regulated delivery."*

**Jump to:** [The story](#the-story-the-8-beats) · [Decision log](#decision-log-adr-style) · [CE1](#ce1--how-do-you-use-a-poc-to-de-risk-a-major-decision) · [CE2](#ce2--how-did-you-keep-code-quality-consistent-across-a-large-team) · [CE3](#ce3--how-does-regulated-delivery-nhs-bupa-change-how-you-architect) · [CE4](#ce4--how-do-you-decide-build-vs-buy-vs-reuse-on-an-enterprise-platform) · [CE5](#ce5--how-do-you-turn-a-poc-into-a-production-decision-without-throwing-work-away) · [Section index](#section-index)

---

## The story (the 8 beats)

![Presales to delivery flow: PoC-led direction feeding into funded delivery](assets/presales-to-delivery.svg)

*Figure 57.1 — Project E. PoC-led direction: cheap evidence before an expensive build, then consistent, regulated delivery.*

**1. How it started.** These are large UK enterprises — **Bupa** (health insurance), the **NHS** (public healthcare), **Unilever** (consumer goods) — building or modernising **customer-facing web platforms**. The recurring trigger: the client had a **direction they weren't yet sure of**, and a big build is expensive to get wrong. Before committing budget, they needed **evidence** that an approach would work.

**2. The problem / constraints.**
- **High cost of a wrong direction** — enterprise builds are expensive; a mistaken architecture is costly to unwind.
- **Regulated / high-scrutiny** environments (health, public sector) — accessibility, security, privacy and auditability are non-negotiable.
- **Large teams** — keeping code quality consistent across many engineers is hard.
- **Real users at scale** — performance and reliability matter publicly.

**3. Options I considered.**
- *Commit to a full build on the client's initial direction.* Fast to start, catastrophic if the direction is wrong — rejected for high-stakes calls.
- *Analysis-paralysis — endless design docs.* Cheap but produces no evidence and delays value.
- *A focused Proof of Concept* to test the riskiest assumption cheaply, then fund the build on evidence.

**4. The decision & why.** **Lead with a PoC** to de-risk the direction before funding the build, and **own the code standards** so quality stayed consistent across a large team in a regulated setting. The settling reason: *the cheapest place to be wrong is in a PoC.* Evidence before budget, standards before scale.

**5. What I built / did.**
- **Proofs of Concept** targeting the riskiest assumption (a technology fit, an integration, a performance question) to prove or kill the direction cheaply.
- **Owned coding standards, patterns and reviews** so a large team produced consistent, maintainable, secure code.
- **ASP.NET / .NET web platforms** with the accessibility, security and privacy discipline these regulated sectors demand.
- Translated PoC learnings into the funded architecture so nothing was wasted.

**6. Who was involved.** I worked with **client stakeholders** (to frame the direction and the risk), **business analysts**, a **large engineering team** (whose standards and reviews I owned), **QA/accessibility specialists**, and **security/compliance** in the regulated sectors. My role was to **turn uncertainty into evidence** and then **hold quality steady at scale**.

**7. The result.** Big decisions were **shaped by evidence** before money was committed, and quality stayed **consistent across a large team** through owned standards — the two things that most often go wrong on enterprise builds.

**8. The lesson.** *"The cheapest place to be wrong is in a Proof of Concept. Spend a little to learn, before you spend a lot to build."*

---

## Decision log (ADR-style)

| # | Decision | Options weighed | What I chose & the trade-off accepted |
|---|----------|-----------------|----------------------------------------|
| E-1 | De-risking method | Full build on faith / docs / **targeted PoC** | **PoC** — a little time upfront, bought evidence before big spend |
| E-2 | Quality at scale | Trust each engineer / **owned standards + reviews** | **Owned standards** — review overhead, bought consistency across a large team |
| E-3 | Regulated NFRs | Bolt on later / **accessibility+security by design** | **By design** — slower per feature, bought compliance & trust |
| E-4 | PoC outcome | Throwaway PoC / **learnings feed the build** | **Feed the build** — discipline to extract lessons, bought no wasted work |

---

### CE1 · How do you use a PoC to de-risk a major decision?

**Context.** A client is unsure of a direction, and a full build is expensive to get wrong.

**The decision & why.** I build a **focused PoC that tests the single riskiest assumption** — not a mini-product, just the one question that would sink the project if the answer is "no." It's time-boxed, cheap, and has a clear success/failure criterion agreed up front. If it fails, we've saved a fortune; if it succeeds, we fund the build **with evidence and a clearer design**.

**Result.** Direction decided by evidence, not opinion, at a fraction of the cost of being wrong in production.

**Lesson.** *"A PoC has one job: kill or confirm the riskiest assumption, cheaply. If it tries to prove everything, it proves nothing."*

**Follow-up: How do you scope a PoC so it doesn't become a mini-project?**
> Name the one riskiest assumption, define the success criterion and the time-box before starting, and refuse scope creep — anything not testing that assumption is out. The discipline is saying no to the interesting-but-irrelevant.

**Follow-up: What if the PoC succeeds but the code is throwaway?**
> The *code* can be throwaway; the *learning* never is. I capture the decisions, the numbers and the pitfalls so the funded build starts from evidence. Sometimes I harden the PoC into a spike that seeds the real architecture — see CE5.

---

### CE2 · How did you keep code quality consistent across a large team?

**Context.** Many engineers, one platform, regulated sector — inconsistency is a real risk to quality and security.

**The decision & why.** I **owned the coding standards, patterns and review process**: a clear, documented standard; a reference implementation people copy; and code review as a consistent gate, not a personality contest. Automated checks (lint, static analysis, tests) enforce the mechanical parts so reviews focus on design. The right way is made the easy way.

**Result.** Consistent, maintainable, secure code across a large team — quality didn't depend on which engineer wrote it.

**Lesson.** *"Consistency at scale comes from owned standards plus automated enforcement. Don't rely on heroics or memory — make the right way the default."* See [06 Quality](06-quality-engineering.md).

**Follow-up: How do you enforce standards without becoming a bottleneck?**
> Automate everything a machine can check (lint, static analysis, tests, security scans) so humans review only design and intent, and distribute review authority to trusted seniors. I set the standard; I don't gate every PR personally.

**Follow-up: How do you handle an experienced engineer who resists the standard?**
> I bring them into *setting* the standard — experienced people who help write the rules defend them. If it's genuine improvement, I adopt it; if it's just preference, I explain the cost of inconsistency at this scale. Ownership beats enforcement.

---

### CE3 · How does regulated delivery (NHS, Bupa) change how you architect?

**Context.** Health and public-sector platforms carry accessibility, security, privacy and audit obligations that aren't optional.

**The decision & why.** I treat the regulated non-functionals as **first-class from day one**, not bolt-ons: **accessibility by design** (WCAG, tested, not retrofitted), **security and privacy by design** (least privilege, data minimisation, encryption), and **auditability** built in. These constraints shape the architecture up front — retrofitting them after build is far more expensive and often fails audit.

**Result.** Platforms that pass scrutiny because compliance was designed in, not inspected in.

**Lesson.** *"In regulated sectors, accessibility, security and audit are architecture inputs, not final-QA checkboxes. Design for the audit you know is coming."*

**Follow-up: How do you make accessibility real, not a tick-box?**
> Bake it into the definition-of-done and the component library, test with real assistive tech and automated tools, and treat an accessibility failure like any other bug. If accessible components are the default building blocks, accessibility is nearly free.

**Follow-up: How do you balance regulation with delivery speed?**
> By building the compliant path into the defaults so engineers get it for free — secure components, accessible components, audit logging as a cross-cutting concern. The cost is paid once in the platform, not per feature. Discipline up front buys speed later.

---

### CE4 · How do you decide build vs buy vs reuse on an enterprise platform?

**Context.** Big enterprises have budgets and options; the wrong build-vs-buy call is expensive.

**The decision & why.** I run the decision lens: **buy or reuse** for anything that isn't a differentiator (identity, CMS, commodity components) so the team spends effort where it's unique; **build** only the parts that are genuinely the client's competitive edge or that no product fits. A PoC often settles a close call by testing the fit of a bought option against the real requirement.

**Result.** Effort concentrated on what's unique to the client; commodity needs met by proven products instead of reinvented.

**Lesson.** *"Build what's your edge; buy or reuse the rest. Reinventing commodities is how enterprise budgets get wasted."* See [21 Objections](21-objections-and-tough-questions.md).

**Follow-up: How do you avoid lock-in when you buy?**
> Put the bought product behind an interface/adapter so it's replaceable, and prefer products with open standards and export paths. The reversible-path filter again — buy, but keep the exit.

---

### CE5 · How do you turn a PoC into a production decision without throwing work away?

**Context.** A PoC that just proves a point and vanishes wastes the investment.

**The decision & why.** I **extract the learnings deliberately**: the decisions made, the numbers observed, the pitfalls found — and feed them straight into the funded architecture and the ADR log. Where the PoC code is sound, I harden it into a seed for the real build; where it's throwaway, I keep the knowledge. The PoC's output is a **de-risked design**, not just a yes/no.

**Result.** The funded build starts from evidence and a clearer architecture, so the PoC investment compounds instead of evaporating.

**Lesson.** *"A PoC's real deliverable is a de-risked decision and a better design — capture the learning even when you bin the code."*

**Follow-up: When do you harden a PoC vs rebuild from scratch?**
> Harden when the PoC code met the real standards (tests, structure, security); rebuild when it cut corners to move fast — which is fine, that was its job. I never let PoC shortcuts silently become production debt. See [58 Decision-Making](58-case-study-decision-making.md).

---

## Section index

| ID | Topic | One-line summary |
|----|-------|------------------|
| — | The story | PoC-led direction; owned standards; regulated by design |
| — | Decision log | Four ADR-style decisions with the trade-off accepted |
| CE1 | PoC to de-risk | Kill or confirm the riskiest assumption cheaply |
| CE2 | Quality at scale | Owned standards + automated enforcement |
| CE3 | Regulated delivery | Accessibility/security/audit are architecture inputs |
| CE4 | Build vs buy vs reuse | Build your edge; buy/reuse commodities behind interfaces |
| CE5 | PoC to production | The deliverable is a de-risked decision, not just code |

---

[← Case Study D: Asset-Management Reporting](56-case-study-d-asset-management-reporting.md) · [Home](README.md) · [Next → Cross-cutting Decision-Making](58-case-study-decision-making.md)
