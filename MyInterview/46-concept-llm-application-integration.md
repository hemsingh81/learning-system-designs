# 46 · Concept: LLM Application Integration (30 questions)

[← Embeddings & Semantic Search](45-concept-embeddings-semantic-search.md) · [Home](README.md) · [Next → System Design](47-concept-system-design.md)

This file explains how I **integrate LLMs into real applications** — not the model itself, but the engineering around it: APIs, prompts, streaming, safety, cost, monitoring and rollout — in simple English and real depth. I answer from projects A–E, especially TCW's RAG assistant and internal AI tools.

> Simple one-liner: *"Integrating an LLM means treating it as an unreliable, non-deterministic, external, paid dependency — so I wrap it with prompts, validation, retries, caching, safety, monitoring and cost control, and I design fallbacks for when it's slow, wrong, or down."*

**Jump to:** [LI1 What it means](#li1--what-llm-integration-means) · [LI2 The mindset](#li2--the-integration-mindset) · [LI3 Calling the API](#li3--calling-the-llm-api) · [LI4 Prompt management](#li4--prompt-management) · [LI5 Structured output](#li5--structured-output) · [LI6 Streaming](#li6--streaming) · [LI7 Context window](#li7--context-window) · [LI8 Function/tool calling](#li8--functiontool-calling) · [LI9 RAG integration](#li9--rag-integration) · [LI10 State & memory](#li10--conversation-state)
> [LI11 Reliability](#li11--reliability-retries-timeouts) · [LI12 Rate limits](#li12--rate-limits) · [LI13 Fallbacks](#li13--fallbacks-and-degradation) · [LI14 Caching](#li14--caching) · [LI15 Cost control](#li15--cost-control) · [LI16 Latency](#li16--latency) · [LI17 Safety](#li17--safety-and-guardrails) · [LI18 Security](#li18--security-and-privacy) · [LI19 Hallucination](#li19--handling-hallucination) · [LI20 Evaluation](#li20--evaluation)
> [LI21 Monitoring](#li21--monitoring-and-observability) · [LI22 Versioning](#li22--model-and-prompt-versioning) · [LI23 Async & queues](#li23--async-and-queues) · [LI24 UX patterns](#li24--ux-patterns) · [LI25 Testing](#li25--testing-llm-features) · [LI26 Multi-model](#li26--multi-model-routing) · [LI27 Deployment](#li27--deployment-and-rollout) · [LI28 Architecture](#li28--reference-architecture) · [LI29 Pitfalls](#li29--common-pitfalls) · [LI30 My approach](#li30--my-approach) · [Section index](#section-index)

---

## LI1 · What LLM integration means

**Simple explanation.** **LLM integration** is the engineering that turns a model into a **reliable product feature**: calling the API, managing prompts, validating output, adding RAG/tools, handling errors and cost, keeping it safe, and monitoring it in production. The model is 20% of the work — this is the other 80%.

**Architect's view:** I design around the LLM as a probabilistic, external dependency, applying the same rigour I'd apply to any critical third-party service.

**Follow-ups**
- *"One-line?"* — The production engineering that makes an LLM safe, reliable and affordable in an app.
- *"Hardest part?"* — Non-determinism + reliability + cost, not the prompt itself.

---

## LI2 · The integration mindset

**Simple explanation.** I treat the LLM as **non-deterministic** (same input, different output), **fallible** (can be wrong), **external** (network, outages), and **paid** (per token). So I add validation, retries, fallbacks, caching, and monitoring — never assume a perfect, free, instant answer.

**Follow-ups**
- *"Why this mindset?"* — It drives every design choice — guardrails, fallbacks, cost controls.
- *"Compare to a normal API?"* — Like an API that's slow, sometimes wrong, and charges per call.

---

## LI3 · Calling the LLM API

**Simple explanation.** I call a hosted endpoint (**Azure OpenAI** in my case) with the model, messages, and parameters (temperature, max tokens). I keep keys in **Key Vault**, use managed identity, and centralise the call in one client so cross-cutting concerns live in one place.

**Follow-ups**
- *"Why one client wrapper?"* — Central logging, retries, cost tracking, model swaps.
- *"Key parameters?"* — Temperature (creativity), max tokens (length/cost), top_p, stop.

---

## LI4 · Prompt management

**Simple explanation.** Prompts are code, so I **version them**, store them as templates (not scattered strings), test them, and separate **system** (rules) from **user** (input) messages ([file 41 LC5](41-concept-langchain.md#lc5--prompt-templates)). I never concatenate raw user text into instructions ([LI18](#li18--security-and-privacy)).

**Follow-ups**
- *"Why version prompts?"* — A prompt tweak can change behaviour — track and A/B it.
- *"System vs user?"* — System holds durable rules; user holds the request — keeps control.

---

## LI5 · Structured output

**Simple explanation.** When code consumes the answer I force **structured output** (JSON schema / function calling) and **validate** it, so I get reliable fields instead of free text ([file 41 LC8](41-concept-langchain.md#lc8--output-parsers)). If validation fails, I retry or fall back.

**Follow-ups**
- *"Why not parse free text?"* — Fragile — format drifts and breaks code.
- *"How enforce?"* — JSON mode/schema + a validator; reject and retry on failure.

---

## LI6 · Streaming

**Simple explanation.** LLMs generate token-by-token, so I **stream** the response to the UI. The user sees words appear immediately — far better perceived speed than waiting for the whole answer ([file 41 LC17](41-concept-langchain.md#lc17--streaming)).

**Follow-ups**
- *"Why stream?"* — Cuts perceived latency dramatically for chat.
- *"Downsides?"* — Harder to validate/guardrail mid-stream — I check as it completes or buffer sensitive parts.

---

## LI7 · Context window

**Simple explanation.** The model has a token limit (**context window**) for input + output. I manage it: trim history, summarise, and retrieve only the most relevant chunks ([file 40 RG9](40-concept-rag.md#rg9--retrieval)). Overflowing it drops information or errors, and more tokens = more cost.

**Follow-ups**
- *"Long chats?"* — Summarise older turns; keep recent ones verbatim ([file 41 LC11](41-concept-langchain.md#lc11--memory)).
- *"Big docs?"* — Don't dump them — retrieve relevant chunks (RAG).

---

## LI8 · Function/tool calling

**Simple explanation.** **Function calling** lets the model ask my app to run a tool (fetch data, call an API) and use the result ([file 41 LC12](41-concept-langchain.md#lc12--tools-and-agents)). This connects the LLM to live systems safely — the app controls what actually runs.

**Follow-ups**
- *"Who executes the tool?"* — My code — the model only *requests* it, so I validate first.
- *"Use case?"* — Live account balances, database lookups, calculations.

---

## LI9 · RAG integration

**Simple explanation.** For questions about my data I integrate **RAG** ([file 40](40-concept-rag.md)): retrieve relevant chunks and pass them as context so answers are grounded and citable. This is my default for factual, domain-specific features.

**Follow-ups**
- *"RAG vs fine-tuning?"* — RAG for changing/factual knowledge; fine-tuning for style/format ([file 40 RG26](40-concept-rag.md#rg26--rag-vs-fine-tuning)).
- *"Why default to RAG?"* — Fresh, controllable, citable, cheaper to update.

---

## LI10 · Conversation state

**Simple explanation.** LLM calls are **stateless**, so my app stores conversation **history/memory** and sends the needed context each turn ([file 41 LC11](41-concept-langchain.md#lc11--memory)). I manage what to keep, summarise, or drop to fit the context window and cost.

**Follow-ups**
- *"Where store history?"* — Redis/DB keyed by session — not in the model.
- *"All history each call?"* — No — recent + summarised, to control tokens.

---

## LI11 · Reliability (retries, timeouts)

**Simple explanation.** The API can be slow or fail, so I set **timeouts**, **retry with backoff** on transient errors, and use **circuit breakers** so one bad dependency doesn't cascade. Standard resilience patterns applied to the LLM.

**Follow-ups**
- *"Retry everything?"* — Only transient errors (429/5xx/timeouts), with backoff — not validation failures blindly.
- *"Circuit breaker?"* — Stop calling a failing model and fall back fast.

---

## LI12 · Rate limits

**Simple explanation.** LLM endpoints have **token/request limits**. I handle **429s** with backoff, spread load, use **provisioned throughput** for critical paths, and queue non-urgent work so I stay within quota.

**Follow-ups**
- *"Hit limits under load?"* — Queue, backoff, and/or provisioned capacity for guaranteed throughput.
- *"Multiple deployments?"* — Yes — spread across regions/deployments to raise limits.

---

## LI13 · Fallbacks and degradation

**Simple explanation.** When the LLM is down, slow, or over quota I **degrade gracefully**: a cached answer, a cheaper/smaller model, a keyword-search result, or an honest "try again shortly" — never a hard crash. The feature stays usable.

**Follow-ups**
- *"Fallback examples?"* — Secondary model, cache, non-AI path, friendly message.
- *"Why essential?"* — LLMs *will* fail — design for it up front.

---

## LI14 · Caching

**Simple explanation.** I **cache** where safe: exact/semantic response caching for repeated questions, embedding caches, and RAG-context caches. It cuts cost and latency a lot — with care that I don't serve stale or user-specific data wrongly.

**Follow-ups**
- *"Semantic cache?"* — Match similar questions to a cached answer — big savings on FAQs.
- *"Risk?"* — Staleness/privacy — scope caches per tenant and expire them.

---

## LI15 · Cost control

**Simple explanation.** Cost is per token, so I: pick the **cheapest model that passes evals**, trim prompts/context, cache, cap max tokens, and **track spend per feature/user**. I route simple tasks to small models and hard ones to big models ([LI26](#li26--multi-model-routing)).

**Follow-ups**
- *"Biggest lever?"* — Right-sizing the model and shrinking context.
- *"How track cost?"* — Log tokens per call, tagged by feature — alert on spikes.

---

## LI16 · Latency

**Simple explanation.** LLMs are slow (seconds). I improve *perceived* and real latency with **streaming**, **smaller models** for simple steps, **parallel** independent calls, **caching**, and **async** for non-interactive work.

**Follow-ups**
- *"Perceived vs real?"* — Streaming fixes perceived; smaller models/caching fix real.
- *"Long tasks?"* — Make them async with progress, not a blocking request.

---

## LI17 · Safety and guardrails

**Simple explanation.** I add **guardrails**: content filters (Azure AI Content Safety), input/output moderation, allow/deny topics, and rules the model must follow. I validate outputs before acting on them — essential in a regulated firm.

**Follow-ups**
- *"Input and output?"* — Both — filter bad input and check output before showing/acting.
- *"Tooling?"* — Azure AI Content Safety + my own validation rules.

---

## LI18 · Security and privacy

**Simple explanation.** I guard against **prompt injection** (treat user/retrieved text as data, not instructions), keep keys in **Key Vault**, use **private networking**, ensure the provider **doesn't train on my data** (Azure OpenAI), and never put secrets/PII in prompts unnecessarily.

**Follow-ups**
- *"Prompt injection defence?"* — Separate instructions from data, least-privilege tools, validate/limit actions.
- *"Data leaving the org?"* — Azure OpenAI in-tenant — no public API for sensitive data.

---

## LI19 · Handling hallucination

**Simple explanation.** Models can make things up, so I **ground with RAG**, ask for **citations**, instruct "say you don't know", **validate** facts where possible, and keep a **human in the loop** for high-stakes actions ([file 40 RG21](40-concept-rag.md#rg21--reducing-hallucination)).

**Follow-ups**
- *"Can you eliminate it?"* — Not fully — reduce with grounding + citations + validation + oversight.
- *"High-stakes output?"* — Human approval before it affects money/clients.

---

## LI20 · Evaluation

**Simple explanation.** Because output is non-deterministic, I **evaluate** with datasets and scorers ([file 43 LS9](43-concept-langsmith.md#ls9--evaluation)) — measuring correctness, groundedness, safety and cost — before and after every change, instead of eyeballing a few examples.

**Follow-ups**
- *"Why not manual testing?"* — Doesn't scale or catch regressions — automate evals.
- *"When run?"* — On every prompt/model change, in CI.

---

## LI21 · Monitoring and observability

**Simple explanation.** In production I **trace** every call ([file 43](43-concept-langsmith.md)): inputs, outputs, tokens, cost, latency, tool calls, errors and user feedback. LLM features fail silently (plausible-but-wrong), so tracing is how I catch quality issues, not just crashes.

**Follow-ups**
- *"What to log?"* — Prompts, responses, tokens, latency, cost, feedback — with PII care.
- *"Why extra important?"* — Failures are often wrong answers, not exceptions.

---

## LI22 · Model and prompt versioning

**Simple explanation.** I **pin model versions** and **version prompts**, roll out changes gradually (A/B, canary), and can **roll back** instantly. A silent model or prompt change can shift behaviour, so I control and test every change.

**Follow-ups**
- *"Why pin the model?"* — Providers update models — pinning avoids surprise behaviour changes.
- *"Safe rollout?"* — Canary/A-B with evals, easy rollback.

---

## LI23 · Async and queues

**Simple explanation.** For slow or bulk LLM work (batch analysis, document processing) I use **queues and background workers** ([file 49](49-concept-kafka.md)) instead of blocking a request. The user gets a job id and result later; the system stays responsive and rate-limit-friendly.

**Follow-ups**
- *"When async?"* — Long tasks, bulk jobs, anything beyond a few seconds.
- *"Benefit?"* — Responsiveness, ret/rate-limit control, resilience.

---

## LI24 · UX patterns

**Simple explanation.** Good LLM UX: **stream** answers, show **"thinking"** states, display **citations/sources**, allow **feedback** (thumbs up/down), let users **edit/regenerate**, and set expectations ("AI can be wrong"). UX is part of trust and safety.

**Follow-ups**
- *"Why citations?"* — Trust and verifiability — users check the source.
- *"Feedback loop?"* — Thumbs feed evals and prompt improvements.

---

## LI25 · Testing LLM features

**Simple explanation.** I test with **eval datasets** (not asserting exact strings), **golden examples**, **guardrail tests** (injection, unsafe input), and **contract tests** for structured output. I automate these in CI so regressions are caught.

**Follow-ups**
- *"Assert exact output?"* — No — it's non-deterministic; assert properties/quality via scorers.
- *"Security tests?"* — Yes — prompt-injection and unsafe-content cases.

---

## LI26 · Multi-model routing

**Simple explanation.** I **route** each request to the right model: small/cheap for simple tasks, large for hard ones, and a **fallback** model if the primary fails. This optimises cost, latency and reliability together.

**Follow-ups**
- *"How route?"* — By task type/complexity, with rules or a classifier.
- *"Benefit?"* — Lower cost/latency and built-in failover.

---

## LI27 · Deployment and rollout

**Simple explanation.** I ship LLM features like any service: **config-driven** model/prompt, **feature flags**, **canary/A-B**, **evals in CI/CD**, and instant **rollback**. Infra (Azure OpenAI deployments) is provisioned via IaC ([file 37 Z16](37-concept-azure-services.md#z16--infrastructure-as-code)).

**Follow-ups**
- *"Feature flags?"* — Turn AI features on/off per tenant without redeploying.
- *"CI/CD gate?"* — Evals must pass before promotion.

---

## LI28 · Reference architecture

**Simple explanation.** My typical LLM app: **UI → API/orchestrator** (prompt build, guardrails, retries) **→ retriever (vector store)** for RAG **→ Azure OpenAI** **→ validate/parse → stream to UI**, with **Redis** for cache/state, **queues** for async, **Key Vault** for secrets, and **LangSmith/App Insights** for tracing.

**Follow-ups**
- *"Where's the orchestrator?"* — A service (often LangChain/LangGraph) coordinating prompts, tools, RAG, guardrails.
- *"Stateless model?"* — Yes — state lives in Redis/DB, not the LLM.

---

## LI29 · Common pitfalls

**Simple explanation.** Pitfalls: no fallbacks, no cost tracking, parsing free text, ignoring prompt injection, no evals/monitoring, dumping whole documents into the prompt, and assuming the model is always right, fast and free. I design against every one.

**Follow-ups**
- *"Most common in early projects?"* — No monitoring/evals — quality drifts unseen.
- *"Costliest?"* — No cost controls — bills spike from big prompts/models.

---

## LI30 · My approach

**How I answer (the whole picture).** *"I integrate an LLM as a probabilistic, external, paid dependency. I centralise the call in one client with **timeouts, retries, rate-limit handling and cost tracking**; I version prompts and pin model versions; I force **structured output** with validation where code consumes it; and I **stream** to the UI for responsiveness. For factual features I ground with **RAG** and citations, add **guardrails** (content safety, prompt-injection defence) and **fallbacks** (cheaper model, cache, non-AI path) so it degrades gracefully. I keep state in **Redis/DB**, push slow work to **queues**, and I **trace, evaluate and monitor** everything with LangSmith/App Insights so I catch wrong-but-plausible answers, not just crashes. Rollout is config-driven with flags, canary and instant rollback. That's how I took TCW's RAG assistant from prototype to a trustworthy production feature."*

**Follow-ups**
- *"One sentence?"* — Wrap the model with reliability, safety, cost control and observability — and always have a fallback.
- *"First thing you add?"* — Tracing/evals and a fallback path — before scaling anything.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| LI1 | What it means | Engineering that makes an LLM a product |
| LI2 | Mindset | Non-deterministic, fallible, external, paid |
| LI3 | Calling API | One client wrapper; keys in Key Vault |
| LI4 | Prompt mgmt | Version, template, separate system/user |
| LI5 | Structured output | JSON schema + validation |
| LI6 | Streaming | Token-by-token for perceived speed |
| LI7 | Context window | Manage tokens; retrieve, summarise |
| LI8 | Tool calling | Model requests, app executes safely |
| LI9 | RAG | Default for factual, domain answers |
| LI10 | State | History in Redis/DB; model is stateless |
| LI11 | Reliability | Timeouts, retries, circuit breakers |
| LI12 | Rate limits | Backoff, queue, provisioned throughput |
| LI13 | Fallbacks | Degrade gracefully, never crash |
| LI14 | Caching | Response/semantic/embedding caches |
| LI15 | Cost control | Right-size model, trim, cache, track |
| LI16 | Latency | Stream, small models, parallel, async |
| LI17 | Safety | Content filters + output validation |
| LI18 | Security | Injection defence, Key Vault, in-tenant |
| LI19 | Hallucination | Ground, cite, validate, human-in-loop |
| LI20 | Evaluation | Datasets + scorers, not eyeballing |
| LI21 | Monitoring | Trace tokens/cost/latency/quality |
| LI22 | Versioning | Pin model, version prompts, roll back |
| LI23 | Async | Queues/workers for slow/bulk work |
| LI24 | UX | Stream, citations, feedback, expectations |
| LI25 | Testing | Eval datasets, guardrail & contract tests |
| LI26 | Multi-model | Route by task; fallback model |
| LI27 | Deployment | Config-driven, flags, canary, rollback |
| LI28 | Architecture | UI→orchestrator→RAG→LLM→validate |
| LI29 | Pitfalls | No fallback/cost/evals; free-text parsing |
| LI30 | My approach | Reliable, safe, cheap, observed + fallback |

---

[← Embeddings & Semantic Search](45-concept-embeddings-semantic-search.md) · [Home](README.md) · [Next → System Design](47-concept-system-design.md)
