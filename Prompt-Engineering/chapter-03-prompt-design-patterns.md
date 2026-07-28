--- filename: chapter-03-prompt-design-patterns.md ---

# Chapter 3 — Prompt Design Patterns

← [Chapter 2 — Foundations](./chapter-02-foundations.md) · [Learning path](./learning-path.md) · Next: [Chapter 4 — Prompt Management](./chapter-04-prompt-management.md)

## Narrative

Asha's manager gives her a small task. Take one code diff and write five things from it:

1. A pull request description
2. A release note
3. A Jira comment
4. A Slack update
5. A customer-facing changelog entry

She starts writing five separate prompts from scratch. Twenty minutes in, she notices she has typed "given this diff" five times. And "in Markdown" five times. And "do not invent features that are not in the diff" five times.

She stops and looks at what is actually different between them.

Only three things change: **who the model should act as** (engineer, PM, support), **who is reading it**, and **the tone**. Everything else is identical.

That is the moment prompt engineering stops being "write good sentences" and becomes something she already knows how to do: **factor out what repeats, parameterise what varies.** It is the same instinct as refactoring five near-identical functions into one function with arguments.

---

## Learning objectives

By the end of this chapter you will be able to:

1. Apply a 5-part prompt anatomy to any request, from a quick question to a reusable template.
2. Use at least 3 named patterns — few-shot, chain-of-thought, role-play, output-schema, self-critique — and know when each fits.
3. Build one prompt template with placeholders that works across a whole project, not just one conversation.

---

## Key concepts

### Prompt anatomy — the 5 parts

This is the master pattern. Everything else in this chapter is a specialisation of it.

| Part | Question it answers | Example |
|---|---|---|
| **Role** | Who should the model act as? | "You are a senior security auditor" |
| **Context** | What does it need to know? | The code, the error, the recent changes |
| **Task** | What should it do? | "Find injection risks" |
| **Constraints** | What must it *not* do? | "Do not change public API signatures" |
| **Output format** | What shape should the answer be? | "Markdown with these headers: ..." |

**Why five parts and not three or seven?**

Because each one removes a specific kind of guessing. Leave out Role and the model picks a default voice — usually a helpful generalist, which is wrong for a security review. Leave out Constraints and it "helpfully" refactors things you did not want touched. Leave out Output format and you get prose when you needed JSON.

Fill in all five and there is very little left to guess about.

**You do not always need all five.** For a quick throwaway question, Task alone is fine. But when a prompt gives you a mediocre answer, checking which of the five you skipped is the fastest way to find the problem.

### Few-shot prompting

**Plain definition:** Show 2–5 examples of input → output before the real task.

**When to use it:** When you want a specific *style* and describing that style in words is hard.

**Why it works better than describing:** Try writing a paragraph that fully specifies your team's commit message conventions. Verb tense, scope prefixes, length limit, when to include a ticket number. It takes a while and it is still ambiguous.

Now show three real commit messages. The model picks up all of it immediately, including conventions you would not have thought to mention.

**Style is easier to demonstrate than to describe.** That is the whole idea.

### Chain-of-thought (CoT)

**Plain definition:** Ask the model to reason step-by-step before answering.

**When to use it:** Multi-step logic. Debugging. Anything where the answer depends on tracing through something carefully.

**Why it works:** Without it, the model tends to jump to a plausible-sounding answer. Pattern-matching is fast and usually right — but "usually right" is exactly the problem when you are tracing a specific bug through specific code.

Forcing numbered reasoning steps means it has to actually walk the path. And you get a reviewable trail, so if the answer is wrong you can see *which step* went wrong.

**When not to use it:** Simple lookups and extraction tasks. Adding reasoning steps to "extract the date from this invoice" just makes the output longer.

### Role-play / persona framing

**Plain definition:** Tell the model who to be.

**Why it works:** A role carries a whole set of defaults with it — vocabulary, priorities, level of caution. "You are a senior security auditor" produces different output from "help me review this code," even with identical code attached.

**The important trick:** you can also assign *traits*, not just job titles. "Skeptical by default, flag anything uncertain" counteracts the model's natural tendency to be agreeable. Without that, security reviews often come back reassuring when they should not.

### Output-schema prompting

**Plain definition:** Specify the exact structure of the answer — a JSON schema, table columns, named sections.

**When to use it:** Any time the output feeds into something else. A script, a dashboard, a template.

**Why it works:** Two failures disappear. First, you stop getting prose when you wanted data. Second — and this one bites in production — you stop getting JSON wrapped in Markdown code fences that then fails to parse.

### Self-critique / reflection

**Plain definition:** Ask the model to draft, then criticise its own draft, then produce a final version.

**When to use it:** Anything customer-facing, or anything where being wrong is expensive.

**Why it works:** A single pass optimises for sounding complete. A critique pass optimises for finding problems. Those are different jobs, and doing them separately produces better results than asking for "a really good answer" once.

Making the critique **visible** matters too — you get to see what it caught, which tells you whether to trust the final version.

### Prompt template

**Plain definition:** A prompt where the stable parts are fixed and the variable parts are named placeholders.

**The test:** Could someone else on your team use it next month, on a different input, without asking you what to change? If yes, it is a template. If no, it is just a prompt that happened to work once.

---

## Example prompts (6)

### 1. The 5-part anatomy skeleton

**Purpose:** The master pattern.

```
Role: You are [expert role].
Context: [what the model needs to know — code, data, background]
Task: [the specific thing to do]
Constraints: [what must NOT happen, or rules that must hold]
Output format: [exact shape — e.g., "Markdown with these headers: ...", or a JSON schema]
```

**Why it works:** Each line closes off one source of ambiguity. Filling all five removes almost all guessing in a single pass.

### 2. Few-shot commit message prompt

**Purpose:** Teach your team's exact style faster than you could describe it.

```
Write a commit message for the diff below, matching the style of these
examples:

Example 1 — diff: [short diff] → message: "fix(auth): reject expired
refresh tokens before session lookup"
Example 2 — diff: [short diff] → message: "feat(checkout): add retry
with backoff for payment gateway timeouts"

Now write one for this diff:
[paste diff]
```

**Why it works:** Those two examples silently encode the scope prefix convention, the imperative mood, the lowercase style, and the rough length. Writing all of that as instructions would take a paragraph and still miss something.

### 3. Chain-of-thought debugging prompt

**Purpose:** Force visible reasoning for a logic bug.

```
Think through this step-by-step before giving a final answer. Do not
skip to the conclusion.

1. What does this code intend to do?
2. Trace the actual execution path for input: [input]
3. Where does actual behavior diverge from intent?
4. What is the minimal fix?

Code:
[paste code]
```

**Why it works:** Step 2 is the one that matters. "Trace the actual execution path" cannot be answered by pattern-matching — it requires walking the code. And if the trace is wrong, you can see exactly where.

### 4. Role-play security review prompt

**Purpose:** Get rigour instead of reassurance.

```
You are a senior application security auditor conducting a pre-release
review. You are skeptical by default and flag anything uncertain rather
than assuming best intent. Review the following code for injection,
auth bypass, and data exposure risks. For each finding, state severity
(critical/high/medium/low) and a concrete fix.

[paste code]
```

**Why it works:** "Skeptical by default" is doing real work here. The model's default is to be helpful and agreeable. In a security review, agreeable means underselling risks. This one phrase changes the whole posture.

### 5. Output-schema data extraction prompt

**Purpose:** Get output a script can actually parse.

```
Extract the following fields from the text below and return ONLY valid
JSON matching this schema — no prose, no markdown fences:
{
  "severity": "critical|high|medium|low",
  "component": "string",
  "summary": "string, max 15 words",
  "affected_versions": ["string"]
}

Text:
[paste incident report or bug text]
```

**Why it works:** "No prose, no markdown fences" is the load-bearing phrase. Without it you often get valid JSON wrapped in ` ```json ` fences, which breaks a naive parser — and that is a genuinely annoying bug to debug because the JSON itself is fine.

### 6. Self-critique refinement prompt

**Purpose:** Catch what a single pass misses.

```
Draft an answer to: [task]. Then, as a second pass, critique your own
draft: what's unclear, what's unverified, what would a skeptical
reviewer flag? Then produce a final, revised version incorporating that
critique. Show all three: draft, critique, final.
```

**Why it works:** Asking to see all three matters. If you only get the final version, you cannot tell whether the critique step did anything. Seeing the critique tells you what was fixed — and sometimes tells you the draft was fine and the "improvements" made it worse.

---

## Lab exercise (step-by-step)

1. Take one real request you made to an LLM recently that gave a mediocre answer.

2. Rebuild it using the 5-part anatomy. Fill in **all five parts**, even the ones that feel obvious.

3. Compare the two answers. Do not just note that it is better — work out **which of the five parts** fixed which problem. That diagnosis is the actual skill.

4. Pick a task you do at least weekly. Commit messages, PR descriptions, test names — anything repetitive.

5. Write a few-shot version using 3 real examples from your own history.

6. Extract it into a template file. Replace the one thing that changes each time with a named `[placeholder]`. Save it — this is your first real catalog entry for [Chapter 4](./chapter-04-prompt-management.md).

---

## Expected outputs

```
Original prompt: "fix this bug" + [pasted code]
Original answer: generic. Guessed at the framework. Missed the root cause.

Rebuilt with the anatomy:
  Role:          senior backend engineer familiar with [framework]
  Context:       the actual error, the actual code, the recent diff
  Task:          identify root cause and propose a minimal fix
  Constraints:   don't change public API signatures; must not break [test file]
  Output format: root cause (1 para), fix (diff), test (code block)

Rebuilt answer: found the root cause first try, respected the API
constraint, produced a runnable test.

WHICH PART FIXED IT:
  Mostly Context — the model had never seen the recent diff before.
  Also Constraints — previously it "helpfully" refactored a public
  method I did not want touched.
```

Plus one saved file: `templates/my-commit-message-prompt.md`, with real few-shot examples and named placeholders.

---

## Reflection questions

1. Of the 5 anatomy parts, which do you skip most often? What does skipping it actually cost you?
2. Pick a pattern you have not used yet — few-shot, CoT, role-play, output-schema, or self-critique. Which task in your work is it clearly right for?
3. What is the difference between a prompt that is *good* and a template that is *reusable*? Can something be one without the other?

---

## Further reading

- Anthropic prompt engineering guide *(placeholder link)*
- Research on chain-of-thought prompting *(placeholder link)*
- Next: [`chapter-04-prompt-management.md`](./chapter-04-prompt-management.md) — turning your templates into a versioned, tested catalog

---

## Quiz (5 MCQs)

**1. What are the 5 parts of the prompt anatomy?**
- A) Intro, Body, Conclusion, Summary, References
- B) Role, Context, Task, Constraints, Output format
- C) Question, Answer, Example, Test, Documentation
- D) Model, Temperature, Max tokens, Stop sequence, System prompt

> **Answer: B.**

**2. Why does few-shot often beat written instructions for matching a style?**
- A) Few-shot prompts are shorter
- B) Style is easier to demonstrate with examples than to describe in words
- C) Written instructions are not supported by most models
- D) It uses less computation

> **Answer: B.**

**3. What does chain-of-thought specifically prevent?**
- A) Using too many tokens
- B) The model jumping to a plausible-sounding conclusion without tracing the actual logic
- C) Hallucination in general
- D) The need for context

> **Answer: B.** Note it is about *reasoning*, which is different from *grounding* (Chapter 2's fix for hallucination).

**4. Why does the security review prompt say "skeptical by default"?**
- A) It is required syntax for role-play prompts
- B) It counteracts the model's tendency to be agreeable, which undersells risk in a review
- C) It makes the output shorter
- D) It has no real effect

> **Answer: B.**

**5. What makes something a reusable *template* rather than just a prompt?**
- A) It is over 100 words
- B) It uses role-play
- C) Its variable parts are named placeholders, so someone else could use it on a different input without asking you
- D) A senior engineer wrote it

> **Answer: C.**

---

← [Chapter 2 — Foundations](./chapter-02-foundations.md) · [Learning path](./learning-path.md) · Next: [Chapter 4 — Prompt Management](./chapter-04-prompt-management.md)
