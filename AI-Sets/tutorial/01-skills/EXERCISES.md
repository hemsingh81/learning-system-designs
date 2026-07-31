# Exercises — AI Skills

## Easy: add a category

Add `"spam"` to `classify_ticket.py`'s `Category` literal. Update the
system prompt to describe when to use it. Write one new test in
`tests/unit/test_skills_classify_ticket.py` proving a spam-like ticket
gets classified correctly (script a `FakeLLM` response for it — see the
existing `test_happy_path` for the pattern).

**Check yourself:** run `.\scripts\test.ps1 -Path tests\unit\test_skills_classify_ticket.py`
— your new test should pass alongside all the existing ones.

## Medium: build a new skill — `detect_language`

Create `src/aisets/skills/detect_language.py` with:
- An output schema `DetectedLanguage(language_code: str, confidence: float)`
  (use a 2-letter ISO code like `"en"`, `"fr"`, `"hi"`).
- A sensible `empty_input_result()`.
- A system prompt following `docs/04-prompting-guide.md`'s template.

Then:
1. Write at least the five standard test cases (see `DECISIONS.md` /
   `README.md` section 10) in `tests/unit/test_skills_detect_language.py`.
2. Add a short new example, `examples/17_detect_language.py`, that runs it
   against 3 sample strings in different languages.

**Check yourself:** all your new tests pass, and running the example
prints three different language codes.

## Break it on purpose: watch a skill fail without the safety net

Temporarily comment out the `Field(ge=1, le=10)` bound in
`score_severity.py`'s `SeverityScore.score`, leaving it as a plain `int`.
Then:

1. Run `python -c` (or a scratch script) that queues a `FakeLLM` response
   with `"score": 9999` and call `ScoreSeverity.run(...)`.
2. Observe: it now SUCCEEDS with an obviously wrong value, instead of
   raising `BadOutput`.
3. Put the `Field(ge=1, le=10)` bound back, run the same script again, and
   confirm it now raises (after one retry).

**What this teaches:** the schema IS the safety net. Removing a bound
doesn't just remove a nice-to-have — it silently lets garbage through as
if it were a normal, valid answer. This is why `docs/00-PLAN.md`'s testing
plan requires 100% coverage on files where an out-of-range value would be
dangerous.
