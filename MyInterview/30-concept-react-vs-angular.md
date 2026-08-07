# 30 · Concept: React vs Angular (30 questions)

[← Concept: Angular](29-concept-angular.md) · [Home](README.md) · [Next → Concept: ASP.NET Core Web API](31-concept-aspnet-webapi.md)

This file compares **React** and **Angular** simply and fairly. I've shipped both — React on TCW (A), Angular on TengizChevroil (C) — so I answer as someone who chose each for a reason, not a fan of one.

> Simple one-liner: *"React is a flexible **library** — you assemble your own stack. Angular is a complete **framework** — it gives you everything and a structure. React wins on flexibility and ecosystem; Angular wins on consistency for big teams."*

**Jump to (core):** [V1 Core difference](#v1--the-core-difference) · [V2 Side-by-side table](#v2--side-by-side-comparison) · [V3 Language & structure](#v3--language-and-structure) · [V4 Data flow & state](#v4--data-flow-and-state) · [V5 Learning curve & team](#v5--learning-curve-and-team-fit) · [V6 Which would you choose](#v6--which-would-you-choose)
> **Architecture & full-stack lens:** [V7 Rendering & performance](#v7--rendering-model-and-performance) · [V8 Talking to the API](#v8--talking-to-the-back-end) · [V9 Scaling to big teams](#v9--scaling-to-large-codebases-and-teams) · [V10 Migration & coexistence](#v10--migration-and-coexistence)
> **Feature-by-feature:** [V11 Components](#v11--components-jsx-vs-templates) · [V12 Forms](#v12--forms) · [V13 Routing](#v13--routing) · [V14 DI](#v14--dependency-injection) · [V15 Reactivity](#v15--reactivity-hooks-vs-rxjs-signals) · [V16 Tooling & CLI](#v16--tooling-and-cli) · [V17 Testing](#v17--testing) · [V18 SSR](#v18--ssr-nextjs-vs-universal)
> **Ecosystem & decisions:** [V19 Ecosystem](#v19--ecosystem-and-longevity) · [V20 Bundle & load](#v20--bundle-size-and-load-time) · [V21 Hiring](#v21--hiring-and-team-availability) · [V22 Mobile](#v22--mobile-story) · [V23 Upgrades](#v23--upgrades-and-maintenance) · [V24 Design systems](#v24--design-systems) · [V25 Security](#v25--security-parity) · [V26 Accessibility](#v26--accessibility)
> **Judgement:** [V27 What's the same](#v27--what-is-actually-the-same) · [V28 Common myths](#v28--common-myths-i-correct) · [V29 Cost/TCO](#v29--cost-and-total-cost-of-ownership) · [V30 My decision framework](#v30--my-one-minute-decision-framework) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of comparing React and Angular in plain English. I've shipped both — React on TCW (A), Angular on TengizChevroil (C) — so I frame this as the *axes I compare on*, not a fan cheering for one side. Hold these ideas and every question below is a detail hanging off one of them.

**1. Library vs framework is the root of everything.** React is a **library** that does the view well and lets me assemble the rest (router, data layer, state). Angular is a **complete framework** that ships routing, forms, HTTP and DI in one opinionated box. Almost every other difference — flexibility, consistency, learning curve — flows straight out of this one fact.

**2. The axes I actually compare on.** I never argue "which is better" in the abstract. I score both on a fixed set of axes: flexibility, consistency, team size and skill, hiring pool, ecosystem depth, bundle size, testing story, and long-term maintenance. React wins some axes; Angular wins others. The *project* decides which axes matter most.

**3. Language and structure.** React is JavaScript/TypeScript with JSX — markup and logic live together, and structure is whatever I impose. Angular is TypeScript-first with templates, decorators and a prescribed file structure. Angular's structure is a gift on a big team and a tax on a tiny one.

**4. Data flow and reactivity.** React uses one-way data flow with hooks (and libraries like Redux/Zustand/React Query for bigger state). Angular gives two-way binding, RxJS and now signals built in. Both end up reactive; the difference is whether reactivity is something I *choose* (React) or something *handed to me* (Angular).

**5. Ecosystem vs batteries-included.** React's flexibility means a huge, fast-moving ecosystem — I pick best-of-breed parts but I own the choices and the churn. Angular gives fewer decisions and a coherent, versioned upgrade path — less freedom, more predictability.

**6. Team and hiring reality.** React has the larger hiring pool and shorter ramp-up for JS developers; Angular rewards teams that value one enforced way of doing things. On C, Angular's consistency kept a large, rotating team aligned; on A, React's flexibility let a small team move fast.

**7. The things that are actually the same.** Both are component-based, both do SSR, both are secure when used correctly, both scale to large apps, and both have strong tooling. Most "X is faster/safer than Y" claims are myths — the real differences are ergonomic and organisational, not capability.

**The full-stack / architect lens:** the later Q&As go deeper — rendering models and performance, talking to the back end, scaling to large codebases, migration and coexistence, bundle size and load time, mobile story, accessibility, security parity, and total cost of ownership. That's where a senior answer lives: not "I like React" but "here's how each choice plays out in production over years."

**One rule I never break:** *choose the framework that fits the team and the problem, not the one I personally enjoy — and be able to defend the choice on the axes, in one minute.*

---

## V1 · The core difference

**Simple explanation.** The single biggest difference: **React is a library, Angular is a framework.**

- **React** does one job well — the view. You add your own router (React Router), data layer (React Query), and state tool (Redux/Zustand). Maximum flexibility, but *you* make the decisions.
- **Angular** is the whole package — routing, forms, HTTP, dependency injection, all built in and structured. Fewer decisions, more consistency, but more opinionated.

*"I think of it as: React is a set of great parts I assemble; Angular is a pre-built car."*

**Follow-ups**
- *"Is one 'better'?"* — No — they solve the same problem differently. The right pick depends on team size, timeline and how much structure you want.
- *"Which is more popular?"* — React has the larger ecosystem and job market; Angular is strong in large enterprises.

---

## V2 · Side-by-side comparison

| Aspect | React | Angular |
|---|---|---|
| Type | Library (view only) | Full framework |
| Made by | Meta | Google |
| Language | JavaScript / **TypeScript** | **TypeScript** (first-class) |
| DOM | Virtual DOM + diffing | Real DOM + change detection (Zone.js) |
| Data flow | One-way | One-way + optional two-way (`[(ngModel)]`) |
| Routing / HTTP / forms | Add libraries yourself | Built in |
| State | useState/Context + libraries | Services + RxJS (+ NgRx) |
| Structure | You decide | Enforced, opinionated |
| Learning curve | Gentler start | Steeper (DI, RxJS, modules) |
| Best for | Flexibility, fast start, big ecosystem | Large teams needing consistency |

**Follow-ups**
- *"Both use TypeScript?"* — Angular is TypeScript-first; React works great with TypeScript too (I always use it) but doesn't require it.
- *"Both component-based?"* — Yes — both build UIs from reusable components; the plumbing around them differs.

---

## V3 · Language and structure

**Simple explanation.** React is unopinionated — two React projects can look totally different in folder layout and libraries. Angular is opinionated — it dictates structure (components, services, modules), uses **decorators** (`@Component`, `@Injectable`), and has a CLI that scaffolds everything the same way.

**Trade-off:** React's freedom means faster starts but the team must agree on conventions; Angular's structure means slower onboarding but instant consistency across a big codebase.

**Follow-ups**
- *"Why does structure matter on a big team?"* — On TengizChevroil (multi-team, regulated), Angular's enforced structure meant any engineer could open any module and know where things live.
- *"Downside of React's freedom?"* — Without discipline, projects drift into inconsistent patterns — so I set conventions early.

---

## V4 · Data flow and state

**Simple explanation.** Both favour **one-way data flow** (data down, events up), which keeps apps predictable. Angular *also* offers **two-way binding** (`[(ngModel)]`) for convenience. For state, React uses hooks + Context or a library; Angular uses **services + RxJS** (and NgRx for large apps).

My shared principle on both: **treat server data as a cache**, not app state — React Query on React, cached service Observables on Angular.

**Follow-ups**
- *"Is two-way binding bad?"* — Not bad — convenient for forms — but overuse can hide where data changes. React avoids it on purpose.
- *"React Query equivalent in Angular?"* — RxJS with caching operators, or libraries like TanStack Query (now framework-agnostic).

---

## V5 · Learning curve and team fit

**Simple explanation.** **React is easier to start** — learn components, props, state, and you're productive. The complexity comes later when you assemble the ecosystem. **Angular is harder to start** — you meet DI, RxJS, decorators and modules early — but once learned, everything is consistent.

**Team fit:** small/fast-moving teams and startups often pick React; large enterprises with many teams often pick Angular for the guardrails.

**Follow-ups**
- *"What trips people up in Angular?"* — RxJS Observables and change detection — they're powerful but a mental shift.
- *"What trips people up in React?"* — `useEffect` dependencies and stale closures — subtle re-render bugs.

---

## V6 · Which would you choose?

**How I answer (the mature take).** *"It depends on the context, and I've genuinely chosen both."*

- **I'd pick React** for a product needing flexibility, a fast start, a rich ecosystem, or where the team is smaller and comfortable assembling their stack — like the TCW reporting screens where I wanted lightweight, typed, reusable components.
- **I'd pick Angular** for a large, multi-team, long-lived enterprise app that benefits from enforced structure, built-in tooling and DI — like the TengizChevroil completion platform.

*"The worst answer is 'React because it's popular'. The right answer names the context and the trade-off."*

**Follow-ups**
- *"One-word summary?"* — React = flexibility; Angular = consistency.
- *"Can you migrate between them?"* — Not trivially — they're architecturally different — so the choice is a real commitment; I make it deliberately up front.

---

## V7 · Rendering model and performance

**Simple explanation (architect lens).** They keep the screen in sync differently:
- **React** builds a **Virtual DOM** and diffs it, updating only changed nodes. You tune re-renders with `memo`/`useMemo`/`useCallback`.
- **Angular** runs **change detection** over the component tree (Zone.js), and you tune it with **OnPush** and `trackBy`.

**Performance verdict:** both are fast when used well; both slow down the same way — too many re-renders/checks on data-heavy screens — and both solve it the same way: skip unnecessary work and **virtualise large lists**. The framework is rarely the bottleneck; the data volume and network are.

**Follow-ups**
- *"Which is faster out of the box?"* — Comparable for real apps. Bundle size and first load matter more than raw render speed — both need code-splitting/lazy-loading.
- *"Same fix for big grids?"* — Yes — virtualisation (render only visible rows) plus memoisation/OnPush on both.

---

## V8 · Talking to the back end

**Simple explanation (full-stack lens).** From my ASP.NET Core Web API's point of view, both are just HTTP clients — the contract is identical:
- **React:** a typed fetch/Axios client, usually with **React Query** for caching/retries.
- **Angular:** the built-in `HttpClient` with **interceptors** for the token and errors, returning Observables.

**What I do identically on both:** attach the **Entra ID bearer token**, share one error shape with the API, and generate **TypeScript DTOs from the API's OpenAPI spec** so the front and back never drift. The front-end framework choice doesn't change the API design at all.

**Follow-ups**
- *"Does the API care which one you use?"* — No — it exposes REST/JSON; either consumes it the same way. That decoupling is deliberate.
- *"Auth handling difference?"* — React: an Axios interceptor or wrapper; Angular: a built-in `HttpInterceptor`. Same idea, framework-specific mechanism.

---

## V9 · Scaling to large codebases and teams

**Simple explanation.** This is where the library-vs-framework difference really bites:
- **Angular** enforces structure (modules, DI, CLI), so a big, multi-team codebase stays consistent by default — why it fit **TengizChevroil**'s regulated, multi-team build.
- **React** gives freedom, so a large team must **agree conventions early** (folder structure, state approach, lint rules) or it drifts — I set those guardrails up front on **TCW**.

**Architect takeaway:** with Angular consistency is free; with React consistency is a choice you must enforce with tooling and code review.

**Follow-ups**
- *"How do you keep a big React app consistent?"* — Strict ESLint rules, a shared component library, a documented folder convention, and PR review — tooling replaces the framework's guardrails.
- *"Angular downside at scale?"* — More boilerplate and a steeper onboarding curve (DI, RxJS) — the price of the enforced structure.

---

## V10 · Migration and coexistence

**Simple explanation.** Migrating between them is a **rewrite**, not a port — they're architecturally different (JSX + hooks vs decorators + DI + RxJS). So I don't switch casually.

**Pragmatic approaches when you must move:** run both side by side behind routing (each owns different pages), or use micro-front-ends / **web components** so a shared widget works in either shell — the same **strangler-fig** thinking I use for back-end modernisation: migrate page by page, never big-bang.

**Follow-ups**
- *"Big-bang rewrite — good idea?"* — Almost never — high risk. Incremental, route-by-route migration with both running keeps the business live.
- *"Can a component be shared across both?"* — Via web components (custom elements) you can wrap a widget that both frameworks host — useful during a transition.

---

## V11 · Components: JSX vs templates

**Simple explanation.** **React** writes markup as **JSX** inside the component — logic and view live together in TypeScript. **Angular** separates the **HTML template** from the component class, using its own template syntax (`*ngIf`, `*ngFor`, `[prop]`, `(event)`).

**Trade-off:** JSX feels natural to JS developers and keeps everything in one language; Angular's separation suits designers editing HTML and enforces a clear split.

**Follow-ups**
- *"Which is more powerful?"* — Comparable — JSX is 'just JavaScript' so any logic is easy; Angular templates are safer/typed but need special syntax.
- *"Which do juniors prefer?"* — JS-first devs like JSX; those from a designer/HTML background often like Angular's separation.

---

## V12 · Forms

**Simple explanation.** **Angular** has forms **built in** — Reactive Forms give a typed model, validators and `FormArray` out of the box. **React** has no built-in forms; I add **React Hook Form + Zod**. Both end up powerful; Angular includes it, React composes it.

**Follow-ups**
- *"Which is less work for complex forms?"* — Roughly equal once you add RHF to React — Angular just ships it by default.
- *"Where does validation truly run?"* — Both validate on the client for UX, but the **API re-validates** on both — identical principle.

---

## V13 · Routing

**Simple explanation.** **Angular Router** is built in — nested routes, guards, resolvers, lazy loading. **React** adds **React Router** for the same features. Same capabilities; one is included, one is a library.

**Follow-ups**
- *"Guards vs wrappers?"* — Angular uses `canActivate` guards; React uses wrapper components — same outcome, and the **API still authorises** on both.
- *"Lazy-loaded routes on both?"* — Yes — both split code per route to shrink first load.

---

## V14 · Dependency injection

**Simple explanation (architect lens).** **Angular has a powerful built-in DI system** — services are injected via the constructor, which makes swapping implementations and testing easy. **React has no DI**; it uses **props, Context, and custom hooks** to share dependencies. Angular's DI is a genuine differentiator for large apps.

**Follow-ups**
- *"Why does DI help at scale?"* — It decouples components from concrete services and makes mocking in tests trivial — great for big, layered codebases.
- *"React's equivalent?"* — Context + custom hooks approximate it, but it's a convention, not a framework feature.

---

## V15 · Reactivity: hooks vs RxJS/signals

**Simple explanation.** **React** reacts through **hooks** (`useState`/`useEffect`) and re-renders components. **Angular** reacts through **RxJS Observables** (async streams) and now **signals** (fine-grained). RxJS is more powerful for complex async but has a steeper curve; hooks are simpler to pick up.

**Follow-ups**
- *"Steeper learning?"* — RxJS — stream thinking is a mental shift; hooks are easier but have their own trap (dependency arrays/stale closures).
- *"Are signals closing the gap?"* — Yes — Angular signals feel closer to simple reactive state, similar in spirit to React state.

---

## V16 · Tooling and CLI

**Simple explanation.** **Angular CLI** is a strong, unified tool — scaffold, build (AOT), test, and `ng update` migrations. **React** uses **Vite** (or Next.js tooling) plus separately-chosen tools; more flexible, less unified.

**Follow-ups**
- *"Biggest CLI advantage?"* — `ng update` automates framework upgrades with migration scripts — a real maintenance win at scale.
- *"React tooling downside?"* — You assemble/upgrade tools yourself — flexible but more decisions and coordination.

---

## V17 · Testing

**Simple explanation.** Both test well. **React**: Jest/Vitest + **React Testing Library** (test behaviour, not internals) + Playwright for E2E. **Angular**: **TestBed** + Jasmine/Karma (or Jest) + Playwright/Cypress. Angular includes a testing setup; React composes one.

**Follow-ups**
- *"Same philosophy?"* — Yes — test what the user sees, mock the API, keep unit tests fast, few E2E on critical journeys.
- *"Which is easier to set up?"* — Angular ships a test config; React's is quick with Vitest + RTL — roughly even.

---

## V18 · SSR: Next.js vs Universal

**Simple explanation.** For server-side rendering (SEO, fast first paint): **React → Next.js** (the mature, dominant SSR framework), **Angular → Angular Universal**. Next.js is more widely adopted and feature-rich for SSR/SSG; Universal is solid but less ubiquitous.

**Follow-ups**
- *"When does SSR matter?"* — Public, SEO-sensitive, or first-paint-critical sites — not for authenticated internal apps like mine.
- *"Edge on SSR?"* — React via Next.js — its SSR/SSG ecosystem is the industry benchmark.

---

## V19 · Ecosystem and longevity

**Simple explanation.** **React** has the **larger ecosystem** and community — more libraries, examples, and hires — backed by Meta. **Angular** has a **cohesive, Google-backed** ecosystem where official packages cover most needs. Both are stable, long-lived, and safe enterprise bets.

**Follow-ups**
- *"Any risk either disappears?"* — Low — both are mature, widely used, and corporate-backed. Neither is a risky choice.
- *"More third-party choices?"* — React — more options, but you must vet quality; Angular's first-party packages reduce that burden.

---

## V20 · Bundle size and load time

**Simple explanation.** A minimal **React** app ships a smaller baseline than a full **Angular** app, because Angular bundles more framework. In practice both are fine when you **lazy-load, code-split, tree-shake, and set a size budget** — the app's own code and data usually dwarf the framework difference.

**Follow-ups**
- *"Does the framework decide load time?"* — Rarely — your bundle discipline and payload size matter far more than React-vs-Angular.
- *"Same optimisations?"* — Yes — lazy routes, code-split, tree-shake, CI size budget on both.

---

## V21 · Hiring and team availability

**Simple explanation (architect lens).** **React developers are more numerous** in the market, so hiring/onboarding is often faster. **Angular** skills are common in enterprise/regulated sectors. I factor the *available team* into the decision — the best framework is one the team can build and maintain well.

**Follow-ups**
- *"Would hiring alone decide it?"* — It's a real input, not the only one — I weigh it with app type, team size and longevity.
- *"Upskilling cost?"* — React onboards faster; Angular takes longer (DI/RxJS) but yields high consistency — I budget for it.

---

## V22 · Mobile story

**Simple explanation.** **React → React Native** lets you reuse React skills to build native mobile apps — a big strategic plus. **Angular → Ionic** (web-tech hybrid) or NativeScript. React's mobile path (React Native) is more mainstream.

**Follow-ups**
- *"Share code web + mobile?"* — React Native shares logic/patterns (not DOM markup) with React web — partial reuse. Angular+Ionic reuses web components in a hybrid shell.
- *"Does this affect the choice?"* — If a native mobile app is on the roadmap, React's ecosystem tilts the decision.

---

## V23 · Upgrades and maintenance

**Simple explanation.** **Angular** offers a predictable release cadence and **`ng update`** migration tooling — upgrades are structured. **React** upgrades are usually small for React itself, but you separately track your assembled libraries. Angular centralises upgrade pain; React distributes it.

**Follow-ups**
- *"Which is lower long-term maintenance?"* — Angular's unified upgrades help big apps; React needs discipline to keep many libraries current.
- *"Breaking changes?"* — Both manage them well; Angular's migration scripts automate much of the churn.

---

## V24 · Design systems

**Simple explanation.** **Angular** has first-party **Angular Material** (accessible, themeable) — a quick consistent design system. **React** picks from many (MUI, Ant, Fluent, Chakra) — more choice, more decisions. Both support building a custom system + Storybook.

**Follow-ups**
- *"Fastest to a consistent UI?"* — Angular Material out of the box; React needs you to pick a library first, then equally fast.
- *"Custom system on both?"* — Yes — shared tokens + component library + Storybook works identically on either.

---

## V25 · Security parity

**Simple explanation.** Security is **essentially the same** on both because the real boundary is the API. Angular **auto-sanitises** template bindings against XSS; React escapes JSX by default (danger only via `dangerouslySetInnerHTML`). Both use the Entra ID token pattern; both never trust the client.

**Follow-ups**
- *"Any security edge?"* — Marginal — Angular's built-in sanitisation is convenient, but disciplined React is equally safe. The **API enforces authorisation** on both.
- *"Where do people get it wrong?"* — Putting trust/business rules on the client on either framework — the API must always re-check.

---

## V26 · Accessibility

**Simple explanation.** Accessibility is a **discipline, not a framework feature** — semantic HTML, keyboard, ARIA, contrast apply equally. **Angular CDK a11y** and React a11y libraries both help; I run **axe/Lighthouse in CI** on both.

**Follow-ups**
- *"Does either make a11y easier?"* — Angular CDK gives ready focus-management utilities; React has equivalents — the outcome depends on the team, not the framework.
- *"First step on both?"* — Semantic HTML — most accessibility comes free from correct markup.

---

## V27 · What is actually the same

**Simple explanation (balanced view).** People overstate the differences. Both are **component-based**, **TypeScript-friendly**, favour **one-way data flow**, are **fast when tuned**, **consume the same REST/JSON API the same way**, need the **same performance work** (virtualisation, code-splitting), and share the **same security model** (API is the boundary). The *view layer plumbing* differs; the architecture around it is nearly identical.

**Follow-ups**
- *"So the choice is smaller than people think?"* — Often yes — team, structure and ecosystem drive it more than raw capability.
- *"Does my API change?"* — No — I design the ASP.NET Core API identically regardless of the front-end pick.

---

## V28 · Common myths I correct

**Simple explanation.** Myths I gently correct: *"React is always faster"* (comparable when tuned), *"Angular is dead"* (very much alive — signals/standalone modernised it), *"AngularJS = Angular"* (totally different — v1 vs v2+), *"Angular is too heavy"* (lazy-loading fixes bundle size), *"React needs Redux"* (Context/React Query cover most apps).

**Follow-ups**
- *"Biggest myth?"* — Conflating AngularJS with modern Angular — they're separate frameworks a decade apart.
- *"React always needs Redux?"* — No — most apps do fine with Context + React Query; reach for Redux/Zustand only for genuinely complex global state.

---

## V29 · Cost and total cost of ownership

**Simple explanation (architect lens).** I weigh **TCO**, not just build speed: hiring/onboarding cost, long-term maintenance and upgrades, consistency at scale, and ecosystem risk. **React** can be cheaper to start and staff; **Angular** can be cheaper to maintain consistently across many teams. The 'cheaper' one depends on team size and app lifespan.

**Follow-ups**
- *"Short project vs 10-year platform?"* — Short/small → React's fast start; long-lived multi-team → Angular's structure often wins on TCO.
- *"Hidden cost of React?"* — Governance — you pay in conventions, lint rules and reviews to keep a big codebase consistent.

---

## V30 · My one-minute decision framework

**How I answer (the crisp close).** *"I ask five questions: (1) Team size and skills? (2) App lifespan — short product or 10-year platform? (3) How much structure does the team want? (4) SEO/first-paint needed? (5) Mobile on the roadmap? If it's a large, multi-team, long-lived enterprise app wanting guardrails, I lean **Angular** (TengizChevroil). If it's flexible, fast-moving, ecosystem-heavy, or mobile is coming, I lean **React** — or **Next.js** if SEO matters (TCW). Either way I design the same API behind it and enforce the same performance, security and testing standards."*

**Follow-ups**
- *"One sentence?"* — Big-team consistency → Angular; flexibility + ecosystem → React; SEO → Next.js — and the back-end architecture stays the same.
- *"What never drives your choice?"* — Hype or personal preference — I pick on team fit, app type and lifespan, and I've genuinely shipped both.

---

## Section index

| # | Question | The key point |
|---|---|---|
| V1 | Core difference | React = library (view); Angular = full framework |
| V2 | Side-by-side | React: flexible + big ecosystem; Angular: batteries-included |
| V3 | Language & structure | React unopinionated; Angular structured with decorators + CLI |
| V4 | Data flow & state | Both one-way; Angular adds two-way; server data = cache on both |
| V5 | Learning curve | React easier to start; Angular consistent once learned |
| V6 | Which to choose | Context-driven: flexibility → React, big-team consistency → Angular |
| V7 | Rendering & performance | Virtual DOM vs change detection; both need virtualisation |
| V8 | Talking to the API | Same REST/JSON contract; token + OpenAPI DTOs on both |
| V9 | Scaling to teams | Angular consistency free; React consistency you must enforce |
| V10 | Migration | It's a rewrite — migrate incrementally, strangler-fig style |
| V11 | Components | JSX (logic+view together) vs separated Angular templates |
| V12 | Forms | Angular built-in Reactive Forms; React adds RHF+Zod |
| V13 | Routing | Both: nested/guards/lazy; Angular built-in, React library |
| V14 | Dependency injection | Angular built-in DI (a real edge); React uses Context/hooks |
| V15 | Reactivity | React hooks vs Angular RxJS + signals |
| V16 | Tooling & CLI | Angular CLI + ng update vs React Vite + chosen tools |
| V17 | Testing | RTL vs TestBed; same philosophy; both add Playwright |
| V18 | SSR | Next.js (dominant) vs Angular Universal |
| V19 | Ecosystem | React larger community; Angular cohesive Google-backed |
| V20 | Bundle & load | React smaller baseline; both fine with lazy-load + budget |
| V21 | Hiring | More React devs; Angular strong in enterprise |
| V22 | Mobile | React Native (mainstream) vs Ionic/NativeScript |
| V23 | Upgrades | Angular ng update centralises; React tracks libs separately |
| V24 | Design systems | Angular Material first-party; React many choices |
| V25 | Security | Parity — API is the boundary; both auto-escape XSS |
| V26 | Accessibility | Discipline not framework; axe in CI on both |
| V27 | What's the same | Components, TS, one-way flow, same API, same perf/security work |
| V28 | Common myths | 'React always faster', 'Angular dead', AngularJS≠Angular |
| V29 | Cost / TCO | React cheaper to start; Angular cheaper to maintain at scale |
| V30 | Decision framework | 5 questions: team, lifespan, structure, SEO, mobile |

---

[← Concept: Angular](29-concept-angular.md) · [Home](README.md) · [Next → Concept: ASP.NET Core Web API](31-concept-aspnet-webapi.md)
