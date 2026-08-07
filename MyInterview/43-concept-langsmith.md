# 43 · Concept: LangSmith (30 questions)

[← LangGraph](42-concept-langgraph.md) · [Home](README.md) · [Next → Vector Databases & Chroma](44-concept-vector-databases-chroma.md)

This file explains **LangSmith** — the platform to **trace, test, evaluate and monitor** LLM apps — in simple English and real depth. I answer from Project B: LangSmith is the feedback loop that made TCW's first production RAG assistant trustworthy.

> Simple one-liner: *"LangSmith is the observability and evaluation layer for LLM apps. It records every run so I can see exactly what the model saw, and it scores quality on datasets so no change ships without passing the bar."*

**Jump to:** [LS1 What is LangSmith](#ls1--what-is-langsmith) · [LS2 Why use it](#ls2--why-use-langsmith) · [LS3 Tracing](#ls3--tracing) · [LS4 Runs/spans](#ls4--runs-and-spans) · [LS5 Setup](#ls5--setting-it-up) · [LS6 Non-LangChain](#ls6--tracing-non-langchain-code) · [LS7 Debugging](#ls7--debugging-with-traces) · [LS8 Datasets](#ls8--datasets) · [LS9 Evaluations](#ls9--evaluations) · [LS10 Evaluators](#ls10--types-of-evaluators)
> [LS11 LLM-as-judge](#ls11--llm-as-judge) · [LS12 RAG evals](#ls12--rag-evaluation) · [LS13 Regression](#ls13--regression-testing) · [LS14 Experiments](#ls14--experiments-and-comparison) · [LS15 Prompt Hub](#ls15--prompt-hub) · [LS16 Monitoring](#ls16--production-monitoring) · [LS17 Feedback](#ls17--capturing-feedback) · [LS18 Annotation](#ls18--annotation-queues) · [LS19 Cost/latency](#ls19--cost-and-latency-tracking) · [LS20 Alerts](#ls20--alerts)
> [LS21 Datasets from prod](#ls21--building-datasets-from-production) · [LS22 CI/CD](#ls22--evals-in-cicd) · [LS23 Security/privacy](#ls23--security-and-privacy) · [LS24 Self-host](#ls24--self-hosting) · [LS25 vs App Insights](#ls25--langsmith-vs-app-insights) · [LS26 vs LangFuse](#ls26--alternatives) · [LS27 With LangGraph](#ls27--with-langgraph) · [LS28 Best practices](#ls28--best-practices) · [LS29 Pitfalls](#ls29--pitfalls) · [LS30 My use](#ls30--how-i-use-langsmith) · [Section index](#section-index)

---

## LS1 · What is LangSmith?

**Simple explanation.** **LangSmith** is a platform for the LLM app lifecycle: **tracing** (record every run), **evaluation** (score quality on datasets), and **monitoring** (watch production). It's built by the LangChain team but works with any LLM code.

**Architect's view:** It's the missing feedback loop for AI. Code has logs, tests and APM; LangSmith is the equivalent for LLM apps — you can't govern what you can't measure.

**Follow-ups**
- *"One-line?"* — Observability + evaluation + monitoring for LLM applications.
- *"Tied to LangChain?"* — Best with it, but it traces plain SDK code too ([LS6](#ls6--tracing-non-langchain-code)).

---

## LS2 · Why use LangSmith?

**Simple explanation.** LLM apps are non-deterministic and opaque. LangSmith lets me **see** each run (prompt, retrieved context, tools, tokens), **measure** quality with evals, and **catch regressions** before release. It turns "it feels better" into a number.

*"Before any prompt or model change ships, it must pass the eval set in LangSmith — that's how I made the RAG app production-grade, not vibe-based."*

**Follow-ups**
- *"Biggest value?"* — Turning subjective quality into measured, gated numbers.
- *"Debugging value?"* — Open any bad answer and see exactly what the model received.

---

## LS3 · Tracing

**Simple explanation.** **Tracing** records everything that happens in a run — the prompt, retrieved chunks, each model/tool call, inputs/outputs, tokens, latency and errors — as a nested tree. It's the flight recorder for an AI request.

**Follow-ups**
- *"What's captured?"* — The full call tree with inputs/outputs, tokens, cost and timing per step.
- *"Why nested?"* — Chains/agents have sub-steps — the tree shows the whole path.

---

## LS4 · Runs and spans

**Simple explanation.** A **run** (or **span**) is one recorded step; a top-level run contains child runs for each sub-step (retrieve, model, tool). Together they form the trace tree of a request.

**Follow-ups**
- *"Run vs trace?"* — A trace is the whole tree; a run/span is one node in it.
- *"Why care?"* — You can drill into the exact sub-step that failed or was slow.

---

## LS5 · Setting it up

**Simple explanation.** For LangChain/LangGraph, I set a few environment variables (`LANGSMITH_TRACING=true`, API key, project) and traces flow automatically — no code changes. Each app logs to a named **project**.

**Follow-ups**
- *"Code changes needed?"* — For LangChain, none — just env vars.
- *"Projects?"* — Separate dev/stage/prod or per-app to keep traces organised.

---

## LS6 · Tracing non-LangChain code

**Simple explanation.** I can trace any Python/JS code with the `@traceable` decorator or the SDK — so raw Azure OpenAI calls or custom logic still show up. LangSmith isn't limited to LangChain apps.

**Follow-ups**
- *"How?"* — Decorate functions with `@traceable` or wrap the client — they appear as runs.
- *"Why it matters?"* — I get one observability tool across all my AI code, framework or not.

---

## LS7 · Debugging with traces

**Simple explanation.** When an answer is wrong, I open its trace and check the chain: were the right chunks retrieved? was the prompt correct? what did the model actually return? Usually the fix is obvious once I see what the model saw.

*"Most 'the AI is wrong' tickets I solve in the trace — nine times out of ten it's retrieval, not the model."*

**Follow-ups**
- *"First thing you look at?"* — The retrieved context — did the right facts even reach the model?
- *"Then?"* — The exact prompt and the raw model output.

---

## LS8 · Datasets

**Simple explanation.** A **dataset** is a saved set of examples (inputs, and often expected outputs) I use to test the app. I build them from real questions, edge cases and past failures. Datasets are the AI equivalent of a test suite.

**Follow-ups**
- *"Where do examples come from?"* — Real production questions, curated edge cases, and past bad answers.
- *"Do they grow?"* — Yes — every new failure becomes a dataset case.

---

## LS9 · Evaluations

**Simple explanation.** An **evaluation** runs my app over a dataset and scores each output with **evaluators**, giving an overall quality number. I run evals on every prompt/model/index change to prove it's better, not just different.

**Follow-ups**
- *"What does an eval produce?"* — Per-example scores and an aggregate — accuracy, groundedness, etc.
- *"How often?"* — On every meaningful change, and in CI ([LS22](#ls22--evals-in-cicd)).

---

## LS10 · Types of evaluators

**Simple explanation.** Evaluators can be **heuristic/code** (exact match, JSON valid, contains a citation), **LLM-as-judge** (a model scores against a rubric), or **human**. I combine them — cheap code checks plus judge/human for nuance.

**Follow-ups**
- *"When code vs judge?"* — Code for objective checks (format, exact facts); judge for open-ended quality.
- *"Human still needed?"* — For spot-checks and to calibrate the automatic evaluators.

---

## LS11 · LLM-as-judge

**Simple explanation.** **LLM-as-judge** uses a model with a strict **rubric** to score outputs (e.g. "is this grounded in the sources? 1–5"). It scales evaluation of open-ended answers, but I calibrate it against human scores so I trust it.

**Follow-ups**
- *"Reliable?"* — Reasonably, with a clear rubric and calibration — I don't take it blindly.
- *"Risk?"* — Judge bias/variance — mitigate with a strict rubric and human spot-checks.

---

## LS12 · RAG evaluation

**Simple explanation.** For RAG I score **retrieval** (did I fetch the right context?) and **generation** (**groundedness/faithfulness** — is it supported by sources? **relevance** — does it answer?). LangSmith runs these evaluators over my dataset ([file 40 RG19](40-concept-rag.md#rg19--evaluating-rag)).

**Follow-ups**
- *"Key RAG metrics here?"* — Context recall/precision, faithfulness/groundedness, answer relevance.
- *"Diagnose retrieval vs generation?"* — Separate scores tell me which half to fix.

---

## LS13 · Regression testing

**Simple explanation.** **Regression testing** re-runs the eval dataset after any change and compares scores to the last version. If groundedness/accuracy drops, I don't ship. Same gate as unit tests for code.

**Follow-ups**
- *"What triggers a re-eval?"* — Prompt, model, retrieval, or chunking changes.
- *"Fail behaviour?"* — Block the release and investigate the trace of regressed cases.

---

## LS14 · Experiments and comparison

**Simple explanation.** LangSmith shows **experiments** side by side — e.g. prompt A vs B, or GPT-4o vs a cheaper model — with scores and cost/latency. I choose changes on evidence, not guesswork.

**Follow-ups**
- *"What do you compare?"* — Prompts, models, retrievers, chunking — on quality, cost and latency together.
- *"Decision basis?"* — The best quality within my cost/latency budget.

---

## LS15 · Prompt Hub

**Simple explanation.** **Prompt Hub** stores and **versions** prompts, so I can manage, compare and roll back prompts like code, and pull them at runtime. No more prompts buried in source with no history.

**Follow-ups**
- *"Why version prompts?"* — A prompt change is a behaviour change — it needs history and rollback.
- *"Runtime pull?"* — Optional — fetch the approved prompt version at runtime.

---

## LS16 · Production monitoring

**Simple explanation.** In production LangSmith dashboards track **volume, latency, cost, error rate**, and quality signals (feedback, online evals). It's my APM for the AI layer — I watch trends and drill into any bad run.

**Follow-ups**
- *"What do you watch?"* — Latency, cost per request, error rate, and answer-quality feedback.
- *"Online evals?"* — Sampled production runs scored automatically to catch drift.

---

## LS17 · Capturing feedback

**Simple explanation.** I log **user feedback** (thumbs up/down, ratings, corrections) against runs. That real signal shows what's actually failing and feeds new dataset cases and monitoring.

**Follow-ups**
- *"How captured?"* — The app sends feedback to the run via the SDK.
- *"Use of it?"* — Prioritise fixes and turn thumbs-down into eval cases.

---

## LS18 · Annotation queues

**Simple explanation.** **Annotation queues** let humans review and label runs (correct/incorrect, add the right answer) in a UI. This builds high-quality datasets and calibrates the LLM-judge.

**Follow-ups**
- *"Who annotates?"* — SMEs/reviewers — their labels become ground truth.
- *"Payoff?"* — Better datasets and trustworthy automatic evaluation.

---

## LS19 · Cost and latency tracking

**Simple explanation.** Each run records **tokens, cost and latency** per step, so I see which prompts/models/steps are expensive or slow and optimise them ([file 38 AS22](38-concept-ai-skills-workflow.md#as22--cost-control)).

**Follow-ups**
- *"Find the cost hotspot?"* — Sort runs by cost/tokens and inspect the heavy step.
- *"Latency hotspot?"* — The trace shows which sub-step is slow (often generation).

---

## LS20 · Alerts

**Simple explanation.** I set **alerts** on production metrics — error-rate spike, latency or cost jump, quality-score drop — so I'm told before users complain. Monitoring without alerts is just history.

**Follow-ups**
- *"What do you alert on?"* — Errors, latency, cost, and feedback/eval-score drops.
- *"Where do alerts go?"* — Team channels/on-call — same as any service alert.

---

## LS21 · Building datasets from production

**Simple explanation.** I turn real production runs — especially failures and thumbs-down — into **dataset examples** with one click. The eval set grows from reality, so it keeps getting more representative.

**Follow-ups**
- *"Why prod-sourced data?"* — It reflects real usage and real failures — the best tests.
- *"Privacy?"* — Redact PII before adding to datasets ([LS23](#ls23--security-and-privacy)).

---

## LS22 · Evals in CI/CD

**Simple explanation.** I run LangSmith **evals in the CI pipeline**: a prompt/model/code change triggers the eval; if scores drop below the threshold, the build fails. Quality becomes a gate, not an afterthought.

*"This is the single practice that made our AI releases safe — evals as a required check, just like unit tests."*

**Follow-ups**
- *"How wired?"* — A CI step calls the eval SDK on the dataset and asserts on the score.
- *"Threshold?"* — Set per metric (e.g. min groundedness) — below it, block.

---

## LS23 · Security and privacy

**Simple explanation.** Traces can contain sensitive data, so I **redact/mask PII**, control **retention**, restrict access (RBAC), and for strict cases use **self-hosting** ([LS24](#ls24--self-hosting)). In finance, trace data is treated like any sensitive data.

**Follow-ups**
- *"Main concern?"* — PII/secrets in prompts or outputs landing in traces — redact at source.
- *"Regulated option?"* — Self-hosted LangSmith keeps data in our environment.

---

## LS24 · Self-hosting

**Simple explanation.** LangSmith can be **self-hosted** in our own cloud/VNet so trace and eval data never leaves our environment — important for a regulated firm with data-residency rules.

**Follow-ups**
- *"Why self-host?"* — Data residency and compliance — keep sensitive traces in-house.
- *"Trade-off?"* — We operate it — more control, more ops.

---

## LS25 · LangSmith vs App Insights

**Simple explanation.** **App Insights** monitors the *service* (requests, dependencies, exceptions, infra). **LangSmith** monitors the *AI* (prompts, retrieved context, tokens, quality). They're complementary — I use both ([file 37 Z9](37-concept-azure-services.md#z9--monitoring-and-devops)).

**Follow-ups**
- *"Do I need both?"* — Yes — App Insights for system health, LangSmith for AI behaviour/quality.
- *"Overlap?"* — Some latency/error overlap, but LangSmith sees inside the LLM steps.

---

## LS26 · Alternatives

**Simple explanation.** Alternatives include **LangFuse** (open-source), **Phoenix/Arize**, **Weights & Biases**, and Azure's own AI evaluation tooling in **AI Foundry**. I pick by ecosystem fit — LangSmith pairs naturally with LangChain/LangGraph.

**Follow-ups**
- *"Open-source option?"* — LangFuse — similar tracing/eval, self-hostable.
- *"Azure-native?"* — AI Foundry evaluation for a fully Azure stack.

---

## LS27 · With LangGraph

**Simple explanation.** LangGraph runs stream full **node-by-node traces** to LangSmith automatically ([file 42 LG23](42-concept-langgraph.md#lg23--observability-with-langsmith)). For an agent, this replay of every state, tool call and decision is how I debug emergent behaviour.

**Follow-ups**
- *"Why crucial for agents?"* — Agent paths vary — the trace shows the exact route taken and why.
- *"Automatic?"* — Yes — with tracing env vars set, graph runs appear as trees.

---

## LS28 · Best practices

**Simple explanation.** Trace everything from day one, build datasets from real usage, run evals in CI as a gate, capture user feedback, monitor cost/latency/quality with alerts, version prompts, and redact PII. Treat AI quality with the same rigour as code.

**Follow-ups**
- *"Highest-impact practice?"* — Evals-as-a-CI-gate — stops regressions reaching users.
- *"Start small?"* — Yes — tracing first, then a small dataset, then CI evals.

---

## LS29 · Pitfalls

**Simple explanation.** Common mistakes: **no eval set** (flying blind), **tiny/unrepresentative datasets**, **trusting the LLM-judge uncalibrated**, **leaking PII into traces**, and treating tracing as optional. Avoid these and the loop actually works.

**Follow-ups**
- *"Worst pitfall?"* — Shipping changes with no eval — you can't tell better from worse.
- *"Judge pitfall?"* — Trusting it without calibrating against humans.

---

## LS30 · How I use LangSmith

**How I answer (the whole picture).** *"LangSmith is my feedback loop for AI. Every run — LangChain, LangGraph or raw SDK — traces there, so I can open any bad answer and see the retrieved context, prompt and output. I keep datasets built from real questions and past failures, and run evaluations (code checks, LLM-as-judge, and human annotation) that score groundedness, relevance, cost and latency. Those evals run in CI as a gate: no prompt or model change ships if quality drops. In production I monitor volume, latency, cost and quality with alerts, capture user feedback, version prompts, and redact PII — self-hosting where data residency demands it. Paired with App Insights, that's how I made TCW's first production RAG app measurable, safe and continuously improving."*

**Follow-ups**
- *"One-line value?"* — It turns AI quality from a feeling into a measured, gated number.
- *"With the rest of the stack?"* — LangChain/LangGraph for building, LangSmith for seeing and scoring, App Insights for service health.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| LS1 | What is LangSmith | Trace + evaluate + monitor LLM apps |
| LS2 | Why use it | See, measure, and gate AI quality |
| LS3 | Tracing | Flight recorder for each run |
| LS4 | Runs/spans | Trace tree of steps |
| LS5 | Setup | Env vars; automatic for LangChain |
| LS6 | Non-LangChain | @traceable traces any code |
| LS7 | Debugging | Open the trace; usually retrieval |
| LS8 | Datasets | Test suite of real examples |
| LS9 | Evaluations | Score app over a dataset |
| LS10 | Evaluators | Code, LLM-judge, human |
| LS11 | LLM-as-judge | Rubric-scored, calibrated |
| LS12 | RAG evals | Retrieval + groundedness + relevance |
| LS13 | Regression | Re-eval on change; block drops |
| LS14 | Experiments | Compare prompts/models by evidence |
| LS15 | Prompt Hub | Version and roll back prompts |
| LS16 | Monitoring | APM for the AI layer |
| LS17 | Feedback | Log user thumbs/ratings to runs |
| LS18 | Annotation | Human labels build ground truth |
| LS19 | Cost/latency | Per-step tokens/cost/timing |
| LS20 | Alerts | Warn on error/latency/cost/quality |
| LS21 | Datasets from prod | Turn failures into test cases |
| LS22 | CI/CD | Evals as a required build gate |
| LS23 | Security | Redact PII, control retention/access |
| LS24 | Self-host | Keep data in-house for compliance |
| LS25 | vs App Insights | AI behaviour vs service health |
| LS26 | Alternatives | LangFuse, Phoenix, AI Foundry |
| LS27 | With LangGraph | Node-by-node agent traces |
| LS28 | Best practices | Trace, dataset, CI-eval, alert, redact |
| LS29 | Pitfalls | No/weak evals, uncalibrated judge, PII |
| LS30 | My use | Measured, gated, continuously-improving AI |

---

[← LangGraph](42-concept-langgraph.md) · [Home](README.md) · [Next → Vector Databases & Chroma](44-concept-vector-databases-chroma.md)
