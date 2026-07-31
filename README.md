# learning-system-designs

A comprehensive collection of hands-on tutorials and case studies on building software with AI, microservices, messaging systems, and prompt engineering — written as stories, with a consistent cast, working code, and the parts that usually go wrong left in.

---

## The AI series

Four books, in order. Each stands alone, but they're one continuous story and they build on each other.

| | Book | The idea | Scope | Tutorials |
|---|---|---|---|---|
| 1 | [**AI-Skills**](AI-Skills/README.md) | One focused instruction set, triggered automatically when a request matches it | One task | [10 chapters](#ai-skills-tutorials) |
| 2 | [**AI-Workflows**](AI-Workflows/README.md) | A fixed plan, written in advance, coordinating several pieces of work | One job | [10 chapters](#ai-workflows-tutorials) |
| 3 | [**AI-Agents**](AI-Agents/README.md) | A goal and a loop that decides its own next step from what it discovers | One investigation | [10 chapters](#ai-agents-tutorials) |
| 4 | [**AI-Agile-Development**](AI-Agile-Development/README.md) | Seven roles, thirty-six prompts, and the seams between them | One project | [36 prompts](#ai-agile-development-prompts) |

**[How the books connect](docs/how-the-three-connect.md)** — the single decision framework, and the one piece of logic followed across all of them.

### Where to start

- **Never built any of this** → [AI-Skills](AI-Skills/README.md), [Chapter 1](AI-Skills/tutorial/01-what-is-a-skill.md)
- **You prompt well alone and want to run a team that way** → [AI-Agile-Development](AI-Agile-Development/README.md)
- **You have code an AI wrote and QA says it's broken** → [P27 — Fix from a QA bug report](AI-Agile-Development/AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md)
- **You want an Azure ETL architecture more than a prompting method** → [Python ETL case study](AI-Agile-Development/Case-Study/Python-ETL/README.md)

---

## The other collections

| | What it covers | Tutorials |
|---|---|---|
| [**Prompt-Engineering**](Prompt-Engineering/README.md) | Eight chapters on prompt design patterns, prompt management and workflows, with three case studies (e-commerce, trading, dating) | [8 chapters](#prompt-engineering-chapters) |
| [**MicroServices**](MicroServices/README.md) | Service decomposition, case studies, diagrams and interview prep | [11 chapters](#microservices-tutorials) |
| [**Messaging-Systems**](Messaging-Systems/README.md) | A full mini-repo — code, diagrams, Kubernetes manifests, runbooks and a cheatsheet | [Full tutorial](Messaging-Systems/docs/tutorial.md) |
| **Langchain** | Not started | — |

---

## 📚 Tutorial Navigation

### AI-Skills Tutorials

**Start here:** [The Story](AI-Skills/00-the-story.md) | [Learning Path](AI-Skills/learning-path.md)

| # | Tutorial | What it teaches |
|---|---|---|
| 1 | [What is a Skill](AI-Skills/tutorial/01-what-is-a-skill.md) | What a skill is, in plain words, with real engineering use cases |
| 2 | [Anatomy of a Skill](AI-Skills/tutorial/02-anatomy-of-a-skill.md) | The shape every skill has, so you can read any skill on sight |
| 3 | [Your First Skill](AI-Skills/tutorial/03-your-first-skill.md) | Build a real, tiny skill from nothing |
| 4 | [Writing Trigger Descriptions](AI-Skills/tutorial/04-writing-trigger-descriptions.md) | The single hardest, most important part of any skill |
| 5 | [Tools and Scripts](AI-Skills/tutorial/05-tools-and-scripts.md) | Bundling real scripts, not just instructions |
| 6 | [Skills vs Other Tools](AI-Skills/tutorial/06-skills-vs-other-tools.md) | Skill vs. slash command vs. subagent vs. hook — the decision framework |
| 7 | [Testing and Iterating](AI-Skills/tutorial/07-testing-and-iterating.md) | Proving a skill actually works, before anyone relies on it |
| 8 | [Packaging and Sharing](AI-Skills/tutorial/08-packaging-and-sharing.md) | Versioning, and three levels of sharing |
| 9 | [Governance and Capstone](AI-Skills/tutorial/09-governance-and-capstone.md) | Safety review, and the full checklist for "is this ready?" |
| 10 | [Lifecycle of Execution](AI-Skills/tutorial/10-lifecycle-of-execution.md) | Bonus: the exact runtime sequence, from listed to loaded to executed |

**Case Studies:** [Frontend](AI-Skills/case-studies/01-frontend-skill/README.md) | [Backend](AI-Skills/case-studies/02-backend-skill/README.md) | [QA](AI-Skills/case-studies/03-qa-skill/README.md) | [Code Review](AI-Skills/case-studies/04-code-review-skill/README.md)

---

### AI-Workflows Tutorials

**Start here:** [The Story](AI-Workflows/00-the-story.md) | [Learning Path](AI-Workflows/learning-path.md)

| # | Tutorial | What it teaches |
|---|---|---|
| 1 | [What is a Workflow](AI-Workflows/tutorial/01-what-is-a-workflow.md) | What a workflow is, and why a skill alone can't do this job |
| 2 | [Anatomy of a Workflow](AI-Workflows/tutorial/02-anatomy-of-a-workflow.md) | The shape every workflow has |
| 3 | [Your First Workflow](AI-Workflows/tutorial/03-your-first-workflow.md) | Build a real, tiny workflow from nothing |
| 4 | [Parallel vs Pipeline](AI-Workflows/tutorial/04-parallel-vs-pipeline.md) | The single most important orchestration decision |
| 5 | [Fan-out and Verify](AI-Workflows/tutorial/05-fan-out-and-verify.md) | Checking from several angles, then verifying what you found |
| 6 | [Workflows vs Other Tools](AI-Workflows/tutorial/06-workflows-vs-other-tools.md) | Workflow vs. skill vs. subagent — and where Agents fit next |
| 7 | [Testing and Iterating](AI-Workflows/tutorial/07-testing-and-iterating.md) | Proving a workflow actually works, before anyone relies on it |
| 8 | [Packaging and Sharing](AI-Workflows/tutorial/08-packaging-and-sharing.md) | Versioning, sharing, and why workflows need explicit consent to run |
| 9 | [Governance and Capstone](AI-Workflows/tutorial/09-governance-and-capstone.md) | Cost governance, and the full "is this ready?" checklist |
| 10 | [Lifecycle of Execution](AI-Workflows/tutorial/10-lifecycle-of-execution.md) | Bonus: the exact runtime sequence, phase by phase, including failure paths |

**Case Studies:** [Frontend](AI-Workflows/case-studies/01-frontend-workflow/README.md) | [Backend](AI-Workflows/case-studies/02-backend-workflow/README.md) | [QA](AI-Workflows/case-studies/03-qa-workflow/README.md) | [Code Review](AI-Workflows/case-studies/04-code-review-workflow/README.md)

---

### AI-Agents Tutorials

**Start here:** [The Story](AI-Agents/00-the-story.md) | [Learning Path](AI-Agents/learning-path.md)

| # | Tutorial | What it teaches |
|---|---|---|
| 1 | [What is an Agent](AI-Agents/tutorial/01-what-is-an-agent.md) | What an agent is, and why a fixed workflow plan can't do this job |
| 2 | [Anatomy of an Agent](AI-Agents/tutorial/02-anatomy-of-an-agent.md) | The shape every agent has: goal, tools, loop, stopping condition |
| 3 | [Your First Agent](AI-Agents/tutorial/03-your-first-agent.md) | Build a real, tiny agent from nothing |
| 4 | [Tools and Grounding](AI-Agents/tutorial/04-tools-and-grounding.md) | Giving an agent tools it can choose correctly between |
| 5 | [Stopping Conditions and Budgets](AI-Agents/tutorial/05-stopping-conditions-and-budgets.md) | The limit that stops an agent from looping or drifting forever |
| 6 | [Agents vs Other Tools](AI-Agents/tutorial/06-agents-vs-other-tools.md) | Agent vs. workflow vs. skill vs. subagent vs. hook |
| 7 | [Testing and Iterating](AI-Agents/tutorial/07-testing-and-iterating.md) | Proving an agent reaches its goal, across more than one real path |
| 8 | [Packaging and Sharing](AI-Agents/tutorial/08-packaging-and-sharing.md) | Versioning, sharing, and the trust boundary a teammate shouldn't have to take on faith |
| 9 | [Governance and Capstone](AI-Agents/tutorial/09-governance-and-capstone.md) | Irreversible-action governance, and the full "is this ready?" checklist |
| 10 | [Lifecycle of Execution](AI-Agents/tutorial/10-lifecycle-of-execution.md) | Bonus: the turn-by-turn runtime trace, including both approval and grounding gates |

**Case Studies:** [Frontend](AI-Agents/case-studies/01-frontend-agent/README.md) | [Backend](AI-Agents/case-studies/02-backend-agent/README.md) | [QA](AI-Agents/case-studies/03-qa-agent/README.md) | [Code Review](AI-Agents/case-studies/04-code-review-agent/README.md)

---

### AI-Agile-Development Prompts

**Start here:** [The Story](AI-Agile-Development/00-the-story.md) | [The Cast](AI-Agile-Development/the-cast.md) | [Learning Path](AI-Agile-Development/learning-path.md)

**[📚 AI Prompts Library](AI-Agile-Development/AI-Prompts-Library/README.md)** | **[🏗 Python ETL Case Study](AI-Agile-Development/Case-Study/Python-ETL/README.md)**

#### Phase 0 — Foundation (Team Lead)
| | Prompt | The story behind it |
|---|---|---|
| P01 | [Generate Project Context File](AI-Agile-Development/AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md) | Rahul closes Tomas's laptop after AI generates code with a password — the one thing Northwind's security forbids. Make the AI read your rules once, properly. |
| P02 | [Connect the Database](AI-Agile-Development/AI-Prompts-Library/phase-0-foundation/P02-connect-the-database.md) | Azure SQL silver + Snowflake gold, managed identity not passwords, transactions that can't half-fail. Sofia asks: "What does this look like when it's wrong?" |
| P03 | [Wire Up MCP Server](AI-Agile-Development/AI-Prompts-Library/phase-0-foundation/P03-wire-up-an-mcp-server.md) | Stop the AI from hallucinating table columns. Wire it to the real schema so it stops guessing your database structure. |
| P04 | [Hooks as Guardrails](AI-Agile-Development/AI-Prompts-Library/phase-0-foundation/P04-hooks-as-guardrails.md) | The only way to guarantee secrets never reach Git. Pre-commit hooks that catch what code review misses. |
| P05 | [Turn Repeated Task into Skill](AI-Agile-Development/AI-Prompts-Library/phase-0-foundation/P05-turn-a-repeated-task-into-a-skill.md) | The team runs the same nine-step counterparty onboarding every month. Turn repetition into automation. |

#### Phase 1 — Discovery (Product Owner)
| | Prompt | The story behind it |
|---|---|---|
| P06 | [Write a Full PRD](AI-Agile-Development/AI-Prompts-Library/phase-1-discovery/P06-write-a-full-prd.md) | Amara gets a 2-page email: "stop manually keying broker statements." That's the entire brief for a signed contract. Turn vague into measurable. |
| P07 | [Slice PRD into Stories](AI-Agile-Development/AI-Prompts-Library/phase-1-discovery/P07-slice-the-prd-into-stories.md) | Break a system into pieces that can ship individually. Vertical slices that deliver value, not architectural layers. |
| P08 | [Write Acceptance Criteria](AI-Agile-Development/AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) | Put QA in the room or the criteria only cover the happy path. Divya asks the question nobody thought to test. |
| P09 | [Estimate and Rank Backlog](AI-Agile-Development/AI-Prompts-Library/phase-1-discovery/P09-estimate-and-rank-the-backlog.md) | AI assistance changes some estimates but not others. Rank by business value, capacity, and dependency reality. |

#### Phase 2 — Design (Architect)
| | Prompt | The story behind it |
|---|---|---|
| P10 | [Ultra Plan Mode](AI-Agile-Development/AI-Prompts-Library/phase-2-design/P10-ultra-plan-mode.md) | Force the AI to stop at every decision point. Design gates first, code never — until the hard questions have answers. |
| P11 | [Write Technical Spec](AI-Agile-Development/AI-Prompts-Library/phase-2-design/P11-write-the-technical-spec.md) | Not the business document. The behaviour contract: inputs, outputs, error states, and what "done" actually means. |
| P12 | [Record Architecture Decision](AI-Agile-Development/AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) | Sofia writes ADR-0003: one failing field rejects the whole document. The reason must survive the person who made the call. |
| P13 | [Design Data Contract](AI-Agile-Development/AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md) | On an ETL project, this matters more than the code. Bronze, silver, gold — define the shape before extraction starts. |
| P14 | [UI/UX Design Brief](AI-Agile-Development/AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md) | Design for Priya's 8am ritual, not a component inventory. The operations analyst's working day drives the UI. |

#### Phase 3 — Planning (Team Lead + PM)
| | Prompt | The story behind it |
|---|---|---|
| P15 | [Implementation Plan](AI-Agile-Development/AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md) | Break one story into 8 checkpoints. The app compiles and runs after every single step — no 400-line drops. |
| P16 | [Sprint Plan and Assignment](AI-Agile-Development/AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md) | Farhan maps capacity, goal, and the dependency nobody saw in planning. One story blocks three — spot it early. |
| P17 | [Definition of Done](AI-Agile-Development/AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md) | "Done" includes one non-negotiable line: a human has read every line the AI wrote. No skimming. |

#### Phase 4 — Build (Engineers)
| | Prompt | The story behind it |
|---|---|---|
| P18 | [Implement a Story](AI-Agile-Development/AI-Prompts-Library/phase-4-build/P18-implement-a-story.md) | Tomas builds the confidence gate in 8 pieces. One verifiable step at a time. The decision to avoid imports saves him 2 days in Sprint 3. |
| P19 | [Build UI from Brief](AI-Agile-Development/AI-Prompts-Library/phase-4-build/P19-build-the-ui-from-the-brief.md) | Ji-woo builds Priya's exception queue. Error states and empty states before the happy path — the part most teams skip. |
| P20 | [Write Tests Alongside Code](AI-Agile-Development/AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) | Test behaviour, not a restatement of the implementation. If the test reads like the code, it catches nothing. |
| P21 | [Daily Standup Summary](AI-Agile-Development/AI-Prompts-Library/phase-4-build/P21-daily-standup-summary.md) | Seven people, seven private AI sessions. The standup is where they reconcile what they built and what they assumed. |

#### Phase 5 — Verify (QA)
| | Prompt | The story behind it |
|---|---|---|
| P22 | [E2E Test Application](AI-Agile-Development/AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md) | Ananya's E2E suite spans a pipeline, not a browser. PDF in, Snowflake row out, recon report clean — the full journey. |
| P23 | [Review Someone Else's Code](AI-Agile-Development/AI-Prompts-Library/phase-5-verify/P23-review-someone-elses-code.md) | Rahul reviews the flagship story. AI code is beautifully formatted and reads perfectly. The classic checklist finds nothing. That's not the same as right. |
| P24 | [Find Security Gaps](AI-Agile-Development/AI-Prompts-Library/phase-5-verify/P24-find-security-gaps.md) | Attack the system like you want in. Secrets in logs, PII in exceptions, SQL injection in parameters — test like an adversary. |
| P25 | [Data Quality Validation](AI-Agile-Development/AI-Prompts-Library/phase-5-verify/P25-data-quality-validation.md) | This is the prompt that would have caught NWD-142 before it reached production. Row counts, field distributions, referential integrity. |

#### Phase 6 — Rework (The Loop)
| | Prompt | The story behind it |
|---|---|---|
| P26 | [Debug an Error Fast](AI-Agile-Development/AI-Prompts-Library/phase-6-rework/P26-debug-an-error-fast.md) | Stack trace in hand. Find the root cause, not just the symptom. This is the easy one. |
| P27 | [**Fix from QA Bug Report**](AI-Agile-Development/AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md) | **Priya's message ruins everybody's morning: "The recon's wrong." 16 positions missing. Nothing crashed. Every test passed. This is the situation the whole book exists for.** |
| P28 | [Respond to Code Review](AI-Agile-Development/AI-Prompts-Library/phase-6-rework/P28-respond-to-code-review-feedback.md) | Rahul left 9 comments. Classify each: spec ambiguity, implementation bug, style preference, nice-to-have. Fix in that order. |
| P29 | [The Spec Was Wrong](AI-Agile-Development/AI-Prompts-Library/phase-6-rework/P29-the-spec-was-wrong.md) | The code isn't broken — the spec is. The escape hatch nobody documents. Update the spec or it becomes a lie every AI session reads. |
| P30 | [When the AI Is Stuck](AI-Agile-Development/AI-Prompts-Library/phase-6-rework/P30-when-the-ai-is-stuck.md) | Same fix attempted 11 times. No progress. The sunk-cost advice people resist: stop, rubber-duck it, rebuild the prompt from scratch. |

#### Phase 7 — Release
| | Prompt | The story behind it |
|---|---|---|
| P31 | [Write Clean Git Commits](AI-Agile-Development/AI-Prompts-Library/phase-7-release/P31-write-clean-git-commits.md) | AI generates 400 lines in one commit. Split it: setup, logic, tests, docs. The archeology in 6 months depends on it. |
| P32 | [Release Readiness Check](AI-Agile-Development/AI-Prompts-Library/phase-7-release/P32-release-readiness-check.md) | Run the new pipeline in parallel with the old. Tests pass, but do the numbers match? Parallel runs catch what tests structurally can't. |
| P33 | [Write the Runbook](AI-Agile-Development/AI-Prompts-Library/phase-7-release/P33-write-the-runbook.md) | It's 3am. The on-call engineer didn't build this. Symptoms, triage steps, escalation path — write it for the worst case. |

#### Phase 8 — Improve
| | Prompt | The story behind it |
|---|---|---|
| P34 | [Clean Up Dead Code](AI-Agile-Development/AI-Prompts-Library/phase-8-improve/P34-clean-up-dead-code.md) | AI generates dead code faster than humans ever did. Five unused functions, three deprecated imports — find it before it rots. |
| P35 | [Run the Retrospective](AI-Agile-Development/AI-Prompts-Library/phase-8-improve/P35-run-the-retrospective.md) | Sprint 3 retro. "We'll be more careful" is not an action item. What broke, why it passed review, what changes to prevent it. |
| P36 | [Tech Debt Triage](AI-Agile-Development/AI-Prompts-Library/phase-8-improve/P36-tech-debt-triage.md) | List every shortcut taken under pressure. Calculate interest rate, not just principal — what's this costing us per sprint? |

---

### Prompt-Engineering Chapters

**Start here:** [Learning Path](Prompt-Engineering/learning-path.md)

| # | Chapter | What it covers |
|---|---|---|
| 1 | [Assumptions](Prompt-Engineering/chapter-01-assumptions.md) | Who this is for, and the mindset shift from search-first to prompt-first |
| 2 | [Foundations](Prompt-Engineering/chapter-02-foundations.md) | Core concepts and mental models for working with LLMs |
| 3 | [Prompt Design Patterns](Prompt-Engineering/chapter-03-prompt-design-patterns.md) | Prompt anatomy, the prompt lifecycle, and reusable patterns |
| 4 | [Prompt Management](Prompt-Engineering/chapter-04-prompt-management.md) | Versioning, tagging, testing, and prompt catalogs |
| 5 | [Workflows](Prompt-Engineering/chapter-05-workflows.md) | Integrating prompts into dev workflows, CI, and code review |
| 6 | [Case Study: E-commerce](Prompt-Engineering/chapter-06-case-study-ecommerce.md) | An e-commerce app, start to end |
| 7 | [Case Study: Trading](Prompt-Engineering/chapter-07-case-study-trading.md) | A trading platform prototype, start to end |
| 8 | [Case Study: Dating](Prompt-Engineering/chapter-08-case-study-dating.md) | A dating site MVP, start to end |

**Templates:** [Bug Fix](Prompt-Engineering/templates/prompts-bug-fix.md) | [Status Email](Prompt-Engineering/templates/prompts-status-email.md) | [Research](Prompt-Engineering/templates/prompts-research.md)

---

### MicroServices Tutorials

**Start here:** [The Example](MicroServices/tutorial/00-the-example.md) | [Tutorial Index](MicroServices/tutorial/README.md)

| # | Chapter | The problem it solves |
|---|---|---|
| 1 | [Three Axes](MicroServices/tutorial/01-three-axes.md) | East-west, north-south, and the boundary |
| 2 | [Synchronous](MicroServices/tutorial/02-synchronous.md) | The 2 a.m. incident — checkout dies during the sale |
| 3 | [Asynchronous](MicroServices/tutorial/03-asynchronous.md) | Commands vs events; 4 s → 40 ms |
| 4 | [Choosing a Broker](MicroServices/tutorial/04-choosing-a-broker.md) | Name the consumer that needs replay |
| 5 | [Gateway and BFF](MicroServices/tutorial/05-gateway-and-bff.md) | One front door, shaped per client |
| 6 | [Boundaries and Data](MicroServices/tutorial/06-boundaries-and-data.md) | One writer per entity, always |
| 7 | [Saga](MicroServices/tutorial/07-saga.md) | You cannot roll back — only apologise correctly |
| 8 | [Outbox and Idempotency](MicroServices/tutorial/08-outbox-and-idempotency.md) | The dual-write bug almost everyone ships |
| 9 | [Resilience](MicroServices/tutorial/09-resilience.md) | Timeout → retry → breaker → bulkhead → fallback |
| 10 | [Observability](MicroServices/tutorial/10-observability.md) | Correlation IDs and distributed tracing |
| 11 | [Decision Framework](MicroServices/tutorial/11-decision-framework.md) | Five questions instead of "it depends" |

**Case Studies:** [E-commerce](MicroServices/case-studies/01-ecommerce/README.md) | [Banking](MicroServices/case-studies/02-banking-payments/README.md) | [Stock Market](MicroServices/case-studies/03-stock-market-data/README.md) | [Trading](MicroServices/case-studies/04-trading-app/README.md) | [Logistics](MicroServices/case-studies/05-logistics-tracking/README.md)

**Interview Prep:** [137 Questions](MicroServices/interview-prep/README.md) | [Fundamentals](MicroServices/interview-prep/01-fundamentals.md) | [Communication](MicroServices/interview-prep/02-communication.md) | [Reliability](MicroServices/interview-prep/04-reliability.md)

---

### Messaging-Systems

**Start here:** [Tutorial](Messaging-Systems/docs/tutorial.md) | [Learning Path](Messaging-Systems/README.md#the-learning-path) | [One-Page Summary](Messaging-Systems/docs/summary-one-page.md)

**Quick Navigation:**
- **Tutorial:** [25 sections](Messaging-Systems/docs/tutorial.md) covering Kafka, Azure Service Bus, and RabbitMQ
- **Case Study:** [E-commerce backbone](Messaging-Systems/docs/case-study-ecommerce.md) — three architectures scored
- **Interview Prep:** [40 questions](Messaging-Systems/docs/interview-qa.md) with collapsible answers
- **Production:** [30 real incidents](Messaging-Systems/docs/production-incidents.md) | [Monitoring guide](Messaging-Systems/docs/monitoring.md)
- **Code Samples:** [C# examples](Messaging-Systems/code/csharp/) for all three brokers
- **Operations:** [Runbooks](Messaging-Systems/runbooks/) | [K8s manifests](Messaging-Systems/k8s/) | [Cheatsheet](Messaging-Systems/cheatsheet/cheat-sheet.md)

---

## What these have in common

Every one of them is written the same way, on purpose:

- **Story first.** A named person with a real problem, not a feature list. You remember what someone got wrong; you don't remember a bullet point.
- **Plain language before jargon.** Every term gets defined in ordinary words the first time it appears. If you'd need a search engine to follow a sentence, that sentence is a bug.
- **The failures are in.** The wrong first attempt, the argument in the design review, the bug that passed every test. That's the part that transfers.
- **Real artifacts.** Working code, actual documents, genuine bug reports — not descriptions of what they'd contain.

---

## The cast

The AI series shares a cast across all four books. [Kestrel Software](AI-Agile-Development/the-cast.md) is a consultancy; **Rahul Nair** (team lead) and **Divya Menon** (QA) appear throughout. Book four adds a project manager, product owner, architect and two engineers, plus **Priya Raman** — the operations analyst at the client who is the reason any of it exists.

---

## Licence

See individual folders. [Messaging-Systems](Messaging-Systems/LICENSE) and [Prompt-Engineering](Prompt-Engineering/LICENSE) carry their own.
