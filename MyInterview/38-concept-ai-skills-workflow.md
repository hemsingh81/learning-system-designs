# 38 · Concept: AI Skills & AI Workflow (30 questions)

[← Azure Services](37-concept-azure-services.md) · [Home](README.md) · [Next → AI Agents](39-concept-ai-agents-agentic.md)

This file explains **AI skills** (the reusable capabilities we give an AI system) and **AI workflows** (how we chain steps into a reliable pipeline), in simple English and real depth. I answer from the AI/LLM reference architecture and first production RAG app I built on TCW (Project B).

> Simple one-liner: *"An AI 'skill' is one well-scoped thing the AI can do (summarise, extract, classify, call a tool). An AI 'workflow' is how I stitch those skills into a predictable, testable pipeline — not one giant prompt."*

**Jump to:** [AS1 What is an AI skill](#as1--what-is-an-ai-skill) · [AS2 Skill vs prompt](#as2--skill-vs-a-raw-prompt) · [AS3 What is an AI workflow](#as3--what-is-an-ai-workflow) · [AS4 Workflow vs agent](#as4--workflow-vs-agent) · [AS5 Prompt engineering](#as5--prompt-engineering-basics) · [AS6 System prompts](#as6--system-prompts) · [AS7 Few-shot](#as7--few-shot-prompting) · [AS8 Structured output](#as8--structured-output) · [AS9 Tool/function calling](#as9--tool-and-function-calling) · [AS10 Chaining](#as10--prompt-chaining)
> [AS11 Routing](#as11--routing) · [AS12 Parallelisation](#as12--parallelisation) · [AS13 Orchestrator-worker](#as13--orchestrator-worker) · [AS14 Evaluator-optimiser](#as14--evaluator-optimiser-loop) · [AS15 Memory](#as15--memory-in-workflows) · [AS16 Context window](#as16--the-context-window) · [AS17 Chunking](#as17--chunking) · [AS18 Guardrails](#as18--guardrails) · [AS19 Hallucination control](#as19--controlling-hallucinations) · [AS20 Evaluation](#as20--evaluating-a-workflow)
> [AS21 Observability](#as21--observability-and-tracing) · [AS22 Cost control](#as22--cost-control) · [AS23 Latency](#as23--latency-and-streaming) · [AS24 Caching](#as24--caching) · [AS25 Idempotency/retries](#as25--idempotency-and-retries) · [AS26 Human-in-the-loop](#as26--human-in-the-loop) · [AS27 Security](#as27--security-of-ai-workflows) · [AS28 Testing](#as28--testing-ai-workflows) · [AS29 Deployment](#as29--deploying-ai-workflows) · [AS30 My reference workflow](#as30--my-reference-workflow) · [Section index](#section-index)

---

## AS1 · What is an AI skill?

**Simple explanation.** A **skill** is one well-scoped capability I give the AI system — for example "summarise a document", "extract fields as JSON", "classify a ticket", or "call the search tool". Each skill has a clear input, a clear output, and one job.

**Architect's view:** I treat skills like small functions. Small, named, testable, reusable — the same discipline as good code. That's what makes an AI system maintainable instead of one giant unpredictable prompt.

**Follow-ups**
- *"Why scope skills tightly?"* — A tight skill is easy to test, cache and swap; a broad one is unpredictable and hard to debug.
- *"Where did you use this?"* — On the RAG support assistant (Project B): retrieve, ground, answer and cite were separate skills, each testable on its own.

---

## AS2 · Skill vs a raw prompt

**Simple explanation.** A raw prompt is free text I send once. A **skill** wraps a prompt with a fixed contract: a defined input schema, an output schema, examples, and validation. It's a prompt turned into a reliable, reusable unit.

*"I never ship a bare prompt to production — I wrap it as a skill with a Pydantic output model and validation, so the rest of the pipeline can trust the shape."*

**Follow-ups**
- *"What's the risk of a bare prompt?"* — Output drifts, breaks parsing downstream, and can't be versioned or tested.
- *"How do you version a skill?"* — Prompt text + model + params in source control, with an eval that must pass before release.

---

## AS3 · What is an AI workflow?

**Simple explanation.** An **AI workflow** is a defined sequence of steps (skills, tool calls, code) that I orchestrate to complete a task — for example: receive question → retrieve context → build prompt → call model → validate → return with citations. The path is mostly **predetermined by me**.

**Architect's view:** A workflow is deterministic scaffolding around non-deterministic model calls. I decide the control flow; the model fills the gaps. That predictability is what enterprises need.

**Follow-ups**
- *"Why not one big prompt?"* — Smaller steps are testable, cheaper, and let me put validation between them.
- *"Workflow vs pipeline?"* — Same idea; "pipeline" is the data-engineering word I use in Project A, "workflow" the AI word in Project B.

---

## AS4 · Workflow vs agent

**Simple explanation.** In a **workflow**, *I* decide the steps and order in code. In an **agent**, the *model* decides the next step at runtime — it loops, picks tools, and reacts. Workflow = fixed path; agent = the model drives ([see file 39](39-concept-ai-agents-agentic.md)).

*"I default to a workflow because it's predictable and cheaper. I only add agentic freedom where the task genuinely needs dynamic tool choice."*

**Follow-ups**
- *"When do you pick a workflow over an agent?"* — When the steps are known and repeatable — most enterprise tasks. Less cost, less risk.
- *"Can they mix?"* — Yes — a workflow can call an agent for one open-ended sub-step and keep control everywhere else.

---

## AS5 · Prompt engineering basics

**Simple explanation.** Prompt engineering is writing the instruction so the model does the right thing reliably: be specific, give the role, give the format, give examples, and set constraints. Clear input → reliable output.

*"My rule: tell it who it is, what to do, what NOT to do, and exactly what shape to return."*

**Follow-ups**
- *"One tip that helps most?"* — Ask for a strict output format (JSON schema) and give one example — parsing errors drop sharply.
- *"How do you stop rambling?"* — Constrain length and format, and say "answer only from the provided context".

---

## AS6 · System prompts

**Simple explanation.** The **system prompt** sets the model's persistent role, rules and tone for the whole conversation — "You are a support assistant for TCW. Answer only from the given context. Cite sources. If unsure, say so." It's the guardrail that every turn inherits.

**Follow-ups**
- *"System vs user prompt?"* — System = fixed rules/persona; user = the actual question. Keep rules in the system prompt so users can't easily override them.
- *"Can users override it?"* — They can try (prompt injection) — I add input filtering and keep sensitive rules server-side ([AS27](#as27--security-of-ai-workflows)).

---

## AS7 · Few-shot prompting

**Simple explanation.** **Few-shot** means I include a few worked examples in the prompt so the model copies the pattern. Zero-shot = no examples; few-shot = 1–5 examples. Examples beat long instructions for tricky formats.

*"For field extraction I show two example documents and their JSON output — accuracy jumps versus describing the format in words."*

**Follow-ups**
- *"Cost of few-shot?"* — More tokens per call — I balance accuracy against cost, or move examples into a fine-tune if volume is high.
- *"How many examples?"* — Enough to pin the pattern, usually 2–3; more can hurt if they crowd the context.

---

## AS8 · Structured output

**Simple explanation.** I make the model return **structured data** (JSON matching a schema) instead of free text, so downstream code can use it safely. Modern models support JSON mode / schema-constrained output.

```python
class Extraction(BaseModel):
    account_id: str
    amount: Decimal
    as_of: date
# I validate the model's JSON against this schema before trusting it
result = Extraction.model_validate_json(llm_json)
```

**Follow-ups**
- *"Why validate if the model returns JSON?"* — Models still drift; validation is my contract boundary — reject and retry on failure.
- *"What if it keeps failing?"* — Retry with the error message fed back, then fall back to a safe default and log it.

---

## AS9 · Tool and function calling

**Simple explanation.** **Tool calling** lets the model ask my code to run a function — search a database, call an API, do maths — and use the result. I describe the tools; the model picks one and gives arguments; my code runs it and returns the output.

*"This is how the AI touches real systems safely — it doesn't call anything itself; it requests, and my code executes with proper auth and limits."*

**Follow-ups**
- *"Who actually runs the tool?"* — My code, not the model — so I control auth, validation and rate limits.
- *"How do you keep it safe?"* — Whitelist tools, validate arguments, least-privilege identity, and never expose raw destructive actions.

---

## AS10 · Prompt chaining

**Simple explanation.** **Chaining** breaks a task into steps where each step's output feeds the next — e.g. outline → draft → critique → final. Each step is simpler and more accurate than doing everything at once.

*"I chain 'extract facts' → 'compose answer' → 'add citations' so each skill stays small and testable."*

**Follow-ups**
- *"Downside of chaining?"* — More calls = more cost/latency; I chain only where it clearly improves quality.
- *"How do you stop errors compounding?"* — Validate between steps and stop early on failure.

---

## AS11 · Routing

**Simple explanation.** **Routing** classifies the input first, then sends it to the right skill or model — e.g. simple FAQ → cheap fast model; complex analysis → strong model; billing question → billing tool. One smart front door.

*"Routing cut our cost — most questions are simple and don't need the biggest model."*

**Follow-ups**
- *"How do you route?"* — A small classifier (a cheap model or rules) picks the branch by intent/complexity.
- *"Risk?"* — Mis-routing; I add a fallback to the strong model and log routing decisions to tune it.

---

## AS12 · Parallelisation

**Simple explanation.** **Parallelisation** runs independent steps at the same time — e.g. summarise 10 documents concurrently, then merge. It cuts latency and can improve quality (run several attempts and vote).

**Follow-ups**
- *"Two flavours?"* — Sectioning (split work, run in parallel, combine) and voting (run the same task several times, take the best/majority).
- *"When not to?"* — When steps depend on each other — then it's a chain, not parallel.

---

## AS13 · Orchestrator-worker

**Simple explanation.** An **orchestrator** model breaks a big task into subtasks, hands each to a **worker** skill, and combines the results. Good when you can't predict the subtasks in advance (e.g. a research question that needs different sources).

**Follow-ups**
- *"How is this different from static chaining?"* — The orchestrator decides the subtasks dynamically; a chain is fixed by me.
- *"Cost?"* — Higher — I use it only for genuinely open-ended tasks.

---

## AS14 · Evaluator-optimiser loop

**Simple explanation.** One skill **generates**, another **evaluates** against criteria, and it **loops** until good enough — like a writer and an editor. Great when there are clear quality criteria and a first draft is rarely perfect.

*"For generated answers I run an evaluator skill: 'is this grounded in the sources and does it answer the question?' If not, regenerate with the feedback."*

**Follow-ups**
- *"When is this worth it?"* — When quality matters and you can state clear criteria; skip it for trivial tasks.
- *"How do you avoid infinite loops?"* — A max-iteration cap and a fallback to the best attempt.

---

## AS15 · Memory in workflows

**Simple explanation.** **Memory** lets a workflow remember across turns or runs. **Short-term** = the current conversation (chat history in the context window); **long-term** = stored facts/preferences retrieved when relevant (often via a vector store).

**Follow-ups**
- *"Short vs long-term?"* — Short = this chat; long = persisted and fetched by retrieval next time.
- *"Risk with memory?"* — Storing sensitive data — I control what's persisted and honour retention/privacy rules.

---

## AS16 · The context window

**Simple explanation.** The **context window** is how much text (tokens) the model can consider at once — system prompt + history + retrieved context + question + answer must all fit. Bigger windows help but cost more and can "lose" the middle.

*"I don't stuff the whole document in — I retrieve only the relevant chunks. It's cheaper and more accurate."*

**Follow-ups**
- *"What's 'lost in the middle'?"* — Models attend best to the start/end; key facts buried in the middle can be missed — so I keep context tight and ordered.
- *"Bigger window = always better?"* — No — more tokens = more cost/latency and can dilute focus.

---

## AS17 · Chunking

**Simple explanation.** **Chunking** splits documents into smaller passages before indexing so retrieval returns focused, relevant pieces. Chunk size and overlap matter — too big loses precision, too small loses meaning.

*"I chunk by structure (headings/paragraphs) with a small overlap so a sentence isn't cut in half."*

**Follow-ups**
- *"Fixed size or semantic?"* — I prefer structure-aware/semantic chunks over blind fixed sizes — better retrieval.
- *"Why overlap?"* — So context spanning a boundary isn't lost between two chunks.

---

## AS18 · Guardrails

**Simple explanation.** **Guardrails** are checks around the model: input filters (block prompt injection, PII), output filters (block unsafe/off-topic answers), and rules ("only answer from context"). They keep the system safe and on-task.

*"In a regulated firm, guardrails aren't optional — content safety and 'answer only from grounded sources' are part of the design."*

**Follow-ups**
- *"Input vs output guardrails?"* — Input: sanitise/limit what goes in; output: validate/filter what comes back.
- *"Tooling?"* — Azure AI Content Safety plus my own validators and allow-lists.

---

## AS19 · Controlling hallucinations

**Simple explanation.** A **hallucination** is a confident wrong answer. I reduce it by **grounding** (RAG on real data), telling the model to answer only from provided context and say "I don't know" otherwise, asking for **citations**, and evaluating answers.

*"Grounding plus 'cite your source or refuse' is the biggest single lever — it's central to my reference architecture."*

**Follow-ups**
- *"Can you eliminate hallucinations?"* — No — you reduce and detect them: grounding, citations, evaluation, human review for high-stakes.
- *"How do you detect them?"* — Check the answer's claims against retrieved sources (an evaluator step) and log low-confidence cases.

---

## AS20 · Evaluating a workflow

**Simple explanation.** I measure quality with an **eval set** — a fixed set of inputs with expected outcomes — and score each release on **accuracy/groundedness, relevance, safety, latency and cost**. No eval = flying blind.

*"Before any prompt or model change ships, it must pass the eval set — same gate as unit tests for code."*

**Follow-ups**
- *"How do you score open-ended answers?"* — Rubric-based checks, an LLM-as-judge with a strict rubric, plus human spot-checks.
- *"Where do eval cases come from?"* — Real questions, edge cases, and past failures — the set grows over time.

---

## AS21 · Observability and tracing

**Simple explanation.** I **trace** every run — the prompt, retrieved chunks, tool calls, tokens, latency and the final output — so I can debug why an answer was wrong. Without tracing, an AI app is a black box.

*"I use LangSmith-style tracing ([file 43](43-concept-langsmith.md)) plus App Insights so I can open any bad answer and see exactly what the model saw."*

**Follow-ups**
- *"What do you log per run?"* — Inputs, retrieved context, model/params, tool calls, tokens, cost, latency, output, and eval score.
- *"Privacy concern?"* — Yes — I redact PII in traces and control retention.

---

## AS22 · Cost control

**Simple explanation.** LLM cost is per token. I control it by routing simple work to cheaper models ([AS11](#as11--routing)), retrieving only what's needed, caching ([AS24](#as24--caching)), trimming prompts, and capping output length. Cost is a design constraint from day one.

**Follow-ups**
- *"Biggest lever?"* — Right-size the model per task and cache repeated calls — often the largest saving.
- *"How do you track it?"* — Token/cost logged per run and per feature, with budgets and alerts.

---

## AS23 · Latency and streaming

**Simple explanation.** LLM calls are slow, so I **stream** tokens to the user as they generate (the answer appears progressively), run steps in parallel where possible, and use faster models for the first response. Perceived speed matters as much as raw speed.

**Follow-ups**
- *"Why stream?"* — The user sees words immediately — far better experience than a long blank wait.
- *"Other latency wins?"* — Cache, parallelise, smaller models, and shorter prompts.

---

## AS24 · Caching

**Simple explanation.** I **cache** results so identical or similar requests don't hit the model again. **Exact cache** for repeated prompts; **semantic cache** returns a stored answer when a new question is similar enough (by embedding). Big cost and latency win for FAQs.

**Follow-ups**
- *"Exact vs semantic cache?"* — Exact matches the same text; semantic matches similar meaning via embeddings.
- *"Risk of semantic cache?"* — Returning a close-but-wrong answer — I set a strict similarity threshold and can bypass for critical queries.

---

## AS25 · Idempotency and retries

**Simple explanation.** Model/tool calls fail or time out, so I make steps **retry with backoff** and keep them **idempotent** (safe to run twice). This is the same reliability discipline as my ETL work (Project A).

**Follow-ups**
- *"Why idempotency?"* — A retry must not double-charge or duplicate data — design each step to be safely repeatable.
- *"Retry everything?"* — No — retry transient errors (timeouts, 429); don't retry validation failures.

---

## AS26 · Human-in-the-loop

**Simple explanation.** For high-stakes actions, a **human approves** before the workflow commits — e.g. the AI drafts, a person reviews and confirms. It combines AI speed with human accountability.

*"In a regulated firm I keep a human on anything that changes data or is customer-facing until trust and evals justify automation."*

**Follow-ups**
- *"When is human-in-the-loop required?"* — Financial actions, external comms, anything irreversible or regulated.
- *"How do you phase it out?"* — Only as evals and monitoring prove accuracy — reduce review gradually, never blindly.

---

## AS27 · Security of AI workflows

**Simple explanation.** Key risks: **prompt injection** (malicious text hijacks instructions), **data leakage** (secrets/PII in prompts or logs), and **over-privileged tools**. I mitigate with input sanitisation, keeping rules server-side, least-privilege tool identities, and redacted logs.

*"Treat all model input as untrusted — the same mindset as web input. Never let retrieved text issue commands."*

**Follow-ups**
- *"What is prompt injection?"* — Hidden instructions in user or retrieved content that try to override your rules.
- *"Defence?"* — Separate instructions from data, filter inputs, restrict tools, and never execute model output directly.

---

## AS28 · Testing AI workflows

**Simple explanation.** I test the **deterministic parts** as normal (routing, parsing, tools) with unit tests, and the **model parts** with eval sets and regression checks. Non-determinism means I assert on properties (grounded? valid schema? safe?), not exact strings.

**Follow-ups**
- *"How do you test a non-deterministic output?"* — Assert on invariants: valid JSON, contains a citation, stays on topic — plus eval scores over a set.
- *"Regression testing?"* — Re-run the eval set on every change; block release if scores drop.

---

## AS29 · Deploying AI workflows

**Simple explanation.** I deploy the workflow like any service: containerised API, secrets in Key Vault, managed identity, autoscaling, monitoring, and CI/CD that runs the eval set as a gate. Prompts and model versions are pinned and versioned.

*"On Azure this is Azure OpenAI + AI Foundry for the model layer, my FastAPI/.NET service around it, and App Insights for observability ([file 37](37-concept-azure-services.md))."*

**Follow-ups**
- *"How do you roll out a prompt change safely?"* — Version it, pass evals, canary to a small % , monitor, then full rollout.
- *"Model upgrade risk?"* — A new model can change behaviour — re-run evals before switching.

---

## AS30 · My reference workflow

**How I answer (the whole picture).** *"My default AI workflow is a grounded pipeline: sanitise input → route by intent → retrieve relevant chunks → build a tight prompt with a system role and citations rule → call the right-sized model with structured output → validate the JSON → evaluate for groundedness → stream the answer with sources. Around it: guardrails, tracing on every run, caching, retries, cost/latency budgets, and a human-in-the-loop for high-stakes actions. I keep control in code and let the model do the language work — that's how I shipped TCW's first production RAG assistant safely."*

**Follow-ups**
- *"Workflow or agent for this?"* — A workflow — the steps are known; I add agentic freedom only where needed ([file 39](39-concept-ai-agents-agentic.md)).
- *"How do you know it's good?"* — Eval scores, groundedness, cost/latency, and user feedback — all tracked release over release.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| AS1 | AI skill | One well-scoped capability with a clear contract |
| AS2 | Skill vs prompt | A skill wraps a prompt with schema, examples, validation |
| AS3 | AI workflow | Ordered steps I orchestrate around model calls |
| AS4 | Workflow vs agent | Workflow = fixed path; agent = model decides |
| AS5 | Prompt engineering | Be specific: role, task, format, constraints, examples |
| AS6 | System prompts | Persistent role/rules every turn inherits |
| AS7 | Few-shot | Examples in the prompt pin the pattern |
| AS8 | Structured output | Return schema-validated JSON, not free text |
| AS9 | Tool calling | Model requests; my code executes safely |
| AS10 | Chaining | Split into steps; each feeds the next |
| AS11 | Routing | Classify first, send to the right skill/model |
| AS12 | Parallelisation | Run independent steps together; section or vote |
| AS13 | Orchestrator-worker | Model splits dynamic subtasks, then combines |
| AS14 | Evaluator-optimiser | Generate → evaluate → loop until good |
| AS15 | Memory | Short-term chat vs long-term retrieved facts |
| AS16 | Context window | Fixed token budget; keep it tight and ordered |
| AS17 | Chunking | Split docs for focused retrieval; overlap matters |
| AS18 | Guardrails | Input/output filters and rules keep it safe |
| AS19 | Hallucinations | Ground, cite, refuse, evaluate |
| AS20 | Evaluation | Eval set scores accuracy/safety/cost as a gate |
| AS21 | Observability | Trace every run to debug bad answers |
| AS22 | Cost control | Right-size model, retrieve less, cache, cap output |
| AS23 | Latency | Stream tokens; parallelise; faster models |
| AS24 | Caching | Exact and semantic cache cut cost/latency |
| AS25 | Idempotency/retries | Safe-to-repeat steps with backoff |
| AS26 | Human-in-the-loop | Human approves high-stakes actions |
| AS27 | Security | Prompt injection, leakage, over-privilege — mitigate |
| AS28 | Testing | Unit-test deterministic parts; eval the model parts |
| AS29 | Deployment | Service + Key Vault + evals-as-gate + versioning |
| AS30 | Reference workflow | Grounded pipeline with control in code |

---

[← Azure Services](37-concept-azure-services.md) · [Home](README.md) · [Next → AI Agents](39-concept-ai-agents-agentic.md)
