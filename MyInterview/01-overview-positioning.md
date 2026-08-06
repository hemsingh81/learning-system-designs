# 01 · Overview & Positioning

[← Home](README.md) · [Next → Technical Q&A](02-technical-qa.md)

---

## 1.1 Who I am, in one paragraph

I am a **hands-on solution architect** on the Microsoft stack. I have 19 years in software and the last 7 of those I have spent as an architect — but I never stopped writing production code. The difference matters in an interview: a senior developer is asked *"can you build it?"*; an architect is asked *"should we build it, what will it cost, what breaks first, and who owns it at 3 a.m.?"* I answer both, because on every project I designed I also **built** — the React and Angular screens, the ASP.NET Core Web APIs in C#, the Python/FastAPI ETL services, and the SQL underneath. My work sits across ASP.NET Core and C#, RESTful Web APIs and microservices on Azure, with the data tier in SQL Server, Azure SQL and Snowflake, orchestrated through Azure Data Factory, Tidal Workload Automation and Apache Airflow. Most of my clients are regulated — asset management, energy, healthcare, public sector — in the US and UK.

> **My one-line positioning:** *"I am a hands-on Solution Architect — I own the design end to end, and I still write production code myself across the full stack. Nineteen years of building is why my architecture survives contact with the code."* For the deep-technical / coding rounds, see [Full-Stack Hands-On](14-fullstack-hands-on.md).

---

## 1.2 What "7 years as an architect" actually means

When an interviewer hears "7 years", they are testing whether I have done the **architect jobs**, not just the years. Here is the honest map I use.

| Architect responsibility | Where I did it | Proof point I say out loud |
|---|---|---|
| Own end-to-end solution design | TCW investment reporting (A) | App tier + Web API layer + data pipeline, all mine |
| Decompose a system into services | TengizChevroil (C) | Four cloud apps, defined the service boundaries and Azure hosting topology |
| Define integration contracts | C and A | REST contracts between construction systems; Aladdin ingestion contracts |
| Set patterns others reuse | A | Controller + Web API pattern now reused by every reporting module |
| Own non-functional requirements | A | Daily reporting must land inside the pre-market window |
| Cost and platform choices | A, C | SQL Server vs Snowflake split; App Services vs Functions |
| Production governance | A | Incident triage, root cause, slow-query tuning, SLA ownership |
| Technical leadership of people | A, C, D | Mentoring engineers, running scrums, code-review standards |
| Innovation with a business case | B | AI/LLM reference architecture and the firm's first RAG app |
| Client-facing design authority | C, E | Presented architecture decisions to stakeholders for refinement |

**If asked "why only 7 years as architect out of 19?"** — my answer:

> "The first twelve years were deep build years. I wrote the C#, tuned the SQL, and shipped the front ends. That is exactly why my architecture is buildable. I moved into the architect seat when I started owning the decisions rather than the tickets — service boundaries, integration contracts, hosting topology, and the non-functional promises we make to the business. Seven years of that, on live regulated systems, across three countries."

---

## 1.3 The story bank — four projects, told properly

![Four anchor projects with their stacks and headline results](assets/anchor-projects.svg)

*Figure 1.1 — Anchor projects. Learn the four boxes; every answer starts from one of them.*

### Project A — Investment Reporting Platform (TCW Group, Los Angeles)

**Context.** TCW is a large US asset manager. Portfolio managers and client-reporting teams need Emerging Markets and Equity reports on their desk *before the US market opens*. The source of truth for portfolio, position and transaction data is **BlackRock Aladdin**, a third-party investment platform we consume through its API.

**My role.** Solution architect. I own the whole vertical: the React reporting screens, the ASP.NET Core Web API layer under them, the FastAPI ETL services that pull Aladdin data, and the orchestration that makes it all run on time. I lead and mentor the engineering team across the application, API and data workstreams, and I sit with business analysts and stakeholders to turn business language into technical design.

**Constraints.** A hard time window (pre-market). Third-party API rate limits and occasional late data. Financial data — so correctness beats speed, and every number must be reconcilable. Two data stores by design: SQL Server for the transactional and operational reads, Snowflake for the analytical and historical work.

**What I built.** FastAPI ETL services with automated validation, retry logic and reconciliation checks. A dependency-aware orchestration layer spanning Azure Data Factory pipelines, Tidal Workload Automation jobs and Apache Airflow DAGs, with structured logging and automated failure alerting. A reusable server-side controller and Web API pattern that replaced bespoke per-report code. A cross-platform database utility generator for Azure SQL and Snowflake that standardises script and data-access generation.

**Result.** Daily reporting lands inside the pre-market window. New reports are built on the shared pattern instead of from scratch, so the build cycle is shorter. Change traceability from schema change to release is one repeatable path.

**Lesson I quote.** *"The hard part of a data platform is not moving the data. It is proving the data is right, and proving it before a deadline."*

---

### Project B — AI/LLM Integration Framework and RAG Support Assistant (TCW Group)

**Context.** The firm wanted to use LLMs but had no agreed way to do it safely. Every team would have invented its own approach — different models, different data handling, no evaluation. That is how you get a compliance problem in a regulated firm.

**My role.** I defined the reference architecture and integration framework: a reusable pattern for **retrieval, grounding, orchestration and evaluation**. Then I proved it by delivering the first end-to-end implementation on it.

**What I built.** A RAG support-assistant application. It indexes support emails, Confluence runbooks and past response threads into a **Chroma** vector database, and answers recurring support questions with grounded, cited answers. Built on LangChain for the chain, LangGraph for the multi-step orchestration, and LangSmith for tracing and evaluation.

**Result.** TCW's first production RAG application, and a pattern the firm now reuses. Support engineers get grounded answers to repeat issues in minutes instead of digging through mail archives.

**Lesson I quote.** *"With LLMs, the architecture is not the model. The model is a commodity. The architecture is retrieval quality, grounding, and the evaluation loop that tells you when it degrades."*

---

### Project C — Construction Completion Platform (TengizChevroil, Kazakhstan)

**Context.** TengizChevroil runs one of the world's largest oil and gas expansion projects. "Completion" is the process of proving that thousands of pieces of equipment have been built, tested, commissioned and handed over. It was running on paper, spreadsheets and email across many contractors.

**My role.** Solution architect, on site. I defined the microservices decomposition, the Azure hosting topology (App Services, Functions, Blob Storage, Azure SQL) and the integration contracts between systems. I also mentored engineers on Azure, microservices and API design, and presented architecture decisions to stakeholders.

**What I built.** Four cloud applications on ASP.NET Core and Azure Functions — commissioning certificates, contract transfer, exception handling and change notice. An ETL and orchestration layer on Azure Data Factory and Azure Functions with a validation stage. SQL Server schemas modelled for query performance, integrity and governance across completion, commissioning and change management. REST API contracts for real-time exchange between construction systems, with Angular and jQuery front ends. Power BI dashboards covering Workdown, Mechanical Completion, RFO and Commissioning. Azure DevOps CI/CD pipelines and a release strategy.

**Result.** Manual effort down **60%**. Processing errors down **25%**. Release cycle time **halved**. Leadership got real-time completion tracking instead of a weekly spreadsheet.

**Lesson I quote.** *"In heavy industry, adoption is the architecture problem. If the approval screen does not fit how a commissioning engineer actually works, the best design on paper stays unused."*

---

### Project D — Asset-Management Reporting (Sculptor Capital, New York · Bain Capital, Boston)

**Context.** Two US alternative-investment managers. Both needed reporting they could trust, and both were doing too much of it by hand.

**My role.** Architected and delivered the web applications, owning technical design from requirements through production release. I also ran sprint planning and daily scrums.

**What I built.** ASP.NET MVC and Web API applications with Knockout and AngularJS front ends. Automated ETL pipelines in Azure Data Factory for ingestion, transformation and validation. Interactive reporting in Power BI and IBM Cognos.

**Result.** Manual processing down **30%**. Decision turnaround up **20%**. Team velocity up **20%** and post-deployment defects down **15%**.

**Lesson I quote.** *"Velocity is a by-product of clarity. We got 20% faster mostly by cutting rework, not by working harder."*

---

### Project E — UK Enterprise Web Platforms (Bupa, NHS e-Contracting, Unilever)

**Context.** Content-managed and transactional platforms for UK healthcare, public sector and FMCG, on Sitecore and SDL Tridion, delivered on-site in London.

**Use it for.** Proof-of-concept work presented to client stakeholders, shaping solution direction before build. Owning coding standards and code review across a team. Regulated and public-sector delivery discipline.

---

## 1.4 Frameworks I use to answer, so I never ramble

### For a behavioural or leadership question — **STAR-D**

| Step | What I say | Time |
|---|---|---|
| **S**ituation | One line of context. Client, system, stake. | 15s |
| **T**ask | What I specifically owned. Not "we". | 10s |
| **A**ction | Two or three decisions I made, and what I rejected. | 60s |
| **R**esult | A number. Always a number. | 15s |
| **D**ifference | What I do differently now. This is what juniors leave out. | 15s |

### For a technical or design question — **C-QUAD**

| Step | What I cover |
|---|---|
| **C**larify | Ask two questions before answering. Scale, and the hard constraint. |
| **Q**ualities | Name the non-functionals that will drive the design (latency, correctness, cost, RPO/RTO). |
| **A**rchitecture | Draw or describe the boxes and the data flow. |
| **A**lternatives | Name the option I did *not* pick, and why. |
| **D**ownside | State the weakness of my own design and how I would monitor it. |

> Interviewers score the **Alternatives** and **Downside** steps highest, and most candidates skip both.

### For a "tell me about a failure" question — **OAR**

**O**wn it plainly → **A**ction I took to contain it → **R**ule I now apply.
No blaming a vendor, a junior, or "the business".

---

## 1.5 My positioning statements, by interviewer type

**To a hiring manager (delivery focus):**
> "I take a business promise — reports before market open, or a completion certificate approved in a day not a week — and I make it a system that keeps that promise on a Monday morning without me in the room."

**To a CTO or chief architect (technical depth focus):**
> "I work top-down and bottom-up at the same time. I set the service boundaries and integration contracts, and I still read the execution plan when a report is slow. Nineteen years of building is why my designs survive contact with the code."

**To a deep-technical / coding panel (hands-on focus):**
> "I am not a diagram-only architect. I still ship code across the stack — React and Angular front ends, ASP.NET Core Web APIs in C#, FastAPI ETL in Python, and the T-SQL underneath. Open the hood and I will write the endpoint, the query, or the component with you. The code samples are in [Full-Stack Hands-On](14-fullstack-hands-on.md)."

**To a client or pre-sales panel (commercial focus):**
> "I have been the architect in the room when regulated clients decide where their money goes. I write the solution outline, I stand behind the estimate, and I stay on the account through delivery and support — so what I promise in the proposal is what I have to run in production."

**To an AI-focused interviewer:**
> "I built the firm's AI/LLM reference architecture before I built the AI app — retrieval, grounding, orchestration, evaluation. Then I proved it with a production RAG assistant. I treat LLM work like any integration: contracts, observability, evaluation, and a rollback story."

---

## 1.6 Weak spots I prepare for, and how I answer honestly

| Likely challenge | My honest answer |
|---|---|
| "You are Azure-heavy. Do you know AWS?" | "My depth is Azure. The concepts move — App Services to ECS/Fargate, Functions to Lambda, ADF to Glue or Step Functions, Azure SQL to RDS, Entra ID to IAM and Cognito. I would need weeks on the tooling, not on the architecture." |
| "Have you run Kubernetes in production?" | "My production hosting has been App Services, Azure Functions and Container Apps, because that fit the operating model of my clients. I have designed the container topology and understand the AKS trade-off — I have chosen managed platforms deliberately to avoid the ops overhead, not to avoid the tech." |
| "You have not worked at internet scale." | "Correct. My scale problems are throughput inside a deadline and correctness on financial data, not a million concurrent users. That trade-off shows up in different places — I optimise for reconcilable, on-time and auditable." |
| "You are a contractor / you move clients." | "I stay where the problem is. Four years on-site at Tengiz, six years with Sapient clients in asset management. I am not a short-stay consultant; I own production." |
| "Only 7 years as an architect." | See [1.2](#12-what-7-years-as-an-architect-actually-means). |

---

## 1.7 Questions I ask them (always ask three)

1. "Who owns the non-functional requirements today — is that this role, or is it shared with the platform team?"
2. "When an architecture decision is contested, how does it get settled? Is there a design authority or an ADR process?"
3. "What is the one system in the estate that everyone is nervous about? That usually tells me what the first six months look like."

---

[← Home](README.md) · [Next → Technical Q&A](02-technical-qa.md)
