using System.Data;
using Banking.Contracts.Events;
using Banking.Ledger.Domain;
using Banking.Ledger.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Banking.Ledger.Services;

// ─────────────────────────────────────────────────────────────────────────────
// THE ONLY CODE IN THE ENTIRE BANK THAT WRITES A BALANCE
//
// Everything else — Transfers, Payments, admin tools, support scripts — must
// come through here. A second writer is not a design smell; it is an incident
// waiting to be found by an auditor.
//
// Four properties, and all four are needed:
//
//   ATOMIC        debit and credit commit together, or not at all
//   ISOLATED      Serializable, so two concurrent posts cannot both pass a
//                 balance check that only one of them should pass
//   IDEMPOTENT    the same command twice posts once
//   AUDITABLE     nothing is ever updated or deleted; corrections are new entries
// ─────────────────────────────────────────────────────────────────────────────

public sealed class PostingService(
    LedgerDbContext db,
    IBalanceService balances,
    ILogger<PostingService> log)
{
    public async Task<PostingResult> PostTransferAsync(
        Guid   transferId,
        Guid   fromAccountId,
        Guid   toAccountId,
        Money  amount,
        string narrative,
        CancellationToken ct)
    {
        // ── IDEMPOTENCY, level 1: has this transfer already posted? ─────────
        // The cheap check. The real guarantee is the unique index at the commit.
        var existing = await db.Journals
            .AsNoTracking()
            .FirstOrDefaultAsync(j => j.Reference == transferId.ToString(), ct);

        if (existing is not null)
        {
            log.LogInformation("Transfer {TransferId} already posted as journal {JournalId}",
                transferId, existing.Id);

            // Return the ORIGINAL result. From the caller's point of view this succeeded.
            return PostingResult.AlreadyPosted(existing.Id);
        }

        // ── SERIALIZABLE, and nothing weaker ────────────────────────────────
        //
        // Under ReadCommitted, two concurrent transfers from the same account can
        // both read a balance of 1,000, both pass a check for 800, and both post,
        // leaving -600. That overdraft is invisible until someone complains.
        //
        // Serializable makes the database refuse one of them. It costs throughput,
        // and for money that is the correct thing to buy with throughput.
        await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.Serializable, ct);

        try
        {
            // ── Read the balance INSIDE the transaction ─────────────────────
            // Reading it outside would leave a window between the check and the
            // write — the classic time-of-check-to-time-of-use bug, with money.
            var available = await balances.GetAvailableBalanceAsync(fromAccountId, amount.Currency, ct);

            if (available < amount)
            {
                await tx.RollbackAsync(ct);

                log.LogInformation(
                    "Transfer {TransferId} rejected: available {Available} < requested {Amount}",
                    transferId, available, amount);

                // A normal business outcome, not an exception. Nothing was written,
                // so there is nothing to compensate.
                return PostingResult.Rejected(RejectionReason.InsufficientFunds,
                    $"available {available}, requested {amount}");
            }

            // Account status is also checked here, in the same transaction —
            // an account frozen one millisecond ago must not be debited.
            var fromAccount = await db.Accounts.FirstAsync(a => a.Id == fromAccountId, ct);
            var toAccount   = await db.Accounts.FirstAsync(a => a.Id == toAccountId, ct);

            if (!fromAccount.CanDebit)
            {
                await tx.RollbackAsync(ct);
                return PostingResult.Rejected(RejectionReason.AccountBlocked,
                    $"source account is {fromAccount.Status}");
            }

            if (!toAccount.CanCredit)
            {
                await tx.RollbackAsync(ct);
                return PostingResult.Rejected(RejectionReason.AccountBlocked,
                    $"destination account is {toAccount.Status}");
            }

            // ── Build the journal. It cannot be unbalanced — Journal enforces it. ──
            var journal = Journal.Transfer(
                fromAccountId:   fromAccountId,
                toAccountId:     toAccountId,
                amount:          amount,
                narrative:       narrative,
                sourceReference: transferId.ToString());

            db.Journals.Add(journal);

            // The event goes out through the outbox, in this same transaction.
            // Publishing directly to the broker here would be the dual-write bug,
            // and in a ledger that bug means the books and the event log disagree
            // permanently (chapter 8).
            db.OutboxMessages.Add(OutboxMessage.From(new TransferPosted
            {
                TransferId    = transferId,
                JournalId     = journal.Id,
                FromAccountId = fromAccountId,
                ToAccountId   = toAccountId,
                Amount        = amount.Amount,
                Currency      = amount.Currency,
                OccurredAtUtc = DateTime.UtcNow
            }));

            await db.SaveChangesAsync(ct);
            await tx.CommitAsync(ct);

            log.LogInformation("Posted transfer {TransferId} as journal {JournalId}: {Amount}",
                transferId, journal.Id, amount);

            return PostingResult.Posted(journal.Id);
        }
        catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("IX_Journals_Reference"))
        {
            // ── IDEMPOTENCY, level 2: the real guarantee ────────────────────
            // Two instances raced past the check at the top. The unique index on
            // Reference just stopped the second one. This is the constraint doing
            // exactly its job, and it is why the check above is only an optimisation.
            await tx.RollbackAsync(ct);

            var winner = await db.Journals.AsNoTracking()
                .FirstAsync(j => j.Reference == transferId.ToString(), ct);

            log.LogInformation("Concurrent duplicate post of {TransferId} rejected by the index",
                transferId);

            return PostingResult.AlreadyPosted(winner.Id);
        }
        catch (DbUpdateException ex) when (ex.IsSerializationFailure())
        {
            // Serializable isolation refused to allow a concurrent conflict.
            // NOTHING was written. Rethrow so the broker redelivers and we try
            // again — the retry re-reads a now-correct balance.
            await tx.RollbackAsync(ct);
            log.LogWarning("Serialization conflict posting {TransferId}, will retry", transferId);
            throw;
        }
    }

    /// <summary>
    /// Undo a posting by writing an OPPOSING journal.
    ///
    /// The original entries are not touched. Both journals appear on the
    /// statement, because both really happened. This is what "you cannot roll
    /// back, you can only apologise correctly" means in a ledger (chapter 7).
    /// </summary>
    public async Task<PostingResult> ReverseAsync(
        Guid originalJournalId, string reason, CancellationToken ct)
    {
        await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.Serializable, ct);

        var original = await db.Journals
            .Include(j => j.Entries)
            .FirstOrDefaultAsync(j => j.Id == originalJournalId, ct);

        if (original is null)
            return PostingResult.Rejected(RejectionReason.NotFound, "original journal not found");

        // Do not reverse a reversal twice. Compensation must be idempotent
        // (chapter 7, rule 1) — and here a double reversal literally invents money.
        var alreadyReversed = await db.Journals
            .AnyAsync(j => j.ReversesJournalId == originalJournalId, ct);

        if (alreadyReversed)
        {
            await tx.RollbackAsync(ct);
            log.LogInformation("Journal {JournalId} is already reversed, ignoring", originalJournalId);
            return PostingResult.AlreadyPosted(originalJournalId);
        }

        var reversal = Journal.Reverse(original, reason);
        db.Journals.Add(reversal);

        db.OutboxMessages.Add(OutboxMessage.From(new TransferReversed
        {
            OriginalJournalId = originalJournalId,
            ReversalJournalId = reversal.Id,
            Reason            = reason,
            OccurredAtUtc     = DateTime.UtcNow
        }));

        await db.SaveChangesAsync(ct);
        await tx.CommitAsync(ct);

        log.LogWarning("Reversed journal {Original} with {Reversal}: {Reason}",
            originalJournalId, reversal.Id, reason);

        return PostingResult.Posted(reversal.Id);
    }
}

// ── Results ─────────────────────────────────────────────────────────────────
// Note there is no "Failed" here. A posting either happened, already happened,
// or was rejected for a stated business reason. Anything else throws, so it
// cannot be silently mistaken for a clean failure.

public sealed record PostingResult
{
    public required PostingOutcome  Outcome   { get; init; }
    public Guid?                    JournalId { get; init; }
    public RejectionReason?         Reason    { get; init; }
    public string?                  Detail    { get; init; }

    public static PostingResult Posted(Guid journalId) =>
        new() { Outcome = PostingOutcome.Posted, JournalId = journalId };

    public static PostingResult AlreadyPosted(Guid journalId) =>
        new() { Outcome = PostingOutcome.AlreadyPosted, JournalId = journalId };

    public static PostingResult Rejected(RejectionReason reason, string detail) =>
        new() { Outcome = PostingOutcome.Rejected, Reason = reason, Detail = detail };
}

public enum PostingOutcome { Posted, AlreadyPosted, Rejected }

public enum RejectionReason
{
    InsufficientFunds,
    AccountBlocked,
    NotFound,
    LimitExceeded,
    CurrencyMismatch
}
