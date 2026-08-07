# 61 · Concept: React Performance Tuning (30 questions)

[← Design Principles & Patterns](60-concept-design-principles.md) · [Home](README.md) · [Next → Angular Performance Tuning](62-concept-angular-performance.md)

This file explains **how I make React apps fast** — in simple English and real depth. I answer from project A, the TCW React reporting screens, where the promise is *"the report is on the desk before the US market opens"* — so slow is a missed deadline, not a nicety.

> Simple one-liner: *"React speed is two things — **real speed** (smaller bundle, less work, less data) and **perceived speed** (show the frame and a skeleton instantly). I always measure first, fix the one bottleneck that matters, then measure again."*

## Concepts first — the whole idea before the questions

**Why React apps get slow.** React is fast by default, but three things slow real apps: (1) **too much JavaScript** shipped and parsed up front (big bundle), (2) **too many or too large re-renders** (React re-computing UI that didn't change), and (3) **too much data** fetched or held in memory. Every fix below targets one of these.

**The mental model — how React renders.** When state/props change, React **re-renders** a component (runs its function), builds a new virtual DOM, **diffs** it against the old one, and updates only the changed real DOM. "Performance work" is mostly about doing this **less often** and over **smaller trees**.

```
state change → component re-runs → new virtual DOM → diff → minimal real-DOM update
              (make this cheaper & rarer)         (React handles this well)
```

**The golden method (never changes):** **measure → find the biggest bottleneck → fix that one → measure again.** I use Lighthouse, the Network tab, and the React DevTools Profiler — I never guess.

**The two speeds:**
- **Real speed** — smaller bundle (code-splitting), fewer re-renders (memoisation), less data (pagination), fewer network round-trips.
- **Perceived speed** — show layout + skeleton immediately, stream/lazy-load below-the-fold, optimistic UI. Users judge the wait they *can see*.

**The load-order picture (Core Web Vitals):** the browser downloads HTML → JS → renders → becomes interactive. The metrics I watch are **LCP** (largest content painted), **INP** (interaction responsiveness), and **CLS** (layout stability). Good performance work moves these numbers.

**Jump to:** [RP1 What makes React slow](#rp1--what-makes-a-react-app-slow) · [RP2 Measure first](#rp2--how-do-you-measure-react-performance) · [RP3 Render model](#rp3--the-render-model) · [RP4 Re-render causes](#rp4--what-causes-re-renders) · [RP5 React.memo](#rp5--reactmemo) · [RP6 useMemo](#rp6--usememo) · [RP7 useCallback](#rp7--usecallback) · [RP8 Keys](#rp8--list-keys) · [RP9 Code-splitting](#rp9--code-splitting-and-lazy) · [RP10 Bundle size](#rp10--reducing-bundle-size)
> [RP11 Virtualisation](#rp11--list-virtualisation) · [RP12 Pagination](#rp12--pagination-and-less-data) · [RP13 Skeletons](#rp13--skeletons-and-perceived-speed) · [RP14 Data fetching](#rp14--efficient-data-fetching) · [RP15 Caching (React Query)](#rp15--client-caching-react-query) · [RP16 Debounce/throttle](#rp16--debounce-and-throttle) · [RP17 Context perf](#rp17--context-performance) · [RP18 State placement](#rp18--state-placement) · [RP19 Expensive renders](#rp19--taming-expensive-renders) · [RP20 Images/assets](#rp20--images-and-assets)
> [RP21 SSR/SSG](#rp21--ssr-ssg-and-streaming) · [RP22 Web Vitals](#rp22--core-web-vitals) · [RP23 Concurrent features](#rp23--concurrent-react-transitions) · [RP24 Memory leaks](#rp24--memory-leaks) · [RP25 Reconciliation](#rp25--helping-reconciliation) · [RP26 Profiler](#rp26--the-react-profiler) · [RP27 Anti-patterns](#rp27--performance-anti-patterns) · [RP28 When NOT to optimise](#rp28--when-not-to-optimise) · [RP29 A real fix](#rp29--a-real-fix-story) · [RP30 My approach](#rp30--my-approach) · [Section index](#section-index)

---

## RP1 · What makes a React app slow?

**Simple explanation.** Three root causes: **too much JavaScript** shipped up front (large bundle → slow first load), **too many/too big re-renders** (React re-doing work that didn't change), and **too much data** (huge lists, over-fetching). Almost every fix maps to one of these.

**Architect's view:** I diagnose which of the three it is *before* touching code — the fix is completely different for each.

**Follow-ups**
- *"First question you ask?"* — "Is it slow to *load* or slow to *interact*?" — that splits the problem.
- *"Most common?"* — Big bundle for first-load; needless re-renders for jank.

---

## RP2 · How do you measure React performance?

**Simple explanation.** I never guess — I measure. **Lighthouse** for overall scores + Web Vitals, the **Network tab** for bundle/requests, and the **React DevTools Profiler** to see which components re-render and how long they take. Measure → fix the biggest → measure again.

**Follow-ups**
- *"Production data?"* — Real-user monitoring (RUM) / Web Vitals field data — lab ≠ field.
- *"Bundle analysis?"* — `source-map-explorer` / bundle analyzer to see what's heavy.

---

## RP3 · The render model

**Simple explanation.** On a state/props change React **re-runs the component**, builds a new virtual DOM, **diffs** it against the previous one, and updates only the changed real DOM nodes. The DOM update is cheap; the goal of tuning is to make the component **re-run less often** and over **smaller trees**.

**Follow-ups**
- *"Re-render = DOM change?"* — No — re-render runs the function; DOM changes only if the diff differs.
- *"Why care then?"* — Re-running expensive components/large trees still costs CPU.

---

## RP4 · What causes re-renders?

**Simple explanation.** A component re-renders when its **state** or **props** change, its **parent** re-renders, or a **context** it consumes changes. The common trap: passing **new object/array/function references** each render makes children think props changed when they didn't.

**Follow-ups**
- *"New reference trap?"* — Inline `{}`, `[]`, `() => {}` create fresh references every render.
- *"Fix?"* — `useMemo`/`useCallback` to stabilise references; `React.memo` on the child.

---

## RP5 · React.memo

**Simple explanation.** `React.memo` wraps a component so it **skips re-rendering when its props haven't changed** (shallow compare). I use it on pure presentational components that re-render often with the same props — like a table row.

```tsx
const Row = React.memo(function Row({ item }) { /* … */ });
```

**Follow-ups**
- *"Always use it?"* — No — only where re-renders are frequent and props stable; otherwise it adds compare cost.
- *"Breaks when?"* — If props are new references each render — pair with useMemo/useCallback.

---

## RP6 · useMemo

**Simple explanation.** `useMemo` **caches an expensive computed value** between renders, recomputing only when its dependencies change. I use it for costly derived data (sorting/filtering a big list), not for trivial values.

```tsx
const sorted = useMemo(() => rows.sort(cmp), [rows]);
```

**Follow-ups**
- *"Overuse cost?"* — Memoisation isn't free (memory + dep checks) — use for genuinely expensive work.
- *"Also for references?"* — Yes — to keep object/array props stable for memoised children.

---

## RP7 · useCallback

**Simple explanation.** `useCallback` **caches a function reference** so it stays stable across renders — important when passing callbacks to `React.memo` children or as effect dependencies. It's `useMemo` for functions.

**Follow-ups**
- *"When needed?"* — Passing handlers to memoised children, or as `useEffect` deps.
- *"Everywhere?"* — No — unnecessary useCallback is just noise and cost.

---

## RP8 · List keys

**Simple explanation.** Stable, unique **`key`** props let React match list items across renders and avoid re-creating DOM. Using the array **index** as key on a reorderable/filterable list causes wrong reuse and subtle bugs plus wasted work.

**Follow-ups**
- *"Best key?"* — A stable id from the data, never the index for dynamic lists.
- *"Symptom of bad keys?"* — Wrong item state after sort/insert; extra re-renders.

---

## RP9 · Code-splitting and lazy

**Simple explanation.** **Code-splitting** ships only the JS for the screen the user opens, not the whole app. I use `React.lazy` + `Suspense` and route-level splitting. On TCW this cut the initial bundle so the first paint came sooner.

```tsx
const ReportScreen = React.lazy(() => import('./ReportScreen'));
<Suspense fallback={<Spinner/>}><ReportScreen/></Suspense>
```

**Follow-ups**
- *"Where to split?"* — By route first; then heavy below-the-fold widgets.
- *"Risk?"* — Too many tiny chunks add request overhead — balance.

---

## RP10 · Reducing bundle size

**Simple explanation.** Smaller JS = faster load. I **tree-shake**, avoid heavy libraries (or import only what I use), replace big deps with small ones (e.g. date-fns over moment), enable **gzip/brotli**, and analyse the bundle to find bloat.

**Follow-ups**
- *"Biggest wins?"* — Dropping/replacing a heavy library; removing unused polyfills.
- *"How to see bloat?"* — Bundle analyzer / source-map-explorer.

---

## RP11 · List virtualisation

**Simple explanation.** For thousands of rows, **virtualisation** renders only the rows visible in the viewport (plus a small buffer), recycling DOM as you scroll — `react-window`/`react-virtualized`. This is the fix for the laggy big report table on TCW.

**Follow-ups**
- *"Why it works?"* — DOM has ~30 rows instead of 5,000; huge memory/CPU saving.
- *"Trade-off?"* — Fixed/measured row heights; find-in-page only sees rendered rows.

---

## RP12 · Pagination and less data

**Simple explanation.** Don't fetch everything. **Paginate** (page or infinite-scroll), request the first page, load more on demand. Less data means smaller payloads, less parsing, less memory — real speed *and* perceived speed improve.

**Follow-ups**
- *"Server or client paging?"* — Server-side for large data — don't ship it all to filter on the client.
- *"Combine with?"* — Virtualisation for smooth infinite scroll.

---

## RP13 · Skeletons and perceived speed

**Simple explanation.** Instead of a blank screen until data arrives, render the **layout + a loading skeleton immediately**, then fill in data (the four-state pattern: loading/empty/error/data). Perceived speed jumps even before real speed does — users judge the visible wait.

**Follow-ups**
- *"Spinner vs skeleton?"* — Skeleton feels faster and avoids layout shift (CLS).
- *"Links to?"* — The four-state screen pattern ([F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen)).

---

## RP14 · Efficient data fetching

**Simple explanation.** Reduce round-trips: fetch in **parallel** not waterfalls, request only needed fields, **batch** related calls, and avoid the N+1 on the client. On TCW I collapsed several sequential calls into one aggregated endpoint.

**Follow-ups**
- *"Waterfall smell?"* — Each request waiting for the previous — parallelise with `Promise.all`.
- *"Too many calls?"* — Aggregate server-side (BFF) or GraphQL to fetch once.

---

## RP15 · Client caching (React Query)

**Simple explanation.** A data-fetching cache like **React Query/SWR** dedupes requests, caches responses, revalidates in the background, and avoids refetching on every mount. It removes a whole class of "too many API calls" problems.

**Follow-ups**
- *"Benefit over raw fetch?"* — Caching, dedupe, stale-while-revalidate, retries — free.
- *"Stale data?"* — Tune staleTime/refetch policy per data's freshness need.

---

## RP16 · Debounce and throttle

**Simple explanation.** For rapid events (typing in search, scroll, resize) I **debounce** (wait for a pause) or **throttle** (cap the rate) so I don't fire an API call or heavy render on every keystroke. On TCW search this cut needless requests dramatically.

**Follow-ups**
- *"Debounce vs throttle?"* — Debounce waits for quiet; throttle runs at most once per interval.
- *"Search box?"* — Debounce ~300ms before calling the API.

---

## RP17 · Context performance

**Simple explanation.** React **context** re-renders *all* consumers when its value changes. A single big context for everything causes wide re-renders. I split contexts by concern, memoise the value, and keep fast-changing state out of context.

**Follow-ups**
- *"Symptom?"* — Unrelated components re-rendering when one value changes.
- *"Fix?"* — Split contexts; memoise value; consider a state lib (Zustand/Redux) for hot state.

---

## RP18 · State placement

**Simple explanation.** Put state **as low as possible** — close to where it's used. State too high re-renders large trees on every change. "Lift state up" only as far as truly needed; colocation keeps re-renders small.

**Follow-ups**
- *"Rule?"* — Lowest common ancestor of the components that need it — no higher.
- *"Global state?"* — Only for genuinely shared/cross-cutting state.

---

## RP19 · Taming expensive renders

**Simple explanation.** If a component does heavy work each render, I: move the work out of render (`useMemo`), split the component so only the changing part re-renders, and defer non-urgent work. The profiler tells me which component and why.

**Follow-ups**
- *"Split how?"* — Extract the stable part into its own memoised child.
- *"Heavy compute?"* — Consider a web worker for truly CPU-bound work.

---

## RP20 · Images and assets

**Simple explanation.** Images are often the heaviest bytes. I use modern formats (**WebP/AVIF**), correct sizes, **lazy-load** below-the-fold images (`loading="lazy"`), and reserve space to avoid layout shift (CLS). Assets served via CDN with caching.

**Follow-ups**
- *"Biggest LCP win?"* — Optimising the hero image (size/format/priority).
- *"CLS fix?"* — Set width/height so layout doesn't jump.

---

## RP21 · SSR, SSG and streaming

**Simple explanation.** **Server-side rendering (SSR)** and **static generation (SSG)** (e.g. Next.js) send ready HTML so users see content before JS loads — better LCP and SEO. **Streaming SSR** sends HTML in chunks. For content-heavy public pages this beats a pure SPA.

**Follow-ups**
- *"SPA vs SSR?"* — SPA for app-like internal tools; SSR/SSG for public, SEO-sensitive, first-paint-critical pages.
- *"Hydration cost?"* — JS still runs to make HTML interactive — keep it lean.

---

## RP22 · Core Web Vitals

**Simple explanation.** Google's user-centric metrics: **LCP** (largest paint — loading), **INP** (interaction to next paint — responsiveness), **CLS** (cumulative layout shift — stability). I optimise toward these because they reflect real user experience (and SEO).

**Follow-ups**
- *"Fix LCP?"* — Smaller bundle/image, faster server, preload critical assets.
- *"Fix INP?"* — Reduce long tasks; break up heavy JS; concurrent features.

---

## RP23 · Concurrent React (transitions)

**Simple explanation.** React 18's `useTransition`/`startTransition` mark **non-urgent updates** (like filtering a big list) so urgent updates (typing) stay responsive. React can interrupt the heavy work to keep the UI snappy.

**Follow-ups**
- *"Use case?"* — Keep an input responsive while a big filtered list updates.
- *"useDeferredValue?"* — Defer a value's downstream render to avoid blocking input.

---

## RP24 · Memory leaks

**Simple explanation.** Leaks come from not cleaning up: subscriptions, timers, event listeners, or setting state after unmount. I return a **cleanup function** from `useEffect` and abort in-flight fetches on unmount. Leaks slow the app over time and crash long-lived screens.

**Follow-ups**
- *"Cleanup example?"* — `return () => clearInterval(id)` / `controller.abort()`.
- *"Symptom?"* — Growing memory, "set state on unmounted component" warnings.

---

## RP25 · Helping reconciliation

**Simple explanation.** I help React's diffing: stable **keys**, stable component **types/structure** (don't swap element types needlessly), and avoid re-mounting subtrees by conditionally rendering rather than recreating. Stable structure = cheaper diffs.

**Follow-ups**
- *"Remount cause?"* — Changing a component's key or type unmounts/remounts it (loses state, costs work).
- *"Benefit of stability?"* — React reuses DOM/state instead of rebuilding.

---

## RP26 · The React Profiler

**Simple explanation.** The **React DevTools Profiler** records a render and shows which components re-rendered, how long each took, and *why*. It turns "the app feels slow" into "this component re-renders 40 times — memoise it." Evidence over guesswork.

**Follow-ups**
- *"What I look for?"* — Frequent re-renders, long commit times, unexpected renders.
- *"Why did it render?"* — Enable "record why each component rendered."

---

## RP27 · Performance anti-patterns

**Simple explanation.** Common traps: inline objects/functions as props to memoised children, index-as-key on dynamic lists, one giant context, fetching all data then filtering client-side, huge un-virtualised lists, and premature `useMemo` everywhere. Each undoes the wins.

**Follow-ups**
- *"Most common?"* — New references breaking memoisation.
- *"Premature memo?"* — Memoising cheap things adds cost without benefit.

---

## RP28 · When NOT to optimise

**Simple explanation.** Don't optimise without evidence. If a component isn't slow, memoising it adds complexity and cost for nothing. I optimise the **measured** bottleneck only. Premature optimisation makes code harder to read and rarely helps.

*"Most failed 'performance work' optimised the wrong thing — measure first, always."*

**Follow-ups**
- *"Rule?"* — No profiler evidence, no optimisation.
- *"Readability cost?"* — Memo/callbacks everywhere hurt clarity — use where it pays.

---

## RP29 · A real fix story

**The story.** On TCW (A), a report screen with thousands of rows was laggy and the morning first-load felt heavy. I **measured** (Lighthouse + Profiler), then: **code-split** the route (smaller bundle), showed a **skeleton** immediately (perceived speed), **paginated** + **virtualised** the table (rendered ~30 rows not 5,000), and **debounced** the search box. I measured again — first paint sooner, scrolling smooth, far fewer API calls. The "heavy morning" complaint disappeared.

**Lesson.** *"I didn't do everything — I measured, fixed the biggest few, and proved it with numbers."*

**Follow-ups**
- *"Single biggest win?"* — Virtualising the table — it killed the scroll jank.
- *"Cross-link?"* — Same method as the performance deep dive ([PF1–PF4](19-performance-deep-dive.md)).

---

## RP30 · My approach

**How I answer (the whole picture).** *"I treat React performance as a method, not a bag of tricks. First I **measure** with Lighthouse, the Network tab and the React Profiler to decide whether the problem is *load* (bundle) or *interaction* (re-renders) or *data* (too much). For load I **code-split** and shrink the bundle; for interaction I cut needless re-renders with **React.memo/useMemo/useCallback**, fix **keys**, split **context** and place **state low**; for data I **paginate, virtualise and cache** (React Query) and **debounce** rapid events. Alongside real speed I always buy **perceived speed** with an instant layout + skeleton. Then I **measure again** to prove the fix. And I deliberately *don't* optimise without evidence — most failed performance work optimised the wrong thing. On TCW that discipline turned a laggy, heavy-morning report screen into one that loads fast and scrolls smoothly."*

**Follow-ups**
- *"One tool if forced?"* — The React Profiler — it tells me exactly what to fix.
- *"Biggest lever usually?"* — Bundle size for load; virtualisation for big lists.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| RP1 | What's slow | Bundle, re-renders, or too much data |
| RP2 | Measure first | Lighthouse, Network, Profiler |
| RP3 | Render model | Re-run → diff → minimal DOM update |
| RP4 | Re-render causes | State/props/parent/context; new references |
| RP5 | React.memo | Skip re-render on unchanged props |
| RP6 | useMemo | Cache expensive computed values |
| RP7 | useCallback | Stabilise function references |
| RP8 | Keys | Stable ids, never index for dynamic lists |
| RP9 | Code-splitting | Ship only the current screen's JS |
| RP10 | Bundle size | Tree-shake, drop heavy libs, compress |
| RP11 | Virtualisation | Render only visible rows |
| RP12 | Pagination | Fetch less; server-side paging |
| RP13 | Skeletons | Instant frame = perceived speed |
| RP14 | Data fetching | Parallel, batched, fewer round-trips |
| RP15 | React Query | Cache, dedupe, revalidate |
| RP16 | Debounce/throttle | Tame rapid events |
| RP17 | Context perf | Split contexts; memoise value |
| RP18 | State placement | Keep state low/colocated |
| RP19 | Expensive renders | Memoise/split/defer heavy work |
| RP20 | Images | WebP/AVIF, lazy-load, reserve space |
| RP21 | SSR/SSG | Ready HTML for LCP + SEO |
| RP22 | Web Vitals | LCP, INP, CLS |
| RP23 | Concurrent | Transitions keep UI responsive |
| RP24 | Memory leaks | Clean up effects/subscriptions |
| RP25 | Reconciliation | Stable keys/structure = cheap diffs |
| RP26 | Profiler | Evidence of what re-renders and why |
| RP27 | Anti-patterns | New references, index keys, giant context |
| RP28 | When not to | No evidence, no optimisation |
| RP29 | Real fix | Split+skeleton+paginate+virtualise+debounce |
| RP30 | My approach | Measure → fix biggest → measure again |

---

[← Design Principles & Patterns](60-concept-design-principles.md) · [Home](README.md) · [Next → Angular Performance Tuning](62-concept-angular-performance.md)
