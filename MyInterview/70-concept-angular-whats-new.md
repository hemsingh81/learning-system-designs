# 70 · Concept: Angular — What's New (Version Evolution) (30 questions)

[← React What's New](69-concept-react-whats-new.md) · [Home](README.md) · [Next → TypeScript & Frontend Tooling What's New](71-concept-typescript-tooling-whats-new.md)

This file explains **what is new in Angular** — from NgModules and Zone.js through standalone components (v14+), Signals (v16+), the new control flow (v17), `@defer`, and zoneless (v18–v20) — in simple English, with *why it matters* and *old-vs-new code*. Angular is a strong choice for large TCW enterprise apps, so I track its modern, simpler direction.

> Simple one-liner: *"Angular reinvented itself: NgModules → standalone components, Zone.js → Signals + zoneless, `*ngIf/*ngFor` → built-in `@if/@for`, plus lazy `@defer` and fast SSR/hydration. It ships every 6 months and the theme is 'simpler, faster, and less magic'."*

**Jump to (the model):** [NW1 Release cadence](#nw1--angular-release-cadence) · [NW2 AngularJS vs Angular](#nw2--angularjs-vs-modern-angular) · [NW3 How I upgrade](#nw3--how-i-upgrade-angular) · [NW4 Ivy](#nw4--the-ivy-renderer)
> **Standalone era (v14–15):** [NW5 Standalone components](#nw5--standalone-components) · [NW6 Standalone APIs](#nw6--standalone-bootstrap-and-routing) · [NW7 inject()](#nw7--the-inject-function) · [NW8 Typed forms](#nw8--typed-reactive-forms)
> **Signals era (v16–17):** [NW9 Signals](#nw9--signals) · [NW10 computed/effect](#nw10--computed-and-effect) · [NW11 Signal inputs](#nw11--signal-inputs-and-model) · [NW12 New control flow](#nw12--built-in-control-flow-ifforswitch) · [NW13 @defer](#nw13--deferrable-views-defer) · [NW14 esbuild builder](#nw14--esbuildvite-builder)
> **SSR & performance (v17–19):** [NW15 SSR + hydration](#nw15--ssr-and-non-destructive-hydration) · [NW16 View transitions](#nw16--view-transitions) · [NW17 Deferred loading strategies](#nw17--defer-triggers)
> **Zoneless era (v18–v20):** [NW18 Zoneless](#nw18--zoneless-change-detection) · [NW19 Signal-based components](#nw19--signal-based-components-and-queries) · [NW20 httpResource/resource](#nw20--resource-and-async-signals) · [NW21 What v19v20 add](#nw21--v19v20-highlights)
> **Cross-cutting:** [NW22 Change detection evolution](#nw22--change-detection-evolution) · [NW23 RxJS vs Signals](#nw23--rxjs-vs-signals) · [NW24 Standalone migration](#nw24--migrating-to-standalone) · [NW25 Control-flow migration](#nw25--migrating-to-new-control-flow) · [NW26 CLI & tooling](#nw26--cli-and-tooling-updates) · [NW27 Testing](#nw27--testing-updates)
> **Decisions:** [NW28 When to adopt](#nw28--when-i-adopt-new-angular-features) · [NW29 Upgrade risks](#nw29--upgrade-risks-and-known-issues) · [NW30 My approach](#nw30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of "what's new in Angular" in plain English. Hold these ideas and every question hangs off one of them.

**1. Angular is deliberately simplifying itself.** The last few years removed the two hardest-to-learn parts: **NgModules** (replaced by **standalone components**) and the **Zone.js magic** (replaced by **Signals + zoneless**). Modern Angular is far more approachable than the module era.

**2. It ships on a predictable 6-month cadence with LTS.** A new major every ~6 months (v17, v18, v19, v20…), each supported ~18 months (6 active + 12 LTS). Predictable, small upgrades — the `ng update` tool automates most of them.

**3. Signals are the headline shift.** A **Signal** is a reactive value; when it changes, only the views that read it update. This gives fine-grained reactivity and is the path to **zoneless** change detection — faster and easier to reason about than Zone.js dirty-checking.

**4. The template got a built-in control flow.** `*ngIf/*ngFor/*ngSwitch` became `@if/@for/@switch` — no imports, faster, with a mandatory `track` on `@for`. Plus **`@defer`** for lazy-loading parts of a template declaratively.

**5. Rendering and SSR got serious.** A new **esbuild/Vite** builder made builds much faster; **SSR with non-destructive hydration** (v16+) reuses server HTML instead of re-rendering — big load-performance and SEO wins.

**6. Old way vs new way is the interview gold.** For each shift I can state the before/after: NgModule declarations → standalone `imports`; constructor DI → `inject()`; `*ngFor` → `@for ... track`; Zone.js → Signals/zoneless; destructive hydration → non-destructive.

**7. RxJS still matters — alongside Signals.** Signals are for synchronous UI state; RxJS remains for streams/async (HTTP, events, debouncing). Knowing *which to use when* is a key modern-Angular skill.

**8. I adopt gradually with `ng update`.** Standalone and new control flow have official migration schematics, so I modernise incrementally rather than rewriting. I adopt for real simplicity/perf, not novelty.

**The full-stack / architect lens:** the later Q&As go era-by-era (standalone v14–15, Signals v16–17, SSR/hydration, zoneless v18–v20) with old-vs-new templates and TS, plus change-detection evolution, RxJS-vs-Signals, migration schematics, CLI/testing updates, and how I decide to adopt. They all trace back to the core: simpler (no modules), more reactive (Signals), faster (zoneless + esbuild + hydration) — adopted gradually with `ng update`.

**One rule I never break:** *modernise Angular gradually using the official `ng update` schematics — adopt standalone, Signals and new control flow for real simplicity and performance, never a big-bang rewrite.*

---

## NW1 · Angular release cadence

**Simple explanation.** Angular ships a **major version every ~6 months** (v14 … v20), each supported ~18 months (6 months active + 12 months LTS). Upgrades are automated with **`ng update`**.

**Architect's view:** predictable, small hops — I keep enterprise apps on a supported version and let the CLI migrate most breaking changes.

**Follow-ups**
- *How do I upgrade?* — I run `ng update @angular/core @angular/cli`, which figures out the target version, bumps the packages, and automatically runs migration schematics that rewrite my code to match the new APIs. It's not just a version bump — it actively fixes breaking changes for me, so most upgrades are a review-and-test job rather than a manual rewrite.
```bash
# checks what can be updated first (safe, read-only)
ng update
# then perform the actual upgrade + auto-migrations
ng update @angular/core @angular/cli
```
- *Do I skip versions?* — I avoid jumping several majors at once because each major ships its own migration schematics, and skipping means those code-mods never run. I step through one major at a time (v16 → v17 → v18), running tests between each hop; the official update guide at `angular.dev/update-guide` gives the exact per-version steps for the from/to pair I pick.

---

## NW2 · AngularJS vs modern Angular

**Simple explanation.** **AngularJS (1.x)** is the old, different framework (scopes, `$digest`). **Angular (2+)** is a full rewrite: TypeScript, components, DI, RxJS. They share almost nothing but a name.

**Architect's view:** any AngularJS left is pure legacy; migration is essentially a rewrite (or hybrid via ngUpgrade). All new work is modern Angular.

**Follow-ups**
- *ngUpgrade?* — `ngUpgrade` (the `@angular/upgrade` package) is a bridge that runs AngularJS (1.x) and modern Angular in the *same* app at the same time, so I can migrate one screen or component at a time instead of a risky big-bang rewrite. It lets the two frameworks share dependency injection and change detection, e.g. `downgradeComponent` exposes a new Angular component to old AngularJS templates and `upgradeComponent` does the reverse. It's a transition tool — the goal is always to finish and delete the AngularJS half.
- *Is AngularJS supported?* — No — AngularJS (1.x) reached official end-of-life at the end of 2021, so it gets no more security patches or fixes. Any AngularJS still running is pure legacy risk, and my plan for it is migration to modern Angular (via ngUpgrade or a rewrite), not maintenance.

---

## NW3 · How I upgrade Angular

**Simple explanation.** My steps: check the official **update guide**, run **`ng update`** (applies migration schematics automatically), fix any remaining warnings, run tests, then adopt new features (standalone, control flow) via their own schematics.

**Architect's view:** Angular's automated migrations make upgrades unusually smooth — most breaking changes are code-modded for me.

**Follow-ups**
- *Biggest risk?* — The biggest risk is third-party libraries lagging the new major — Angular itself upgrades cleanly via `ng update`, but a UI library, state library, or wrapper that hasn't published a compatible version can block the whole app. So before I upgrade I check each key dependency's peer-dependency range against the target Angular version, and if a critical one isn't ready I either wait or find a replacement.
- *Do schematics change my code?* — Yes — schematics are automated code-mods that edit my actual source: they rewrite templates (`*ngIf` → `@if`), convert TypeScript to new APIs (constructor DI → `inject()`), and update `angular.json`. Because they touch real code I always run them on a clean git branch and review the diff carefully, then run the test suite before committing:
```bash
git checkout -b upgrade/v18
ng update @angular/core @angular/cli
git diff        # review every schematic change
npm test
```

---

## NW4 · The Ivy renderer

**Simple explanation.** **Ivy** (default since v9) is Angular's compilation/rendering engine — smaller bundles (better tree-shaking), faster builds, and it's what makes later features (standalone, Signals) possible.

**Architect's view:** Ivy was the foundation; everything modern builds on it. Nothing to "do" — but it's why bundles shrank and features accelerated.

**Follow-ups**
- *View Engine?* — The old pre-Ivy engine, now removed.
- *Do I configure Ivy?* — No — it's the default engine.

---

## NW5 · Standalone components

**Simple explanation.** **Standalone components** (stable v15) remove the need for **NgModules** — a component declares its own `imports` directly. Less boilerplate, easier mental model.

**Old vs new.**

```ts
// OLD: NgModule declaring/importing everything
@NgModule({ declarations: [UserComp], imports: [CommonModule] })
export class UserModule {}

// NEW: standalone component
@Component({ standalone: true, imports: [CommonModule], template: `...` })
export class UserComp {}
```

**Architect's view:** standalone is now the default for new components (v17+ scaffolds standalone). It kills the "which module declares this?" confusion — a big onboarding win.

**Follow-ups**
- *Do NgModules still work?* — Yes — you can mix; migration is gradual.
- *Default now?* — From v17 the CLI generates standalone by default; from v19 `standalone: true` is implied.

---

## NW6 · Standalone bootstrap and routing

**Simple explanation.** With standalone you bootstrap via `bootstrapApplication(AppComponent, { providers: [...] })` and configure routing/HTTP with `provideRouter`, `provideHttpClient` — no root module.

```ts
bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes), provideHttpClient()]
});
```

**Old vs new.** Replaces `AppModule` + `RouterModule.forRoot` + `HttpClientModule` with functional providers.

**Architect's view:** cleaner, tree-shakable bootstrap; providers are explicit and composable.

**Follow-ups**
- *Lazy routes?* — `loadComponent`/`loadChildren` with standalone components.
- *Where do global providers go?* — In the `bootstrapApplication` providers array.

---

## NW7 · The inject() function

**Simple explanation.** **`inject()`** retrieves dependencies without a constructor — usable in field initialisers, functional guards/interceptors and composables.

```ts
// NEW
export class UserComp {
  private http = inject(HttpClient);
}
// OLD: constructor(private http: HttpClient) {}
```

**Old vs new.** Reduces constructor boilerplate and enables functional guards/interceptors and reusable "inject" helpers.

**Architect's view:** I use `inject()` for cleaner components and to build reusable functions that need DI — the modern DI style.

**Follow-ups**
- *Where can inject() run?* — In an injection context (field init, factory, functional guard).
- *Functional interceptors?* — Yes — `provideHttpClient(withInterceptors([...]))`.

---

## NW8 · Typed reactive forms

**Simple explanation.** **Typed forms** (v14) made `FormControl`/`FormGroup` strongly typed — the compiler now checks form value shapes.

```ts
const form = new FormGroup({
  name: new FormControl('', { nonNullable: true }),
  age: new FormControl<number | null>(null)
});
form.value.name; // typed as string
```

**Old vs new.** Before, form values were `any` — runtime surprises. Now the type system catches mistakes.

**Architect's view:** a real safety win on data-entry-heavy enterprise apps — fewer form bugs shipped.

**Follow-ups**
- *nonNullable?* — Guarantees the control isn't null on reset — cleaner types.
- *Migration?* — A schematic converts untyped to typed forms.

---

## NW9 · Signals

**Simple explanation.** A **Signal** (stable v17) is a reactive value: read it with `count()`, set it with `count.set(x)`, update with `count.update(fn)`. When it changes, only views that read it re-render.

```ts
count = signal(0);
inc() { this.count.update(n => n + 1); }
// template: {{ count() }}
```

**Old vs new.** Before, Angular dirty-checked the whole component tree via Zone.js. Signals give fine-grained, targeted updates.

**Architect's view:** Signals are the biggest change in years — simpler mental model and the foundation for zoneless. I use them for component/UI state.

**Follow-ups**
- *Do Signals replace RxJS?* — For sync UI state, largely; RxJS stays for async streams.
- *Read in template?* — Call it like a function: `count()`.

---

## NW10 · computed and effect

**Simple explanation.** **`computed`** derives a value from other signals (cached, auto-updating). **`effect`** runs side effects when signals it reads change.

```ts
first = signal('Ada'); last = signal('L');
full = computed(() => `${this.first()} ${this.last()}`);
constructor() { effect(() => console.log(this.full())); }
```

**Old vs new.** Replaces manual derivation and `ngOnChanges`/subscriptions for derived UI state.

**Architect's view:** `computed` for derived display values, `effect` sparingly for genuine side effects (logging, sync to storage) — not for state changes.

**Follow-ups**
- *Is computed lazy?* — Yes — recomputes only when read and a dependency changed.
- *effect for state?* — Avoid setting signals in effects; prefer computed.

---

## NW11 · Signal inputs and model

**Simple explanation.** **Signal inputs** (`input()`, `input.required()`) and **two-way `model()`** replace `@Input()`/`@Output()` decorators with signal-based, typed reactivity.

```ts
// NEW (v17.1+)
price = input.required<number>();
qty = model(1); // two-way bindable signal
```

**Old vs new.** Replaces `@Input() price!: number;` and `@Output()` + EventEmitter for two-way binding.

**Architect's view:** inputs become reactive signals — they compose with `computed`/`effect` naturally; `model()` cleans up two-way binding.

**Follow-ups**
- *Required inputs?* — `input.required()` — compiler enforces the binding is provided.
- *output()?* — A function-based replacement for `@Output()`.

---

## NW12 · Built-in control flow (@if/@for/@switch)

**Simple explanation.** **v17** added template control flow: **`@if`, `@for`, `@switch`** — built into the compiler, no `CommonModule` import, faster than the old structural directives. `@for` **requires** a `track`.

**Old vs new.**

```html
<!-- OLD -->
<div *ngIf="user">{{user.name}}</div>
<li *ngFor="let x of items; trackBy: trackId">{{x}}</li>

<!-- NEW (v17) -->
@if (user) { <div>{{user.name}}</div> }
@for (x of items; track x.id) { <li>{{x}}</li> }
```

**Architect's view:** cleaner, faster rendering, and `track` is mandatory (so list perf is correct by default). A schematic migrates existing templates.

**Follow-ups**
- *Why is track mandatory?* — It fixes the #1 `*ngFor` perf mistake automatically.
- *@empty?* — `@for` supports an `@empty {}` block for empty lists.

---

## NW13 · Deferrable views (@defer)

**Simple explanation.** **`@defer`** (v17) lazily loads part of a template (and its component's JS) on a trigger — viewport, interaction, idle, timer — with `@placeholder`/`@loading`/`@error` blocks.

```html
@defer (on viewport) {
  <heavy-chart />
} @placeholder { <div>Scroll to load…</div> }
```

**Old vs new.** Before, lazy-loading a heavy component meant manual dynamic imports/routing tricks. `@defer` makes it declarative in the template.

**Architect's view:** great for below-the-fold heavy widgets (charts, maps) on dashboards — smaller initial bundle, faster first load.

**Follow-ups**
- *Triggers?* — `on idle`, `on viewport`, `on interaction`, `on timer`, `on hover`, or `when <condition>`.
- *Prefetch?* — `prefetch on idle` loads early without rendering yet.

---

## NW14 · esbuild/Vite builder

**Simple explanation.** Angular replaced the old Webpack builder with an **esbuild-based application builder** (default v17) — much faster builds and a Vite-powered dev server with fast HMR.

**Old vs new.** Webpack builds were slow; esbuild cut build and rebuild times dramatically.

**Architect's view:** faster CI and dev loop for free on upgrade — I switch to the application builder as part of modernising.

**Follow-ups**
- *Do I change config?* — The `ng update` path migrates `angular.json` to the new builder.
- *Custom Webpack?* — Rare cases still need it; most apps move to esbuild.

---

## NW15 · SSR and non-destructive hydration

**Simple explanation.** Angular's SSR (Angular Universal, now built into the CLI) added **non-destructive hydration** (v16) — the client **reuses** the server-rendered DOM instead of throwing it away and re-rendering.

**Old vs new.** Old hydration was *destructive* (re-rendered everything — flicker, wasted work). Non-destructive hydration reuses the HTML — faster, no flash.

**Architect's view:** big win for load performance and SEO on public-facing pages; `ng add @angular/ssr` sets it up.

**Follow-ups**
- *Incremental hydration?* — Newer versions hydrate on interaction/viewport (with `@defer`), hydrating only what's needed.
- *Enable hydration?* — `provideClientHydration()` in bootstrap.

---

## NW16 · View transitions

**Simple explanation.** Angular integrated the browser **View Transitions API** into the router — smooth animated transitions between routes with `withViewTransitions()`.

```ts
provideRouter(routes, withViewTransitions());
```

**Old vs new.** Before, route animations needed Angular's animation package and setup. Now the router taps the native API.

**Architect's view:** nicer UX with minimal code where the browser supports it (progressive enhancement).

**Follow-ups**
- *Browser support?* — Progressive — falls back gracefully.
- *Fine control?* — CSS `::view-transition` styles the animation.

---

## NW17 · @defer triggers

**Simple explanation.** `@defer` supports several loading strategies: **`on idle`** (default), **`on viewport`**, **`on interaction`**, **`on hover`**, **`on timer(ms)`**, and **`when <expr>`**, plus **`prefetch`** variants.

**Architect's view:** I match the trigger to intent — `on viewport` for below-the-fold charts, `on interaction` for modals, `prefetch on idle` to warm up likely-needed code.

**Follow-ups**
- *Combine triggers?* — Yes — e.g. `prefetch on idle; on viewport`.
- *Server rendering + defer?* — Works with incremental hydration.

---

## NW18 · Zoneless change detection

**Simple explanation.** **Zoneless** (developer preview v18, maturing v19–v20) removes **Zone.js** — Angular updates based on **Signals** and explicit notifications instead of monkey-patching every async API.

**Old vs new.** Before, Zone.js patched setTimeout/promises/events to trigger dirty-checking of the whole tree — heavy and "magic". Zoneless is lighter and only updates what changed.

**Architect's view:** the destination of the Signals journey — better performance, smaller bundle (no Zone.js), simpler debugging. I adopt it once my components are Signal-based.

**Follow-ups**
- *Enable it?* — `provideZonelessChangeDetection()` (preview) and drop the `zone.js` polyfill.
- *Do I need Signals first?* — Yes — zoneless relies on signal-driven updates.

---

## NW19 · Signal-based components and queries

**Simple explanation.** Signal-based APIs extended to component queries: **`viewChild()`, `viewChildren()`, `contentChild()`** as signals, replacing the `@ViewChild` decorator.

```ts
// NEW
chart = viewChild<ChartComp>('chart');
// OLD: @ViewChild('chart') chart!: ChartComp;
```

**Old vs new.** Query results become signals — reactive and composable with `computed`/`effect`.

**Architect's view:** consistent signal model across inputs, outputs, and queries — the component API is converging on signals.

**Follow-ups**
- *Timing?* — Signal queries resolve after the view initialises; read them in effects.
- *Still support decorators?* — Yes — both work during transition.

---

## NW20 · resource() and async signals

**Simple explanation.** **`resource()`/`httpResource()`** (experimental, v19+) load async data into signals — a signal-native way to fetch, with loading/error state, bridging RxJS/HTTP and Signals.

**Old vs new.** Before, async data meant an Observable + `async` pipe or manual subscribe. `resource()` exposes it as signals.

**Architect's view:** promising for signal-first data flows; I watch it mature before production use, and still use RxJS/`toSignal` where appropriate.

**Follow-ups**
- *toSignal/toObservable?* — Interop helpers to convert between Observables and Signals.
- *Production-ready?* — Experimental — I trial it, not critical path yet.

---

## NW21 · v19/v20 highlights

**Simple explanation.** Recent majors focused on stabilising the modern stack: **standalone by default** (implied), maturing **zoneless**, **incremental hydration**, signal APIs stabilising, and performance/DX polish.

**Architect's view:** v19/v20 are about *finishing* the Signals/standalone/zoneless story — the framework I recommend for new enterprise apps.

**Follow-ups**
- *standalone: true still needed?* — From v19 it's the default — you omit the flag.
- *Should new apps be zoneless?* — Increasingly yes as it matures; check library support.

---

## NW22 · Change detection evolution

**Simple explanation.** The journey: **default (Zone.js dirty-checking)** → **`OnPush`** (check only on input/observable change) → **Signals** (fine-grained) → **zoneless** (no Zone.js at all).

**Old vs new.** Each step narrows *what* gets checked and *when* — from "check everything on any async event" to "update only what actually changed".

**Architect's view:** on existing apps I use `OnPush` everywhere as the near-term win; new apps go Signals → zoneless for the best performance.

**Follow-ups**
- *OnPush pitfalls?* — Mutating objects in place won't trigger updates — use immutable updates or signals.
- *Do Signals need OnPush?* — They work best with it and are the bridge to zoneless.

---

## NW23 · RxJS vs Signals

**Simple explanation.** **Signals** = synchronous reactive *values* (UI state) — simple, glitch-free. **RxJS** = asynchronous *streams* (HTTP, events, debounce, combine) — powerful operators. They coexist.

**Old vs new.** Before Signals, RxJS was used even for simple sync state (heavy). Now Signals handle that; RxJS stays for async.

**Architect's view:** my rule — **Signals for state, RxJS for streams**; convert between them with `toSignal`/`toObservable`. This keeps components simpler.

**Follow-ups**
- *Debounced search?* — RxJS (`debounceTime`, `switchMap`), then `toSignal` for the template.
- *Is RxJS going away?* — No — it remains for async; Angular just stopped over-using it for sync state.

---

## NW24 · Migrating to standalone

**Simple explanation.** Angular ships an official **standalone migration schematic** (`ng generate @angular/core:standalone`) that runs in steps: convert components, remove NgModules, then bootstrap standalone.

**Architect's view:** I run it module-by-module, review the diff, and test — gradual, not big-bang. Mixed module+standalone works during the transition.

**Follow-ups**
- *Order of steps?* — Convert declarations to standalone → remove unnecessary NgModules → switch bootstrap.
- *Third-party modules?* — You can still import a library's NgModule from a standalone component.

---

## NW25 · Migrating to new control flow

**Simple explanation.** A schematic (`ng generate @angular/core:control-flow`) rewrites `*ngIf/*ngFor/*ngSwitch` to `@if/@for/@switch` automatically, adding required `track` expressions.

**Architect's view:** low-risk automated migration; I run it, review, and drop the now-unneeded `CommonModule` imports.

**Follow-ups**
- *Does it pick a good track?* — It infers `track` (often the item or index) — I review for correctness (prefer a stable id).
- *Can I mix old and new?* — Yes during transition.

---

## NW26 · CLI and tooling updates

**Simple explanation.** The **Angular CLI** gained the esbuild application builder, `ng add`/`ng update` schematics, better standalone scaffolding, and improved SSR setup (`ng add @angular/ssr`).

**Architect's view:** the CLI is Angular's superpower — automated upgrades and consistent project structure across teams. I lean on it heavily for governance at scale.

**Follow-ups**
- *ng add vs npm install?* — `ng add` installs *and* runs setup schematics.
- *Nx?* — For monorepos I often layer Nx on top of the CLI.

---

## NW27 · Testing updates

**Simple explanation.** Angular is moving the default test runner from **Karma** (deprecated) toward modern runners (Jest/Web Test Runner/Vitest experimental), plus better harnesses for component testing.

**Old vs new.** Karma/Jasmine was slow; the ecosystem is shifting to faster runners.

**Architect's view:** for new apps I use a modern runner (Jest today) for speed; I watch the official runner direction and component test harnesses.

**Follow-ups**
- *Component Harnesses?* — Material CDK harnesses give stable, implementation-agnostic component tests.
- *E2E?* — Protractor is dead — use Cypress/Playwright.

---

## NW28 · When I adopt new Angular features

**Simple explanation.** My rule: adopt when it **simplifies** (standalone, `inject`), **improves performance** (Signals, zoneless, `@defer`, hydration), or **improves safety** (typed forms) — using the official schematics, gradually.

**Architect's view:** upgrade the version early (CLI makes it safe), then adopt features where they pay off. For a big existing app I sequence: `OnPush` → standalone → new control flow → Signals → zoneless.

**Follow-ups**
- *First modernisation step?* — Standalone + new control flow (both automated).
- *Zoneless yet?* — New apps yes as it matures; large legacy apps after Signal adoption.

---

## NW29 · Upgrade risks and known issues

**Simple explanation.** Risks: **third-party libraries** lagging the new major, **breaking changes** in RxJS/TypeScript peer versions, **builder migration** edge cases (custom Webpack), and **Zone.js assumptions** when going zoneless.

**Architect's view:** I mitigate with `ng update` (auto-migrations), checking library compatibility first, testing after each hop, and adopting zoneless only once components are Signal-ready.

**Follow-ups**
- *Most common blocker?* — A key library not yet supporting the target major.
- *Zoneless gotcha?* — Code relying on Zone.js patching (some third-party) needs updating.

---

## NW30 · My approach

**Simple explanation.** I keep Angular on a **supported version**, upgrade with **`ng update`** (automated migrations), and modernise **gradually**: standalone components, `inject()`, typed forms, built-in control flow, `@defer`, Signals, and eventually zoneless — using **Signals for state, RxJS for streams**. For every feature I know the old way and the new way.

**Architect's view:** Angular's direction is unmistakable — simpler (no modules), more reactive (Signals), faster (zoneless + esbuild + hydration). For large TCW enterprise apps that's ideal: strong structure with far less ceremony. I ride the direction with the CLI's automated migrations, adopting each feature for real simplicity or performance, never a big-bang rewrite.

**Follow-ups**
- *One-sentence philosophy?* — "Upgrade with the CLI, modernise gradually, Signals for state."
- *Angular or React for a new app?* — Angular for large, structured enterprise apps with many teams; React for flexibility/lighter apps — both are strong.

---

## Section index

| ID | Topic | Core message |
|----|-------|--------------|
| NW1 | Release cadence | Major every ~6 months; `ng update` automates |
| NW2 | AngularJS vs Angular | 1.x is legacy; 2+ is a different framework |
| NW3 | How I upgrade | Update guide + `ng update` schematics + test |
| NW4 | Ivy | Engine enabling smaller bundles + modern features |
| NW5 | Standalone components | No NgModules; component declares its imports |
| NW6 | Standalone bootstrap | `bootstrapApplication` + functional providers |
| NW7 | inject() | DI without constructors; functional guards |
| NW8 | Typed forms | Compiler-checked form value shapes |
| NW9 | Signals | Fine-grained reactive values |
| NW10 | computed/effect | Derived values + side effects on signal change |
| NW11 | Signal inputs/model | input()/model() replace @Input/@Output |
| NW12 | Control flow | @if/@for/@switch; track mandatory |
| NW13 | @defer | Declarative lazy-load parts of a template |
| NW14 | esbuild builder | Much faster builds + Vite dev server |
| NW15 | SSR + hydration | Non-destructive hydration reuses server HTML |
| NW16 | View transitions | Native animated route transitions |
| NW17 | @defer triggers | idle/viewport/interaction/timer + prefetch |
| NW18 | Zoneless | Remove Zone.js; update via Signals |
| NW19 | Signal queries | viewChild()/contentChild() as signals |
| NW20 | resource() | Signal-native async data (experimental) |
| NW21 | v19/v20 | Standalone default; zoneless/hydration maturing |
| NW22 | Change detection | Default → OnPush → Signals → zoneless |
| NW23 | RxJS vs Signals | Signals for state, RxJS for streams |
| NW24 | Standalone migration | Automated schematic, step by step |
| NW25 | Control-flow migration | Schematic rewrites to @if/@for with track |
| NW26 | CLI/tooling | esbuild builder, ng add/update, SSR setup |
| NW27 | Testing | Karma deprecated; move to Jest/modern runners |
| NW28 | When to adopt | Simpler/faster/safer via official schematics |
| NW29 | Upgrade risks | Lib lag, peer versions, builder/zoneless edges |
| NW30 | My approach | Upgrade with CLI, modernise gradually, Signals for state |

---

[← React What's New](69-concept-react-whats-new.md) · [Home](README.md) · [Next → TypeScript & Frontend Tooling What's New](71-concept-typescript-tooling-whats-new.md)
