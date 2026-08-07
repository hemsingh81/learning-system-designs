# 44 · Concept: Vector Databases & Chroma DB (30 questions)

[← LangSmith](43-concept-langsmith.md) · [Home](README.md) · [Next → Embeddings & Semantic Search](45-concept-embeddings-semantic-search.md)

This file explains **vector databases** — how AI apps store and search by meaning — with **Chroma** as the worked example, in simple English and real depth. I answer from Project B: I used a Chroma vector database in TCW's first production RAG assistant.

> Simple one-liner: *"A vector database stores embeddings and finds the nearest ones to a query fast. It's the retrieval engine of RAG — Chroma is the simple, developer-friendly one I start with, and I move to a managed store like Azure AI Search for scale."*

**Jump to:** [VD1 What is a vector DB](#vd1--what-is-a-vector-database) · [VD2 Why needed](#vd2--why-a-vector-db-and-not-sql) · [VD3 What it stores](#vd3--what-it-stores) · [VD4 Similarity](#vd4--similarity-metrics) · [VD5 ANN indexes](#vd5--ann-indexes) · [VD6 HNSW](#vd6--hnsw) · [VD7 Metadata filters](#vd7--metadata-filtering) · [VD8 Hybrid search](#vd8--hybrid-search) · [VD9 CRUD](#vd9--adding-updating-deleting) · [VD10 What is Chroma](#vd10--what-is-chroma)
> [VD11 Chroma model](#vd11--chromas-data-model) · [VD12 Add docs](#vd12--adding-documents-in-chroma) · [VD13 Query](#vd13--querying-in-chroma) · [VD14 Embeddings in Chroma](#vd14--embeddings-in-chroma) · [VD15 Persistence](#vd15--persistence-and-modes) · [VD16 Chroma + LangChain](#vd16--chroma-with-langchain) · [VD17 Scaling Chroma](#vd17--scaling-chroma) · [VD18 Chroma vs others](#vd18--chroma-vs-other-vector-dbs) · [VD19 Azure AI Search](#vd19--azure-ai-search) · [VD20 pgvector](#vd20--pgvector)
> [VD21 Choosing](#vd21--how-i-choose-a-vector-store) · [VD22 Sizing](#vd22--sizing-and-dimensions) · [VD23 Performance](#vd23--performance-tuning) · [VD24 Accuracy tradeoff](#vd24--recall-vs-speed) · [VD25 Reindexing](#vd25--reindexing-and-updates) · [VD26 Multitenancy](#vd26--multi-tenancy-and-security) · [VD27 Cost](#vd27--cost) · [VD28 Pitfalls](#vd28--common-pitfalls) · [VD29 Testing](#vd29--testing-retrieval) · [VD30 My approach](#vd30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of vector databases and Chroma in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. A vector DB searches by meaning, not by words.** A normal SQL database finds rows where a column *equals* something. A vector database stores **embeddings** — vectors that capture meaning — and finds the ones **closest** to my query vector. On Project B this is what let TCW's RAG assistant find the right passage even when the user's words didn't match the document's words.

**2. It stores the vector, the original text, and metadata together.** Each record is: the embedding (for searching), the source chunk (to feed the model), and metadata like document, date, or client (to filter). That trio is what makes retrieval both accurate and governable.

**3. Similarity is just distance in space.** "Closest" means a distance metric — usually cosine similarity. Two chunks about the same idea sit near each other; unrelated ones sit far apart. Searching is finding the nearest neighbours to the query point.

**4. Exact nearest-neighbour is too slow, so we approximate.** Comparing a query to millions of vectors one by one won't scale. **ANN** indexes like **HNSW** build a smart graph so search jumps close to the answer in a few hops. I trade a tiny bit of accuracy (recall) for a massive speed win — and I can tune that trade-off.

**5. Metadata filtering is what makes it safe and precise.** Pure similarity isn't enough in a real app. I filter first — only this client's documents, only current versions — then do the vector search. That's how I stop one user seeing another's data and how I keep answers on-scope.

**6. Hybrid search covers what pure vectors miss.** Semantic search is weak on exact tokens — a specific fund code, an error number, a name. Combining vector search with keyword (BM25) search gets both the meaning and the exact match, which is why I lean on hybrid for real corpora.

**7. Chroma is where I start; a managed store is where I scale.** Chroma is simple, local, developer-friendly — perfect for building and for the first version. When I need scale, security, and ops I don't want to run myself, I move to a managed store like **Azure AI Search** (or pgvector when I want it inside Postgres). Same concepts, different operational trade-offs.

**The full-stack / architect lens:** the later Q&As go into Chroma's data model, persistence modes, LangChain integration, sizing and dimensions, performance tuning, recall-vs-speed, reindexing, multi-tenancy, cost and testing retrieval. The through-line: the vector DB is the **retrieval engine of RAG**, and retrieval quality decides answer quality.

**One rule I never break:** *filter by metadata before I trust similarity — the closest vector is worthless if it belongs to data this user should never see.*

---

## VD1 · What is a vector database?

**Simple explanation.** A **vector database** stores **embeddings** (vectors representing meaning) and finds the ones **closest** to a query vector very fast. Instead of matching exact words, it matches by **meaning** — the core of semantic search and RAG.

**Architect's view:** It's a specialised store optimised for **nearest-neighbour search** at scale — the piece that makes "find the most relevant text" fast enough for production.

**Follow-ups**
- *"One-line?"* — A database that finds the most similar vectors to a query, fast.
- *"Where used?"* — RAG retrieval, semantic search, recommendations, deduplication.

---

## VD2 · Why a vector DB and not SQL?

**Simple explanation.** SQL matches exact values and keywords; it can't efficiently answer "find text with similar *meaning*". Vector DBs use **ANN indexes** to search millions of high-dimensional vectors in milliseconds — something a normal B-tree index can't do.

**Follow-ups**
- *"Can SQL do vectors at all?"* — Yes with extensions (pgvector) — fine at small/medium scale ([VD20](#vd20--pgvector)).
- *"Why specialised?"* — High-dimensional similarity search needs purpose-built indexes for speed.

---

## VD3 · What it stores

**Simple explanation.** Each record holds: the **vector** (embedding), the **original text/chunk**, an **id**, and **metadata** (source, date, permissions). The vector powers similarity search; the metadata powers filtering and citations.

**Follow-ups**
- *"Why keep the text too?"* — To return it as context and cite it — the vector alone isn't readable.
- *"Metadata role?"* — Filter (only this client/date) and secure retrieval ([VD7](#vd7--metadata-filtering)).

---

## VD4 · Similarity metrics

**Simple explanation.** How "close" two vectors are is measured by a metric: **cosine similarity** (angle — most common for text), **dot product**, or **Euclidean distance**. Cosine is my default for embeddings.

**Follow-ups**
- *"Which for text?"* — Cosine — it ignores magnitude and focuses on direction/meaning.
- *"Must match the model?"* — Use the metric the embedding model was trained for (often cosine).

---

## VD5 · ANN indexes

**Simple explanation.** **ANN** = Approximate Nearest Neighbour. Exact search over millions of vectors is too slow, so ANN indexes trade a tiny bit of accuracy for huge speed — returning *almost* the exact nearest neighbours in milliseconds.

**Follow-ups**
- *"Why approximate?"* — Exact is O(n) per query — too slow at scale; ANN is near-exact and fast.
- *"Common algorithms?"* — HNSW ([VD6](#vd6--hnsw)), IVF, PQ — HNSW is the popular default.

---

## VD6 · HNSW

**Simple explanation.** **HNSW** (Hierarchical Navigable Small World) is a graph-based ANN index. It builds layered "shortcut" graphs so a query hops quickly to its nearest neighbours. It's fast and accurate — what Chroma and many others use.

**Follow-ups**
- *"Why popular?"* — Excellent speed/recall balance for most workloads.
- *"Tunable?"* — Yes — parameters trade build time/memory against recall and query speed.

---

## VD7 · Metadata filtering

**Simple explanation.** I combine **vector search with metadata filters** — "nearest chunks *where source = client-A and date >= 2024*". This makes retrieval precise and enforces access control ([file 40 RG14](40-concept-rag.md#rg14--metadata-filtering)).

**Follow-ups**
- *"Pre- or post-filter?"* — Ideally filter during search for correctness and speed; post-filtering can drop results.
- *"Security use?"* — Filter by the user's permissions so they only retrieve allowed chunks.

---

## VD8 · Hybrid search

**Simple explanation.** **Hybrid search** blends vector (meaning) with keyword/BM25 (exact terms) and fuses the scores ([file 40 RG10](40-concept-rag.md#rg10--hybrid-search)). It catches both semantic matches and exact IDs/codes — usually the best quality.

**Follow-ups**
- *"Does Chroma do keyword too?"* — It's primarily vector; for full hybrid I use Azure AI Search or add a keyword layer.
- *"When keyword matters?"* — Exact codes, names, IDs a pure vector search can miss.

---

## VD9 · Adding, updating, deleting

**Simple explanation.** A vector DB supports **upsert** (add/update by id) and **delete** so the index stays fresh as source data changes ([file 40 RG18](40-concept-rag.md#rg18--keeping-data-fresh)). I update only changed chunks, not the whole store.

**Follow-ups**
- *"How keep it current?"* — Incremental upserts/deletes from the ingestion pipeline.
- *"Stale data risk?"* — Delete replaced chunks so old facts aren't retrieved.

---

## VD10 · What is Chroma?

**Simple explanation.** **Chroma** is an open-source, developer-friendly **vector database**. It's lightweight, runs in-process or as a server, handles embeddings for you, and integrates cleanly with LangChain — ideal for prototyping and small/medium RAG apps.

*"I chose Chroma for the first RAG app because it's simple and fast to build with — then the retriever abstraction lets me swap to a managed store for scale."*

**Follow-ups**
- *"Why start with Chroma?"* — Minimal setup, great DX, LangChain-native — quick to a working RAG.
- *"Production-ready?"* — For modest scale yes; for large enterprise scale I move to managed (AI Search).

---

## VD11 · Chroma's data model

**Simple explanation.** Chroma organises data into **collections** (like tables). Each item has an **id**, an **embedding**, the **document** (text), and **metadata**. You query a collection for nearest neighbours, optionally with a metadata filter.

**Follow-ups**
- *"What's a collection?"* — A named group of related vectors — e.g. one per corpus or tenant.
- *"Multiple collections?"* — Yes — useful for separation by domain or tenant.

---

## VD12 · Adding documents in Chroma

**Simple explanation.** I `add` documents with ids, text and metadata; Chroma can embed them for me or I pass my own vectors.

```python
collection.add(
    ids=["doc1"],
    documents=["Fee schedule text…"],
    metadatas=[{"source": "fees.pdf", "client": "A"}],
)
```

**Follow-ups**
- *"Who embeds?"* — Chroma's embedding function, or I supply embeddings from Azure OpenAI.
- *"Batch?"* — Yes — add many at once for efficient ingestion.

---

## VD13 · Querying in Chroma

**Simple explanation.** I `query` with the question text (or its vector); Chroma returns the top-k nearest documents with distances and metadata.

```python
collection.query(query_texts=["What are the fees?"], n_results=4,
                 where={"client": "A"})
```

**Follow-ups**
- *"n_results?"* — The top-k — tune it for relevance vs noise ([file 40 RG9](40-concept-rag.md#rg9--retrieval)).
- *"where clause?"* — Metadata filter applied to the search.

---

## VD14 · Embeddings in Chroma

**Simple explanation.** Chroma uses an **embedding function** to turn text into vectors. It defaults to a local model but I plug in **Azure OpenAI embeddings** so documents and queries use the same enterprise model ([file 45](45-concept-embeddings-semantic-search.md)).

**Follow-ups**
- *"Default embeddings okay?"* — Fine for demos; I use Azure OpenAI for quality and compliance.
- *"Same model both sides?"* — Yes — query and docs must share the embedding model.

---

## VD15 · Persistence and modes

**Simple explanation.** Chroma runs **in-memory** (ephemeral), **persistent** (saves to disk), or **client/server** (a running Chroma service). For anything beyond a script I use persistent or server mode so the index survives restarts.

**Follow-ups**
- *"Prod mode?"* — Server or persistent — never ephemeral.
- *"Where's data stored?"* — On disk (persistent) or in the server's backend.

---

## VD16 · Chroma with LangChain

**Simple explanation.** LangChain wraps Chroma as a **vector store + retriever**, so it drops straight into a RAG chain ([file 41 LC10](41-concept-langchain.md#lc10--vector-store-integrations)). I build the retriever from Chroma and pipe it into the chain.

```python
store = Chroma(collection_name="fees", embedding_function=emb)
retriever = store.as_retriever(search_kwargs={"k": 4})
```

**Follow-ups**
- *"Swap later?"* — Yes — replace with `AzureSearch` retriever; the chain is unchanged.
- *"Why this abstraction?"* — Store-agnostic RAG — change infra by config.

---

## VD17 · Scaling Chroma

**Simple explanation.** Chroma scales to millions of vectors on a good server, but it's not built for massive, highly-concurrent, globally-distributed workloads. When I outgrow it, I move to a managed store (Azure AI Search, Pinecone).

**Follow-ups**
- *"When move off Chroma?"* — Very large corpora, heavy concurrency, HA/geo needs.
- *"Migration pain?"* — Low — re-embed/re-index into the new store; the retriever interface hides it.

---

## VD18 · Chroma vs other vector DBs

**Simple explanation.** **Chroma** — simple, open-source, great DX, prototyping. **Pinecone/Weaviate/Qdrant/Milvus** — managed or heavy-duty at scale. **Azure AI Search/pgvector** — fit existing Azure/Postgres stacks. Pick by scale and ecosystem.

**Follow-ups**
- *"Chroma's niche?"* — Fast start and small/medium apps.
- *"Enterprise Azure choice?"* — Azure AI Search — managed, secure, hybrid search.

---

## VD19 · Azure AI Search

**Simple explanation.** **Azure AI Search** is the managed retrieval engine I use for enterprise RAG on Azure — **hybrid** (vector + keyword), security integration, scale and SLA ([file 37 Z27](37-concept-azure-services.md#z27--ai-search-for-rag)). It's my production destination after Chroma.

**Follow-ups**
- *"Why for prod?"* — Managed, secure, hybrid, scalable — fits the regulated Azure stack.
- *"Vs Chroma?"* — More features/scale/ops-managed; Chroma is lighter for prototyping.

---

## VD20 · pgvector

**Simple explanation.** **pgvector** adds vector search to **PostgreSQL**. Great when I already run Postgres and want vectors *and* relational data in one place at small/medium scale — no separate vector DB to operate.

**Follow-ups**
- *"When pgvector?"* — Existing Postgres, moderate scale, want one database.
- *"Limit?"* — At very large scale a dedicated vector DB usually outperforms it.

---

## VD21 · How I choose a vector store

**Simple explanation.** My decision path: **prototype/small → Chroma**; **already on Postgres → pgvector**; **enterprise on Azure → Azure AI Search**; **massive/managed scale → Pinecone/Milvus**. I choose by scale, ecosystem, security and ops appetite.

**Follow-ups**
- *"First question?"* — Scale and where the rest of my stack lives.
- *"Default in a regulated Azure firm?"* — Azure AI Search for production.

---

## VD22 · Sizing and dimensions

**Simple explanation.** Embeddings have a fixed **dimension** (e.g. 1536). Storage ≈ vectors × dimensions × 4 bytes, plus the index. More dimensions = more memory and slower search, so I pick an embedding model whose dimension fits my scale.

**Follow-ups**
- *"Fewer dimensions?"* — Cheaper/faster but can lose some quality — test the trade-off.
- *"Memory matters?"* — Yes — HNSW keeps the graph in memory; size the host accordingly.

---

## VD23 · Performance tuning

**Simple explanation.** I tune **index parameters** (HNSW build/search settings), **top-k**, **filters** (narrow the search space), and **batch** operations. I keep vectors in memory and put the store close to the app to cut latency.

**Follow-ups**
- *"Fastest win?"* — Smaller top-k and tight metadata filters.
- *"Index tuning?"* — Raise search-effort for recall, lower for speed — measure on evals.

---

## VD24 · Recall vs speed

**Simple explanation.** ANN trades **recall** (finding the true nearest neighbours) against **speed/memory**. Higher search effort = better recall, slower queries. I set this by evaluating retrieval quality against latency, not by guessing.

**Follow-ups**
- *"How decide?"* — Measure retrieval recall vs latency on my eval set; pick the knee of the curve.
- *"Symptom of low recall?"* — Relevant chunks missed → wrong answers → raise search effort.

---

## VD25 · Reindexing and updates

**Simple explanation.** As data changes I **upsert** changed chunks and **delete** removed ones. Occasionally I fully rebuild (new embedding model or big schema change). I automate this in the ingestion pipeline.

**Follow-ups**
- *"When full rebuild?"* — Switching embedding models (all vectors must be re-embedded) or major changes.
- *"Zero-downtime?"* — Build a new index and swap, so search stays available.

---

## VD26 · Multi-tenancy and security

**Simple explanation.** For multiple clients I isolate data — by **collection/index per tenant** or a strict **tenant metadata filter** on every query — and enforce **access control** so users only retrieve permitted chunks. In finance this is mandatory.

**Follow-ups**
- *"Separate index vs filter?"* — Separate for strong isolation; filter for many small tenants — with careful enforcement.
- *"Biggest risk?"* — A missing tenant filter leaking data — enforce it centrally, not per call.

---

## VD27 · Cost

**Simple explanation.** Costs: **embedding** generation (one-off per chunk), **storage** (vectors + index), and **compute/hosting** (managed service or your server). I control it with incremental updates, right-sized dimensions, and choosing self-hosted (Chroma) vs managed by scale.

**Follow-ups**
- *"Chroma cheaper?"* — Lower service cost (self-hosted) but I run/operate it; managed costs more but less ops.
- *"Embedding cost?"* — Mostly one-off; re-embed only changed docs.

---

## VD28 · Common pitfalls

**Simple explanation.** Watch for: **mismatched embedding models** (query vs docs), **poor chunking** (bad retrieval), **no metadata filters** (noise/leaks), **ephemeral mode in prod** (lost index), and **wrong similarity metric**. Most retrieval bugs are here, not in the DB.

**Follow-ups**
- *"Most common?"* — Different embedding models for indexing vs querying — results become meaningless.
- *"Prod mistake?"* — Ephemeral Chroma — index gone on restart; use persistent/server.

---

## VD29 · Testing retrieval

**Simple explanation.** I test retrieval with a **dataset of questions and their correct source chunks**, measuring **recall/precision** ([file 43 LS12](43-concept-langsmith.md#ls12--rag-evaluation)). If answers are wrong, I check retrieval first — usually that's the fix.

**Follow-ups**
- *"Key metric?"* — Context recall — did the right chunk get retrieved at all?
- *"Tooling?"* — LangSmith/RAGAS evals plus manual trace checks.

---

## VD30 · My approach

**How I answer (the whole picture).** *"I treat the vector store as the retrieval engine of RAG. I start with **Chroma** — simple, LangChain-native, quick to a working assistant — storing each chunk with its embedding and metadata (source, date, permissions), embedded with the same Azure OpenAI model for queries and documents. I tune top-k, use metadata filters for precision and access control, and keep the index fresh with incremental upserts/deletes. As scale and governance demand, I move to **Azure AI Search** for managed hybrid search, security and SLA — the retriever abstraction makes that a config change. Throughout, I measure retrieval quality with datasets and evals, because in RAG the answer is only as good as the chunks I fetch. That's exactly how I built TCW's first production RAG assistant."*

**Follow-ups**
- *"Chroma to AI Search — hard?"* — No — re-index and swap the retriever; the chain stays.
- *"Golden rule?"* — Same embedding model both sides, good chunks, filtered retrieval, measured recall.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| VD1 | Vector DB | Stores embeddings; finds nearest by meaning |
| VD2 | Why not SQL | ANN similarity search SQL can't do fast |
| VD3 | What it stores | Vector + text + id + metadata |
| VD4 | Similarity | Cosine default for text |
| VD5 | ANN indexes | Approximate = fast at scale |
| VD6 | HNSW | Graph index; great speed/recall |
| VD7 | Metadata filters | Precision + access control |
| VD8 | Hybrid search | Vector + keyword for best recall |
| VD9 | CRUD | Upsert/delete to stay fresh |
| VD10 | Chroma | Simple, open-source, LangChain-native |
| VD11 | Chroma model | Collections of id/embedding/doc/metadata |
| VD12 | Add docs | add() with ids, text, metadata |
| VD13 | Query | query() top-k with where filter |
| VD14 | Embeddings | Plug in Azure OpenAI; same both sides |
| VD15 | Persistence | Persistent/server in prod, not ephemeral |
| VD16 | With LangChain | as_retriever into a RAG chain |
| VD17 | Scaling | Good to millions; managed store beyond |
| VD18 | Chroma vs others | Prototyping vs managed/heavy-duty |
| VD19 | Azure AI Search | Managed hybrid retrieval for prod |
| VD20 | pgvector | Vectors inside Postgres |
| VD21 | Choosing | By scale, ecosystem, security, ops |
| VD22 | Sizing | Dimensions drive memory/speed |
| VD23 | Perf tuning | Index params, top-k, filters, batching |
| VD24 | Recall vs speed | ANN trade-off; set by evals |
| VD25 | Reindexing | Incremental upsert/delete; rebuild on model change |
| VD26 | Multi-tenancy | Isolate by index or enforced filter |
| VD27 | Cost | Embedding + storage + hosting |
| VD28 | Pitfalls | Model mismatch, chunking, no filters, ephemeral |
| VD29 | Testing | Measure context recall/precision |
| VD30 | My approach | Chroma → AI Search; measured, filtered retrieval |

---

[← LangSmith](43-concept-langsmith.md) · [Home](README.md) · [Next → Embeddings & Semantic Search](45-concept-embeddings-semantic-search.md)
