# Visuals

← [Back to README](../README.md)

Same two-part shape as the AI-Skills tutorial's visuals page. Part 1 is real, working Mermaid diagrams — most Markdown viewers, including GitHub, render these directly. Part 2 has copy-paste prompts for illustrative art, if you want a more polished look for a wiki page or a presentation.

---

## Part 1 — Real diagrams

### Parallel vs. pipeline

The single most important picture in this tutorial — [Chapter 4](../tutorial/04-parallel-vs-pipeline.md)'s core distinction, made visual.

```mermaid
flowchart TD
    subgraph PAR ["Parallel — a barrier"]
        direction LR
        P1["Item A"] --> PB["Wait for\nALL items"]
        P2["Item B"] --> PB
        P3["Item C\n(slow)"] --> PB
        PB --> PN["Next stage starts\nonly once C finishes"]
    end

    subgraph PIPE ["Pipeline — no barrier"]
        direction LR
        A1["Item A\nstage 1"] --> A2["Item A\nstage 2"] --> A3["Item A\nstage 3"]
        B1["Item B\nstage 1"] --> B2["Item B\nstage 2"] --> B3["Item B\nstage 3"]
        C1["Item C (slow)\nstage 1"] --> C2["Item C\nstage 2"] --> C3["Item C\nstage 3"]
    end
```

In the pipeline, item A can finish all three of its own stages before slow item C even reaches stage 2 — nothing makes A wait for C. That's the entire reason pipeline is the default.

---

### Fan-out and verify

The pattern from [Chapter 5](../tutorial/05-fan-out-and-verify.md) — several angles, then independent verification before anything is trusted.

```mermaid
flowchart TD
    D["The diff"] --> S["Security angle"]
    D --> T["Test-coverage angle"]
    D --> ST["Style angle"]
    D --> DA["Data-access angle"]
    D --> DO["Docs angle"]

    S --> F["Raw findings"]
    T --> F
    ST --> F
    DA --> F
    DO --> F

    F --> V{"Fresh agent call per finding:\nfind a reason this is WRONG"}
    V -->|"Survives"| C["CONFIRMED —\nreaches the PR"]
    V -->|"Doesn't survive"| R["REJECTED —\ndiscarded"]
```

---

### The nested-multiplication risk

[Chapter 9](../tutorial/09-governance-and-capstone.md)'s near-miss — two individually-reasonable patterns, nested together.

```mermaid
flowchart TD
    PR["One PR,\n8 changed files"] --> PIPE["Pipeline through\neach file"]
    PIPE --> F1["File 1"]
    PIPE --> F2["File 2"]
    PIPE --> FD["... 8 files total"]
    F1 --> FO1["5-angle fan-out\n(each file)"]
    F2 --> FO2["5-angle fan-out\n(each file)"]
    FD --> FOD["5-angle fan-out\n(each file)"]
    FO1 --> TOTAL["Real total:\n8 x 5 = 40+ pieces of work"]
    FO2 --> TOTAL
    FOD --> TOTAL

    TOTAL --> CAP{"Explicit cap\nchecked?"}
    CAP -->|"Under cap"| RUN["Runs, cost\nis expected"]
    CAP -->|"Over cap"| FALLBACK["Falls back loudly,\nexplains what was\navoided and why"]

    style TOTAL fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    style FALLBACK fill:#122B22,stroke:#3DDC97,color:#E8EEF4
```

---

### The nine-chapter arc

```mermaid
flowchart TD
    C1["1. What Is a Workflow?"] --> C2["2. Anatomy of a Workflow"]
    C2 --> C3["3. Your First Workflow"]
    C3 --> C4["4. Parallel vs. Pipeline"]
    C4 --> C5["5. Fan-Out and Verify"]
    C5 --> C6["6. Workflows vs. Other Tools"]
    C6 --> C7["7. Testing and Iterating"]
    C7 --> C8["8. Packaging and Sharing"]
    C8 --> C9["9. Governance and Capstone"]
    C9 --> CS["Case studies:\nfrontend, backend, QA,\ncode review"]
    CS --> NEXT["Next: AI-Agents"]
```

---

### A workflow's own anatomy

The structural picture from [Chapter 2](../tutorial/02-anatomy-of-a-workflow.md).

```mermaid
flowchart LR
    subgraph WF ["A workflow script"]
        META["meta\n(name, version,\ndescription, phases —\ndocumentation, not a trigger)"]
        PHASE["phase() calls\n(group related agent()\ncalls in the progress view)"]
        ORCH["parallel() / pipeline()\n(the orchestration shape)"]
        AGENTCALL["agent() calls\n(the actual work,\none focused piece each)"]
    end

    RUN["A deliberate,\non-purpose run"] -->|"never automatic"| META
    META --> PHASE
    PHASE --> ORCH
    ORCH --> AGENTCALL
```

---

### The sharing ladder, workflow version

Same three levels as AI-Skills, with the workflow-specific gate on Level 3 from [Chapter 8](../tutorial/08-packaging-and-sharing.md).

```mermaid
flowchart LR
    L1["Level 1\nPersonal\n\nStill testing,\nstill changing"] --> L2["Level 2\nProject\n\nChecked into your repo.\nEveryone who clones it\ngets it automatically."]
    L2 --> L3["Level 3\nCompany-wide\n\nNeeds visible cost\ndocumentation, not just\nversioning."]

    style L1 fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    style L2 fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
    style L3 fill:#122B22,stroke:#3DDC97,color:#E8EEF4
```

Most workflows should stop at Level 2, same as skills — Level 3 asks for one extra thing a skill never needed: the real, written-down cost.

---

## Part 2 — Image-generation prompts

Optional. Use these with any image-capable tool for a team wiki, a slide deck, or an onboarding page. None of this is required to use the tutorial.

### 1. Cover image

**Suggested filename:** `assets/cover.png`

**Brief:** A wide banner showing several small, focused threads of work converging into one combined result — visually distinct from the AI-Skills cover's single calm interaction. Think several small streams merging into one river, or several separate desks feeding into one shared report board.

**Style:** Flat, modern illustration, same palette family as the AI-Skills cover (muted blue, teal, warm-neutral) so the two repos read as one series. Wide aspect ratio (roughly 3:1).

---

### 2. The cast, at their workflows

**Suggested filename:** `assets/kestrel-team-workflows.png`

**Brief:** The same five illustrated portraits as AI-Skills (protagonist, Rahul, Divya, Vikram, Ananya), same consistent style, but each now shown coordinating multiple small work-items at once instead of a single task — Divya with three device-size mockups in front of her, Vikram with several endpoint cards mid-pipeline, Ananya with four labelled test-angle folders.

**Style:** Same flat illustration style as the AI-Skills cast image, for visual continuity across the two repos.

---

### 3. Barrier vs. no barrier, illustrated

**Suggested filename:** `assets/barrier-illustrated.png`

**Brief:** Split image. Left: three runners stopped at a single finish-line tape, all waiting for the slowest one before anyone can continue — a literal barrier. Right: three runners on separate tracks, each running straight through to their own finish line at their own pace. Makes Chapter 4's core idea visually literal without any text needed.

**Style:** Clean, simple, icon-like — closer to an infographic than a photo. One accent colour marking "the slow one" on the left side.

---

### 4. The near-miss, calm not alarming

**Suggested filename:** `assets/near-miss-workflow.png`

**Brief:** A small team looking at a dashboard showing an unexpectedly large number (something like "47 pieces of work"), with one person circling it with a marker — curious and diagnostic, not panicked. Should read as "caught and explained," matching the AI-Skills near-miss image's calm tone.

**Style:** Same flat illustration style as the rest of this series. Neutral palette, one accent colour on the circled number.

---

### 5. Skill inside workflow, illustrated

**Suggested filename:** `assets/skill-inside-workflow.png`

**Brief:** A small, single labelled block ("style review") nested inside a larger diagram of five parallel blocks feeding into one combined report — visually showing that one of the five is smaller and came from somewhere else, without needing any caption. This is the picture-version of Case Study 4's whole point.

**Style:** Simple, icon-driven, matches the fan-out-and-verify Mermaid diagram above in spirit.

---

← [Back to README](../README.md)
