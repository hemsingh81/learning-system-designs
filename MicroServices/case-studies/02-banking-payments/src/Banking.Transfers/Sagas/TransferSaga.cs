using Banking.Contracts.Commands;
using Banking.Contracts.Events;
using MassTransit;

namespace Banking.Transfers.Sagas;

// ─────────────────────────────────────────────────────────────────────────────
// THE TRANSFER SAGA — ORCHESTRATION
//
// Why orchestration here and choreography in the e-commerce case study:
//
//   1. Compliance reviews this flow. It must be readable in ONE file.
//   2. Support must answer "where is transfer T-123?" instantly. One query does it.
//   3. Compensation needs context: did the ledger post BEFORE the payment failed?
//      Only a coordinator holding the state knows that.
//   4. A regulator will eventually ask for the exact sequence of steps.
//      This file IS that document.
//
// What this saga does NOT do: decide fraud rules, decide balance rules, or
// decide payment routing. It decides SEQUENCE and COMPENSATION only. The moment
// it holds policy, every team must edit it to ship anything (chapter 7, edge 6).
// ─────────────────────────────────────────────────────────────────────────────

public sealed class TransferSaga : MassTransitStateMachine<TransferSagaState>
{
    // ── States ──────────────────────────────────────────────────────────────
    public State Screening      { get; private set; } = null!;
    public State UnderReview    { get; private set; } = null!;
    public State Posting        { get; private set; } = null!;
    public State Paying         { get; private set; } = null!;
    public State Compensating   { get; private set; } = null!;
    public State Completed      { get; private set; } = null!;
    public State Rejected       { get; private set; } = null!;

    /// <summary>Money may or may not have left. A human must resolve it.
    /// Never auto-resolve this state — that is how a customer loses money.</summary>
    public State NeedsManualResolution { get; private set; } = null!;

    // ── Events ──────────────────────────────────────────────────────────────
    public Event<TransferRequested>  TransferRequested  { get; private set; } = null!;
    public Event<TransferScreened>   Screened           { get; private set; } = null!;
    public Event<TransferHeld>       Held               { get; private set; } = null!;
    public Event<ReviewDecided>      ReviewDecided      { get; private set; } = null!;
    public Event<TransferPosted>     Posted             { get; private set; } = null!;
    public Event<PostRejected>       PostRejected       { get; private set; } = null!;
    public Event<PaymentSent>        PaymentSent        { get; private set; } = null!;
    public Event<PaymentFailed>      PaymentFailed      { get; private set; } = null!;
    public Event<PaymentUnknown>     PaymentUnknown     { get; private set; } = null!;
    public Event<TransferReversed>   Reversed           { get; private set; } = null!;

    // ── Timeouts ────────────────────────────────────────────────────────────
    // EVERY wait has one. A saga with no timeout is a customer whose money is
    // frozen with nobody watching (chapter 7, rule 4). This is the single most
    // common real-world saga bug.
    public Schedule<TransferSagaState, ScreeningTimeout> ScreeningTimeout { get; private set; } = null!;
    public Schedule<TransferSagaState, ReviewTimeout>    ReviewTimeout    { get; private set; } = null!;
    public Schedule<TransferSagaState, PostingTimeout>   PostingTimeout   { get; private set; } = null!;
    public Schedule<TransferSagaState, PaymentTimeout>   PaymentTimeout   { get; private set; } = null!;

    public TransferSaga()
    {
        InstanceState(x => x.CurrentState);

        // Every event correlates on the transfer ID. One saga per transfer, always.
        Event(() => TransferRequested, x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => Screened,          x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => Held,              x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => ReviewDecided,     x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => Posted,            x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => PostRejected,      x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => PaymentSent,       x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => PaymentFailed,     x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => PaymentUnknown,    x => x.CorrelateById(m => m.Message.TransferId));
        Event(() => Reversed,          x => x.CorrelateById(m => m.Message.TransferId));

        Schedule(() => ScreeningTimeout, x => x.ScreeningTimeoutToken, s => s.Delay = TimeSpan.FromMinutes(2));
        Schedule(() => ReviewTimeout,    x => x.ReviewTimeoutToken,    s => s.Delay = TimeSpan.FromHours(24));
        Schedule(() => PostingTimeout,   x => x.PostingTimeoutToken,   s => s.Delay = TimeSpan.FromMinutes(1));
        Schedule(() => PaymentTimeout,   x => x.PaymentTimeoutToken,   s => s.Delay = TimeSpan.FromMinutes(10));

        // ── 1. Requested → screening ────────────────────────────────────────
        Initially(
            When(TransferRequested)
                .Then(c =>
                {
                    c.Saga.FromAccountId = c.Message.FromAccountId;
                    c.Saga.ToAccountId   = c.Message.ToAccountId;
                    c.Saga.Amount        = c.Message.Amount;
                    c.Saga.Currency      = c.Message.Currency;
                    c.Saga.Narrative     = c.Message.Narrative;
                    c.Saga.IsExternal    = c.Message.IsExternal;
                    c.Saga.StartedAtUtc  = DateTime.UtcNow;
                })
                .Send(c => new ScreenTransfer(
                    c.Saga.CorrelationId, c.Saga.FromAccountId, c.Saga.ToAccountId,
                    c.Saga.Amount, c.Saga.Currency))
                .Schedule(ScreeningTimeout, c => new ScreeningTimeout(c.Saga.CorrelationId))
                .TransitionTo(Screening));

        // ── 2. Screening ────────────────────────────────────────────────────
        During(Screening,
            When(Screened)
                .Unschedule(ScreeningTimeout)
                .Then(c => c.Saga.FraudScore = c.Message.Score)
                .Send(c => new PostTransfer(
                    c.Saga.CorrelationId, c.Saga.FromAccountId, c.Saga.ToAccountId,
                    c.Saga.Amount, c.Saga.Currency, c.Saga.Narrative))
                .Schedule(PostingTimeout, c => new PostingTimeout(c.Saga.CorrelationId))
                .TransitionTo(Posting),

            When(Held)
                .Unschedule(ScreeningTimeout)
                .Then(c =>
                {
                    c.Saga.FraudScore = c.Message.Score;
                    c.Saga.HoldReason = c.Message.Reason;
                })
                .Schedule(ReviewTimeout, c => new ReviewTimeout(c.Saga.CorrelationId))
                .Publish(c => new TransferUnderReview(c.Saga.CorrelationId, c.Message.Reason))
                .TransitionTo(UnderReview),

            // Fraud never answered. Money has NOT moved, so the safe default is
            // to hold, not to proceed. In banking, silence means stop.
            When(ScreeningTimeout.Received)
                .Then(c => c.Saga.HoldReason = "fraud screening timed out")
                .Schedule(ReviewTimeout, c => new ReviewTimeout(c.Saga.CorrelationId))
                .Publish(c => new TransferUnderReview(c.Saga.CorrelationId, "screening timeout"))
                .TransitionTo(UnderReview));

        // ── 3. Manual review ────────────────────────────────────────────────
        During(UnderReview,
            When(ReviewDecided)
                .Unschedule(ReviewTimeout)
                .IfElse(c => c.Message.Approved,
                    approved => approved
                        .Send(c => new PostTransfer(
                            c.Saga.CorrelationId, c.Saga.FromAccountId, c.Saga.ToAccountId,
                            c.Saga.Amount, c.Saga.Currency, c.Saga.Narrative))
                        .Schedule(PostingTimeout, c => new PostingTimeout(c.Saga.CorrelationId))
                        .TransitionTo(Posting),
                    denied => denied
                        .Then(c => c.Saga.FailureReason = c.Message.Reason)
                        .Publish(c => new TransferRejected(c.Saga.CorrelationId, c.Message.Reason))
                        .TransitionTo(Rejected)
                        .Finalize()),

            // 24 hours with no human decision. Escalate — do NOT auto-approve.
            When(ReviewTimeout.Received)
                .Publish(c => new ReviewEscalated(c.Saga.CorrelationId, "no decision within 24 hours"))
                .TransitionTo(NeedsManualResolution));

        // ── 4. Posting to the ledger ────────────────────────────────────────
        During(Posting,
            When(Posted)
                .Unschedule(PostingTimeout)
                .Then(c =>
                {
                    c.Saga.JournalId = c.Message.JournalId;   // needed for compensation
                    c.Saga.PostedAtUtc = DateTime.UtcNow;
                })
                .IfElse(c => c.Saga.IsExternal,
                    // External: the money must leave the bank.
                    external => external
                        .Send(c => new SendPayment(
                            c.Saga.CorrelationId, c.Saga.ToAccountId,
                            c.Saga.Amount, c.Saga.Currency))
                        .Schedule(PaymentTimeout, c => new PaymentTimeout(c.Saga.CorrelationId))
                        .TransitionTo(Paying),
                    // Internal: both accounts are ours. The posting IS the transfer. Done.
                    internalOnly => internalOnly
                        .Publish(c => new TransferCompleted(c.Saga.CorrelationId, c.Saga.JournalId!.Value))
                        .TransitionTo(Completed)
                        .Finalize()),

            // Rejected by the ledger (insufficient funds, blocked account).
            // NOTHING was posted, so there is nothing to compensate.
            When(PostRejected)
                .Unschedule(PostingTimeout)
                .Then(c => c.Saga.FailureReason = c.Message.Reason)
                .Publish(c => new TransferRejected(c.Saga.CorrelationId, c.Message.Reason))
                .TransitionTo(Rejected)
                .Finalize(),

            // The ledger did not answer. We do not know whether it posted.
            // NEVER retry a posting blindly — that risks a double debit.
            // A human (or the reconciler) checks the ledger and decides.
            When(PostingTimeout.Received)
                .Then(c => c.Saga.FailureReason = "ledger did not respond — posting status unknown")
                .Publish(c => new TransferNeedsResolution(
                    c.Saga.CorrelationId, "posting timed out; verify the ledger before retrying"))
                .TransitionTo(NeedsManualResolution));

        // ── 5. External payment ─────────────────────────────────────────────
        During(Paying,
            When(PaymentSent)
                .Unschedule(PaymentTimeout)
                .Then(c => c.Saga.NetworkReference = c.Message.NetworkReference)
                .Publish(c => new TransferCompleted(c.Saga.CorrelationId, c.Saga.JournalId!.Value))
                .TransitionTo(Completed)
                .Finalize(),

            // The ONLY path that needs compensation: the ledger posted, then the
            // payment definitively failed. Reverse the posting with a new journal.
            When(PaymentFailed)
                .Unschedule(PaymentTimeout)
                .Then(c => c.Saga.FailureReason = c.Message.Reason)
                .If(c => c.Saga.JournalId is not null,          // only undo what actually happened
                    b => b.Send(c => new ReverseTransfer(
                        c.Saga.CorrelationId, c.Saga.JournalId!.Value,
                        $"outbound payment failed: {c.Message.Reason}")))
                .TransitionTo(Compensating),

            // The network timed out. The money MAY have left. This is the state
            // that must never be guessed — see "Decision 5" in the README.
            When(PaymentUnknown)
                .Unschedule(PaymentTimeout)
                .Then(c => c.Saga.FailureReason = "payment status unknown")
                .Publish(c => new TransferNeedsResolution(
                    c.Saga.CorrelationId, "query the payment network before any action"))
                .TransitionTo(NeedsManualResolution),

            When(PaymentTimeout.Received)
                .Publish(c => new TransferNeedsResolution(
                    c.Saga.CorrelationId, "payment did not respond within 10 minutes"))
                .TransitionTo(NeedsManualResolution));

        // ── 6. Compensation ─────────────────────────────────────────────────
        During(Compensating,
            When(Reversed)
                .Publish(c => new TransferRejected(
                    c.Saga.CorrelationId, c.Saga.FailureReason ?? "payment failed"))
                .TransitionTo(Rejected)
                .Finalize());

        // A saga stuck here is a real customer with real money in limbo.
        // Alert on the COUNT of sagas in this state — it should normally be zero.
        During(NeedsManualResolution,
            Ignore(PaymentSent),
            Ignore(PaymentFailed),
            Ignore(Posted));

        // Keep the saga table small: finished sagas are removed. History lives
        // in the ledger and the event log, which are the real records.
        SetCompletedWhenFinalized();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// SAGA STATE
//
// Persisted after EVERY transition. If the coordinator dies between two steps,
// it resumes from exactly where it was. If this were held in memory, a restart
// would lose transfers mid-flight (chapter 7, edge 3).
// ─────────────────────────────────────────────────────────────────────────────

public sealed class TransferSagaState : SagaStateMachineInstance, ISagaVersion
{
    public Guid   CorrelationId { get; set; }         // = TransferId
    public string CurrentState  { get; set; } = "";

    public Guid    FromAccountId { get; set; }
    public Guid    ToAccountId   { get; set; }
    public decimal Amount        { get; set; }
    public string  Currency      { get; set; } = "INR";
    public string  Narrative     { get; set; } = "";
    public bool    IsExternal    { get; set; }

    // What actually HAPPENED. Compensation reads these so it never undoes a
    // step that never ran — the most common compensation bug.
    public Guid?   JournalId        { get; set; }
    public string? NetworkReference { get; set; }
    public DateTime? PostedAtUtc    { get; set; }

    public int?    FraudScore    { get; set; }
    public string? HoldReason    { get; set; }
    public string? FailureReason { get; set; }
    public DateTime StartedAtUtc { get; set; }

    // Timeout tokens
    public Guid? ScreeningTimeoutToken { get; set; }
    public Guid? ReviewTimeoutToken    { get; set; }
    public Guid? PostingTimeoutToken   { get; set; }
    public Guid? PaymentTimeoutToken   { get; set; }

    /// <summary>Optimistic concurrency. Two messages for the same saga can arrive
    /// at two instances simultaneously; without this, one silently overwrites the
    /// other's decision (chapter 7, edge 4).</summary>
    public int Version { get; set; }
}
