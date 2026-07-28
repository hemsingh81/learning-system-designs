--- filename: templates/prompts-research.md ---

# Research Prompt Templates

← [Back to README](../README.md) · Related: [Chapter 2 — Foundations](../chapter-02-foundations.md)

10 prompts for researching new concepts: summarizing papers, comparing algorithms, generating reading lists, extracting key equations, and producing annotated bibliographies. Each includes the expected output structure and citation style.

---

## 1. Paper Summarizer (TL;DR + Contributions)

**Purpose:** Fast orientation on a new paper before deciding whether to read it in full.

**Prompt:**
```
Summarize the key ideas of [paper title, or paste the text/abstract].
Provide: 1) a 3-sentence TL;DR, 2) the 5 key contributions, 3)
limitations the authors themselves acknowledge (or that are evident from
the method), 4) 3 follow-up experiments you'd want to see, 5) 5
references from the paper with a one-sentence annotation each. Output
as Markdown.
```

**Expected output structure:**
```
## TL;DR
[3 sentences]

## Key Contributions
1-5. [bullets]

## Limitations
[bullets, distinguish author-acknowledged vs. inferred]

## Follow-up Experiments
1-3. [bullets]

## Annotated References
- [Citation] — [one-sentence annotation of relevance]
```

**Citation style:** Author (Year), Title — matches whatever the source paper uses; don't invent a citation format the paper doesn't have.

**Guardrail:** If working from a title only (no pasted text), the model is summarizing from training-data familiarity, not the actual paper — explicitly flag this distinction in the output and treat it as lower-confidence than a summary grounded in pasted text.

---

## 2. Algorithm Comparator

**Purpose:** Structured comparison of two or more algorithms/approaches for a specific problem.

**Prompt:**
```
Compare [algorithm A] and [algorithm B] for [specific use case/problem].
Produce a table with columns: Time complexity, Space complexity, Best
case, Worst case, When to prefer this approach. Add one paragraph on a
scenario where the "textbook better" choice is actually the wrong one
in practice, if applicable.
```

**Expected output structure:** A comparison table (as specified) followed by a short practical-tradeoffs paragraph.

**Citation style:** N/A — algorithmic comparisons are typically well-established and don't require citation, but flag if a claimed complexity bound is disputed or context-dependent.

**Guardrail:** Verify any Big-O claim against a primary source (textbook, original paper) before using it in a decision document — the model can state a commonly-cited bound that's actually average-case, not worst-case, without flagging the distinction unless asked.

---

## 3. Reading List Generator

**Purpose:** Builds a structured, leveled reading list for learning a new concept from scratch.

**Prompt:**
```
Generate a reading list for learning [topic] from [current level, e.g.,
"knows general backend engineering, new to this specific topic"].
Structure as: Foundational (2-3 items, prerequisites), Core (3-5 items,
the main concept), Advanced (2-3 items, edge cases/current research).
For each item: title, format (paper/blog/book/video), and one sentence
on why it's included at that level.
```

**Expected output structure:** Three leveled sections (Foundational/Core/Advanced), each item with title, format, and inclusion rationale.

**Citation style:** Title + author/publisher, informal (this is a reading list, not a bibliography) — full citation formatting isn't needed here.

**Guardrail:** Treat all suggested titles as candidates to verify exist and are accessible, not confirmed facts — ask the model to flag any item it's less confident actually exists as stated, especially for less mainstream topics.

---

## 4. Key Equation Extractor

**Purpose:** Pulls out and explains the core mathematical formulation from a technical source, in plain language.

**Prompt:**
```
From this text: [paste paper/documentation section], extract the key
equation(s). For each: state the equation, define every variable in
plain English, and explain in one sentence what it's actually computing
in intuitive terms (not just restating the math).
```

**Expected output structure:**
```
Equation: [as written, using standard notation]
Variables: [var] = [plain-English meaning], for each variable
Intuition: [one sentence, non-mathematical]
```

**Citation style:** Reference the section/page of the source text the equation came from, if available.

**Guardrail:** Grounding matters enormously here — this prompt should always be run with the actual source text pasted in, never from the model's memory of a paper's equations, since subscript/variable errors are exactly the kind of subtle mistake that's easy to introduce and hard to catch without the source in front of both you and the model.

---

## 5. Annotated Bibliography Builder

**Purpose:** Produces a formal annotated bibliography from a set of sources for a research doc or design doc.

**Prompt:**
```
Build an annotated bibliography from these sources: [paste list of
titles/URLs/citations]. For each: full citation in [APA/IEEE/Chicago —
specify], a 2-3 sentence annotation covering what it argues/finds, and
one sentence on its relevance to [your specific research question].
```

**Expected output structure:** A list of full citations (in the specified style) each followed by a 2-3 sentence annotation and a relevance sentence.

**Citation style:** Explicitly specified per use (APA is the default if unstated, since it's most common in technical/software contexts) — always state which style you want, since the model will otherwise pick one inconsistently across sources.

**Guardrail:** Verify page numbers and publication years independently for any citation going into a formal document — these are exactly the kind of small, plausible-looking detail that can be wrong without changing the overall fluency of the output.

---

## 6. Concept Explainer via Analogy

**Purpose:** Translates an unfamiliar concept into terms you already understand, using your existing expertise as the bridge.

**Prompt:**
```
Explain [new concept] to me using an analogy to [something I already
know well, e.g., "database transactions" or "TCP handshakes"]. Be
explicit about where the analogy holds and where it breaks down — don't
let me walk away with a mental model that's wrong in an important way.
```

**Expected output structure:** The analogy, followed by an explicit "where this breaks down" section.

**Citation style:** N/A.

**Guardrail:** The "where it breaks down" section is the actual safety mechanism of this prompt — always require it explicitly, since an analogy without stated limits is how confident-but-wrong mental models form.

---

## 7. Competing Claims Reconciler

**Purpose:** When two sources disagree, surfaces the disagreement instead of silently picking one.

**Prompt:**
```
Source A says: [paste claim/excerpt]. Source B says: [paste claim/
excerpt]. These appear to disagree on [topic]. Do they actually
contradict, or are they compatible under different assumptions (e.g.,
different scale, different constraints)? If they genuinely contradict,
state what evidence would resolve which is right for my use case:
[describe your use case].
```

**Expected output structure:** A verdict (genuine contradiction / compatible under different assumptions) plus the specific assumptions or resolving evidence needed.

**Citation style:** Reference both sources by name throughout, never blend them into one unattributed claim.

**Guardrail:** This is specifically for cases where you have two real, pasted sources — don't use this pattern to ask the model to adjudicate between two claims it's recalling from training data, since that reintroduces the exact grounding problem Chapter 2 covers.

---

## 8. Technology Evaluation Matrix

**Purpose:** Structured research output for a build-vs-buy or tool-selection decision.

**Prompt:**
```
Build an evaluation matrix comparing [option A], [option B], [option C]
for [use case]. Columns: Maturity/community size, Learning curve,
Operational cost, Fit for our specific constraint: [state your actual
constraint, e.g., "must run on Azure"]. Rate each Low/Medium/High per
cell with a one-clause justification, not just the rating alone.
```

**Expected output structure:** A matrix table with justified ratings per cell.

**Citation style:** N/A, but flag any rating based on the model's general knowledge vs. anything you provided as source material.

**Guardrail:** Treat "Maturity" and "community size" ratings as directional, not authoritative — these change fast and the model's training cutoff means this specific cell is the most likely to be stale; verify independently before it drives a real decision.

---

## 9. Research Question Sharpener

**Purpose:** Turns a vague research interest into a focused, answerable question — often the highest-leverage step before any research begins.

**Prompt:**
```
I'm curious about [vague topic/question]. Help me sharpen this into 3
specific, answerable research questions, each narrow enough to actually
investigate in [available time, e.g., "a few hours"]. For each, note
what kind of source would answer it (a benchmark, a paper, a
production case study, an experiment you'd run yourself).
```

**Expected output structure:** 3 sharpened questions, each tagged with the type of source that would answer it.

**Citation style:** N/A — this is a planning step before sourcing begins.

**Guardrail:** None specific — this is a low-risk, ideation-stage prompt; treat the output as a starting menu, not a commitment.

---

## 10. Post-Research Synthesis

**Purpose:** Consolidates research notes gathered from multiple sources into a single decision-ready summary.

**Prompt:**
```
Here are my research notes from [N] sources on [topic]: [paste notes,
ideally with source attribution per note]. Synthesize into: a one-
paragraph summary of consensus (if any), a list of open disagreements
between sources, and a recommendation for [your specific decision],
explicitly flagging where the recommendation rests on thinner evidence.
```

**Expected output structure:** Consensus summary, disagreements list, recommendation with confidence flagged per point.

**Citation style:** Preserve source attribution from your notes throughout — don't let the synthesis step anonymize which claim came from which source.

**Guardrail:** The "flag where the recommendation rests on thinner evidence" instruction is load-bearing — a synthesis that presents all conclusions with equal confidence is more dangerous than one that's honest about which parts are well-supported and which are extrapolation.

---

← [Back to README](../README.md) · Related: [`prompts-bug-fix.md`](./prompts-bug-fix.md), [`prompts-status-email.md`](./prompts-status-email.md)
