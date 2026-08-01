# Release Readiness — v1.0, counterparty document ingestion

| | |
|---|---|
| **Produced by** | Atul, Project Manager · Gautam , Team Lead |
| **Using** | [P32 — Release Readiness Check](../../../AI-Prompts-Library/phase-7-release/P32-release-readiness-check.md) |
| **Date** | 2026-07-20 |
| **Status** | **AMBER — conditionally approved, gated on the parallel run** |
| **Version** | 1.0 |
| **Release** | v1.0 — `broker_alpha` and `broker_beta_em`, EM and EQ books |
| **Decision meeting** | 2026-07-20, 14:00 London. Present: Atul, Gautam, Hem, Preetinka, Ravi, Dzmitry, Pankaj, and Preeti Singh for Northwind |

---

## 1. The decision

**We are not cutting over on 2026-07-27 as planned.** We are deploying to production on 2026-07-27 and running it **in parallel with the manual process** for a minimum of two weeks and a maximum of four, with outputs compared every day. Cutover happens when the parallel run's exit criteria in §6 are met, and not on a date.

Nothing on this checklist is red. Four items are amber and every one of them is amber for the same reason: we have measured the system against fixtures and against six weeks of `dev` traffic, and we have not yet measured it against a month of real production volume with a human checking the answer.

The parallel run is not a formality and it is not a soft launch. It is the last control in the system that does not depend on the system being correct.

**Rating key.** 🟢 verified and evidenced · 🟠 works, but not yet proven at production volume or duration · 🔴 not ready, blocks release.

---

## 2. Functionality

| # | Item | Rating | Evidence |
|---|---|---|---|
| 2.1 | All eight stories NWD-101…108 accepted by Preetinka against their criteria | 🟢 | Acceptance log, 2026-07-16 |
| 2.2 | Five defects NWD-138…142 fixed and verified by Pankaj | 🟢 | Each bug report §9, all verified |
| 2.3 | Confidence gate matches [spec](spec-confidence-gate.md) v2.0, including completeness | 🟢 | `tests/test_confidence.py`, `tests/test_rules.py` — 214 tests, all green |
| 2.4 | Both counterparties end to end on real documents | 🟢 | 340 `broker_alpha`, 180 `broker_beta_em` processed in `dev` since 2026-06-30 |
| 2.5 | Exception queue usable by an analyst who did not build it | 🟢 | Preeti worked 60 exceptions unaccompanied, 2026-07-13. Two UI changes came out of it; both shipped |
| 2.6 | Reconciliation produces a break report that matches the manual one | 🟠 | Matches on 11 of 12 days tested. Day 12's divergence was a genuine manual error, which is encouraging and is still a divergence. Not enough days |
| 2.7 | **Straight-through rate ≥ 85% (PRD metric M2)** | 🟠 | **78%**. Started at 61%, rose to 84%, fell to 71% when Revision 2's completeness rules started rejecting incomplete documents that used to load, now recovering as `broker_alpha`'s multi-page handling settles. Trend is right; the number is not there yet |
| 2.8 | A new counterparty can be onboarded without a code change | 🟠 | True for the two we have. Untested on a third. The claim is architectural until somebody proves it |

**On 2.7.** The fall from 84% to 71% was correct. Those documents were loading incomplete. Atul told Northwind the number would fall **before** it fell, which is the only reason the conversation was five minutes rather than an hour. A metric that moves in the wrong direction for a good reason is survivable; a metric that moves in the wrong direction and surprises the client is not.

---

## 3. Data quality

| # | Item | Rating | Evidence |
|---|---|---|---|
| 3.1 | Every canonical column populated or explicitly nullable | 🟢 | [`data-contract-counterparty-position.md`](data-contract-counterparty-position.md); profiling run 2026-07-17 |
| 3.2 | `min_confidence` and `bronze_path` on every gold row | 🟢 | 100% over 12,400 rows |
| 3.3 | Idempotency by content hash in every code path | 🟢 | NWD-140 fixed; `content_hash` refuses non-bytes input |
| 3.4 | Completeness rules active on both sources | 🟢 | `line_item_count_field` configured on both; `page_continuation` runs on all |
| 3.5 | Row-count reconciliation in the data-quality suite | 🟢 | Pankaj's retro action item, shipped 2026-07-10 |
| 3.6 | Rejected documents produce one exception row, zero silver, zero gold | 🟢 | Asserted in tests and spot-checked over 90 rejections |
| 3.7 | Zero auto-accepted monetary errors on the labelled ground-truth set | 🟢 | 60-document set, zero, which is where the thresholds were set |
| 3.8 | **No silently-missing data anywhere in the pipeline** | 🟠 | Two mechanisms now detect it and both are tested. But NWD-142 was invisible for three weeks and we cannot prove there is not a third mechanism we have not thought of. This is the honest rating |

---

## 4. Security

| # | Item | Rating | Evidence |
|---|---|---|---|
| 4.1 | No API keys, connection strings or secrets in source, config, logs or test fixtures | 🟢 | Secret scan clean; [P24](../../../AI-Prompts-Library/phase-5-verify/P24-find-security-gaps.md) review 2026-07-08 |
| 4.2 | Managed identity via `DefaultAzureCredential` for every Azure call | 🟢 | Verified per client |
| 4.3 | Roles least-privilege: `Cognitive Services User`, `Storage Blob Data Contributor`, `Key Vault Secrets User` | 🟢 | Reviewed with Northwind IT, 2026-07-09 |
| 4.4 | Snowflake key-pair (JWT) auth; key in Key Vault, rotation documented | 🟢 | Rotation runbook §7 |
| 4.5 | PII redaction fails closed — service error persists a marker, never the raw text | 🟢 | Tested by forcing the Language endpoint to 500 |
| 4.6 | Raw and bronze containers immutable, with retention policy agreed | 🟢 | 7-year retention, Northwind compliance signed 2026-07-24 |
| 4.7 | Audit trail reconstructs any warehouse number from stored data alone | 🟢 | `content_hash` + `bronze_path` + `min_confidence` + applied threshold on every failure |
| 4.8 | Penetration test of the exception queue UI | 🟢 | Northwind's own team, 2026-07-31. Two low findings, both fixed |

---

## 5. Operations

| # | Item | Rating | Evidence |
|---|---|---|---|
| 5.1 | [`runbook-doc-ingestion.md`](runbook-doc-ingestion.md) complete, covering five failure modes with exact commands | 🟢 | Written by Ravi; **walked through by Dzmitry, who did not build the backend**, 2026-07-19. That is the test that matters |
| 5.2 | Alerts on every failure mode in the runbook, each linking to its entry | 🟢 | Eight alerts, Application Insights |
| 5.3 | Throttling handled with backoff and jitter; verified at month-end volume | 🟢 | NWD-141 fixed; 200 documents in 4 minutes, 0 failures |
| 5.4 | Dead-letter queue monitored and drainable | 🟢 | Alert on depth > 0; drain procedure runbook §6 |
| 5.5 | Rollback is one documented step, performed at least once | 🟢 | Slot swap, performed in `dev` 2026-07-17 |
| 5.6 | Straight-through rate on a dashboard Northwind can see | 🟢 | Live tile, per counterparty, per day |
| 5.7 | Cost tracked against the $420/month estimate | 🟢 | $402 in the last full month at 12,600 pages. Within tolerance |
| 5.8 | On-call rota and escalation path agreed with Northwind | 🟢 | Runbook §8 |
| 5.9 | **A human is accountable for the daily output** | 🟢 | Preeti, with Preetinka as escalation. Named, not implied |

---

## 6. The gate — the parallel run

**Both processes run. Every day. Outputs compared. Nobody switches anything off until the numbers agree.**

| | |
|---|---|
| **Duration** | Minimum **two weeks** of business days. Maximum four. Must include one month-end. |
| **Start** | 2026-07-27 |
| **What runs** | The pipeline in production, and Preeti's existing manual keying process, over the same documents |
| **Compared** | Every field of every row, daily, automated, results in a comparison report by 10:00 London |
| **Owner** | Pankaj runs the comparison. Preeti adjudicates every divergence. Atul reports weekly to Northwind |

### Exit criteria — all four, or the run continues

1. **Zero divergence on auto-accepted rows.** Not "low". Zero. A row the system was confident enough to load without a human must match the human's answer exactly, on every field, on every day of the run. One divergence resets the two-week clock.
2. **Every divergence on exception-queue rows explained**, with a named cause and either a fix or a recorded accepted limitation.
3. **Straight-through rate ≥ 85%**, sustained over the final five business days.
4. **One month-end processed** inside the window, at spike volume, with criteria 1 to 3 holding through it.

Cost of the run: roughly two hours of Preeti's day, for two to four weeks. That is the entire price.

### On the proposal to skip it

On 2026-07-20 it was proposed that the parallel run be shortened to three days, or dropped in favour of a "watch it closely for a week" arrangement. The argument was reasonable: 214 tests pass, five defects are fixed and verified, the manual process is the thing we are being paid to remove, and every day of parallel running is a day Preeti spends doing the job twice.

**Hem refused.**

> Every defect we found this sprint passed every control we had. NWD-142 loaded nine rows out of fourteen, marked itself `loaded`, reported a confidence of 0.9412, and produced a complete audit trail for data that was wrong. The tests passed. The gate passed. The logs were clean. We found it because a human counted the rows on the PDF.
>
> The parallel run is the only control we have that does not depend on the system being right. Three days is not long enough to hit a month-end, and month-end is the failure mode. Ask me what this looks like when it is wrong: it looks like Northwind trusting a break report for six weeks and then finding out it has been quietly wrong the whole time. We do not get that trust back.

**Preetinka refused, on different grounds.**

> I worked a reconciliation floor for nine years. What I know that the test suite does not is what a break report does to a team when it is wrong twice. They stop opening it. Then a real break sits in it for a week.
>
> Preeti is being asked to stop doing the check by hand and start trusting a system instead. That trust is the deliverable — not the pipeline. You earn it by showing her two weeks of the machine agreeing with her, including the days she was right and it was not. Two hours a day for two weeks is what that costs. It is the cheapest thing on this entire plan.

Recorded here rather than in the minutes because the reasoning matters more than the outcome, and because in six months somebody will propose skipping the parallel run for release v1.1. Atul and Gautam agreed. Northwind agreed the same afternoon.

---

## 7. Accepted risks

| # | Risk | Why we accept it | Mitigation |
|---|---|---|---|
| R1 | Third counterparty onboarding untested | No third counterparty exists yet | First onboarding runs with an engineer present, treated as a spike |
| R2 | A counterparty changes template silently | Cannot be prevented, only detected | Straight-through rate per counterparty on the dashboard; a drop is the signal. Runbook §5.1 |
| R3 | Straight-through rate below 85% at cutover | It is trending up and the shortfall costs analyst time, not correctness | Exit criterion 3 keeps the parallel run going until it clears |
| R4 | Azure AI cost rises with volume growth | Linear and small: ~$420/month at 12,600 pages | Monthly review; bronze means reprocessing is free |
| R5 | A completeness mechanism we have not thought of | The honest statement of §3.8 | The parallel run is the mitigation. This is the risk it exists for |

---

## 8. Sign-off

| Role | Name | Position | Date |
|---|---|---|---|
| Project Manager | Atul| Approved for parallel run. Cutover on criteria, not on a date. | 2026-07-20 |
| Team Lead | Gautam  | Approved. | 2026-07-20 |
| Architect | Hem Singh | Approved, conditional on §6 running in full. | 2026-07-20 |
| Product Owner | Preetinka Sharma | Approved, conditional on §6 running in full. | 2026-07-20 |
| QA | Pankaj  | Approved for production deployment. **Not** approved for cutover. | 2026-07-20 |
| Northwind | Preeti Singh, operations | Agreed, including the two hours a day. | 2026-07-20 |

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/release-readiness-v1.0.md`**
>
> Produced by: Project Manager (Atul) and Team Lead (Gautam ) using P32 — Release Readiness Check
> Signed by: all six roles plus the client, 2026-07-20
>
> Anyone consuming this file can rely on finding:
> - A red / amber / green rating for every item across functionality, data quality, security and operations, each with evidence
> - The release decision stated up front, including what is *not* being approved
> - The gate that must pass before cutover, with measurable exit criteria and a named owner
> - Accepted risks listed explicitly, each with why it is accepted and how it is mitigated
> - The record of a challenge to the gate, who refused it, and their reasoning
> - Named sign-off per role, with any condition attached to it
>
> This file does **not** contain: the deployment procedure, the operational runbook, or the test results themselves.
> Those live in: the pipeline release notes, `runbook-doc-ingestion.md` (P33), and the test suite.
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not release on it — send it back.
>
> Changing this file: Atuland Gautam  jointly. An amber cannot be raised to green without new evidence recorded in the row. The gate in §6 may only be waived by Hem Singh and Preetinka Sharma together, in writing, with reasons recorded here.
