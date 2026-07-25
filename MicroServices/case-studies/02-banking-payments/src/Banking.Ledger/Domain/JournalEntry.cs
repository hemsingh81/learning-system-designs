namespace Banking.Ledger.Domain;

// ─────────────────────────────────────────────────────────────────────────────
// DOUBLE-ENTRY BOOKKEEPING
//
// Two absolute rules, and everything in this file exists to enforce them:
//
//   RULE 1  An entry, once written, is NEVER updated and NEVER deleted.
//           A mistake is corrected by writing a new, opposing entry.
//           Both stay visible. That is the audit trail.
//
//   RULE 2  Every journal must balance: sum(debits) == sum(credits).
//           If it does not, money was created or destroyed, and the system
//           must refuse to save rather than persist a lie.
//
// There are no setters below. There is no Delete method. That is on purpose.
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>
/// One side of one movement. Immutable. Append-only. This is the atom of the
/// entire financial system — every balance, statement, and regulatory report
/// is derived from rows of this shape.
/// </summary>
public sealed class JournalEntry
{
    public long      Id        { get; private init; }
    public Guid      JournalId { get; private init; }   // groups the balanced pair
    public Guid      AccountId { get; private init; }
    public Direction Direction { get; private init; }
    public Money     Amount    { get; private init; } = null!;

    /// <summary>Human-readable, and it appears on the customer's statement.</summary>
    public string Narrative { get; private init; } = "";

    /// <summary>The business event that caused this — a transfer ID, a fee ID.
    /// This is how you answer "why is this ₹500 here?" years later.</summary>
    public string SourceReference { get; private init; } = "";

    /// <summary>When it was BOOKED. Never changes, never back-dates.</summary>
    public DateTime BookedAtUtc { get; private init; }

    /// <summary>The business date it belongs to. Can differ from BookedAtUtc —
    /// a payment made at 23:59 on a Friday may have a value date of Monday.</summary>
    public DateOnly ValueDate { get; private init; }

    private JournalEntry() { }   // for EF

    internal static JournalEntry Create(
        Guid journalId, Guid accountId, Direction direction, Money amount,
        string narrative, string sourceReference, DateOnly valueDate)
    {
        // A zero or negative entry is always a bug. Direction carries the sign,
        // the amount never does — allowing a negative debit would let two bugs
        // cancel out and hide themselves.
        if (amount.Amount <= 0)
            throw new ArgumentException("an entry amount must be positive; direction carries the sign");

        if (string.IsNullOrWhiteSpace(sourceReference))
            throw new ArgumentException("sourceReference is required — every entry must be explainable");

        return new JournalEntry
        {
            JournalId       = journalId,
            AccountId       = accountId,
            Direction       = direction,
            Amount          = amount,
            Narrative       = narrative,
            SourceReference = sourceReference,
            BookedAtUtc     = DateTime.UtcNow,
            ValueDate       = valueDate
        };
    }

    /// <summary>Signed value for summing. Debit reduces a customer balance, credit increases it.</summary>
    public decimal SignedAmount => Direction == Direction.Debit ? -Amount.Amount : Amount.Amount;
}

public enum Direction
{
    /// <summary>Money out of this account.</summary>
    Debit = 1,

    /// <summary>Money into this account.</summary>
    Credit = 2
}

// ─────────────────────────────────────────────────────────────────────────────
// A JOURNAL — a balanced set of entries
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>
/// A journal is one financial event, made of two or more entries that must sum
/// to zero. Nothing can construct an unbalanced journal: the check is in the
/// factory, so an unbalanced one cannot reach the database.
/// </summary>
public sealed class Journal
{
    private readonly List<JournalEntry> _entries = [];

    public Guid     Id          { get; private init; }
    public string   Type        { get; private init; } = "";
    public string   Reference   { get; private init; } = "";
    public DateTime CreatedAtUtc { get; private init; }

    /// <summary>Set only when this journal REVERSES an earlier one.
    /// The original is untouched — reversal is a new fact, not an edit.</summary>
    public Guid? ReversesJournalId { get; private init; }

    public IReadOnlyList<JournalEntry> Entries => _entries;

    private Journal() { }

    /// <summary>A simple transfer: one account down, another up.</summary>
    public static Journal Transfer(
        Guid   fromAccountId,
        Guid   toAccountId,
        Money  amount,
        string narrative,
        string sourceReference,
        DateOnly? valueDate = null)
    {
        if (fromAccountId == toAccountId)
            throw new ArgumentException("cannot transfer to the same account");

        var journalId = Guid.CreateVersion7();
        var vd        = valueDate ?? DateOnly.FromDateTime(DateTime.UtcNow);

        var journal = new Journal
        {
            Id           = journalId,
            Type         = "transfer",
            Reference    = sourceReference,
            CreatedAtUtc = DateTime.UtcNow
        };

        journal._entries.Add(JournalEntry.Create(
            journalId, fromAccountId, Direction.Debit, amount, narrative, sourceReference, vd));

        journal._entries.Add(JournalEntry.Create(
            journalId, toAccountId, Direction.Credit, amount, narrative, sourceReference, vd));

        journal.AssertBalanced();
        return journal;
    }

    /// <summary>
    /// Reverse an earlier journal.
    ///
    /// This does NOT delete or edit the original. It writes a new journal with
    /// every entry's direction flipped. Both appear on the statement, because
    /// both really happened: the money left, and the money came back.
    /// </summary>
    public static Journal Reverse(Journal original, string reason)
    {
        var journalId = Guid.CreateVersion7();

        var journal = new Journal
        {
            Id                = journalId,
            Type              = "reversal",
            Reference         = $"reversal-of-{original.Reference}",
            ReversesJournalId = original.Id,
            CreatedAtUtc      = DateTime.UtcNow
        };

        foreach (var e in original.Entries)
        {
            journal._entries.Add(JournalEntry.Create(
                journalId,
                e.AccountId,
                e.Direction == Direction.Debit ? Direction.Credit : Direction.Debit,   // flipped
                e.Amount,
                $"Reversal: {reason}",
                journal.Reference,
                DateOnly.FromDateTime(DateTime.UtcNow)));
        }

        journal.AssertBalanced();
        return journal;
    }

    /// <summary>
    /// RULE 2, enforced in code. If this throws, the bug is caught before the
    /// database, at the cost of one failed request instead of corrupt books.
    /// </summary>
    private void AssertBalanced()
    {
        // Group by currency: a journal mixing INR and USD cannot balance and
        // must be modelled as two journals plus an FX position.
        foreach (var group in _entries.GroupBy(e => e.Amount.Currency))
        {
            var debits  = group.Where(e => e.Direction == Direction.Debit).Sum(e => e.Amount.Amount);
            var credits = group.Where(e => e.Direction == Direction.Credit).Sum(e => e.Amount.Amount);

            if (debits != credits)
                throw new InvalidOperationException(
                    $"journal does not balance in {group.Key}: debits {debits} != credits {credits}. " +
                    "Refusing to save — this would create or destroy money.");
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MONEY
//
// Never pass a bare `decimal` around a financial system. A decimal does not
// know it is rupees, so nothing stops you adding INR to USD, and the compiler
// will happily let you do it. This type makes that a compile-time impossibility.
// ─────────────────────────────────────────────────────────────────────────────

public sealed record Money
{
    public decimal Amount   { get; }
    public string  Currency { get; }

    private Money(decimal amount, string currency)
    {
        // 4 decimal places: enough for interest and FX, and a fixed scale so
        // rounding behaviour is identical everywhere in the system.
        Amount   = Math.Round(amount, 4, MidpointRounding.ToEven);
        Currency = currency;
    }

    public static Money Of(decimal amount, string currency)
    {
        if (string.IsNullOrWhiteSpace(currency) || currency.Length != 3)
            throw new ArgumentException("currency must be a 3-letter ISO code");

        return new Money(amount, currency.ToUpperInvariant());
    }

    public static Money Inr(decimal amount) => Of(amount, "INR");
    public static Money Zero(string currency) => Of(0m, currency);

    public static Money operator +(Money a, Money b)
    {
        AssertSameCurrency(a, b);
        return new Money(a.Amount + b.Amount, a.Currency);
    }

    public static Money operator -(Money a, Money b)
    {
        AssertSameCurrency(a, b);
        return new Money(a.Amount - b.Amount, a.Currency);
    }

    public static bool operator >(Money a, Money b) { AssertSameCurrency(a, b); return a.Amount > b.Amount; }
    public static bool operator <(Money a, Money b) { AssertSameCurrency(a, b); return a.Amount < b.Amount; }
    public static bool operator >=(Money a, Money b){ AssertSameCurrency(a, b); return a.Amount >= b.Amount; }
    public static bool operator <=(Money a, Money b){ AssertSameCurrency(a, b); return a.Amount <= b.Amount; }

    private static void AssertSameCurrency(Money a, Money b)
    {
        if (a.Currency != b.Currency)
            throw new InvalidOperationException(
                $"cannot combine {a.Currency} and {b.Currency} — convert explicitly with a rate and an FX entry");
    }

    public override string ToString() => $"{Amount:N2} {Currency}";
}
