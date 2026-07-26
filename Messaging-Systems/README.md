# Messaging Systems — Kafka vs Azure Service Bus vs RabbitMQ

Three brokers, one honest comparison. Written for engineers who have to pick one, run it, and be woken up by it.

Plain English throughout. Every technical term is explained the first time it appears. Every code example gives you the **algorithm in words first**, then the C# — because the algorithm is the part that transfers.

---

## Start here

**Two ways in.** If you want to learn this properly, follow the [learning path](#the-learning-path) below — it is sequenced, has exercises, and tells you when you have actually got it. If you have one specific question right now, use the [jump table](#jump-straight-to-what-you-need) instead.

---

## The learning path

Seven stages, roughly **12–14 hours** of reading plus hands-on. You do not have to do all of it — [the shortcuts](#shortcuts-if-you-have-less-time) at the end map common deadlines onto subsets.

> **The one rule that matters: do not start with the comparison.**
>
> The instinct is to open the side-by-side table and pick a winner. It does not work — you cannot meaningfully compare three things you do not yet understand, and the table will just confirm whatever you already believed. **Learn one broker properly first (Stage 2), then compare (Stage 4).** Everything after that lands differently.

### Stage 0 — Orientation

**Time: 20 min · Prerequisite: none**

| Do this | Where |
|---|---|
| Read the TL;DR and the five questions | [README, above](#tldr) |
| Read "what a broker actually does" and the vocabulary table | [Tutorial §1](docs/tutorial.md#1-what-a-broker-actually-does) |
| Read "why not just use a database table?" | [Tutorial §1](docs/tutorial.md#why-not-just-use-a-database-table) |

**✅ You can now:** explain what a broker is for, and — more usefully — say when you do *not* need one.

---

### Stage 1 — The three ideas everything rests on

**Time: 1 hour · Prerequisite: Stage 0**

These three concepts appear in every later section. If any is shaky, the rest will feel arbitrary rather than logical.

| Do this | Where |
|---|---|
| **Delivery semantics** — ack before or after the work | [Tutorial §2](docs/tutorial.md#2-delivery-semantics) |
| **Ordering** — why a key gives you sequence, and what it costs | [Tutorial §3](docs/tutorial.md#3-ordering-and-what-it-costs) |
| **Idempotency** — the pattern that makes at-least-once survivable | [Tutorial §19](docs/tutorial.md#19-idempotency--the-pattern-that-makes-everything-else-safe) |

> Yes, §19 is out of numerical order. Read it now anyway — everything in Stages 2 and 3 assumes it.

**🔍 Checkpoint.** Answer these out loud *before* opening the collapsed answers: [Q1–15](docs/interview-qa.md#beginner). Aim for 12 of 15. If "what does at-least-once mean" is not instant, re-read §2 — it is the single most load-bearing idea in this repo.

**✅ You can now:** explain why duplicates are normal rather than a bug, and why "exactly-once" is a trap question.

---

### Stage 2 — Learn ONE broker deeply

**Time: 3 hours · Prerequisite: Stage 1**

Pick one. Not three. Depth in one beats a shallow pass over all of them, and it makes Stage 4 possible.

| Pick | If |
|---|---|
| **RabbitMQ** | You want to learn fastest. One Docker command, a management UI you can click, immediate feedback. **The best choice for learning**, even if you end up using something else. |
| **Kafka** | Your job needs it, or streams and replay are your actual problem |
| **Azure Service Bus** | Your company is on Azure and this is what you will use |

Then read that broker's twelve sections — [Kafka §5–16](docs/tutorial.md#part-ii--apache-kafka), [Service Bus §5b–16b](docs/tutorial.md#part-iii--azure-service-bus), or [RabbitMQ §5c–16c](docs/tutorial.md#part-iv--rabbitmq) — and its two code files in [`code/csharp/`](code/csharp/). Read the plain-English algorithm at the top of each file before the code.

**🔬 Hands-on — this is the part that actually teaches you.** Reading about prefetch does not teach prefetch. Watching one consumer starve nineteen others does.

```bash
docker run -d --name rabbit -p 5672:5672 -p 15672:15672 rabbitmq:4-management
# management UI: http://localhost:15672  (guest/guest)
```

1. Publish a message by hand in the UI. Watch it sit in the queue.
2. Write a consumer that acks. Watch the queue drain.
3. **Kill the consumer mid-message.** Watch the message come back. *That is at-least-once, live.*
4. **Set prefetch to unlimited, start three consumers.** Watch one take everything while two idle. *That is [incident R2](docs/production-incidents.md#r2--unlimited-prefetch-starving-the-fleet).*
5. **`basicNack(requeue: true)` on a message that always fails.** Watch the CPU pin. Kill it quickly. *That is [incident R3](docs/production-incidents.md#r3--the-requeue-poison-loop).*

Steps 3–5 take twenty minutes and will teach you more than an hour of reading.

**🔍 Checkpoint.** [Q16–30](docs/interview-qa.md#intermediate) — the ones relevant to your broker. Aim for 10 of 15.

**✅ You can now:** build a correct producer and consumer on one broker, and explain its main failure mode.

---

### Stage 3 — The patterns that save you

**Time: 2 hours · Prerequisite: Stage 2**

Broker-independent. These are what separate code that works in dev from code that survives production.

| Do this | Where |
|---|---|
| Dead-letter handling and poison messages | [Tutorial §18](docs/tutorial.md#18-dead-letter-handling-and-poison-messages) |
| **The outbox pattern** — re-read §19, focusing on dual writes | [Tutorial §19](docs/tutorial.md#the-outbox-pattern--for-dual-writes) |
| Schema evolution | [Tutorial §20](docs/tutorial.md#20-schema-evolution-and-versioning) |
| Consumer group management | [Tutorial §21](docs/tutorial.md#21-consumer-group-management) |

**🔬 Hands-on.** Write the test that most teams never write:

> Deliver the same message twice. Assert the side effect happened **once**.

If that test does not exist, your idempotency does not work — nobody discovers a broken dedupe check by accident. Then write the outbox: one transaction, two rows, a publisher process that marks rows sent.

**✅ You can now:** design a consumer that survives duplicates, poison messages and a schema change.

---

### Stage 4 — Now compare

**Time: 90 min · Prerequisite: Stage 2 (this is why it was gated)**

| Do this | Where |
|---|---|
| The side-by-side table | [Tutorial §17](docs/tutorial.md#17-side-by-side-comparison) |
| **Choose by workload** — 18 workload types | [§17a](docs/tutorial.md#17a-choose-by-workload) |
| **One problem, three ways** — the same requirement on all three | [§17b](docs/tutorial.md#17b-one-problem-three-ways) |
| When two brokers is right | [§17c](docs/tutorial.md#17c-when-two-brokers-is-the-right-answer) |
| What actually decides it — team, scale, exit cost | [§17d](docs/tutorial.md#17d-the-constraints-that-decide-more-than-features-do) |
| Wrong reasons and anti-patterns | [§17e](docs/tutorial.md#17e-wrong-reasons-anti-patterns-and-knowing-when-you-were-wrong) |
| Dapr — abstracting over all three | [§17f](docs/tutorial.md#17f-dapr--not-choosing-for-now) → [`dapr.md`](docs/dapr.md) |

§17b will make far more sense than it would have three hours ago, because you now know one of the three columns from the inside.

**✅ You can now:** choose a broker for a given workload and defend it — including what you gave up.

---

### Stage 5 — Run it in production

**Time: 3 hours · Prerequisite: Stage 3**

The stage most tutorials skip, and the one that decides whether your system survives its first bad week.

| Do this | Where |
|---|---|
| Read all 30 incidents. Not skim — read. | [`production-incidents.md`](docs/production-incidents.md) |
| Set up the five alerts that matter | [`monitoring.md`](docs/monitoring.md#getting-started--the-minimum-viable-setup) |
| Walk your broker's runbook | [`runbooks/`](runbooks/) |
| Read the deployment manifests | [`k8s/`](k8s/) |

**🔬 Hands-on — break it on purpose.** Pick three incidents from your broker's section and reproduce them locally. Then follow the runbook to fix them. **An untested runbook is fiction**, and you would rather find that out now than at 3am.

**🔍 Checkpoint.** [Q31–41](docs/interview-qa.md#advanced). These are the ones that separate levels — especially [Q33](docs/interview-qa.md#33-a-consumer-group-is-stuck-walk-through-your-diagnosis) (diagnosis) and [Q40](docs/interview-qa.md#40-you-inherit-a-system-with-40-million-messages-in-one-rabbitmq-queue-what-do-you-do) (the inherited backlog).

**✅ You can now:** take on-call for a messaging system without lying about it.

---

### Stage 6 — Design a whole system

**Time: 2.5 hours · Prerequisite: Stages 4 and 5**

| Do this | Where |
|---|---|
| The case study, end to end | [`case-study-ecommerce.md`](docs/case-study-ecommerce.md) |
| Migration | [Tutorial §22](docs/tutorial.md#22-migration) |

**🔬 Hands-on.** Before reading the recommendation, **design it yourself.** Read the [requirements](docs/case-study-ecommerce.md#1-requirements), sketch an architecture, then compare against the three candidates and the trade-off scoring. Where you differ is where you learn something — and note that RabbitMQ is worked through in full and then *fails* two requirements, which is the most instructive part of the document.

**✅ You can now:** design a multi-region messaging backbone and defend the trade-offs.

---

### Stage 7 — Prove it

**Time: varies**

- Answer all [41 interview questions](docs/interview-qa.md) cold. Anything you fumble points at a section to revisit.
- Fill in the decision record from [§17e](docs/tutorial.md#17e-wrong-reasons-anti-patterns-and-knowing-when-you-were-wrong) for a system you actually work on. **If the "we gave up ___" line is empty, you are not finished.**
- Explain the outbox pattern to a colleague without notes. Teaching is the real test.

---

### Shortcuts if you have less time

| You have | Do | Get |
|---|---|---|
| **30 minutes** | Stage 0 + [§17a](docs/tutorial.md#17a-choose-by-workload) + [decision checklist](cheatsheet/decision-checklist.md) | A defensible choice, no depth |
| **2 hours** | Stages 0 and 1 + [§17a](docs/tutorial.md#17a-choose-by-workload), [§17b](docs/tutorial.md#17b-one-problem-three-ways) | The concepts, and a choice you understand |
| **1 day** | Stages 0–3 | Ship correct code on one broker |
| **3 days** | Stages 0–5 | Ship it and run it |
| **1 week** | All seven | Design and own the system |
| **Interview Monday** | Stage 1 → Stage 4 → [all 41 Q](docs/interview-qa.md) | Skip the hands-on; read [§17b](docs/tutorial.md#17b-one-problem-three-ways) twice |
| **On call tonight** | [Runbook](runbooks/) triage section + your broker's [10 incidents](docs/production-incidents.md) | Enough to not make it worse |

### If you get stuck

The hard concepts — delivery semantics, ordering, the outbox, PeekLock, exchanges, Dapr — are each written **problem first, then before/after, then the mechanism, then the cost**. If a section leaves you thinking *"I can see what it says, but not why"*, that is a defect in the writing rather than in your reading. Re-read the "first, what goes wrong without it" opening; that is where the reasoning lives.

---

## Jump straight to what you need

| You are | Read this | Time |
|---|---|---|
| **"I'm building X — what do I use?"** | [Choose by workload](docs/tutorial.md#17a-choose-by-workload) — 18 workload types, with the reasoning | 5 min |
| **Picking a broker this week** | [One-page summary](docs/summary-one-page.md) → [decision checklist](cheatsheet/decision-checklist.md) | 15 min |
| **Wanting to see the difference concretely** | [One problem, three ways](docs/tutorial.md#17b-one-problem-three-ways) — same requirement on all three | 10 min |
| **Justifying a choice to someone** | [What actually decides it](docs/tutorial.md#17d-the-constraints-that-decide-more-than-features-do) — team, scale, exit cost | 10 min |
| **Suspecting you chose wrong** | [Signals your decision expired](docs/tutorial.md#17e-wrong-reasons-anti-patterns-and-knowing-when-you-were-wrong) | 8 min |
| **Wanting to not choose yet** | [Dapr](docs/dapr.md) — one API over all three, and what it hides | 30 min |
| **New to messaging** | [Tutorial, Part I](docs/tutorial.md#part-i--foundations), then the one system you will use | 45 min |
| **Designing a real system** | [Case study](docs/case-study-ecommerce.md) — three architectures, scored | 35 min |
| **Interviewing (either side)** | [40 questions](docs/interview-qa.md) with collapsible answers, tagged by role | 60 min |
| **On call tonight** | [Runbooks](runbooks/) and [30 real incidents](docs/production-incidents.md) | as needed |
| **Building it** | [C# samples](code/csharp/) — algorithm first, then code | 30 min |
| **Setting up alerts** | [Monitoring](docs/monitoring.md) — queries, dashboards, thresholds with reasoning | 25 min |

---

## TL;DR

- **Kafka is a log you can rewind.** Nothing is deleted when read, so ten teams read the same event independently and you can replay last Tuesday. Costs you a team that knows Kafka.
- **Azure Service Bus is a managed queue with enterprise manners.** Sessions, scheduling, per-message TTL, dead-lettering and transactions are broker features you do not build. Costs you replay and raw throughput.
- **RabbitMQ is a smart router.** The exchange decides where copies go, so you rewire consumers without touching publishers. Costs you archival — a queue is a working set, not a store.
- **All three deliver at-least-once in practice.** Exactly-once exists only inside Kafka, Kafka-to-Kafka. Everything real is at-least-once plus an idempotency key. Build for duplicates or meet them in production.
- **Most large systems end up hybrid** — a firehose broker plus a command broker. Fine when it is a decision with a written boundary; a mess when it is an accident.

---

## Choosing, in five questions

![Choosing a broker](images/svg/broker-decision.svg)

1. **Several teams need the same message, at different times, with history?** Yes → 2. No → 4.
2. **Sustained peak above ~50k msg/sec?** Yes → **Kafka**. No, but replay matters → 3.
3. **All-in on Azure, want zero brokers to operate?** Yes → **Service Bus**. No → **Kafka**.
4. **Need per-message scheduling, TTL, priority, or routing that changes without a redeploy?** Yes → 3. No → 5.
5. **Small ops team a hard constraint?** Yes + Azure → **Service Bus**. Yes, not Azure → **RabbitMQ**. No → **RabbitMQ**.

**Question zero:** do you need a broker at all? A synchronous call, a database table polled by a worker, or a scheduled batch job beats a broker you have to operate.

**Tie-breaker:** pick the one your team can debug at 3am. Operational familiarity beats a 15% benchmark win every time.

---

## How the folders are organised

```
Messaging-Systems/
├── README.md                    ← you are here (the map)
│
├── docs/                        ← the reading material
│   ├── tutorial.md              ← THE MAIN DOCUMENT — 25 sections, all three brokers
│   ├── case-study-ecommerce.md  ← global e-commerce backbone, three architectures scored
│   ├── interview-qa.md          ← 40 questions, collapsible answers, role-tagged
│   ├── production-incidents.md  ← 30 real incidents, 10 per broker
│   ├── monitoring.md            ← Prometheus, Grafana, alert rules with reasoning
│   └── summary-one-page.md      ← paste into a design doc or slide
│
├── images/                      ← EVERY image lives here, nowhere else
│   ├── svg/                     ← 4 hand-authored, dark, annotated
│   └── png/                     ← 1600×900 exports (gitignored, regenerate)
│
├── diagrams/                    ← Mermaid sources, .mmd, GitHub renders them inline
│
├── code/csharp/                 ← 6 files: producer + consumer per broker
│                                  every file opens with the algorithm in plain English
│
├── k8s/                         ← Strimzi CRs, Bitnami values, Azure Service Operator
│
├── runbooks/                    ← one per broker: triage, incidents, routine procedures
│
├── cheatsheet/                  ← print these two
│   ├── cheat-sheet.md
│   └── decision-checklist.md
│
└── scripts/render-diagrams.sh   ← .mmd → SVG + PNG
```

This mirrors the layout of [`../MicroServices/`](../MicroServices/), so the two folders read as one body of work.

---

## Generated assets

Every file, with a direct link.

### Documents

| File | Contents |
|---|---|
| [`docs/tutorial.md`](docs/tutorial.md) | **The main document.** Foundations, then all three brokers across 12 headings each, then comparison, idempotency, outbox, schema evolution, consumer groups, migration, references |
| [`docs/dapr.md`](docs/dapr.md) | **Dapr** — the sidecar abstraction over all three: components per broker, CloudEvents, resiliency, the transactional outbox, what each broker loses, vs MassTransit/NServiceBus |
| [`docs/case-study-ecommerce.md`](docs/case-study-ecommerce.md) | Requirements, three candidate architectures, trade-off scoring, implementation plan, SLOs, incident runbook, cost model, migration plan |
| [`docs/interview-qa.md`](docs/interview-qa.md) | 40 questions — 15 beginner, 15 intermediate, 10 advanced |
| [`docs/production-incidents.md`](docs/production-incidents.md) | 30 incidents with symptoms, root cause, detection, mitigation, long-term fix |
| [`docs/monitoring.md`](docs/monitoring.md) | PromQL, KQL, Grafana panels, alert rules |
| [`docs/summary-one-page.md`](docs/summary-one-page.md) | Export-friendly one-pager |

### Diagrams

| Mermaid source | Rendered image | Shows |
|---|---|---|
| [`diagrams/kafka-architecture.mmd`](diagrams/kafka-architecture.mmd) | [`images/svg/kafka-architecture.svg`](images/svg/kafka-architecture.svg) *(hand-authored)* | Brokers, partitions, leaders/followers, consumer groups, tiered storage |
| [`diagrams/azure-service-bus-architecture.mmd`](diagrams/azure-service-bus-architecture.mmd) | [`images/svg/azure-service-bus-architecture.svg`](images/svg/azure-service-bus-architecture.svg) *(hand-authored)* | Topic, filtered subscriptions, sessions, DLQ, Geo-DR |
| [`diagrams/rabbitmq-architecture.mmd`](diagrams/rabbitmq-architecture.mmd) | [`images/svg/rabbitmq-architecture.svg`](images/svg/rabbitmq-architecture.svg) *(hand-authored)* | Exchange types, bindings, quorum queues, DLX, the TTL retry trick |
| [`diagrams/broker-decision.mmd`](diagrams/broker-decision.mmd) | [`images/svg/broker-decision.svg`](images/svg/broker-decision.svg) *(hand-authored)* | The five questions |
| [`diagrams/delivery-semantics.mmd`](diagrams/delivery-semantics.mmd) | renders inline in [`tutorial.md`](docs/tutorial.md#2-delivery-semantics) | At-most-once vs at-least-once vs effectively-once |
| [`diagrams/case-study-kafka.mmd`](diagrams/case-study-kafka.mmd) | renders inline in [`case-study-ecommerce.md`](docs/case-study-ecommerce.md) | Architecture A |
| [`diagrams/case-study-azure.mmd`](diagrams/case-study-azure.mmd) | renders inline | Architecture B |
| [`diagrams/case-study-rabbitmq.mmd`](diagrams/case-study-rabbitmq.mmd) | renders inline | Architecture C |
| [`diagrams/migration-strangler.mmd`](diagrams/migration-strangler.mmd) | renders inline | Four-phase migration |
| [`diagrams/dapr-architecture.mmd`](diagrams/dapr-architecture.mmd) | renders inline in [`dapr.md`](docs/dapr.md) | Sidecar, component config, and what the abstraction hides |

The four hand-authored SVGs are dense and annotated; the Mermaid companions carry the same structure in a form GitHub renders inline and diffs cleanly. Both are checked in — see [`images/README.md`](images/README.md) for the colour semantics and how to regenerate.

### Code

| File | Teaches |
|---|---|
| [`code/csharp/kafka-producer.cs`](code/csharp/kafka-producer.cs) | Idempotent producer, `acks=all`, keys and partitioning, transactional read-process-write |
| [`code/csharp/kafka-consumer.cs`](code/csharp/kafka-consumer.cs) | Manual commits, cooperative rebalancing, bounded retry, hand-built DLQ |
| [`code/csharp/azure-producer.cs`](code/csharp/azure-producer.cs) | Sessions, batching, scheduled messages, topology as code |
| [`code/csharp/azure-consumer.cs`](code/csharp/azure-consumer.cs) | Lock renewal, all four settlement outcomes, session sagas, DLQ drain |
| [`code/csharp/rabbitmq-producer.cs`](code/csharp/rabbitmq-producer.cs) | Publisher confirms, `mandatory` + returns, quorum queues, **the outbox pattern** |
| [`code/csharp/rabbitmq-consumer.cs`](code/csharp/rabbitmq-consumer.cs) | Prefetch, manual ack, the TTL retry queue, `x-death` triage |
| [`code/csharp/dapr-publisher.cs`](code/csharp/dapr-publisher.cs) | Broker-agnostic publish, partition keys, bulk publish, raw payload, the Dapr outbox |
| [`code/csharp/dapr-subscriber.cs`](code/csharp/dapr-subscriber.cs) | SUCCESS/RETRY/DROP semantics, CloudEvents, dead letter topics |
| [`code/csharp/README.md`](code/csharp/README.md) | How to run them, package versions, local brokers |

### Infrastructure and operations

| File | Contents |
|---|---|
| [`k8s/kafka-helm-values.yaml`](k8s/kafka-helm-values.yaml) | Strimzi node pools, topics as code, ACLs, MirrorMaker 2, PDB |
| [`k8s/rabbitmq-helm-values.yaml`](k8s/rabbitmq-helm-values.yaml) | Bitnami values: quorum queues, watermarks, probes, alert rules |
| [`k8s/azure-service-bus-operator.md`](k8s/azure-service-bus-operator.md) | ASO custom resources, workload identity, KEDA, Private Link, Geo-DR |
| [`k8s/dapr-components.yaml`](k8s/dapr-components.yaml) | The same app on all three brokers: components, subscriptions, resiliency, outbox, sidecar annotations |
| [`runbooks/kafka-runbook.md`](runbooks/kafka-runbook.md) | 7 incidents + routine procedures + escalation |
| [`runbooks/rabbitmq-runbook.md`](runbooks/rabbitmq-runbook.md) | 7 incidents + routine procedures + escalation |
| [`runbooks/azure-runbook.md`](runbooks/azure-runbook.md) | 7 incidents + **what you cannot do**, which matters more here |
| [`cheatsheet/cheat-sheet.md`](cheatsheet/cheat-sheet.md) | Vocabulary, settings, metrics, CLI, sizing rules |
| [`cheatsheet/decision-checklist.md`](cheatsheet/decision-checklist.md) | Questions to answer before coding, red flags, sign-off table |
| [`scripts/render-diagrams.sh`](scripts/render-diagrams.sh) | `.mmd` → SVG + PNG; `--check` mode for CI |

---

## The five things that are true of all three

1. **At-least-once is the contract.** Build idempotent consumers, or meet duplicates in production.
2. **Dual writes do not work.** Saving to a database and publishing a message are two operations that can half-fail. Use the outbox pattern.
3. **The DLQ needs an owner and an alert at depth > 0**, or it is a place messages go to die quietly.
4. **Ordering costs parallelism.** Always. Decide the smallest unit that actually needs it.
5. **Pick the one your team can debug at 3am.** Operational familiarity beats a 15% benchmark win.

---

## Regenerating the diagrams

```bash
./scripts/render-diagrams.sh            # everything
./scripts/render-diagrams.sh case-study # only files matching "case-study"
./scripts/render-diagrams.sh --check    # CI gate: fail if a .mmd has no image
```

Requires Node 18+. The four hand-authored SVGs are skipped so they are never machine-overwritten. PNG export of those needs `pip install cairosvg` — optional, since the SVGs render fine on GitHub.

---

## Assumptions and freshness

Product behaviour, quotas and prices were checked in **July 2026**, against Kafka 3.9 (KRaft), RabbitMQ 4.x (quorum queues), and Azure Service Bus Premium. Vendor limits move. Verify against the live docs before putting money or an SLA behind any number here — the [full assumptions list](docs/tutorial.md#assumptions) is at the top of the tutorial.

Licensed MIT. See [`LICENSE`](LICENSE) for what is original and what summarises vendor documentation.
