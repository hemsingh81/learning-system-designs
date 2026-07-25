using Banking.Ledger.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace Banking.Ledger.Jobs;

// ─────────────────────────────────────────────────────────────────────────────
// PROVING THE BOOKS BALANCE — EVERY NIGHT
//
// This is PRODUCTION code, not a test. The distinction matters:
//
//   A test proves the code was correct when you wrote it.
//   This proves the DATA is correct right now.
//
// Bugs, bad migrations, manual database edits, and partial failures all corrupt
// data in ways no unit test can see. Without a job like this, you find out from
// an auditor, months later, and you cannot say when it started.
//
// The rule: EVERY financial invariant you rely on must be checked by something
// that runs on a schedule and alerts a human.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class DailyReconciliationJob(
    IServiceScopeFactory scopes,
    IAlertService alerts,
    ILogger<DailyReconciliationJob> log) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            var nextRun = NextRunUtc();
            var delay   = nextRun - DateTime.UtcNow;

            if (delay > TimeSpan.Zero)
                await Task.Delay(delay, ct);

            try
            {
                await RunAsync(ct);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                // A reconciliation that FAILS is itself an alert. Silence here
                // would mean nobody is checking, and nobody would know.
                log.LogError(ex, "Reconciliation run failed");
                await alerts.RaiseAsync(AlertSeverity.High,
                    "Ledger reconciliation failed to run", ex.ToString(), ct);
            }
        }
    }

    public async Task<ReconciliationReport> RunAsync(CancellationToken ct)
    {
        using var scope = scopes.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<LedgerDbContext>();

        var startedAt = DateTime.UtcNow;
        var report    = new ReconciliationReport { StartedAtUtc = startedAt };

        log.LogInformation("Starting ledger reconciliation");

        // ── CHECK 1: the global invariant ───────────────────────────────────
        //
        // Across the entire ledger, per currency, total debits must equal total
        // credits. If this fails, money was created or destroyed. There is no
        // benign explanation and no acceptable delay in investigating it.
        var globals = await db.JournalEntries
            .GroupBy(e => e.Amount.Currency)
            .Select(g => new
            {
                Currency = g.Key,
                Debits   = g.Where(e => e.Direction == Direction.Debit).Sum(e => e.Amount.Amount),
                Credits  = g.Where(e => e.Direction == Direction.Credit).Sum(e => e.Amount.Amount)
            })
            .ToListAsync(ct);

        foreach (var g in globals)
        {
            var difference = g.Debits - g.Credits;
            report.CurrencyTotals.Add(new CurrencyTotal(g.Currency, g.Debits, g.Credits, difference));

            if (difference != 0)
            {
                report.IsBalanced = false;

                // CRITICAL. Wake someone up. This is not a "look at it on Monday".
                await alerts.RaiseAsync(AlertSeverity.Critical,
                    $"LEDGER DOES NOT BALANCE in {g.Currency}",
                    $"Debits {g.Debits:N4}, credits {g.Credits:N4}, difference {difference:N4}. " +
                    "Money has been created or destroyed. Freeze postings and investigate now.",
                    ct);

                log.LogCritical("Ledger does not balance in {Currency}: difference {Difference}",
                    g.Currency, difference);
            }
        }

        // ── CHECK 2: every journal balances individually ────────────────────
        //
        // The global check can pass while two individual journals are wrong in
        // opposite directions. This finds those.
        var unbalanced = await db.JournalEntries
            .GroupBy(e => new { e.JournalId, e.Amount.Currency })
            .Select(g => new
            {
                g.Key.JournalId,
                g.Key.Currency,
                Net = g.Sum(e => e.Direction == Direction.Debit ? e.Amount.Amount : -e.Amount.Amount)
            })
            .Where(x => x.Net != 0)
            .Take(1000)
            .ToListAsync(ct);

        foreach (var j in unbalanced)
        {
            report.IsBalanced = false;
            report.UnbalancedJournals.Add(j.JournalId);

            log.LogCritical("Journal {JournalId} does not balance in {Currency}: net {Net}",
                j.JournalId, j.Currency, j.Net);
        }

        if (unbalanced.Count > 0)
        {
            await alerts.RaiseAsync(AlertSeverity.Critical,
                $"{unbalanced.Count} unbalanced journal(s) found",
                string.Join(", ", unbalanced.Take(20).Select(j => j.JournalId)), ct);
        }

        // ── CHECK 3: cached balances match derived balances ─────────────────
        //
        // Balances are DERIVED from entries. If a cached balance column is used
        // for speed, it must be proved correct — a stale cache shows a customer
        // the wrong number, and support cannot tell which one is real.
        var drifted = await db.Database
            .SqlQuery<BalanceDrift>($"""
                SELECT  a.Id                  AS AccountId,
                        a.CachedBalance        AS Cached,
                        COALESCE(SUM(CASE WHEN e.Direction = 1
                                          THEN -e.Amount ELSE e.Amount END), 0) AS Derived
                FROM    Accounts a
                LEFT JOIN JournalEntries e ON e.AccountId = a.Id
                GROUP BY a.Id, a.CachedBalance
                HAVING  a.CachedBalance <> COALESCE(SUM(CASE WHEN e.Direction = 1
                                                            THEN -e.Amount ELSE e.Amount END), 0)
                """)
            .ToListAsync(ct);

        foreach (var d in drifted)
        {
            report.DriftedAccounts.Add(d);

            log.LogError("Balance drift on account {AccountId}: cached {Cached}, derived {Derived}",
                d.AccountId, d.Cached, d.Derived);
        }

        if (drifted.Count > 0)
        {
            // The derived value is ALWAYS the truth. The cache is repaired from
            // the entries, never the other way round.
            await alerts.RaiseAsync(AlertSeverity.High,
                $"{drifted.Count} account(s) have a stale cached balance",
                "Rebuild the cache from journal entries. Entries are the source of truth.", ct);
        }

        // ── CHECK 4: nothing was mutated ────────────────────────────────────
        //
        // Entries are append-only. If a row's hash no longer matches what was
        // written, someone edited the ledger directly — a serious event that
        // no amount of application code can prevent, only detect.
        var tamperedCount = await db.JournalEntries
            .Where(e => e.BookedAtUtc > startedAt.AddDays(-1))
            .CountAsync(e => e.IntegrityHash != e.ComputedHash, ct);

        if (tamperedCount > 0)
        {
            report.IsBalanced = false;

            await alerts.RaiseAsync(AlertSeverity.Critical,
                $"{tamperedCount} journal entries fail their integrity check",
                "Entries have been modified after being written. Treat as a security incident.", ct);
        }

        report.CompletedAtUtc = DateTime.UtcNow;
        report.EntriesChecked = await db.JournalEntries.CountAsync(ct);

        if (report.IsBalanced && report.DriftedAccounts.Count == 0)
        {
            log.LogInformation(
                "Reconciliation passed: {Entries} entries, {Currencies} currencies, all balanced in {Duration}",
                report.EntriesChecked, report.CurrencyTotals.Count,
                report.CompletedAtUtc - report.StartedAtUtc);
        }

        // Keep every report. "When did this start?" is the first question asked
        // after a discrepancy is found, and only a history can answer it.
        db.ReconciliationReports.Add(report);
        await db.SaveChangesAsync(ct);

        return report;
    }

    // 02:00 UTC — after the day's posting has settled, before the business day starts.
    private static DateTime NextRunUtc()
    {
        var now  = DateTime.UtcNow;
        var next = new DateTime(now.Year, now.Month, now.Day, 2, 0, 0, DateTimeKind.Utc);
        return next <= now ? next.AddDays(1) : next;
    }
}

public sealed class ReconciliationReport
{
    public long     Id             { get; set; }
    public DateTime StartedAtUtc   { get; set; }
    public DateTime CompletedAtUtc { get; set; }
    public int      EntriesChecked { get; set; }
    public bool     IsBalanced     { get; set; } = true;

    public List<CurrencyTotal> CurrencyTotals     { get; } = [];
    public List<Guid>          UnbalancedJournals { get; } = [];
    public List<BalanceDrift>  DriftedAccounts    { get; } = [];
}

public sealed record CurrencyTotal(string Currency, decimal Debits, decimal Credits, decimal Difference);

public sealed record BalanceDrift(Guid AccountId, decimal Cached, decimal Derived);

public enum AlertSeverity { Low, Medium, High, Critical }
