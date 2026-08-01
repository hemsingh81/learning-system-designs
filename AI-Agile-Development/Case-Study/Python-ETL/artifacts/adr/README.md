# Architecture Decision Records — Northwind counterparty ingestion

| | |
|---|---|
| **Produced by** | Hem Singh, Architect |
| **Using** | [P12 — Record an Architecture Decision](../../../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) |
| **Date** | 2026-06-15 |
| **Status** | Active |
| **Version** | 1.0 |

---

## What is recorded here

One file per decision that is **expensive to reverse**. Not every decision — most decisions are cheap to change and recording them is noise. The test I apply: *if we get this wrong, does fixing it in three months cost days or weeks?* Weeks goes in here.

An ADR is not a design document. It records one choice, the options that were genuinely considered, and what we accepted as a consequence. The consequences section is the one that matters and is the one people leave out. A decision with only good consequences was not a decision.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [0001](0001-extraction-approach.md) | Use Document Intelligence custom models, not an LLM, for extraction | Accepted | 2026-06-15 |
| [0002](0002-persist-bronze-before-parsing.md) | Persist the raw extraction response before parsing it | Accepted | 2026-06-16 |
| [0003](0003-one-failing-field-rejects-the-document.md) | One failing field rejects the whole document | Accepted, contested | 2026-06-17 |

## Conventions

- Numbers are sequential and never reused. A superseded ADR keeps its number and gains a status line pointing at the one that replaced it.
- Status is one of: **Proposed**, **Accepted**, **Accepted, contested**, **Superseded by NNNN**, **Deprecated**.
- **Accepted, contested** means the decision stands and a named person disagreed on the record. That is not a defect in the process; it is the process working. ADR-0003 is the live example.
- Never edit the Decision section of an accepted ADR. Write a new one that supersedes it.
- Every ADR names the date and the people in the room. In four months the question will not be "what did we decide" but "who decided, knowing what".

## Template

[`TEMPLATE.md`](TEMPLATE.md). Copy it. Do not improve it in place.

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/adr/README.md`**
>
> Produced by: Architect (Hem Singh) using P12 — Record an Architecture Decision
> Approved by: Gautam  (Team Lead) 2026-06-15
>
> Anyone consuming this file can rely on finding:
> - The test for what belongs in an ADR and what does not
> - A complete index of every ADR with its status and date
> - The status vocabulary, including what "Accepted, contested" means
> - The rule for superseding a decision rather than editing one
>
> This file does **not** contain: the decisions themselves, or any technical design.
> Those live in: the numbered ADR files in this folder, and `spec-confidence-gate.md` (P11).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: Hem Singh approves. Adding an ADR requires adding a row to the index in the same commit.
