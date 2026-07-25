# Case Study 2 — Banking and Payments

← [E-commerce](../01-ecommerce/) · [All case studies](../README.md) · Next: [Stock market data](../03-stock-market-data/)

---

## The business

A digital bank. Customers hold accounts, move money between them, pay other banks, and receive salary. Every movement must be recorded, auditable, and reversible only by an explicit correcting entry.

Volume is modest by internet standards — a few hundred transfers a second at peak. **Volume is not the problem here.**

---

## The constraint

> **Money must never move twice, and must never disappear. Every rupee must be accounted for, forever.**

Read that against [case study 1's](../01-ecommerce/) constraint — "checkout must stay up" — and you have the whole difference between the two systems.

| Question | E-commerce | Banking |
|---|---|---|
| Dependency is down. Proceed anyway? | **Yes.** Keep selling, reconcile later | **No.** Stop. Never guess with money |
| Duplicate message? | Recoverable — refund and apologise | **Unacceptable.** A double debit is a regulatory event |
| Eventual consistency? | Fine, show "Processing" | Fine *between* services. **Never inside the ledger** |
| Availability vs correctness? | Availability | **Correctness, every time** |

A bank that is briefly unavailable annoys people. A bank that loses money loses its licence.

---

## The services

| Service | Owns | Notes |
|---|---|---|
| **Accounts** | Account records, ownership, status, limits | Does **not** own balances |
| **Ledger** | Every journal entry, every balance | **The single source of financial truth** |
| **Transfers** | Transfer requests and their lifecycle | Orchestrates; never touches balances directly |
| **Payments** | Outbound payments to other banks (NEFT/RTGS/UPI) | Talks to the network |
| **Fraud** | Risk scoring, rules, holds | Can block a transfer |
| **Notifications** | SMS, email, push | |
| **Reporting** | Statements, regulatory reports | Read-only projections |

### The rule that defines this system

> **Only the Ledger writes balances. Nothing else. Ever.**

Not Transfers. Not Payments. Not an admin tool. Not a support script. A second writer to the ledger is not a design smell here — it is an incident waiting to be discovered by an auditor.

---

## Why double-entry, not a balance column

The naive design:

```sql
UPDATE accounts SET balance = balance - 500 WHERE id = 'A';
UPDATE accounts SET balance = balance + 500 WHERE id = 'B';
```

This is wrong for a bank, for four reasons:

1. **No history.** You know the balance is ₹4,500. You cannot prove how it got there.
2. **No audit trail.** A regulator asks "explain this ₹500". You cannot.
3. **Nothing detects corruption.** If a bug adds ₹500 without removing it, nothing notices. Money is created from nothing.
4. **Cannot be replayed.** You cannot rebuild the balance after a bug, because the history was overwritten.

The double-entry design instead records **immutable journal entries**, always in balanced pairs:

```
Journal J-1001                          debit      credit
  Account A (customer)                  500.00
  Account B (customer)                             500.00
                                        ───────   ───────
                                        500.00     500.00   ← must always be equal
```

The balance is now a **derived** value: the sum of all entries for an account. It is never stored as the truth — it may be cached for speed, but the entries are the truth.

**What this buys you:**

| Property | How |
|---|---|
| Complete history | Every movement is a row that is never updated or deleted |
| Self-checking | Sum of all debits must equal sum of all credits. Globally. Always. |
| Corruption is detectable | A nightly job proves the books balance. If they do not, you know within hours |
| Reversal without deletion | A mistake is corrected by a *new* opposing entry, and both stay visible |
| Point-in-time answers | "What was this balance on 3 March?" is a query, not an archaeology project |

This is a 500-year-old pattern. Every serious financial system uses it. Do not invent something newer.

---

## The communication map

```
Client ──► Gateway ──► Transfers API   (sync, 202 Accepted)
                            │
                            ▼
                     TransferSaga (orchestration)
                            │
        ┌───────────────────┼─────────────────────┐
        ▼                   ▼                     ▼
   Fraud (sync-ish)     Ledger (command)     Payments (command)
        │                   │                     │
        └───────────────────┴─────────────────────┘
                            │
                            ▼
                     events → Notifications, Reporting
```

### Every decision, with the reason

| Call | Choice | Why |
|---|---|---|
| Client → Transfers | **Sync API, `202 Accepted`** | The client needs a reference ID immediately. The money moves behind it |
| Transfers → Fraud | **Command on a queue** | Must complete before posting. Modelled as a saga step with a timeout, not a blocking HTTP call |
| Transfers → Ledger | **Command on a queue, FIFO per account** | Exactly one service must post. Ordering per account is mandatory |
| Ledger internal posting | **One database transaction** | Debit and credit must be atomic. This is the one place that must be ACID |
| Ledger → everyone | **Events** | Notifications, reporting, fraud all react |
| Transfers → Payments | **Command** | Only after the ledger has posted |
| Payments → external network | **Sync with idempotency key** | Their API; their rules |

### Why the ledger posting is NOT a saga

The debit and the credit go in **one local database transaction**, in **one service**:

```csharp
using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.Serializable, ct);
db.JournalEntries.Add(debit);
db.JournalEntries.Add(credit);
await db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);      // both, or neither. Real ACID.
```

If you split debit and credit into two services, you have made money movement eventually consistent — and there is a window where money exists in neither account, or in both.

> **This is [chapter 7's](../../tutorial/07-saga.md) most important note in practice: "we need a distributed transaction here" usually means the boundary is wrong.** Debit and credit belong together, in one service, in one transaction. The saga coordinates everything *around* the posting; it does not coordinate the posting itself.

---

## Walkthrough: transferring ₹5,000

```
t=0ms      Client       POST /transfers  (Idempotency-Key: 7f3a…)
t=3ms      Transfers    key not seen → create Transfer (status = Requested)
t=6ms      Transfers    INSERT transfer + INSERT outbox  ← one transaction
t=8ms      Transfers    202 Accepted { transferId, status: "Requested" }

t=200ms    Saga         → Fraud: ScreenTransfer
t=340ms    Fraud        score 12/100, clean → TransferScreened(approved)

t=350ms    Saga         → Ledger: PostTransfer (SessionId = fromAccountId)
t=380ms    Ledger       BEGIN
t=381ms    Ledger         check available balance from entries
t=384ms    Ledger         INSERT debit  A -5000
t=385ms    Ledger         INSERT credit B +5000
t=387ms    Ledger       COMMIT                      ← atomic, ACID, non-negotiable
t=390ms    Ledger       → TransferPosted

t=400ms    Saga         status = Posted → Finalize
t=405ms    Notifications SMS to both customers
t=410ms    Reporting    update the statement projection
```

The customer got a reference in **8 ms** and an SMS in **under half a second**.

### The unhappy paths

**Insufficient funds** — this is a normal outcome, not an error:
```
t=384ms    Ledger      available = 3,200 < 5,000 → PostRejected(InsufficientFunds)
t=390ms    Saga        status = Rejected. NOTHING was posted. No compensation needed.
t=400ms    Notifications "Transfer failed: insufficient balance"
```

**Fraud hold:**
```
t=340ms    Fraud       score 87/100 → TransferHeld(reason: unusual-beneficiary)
t=350ms    Saga        status = UnderReview. Money has NOT moved.
                       A human decides. The saga waits, with a 24-hour timeout.
```

**Outbound payment fails after the ledger posted** — the only case needing compensation:
```
t=800ms    Payments    the beneficiary bank rejected the payment
t=810ms    Saga        → Ledger: ReverseTransfer(originalJournalId)
t=830ms    Ledger      posts a NEW, OPPOSING journal entry.
                       The original entry is NEVER deleted or updated.
                       Both are visible on the statement, and that is correct —
                       the customer's money did leave and did come back.
```

---

## Key decisions

### Decision 1 — Orchestration, not choreography

Six steps: validate → screen → post → pay → confirm → notify. With compensation, a review path, and timeouts.

**Why orchestration:**

- The flow is a **business process** that compliance reviews and that changes when regulation changes. It must be readable in one file.
- **"Where is transfer T-123?"** must be answerable instantly, by support staff. One query on saga state answers it.
- Compensation needs full context: *was the ledger posted before the payment failed?* Only a coordinator with the state knows.
- A regulator will eventually ask you to produce the exact sequence of steps. Choreography cannot produce that document; a state machine is that document.

**The cost:** one more component, and it must never become a god object. The saga decides *sequence*. Fraud rules live in Fraud; balance rules live in Ledger.

### Decision 2 — Idempotency key is mandatory, not optional

In [case study 1](../01-ecommerce/), a missing key means a duplicate order. Here it means a duplicate transfer.

```csharp
if (string.IsNullOrWhiteSpace(idempotencyKey))
    return Results.BadRequest("Idempotency-Key is required");     // 400. Always. No default.
```

**Never generate one server-side.** A server-generated key is new on every retry, which defeats the mechanism at exactly the moment it is needed.

And the key is checked at **three** levels:

| Level | Guard | Catches |
|---|---|---|
| API | Unique index on `Transfers.IdempotencyKey` | Client retries |
| Saga | `CorrelationId` = transfer ID | Duplicate commands |
| Ledger | Unique index on `(JournalId, AccountId, Direction)` | Duplicate postings |

**Three levels, because one bug at any level moves real money.** Belt, braces, and a second belt.

### Decision 3 — Strict FIFO per account

Two transfers from the same account must be processed **in order**. Otherwise:

```
Balance: 1,000
Transfer X: -800   ┐ processed in parallel
Transfer Y: -600   ┘
Both read balance = 1,000. Both pass the check. Both post.
Final balance: -400.  ← an overdraft that should not exist
```

The fix is ordering per account, plus a database-level constraint:

```csharp
// Azure Service Bus sessions: strict FIFO within a session, parallel across sessions
await sender.SendMessageAsync(new ServiceBusMessage(json)
{
    SessionId = fromAccountId.ToString(),      // ordering key
    MessageId = $"post-{transferId}"           // broker-level dedupe
});
```

**And never rely on ordering alone.** The ledger also checks the balance inside a `Serializable` transaction, so a concurrency bug fails loudly instead of creating an overdraft.

**The cost:** one account's transfers are single-threaded. For a retail bank that is irrelevant (nobody makes 50 transfers a second from one account). For a corporate settlement account processing thousands a second, it is a real bottleneck — and there you use per-account queues with a different partitioning strategy.

### Decision 4 — Kafka as the audit log

Every ledger event goes to a Kafka topic with **infinite retention**.

**Why:**

- Regulators can ask for any period, years later.
- Reporting projections can be rebuilt from scratch after a bug.
- New consumers (a fraud model, a data warehouse) get full history without asking anyone.

**The cost:** storage, and a strict rule that personal data in the log must be handled for GDPR-style erasure — usually by keeping identifiers in the log and personal data in a separate, erasable store.

### Decision 5 — Never auto-retry an ambiguous payment

If an outbound payment times out, you do **not** know whether it went through.

E-commerce would retry and refund a duplicate. A bank does not:

```csharp
catch (TimeoutException)
{
    // Do NOT retry blindly. Do NOT mark it failed — the money may have left.
    transfer.MarkUnknown("payment network timeout — status unknown");

    // Query the network for the real status, with the same reference.
    await scheduler.SchedulePublish(TimeSpan.FromSeconds(30),
        new QueryPaymentStatus(transfer.Id, transfer.NetworkReference));
}
```

**Unknown is a first-class state.** A system that only has "success" and "failure" will eventually record one of them wrongly, and in banking that is a customer whose money vanished.

---

## Folder structure

`src/` sits alongside a real [`docker-compose.yml`](docker-compose.yml) — RabbitMQ for commands, Kafka with infinite retention for the audit log, PostgreSQL (for `Serializable` isolation), Jaeger, and a mock payment network you can make time out on purpose.

```
src/
├── Banking.Contracts/
│   ├── Commands/          PostTransfer.cs, ReverseTransfer.cs, ScreenTransfer.cs
│   └── Events/            TransferEvents.cs, LedgerEvents.cs
│
├── Banking.Ledger/                        ← the most important service in the bank
│   ├── Domain/
│   │   ├── JournalEntry.cs                ← immutable. No setters. No delete.
│   │   ├── Journal.cs                     ← a balanced set of entries
│   │   ├── Account.cs
│   │   └── Money.cs                       ← never use raw decimal for money
│   ├── Services/
│   │   ├── PostingService.cs              ← the ONLY code that writes entries
│   │   └── BalanceService.cs              ← derives balances from entries
│   ├── Consumers/         PostTransferConsumer.cs, ReverseTransferConsumer.cs
│   ├── Jobs/              DailyReconciliationJob.cs   ← proves the books balance
│   └── Infrastructure/
│
├── Banking.Transfers/
│   ├── Api/               TransfersEndpoints.cs
│   ├── Sagas/             TransferSaga.cs, TransferSagaState.cs
│   ├── Domain/            Transfer.cs, TransferStatus.cs
│   └── Infrastructure/
│
├── Banking.Fraud/
│   ├── Consumers/         ScreenTransferConsumer.cs
│   └── Rules/             VelocityRule.cs, NewBeneficiaryRule.cs, AmountRule.cs
│
├── Banking.Payments/
│   ├── Consumers/         SendPaymentConsumer.cs
│   ├── Networks/          INetworkClient.cs, NeftClient.cs, UpiClient.cs
│   └── Jobs/              PaymentStatusReconciler.cs   ← resolves Unknown states
│
└── Banking.Reporting/
    ├── Projections/       StatementProjection.cs
    └── Consumers/         LedgerEventsConsumer.cs
```

### Why this layout

**`Money.cs` exists.** Using `decimal` directly for money is how currency mismatches ship. A `Money` type that refuses to add INR to USD catches an entire class of bug at compile time.

**`PostingService.cs` is the only writer.** One file. Reviewable. Every change to it needs two approvals. That is a policy the folder structure makes easy to enforce.

**`DailyReconciliationJob.cs` is in `Jobs/`, not `Tests/`.** Proving the books balance is a production job that runs every night, not a test that runs in CI.

**`Networks/` is an ACL folder.** NEFT, RTGS, and UPI have three different, awkward APIs. Each gets an adapter, and their vocabulary never escapes into the domain.

---

## The code

> Read [HOW-TO-READ-THE-CODE.md](../HOW-TO-READ-THE-CODE.md) first. **These are the hardest files in the set** — read `JournalEntry.cs` before `PostingService.cs`, and read `TransferSaga.cs` as a flowchart (states → events → each `During` block), not top to bottom.

| File | Shows |
|---|---|
| [`Banking.Ledger/Domain/JournalEntry.cs`](src/Banking.Ledger/Domain/JournalEntry.cs) | Immutable double-entry, and a `Money` type |
| [`Banking.Ledger/Services/PostingService.cs`](src/Banking.Ledger/Services/PostingService.cs) | The only balance writer: ACID, serializable, idempotent |
| [`Banking.Transfers/Api/TransfersEndpoints.cs`](src/Banking.Transfers/Api/TransfersEndpoints.cs) | Mandatory idempotency, `202`, validation |
| [`Banking.Transfers/Sagas/TransferSaga.cs`](src/Banking.Transfers/Sagas/TransferSaga.cs) | Orchestration with review, timeouts, and compensation |
| [`Banking.Ledger/Jobs/DailyReconciliationJob.cs`](src/Banking.Ledger/Jobs/DailyReconciliationJob.cs) | Proving the books balance, every night |

---

## Failure modes

| What fails | What happens | Customer sees |
|---|---|---|
| **Fraud down** | Saga waits, then times out to manual review | "Your transfer is being reviewed" |
| **Ledger down** | **Nothing posts.** Commands queue up | "Transfer pending" — money has not moved |
| **Payments down** | Ledger already posted; payment queues | Money left their account, arrives when it recovers |
| **Broker down** | Outbox fills; nothing lost | Transfers accepted, processing delayed |
| **Payment times out** | State = Unknown; reconciler queries the network | "Processing" until resolved. Never a guess |
| **Duplicate PostTransfer** | Unique index rejects the second | Nothing. One posting. |
| **Books do not balance** | Nightly job alerts **immediately** | Nothing yet — you have hours to fix it before it matters |

**Note what is absent: no row says "the customer loses money" and no row says "we guess".** That is the constraint holding.

---

## Now break it

1. **Send the same `Idempotency-Key` twice.** One transfer. Same ID both times. If you get two, stop everything and fix it — this is the single most important test in the folder.
2. **Deliver `PostTransfer` twice** to the Ledger. The unique index on `(JournalId, AccountId, Direction)` must reject the second. Confirm the balance moved once.
3. **Two transfers from the same account, in parallel, that together exceed the balance.** Without FIFO and serializable isolation, you will create an overdraft. Try it with and without.
4. **Kill the Ledger mid-posting**, between the debit and the credit inserts. Restart. The transaction must have rolled back completely. If you find a debit with no credit, your isolation or transaction scope is wrong — and this is the bug that ends careers.
5. **Make the payment network time out.** Confirm the transfer goes to `Unknown`, not `Failed`. Confirm the reconciler resolves it. If your code marks it failed, you have just told a customer their money is safe when it may not be.
6. **Insert a deliberately unbalanced journal** (debit 500, credit 400) directly in the database. Confirm the nightly reconciliation catches it and alerts. If it does not, your safety net has a hole.
7. **Hold a transfer in Fraud and never respond.** Confirm the 24-hour timeout fires and routes to manual review. A saga with no timeout is a customer whose money is frozen with nobody watching.
8. **Rebuild a customer's statement from the event log alone.** It must match the live projection exactly. If it does not, your events and your state have already diverged.
9. **Try to write a balance from a service other than the Ledger.** It should be impossible — different database, no credentials. If you *can*, that is your most urgent piece of work.

---

## What this case study teaches

- **Correctness and availability are a real trade, and the business picks.** Compare row by row with [case study 1](../01-ecommerce/): same patterns, opposite answers.
- **Some things must not be distributed.** Debit and credit belong in one transaction in one service. A saga around the posting, never through it.
- **Immutable history beats mutable state** whenever "how did we get here?" matters.
- **"Unknown" is a legitimate state.** Systems with only success and failure will eventually record the wrong one.
- **Idempotency at three levels**, because a single missed guard moves real money.
- **Reconciliation is production code.** If nothing proves your invariant nightly, you will learn it is broken from an auditor.

---

← [E-commerce](../01-ecommerce/) · [All case studies](../README.md) · Next: [Stock market data](../03-stock-market-data/)
