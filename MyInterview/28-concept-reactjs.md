# 28 · Concept: ReactJS (30 questions)

[← My First 90 Days](27-first-90-days.md) · [Home](README.md) · [Next → Concept: Angular](29-concept-angular.md)

This file explains **React** from the ground up, in very simple English, in the depth an interviewer expects. I built the React reporting screens on TCW (Project A), so I answer from real code. Every code sample is **TypeScript**.

> Simple one-liner: *"React is a JavaScript library for building user interfaces out of small, reusable pieces called components. You describe *what* the screen should look like for a given state, and React figures out *how* to update the screen efficiently."*

**Jump to (fundamentals):** [C1 What is React](#c1--what-is-react-and-why-use-it) · [C2 Components & JSX](#c2--components-props-and-jsx) · [C3 State & useState](#c3--state-and-usestate) · [C4 useEffect](#c4--useeffect-and-side-effects) · [C5 Virtual DOM](#c5--the-virtual-dom-explained-simply) · [C6 Lists & keys](#c6--lists-keys-and-conditional-rendering) · [C7 Hooks & custom hooks](#c7--hooks-rules-and-custom-hooks) · [C8 State management](#c8--state-management-context-vs-libraries)
> **Architecture & full-stack lens:** [C9 Performance](#c9--performance-memo-usememo-usecallback) · [C10 App architecture](#c10--structuring-a-large-react-app) · [C11 Data fetching & the API](#c11--data-fetching-and-talking-to-the-api) · [C12 Rendering & SSR/Next.js](#c12--csr-ssr-and-nextjs) · [C13 Security](#c13--front-end-security) · [C14 Testing & quality](#c14--testing-and-quality)
> **Hooks & rendering deep:** [C15 useReducer](#c15--usereducer-for-complex-state) · [C16 useRef](#c16--useref-and-the-dom) · [C17 Controlled forms](#c17--controlled-forms-and-validation) · [C18 Lifting state](#c18--lifting-state-and-composition) · [C19 Error boundaries](#c19--error-boundaries) · [C20 Suspense & lazy](#c20--suspense-and-code-splitting)
> **Routing, types & quality:** [C21 Routing](#c21--routing-with-react-router) · [C22 TypeScript with React](#c22--typescript-with-react) · [C23 Accessibility](#c23--accessibility) · [C24 Styling](#c24--styling-approaches) · [C25 Build tooling](#c25--build-tooling-vite-and-bundling) · [C26 Common pitfalls](#c26--common-mistakes-i-watch-for)
> **Architecture decisions:** [C27 Micro-frontends](#c27--micro-frontends) · [C28 Design system](#c28--design-systems-and-component-libraries) · [C29 Real-time](#c29--real-time-updates) · [C30 Why React (decision)](#c30--when-i-choose-react) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of React in plain English. If you hold these six ideas, every question below is just a detail hanging off one of them.

**1. Components — the Lego brick.** React builds UI out of small, reusable functions called **components**. Each returns a piece of UI. You compose big screens from little bricks (a `Button` inside a `Row` inside a `DataGrid` inside a `ReportPage`). Build once, reuse everywhere. *On TCW I built one typed `DataGrid` reused across every report.*

**2. Declarative UI — describe the what, not the how.** You don't write "find this cell and change its text". You describe *what the screen should look like for the current data*, and React works out the minimal DOM changes. Your job is to keep the data right; React keeps the screen right.

**3. State & props — the data that drives the screen.** **Props** are inputs passed *into* a component (read-only). **State** is data a component *owns and can change* (`useState`). When state or props change, the component **re-renders**. This one rule — *UI is a function of state* — is the heart of React.

**4. The Virtual DOM — why it's fast.** React keeps a lightweight copy of the UI in memory. On a change it builds a new copy, **diffs** it against the old one, and touches only the real DOM nodes that actually changed. That's why you can re-describe the whole screen cheaply.

```
state change → component re-runs → new virtual DOM → diff vs old → minimal real-DOM update
```

**5. Hooks — how function components get powers.** Hooks are functions starting with `use` that let a component remember state (`useState`), run side-effects like data fetching (`useEffect`), hold a mutable reference (`useRef`), or share logic (custom hooks). They run in order on every render, which is why the *rules of hooks* (call them at the top level, never in conditions) matter.

**6. Data flow — one way, downward.** Data flows **down** via props; events flow **up** via callbacks. State lives at the lowest common parent that needs it ("lifting state up"). For data from the server, a cache library (React Query) is usually better than raw `useState`.

**The full-stack lens (how I think as an architect):** beyond the basics I care about **performance** (avoiding needless re-renders, code-splitting), **architecture** (folder-by-feature, typed contracts with the Web API), **rendering strategy** (CSR vs SSR/Next.js), **security** (XSS, tokens), and **testing** (behaviour, not implementation). Those are the C9–C30 questions.

**One rule I never break:** *every piece of UI is a function of state.* Get the state model right and the components fall out naturally.

---

## C1 · What is React, and why use it?

**Simple explanation.** React is a library (not a full framework) made by Meta for building the *view* — what the user sees. Its big idea is **components**: you break a page into small building blocks (a button, a table, a form), build each one once, and reuse it everywhere.

The second big idea is **declarative UI**. Instead of writing step-by-step instructions to change the screen ("find this element, change its text"), you just describe *what the screen should look like for the current data*, and React updates the real page for you.

**Why teams use it.** Reusable components, a huge ecosystem, and it's fast because of the virtual DOM ([C5](#c5--the-virtual-dom-explained-simply)). *"On TCW I built typed React components for reporting screens — one `DataGrid` component reused across every report instead of rebuilding a table each time."*

**Follow-ups**
- *"Is React a framework or a library?"* — A library. It does the view; you add routing (React Router) and data-fetching (React Query) yourself. Angular, by contrast, is a full framework.
- *"What does 'declarative' actually mean?"* — I say *what* I want ("show these rows"), not *how* to change the DOM step by step. React handles the how.

---

## C2 · Components, props, and JSX

**Simple explanation.** A **component** is a function that returns UI. **Props** are the inputs you pass to it (like function arguments) — they are read-only. **JSX** is the HTML-like syntax inside JavaScript that describes the UI.

```tsx
type BadgeProps = { label: string; tone: 'ok' | 'warn' };

function Badge({ label, tone }: BadgeProps) {
  return <span className={`badge badge--${tone}`}>{label}</span>;
}

// used like an HTML tag, with props passed in:
<Badge label="On time" tone="ok" />
```

**Key rule:** props flow **down** (parent → child) and are never changed by the child. If a child needs to tell the parent something, the parent passes a **callback** prop down.

**Follow-ups**
- *"Why are props read-only?"* — So data flows one way and the UI stays predictable. A child mutating a prop would make bugs impossible to trace.
- *"What are `children`?"* — A special prop for whatever you put *between* a component's tags — great for wrappers like `<Card>...</Card>`.

---

## C3 · State and useState

**Simple explanation.** **State** is data that changes over time and belongs to a component (a typed value, a form input, a toggle). When state changes, React **re-renders** that component to show the new value. The `useState` hook gives a component state.

```tsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState<number>(0);
  return <button onClick={() => setCount(count + 1)}>Clicked {count} times</button>;
}
```

**Props vs state (the classic question):** props come *from the parent* and don't change inside the component; state is *owned and changed* by the component itself.

**Follow-ups**
- *"Why not just use a normal variable?"* — A normal variable doesn't tell React to re-render. `setCount` both updates the value *and* triggers the re-render.
- *"State update from the previous value?"* — Use the function form: `setCount(prev => prev + 1)`. It's safe when updates batch together.
- *"Is `setState` synchronous?"* — No, React batches updates for performance, so the new value isn't available on the very next line — it appears on the next render.

---

## C4 · useEffect and side effects

**Simple explanation.** Rendering should be pure — just turn data into UI. Anything *else* (fetching data, timers, subscriptions) is a **side effect**, and those go in `useEffect`. The **dependency array** controls when the effect runs.

```tsx
useEffect(() => {
  const controller = new AbortController();
  fetch(`/api/reports/${type}`, { signal: controller.signal })
    .then(r => r.json())
    .then(setData);
  return () => controller.abort();   // cleanup: cancels the request
}, [type]);   // re-run only when `type` changes
```

- `[]` → runs **once** after first render.
- `[type]` → runs whenever `type` changes.
- no array → runs after **every** render (usually a bug).

The **cleanup function** (the returned function) prevents leaks — cancel the fetch, clear the timer, unsubscribe.

**Follow-ups**
- *"What's the most common useEffect bug?"* — A missing dependency (stale data) or no cleanup (memory leak / setting state after unmount).
- *"Should data fetching live in useEffect?"* — It works, but I prefer a library like React Query that handles caching, retries and loading states for me.

---

## C5 · The Virtual DOM, explained simply

**Simple explanation.** Changing the real browser DOM directly is slow. React keeps a lightweight copy in memory called the **Virtual DOM**. When state changes, React builds a new virtual copy, **compares** it to the old one (this diffing is called *reconciliation*), and updates only the *few* real DOM nodes that actually changed — not the whole page.

**Analogy:** instead of reprinting a whole document because one word changed, React finds the one word and fixes just that.

**Follow-ups**
- *"Why is this faster?"* — Real DOM updates trigger layout and repaint, which are expensive. Batching the minimum number of real changes avoids most of that cost.
- *"What are keys' role here?"* — Keys help React match old and new list items during diffing so it moves/reuses nodes instead of rebuilding them ([C6](#c6--lists-keys-and-conditional-rendering)).

---

## C6 · Lists, keys, and conditional rendering

**Simple explanation.** To show a list, `map` an array to components. Each item needs a **stable, unique `key`** so React can track it across renders.

```tsx
{positions.map(p => <Row key={p.id} data={p} />)}   // key = stable id, NOT the array index
```

**Conditional rendering** — show different UI for different states (I always cover all four):
```tsx
if (state.status === 'loading') return <Spinner />;
if (state.status === 'error')   return <Error message={state.message} />;
if (state.status === 'empty')   return <EmptyState />;
return <DataGrid rows={state.data} />;
```

**Follow-ups**
- *"Why not use the array index as the key?"* — If the list reorders or items are added/removed, indexes shift and React reuses the wrong DOM node — causing subtle bugs. Use a real id.
- *"What's the danger of forgetting keys?"* — React warns you, and rendering gets slower and buggier on updates.

---

## C7 · Hooks rules and custom hooks

**Simple explanation.** **Hooks** are functions starting with `use` that let function components use React features (state, effects, context). Two rules: **only call hooks at the top level** (never in loops/conditions) and **only from React functions**. This is so React can match each hook to the right state across renders.

A **custom hook** is my own `use...` function that packages reusable logic:

```tsx
function useReport(type: string) {
  const [state, setState] = useState<ReportState>({ status: 'loading' });
  useEffect(() => { /* fetch + setState */ }, [type]);
  return state;   // any component can now reuse this logic
}
```

**Follow-ups**
- *"Why can't hooks go in an `if`?"* — React tracks hooks by call order. A conditional call changes the order and breaks that matching.
- *"When do you write a custom hook?"* — When two components share the same stateful logic — I extract it once instead of copy-pasting.

---

## C8 · State management: Context vs libraries

**Simple explanation.** Passing props down many levels gets painful ("prop drilling"). **Context** lets you share a value (theme, current user) with a whole subtree without passing props at every level. For bigger app state, teams use libraries like **Redux Toolkit** or **Zustand**.

My rule: **server data is a cache, not app state.** I keep fetched data in **React Query**, and use Context/Zustand only for genuine client state (UI settings, auth).

**Follow-ups**
- *"Context vs Redux?"* — Context is built-in and great for low-frequency global values; Redux/Zustand suit complex, frequently-changing state with dev-tools and middleware.
- *"Isn't Context slow?"* — It can re-render everything that consumes it, so I keep contexts small and split them by concern.

---

## C9 · Performance: memo, useMemo, useCallback

**Simple explanation.** React re-renders a component whenever its state or props change — and that cascades to children. Most of the time this is cheap, but on data-heavy screens (like reporting grids) it adds up. Three tools control it:
- **`React.memo`** — skips re-rendering a child if its props didn't change (reference-wise).
- **`useMemo`** — caches an expensive *calculated value* between renders.
- **`useCallback`** — caches a *function* so its reference stays stable (so `memo` children don't re-render).

```tsx
const filtered = useMemo(() => rows.filter(r => r.active), [rows]);   // recompute only when rows change
const onSelect = useCallback((id: string) => setSelected(id), []);   // stable function reference
```

*"On TCW my `DataGrid` re-rendered on every parent state change until I memoised the row components and stabilised the callbacks — that cut wasted renders on the largest reports and kept scrolling smooth."*

**Follow-ups**
- *"Should you memoise everything?"* — No — memoisation has its own cost. I profile with React DevTools first, then memoise the proven hot spots.
- *"How do you handle 50k rows?"* — **Virtualisation** (react-window / TanStack Virtual) renders only the visible rows — the biggest single win for large grids.
- *"What causes needless re-renders?"* — New object/array/function literals passed as props each render — `useMemo`/`useCallback` fix the reference identity.

---

## C10 · Structuring a large React app

**Simple explanation (architect lens).** For a big app I organise by **feature**, not by file type. Each feature folder owns its components, hooks, and API calls, so teams work independently and code stays cohesive.

```
src/
  features/reports/    (components, hooks, api, types for reports)
  features/auth/
  shared/ui/           (reusable Button, DataGrid, Modal)
  shared/lib/          (api client, formatting, hooks)
  app/                 (routing, providers, layout)
```

**My layering rules:** UI components stay "dumb" (presentation only); logic lives in custom hooks; all network calls go through **one typed API client** so auth, errors and base URLs are handled in one place. This mirrors the clean separation I enforce on the back end.

**Follow-ups**
- *"Feature folders vs type folders — why?"* — Type folders (`/components`, `/services`) don't scale — changing one feature touches many folders. Feature folders keep a change local.
- *"How do you share components across features?"* — A `shared/ui` library of presentational components with a documented prop contract (Storybook helps).
- *"Where do you draw the FE/BE boundary?"* — The API contract. I keep the front end thin and put real business rules on the server, so they can't be bypassed.

---

## C11 · Data fetching and talking to the API

**Simple explanation (full-stack lens).** I treat server data as a **cache**, not component state. **React Query (TanStack Query)** fetches, caches, dedupes, retries, and refreshes it — removing most manual `useEffect` fetching.

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['report', type],
  queryFn: () => api.getReport(type),   // typed call to my ASP.NET Core Web API
  staleTime: 30_000,
});
```

**Full-stack details I own:** shared **TypeScript types** for request/response (ideally generated from the API's OpenAPI/Swagger so front and back never drift), consistent error shapes, and a single Axios/fetch wrapper that attaches the **Entra ID bearer token** and handles 401 refresh.

*"On TCW the React screens call my Web API; keeping one typed client and shared DTO types meant a change to a report contract surfaced as a TypeScript error at build time, not a runtime bug in production."*

**Follow-ups**
- *"REST vs GraphQL from the front end?"* — REST is my default (simple, cacheable); GraphQL when screens need to pull many shapes and I want to avoid over-fetching.
- *"How do you avoid front/back type drift?"* — Generate the TS client from the API's OpenAPI spec — the contract becomes the single source of truth.
- *"Optimistic updates?"* — React Query can update the UI immediately and roll back on error — good for responsive forms.

---

## C12 · CSR, SSR, and Next.js

**Simple explanation.** Plain React is **CSR** (Client-Side Rendering) — the browser downloads JS, then builds the page. That's fine for internal apps behind a login (like my reporting screens). **SSR** (Server-Side Rendering) renders HTML on the server first — better for first-load speed and SEO. **Next.js** is the React framework that gives SSR, static generation, routing and API routes out of the box.

**Architect decision:** CSR for internal, data-heavy dashboards; SSR/Next.js for public, SEO-sensitive, or first-paint-critical sites.

**Follow-ups**
- *"When would you reach for Next.js?"* — Public marketing/e-commerce pages needing SEO and fast first paint, or when I want file-based routing and server components.
- *"What are React Server Components?"* — Components rendered on the server that send zero JS to the browser — less bundle, faster loads for content-heavy pages.
- *"Why was CSR fine on TCW?"* — It's an authenticated internal app; SEO is irrelevant and users tolerate a one-time load for a rich experience.

---

## C13 · Front-end security

**Simple explanation (full-stack lens).** The front end is never the security boundary — the **API enforces the rules** — but the client still has real responsibilities:
- **XSS (Cross-Site Scripting):** React escapes values by default, so avoid `dangerouslySetInnerHTML`; if I must render HTML, sanitise it (DOMPurify).
- **Tokens:** validate auth on the server; store tokens carefully (prefer httpOnly cookies over localStorage where possible to reduce XSS token theft).
- **Never trust the client:** hiding a button doesn't secure an action — the API must re-check the user's role.

**Follow-ups**
- *"How does React help against XSS?"* — It auto-escapes interpolated content, so injected scripts render as text, not code.
- *"Role-based UI vs API auth?"* — I hide unauthorised UI for UX, but the **server** still authorises every request — the UI check is convenience, not security.
- *"CORS — what is it?"* — The browser rule controlling which origins may call my API; I configure it on the API to allow only my front-end origin.

---

## C14 · Testing and quality

**Simple explanation.** I test React the way users use it, with **React Testing Library** (query by what's on screen, not internals) plus **Jest**, and **Playwright/Cypress** for end-to-end flows.

```tsx
test('shows the report rows', async () => {
  render(<ReportScreen type="equity" />);
  expect(await screen.findByText('On time')).toBeInTheDocument();
});
```

**Quality gates I wire into CI:** TypeScript type-check, ESLint + Prettier, unit/component tests, and a bundle-size check — so quality is enforced automatically, matching the discipline I apply on the back end.

**Follow-ups**
- *"What do you test — and not?"* — Test behaviour and contracts (does the screen show the right thing for a given state); don't test implementation details that change often.
- *"Unit vs E2E balance?"* — Many fast component tests, a few high-value E2E tests on critical journeys (login → view report).
- *"How do you keep bundles small?"* — Code-splitting with `React.lazy`, tree-shaking, and watching dependency weight in CI.

---

## C15 · useReducer for complex state

**Simple explanation.** When state has many related fields or complex transitions, `useState` gets messy. **`useReducer`** centralises the logic in one pure `reducer(state, action)` function — like a mini Redux inside one component. Great for forms, wizards, and my report filters.

```tsx
type Action = { type: 'setPage'; page: number } | { type: 'reset' };
function reducer(s: State, a: Action): State {
  switch (a.type) {
    case 'setPage': return { ...s, page: a.page };
    case 'reset':   return initial;
  }
}
const [state, dispatch] = useReducer(reducer, initial);
```

**Follow-ups**
- *"useState vs useReducer?"* — useState for a few independent values; useReducer when updates are complex or depend on each other.
- *"Why is a reducer easy to test?"* — It's a pure function — given state + action, assert the new state, no React needed.

---

## C16 · useRef and the DOM

**Simple explanation.** **`useRef`** holds a mutable value that **survives re-renders without causing one**. Two uses: access a DOM node (focus an input) and store a value across renders (a previous value, a timer id).

```tsx
const inputRef = useRef<HTMLInputElement>(null);
useEffect(() => inputRef.current?.focus(), []);   // focus on mount
return <input ref={inputRef} />;
```

**Follow-ups**
- *"ref vs state?"* — State re-renders on change; a ref doesn't — use a ref for values the UI doesn't need to react to.
- *"When touch the DOM directly?"* — Focus, scroll, measuring, or integrating a non-React library — rarely otherwise.

---

## C17 · Controlled forms and validation

**Simple explanation.** In a **controlled** input, React state is the single source of truth — value comes from state, changes go through `onChange`. For real forms I use **React Hook Form** + a schema (Zod) for typed, performant validation instead of hand-wiring every field.

```tsx
const { register, handleSubmit, formState:{ errors } } = useForm<TradeForm>({ resolver: zodResolver(schema) });
<input {...register('quantity')} />
{errors.quantity && <span>{errors.quantity.message}</span>}
```

**Follow-ups**
- *"Controlled vs uncontrolled?"* — Controlled = state drives the value (predictable); uncontrolled reads via a ref (less code, less control). I default to controlled/RHF.
- *"Where does validation really live?"* — Client for UX, but the **API re-validates** — the client check is convenience, not security.

---

## C18 · Lifting state and composition

**Simple explanation.** When two components need the same data, **lift the state up** to their nearest common parent and pass it down. For flexibility I prefer **composition** (passing components as `children`/props) over deep inheritance or giant components.

**Follow-ups**
- *"When lift state?"* — As soon as two siblings must share/agree on a value — the parent owns it.
- *"Composition over what?"* — Over prop-drilling everything or building one huge component — small composed pieces stay reusable.

---

## C19 · Error boundaries

**Simple explanation.** An **error boundary** is a component that catches JavaScript errors in its child tree and shows a fallback UI instead of a blank white screen — so one broken widget doesn't crash the whole app.

**Follow-ups**
- *"Why not try/catch?"* — try/catch doesn't catch render errors in children; an error boundary does (via `componentDidCatch`/libraries).
- *"Where do you place them?"* — Around major regions (each report panel) so a failure is isolated and reported to App Insights.

---

## C20 · Suspense and code-splitting

**Simple explanation.** **`React.lazy` + `Suspense`** load a component's code only when needed, showing a fallback (spinner) while it loads — shrinking the initial bundle so the app starts faster.

```tsx
const Reports = React.lazy(() => import('./features/reports/Reports'));
<Suspense fallback={<Spinner />}><Reports /></Suspense>
```

**Follow-ups**
- *"What problem does this solve?"* — A huge single bundle slows first load; splitting by route/feature loads only what's needed.
- *"Suspense for data too?"* — Yes with data libraries/frameworks — it can suspend until data is ready, unifying loading states.

---

## C21 · Routing with React Router

**Simple explanation.** React has no built-in router, so I add **React Router**: it maps URLs to components, supports nested routes, route params, and lazy-loaded routes, and lets me guard routes (redirect if not authenticated).

**Follow-ups**
- *"How do you protect a route?"* — A wrapper that checks auth and redirects to login — but the **API still authorises** every call.
- *"Nested routes value?"* — Shared layouts (a reports shell with sub-pages) without duplicating chrome.

---

## C22 · TypeScript with React

**Simple explanation (full-stack lens).** I always use **TypeScript** — typed props, state, and API responses catch mistakes at build time. Shared DTO types (generated from the API's OpenAPI) mean a back-end contract change breaks the front-end build, not production.

```tsx
type ReportProps = { type: ReportType; onSelect: (id: string) => void };
```

**Follow-ups**
- *"Biggest TS win in React?"* — Typed props + typed API responses — whole classes of bugs vanish before running.
- *"`type` vs `interface` for props?"* — Either works; I use `type` for props/unions and stay consistent across the codebase.

---

## C23 · Accessibility

**Simple explanation.** Accessible UIs (a11y) work for everyone and are often a compliance requirement. I use **semantic HTML** (real `<button>`, `<label>`), keyboard navigation, focus management, ARIA only where needed, and sufficient colour contrast — checked with axe/Lighthouse in CI.

**Follow-ups**
- *"First a11y step?"* — Use semantic elements — most accessibility comes free from correct HTML.
- *"How do you test it?"* — Automated axe checks in CI plus keyboard/screen-reader spot checks — tools catch ~50%, manual covers the rest.

---

## C24 · Styling approaches

**Simple explanation.** Options: plain CSS/**CSS Modules** (scoped classes), **CSS-in-JS** (styled-components/Emotion), and utility CSS (**Tailwind**). I pick per project — CSS Modules or Tailwind for performance and simplicity; a design-system component library for consistency across teams.

**Follow-ups**
- *"CSS-in-JS downside?"* — Runtime cost and larger bundles — for perf-sensitive apps I lean to CSS Modules/Tailwind or zero-runtime CSS-in-JS.
- *"How do you keep styling consistent?"* — A shared design system/tokens so every team uses the same spacing, colour and components.

---

## C25 · Build tooling: Vite and bundling

**Simple explanation.** Modern React apps build with **Vite** (fast dev server + optimised production build) or the framework's tooling (Next.js). Bundling tree-shakes dead code, splits chunks, and minifies — I watch the bundle with a size budget in CI.

**Follow-ups**
- *"Why Vite over CRA?"* — Much faster dev startup/HMR and a leaner modern build — CRA is effectively deprecated.
- *"What is tree-shaking?"* — The bundler drops code you don't import — smaller bundles, faster loads.

---

## C26 · Common mistakes I watch for

**Simple explanation.** Recurring React bugs I catch in reviews: using the array index as a key, missing `useEffect` dependencies (stale data) or cleanup (leaks), unnecessary state (derive it instead), over-using Context (re-render storms), premature memoisation, and putting business rules on the client instead of the API.

**Follow-ups**
- *"Most common performance bug?"* — New object/function literals as props causing children to re-render — stabilise with useMemo/useCallback where it matters.
- *"Derived state smell?"* — Storing something you can compute from existing state/props — compute it in render instead of duplicating state.

---

## C27 · Micro-frontends

**Simple explanation (architect lens).** A **micro-frontend** splits a large app into independently-built, independently-deployed pieces (often via Module Federation) so multiple teams ship without stepping on each other. Powerful but adds complexity — I use it only when team scale justifies it.

**Follow-ups**
- *"When micro-frontends?"* — Many teams, one large app, needing independent release cadence — otherwise a well-structured monolith SPA is simpler.
- *"Main risk?"* — Shared-dependency and consistency overhead — governance (shared design system, versions) is essential.

---

## C28 · Design systems and component libraries

**Simple explanation.** A **design system** is a shared, documented set of reusable components and tokens (colour, spacing, typography). I build one (or adopt MUI/Ant/Fluent) so every screen looks consistent and teams don't rebuild buttons/tables — my reused `DataGrid` on TCW is exactly this idea.

**Follow-ups**
- *"Build vs buy a component library?"* — Buy/adopt for speed; build a thin wrapper layer so we can theme and swap later without rewriting screens.
- *"How do you document it?"* — Storybook — living docs of every component and its states.

---

## C29 · Real-time updates

**Simple explanation.** For live data (prices, statuses) I use **WebSockets** or **SignalR** (with my .NET back end) to push updates, or Server-Sent Events for one-way streams. React state updates from the stream and the UI re-renders — with care to avoid update storms on high-frequency feeds.

**Follow-ups**
- *"WebSocket vs polling?"* — WebSocket/SignalR for true real-time push; polling (or React Query refetch) for near-real-time when simplicity wins.
- *"High-frequency feed problem?"* — Too many re-renders — I throttle/batch updates and virtualise the list.

---

## C30 · When I choose React

**How I answer (decision lens).** *"I choose React when I want flexibility and a huge ecosystem, a component-driven UI, and a team comfortable assembling their own stack (React Router, React Query, TypeScript). It's my default for interactive, data-heavy internal apps like the TCW reporting screens. I'd lean to Angular instead for a very large, multi-team enterprise build wanting an opinionated, batteries-included framework, and to Next.js when SEO and fast first paint matter."*

**Follow-ups**
- *"React's main trade-off?"* — Freedom = decisions; I mitigate it with a fixed, documented stack and structure so the team is consistent.
- *"Would you still pick React in 3 years?"* — I choose per project on merit — React remains excellent, but I stay open to Angular/Next/Svelte by fit (see file 30).

---

## Section index

| # | Concept | One-line takeaway |
|---|---|---|
| C1 | What is React | A library for building UI from reusable, declarative components |
| C2 | Components, props, JSX | Functions returning UI; props flow down and are read-only |
| C3 | State & useState | Data that changes; updating it re-renders the component |
| C4 | useEffect | Side effects (fetch/timers) with a dependency array + cleanup |
| C5 | Virtual DOM | In-memory diff updates only the DOM nodes that changed |
| C6 | Lists & keys | Map arrays to components with stable unique keys; handle all states |
| C7 | Hooks & custom hooks | `use` functions with two rules; extract shared logic into custom hooks |
| C8 | State management | Context for global values; React Query for server data (a cache) |
| C9 | Performance | memo/useMemo/useCallback + virtualisation for large grids |
| C10 | App architecture | Feature folders, dumb UI + logic in hooks, one typed API client |
| C11 | Data fetching | React Query + shared DTO types generated from OpenAPI |
| C12 | CSR/SSR/Next.js | CSR for internal apps; SSR/Next.js for SEO & fast first paint |
| C13 | Security | API is the boundary; escape XSS; never trust the client |
| C14 | Testing | Testing Library + Jest + Playwright; quality gates in CI |
| C15 | useReducer | Centralise complex state in a pure reducer; easy to test |
| C16 | useRef | Mutable value/DOM access without re-rendering |
| C17 | Controlled forms | State-driven inputs; React Hook Form + Zod; API re-validates |
| C18 | Lifting state | Move shared state to common parent; prefer composition |
| C19 | Error boundaries | Catch child render errors, show fallback, report |
| C20 | Suspense & lazy | Code-split with React.lazy for a smaller first load |
| C21 | Routing | React Router: nested routes, params, guarded routes |
| C22 | TypeScript | Typed props + API DTOs from OpenAPI catch bugs at build |
| C23 | Accessibility | Semantic HTML, keyboard, ARIA; axe in CI |
| C24 | Styling | CSS Modules/Tailwind for perf; design system for consistency |
| C25 | Build tooling | Vite; tree-shaking + code-split + size budget in CI |
| C26 | Common mistakes | index keys, missing deps, needless state/Context storms |
| C27 | Micro-frontends | Independent team deploys; use only when scale justifies |
| C28 | Design systems | Shared components/tokens; reuse (my DataGrid); Storybook |
| C29 | Real-time | WebSockets/SignalR push; throttle high-frequency feeds |
| C30 | When to choose React | Flexible, ecosystem-rich; Angular for big enterprise, Next for SEO |

---

[← My First 90 Days](27-first-90-days.md) · [Home](README.md) · [Next → Concept: Angular](29-concept-angular.md)
