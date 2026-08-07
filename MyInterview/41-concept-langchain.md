# 41 · Concept: LangChain (30 questions)

[← RAG](40-concept-rag.md) · [Home](README.md) · [Next → LangGraph](42-concept-langgraph.md)

This file explains **LangChain** — the framework for building LLM apps by composing reusable pieces — in simple English and real depth. I answer from Project B: I built TCW's first production RAG assistant with LangChain, LangGraph, LangSmith and Chroma.

> Simple one-liner: *"LangChain gives me building blocks — models, prompts, retrievers, tools, memory — and a clean way to wire them together, so I build LLM apps from tested parts instead of raw API calls and string glue."*

**Jump to:** [LC1 What is LangChain](#lc1--what-is-langchain) · [LC2 Why use it](#lc2--why-use-langchain) · [LC3 Core pieces](#lc3--core-building-blocks) · [LC4 LCEL](#lc4--lcel-the-expression-language) · [LC5 Models](#lc5--chat-models-and-llms) · [LC6 Prompts](#lc6--prompt-templates) · [LC7 Output parsers](#lc7--output-parsers) · [LC8 Chains](#lc8--chains) · [LC9 Retrievers](#lc9--retrievers) · [LC10 Vector stores](#lc10--vector-store-integrations)
> [LC11 Document loaders](#lc11--document-loaders) · [LC12 Text splitters](#lc12--text-splitters) · [LC13 Embeddings](#lc13--embeddings) · [LC14 Memory](#lc14--memory) · [LC15 Tools](#lc15--tools) · [LC16 Agents](#lc16--agents) · [LC17 RAG chain](#lc17--building-a-rag-chain) · [LC18 Streaming](#lc18--streaming) · [LC19 Async/batch](#lc19--async-and-batch) · [LC20 Callbacks](#lc20--callbacks-and-tracing)
> [LC21 Structured output](#lc21--structured-output) · [LC22 vs LangGraph](#lc22--langchain-vs-langgraph) · [LC23 LangSmith](#lc23--langchain-and-langsmith) · [LC24 Errors/retries](#lc24--error-handling-and-retries) · [LC25 Caching](#lc25--caching) · [LC26 Testing](#lc26--testing) · [LC27 Production](#lc27--running-in-production) · [LC28 Pitfalls](#lc28--common-pitfalls) · [LC29 Alternatives](#lc29--alternatives) · [LC30 My use](#lc30--how-i-use-langchain) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of LangChain in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. LangChain gives me reusable parts plus a clean way to wire them.** Model wrappers, prompt templates, retrievers, tools, memory, output parsers — standard components — and a way to compose them into chains and agents. So I build LLM apps from tested pieces instead of raw API calls and string glue. On Project B I built TCW's first production RAG assistant this way, with LangGraph, LangSmith and Chroma.

**2. It standardises how I talk to models and data.** Swap OpenAI for another provider, or one vector store for another, and most of my code stays the same because I'm coding against LangChain's interfaces. That portability is a big part of why I use it.

**3. LCEL is the composition glue.** The LangChain Expression Language lets me pipe components together — prompt → model → parser — into a runnable chain that supports streaming, batching and async for free. It's the modern, clean way to build; I think of it like composing Unix pipes.

**4. Prompts and output parsers make results trustworthy.** Prompt templates keep my prompts consistent and parameterised; output parsers (and structured output) force the model's reply into a schema I can validate. Together they turn free text into data the next step can rely on.

**5. Retrievers, loaders, splitters and embeddings are the RAG toolkit.** Document loaders pull data in, text splitters chunk it, embeddings turn it into vectors, vector stores hold it, and retrievers fetch the relevant bits at query time. This is exactly the pipeline behind my RAG assistant.

**6. Memory carries context across turns.** For a chat assistant I need it to remember earlier messages within the window. LangChain's memory abstractions handle that so a conversation feels continuous instead of amnesiac.

**7. Tools and agents let the model act, not just talk.** A tool is a function the model can call (search, lookup, calculation); an agent decides which tools to use to reach a goal. LangChain gives me the wiring — though for complex, stateful control I graduate to LangGraph.

**8. Production means callbacks, tracing, retries and caching.** LangSmith gives me tracing and evaluation; callbacks expose what's happening; retries and caching keep it reliable and cheap. I treat a LangChain app like any other service — observable, tested and hardened before it ships.

**The full-stack / architect lens:** the later Q&As go deeper — structured output, LangChain vs LangGraph, LangSmith, error handling and retries, caching, testing, running in production, common pitfalls, alternatives, and how I actually use it. They all trace back to the core: reusable parts, composed cleanly with LCEL, wired into RAG or agents, and hardened for production.

**One rule I never break:** *use LangChain for the plumbing, but keep my own logic and tests around it — never let the framework become a black box I can't reason about.*

---

## LC1 · What is LangChain?

**Simple explanation.** **LangChain** is an open-source framework for building applications with LLMs. It provides standard **components** — model wrappers, prompt templates, retrievers, tools, memory — and a way to **compose** them into chains and agents, so I don't hand-write the plumbing.

**Architect's view:** It's the glue and the parts for LLM apps. It standardises how I talk to models and data, so I focus on the logic, not the boilerplate.

**Follow-ups**
- *"One-line?"* — A toolkit of reusable pieces plus a way to wire them into LLM apps.
- *"Python only?"* — Mainly Python (also JS/TS) — I use the Python side alongside my FastAPI services.

---

## LC2 · Why use LangChain?

**Simple explanation.** It saves time and enforces good structure: swappable model/vector-store integrations, ready-made RAG and agent patterns, streaming, retries, and tracing hooks. I build from tested parts and swap providers without rewriting my app.

*"The big win is abstraction — I can change the model or vector DB by config, and I get RAG/agent patterns and LangSmith tracing out of the box."*

**Follow-ups**
- *"Biggest benefit?"* — Standard, swappable components + patterns — less glue code, faster to production.
- *"Any cost?"* — A learning curve and abstraction overhead — for simple apps a plain SDK call can be enough ([LC28](#lc28--common-pitfalls)).

---

## LC3 · Core building blocks

**Simple explanation.** The main pieces I use: **Models** (chat/LLM), **Prompts** (templates), **Output parsers** (structure the response), **Retrievers** + **Vector stores** (RAG), **Document loaders** + **Text splitters** (ingestion), **Embeddings**, **Memory**, **Tools**, and **Agents**. Each is a standard interface.

**Follow-ups**
- *"Why standard interfaces?"* — Swap implementations (e.g. OpenAI ↔ Azure OpenAI, Chroma ↔ AI Search) without changing app code.
- *"Which do you use most?"* — Prompts, retrievers, vector stores, output parsers — the RAG core.

---

## LC4 · LCEL (the expression language)

**Simple explanation.** **LCEL** (LangChain Expression Language) composes components with the pipe operator: `prompt | model | parser`. The output of one flows into the next. It gives streaming, async and batching for free and makes chains readable.

```python
chain = prompt | chat_model | StrOutputParser()
answer = chain.invoke({"question": q})
```

**Follow-ups**
- *"Why LCEL?"* — Declarative, composable chains with built-in streaming/async/batch — less imperative glue.
- *"Readable?"* — Yes — the pipe shows the data flow at a glance.

---

## LC5 · Chat models and LLMs

**Simple explanation.** LangChain wraps model providers behind a common interface (`ChatOpenAI`, `AzureChatOpenAI`, etc.). I code against the interface, so switching providers is a config change, not a rewrite.

**Follow-ups**
- *"Chat vs LLM interface?"* — Chat models take message lists (system/user/assistant); older LLMs take plain text — chat is standard now.
- *"Provider switch?"* — Swap the class/config — e.g. OpenAI to Azure OpenAI — the chain stays the same.

---

## LC6 · Prompt templates

**Simple explanation.** A **PromptTemplate** is a reusable prompt with placeholders I fill at runtime. It keeps prompts versioned, consistent, and testable instead of scattered f-strings.

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer only from the context. Cite sources."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
```

**Follow-ups**
- *"Why templates over f-strings?"* — Reuse, versioning, validation of inputs — cleaner and testable.
- *"Where's the system rule?"* — In the template's system message — the guardrail every call inherits.

---

## LC7 · Output parsers

**Simple explanation.** **Output parsers** turn the model's text into structured data — a string, JSON, or a Pydantic object — and can retry/fix malformed output. They're my contract boundary after the model.

**Follow-ups**
- *"Why parse?"* — Downstream code needs reliable structure, not free text.
- *"On parse failure?"* — Use a retrying/fixing parser or re-prompt with the error, then fall back safely.

---

## LC8 · Chains

**Simple explanation.** A **chain** is components wired in sequence (via LCEL) — e.g. prompt → model → parser, or a multi-step RAG chain. Chains are the fixed-path **workflows** of file 38 ([AS3](38-concept-ai-skills-workflow.md#as3--what-is-an-ai-workflow)).

**Follow-ups**
- *"Chain vs agent?"* — A chain follows my fixed steps; an agent lets the model choose steps ([LC16](#lc16--agents)).
- *"Multi-step chains?"* — Yes — compose sub-chains and pass outputs along.

---

## LC9 · Retrievers

**Simple explanation.** A **retriever** is the standard interface that returns relevant documents for a query — usually backed by a vector store, but it can be hybrid, keyword, or custom. It's the 'R' in my RAG chains.

**Follow-ups**
- *"Why an abstraction over the vector store?"* — Swap retrieval strategy (vector/hybrid/re-rank) without changing the chain.
- *"Configurable?"* — Yes — top-k, filters, search type are set on the retriever.

---

## LC10 · Vector store integrations

**Simple explanation.** LangChain integrates many vector stores — **Chroma**, Azure AI Search, pgvector, FAISS, Pinecone — behind one interface. I used **Chroma** for the first RAG app ([file 44](44-concept-vector-databases-chroma.md)); I can move to Azure AI Search by config.

**Follow-ups**
- *"Why start with Chroma?"* — Simple, local, fast to prototype — then swap to a managed store for scale.
- *"Swap cost?"* — Low — the retriever interface hides the store; mainly config + re-index.

---

## LC11 · Document loaders

**Simple explanation.** **Document loaders** read source data — PDF, Word, HTML, CSV, DB, SharePoint — into a standard `Document` (text + metadata). They're the front of the ingestion pipeline.

**Follow-ups**
- *"Why standard Documents?"* — So splitters, embedders and retrievers all work the same regardless of source.
- *"Metadata?"* — Loaders capture source/path/date — vital for citations and filtering.

---

## LC12 · Text splitters

**Simple explanation.** **Text splitters** chunk documents for indexing ([file 40 RG6](40-concept-rag.md#rg6--chunking)). The recursive splitter respects structure (paragraphs → sentences) with overlap; there are code- and markdown-aware splitters too.

**Follow-ups**
- *"Which splitter?"* — Recursive/structure-aware by default; specialised ones for code/markdown/tables.
- *"Tune what?"* — Chunk size and overlap, measured against the eval set.

---

## LC13 · Embeddings

**Simple explanation.** LangChain wraps **embedding models** (Azure OpenAI, OpenAI, open models) behind one interface to turn text into vectors for indexing and retrieval ([file 45](45-concept-embeddings-semantic-search.md)). Same model for docs and queries.

**Follow-ups**
- *"Which embedding model?"* — Azure OpenAI embeddings in a regulated firm — privacy and compliance.
- *"Consistency?"* — Index and query must use the same embedding model.

---

## LC14 · Memory

**Simple explanation.** **Memory** stores conversation history so a chat chain has context across turns — from simple buffer memory to summarised or vector-backed memory for long chats ([file 38 AS15](38-concept-ai-skills-workflow.md#as15--memory-in-workflows)).

**Follow-ups**
- *"Why summarise memory?"* — Long chats blow the context window — summarise older turns to save tokens.
- *"State in production?"* — Often LangGraph handles durable state better for complex apps ([LC22](#lc22--langchain-vs-langgraph)).

---

## LC15 · Tools

**Simple explanation.** A **tool** is a function the model can call — search, calculator, API, DB query. I define it with a name, description and argument schema; the model requests it; LangChain runs it and returns the result ([file 39 AG6](39-concept-ai-agents-agentic.md#ag6--tools-for-agents)).

**Follow-ups**
- *"How define a tool?"* — A typed function with a clear docstring/schema — the description guides the model.
- *"Safety?"* — Least privilege, validate arguments, gate destructive tools.

---

## LC16 · Agents

**Simple explanation.** LangChain **agents** let the model choose which tools to call in a loop to reach a goal ([file 39](39-concept-ai-agents-agentic.md)). For anything beyond simple, I now build agents with **LangGraph** for explicit state and control ([file 42](42-concept-langgraph.md)).

**Follow-ups**
- *"LangChain agents vs LangGraph?"* — Classic agents are quick; LangGraph gives durable state, branching and control I need in production.
- *"Guardrails?"* — Step caps, tool allow-lists, human-in-the-loop — same as file 39.

---

## LC17 · Building a RAG chain

**Simple explanation.** A RAG chain in LCEL: take the question → retriever fetches context → prompt injects context + question → model answers → parser structures it.

```python
rag = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt | chat_model | StrOutputParser()
)
rag.invoke("What is the fee schedule?")
```

**Follow-ups**
- *"Where do citations come from?"* — Retrieved docs carry source metadata; I include it in the prompt/output.
- *"Add re-ranking?"* — Insert a re-rank step between retriever and prompt.

---

## LC18 · Streaming

**Simple explanation.** LCEL chains **stream** tokens as the model generates them, so the UI shows the answer progressively ([file 38 AS23](38-concept-ai-skills-workflow.md#as23--latency-and-streaming)). `chain.stream(...)` yields chunks.

**Follow-ups**
- *"Why stream?"* — Much better UX — words appear immediately instead of a long wait.
- *"Works through retrieval?"* — Retrieval finishes first; generation streams — I show a "searching…" state meanwhile.

---

## LC19 · Async and batch

**Simple explanation.** LCEL gives `ainvoke` (async) and `batch` (many inputs) for free. Async fits my FastAPI services; batch processes many items efficiently (e.g. embedding a folder of docs).

**Follow-ups**
- *"Why async?"* — LLM/IO calls are slow — async frees the server to handle other requests.
- *"Batch use?"* — Bulk embedding/ingestion and offline evaluation runs.

---

## LC20 · Callbacks and tracing

**Simple explanation.** **Callbacks** hook into each step (start, token, end, error) for logging, metrics and tracing. With one setting they feed **LangSmith** ([file 43](43-concept-langsmith.md)) so I can replay any run — prompts, retrieved chunks, tokens, latency.

**Follow-ups**
- *"Why callbacks matter?"* — Observability — you can't debug or govern what you can't see.
- *"Enable tracing?"* — Set the LangSmith env vars — traces flow automatically.

---

## LC21 · Structured output

**Simple explanation.** `with_structured_output(MyModel)` makes the model return data matching a Pydantic schema, validated automatically ([file 38 AS8](38-concept-ai-skills-workflow.md#as8--structured-output)). Reliable structure without hand-parsing.

```python
structured = chat_model.with_structured_output(Extraction)
structured.invoke("Extract the amount and date")  # -> Extraction object
```

**Follow-ups**
- *"Why prefer this?"* — Type-safe results, fewer parsing errors, cleaner downstream code.
- *"On failure?"* — It retries/repairs; I still validate and handle the rare miss.

---

## LC22 · LangChain vs LangGraph

**Simple explanation.** **LangChain** is great for linear chains and quick agents. **LangGraph** ([file 42](42-concept-langgraph.md)) models the app as a **stateful graph** with nodes, edges, branches, loops, persistence and human-in-the-loop — what I use for reliable, complex agents.

*"Chains for straight-through pipelines; LangGraph when I need real control flow, state and recovery."*

**Follow-ups**
- *"When switch to LangGraph?"* — Loops, branches, durable state, human approval — production agents.
- *"Do they coexist?"* — Yes — LangGraph nodes use LangChain components.

---

## LC23 · LangChain and LangSmith

**Simple explanation.** **LangSmith** is the observability + evaluation platform from the same team ([file 43](43-concept-langsmith.md)). LangChain apps send traces to it automatically, and I run **evaluations** on datasets there — the quality gate for my RAG app.

**Follow-ups**
- *"What does LangSmith add?"* — Trace replay, datasets, evals, and prompt comparison — the feedback loop.
- *"Only for LangChain?"* — Best with it, but it can trace non-LangChain code too.

---

## LC24 · Error handling and retries

**Simple explanation.** I add `with_retry` for transient failures (timeouts, 429s), `with_fallbacks` to swap to a backup model/provider, and validate outputs. Reliability discipline — the same as my ETL work.

**Follow-ups**
- *"Fallbacks?"* — If the primary model fails, automatically try a backup — keeps the app up.
- *"Retry everything?"* — No — transient errors only; not validation failures.

---

## LC25 · Caching

**Simple explanation.** LangChain supports **LLM response caching** (in-memory, Redis, semantic) so repeated prompts don't re-hit the model ([file 38 AS24](38-concept-ai-skills-workflow.md#as24--caching)). Big cost/latency win for FAQs.

**Follow-ups**
- *"Which cache backend?"* — Redis for a shared, scaled-out cache; semantic cache for similar questions.
- *"Risk?"* — Semantic cache returning a close-but-wrong answer — set a strict threshold.

---

## LC26 · Testing

**Simple explanation.** I unit-test deterministic pieces (prompt formatting, parsers, tools, retrieval filters) and evaluate the model parts with LangSmith datasets. I mock the model in unit tests for speed and determinism.

**Follow-ups**
- *"Mock the LLM?"* — Yes in unit tests — fast, deterministic; real-model quality goes through evals.
- *"Regression?"* — Re-run eval datasets on every change; gate on score.

---

## LC27 · Running in production

**Simple explanation.** I wrap chains in a **FastAPI** service, secrets in **Key Vault**, models via **Azure OpenAI**, tracing to **LangSmith** + **App Insights**, caching in **Redis**, retries/fallbacks on, and evals as a CI gate. Standard service discipline around the LLM.

**Follow-ups**
- *"Where does it run?"* — Containerised on App Service/Container Apps ([file 37](37-concept-azure-services.md)).
- *"Version pinning?"* — Pin model, prompt and LangChain versions; re-eval before upgrades.

---

## LC28 · Common pitfalls

**Simple explanation.** Watch for: **over-abstraction** (using LangChain where a plain SDK call would do), **version churn** (fast-moving API), **hidden prompts** in some helpers, and **too many layers** hurting debuggability. I keep chains explicit and lean.

**Follow-ups**
- *"When NOT to use LangChain?"* — A single simple call — the raw SDK is clearer.
- *"How avoid hidden behaviour?"* — Prefer explicit LCEL, inspect prompts, and trace with LangSmith.

---

## LC29 · Alternatives

**Simple explanation.** Alternatives include **LlamaIndex** (data/RAG-focused), **Semantic Kernel** (Microsoft, strong .NET story), **Haystack**, and raw SDKs. I pick by fit — LangChain/LangGraph for flexible orchestration; Semantic Kernel when I'm deep in .NET.

**Follow-ups**
- *"LangChain vs LlamaIndex?"* — LlamaIndex shines at data/RAG indexing; LangChain is broader orchestration — they can combine.
- *"Why Semantic Kernel sometimes?"* — First-class .NET integration for my ASP.NET stack.

---

## LC30 · How I use LangChain

**How I answer (the whole picture).** *"I use LangChain for the building blocks and LCEL for clean, streaming, async chains — loaders and splitters for ingestion, embeddings and a retriever for RAG, prompt templates with a strict grounding rule, and structured output for reliable results. For anything with loops, branches, durable state or human approval I move to LangGraph, and I wire everything to LangSmith for tracing and evaluation. In production it sits inside a FastAPI service on Azure with Key Vault, Azure OpenAI, Redis caching and retries/fallbacks. That's the stack behind TCW's first production RAG assistant — built from tested parts, observable, and evaluated."*

**Follow-ups**
- *"Why a framework at all?"* — Speed, swappable integrations, patterns, and free observability — without reinventing plumbing.
- *"Where's the control?"* — In my code and LangGraph — the framework helps; I still own the flow.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| LC1 | What is LangChain | Framework of LLM components + composition |
| LC2 | Why use it | Swappable parts, patterns, tracing — less glue |
| LC3 | Core pieces | Models, prompts, parsers, retrievers, tools, memory |
| LC4 | LCEL | Pipe-composed chains with streaming/async/batch |
| LC5 | Models | One interface over providers; swap by config |
| LC6 | Prompt templates | Reusable, versioned, testable prompts |
| LC7 | Output parsers | Turn text into validated structure |
| LC8 | Chains | Fixed-path workflows via LCEL |
| LC9 | Retrievers | Standard interface to fetch relevant docs |
| LC10 | Vector stores | Chroma/AI Search/pgvector behind one API |
| LC11 | Loaders | Read many sources into standard Documents |
| LC12 | Text splitters | Structure-aware chunking with overlap |
| LC13 | Embeddings | Text → vectors; same model both sides |
| LC14 | Memory | Conversation state; summarise long chats |
| LC15 | Tools | Model-callable functions, run safely by code |
| LC16 | Agents | Model chooses tools; use LangGraph for control |
| LC17 | RAG chain | retriever → prompt → model → parser |
| LC18 | Streaming | Progressive token output for UX |
| LC19 | Async/batch | Fit FastAPI; bulk embedding/eval |
| LC20 | Callbacks | Hooks feeding LangSmith tracing |
| LC21 | Structured output | Pydantic-validated model results |
| LC22 | vs LangGraph | Chains vs stateful graph control |
| LC23 | LangSmith | Tracing + evaluation feedback loop |
| LC24 | Errors/retries | Retry, fallback, validate |
| LC25 | Caching | Redis/semantic cache cuts cost/latency |
| LC26 | Testing | Unit-test parts; eval the model |
| LC27 | Production | FastAPI + Key Vault + Azure OpenAI + evals |
| LC28 | Pitfalls | Over-abstraction, version churn, hidden prompts |
| LC29 | Alternatives | LlamaIndex, Semantic Kernel, Haystack |
| LC30 | My use | Tested parts + LangGraph control + LangSmith evals |

---

[← RAG](40-concept-rag.md) · [Home](README.md) · [Next → LangGraph](42-concept-langgraph.md)
