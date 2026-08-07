# 29 · Concept: Angular (30 questions)

[← Concept: ReactJS](28-concept-reactjs.md) · [Home](README.md) · [Next → React vs Angular](30-concept-react-vs-angular.md)

This file explains **Angular** simply and in depth. Note: modern **Angular** (v2+) is a complete, TypeScript-based framework — not the old **AngularJS** (v1, from 2010). I built Angular front ends on TengizChevroil (Project C), so I answer from real experience. All code is TypeScript (Angular is TypeScript-first).

> Simple one-liner: *"Angular is a full, opinionated framework from Google for building large applications. Unlike React, it gives you everything in the box — routing, forms, HTTP, dependency injection — so a big team builds the same way."*

**Jump to (fundamentals):** [A1 What is Angular](#a1--what-is-angular-and-angularjs) · [A2 Components & modules](#a2--components-templates-and-modules) · [A3 Data binding](#a3--data-binding-the-four-types) · [A4 Dependency injection](#a4--dependency-injection-and-services) · [A5 Directives & pipes](#a5--directives-and-pipes) · [A6 RxJS & Observables](#a6--rxjs-and-observables) · [A7 Change detection](#a7--change-detection) · [A8 Routing & forms](#a8--routing-and-forms)
> **Architecture & full-stack lens:** [A9 App architecture](#a9--structuring-a-large-angular-app) · [A10 Performance](#a10--performance-and-lazy-loading) · [A11 HTTP & the API](#a11--http-interceptors-and-talking-to-the-api) · [A12 State management](#a12--state-management-services-vs-ngrx) · [A13 Security](#a13--front-end-security-in-angular) · [A14 Testing & build](#a14--testing-and-build)
> **Deeper mechanics:** [A15 Component lifecycle](#a15--component-lifecycle-hooks) · [A16 Signals](#a16--signals-modern-reactivity) · [A17 Standalone components](#a17--standalone-components-and-modern-angular) · [A18 RxJS operators](#a18--rxjs-operators-in-depth) · [A19 Content projection](#a19--content-projection-and-viewchild) · [A20 Route guards & resolvers](#a20--route-guards-and-resolvers)
> **Forms, quality & tooling:** [A21 Reactive forms deep](#a21--reactive-forms-in-depth) · [A22 Custom pipes/directives](#a22--custom-pipes-and-directives) · [A23 Accessibility](#a23--accessibility) · [A24 i18n](#a24--internationalisation) · [A25 CLI & tooling](#a25--the-angular-cli-and-tooling) · [A26 Common pitfalls](#a26--common-mistakes-i-watch-for)
> **Architecture decisions:** [A27 Micro-frontends](#a27--micro-frontends) · [A28 Design system](#a28--design-systems-and-material) · [A29 SSR](#a29--server-side-rendering-with-angular-universal) · [A30 When I choose Angular](#a30--when-i-choose-angular) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of Angular in plain English. Hold these seven ideas and every question below is a detail hanging off one of them.

**1. A full framework, not a library.** Where React gives you the view and you pick the rest, **Angular is opinionated and complete** — routing, forms, an HTTP client, and dependency injection are all in the box, and TypeScript is mandatory. That structure is its superpower for **large teams and large apps**: everyone builds the same way. *(Modern Angular = v2+; the old AngularJS v1 is a different, legacy thing.)*

**2. Components & templates — the building block.** The UI is a tree of **components**, each with a TypeScript class (logic) and an HTML template (view). Templates use Angular syntax — `{{ }}` interpolation, `[prop]` property binding, `(event)` event binding, and `[(ngModel)]` two-way binding. Modern Angular favours **standalone components** over the older NgModules.

**3. Dependency Injection — Angular's backbone.** You declare what a component needs (a service) in its constructor and Angular **provides** it. DI gives you shared singletons, easy mocking in tests, and clean separation of concerns. It is the single most important Angular concept to understand deeply.

**4. RxJS & Observables — data over time.** Angular is built on **RxJS**. An **Observable** is a stream of values (HTTP responses, form changes, route params) you subscribe to and transform with operators (`map`, `switchMap`, `debounceTime`). The newer **Signals** add simpler, fine-grained reactivity alongside RxJS.

**5. Change detection — how the screen stays in sync.** When something changes, Angular **checks the component tree** and updates the DOM. By default it checks a lot; you make it fast with the **OnPush** strategy (check only when inputs change), Signals, and — newest — **zoneless** change detection. This is the #1 performance topic.

**6. Routing, forms & guards — the built-ins.** The **Router** maps URLs to components with **lazy-loaded** feature areas. **Reactive forms** model form state as objects you can validate and test. **Guards/resolvers** protect routes and pre-fetch data. You get all this without third-party libraries.

**7. The toolchain — the Angular CLI.** One CLI scaffolds, builds, tests, and serves. It enforces a consistent project shape, which is exactly why enterprises pick Angular.

**The full-stack lens (how I think as an architect):** beyond the basics I care about **architecture** (feature modules/standalone, lazy loading), **performance** (OnPush/Signals, trackBy), **HTTP** (interceptors for auth/errors), **state** (services vs NgRx), **security** (Angular's built-in XSS escaping, tokens), and **testing** (TestBed, DI-mocked specs). Those are the A9–A30 questions.

**One rule I never break:** *lean on DI and let change detection do the least work possible.* Get those two right and a large Angular app stays fast and maintainable.

---

## A1 · What is Angular (and AngularJS)?

**Simple explanation.** Angular is a **framework** — a complete toolkit. Where React gives you just the view and you pick the rest, Angular ships routing, forms, an HTTP client, and dependency injection built in, and enforces a structure. This is great for **large teams and large apps** because everyone builds the same way.

**Important distinction:**
- **AngularJS** = version 1 (2010), used JavaScript and "scopes". It is legacy.
- **Angular** = version 2 and up (a full rewrite), uses **TypeScript**, components, and RxJS. When people say "Angular" today they mean this.

*"On TengizChevroil I used Angular for the completion-platform front ends — its structure and dependency injection suited a big, multi-team, regulated build."*

**Follow-ups**
- *"Angular vs AngularJS — same thing?"* — No. Different architecture entirely; Angular 2+ was a rewrite. Don't confuse them in an interview.
- *"Why pick a full framework?"* — Consistency and less decision-fatigue on big teams — the batteries are included and the structure is enforced.

---

## A2 · Components, templates, and modules

**Simple explanation.** Like React, Angular builds UI from **components**. A component = a TypeScript class (logic) + an HTML template (view) + styles. **Modules** (`NgModule`) group related components/services — though modern Angular also supports **standalone components** without modules.

```typescript
@Component({
  selector: 'app-badge',
  template: `<span class="badge badge--{{tone}}">{{ label }}</span>`,
})
export class BadgeComponent {
  @Input() label = '';
  @Input() tone: 'ok' | 'warn' = 'ok';
}
```

`@Input()` is how a parent passes data in (like React props); `@Output()` with an `EventEmitter` sends events back up.

**Follow-ups**
- *"@Input / @Output vs React props?"* — Same idea: `@Input` = data in, `@Output` = events out. Angular just uses decorators.
- *"What are standalone components?"* — Newer Angular lets components declare their own dependencies, reducing `NgModule` boilerplate.

---

## A3 · Data binding (the four types)

**Simple explanation.** Data binding connects the class and the template. Angular has four kinds — a very common interview question:

| Type | Syntax | Direction |
|---|---|---|
| Interpolation | `{{ value }}` | class → view |
| Property binding | `[src]="url"` | class → view |
| Event binding | `(click)="save()"` | view → class |
| Two-way binding | `[(ngModel)]="name"` | both ways |

The famous `[(ngModel)]` "banana in a box" is just property binding + event binding combined — the input shows the value *and* updates it.

**Follow-ups**
- *"How does two-way binding actually work?"* — It's shorthand for `[value]` + `(valueChange)` — bind in and emit out at once.
- *"Does React have two-way binding?"* — No, React is one-way by design; you wire the input's `onChange` yourself (controlled components).

---

## A4 · Dependency injection and services

**Simple explanation.** A **service** is a class for shared logic or data (e.g. an API client). **Dependency Injection (DI)** means Angular *creates and supplies* these for you — you just ask for them in the constructor. This is one of Angular's biggest strengths.

```typescript
@Injectable({ providedIn: 'root' })
export class ReportService {
  constructor(private http: HttpClient) {}
  getReport(type: string) { return this.http.get<Report>(`/api/reports/${type}`); }
}

@Component({ /* ... */ })
export class ReportComponent {
  constructor(private reports: ReportService) {}   // Angular injects it — I don't 'new' it
}
```

**Why it matters:** loose coupling and easy testing — in a test I inject a fake `ReportService`.

**Follow-ups**
- *"Why is DI good?"* — Components don't build their own dependencies, so they're easy to swap and mock — great for unit tests.
- *"What does `providedIn: 'root'` mean?"* — One shared (singleton) instance for the whole app.

---

## A5 · Directives and pipes

**Simple explanation.** **Directives** add behaviour to elements. **Structural directives** change the DOM layout — `*ngIf` (show/hide), `*ngFor` (loop). **Attribute directives** change appearance — `[ngClass]`, `[ngStyle]`. **Pipes** transform displayed values.

```html
<div *ngIf="loaded; else spinner">
  <p *ngFor="let p of positions">{{ p.marketValue | currency:'USD' }} — {{ p.asOf | date }}</p>
</div>
<ng-template #spinner><app-spinner></app-spinner></ng-template>
```

Here `currency` and `date` are built-in **pipes**; I can also write custom pipes.

**Follow-ups**
- *"Structural vs attribute directive?"* — Structural (`*`) adds/removes DOM; attribute changes an existing element's look/behaviour.
- *"When a custom pipe?"* — For reusable display formatting (e.g. masking an account number) — keeps templates clean.

---

## A6 · RxJS and Observables

**Simple explanation.** Angular uses **RxJS** heavily. An **Observable** is a stream of values over time — like a Promise, but it can emit *many* values and you can cancel it. `HttpClient` returns Observables.

```typescript
this.reports.getReport(type)
  .pipe(
    retry(2),                      // retry twice on failure
    map(r => r.rows),              // transform
    takeUntil(this.destroyed$)     // auto-unsubscribe on destroy
  )
  .subscribe(rows => this.rows = rows);
```

**Key idea:** you must **unsubscribe** (or use `async` pipe / `takeUntil`) or you leak memory.

**Follow-ups**
- *"Observable vs Promise?"* — A Promise resolves once; an Observable can emit many values, be cancelled, and transformed with operators (`map`, `filter`, `retry`).
- *"Easiest way to avoid leaks?"* — The `async` pipe in the template subscribes and unsubscribes automatically.

---

## A7 · Change detection

**Simple explanation.** **Change detection** is how Angular keeps the screen in sync with the data. By default Angular checks components after events, HTTP calls and timers. For performance, I switch hot components to **OnPush**, which only re-checks when an `@Input` reference changes or an Observable emits.

**Follow-ups**
- *"How is this different from React?"* — React re-renders when state/props change and diffs a virtual DOM. Angular runs change detection over the component tree (via Zone.js) — different mechanism, same goal.
- *"When use OnPush?"* — On components with lots of data or frequent parent re-renders — it cut needless checks and sped up our grids.

---

## A8 · Routing and forms

**Simple explanation.** Angular's **Router** maps URLs to components (built-in, unlike React where you add React Router). Angular has two form styles: **Template-driven** (simple, logic in the HTML) and **Reactive forms** (logic in TypeScript — better for complex, testable validation).

```typescript
// Reactive form — my choice for anything non-trivial
this.form = this.fb.group({
  ticker: ['', Validators.required],
  quantity: [0, [Validators.required, Validators.min(1)]],
});
```

**Follow-ups**
- *"Template-driven vs Reactive forms?"* — Template-driven for tiny forms; Reactive for complex validation, dynamic fields, and testability — the logic lives in code.
- *"How do route guards help?"* — They block navigation (e.g. `canActivate` for auth) before a component loads.

---

## A9 · Structuring a large Angular app

**Simple explanation (architect lens).** Angular already enforces structure, and I extend that for big builds by organising into **feature modules** (or standalone-component feature areas), a **core module** (singletons like auth and the API client, imported once), and a **shared module** (reusable components/pipes).

```
src/app/
  core/        (auth, http interceptors, guards — singletons)
  shared/      (reusable UI components, pipes, directives)
  features/completions/   (components, services, routing for one area)
  features/reports/
```

**Why this suited TengizChevroil:** it was a multi-team, regulated build. Feature modules let teams own an area and lazy-load it, while the core/shared split stopped duplication — any engineer could open any feature and know exactly where things live.

**Follow-ups**
- *"Core vs shared module?"* — Core = app-wide singletons imported once; Shared = reusable presentational pieces imported by many features.
- *"Standalone components change this?"* — Modern Angular reduces `NgModule` boilerplate, but the *feature/core/shared* separation of concerns still holds.
- *"How do teams work independently?"* — One feature area per team, lazy-loaded and route-isolated, with shared contracts in `shared`.

---

## A10 · Performance and lazy loading

**Simple explanation.** The two biggest Angular performance levers are **lazy loading** and **OnPush change detection**. Lazy loading splits the app so a feature's code only downloads when the user visits that route — a much smaller, faster initial load.

```typescript
// route config — the reports feature loads only when visited
{ path: 'reports', loadChildren: () => import('./features/reports/reports.routes') }
```

Add **OnPush** on data-heavy components (re-check only when an `@Input` reference changes or an Observable emits), `trackBy` on `*ngFor` (reuse DOM rows instead of rebuilding), and the **`async` pipe** (auto subscribe/unsubscribe).

*"On TengizChevroil, lazy-loading feature modules cut the initial bundle, and OnPush + trackBy kept the completion grids responsive under lots of live data."*

**Follow-ups**
- *"What does trackBy do?"* — It tells `*ngFor` how to identify a row so Angular reuses its DOM node instead of re-rendering the whole list.
- *"How do you find the bottleneck?"* — Angular DevTools profiler for change-detection cost, and source-map-explorer for bundle size.
- *"AOT compilation?"* — Ahead-of-Time compiles templates at build time — smaller, faster, and errors caught early. It's the production default.

---

## A11 · HTTP interceptors and talking to the API

**Simple explanation (full-stack lens).** Angular's `HttpClient` returns Observables, and **interceptors** are the killer feature for a full-stack app: they sit in the middle of *every* HTTP call, so I add the auth token, handle errors, and log — all in one place (just like server-side middleware).

```typescript
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token;
  const authReq = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  return next(authReq).pipe(catchError(handleApiError));   // one place for token + errors
};
```

**Full-stack details I own:** strongly-typed responses (`http.get<Report>()`), a shared error shape matching my ASP.NET Core Web API, and retry/timeout policies — so the Angular front end and the C# back end share one consistent contract.

**Follow-ups**
- *"Why interceptors over per-call code?"* — DRY — auth and error handling live once, not copied into every service.
- *"How do FE and BE stay in sync?"* — Shared DTO shapes (I generate TypeScript models from the API's OpenAPI spec) so a contract change breaks the build, not production.
- *"Where do you attach the Entra ID token?"* — In the interceptor, from the auth/MSAL service — the API then validates it.

---

## A12 · State management: services vs NgRx

**Simple explanation.** For most apps, a **service holding state in an RxJS `BehaviorSubject`** is enough — components subscribe and stay in sync. For large apps with complex, shared, frequently-changing state, **NgRx** (Angular's Redux) adds a single store, actions and reducers with great dev-tools and traceability.

**My rule (same as React):** don't reach for NgRx by default — it's boilerplate-heavy. Use a simple stateful service until the app genuinely needs a central store; treat server data as a cached stream, not duplicated state.

**Follow-ups**
- *"When is NgRx worth it?"* — When many components share complex state and you need time-travel debugging and strict, predictable updates — otherwise it's overkill.
- *"Service-with-Subject pattern?"* — A service exposes a `BehaviorSubject` as an Observable; components read via the `async` pipe and update through service methods.

---

## A13 · Front-end security in Angular

**Simple explanation (full-stack lens).** Like React, the front end isn't the security boundary — the API is — but Angular gives strong built-in protection:
- **XSS:** Angular **auto-sanitises** values bound into templates by default; I avoid `bypassSecurityTrust...` unless the content is trusted.
- **Auth:** MSAL for Entra ID login, token attached via interceptor, `canActivate` **route guards** block unauthorised pages.
- **Never trust the client:** guards improve UX but the **server re-authorises** every request.

**Follow-ups**
- *"How does Angular prevent XSS?"* — It sanitises interpolated/bound values automatically, so injected markup renders as inert text.
- *"Route guard vs API auth?"* — Guards stop navigation for UX; the API still enforces authorisation on every call — defence in depth.
- *"CSRF?"* — Angular's `HttpClient` has built-in XSRF-token support that pairs with a server cookie/header scheme.

---

## A14 · Testing and build

**Simple explanation.** Angular is testing-first: the CLI scaffolds **Jasmine + Karma** unit tests (many teams now use **Jest**), with `TestBed` to configure components and DI, and **Cypress/Playwright** for end-to-end. DI makes tests easy — I inject fake services.

```typescript
it('loads reports', () => {
  const fixture = TestBed.createComponent(ReportComponent);
  fixture.detectChanges();
  expect(fixture.nativeElement.textContent).toContain('On time');
});
```

**Build & quality gates:** the Angular CLI produces AOT-optimised, tree-shaken production bundles; I wire lint, unit tests and bundle-budget checks into CI — the same discipline I apply to the C# back end.

**Follow-ups**
- *"Why is DI great for testing?"* — I swap real services for fakes at the boundary, so components are tested in isolation.
- *"What's a bundle budget?"* — A CI limit on bundle size that fails the build if it grows too big — keeps load times in check.
- *"Unit vs E2E balance?"* — Lots of fast unit/component tests, a few E2E on critical journeys (login → view completion).

---

## A15 · Component lifecycle hooks

**Simple explanation.** Angular calls **lifecycle hooks** at key moments: `ngOnInit` (set up, fetch data), `ngOnChanges` (an `@Input` changed), `ngOnDestroy` (clean up — unsubscribe!), plus `ngAfterViewInit`. I do initial work in `ngOnInit` and always clean up in `ngOnDestroy`.

```typescript
ngOnInit()    { this.load(); }
ngOnDestroy() { this.destroyed$.next(); }   // triggers takeUntil to unsubscribe
```

**Follow-ups**
- *"Why not fetch in the constructor?"* — The constructor is for DI wiring; `ngOnInit` runs after inputs are set — the right place for setup.
- *"Most important hook for leaks?"* — `ngOnDestroy` — unsubscribe there (or use the `async` pipe/takeUntil).

---

## A16 · Signals (modern reactivity)

**Simple explanation.** **Signals** (Angular 16+) are a new, simpler reactivity model: a `signal()` holds a value, `computed()` derives from it, and the view updates automatically — fine-grained change detection without heavy RxJS or Zone.js for local state.

```typescript
count = signal(0);
double = computed(() => this.count() * 2);
inc() { this.count.update(c => c + 1); }
```

**Follow-ups**
- *"Signals vs RxJS?"* — Signals for synchronous local component state (simpler); RxJS for async streams/events — they complement each other.
- *"Why do signals matter?"* — More precise updates and a path away from Zone.js — better performance and simpler code.

---

## A17 · Standalone components and modern Angular

**Simple explanation.** Modern Angular lets components be **standalone** — they import their own dependencies directly, so you no longer need `NgModule` boilerplate. New apps are bootstrapped standalone with functional providers and lazy-loaded routes.

**Follow-ups**
- *"Are NgModules dead?"* — Not gone, but standalone is the default direction — less boilerplate, clearer dependencies.
- *"Does architecture change?"* — The feature/core/shared *separation* still holds; only the module wiring gets simpler.

---

## A18 · RxJS operators in depth

**Simple explanation.** The operators I use most on real screens: `map`/`filter` (transform), `switchMap` (cancel previous — perfect for search/type-ahead), `debounceTime` (wait for typing to stop), `combineLatest` (merge streams), `catchError` (handle failures), `takeUntil` (auto-unsubscribe).

```typescript
this.search$.pipe(
  debounceTime(300), distinctUntilChanged(),
  switchMap(q => this.api.search(q))   // cancels the previous request
).subscribe(...);
```

**Follow-ups**
- *"switchMap vs mergeMap?"* — switchMap cancels the previous inner request (search); mergeMap runs all in parallel (independent tasks).
- *"Why debounceTime on search?"* — It waits until the user stops typing so I fire one request, not one per keystroke.

---

## A19 · Content projection and ViewChild

**Simple explanation.** **Content projection** (`<ng-content>`) lets a component render whatever markup the parent puts inside its tags — like React `children` — great for reusable cards/panels. **`@ViewChild`** gets a reference to a child component/element to call its methods.

**Follow-ups**
- *"ng-content use case?"* — A generic `<app-card>` that wraps any content the caller supplies — reusable layout.
- *"When @ViewChild?"* — To call a child's method or focus an element — sparingly, preferring inputs/outputs first.

---

## A20 · Route guards and resolvers

**Simple explanation.** **Guards** control navigation: `canActivate` (block unauthorised pages), `canDeactivate` (warn about unsaved changes). **Resolvers** pre-fetch data *before* a route loads so the screen appears with data ready.

**Follow-ups**
- *"Guard vs API auth?"* — Guards are UX (don't show the page); the API still authorises every request — defence in depth.
- *"Why a resolver?"* — Avoids a flash of empty screen — data is loaded before the component shows.

---

## A21 · Reactive forms in depth

**Simple explanation.** For anything non-trivial I use **Reactive forms**: the form model lives in TypeScript (`FormGroup`/`FormControl`), giving typed values, sync/async validators, dynamic controls (`FormArray`), and easy testing.

```typescript
this.form = this.fb.group({
  ticker: ['', [Validators.required], [this.tickerExistsValidator]],   // async validator
  lots: this.fb.array([]),                                              // dynamic rows
});
```

**Follow-ups**
- *"Async validator example?"* — Check a ticker exists via the API as the user types — returns an Observable of the error/null.
- *"FormArray use?"* — Add/remove repeated groups (e.g. multiple trade lots) dynamically.

---

## A22 · Custom pipes and directives

**Simple explanation.** I write **custom pipes** for reusable display formatting (mask an account number) and **custom directives** for reusable behaviour (a `hasPermission` directive that hides elements by role). Pure pipes are cached for performance.

**Follow-ups**
- *"Pure vs impure pipe?"* — Pure (default) recomputes only when the input reference changes (fast); impure runs every change detection (use rarely).
- *"Directive example?"* — An attribute directive that shows/hides by user role — UX only; the API still enforces it.

---

## A23 · Accessibility

**Simple explanation.** Same discipline as React: semantic HTML, keyboard support, ARIA where needed, focus management, and colour contrast. **Angular CDK a11y** helps with focus traps and live announcements; I check with axe/Lighthouse in CI.

**Follow-ups**
- *"What does the CDK a11y module give?"* — Focus management, focus traps (dialogs), and screen-reader live announcements — ready-made a11y utilities.
- *"First step?"* — Semantic elements — most accessibility follows from correct HTML.

---

## A24 · Internationalisation

**Simple explanation.** Angular has **built-in i18n** (and libraries like ngx-translate) to translate text, and locale-aware pipes for dates/numbers/currency — important for the global, regulated apps I build.

**Follow-ups**
- *"Built-in i18n vs ngx-translate?"* — Built-in compiles per-locale builds (fast, SEO-friendly); ngx-translate switches language at runtime (more flexible).
- *"Locale pipes?"* — `date`/`currency`/`number` format correctly per locale automatically.

---

## A25 · The Angular CLI and tooling

**Simple explanation.** The **Angular CLI** is a big strength — it scaffolds components/services, runs the dev server, builds AOT-optimised production bundles, runs tests, and manages upgrades via `ng update`. Consistent, batteries-included tooling for large teams.

**Follow-ups**
- *"Why is `ng update` valuable?"* — It automates framework upgrades with migration scripts — keeping big apps current with less pain.
- *"AOT vs JIT?"* — AOT compiles templates at build time (production default — smaller/faster, errors caught early); JIT compiles in the browser (dev only).

---

## A26 · Common mistakes I watch for

**Simple explanation.** Recurring Angular issues I catch: forgetting to unsubscribe (memory leaks), overusing default change detection on heavy components (should be OnPush), no `trackBy` on big `*ngFor`, reaching for NgRx too early, huge eager bundles (should lazy-load), and putting business rules on the client.

**Follow-ups**
- *"Biggest perf mistake?"* — Default change detection on a heavy grid — switch to OnPush + trackBy.
- *"Most common leak?"* — Manual `subscribe` without unsubscribe — use `async` pipe or `takeUntil`.

---

## A27 · Micro-frontends

**Simple explanation (architect lens).** Angular supports **micro-frontends** (Module Federation) so multiple teams build/deploy areas of a large app independently. Powerful for scale, but adds shared-dependency and consistency overhead — I use it only when team size justifies it.

**Follow-ups**
- *"When justified?"* — Many teams needing independent release cadence on one big app — otherwise a well-structured single app is simpler.
- *"Main risk?"* — Version/dependency drift between shells — governance and a shared design system are essential.

---

## A28 · Design systems and Material

**Simple explanation.** **Angular Material** (built on the CDK) gives accessible, themeable components out of the box — a fast path to a consistent design system. I theme it or wrap it so teams share one component set instead of rebuilding tables/dialogs.

**Follow-ups**
- *"Why Material?"* — Accessible, well-tested components + theming — consistency and speed for enterprise apps.
- *"Wrap Material?"* — A thin wrapper layer lets us apply our brand and swap implementations later without touching every screen.

---

## A29 · Server-side rendering with Angular Universal

**Simple explanation.** **Angular Universal** renders the app's HTML on the server for faster first paint and SEO — the Angular equivalent of Next.js SSR. For authenticated internal apps (like TengizChevroil) SEO is irrelevant so CSR is fine; Universal shines for public sites.

**Follow-ups**
- *"When Universal?"* — Public, SEO-sensitive, or first-paint-critical apps — not needed behind a login.
- *"Equivalent to?"* — Next.js for React — same SSR benefits.

---

## A30 · When I choose Angular

**How I answer (decision lens).** *"I choose Angular for large, long-lived enterprise apps built by multiple teams — its opinionated structure, built-in DI, routing, forms and HTTP, and strong CLI mean everyone builds the same way, which is exactly why it suited the regulated TengizChevroil completion platform. I'd choose React instead when I want flexibility and a lighter footprint for a smaller or fast-moving team, and Next.js when SEO/first-paint matter. It's a fit decision, not a favourite."*

**Follow-ups**
- *"Angular's main trade-off?"* — More structure and a steeper learning curve, but that consistency pays off at enterprise scale.
- *"Would you start a new app in Angular today?"* — For a big multi-team enterprise build, yes — modern Angular (standalone + signals) is lean; for a small app I might pick React (see file 30).

---

## Section index

| # | Concept | One-line takeaway |
|---|---|---|
| A1 | What is Angular | A full TypeScript framework (Angular 2+); AngularJS v1 is legacy |
| A2 | Components & modules | Class + template + styles; `@Input`/`@Output` pass data in/out |
| A3 | Data binding | Four types; `[(ngModel)]` is two-way = property + event |
| A4 | Dependency injection | Angular supplies services you ask for — loose coupling, easy tests |
| A5 | Directives & pipes | `*ngIf`/`*ngFor` change DOM; pipes format displayed values |
| A6 | RxJS & Observables | Cancellable streams of many values; always unsubscribe |
| A7 | Change detection | Keeps view in sync; OnPush for performance |
| A8 | Routing & forms | Built-in router; Reactive forms for complex validation |
| A9 | App architecture | Feature + core + shared modules; teams own lazy-loaded areas |
| A10 | Performance | Lazy loading, OnPush, trackBy, async pipe, AOT |
| A11 | HTTP & the API | Interceptors add token/errors once; typed shared contracts |
| A12 | State management | Stateful service (BehaviorSubject) by default; NgRx when complex |
| A13 | Security | Auto-sanitise XSS; MSAL + guards; server re-authorises |
| A14 | Testing & build | TestBed + Jasmine/Jest + E2E; AOT bundles; CI quality gates |
| A15 | Lifecycle hooks | ngOnInit to set up; ngOnDestroy to clean up/unsubscribe |
| A16 | Signals | Simple fine-grained reactivity; complements RxJS |
| A17 | Standalone components | Import deps directly; less NgModule boilerplate |
| A18 | RxJS operators | switchMap/debounceTime/takeUntil for real screens |
| A19 | Content projection | ng-content = children; @ViewChild for child refs |
| A20 | Guards & resolvers | Guards control nav; resolvers pre-fetch data |
| A21 | Reactive forms deep | Typed model, async validators, FormArray |
| A22 | Custom pipes/directives | Reusable formatting/behaviour; pure pipes cached |
| A23 | Accessibility | Semantic HTML + CDK a11y; axe in CI |
| A24 | i18n | Built-in i18n + locale pipes for global apps |
| A25 | CLI & tooling | Scaffold, AOT build, ng update migrations |
| A26 | Common mistakes | No unsubscribe, default CD on heavy grids, early NgRx |
| A27 | Micro-frontends | Module Federation for many teams; use when scale needs it |
| A28 | Design systems | Angular Material + CDK; wrap for branding |
| A29 | SSR (Universal) | Server render for SEO/first paint; CSR fine behind login |
| A30 | When to choose Angular | Big multi-team enterprise; React for flexibility, Next for SEO |

---

[← Concept: ReactJS](28-concept-reactjs.md) · [Home](README.md) · [Next → React vs Angular](30-concept-react-vs-angular.md)
