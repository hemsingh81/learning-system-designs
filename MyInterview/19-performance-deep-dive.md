# 19 · Performance Deep Dive — Front-end, Backend, Database (12 questions)

[← Coding-Round Prep](18-coding-round-prep.md) · [Home](README.md) · [Next → AI-Assisted Development](20-ai-assisted-development.md)

Performance is where an architect earns trust. On the TCW reporting platform (A) the whole business promise is *"the report is on the desk before the US market opens"* — so slow is not a nice-to-have, slow is a missed deadline. This section is the questions I get asked about making things fast, answered with a real project story, the numbers, the tools I used, and the follow-ups.

> How I open any performance question: *"I never guess. I measure first, find the one bottleneck that matters, fix it, and measure again to prove it. Most 'performance work' fails because someone optimised the wrong thing."*

**The one rule I repeat:** measure → find the biggest bottleneck → fix that one → measure again. Front-end, backend, or database — the method never changes.

**Jump to:**
[Front-end](#front-end-performance) · [PF1 slow first load](#pf1--the-page-took-too-long-to-load-what-did-you-do) · [PF2 slow big table](#pf2--a-report-screen-with-thousands-of-rows-was-laggy) · [PF3 measuring FE](#pf3--how-do-you-measure-front-end-performance) · [PF4 too many API calls](#pf4--the-screen-was-making-too-many-api-calls)
[Backend](#backend-performance) · [PB1 slow API](#pb1--an-api-endpoint-was-slow-under-load) · [PB2 N+1](#pb2--the-classic-n1-you-hit-in-production) · [PB3 memory/GC](#pb3--the-etl-service-was-eating-memory) · [PB4 measuring BE](#pb4--how-do-you-find-a-backend-bottleneck)
[Database](#database-performance) · [PD1 slow query](#pd1--a-report-query-missed-the-deadline) · [PD2 indexing](#pd2--how-do-you-decide-what-to-index) · [PD3 locking/blocking](#pd3--the-database-was-blocking-under-load) · [PD4 scaling data](#pd4--how-do-you-keep-queries-fast-as-data-grows)
[Tools summary](#tools-that-help-me-and-how) · [Section index](#section-index)

---

# Front-end performance

## PF1 · The page took too long to load. What did you do?

**The story.** On the TCW React reporting screens (A), the first load of a report page felt slow — the user clicked, then waited, then finally saw data. The business feedback was simple: *"it feels heavy in the morning."*

**How I fixed it, in order.**

1. **Measured first.** I opened Chrome DevTools → Lighthouse and the Network tab. Two problems stood out: the initial JavaScript bundle was large, and the page waited for the whole data set before showing anything.
2. **Split the bundle.** I used **code-splitting** — React `lazy` + `Suspense` — so the browser only downloads the code for the screen the user actually opens, not the whole app up front.
   ```tsx
   const ReportScreen = React.lazy(() => import('./ReportScreen'));
   // wrapped in <Suspense fallback={<Spinner/>}> so it loads on demand
   ```
3. **Showed something immediately.** Instead of a blank screen until all data arrived, I rendered the layout and a loading skeleton straight away, then filled in the data — the four-state pattern from [F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen). Perceived speed improved even before the real speed did.
4. **Paged the data.** The screen no longer asked for everything — it asked for the first page and loaded more on scroll ([PF2](#pf2--a-report-screen-with-thousands-of-rows-was-laggy)).

**The result.** The page felt fast because the user saw the frame instantly and the first rows shortly after, and the smaller bundle downloaded quicker. The heavy-morning complaint went away.

**Lesson.** *"Front-end speed is two things: real speed (smaller bundle, less data) and perceived speed (show the frame and a skeleton at once). Fix both — users judge the wait they can see."*

**Tools I used and how they helped.**
- **Lighthouse** — gave me a score and named the exact problems (bundle size, largest paint), so I fixed facts, not feelings.
- **DevTools Network tab** — showed what downloaded and how big, so I could see the large bundle and slow requests.
- **Webpack/Vite bundle analyzer** — showed which libraries were bloating the bundle, so I could lazy-load or replace them.

**Follow-ups**
- *"What is code-splitting really doing?"* — It breaks one giant JavaScript file into smaller ones and only downloads each when needed. First load gets lighter.
- *"What is a skeleton screen?"* — A grey placeholder shaped like the content. It tells the user "data is coming" so the wait feels shorter, even though the data takes the same time.
- *"How do you stop the bundle growing again?"* — I set a bundle-size budget in CI — if a change makes the bundle too big, the build warns. Performance stays a rule, not a one-off cleanup.

---

## PF2 · A report screen with thousands of rows was laggy.

**The story.** One TCW report (A) could return several thousand positions. The React table rendered *every* row into the DOM. Scrolling stuttered and the browser tab used a lot of memory — because the browser was holding thousands of DOM nodes it did not need.

**How I fixed it.**

1. **Virtualised the list.** I only render the rows the user can actually see (plus a small buffer), using a windowing library (`react-window` / `@tanstack/react-virtual`). As the user scrolls, rows are recycled. A table of 5,000 rows now keeps maybe 30 in the DOM at a time.
   ```tsx
   // render only visible rows; the rest exist as a scroll area, not DOM nodes
   <FixedSizeList height={600} itemCount={rows.length} itemSize={36} width="100%">
     {({ index, style }) => <Row style={style} data={rows[index]} />}
   </FixedSizeList>
   ```
2. **Stopped needless re-renders.** I wrapped the row in `React.memo` and kept callback identities stable with `useCallback` ([R5](16-deepdive-react-typescript.md#r5--react-performance-memo-usememo-usecallback)), so scrolling did not re-render rows that had not changed.
3. **Paged from the server too.** For truly huge results, the API returns pages, so the browser never even receives 50,000 rows at once.

**The result.** Scrolling became smooth and memory dropped sharply, because the DOM went from thousands of nodes to a few dozen.

**Lesson.** *"The browser is slow when the DOM is huge, not when the array is huge. Virtualise — render only what is on screen — and the size of the data stops mattering."*

**Tools I used and how they helped.**
- **React DevTools Profiler** — showed which components re-rendered and how often, so I could see the row re-render storm and confirm `memo` fixed it.
- **DevTools Performance tab** — recorded the scroll and showed long "scripting" and "rendering" frames, proving the DOM size was the cost.
- **react-window / react-virtual** — the windowing library that does the recycling for me.

**Follow-ups**
- *"Why is a big DOM slow?"* — The browser has to lay out, paint and keep every node in memory. More nodes = more work on every scroll and update.
- *"When do you NOT virtualise?"* — Small lists (a few dozen rows). Virtualisation adds complexity; only pay it when the list is genuinely large.
- *"What about the initial sort/filter?"* — I do that on the server for big data, so the browser receives already-sorted pages and does less work.

---

## PF3 · How do you measure front-end performance?

**The story.** I do not trust "it feels fast." On the reporting screens (A) I set real targets and measured them, so I could prove improvement to the business.

**How I measure.** I use the **Core Web Vitals** — Google's user-focused metrics — as my language:

- **LCP (Largest Contentful Paint)** — how fast the main content appears. Target under ~2.5s.
- **INP (Interaction to Next Paint)** — how fast the page responds to a click/typing. Target under ~200ms.
- **CLS (Cumulative Layout Shift)** — how much the page jumps around while loading. Should be tiny.

I measure them two ways: **in the lab** (Lighthouse in DevTools, on a throttled connection so I see what a real user on slower internet sees) and **in the field** (real-user monitoring — Application Insights browser SDK / `web-vitals` library sending real user timings back). Lab tells me *why* it is slow; field tells me *whether real users are actually slow*.

**The result.** Instead of arguing about feelings, I could say "LCP was 4.1s, it is now 1.9s" — a number the business understood.

**Lesson.** *"If I cannot put a number on it, I cannot improve it or prove I improved it. Core Web Vitals give me the user's language for speed."*

**Tools I used and how they helped.**
- **Lighthouse** — lab scores and specific fixes, on a simulated slow device/network.
- **`web-vitals` library + Application Insights** — collects real users' LCP/INP/CLS, so I see actual experience, not just my fast laptop.
- **DevTools Performance + Network** — the deep view of *why* a metric is bad (big image, blocking script, slow API).

**Follow-ups**
- *"Lab vs field — why both?"* — Lab is repeatable and shows the cause; field is real and shows who is actually affected. I need both.
- *"What is throttling?"* — Deliberately simulating a slower CPU/network so I test the experience of a real user, not my fast dev machine.
- *"One metric to watch?"* — For a data app, INP — responsiveness after a click — because users click, filter and sort constantly.

---

## PF4 · The screen was making too many API calls.

**The story.** A dashboard screen (A) called several APIs on load, some repeatedly as the user changed filters. It felt sluggish and hammered the backend — the same data was being fetched again and again.

**How I fixed it.**

1. **Cached server data properly.** I moved data fetching to **React Query** ([F6](14-fullstack-hands-on.md#f6--how-do-you-handle-state-and-data-fetching-in-react)). It caches responses, dedupes identical in-flight requests, and only refetches when the data is stale. Switching back to a filter I already viewed became instant — served from cache.
2. **Debounced the filters.** When a user typed in a search box, I waited until they stopped typing (debounce) before calling the API — so five keystrokes made one call, not five.
3. **Cancelled stale requests.** Using `AbortController` ([R4](16-deepdive-react-typescript.md#r4--useeffect-done-right)), if the user changed the filter mid-request, the old request was cancelled so a late response could not overwrite the new one.

**The result.** Far fewer API calls, a snappier screen, and less load on the backend — one fix helped both tiers at once.

**Lesson.** *"Treat server data as a cache, not something to re-fetch every render. Cache it, dedupe it, debounce the triggers — the fastest API call is the one you did not need to make."*

**Tools I used and how they helped.**
- **React Query** — the caching, deduping and stale-tracking, so I did not hand-roll it.
- **DevTools Network tab** — showed the flood of duplicate calls, which is how I spotted the problem in the first place.

**Follow-ups**
- *"Debounce vs throttle?"* — Debounce waits until activity stops (good for search typing); throttle limits calls to once per interval (good for scroll/resize).
- *"How long do you cache?"* — As long as the data is safe to reuse. Immutable data (a past-dated report) caches long; live data caches briefly or not at all.
- *"Does caching risk stale data?"* — Yes, so I set sensible staleness and invalidate on the events that change the data. Caching without an invalidation plan is a bug.

---

# Backend performance

## PB1 · An API endpoint was slow under load.

**The story.** On the TCW Web API (A), one reporting endpoint was fine for one user but slowed badly when many report jobs and users hit it together. Response times climbed under load.

**How I fixed it, in order.**

1. **Measured the endpoint.** I used Application Insights to see the endpoint's response time and its dependency calls. Most of the time was spent waiting on the database — not in C# code.
2. **Made it async all the way.** Some calls were blocking a thread while waiting on I/O. I made the path fully async ([F2](14-fullstack-hands-on.md#f2--how-do-you-write-correct-async-c)) so a waiting request frees its thread for another request. Under load, the server handled far more concurrent requests with the same threads.
3. **Cached the expensive, stable results.** A report for a past as-of date never changes, so I cached it ([D7](15-deepdive-dotnet.md#d7--caching-that-actually-helps)). Repeat requests for the same report skipped the database entirely.
4. **Pushed the slow query down to the DB team of one — me.** The remaining cost was one query, which I tuned ([PD1](#pd1--a-report-query-missed-the-deadline)).

**The result.** The endpoint stayed fast under concurrent load, because it was no longer blocking threads and no longer re-computing the same report.

**Lesson.** *"Under load, the enemy is usually blocked threads and repeated work. Async frees the threads; caching removes the repeated work; and the last mile is almost always one slow query."*

**Tools I used and how they helped.**
- **Application Insights (APM)** — showed exactly where the time went (app vs database vs external call), so I fixed the real bottleneck.
- **Load testing (k6 / Azure Load Testing)** — I reproduced "many users at once" safely, so I could prove the fix under the same load, not just on my machine.
- **`dotnet-counters` / `dotnet-trace`** — live look at thread pool and CPU to confirm the threads were the problem, then that they were fixed.

**Follow-ups**
- *"Why does async help under load specifically?"* — A blocked thread waiting on the database does nothing useful. Async gives that thread back to serve another request, so a fixed number of threads serves many more users.
- *"How did you know it was the DB, not the code?"* — The APM trace showed most time in the dependency (SQL) call, not in CPU. That points the finger before I touch anything.
- *"Vertical or horizontal scaling?"* — First I make one instance efficient (async, caching, query). Then if needed I scale out (more instances behind the load balancer). Fixing the code first means I do not pay to run slow code on more servers.

---

## PB2 · The classic N+1 you hit in production.

**The story.** A screen listing portfolios with their positions was slow. When I looked at the database calls, the API was running **one query for the list, then one more query per row** to load each portfolio's positions — 50 portfolios meant 51 queries. This is the N+1 problem.

**How I fixed it.**

1. **Saw it in the trace.** Application Insights showed a burst of near-identical small queries — the tell-tale sign of N+1.
2. **Fetched in one query.** Instead of lazy-loading per row, I loaded the data in a single query and projected exactly the columns the screen needs into a DTO ([F3](14-fullstack-hands-on.md#f3--entity-framework-or-dapper-show-me)).
   ```csharp
   // one query, projected to a DTO — no per-row round trips
   var rows = await _db.Portfolios
       .Select(p => new PortfolioRow {
           Id = p.Id, Name = p.Name, PositionCount = p.Positions.Count })
       .ToListAsync(ct);
   ```
3. **Disabled lazy loading** where it was hiding these round trips, so the pattern could not silently come back.

**The result.** 51 queries became 1. The screen loaded quickly and the database load dropped, because chatty round trips were replaced by one efficient query.

**Lesson.** *"One screen firing fifty queries is an N+1. The fix is almost always: load it in one query and project to exactly what the screen needs. Chatty is slow — even when each query is tiny."*

**Tools I used and how they helped.**
- **Application Insights / SQL Profiler** — made the invisible visible: a wall of repeated queries I would never see by reading code.
- **EF Core query logging** — shows the exact SQL EF generates, so I could confirm the N+1 and confirm the single-query fix.

**Follow-ups**
- *"Why is N+1 so common?"* — ORMs make lazy loading easy and invisible. The code looks innocent (`portfolio.Positions`), but each access is a hidden query.
- *"`Include` vs projection?"* — `Include` loads whole related entities; projecting to a DTO loads only the fields I need — usually faster and lighter for a screen.
- *"How do you prevent it?"* — Log SQL in development, review generated queries, and prefer explicit projections over lazy navigation.

---

## PB3 · The ETL service was eating memory.

**The story.** A FastAPI/Python ETL service (A) that ingests Aladdin data used a lot of memory on big runs. It loaded the entire data set into memory, transformed it, then loaded it — which does not scale as the data grows.

**How I fixed it.**

1. **Streamed instead of loading all at once.** I processed the data in **chunks/batches** rather than one giant in-memory structure — read a batch, transform it, load it, release it. Memory stayed flat regardless of total size.
2. **Vectorised the transform.** I replaced row-by-row Python loops with vectorised Pandas operations ([P3](17-deepdive-python-data.md#p3--pandas-transform-vectorised)) — faster and less wasteful.
3. **Pushed heavy aggregation into the database.** Some work I was doing in Python was cheaper as a set-based SQL query, so I let the database do it and only brought back the result.
4. **On the .NET side, the same instinct** — for hot parsing loops I reduced per-row allocations with `Span`/`StringBuilder` ([D4](15-deepdive-dotnet.md#d4--allocations-gc-and-span)) so the garbage collector had less to clean up.

**The result.** Memory use became flat and predictable instead of growing with the data, so the service could handle larger loads on the same machine — and inside the daily window.

**Lesson.** *"Never load the whole world into memory when you can stream it. Process in batches, push aggregation to the database, and the size of the data stops being a memory problem."*

**Tools I used and how they helped.**
- **Python memory profiler (`memray` / `tracemalloc`)** — showed where memory was held, so I fixed the real hot spot, not a guess.
- **`dotnet-counters` / a memory profiler (for .NET paths)** — showed GC pressure and allocations per second, confirming the `Span` fix reduced them.
- **Database (SQL/Snowflake)** — the best tool for aggregation at volume; moving work there removed memory pressure from the app entirely.

**Follow-ups**
- *"What is streaming/chunking?"* — Processing a little at a time and releasing it, instead of holding everything. Memory stays low no matter how big the total is.
- *"When keep it in memory?"* — When the data is small and fits comfortably — then in-memory is simplest and fastest. I only stream when size demands it.
- *"Why push work to the database?"* — Databases are built to aggregate large data efficiently and close to where it lives. Pulling millions of rows into the app to sum them is wasteful.

---

## PB4 · How do you find a backend bottleneck?

**The story.** When something is slow, I do not read the whole codebase hoping to spot it. I follow a fixed method that has never let me down across A, C and D.

**My method.**

1. **Reproduce and measure.** Get the slow case to happen and put a number on it. If I cannot measure it, I cannot fix it.
2. **Look at the trace, not the code.** Application Insights (or logs with a correlation ID, [F12](14-fullstack-hands-on.md#f12--walk-me-through-debugging-a-production-issue-in-code)) shows where the time goes: app CPU, database, or an external call. This instantly narrows the search.
3. **Split the time in half.** Is the time in my code or waiting on something? If waiting → database or external API. If CPU → my code. This halving finds the culprit fast.
4. **Fix the one biggest thing.** There is usually one dominant cost. Fix that, then measure again — the ranking often changes.
5. **Prove it with a load test.** Re-run the load test to show the fix holds under the same pressure.

**The result.** I fix the right thing first, quickly, with evidence — instead of scattering micro-optimisations that do not move the number.

**Lesson.** *"Performance is detective work, not guesswork. Measure, follow the trace, split the time in half, fix the biggest cost, prove it. The tools point at the culprit — I just have to look."*

**Tools I used and how they helped.**
- **Application Insights / OpenTelemetry** — distributed tracing across front-end → API → database, so I see the whole request's time broken down.
- **k6 / Azure Load Testing** — reproduces real load so bottlenecks that only appear under concurrency actually show up.
- **`dotnet-trace` / `dotnet-counters`** — low-level CPU, GC and thread-pool view when the problem is inside the .NET process.

**Follow-ups**
- *"What is distributed tracing?"* — A single request gets an ID that follows it across every service, so I can see the full journey and where the time was spent.
- *"Most common backend bottleneck?"* — The database — a slow query or too many round trips. That is why I always check the DB dependency time first.
- *"Premature optimisation?"* — Optimising before measuring. I refuse to — it wastes effort and often makes code harder to read for no gain.

---

# Database performance

## PD1 · A report query missed the deadline.

**The story.** On TCW (A) the whole promise is the pre-market deadline. One reporting query grew slow as data volume rose and threatened the window. This is the query where the business impact is real — slow means a late report.

**How I fixed it, in order.**

1. **Read the execution plan.** I looked at the actual plan in SQL Server Management Studio. It showed a **table scan** — the database was reading the whole table instead of jumping to the rows it needed.
2. **Made the query sargable.** The `WHERE` clause wrapped a function around the date column, which disables the index. I rewrote it as a plain range so the index could be used ([P5](17-deepdive-python-data.md#p5--sql-tuning-and-sargability)).
   ```sql
   -- BAD: function on the column → full scan
   WHERE CONVERT(date, trade_time) = @asOf
   -- GOOD: bare column range → index seek
   WHERE trade_time >= @asOf AND trade_time < DATEADD(day, 1, @asOf)
   ```
3. **Selected only needed columns**, so the query moved less data.
4. **Rewrote a per-row calculation** as a single-pass window function instead of a correlated subquery running once per row.
5. **Added a covering index** — deliberately — so the query got everything from the index without touching the table.

**The result.** The scan became a seek and the query returned well inside the window. The deadline was safe again.

**Lesson.** *"The deadline usually lives in one query. Read the plan first — a table scan or a function around an indexed column is nearly always the cause — and fix the query before you touch hardware."*

**Tools I used and how they helped.**
- **SQL Server execution plan (SSMS)** — the single most useful tool: it shows exactly *how* the database ran the query (seek vs scan) and where the cost is.
- **Query Store** — tracks query performance over time, so I can see which query regressed and when.
- **SQL Server Profiler / Extended Events** — captures the actual slow queries hitting the server in production.

**Follow-ups**
- *"Scan vs seek?"* — A scan reads the whole table; a seek jumps straight to the rows via an index. Turning a scan into a seek is the biggest common win.
- *"What is sargable?"* — A predicate the index can use. Wrap a function around the indexed column and it stops being sargable — so keep the column bare.
- *"Why read the plan first?"* — It tells me the truth about what the database did, so I fix the real cause instead of adding indexes at random.

---

## PD2 · How do you decide what to index?

**The story.** Indexes make reads fast but slow down writes and use storage — so I add them deliberately, not everywhere. On A, with a read-heavy reporting workload, the right indexes were worth a lot; the wrong ones just slowed the nightly load.

**How I decide.**

1. **Index what you filter and join on.** Columns in `WHERE`, `JOIN` and `ORDER BY` are the candidates — those are what the database searches by.
2. **Use covering indexes for hot queries.** If one query runs constantly, an index that *includes* all its columns lets it answer entirely from the index, never touching the table.
3. **Watch the write cost.** Every index must be updated on every insert/update. On a write-heavy table I keep indexes lean; on a read-heavy reporting table I can afford more.
4. **Let the tools suggest, but I decide.** SQL Server's missing-index hints and Database Engine Tuning Advisor propose indexes — I treat them as suggestions and validate with the execution plan, because blindly adding every suggestion bloats writes.

**The result.** Reads that matter got fast; the nightly load stayed fast because I did not over-index. It is a balance, chosen per table by its read/write pattern.

**Lesson.** *"Indexes are a trade: faster reads for slower writes and more storage. Index what you filter and join on, cover the hot queries, and never add an index the tool suggests without checking the plan."*

**Tools I used and how they helped.**
- **Execution plan missing-index hints** — point at columns that would help a specific slow query.
- **Database Engine Tuning Advisor** — analyses a workload and suggests indexes; useful as a starting list, not a final answer.
- **Query Store / DMVs** — show which queries are expensive and how often they run, so I index the ones that actually matter.

**Follow-ups**
- *"Clustered vs non-clustered?"* — Clustered is the physical row order (one per table); non-clustered is a separate lookup structure (many allowed). I choose the clustered key carefully because everything hangs off it.
- *"Can too many indexes hurt?"* — Yes — they slow every write and waste storage, and the optimiser can even pick a worse one. Lean and deliberate beats many.
- *"Composite index column order?"* — Most selective / most-filtered column first, matching how queries filter — order matters for whether the index gets used.

---

## PD3 · The database was blocking under load.

**The story.** During the nightly load on A, reporting reads and the ingestion writes sometimes fought each other — one held locks the other was waiting for, so queries queued and slowed. This is blocking (and its worst form, deadlock).

**How I fixed it.**

1. **Found the blocking chain.** I used DMVs and Extended Events to see which session was blocking which — who held the lock and who waited.
2. **Shortened transactions.** Long transactions hold locks longer. I kept each transaction small and quick — do the minimum, commit, release the locks fast ([P4](17-deepdive-python-data.md#p4--idempotent-loads-and-reconciliation)).
3. **Separated read and write workloads.** Heavy analytical reads go to Snowflake / a read replica, while SQL Server handles the operational writes — the operational/analytical split ([P6](17-deepdive-python-data.md#p6--snowflake-vs-sql-server)). Reads and writes stopped competing.
4. **Used the right isolation.** For reports that can tolerate a consistent snapshot, snapshot isolation lets readers not block writers.

**The result.** The load and the reads stopped fighting, so both ran predictably during the window.

**Lesson.** *"Blocking is two operations wanting the same rows at the same time. Keep transactions short, separate heavy reads from writes, and pick the isolation level on purpose — then locks stop being a traffic jam."*

**Tools I used and how they helped.**
- **DMVs (`sys.dm_exec_requests`, `sys.dm_tran_locks`)** — show live blocking chains: who is waiting on whom.
- **Extended Events / deadlock graph** — captures the exact deadlock, showing both sides so I can fix the cause.
- **Query Store** — shows when waits spiked, tying blocking to a time and a query.

**Follow-ups**
- *"Blocking vs deadlock?"* — Blocking is one waiting for another to finish. Deadlock is two waiting on each other forever — the database kills one. Both come from lock contention.
- *"How do you avoid deadlocks?"* — Access tables in a consistent order everywhere, keep transactions short, and retry the victim (deadlocks are often transient).
- *"What is snapshot isolation?"* — Readers see a consistent snapshot without taking locks that block writers — great for reporting reads alongside writes.

---

## PD4 · How do you keep queries fast as data grows?

**The story.** Financial history only grows. A query that was fast on one year of data can crawl on five. On A I designed for growth so the deadline held as volume rose.

**How I keep it fast at scale.**

1. **Partition big tables.** Splitting a huge table by date lets a query for one day read only that partition, not the whole history — "partition pruning."
2. **Archive cold data.** Old data that is rarely queried moves to cheaper storage or the analytical store, keeping the operational tables lean.
3. **Pre-aggregate for reporting.** For dashboards, I precompute summaries (materialised/indexed views or a nightly rollup) so the screen reads a small summary, not millions of raw rows.
4. **Use the right store for the job.** Heavy historical analytics live in Snowflake (columnar, built for big scans); operational reads stay in SQL Server ([P6](17-deepdive-python-data.md#p6--snowflake-vs-sql-server)).
5. **Test with realistic volumes.** I test on data sizes like production, not tiny dev data — so a scaling problem shows up before go-live, not after.

**The result.** Queries stayed fast as the data grew, because each query touches only the slice it needs and heavy work lives where it belongs.

**Lesson.** *"Fast today is not fast forever. Partition by date so queries read one slice, pre-aggregate for dashboards, archive cold data, and put big analytics in a columnar store. Design for the data you will have, not the data you have now."*

**Tools I used and how they helped.**
- **Table partitioning (SQL Server) / clustering (Snowflake)** — lets queries prune to the relevant slice instead of scanning everything.
- **Materialised / indexed views** — precompute expensive aggregates so reports read a small, ready answer.
- **Query Store** — shows a query slowly regressing as data grows, so I act before it breaks the deadline.

**Follow-ups**
- *"What is partition pruning?"* — The database skips partitions that cannot match the filter, so a one-day query ignores years of other data.
- *"Materialised view trade-off?"* — Reads get very fast, but the summary must be refreshed — so it fits data that updates on a schedule, like daily reporting.
- *"When to shard?"* — Only when one database genuinely cannot cope. It adds a lot of complexity, so partitioning, archiving and the right store come first.

---

## Tools that help me, and how

A quick recall table — the tool, and the one job it does for me.

| Layer | Tool | How it helps performance |
|---|---|---|
| Front-end | **Lighthouse** | Scores the page and names the exact problems (bundle, LCP) |
| Front-end | **DevTools Network / Performance** | Shows what downloads and what makes frames slow |
| Front-end | **React DevTools Profiler** | Shows needless re-renders so I can memoize the right thing |
| Front-end | **Bundle analyzer** | Shows which libraries bloat the JS bundle |
| Front-end | **web-vitals + App Insights (RUM)** | Real users' LCP/INP/CLS from the field, not my laptop |
| Front-end | **React Query** | Caches/dedupes server data so I make fewer API calls |
| Front-end | **react-window / react-virtual** | Renders only visible rows so big tables stay smooth |
| Backend | **Application Insights / OpenTelemetry** | Traces a request across tiers; shows where time goes |
| Backend | **k6 / Azure Load Testing** | Reproduces real concurrent load so bottlenecks appear |
| Backend | **dotnet-trace / dotnet-counters** | CPU, GC and thread-pool view inside the .NET process |
| Backend | **memray / tracemalloc** | Finds where Python memory is held |
| Database | **Execution plan (SSMS)** | Shows seek vs scan and the real cost — my first stop |
| Database | **Query Store** | Tracks query performance over time; catches regressions |
| Database | **Profiler / Extended Events** | Captures the actual slow or deadlocking queries in prod |
| Database | **DMVs** | Live blocking chains and expensive-query stats |
| Database | **Tuning Advisor / missing-index hints** | Suggests indexes (I validate before applying) |

---

## Section index

| # | Question | Core message |
|---|---|---|
| PF1 | Slow first page load | Smaller bundle (code-split) + show the frame/skeleton at once |
| PF2 | Laggy big table | Virtualise — render only visible rows; the DOM size is the cost |
| PF3 | Measuring front-end | Core Web Vitals (LCP/INP/CLS), lab + field; put a number on it |
| PF4 | Too many API calls | Cache (React Query), debounce, cancel stale — fewer calls |
| PB1 | Slow API under load | Async frees threads; cache stable results; tune the last query |
| PB2 | N+1 in production | 51 queries → 1; load in one query, project to a DTO |
| PB3 | ETL eating memory | Stream in batches; push aggregation to the DB; reduce allocations |
| PB4 | Finding a bottleneck | Measure, follow the trace, split time in half, fix biggest, prove it |
| PD1 | Query missed deadline | Read the plan; make it sargable (seek not scan); covering index |
| PD2 | What to index | Index filters/joins; cover hot queries; mind the write cost |
| PD3 | Blocking under load | Short transactions; split read/write; pick isolation on purpose |
| PD4 | Fast as data grows | Partition by date, pre-aggregate, archive, right store for the job |

---

[← Coding-Round Prep](18-coding-round-prep.md) · [Home](README.md) · [Next → AI-Assisted Development](20-ai-assisted-development.md)
