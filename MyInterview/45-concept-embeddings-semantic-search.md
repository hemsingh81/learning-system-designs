# 45 · Concept: Embeddings & Semantic Search (30 questions)

[← Vector Databases & Chroma](44-concept-vector-databases-chroma.md) · [Home](README.md) · [Next → LLM Application Integration](46-concept-llm-application-integration.md)

This file explains **embeddings** (turning meaning into numbers) and **semantic search** (finding by meaning, not keywords), in simple English and real depth. I answer from Project B, where embeddings power the retrieval behind TCW's first production RAG assistant.

> Simple one-liner: *"An embedding turns text into a vector that captures meaning, so similar meanings sit close together. Semantic search compares those vectors to find relevant text even when the words don't match."*

**Jump to:** [EM1 What is an embedding](#em1--what-is-an-embedding) · [EM2 Why they work](#em2--why-embeddings-work) · [EM3 Dimensions](#em3--dimensions) · [EM4 Semantic search](#em4--what-is-semantic-search) · [EM5 vs keyword](#em5--semantic-vs-keyword-search) · [EM6 Similarity](#em6--measuring-similarity) · [EM7 Models](#em7--embedding-models) · [EM8 Same model rule](#em8--the-same-model-rule) · [EM9 Generating](#em9--generating-embeddings) · [EM10 Normalisation](#em10--normalisation)
> [EM11 Chunking link](#em11--chunking-and-embeddings) · [EM12 In RAG](#em12--embeddings-in-rag) · [EM13 Hybrid](#em13--hybrid-search) · [EM14 Re-ranking](#em14--re-ranking) · [EM15 Multilingual](#em15--multilingual-embeddings) · [EM16 Multimodal](#em16--multimodal-embeddings) · [EM17 Domain fit](#em17--domain-specific-embeddings) · [EM18 Fine-tuning](#em18--fine-tuning-embeddings) · [EM19 Beyond search](#em19--other-uses) · [EM20 Caching](#em20--caching-embeddings)
> [EM21 Cost](#em21--cost) · [EM22 Latency](#em22--latency) · [EM23 Storage](#em23--storage) · [EM24 Quality eval](#em24--evaluating-embedding-quality) · [EM25 MTEB](#em25--choosing-a-model-mteb) · [EM26 Privacy](#em26--privacy-and-security) · [EM27 On Azure](#em27--embeddings-on-azure) · [EM28 Pitfalls](#em28--common-pitfalls) · [EM29 Versioning](#em29--model-versioning) · [EM30 My approach](#em30--my-approach) · [Section index](#section-index)

---

## EM1 · What is an embedding?

**Simple explanation.** An **embedding** is a list of numbers (a **vector**) that represents the **meaning** of text (or an image/audio). A model reads the text and outputs the vector, so "invoice" and "bill" land near each other in vector space.

**Architect's view:** Embeddings turn language into maths I can search and compare — the foundation of semantic search, RAG and recommendations.

**Follow-ups**
- *"One-line?"* — Text → a vector of numbers that captures meaning.
- *"Why numbers?"* — Computers compare numbers fast; similarity becomes a distance.

---

## EM2 · Why embeddings work

**Simple explanation.** Models learn embeddings from huge text so that **similar meanings get similar vectors**. Distance in vector space ≈ difference in meaning. That's why I can find relevant text even when it uses different words.

**Follow-ups**
- *"Capture synonyms?"* — Yes — "car" and "automobile" sit close, so search finds both.
- *"Understand context?"* — Modern embeddings are context-aware, so meaning shifts with the sentence.

---

## EM3 · Dimensions

**Simple explanation.** The vector's length is its **dimension** (e.g. 384, 768, 1536, 3072). More dimensions can capture more nuance but cost more memory and slower search. I pick a model whose dimension fits my scale and quality needs.

**Follow-ups**
- *"More dimensions always better?"* — No — diminishing returns, more cost/latency; test the trade-off.
- *"Reduce dimensions?"* — Some models allow shortening vectors to save space with small quality loss.

---

## EM4 · What is semantic search?

**Simple explanation.** **Semantic search** finds results by **meaning**: embed the query, embed the documents, and return the closest vectors. Unlike keyword search, it matches intent even when exact words differ.

**Follow-ups**
- *"One-line?"* — Search by meaning using embeddings, not exact word matching.
- *"Where used?"* — RAG retrieval, site search, FAQ matching, recommendations.

---

## EM5 · Semantic vs keyword search

**Simple explanation.** **Keyword** (BM25) matches exact terms — great for IDs, codes, names. **Semantic** matches meaning — great for natural questions and synonyms. Each misses what the other catches, so I often combine them (hybrid).

**Follow-ups**
- *"When keyword wins?"* — Exact codes/IDs a semantic search may blur.
- *"When semantic wins?"* — Natural-language questions and paraphrases.

---

## EM6 · Measuring similarity

**Simple explanation.** I compare vectors with **cosine similarity** (angle between them) most often for text; also dot product or Euclidean distance ([file 44 VD4](44-concept-vector-databases-chroma.md#vd4--similarity-metrics)). Smaller angle = more similar meaning.

**Follow-ups**
- *"Why cosine?"* — It focuses on direction (meaning), ignoring vector length.
- *"Match the model?"* — Use the metric the embedding model expects.

---

## EM7 · Embedding models

**Simple explanation.** Embeddings come from dedicated models — **Azure OpenAI text-embedding-3**, OpenAI, Cohere, and open models (e.g. `all-MiniLM`, `bge`, `e5`). In a regulated firm I use Azure OpenAI embeddings for privacy and compliance.

**Follow-ups**
- *"Open vs hosted?"* — Open (local) for control/cost; hosted for quality/ease — I use Azure OpenAI.
- *"Same as the chat model?"* — No — embedding models are separate, cheaper models.

---

## EM8 · The same-model rule

**Simple explanation.** I **must embed queries and documents with the same model**. Vectors from different models aren't comparable — mixing them makes similarity meaningless. This is the number-one embedding rule.

*"If I upgrade the embedding model, I re-embed everything — no mixing old and new vectors."*

**Follow-ups**
- *"Why?"* — Different models put meaning in different vector spaces — distances stop making sense.
- *"Model change?"* — Full re-index of all documents.

---

## EM9 · Generating embeddings

**Simple explanation.** I call the embedding model with text and get back a vector. I do this offline for all document chunks (indexing) and online for each query.

```python
vec = client.embeddings.create(model="text-embedding-3-large",
                               input="What are the fees?").data[0].embedding
```

**Follow-ups**
- *"Batch documents?"* — Yes — embed in batches for speed and cost.
- *"Query each time?"* — Yes, unless cached ([EM20](#em20--caching-embeddings)).

---

## EM10 · Normalisation

**Simple explanation.** Many pipelines **normalise** vectors to unit length so cosine similarity and dot product agree and comparisons are stable. Some models return normalised vectors already.

**Follow-ups**
- *"Why normalise?"* — Consistent similarity math; length no longer skews results.
- *"Always needed?"* — Depends on model/metric — follow the model's guidance.

---

## EM11 · Chunking and embeddings

**Simple explanation.** I embed **chunks**, not whole documents, so each vector represents a focused idea ([file 40 RG6](40-concept-rag.md#rg6--chunking)). Chunk quality drives embedding usefulness — a huge chunk gives a fuzzy, less-searchable vector.

**Follow-ups**
- *"Why not embed whole docs?"* — One vector can't represent many ideas — retrieval gets vague.
- *"Chunk size effect?"* — Too big blurs meaning; too small loses context — tune it.

---

## EM12 · Embeddings in RAG

**Simple explanation.** Embeddings are the **retrieval** step of RAG ([file 40](40-concept-rag.md)): embed chunks into a vector store, embed the question, fetch nearest chunks, feed them to the LLM. No embeddings, no semantic retrieval.

**Follow-ups**
- *"Which part of RAG?"* — The 'R' — finding the right context before generation.
- *"Quality link?"* — Better embeddings → better retrieval → better answers.

---

## EM13 · Hybrid search

**Simple explanation.** **Hybrid** combines semantic (embeddings) and keyword search and fuses scores ([file 40 RG10](40-concept-rag.md#rg10--hybrid-search)) — usually the best retrieval quality because it catches both meaning and exact terms.

**Follow-ups**
- *"Why hybrid over pure semantic?"* — Semantic can miss exact IDs/codes; keyword catches them.
- *"How fuse?"* — Score fusion (e.g. RRF) then optional re-ranking.

---

## EM14 · Re-ranking

**Simple explanation.** After a first-pass embedding search I can **re-rank** the top results with a stronger **cross-encoder** that reads query+chunk together and scores relevance more precisely ([file 40 RG11](40-concept-rag.md#rg11--re-ranking)). It sharpens the final context.

**Follow-ups**
- *"Bi- vs cross-encoder?"* — Bi-encoder (embeddings) is fast for search; cross-encoder is slower but more precise for re-ranking a shortlist.
- *"Always re-rank?"* — Only when precision matters — it adds cost/latency.

---

## EM15 · Multilingual embeddings

**Simple explanation.** **Multilingual** embedding models place the same meaning in different languages near each other, so a French query can retrieve an English document. Useful for global data (relevant to my international clients).

**Follow-ups**
- *"Cross-language retrieval?"* — Yes — query in one language, retrieve content in another.
- *"Trade-off?"* — Sometimes slightly lower per-language quality vs a dedicated model.

---

## EM16 · Multimodal embeddings

**Simple explanation.** **Multimodal** models embed text *and* images (and more) into the same space, so I can search images by text or find similar images. Useful when documents contain charts/scans.

**Follow-ups**
- *"Example?"* — "Find the diagram about fees" retrieves an image by its meaning.
- *"Same store?"* — Yes — shared vector space lets text and image vectors coexist.

---

## EM17 · Domain-specific embeddings

**Simple explanation.** General models can miss niche jargon (finance/legal terms). I check whether a **domain-tuned** model or hybrid search improves retrieval on my data — measured, not assumed.

**Follow-ups**
- *"When domain model?"* — When evals show general embeddings miss domain terms.
- *"Cheaper fix first?"* — Hybrid search often closes the gap without a new model.

---

## EM18 · Fine-tuning embeddings

**Simple explanation.** I can **fine-tune** an embedding model on my own query–document pairs so retrieval fits my domain better. It's advanced — I try chunking, hybrid and re-ranking first, and fine-tune only if evals justify it.

**Follow-ups**
- *"Worth it?"* — Sometimes for specialised domains with data — measure the lift.
- *"Cheaper alternatives?"* — Hybrid + re-ranking + better chunking usually first.

---

## EM19 · Other uses

**Simple explanation.** Beyond search, embeddings power **classification**, **clustering** (group similar items), **deduplication**, **recommendations**, and **anomaly/outlier detection**. Any "how similar are these?" task fits.

**Follow-ups**
- *"Classification with embeddings?"* — Embed text, then a small classifier on the vectors — cheap and effective.
- *"Clustering use?"* — Group tickets/documents by theme automatically.

---

## EM20 · Caching embeddings

**Simple explanation.** Embeddings are deterministic per model+text, so I **cache** them — never re-embed the same chunk, and cache frequent query embeddings. Saves cost and latency ([file 38 AS24](38-concept-ai-skills-workflow.md#as24--caching)).

**Follow-ups**
- *"Cache key?"* — Hash of text + model + version.
- *"Invalidate?"* — On embedding-model change (re-embed everything).

---

## EM21 · Cost

**Simple explanation.** Embedding cost is per token, cheap per call but adds up over large corpora. I control it by embedding only changed chunks, batching, caching, and choosing a right-sized model.

**Follow-ups**
- *"Big cost driver?"* — Initial indexing of a large corpus — one-off, then incremental.
- *"Cheaper model?"* — Smaller-dimension models cost/store less — verify quality on evals.

---

## EM22 · Latency

**Simple explanation.** Embedding a query adds a small call before retrieval. I keep it fast with a nearby/managed endpoint, caching frequent queries, and batching for bulk work.

**Follow-ups**
- *"Query latency concern?"* — Usually small vs generation; cache hot queries anyway.
- *"Bulk latency?"* — Batch and parallelise indexing jobs.

---

## EM23 · Storage

**Simple explanation.** Storage ≈ number of vectors × dimension × 4 bytes, plus the ANN index in memory ([file 44 VD22](44-concept-vector-databases-chroma.md#vd22--sizing-and-dimensions)). Millions of high-dim vectors need real memory — I size hosts accordingly.

**Follow-ups**
- *"Cut storage?"* — Smaller dimensions or quantisation, trading a little quality.
- *"Index in memory?"* — HNSW is memory-resident — plan RAM for it.

---

## EM24 · Evaluating embedding quality

**Simple explanation.** I judge embeddings by **retrieval quality on my data** — does the right chunk come back for known questions (recall/precision)? A model that tops leaderboards may still underperform on my domain, so I test on my own eval set.

**Follow-ups**
- *"Trust leaderboards?"* — As a starting shortlist — then validate on my data.
- *"Key metric?"* — Context recall for my real questions.

---

## EM25 · Choosing a model (MTEB)

**Simple explanation.** **MTEB** is a public benchmark ranking embedding models across tasks. I use it to shortlist, then pick by **quality on my data**, **dimension/cost**, **language**, and **privacy** (Azure OpenAI for regulated work).

**Follow-ups**
- *"First filter?"* — Privacy/hosting — in finance, that narrows it to Azure OpenAI fast.
- *"Then?"* — Quality-on-my-data vs cost/dimension.

---

## EM26 · Privacy and security

**Simple explanation.** Text I embed leaves my system if I use a public API, so in a regulated firm I use **Azure OpenAI** (data not used for training, private networking) and treat vectors + stored text as sensitive with access control.

**Follow-ups**
- *"Can you reverse an embedding to text?"* — Not exactly, but it can leak info — protect vectors like the source data.
- *"Regulated choice?"* — Azure OpenAI or a local model — no public API for sensitive data.

---

## EM27 · Embeddings on Azure

**Simple explanation.** On Azure I use **Azure OpenAI embeddings** (e.g. text-embedding-3) to index into **Azure AI Search** or Chroma, secured with **Key Vault** + managed identity ([file 37](37-concept-azure-services.md)). Same model for docs and queries, monitored via App Insights/LangSmith.

**Follow-ups**
- *"Why Azure OpenAI embeddings?"* — Privacy, compliance, and integration with the Azure stack.
- *"Store?"* — Azure AI Search for managed hybrid retrieval at scale.

---

## EM28 · Common pitfalls

**Simple explanation.** Pitfalls: **different models for query vs docs**, **forgetting to re-embed after a model change**, **huge chunks** (fuzzy vectors), **wrong similarity metric**, and **ignoring hybrid** for exact terms. Most retrieval bugs trace back here.

**Follow-ups**
- *"Number-one pitfall?"* — Query/document model mismatch — similarity becomes noise.
- *"Silent failure?"* — A stale index after a model upgrade — always re-embed.

---

## EM29 · Model versioning

**Simple explanation.** I **pin the embedding model + version** and record it with the index. Upgrading means a planned full re-embed and re-index — never a silent switch that corrupts similarity.

**Follow-ups**
- *"Why record the version?"* — So I know all vectors share one space and when to re-embed.
- *"Zero-downtime upgrade?"* — Build a new index with the new model, then swap.

---

## EM30 · My approach

**How I answer (the whole picture).** *"Embeddings are how I make meaning searchable. I chunk documents sensibly, embed them with an Azure OpenAI model, and store the vectors with text and metadata in a vector store — always using the same model for documents and queries. Retrieval is semantic, usually **hybrid** (adding keyword for exact IDs), with metadata filters for precision and access control, and re-ranking when precision matters. I choose models by quality on *my* data (shortlisting via MTEB), balancing dimension, cost, language and privacy, and I cache embeddings and pin the model version so an upgrade is a planned re-index, not a silent break. This retrieval layer — measured with recall on real questions — is what makes TCW's RAG assistant actually answer from the right facts."*

**Follow-ups**
- *"One rule to remember?"* — Same embedding model for queries and documents — always.
- *"Biggest quality lever?"* — Good chunking + hybrid search + measured retrieval, before fancier models.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| EM1 | Embedding | Text → vector capturing meaning |
| EM2 | Why they work | Similar meaning → similar vector |
| EM3 | Dimensions | Vector length; nuance vs cost |
| EM4 | Semantic search | Search by meaning, not words |
| EM5 | Semantic vs keyword | Meaning vs exact terms |
| EM6 | Similarity | Cosine default for text |
| EM7 | Models | Azure OpenAI/OpenAI/Cohere/open |
| EM8 | Same-model rule | Embed query & docs with one model |
| EM9 | Generating | Offline for docs, online for query |
| EM10 | Normalisation | Unit vectors for stable similarity |
| EM11 | Chunking | Embed focused chunks, not whole docs |
| EM12 | In RAG | Embeddings are the retrieval step |
| EM13 | Hybrid | Semantic + keyword for best recall |
| EM14 | Re-ranking | Cross-encoder sharpens shortlist |
| EM15 | Multilingual | Cross-language retrieval |
| EM16 | Multimodal | Text + image in one space |
| EM17 | Domain fit | Test if niche jargon needs tuning |
| EM18 | Fine-tuning | Advanced; measure the lift first |
| EM19 | Other uses | Classify, cluster, dedupe, recommend |
| EM20 | Caching | Cache deterministic embeddings |
| EM21 | Cost | Per token; incremental + batch + cache |
| EM22 | Latency | Small per query; cache hot ones |
| EM23 | Storage | Vectors × dims + in-memory index |
| EM24 | Quality eval | Recall on my own data |
| EM25 | MTEB | Shortlist, then test on my data |
| EM26 | Privacy | Azure OpenAI/local for sensitive data |
| EM27 | On Azure | Azure OpenAI + AI Search + Key Vault |
| EM28 | Pitfalls | Model mismatch, no re-embed, huge chunks |
| EM29 | Versioning | Pin model; upgrade = planned re-index |
| EM30 | My approach | Same model, hybrid, filtered, measured |

---

[← Vector Databases & Chroma](44-concept-vector-databases-chroma.md) · [Home](README.md) · [Next → LLM Application Integration](46-concept-llm-application-integration.md)
