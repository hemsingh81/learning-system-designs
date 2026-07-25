# Interview Preparation

← [Back to the map](../README.md) · [Tutorial](../tutorial/README.md) · [Case studies](../case-studies/README.md)

Every question is collapsed. **Read the question, answer it in your head, then expand to check.** Reading the answers straight through feels productive and teaches you very little.

---

## How each answer is written

Every answer has the same three parts, because that is how a good interview answer is actually structured:

| Part | What it is | Why |
|---|---|---|
| **The 30-second answer** | What you say first | Interviewers ask a question, not for a lecture. Lead with the short version |
| **If they dig deeper** | The detail, the trade-off, the failure mode | This is where senior candidates separate themselves |
| **Follow-up to expect** | The question that almost always comes next | Being ready for it is most of the advantage |

Then a 📖 link to the full explanation in the tutorial or a case study, so you can go from "I can answer this" to "I actually understand this".

---

## Difficulty labels

| Label | Means |
|---|---|
| `Junior` | You should know this to pass a screening call |
| `Mid` | Standard for any backend role that touches distributed systems |
| `Senior` | You are expected to discuss trade-offs, not just definitions |
| `Staff+` | You are expected to challenge the question's premise when it deserves it |

---

## The sections

| # | Section | Questions | Covers |
|---|---|---|---|
| 1 | [Fundamentals](01-fundamentals.md) | 12 | What microservices are, when *not* to use them, distributed monoliths |
| 2 | [Communication](02-communication.md) | 20 | Sync vs async, commands vs events, queues vs topics, broker choice |
| 3 | [Boundaries and edges](03-boundaries-and-edges.md) | 16 | Bounded contexts, database-per-service, contracts, gateway, BFF |
| 4 | [Reliability](04-reliability.md) | 24 | Sagas, outbox, idempotency, timeouts, retries, circuit breakers |
| 5 | [Observability and operations](05-observability.md) | 12 | Correlation IDs, tracing, metrics, health checks |
| 6 | [System design scenarios](06-system-design-scenarios.md) | 8 | "Design me X" — full worked answers with a structure to follow |
| 7 | [Rapid fire](07-rapid-fire.md) | 45 | One-line answers for the quick-check round |

**137 questions total.**

---

## If you have limited time

**30 minutes before a call** → [Rapid fire](07-rapid-fire.md), then the six questions below.

**One evening** → Sections 1, 2, and 4. That is where most interviews actually live.

**A week** → All seven, plus build the e-commerce case study and do its [Now break it](../case-studies/01-ecommerce/README.md#now-break-it) exercises. Answers backed by "I ran this and watched it fail" are recognisably different.

---

## The six questions you are most likely to be asked

If you can answer only six, make them these:

1. [What is the difference between a command and an event?](02-communication.md#q3) — asked constantly, answered poorly
2. [How do you handle a message being delivered twice?](04-reliability.md#q9) — the real test of whether you have run async in production
3. [What is the dual-write problem?](04-reliability.md#q7) — separates people who have shipped this from people who have read about it
4. [Choreography or orchestration, and why?](04-reliability.md#q3) — a trade-off question, so never answer with one word
5. [Why is retrying without a circuit breaker dangerous?](04-reliability.md#q17) — tests whether you understand cascading failure
6. [When would you *not* use microservices?](01-fundamentals.md#q2) — the one where candidates over-sell and lose credibility

---

## Three things that make an answer sound senior

**1. Lead with the trade-off, not the definition.**

> ❌ "A saga is a sequence of local transactions with compensating actions."
> ✅ "A saga trades atomicity for availability. You give up rollback and buy the ability to keep working when one service is down — and you pay for it by writing compensation logic that has to be idempotent."

**2. Name the failure mode.**

Anyone can describe the happy path. Say what breaks: *"the risk here is a lost `PaymentFailed` event leaving stock reserved forever, so you need a sweeper with a TTL."*

**3. Say "it depends" — then immediately say on what.**

> ❌ "It depends."
> ✅ "It depends on one thing: does anyone need to replay these messages? If yes, Kafka. If no, a queue is less operational work."

---

## A note on honesty

If you have not run Kafka in production, do not imply you have. Say what you have done and what you have only read about. A candidate who says *"I have used RabbitMQ; I understand Kafka's model but have not operated a cluster"* is far more trustworthy than one who is fluent until the second follow-up.

The [Now break it](../case-studies/01-ecommerce/README.md#now-break-it) exercises exist so you can honestly say you have seen these failures happen.

---

← [Back to the map](../README.md) · Start with [Fundamentals →](01-fundamentals.md)
