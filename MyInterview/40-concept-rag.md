# 40 · Concept: RAG — Retrieval-Augmented Generation (30 questions)

[← AI Agents](39-concept-ai-agents-agentic.md) · [Home](README.md) · [Next → LangChain](41-concept-langchain.md)

This file explains **RAG** — giving an LLM your own data so it answers from facts, not guesses — in simple English and real depth. I answer from Project B: I authored TCW's AI/LLM reference architecture and shipped the firm's **first production RAG assistant**.

> Simple one-liner: *"RAG = retrieve the right facts from my own data, then let the LLM answer using only those facts, with citations. It's the single biggest lever against hallucination."*

**Jump to:** [RG1 What is RAG](#rg1--what-is-rag) · [RG2 Why RAG](#rg2--why-use-rag) · [RG3 RAG vs fine-tuning](#rg3--rag-vs-fine-tuning) · [RG4 The pipeline](#rg4--the-rag-pipeline) · [RG5 Ingestion](#rg5--ingestion-and-indexing) · [RG6 Chunking](#rg6--chunking) · [RG7 Embeddings](#rg7--embeddings) · [RG8 Vector store](#rg8--the-vector-store) · [RG9 Retrieval](#rg9--retrieval) · [RG10 Hybrid search](#rg10--hybrid-search)
> [RG11 Re-ranking](#rg11--re-ranking) · [RG12 Prompt assembly](#rg12--prompt-assembly) · [RG13 Grounding](#rg13--grounding-and-citations) · [RG14 Metadata filters](#rg14--metadata-filtering) · [RG15 Query rewriting](#rg15--query-rewriting) · [RG16 Multi-hop](#rg16--multi-hop-questions) · [RG17 Chunk size](#rg17--choosing-chunk-size) · [RG18 Freshness](#rg18--keeping-data-fresh) · [RG19 Evaluation](#rg19--evaluating-rag) · [RG20 Hallucination](#rg20--hallucination-control)
> [RG21 Security](#rg21--security-and-access-control) · [RG22 Cost](#rg22--cost) · [RG23 Latency](#rg23--latency) · [RG24 Agentic RAG](#rg24--agentic-rag) · [RG25 Graph RAG](#rg25--graph-rag) · [RG26 On Azure](#rg26--rag-on-azure) · [RG27 Failure modes](#rg27--common-failure-modes) · [RG28 When not to](#rg28--when-not-to-use-rag) · [RG29 Testing](#rg29--testing-rag) · [RG30 My architecture](#rg30--my-rag-reference-architecture) · [Section index](#section-index)

---

## RG1 · What is RAG?

**Simple explanation.** **RAG (Retrieval-Augmented Generation)** means: before the LLM answers, I **retrieve** relevant facts from my own data and put them in the prompt, so the model **generates** an answer grounded in those facts — not its training memory. Retrieve, then generate.

**Architect's view:** RAG turns a general model into a domain expert on *my* data without retraining it. It's how I let an LLM safely answer about TCW's own documents.

**Follow-ups**
- *"One-line definition?"* — Fetch the right context from my data, then let the model answer from it with citations.
- *"The three letters?"* — Retrieval (find facts), Augmented (add to prompt), Generation (model writes the answer).

---

## RG2 · Why use RAG?

**Simple explanation.** Because a base LLM doesn't know my private/current data and will guess. RAG gives it **accurate, up-to-date, private** facts, cuts hallucination, provides **citations**, and needs **no retraining** when data changes — I just update the index.

*"For a regulated firm, 'answer only from grounded sources and cite them' is the difference between a demo and something I can put in production."*

**Follow-ups**
- *"Main benefits?"* — Accuracy, freshness, privacy, citations, and cheap updates (re-index, not re-train).
- *"Why not just a bigger model?"* — A bigger model still doesn't know my private data — and it's costlier.

---

## RG3 · RAG vs fine-tuning

**Simple explanation.** **RAG** adds knowledge at query time via retrieval — best for facts that change and for citations. **Fine-tuning** bakes behaviour/style into the model by training — best for tone, format, or narrow skills, not fresh facts. They're complementary.

*"Rule of thumb: RAG for knowledge, fine-tuning for behaviour. I reach for RAG first — it's cheaper to build and to keep current."*

**Follow-ups**
- *"Which for changing data?"* — RAG — update the index, no retraining.
- *"Can you use both?"* — Yes — fine-tune for style/format, RAG for the facts.

---

## RG4 · The RAG pipeline

**Simple explanation.** Two phases. **Offline (index):** load docs → chunk → embed → store vectors. **Online (query):** embed the question → retrieve top chunks → (re-rank) → build prompt with context → LLM answers with citations → validate.

**Follow-ups**
- *"Two phases?"* — Indexing (prepare data) and querying (answer with retrieved context).
- *"Where does quality come from?"* — Mostly retrieval — good chunks in means a good answer out; bad retrieval dooms the answer.

---

## RG5 · Ingestion and indexing

**Simple explanation.** **Ingestion** loads source data (PDFs, wikis, DB rows), cleans it, splits into chunks, generates embeddings, and stores them with **metadata** (source, date, permissions) in the vector store. It's an ETL job — my Project A strength applied to AI.

**Follow-ups**
- *"Why metadata?"* — To filter by source/date/permission and to build citations.
- *"One-off or ongoing?"* — Ongoing — a scheduled pipeline keeps the index fresh ([RG18](#rg18--keeping-data-fresh)).

---

## RG6 · Chunking

**Simple explanation.** **Chunking** splits documents into passages so retrieval returns focused pieces. I chunk by structure (headings/paragraphs) with small **overlap** so meaning isn't cut across a boundary. Chunk quality drives retrieval quality ([file 38 AS17](38-concept-ai-skills-workflow.md#as17--chunking)).

**Follow-ups**
- *"Too big vs too small?"* — Too big dilutes relevance and wastes tokens; too small loses context — tune to the content.
- *"Best practice?"* — Structure-aware chunks with overlap, keeping related text together.

---

## RG7 · Embeddings

**Simple explanation.** An **embedding** turns text into a vector (a list of numbers) that captures meaning, so similar meanings sit close together in vector space ([file 45](45-concept-embeddings-semantic-search.md)). I embed both my chunks (offline) and the user's question (online) to compare them.

**Follow-ups**
- *"Why embeddings for retrieval?"* — They let me match by *meaning*, not exact words — finds relevant text even with different wording.
- *"Same model both sides?"* — Yes — query and documents must use the same embedding model to be comparable.

---

## RG8 · The vector store

**Simple explanation.** A **vector store** (e.g. Chroma, Azure AI Search, pgvector) stores embeddings and finds the **nearest** vectors to a query fast, using ANN (approximate nearest neighbour) indexes. It's the retrieval engine of RAG ([file 44](44-concept-vector-databases-chroma.md)).

**Follow-ups**
- *"Why not a normal DB?"* — Vector similarity search needs specialised ANN indexes for speed at scale.
- *"What did you use?"* — Chroma for the first RAG app (Project B); Azure AI Search for the Azure-native path.

---

## RG9 · Retrieval

**Simple explanation.** **Retrieval** embeds the question and pulls the **top-k** most similar chunks. k is a trade-off: too few misses context, too many adds noise and cost. I tune k and use filters to keep it relevant.

**Follow-ups**
- *"What's top-k?"* — The number of chunks I fetch — typically a handful; I tune it by eval.
- *"Biggest retrieval mistake?"* — Grabbing too many low-relevance chunks — noise hurts the answer.

---

## RG10 · Hybrid search

**Simple explanation.** **Hybrid search** combines **vector** (meaning) and **keyword/BM25** (exact terms) search, then merges results. It catches both semantically-similar and exact-match content — usually the best retrieval quality.

*"Pure vector can miss an exact code or ID; hybrid gets both — my default when the platform supports it."*

**Follow-ups**
- *"When does keyword still matter?"* — Exact IDs, codes, names — where meaning-match alone can miss.
- *"How merge?"* — Score fusion (e.g. reciprocal rank fusion) then re-rank the top results.

---

## RG11 · Re-ranking

**Simple explanation.** After retrieval I can **re-rank** the top chunks with a stronger model (a cross-encoder) that scores each chunk against the question more precisely, then keep the best few. It lifts answer quality by sending only the most relevant context.

**Follow-ups**
- *"Why re-rank?"* — First-pass retrieval is fast but rough; re-ranking sharpens relevance before the LLM sees it.
- *"Cost?"* — Extra compute — worth it when precision matters; skip for simple cases.

---

## RG12 · Prompt assembly

**Simple explanation.** I build the final prompt: a **system rule** ("answer only from the context; cite sources; if not present, say you don't know"), the **retrieved chunks** (with source tags), and the **question**. Order and clarity matter — the model answers from what I give it.

**Follow-ups**
- *"Key instruction?"* — "Use only the provided context and cite it; otherwise say you don't know."
- *"Token budget?"* — Keep context tight — relevant chunks only, to fit the window and cut cost.

---

## RG13 · Grounding and citations

**Simple explanation.** **Grounding** means the answer is based on retrieved sources; **citations** show which chunk/source each claim came from. Together they make answers trustworthy and checkable — essential in finance.

*"Every answer from my RAG assistant carries sources — a user (and auditor) can verify it."*

**Follow-ups**
- *"Why cite?"* — Trust and audit — users can verify; it also discourages the model from inventing.
- *"How do you get reliable citations?"* — Tag chunks with source metadata and ask the model to reference those tags.

---

## RG14 · Metadata filtering

**Simple explanation.** I attach **metadata** to chunks (source, date, department, permission) and filter retrieval by it — e.g. only this client's docs, only the latest version, only what the user is allowed to see. Retrieval + filter = relevant *and* secure.

**Follow-ups**
- *"Why filter?"* — Precision and security — don't retrieve stale, irrelevant, or unauthorised content.
- *"Access control link?"* — Permission metadata enforces who can retrieve what ([RG21](#rg21--security-and-access-control)).

---

## RG15 · Query rewriting

**Simple explanation.** Users ask messy or short questions. **Query rewriting** uses the LLM to expand/clarify the query (add synonyms, resolve "it" from chat history) before retrieval, so I fetch better chunks.

**Follow-ups**
- *"Example?"* — "What about last year?" → rewritten with the topic and year from context so retrieval works.
- *"Cost?"* — One extra small call — usually pays off in retrieval quality.

---

## RG16 · Multi-hop questions

**Simple explanation.** A **multi-hop** question needs facts from several places ("compare A's fee to B's over two years"). Plain single-shot retrieval struggles; I use iterative/agentic retrieval ([RG24](#rg24--agentic-rag)) — retrieve, reason, retrieve again.

**Follow-ups**
- *"Why do they fail plain RAG?"* — One retrieval can't gather all the scattered pieces at once.
- *"Fix?"* — Break the question down and retrieve per part, or let an agent iterate.

---

## RG17 · Choosing chunk size

**Simple explanation.** No single right size — it depends on content. Prose does well with medium chunks; tables/code want structure-aware splits. I **test chunk sizes against my eval set** and pick what scores best, rather than guessing.

**Follow-ups**
- *"How do you decide?"* — Empirically — try a few sizes, measure retrieval/answer quality, choose the winner.
- *"Overlap value?"* — A small overlap prevents losing context at boundaries.

---

## RG18 · Keeping data fresh

**Simple explanation.** Data changes, so I run a **scheduled ingestion** that adds/updates/deletes chunks as sources change (incremental, not full re-index each time). Stale chunks are removed so the assistant never cites outdated facts.

**Follow-ups**
- *"Full vs incremental re-index?"* — Incremental — only changed docs, for cost and speed.
- *"How avoid stale answers?"* — Delete/replace old chunks and filter by date/version.

---

## RG19 · Evaluating RAG

**Simple explanation.** I measure two things: **retrieval quality** (did I fetch the right chunks? — recall/precision) and **answer quality** (**groundedness**: is it supported by sources? **relevance**: does it answer the question?). I use an eval set and score every change.

*"If answers are wrong, I first check retrieval — usually the fix is there, not in the prompt."*

**Follow-ups**
- *"Key RAG metrics?"* — Context recall/precision, groundedness/faithfulness, answer relevance.
- *"Tooling?"* — Eval frameworks (e.g. RAGAS) + LangSmith traces + human spot-checks.

---

## RG20 · Hallucination control

**Simple explanation.** RAG cuts hallucination by grounding, but doesn't erase it. I add: "answer only from context, else say you don't know", citations, an **evaluator** that checks the answer against sources, and human review for high-stakes.

**Follow-ups**
- *"Does RAG stop hallucination?"* — It greatly reduces it — combined with refuse-if-not-found and evaluation.
- *"What if the answer isn't in the data?"* — The model should say so — I instruct and evaluate for that.

---

## RG21 · Security and access control

**Simple explanation.** Users must only retrieve what they're allowed to. I store **permission metadata** on chunks and filter retrieval by the caller's identity, keep the index private, and redact PII. Retrieval respects the same access rules as the source systems.

*"In finance, 'the AI leaked a document to the wrong user' is a breach — access-filtered retrieval is non-negotiable."*

**Follow-ups**
- *"How enforce per-user access?"* — Tag chunks with permissions; filter retrieval by the user's entitlements.
- *"Other risks?"* — Prompt injection via retrieved content — treat retrieved text as data, never instructions.

---

## RG22 · Cost

**Simple explanation.** RAG cost = embeddings (indexing) + retrieval + the LLM call. I control it by retrieving only what's needed (tune k), caching, right-sizing the answer model, and re-embedding only changed docs.

**Follow-ups**
- *"Biggest cost?"* — Usually the generation call — keep context tight and cache repeats.
- *"Indexing cost?"* — One-off per doc; incremental updates keep it small.

---

## RG23 · Latency

**Simple explanation.** RAG adds a retrieval step before generation. I keep it fast with an efficient vector index, small top-k, optional re-rank only when needed, caching, and **streaming** the answer so the user sees it immediately.

**Follow-ups**
- *"Where's the time spent?"* — Mostly the LLM generation; retrieval is usually fast with a good index.
- *"Perceived speed?"* — Stream tokens — the answer starts appearing right away.

---

## RG24 · Agentic RAG

**Simple explanation.** **Agentic RAG** lets the model decide how to retrieve — rewrite the query, search multiple sources, judge sufficiency, and retrieve again — instead of one fixed pass ([file 39 AG23](39-concept-ai-agents-agentic.md#ag23--agentic-rag)). Better for hard, multi-hop questions.

**Follow-ups**
- *"When worth it?"* — Complex/ambiguous/multi-hop questions; overkill for simple lookups.
- *"Cost?"* — Higher (multiple retrievals/calls) — use selectively.

---

## RG25 · Graph RAG

**Simple explanation.** **Graph RAG** builds a knowledge graph (entities + relationships) from the data and retrieves connected facts, not just similar text. It's strong for questions about relationships and "how do these connect" across many documents.

**Follow-ups**
- *"Graph RAG vs vector RAG?"* — Vector finds similar passages; graph follows explicit relationships — better for connected reasoning.
- *"Cost/complexity?"* — Higher — building/maintaining the graph — I use it only when relationships are central.

---

## RG26 · RAG on Azure

**Simple explanation.** My Azure-native RAG: **Azure AI Search** for hybrid retrieval, **Azure OpenAI** for embeddings + generation, **Blob/ADLS** for source docs, **AI Foundry** to build/evaluate/secure, **Key Vault** + managed identity for secrets, **App Insights** for monitoring ([file 37](37-concept-azure-services.md)).

**Follow-ups**
- *"Why Azure AI Search?"* — Managed hybrid (vector+keyword) retrieval with security integration.
- *"Why Azure OpenAI over public?"* — Data privacy, networking, compliance — required in a regulated firm.

---

## RG27 · Common failure modes

**Simple explanation.** RAG fails by **bad retrieval** (wrong/no chunks), **poor chunking**, **stale data**, **too much context** (noise), **ignored citations**, and **injection via retrieved text**. Most "the AI is wrong" issues trace back to retrieval, not the model.

**Follow-ups**
- *"First thing you check on a bad answer?"* — The retrieved chunks in the trace — was the right context even fetched?
- *"Fixes?"* — Better chunking, hybrid search, re-ranking, filters, and refreshed data.

---

## RG28 · When not to use RAG

**Simple explanation.** Skip RAG when the model already knows enough (general knowledge), when you need **behaviour/style** not facts (fine-tune), or for pure reasoning/maths with no external facts. Don't add a retrieval layer you don't need.

**Follow-ups**
- *"Simplest alternative?"* — A plain prompt if no private/fresh data is needed.
- *"RAG for style?"* — No — that's fine-tuning; RAG is for knowledge.

---

## RG29 · Testing RAG

**Simple explanation.** I test the deterministic parts (chunking, embedding calls, filters, parsing) with unit tests, and end-to-end quality with an **eval set**: known questions, expected sources, and groundedness checks. Every prompt/model/index change re-runs the evals as a gate.

**Follow-ups**
- *"What's in the eval set?"* — Real questions, their correct source docs, and edge/adversarial cases.
- *"Regression?"* — Block release if groundedness or retrieval recall drops.

---

## RG30 · My RAG reference architecture

**How I answer (the whole picture).** *"My RAG reference architecture has four pillars: **retrieval** (hybrid search over well-chunked, metadata-tagged data in a vector store), **grounding** (answer only from retrieved context, with citations and access filtering), **orchestration** (query rewrite → retrieve → re-rank → assemble → generate → validate, built with LangChain/LangGraph), and **evaluation** (an eval set scoring groundedness, relevance and retrieval quality, wired into CI with LangSmith tracing). On Azure that's AI Search + Azure OpenAI + AI Foundry, secured with Key Vault and managed identity. I designed this at TCW and shipped the firm's first production RAG assistant on it."*

**Follow-ups**
- *"The four pillars again?"* — Retrieval, grounding, orchestration, evaluation.
- *"What made it production-grade?"* — Access-filtered retrieval, citations, evaluation gates, tracing, and human review for high-stakes — governance, not just a demo.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| RG1 | What is RAG | Retrieve facts, then generate from them |
| RG2 | Why RAG | Accurate, fresh, private, cited; no retraining |
| RG3 | RAG vs fine-tune | RAG for knowledge, fine-tune for behaviour |
| RG4 | Pipeline | Index offline; retrieve+generate online |
| RG5 | Ingestion | ETL: load, clean, chunk, embed, store + metadata |
| RG6 | Chunking | Structure-aware chunks with overlap |
| RG7 | Embeddings | Text → vectors capturing meaning |
| RG8 | Vector store | Fast nearest-neighbour retrieval engine |
| RG9 | Retrieval | Top-k similar chunks; tune k |
| RG10 | Hybrid search | Vector + keyword for best recall |
| RG11 | Re-ranking | Sharpen relevance before the LLM |
| RG12 | Prompt assembly | System rule + context + question |
| RG13 | Grounding/citations | Answer from sources; show them |
| RG14 | Metadata filters | Precision + security via metadata |
| RG15 | Query rewriting | Clarify the query before retrieval |
| RG16 | Multi-hop | Iterative retrieval for scattered facts |
| RG17 | Chunk size | Choose empirically via evals |
| RG18 | Freshness | Scheduled incremental re-indexing |
| RG19 | Evaluation | Score retrieval + groundedness/relevance |
| RG20 | Hallucination | Ground, refuse, cite, evaluate |
| RG21 | Security | Access-filtered retrieval; treat text as data |
| RG22 | Cost | Tune k, cache, right-size, incremental index |
| RG23 | Latency | Fast index, small k, stream the answer |
| RG24 | Agentic RAG | Model decides how to retrieve, iteratively |
| RG25 | Graph RAG | Retrieve via entity relationships |
| RG26 | On Azure | AI Search + Azure OpenAI + AI Foundry |
| RG27 | Failure modes | Usually retrieval, not the model |
| RG28 | When not to | No private/fresh data; behaviour needs fine-tune |
| RG29 | Testing | Unit-test parts; eval-gate the whole |
| RG30 | My architecture | Retrieval, grounding, orchestration, evaluation |

---

[← AI Agents](39-concept-ai-agents-agentic.md) · [Home](README.md) · [Next → LangChain](41-concept-langchain.md)
