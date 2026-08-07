# 13 · Reproduce Prompt

[← Checklists](12-checklists.md) · [Home](README.md) · [Next → Full-Stack Hands-On](14-fullstack-hands-on.md)

This is the single prompt to regenerate or extend this kit with a future model (e.g. Claude Opus 5). It is self-contained: paste it, attach the resume, and it will rebuild the kit in the same voice and structure. Below the prompt are notes on how to extend rather than regenerate.

---

## The prompt (copy everything in the block)

```text
You are an expert career coach and solution architect. Build me a complete, navigable, interview-ready
learning kit as a set of Markdown files for a HANDS-ON Solution Architect named Hem Singh (19 years in
software, the last 7 as an architect, Microsoft/Azure & .NET focus) who still writes production code across
the full stack (React/Angular front end, ASP.NET Core Web API and C#, Python/FastAPI ETL, and T-SQL). The
overall positioning must be 'a Solution Architect with hands-on full-stack delivery' — someone who owns the
design end to end AND codes it himself. Ground EVERY example strictly in the attached resume
(Hem_Singh.pdf) — use only real projects, clients, stacks, roles, and metrics from it; invent nothing. Write
all model answers in the first person ("I designed…", "I built…", "I own…") in extremely simple English with short
sentences, and make every answer concrete: a story, the decision, the trade-off, and a measurable number.
Bias technology examples toward the Microsoft/Azure ecosystem and include short code or config samples where
they genuinely help. Anchor everything to five reusable projects, labelled A–E, and reference them by code
throughout: A = TCW Group investment-reporting platform + BlackRock Aladdin ingestion into SQL Server and
Snowflake with dependency-aware orchestration across Azure Data Factory, Tidal and Apache Airflow, landing
reporting inside the daily pre-market window; B = TCW's AI/LLM integration reference architecture (retrieval,
grounding, orchestration, evaluation) and the firm's first production RAG support assistant built with
LangChain, LangGraph, LangSmith and a Chroma vector database; C = TengizChevroil construction-completion
platform, four cloud apps on ASP.NET Core and Azure Functions with a microservices decomposition and Azure
DevOps CI/CD (60% less manual effort, 25% fewer processing errors, 50% shorter release cycle); D = reporting
and ETL for Sculptor Capital and Bain Capital (30% less manual processing, 20% faster decisions, +20%
velocity, −15% defects); E = UK enterprise web platforms for Bupa, NHS e-Contracting and Unilever (PoCs,
pre-sales, code standards, regulated/public sector). Produce these files under a folder named MyInterview,
using exactly these names: README.md (with a Contents table, the five anchor projects, a 'quick numbers'
table, and the three-sentence opening); 01-overview-positioning.md (story bank, STAR-D and C-QUAD answer
frameworks); 02-technical-qa.md (~22 questions across .NET, Azure, APIs, data, security, DevOps,
observability, and AI/RAG); 03-system-design.md (8 full design scenarios, each with a diagram); 
04-team-management.md (10 questions on hiring, mentoring, conflict, scope change, hard messages);
05-client-engagement.md (8 questions on proposals, negotiation, PoCs, change requests, follow-ups);
06-rfp-presales.md (7 questions on leading responses, solution outlines, estimates, win themes, plus a
reusable response outline and checklist); 07-support-post-delivery.md (8 questions on deadline-driven
production support, incident handling, root-cause analysis, slow-query tuning, data discrepancies,
runbooks/knowledge transfer, the RAG support assistant, and turning support into more work, plus a runbook
template); 08-cheatsheets.md (one-page recall: numbers, anchor projects, stack, Azure services, patterns,
AI/RAG pillars, orchestration, an NFR checklist, power phrases, and the frameworks); 09-study-plan.md (a
2-week and a 1-week plan, a night-before routine, three timed mock-interview scripts, and a self-scoring
rubric); 10-pitch-and-resume.md (30-second and 2-minute pitches, a pre-sales pitch, a 'why me' trio, a
paste-ready one-page resume summary, and LinkedIn headline options); 11-email-templates.md (adaptable
templates for a proposal cover, post-demo follow-up, scope/change request, support handover, incident
notification, and estimate-with-assumptions, plus writing rules); 12-checklists.md (bid/no-bid, pre-sales
activity, solution outline, estimate, design review, go-live readiness, support handover, and interview-day);
13-reproduce-prompt.md (this prompt); and 14-fullstack-hands-on.md (12 hands-on, CODE-BACKED questions
proving he still builds — a clean ASP.NET Core Web API endpoint, correct async C#, EF vs Dapper and killing
N+1, a FastAPI ETL ingestion endpoint with validation/retry/reconciliation, a React data screen handling the
four states with an AbortController, React state vs server-cache, an Angular service+component, hand-written
sargable T-SQL, end-to-end Entra ID auth across front end and API, centralised error handling per layer,
testing with real xUnit/pytest/RTL samples, and a hands-on production debugging walkthrough — each answer
must include a real code sample in the relevant language); 15-deepdive-dotnet.md (10 advanced .NET/C#
questions with code: DI & service lifetimes and the captive-dependency trap, the middleware pipeline and
ordering, LINQ deferred execution and IQueryable vs IEnumerable, allocations/GC and Span on hot paths,
concurrency beyond async/await, resilience with Polly (retry/backoff/jitter, circuit breaker, timeout),
caching with invalidation, EF Core advanced (AsNoTracking, rowversion concurrency, ExecuteUpdate/Delete),
minimal APIs vs gRPC, and configuration/options/secrets via Key Vault + managed identity);
16-deepdive-react-typescript.md (10 advanced React + TypeScript questions with code: generics and
discriminated unions for the four states, typing components/props precisely, hooks and what re-renders,
useEffect with cleanup and honest dependencies, performance (memo/useMemo/useCallback, virtualisation),
custom hooks, schema-first forms with Zod + React Hook Form, error boundaries and Suspense, testing with
React Testing Library by role/behaviour, and component patterns + accessibility for regulated clients);
17-deepdive-python-data.md (10 advanced Python/data questions with code: async and the GIL, Pydantic v2
validation at the boundary with Decimal for money, vectorised Pandas, idempotent loads with reconciliation,
SQL tuning and sargability, Snowflake vs SQL Server operational/analytical split, orchestration DAGs across
Airflow/ADF/Tidal, RAG code behind the four pillars, packaging/typing/quality (mypy, ruff, pytest), and
testing data pipelines); 18-coding-round-prep.md (a playbook for BOTH coding-interview formats — a DSA/
algorithms section with a pattern table, complexity guidance and worked examples in C#, TypeScript and
Python, and a feature-building section with a 6-step method, a scoring table and a drill list cross-linked to
files 14–17); 19-performance-deep-dive.md (12 in-depth performance questions split into Front-end,
Backend and Database — each with a real project story from the TCW reporting platform, measurable before/after
results, the exact tools that help and how (Lighthouse, DevTools, React Profiler, bundle analyzer, web-vitals
+ App Insights, React Query, react-window; Application Insights/OpenTelemetry, k6/Azure Load Testing,
dotnet-trace/counters, memray; SQL execution plan, Query Store, Profiler/Extended Events, DMVs, Tuning
Advisor), and follow-up Q&As, plus a tools summary table); 20-ai-assisted-development.md (a complete
start-to-end playbook for setting up AI-assisted development in a team — an end-to-end flow diagram, how to
start with a small measured pilot, roles and who does what, controlling AI behaviour while writing code via
repo rules + human ownership + automated gates, QA/testing with AI, security both into and out of the AI,
performance metrics balancing speed and quality, an automatic honest daily report, the order of work in a
sprint, writing the PRD with AI, a 90-day rollout plan, and four interview Q&As with follow-ups — grounded in
the candidate's TCW AI/LLM reference architecture and first production RAG app);
21-objections-and-tough-questions.md (10 tough interviewer challenges with calm first-person rebuttals and
follow-ups — still hands-on enough, only 7 years as architect, jack-of-all-trades, only Microsoft, rusty coder,
big-picture vs details, built vs just managed, will AI replace architects, overqualified, biggest weakness —
each following 'agree with the fair part, correct the wrong part, give one piece of evidence' and grounded in
projects A/B/C with real metrics); 22-panic-sheet.md (a single one-page 'last 2 minutes' recall sheet — the
opening line, the four anchor projects, the must-land numbers, five phrases, the two frameworks, a 'reset' routine
for when a question floors you, and three things to do in the room — no new content, pure recall linking back to
the fuller files); 23-offer-negotiation.md (8 first-person Q&As on the compensation conversation — handling
'what's your current salary', giving a researched expectation range, countering a low offer, justifying the number
with measured impact, trading beyond base (sign-on, bonus/equity, early review, leave, flex, title), competing
offers, decide-today pressure, and accepting/declining gracefully — calm, evidence-based, never adversarial);
24-role-tailoring-guide.md (a 20-minute routine to adapt the kit to a specific job description — how to read a
JD for its centre of gravity, a table mapping JD emphasis to the right anchor projects and files, choosing the
right pitch version and one lead story, four ready role profiles (data-platform, AI, hands-on, consulting), and a
gaps/red-flag check with questions to ask back); 25-star-story-bank.md (10 fully-written behavioural stories in
STAR-D form — failure, conflict, influence without authority, tight deadline, difficult stakeholder, disagreeing
with a decision, mentoring, ambiguity, a production crisis, and proudest achievement — each anchored to a real
project A–E with a number and a one-line lesson, plus follow-ups and a section index); 26-reverse-interview-questions.md
(the sharp questions the candidate asks the panel, grouped by audience — hiring manager, peer architect/engineer,
CTO/senior leader, HR/recruiter — a 'top 5 if short on time', a 'what their answers tell me' signal table, and a
'questions I never ask' list); 27-first-90-days.md (a ready first-person answer to 'what would you do in your
first 90 days?' — three phases: Days 0–30 Listen & Learn (meet people, trace a request end to end, learn how it
ships, find the real pain, change nothing big), Days 30–60 Plan & Small Wins (agreed plan socialised not imposed,
a few low-risk visible wins, gentle standards), Days 60–90 Deliver (ship one measurable improvement end to end,
prove it with a number, set a team-owned direction), with a Mermaid three-phase diagram, a 90-second spoken
version, follow-ups and a section index). Then add TEN concept deep-dive files, each with AT LEAST 30 top
interview Q&As written in the same voice (simple English, first person, architecture and full-stack-developer
lens, code samples where useful, all front-end code in TypeScript), each Q&A having a concise question, a
model answer, and follow-up questions with short answers, and each file using a per-topic letter+number ID
scheme with a 'Jump to' line and a 'Section index' table: 28-concept-reactjs.md (React fundamentals through
advanced — components/JSX, state, hooks, useReducer/useRef, VDOM, effects, performance, routing, TypeScript,
Suspense/lazy, error boundaries, security, testing, micro-frontends, design systems, real-time, and when to
choose React); 29-concept-angular.md (modern Angular — components/modules, data binding, DI, RxJS + signals,
change detection, lifecycle, standalone components, guards/resolvers, reactive forms, pipes/directives, i18n,
CLI, SSR/Universal, Material, and when to choose Angular); 30-concept-react-vs-angular.md (a fair,
feature-by-feature comparison — components, forms, routing, DI, reactivity, tooling, testing, SSR, ecosystem,
bundle size, hiring, mobile, upgrades, security, accessibility, myths, TCO — ending in a one-minute decision
framework); 31-concept-aspnet-webapi.md (ASP.NET Core Web API — controllers/minimal APIs, DI, middleware,
model binding/validation, EF Core, auth with Entra ID, versioning, performance, testing, hosting/deployment);
32-concept-fastapi.md (FastAPI — async, Pydantic, dependency injection, auth, background tasks, middleware,
testing, deployment, and ETL usage grounded in projects A/D); 33-concept-webapi-vs-fastapi.md (when to pick
.NET vs Python side by side, with a decision framework); 34-concept-sql-server.md (indexes, execution plans,
transactions/isolation, tuning, concurrency, security, HA/DR, T-SQL); 35-concept-snowflake.md (architecture,
virtual warehouses, micro-partitions, clustering, cost control, data sharing, performance, Time Travel);
36-concept-sqlserver-vs-snowflake.md (OLTP vs analytics, cost models, when to use each, with a decision
framework); and 37-concept-azure-services.md (Blob Storage, Key Vault, App Service, Service Bus, Functions,
managed identity, App Insights, and Azure AI Foundry, grounded in the candidate's Azure projects). Wire file
27's forward navigation to 28, chain 28→37 in order and loop 37 back to Home, and add the concept files to
the README Contents table and a 'Concept deep-dives' quick-index row. Also add to README a 'Quick index by
interview round' jump table mapping each round type to the right file(s), and wire files 19/20/21 into the
study plan (a performance+AI day, a new
'Mock E — AI-in-team leadership round', and objections drilling) and into the cheat sheets (a 'Performance
recall' and an 'AI-in-team recall' section). Also weave the hands-on angle into README (title,
positioning line), 01-overview-positioning.md (a hands-on 'who I am' and a deep-technical/coding positioning
statement), 08-cheatsheets.md (a 'hands-on code recall' table and code one-liners), 09-study-plan.md (a
hands-on coding mock), and 10-pitch-and-resume.md (a hands-on pitch version and hands-on resume/LinkedIn
wording). Aim for roughly 440+ total interview questions across the Q&A sections (the ten concept files 28–37
contribute 30 each);
each question must have a concise interviewer-style prompt, a model answer of 2–6 short paragraphs following
Story → Approach → Trade-off → Outcome-with-a-number → Lesson, and 2–4 follow-up prompts each with a short
reply. Enforce these conventions in every file: a top H1 header stating the section number, title and
question count (e.g. '# 07 · Support & Post-Delivery (8 questions)'); a nav footer AND header of the form
'[← Previous](file.md) · [Home](README.md) · [Next → ...](file.md)'; a 'Jump to' anchor-link line near the
top; a 'Section index' table near the bottom summarising each question's core message; consistent use of the
anchor-project codes A–E; and store any diagrams as SVGs under an assets/ subfolder referenced with relative
paths and descriptive alt text. Keep the tone credible and non-salesy, prefer specifics over adjectives
('recovers by replaying from the last checkpoint without duplicating data', never 'robust and scalable'), and
make internal cross-links between files wherever one answer references another. Verify at the end that the
README Contents table, the file names, and every internal link are mutually consistent.
```

---

## How to extend instead of regenerate

If the kit already exists and you only want to add or improve, do **not** paste the full prompt. Instead give the model a scoped instruction like:

> "Here is my existing MyInterview kit. Keep the exact style, conventions, and anchor projects A–E. Add a new file `14-negotiation-deep-dive.md` with 6 questions on commercial negotiation, grounded only in the attached resume, following the same header/footer/jump-to/section-index conventions. Then update the README Contents table and the nav links in the adjacent files."

### Extension ideas that stay true to the resume

| Idea | Grounded in |
|------|-------------|
| Deep-dive on **Aladdin integration** — entity types, reconciliation, edge cases | Project A |
| Deep-dive on **the AI/LLM reference architecture** — the four pillars in detail, evaluation harness | Project B |
| **Microservices decomposition** worked example — the four completion apps and their contracts | Project C |
| **On-site regulated delivery** — stakeholder management, working abroad, public/regulated sector | Projects C, E |
| **AI-assisted development rollout** — GitHub Copilot adoption, usage/review guidelines | TCW, Project B |
| **Cross-platform DB utility generator** — standardising script/data-access generation | TCW, Project A |

### Rules for any extension

1. **Resume-true only.** Every new example must trace to something in `Hem_Singh.pdf`. No invented clients, tools, or numbers.
2. **Match the conventions.** Header with question count, header + footer nav, jump-to line, section-index table, anchor codes A–E.
3. **Update the index.** Any new file means updating the README Contents table, the total question count, and the nav links in the two adjacent files.
4. **Keep the voice.** First person, simple English, specific over adjective, always land a number.

---

[← Checklists](12-checklists.md) · [Home](README.md) · [Next → Full-Stack Hands-On](14-fullstack-hands-on.md)
