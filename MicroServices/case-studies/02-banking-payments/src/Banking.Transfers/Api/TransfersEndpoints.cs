using Banking.Transfers.Domain;
using Banking.Transfers.Infrastructure;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace Banking.Transfers.Api;

// ─────────────────────────────────────────────────────────────────────────────
// THE TRANSFER API
//
// Compare this with the e-commerce endpoint. Same shape, three differences,
// and every one of them exists because this endpoint moves money:
//
//   1. Idempotency-Key is MANDATORY. Not defaulted. Not generated. 400 without it.
//   2. Validation is strict and explicit — a wrong currency is a rejection,
//      never a best-effort conversion.
//   3. The response never claims more than is true. "Requested" means requested.
// ─────────────────────────────────────────────────────────────────────────────

public static class TransfersEndpoints
{
    public static IEndpointRouteBuilder MapTransfers(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/transfers").RequireAuthorization();

        group.MapPost("/",           RequestAsync);
        group.MapGet ("/{id}",       GetAsync);
        group.MapGet ("/{id}/status", GetStatusAsync);

        return app;
    }

    private static async Task<IResult> RequestAsync(
        TransferRequest request,
        [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey,
        TransfersDbContext db,
        IAccountValidator accounts,
        ILogger<TransferRequest> log,
        CancellationToken ct)
    {
        // ── 1. Idempotency key is mandatory ─────────────────────────────────
        //
        // In the e-commerce case a missing key means a duplicate order.
        // Here it means a duplicate transfer — real money, twice.
        //
        // We do NOT generate one server-side. A generated key would be new on
        // every retry, which defeats the mechanism at exactly the moment it
        // matters. The key must come from the client and must survive its retry.
        if (string.IsNullOrWhiteSpace(idempotencyKey))
            return Results.Problem(
                title:  "Idempotency-Key header is required",
                detail: "Send a stable client-generated key (for example a UUID stored with the " +
                        "request) and reuse it for every retry of this transfer.",
                statusCode: StatusCodes.Status400BadRequest);

        if (idempotencyKey.Length > 100)
            return Results.Problem(title: "Idempotency-Key is too long (max 100 characters)",
                                   statusCode: StatusCodes.Status400BadRequest);

        // ── 2. Replay? Return the ORIGINAL result. ──────────────────────────
        var existing = await db.Transfers
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.IdempotencyKey == idempotencyKey, ct);

        if (existing is not null)
        {
            // A retry of a request we already accepted. This is a success.
            //
            // BUT: if the key was reused with DIFFERENT details, that is a client
            // bug and we must refuse loudly rather than silently returning an
            // unrelated transfer.
            if (!existing.Matches(request.FromAccountId, request.ToAccountId,
                                  request.Amount, request.Currency))
            {
                log.LogError("Idempotency key {Key} reused with different parameters", idempotencyKey);

                return Results.Problem(
                    title:  "Idempotency-Key was already used with different transfer details",
                    detail: "Use a new key for a different transfer.",
                    statusCode: StatusCodes.Status409Conflict);
            }

            return Results.Ok(TransferResponse.From(existing));
        }

        // ── 3. Validate. Strictly. ──────────────────────────────────────────
        if (request.Amount <= 0)
            return Bad("Amount must be greater than zero");

        if (request.Amount > 10_000_000m)
            return Bad("Amount exceeds the single-transfer limit; use the bulk payment channel");

        if (request.FromAccountId == request.ToAccountId)
            return Bad("Source and destination accounts must differ");

        if (string.IsNullOrWhiteSpace(request.Currency) || request.Currency.Length != 3)
            return Bad("Currency must be a 3-letter ISO code");

        // The source account must exist, be ours, and be usable. This is a
        // synchronous call because we cannot accept a transfer from an account
        // that does not exist — question 1 of the framework says sync.
        var validation = await accounts.ValidateForDebitAsync(
            request.FromAccountId, request.Currency, ct);

        if (!validation.IsValid)
            return Results.Problem(title: "Source account cannot be debited",
                                   detail: validation.Reason,
                                   statusCode: StatusCodes.Status422UnprocessableEntity);

        // ── 4. Create + outbox in ONE transaction ───────────────────────────
        var transfer = Transfer.Request(
            fromAccountId:  request.FromAccountId,
            toAccountId:    request.ToAccountId,
            amount:         request.Amount,
            currency:       request.Currency.ToUpperInvariant(),
            narrative:      request.Narrative ?? "Transfer",
            isExternal:     validation.IsExternalBeneficiary,
            idempotencyKey: idempotencyKey);

        db.Transfers.Add(transfer);

        foreach (var e in transfer.DomainEvents)
            db.OutboxMessages.Add(OutboxMessage.From(e));

        transfer.ClearDomainEvents();

        try
        {
            await db.SaveChangesAsync(ct);
        }
        catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("IX_Transfers_IdempotencyKey"))
        {
            // Two identical requests hit two instances at the same instant.
            // The unique index caught the second. Return the winner.
            var winner = await db.Transfers.AsNoTracking()
                .FirstAsync(t => t.IdempotencyKey == idempotencyKey, ct);

            return Results.Ok(TransferResponse.From(winner));
        }

        log.LogInformation("Transfer {TransferId} requested: {Amount} {Currency}",
            transfer.Id, transfer.Amount, transfer.Currency);

        // ── 5. 202 Accepted, and the status says exactly what is true ───────
        // "Requested" — not "Sent", not "Complete". Nothing has moved yet.
        // Overstating this is how a customer thinks money has arrived when it
        // is still in fraud review.
        return Results.Accepted($"/transfers/{transfer.Id}", TransferResponse.From(transfer));

        static IResult Bad(string message) =>
            Results.Problem(title: "Invalid transfer", detail: message,
                            statusCode: StatusCodes.Status400BadRequest);
    }

    private static async Task<IResult> GetAsync(Guid id, TransfersDbContext db, CancellationToken ct)
    {
        var transfer = await db.Transfers.AsNoTracking().FirstOrDefaultAsync(t => t.Id == id, ct);
        return transfer is null ? Results.NotFound() : Results.Ok(TransferResponse.From(transfer));
    }

    /// <summary>
    /// The support desk's endpoint: "where is transfer T-123?"
    ///
    /// This reads the SAGA state, not the transfer row, because the saga is what
    /// knows which step is in progress. Being able to answer this in one query is
    /// a large part of why this system uses orchestration (chapter 7).
    /// </summary>
    private static async Task<IResult> GetStatusAsync(
        Guid id, TransfersDbContext db, CancellationToken ct)
    {
        var saga = await db.TransferSagas.AsNoTracking()
            .FirstOrDefaultAsync(s => s.CorrelationId == id, ct);

        if (saga is null)
        {
            // No saga: either finished (finalised and removed) or never started.
            var transfer = await db.Transfers.AsNoTracking().FirstOrDefaultAsync(t => t.Id == id, ct);
            return transfer is null
                ? Results.NotFound()
                : Results.Ok(new { transfer.Id, Stage = transfer.Status.ToString(), IsFinal = true });
        }

        return Results.Ok(new
        {
            Id           = saga.CorrelationId,
            Stage        = saga.CurrentState,
            JournalId    = saga.JournalId,          // null until the ledger posted
            MoneyMoved   = saga.JournalId is not null,
            HeldReason   = saga.HoldReason,
            FailureReason = saga.FailureReason,
            WaitingSince = saga.StartedAtUtc,

            // The flag support actually needs: is a human required?
            NeedsHuman   = saga.CurrentState is "UnderReview" or "NeedsManualResolution"
        });
    }
}

public sealed record TransferRequest
{
    public required Guid    FromAccountId { get; init; }
    public required Guid    ToAccountId   { get; init; }
    public required decimal Amount        { get; init; }
    public required string  Currency      { get; init; }
    public string? Narrative { get; init; }
}

public sealed record TransferResponse
{
    public required Guid    Id       { get; init; }
    public required string  Status   { get; init; }
    public required decimal Amount   { get; init; }
    public required string  Currency { get; init; }
    public required DateTime RequestedAtUtc { get; init; }

    /// <summary>False while the transfer is still moving through the saga.
    /// The client polls or listens until this is true.</summary>
    public required bool IsFinal { get; init; }

    public static TransferResponse From(Transfer t) => new()
    {
        Id             = t.Id,
        Status         = t.Status.ToString(),
        Amount         = t.Amount,
        Currency       = t.Currency,
        RequestedAtUtc = t.RequestedAtUtc,
        IsFinal        = t.Status is TransferStatus.Completed or TransferStatus.Rejected
    };
}
