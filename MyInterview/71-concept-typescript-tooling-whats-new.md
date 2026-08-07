# 71 · Concept: TypeScript & Frontend Tooling — What's New (Version Evolution) (30 questions)

[← Angular What's New](70-concept-angular-whats-new.md) · [Home](README.md) · [Next → Back to Home](README.md)

This file explains **what is new in TypeScript and the frontend build/tooling world** — TS 4.x→5.x, ES modules, Vite, esbuild/SWC, the new decorators, and modern testing/linting — in simple English, with *why it matters* and *old-vs-new code*. Both TCW front ends (React and Angular) are TypeScript, so I keep the language and toolchain current and fast.

> Simple one-liner: *"TypeScript keeps making types safer and inference smarter (`satisfies`, `const` type params, standard decorators), while the build world got dramatically faster — ESM everywhere, Vite/esbuild/SWC replacing Webpack/Babel. The theme is 'safer types, faster tools'."*

**Jump to (TypeScript):** [TW1 Why TS](#tw1--why-typescript-and-how-it-ships) · [TW2 strict mode](#tw2--strict-mode-and-config) · [TW3 4.x highlights](#tw3--typescript-4x-highlights) · [TW4 satisfies](#tw4--the-satisfies-operator-49) · [TW5 const type params](#tw5--const-type-parameters-50) · [TW6 standard decorators](#tw6--standard-decorators-50) · [TW7 using/disposable](#tw7--using-and-explicit-resource-management-52) · [TW8 5.x perf](#tw8--typescript-5x-performance-and-esm)
> **Key type features:** [TW9 Utility types](#tw9--utility-types) · [TW10 Generics](#tw10--generics) · [TW11 Union/narrowing](#tw11--unions-and-narrowing) · [TW12 Template literal types](#tw12--template-literal-types) · [TW13 unknown vs any](#tw13--unknown-vs-any) · [TW14 Type vs interface](#tw14--type-alias-vs-interface)
> **Modules & build:** [TW15 ESM vs CommonJS](#tw15--esm-vs-commonjs) · [TW16 Vite](#tw16--vite) · [TW17 esbuild](#tw17--esbuild) · [TW18 SWC](#tw18--swc) · [TW19 Bundlers vs no-bundle](#tw19--bundlers-vs-native-esm-dev) · [TW20 Monorepos](#tw20--monorepos-nx--turborepo)
> **Package & quality tooling:** [TW21 Package managers](#tw21--package-managers-npmpnpmyarn) · [TW22 ESLint flat config](#tw22--eslint-flat-config--typescript-eslint) · [TW23 Prettier/Biome](#tw23--formatting-prettier-and-biome) · [TW24 Testing (Vitest)](#tw24--testing-vitest) · [TW25 Type-only imports](#tw25--type-only-imports)
> **Runtime & future:** [TW26 Node/Deno/Bun](#tw26--runtimes-node-deno-bun) · [TW27 Type-stripping](#tw27--native-typescript-type-stripping)
> **Decisions:** [TW28 Migrating JS→TS](#tw28--migrating-javascript-to-typescript) · [TW29 When to adopt](#tw29--when-i-adopt-new-tooling) · [TW30 My approach](#tw30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of "what's new in TypeScript and frontend tooling" in plain English. Hold these ideas and every question hangs off one of them.

**1. TypeScript's whole job is to catch bugs before runtime.** Every release makes the type system **safer** (stricter checks) and **smarter** (better inference), so I write fewer annotations and catch more mistakes at compile time. `satisfies`, `const` type params and narrowing are all about better inference.

**2. TS ships roughly every 3 months and follows the standards.** It tracks ECMAScript (new JS features) and adopts stage-3 proposals — e.g. **standard decorators** and **`using`/disposables** landed as they became standard. So "new TS" often means "new JavaScript, typed".

**3. The build world's theme is 'faster tools'.** The old stack (Webpack + Babel) was slow. The new stack — **Vite** (dev), **esbuild** and **SWC** (Go/Rust-based transpilers) — is 10–100× faster. Instant dev servers and quick CI are the payoff.

**4. ES Modules (ESM) won.** `import/export` is now the standard everywhere — browsers, Node, bundlers. The old **CommonJS** (`require`) is legacy. Modern tooling assumes ESM, which enables tree-shaking and native browser modules.

**5. `strict` mode is the real TypeScript.** Turning on `strict` (and treating type errors as build failures) is what actually delivers the safety. TS without strict is barely typed. This is a config decision I always make.

**6. Old way vs new way is the interview gold.** For each item I can state the before/after: `as const` casts → `satisfies`; experimental Babel decorators → standard decorators; Webpack/Babel → Vite/esbuild/SWC; CommonJS `require` → ESM `import`; `.eslintrc` → flat config; Jest → Vitest.

**7. The toolchain is consolidating and speeding up.** Vite unifies dev/build; Biome merges lint+format in Rust; pnpm fixes npm's disk/speed issues; Vitest reuses Vite config. Fewer, faster tools.

**8. I adopt for safety and speed, not novelty.** A TS feature earns its place if it catches more bugs or clarifies intent; a tool earns its place if it's meaningfully faster or simpler for *my* team. Newest loses to proven-and-fast on the critical path.

**The full-stack / architect lens:** the later Q&As cover TypeScript features (strict, 4.x/5.x highlights, `satisfies`, const type params, standard decorators, `using`, utility types, generics, narrowing, template literal types, `unknown`, type vs interface), then modules and build (ESM vs CJS, Vite, esbuild, SWC, monorepos), package/quality tooling (pnpm, ESLint flat config, Prettier/Biome, Vitest, type-only imports), runtimes (Node/Deno/Bun, native type-stripping), and JS→TS migration — all with old-vs-new. They trace back to the core: safer types, faster tools, ESM everywhere, adopted for real benefit.

**One rule I never break:** *turn on `strict` and treat type errors as build failures — then adopt new TS features and faster tools for genuine safety or speed, never for novelty.*

---

## TW1 · Why TypeScript and how it ships

**Simple explanation.** **TypeScript** adds static types to JavaScript, catching bugs at compile time and powering editor autocomplete/refactoring. It ships a new minor (4.8, 4.9, 5.0, 5.x…) roughly every **3 months**.

**Architect's view:** on any team over a few people, TS pays for itself in caught bugs and safe refactors. I keep it current for better inference and editor tooling.

**Follow-ups**
- *Does TS run at runtime?* — No — types are erased; it compiles to plain JS.
- *Version check?* — `tsc --version` / `package.json`.

---

## TW2 · strict mode and config

**Simple explanation.** **`"strict": true`** in `tsconfig.json` turns on all the strong checks (`strictNullChecks`, `noImplicitAny`, etc.). Without it, TS is barely safer than JS.

```json
{ "compilerOptions": { "strict": true, "noUncheckedIndexedAccess": true } }
```

**Old vs new.** Older projects ran non-strict (lots of implicit `any`). Modern projects are strict from day one.

**Architect's view:** I mandate `strict` and make type errors fail the build — the single biggest quality lever in a TS codebase.

**Follow-ups**
- *Migrating a loose project?* — Enable strict flags incrementally; fix file by file.
- *noUncheckedIndexedAccess?* — Makes `arr[i]` possibly-undefined — catches real bugs.

---

## TW3 · TypeScript 4.x highlights

**Simple explanation.** 4.x added **template literal types** (4.1), **labeled tuple elements**, better inference, and quality-of-life: `.at()` typing, **`satisfies`** (4.9), and faster editor performance.

**Architect's view:** 4.x was steady refinement — smarter inference so I write fewer manual types. 4.9's `satisfies` is the standout.

**Follow-ups**
- *Template literal types use?* — Type-safe string patterns (e.g. route/event names).
- *Biggest 4.x win?* — `satisfies` (next question).

---

## TW4 · The satisfies operator (4.9)

**Simple explanation.** **`satisfies`** checks a value matches a type **without widening** its inferred type — you get validation *and* the precise literal types.

```ts
// NEW (4.9)
const config = {
  port: 8080,
  host: "localhost"
} satisfies Record<string, string | number>;
config.port; // still typed as number (not string|number)

// OLD: `: Record<...>` validated but widened; `as const` lost validation
```

**Old vs new.** Before, a type annotation validated but *widened* the value; `as const` kept literals but skipped validation. `satisfies` gives both.

**Architect's view:** my default for config objects and lookup maps — validated shape, precise types.

**Follow-ups**
- *satisfies vs as?* — `as` is an assertion (can be unsafe); `satisfies` is a real check that keeps inference.
- *Common use?* — Theme/config objects, discriminated maps.

---

## TW5 · const type parameters (5.0)

**Simple explanation.** **`const` type parameters** (5.0) let a generic infer **literal (narrow)** types automatically, without callers writing `as const`.

```ts
function first<const T>(arr: readonly T[]): T { return arr[0]; }
const x = first(["a", "b"]); // x: "a" (literal), not string
```

**Old vs new.** Before, you needed `as const` at the call site to keep literals. Now the function can request it.

**Architect's view:** nicer library APIs — precise inference for callers with zero extra syntax.

**Follow-ups**
- *When useful?* — APIs where literal types drive further inference (builders, routers).
- *Any cost?* — None to callers; it's an authoring choice.

---

## TW6 · Standard decorators (5.0)

**Simple explanation.** **TypeScript 5.0** implemented the **standard (stage-3 ECMAScript) decorators** — no more `experimentalDecorators` flag for the standard form.

```ts
function log(target: any, ctx: ClassMethodDecoratorContext) { /* standard signature */ }
class Api { @log fetch() {} }
```

**Old vs new.** The old decorators were an experimental, non-standard proposal (used by Angular/NestJS). The new ones follow the finalised standard — different signature.

**Architect's view:** important to know both exist — Angular still uses the legacy metadata-based decorators; new plain-TS code can use the standard ones.

**Follow-ups**
- *Do Angular/Nest use standard decorators?* — Not yet — they rely on `experimentalDecorators` + `emitDecoratorMetadata`.
- *Metadata?* — Standard decorators added a metadata mechanism separately.

---

## TW7 · using and explicit resource management (5.2)

**Simple explanation.** **TS 5.2** added **`using`** (and `await using`) for the ECMAScript **explicit resource management** proposal — automatic cleanup (`Symbol.dispose`) when a scope ends, like C#'s `using`.

```ts
{
  using file = openFile("a.txt"); // has [Symbol.dispose]()
  // ... use file
} // file.dispose() called automatically here
```

**Old vs new.** Before, cleanup meant `try/finally`. `using` makes it declarative and leak-resistant.

**Architect's view:** great for file handles, DB connections, locks — deterministic cleanup without boilerplate.

**Follow-ups**
- *await using?* — For async disposables (`Symbol.asyncDispose`).
- *Runtime support?* — Needs the polyfill/target that supports it.

---

## TW8 · TypeScript 5.x performance and ESM

**Simple explanation.** 5.x focused on **smaller, faster** compiles (decorator/enum improvements, `moduleResolution: "bundler"`), and better **ESM** support. A native (Go-based) compiler for major speedups is in progress.

**Architect's view:** faster `tsc` and editor responsiveness matter on big codebases; `moduleResolution: "bundler"` matches how Vite/esbuild actually resolve modules.

**Follow-ups**
- *moduleResolution bundler?* — Resolves like modern bundlers — fewer config headaches.
- *Native tsc?* — A Go port targeting ~10× faster type-checking is underway.

---

## TW9 · Utility types

**Simple explanation.** Built-in **utility types** transform types: `Partial<T>`, `Required<T>`, `Pick<T,K>`, `Omit<T,K>`, `Record<K,V>`, `Readonly<T>`, `ReturnType<F>`.

```ts
type User = { id: number; name: string; email: string };
type Draft = Partial<User>;          // all optional
type Public = Omit<User, "email">;   // drop a field
```

**Architect's view:** they keep types DRY — derive one type from another instead of duplicating shapes across DTOs/forms.

**Follow-ups**
- *Pick vs Omit?* — Pick keeps listed keys; Omit removes them.
- *Custom utilities?* — Build your own with mapped + conditional types.

---

## TW10 · Generics

**Simple explanation.** **Generics** let types be parameterised — reusable, type-safe functions/containers.

```ts
function wrap<T>(value: T): { value: T } { return { value }; }
const r = wrap(5); // { value: number }
```

**Architect's view:** essential for reusable data/service layers (e.g. a generic `ApiResponse<T>`); I add constraints (`<T extends {id:number}>`) to keep them safe.

**Follow-ups**
- *Constraints?* — `extends` limits what T can be.
- *Default type params?* — `<T = string>` provides a fallback.

---

## TW11 · Unions and narrowing

**Simple explanation.** **Union types** (`A | B`) plus **narrowing** (the compiler figures out the specific type from checks) enable safe branching, especially with **discriminated unions**.

```ts
type Shape = { kind: "circle"; r: number } | { kind: "square"; s: number };
function area(s: Shape) {
  switch (s.kind) { case "circle": return Math.PI*s.r**2; case "square": return s.s**2; }
}
```

**Architect's view:** discriminated unions model state/results cleanly (e.g. loading/success/error) and the compiler enforces every case.

**Follow-ups**
- *Exhaustiveness?* — A `never` default catches missed cases at compile time.
- *Type guards?* — `is` predicates (`function isCat(a): a is Cat`) narrow custom types.

---

## TW12 · Template literal types

**Simple explanation.** **Template literal types** (4.1) build string types from patterns — type-safe string keys/events.

```ts
type Event = `on${"Click" | "Hover"}`; // "onClick" | "onHover"
```

**Architect's view:** useful for typed event names, route params, and CSS-in-JS keys — catches typos in strings.

**Follow-ups**
- *Combine with generics?* — Yes — powerful for typed builders.
- *Overuse?* — Can get hard to read; I keep them purposeful.

---

## TW13 · unknown vs any

**Simple explanation.** **`any`** disables type checking (dangerous). **`unknown`** is the safe top type — you must narrow it before use.

```ts
function handle(x: unknown) {
  if (typeof x === "string") return x.toUpperCase(); // narrowed
}
```

**Old vs new.** `unknown` (added in 3.0) is the modern replacement for `any` at boundaries (JSON, API responses).

**Architect's view:** I ban `any` in reviews and use `unknown` at untyped edges, narrowing explicitly — keeps safety intact.

**Follow-ups**
- *Where does any sneak in?* — `JSON.parse`, untyped libs, `catch (e)`.
- *catch typing?* — `catch (e: unknown)` then narrow.

---

## TW14 · type alias vs interface

**Simple explanation.** **`interface`** describes object shapes and can be extended/merged; **`type`** aliases anything (unions, primitives, mapped types). They overlap for object shapes.

**Architect's view:** my rule of thumb — `interface` for public object/contract shapes (extensible), `type` for unions/utilities/complex compositions. Consistency matters more than the exact choice.

**Follow-ups**
- *Declaration merging?* — Interfaces merge; types don't — useful for augmenting libraries.
- *Performance?* — Interfaces can be marginally faster for the checker on large shapes.

---

## TW15 · ESM vs CommonJS

**Simple explanation.** **ES Modules (ESM)** use `import/export` (the standard, tree-shakable, works in browsers). **CommonJS (CJS)** uses `require/module.exports` (legacy Node).

```ts
// ESM (modern)
import { sum } from "./math.js";
// CJS (legacy)
const { sum } = require("./math");
```

**Old vs new.** The whole ecosystem moved to ESM; new packages ship ESM (some dual-publish). Interop can be fiddly.

**Architect's view:** I author ESM everywhere; the payoff is tree-shaking (smaller bundles) and native browser modules.

**Follow-ups**
- *Interop pain?* — Importing CJS from ESM sometimes needs default-import juggling; bundlers smooth it.
- *package.json "type"?* — `"type": "module"` makes `.js` files ESM.

---

## TW16 · Vite

**Simple explanation.** **Vite** is the modern dev/build tool: a **native-ESM dev server** (instant start, fast HMR) plus an optimised production build (Rollup). It replaced Create React App and is Angular's dev server too.

**Old vs new.** Webpack rebuilt the whole bundle on start/change (slow). Vite serves ES modules directly in dev — near-instant.

**Architect's view:** default for new SPAs/libraries; the dev-loop speed alone justifies it. Frameworks (Next/Angular) wrap similar ideas.

**Follow-ups**
- *Why fast in dev?* — No dev bundling; transforms on demand via esbuild.
- *Production bundler?* — Rollup (Vite is adopting Rolldown, a Rust Rollup).

---

## TW17 · esbuild

**Simple explanation.** **esbuild** is a **Go-based** bundler/transpiler that is 10–100× faster than JS-based tools. Vite and Angular use it under the hood for transforms.

**Old vs new.** Replaces Babel/Webpack for transpilation speed; strips types and transforms JSX/TS extremely fast.

**Architect's view:** the reason modern builds got fast. I rarely use it directly — it powers Vite/Angular's builder.

**Follow-ups**
- *Does esbuild type-check?* — No — it strips types fast; `tsc`/IDE does the checking.
- *Why so fast?* — Written in Go, heavily parallel.

---

## TW18 · SWC

**Simple explanation.** **SWC** is a **Rust-based** transpiler (a fast Babel replacement) used by **Next.js**, Jest (via `@swc/jest`) and others.

**Old vs new.** Replaces Babel for TS/JSX transpilation with big speed gains; Next.js uses it for compile and minify.

**Architect's view:** another "native tool = fast" story — I benefit through Next.js's compiler and faster test transforms.

**Follow-ups**
- *SWC vs esbuild?* — Both fast native transpilers; different projects picked different ones.
- *Type-check?* — Also no — transpile only; keep `tsc` for checking.

---

## TW19 · Bundlers vs native ESM dev

**Simple explanation.** In **dev**, Vite skips bundling and serves native ES modules (instant). For **production**, it bundles (Rollup) for optimised, tree-shaken output.

**Old vs new.** Webpack bundled even in dev; the new model is "no-bundle dev, bundle for prod".

**Architect's view:** best of both — fast feedback locally, optimised artifact in prod.

**Follow-ups**
- *Why bundle for prod at all?* — Fewer requests, tree-shaking, minification.
- *Rolldown?* — A Rust-based Rollup replacement to speed the prod build too.

---

## TW20 · Monorepos (Nx / Turborepo)

**Simple explanation.** **Nx** and **Turborepo** manage monorepos — multiple apps/libs in one repo with **caching**, **task orchestration**, and **affected-only** builds/tests.

**Old vs new.** Before, multi-repo or naive monorepos rebuilt everything. These tools cache and only rebuild what changed.

**Architect's view:** for a platform with shared UI/libraries (Projects B/C) a monorepo with caching cuts CI time hugely and enforces consistency.

**Follow-ups**
- *Nx vs Turborepo?* — Nx = richer (generators, graph, plugins); Turborepo = lighter, simpler caching.
- *Remote cache?* — Share build cache across the team/CI.

---

## TW21 · Package managers (npm/pnpm/yarn)

**Simple explanation.** **npm** (default), **yarn** (early speed/workspaces), and **pnpm** (fast, disk-efficient via a content-addressed store and strict linking). pnpm is increasingly the modern default.

**Old vs new.** npm's flat `node_modules` was slow and allowed "phantom dependencies". pnpm is faster and stricter (only declared deps are importable).

**Architect's view:** I lean to **pnpm** for speed, disk savings, and correctness — especially in monorepos.

**Follow-ups**
- *Lockfiles?* — Commit them for reproducible installs.
- *Phantom deps?* — pnpm prevents importing undeclared packages.

---

## TW22 · ESLint flat config + typescript-eslint

**Simple explanation.** ESLint moved to a new **flat config** (`eslint.config.js`) replacing `.eslintrc`; **typescript-eslint** provides TS-aware linting (type-checked rules).

**Old vs new.**

```js
// NEW: eslint.config.js (flat)
import tseslint from "typescript-eslint";
export default tseslint.config(tseslint.configs.recommended);
// OLD: .eslintrc.json with "extends"/"parser" strings
```

**Architect's view:** flat config is clearer and composable; I use type-aware rules to catch real bugs (floating promises, unsafe any).

**Follow-ups**
- *Type-aware rules cost?* — Slower (needs type info) but catches more — worth it in CI.
- *TSLint?* — Deprecated — typescript-eslint replaced it.

---

## TW23 · Formatting: Prettier and Biome

**Simple explanation.** **Prettier** auto-formats code (opinionated, consistent). **Biome** is a newer **Rust** tool that does **lint + format** together, very fast.

**Old vs new.** Prettier (format) + ESLint (lint) were separate JS tools. Biome merges both in one fast binary.

**Architect's view:** Prettier is still the safe default; I watch Biome for teams wanting one fast tool for lint+format.

**Follow-ups**
- *Why auto-format?* — Ends style debates; consistent diffs.
- *Biome mature enough?* — Fast-moving; I trial it, keep Prettier as the default for now.

---

## TW24 · Testing: Vitest

**Simple explanation.** **Vitest** is a fast, Vite-native test runner with a **Jest-compatible API** — it reuses your Vite config and is much faster to start.

**Old vs new.** Jest (Babel-based) was the standard but slow to start and needs separate config. Vitest reuses Vite, supports ESM/TS natively, and runs faster.

**Architect's view:** for Vite projects I default to Vitest (shared config, speed); Jest is still fine on existing setups.

**Follow-ups**
- *Migration from Jest?* — Largely API-compatible — often a small change.
- *E2E?* — Playwright/Cypress separately for browser flows.

---

## TW25 · Type-only imports

**Simple explanation.** **`import type`** imports only types (erased at compile) — avoids accidental runtime imports and side effects, and helps bundlers.

```ts
import type { User } from "./models";      // erased
import { getUser } from "./api";           // runtime
```

**Old vs new.** Before, a type-only import could accidentally pull runtime code. `import type` (and `verbatimModuleSyntax`) make intent explicit.

**Architect's view:** I use `import type` for clarity and to keep bundles clean; the linter can enforce it.

**Follow-ups**
- *verbatimModuleSyntax?* — A tsconfig flag that makes type-vs-value imports explicit/predictable.
- *Why bundlers care?* — They can drop type-only imports entirely.

---

## TW26 · Runtimes: Node, Deno, Bun

**Simple explanation.** **Node.js** is the standard (now with a built-in test runner, `--watch`, and native `.ts` type-stripping arriving). **Deno** (secure, TS-first) and **Bun** (very fast, all-in-one) are challengers.

**Old vs new.** Node kept modernising (ESM, fetch, test runner) partly in response to Deno/Bun. TS is increasingly runnable without a separate build.

**Architect's view:** I stay on Node for the ecosystem/support in enterprise; I watch Bun for speed and Deno for security — but production defaults to Node LTS.

**Follow-ups**
- *Bun's pitch?* — Runtime + bundler + package manager + test runner, all fast.
- *Deno's pitch?* — Secure-by-default, native TS, web-standard APIs.

---

## TW27 · Native TypeScript type-stripping

**Simple explanation.** Recent **Node.js** can run `.ts` files by **stripping types** (no full type-check, just erase types) — run TS directly without a build step for scripts/dev.

**Old vs new.** Before, running TS meant `ts-node`/a build. Native type-stripping removes that friction for many cases.

**Architect's view:** handy for scripts and quick dev; I still run `tsc` in CI for real type-checking (stripping doesn't check types).

**Follow-ups**
- *Does stripping type-check?* — No — it only erases types; keep `tsc` for validation.
- *Deno/Bun?* — Both run TS directly too.

---

## TW28 · Migrating JavaScript to TypeScript

**Simple explanation.** Migration path: add `tsconfig` with `allowJs`, rename files `.js→.ts` gradually, fix types, tighten `strict` flags incrementally, and lean on editor inference.

**Architect's view:** I migrate incrementally (file by file), turning on strict flags one at a time — never a big-bang. `// @ts-check` on JS files is a low-cost first step.

**Follow-ups**
- *JSDoc typing?* — You can type JS via JSDoc as a stepping stone.
- *Third-party types?* — `@types/*` packages or bundled types.

---

## TW29 · When I adopt new tooling

**Simple explanation.** My rule: adopt a TS feature when it **catches more bugs or clarifies intent** (`satisfies`, `unknown`, strict flags); adopt a tool when it's **meaningfully faster/simpler** (Vite, pnpm, Vitest) and stable enough for my team.

**Architect's view:** I keep TS current (safe, ~quarterly), modernise the toolchain for speed (Vite/esbuild/pnpm), and trial the bleeding edge (Biome, Bun, native tsc) on side projects before the critical path.

**Follow-ups**
- *First tooling upgrade you'd make on a legacy app?* — CRA/Webpack → Vite for the dev-loop speed, plus `strict` TS.
- *How do you avoid churn?* — Adopt for a concrete benefit; standardise once, don't chase every tool.

---

## TW30 · My approach

**Simple explanation.** I keep **TypeScript strict and current**, author **ESM** everywhere, use **fast native tooling** (Vite/esbuild/SWC, pnpm, Vitest), adopt smart type features (`satisfies`, const type params, `unknown`, discriminated unions) for safety, and treat **type errors and lint as build failures**. For every feature/tool I know the old way and the new way.

**Architect's view:** the two themes — **safer types** and **faster tools** — both raise developer velocity and reduce bugs, which is exactly what a platform needs at scale. On the TCW front ends I standardise on strict TS + Vite-class tooling, adopt new language features where they catch real bugs, and keep the toolchain fast so the team ships confidently. New feature, same discipline: safety, speed, and a clear before-and-after.

**Follow-ups**
- *One-sentence philosophy?* — "Strict types, fast tools, ESM everywhere."
- *How do you keep the team aligned?* — Shared tsconfig/eslint config + short notes on new TS features and where we use them.

---

## Section index

| ID | Topic | Core message |
|----|-------|--------------|
| TW1 | Why TS / cadence | Static types; ships ~quarterly |
| TW2 | strict mode | `strict` is what makes TS actually safe |
| TW3 | 4.x highlights | Template literal types, better inference, satisfies |
| TW4 | satisfies (4.9) | Validate without widening — keep precise types |
| TW5 | const type params (5.0) | Infer literals without `as const` |
| TW6 | Standard decorators (5.0) | Stage-3 decorators; Angular still uses legacy |
| TW7 | using (5.2) | Deterministic resource cleanup (like C# using) |
| TW8 | 5.x perf/ESM | Faster compiles; `moduleResolution: bundler` |
| TW9 | Utility types | Partial/Pick/Omit/Record keep types DRY |
| TW10 | Generics | Reusable, constrained type-safe code |
| TW11 | Unions/narrowing | Discriminated unions + exhaustiveness |
| TW12 | Template literal types | Type-safe string patterns |
| TW13 | unknown vs any | Use `unknown` at boundaries; ban `any` |
| TW14 | type vs interface | interface for contracts, type for unions/utils |
| TW15 | ESM vs CJS | ESM won; tree-shakable, browser-native |
| TW16 | Vite | Instant dev server + optimised prod build |
| TW17 | esbuild | Go-based, 10–100× faster transpile |
| TW18 | SWC | Rust transpiler powering Next.js |
| TW19 | Bundler vs no-bundle | No-bundle dev, bundle for prod |
| TW20 | Monorepos | Nx/Turborepo: caching + affected-only builds |
| TW21 | Package managers | pnpm: fast, disk-efficient, strict |
| TW22 | ESLint flat config | New config + type-aware typescript-eslint |
| TW23 | Prettier/Biome | Auto-format; Biome merges lint+format (Rust) |
| TW24 | Vitest | Fast Vite-native, Jest-compatible testing |
| TW25 | Type-only imports | `import type` erased; cleaner bundles |
| TW26 | Runtimes | Node LTS default; watch Deno/Bun |
| TW27 | Type-stripping | Node runs .ts by erasing types (no check) |
| TW28 | JS→TS migration | allowJs, rename gradually, tighten strict |
| TW29 | When to adopt | More safety or real speed, then standardise |
| TW30 | My approach | Strict types, fast tools, ESM everywhere |

---

[← Angular What's New](70-concept-angular-whats-new.md) · [Home](README.md) · [Next → Back to Home](README.md)
