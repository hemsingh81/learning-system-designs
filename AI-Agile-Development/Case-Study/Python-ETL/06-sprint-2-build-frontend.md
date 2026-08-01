# Sprint 2 — Dzmitry Builds the Exception Queue

← [Previous](05-sprint-2-build-backend.md) · [Case study index](README.md) · Next: [Sprint 3 — Verify](07-sprint-3-verify.md)

> **One line:** the screen where a human fixes what the machine got wrong, built by someone who spent a morning watching the human do it the old way first.

---

## 1. Monday, 6 July — Dzmitry sits behind Preeti for three hours

Sprint 2 is the build sprint. Ravi has the pipeline, which you watched him build in [the previous chapter](05-sprint-2-build-backend.md). Dzmitry has story **NWD-108 — Exception queue screen for analyst review**, and a [UI brief](artifacts/ui-brief-exception-queue.md) that Preetinka and Dzmitry wrote together in Sprint 1 using [P14](../../AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md).

Before writing a line of it, Dzmitry asks for three hours on a video call with Preeti Singh, the operations analyst at Northwind who currently does this job by hand, and just watches.

Here is what that looks like, because it is the entire design input for this chapter.

Preeti has two monitors. On the left, Adobe Acrobat, full screen, a Broker Alpha daily position statement. On the right, Excel. Between them, a paper notepad with a pencil line drawn down the middle — the left column is the row she is on, the right column is anything that looked odd and she will come back to.

She reads a position off the PDF. She clicks into Excel. She types it. She clicks back to the PDF. Acrobat has kept her scroll position, which is the only reason this is survivable. She reads the next one.

At 9:12am she gets an email, deals with it, and comes back to the PDF. Acrobat has kept her place. She finds her row again by looking at the pencil mark on the notepad.

**The number Dzmitry writes down and underlines twice: Preeti does this about forty times in a morning.**

Not forty fields. Forty documents. Forty times through the whole cycle of open, orient, find the problem, fix it, confirm, move on.

That number is the design.

---

## 2. The arithmetic of a click

Here is the framing Dzmitry brings back to the team, and it is worth stealing whole.

**In a screen used once, a click costs a click. In a screen used forty times before lunch, a click costs forty clicks.**

That sounds obvious written down. It is not obvious when you are building the thing, because you build each interaction once and you test it once, and one click feels like nothing.

Dzmitry makes a table for the standup. Left column, a design decision that seems harmless. Right column, what it actually costs Preeti per morning.

| A decision that seems small | What it costs across forty documents |
|---|---|
| "Confirm" button needs a mouse click | 40 mouse trips from keyboard to trackpad and back |
| Field list scrolls independently of the PDF | 40 × ~6 manual re-scrolls to line the two up |
| PDF viewer resets to page 1 when you edit a field | 40 × finding your place again |
| Queue returns to the top of the list after you resolve one | 40 × scrolling back down to where you were |
| A modal confirms "are you sure?" on save | 40 extra keystrokes and 40 breaks in flow |
| Confidence shown as a raw number instead of a percentage | 40 × a small pause while you translate it in your head |

That last row is in the table on 6 July. Hold on to it.

Atul looks at the table and asks his usual question — *what happens if that takes twice as long* — and Dzmitry gives the answer that gets the extra two days approved: **"If the screen is bad, Preeti does the same job she does today with more steps, and we've spent £180,000 making her morning worse."**

Preetinka, who spent six years on an operations floor, does not need convincing.

---

## 3. What the screen actually has to do

Before the code, the plain-language version. If you have not read the earlier chapters, this is the whole context you need.

**Where the exceptions come from.** Ravi's pipeline reads a counterparty PDF, sends it to Azure AI Document Intelligence — a service you hand a PDF and get back structured fields rather than a wall of text — and each field comes back with a **confidence score**, a number from 0 to 1 saying how sure the model was. The rules engine compares each score against a threshold and applies a set of other checks. If anything fails, the whole document is refused and written to a table called `etl.extraction_exception` with the reason attached.

**Why the whole document and not just the bad field.** Because half a statement in the warehouse produces a reconciliation break that looks exactly like a real settlement failure, and nobody downstream can tell the difference. That is [ADR-0003](artifacts/adr/), and it is the decision Ravi argued against and later stopped arguing against.

**What the screen is.** A queue of refused documents. Preeti opens one, sees the original PDF on the left and the extracted fields on the right, with the specific failing fields marked and the reason spelled out. She corrects them and confirms. The corrected document goes back into the pipeline at the transform step, and her corrections are kept as training data for the next version of the model.

**What "refused" carries with it.** Every row in that table has: the content hash of the document, a path to the original PDF in blob storage, a path to the raw Azure response in the bronze layer, the counterparty key, a short reason string, and a JSON array of structured violations. Ravi's `write_exception` in `sinks/sql_sink.py` writes exactly that, and Dzmitry reads exactly that. Nothing is re-derived on the UI side.

That last sentence is the handoff working. The backend does not send `"validation failed"` and let the frontend guess. It sends this, per violation:

```json
{
  "rule_id": "value_consistency",
  "rule_type": "cross_field_product",
  "severity": "error",
  "message": "quantity 1250 x price 48.20 = 60250.00, but market_value says 62050.00",
  "field": "market_value",
  "row": 7,
  "observed": "62050.00",
  "expected": "60250.00"
}
```

Preeti can fix that in one pass because it tells her the row, the field, what is there, and what the arithmetic says should be there. **A boolean would have told her nothing and cost her a morning.**

---

## 4. Running P19 — build the UI from the brief

Dzmitry's app lives in its own repository, `northwind-exception-queue`, separate from `doc_ingestion`. Different deploy cadence, different pipeline, no shared build. React 19 with TypeScript, Vite for the build, Vitest for tests.

Quick definitions, because the style of this book is that you should not have to open a search engine:

| Term | Plainly |
|---|---|
| **React** | A JavaScript library for building screens out of reusable pieces called components. |
| **TypeScript** | JavaScript with types. You declare the shape of your data and the compiler complains before your users do. |
| **Component** | One reusable piece of screen. `<ConfidenceBadge value={0.82} />` is a component being used. |
| **Hook** | A reusable piece of *behaviour* rather than screen — fetching data, tracking keyboard state. By convention the name starts with `use`. |
| **Vite** | The build tool. Turns your TypeScript into something a browser runs, fast. |
| **Vitest** | The test runner. Same idea as `pytest` on the Python side. |
| **PDF.js** | Mozilla's library for rendering a PDF inside a web page, so you are not embedding a plugin or a viewer you do not control. |
| **SAS URL** | Shared Access Signature. A time-limited link to one blob in Azure Storage. It lets the browser fetch the PDF directly without the app holding a storage key. |

Here is [P19](../../AI-Prompts-Library/phase-4-build/P19-build-the-ui-from-the-brief.md) as Dzmitry actually fills it in. Note how much of it is constraints rather than description.

```text
You are a senior React 19 / TypeScript 5 engineer building one screen of the
Northwind counterparty exception queue.

## The brief

[FULL TEXT OF artifacts/ui-brief-exception-queue.md]

## The data contract

The API is already built and is not negotiable. Types:

GET  /api/exceptions?status=open&source=&cursor=
     -> { items: ExceptionSummary[]; nextCursor: string | null }
GET  /api/exceptions/{contentHash}
     -> ExceptionDetail
POST /api/exceptions/{contentHash}/resolve
     -> { corrections: Correction[]; note?: string }

The exact TypeScript types are in src/api/types.ts and are generated from the
backend contract. Do not change them. If you need a field that is not there,
say so and stop.

## The user, and the constraint that follows from her

Preeti Singh clears about forty exceptions in a morning. Every interaction in
this screen is multiplied by forty. Therefore:

* Every action in the review screen MUST have a keyboard binding, and the
  keyboard path MUST be the primary one. The mouse is the fallback.
* Focus must never be lost. After any action, focus is somewhere deliberate.
* The PDF viewer must keep its scroll position across field edits and across
  re-renders. Selecting a field scrolls the PDF to that field's page and
  highlights its bounding box.
* Resolving a document advances to the next one in the queue without returning
  to the list.
* No confirmation modal on save. Make the action reversible instead.

## Build this component only

src/features/review/ExceptionReview.tsx and the hooks it needs.
Do not build the queue list screen — that already exists.

## Rules

* Function components and hooks only. No class components.
* Data fetching goes through TanStack Query, already configured in
  src/api/queryClient.ts. Do not add a second data-fetching approach.
* No new dependencies without asking. The PDF viewer is react-pdf, already
  installed.
* Styling is Tailwind utility classes. No CSS-in-JS, no new stylesheet.
* Every interactive element needs an accessible name and a visible focus ring.
* Strict TypeScript. No `any`. No non-null assertions on API data.

## Do not

* Do not invent API fields.
* Do not add a feature the brief does not ask for, including anything you
  consider an obvious improvement. List those at the end instead.
* Do not write tests in this pass — those come from P20 separately.

## You are done when

* The component compiles under `tsc --noEmit` with no errors.
* Every keyboard binding in the brief's table is implemented and listed back
  to me with the key and what it does.
* You have told me every place you were unsure what the brief meant.
```

### Every placeholder, explained

| Placeholder | What Dzmitry put in it | What goes wrong if you skip it |
|---|---|---|
| The full brief text | All of `ui-brief-exception-queue.md`, pasted, not summarised | Summarising is where your own taste leaks in. The brief's phrase "no confirmation modal on save" would not have survived a summary, and it is the single most contested decision in the screen |
| The data contract | The literal endpoint shapes plus a pointer to the generated types | Without it the AI invents a plausible API and you get a beautiful screen bound to fields that do not exist |
| The user and the multiplier | "Forty in a morning, therefore every interaction ×40" | This is the line that produces keyboard-first output instead of a nice-looking form. Remove it and you get a nice-looking form |
| Build this component only | One file plus its hooks | Otherwise you get the queue list rebuilt too, differently from the one already in the repo |
| The rules block | Framework, data layer, styling, strictness | Each missing rule is a second way of doing something in your codebase, forever |
| The do-not block | No invented fields, no bonus features, no tests yet | Bonus features are the most expensive thing an AI gives you for free, because you have to review them |

The one that matters most is the third. **"Preeti clears forty in a morning" is doing more work than the entire rules section**, because it is the only line that tells the model what kind of screen this is.

---

## 5. What came back, and what Dzmitry kept

The first pass is about four hundred lines across five files. Dzmitry keeps roughly two thirds of it, rewrites the keyboard layer entirely, and throws away a "helpful" auto-save that the brief did not ask for.

Here is the core of what shipped.

### The types, which are not negotiable

```typescript
// src/api/types.ts — generated from the backend contract, do not hand-edit.

export type Severity = "error" | "warning";

export interface Failure {
  ruleId: string;
  ruleType: string;
  severity: Severity;
  message: string;
  field: string | null;
  row: number | null;
  observed: unknown;
  expected: unknown;
}

export interface ExtractedFieldView {
  name: string;
  value: string | number | null;
  confidence: number | null;
  fieldType: "string" | "number" | "currency" | "date" | "integer";
  pageNumber: number | null;
  /** Normalised 0-1 box on the page, from the bronze payload. */
  boundingBox: { x: number; y: number; w: number; h: number } | null;
}

export interface ExceptionDetail {
  contentHash: string;
  sourceKey: string;
  sourceDisplayName: string;
  statementDate: string | null;
  reason: string;
  /** Read-only SAS URL for the original PDF. Short-lived. */
  reviewUrl: string;
  header: ExtractedFieldView[];
  lineItems: ExtractedFieldView[][];
  failures: Failure[];
}
```

Two things to notice.

`observed` and `expected` are `unknown`, not `any`. `unknown` in TypeScript means "there is a value here and you must check what it is before using it". `any` means "stop checking". The difference is that `unknown` makes the compiler force you to handle the case where the backend sends a number and you assumed a string — which is exactly what happens with `observed`, because a `cross_field_product` violation reports a decimal and a `required_fields` violation reports `null`.

`boundingBox` comes from the bronze payload. **Bronze is the layer where the full raw Azure response is stored before anything parses it**, and Hem insisted on it in Sprint 1 for a cost reason — reprocessing a parsing bug should be free rather than costing $30 per thousand pages again. It turns out to also be the reason Dzmitry can draw a box around the exact field on the exact page. Design decisions pay off in places you did not plan.

### The keyboard layer

This is the piece Dzmitry rewrote from scratch, because the first pass bound keys with a global `window.addEventListener` and it fired while Preeti was typing into a text input.

```typescript
// src/features/review/useReviewKeys.ts

import { useEffect } from "react";

export interface ReviewKeyHandlers {
  nextField: () => void;
  prevField: () => void;
  nextFailure: () => void;
  acceptField: () => void;
  resolveAndAdvance: () => void;
  undo: () => void;
}

/** True when the event came from somewhere the user is genuinely typing. */
function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

export function useReviewKeys(handlers: ReviewKeyHandlers, enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;

    function onKeyDown(event: KeyboardEvent) {
      // Ctrl+Enter and Escape work everywhere, including mid-edit.
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        handlers.resolveAndAdvance();
        return;
      }
      if (event.key === "Escape") {
        (event.target as HTMLElement | null)?.blur();
        return;
      }

      // Everything else stands down while the user is typing a value.
      if (isTypingTarget(event.target)) return;

      switch (event.key) {
        case "j":
        case "ArrowDown":
          event.preventDefault();
          handlers.nextField();
          break;
        case "k":
        case "ArrowUp":
          event.preventDefault();
          handlers.prevField();
          break;
        case "n":
          event.preventDefault();
          handlers.nextFailure();
          break;
        case "a":
          event.preventDefault();
          handlers.acceptField();
          break;
        case "u":
          event.preventDefault();
          handlers.undo();
          break;
        default:
          break;
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [handlers, enabled]);
}
```

The `isTypingTarget` guard is eleven lines and it is the whole difference between a keyboard-first screen and an unusable one. Without it, Preeti types `n` into a security name and the app jumps to the next failure.

The `Escape` handler blurs the current input rather than closing anything. That is deliberate: Preeti's hands stay on the keys, she escapes out of the field she is editing, and `j`/`k` start working again immediately. No mouse.

**The binding list, which Dzmitry made the AI report back explicitly, because a keyboard scheme that lives only in a switch statement is one nobody can review:**

| Key | Does |
|---|---|
| `j` / `↓` | Next field |
| `k` / `↑` | Previous field |
| `n` | Jump to the next field that failed a rule |
| `a` | Accept the extracted value as-is |
| `u` | Undo the last change |
| `Enter` | Start editing the selected field |
| `Esc` | Stop editing, keep the value |
| `Ctrl` + `Enter` | Resolve this document and advance to the next |

### Locking the PDF to the field list

This is the piece Preeti notices, and the piece nobody would have specified without watching her work.

```typescript
// src/features/review/PdfPane.tsx

import { useEffect, useRef } from "react";
import { Document, Page } from "react-pdf";
import type { ExtractedFieldView } from "../../api/types";

interface Props {
  url: string;
  pageCount: number;
  selected: ExtractedFieldView | null;
}

export function PdfPane({ url, pageCount, selected }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Scroll to the selected field's page — and only when the PAGE changes.
  // Selecting another field on the page you are already looking at must not
  // move the document under Preeti's eyes.
  const targetPage = selected?.pageNumber ?? null;
  const lastPage = useRef<number | null>(null);

  useEffect(() => {
    if (targetPage === null || targetPage === lastPage.current) return;
    lastPage.current = targetPage;
    pageRefs.current.get(targetPage)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [targetPage]);

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto bg-slate-100">
      <Document file={url} loading={<PdfSkeleton />}>
        {Array.from({ length: pageCount }, (_, i) => i + 1).map((page) => (
          <div
            key={page}
            ref={(el) => {
              if (el) pageRefs.current.set(page, el);
              else pageRefs.current.delete(page);
            }}
            className="relative mx-auto my-4 w-fit shadow"
          >
            <Page pageNumber={page} width={720} renderTextLayer={false} />
            {selected?.pageNumber === page && selected.boundingBox && (
              <Highlight box={selected.boundingBox} />
            )}
          </div>
        ))}
      </Document>
    </div>
  );
}
```

The comment above `lastPage` is the design decision. The obvious implementation scrolls whenever the selection changes. That is wrong, and you only find out it is wrong by watching someone use it: Preeti moves down a field, the page jumps two pixels to re-centre, and her eye loses the row. **Scrolling only on a page change is one extra `useRef` and it is the difference between a viewer that helps and a viewer that fights you.**

`renderTextLayer={false}` is there for a duller reason. PDF.js draws an invisible layer of selectable text over the rendered page, and on a scanned Broker Alpha statement that layer is both useless and slow. Turning it off took the render of a three-page statement from about 900ms to about 300ms.

### The review screen itself

```typescript
// src/features/review/ExceptionReview.tsx  (abridged)

export function ExceptionReview({ contentHash, onAdvance }: Props) {
  const { data, isPending, error } = useExceptionDetail(contentHash);
  const resolve = useResolveException(contentHash);

  const [edits, dispatch] = useReducer(editsReducer, EMPTY_EDITS);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const fields = useMemo(() => (data ? flattenFields(data) : []), [data]);
  const failuresByField = useMemo(() => indexFailures(data?.failures ?? []), [data]);
  const selected = fields[selectedIndex] ?? null;

  const handlers = useMemo<ReviewKeyHandlers>(
    () => ({
      nextField: () => setSelectedIndex((i) => Math.min(i + 1, fields.length - 1)),
      prevField: () => setSelectedIndex((i) => Math.max(i - 1, 0)),
      nextFailure: () => setSelectedIndex((i) => nextFailingIndex(fields, failuresByField, i)),
      acceptField: () => selected && dispatch({ type: "accept", field: selected }),
      undo: () => dispatch({ type: "undo" }),
      resolveAndAdvance: () => {
        resolve.mutate(
          { corrections: toCorrections(edits) },
          { onSuccess: onAdvance },
        );
      },
    }),
    [fields, failuresByField, selected, edits, resolve, onAdvance],
  );

  useReviewKeys(handlers, !isPending && !error);

  if (isPending) return <ReviewSkeleton />;
  if (error) return <ReviewError error={error} onRetry={...} />;

  return (
    <div className="grid h-full grid-cols-2 gap-0">
      <PdfPane url={data.reviewUrl} pageCount={data.pageCount} selected={selected} />
      <FieldPane
        fields={fields}
        edits={edits}
        failures={failuresByField}
        selectedIndex={selectedIndex}
        onSelect={setSelectedIndex}
        onChange={(field, value) => dispatch({ type: "edit", field, value })}
      />
    </div>
  );
}
```

Two things here that are worth copying regardless of what you are building.

**The edits are a reducer, not a pile of `useState` calls.** A reducer is a single function that takes the current state and an action and returns the new state. That is what makes `u` for undo a five-line addition instead of a rewrite — undo is just "pop the last action off and replay". With scattered `useState` you would be reconstructing history from nothing.

**There is no confirmation modal.** The brief forbids one, and the reason is the ×40 arithmetic: a modal is one extra keystroke and one broken train of thought, forty times. What replaces it is that `Ctrl+Enter` is *reversible* — resolving a document moves it to a `resolved` state that Preeti can reopen from the queue for the rest of the day. **Reversibility is almost always cheaper than confirmation, and it is always kinder.**

---

## 6. What Dzmitry refused to build

Preetinka asks for a bulk-accept: select twelve documents in the queue, accept them all.

Dzmitry says no, and the reasoning is worth recording because it is a product argument made by an engineer and it holds.

> "Bulk accept means accepting things you haven't looked at. The whole system is built on the idea that a wrong number is worse than no number. If I give her a button that accepts twelve documents in one keystroke, on a bad Friday she will use it, and then we have a control that can be switched off by someone under time pressure."

Preetinka pushes once, then agrees, and it goes on the backlog as a `won't do` with the reason written down, which is more useful than deleting it. **A refused feature with a recorded reason does not come back every sprint.**

She does get one thing: a filter on the queue by counterparty and by reason, so Preeti can do all fourteen `low_confidence: quantity` documents in a row while her eye is already tuned for it. That one is genuinely a nice-to-have that turned out not to be.

---

## 7. Running P20 — the tests, written alongside

[P20](../../AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) is the same prompt Ravi runs on the Python side, pointed at a different stack. The rule Gautam put in the [Definition of Done](artifacts/definition-of-done.md) applies to both: **the tests are written in a separate pass from the code, and the AI is never allowed to edit a test to make it pass.**

The separate pass matters more than it sounds. If you ask for code and tests in one go, you get tests that assert what the code does, which is a tautology dressed as a safety net.

Here is what the keyboard tests look like, using Vitest and Testing Library — a library whose whole philosophy is that you test what a user can see and do, not what the component's internals are.

```typescript
// src/features/review/__tests__/keyboard.test.tsx

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ExceptionReview } from "../ExceptionReview";
import { renderWithQuery, mockDetail } from "../../../test/harness";

describe("ExceptionReview keyboard navigation", () => {
  it("moves the selection down the field list with j", async () => {
    const user = userEvent.setup();
    renderWithQuery(<ExceptionReview contentHash="abc" onAdvance={vi.fn()} />, {
      detail: mockDetail({ headerFields: ["account_number", "statement_date"] }),
    });

    expect(await screen.findByRole("option", { selected: true })).toHaveAccessibleName(
      /account number/i,
    );

    await user.keyboard("j");

    expect(screen.getByRole("option", { selected: true })).toHaveAccessibleName(
      /statement date/i,
    );
  });

  it("does not treat typing in a field as a navigation key", async () => {
    const user = userEvent.setup();
    renderWithQuery(<ExceptionReview contentHash="abc" onAdvance={vi.fn()} />, {
      detail: mockDetail({ headerFields: ["security_name"] }),
    });

    await user.keyboard("{Enter}");                 // start editing
    await user.keyboard("JOHNSON & JOHNSON");       // contains j, n, a, u

    expect(screen.getByRole("textbox")).toHaveValue("JOHNSON & JOHNSON");
    expect(screen.getByRole("option", { selected: true })).toHaveAccessibleName(
      /security name/i,
    );
  });

  it("resolves and advances on ctrl+enter without a confirmation step", async () => {
    const user = userEvent.setup();
    const onAdvance = vi.fn();
    renderWithQuery(<ExceptionReview contentHash="abc" onAdvance={onAdvance} />, {
      detail: mockDetail({}),
    });

    await user.keyboard("{Control>}{Enter}{/Control}");

    expect(await screen.findByRole("status")).toHaveTextContent(/resolved/i);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(onAdvance).toHaveBeenCalledOnce();
  });
});
```

The second test is the one that earns its place. `JOHNSON & JOHNSON` contains `j`, `n`, `a` and `u` — four of the six single-key bindings. It is the exact string Dzmitry used by hand to find the bug in the AI's first keyboard implementation, and turning that manual check into a test took ninety seconds.

**When you find a bug by hand, the test that catches it is already written in your head. Write it down before the feeling fades.**

---

## 8. The bug that is not a crisis

Thursday 16 July. The screen works. Gautam reviews it with [P23](../../AI-Prompts-Library/phase-5-verify/P23-review-someone-elses-code.md), leaves two comments about the reducer's action types, both fair, both fixed in ten minutes. NWD-108 goes to Done.

Then Sprint 3 starts and Pankaj opens it with a real document in front of her, and files this:

```text
ID: NWD-139
Title: Exception queue shows raw confidence value, not a percentage
Severity: Cosmetic
Found by: Pankaj 
Found in: Sprint 3 acceptance testing, build 1.0.0-rc2

STEPS TO REPRODUCE
1. Open any exception with a low-confidence failure.
2. Look at the confidence chip next to the field name.

EXPECTED
82%

ACTUAL
0.8234567

NOTES
- Every field shows this, not just failing ones.
- Column width jumps around as values change length, so the list shifts
  slightly when you move between fields.
```

Here is the line responsible:

```typescript
// src/features/review/ConfidenceBadge.tsx
export function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null) return <span className="chip chip-unknown">no score</span>;
  return <span className={chipClass(value)}>{value}</span>;
  //                                          ^^^^^^^ NWD-139
}
```

That is the whole bug. `{value}` where `{formatConfidence(value)}` should be.

**This bug is in this book on purpose, and the reason is that not everything is a crisis.**

Most of what QA finds is this. A wrong label. A number in the wrong format. A column that jumps. The rework loop you are about to watch in [chapter 8](08-sprint-3-rework.md) is real and it is where the sprint went, but if you come away believing every defect requires a reproduction fixture, a root-cause trace and a specification change, you will have learned the wrong lesson and you will make your team miserable.

**Match the process to the defect.** NWD-139 does not need [P27](../../AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md). It does not need a stop gate. Dzmitry reads it, sees the line, and fixes it:

```diff
--- a/src/features/review/ConfidenceBadge.tsx
+++ b/src/features/review/ConfidenceBadge.tsx
@@ -1,7 +1,20 @@
+/**
+ * Confidence as Preeti reads it, not as the model emits it.
+ *
+ * Rounded to a whole percent and rendered in tabular figures so the chip does
+ * not change width between 9% and 82%. NWD-139.
+ */
+export function formatConfidence(value: number): string {
+  return `${Math.round(value * 100)}%`;
+}
+
 export function ConfidenceBadge({ value }: { value: number | null }) {
   if (value === null) return <span className="chip chip-unknown">no score</span>;
-  return <span className={chipClass(value)}>{value}</span>;
+  return (
+    <span className={`${chipClass(value)} tabular-nums`} title={value.toFixed(4)}>
+      {formatConfidence(value)}
+    </span>
+  );
 }
```

And a two-line test, because a bug that reached QA gets a test even when it is one line:

```typescript
it.each([
  [0.8234567, "82%"],
  [0.9, "90%"],
  [0.005, "1%"],
  [1, "100%"],
])("renders %s as %s", (input, expected) => {
  render(<ConfidenceBadge value={input} />);
  expect(screen.getByText(expected)).toBeInTheDocument();
});
```

Twenty minutes end to end, including the test. No prompt was needed at all.

### How it got in

Worth two sentences, because the answer is not "Dzmitry was careless."

The brief said *"show the field's confidence."* It did not say in what unit. The AI rendered the value it was given, which is exactly what it was asked to do. Gautam's review looked at the reducer, the data flow and the keyboard layer — the things where a mistake is expensive — and did not look hard at a badge. Dzmitry had been staring at raw confidence values in JSON for a fortnight and had stopped seeing them as anything but normal.

The `title={value.toFixed(4)}` in the fix is Dzmitry hedging honestly: Preeti sees `82%`, and if she ever needs the real number she can hover. The rounded value is for reading; the precise one is for arguing.

**Three people looked at this screen and none of them saw it, because none of them were the person who has to read it forty times before lunch.** That is not a failure of care. It is what fresh eyes are for, and it is why Pankaj's chapter is next.

---

## 9. What Dzmitry hands over

By Friday 17 July, NWD-108 is done in the sense the [Definition of Done](artifacts/definition-of-done.md) means it: reviewed, tested, deployed to the dev environment, and demonstrated to Preetinka and Preeti on a call.

What crosses the handoff into Sprint 3:

| Artifact | Where | For whom |
|---|---|---|
| The review screen | `northwind-exception-queue`, deployed to dev | Pankaj, to test against real refused documents |
| The keyboard binding table | In the README and in the screen's own `?` overlay | Preeti, and Pankaj's E2E scripts |
| The API contract types | `src/api/types.ts`, generated from the backend | Ravi, who now cannot change a field name without breaking a build |
| Two open questions | On NWD-108 as comments | Preetinka |

The two open questions, written down rather than resolved by guessing:

1. When Preeti corrects a field, do her corrections need to be visible to a second reviewer before the document reloads? Northwind's audit team may want four-eyes on any manual override. Nobody has asked them.
2. What happens if the same document is open in two browser tabs? Right now, last write wins, silently.

Neither is a defect. Both are things nobody decided, and writing them on the story is what stops them becoming a defect in November.

Preeti's reaction on the demo call, which Atul writes down verbatim and reads out in the retro three weeks later:

> "So I don't have to type the good ones any more. I only look at the ones that are actually hard."

That is the whole project in one sentence from the only person whose opinion is a fact.

Now Pankaj gets hold of it.

---

← [Previous](05-sprint-2-build-backend.md) · [Case study index](README.md) · Next: [Sprint 3 — Verify](07-sprint-3-verify.md)
