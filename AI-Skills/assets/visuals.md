# Visuals

← [Back to README](../README.md)

Two kinds of visual here. The diagrams in Part 1 are real — they're written in Mermaid, which most modern Markdown viewers (including GitHub) render directly, no image generator needed. Part 2 has copy-paste prompts for illustrative art, if you want a more polished, story-driven look for a wiki page or a presentation.

---

## Part 1 — Real diagrams

### How a skill gets picked

The company-directory idea from [Chapter 1](../tutorial/01-what-is-a-skill.md), as a flow.

```mermaid
flowchart TD
    A["You type a request"] --> B{"Does it match any\nskill's description?"}
    B -->|"No match"| C["Answered directly,\nno skill involved"]
    B -->|"Matches one skill"| D["That skill's full\ninstructions load in"]
    B -->|"Matches more than\none skill"| E["The most specific\nmatch wins"]
    D --> F["Instructions followed,\nresponse produced"]
    E --> F
```

---

### The decision framework from Chapter 6

```mermaid
flowchart TD
    Q1{"Must this happen every time,\nwith zero exceptions,\nno judgement call?"}
    Q1 -->|Yes| HOOK["Hook"]
    Q1 -->|No| Q2{"Does this need a separate\nworkspace — big or\nparallel work?"}
    Q2 -->|Yes| SUB["Subagent"]
    Q2 -->|No| Q3{"Will you always remember\nto type this yourself?"}
    Q3 -->|Yes| SLASH["Slash command"]
    Q3 -->|No| Q4{"Repeated, recognisable,\nphrased differently\nby different people?"}
    Q4 -->|Yes| SKILL["Skill"]
    Q4 -->|No| RETHINK["Rethink — this might\nnot need automating"]
```

---

### The sharing ladder from Chapter 8

```mermaid
flowchart LR
    L1["Level 1\nPersonal\n\nStill testing,\nstill changing"] --> L2["Level 2\nProject\n\nChecked into your repo.\nEveryone who clones it\ngets it automatically."]
    L2 --> L3["Level 3\nCompany-wide\n\nGenuinely useful across\nmany teams. Needs real\npackaging and versioning."]

    style L1 fill:#2E1F17,stroke:#FF7A45,color:#E8EEF4
    style L2 fill:#1B2A4A,stroke:#6C8EF5,color:#E8EEF4
    style L3 fill:#122B22,stroke:#3DDC97,color:#E8EEF4
```

Most skills should stop at Level 2. That's a complete, successful outcome — not a step on the way to something bigger.

---

### The nine-chapter arc

```mermaid
flowchart TD
    C1["1. What Is a Skill?"] --> C2["2. Anatomy of a Skill"]
    C2 --> C3["3. Your First Skill"]
    C3 --> C4["4. Trigger Descriptions"]
    C4 --> C5["5. Tools and Scripts"]
    C5 --> C6["6. Skills vs Other Tools"]
    C6 --> C7["7. Testing and Iterating"]
    C7 --> C8["8. Packaging and Sharing"]
    C8 --> C9["9. Governance and Capstone"]
    C9 --> CS["Case studies:\nfrontend, backend, QA,\ncode review"]
```

---

### A skill's own anatomy

```mermaid
flowchart LR
    subgraph SKILL ["A skill folder"]
        NAME["name\n(an identifier)"]
        DESC["description\n(decides IF it's used —\nthe most important part)"]
        INST["instructions\n(decides WHAT happens\nonce it's used)"]
        EXTRA["optional: scripts,\nreference data\n(Chapter 5)"]
    end

    REQUEST["Your request"] -.->|"matched against"| DESC
    DESC -->|"if matched"| INST
    INST -->|"may call"| EXTRA
```

---

## Part 2 — Image-generation prompts

Optional. Use these with any image-capable tool if you want illustrative art — for a team wiki, a slide deck, or an onboarding page. None of this is required to use the tutorial.

### 1. Cover image

**Suggested filename:** `assets/cover.png`

**Brief:** A wide banner showing a software engineer at a desk, split composition — left side shows scattered sticky notes and repeated typing (representing explaining the same thing over and over), right side shows a single calm interaction with an assistant that already "knows" the convention. Warm-to-cool colour transition left to right.

**Style:** Flat, modern illustration. Muted blue, teal, and warm-neutral palette. Wide aspect ratio (roughly 3:1), suitable for a repo banner.

---

### 2. The cast

**Suggested filename:** `assets/kestrel-team.png`

**Brief:** Five simple, friendly illustrated portraits in a row — the protagonist, Rahul (tech lead), Divya (frontend), Vikram (backend), Ananya (QA). Consistent art style across all five so they read as one team.

**Style:** Flat illustration, same style as the cover image. Each person doing something small and specific — Divya at a component preview, Vikram at a terminal, Ananya with a checklist.

---

### 3. The company directory analogy

**Suggested filename:** `assets/directory-analogy.png`

**Brief:** A literal illustrated company directory board, like you'd see in a lobby, but the name plates say things like "Commit Message Skill — writes commit messages, use when asked to commit changes" instead of real job titles. Makes Chapter 1's core analogy visually literal.

**Style:** Clean, slightly playful, like an infographic rather than a photo. Light background, one accent colour for the "matched" entry.

---

### 4. The near-miss (Chapter 9)

**Suggested filename:** `assets/near-miss-review.png`

**Brief:** A small group around a screen in a code review, one person pointing at a specific line with a concerned but calm expression — not alarmed, just careful. Should read as "caught in review, working as intended," not as a disaster.

**Style:** Same flat illustration style as the cast. Calm, neutral colour palette — this is a routine catch, not a crisis, and the art should say that.

---

### 5. The sharing ladder, illustrated

**Suggested filename:** `assets/sharing-ladder-illustrated.png`

**Brief:** A literal small ladder or staircase with three steps, labelled Personal, Project, Company-wide, with a small skill-folder icon climbing it — but stopping comfortably at step two, to visually reinforce that most skills shouldn't climb further than that.

**Style:** Simple, icon-driven, matches the Mermaid diagram above in spirit — this is the same content as a more polished illustration, not new content.

---

← [Back to README](../README.md)
