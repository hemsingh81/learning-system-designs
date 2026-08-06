# 16 · Deep Dive: React & TypeScript (10 questions)

[← Deep Dive: .NET & C#](15-deepdive-dotnet.md) · [Home](README.md) · [Next → Deep Dive: Python & Data](17-deepdive-python-data.md)

This is the React-heavy round with TypeScript throughout — where they test whether I really build front ends or just wire them. I built the React reporting screens on TCW (A) and Angular front ends on TengizChevroil (C), so I answer from real component code, all typed.

> Opening line for a front-end-deep panel: *"I write React with TypeScript because the compiler catches the bug before the user does. My components handle every state — loading, error, empty, data — and I treat server data as a cache, not as app state."*

**Jump to:** [R1 TS generics](#r1--typescript-generics-and-real-types) · [R2 typing components](#r2--typing-components-and-props-properly) · [R3 hooks internals](#r3--hooks-rules-and-what-actually-re-renders) · [R4 useEffect](#r4--useeffect-done-right) · [R5 performance](#r5--react-performance-memo-usememo-usecallback) · [R6 custom hooks](#r6--custom-hooks-and-reuse) · [R7 forms](#r7--forms-and-validation) · [R8 error boundaries](#r8--error-boundaries-and-suspense) · [R9 testing](#r9--testing-react-the-right-way) · [R10 patterns & a11y](#r10--component-patterns-and-accessibility) · [Section index](#section-index)

---

## R1 · TypeScript generics and real types

**What they are testing.** Whether I use TypeScript for real safety or just sprinkle `any`.

**How I answer.** Generics let me write reusable code that keeps its types. A typed fetch helper I actually use:

```typescript
async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json() as Promise<T>;
}

// caller gets full type safety, no `any`
const positions = await getJson<Position[]>(`/api/reports/${type}?asOf=${asOf}`);
```

**Utility types** save me writing duplicate shapes:
```typescript
type Position = { ticker: string; quantity: number; marketValue: number; asOf: string };
type PositionSummary = Pick<Position, 'ticker' | 'marketValue'>;   // subset
type PartialPosition = Partial<Position>;                           // all optional (patch)
type ReadonlyPosition = Readonly<Position>;                         // immutable
```

**Discriminated unions** — how I model the four screen states so the compiler forces me to handle each:
```typescript
type ReportState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'empty' }
  | { status: 'success'; data: T };
```
Now a `switch` on `status` is exhaustively checked — if I forget `empty`, TypeScript complains. That is the compiler catching my bug.

**Lesson.** *"Generics keep types through reusable code, and discriminated unions make the compiler force me to handle every state. `any` throws all of that away — I treat an `any` in a review as a defect."*

**Follow-ups**
- *"`unknown` vs `any`?"* — `unknown` is safe — I must narrow it before use; `any` disables checking entirely. I use `unknown` for genuinely untyped input, then validate.
- *"`type` vs `interface`?"* — `interface` for object shapes that might be extended; `type` for unions, primitives, and composition. Mostly interchangeable for objects.
- *"How do you type an API response you don't control?"* — Define the type from the contract and validate at the boundary (e.g. Zod), so a shape change fails loudly, not silently.

---

## R2 · Typing components and props properly

**What they are testing.** Whether my component contracts are precise — loose props are a runtime-bug source.

**How I answer.** Props are a typed contract. I make illegal states unrepresentable where I can:

```tsx
type ButtonProps = {
  variant: 'primary' | 'secondary' | 'danger';   // not just string
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
};

function Button({ variant, onClick, disabled = false, children }: ButtonProps) {
  return <button className={`btn btn-${variant}`} onClick={onClick} disabled={disabled}>{children}</button>;
}
```

The `variant` is a union, not `string`, so a typo is a compile error. For a component that wraps a native element, I extend the real HTML attribute types instead of re-declaring them:

```tsx
type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};
```

And I avoid `React.FC` these days — it implicitly adds `children` and complicates generics; a plain typed function is cleaner.

**Lesson.** *"Props are a contract — I use unions over `string`, extend native HTML types instead of re-typing them, and make illegal combinations impossible to compile. A precise prop type deletes a category of runtime bug."*

**Follow-ups**
- *"Making illegal states unrepresentable?"* — e.g. a discriminated union of props so you can't pass `href` and `onClick` to the same button-or-link component.
- *"Generic components?"* — A typed `Table<T>` that infers the row type from the data — real reuse across every report.
- *"Default props?"* — Default parameter values in the destructure, not the legacy `defaultProps`.

---

## R3 · Hooks rules and what actually re-renders

**What they are testing.** Whether I understand render behaviour — the root of most React performance questions.

**How I answer.** A component re-renders when its **state changes**, its **props change**, or its **parent re-renders**. That last one surprises people: a parent re-render re-renders all children by default, even if their props didn't change (until you memoize — [R5](#r5--react-performance-memo-usememo-usecallback)).

**The rules of hooks, and why they exist:** hooks must be called in the same order every render — so never inside a condition or loop. React tracks hook state *by call order*, not by name; a conditional hook shifts the order and corrupts state:

```tsx
// WRONG — conditional hook, breaks the order contract
if (isLoggedIn) { const [name, setName] = useState(''); }

// RIGHT — hook always runs; the condition is inside
const [name, setName] = useState('');
if (isLoggedIn) { /* use name */ }
```

**State updates are batched and asynchronous** — so I use the functional updater when the new value depends on the old:
```tsx
setCount(c => c + 1); // correct across batching
setCount(count + 1);  // can use a stale value
```

**Lesson.** *"A component re-renders on state change, prop change, or parent render — and hooks work by call order, so they must never be conditional. When new state depends on old, always use the functional updater or you'll read a stale value."*

**Follow-ups**
- *"Why does state seem stale in a closure?"* — A closure captures the value from its render. The functional updater or a ref avoids reading a stale capture.
- *"`useState` vs `useReducer`?"* — `useReducer` when state transitions are complex or interdependent — the report's loading/error/empty/data machine is a natural reducer.
- *"Key prop?"* — Stable, unique keys so React reconciles lists correctly; index-as-key causes bugs when the list reorders.

---

## R4 · useEffect, done right

**What they are testing.** Whether I use effects correctly — the most misused hook, and the source of infinite loops and race conditions.

**How I answer.** An effect synchronises with something **outside** React — a fetch, a subscription, the DOM. It is not for deriving state from props (that's just a calculation during render).

The dependency array and cleanup are where correctness lives — the fetch pattern from [F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen), typed and race-safe:

```tsx
useEffect(() => {
  const controller = new AbortController();
  let active = true;
  (async () => {
    try {
      const data = await getJson<Position[]>(`/api/reports/${type}?asOf=${asOf}`, controller.signal);
      if (active) setState({ status: data.length ? 'success' : 'empty', data });
    } catch (e) {
      if (active && (e as Error).name !== 'AbortError')
        setState({ status: 'error', message: (e as Error).message });
    }
  })();
  return () => { active = false; controller.abort(); }; // cleanup on unmount / dep change
}, [type, asOf]); // re-run ONLY when these change
```

The cleanup does two jobs: aborts the in-flight fetch and flips `active` so a late response can't set state on an unmounted component. The dependency array lists exactly what the effect reads — lying to it (omitting a dep) is the classic stale-closure bug; over-listing it causes infinite loops.

**Lesson.** *"An effect syncs with the outside world and must clean up after itself — abort the fetch, ignore the late response. And the dependency array must be honest: exactly what the effect reads, no more, no less."*

**Follow-ups**
- *"Effect running twice in dev?"* — Strict Mode intentionally double-invokes to surface missing cleanup. If double-run breaks something, my cleanup is wrong.
- *"Deriving state in an effect?"* — Anti-pattern. If it can be computed from props/state during render, compute it — don't mirror it into state via an effect.
- *"Data fetching — effect or library?"* — For anything real I use React Query ([F6](14-fullstack-hands-on.md#f6--how-do-you-handle-state-and-data-fetching-in-react)); the raw effect is for teaching and for genuinely non-cache side effects.

---

## R5 · React performance: memo, useMemo, useCallback

**What they are testing.** Whether I optimise with a profiler or by cargo-culting `useMemo` everywhere.

**How I answer.** First: **measure with the React Profiler**, don't guess. Then apply the right tool:

- **`React.memo`** — skip re-rendering a child when its props are unchanged (shallow compare). Useful for an expensive child under a frequently-rendering parent.
- **`useMemo`** — cache an expensive *calculation* between renders.
- **`useCallback`** — keep a *function identity* stable so a `memo`'d child doesn't re-render because its callback prop is "new" every render.

```tsx
const sorted = useMemo(
  () => positions.slice().sort((a, b) => b.marketValue - a.marketValue),
  [positions] // only re-sort when positions change
);

const handleSelect = useCallback((ticker: string) => onSelect(ticker), [onSelect]);

const Row = React.memo(function Row({ p }: { p: Position }) { /* ... */ });
```

The honest part: memoization is not free — it costs memory and a comparison. On a small component it can be slower than just re-rendering. So I reach for it when the Profiler shows a real problem: an expensive sort on a big list, or a heavy child re-rendering needlessly. For a huge table, the bigger win is **virtualisation** (render only visible rows) and server-side paging — not memoizing 50,000 rows.

**Lesson.** *"Profile first. `memo` skips unchanged children, `useMemo` caches a calculation, `useCallback` stabilises a function so a memo'd child stays put. But memoization has a cost — sprinkling it everywhere makes code slower and harder to read."*

**Follow-ups**
- *"Why did my `memo` child still re-render?"* — A new object/array/function prop every render defeats the shallow compare — that's what `useCallback`/`useMemo` fix.
- *"Biggest real-world win?"* — Virtualising long lists and paging server-side. DOM size, not render count, is usually the bottleneck on a reporting screen.
- *"React Compiler?"* — It auto-memoizes, reducing manual `useMemo`/`useCallback` — but I still understand the mechanics so I can reason about it.

---

## R6 · Custom hooks and reuse

**What they are testing.** Whether I extract reusable logic cleanly — the React way to share behaviour.

**How I answer.** A custom hook is just a function using other hooks. It is how I share stateful logic without wrapper-component nesting. The typed data hook behind every report screen:

```tsx
function useReport<T>(url: string) {
  const [state, setState] = useState<ReportState<T>>({ status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    getJson<T[]>(url, controller.signal)
      .then(d => active && setState({ status: d.length ? 'success' : 'empty', data: d as T }))
      .catch(e => active && e.name !== 'AbortError' && setState({ status: 'error', message: e.message }));
    return () => { active = false; controller.abort(); };
  }, [url]);
  return state;
}

// every screen uses it — the four-state discipline, once, typed, reused
const report = useReport<Position>(`/api/reports/${type}?asOf=${asOf}`);
```

This is the same instinct as the reusable Web API controller pattern on the backend (A) — write the shape once, reuse it everywhere, so a new report is one line, not a new hand-rolled fetch-and-state block.

**Lesson.** *"Custom hooks share stateful logic the React way — I extract the four-state fetch-and-cache once, typed, and every screen reuses it. Same instinct as my reusable backend patterns: write it once, reuse it, shorten the build."*

**Follow-ups**
- *"Naming?"* — Always `use*` so the linter enforces the rules-of-hooks on it.
- *"Hook vs HOC vs render prop?"* — Hooks won — no wrapper nesting, composable, typed. HOCs/render-props are legacy patterns I can still read.
- *"Testing a hook?"* — `renderHook` from Testing Library, asserting on the returned state transitions.

---

## R7 · Forms and validation

**What they are testing.** Whether I build real forms — controlled inputs, validation, submission, error display.

**How I answer.** For anything beyond trivial, I use React Hook Form + a schema (Zod), because hand-rolling controlled state for every field is boilerplate and re-renders on every keystroke.

```tsx
const schema = z.object({
  portfolioId: z.string().min(1, 'Required'),
  asOf: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Use YYYY-MM-DD'),
});
type FormValues = z.infer<typeof schema>; // types derived from the schema — one source of truth

function ReportForm({ onRun }: { onRun: (v: FormValues) => void }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<FormValues>({ resolver: zodResolver(schema) });

  return (
    <form onSubmit={handleSubmit(onRun)} noValidate>
      <label htmlFor="asOf">As of</label>
      <input id="asOf" {...register('asOf')} aria-invalid={!!errors.asOf} />
      {errors.asOf && <span role="alert">{errors.asOf.message}</span>}
      <button disabled={isSubmitting}>Run report</button>
    </form>
  );
}
```

The schema is the single source of truth — it validates *and* generates the TypeScript type via `z.infer`. React Hook Form keeps inputs uncontrolled internally, so typing a character doesn't re-render the whole form. And validation always runs **again on the server** ([F4](14-fullstack-hands-on.md#f4--write-a-fastapi-etl-ingestion-endpoint)) — client validation is UX, not security.

**Lesson.** *"Schema-first forms — one Zod schema validates the input and generates the type. React Hook Form avoids the per-keystroke re-render. And I never trust client validation for correctness; the server validates too."*

**Follow-ups**
- *"Controlled vs uncontrolled?"* — Controlled for instant cross-field logic; uncontrolled (RHF) for performance on big forms.
- *"Accessibility?"* — `label` tied to input, `aria-invalid`, `role="alert"` on errors, focus the first error on submit.
- *"Async validation?"* — e.g. "portfolio exists" — debounced, against the API, with a pending state.

---

## R8 · Error boundaries and Suspense

**What they are testing.** Whether one broken component can white-screen the whole app on my watch.

**How I answer.** A JavaScript error in render crashes the whole React tree unless an **error boundary** catches it. So I wrap regions in a boundary that shows a fallback instead of a blank page:

```tsx
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    logger.error('UI crash', { error, info }); // report it, with the correlation ID
  }
  render() {
    return this.state.hasError
      ? <ErrorBanner message="Something went wrong. Please retry." />
      : this.props.children;
  }
}
```

I place boundaries around independent regions — so a crash in one report widget doesn't take down the navigation or the other widgets. It pairs with the per-layer error handling on the backend ([F10](14-fullstack-hands-on.md#f10--how-do-you-handle-errors-across-the-stack)): the API returns a safe error, the data hook surfaces the `error` state, and the boundary catches anything unexpected in render.

**Suspense** handles the *loading* side declaratively — with React Query/`use`, a boundary can show a spinner for the whole region while data loads, instead of each component tracking its own loading flag.

**Lesson.** *"An error boundary stops one broken component white-screening the app — I wrap independent regions so a crash is contained and reported, not silent. It's the front-end half of centralised error handling."*

**Follow-ups**
- *"Boundaries catch everything?"* — No — not event handlers or async code; those I try/catch and set error state myself.
- *"Where to place them?"* — Around independent regions and risky third-party widgets, not just one at the root.
- *"Retry after error?"* — A reset key on the boundary + a retry button that re-fetches.

---

## R9 · Testing React the right way

**What they are testing.** Whether I test behaviour users care about, not implementation details.

**How I answer.** React Testing Library, and the golden rule: **test what the user sees and does, not the internals**. I query by role/text (like a user), not by CSS class or component state.

```tsx
test('shows an error banner when the report API fails', async () => {
  server.use(rest.get('/api/reports/:type', (_, res, ctx) => res(ctx.status(500))));
  render(<ReportScreen reportType="em" asOf="2026-08-06" />);

  expect(await screen.findByRole('alert')).toHaveTextContent(/went wrong|failed/i);
});

test('renders rows when data loads', async () => {
  render(<ReportScreen reportType="em" asOf="2026-08-06" />);
  expect(await screen.findByText('AAPL')).toBeInTheDocument();
});
```

I mock the network (MSW), not React internals, so the test exercises the real component including its effect, states and rendering. This tests the *four states* explicitly — a test for error, one for empty, one for success — because those are exactly the states that break in production ([F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen)). I do not assert on `useState` values or call counts; if I refactor the internals but the behaviour is unchanged, the test should still pass.

**Lesson.** *"Test behaviour, not implementation — query by role and text like a user, mock the network not React, and cover the error and empty states, not just the happy path. A test coupled to internals just breaks on every refactor."*

**Follow-ups**
- *"Unit vs integration vs e2e for the front end?"* — Mostly component-integration with RTL; Playwright/Cypress for a few critical user journeys end-to-end.
- *"Testing a custom hook?"* — `renderHook`, asserting the returned state machine.
- *"Snapshot tests?"* — Sparingly — they catch unintended markup changes but are noisy and easy to bless blindly.

---

## R10 · Component patterns and accessibility

**What they are testing.** Architectural taste in the UI, and whether accessibility is real for me — it is, in regulated clients.

**How I answer.** The patterns I actually reach for:

- **Composition over configuration** — a component that takes `children`/slots beats one with 20 boolean props. `<Card><Card.Header/>...</Card>` scales; `<Card showHeader showFooter .../>` does not.
- **Container / presentational split** — a hook (or container) owns data and state; a pure presentational component just renders props. The presentational part is trivial to test and reuse.
- **Design-system components** — typed, accessible primitives (Button, Input, Table) reused everywhere, same instinct as the reusable backend patterns.

**Accessibility is not optional** for the regulated clients I serve (healthcare, public sector — E; financial — A). Concretely: semantic HTML first (`<button>`, `<table>`, `<nav>` — not `<div onClick>`); labels tied to inputs; `aria-*` only to fill gaps semantic HTML can't; visible focus states; keyboard navigability; and colour contrast that meets WCAG. On the completion platform (C) the real challenge was making a complex approval workflow usable by non-technical engineers — so clarity and keyboard flow were the architecture, not an afterthought.

**Lesson.** *"Compose components rather than configuring them, split data from presentation, and build accessibility in with semantic HTML — not bolted on with ARIA at the end. For regulated clients, accessible and clear IS the requirement, not a nice-to-have."*

**Follow-ups**
- *"How do you test a11y?"* — `jest-axe` in unit tests, keyboard-only manual passes, and a screen-reader smoke test on key flows.
- *"CSS approach?"* — Whatever the team standardised (CSS Modules, Tailwind, styled) — consistency over preference; I don't mix three in one app.
- *"Design system?"* — Typed, documented, accessible primitives so every screen is consistent and the four states look the same everywhere.

---

## Section index

| # | Question | Core message |
|---|---|---|
| R1 | TS generics & types | Generics keep types; discriminated unions force handling every state |
| R2 | Typing components | Props are a contract — unions over string, make illegal states uncompilable |
| R3 | Hooks & re-renders | Re-render on state/props/parent; hooks work by call order, never conditional |
| R4 | useEffect | Sync with the outside world and clean up; honest dependency array |
| R5 | Performance | Profile first; memo/useMemo/useCallback have a cost; virtualise big lists |
| R6 | Custom hooks | Extract the four-state fetch once, typed, reuse everywhere |
| R7 | Forms | Schema-first (Zod infers the type); server re-validates |
| R8 | Error boundaries | Contain a crash to one region; the front-end half of error handling |
| R9 | Testing | Behaviour not internals; query by role; cover error & empty states |
| R10 | Patterns & a11y | Compose over configure; accessibility built in with semantic HTML |

---

[← Deep Dive: .NET & C#](15-deepdive-dotnet.md) · [Home](README.md) · [Next → Deep Dive: Python & Data](17-deepdive-python-data.md)
