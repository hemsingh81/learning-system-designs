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
files 14–17). Also weave the hands-on angle into README (title,
positioning line), 01-overview-positioning.md (a hands-on 'who I am' and a deep-technical/coding positioning
statement), 08-cheatsheets.md (a 'hands-on code recall' table and code one-liners), 09-study-plan.md (a
hands-on coding mock), and 10-pitch-and-resume.md (a hands-on pitch version and hands-on resume/LinkedIn
wording). Aim for roughly 100–120 total interview questions across the Q&A sections;
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
