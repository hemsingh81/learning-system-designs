# AI-Sets — Master Plan

**Project:** A hands-on tutorial that teaches **AI Skills → AI Workflow → AI Agent → Agentic AI**
**Audience:** A backend software engineer with **no prior AI experience**
**Local path:** `C:\Users\hemsingh9\source\repos\AI-Sets`
**Status:** PLAN ONLY — no code or tutorial content written yet. Waiting for approval.

---

## 0. How to read this plan

This document is the contract. Every later step just executes what is written here.

- **Section 1** explains the four big ideas we will teach, in simple words.
- **Section 2** locks the technology choices, with a decision log.
- **Section 3** is the full folder and file map we will create.
- **Section 4** is the milestone-by-milestone work plan (M0 … M9) with tasks, outputs, and time estimates.
- **Section 5** covers testing, **Section 6** covers docs standards, **Section 7** covers risks.
- **Section 8** is the approval checklist and the open questions for you.

---

## 1. What we are teaching (the learning spine)

We teach four levels. Each level adds exactly **one** new idea on top of the level before it. This is the whole point of the project: you should be able to say *"level N+1 is level N plus this one thing."*

```
LEVEL 1 — SKILL
  One small unit of AI work. Input in, output out. No memory. No decisions.
  Analogy: a single REST endpoint or a pure function.
  Example: "summarize this support ticket".

           + fixed order, wired by YOU
                     v
LEVEL 2 — WORKFLOW
  Several skills chained in an order that a HUMAN decided at design time.
  The path is the same every run. Retries and validation live here.
  Analogy: a CI/CD pipeline, or a message-queue consumer chain.
  Example: classify -> extract fields -> draft reply -> validate.

           + the MODEL picks the order, and can use tools
                     v
LEVEL 3 — AGENT
  A loop: think -> choose a tool -> run it -> look at the result -> repeat.
  The path changes per run. The model decides, not you.
  Analogy: a junior engineer with a runbook and shell access.
  Example: "why did order 8842 fail?" -> reads DB -> reads logs -> answers.

           + goals, memory, planning, self-checks, many agents, humans in the loop
                     v
LEVEL 4 — AGENTIC AI
  A system, not a call. It owns a goal over time. It plans, it remembers,
  it recovers from failure, it knows when to stop, and it escalates to a
  human when the risk is too high.
  Analogy: an on-call team with an incident runbook and an escalation policy.
  Example: the incident-triage case study in Milestone 8.
```

**The single sentence we will repeat in every module:**
> A *skill* does one thing. A *workflow* is a path **you** chose. An *agent* is a path the **model** chooses. *Agentic AI* is an agent that owns a **goal**, with memory, safety limits, and an escape hatch to a human.

---

## 2. Technology decisions (locked)

### 2.1 Primary language: **Python 3.11+**

- Detected on this machine: **Python 3.14.4**, **Node v24.14.0**. Both fine.
- **Python is PRIMARY.** All code is complete and runnable in Python.
- Node.js appears **only once**, as a small side-by-side port of one skill in `appendix/nodejs-port/`, clearly labelled "reference only, not maintained". This satisfies "mark one as primary".

### 2.2 The most important design decision: **it must run with zero API keys**

Every module ships two model backends behind one interface:

| Backend | What it is | When used |
|---|---|---|
| `FakeLLM` | Deterministic, scripted, offline. No network. No cost. | **Default.** All tests. First run of every example. |
| `ClaudeLLM` | Real Anthropic API via the `anthropic` SDK. | Opt-in via `.env` (`LLM_BACKEND=claude`). |

Why this matters: a learner can clone, run `pytest`, and see everything pass in under a minute — no signup, no card, no rate limits. Then they flip one env var and watch the *same* code talk to a real model. This also makes every test fast and deterministic, which is otherwise the hardest problem in AI tutorials.

### 2.3 Dependency list (deliberately small)

| Package | Why | Note |
|---|---|---|
| `anthropic` | Real LLM calls | Optional at runtime; import guarded |
| `pydantic` | Validate model output into typed objects | Core teaching tool for "AI output is untrusted input" |
| `python-dotenv` | Load `.env` | |
| `fastapi` + `uvicorn` | Milestone 9 only: expose an agent as an HTTP service | Shows the backend-engineer angle |
| `httpx` | Test client for FastAPI | |
| `pytest`, `pytest-cov` | Tests | |
| `rich` | Readable console output for example runs | |

No LangChain, no LlamaIndex, no CrewAI, no vector DB. **Reason:** frameworks hide the loop, and the loop is exactly what we are teaching. We will add a short doc — `docs/09-frameworks-and-when-to-use-them.md` — explaining what those frameworks do, so you know what you're opting out of and when to opt back in.

### 2.4 Decision log (the format we will reuse in every module)

Every module gets a `DECISIONS.md` with this exact shape:

```
### D-<id>: <the question>
Options:
  A) <option>  — pros: ...  cons: ...
  B) <option>  — pros: ...  cons: ...
Chosen: <A/B>
Why: <2-4 simple sentences>
Revisit if: <the condition that would flip this decision>
```

Project-level decisions already made:

| ID | Question | Chosen | Why |
|---|---|---|---|
| D-001 | Python or Node as primary | **Python** | Most AI examples/docs are Python; simple syntax for beginners; Node port kept as an appendix. |
| D-002 | Framework or raw SDK | **Raw SDK** | The agent loop is ~40 lines. Frameworks hide it. You cannot debug what you cannot see. |
| D-003 | Real API required to learn | **No — FakeLLM default** | Zero cost, zero setup, deterministic tests. Real API is a one-line opt-in. |
| D-004 | Where does typing/validation live | **Pydantic at every AI boundary** | Model output is untrusted input, exactly like a request body. This is the #1 habit for backend engineers. |
| D-005 | Sync or async code | **Sync** | Beginners first. One async example in the appendix showing parallel tool calls and the latency win. |
| D-006 | Tests: mock the model or hit it | **Mock (FakeLLM) for all CI tests** | Non-deterministic tests are worthless. One `@pytest.mark.live` suite hits the real API, skipped by default. |
| D-007 | Case-study domain | **Backend incident triage** (see M8) | Familiar to the audience; naturally needs tools, failure handling, and escalation. |
| D-008 | Persistence | **SQLite + JSON files** | No Docker, no server. Learner can open the file and look at it. |

---

## 3. Folder and file map

Everything below is created under `C:\Users\hemsingh9\source\repos\AI-Sets\`.
Paths in the tutorial will always be written relative to that root.

```
AI-Sets\
├─ README.md                        <- front door: what this is, 5-minute quickstart
├─ pyproject.toml                   <- deps, pytest config, package metadata
├─ requirements.txt                 <- plain pip fallback
├─ .env.example                     <- every setting, documented, safe defaults
├─ .gitignore
├─ Makefile                         <- optional; Windows users use scripts\ instead
│
├─ scripts\                         <- Windows-first entry points
│  ├─ setup.ps1                     <- venv + install + verify, one command
│  ├─ run-example.ps1               <- run any example by name
│  ├─ test.ps1                      <- pytest with coverage
│  └─ verify-env.ps1                <- the environment checklist from Req 9
│
├─ docs\
│  ├─ 00-PLAN.md                    <- THIS FILE
│  ├─ 01-concepts.md                <- the 4 levels, analogies, ASCII diagrams
│  ├─ 02-setup-windows.md           <- exact Windows setup, step by step
│  ├─ 03-llm-basics.md              <- tokens, prompts, temperature, context window, cost
│  ├─ 04-prompting-guide.md         <- how to write a prompt like an API contract
│  ├─ 05-testing-ai-code.md         <- how to test something non-deterministic
│  ├─ 06-security-and-privacy.md    <- prompt injection, secrets, PII, tool permissions
│  ├─ 07-cost-and-latency.md        <- how to measure and reduce both; tradeoff tables
│  ├─ 08-troubleshooting.md         <- error -> log sample -> cause -> fix
│  ├─ 09-frameworks-and-when-to-use-them.md
│  ├─ 10-glossary.md                <- every term in one line of simple English
│  └─ diagrams\                     <- .md files of ASCII diagrams, reused elsewhere
│
├─ src\aisets\
│  ├─ __init__.py
│  ├─ config.py                     <- typed settings from .env
│  ├─ logging_setup.py              <- structured JSON logs (trace ids)
│  ├─ llm\
│  │  ├─ base.py                    <- LLMClient protocol: complete(), complete_json()
│  │  ├─ fake.py                    <- FakeLLM: scripted, deterministic
│  │  ├─ claude.py                  <- ClaudeLLM: real API + retry + timeout
│  │  ├─ usage.py                   <- token + cost accounting
│  │  └─ errors.py                  <- RateLimited, Timeout, BadOutput, Refused
│  │
│  ├─ skills\                       <- LEVEL 1
│  │  ├─ base.py                    <- Skill ABC: validate_input -> run -> validate_output
│  │  ├─ classify_ticket.py
│  │  ├─ extract_fields.py
│  │  ├─ summarize_log.py
│  │  ├─ draft_reply.py
│  │  └─ score_severity.py
│  │
│  ├─ workflow\                     <- LEVEL 2
│  │  ├─ engine.py                  <- Step, Pipeline, run() with retry/timeout
│  │  ├─ context.py                 <- the data bag passed between steps
│  │  ├─ policies.py                <- retry, backoff, fallback, circuit-breaker
│  │  └─ ticket_pipeline.py         <- the concrete 4-step example workflow
│  │
│  ├─ agent\                        <- LEVEL 3
│  │  ├─ loop.py                    <- the think->act->observe loop (small + commented)
│  │  ├─ tools.py                   <- @tool decorator, JSON schema generation
│  │  ├─ registry.py                <- tool registry + permission flags
│  │  ├─ memory.py                  <- short-term (turns) + long-term (SQLite)
│  │  └─ simple_agent.py            <- the first agent: 3 tools, 5-step budget
│  │
│  ├─ agentic\                      <- LEVEL 4
│  │  ├─ goal.py                    <- goal, success criteria, stop conditions
│  │  ├─ planner.py                 <- make a plan, then re-plan when reality differs
│  │  ├─ critic.py                  <- self-check step: "did we actually meet the goal?"
│  │  ├─ escalation.py              <- risk scoring -> human approval gate
│  │  ├─ budget.py                  <- caps on steps, tokens, money, wall-clock
│  │  └─ orchestrator.py            <- multi-agent coordination (supervisor pattern)
│  │
│  └─ tools\                        <- the fake "production" backend the agent acts on
│     ├─ db.py                      <- SQLite queries over sample data
│     ├─ logs.py                    <- search a sample log file
│     ├─ metrics.py                 <- read sample metrics JSON
│     ├─ runbook.py                 <- retrieve runbook docs (simple keyword search)
│     └─ actions.py                 <- WRITE actions: restart, scale, page (all simulated)
│
├─ examples\                        <- every example is `python examples\NN_x.py`
│  ├─ 01_skill_hello.py
│  ├─ 02_skill_classify.py
│  ├─ 03_skill_structured_output.py
│  ├─ 04_skill_failure_modes.py
│  ├─ 05_workflow_sequential.py
│  ├─ 06_workflow_branching.py
│  ├─ 07_workflow_retry_and_fallback.py
│  ├─ 08_agent_first_loop.py
│  ├─ 09_agent_with_memory.py
│  ├─ 10_agent_guardrails.py
│  ├─ 11_agentic_goal_and_plan.py
│  ├─ 12_agentic_self_correct.py
│  ├─ 13_agentic_escalation.py
│  ├─ 14_agentic_multi_agent.py
│  ├─ 15_case_study_incident_triage.py
│  └─ 16_serve_agent_api.py
│
├─ tutorial\                        <- the READING material, one folder per lesson
│  ├─ 00-start-here.md
│  ├─ 01-skills\  { README.md, DECISIONS.md, EXERCISES.md }
│  ├─ 02-workflows\ { same three files }
│  ├─ 03-agents\    { same three files }
│  ├─ 04-agentic\   { same three files }
│  └─ 05-case-study\{ README.md, DECISIONS.md, RUNBOOK.md, POSTMORTEM-EXERCISE.md }
│
├─ data\                            <- sample data so examples produce real output
│  ├─ tickets.json                  <- 25 support tickets (clean, messy, injection-bait)
│  ├─ orders.db                     <- SQLite, seeded by scripts
│  ├─ app.log                       <- ~2000 lines of realistic backend logs
│  ├─ metrics.json                  <- latency/error-rate/CPU series
│  ├─ runbooks\*.md                 <- 5 short runbooks
│  └─ seed_data.py                  <- regenerates everything above, deterministically
│
├─ tests\
│  ├─ conftest.py                   <- shared fixtures: fake_llm, tmp db, frozen clock
│  ├─ unit\        <- test_llm_fake, test_skills_*, test_workflow_engine, test_tools_*,
│  │                  test_agent_loop, test_memory, test_budget, test_escalation
│  ├─ integration\ <- test_ticket_pipeline, test_agent_end_to_end,
│  │                  test_case_study, test_api
│  └─ live\        <- test_claude_smoke.py  (marker `live`, skipped by default)
│
└─ appendix\
   ├─ nodejs-port\                  <- one skill, ported, reference only
   └─ async-parallel-tools\         <- async version of the agent loop + latency numbers
```

**File count estimate:** ~95 files. ~5,500 lines of Python, ~9,000 lines of Markdown.

---

## 4. Milestones

Time estimates are **your reading/doing time as a learner**, not generation time. Total ≈ **20–26 hours** of study, spread however you like.

Legend for "Skills/tools" = what *you* need to know or have installed going in.

---

### M0 — Foundation and setup
**Goal:** Get a working Python project on Windows that runs tests green with no API key.

| Task | Output files | Est. |
|---|---|---|
| M0.1 Scaffold repo, `pyproject.toml`, `requirements.txt`, `.gitignore` | root config files | 15m |
| M0.2 Windows setup scripts | `scripts\setup.ps1`, `scripts\verify-env.ps1`, `scripts\test.ps1`, `scripts\run-example.ps1` | 20m |
| M0.3 Typed config + `.env.example` | `src\aisets\config.py`, `.env.example` | 15m |
| M0.4 Structured logging with trace ids | `src\aisets\logging_setup.py` | 15m |
| M0.5 Sample data generator + committed data | `data\seed_data.py`, `data\*` | 30m |
| M0.6 Setup doc | `docs\02-setup-windows.md` | 20m |
| M0.7 Concepts doc + all ASCII diagrams | `docs\01-concepts.md`, `docs\diagrams\*` | 40m |
| M0.8 Glossary | `docs\10-glossary.md` | 15m |

**Dependencies:** none. **Exit check:** `.\scripts\setup.ps1` then `.\scripts\verify-env.ps1` prints all-green.
**Est. total: 2h 30m**

---

### M1 — The LLM layer (the seam everything else sits on)
**Goal:** One interface, two implementations — fake and real — so every later lesson is testable offline.

| Task | Output files | Est. |
|---|---|---|
| M1.1 `LLMClient` protocol: `complete()`, `complete_json(schema)` | `src\aisets\llm\base.py` | 20m |
| M1.2 `FakeLLM` — scripted responses, matcher rules, forced-failure mode | `src\aisets\llm\fake.py` | 30m |
| M1.3 `ClaudeLLM` — real SDK, timeout, retry with backoff, error mapping | `src\aisets\llm\claude.py`, `errors.py` | 40m |
| M1.4 Token + cost accounting | `src\aisets\llm\usage.py` | 20m |
| M1.5 Unit tests for both backends incl. every failure path | `tests\unit\test_llm_fake.py`, `test_llm_errors.py` | 30m |
| M1.6 Docs: LLM basics + prompting as an API contract | `docs\03-llm-basics.md`, `docs\04-prompting-guide.md` | 50m |

**Dependencies:** M0. **Exit check:** `pytest tests/unit -q` green; `LLM_BACKEND=claude` smoke test works if a key is present.
**Est. total: 3h 10m**

---

### M2 — Level 1: AI Skills
**Goal:** Build five small, independently testable skills, and learn why every AI output must be validated.

| Task | Output files | Est. |
|---|---|---|
| M2.1 `Skill` base class: validate in → prompt → parse → validate out | `src\aisets\skills\base.py` | 30m |
| M2.2 `classify_ticket` — free text → one of a fixed enum | `skills\classify_ticket.py` | 25m |
| M2.3 `extract_fields` — text → typed Pydantic model | `skills\extract_fields.py` | 30m |
| M2.4 `summarize_log` — long input → short output; chunking + truncation | `skills\summarize_log.py` | 30m |
| M2.5 `draft_reply` — tone/length control, forbidden-content check | `skills\draft_reply.py` | 25m |
| M2.6 `score_severity` — numeric output with clamping and sanity bounds | `skills\score_severity.py` | 20m |
| M2.7 Examples 01–04, including a deliberate failure demo | `examples\01..04_*.py` | 40m |
| M2.8 Unit tests: happy path, malformed JSON, empty, oversized, injection | `tests\unit\test_skills_*.py` | 50m |
| M2.9 Lesson text + decision log + exercises | `tutorial\01-skills\*` | 60m |

**Dependencies:** M1.
**Teaching beats:** *AI output is untrusted input.* *A skill with no schema is a bug waiting to happen.* *Retry vs. fail-fast.*
**Exit check:** `python examples\03_skill_structured_output.py` prints a typed object; `04` prints four caught failures and recovers from three.
**Est. total: 5h 10m**

---

### M3 — Level 2: AI Workflows
**Goal:** Connect skills in an order **you** control, and put reliability where it belongs.

| Task | Output files | Est. |
|---|---|---|
| M3.1 Workflow engine: `Step`, `Pipeline`, context bag, per-step logging | `workflow\engine.py`, `context.py` | 45m |
| M3.2 Policies: retry, exponential backoff, fallback skill, circuit breaker | `workflow\policies.py` | 40m |
| M3.3 Concrete pipeline: classify → extract → severity → draft reply | `workflow\ticket_pipeline.py` | 30m |
| M3.4 Branching: route by classification; short-circuit on low severity | (same file + example 06) | 25m |
| M3.5 Examples 05–07 with printed step-by-step traces | `examples\05..07_*.py` | 40m |
| M3.6 Unit + integration tests incl. forced mid-pipeline failure | `tests\unit\test_workflow_engine.py`, `tests\integration\test_ticket_pipeline.py` | 50m |
| M3.7 Lesson + decisions + exercises | `tutorial\02-workflows\*` | 60m |

**Dependencies:** M2.
**Teaching beats:** *Deterministic path = you can test it, price it, and put it on-call.* *Most "AI agent" products should have been a workflow.* *Where to retry: per-step, not whole-pipeline.*
**Tradeoff table to write:** workflow vs agent — predictability, cost, latency, capability, debuggability.
**Exit check:** `python examples\07_workflow_retry_and_fallback.py` shows a step failing twice, succeeding on retry 3, and a second step falling back.
**Est. total: 4h 30m**

---

### M4 — Tools (the agent's hands)
**Goal:** Give the model safe, typed access to a fake production backend.

| Task | Output files | Est. |
|---|---|---|
| M4.1 `@tool` decorator → JSON schema from type hints + docstring | `agent\tools.py` | 40m |
| M4.2 Tool registry with read/write permission flags and an allowlist | `agent\registry.py` | 30m |
| M4.3 Read tools: `query_orders`, `search_logs`, `get_metrics`, `find_runbook` | `tools\db.py`, `logs.py`, `metrics.py`, `runbook.py` | 50m |
| M4.4 Write tools (simulated + audit-logged): `restart_service`, `scale_service`, `page_oncall` | `tools\actions.py` | 30m |
| M4.5 Tests: schema generation, arg validation, permission denial, tool errors | `tests\unit\test_tools_*.py` | 40m |

**Dependencies:** M0 (data), M1.
**Teaching beats:** *A tool description is a prompt — write it like API docs.* *Separate read from write; write needs a gate.* *Never let a tool take a raw string the model wrote straight into SQL/shell.*
**Est. total: 3h 10m**

---

### M5 — Level 3: The AI Agent
**Goal:** Write the agent loop yourself, in ~50 readable lines, and understand every line.

| Task | Output files | Est. |
|---|---|---|
| M5.1 The loop: think → tool call → observe → repeat → final answer | `agent\loop.py` | 50m |
| M5.2 Step budget, timeout, loop-detection (same tool + same args twice) | `agent\loop.py` (+ tests) | 30m |
| M5.3 Memory: short-term turn history + trimming; long-term SQLite facts | `agent\memory.py` | 45m |
| M5.4 `simple_agent`: 3 read-only tools, budget 5, no writes | `agent\simple_agent.py` | 25m |
| M5.5 Examples 08–10 with a full printed reasoning trace | `examples\08..10_*.py` | 45m |
| M5.6 Tests: forced tool loop, budget exhaustion, bad tool args, tool crash | `tests\unit\test_agent_loop.py`, `test_memory.py` | 60m |
| M5.7 Lesson + decisions + exercises | `tutorial\03-agents\*` | 70m |

**Dependencies:** M3, M4.
**Teaching beats:** *The loop is small; the danger is unbounded.* *Context window is a budget you spend on history.* *Every agent needs a stop condition you can defend in a design review.*
**Exit check:** `python examples\08_agent_first_loop.py` answers "why did order 8842 fail?" using 3 tool calls, printing each.
**Est. total: 5h 25m**

---

### M6 — Level 4a: Agentic building blocks
**Goal:** Turn a one-shot agent into a system with a goal, a plan, self-checks, and hard limits.

| Task | Output files | Est. |
|---|---|---|
| M6.1 `Goal`: objective, success criteria, hard constraints, stop conditions | `agentic\goal.py` | 30m |
| M6.2 `Planner`: produce a plan, execute it, re-plan when a step surprises you | `agentic\planner.py` | 60m |
| M6.3 `Critic`: verify the result against the success criteria; loop back once | `agentic\critic.py` | 45m |
| M6.4 `Budget`: caps on steps, tokens, currency, wall-clock; graceful stop | `agentic\budget.py` | 35m |
| M6.5 `Escalation`: risk score → auto / confirm / human-only; approval record | `agentic\escalation.py` | 50m |
| M6.6 Examples 11–13 | `examples\11..13_*.py` | 50m |
| M6.7 Tests for each block incl. "critic rejects, plan is fixed, second try passes" | `tests\unit\test_planner.py`, `test_critic.py`, `test_budget.py`, `test_escalation.py` | 70m |
| M6.8 Lesson + decisions + exercises | `tutorial\04-agentic\*` | 70m |

**Dependencies:** M5.
**Teaching beats:** *Plans are guesses — re-planning is the feature.* *A critic is cheap insurance.* *Escalation is a product decision, not a technical one.*
**Est. total: 6h 50m**

---

### M7 — Level 4b: Multi-agent orchestration
**Goal:** Show when several agents beat one, and — honestly — when they do not.

| Task | Output files | Est. |
|---|---|---|
| M7.1 Supervisor + specialists (investigator / fixer / communicator) | `agentic\orchestrator.py` | 60m |
| M7.2 Message passing, shared state, and result merging | (same) | 30m |
| M7.3 Failure handling: a specialist dies / stalls / contradicts another | (same + tests) | 40m |
| M7.4 Example 14 + a measured comparison vs the single agent | `examples\14_agentic_multi_agent.py` | 40m |
| M7.5 Tradeoff doc: centralized vs distributed agents | in `tutorial\04-agentic\README.md` | 30m |

**Dependencies:** M6.
**Teaching beats:** *More agents = more tokens, more latency, more ways to disagree.* *Use them for genuinely parallel or genuinely different-skill work, not for show.*
**Est. total: 3h 20m**

---

### M8 — Case study: backend incident triage (the capstone)
**Goal:** One realistic end-to-end system that uses everything above.

**The scenario:** Error rate on the `payments` service jumps at 02:14. An agentic system must: detect it, gather evidence from logs/metrics/DB, form and test a hypothesis, consult the runbook, propose a fix, **stop and ask a human before any write action**, then write an incident summary — and handle the case where evidence is missing or contradictory.

| Task | Output files | Est. |
|---|---|---|
| M8.1 Scenario, data, and injected faults (3 variants: easy / ambiguous / trap) | `data\` additions | 40m |
| M8.2 The triage system wiring all M2–M7 pieces | `examples\15_case_study_incident_triage.py` | 80m |
| M8.3 Failure-handling matrix: tool down, empty result, contradiction, budget hit | `tutorial\05-case-study\RUNBOOK.md` | 45m |
| M8.4 Escalation walkthrough with the approval prompt and audit trail | (same) | 30m |
| M8.5 Integration test covering all 3 variants deterministically | `tests\integration\test_case_study.py` | 60m |
| M8.6 Case-study write-up + decision log + postmortem exercise | `tutorial\05-case-study\*` | 80m |

**Dependencies:** M7.
**Exit check:** All three variants run offline; the "trap" variant must **refuse to act** and escalate.
**Est. total: 5h 35m**

---

### M9 — Productionizing, cross-cutting docs, and the final checklist
**Goal:** Make it look like something you would actually deploy, and close out the deliverables.

| Task | Output files | Est. |
|---|---|---|
| M9.1 FastAPI service exposing the agent: `POST /triage`, `GET /runs/{id}` | `examples\16_serve_agent_api.py` | 50m |
| M9.2 API tests with httpx | `tests\integration\test_api.py` | 30m |
| M9.3 Security & privacy doc: prompt injection (with a live demo), secrets, PII, tool permissions, sandboxing | `docs\06-security-and-privacy.md` | 60m |
| M9.4 Cost & latency doc with a measured table from real runs | `docs\07-cost-and-latency.md` | 45m |
| M9.5 Testing-AI-code doc | `docs\05-testing-ai-code.md` | 40m |
| M9.6 Troubleshooting guide: 15+ real errors, log samples, causes, fixes | `docs\08-troubleshooting.md` | 60m |
| M9.7 Frameworks doc (what LangChain/CrewAI do, when to switch) | `docs\09-frameworks-and-when-to-use-them.md` | 30m |
| M9.8 Node.js port + async appendix | `appendix\*` | 50m |
| M9.9 Root `README.md` + the verification checklist | `README.md`, `scripts\verify-env.ps1` | 40m |

**Dependencies:** M8.
**Est. total: 6h 45m**

---

### Dependency graph

```
M0 ──► M1 ──► M2 ──► M3 ──┐
        │                 ├──► M5 ──► M6 ──► M7 ──► M8 ──► M9
        └──► M4 ──────────┘
```

M4 (tools) can be built in parallel with M2/M3 — it only needs M0 and M1.

---

## 5. Testing plan

**Target:** ≥ 85% line coverage on `src\aisets\`, 100% on `workflow\engine.py`, `agent\loop.py`, `agentic\budget.py`, `agentic\escalation.py` — the four files where a bug is dangerous.

Three tiers:

1. **Unit** (`tests\unit\`) — pure logic, `FakeLLM` only, no network, no clock, no filesystem outside `tmp_path`. Must run in **< 5 seconds total**.
2. **Integration** (`tests\integration\`) — full pipelines/agents against `FakeLLM` + real SQLite + real sample data. Must run in **< 30 seconds**.
3. **Live** (`tests\live\`) — real Anthropic API. Marked `@pytest.mark.live`, **deselected by default** in `pyproject.toml`. Run with `pytest -m live`. Asserts loose properties (non-empty, valid JSON, correct enum), never exact strings.

**Every skill/agent gets these five negative tests** (this list is the module test template):
- malformed / non-JSON model output
- empty or whitespace-only input
- oversized input (context overflow)
- prompt-injection payload in the input
- tool/network error mid-run

Commands (documented in every lesson):
```powershell
.\scripts\test.ps1                                  # everything except live
python -m pytest tests\unit -q                      # fast loop
python -m pytest tests\integration -q
python -m pytest -m live                            # needs ANTHROPIC_API_KEY
python -m pytest --cov=src\aisets --cov-report=term-missing
```

---

## 6. Documentation standard (applies to every module)

Each `tutorial\NN-*\README.md` follows this **fixed** outline, so every lesson reads the same way:

1. **What you will learn** (3–5 bullets)
2. **The idea in one picture** (ASCII diagram)
3. **The idea in plain words** (with an everyday analogy)
4. **Walk the code** (file by file, short paragraphs, exact relative paths)
5. **Run it** (exact PowerShell commands + the exact output you should see)
6. **Why this design** → links to `DECISIONS.md`
7. **When to use this / when NOT to use this** (two short lists)
8. **How it breaks** — failure modes table: *symptom → how to detect → how to recover*
9. **Security, privacy, cost** (three short paragraphs, concrete numbers)
10. **Tests** — what is tested, how to run, how to add one
11. **Exercises** → `EXERCISES.md` (3 tasks: easy / medium / "break it on purpose")
12. **What changes in the next lesson** (the one new idea coming next)

Writing rules: short sentences. Short paragraphs (≤ 4 lines). No unexplained jargon — every new term gets a one-line definition on first use **and** an entry in `docs\10-glossary.md`. Every claim about cost or latency comes with a number from an actual run.

---

## 7. Risks and how we handle them

| Risk | Impact | Mitigation |
|---|---|---|
| Learner has no API key | Blocks everything | `FakeLLM` default — the whole tutorial runs offline (D-003) |
| Real model output varies, breaking examples | Confusing | Examples assert loosely; docs show *shape* of output, not exact text |
| Python 3.14 dependency gaps (very new) | Setup fails | Tiny dep list, all pure-Python or well-maintained; `verify-env.ps1` checks imports and prints a fix; documented fallback to 3.11/3.12 |
| Windows path/venv/PowerShell execution-policy friction | Setup fails | `setup.ps1` handles it and prints the `Set-ExecutionPolicy -Scope Process` fix; all paths use `\` and are quoted |
| Tutorial becomes too long to finish | Abandoned | Each milestone is independently runnable and valuable; `00-start-here.md` gives a 2-hour "fast path" (M0→M2→M3→M5) |
| Concepts drift into hype | Poor learning | Every level ends with an explicit "when NOT to use this" section |
| Real API spend | Money | Cost accounting in `usage.py`, hard `MAX_USD_PER_RUN` budget, live tests off by default, cheapest suitable model in examples |

---

## 8. Approval

### What you get when you approve
Milestones M0 → M9 executed in order. I will report at the end of each milestone with the files created and the exit check result, so you can course-correct early rather than at the end.

### Suggested order of approval
Approve the whole plan, or approve **M0–M2 first** if you'd rather see the shape of one real lesson before committing to the rest. I recommend the latter — it's cheap to change direction after M2.

### Open questions (I have picked a default for each; say nothing and I proceed with the default)

| # | Question | My default |
|---|---|---|
| Q1 | Python primary, Node only as a small appendix? | **Yes, Python primary** |
| Q2 | Do you have an `ANTHROPIC_API_KEY` you want the live tests wired for? | **Assume yes but keep it optional** — everything works without it |
| Q3 | Case-study domain: backend incident triage? (alternatives: order-fulfilment agent, data-pipeline repair agent, code-review agent) | **Incident triage** |
| Q4 | Include the FastAPI service (M9.1)? | **Yes** — it's the part that makes it feel like backend work |
| Q5 | Deliver everything in one pass, or milestone-by-milestone with a checkpoint after each? | **Milestone-by-milestone** |

---

*End of plan. No other content will be generated until this is approved.*
