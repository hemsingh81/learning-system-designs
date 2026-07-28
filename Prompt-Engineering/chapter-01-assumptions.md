--- filename: chapter-01-assumptions.md ---

# Chapter 1 — Assumptions and the Mindset Shift

← [Learning path](./learning-path.md) · Next: [Chapter 2 — Foundations](./chapter-02-foundations.md)

## Narrative

It is 11:40 at night. Asha has 34 browser tabs open.

Somewhere around tab 12 she stopped reading and started skimming. Somewhere after that she stopped skimming and just started pressing Ctrl+F to find the error message. The bug — a race condition in a checkout retry handler — has been "almost fixed" for two hours.

She is good at this. Eight years of experience means she can usually guess where a bug lives before she opens the file. But tonight her guess was wrong three times in a row. Each wrong guess cost her a fresh round of searching: change the search words, open five results, skim, throw them away, change the words again.

At midnight she tries something different, almost by accident.

She pastes three things into Claude: the stack trace, the failing test, and the last three commits. Then, instead of asking "why is this broken?", she writes four numbered questions:

1. What is the most likely root cause?
2. What is the smallest way to reproduce it?
3. What are three possible fixes, ranked by risk?
4. What test would have caught this?

Eleven minutes later she has her answer. By hand it would have taken until 1 a.m.

But the answer is not the important part. The important part is that **she now has a reusable version of the question itself.**

That is what this chapter is about. Not "use AI more." It is this: **stop asking questions and start engineering prompts.**

---

## Learning objectives

By the end of this chapter you will be able to:

1. Name at least 3 habits from search-first debugging that slow you down, and say what replaces each one.
2. Explain the difference between "asking a question" and "engineering a prompt" in your own words.
3. Find 2 recent problems from your own work where a structured prompt would have saved real time.

---

## Key concepts

Five ideas. Each one is defined in plain words, then explained.

### Search-first habit

**What it is:** You treat the LLM like a search engine. You type one line, skim the answer, and move on.

**Why it feels good:** It is fast to start. No setup. No thinking about how to ask.

**Why it fails:** It does not build up over time. Every new question starts from zero. You learned nothing reusable from the last one.

Think of it like solving the same maths problem on a napkin every week and throwing the napkin away each time.

### Prompt-first habit

**What it is:** You treat the request as something you build on purpose. You gather the context. You say exactly what you want. You say what shape the answer should take.

**Why it feels slower:** Because it is, the first time. You spend two minutes setting it up instead of ten seconds typing.

**Why it wins:** It builds up. The same prompt — or a small change to it — works again next week. And the week after.

Napkin versus a saved spreadsheet formula.

### The reusability gap

**What it is:** The cost of not saving a good prompt.

**Why it matters:** If you cannot find the prompt you wrote last week, you pay the "how do I even ask this" tax every single time.

Asha's four-question prompt took her eleven minutes to get an answer. Writing the prompt took maybe two of those minutes. If she throws it away, she pays those two minutes again tomorrow. And the day after. Over a year that is real time.

### Context assembly

**What it is:** Deliberately gathering what the model needs *before* you ask.

**What it replaces:** Hoping the model works it out on its own.

Asha's midnight prompt worked partly because she pasted the stack trace, the failing test, **and** the recent commits. The model could not have guessed at those last two. No search engine could have known them either — they only exist in her repo.

### Output contract

**What it is:** Deciding in advance what shape the answer should be. A ranked list. A code diff. A JSON object.

**Why it helps:** Two reasons. First, you can skim it faster because you know where to look. Second, if you want to use the answer in a script, it will actually parse.

Asha asked for five numbered sections. So she got five numbered sections — not a wall of prose she then had to read carefully to find the fix.

---

## Example prompts (6)

### 1. The "stop and restate" prompt

**Purpose:** Forces you to gather context before you type. Catches the "I do not actually know what I am asking" problem.

```
I'm about to ask an LLM for help with [problem]. Before I do, list exactly
what context it needs to answer well: what code, what error output, what
constraints, and what "done" looks like. Just the list — don't answer the
underlying problem yet.
```

**Why it works:** It splits one job into two. First job: work out what is needed. Second job: solve it. Most bad prompts fail at the first job, not the second — and you cannot tell which is failing when both happen at once.

### 2. Root-cause hypothesis prompt

**Purpose:** Replaces "why is this broken" with a proper diagnostic. This is Asha's midnight prompt.

```
You are an expert debugging assistant. Given:
- Repository: [repo name/path]
- Failing test: [test name]
- Stack trace:
[paste stack trace]
- Recent commit diff:
[paste diff]

Produce: 1) a concise root-cause hypothesis, 2) minimal reproduction steps,
3) three candidate fixes ranked by risk, with code snippets, 4) unit tests
that would cover the fix, 5) a one-line commit message. Output in Markdown.
```

**Why it works:** Two reasons.

First, **every input is explicit and labelled.** The model is not guessing what "the code" means.

Second, **every output section is named.** Without that, the model tends to jump straight to "here is a fix." Naming section 1 as "root cause" forces it to show its reasoning before it proposes anything. If the reasoning is wrong, you can see that immediately — instead of finding out after you have applied the fix.

### 3. "What am I missing" prompt

**Purpose:** Finds blind spots before you commit to a fix.

```
Here is my proposed fix for [bug]: [paste diff or description].
What edge cases, race conditions, or regressions might this introduce?
List them by likelihood, most likely first.
```

**Why it works:** It asks for criticism, not approval.

This matters more than it sounds. If you ask "does this fix look right?", the model will usually agree with you. Agreeing is the easy answer. Asking "what could go wrong" removes that easy path.

### 4. Convert-a-search-query prompt

**Purpose:** A bridge exercise. Take a habit you already have and upgrade it.

```
Here is the Google search I would normally run: "[paste search query]".
Rewrite this as a structured prompt with explicit context, task, and
desired output format, assuming I have access to [describe what you
actually have: logs, code, docs].
```

**Why it works:** It starts where you already are. You know how to write a search query. This reframes that skill instead of asking you to drop it and learn something unrelated.

### 5. Time-box comparison prompt

**Purpose:** Turns "prompting is faster" from a claim into a number you generated yourself.

```
I spent [X minutes] searching for a solution to [problem] before finding
[the answer/giving up]. Here's the problem restated with full context:
[context]. Solve it now, and separately estimate how much of my search
time was probably spent on ambiguity I could have removed up front.
```

**Why it works:** You will believe your own measurement more than you believe this chapter.

### 6. Reusability check prompt

**Purpose:** Tests whether a prompt you just wrote is actually reusable, or was a one-off.

```
Here is a prompt I just used successfully: [paste prompt]. Rewrite it as
a template with [placeholders] so I could reuse it for a different bug,
service, or language. Flag anything in the original that was too specific
to generalize.
```

**Why it works:** It turns a lucky one-off into something you own. This is the seed of the prompt catalog you will build in [Chapter 4](./chapter-04-prompt-management.md).

---

## Lab exercise (step-by-step)

1. Find the last bug you fixed mainly by searching. If nothing comes to mind, open your issue tracker and pick any bug closed in the last month.

2. Write down honestly: how long did it take? Roughly how many searches and tabs?

3. Rebuild the problem as full context. Include the error message, the relevant code, and what you had already tried.

4. Run Prompt #2 (root-cause hypothesis) against that context.

5. Compare. Did the structured prompt reach the same answer faster? What did it catch that your searching missed — and what did your searching catch that it missed?

6. Run Prompt #6 (reusability check) against your prompt from step 4. Save the result somewhere you will find it again. **This is your first catalog entry for Chapter 4.**

---

## Expected outputs

A short written comparison. Roughly this shape:

```
Bug: [one line]
Search-first time: ~45 min, 12 tabs, 3 rephrased queries
Prompt-first time: ~8 min, 1 prompt, 1 follow-up

What the prompt caught that search missed:
  It asked me to include the recent commit diff. Search results could
  never have known about that — the change only exists in my repo.

What search caught that the prompt missed:
  A library-specific bug in a GitHub issue thread from last month.
  The model did not know about it.

Reusable template saved: templates/my-root-cause-prompt.md
```

**Be honest in that third section.** Search genuinely wins sometimes — usually when the answer depends on something very recent or very specific to one library's issue tracker. A tutorial that pretends otherwise is not useful to you.

---

## Reflection questions

1. What is the real reason you reach for search first — speed, trust, habit, or something else? Be specific with yourself.
2. Think of a prompt you have reused more than twice, even informally copy-pasted from a note. What made it worth keeping?
3. What would need to be true for your whole team to work prompt-first, not just you?

---

## Further reading

- Model provider documentation on prompting best practices *(placeholder — add your provider's official guide)*
- Prompt engineering glossary *(placeholder link)*
- Next: [`chapter-02-foundations.md`](./chapter-02-foundations.md) — the mental models that explain *why* structured prompts work better

---

## Quiz (5 MCQs)

**1. What is the "reusability gap"?**
- A) The delay between asking a question and getting an answer
- B) The cost of not saving a good prompt so you can reuse it later
- C) The speed difference between two LLM providers
- D) A measure of context window size

> **Answer: B.** It is about lost reuse value, not raw speed.

**2. Why does the "stop and restate" prompt ask for a list of needed context instead of an answer?**
- A) To save tokens
- B) Because the model cannot solve problems directly
- C) To split context-gathering from problem-solving, since most bad prompts fail at the first step
- D) The order makes no difference

> **Answer: C.**

**3. In the root-cause prompt, why are all five output sections named?**
- A) To make the answer longer
- B) So the model cannot skip to a fix without showing its reasoning first
- C) Because Markdown requires numbered lists
- D) To match a specific model's training format

> **Answer: B.** If the reasoning is wrong, you see it before you apply the fix.

**4. What is the main problem with the search-first habit, according to this chapter?**
- A) Search engines are unreliable
- B) It does not compound — every question starts from zero
- C) It is always slower than prompting
- D) It cannot be used for debugging

> **Answer: B.** Note the chapter does *not* claim search is always slower. Sometimes it wins.

**5. What should the lab exercise leave you with?**
- A) A general feeling of having learned something
- B) A written time comparison and a saved reusable prompt template
- C) A passing test suite
- D) An approved code review

> **Answer: B.**

---

← [Learning path](./learning-path.md) · Next: [Chapter 2 — Foundations](./chapter-02-foundations.md)
