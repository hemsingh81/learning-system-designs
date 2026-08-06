# 14 · Full-Stack Hands-On (12 questions)

[← Reproduce Prompt](13-reproduce-prompt.md) · [Home](README.md) · [Next → Deep Dive: .NET & C#](15-deepdive-dotnet.md)

I am an architect who still writes production code. On every project I designed, I also **built** — React and Angular screens, ASP.NET Core Web APIs in C#, Python/FastAPI ETL services, and the SQL underneath. This section is for the interviews where they open the hood and ask me to go deep and to write code. Every answer here is hands-on, first person, with real code from my actual stack.

> The one line I open a technical-depth interview with: *"I design top-down and I still build bottom-up. Nineteen years of writing C#, SQL, JavaScript and Python is exactly why my architecture survives contact with the code."*

**Jump to:** [F1 Web API](#f1--build-a-clean-aspnet-core-web-api-endpoint) · [F2 Async C#](#f2--how-do-you-write-correct-async-c) · [F3 EF vs Dapper](#f3--entity-framework-or-dapper-show-me) · [F4 FastAPI ETL](#f4--write-a-fastapi-etl-ingestion-endpoint) · [F5 React](#f5--build-a-react-data-screen) · [F6 State & data fetching](#f6--how-do-you-handle-state-and-data-fetching-in-react) · [F7 Angular](#f7--you-also-used-angular--show-me) · [F8 SQL you write](#f8--write-the-sql-not-just-design-it) · [F9 Auth end-to-end](#f9--wire-up-auth-across-the-stack) · [F10 Error handling](#f10--how-do-you-handle-errors-across-the-stack) · [F11 Testing](#f11--how-do-you-test-what-you-build) · [F12 Debugging](#f12--walk-me-through-debugging-a-production-issue-in-code) · [Section index](#section-index)

---

## F1 · Build a clean ASP.NET Core Web API endpoint.

**What they are testing.** Whether I actually write the API layer I design. On the TCW reporting platform (A) I defined the reusable controller + Web API pattern *and* wrote it.

**How I answer.** I keep controllers thin, push logic into a service, validate at the edge, and return the right status codes. Here is the shape I actually use.

```csharp
[ApiController]
[Route("api/reports")]
public class ReportsController : ControllerBase
{
    private readonly IReportService _reports;
    public ReportsController(IReportService reports) => _reports = reports;

    // GET api/reports/emerging-markets?asOf=2026-08-06
    [HttpGet("{reportType}")]
    [ProducesResponseType(typeof(ReportDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ReportDto>> Get(
        string reportType, [FromQuery] DateOnly asOf, CancellationToken ct)
    {
        var report = await _reports.GetAsync(reportType, asOf, ct);
        return report is null ? NotFound() : Ok(report);
    }
}
```

The controller does three things only: bind input, call the service, map the result to a status code. Business rules live in `IReportService`, so the same logic is testable without HTTP and reusable by a background job. I pass `CancellationToken` all the way down so a client that gives up does not leave work running against SQL — which matters when a report has a deadline.

**Lesson.** *"A controller is a translator between HTTP and my domain, nothing more. The moment business logic leaks into a controller, it stops being testable and stops being reusable."*

**Follow-ups**
- *"Why the reusable pattern?"* — On A, every report used to be bespoke controller code. I standardised the controller + service + DTO shape so a new report is configuration and a service method, not a new hand-written stack. That is what shortened the build cycle.
- *"Where does validation go?"* — Model binding + data annotations or FluentValidation at the edge, so bad input never reaches the service. See [F10](#f10--how-do-you-handle-errors-across-the-stack).
- *"Minimal APIs or controllers?"* — Controllers when there is a real domain and a team; minimal APIs for a tiny service. On A the team and the reuse made controllers the right call.

---

## F2 · How do you write correct async C#?

**What they are testing.** Whether I understand async beyond sprinkling `async`/`await`. This bites people in production, and I have debugged it in production.

**How I answer.** Async in .NET is about not blocking a thread while waiting on I/O — a database call, an HTTP call to Aladdin, a file read. The rules I hold to:

```csharp
// GOOD: async all the way, token flowed, no blocking
public async Task<IReadOnlyList<Position>> GetPositionsAsync(
    string portfolioId, CancellationToken ct)
{
    // ConfigureAwait(false) in library code — no need to resume on a context
    return await _db.Positions
        .Where(p => p.PortfolioId == portfolioId)
        .ToListAsync(ct)
        .ConfigureAwait(false);
}
```

What I never do: `.Result` or `.Wait()` on an async call — that blocks a thread and can deadlock. I never mark a method `async void` except for event handlers, because exceptions in `async void` cannot be caught. And I flow `CancellationToken` everywhere so a cancelled request actually stops.

For calling the Aladdin API across many entities, I do not fire them all at once — the API has rate limits. I bound the concurrency:

```csharp
using var throttle = new SemaphoreSlim(4); // max 4 concurrent calls
var tasks = entityTypes.Select(async type =>
{
    await throttle.WaitAsync(ct);
    try { return await _aladdin.FetchAsync(type, ct); }
    finally { throttle.Release(); }
});
var results = await Task.WhenAll(tasks);
```

**Lesson.** *"Async is about freeing the thread during I/O, not about speed. The two things that hurt in production are blocking on `.Result` and unbounded parallelism against a rate-limited API."*

**Follow-ups**
- *"When does async not help?"* — CPU-bound work. Async is for I/O waits; for CPU work I would use `Task.Run` deliberately, or parallelism, not `async`.
- *"What is a deadlock cause?"* — Blocking on async in a context that needs the same thread to resume. Async-all-the-way avoids it.
- *"How do you cancel a slow load?"* — The `CancellationToken` is honoured by EF and `HttpClient`, so cancelling propagates down to the query and the socket.

---

## F3 · Entity Framework or Dapper? Show me.

**What they are testing.** Whether I choose data access deliberately. I have shipped both — EF Core and ADO.NET/raw SQL.

**How I answer.** EF Core for the domain-shaped CRUD and change tracking; hand-tuned SQL (Dapper or ADO.NET) for the hot reporting reads where I need full control of the plan.

```csharp
// EF Core — readable, tracked, good for writes and domain reads
var portfolio = await _db.Portfolios
    .Include(p => p.Positions)
    .FirstOrDefaultAsync(p => p.Id == id, ct);

// Dapper — for a hot report read where I own the exact SQL and shape
const string sql = @"
    SELECT p.Ticker, p.Quantity, p.MarketValue
    FROM   dbo.ReportPosition p
    WHERE  p.PortfolioId = @PortfolioId AND p.AsOf = @AsOf";
var rows = await conn.QueryAsync<PositionRow>(
    new CommandDefinition(sql, new { PortfolioId = id, AsOf = asOf }, cancellationToken: ct));
```

The reason I split them: EF is fantastic for productivity and safety on writes, but for a deadline-driven report I want to read the execution plan and control exactly what SQL runs — no surprise N+1, no over-fetching. On A, the reporting reads are where the deadline lives, so those get hand-written SQL; everything else is EF.

**The N+1 trap I always check for:**

```csharp
// BAD: one query per portfolio — N+1
foreach (var p in portfolios)
    p.Positions = await _db.Positions.Where(x => x.PortfolioId == p.Id).ToListAsync();

// GOOD: one query, projected to exactly what the screen needs
var data = await _db.Portfolios
    .Select(p => new PortfolioDto {
        Id = p.Id,
        PositionCount = p.Positions.Count
    }).ToListAsync(ct);
```

**Lesson.** *"EF for the domain and the writes, hand-tuned SQL for the hot reads on a deadline. And always project to a DTO — never pull whole entities to fill a screen that needs three columns."*

**Follow-ups**
- *"How do you find an N+1?"* — Log the generated SQL in dev, or watch the query count. One screen firing 50 queries is the tell.
- *"AsNoTracking?"* — Yes, for read-only queries — it skips change-tracking overhead, which matters on large reporting reads.
- *"Migrations?"* — EF migrations for the app schema; and on A the DB utility generator standardises script generation so schema change → release is one repeatable path.

---

## F4 · Write a FastAPI ETL ingestion endpoint.

**What they are testing.** My Python/FastAPI hands-on side — the ETL services I actually built to ingest Aladdin data (A).

**How I answer.** The FastAPI services I built ingest portfolio, position and transaction data with validation, retry and reconciliation. Here is the shape.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

app = FastAPI()

class Position(BaseModel):
    portfolio_id: str
    ticker: str
    quantity: float
    market_value: float

    @field_validator("market_value")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("market_value cannot be negative")
        return v

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_from_aladdin(entity: str, as_of: str) -> list[dict]:
    # calls the Aladdin API; retried with backoff on transient failure
    ...

@app.post("/ingest/positions")
async def ingest_positions(as_of: str):
    raw = await fetch_from_aladdin("positions", as_of)
    validated = [Position(**row) for row in raw]          # validation
    loaded = await load_to_sql_and_snowflake(validated)   # dual store
    if not reconcile(source=len(raw), loaded=loaded):     # reconciliation
        raise HTTPException(500, "reconciliation mismatch")
    return {"as_of": as_of, "ingested": loaded}
```

Three things make this production-grade, not a demo: **Pydantic validation** so a bad row is rejected at the door; **tenacity retry with exponential backoff** so a transient Aladdin blip does not fail the run; and a **reconciliation check** so a partial load is caught before it ever reaches a report. That is the "prove the data is right, before the deadline" principle in code.

**Lesson.** *"An ETL endpoint without validation, retry and reconciliation is a data-corruption incident waiting to happen. Those three are not extras — they are the point."*

**Follow-ups**
- *"Why FastAPI over Flask?"* — Async I/O, Pydantic validation built in, and auto OpenAPI docs. For an ETL service hitting a slow external API, the async model matters.
- *"Where does orchestration fit?"* — The endpoint does the work; ADF/Tidal/Airflow decide *when* and in what dependency order. I keep the service dumb about scheduling.
- *"Idempotency?"* — Ingestion is keyed on entity + as-of, so re-running a load replaces rather than duplicates — essential for a safe retry.

---

## F5 · Build a React data screen.

**What they are testing.** My front-end hands-on. I built the React reporting screens on A.

**How I answer.** A reporting screen is: fetch, handle loading/error/empty, render, and keep it accessible. A clean functional component with a custom hook for the data.

```tsx
function useReport(reportType: string, asOf: string) {
  const [state, setState] = useState<{ data?: ReportRow[]; error?: string; loading: boolean }>({ loading: true });

  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true });
    fetch(`/api/reports/${reportType}?asOf=${asOf}`, { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error(`Report failed: ${r.status}`); return r.json(); })
      .then(data => setState({ data, loading: false }))
      .catch(err => { if (err.name !== 'AbortError') setState({ error: err.message, loading: false }); });
    return () => controller.abort(); // cancel on unmount / param change
  }, [reportType, asOf]);

  return state;
}

function ReportScreen({ reportType, asOf }: { reportType: string; asOf: string }) {
  const { data, error, loading } = useReport(reportType, asOf);

  if (loading) return <Spinner aria-label="Loading report" />;
  if (error)   return <ErrorBanner message={error} />;
  if (!data?.length) return <EmptyState message="No positions for this date." />;

  return (
    <table>
      <caption>{reportType} — as of {asOf}</caption>
      <thead><tr><th>Ticker</th><th>Quantity</th><th>Market value</th></tr></thead>
      <tbody>
        {data.map(row => (
          <tr key={row.ticker}>
            <td>{row.ticker}</td><td>{row.quantity}</td><td>{formatCurrency(row.marketValue)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

The four states — loading, error, empty, data — are all handled explicitly, because a reporting screen that silently shows nothing on error is worse than one that says "failed". The `AbortController` cancels the fetch if the user changes the date before it returns, which prevents a stale response overwriting a newer one.

**Lesson.** *"A data screen is four states, not one. Loading, error, empty and data all need a deliberate render — skipping empty and error is the most common front-end bug I fix."*

**Follow-ups**
- *"Why the AbortController?"* — Race conditions. Without it, an old slow request can land after a newer one and show stale data.
- *"Accessibility?"* — Semantic table with a caption, `aria-label` on the spinner, and real focus management. Regulated clients care, and it is just correct.
- *"Big tables?"* — Virtualise the rows and paginate/filter server-side. I do not render 50,000 DOM rows.

---

## F6 · How do you handle state and data fetching in React?

**What they are testing.** Whether I know when to reach for what — not cargo-culting Redux everywhere.

**How I answer.** I match the tool to the state's scope:

| State type | What I use |
|---|---|
| Local UI (open/closed, form input) | `useState` / `useReducer` |
| Server data (reports, lists) | A data-fetching library (React Query) or a custom hook with caching |
| Shared cross-tree app state (user, theme) | Context, or a light store (Zustand/Redux Toolkit) if it grows |

The mistake I have seen teams make is putting *server data* into Redux and then hand-writing caching, loading and invalidation. Server data is not app state — it is a cache of someone else's data. So I use a fetching library that gives me caching, background refresh and de-duplication for free:

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['report', reportType, asOf],
  queryFn: () => fetchReport(reportType, asOf),
  staleTime: 60_000, // report for a given as-of date does not change
});
```

Because a report for a fixed as-of date is immutable, I set a `staleTime` so React Query does not refetch it needlessly — that is a real performance win on a reporting app.

**Lesson.** *"Server data is a cache, not app state. Treat it as a cache and you delete most of your Redux and most of your bugs."*

**Follow-ups**
- *"Redux ever?"* — Yes, for genuinely shared, frequently-changing client state. Just not for server data.
- *"Prop drilling?"* — Context for a few levels; a store when it becomes a tangle. I do not reach for a store on day one.
- *"Knockout/AngularJS legacy?"* — I have worked in those (D, C). The concepts transfer — they were doing observables and two-way binding before hooks existed.

---

## F7 · You also used Angular — show me.

**What they are testing.** Breadth — I delivered Angular front ends on the completion platform (C).

**How I answer.** Angular's model is components + services + dependency injection + RxJS. The service holds the data access; the component subscribes. Here is the completion-platform shape.

```typescript
@Injectable({ providedIn: 'root' })
export class CompletionService {
  constructor(private http: HttpClient) {}

  getCertificates(area: string): Observable<Certificate[]> {
    return this.http.get<Certificate[]>(`/api/certificates?area=${area}`).pipe(
      retry(2),                          // transient retry
      catchError(() => of([]))           // fail soft to empty, banner elsewhere
    );
  }
}

@Component({
  selector: 'app-certificates',
  template: `
    <div *ngIf="certs$ | async as certs; else loading">
      <table><tr *ngFor="let c of certs">{{ c.tagNumber }} — {{ c.status }}</tr></table>
    </div>
    <ng-template #loading><app-spinner></app-spinner></ng-template>`
})
export class CertificatesComponent {
  certs$ = this.completion.getCertificates(this.area);
  constructor(private completion: CompletionService) {}
}
```

The `async` pipe subscribes and unsubscribes automatically, which avoids the classic Angular memory leak from manual subscriptions. DI makes the service trivially mockable in tests. On C, the front end had to make a genuinely complex approval workflow usable by commissioning engineers who were not software people — so the real work was UX and clarity, not the framework.

**Lesson.** *"Angular or React, the discipline is the same: data access in a service, components stay thin, and you always handle the failing and empty states. The framework is the smaller half of the job."*

**Follow-ups**
- *"Angular vs React preference?"* — React for flexibility and the ecosystem; Angular when a team wants a batteries-included, opinionated structure. I am productive in both.
- *"RxJS — comfortable?"* — Yes, for streams and cancellation. I do not over-use it — a simple HTTP call does not need five operators.
- *"jQuery/Knockout?"* — Delivered both (C, D, E). I can maintain legacy front ends and modernise them incrementally.

---

## F8 · Write the SQL, not just design it.

**What they are testing.** Real T-SQL skill — I tune slow queries in production (see [S4](07-support-post-delivery.md#s4--how-do-you-tune-a-slow-query-in-production)) and set the query standards on A.

**How I answer.** I write set-based SQL, I make predicates sargable so indexes get used, and I only pull what the report needs. A real reporting query, written to be fast:

```sql
-- Top holdings per portfolio, as-of a date, ranked — set-based, index-friendly
SELECT PortfolioId, Ticker, MarketValue
FROM (
    SELECT p.PortfolioId, p.Ticker, p.MarketValue,
           ROW_NUMBER() OVER (PARTITION BY p.PortfolioId
                              ORDER BY p.MarketValue DESC) AS rn
    FROM dbo.ReportPosition AS p
    WHERE p.AsOf = @AsOf          -- sargable: no function wrapping the column
) ranked
WHERE rn <= 10
ORDER BY PortfolioId, MarketValue DESC;
```

What makes it fast: a window function does the ranking in one pass instead of a correlated subquery per portfolio; `WHERE p.AsOf = @AsOf` keeps the column bare so an index on `(AsOf, PortfolioId, MarketValue)` can be used. The **non-sargable** version I always rewrite:

```sql
-- BAD: function on the column kills the index
WHERE CONVERT(date, p.AsOfDateTime) = @AsOf
-- GOOD: range predicate keeps the index usable
WHERE p.AsOfDateTime >= @AsOf AND p.AsOfDateTime < DATEADD(day, 1, @AsOf)
```

**Lesson.** *"Think in sets, keep predicates sargable, and select only the columns the report needs. Most 'slow SQL' is a function wrapped around an indexed column or a query pulling ten times what it displays."*

**Follow-ups**
- *"How do you find the slow part?"* — Actual execution plan and I/O stats — I look at where the reads and time actually go before I touch an index. Same method on Snowflake, different levers (clustering, pruning, warehouse size).
- *"Stored procs vs inline?"* — Procs for reusable, security-scoped, plan-stable logic; parameterised inline for simple reads. Never string-concatenated SQL — injection risk.
- *"CTE vs subquery vs temp table?"* — Readability first; temp table when I need to materialise and re-use a large intermediate result the optimiser keeps re-computing.

---

## F9 · Wire up auth across the stack.

**What they are testing.** Whether I can implement end-to-end security, not just name it. I use Entra ID (Azure AD) across apps.

**How I answer.** Token-based, with the API validating a JWT from Entra ID and the front end just carrying the token. The API side:

```csharp
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));

// endpoints require a valid token + a scope/role
[Authorize(Roles = "ReportViewer")]
[HttpGet("{reportType}")]
public Task<ActionResult<ReportDto>> Get(...) { ... }
```

The front end acquires the token via MSAL and attaches it — it never handles passwords:

```tsx
const token = await msalInstance.acquireTokenSilent({ scopes: ['api://reports/.default'] });
fetch('/api/reports/emerging-markets', {
  headers: { Authorization: `Bearer ${token.accessToken}` }
});
```

The principles I hold to: the token is validated server-side on every request (never trust the client), authorization is by role/scope at the endpoint, secrets live in Key Vault not config, and least privilege everywhere — a report viewer cannot hit an admin endpoint. In a regulated firm this is not optional; it is auditable.

**Lesson.** *"Authentication says who you are; authorization says what you may do — and both are enforced on the server, every request. The front end carries a token, it never makes a security decision."*

**Follow-ups**
- *"Where do you store the token client-side?"* — In memory via MSAL, not localStorage, to reduce XSS exposure.
- *"Service-to-service?"* — Managed identity / client-credentials flow, so no secret is passed around — the FastAPI ETL uses its own identity to reach Azure resources.
- *"Data residency?"* — Honoured in the architecture (region choices), because a clause committing to it is my problem to make true — see [R5](06-rfp-presales.md#r5--how-do-you-work-with-sales-commercial-and-legal).

---

## F10 · How do you handle errors across the stack?

**What they are testing.** Whether my error handling is consistent, not scattered `try/catch` everywhere.

**How I answer.** One place per layer. In ASP.NET Core I centralise with middleware so every unhandled error becomes a clean, consistent response — and never leaks a stack trace to the client.

```csharp
app.UseExceptionHandler(errApp => errApp.Run(async ctx =>
{
    var ex = ctx.Features.Get<IExceptionHandlerFeature>()?.Error;
    _logger.LogError(ex, "Unhandled error on {Path}", ctx.Request.Path);
    ctx.Response.StatusCode = ex switch
    {
        NotFoundException      => StatusCodes.Status404NotFound,
        ValidationException     => StatusCodes.Status400BadRequest,
        _                       => StatusCodes.Status500InternalServerError
    };
    await ctx.Response.WriteAsJsonAsync(new { error = SafeMessage(ex) });
}));
```

The rules: map domain exceptions to HTTP status codes in one place; log the full detail server-side with correlation; return a safe message to the client; and on the front end, show the four states ([F5](#f5--build-a-react-data-screen)) with a real error banner. For the ETL, an error is not just logged — it triggers the automated failure alerting and the runbook path ([S6](07-support-post-delivery.md#s6--how-do-you-do-knowledge-transfer-and-runbooks)).

**Lesson.** *"Handle errors in one place per layer, log the detail server-side, and show the user a safe, honest message. Scattered try/catch and leaked stack traces are the two smells I refactor first."*

**Follow-ups**
- *"Correlation IDs?"* — Yes — a request ID flows from front end to API to logs, so I can trace one user's failure across the stack. Essential for the [debugging](#f12--walk-me-through-debugging-a-production-issue-in-code) below.
- *"Retries vs fail-fast?"* — Retry transient (network, throttling) with backoff; fail fast on validation — retrying bad input just fails slower.
- *"Global front-end handling?"* — An error boundary in React so a component crash shows a fallback, not a white screen.

---

## F11 · How do you test what you build?

**What they are testing.** Whether I write tests, not just talk about them. I set and hold code-review and quality standards across teams.

**How I answer.** The pyramid: many fast unit tests, fewer integration tests, a thin layer of end-to-end. I test the service layer hard because that is where the logic lives.

```csharp
[Fact]
public async Task GetAsync_returns_null_when_report_missing()
{
    var repo = new Mock<IReportRepository>();
    repo.Setup(r => r.FindAsync("em", It.IsAny<DateOnly>(), default))
        .ReturnsAsync((Report?)null);
    var sut = new ReportService(repo.Object);

    var result = await sut.GetAsync("em", new DateOnly(2026, 8, 6), default);

    Assert.Null(result);   // arrange → act → assert
}
```

I mock the dependency, test one behaviour per test, and name the test so a failure reads like a sentence. On the Python side I use pytest with the same discipline — a test for the happy path and at least one for the edge (a negative market value gets rejected by the Pydantic validator). For the front end, React Testing Library on user behaviour ("shows the error banner when the API fails"), not implementation detail.

**Lesson.** *"Test the layer where the logic lives — the service — hardest, and always cover one edge case, not just the happy path. A test suite that only covers the happy path gives false confidence."*

**Follow-ups**
- *"Coverage target?"* — I care about covering the risky logic, not a vanity percentage. 100% coverage of getters proves nothing.
- *"AI-assisted tests?"* — I use GitHub Copilot to scaffold test boilerplate fast (I drove its adoption on the team), then I review every generated test — the assertion has to be *mine*, not the model's guess.
- *"Integration tests for the ETL?"* — Yes, against a test schema, asserting the reconciliation actually catches a deliberately broken load.

---

## F12 · Walk me through debugging a production issue in code.

**What they are testing.** How I actually chase a bug in code, hands-on, under pressure.

**How I answer.** A real one: a report intermittently showed a wrong total. Not down — wrong. Here is exactly how I worked it.

**Reproduce with the real inputs.** Intermittent means data-dependent. I found the specific portfolio + as-of date that reproduced it, so I was debugging a fact, not a rumour.

**Follow the correlation ID.** The request ID from the screen let me pull the exact API call and the exact SQL it ran from the logs. That pointed me at one query.

**Isolate the layer.** I ran that SQL directly — the total was correct in the database. So the bug was above SQL, in the C#. That single split (is the data wrong, or is the code wrong?) halves the search space instantly.

**Read the code with the data in hand.** The aggregation was summing a list that, for that portfolio, contained a duplicated position from a retry that had not been made idempotent. The retry ([F4](#f4--write-a-fastapi-etl-ingestion-endpoint)) re-inserted instead of replacing.

**Fix the class, not just the case.** I made the ingestion idempotent (keyed on entity + as-of), added a reconciliation assertion that would have caught the duplicate, and wrote a test with that exact data so it can never regress. Then an RCA note ([S3](07-support-post-delivery.md#s3--how-do-you-do-root-cause-analysis)) so the missing-idempotency lesson was captured.

**Lesson.** *"Debugging is a search. Reproduce it, then split the stack in half — is the data wrong or is the code wrong? — and keep halving. Then fix the class of bug with a test, not just the one instance."*

**Follow-ups**
- *"No correlation ID?"* — Then adding one is my first fix — you cannot debug distributed systems by guessing which log line belongs to which request.
- *"How do you debug the front end?"* — Network tab for the actual payload, React DevTools for state, and I check whether the API returned wrong data or the component rendered right data wrongly — same split.
- *"Debugging async issues?"* — The hardest kind. Logging with timestamps and correlation, and looking for the race — like the stale-response problem the [AbortController](#f5--build-a-react-data-screen) prevents.

---

## Section index

| # | Question | Core message |
|---|---|---|
| F1 | ASP.NET Core Web API | Thin controller, logic in a service, right status codes |
| F2 | Correct async C# | Free the thread on I/O; never block on `.Result`; bound concurrency |
| F3 | EF vs Dapper | EF for domain/writes, hand-tuned SQL for hot reads; kill N+1 |
| F4 | FastAPI ETL | Validation + retry + reconciliation are the point, not extras |
| F5 | React data screen | Four states: loading, error, empty, data — all deliberate |
| F6 | React state & fetching | Server data is a cache, not app state |
| F7 | Angular | Data in a service, thin components, handle failing states |
| F8 | Writing T-SQL | Set-based, sargable predicates, select only what you need |
| F9 | Auth across the stack | Validate the token server-side every request; least privilege |
| F10 | Error handling | One place per layer; log detail, return safe messages |
| F11 | Testing | Test the service hardest; always cover an edge case |
| F12 | Debugging in production | Reproduce, split the stack in half, fix the class with a test |

---

[← Reproduce Prompt](13-reproduce-prompt.md) · [Home](README.md) · [Next → Deep Dive: .NET & C#](15-deepdive-dotnet.md)
