# AI-Sets

A hands-on tutorial that teaches **AI Skills → AI Workflow → AI Agent →
Agentic AI**, for a backend software engineer with no prior AI
experience. Every concept is explained in simple English, with
complete, runnable Python code, real tests, and a capstone case study.

> A **skill** does one thing. A **workflow** is a path **you** chose. An
> **agent** is a path the **model** chooses. **Agentic AI** is an agent
> that owns a **goal**, with memory, safety limits, and an escape hatch
> to a human.

**The whole project runs with ZERO API keys and ZERO cost by default** —
every example and every test runs against `FakeLLM`, an offline,
deterministic stand-in for a real model. Flip one setting in `.env` to
run the exact same code against the real Anthropic API.

## 5-minute quickstart (Windows)

```powershell
cd C:\Users\hemsingh9\source\repos\AI-Sets
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # only if scripts are blocked
.\scripts\setup.ps1
.\scripts\verify-env.ps1
.\scripts\run-example.ps1 01_skill_hello
```

If `verify-env.ps1` prints all `[OK]`, you're ready. See
[docs/02-setup-windows.md](docs/02-setup-windows.md) for the full,
step-by-step setup guide and troubleshooting.

## Start here

1. **[docs/00-PLAN.md](docs/00-PLAN.md)** — the master plan this whole
   project was built from (milestones, file map, decisions).
2. **[docs/01-concepts.md](docs/01-concepts.md)** — the four levels,
   explained with analogies and diagrams. Read this first.
3. **[docs/02-setup-windows.md](docs/02-setup-windows.md)** — exact setup
   instructions for this machine.

## The learning path (in order)

| # | Lesson | What you'll build |
|---|---|---|
| 1 | [tutorial/01-skills](tutorial/01-skills/README.md) | 5 AI skills — classify, extract, score, draft, summarize |
| 2 | [tutorial/02-workflows](tutorial/02-workflows/README.md) | A 4-step pipeline with branching, retries, and a circuit breaker |
| 3 | [tutorial/03-agents](tutorial/03-agents/README.md) | An agent that investigates by calling tools, with a step budget and loop detection |
| 4 | [tutorial/04-agentic](tutorial/04-agentic/README.md) | Goal, Plan, Critic, Budget, Escalation, and multi-agent orchestration |
| 5 | [tutorial/05-case-study](tutorial/05-case-study/README.md) | The capstone: a backend incident-triage system, wiring everything together |

**Fast path (~2 hours):** if you want the shape of the whole project
before committing to everything, do Lessons 1, 2, and skim Lesson 3 —
you'll have seen a real skill, a real workflow, and the beginning of a
real agent.

## Project layout

```
AI-Sets\
├─ docs\            <- concepts, setup, LLM basics, prompting, testing,
│                       security, cost, troubleshooting, frameworks, glossary
├─ src\aisets\       <- the actual library: llm\ skills\ workflow\ agent\
│                       agentic\ tools\
├─ examples\         <- 16 runnable, numbered example scripts
├─ tutorial\         <- the reading material — one folder per lesson,
│                       each with README + DECISIONS + EXERCISES
├─ data\             <- deterministic sample data (tickets, orders,
│                       logs, metrics, runbooks, case-study variants)
├─ tests\            <- unit\ integration\ live\ (140+ tests, 89%+ coverage)
├─ scripts\          <- setup.ps1 verify-env.ps1 run-example.ps1 test.ps1
└─ appendix\         <- a Node.js port of one skill, and an async
                        parallel-tool-calls benchmark
```

## Running tests

```powershell
.\scripts\test.ps1                     # unit + integration (fast, free, ~3s)
.\scripts\test.ps1 -Live               # the real-API suite (needs ANTHROPIC_API_KEY)
```

See [docs/05-testing-ai-code.md](docs/05-testing-ai-code.md) for how this
project tests non-deterministic AI behavior deterministically.

## Using the real Anthropic API

Everything above runs offline by default. To try the real model:

1. Get a key from https://console.anthropic.com/
2. In `.env`, set `LLM_BACKEND=claude` and `ANTHROPIC_API_KEY=sk-ant-...`
3. Re-run any example — the code is identical, only the backend changed.
4. See [docs/07-cost-and-latency.md](docs/07-cost-and-latency.md) for
   what this costs.

## Final verification checklist

Run `.\scripts\verify-env.ps1` — it checks all of the below and tells you
exactly what to fix if something's missing:

- [ ] Python 3.11+ on PATH
- [ ] `.venv` created and activated
- [ ] Core packages (`anthropic`, `pydantic`, `fastapi`, `httpx`, `rich`,
      `python-dotenv`) import correctly
- [ ] `.env` exists (copied from `.env.example`)
- [ ] Sample data exists: `data\tickets.json`, `data\app.log`,
      `data\orders.db` (regenerate with `python data\seed_data.py`)
- [ ] Case-study data exists: `data\case_study\{easy,ambiguous,trap}\`
      (regenerate with `python data\case_study\build_case_study_data.py`)
- [ ] `.\scripts\test.ps1` passes (140+ tests, all offline/free)
- [ ] `.\scripts\run-example.ps1 01_skill_hello` prints a classified ticket

If every box is checked, the tutorial worked — start with
[docs/01-concepts.md](docs/01-concepts.md).

## Glossary

Every term used anywhere in this project, one sentence each:
[docs/10-glossary.md](docs/10-glossary.md).
