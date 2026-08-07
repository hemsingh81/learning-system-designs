# 69 · Concept: React — What's New (Version Evolution) (30 questions)

[← Azure Services What's New](68-concept-azure-whats-new.md) · [Home](README.md) · [Next → Angular What's New](70-concept-angular-whats-new.md)

This file explains **what is new in React** — from class components through hooks (16.8), the automatic-batching and concurrent era (17–18), to Server Components and Actions (19) — in simple English, with *why it matters* and *old-vs-new code*. On the TCW front ends I use React, so I adopt new features when they simplify code or improve performance.

> Simple one-liner: *"React's story is: classes → hooks (16.8) → concurrent rendering & automatic batching (18) → Server Components, Actions and the `use` hook (19). The theme is 'let React do more for you' — less manual state, less boilerplate, better performance by default."*

**Jump to (the model):** [RW1 Version history](#rw1--react-version-history) · [RW2 Release philosophy](#rw2--reacts-release-philosophy) · [RW3 How I upgrade](#rw3--how-i-upgrade-react)
> **The hooks era (16.8):** [RW4 Why hooks](#rw4--hooks-168--the-big-shift) · [RW5 useState/useEffect](#rw5--usestate-and-useeffect) · [RW6 Custom hooks](#rw6--custom-hooks) · [RW7 useContext/useReducer](#rw7--usecontext-and-usereducer)
> **React 17:** [RW8 The 'no new features' release](#rw8--react-17--the-stepping-stone) · [RW9 New JSX transform](#rw9--new-jsx-transform)
> **React 18:** [RW10 Concurrent rendering](#rw10--concurrent-rendering-18) · [RW11 Automatic batching](#rw11--automatic-batching) · [RW12 Transitions](#rw12--usetransition-and-startTransition) · [RW13 Suspense for data](#rw13--suspense) · [RW14 useId/useDeferredValue](#rw14--useid-and-usedeferredvalue) · [RW15 createRoot](#rw15--createroot-strict-mode)
> **React 19:** [RW16 Server Components](#rw16--react-server-components-19) · [RW17 Actions](#rw17--actions-and-form-actions) · [RW18 useActionState](#rw18--useactionstate) · [RW19 useOptimistic](#rw19--useoptimistic) · [RW20 use() hook](#rw20--the-use-hook) · [RW21 ref as prop / cleanup](#rw21--ref-as-a-prop-and-ref-cleanup) · [RW22 Compiler](#rw22--the-react-compiler)
> **Ecosystem:** [RW23 Next.js/App Router](#rw23--nextjs-and-the-app-router) · [RW24 Data libraries](#rw24--data-fetching-libraries) · [RW25 Build tools](#rw25--build-tools-vite)
> **Cross-cutting:** [RW26 Class→function migration](#rw26--migrating-classes-to-hooks) · [RW27 Perf features over time](#rw27--performance-features-over-time) · [RW28 Deprecations](#rw28--deprecations-and-removals)
> **Decisions:** [RW29 When to adopt](#rw29--when-i-adopt-new-react-features) · [RW30 My approach](#rw30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of "what's new in React" in plain English. Hold these ideas and every question hangs off one of them.

**1. React's whole history is "let React do more for you."** Classes made me manage lifecycle by hand; hooks let React manage state/effects; concurrent rendering lets React manage *when* to render; Server Components let React manage *where* code runs. Each era removes manual work.

**2. Hooks (16.8) were the turning point.** Before, stateful logic lived in class lifecycle methods and was hard to reuse. Hooks (`useState`, `useEffect`, custom hooks) let me share logic as plain functions. Almost all modern React is function components + hooks.

**3. React 18 made rendering *concurrent*.** The renderer can now interrupt, pause and prioritise work. This gave us automatic batching, transitions (mark updates as non-urgent), and real Suspense — so a slow update doesn't freeze the UI. Big features, mostly opt-in and backward-compatible.

**4. React 19 shifts work to the server and formalises async.** Server Components run on the server (zero client JS for them); Actions standardise form/mutation handling with pending/error/optimistic state; the `use` hook reads promises/context inside render. The theme: less client code, less boilerplate for async.

**5. Most upgrades are backward-compatible and opt-in.** React takes stability seriously — 18's concurrent features are opt-in, 17 deliberately shipped "no new features" to ease upgrades. So upgrading is usually low-risk; I adopt the *new* features gradually.

**6. Old way vs new way is the interview gold.** For each feature I can state the before/after: class + lifecycle → function + hooks; manual `setState` batching → automatic batching; loading flags everywhere → Suspense; hand-written form submit + loading/error state → Actions + `useActionState`.

**7. The ecosystem is part of "what's new."** Next.js App Router, TanStack Query, and Vite shaped how modern React is actually built. Knowing these matters as much as the core API.

**8. I adopt for real benefit, not novelty.** A feature earns its place if it simplifies code or improves UX/performance for *my* app. I don't rewrite working class components just to use hooks.

**The full-stack / architect lens:** the later Q&As go era-by-era (hooks 16.8, the 17 stepping-stone, 18's concurrent features, 19's Server Components/Actions/`use`/compiler) with old-vs-new JSX, plus the ecosystem (Next.js, TanStack Query, Vite), class→hooks migration, performance features over time, deprecations, and how I decide to adopt. They all trace back to the core: let React do more for you, upgrade safely (it's mostly backward-compatible), and adopt features for genuine simplicity/performance.

**One rule I never break:** *adopt React features gradually and for a real benefit — upgrades are safe because they're backward-compatible, so I never big-bang rewrite working code just to use the newest API.*

---

## RW1 · React version history

**Simple explanation.** The milestones: **16.8** (2019, hooks), **17** (2020, "stepping stone", no new features), **18** (2022, concurrent rendering + automatic batching + Suspense), **19** (2024, Server Components, Actions, `use`, compiler).

**Architect's view:** I track which major we're on and whether we're using the *new* capabilities of it (e.g. on 18 but still not using transitions). Version + adopted-features is the real state.

**Follow-ups**
- *How do I check the version?* — `React.version` or `package.json`.
- *Do I need every major?* — Upgrades are cumulative; I move forward but adopt features gradually.

---

## RW2 · React's release philosophy

**Simple explanation.** React prizes **backward compatibility** and **gradual adoption**. New features are usually opt-in; breaking changes are rare and heavily flagged. React 17 shipped deliberately with *no* new features just to make upgrading easy.

**Architect's view:** this is why upgrading React is usually low-drama — I can move the version and adopt new APIs at my own pace.

**Follow-ups**
- *Codemods?* — React ships automated codemods for many migrations.
- *Deprecation warnings?* — React warns in dev before removing anything.

---

## RW3 · How I upgrade React

**Simple explanation.** My steps: bump `react`/`react-dom`, run codemods, fix StrictMode double-render surprises, switch to `createRoot` (18), test, then adopt new features incrementally.

**Architect's view:** I separate "upgrade the version" (low risk) from "adopt new features" (do gradually). That keeps each change small and reviewable.

**Follow-ups**
- *StrictMode double-invoke?* — In dev, effects run twice to surface bugs — fix effects, don't disable StrictMode.
- *Third-party libs?* — Ensure they support the target major first.

---

## RW4 · Hooks (16.8) — the big shift

**Simple explanation.** **Hooks** let function components use state and lifecycle features — no classes needed. They also let me extract and **reuse stateful logic** as custom hooks.

**Old vs new.**

```jsx
// OLD (class)
class Counter extends React.Component {
  state = { n: 0 };
  render() { return <button onClick={() => this.setState({ n: this.state.n + 1 })}>{this.state.n}</button>; }
}
// NEW (hooks)
function Counter() {
  const [n, setN] = useState(0);
  return <button onClick={() => setN(n + 1)}>{n}</button>;
}
```

**Architect's view:** hooks solved logic reuse (previously HOCs/render props, which nested badly). All new components are function + hooks.

**Follow-ups**
- *Rules of hooks?* — Call at the top level, only from React functions — enforced by the lint plugin.
- *Why not mixins?* — Mixins caused name clashes; custom hooks compose cleanly.

---

## RW5 · useState and useEffect

**Simple explanation.** `useState` holds local state; `useEffect` runs side effects (fetch, subscriptions) after render, with a dependency array controlling when.

```jsx
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id); // cleanup
}, []); // run once
```

**Old vs new.** Replaces `componentDidMount`/`DidUpdate`/`WillUnmount` with one consistent model plus cleanup.

**Architect's view:** the dependency array is the top source of bugs — I use the exhaustive-deps lint rule to catch stale closures.

**Follow-ups**
- *Effect vs event?* — Not everything belongs in an effect; derive during render or handle in event handlers where possible.
- *Cleanup?* — Return a function to tear down subscriptions/timers.

---

## RW6 · Custom hooks

**Simple explanation.** A **custom hook** is a function starting with `use` that calls other hooks — it packages reusable stateful logic.

```jsx
function useDebounced(value, ms) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
}
```

**Old vs new.** Replaces HOCs/render props for logic reuse — flat and composable instead of deeply nested.

**Architect's view:** I keep components thin and push data/logic into well-named custom hooks — great for testing and reuse across the TCW front ends.

**Follow-ups**
- *Do hooks share state?* — No — each call gets its own state; they share *logic*, not values.
- *Naming?* — Must start with `use` so the linter enforces the rules.

---

## RW7 · useContext and useReducer

**Simple explanation.** `useContext` reads shared context without prop-drilling; `useReducer` manages complex state via a reducer function — together a lightweight state-management pattern.

**Old vs new.** For medium apps this pair often replaces reaching for Redux — built-in, less boilerplate.

**Architect's view:** I use context + reducer for cross-cutting state (auth, theme); a dedicated library (Redux Toolkit/Zustand) only when state gets truly large/complex.

**Follow-ups**
- *Context performance?* — A context change re-renders all consumers; I split contexts or memoise to limit blast radius.
- *When Redux?* — Large shared state, middleware, devtools/time-travel needs.

---

## RW8 · React 17 — the stepping stone

**Simple explanation.** **React 17** intentionally added **no new developer-facing features**. Its job was to enable **gradual upgrades** — you can run two React versions on one page — and to change event delegation internals.

**Architect's view:** 17's value was making the jump to 18 safer, especially for large apps that upgrade piece by piece.

**Follow-ups**
- *Why bother releasing it?* — To decouple upgrades so huge apps aren't forced into a big-bang.
- *Event change?* — Events attach to the root container, not `document` — helps embedding.

---

## RW9 · New JSX transform

**Simple explanation.** React 17 introduced the **new JSX transform** — you no longer need `import React from 'react'` just to use JSX; the compiler auto-imports the runtime.

```jsx
// NEW: no `import React` needed for JSX
function Hi() { return <h1>Hi</h1>; }
```

**Architect's view:** small quality-of-life win; less boilerplate at the top of every file.

**Follow-ups**
- *Do I still import hooks?* — Yes — `import { useState }` still required; only the implicit JSX runtime is automatic.
- *Bundle size?* — Slightly smaller, cleaner output.

---

## RW10 · Concurrent rendering (18)

**Simple explanation.** **React 18** introduced **concurrent rendering** — React can prepare multiple versions of the UI, interrupt/pause/resume rendering, and prioritise urgent updates. It's the foundation for transitions and Suspense.

**Old vs new.** Before, rendering was synchronous and blocking — a big update could freeze the page. Concurrent rendering keeps the UI responsive.

**Architect's view:** it's mostly *invisible plumbing* — I benefit via transitions/Suspense rather than calling it directly. Opt-in via `createRoot`.

**Follow-ups**
- *Do I need to rewrite components?* — No — you opt in with `createRoot` and adopt transitions where helpful.
- *Is it on by default?* — The runtime is enabled with `createRoot`; concurrent *features* are used explicitly.

---

## RW11 · Automatic batching

**Simple explanation.** **Automatic batching** (18) groups multiple state updates into a single re-render — now even inside promises, timeouts and native event handlers, not just React events.

```jsx
// React 18: both updates → ONE render, even inside a fetch .then
setCount(c => c + 1);
setFlag(f => !f);
```

**Old vs new.** Before 18, updates inside `setTimeout`/promises each caused a separate render. Now they're batched — fewer renders, better performance for free.

**Architect's view:** a free performance win on upgrade; rarely I need `flushSync` to opt out for a specific case.

**Follow-ups**
- *Opt out?* — `flushSync(() => setX(...))` forces an immediate render.
- *Any behaviour change to watch?* — If code depended on intermediate renders (rare), test it.

---

## RW12 · useTransition and startTransition

**Simple explanation.** **Transitions** mark a state update as **non-urgent**, so React can keep the UI responsive (e.g. typing) while a heavy update (filtering a big list) renders in the background.

```jsx
const [isPending, startTransition] = useTransition();
onChange={e => {
  setQuery(e.target.value);                 // urgent: keep input snappy
  startTransition(() => setResults(filter(e.target.value))); // non-urgent
}}
```

**Old vs new.** Before, a heavy update blocked typing. Transitions prioritise the urgent update.

**Architect's view:** ideal for search/filter over large data on the reporting UIs — the input never stutters.

**Follow-ups**
- *isPending?* — Show a subtle spinner while the transition renders.
- *startTransition vs useTransition?* — The hook adds the pending flag; the standalone function doesn't.

---

## RW13 · Suspense

**Simple explanation.** **Suspense** lets a component "wait" for something (code or data) and show a **fallback** meanwhile — declarative loading states. React 18 added Suspense for SSR streaming; frameworks use it for data.

```jsx
<Suspense fallback={<Spinner/>}>
  <SlowList />
</Suspense>
```

**Old vs new.** Before, every component managed its own `isLoading` boolean. Suspense centralises loading UI declaratively.

**Architect's view:** with a data library or framework, Suspense removes scattered loading flags and enables streaming SSR (send HTML as parts are ready).

**Follow-ups**
- *Data fetching in Suspense — do I write it myself?* — Usually via a framework/library (Next.js, React Query, or `use`).
- *Error states?* — Pair with an error boundary.

---

## RW14 · useId and useDeferredValue

**Simple explanation.** `useId` generates stable unique IDs (safe for SSR, great for accessibility label/for pairs). `useDeferredValue` lets a value "lag" so expensive renders don't block urgent ones.

```jsx
const id = useId();
<label htmlFor={id}>Name</label><input id={id} />
const deferredQuery = useDeferredValue(query); // render list off the deferred value
```

**Old vs new.** Before, hand-rolled IDs broke SSR hydration; heavy derived renders blocked typing. These hooks fix both.

**Architect's view:** `useId` is my default for accessible form IDs; `useDeferredValue` is a lighter alternative to transitions for derived values.

**Follow-ups**
- *useDeferredValue vs useTransition?* — Deferred value for a value you can't wrap; transition for an update you trigger.
- *Why useId for SSR?* — It produces matching IDs on server and client.

---

## RW15 · createRoot & Strict Mode

**Simple explanation.** React 18 replaced `ReactDOM.render` with **`createRoot`** (enables concurrent features). **StrictMode** in dev intentionally double-invokes effects/renders to surface side-effect bugs.

```jsx
import { createRoot } from 'react-dom/client';
createRoot(document.getElementById('root')).render(<App/>);
```

**Old vs new.** `ReactDOM.render` is deprecated; `createRoot` is required for 18's features.

**Architect's view:** the StrictMode double-run flushes out impure effects early — I fix the effect rather than disable StrictMode.

**Follow-ups**
- *Does double-invoke happen in production?* — No — dev only.
- *Migration effort?* — Usually a one-line change plus fixing any effects it exposes.

---

## RW16 · React Server Components (19)

**Simple explanation.** **Server Components (RSC)** render **on the server** and send serialized UI (not JS) to the client — zero client bundle for those components, direct access to server resources (DB, files), and smaller downloads.

**Old vs new.** Before, every component shipped as client JS. RSC keeps data-heavy, non-interactive components on the server — less JS, faster loads.

**Architect's view:** used via a framework (Next.js App Router). Server Components for data/display; Client Components (`"use client"`) only where there's interactivity. Big win for bundle size on content-heavy pages.

**Follow-ups**
- *Can RSC use hooks like useState?* — No — those are client-only; RSC is for rendering/data.
- *How do I mark a client component?* — `"use client"` at the top of the file.

---

## RW17 · Actions and form actions

**Simple explanation.** **Actions** (19) are functions (often async) you pass to handle mutations/form submits; React manages **pending**, **error** and **optimistic** state for you. Forms accept an `action` prop.

```jsx
// React 19: form Action handles submit + pending/error
function NameForm() {
  async function save(formData) { await api.save(formData.get('name')); }
  return <form action={save}><input name="name"/><button>Save</button></form>;
}
```

**Old vs new.** Before, every form meant manual `onSubmit`, `isSubmitting`, try/catch error state. Actions bake that in.

**Architect's view:** removes a huge amount of repetitive form plumbing — exactly the boilerplate that fills CRUD screens.

**Follow-ups**
- *Server actions?* — With a framework, an action can run on the server directly.
- *Progressive enhancement?* — Form actions can work before JS loads in frameworks.

---

## RW18 · useActionState

**Simple explanation.** **`useActionState`** (19) wraps an action and returns the latest **state**, a wrapped **action**, and a **pending** flag — the standard way to track a mutation's result and status.

```jsx
const [error, submitAction, isPending] = useActionState(async (prev, formData) => {
  try { await save(formData); return null; } catch (e) { return e.message; }
}, null);
```

**Old vs new.** Replaces the `useState` + `try/catch` + `isSubmitting` trio every form used to carry.

**Architect's view:** standardises form/mutation state across the app — consistent UX with far less code.

**Follow-ups**
- *Related hook?* — `useFormStatus` reads pending state of the nearest parent form.
- *Where does state come from?* — The action's return value.

---

## RW19 · useOptimistic

**Simple explanation.** **`useOptimistic`** (19) shows an **optimistic UI** immediately (e.g. a sent message) and reconciles when the real result returns — built-in optimistic updates.

```jsx
const [optimistic, addOptimistic] = useOptimistic(messages, (state, m) => [...state, m]);
```

**Old vs new.** Before, optimistic UI meant manual local state juggling and rollback logic. Now it's a hook.

**Architect's view:** makes UIs feel instant (chat, likes, list adds) with clean rollback on failure — great UX with little code.

**Follow-ups**
- *What if the server fails?* — React reverts the optimistic state to the real one.
- *Pair with?* — Actions/`useActionState` for the actual mutation.

---

## RW20 · The use() hook

**Simple explanation.** **`use`** (19) reads the value of a **promise** or **context** during render — unlike other hooks it can be called conditionally, and it integrates with Suspense.

```jsx
function Profile({ userPromise }) {
  const user = use(userPromise); // suspends until resolved
  return <h1>{user.name}</h1>;
}
```

**Old vs new.** Reading a promise's result used to need `useEffect` + state. `use` reads it directly with Suspense handling the loading.

**Architect's view:** simplifies data reads inside render, especially with RSC passing promises down — less effect boilerplate.

**Follow-ups**
- *Can I call use() conditionally?* — Yes — unlike other hooks, that's allowed.
- *Where does the promise come from?* — Often a Server Component or a cache/library.

---

## RW21 · ref as a prop and ref cleanup

**Simple explanation.** In **React 19**, function components can receive **`ref` as a normal prop** (no more `forwardRef` in most cases), and **ref callbacks can return a cleanup function**.

```jsx
// React 19: ref is just a prop
function Input({ ref, ...props }) { return <input ref={ref} {...props} />; }
```

**Old vs new.** Before, exposing a ref meant wrapping in `forwardRef`. Now it's a plain prop — less ceremony.

**Architect's view:** removes a common source of confusion in component libraries.

**Follow-ups**
- *Is forwardRef removed?* — Deprecated for the common case; ref-as-prop is preferred.
- *Ref cleanup use?* — Tear down observers/listeners attached via a ref callback.

---

## RW22 · The React Compiler

**Simple explanation.** The **React Compiler** automatically memoises components/values at build time — aiming to remove most manual `useMemo`/`useCallback`/`React.memo`.

**Old vs new.** Before, I hand-optimised re-renders with `useMemo`/`useCallback` (easy to get wrong). The compiler does it automatically based on analysis.

**Architect's view:** promising — it targets the most common performance foot-gun. I trial it and verify with the profiler before relying on it in production.

**Follow-ups**
- *Does it replace all memoisation?* — Most manual cases; I still profile.
- *Any requirements?* — Code must follow the Rules of React (pure components) for it to optimise safely.

---

## RW23 · Next.js and the App Router

**Simple explanation.** **Next.js** is the leading React framework; its **App Router** is built on **Server Components**, nested layouts, streaming, and server actions — the reference implementation of modern React.

**Old vs new.** The older Pages Router was client-centric; the App Router is server-first with RSC and layouts.

**Architect's view:** for a new React app needing SSR/SEO/performance, I default to Next.js App Router — it operationalises RSC, Suspense and Actions.

**Follow-ups**
- *SSR vs SSG vs ISR?* — Render per-request, at build, or incrementally — chosen per route.
- *Do I have to use Next?* — No — but RSC realistically needs a framework.

---

## RW24 · Data-fetching libraries

**Simple explanation.** **TanStack Query (React Query)** and **SWR** handle server-state: caching, background refetch, dedup, stale-while-revalidate — things `useEffect` fetching does badly.

**Old vs new.** Before, teams fetched in `useEffect` with hand-rolled cache/loading/error. Query libraries standardise it.

**Architect's view:** I separate **server state** (React Query) from **client/UI state** (useState/context) — a clean, scalable split on the TCW front ends.

**Follow-ups**
- *With RSC/Actions do I still need it?* — On the client for cached, interactive data — often yes; it complements RSC.
- *Why not just useEffect?* — No caching, races, refetch-on-focus, or dedup out of the box.

---

## RW25 · Build tools (Vite)

**Simple explanation.** **Vite** replaced Create React App as the default dev/build tool — instant startup (native ESM), fast HMR, and an optimised production build (Rollup). CRA is effectively deprecated.

**Old vs new.** CRA (Webpack) had slow starts and was unmaintained; Vite is far faster and actively developed.

**Architect's view:** new React apps start with Vite (or a framework like Next). I migrated off CRA for the dev-loop speed alone.

**Follow-ups**
- *Vite vs Next?* — Vite = SPA/library tooling; Next = full framework with SSR/RSC.
- *Why is Vite fast?* — Serves native ES modules in dev, no big bundle step.

---

## RW26 · Migrating classes to hooks

**Simple explanation.** To migrate: convert `state` → `useState`, lifecycle methods → `useEffect`, and extract shared logic into custom hooks — one component at a time.

**Old vs new.** Classes still work; hooks are the modern default. I migrate opportunistically, not in a big-bang.

**Architect's view:** I don't rewrite stable class components just for style — I convert when I'm already changing that code or need hook-based reuse.

**Follow-ups**
- *Error boundaries?* — Still class-based (no hook equivalent yet) — one place classes remain.
- *getDerivedStateFromProps?* — Usually replaced by deriving during render or `useMemo`.

---

## RW27 · Performance features over time

**Simple explanation.** Performance tools grew: `React.memo`/`useMemo`/`useCallback` (memoisation), automatic batching (18), transitions/`useDeferredValue` (18), and now the React Compiler (19) automating memoisation.

**Architect's view:** the trend is React handling performance *for* me — I measure with the Profiler first and only hand-optimise where the compiler/defaults don't.

**Follow-ups**
- *First step for a slow list?* — Virtualise (react-window) and check unnecessary re-renders in the Profiler.
- *Do I premature-optimise?* — No — measure first (see file 61 on React performance).

---

## RW28 · Deprecations and removals

**Simple explanation.** Notable removals/deprecations: legacy string refs, legacy context API, `ReactDOM.render` (→ `createRoot`), `forwardRef` for the common case (19), and old lifecycle methods (`componentWillMount` etc., now `UNSAFE_`).

**Architect's view:** React deprecates gently with warnings and codemods, so I clean these up on upgrade rather than being surprised.

**Follow-ups**
- *UNSAFE_ lifecycles?* — Renamed to signal they'll break with concurrent rendering; migrate off them.
- *How to find them?* — StrictMode + dev warnings flag most.

---

## RW29 · When I adopt new React features

**Simple explanation.** My rule: adopt when a feature **simplifies code** (Actions, `use`), **improves UX** (transitions, optimistic, Suspense), or **cuts bundle/load** (Server Components) — on the parts of the app that benefit, gradually.

**Architect's view:** upgrade the version early (it's safe), adopt features where they pay off. I don't chase RSC/compiler on a small internal SPA that doesn't need them.

**Follow-ups**
- *Do you always go Next.js?* — Only when SSR/RSC/SEO matter; otherwise Vite SPA.
- *How do you decide on the compiler?* — Trial it, profile, adopt if it helps and code is Rules-of-React clean.

---

## RW30 · My approach

**Simple explanation.** I keep React **current** (upgrades are backward-compatible and low-risk), write **function components + hooks**, separate **server state** (React Query) from **UI state**, adopt **18's concurrent features** where UX benefits, and use **19's Server Components/Actions** via Next.js where bundle size and form boilerplate matter. For every feature I know the old way and the new way.

**Architect's view:** React's evolution consistently means "less manual work, better defaults." On the TCW front ends I ride that — hooks for reuse, transitions/Suspense for responsiveness, Actions/`use` to kill form and async boilerplate, RSC to shrink bundles — always adopting gradually and measuring, never rewriting working code for novelty.

**Follow-ups**
- *One-sentence philosophy?* — "Upgrade early, adopt gradually, let React do the work."
- *How do you keep the team current?* — Short notes on each major and where we'll use its features.

---

## Section index

| ID | Topic | Core message |
|----|-------|--------------|
| RW1 | Version history | 16.8 hooks → 17 stepping-stone → 18 concurrent → 19 RSC/Actions |
| RW2 | Release philosophy | Backward-compatible, gradual, opt-in |
| RW3 | How I upgrade | Bump, codemods, createRoot, adopt features gradually |
| RW4 | Hooks (16.8) | State/lifecycle in functions; reusable logic |
| RW5 | useState/useEffect | Deps array is the bug source; cleanup effects |
| RW6 | Custom hooks | Composable reusable stateful logic |
| RW7 | useContext/useReducer | Built-in lightweight state management |
| RW8 | React 17 | No new features — enabled gradual upgrades |
| RW9 | New JSX transform | No `import React` needed for JSX |
| RW10 | Concurrent rendering | Interruptible rendering — the 18 foundation |
| RW11 | Automatic batching | Fewer renders (even in promises) — free perf |
| RW12 | Transitions | Mark updates non-urgent; keep UI snappy |
| RW13 | Suspense | Declarative loading + streaming SSR |
| RW14 | useId/useDeferredValue | SSR-safe IDs; lag heavy derived renders |
| RW15 | createRoot/StrictMode | Required for 18; double-invoke finds bugs |
| RW16 | Server Components (19) | Render on server; zero client JS |
| RW17 | Actions | Forms handle pending/error automatically |
| RW18 | useActionState | Standard mutation state + pending |
| RW19 | useOptimistic | Built-in optimistic UI with rollback |
| RW20 | use() hook | Read promises/context in render (conditional OK) |
| RW21 | ref as prop | No forwardRef; ref cleanup callbacks |
| RW22 | React Compiler | Auto-memoisation replacing useMemo/useCallback |
| RW23 | Next.js App Router | Server-first RSC/layouts/streaming |
| RW24 | Data libraries | React Query for server state |
| RW25 | Vite | Fast dev/build; CRA deprecated |
| RW26 | Class→hooks migration | Convert opportunistically, not big-bang |
| RW27 | Perf over time | React handles more perf; measure first |
| RW28 | Deprecations | render→createRoot; UNSAFE_ lifecycles; forwardRef |
| RW29 | When to adopt | Simpler code / better UX / smaller bundle |
| RW30 | My approach | Upgrade early, adopt gradually, let React work |

---

[← Azure Services What's New](68-concept-azure-whats-new.md) · [Home](README.md) · [Next → Angular What's New](70-concept-angular-whats-new.md)
