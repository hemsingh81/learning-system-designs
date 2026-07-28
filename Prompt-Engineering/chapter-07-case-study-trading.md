--- filename: chapter-07-case-study-trading.md ---

# Chapter 7 — Case Study: Trading Platform Prototype, Start to End

← [Chapter 6 — Case Study: E-commerce](./chapter-06-case-study-ecommerce.md) · [Learning path](./learning-path.md) · Next: [Chapter 8 — Case Study: Dating](./chapter-08-case-study-dating.md)

## Narrative

Asha's next project is a trading platform prototype. It is a **paper-trading sandbox** — users design simple rule-based strategies and test them against historical data. No real money moves.

The stakes feel different straight away.

In the e-commerce project, a bad prompt output cost someone a rewrite. Here, a bad prompt output could cost someone real money. Or it could produce compliance language that gets the company in legal trouble.

She finds out how easily on day two.

An early draft of her strategy-ideation prompt cheerfully proposes a strategy called **"guaranteed weekly gains."** She catches it in review. But that phrase alone, if it had reached user-facing copy, would have been a regulatory problem — not an embarrassment, a *problem*.

The lesson is not "review more carefully." It is this: **in this domain, review before shipping is not enough.** The prompts themselves have to refuse to produce that kind of output in the first place.

So every prompt in this project gets an explicit guardrail section. Not as paperwork. Because she has seen what happens without one.

This case study is where prompt engineering stops being about speed and starts being about **containment** — making sure the model's fluency does not outrun what is actually true, tested, or legally sayable.

---

## Domain constraints

Four rules that shape every prompt in this chapter.

**1. Paper trading only.** No prompt may generate code that connects to a real brokerage. This is enforced in the codebase itself, not just by asking nicely in a prompt — but every prompt repeats it anyway. Two layers, in case one fails.

**2. Nothing here is investment advice.** Every user-facing output about performance carries a disclaimer. No prompt may state or imply guaranteed, predictable, or risk-free returns.

**3. Backtests must be reproducible.** Run the same strategy against the same data, get the same result. Every time.

A backtest you cannot reproduce is worse than useless. It is *dangerous* — because a user might act on a number that would come out differently if you ran it again.

**4. Data is historical, never live.** This removes a whole category of risk: no model suggestion can accidentally influence a real trade, because there is no path from here to a live market.

---

## Risk controls

This project uses a **fail-closed** approach. It is the same idea as the risk-check gate in the companion [MicroServices trading case study](../MicroServices/case-studies/04-trading-app/README.md).

**What fail-closed means:** when the system cannot verify something is safe, it blocks. It does not ship it with a warning attached.

The opposite — fail-open — is what the e-commerce store does: keep selling even when the stock service is down, and apologise for the rare oversell. That is correct for a shop. It would be indefensible here.

| Control | What it does |
|---|---|
| Compliance language gate | Every user-facing string is checked against a banned-phrase list before merge (Prompt #12) |
| Backtest sanity gate | A backtest must pass the red-flag check (Prompt #8) before it can be shown as a "result" instead of a "draft" |
| No-execution boundary | Strategy code prompts output signals only — buy/sell/hold — never order-placement code |
| Human sign-off on release | Any release touching user-facing strategy or performance copy needs a named compliance reviewer to sign off, and it is logged (Prompt #15/#16) |

---

## Data feeds

Historical daily OHLCV data — open, high, low, close, volume — for about 50 liquid instruments.

The dataset is **static and versioned**. Not a live feed. That is what makes constraint #3 (reproducibility) achievable at all: if the data can change under you, the same backtest can produce two different answers and neither is wrong.

## Prompt catalog (20 prompts)

| # | Category | Prompt | Purpose |
|---|---|---|---|
| 1 | Ideation | Strategy candidate generator | Propose rule-based strategy ideas from constraints |
| 2 | Ideation | Strategy risk statement writer | Force an explicit risk statement per idea |
| 3 | Ideation | Strategy diversity checker | Avoid proposing near-duplicate strategies |
| 4 | Code gen | Signal logic generator | Turn a strategy's rules into signal-generation code |
| 5 | Code gen | Signal logic reviewer | Check generated code matches the stated rules exactly |
| 6 | Code gen | Parameter sensitivity documenter | Document which parameters the strategy is sensitive to |
| 7 | Backtest | Backtest runner spec | Define the exact backtest configuration |
| 8 | Backtest | Backtest red-flag checker | Flag overfitting/lookahead-bias signs |
| 9 | Backtest | Backtest result summarizer | Plain-English summary of backtest metrics |
| 10 | Backtest | Drawdown explainer | Explain the worst drawdown period in context |
| 11 | Risk | Risk alert copy generator | User-facing alert when a strategy breaches a risk threshold |
| 12 | Compliance | Compliance language checker | Flag guaranteed-return / misleading language |
| 13 | Compliance | Disclaimer completeness checker | Confirm required disclaimers are present |
| 14 | Compliance | Regulatory terminology reviewer | Flag terms that imply licensed-advisor status |
| 15 | Release | Release checklist generator | Full pre-release checklist for a strategy-affecting change |
| 16 | Release | Compliance sign-off request | Draft the sign-off request to the compliance reviewer |
| 17 | Testing | Backtest regression test generator | Ensure a known backtest result doesn't silently drift |
| 18 | Testing | Edge-case data generator | Generate adversarial market data (flash crash, zero volume) |
| 19 | Docs | Strategy documentation generator | User-facing explanation of how a strategy works |
| 20 | Docs | Glossary term definer | Plain-English definitions for trading jargon in the UI |

## Prompt orchestration plan

Five waves. Two of them are **blocking gates** — the flow stops there until something passes.

That is the main structural difference from the e-commerce chapter. There, waves overlapped and work continued in parallel. Here, Wave 3 and Wave 4 are hard stops. A strategy with unresolved red flags does not reach a user, even in a paper-trading sandbox.

```
Wave 1 — Ideation (per new strategy request)
  #1 Strategy candidate generator
    → #3 Strategy diversity checker (against existing catalog of strategies)
    → #2 Strategy risk statement writer (per surviving candidate)

Wave 2 — Implementation
  #4 Signal logic generator (input: chosen strategy's rules)
    → #5 Signal logic reviewer (input: #4's code + original rules — must match exactly)
    → #6 Parameter sensitivity documenter

Wave 3 — Validation (never skipped, never shortcut)
  #7 Backtest runner spec
    → run actual backtest (not a prompt — real code, real data)
    → #8 Backtest red-flag checker (input: real backtest output)
    → IF red flags found: back to Wave 2, do not proceed
    → IF clean: #9 Backtest result summarizer, #10 Drawdown explainer

Wave 4 — Compliance gate (blocking, cannot be skipped)
  #12 Compliance language checker (input: all Wave 3 user-facing text)
  #13 Disclaimer completeness checker
  #14 Regulatory terminology reviewer
    → any FAIL blocks progress to Wave 5, routes back to copy authors

Wave 5 — Release
  #15 Release checklist generator
    → #16 Compliance sign-off request (sent to a NAMED human, logged)
    → human sign-off received → release proceeds
  #17, #18 run in CI on every change to strategy/backtest code, ongoing
```

## Prompt examples (20 in full)

### 1. Strategy candidate generator
**Purpose:** Propose rule-based strategy ideas within stated constraints.
```
Propose [N] rule-based trading strategy candidates for a paper-trading
sandbox, using only these signal types: [moving average crossover, RSI
threshold, volume spike — list allowed types]. For each: entry rule,
exit rule, and the market condition it's designed for (trending,
mean-reverting, high-volatility). Do NOT claim or imply expected
performance — that comes only from an actual backtest, never from
ideation.
```
**Expected output:** N strategy candidates, each with explicit entry/exit rules and a named market regime, zero performance claims.
**Safety/guardrails:** The "do NOT claim expected performance" constraint is non-negotiable — reject any output that includes phrases like "should generate consistent returns" even at the ideation stage.

### 2. Strategy risk statement writer
**Purpose:** Forces an explicit, specific risk statement before any strategy proceeds further.
```
For this strategy: [paste entry/exit rules], write a risk statement
covering: what market condition would make this strategy lose money,
what's the theoretical maximum consecutive-loss scenario given the
rules, and what this strategy does NOT protect against. Be specific to
these exact rules, not generic trading disclaimers.
```
**Expected output:** Three concrete points tied to the specific strategy logic, not boilerplate.
**Safety/guardrails:** Reject generic output ("markets can go down") — if the model can't be specific to the actual rules given, that's a signal the strategy itself is underspecified.

### 3. Strategy diversity checker
**Purpose:** Prevents the catalog filling up with near-duplicate strategies that only look different.

```
Here is our existing strategy catalog: [paste list of strategies with
their entry/exit rules]. Here is a newly proposed strategy: [paste new
strategy rules].

Assess: is this meaningfully different from anything in the catalog, or
is it a near-duplicate with cosmetic changes (e.g., a 20-day moving
average instead of a 21-day)? Compare on: signal type used, market
regime targeted, and whether the entry/exit conditions would fire on
substantially the same days.

Verdict: DISTINCT or NEAR-DUPLICATE of [which existing strategy], with
one sentence of reasoning.
```

**Variants:**
- *Strict mode:* add "treat any strategy using the same signal type and same market regime as NEAR-DUPLICATE unless the entry logic differs structurally, not just numerically."
- *Portfolio mode:* add "also assess whether this strategy's returns would likely correlate with existing ones — diversity of logic matters less than diversity of behavior."

**Expected output format:** Markdown — one verdict line (`DISTINCT` / `NEAR-DUPLICATE of [name]`) plus a reasoning sentence and a comparison table across the three named dimensions.

**Example input:** Catalog contains "MA-Cross-20-50 (trending)". New proposal: "MA-Cross-21-55 (trending)".

**Example output:**
```
Verdict: NEAR-DUPLICATE of MA-Cross-20-50
Reasoning: Same signal type (MA crossover), same regime (trending), and
parameter shift is within noise — these would fire on substantially the
same days.
```

**Safety/guardrails:** A `DISTINCT` verdict is not approval to proceed — it only means the idea isn't redundant. The strategy still passes through #2 (risk statement) and Wave 3 backtesting unchanged.

**Test case:** Given two MA-crossover strategies differing only by a 1-day parameter, returns `NEAR-DUPLICATE`.

**Catalog metadata:** `id: trading-strategy-diversity-v1` · `version: 1.0.0` · `tags: [trading, ideation, comparison]` · `author: asha.k`

---

### 4. Signal logic generator
**Purpose:** Turn stated strategy rules into actual signal-generation code.
```
Implement this strategy's signal logic in [language]: [paste entry/exit
rules]. Output ONLY a function that takes historical OHLCV data and
returns buy/sell/hold signals — no order execution, no broker API calls,
no position sizing. Include inline comments mapping each code block to
the specific rule it implements.
```
**Expected output:** A pure function, signals only, with traceable comments back to the stated rules.
**Safety/guardrails:** "No order execution, no broker API calls" is the no-execution boundary from the risk controls table — this must be true of every strategy-code-generating prompt in the system, with no exceptions.

### 5. Signal logic reviewer
**Purpose:** Independently verifies generated code matches the stated rules exactly — catches silent logic drift.
```
Here are a strategy's stated rules: [paste rules]. Here is generated
code claiming to implement them: [paste code]. Trace through the code
line by line and confirm: does it implement exactly these rules, no
more, no less? Flag any discrepancy, including any logic the code
contains that isn't traceable to a stated rule.
```
**Expected output:** A line-by-line trace with an explicit match/mismatch verdict, not just "looks good."
**Safety/guardrails:** Run this with a *different* prompt/session than the one that generated the code — self-review by the same context is weaker than independent review.

### 6. Parameter sensitivity documenter
**Purpose:** Documents which parameters the strategy is fragile to — the earliest available signal of overfitting risk, before a backtest is even run.

```
Here is a strategy's rules and parameters: [paste rules + parameter set,
e.g., "MA fast=20, MA slow=50, stop-loss=2%"].

For each parameter, document: what it controls in plain terms, what
happens behaviourally if it moves ±20%, and whether the strategy's logic
would break down entirely outside a stated range.

Flag any parameter where a small change causes a large behavioural
change — that fragility is a signal this strategy may be overfitted to
one specific market period.

Do NOT estimate performance impact in percentage-return terms — you have
no backtest data. Describe behaviour only.
```

**Variants:**
- *Terse:* "One line per parameter, table format" — for a strategy with 10+ parameters where the full prose version becomes unreadable.
- *Pre-tuning:* add "recommend a sensible range to sweep for each parameter during tuning" when this runs before a parameter-optimisation pass.

**Expected output format:** Markdown table — columns: Parameter, What it controls, Behaviour at ±20%, Fragility flag (yes/no + why).

**Example input:** `MA fast=20, MA slow=50, stop-loss=2%`

**Example output:**
```
| Parameter | Controls | At ±20% | Fragile? |
|---|---|---|---|
| MA fast=20 | Entry responsiveness | 16-24: more/fewer whipsaw entries in choppy markets | No |
| stop-loss=2% | Max loss per trade | 1.6%-2.4%: at 1.6% most trades stop out on normal daily range | YES — 2% is near typical daily volatility for this universe |
```

**Safety/guardrails:** The "describe behaviour, not performance" constraint is load-bearing — the model has no backtest data at this stage, and any percentage-return estimate it produces here would be fabricated. Reject numeric performance claims in this output.

**Test case:** Given a stop-loss parameter set near typical daily volatility, flags it as fragile.

**Catalog metadata:** `id: trading-param-sensitivity-v1` · `version: 1.0.0` · `tags: [trading, code-gen, risk]` · `author: asha.k`

---

### 7. Backtest runner spec
**Purpose:** Defines the exact backtest configuration so results are reproducible.
```
Define a backtest configuration for this strategy: [paste strategy].
Specify: date range, instrument universe, starting capital, transaction
cost assumption, and slippage assumption. State explicitly: this
configuration, run against the same data, must always produce the same
result — flag anything in the strategy logic that would prevent that
(e.g., use of live/current-time data).
```
**Expected output:** A complete, explicit backtest config plus an explicit reproducibility check.
**Safety/guardrails:** The reproducibility check is the load-bearing part — a strategy that references "today's date" or external live state cannot be backtested meaningfully, and this prompt is designed to catch that before wasted effort.

### 8. Backtest red-flag checker
**Purpose:** The single most important prompt in this case study — catches overfitting and lookahead bias before a result is ever shown to a user.
```
Here is a strategy's backtest result: [paste metrics: returns, Sharpe
ratio, max drawdown, win rate, number of trades]. Here is the strategy's
parameter set: [paste parameters]. Flag red flags: is the Sharpe ratio
inconsistent with the max drawdown (a sign of a broken metric or
manipulation)? Is the number of trades too low to be statistically
meaningful? Do the parameters look tuned to this exact date range
(overfitting)? Does anything suggest the strategy could see future data
(lookahead bias)?
```
**Expected output:** An explicit pass/fail per red-flag category, not a vague "looks reasonable."
**Safety/guardrails:** A single flag here should block the strategy from advancing to Wave 4 — this prompt's output is a hard gate, not advisory, per the orchestration plan.

### 9. Backtest result summarizer
**Purpose:** Plain-English summary for a non-technical user, without overstating confidence.
```
Summarize this backtest result for a retail user with no statistics
background: [paste metrics]. Use plain language, avoid jargon (or define
it inline), and explicitly state the limitations of a backtest (past
performance, limited date range, paper-trading only — does not predict
future results). Do not use the words "guarantee," "will," or "always."
```
**Expected output:** A short, accessible summary with an explicit, non-negotiable limitations section and banned words genuinely absent.
**Safety/guardrails:** Run Prompt #12 (compliance checker) against this output before it ships, every time — this is the exact type of output most likely to accidentally drift into promissory language.

### 10. Drawdown explainer
**Purpose:** Explains the worst losing period in a backtest honestly, in context — the number users most often misread or skip past.

```
Here is a strategy's worst drawdown from its backtest: [paste drawdown
magnitude, start date, end date, recovery date or "not recovered"].
Here is what the market did over that same period: [paste index/
benchmark performance for those dates].

Explain to a retail user with no finance background: what a drawdown is,
what specifically happened to this strategy during that period, whether
the broader market was also falling (context, not excuse), and how long
it took to recover — or state plainly that it had not recovered by the
end of the backtest.

Do not soften this. Do not use "only," "just," or "merely" before a
drawdown figure. Do not imply the drawdown is unlikely to recur.
```

**Variants:**
- *Comparative:* add "also state how this drawdown compares to the benchmark's worst drawdown over the same period" — useful context, but never framed as making the strategy's drawdown acceptable.
- *Brief:* "Maximum 60 words, for a tooltip" — for inline UI surfaces where the full explanation doesn't fit.

**Expected output format:** Markdown — 2-3 short paragraphs, plain language, with the drawdown figure and recovery duration stated explicitly and unhedged.

**Example input:** `-31%, 2022-01-04 to 2022-06-16, not recovered by backtest end (2022-12-31). Benchmark over same period: -19%.`

**Example output:**
> A drawdown is the drop from a strategy's peak value to its lowest point before recovering. This strategy's worst was **-31%**, from January to June 2022 — meaning a ₹100,000 paper balance fell to about ₹69,000.
>
> The broader market also fell over this period (-19%), so conditions were difficult generally. That is context, not reassurance — this strategy fell further than the market did.
>
> **It had not recovered by the end of the backtest period.** A drawdown of this size can recur.

**Safety/guardrails:** The banned softeners ("only," "just," "merely") are explicit because minimising language is the single most common way drawdown copy drifts into misleading territory. Run Prompt #12 against every output of this prompt before it ships.

**Test case:** Given an unrecovered drawdown, output states "not recovered" explicitly rather than omitting recovery status.

**Catalog metadata:** `id: trading-drawdown-explainer-v1` · `version: 1.0.0` · `tags: [trading, backtest, customer-facing]` · `author: asha.k`

---

### 11. Risk alert copy generator
**Purpose:** User-facing alert when a live paper-trading strategy breaches a stated risk threshold.
```
Write a risk alert for a user whose paper-trading strategy [name] has
breached this threshold: [e.g., "drawdown exceeded 15%"]. Tone: clear,
non-alarmist, actionable. Must state: what happened, in plain terms;
what the strategy's rules say to do (if anything); and that this is a
paper-trading environment with no real capital at risk. Do not suggest
a specific action beyond what the strategy's own rules define.
```
**Expected output:** A short alert, factual, explicitly scoped to what the strategy's own rules say — no independent advice injected.
**Safety/guardrails:** "Do not suggest a specific action beyond what the strategy's own rules define" prevents the alert from accidentally becoming ad-hoc investment advice.

### 12. Compliance language checker
**Purpose:** The hard gate — flags any language implying guaranteed or predictable returns.
```
Review this text for compliance risk: [paste text]. Flag, with severity
(critical/high/medium), any language that: implies guaranteed or
predictable returns, implies the platform is a licensed investment
advisor, omits a required risk disclosure, or uses absolute language
("always," "never," "guaranteed") about market outcomes. List each flag
with the exact offending phrase quoted.
```
**Expected output:** A list of flags, each quoting the exact problematic phrase — or an explicit "no flags found."
**Safety/guardrails:** This prompt's own banned-phrase list should itself be version-controlled in the catalog and reviewed periodically by an actual compliance professional, not just engineering — the prompt encodes a policy, and the policy owner should own its accuracy.

### 13. Disclaimer completeness checker
**Purpose:** Confirms every required disclaimer is actually present — a checklist gate, deliberately separate from the tone-focused compliance checker (#12).

```
Here is a user-facing screen's full text: [paste all copy from the
screen]. Here is our required-disclaimer list for this screen type
([backtest result / risk alert / strategy detail]): [paste required
disclaimers].

For each required disclaimer: is it present, is it visible in the main
flow (not hidden behind a link or collapsed section), and is it worded
in a way a non-expert would actually understand?

Output a checklist: PRESENT / MISSING / PRESENT-BUT-BURIED for each.
Do not rewrite the copy — only report status.
```

**Variants:**
- *Strict placement mode:* add "treat any disclaimer below the fold or inside a collapsed accordion as PRESENT-BUT-BURIED" for regulated surfaces where placement is itself a compliance requirement.
- *Multi-locale:* add "check the [locale] version against the locale-specific required-disclaimer list" for internationalised products.

**Expected output format:** Markdown checklist — one line per required disclaimer with status, plus a total count of MISSING items.

**Example input:** Backtest result screen. Required: past-performance disclaimer, paper-trading-only notice, data-date-range statement.

**Example output:**
```
- [x] Past performance disclaimer — PRESENT (visible, plain language)
- [ ] Paper-trading-only notice — MISSING
- [~] Data date range — PRESENT-BUT-BURIED (inside collapsed "details" panel)

MISSING count: 1 → blocks release per Wave 4 gate.
```

**Safety/guardrails:** This prompt reports status only and never rewrites copy — separating detection from correction keeps the check honest and prevents the model from "fixing" a disclaimer into something that technically appears present but no longer says what compliance approved.

**Test case:** Given copy missing the paper-trading notice, returns MISSING for that item and a non-zero MISSING count.

**Catalog metadata:** `id: trading-disclaimer-check-v1` · `version: 1.0.0` · `tags: [trading, compliance, safety-critical]` · `author: asha.k`

---

### 14. Regulatory terminology reviewer
**Purpose:** Flags language implying the platform is a licensed advisor or is giving personalised advice — a distinct legal risk from the "guaranteed returns" problem #12 covers.

```
Review this text for regulatory terminology risk: [paste text].

Flag any language that could imply: that we are a licensed/registered
investment advisor, that we are providing personalised investment advice
to a specific user, that we have assessed a user's suitability for a
strategy, or that we are acting in a fiduciary capacity.

Watch specifically for verbs like "recommend," "advise," "you should,"
"suitable for you," and "we suggest you." Quote each offending phrase
exactly and propose a compliant rewording that preserves the intent.

Return "no flags found" if genuinely clean.
```

**Variants:**
- *Jurisdiction-specific:* add "apply [SEC / FCA / SEBI] terminology conventions specifically" — the trigger vocabulary genuinely differs between regulators.
- *Detection-only:* remove the "propose a compliant rewording" clause when you want a pure audit trail with no suggested edits, mirroring #13's separation of detection from correction.

**Expected output format:** Markdown table — columns: Offending phrase (quoted exactly), Why it's a risk, Proposed rewording.

**Example input:** *"Based on your risk profile, we recommend this strategy is suitable for you."*

**Example output:**
```
| Phrase | Risk | Rewording |
|---|---|---|
| "we recommend" | Implies advisory capacity | "this strategy is available to explore" |
| "suitable for you" | Implies a suitability assessment we are not licensed to make | remove entirely |
| "Based on your risk profile" | Implies personalised advice | "Strategies matching the filters you selected" |
```

**Safety/guardrails:** The proposed rewordings are drafts for a compliance professional to approve, never auto-applied. A rewording that satisfies the model may still fail a real regulator's reading — this prompt narrows the review surface, it does not replace the reviewer.

**Test case:** Given text containing "suitable for you," flags it with a proposed removal.

**Catalog metadata:** `id: trading-regulatory-terms-v1` · `version: 1.0.0` · `tags: [trading, compliance, safety-critical]` · `author: asha.k`

---

### 15. Release checklist generator
**Purpose:** Full pre-release checklist for any change touching strategy or backtest logic.
```
Generate a pre-release checklist for this change: [describe change,
e.g., "new moving-average strategy template + backtest summary copy"].
Include: code review status, backtest red-flag check status, compliance
language check status, disclaimer completeness check status, and named
sign-off required. Format as a checkbox list.
```
**Expected output:** A checkbox-formatted checklist covering all four gates from the risk controls table, plus a named sign-off line.
**Safety/guardrails:** This checklist itself does not constitute sign-off — it's a tool to make sure sign-off is requested against a complete list, not a replacement for the human decision.

### 16. Compliance sign-off request
**Purpose:** Drafts the actual sign-off request sent to a named compliance reviewer — making the human gate in Wave 5 easy to action rather than easy to postpone.

```
Draft a compliance sign-off request for this release: [describe change].

Include: what is changing in one sentence a non-engineer understands,
which user-facing screens are affected, the results of the automated
checks already run (#12 compliance language, #13 disclaimers, #14
regulatory terms — paste their outputs), what specifically we are asking
this reviewer to approve, and a clear deadline.

Address it to [named reviewer]. Do not imply approval is a formality or
that a deadline overrides their judgement.
```

**Variants:**
- *Expedited:* add "note this is an expedited request and state explicitly what the business impact of the timeline is" — for genuine urgency, never as a default.
- *Re-review:* add "this is a re-request following changes made after previous feedback: [paste prior feedback]. Summarise what changed in response."

**Expected output format:** Markdown email — subject line plus body with the named sections above.

**Example input:** New drawdown explainer copy on the backtest results screen; automated checks all clean.

**Example output (excerpt):**
```
Subject: Compliance sign-off request — backtest drawdown copy — needed by Fri 24 Jan

Hi [reviewer],

We're adding a plain-language explanation of a strategy's worst
drawdown to the backtest results screen. Affected screen: Backtest
Results (retail users).

Automated checks run:
- Compliance language check (#12): no flags
- Disclaimer completeness (#13): all 3 required disclaimers present
- Regulatory terminology (#14): no flags

Asking you to approve: the drawdown copy's tone and whether the
past-performance disclaimer placement is adequate for this screen.

Needed by: Fri 24 Jan. If that's not workable, tell me and we'll move
the release — happy to walk through it on a call.
```

**Safety/guardrails:** The "do not imply approval is a formality" constraint exists because a sign-off request that pressures the reviewer produces rubber-stamp approvals, which defeats the entire purpose of the gate. Clean automated-check results are context for the reviewer, never an argument that review is unnecessary.

**Test case:** Output includes all three automated check results and a deadline framed as negotiable.

**Catalog metadata:** `id: trading-compliance-signoff-v1` · `version: 1.0.0` · `tags: [trading, compliance, communication]` · `author: asha.k`

---

### 17. Backtest regression test generator
**Purpose:** Ensures a known-good backtest result doesn't silently change when strategy code is refactored.
```
Here is a strategy's code: [paste code] and its known backtest result on
a fixed dataset: [paste result — returns, Sharpe, trade count]. Generate
a regression test that runs the backtest against the same fixed dataset
and asserts the result matches within [tolerance, e.g., 0.01%] — flagging
any drift as a failure requiring investigation, not silent acceptance.
```
**Expected output:** Runnable test code that fails loudly on any metric drift beyond tolerance.
**Safety/guardrails:** Tolerance should be near-zero for anything except floating-point rounding — silent drift in a backtest result, even small, is exactly the kind of bug this test exists to catch.

---

### 18. Edge-case market data generator
**Purpose:** Generates adversarial synthetic market data (flash crashes, zero-volume days, gaps) to test whether a strategy fails safely under conditions the historical dataset doesn't contain.

```
Generate synthetic OHLCV test data representing these adversarial market
conditions: [list, e.g., flash crash (-20% intraday, full recovery same
day), zero-volume day, limit-up gap, 10-day flat price with no movement].

For each scenario: produce [N] rows of daily OHLCV data in CSV format,
and state what a well-behaved strategy SHOULD do (e.g., "no signal —
insufficient volume to trade") versus what a naive implementation might
wrongly do (e.g., "divide-by-zero on volume-weighted calculation").

This data is for testing only and must never be mixed into the real
historical dataset.
```

**Variants:**
- *Regime-specific:* "Generate data for a prolonged low-volatility regime" — targets strategies that only misbehave when nothing happens for weeks, an easily-missed failure class.
- *Corporate-action variant:* add "include a 10:1 stock split and a large dividend ex-date" — these break price-continuity assumptions in ways a naive backtest silently mishandles.

**Expected output format:** CSV data block per scenario, each preceded by a short header stating the scenario name, expected correct behaviour, and the naive-implementation failure it's designed to catch.

**Example input:** `flash crash, zero-volume day`

**Example output (excerpt):**
```
# Scenario: zero-volume day
# Expected: no signal generated — insufficient liquidity to trade
# Naive failure: divide-by-zero in VWAP calculation
date,open,high,low,close,volume
2024-03-11,101.20,101.40,100.90,101.10,842000
2024-03-12,101.10,101.10,101.10,101.10,0
```

**Safety/guardrails:** Synthetic test data must live in a clearly-named test fixture directory and never enter the versioned historical dataset — contaminating real market data with synthetic rows would silently corrupt every backtest run afterward, and the corruption would be very hard to detect later.

**Test case:** Generated zero-volume row causes the strategy's signal function to return "no signal" rather than throwing or emitting a trade.

**Catalog metadata:** `id: trading-edge-case-data-v1` · `version: 1.0.0` · `tags: [trading, testing, adversarial]` · `author: asha.k`

---

### 19. Strategy documentation generator
**Purpose:** User-facing explanation of how a strategy works, so users choose based on understanding rather than on the backtest number alone.

```
Write a user-facing explanation of this strategy for someone with no
trading background: [paste strategy rules + parameter sensitivity output
from #6].

Cover: what the strategy is trying to do in one plain sentence, when it
enters and exits (in plain terms, not formulas), what market conditions
it is designed for, and what conditions it handles badly.

Do not include any performance figures — those live only on the backtest
screen with their own disclaimers. Do not imply the strategy is
appropriate for any particular user.
```

**Variants:**
- *Card/summary:* "Maximum 40 words for a strategy-list card" — the short form users see when browsing.
- *Technical appendix:* "Include the exact formulas as a collapsible appendix after the plain-language explanation" — for the minority of users who want them, without making the primary explanation unreadable.

**Expected output format:** Markdown — four short labelled sections (What it does / When it trades / Works best when / Struggles when), plain language throughout.

**Example input:** MA crossover 20/50, trending regime, fragile stop-loss at 2% (from #6).

**Example output (excerpt):**
> **What it does:** Follows medium-term price trends, buying when short-term momentum turns upward and selling when it turns down.
>
> **Struggles when:** Prices move sideways in a narrow range. The strategy enters and exits repeatedly without a trend developing, and its 2% stop-loss is close to normal daily movement, so trades may exit early.

**Safety/guardrails:** The "no performance figures" rule keeps performance claims confined to the one screen where the full disclaimer set (#13) is enforced — scattering numbers across documentation would require every surface to carry the full disclaimer stack, which in practice means some surface eventually won't.

**Test case:** Output contains no percentage-return figures and includes a populated "Struggles when" section.

**Catalog metadata:** `id: trading-strategy-docs-v1` · `version: 1.0.0` · `tags: [trading, docs, customer-facing]` · `author: asha.k`

---

### 20. Glossary term definer
**Purpose:** Plain-English definitions for trading jargon appearing in the UI, so a term never appears without an accessible explanation available.

```
Define this trading term for a retail user with no finance background:
[term].

Provide: a one-sentence plain-English definition (no jargon inside the
definition — if you must use another technical term, define it inline),
a concrete example using round numbers, and one sentence on why it
matters when evaluating a strategy.

Maximum 60 words total. Do not include performance claims or imply any
particular value of the metric is "good."
```

**Variants:**
- *Tooltip:* "Maximum 20 words, definition only" — for inline hover text where the example doesn't fit.
- *Comparative:* "Also state one commonly-confused adjacent term and how it differs" — for terms like *drawdown* vs *volatility* that users routinely conflate.

**Expected output format:** Markdown — three short labelled parts (Definition / Example / Why it matters), under 60 words total.

**Example input:** `Sharpe ratio`

**Example output:**
> **Definition:** A measure of how much return a strategy produced relative to how much its value moved up and down along the way.
> **Example:** Two strategies both return 10%. The one with steadier month-to-month results has the higher Sharpe ratio.
> **Why it matters:** It shows whether returns came smoothly or through large swings.

**Safety/guardrails:** The "do not imply any value is good" constraint matters more than it appears — a glossary entry saying "a Sharpe ratio above 2 is excellent" functions as implicit investment guidance and would need the same compliance review as any advisory copy.

**Test case:** Definition of "Sharpe ratio" contains no threshold claim about what value is good or bad.

**Catalog metadata:** `id: trading-glossary-v1` · `version: 1.0.0` · `tags: [trading, docs, customer-facing]` · `author: asha.k`

## Safety guardrails summary

Five rules, and the reason each one exists.

**1. The no-execution boundary is absolute.**
Enforced in the codebase, and repeated in every code-generating prompt. Two layers on purpose. A prompt instruction can be edited by anyone; an architectural constraint cannot be edited by accident.

**2. Compliance checks block, they do not advise.**
A flagged release cannot proceed. The only way past is a fix, or an explicit compliance override that gets logged with a name attached.

An advisory warning that people can click past is not a control. It is a note.

**3. Backtest red flags stop the flow.**
A strategy with unresolved red flags never reaches a user — even here, where no real money is at stake. If you let it through in the sandbox, the habit follows you to production.

**4. User-facing copy is re-checked every release.**
Not written once and assumed still fine. Two things drift over time: model behaviour, and what regulators expect. Copy that passed a year ago may not pass now, and nothing about your codebase would tell you.

**5. Independent review, never self-review.**
The signal-logic reviewer (#5) and the compliance checker (#12) must run in a **fresh session**, not the same conversation that produced the thing being checked.

Why this matters: a model reviewing its own output in the same context has already committed to its reasoning. It tends to defend that reasoning rather than test it. A fresh session has no such attachment.

---

## Reflection questions

1. Wave 3 (backtesting) can never be shortcut or run in parallel with Wave 2 — unlike the e-commerce chapter's more flexible ordering. Why not?
2. The compliance checker (#12) encodes *policy*, not just engineering judgement. Who should own its banned-phrase list, and how often should it be reviewed?
3. If this prototype became a real trading platform, which of the 20 prompts would need to change — and which would need to be **removed entirely** rather than adapted?

---

← [Chapter 6 — Case Study: E-commerce](./chapter-06-case-study-ecommerce.md) · [Learning path](./learning-path.md) · Next: [Chapter 8 — Case Study: Dating](./chapter-08-case-study-dating.md)
