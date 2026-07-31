# Node.js port (reference only, not maintained)

This folder is a small, standalone Node.js port of ONE skill —
`classify_ticket` (see `src/aisets/skills/classify_ticket.py`) — showing
that the same "force structured output, validate it" pattern
(`docs/04-prompting-guide.md`) works identically in a different language.

**This is a reference, not a parallel implementation of the whole
project.** Python is the primary language for this tutorial (see
`docs/00-PLAN.md` D-001) — everything else (workflows, agents, agentic
building blocks, the case study) exists only in Python. This folder is
here so a Node.js-background reader can see the seam translate directly,
not to duplicate the tutorial.

## What's here

- `classifyTicket.js` — the skill: a `FakeLLM`-equivalent class, a
  Zod schema (Node's rough equivalent of a Pydantic model) for
  `TicketCategory`, and a `classifyTicket(llm, text)` function mirroring
  `ClassifyTicket.run()`.
- `run.js` — a tiny runnable demo, same shape as `examples/01_skill_hello.py`.
- `package.json` — the two dependencies (`zod` for schema validation;
  `@anthropic-ai/sdk` only if you want to try the real backend).

## Setup & run

```powershell
cd appendix\nodejs-port
npm install
node run.js
```

This runs entirely offline against the fake backend, exactly like the
Python version's default (`LLM_BACKEND=fake`).

## The direct comparison

| Python (`src/aisets/skills/classify_ticket.py`) | Node.js (`classifyTicket.js`) |
|---|---|
| `Skill` base class (`skills/base.py`) | Plain function, no shared base (kept minimal for this reference) |
| `TicketCategory(BaseModel)` | `TicketCategorySchema` (a Zod object schema) |
| `llm.complete_json(messages, TicketCategory, system=...)` | `llm.completeJson(messages, TicketCategorySchema, { system })` |
| `BadOutput` on schema mismatch | Zod's `.parse()` throws `ZodError` on mismatch |
| `FakeLLM.queue_json({...})` | `FakeLLM.queueJson({...})` |

The lesson to take away: **the pattern (force structured output, validate
it, retry once, escape hatch for empty input) is language-independent.**
Only the syntax for "define a schema" and "validate against it" changes.
