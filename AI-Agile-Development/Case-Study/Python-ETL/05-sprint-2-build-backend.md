# Sprint 2 — Tomas Builds the Confidence Gate

← [Previous](04-sprint-2-planning.md) · [Case study index](README.md) · Next: [Sprint 2 — Frontend](06-sprint-2-build-frontend.md)

> **One line:** three days for something estimated at two weeks, and it genuinely works — plus the standup where Tomas raises a blocker that did not exist as a category three years ago.

---

## 1. Tuesday, 7 July, 09:05

Tomas Vargas opens [`artifacts/implementation-plan-NWD-103.md`](artifacts/implementation-plan-NWD-103.md) and reads Step 0.

Forty minutes later he has an answer, and the answer is yes: Azure AI Document Intelligence does return a confidence score on every cell inside a table, not just on top-level fields. The whole design survives contact with reality. He deletes `scratch/`, as the plan told him to, and starts Step 1.

By Friday afternoon NWD-103 is done. Reviewed, tested, deployed to the shared dev subscription, demonstrated to Amara Osei on a two-minute screen share.

**The proposal Kestrel sent Northwind in April estimated the confidence gate at two weeks.**

That number was not careless. It was written by an experienced engineer costing a piece of work he had done the equivalent of before: a config-driven validation layer with per-type thresholds, per-client overrides, structured failure reporting, a persistence path, and a metric. Two weeks is roughly what that costs to build carefully by hand.

It took three working days, one of which Tomas spent at a wedding.

This chapter is about how, and about the two things that got harder rather than easier.

---

## 2. What Tomas is actually building

If you have skipped the earlier chapters, this is everything you need.

**Where the numbers come from.** Northwind's counterparties — prime brokers, custodians, fund administrators — send position statements and trade confirmations as PDFs, in a different layout each. Those PDFs go to Azure AI Document Intelligence, a service you post a document to and get named fields back: *this is the account number, this is the quantity, this is the market value*. Every field comes back with a **confidence score**, a number between 0 and 1 saying how sure the model is that it read that field correctly.

**What the gate does with them.** It compares each score against a threshold and decides whether the document is trustworthy enough to load. Money is gated hardest, at 0.90. Quantities the same, because a quantity is money by another name. Dates at 0.85. Descriptive text at 0.75, because a slightly wrong security *name* does not break a reconciliation that matches on identifier and quantity, and a slightly wrong *quantity* does.

**The three rules that make it the shape it is**, all from Sofia Marchetti's spec and all argued about in [Chapter 3](03-sprint-1-design.md):

1. A **wrong number is worse than no number.** Low confidence never silently enters the warehouse.
2. A field the model **did not return** is a failure, not a pass. Absence is not evidence of correctness.
3. **One failing field sends the whole document to review.** Not the field. Not the row. The document.

Rule 3 is the one Tomas argued against in the spec review and lost. He is about to implement it, which is a slightly odd position to be in and he mentions it exactly once.

---

## 3. Step at a time — running P18

### The prompt, and the line that does the work

[P18](../../AI-Prompts-Library/phase-4-build/P18-implement-a-story.md) is run once per step. Not once per story. The session stays open across steps because the accumulated context is genuinely useful, but the prompt is re-issued fresh each time with a new step number.

Here is the opening as Tomas fills it in for Step 1:

```text
You are a Python 3.11 engineer implementing ONE step of an agreed implementation
plan. You are not implementing the story.

**STOP GATE — read before anything else.**
You will implement **Step 1 only**. Do not write, sketch, stub or scaffold code
for any other step, even if you can see it will be needed, even if it is two
lines. If Step 1 leaves something incomplete, that is correct and intended. Say
what is incomplete; do not fix it.

**Read** these completely first:
- Story: artifacts/stories/NWD-103.md
- Acceptance criteria: artifacts/acceptance-criteria-NWD-103.md
- Technical spec: artifacts/spec-confidence-gate.md
- Implementation plan: artifacts/implementation-plan-NWD-103.md
- Definition of Done: artifacts/definition-of-done.md
- Repository conventions: artifacts/CLAUDE.md

**Before writing code, list in five bullets or fewer:**
- What Step 1 must produce
- Which acceptance criteria it moves toward (by number)
- Which existing files or functions in this repository you will call
- Anything the spec does not say that you will have to decide
- Anything that makes you think the step as written is wrong

**Design constraints for this step:**
core/confidence.py must have NO Azure imports, NO I/O, and must NOT read
config/sources.yaml. It receives data and returns data. This is not a
preference; it is the reason the gate can be tested exhaustively.
```

Every clause in that prompt exists because of a specific way this goes wrong. Three are worth naming.

**The stop gate is the most important line in the file.** Without it, "implement Step 1" produces Steps 1 through 4, because the model can see where this is going and it is trying to help. You get the whole feature in one response, it looks correct, and you are back to the four-hundred-line problem the plan existed to prevent.

> **A stop gate** is an instruction that halts work at a named point regardless of how obvious the next move is. The awkwardness is the mechanism.

**"Anything that makes you think the step as written is wrong"** is the escape hatch. Rahul added it after Sprint 0. A plan written on Friday by somebody who has not slept on it can contain a step that is simply a bad idea, and an AI that silently implements a bad step is worse than one that argues.

**The design constraint about purity** is one paragraph and it is the highest-value input in the prompt. More on that in a moment.

### The pre-flight bullets

Before any code, five bullets come back. This is the cheapest thirty seconds in the process, because it tells you whether the model has understood the job while it is still free to be wrong.

```text
- Step 1 produces core/confidence.py: the value types, the default threshold
  table, and a document-level evaluation over header fields only.
- Moves toward AC-1 (money gated harder than text), AC-4 (missing value is a
  failure), AC-5 (null confidence never auto-accepts). Not AC-3 or AC-6.
- I will import ExtractedField and ExtractedDocument from core/extract.py and
  SourceConfig from config/settings.py. I will not add helpers that duplicate
  anything in either.
- The spec does not say what min_confidence should be for a document where NO
  field carries a score. I will treat it as 0.0 and flag it as an assumption.
- Nothing in Step 1 looks wrong to me.
```

**The fourth bullet is the one to read.** The spec is silent on one small thing, the model has noticed it is silent rather than quietly picking an answer, and it says which answer it took. That bullet is Definition of Done clause D9 doing its work at the moment it is cheapest — before the code exists, rather than in review.

---

## 4. The code that came back

Here is `core/confidence.py` as it ships. This is the real file, not a sketch of it.

### The verdict type

```python
WHY_MISSING = "missing"
WHY_BELOW_THRESHOLD = "below_threshold"
WHY_NO_CONFIDENCE = "no_confidence"


@dataclass
class GateResult:
    """The gate's verdict on one document."""

    passed: bool
    # Each failure: field, row, value, confidence, threshold, why.
    failures: list[dict] = field(default_factory=list)
    # True only if every field cleared its threshold — this is the numerator of
    # the straight-through rate, the single most useful metric in the system.
    straight_through: bool = False

    @property
    def reason(self) -> str:
        """A short human-readable reason, for the exception queue row."""
        if self.passed:
            return "ok"
        names = ", ".join(sorted({str(f["field"]) for f in self.failures}))
        return f"low_confidence: {names}"
```

> **A dataclass** is Python's way of declaring a small object that mainly holds values. You list the fields and their types and you get the boring parts — the constructor, equality, a readable printout — written for you.

Three things in twenty lines are worth naming.

**The reason codes are string constants, not an enum.** The comment in the file says why: *"Kept as literals rather than an enum so the value survives a round trip through the exception queue's JSON column unchanged."* That failure reason is written into a JSON column in Azure SQL, read back by an API, sent to Ji-woo's React screen and rendered to Priya. Every one of those hops is a chance for a fancy type to become a slightly different string. This is a decision about the *system*, made inside a module that only sees its own boundary, and it is exactly the sort of thing a reviewer should ask about.

**`failures` is a list of dicts and not a list of dataclasses**, which is the one design choice in this file Rahul queries in review. Tomas's answer is that the exception queue's storage is a JSON column and every failure goes into it verbatim, so a shape that serialises without a conversion step is one fewer place for the two sides to drift. Rahul accepts it and writes `Fair` on the thread.

**`reason` sorts the field names.** One line, easy to miss, and it exists so that the same document produces the same reason string every time. Otherwise Priya's queue shows `low_confidence: quantity, market_value` on Tuesday and `low_confidence: market_value, quantity` on Wednesday for the same problem, and her filter stops grouping them.

### The check, which is three questions in a fixed order

```python
def _check(
    f: ExtractedField,
    source: SourceConfig,
    row: int | None = None,
) -> dict | None:
    """Evaluate one field against its type's threshold. ``None`` means it passed."""
    threshold = source.confidence.threshold_for(f.field_type)

    # A field the model did not return at all is a failure, not a pass.
    if f.value is None:
        return {
            "field": f.name,
            "row": row,
            "value": None,
            "confidence": f.confidence,
            "threshold": threshold,
            "why": WHY_MISSING,
        }

    # Custom models return None confidence for some field types — treat as
    # unverified. Auto-accepting a value nobody scored is the exact failure the
    # gate exists to prevent.
    if f.confidence is None:
        return {
            "field": f.name,
            "row": row,
            "value": f.value,
            "confidence": None,
            "threshold": threshold,
            "why": WHY_NO_CONFIDENCE,
        }

    if f.confidence < threshold:
        return {
            "field": f.name,
            "row": row,
            "value": f.value,
            "confidence": f.confidence,
            "threshold": threshold,
            "why": WHY_BELOW_THRESHOLD,
        }

    return None
```

**The order of those three checks is the whole function**, and getting it wrong is easy.

The natural way to write a confidence gate is one line: `if confidence < threshold: fail`. Now consider a field where the model returned no value at all but reported 0.99 confidence — which happens, because the model is confident there is nothing there. One line of code lets it straight through. `None` is not less than 0.90.

So the missing-value check has to come **first**, before confidence is looked at.

The second check catches the same trap from the other direction. A field with a good value and `confidence = None`. In Python, `None < 0.90` raises a `TypeError`, so the code crashes rather than misbehaving — which sounds safe until somebody fixes the crash with `confidence or 1.0`, which silently treats "no score" as "perfect score". That is not a hypothetical; it is the obvious two-character fix and it inverts the meaning of the system.

**Whether an unscored field passes or fails is not a technical question at all.** It is Northwind's business deciding that a wrong number is worse than no number, and the second `if` in that function is where the decision lives.

### The evaluation, and the comprehension Tomas does not like

```python
def evaluate(doc: ExtractedDocument, source: SourceConfig) -> GateResult:
    """Gate every header field and every line-item field in the document.

    Failures are collected rather than short-circuited: the analyst working the
    exception queue needs to see everything wrong with the document at once, not
    fix one field and resubmit to discover the next.
    """
    failures = [c for f in doc.header.values() if (c := _check(f, source)) is not None]

    for idx, row in enumerate(doc.line_items):
        failures.extend(
            c for f in row.values() if (c := _check(f, source, row=idx)) is not None
        )

    return GateResult(
        passed=not failures,
        failures=failures,
        straight_through=not failures,
    )
```

**Failures are collected, not short-circuited**, and the docstring says why in one sentence: Priya needs everything wrong with the document in one pass. A gate that returns the first failure produces a document that bounces through review three times, and the second and third trips cost as much as the first.

The `:=` is Python's assignment expression — informally, the walrus operator. It lets you compute `_check(...)` once, bind it to `c`, and test it, inside a comprehension. It is compact and it is correct.

Tomas does not like it. That is section 5.

### Carrying the audit number

```python
def min_confidence(doc: ExtractedDocument) -> float:
    """The lowest confidence anywhere in the document.

    Carried onto every warehouse row. When a number in a report is questioned,
    this plus ``bronze_path`` is the answer: here is how sure the model was, and
    here is the original response it came from.

    A field with no reported confidence contributes 0.0 — the honest reading of
    "we do not know". An empty document is 0.0 for the same reason.
    """
    scores = [f.confidence if f.confidence is not None else 0.0 for _, f in doc.all_fields()]
    return min(scores) if scores else 0.0
```

This is the value that lands in the `MIN_CONFIDENCE` column in Snowflake, next to `BRONZE_PATH`. Together they are the answer to a question somebody asks eighteen months from now: *why does this row say 40,000?* Here is how sure the model was, and here is the exact JSON it came from, stored before anybody parsed it.

The docstring's second paragraph is the assumption from the pre-flight bullets, now written down permanently in the place a future reader will look.

---

## 5. Why the gate imports nothing

This is the design decision worth copying out of this chapter, so it gets its own section.

`core/confidence.py` has no Azure imports, does no I/O, opens no file, and does not read `config/sources.yaml`. It takes an `ExtractedDocument` and a `SourceConfig` and returns a `GateResult`. That is all it does.

The module docstring states it as an intention rather than an accident:

```python
"""The confidence gate. Pure logic, zero Azure imports, no I/O.

This is the heart of the design, and its isolation is the design decision worth
copying. The gate decides whether a document is trustworthy enough to enter the
warehouse; that decision is the one thing in the pipeline you most need to be
able to test exhaustively and reason about in an audit. So it takes dataclasses
in and returns a dataclass out. There is nothing to mock.
"""
```

> **A mock** is a fake stand-in for a real dependency in a test — a pretend Azure client that returns a canned answer. Mocks are useful and they are also where test suites go to die, because a suite full of mocks can be entirely green while the system is entirely broken.

**The payoff arrives in the next section: forty lines of tests, zero mocks, and a suite that runs in under a second.** You can hold the whole thing in your head, which means you can be sure it is right, which matters because this function decides what enters a financial warehouse.

The cost is that something else has to know about both the gate and the world. That thing is one adapter in the rules engine, and it is deliberately boring:

```python
@validator("confidence_gate")
def confidence_gate(
    doc: ExtractedDocument, source: SourceConfig, rule: RuleConfig
) -> list[RuleViolation]:
    """Fold the pure confidence gate into the rules engine.

    The gate stays in its own module with no Azure dependency and no knowledge
    of rules; this adapter is the only thing that knows both exist. That is why
    ``tests/test_confidence.py`` needs no rules configuration and this file needs
    no threshold logic.
    """
    result = confidence_gate_module.evaluate(doc, source)
    return [
        RuleViolation(
            rule_id=rule.id,
            rule_type="confidence_gate",
            severity=rule.severity,
            message=(
                f"{failure['field']} scored {failure['confidence']} "
                f"against a threshold of {failure['threshold']} ({failure['why']})"
            ),
            field=str(failure["field"]),
            row=failure["row"],
            observed=failure["confidence"],
            expected=failure["threshold"],
        )
        for failure in result.failures
    ]
```

That decorator is Step 4 of the plan and it is the rules engine's whole extension model. A rule is a `{id, type, severity, params}` block in `config/sources.yaml`; `type` selects one of the implementations registered with `@validator`. **Adding a control is a registration plus a YAML block, never a branch in the pipeline.**

Which is why the gate arrives in the running system as six lines of configuration:

```yaml
    - id: confidence_gate
      type: confidence_gate
      severity: error
      params: {}
```

and Broker Alpha's poor scan quality arrives as three:

```yaml
    confidence:
      by_field_type:
        currency: 0.92      # override: this broker's scan quality is weaker
```

**Look at the `message` string in that adapter.** It is not decoration. It is what Priya reads at 8:40 in the morning: *"market_value scored 0.87 against a threshold of 0.92 (below_threshold)"*. She can act on that without opening anything. `confidence_gate: failed` would tell her nothing and cost her ten minutes, forty times a morning.

---

## 6. Wednesday standup — a blocker that did not used to exist

Standup is fifteen minutes at 09:30, standing up, which is the only reason it stays fifteen minutes. Farhan runs it with [P21](../../AI-Prompts-Library/phase-4-build/P21-daily-standup-summary.md), which produces the summary afterwards rather than replacing the conversation.

Ji-woo goes first: the fixture agreement held, the queue list renders six rows, no blockers.

Then Tomas.

> **Tomas:** "Steps one to three are done. Tests pass. Um — I've got a blocker and it's a weird one."
>
> **Farhan:** "Go on."
>
> **Tomas:** "The AI produced something I don't fully understand yet, and I'm not comfortable merging it."
>
> *(a pause of about two seconds)*
>
> **Rahul:** "Which bit?"
>
> **Tomas:** "The number normaliser. It handles Broker Alpha writing one-two-three-four-point-five-six with a comma, and Broker Beta writing it with a dot as the thousands separator and a comma as the decimal. It decides which convention you're in by looking at the *last* separator in the string. I've read it four times. I believe it's right. I can't tell you why it's right for a number with no separators at all, and I can't name an input that breaks it."

Here is what he is looking at, in `core/rules.py`:

```python
def _strip_grouping(text: str) -> str:
    """Turn ``1,234.56`` or ``1.234,56`` or ``1 234,56`` into ``1234.56``.

    EM counterparties use the European convention; Broker Alpha uses the
    Anglo-American one. Deciding which is which by looking at the *last*
    separator is the only reading that works for both.
    """
```

**This is a legitimate blocker and it is a new category.**

For most of the history of this job, "I don't understand this code" meant one of two things: you were new, or the code was bad. Both had known responses. Neither of them is what is happening here. The code is good, Tomas is not new, and he did not write it — he asked for it and received it, complete, correct-looking, in about nine seconds.

Rahul's response is the reason this gets raised out loud rather than merged quietly at 6pm:

> **Rahul:** "That's D7. Don't merge it. What's your next move?"
>
> **Tomas:** "Ask it to explain?"
>
> **Rahul:** "Ask it to explain and you'll get a very good explanation of what it wrote, which you'll believe. Do that second. Do the boring thing first."

The boring thing takes Tomas twenty minutes and produces a table:

| Input | Convention | Should be |
|---|---|---|
| `1,234.56` | Anglo | `1234.56` |
| `1.234,56` | European | `1234.56` |
| `1 234,56` | European with a space | `1234.56` |
| `1234` | neither — no separator at all | `1234` |
| `1,234` | ambiguous. Anglo thousands, or European decimal? | ← **the real question** |
| `1.234` | same ambiguity, other way round | ← |

He writes the table by hand, from the two counterparties' actual documents, before asking the AI anything. Then he tests the function against every row.

It passes all six. And row five is where the twenty minutes pays for itself, because the answer turns out to be *"Broker Alpha never sends a bare `1,234` — quantities always carry two decimal places"*, which is true of every document in the fixture set and is **not a property of the code at all**. It is a property of one counterparty's formatting, held nowhere, relied on silently.

Tomas adds it as a comment and a test, and raises it as an open question on the story rather than solving it. Farhan's standup summary carries one line about it, which is what a standup summary is for:

```text
Tomas — NWD-103 steps 1-3 done, tests green.
  Blocked (self): number normaliser understood but one input class is
  undecidable from the string alone (`1,234`). Currently safe because
  broker_alpha always emits 2dp. Unsafe if a third counterparty doesn't.
  Written up on NWD-106. Not blocking the sprint.
```

**Three things about this standup are worth taking away.**

**"I don't understand what the AI gave me" has to be sayable.** If it is heard as an admission of weakness, nobody says it, and the code merges anyway. The only difference is that the not-understanding is now invisible and in production. Rahul's entire contribution to making it sayable is that he treated it as a normal engineering fact and asked what the next move was.

**Asking the AI to explain its own code is a fine second move and a terrible first one.** You will get a fluent, plausible, confident explanation, and you have no independent way to check it. Worse, once you have read it you *feel* like you understand the code, and the feeling is indistinguishable from the real thing. Build your own model first — a table of cases, a handful of inputs, a prediction of what each should do — and use the explanation to check yours rather than to replace it.

**The thing Tomas found was not in the code.** It was an assumption about a counterparty's document formatting that the code depended on and nothing recorded. You do not find those by reading a diff. You find them by trying to predict what the code does and discovering you cannot.

> **Comprehension debt is code in production that nobody on the team can explain.** It is invisible, it accrues silently, and it is called in during an incident, at night, by whoever understands it least. Clause D7 exists to stop it accruing, and standup is where it gets declared.

---

## 7. Friday — the tests, in a fresh session

[P20](../../AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) is run in a **new session**, with `core/confidence.py` deliberately not open. That is not tidiness, it is the entire mechanism.

Its first instruction is a refusal:

```text
**STOP GATE — read before anything else.**
Do NOT read, open, request or infer the implementation. You are writing tests
from the requirement, not from the code. If you find yourself needing to know how
something is implemented in order to test it, that is a signal the requirement is
under-specified — say so and stop, rather than guessing.
```

**A test is only worth having if it could disagree with the code.** Generate it in the same session that wrote the code and it never can — you get a suite that asserts the implementation does what the implementation does, which is a tautology wearing a safety net's clothes. It goes green forever, including when the behaviour is wrong.

So the model is given the acceptance criteria, the spec, the Definition of Done, and the **signatures only** of the things it is testing. No bodies. Tomas gets that placeholder wrong the first time, pastes the dataclasses with their methods, notices, and starts again. It costs him four minutes and it is the single most common way this prompt is misused.

### The four tests

Nine tests come back. Four of them carry almost all the value, and each protects a different way the gate could be wrong.

```python
def test_money_field_gated_harder_than_text(source: SourceConfig) -> None:
    """0.82 passes for a name and 0.85 fails for a value. That asymmetry is the point."""
    doc = make_document(
        header={
            # 0.82 clears the 0.75 string threshold
            "security_name": _f("security_name", "Acme Corp", 0.82, "string"),
            # 0.85 does NOT clear the 0.90 currency threshold
            "market_value": _f("market_value", 1_000_000, 0.85, "currency"),
        }
    )

    result = evaluate(doc, source)

    assert not result.passed
    assert {f["field"] for f in result.failures} == {"market_value"}
```

**Test one is the entire design in one assertion.** A lower confidence passes for a name than fails for a value. If somebody later flattens the thresholds to a single constant "for simplicity" — which is a genuinely tempting thing to do when you are reading the config loader and it looks over-engineered — this test goes red immediately and explains itself in its own name.

```python
def test_missing_value_is_a_failure_not_a_pass(source: SourceConfig) -> None:
    """A field the model did not return is a failure, however sure it claims to be."""
    doc = make_document(header={"quantity": _f("quantity", None, 0.99, "number")})

    assert evaluate(doc, source).failures[0]["why"] == "missing"
```

**Test two catches the easy mistake.** `value=None`, `confidence=0.99`. This is the one-line gate — `if confidence < threshold` — sailing straight past a field that does not exist, at the highest confidence in the file. The test forces the missing-value check to come first, and it is why `_check` is ordered the way it is.

```python
def test_null_confidence_never_auto_accepts(source: SourceConfig) -> None:
    """No score means unverified. Unverified never loads."""
    doc = make_document(header={"quantity": _f("quantity", 100, None, "number")})

    assert not evaluate(doc, source).passed
```

**Test three is the same trap from the other direction**, and its value is that the right answer is not obvious from first principles. Nothing about programming tells you whether an unscored field should pass. It is a business decision — a wrong number is worse than no number — and this three-line test is where that decision is recorded in a form the machine enforces.

```python
def test_one_bad_line_item_fails_whole_document(source: SourceConfig) -> None:
    """Partial ingestion of a statement produces a break that looks real.

    So one bad row rejects the document, not the row.
    """
    doc = make_document(
        header={"account_number": _f("account_number", "ACC-1", 0.99)},
        line_items=[
            {"quantity": _f("quantity", 100, 0.99, "number")},
            {"quantity": _f("quantity", 200, 0.60, "number")},  # bad row
        ],
    )

    result = evaluate(doc, source)

    assert not result.passed
    assert result.failures[0]["row"] == 1
```

**Test four is the least intuitive of the four and it is the one Tomas is pleased with.**

He is pleased with it for a reason that is worth stating, because he argued the opposite position in the spec review six days ago and lost. A reasonable engineer looks at a statement with fourteen positions, one of which has a weak settlement date, and wants to load the thirteen good ones. Most systems do exactly that. Here it is forbidden, because a statement loaded with thirteen of its fourteen positions produces a reconciliation break on the fourteenth that looks precisely like a genuine settlement failure, and the analyst chasing it will spend half a day emailing a broker about a position that was simply never loaded.

Tomas lost that argument to Amara, whose framing went into [ADR-0003](artifacts/adr/) verbatim: *"a break I have to chase and then find out was never real costs me more than a document I have to key."*

This test is that ADR, in code, enforced. It is the only test in the file that reasons about line items as a **collection** rather than one field at a time: it builds a list of rows and asserts something about the document as a whole. The second assertion — `result.failures[0]["row"] == 1` — is Step 3's off-by-one hazard, the one Rahul flagged in "Where a human must look", pinned down permanently.

Tomas reads it, checks the row index is zero-based and that the bad row is index 1, and moves on to the next thing on his list.

### What the suite looks like

```text
$ pytest -q tests/test_confidence.py
9 passed in 0.19s
```

Nine tests. No mocks, none needed. Under a fifth of a second, which means Tomas runs them on every save rather than every commit, which is the difference between tests you use and tests you have.

The names alone read as a specification, which is the actual test of a behaviour-driven suite:

```text
money field gated harder than text
missing value is a failure not a pass
null confidence never auto accepts
one bad line item fails whole document
clean document is straight through
integer fields are gated as numbers
failure reason names every bad field
min confidence is the weakest field
min confidence treats unscored as zero
```

Hand that list to Amara and she can check it. Not one name mentions `evaluate`, `_check` or `GateResult`. Rewrite the module tomorrow and, if the behaviour is the same, this file does not change.

### Criteria-to-test map, and the things it could not test

The prompt requires three sections after the file, and the third is the one that earns it a place in the process.

```text
| Criterion | Test |
|---|---|
| AC-1 currency below 0.90 rejected        | test_money_field_gated_harder_than_text |
| AC-3 broker_alpha currency at 0.92       | test_integer_fields_are_gated_as_numbers + fixture override |
| AC-4 missing value is a failure          | test_missing_value_is_a_failure_not_a_pass |
| AC-5 null confidence never auto-accepts  | test_null_confidence_never_auto_accepts |
| AC-6 one bad line item fails the document| test_one_bad_line_item_fails_whole_document |
| AC-8 failure identifies the row          | test_one_bad_line_item_fails_whole_document (row assertion) |
| AC-9 MIN_CONFIDENCE carried for audit    | test_min_confidence_is_the_weakest_field |

No criterion is unmapped.
```

And then:

```text
TESTS I COULD NOT WRITE

1. COMPLETENESS OF THE LINE ITEM LIST. I cannot write a test proving the gate
   received every line item the document contained. `evaluate` takes a document
   whose line_items are already assembled and has no access to the source PDF,
   so the information does not exist at this layer. The acceptance criteria do
   not state where completeness is meant to be checked. To write this test I
   would need either (a) an expected row count passed in alongside the line
   items, or (b) a completeness check at the extraction layer with its own
   criteria. Recommend raising this with the architect.

2. UNKNOWN FIELD TYPE. The criteria do not say what happens to a field type
   outside the four in spec §3.1. Needs a criterion.

3. EMPTY DOCUMENT. The criteria do not say whether a document with no fields
   and no line items should pass. Passing seems technically defensible and
   operationally alarming. Needs a criterion.
```

Tomas reads all three. He agrees with all three.

Item 1 is straightforwardly correct as a statement about the module: a function handed a list has no way to know what is not in it, and no amount of cleverness inside `evaluate` changes that. Items 2 and 3 are real gaps in the acceptance criteria, and he raises both with Amara that afternoon; an empty document now fails, and an unknown field type gets the hard default of 0.90.

Item 1 he leaves, because it reads as a description of where the module's boundary is rather than as something that needs doing, and because it is Friday afternoon and NWD-106 is next.

---

## 8. The rest of the backend

NWD-103 is the flagship and it is not the sprint. Over the fortnight Tomas lands six more stories the same way — one step, one verification, one read-through, next step.

| Story | What it does | Landed |
|---|---|---|
| NWD-101 | PDFs land immutably at `raw/{broker}/{yyyy-mm-dd}/{file}.pdf` | day 2 |
| NWD-102 | Classify a PDF to its counterparty layout; below 0.75 confidence it goes to review rather than being guessed | day 3 |
| NWD-103 | The confidence gate | day 4 |
| NWD-106 | Transform extracted fields into the canonical position schema | day 7 |
| NWD-107 | Load into Azure SQL and Snowflake, idempotently by SHA-256 of content | day 9 |
| NWD-104 | Translate EM documents to English before matching | day 10 |
| NWD-105 | Redact PII before anything is persisted; fails closed | day 10 |

Two of those carry a detail that matters later.

**NWD-107 keys idempotency on the SHA-256 hash of the file's content, not its name.** Counterparties resend the same statement under a new filename constantly — `BA_POS_20260724.pdf` becomes `BA_POS_20260724_RESEND.pdf` and it is the same document. Hashing the content means a resend updates the row it should update instead of creating a second one. This is written down as an invariant and it is nevertheless violated in one code path, which becomes bug NWD-140.

**NWD-104 translates descriptive fields only.** The data contract carries the note in [Chapter 3](03-sprint-1-design.md): `INSTRUMENT_ID` is never translated, `INSTRUMENT_NAME` may be. Translating an identifier breaks the match against Aladdin, which is the whole point of extracting it. That note is in the contract, written on the Friday of Sprint 1, and it is violated in Sprint 2 anyway. It becomes NWD-138.

The commit that wires up extraction is `7c30fb1`, 8 July, *"NWD-102 wire up extraction"*. It is unremarkable, it passes review, and one line of it comes back in [Chapter 8](08-sprint-3-rework.md).

---

## 9. What Tomas hands over, and the thing that nearly went wrong

By Friday 17 July the backend is done in the sense the [Definition of Done](artifacts/definition-of-done.md) means it: merged, green, reviewed by a second person, deployed to the shared dev subscription, exercised there, and accepted by Amara.

| What crosses into Sprint 3 | Where | For |
|---|---|---|
| The pipeline, end to end for Broker Alpha | `doc_ingestion`, dev subscription | Ananya, to test |
| 41 tests on the gate and the rules engine | `tests/` | Everyone |
| A real exception-queue endpoint | Azure SQL + API | Ji-woo, who swaps out the fixture on day 6 |
| Three open questions on NWD-106 | Story comments | Sofia and Amara |

**And here is the honest close, because a chapter about a thing that went well is not worth much on its own.**

The speed was real. Three days against two weeks is not a rounding error and it is not a trick — the code in this chapter is the code that ships, it does what the spec says, and it is better tested than most code written under a two-week estimate. Rahul is right when he says at the demo that the plan-then-step-then-test loop is the reason, and that the loop matters more than the model does.

But nobody costed what the speed does to everything downstream of it, and one thing quietly bent under it.

On the Friday, Rahul reviews the whole of NWD-103 in one sitting: eight steps, roughly six hundred lines including tests, in ninety minutes, because the pull request opened at eleven and the sprint demo is at three. Clause D7 says a human has read every line and can explain what it does, and the check is that the reviewer picks a line and asks the author about it.

He picks a line from `core/confidence.py` and Tomas answers it well.

Rahul admits at the retrospective, three weeks later, that by the time he reached `sinks/sql_sink.py` — the last file in the review, the one that writes exception rows — he was reading for shape rather than for meaning. Nothing was wrong with it. He would not have known if there had been.

**The Definition of Done costs ninety minutes a story, and Farhan planned for that.** What nobody planned for is that a team producing code three times faster is asking one reviewer to read three times as much, on the same day, with the same demo at three o'clock. Review capacity was reserved at half a day a day and it was never the thing that got faster.

That is not the bug in this book. The bug is somewhere else entirely and it is already in the repository, in a line of `7c30fb1` that every one of them read and approved, and it will be another three weeks before anybody counts the rows on a PDF by hand.

---

**Next:** [Chapter 6 — Sprint 2: Build, frontend](06-sprint-2-build-frontend.md). Ji-woo builds the screen where a human fixes what the machine got wrong, having spent a morning watching the human do it the old way first.

---

← [Previous](04-sprint-2-planning.md) · [Case study index](README.md) · Next: [Sprint 2 — Frontend](06-sprint-2-build-frontend.md)
