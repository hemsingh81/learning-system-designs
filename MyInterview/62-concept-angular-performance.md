# 62 · Concept: Angular Performance Tuning (30 questions)

[← React Performance Tuning](61-concept-react-performance.md) · [Home](README.md) · [Next → Web API / C# Performance Tuning](63-concept-webapi-performance.md)

This file explains **how I make Angular apps fast** — in simple English and real depth. I answer from projects A–E, including enterprise Angular front-ends where large data grids and forms had to stay smooth under real workloads.

> Simple one-liner: *"Angular speed is mostly about **change detection** (do less of it), **bundle size** (ship less JS), and **rendering less** (virtual scroll, trackBy). Measure with the Angular DevTools profiler first, then fix the biggest cost."*

## Concepts first — the whole idea before the questions

**Why Angular apps get slow.** Angular is fast by default, but three things dominate: (1) **change detection running too often or over too much of the tree**, (2) **large bundles** (shipping too much JS up front), and (3) **rendering too much** (huge lists, heavy templates). Every fix targets one of these.

**The mental model — change detection.** Angular watches for changes (via **Zone.js** by default) and, on any async event (click, HTTP, timer), runs **change detection** to update the view. By default it checks the whole component tree. The two big levers are: **OnPush** (check a component only when its inputs change) and, in modern Angular, **Signals** (fine-grained, precise updates).

```
async event → Zone.js notices → change detection runs → update DOM
            (make CD rarer with OnPush/Signals, and cheaper with trackBy/virtual scroll)
```

**The golden method (never changes):** **measure → find the biggest bottleneck → fix that one → measure again.** I use the **Angular DevTools profiler**, Lighthouse and the Network tab — never guesswork.

**The two speeds (same as everywhere):**
- **Real speed** — smaller bundle (lazy routes, tree-shaking), less change detection (OnPush/Signals), render less (virtual scroll, `trackBy`), less data (pagination).
- **Perceived speed** — skeletons/placeholders, route preloading, `@defer` for below-the-fold blocks.

**Modern Angular matters.** Standalone components, **Signals**, `@defer` blocks, and the option to go **zoneless** change the performance playbook — I call these out where they help.

**Jump to:** [AP1 What makes Angular slow](#ap1--what-makes-an-angular-app-slow) · [AP2 Measure first](#ap2--how-do-you-measure-angular-performance) · [AP3 Change detection](#ap3--how-change-detection-works) · [AP4 Zone.js](#ap4--zonejs) · [AP5 OnPush](#ap5--onpush-change-detection) · [AP6 Signals](#ap6--signals) · [AP7 trackBy](#ap7--trackby-in-ngfor) · [AP8 Pure pipes](#ap8--pure-vs-impure-pipes) · [AP9 Async pipe](#ap9--the-async-pipe) · [AP10 Lazy loading](#ap10--lazy-loading-modules-routes)
> [AP11 Bundle size](#ap11--reducing-bundle-size) · [AP12 Virtual scroll](#ap12--cdk-virtual-scroll) · [AP13 Pagination](#ap13--pagination-and-less-data) · [AP14 detach CD](#ap14--detaching-change-detection) · [AP15 runOutsideAngular](#ap15--ngzone-runoutsideangular) · [AP16 defer](#ap16--defer-blocks) · [AP17 Preloading](#ap17--route-preloading) · [AP18 RxJS pitfalls](#ap18--rxjs-performance-pitfalls) · [AP19 Memory leaks](#ap19--memory-leaks-subscriptions) · [AP20 Template cost](#ap20--expensive-templates)
> [AP21 SSR](#ap21--ssr-angular-universal) · [AP22 Web Vitals](#ap22--core-web-vitals) · [AP23 Standalone](#ap23--standalone-components) · [AP24 Zoneless](#ap24--zoneless-angular) · [AP25 Forms perf](#ap25--large-forms-performance) · [AP26 Images](#ap26--ngoptimizedimage) · [AP27 Profiler](#ap27--the-angular-devtools-profiler) · [AP28 Anti-patterns](#ap28--performance-anti-patterns) · [AP29 A real fix](#ap29--a-real-fix-story) · [AP30 My approach](#ap30--my-approach) · [Section index](#section-index)

---

## AP1 · What makes an Angular app slow?

**Simple explanation.** Three root causes: **change detection** running too often or over the whole tree, **large bundles** (too much JS up front), and **rendering too much** (huge grids, heavy templates, function calls in templates). Most fixes reduce change detection or the amount rendered.

**Follow-ups**
- *"First split?"* — Slow to *load* (bundle) vs slow to *interact* (change detection/rendering).
- *"Most common?"* — Default change detection over a big tree + un-tracked `*ngFor`.

---

## AP2 · How do you measure Angular performance?

**Simple explanation.** I measure first: the **Angular DevTools profiler** shows change-detection cycles and which components are expensive; **Lighthouse** for Web Vitals; the **Network tab** and `source-map-explorer` for bundle size. Then fix the biggest, then re-measure.

**Follow-ups**
- *"CD hotspots?"* — Angular DevTools “profiler” records CD time per component.
- *"Bundle bloat?"* — `ng build --stats-json` + a bundle analyzer.

---

## AP3 · How change detection works

**Simple explanation.** On any async event, Angular runs **change detection** to sync the model to the view, walking the component tree. Default strategy checks **every** component each cycle. The goal of tuning is to make CD run **less often** and check **fewer** components.

**Follow-ups**
- *"What triggers it?"* — Events, HTTP, timers — anything Zone.js patches.
- *"Main lever?"* — OnPush (and Signals) to skip unchanged components.

---

## AP4 · Zone.js

**Simple explanation.** **Zone.js** monkey-patches async APIs so Angular knows when to run change detection automatically. Convenient, but it means CD can fire a lot. Modern Angular can run **zoneless** with Signals for finer control ([AP24](#ap24--zoneless-angular)).

**Follow-ups**
- *"Downside?"* — CD triggered broadly; extra overhead patching async.
- *"Alternative?"* — Zoneless + Signals for precise, event-free updates.

---

## AP5 · OnPush change detection

**Simple explanation.** `ChangeDetectionStrategy.OnPush` tells Angular to check a component **only when its `@Input` references change** (or an event/async pipe fires in it), not on every cycle. It's the single biggest CD win — I default components to OnPush.

```ts
@Component({ changeDetection: ChangeDetectionStrategy.OnPush })
```

**Follow-ups**
- *"Requires what?"* — Immutable inputs (new references) or observables via async pipe.
- *"Gotcha?"* — Mutating an object in place won't trigger CD under OnPush.

---

## AP6 · Signals

**Simple explanation.** **Signals** (modern Angular) are reactive values that track exactly what depends on them, so Angular updates **only** the parts of the view that actually changed — fine-grained, without full-tree CD. They're the future of Angular performance.

**Follow-ups**
- *"vs OnPush?"* — Even more precise — updates the specific binding, not the component.
- *"Enables?"* — Zoneless apps with minimal, targeted updates.

---

## AP7 · trackBy in *ngFor

**Simple explanation.** By default `*ngFor` re-creates DOM for list items when the array reference changes. **`trackBy`** tells Angular how to identify items (by id) so it reuses DOM for unchanged rows. Essential for large lists — avoids re-rendering everything.

```ts
*ngFor="let r of rows; trackBy: trackById"
trackById = (_: number, r: Row) => r.id;
```

**Follow-ups**
- *"Symptom without it?"* — Whole list re-rendered on any change; flicker, lost focus.
- *"Best track key?"* — A stable unique id, like React keys.

---

## AP8 · Pure vs impure pipes

**Simple explanation.** **Pure pipes** (default) recompute only when their input reference changes — cheap. **Impure pipes** run on every CD cycle — expensive. I keep pipes pure and avoid heavy work in them; never call functions in templates that run each cycle.

**Follow-ups**
- *"Function in template?"* — Avoid — it runs every CD cycle; use a pure pipe or precomputed value.
- *"When impure?"* — Rarely — only when truly needed, and keep it light.

---

## AP9 · The async pipe

**Simple explanation.** The **`async` pipe** subscribes to an observable in the template and **auto-unsubscribes** on destroy — preventing leaks — and plays nicely with OnPush (it marks the component for check when data arrives). I prefer it over manual subscribe in components.

**Follow-ups**
- *"Why over subscribe?"* — Auto-unsubscribe (no leaks) + OnPush-friendly.
- *"Multiple uses?"* — Share the stream (`shareReplay`) to avoid multiple subscriptions.

---

## AP10 · Lazy loading modules/routes

**Simple explanation.** **Lazy loading** loads a feature's code only when its route is visited, shrinking the initial bundle — the biggest first-load win. I lazy-load feature routes and standalone components with `loadComponent`/`loadChildren`.

**Follow-ups**
- *"Where to split?"* — By feature/route; heavy rarely-used areas first.
- *"Combine with?"* — Preloading strategy for likely-next routes ([AP17](#ap17--route-preloading)).

---

## AP11 · Reducing bundle size

**Simple explanation.** Smaller JS = faster load. I use **production build** (AOT + tree-shaking + minification), lazy routes, avoid heavy libraries, import only needed parts, and analyse the bundle. AOT also makes rendering faster than JIT.

**Follow-ups**
- *"AOT vs JIT?"* — AOT compiles templates at build — smaller, faster, safer (default in prod).
- *"Budgets?"* — Set bundle budgets in `angular.json` to catch bloat in CI.

---

## AP12 · CDK virtual scroll

**Simple explanation.** For thousands of rows, **`cdk-virtual-scroll-viewport`** renders only the items in view, recycling DOM as you scroll — the Angular equivalent of React virtualisation. This is the fix for a laggy large data grid.

**Follow-ups**
- *"Why it works?"* — ~30 DOM rows instead of thousands — huge CPU/memory saving.
- *"Trade-off?"* — Item size handling; find-in-page only sees rendered rows.

---

## AP13 · Pagination and less data

**Simple explanation.** Don't fetch or render everything. **Paginate** server-side, load the first page, fetch more on demand. Less data = smaller payloads, less CD work, less memory. Combine with virtual scroll for smooth infinite lists.

**Follow-ups**
- *"Client filtering of huge data?"* — Avoid — filter/paginate on the server.
- *"Combine?"* — Pagination + virtual scroll + trackBy.

---

## AP14 · Detaching change detection

**Simple explanation.** For a component with very high-frequency updates (e.g. a live ticker) I can **detach** it from automatic CD (`ChangeDetectorRef.detach()`) and call `detectChanges()` manually at a controlled rate — avoiding flooding the whole tree. A precision tool, used sparingly.

**Follow-ups**
- *"When?"* — Rare, high-frequency components where default CD is too costly.
- *"Risk?"* — You own updates now — easy to show stale data; use carefully.

---

## AP15 · ngZone.runOutsideAngular

**Simple explanation.** For work that shouldn't trigger CD (mouse-move handlers, animations, third-party libs), I run it with **`ngZone.runOutsideAngular`** so Zone.js doesn't fire change detection on every event, then re-enter the zone only when I need a view update.

**Follow-ups**
- *"Use case?"* — Scroll/mousemove/animation loops; charting libs.
- *"Re-enter?"* — `ngZone.run(() => …)` when you actually need CD.

---

## AP16 · @defer blocks

**Simple explanation.** Modern Angular's **`@defer`** lazily loads and renders a template block on a trigger (on viewport, on idle, on interaction), with placeholder/loading/error states built in. Great for below-the-fold or heavy widgets — improves initial load and perceived speed.

**Follow-ups**
- *"Triggers?"* — `on viewport`, `on idle`, `on interaction`, `on timer`.
- *"Benefit?"* — Defers heavy component code/render until actually needed.

---

## AP17 · Route preloading

**Simple explanation.** After the initial load, a **preloading strategy** fetches likely-next lazy routes in the background so navigation feels instant. `PreloadAllModules` or a custom strategy (preload only high-probability routes) balances load time vs snappy navigation.

**Follow-ups**
- *"All vs selective?"* — Selective for large apps — preload only common next steps.
- *"Effect?"* — Small first bundle *and* fast subsequent navigation.

---

## AP18 · RxJS performance pitfalls

**Simple explanation.** RxJS is powerful but easy to misuse: **not unsubscribing** (leaks), **duplicate subscriptions** (use `shareReplay`), heavy operators in hot streams, and nested subscribes (use `switchMap`). I keep streams lean and let the async pipe manage lifecycle.

**Follow-ups**
- *"Nested subscribe?"* — Flatten with `switchMap/mergeMap` — and cancel stale requests with `switchMap`.
- *"Duplicate work?"* — `shareReplay(1)` to multicast one result.

---

## AP19 · Memory leaks (subscriptions)

**Simple explanation.** The classic Angular leak is **forgetting to unsubscribe**. I prefer the **async pipe** (auto-unsubscribes) or `takeUntilDestroyed()`/`DestroyRef`. Leaked subscriptions keep components alive and run work forever, slowing the app.

**Follow-ups**
- *"Cleanest fix?"* — Async pipe or `takeUntilDestroyed()`.
- *"Symptom?"* — Growing memory, handlers firing after navigation.

---

## AP20 · Expensive templates

**Simple explanation.** Templates that call **functions** or **getters** in bindings run on every CD cycle — a silent performance killer. I move that work to a **pure pipe** or a **precomputed property/signal**, so it runs only when inputs change.

**Follow-ups**
- *"Why bad?"* — `{{ compute() }}` runs each CD cycle, many times per second.
- *"Fix?"* — Pure pipe, memoised value, or a signal/computed.

---

## AP21 · SSR (Angular Universal)

**Simple explanation.** **Angular Universal** renders pages on the server so users see content before JS loads — better LCP and SEO — then hydrates for interactivity. For public, content-heavy, SEO-sensitive pages this beats a pure SPA; internal tools often don't need it.

**Follow-ups**
- *"Hydration?"* — Modern non-destructive hydration reuses server DOM instead of re-rendering.
- *"When skip?"* — Internal apps behind login where SEO/first-paint aren't critical.

---

## AP22 · Core Web Vitals

**Simple explanation.** Same user-centric metrics as everywhere: **LCP** (loading), **INP** (responsiveness), **CLS** (stability). Angular levers: smaller bundle + SSR (LCP), less CD + zoneless (INP), `NgOptimizedImage` and reserved space (CLS).

**Follow-ups**
- *"Fix INP in Angular?"* — OnPush/Signals/zoneless to cut long CD tasks.
- *"Fix LCP?"* — Lazy routes, SSR, optimised hero image.

---

## AP23 · Standalone components

**Simple explanation.** **Standalone components** drop NgModules, simplifying the app and improving **tree-shaking** (only what's imported ships). They also make lazy-loading a single component easy (`loadComponent`). Simpler graph = smaller, faster builds.

**Follow-ups**
- *"Perf angle?"* — Better tree-shaking and finer lazy-loading granularity.
- *"Default now?"* — Yes — modern Angular is standalone-first.

---

## AP24 · Zoneless Angular

**Simple explanation.** **Zoneless** drops Zone.js and relies on **Signals** (and explicit triggers) to update the view. CD no longer fires on every async event — only when a signal actually changes — giving precise, minimal updates and a smaller bundle.

**Follow-ups**
- *"Requires?"* — Signal-based state / explicit change notification.
- *"Benefit?"* — Less overhead, fewer needless CD cycles, better INP.

---

## AP25 · Large forms performance

**Simple explanation.** Big reactive forms can be slow because every value change triggers validation/CD across many controls. I use **OnPush**, `updateOn: 'blur'` for expensive validators, split large forms, and avoid heavy synchronous validators — debounce async ones.

**Follow-ups**
- *"updateOn: 'blur'?"* — Validate on blur/submit instead of every keystroke.
- *"Async validators?"* — Debounce and cancel stale ones (switchMap).

---

## AP26 · NgOptimizedImage

**Simple explanation.** The **`NgOptimizedImage`** directive (`ngSrc`) enforces best practices: lazy-loading, priority hints for the LCP image, correct sizing/`srcset`, and preventing layout shift. It's an easy, big win for image-heavy pages' LCP and CLS.

**Follow-ups**
- *"LCP image?"* — Mark it `priority` so it loads first.
- *"CLS?"* — Requires width/height — reserves space, no jump.

---

## AP27 · The Angular DevTools profiler

**Simple explanation.** **Angular DevTools** has a profiler that records change-detection cycles and shows **which components cost the most CD time** and how often they're checked. It turns "the grid feels slow" into "this component runs CD 200 times — make it OnPush."

**Follow-ups**
- *"What I look for?"* — Frequent/expensive CD, components checked needlessly.
- *"Then?"* — Apply OnPush/Signals/trackBy where the profiler points.

---

## AP28 · Performance anti-patterns

**Simple explanation.** Common traps: **function calls in templates**, missing **`trackBy`**, everything on **default CD**, not unsubscribing, impure pipes, giant eager bundles (no lazy routes), and rendering huge lists without virtual scroll. Each undoes the wins.

**Follow-ups**
- *"Number-one?"* — Function calls in bindings + default CD over a big tree.
- *"Quick audit?"* — Search templates for `()` in bindings and `*ngFor` without trackBy.

---

## AP29 · A real fix story

**The story.** An enterprise Angular data grid felt laggy on scroll and typing. I **profiled** with Angular DevTools — change detection was running across the whole tree on every keystroke, and the grid rendered thousands of rows. Fixes, in order: switched components to **OnPush**, added **`trackBy`**, replaced the grid with **CDK virtual scroll**, moved a template `compute()` into a **pure pipe**, and **debounced** the filter. Re-profiled — CD cycles dropped sharply, scrolling smoothed out, typing stayed responsive.

**Lesson.** *"Same method as always — measure, fix the biggest CD/render costs, prove it. OnPush + virtual scroll + trackBy did most of the work."*

**Follow-ups**
- *"Single biggest win?"* — OnPush cut needless CD; virtual scroll cut the render.
- *"Cross-link?"* — Same discipline as the performance deep dive ([PF1](19-performance-deep-dive.md#pf1--the-page-took-too-long-to-load-what-did-you-do)).

---

## AP30 · My approach

**How I answer (the whole picture).** *"Angular performance comes down to three levers, and I always **measure first** with the Angular DevTools profiler to know which one to pull. To cut **change detection** I default to **OnPush**, move to **Signals** (and even **zoneless**) where I can, add **`trackBy`**, keep pipes **pure**, avoid **function calls in templates**, and run noisy work with **`runOutsideAngular`**. To cut **load** I **lazy-load** routes/components, build with **AOT**, shrink and analyse the **bundle**, and use **`@defer`** and **preloading**. To **render less** I use **CDK virtual scroll** and **server-side pagination**. I buy perceived speed with skeletons and `@defer`, prevent leaks with the **async pipe / takeUntilDestroyed**, and then **measure again** to prove the win. And I never optimise without evidence — the profiler decides what to fix."*

**Follow-ups**
- *"One lever if forced?"* — OnPush (moving to Signals) — change detection is usually the cost.
- *"Biggest load win?"* — Lazy routes + smaller bundle.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| AP1 | What's slow | Change detection, bundle, or rendering too much |
| AP2 | Measure first | Angular DevTools profiler, Lighthouse |
| AP3 | Change detection | Runs on async events over the tree |
| AP4 | Zone.js | Auto-triggers CD; zoneless is the alternative |
| AP5 | OnPush | Check only when inputs change |
| AP6 | Signals | Fine-grained, precise updates |
| AP7 | trackBy | Reuse DOM for unchanged list items |
| AP8 | Pure pipes | Pure = cheap; avoid impure/heavy |
| AP9 | Async pipe | Auto-unsubscribe; OnPush-friendly |
| AP10 | Lazy loading | Load feature code on demand |
| AP11 | Bundle size | AOT, tree-shake, budgets |
| AP12 | Virtual scroll | Render only visible rows |
| AP13 | Pagination | Server-side; less data |
| AP14 | Detach CD | Manual CD for high-frequency components |
| AP15 | runOutsideAngular | Keep noisy events out of CD |
| AP16 | @defer | Lazy-render heavy/below-fold blocks |
| AP17 | Preloading | Fast subsequent navigation |
| AP18 | RxJS pitfalls | Unsubscribe, shareReplay, switchMap |
| AP19 | Memory leaks | async pipe / takeUntilDestroyed |
| AP20 | Expensive templates | No function calls in bindings |
| AP21 | SSR | Ready HTML for LCP + SEO |
| AP22 | Web Vitals | LCP, INP, CLS |
| AP23 | Standalone | Better tree-shaking, finer lazy-load |
| AP24 | Zoneless | Signals-driven, minimal CD |
| AP25 | Large forms | OnPush, updateOn blur, debounce validators |
| AP26 | NgOptimizedImage | Lazy/priority images, no CLS |
| AP27 | Profiler | Evidence of CD cost per component |
| AP28 | Anti-patterns | Template functions, no trackBy, default CD |
| AP29 | Real fix | OnPush + virtual scroll + trackBy + debounce |
| AP30 | My approach | Measure → cut CD/load/render → measure again |

---

[← React Performance Tuning](61-concept-react-performance.md) · [Home](README.md) · [Next → Web API / C# Performance Tuning](63-concept-webapi-performance.md)
