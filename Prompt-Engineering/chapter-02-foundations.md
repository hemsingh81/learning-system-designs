--- filename: chapter-02-foundations.md ---

# Chapter 2 — Foundations and Mental Models

← [Chapter 1 — Assumptions](./chapter-01-assumptions.md) · [Learning path](./learning-path.md) · Next: [Chapter 3 — Prompt Design Patterns](./chapter-03-prompt-design-patterns.md)

## Narrative

Asha's root-cause prompt worked last night. So this morning she tries the same approach on a different bug.

She gets back a confident, detailed, **completely wrong** answer. The model invented a config flag that does not exist anywhere in her codebase, then built a whole explanation around it.

Her first instinct is the old one: *the AI is unreliable, back to Google.*

Her second instinct — the one she is trying to build — is to ask **why** it happened.

She looks again. She never pasted the config file. The model did not have it. So it did what any system does when it hits a gap: it filled the gap with the most likely thing. It had seen thousands of codebases with config flags like that one. It guessed, and it presented the guess as fact.

That is not mysterious. It is the same as calling a function with the wrong arguments and getting a plausible-looking wrong result. The difference is that a function throws an exception. **The model just answers anyway.**

Once she sees it that way, the fix is obvious. She did not tell the model what was *known* versus what it should *not assume*. So it assumed.

This chapter builds the mental models that make failures like this predictable instead of confusing.

---

## Learning objectives

By the end of this chapter you will be able to:

1. Explain context windows, tokens, and instruction-following using ideas you already know from software engineering.
2. Say what causes hallucination, and use 3 concrete techniques to reduce it.
3. Tell the difference between a **prompting failure** (your input was unclear) and a **model capability failure** (the task is genuinely too hard).

---

## Key concepts

Six ideas. Each one gets a plain definition, an analogy to something you already know, and why it matters in practice.

### Token

**Plain definition:** The model's unit of text. Roughly ¾ of a word in English.

**Analogy:** Like a buffer's smallest addressable unit. Everything the model reads or writes is counted in tokens — and billed in tokens.

**Why ¾ of a word, not one word?** Because tokenization splits on subword pieces, not on spaces. Common words are usually one token. Rare words get split into several. `"unbelievable"` might be three tokens: `un` + `believ` + `able`.

**Why it matters:** When someone says "the context window is 200,000 tokens," that is roughly 150,000 words. Useful to know when you are about to paste a very large file.

### Context window

**Plain definition:** The total tokens the model can see at once — your input plus its output, together.

**Analogy:** A function's local scope. Anything outside it does not exist.

**Why it matters:** This is the one that catches people. The model cannot see your repo. It cannot see the file you *meant* to paste. It cannot see the conversation you had yesterday in a different session.

If it is not in the context window, **it does not exist to the model** — no matter how obvious it seems to you.

Asha's bug this morning was exactly this. The config file was obvious to her. It was outside the window, so to the model it was not just unknown, it was *absent* — and absence gets filled with a guess.

### Instruction-following

**Plain definition:** The model does what you literally asked, not what you meant.

**Analogy:** A very literal junior engineer. Not a mind reader.

**The key difference from a real junior:** a human junior will usually come back and ask, "when you said 'the config,' did you mean the YAML file or the .env file?" The model, by default, **does not ask.** It picks the more common one and continues.

**Why it matters:** Ambiguity does not produce an error. It produces a confident answer to a slightly different question than the one you asked. You can make it ask — but only if you tell it to (see Prompt #2 below).

### Hallucination

**Plain definition:** Confident, fluent output that is not grounded in your context or in verifiable fact.

**What it is not:** The model "lying." There is no intent.

**Analogy:** Autocomplete finishing a word you did not mean. Your phone suggests "duck" because it is the most common completion. It is not deceiving you — it is completing a pattern with the information it has.

The model does the same thing at a much larger scale. Missing config file? It completes the pattern using config files it saw in training. The output *sounds* right because pattern-completion is exactly what it is good at.

**Why this framing matters:** If you think of hallucination as "the AI being unreliable," there is nothing to do about it except distrust the tool. If you think of it as "pattern completion in the absence of grounding," you know the fix: **supply the grounding.**

### Grounding

**Plain definition:** Giving the model the actual source material — the real code, the real docs, the real data — instead of relying on what it remembers from training.

**Why it matters:** This is the single highest-leverage anti-hallucination technique. Not clever wording. Not asking it to "be accurate." Just: paste the actual thing.

Training memory is fuzzy and possibly out of date. Your pasted file is exact and current.

### Temperature (determinism)

**Plain definition:** How much randomness is allowed when the model picks each next word.

**Lower temperature:** more repeatable. Ask twice, get nearly the same answer. Good for code, data extraction, classification.

**Higher temperature:** more varied. Ask twice, get two different answers. Good for brainstorming, naming things, generating options.

**Why it matters:** Variance is not always a bug. If you are generating 10 product name ideas, you *want* variety. If you are extracting a date from an invoice, you do not.

---

## Example prompts (6)

### 1. Context window stress test

**Purpose:** Feel the edge of the context window yourself, instead of trusting a number in the docs.

```
I'm going to paste a large file below. First, tell me you've received it
in full by quoting the exact last line. Then answer: [question about the
file]. If you cannot see the whole file, say so explicitly rather than
guessing.
[paste large file]
```

**Why it works:** It makes truncation **visible**.

This matters a lot. A model that quietly answers about a file it only half-received is much more dangerous than one that admits it got cut off. Asking it to quote the last line is a cheap way to verify the whole thing arrived.

### 2. Ambiguity surfacing prompt

**Purpose:** Makes hidden assumptions visible before the model acts on them.

```
Before answering, list every assumption you'd have to make to complete
this task: [task]. Don't answer yet — just the assumptions, so I can
confirm or correct them.
```

**Why it works:** Remember that the model does not ask clarifying questions by default. This prompt turns that default off.

It converts silent guessing into a checkable list. If Asha had run this yesterday, the model would have said something like *"I am assuming the config flag is defined in a standard config file, which I have not seen"* — and she would have caught it in five seconds.

### 3. Grounding-enforced prompt

**Purpose:** The main hallucination-reduction pattern. Learn this one properly.

```
Answer using ONLY the information in the context below. If the answer
isn't in the context, respond exactly with "Not found in provided
context" — do not use outside knowledge or guess.

Context:
[paste source material]

Question: [question]
```

**Why it works:** It does two things at once.

First, it restricts the model to your material. Second — and this part is easy to miss — **it gives the model a safe way to fail.**

Without an explicit "say this if you do not know," the model has no good option. Every path leads to producing *some* answer. Giving it an exact phrase to return makes "I do not know" the easy choice instead of an awkward one.

### 4. Capability-vs-prompting diagnostic

**Purpose:** Tells you whether a bad answer is your fault or a real limitation.

```
I asked you [original prompt] and got [paste answer, note what's wrong].
Was the issue likely that my prompt was ambiguous or under-specified, or
is this close to the limit of what you can reliably do with the
information given? Be honest, don't just apologize and retry the same way.
```

**Why it works:** These two failures need completely different responses.

A **prompting failure** means rewrite the prompt — add context, add constraints, name the output format. A **capability failure** means the prompt is fine and you need a different approach entirely (break the task into smaller steps, or do this part by hand).

Retrying a prompt that failed for capability reasons just wastes time. This prompt tells you which situation you are in.

### 5. Token-budget-aware summarization prompt

**Purpose:** Handles content too large for one context window, without losing what matters.

```
Summarize the following in under [N] words, preserving: [list the 2-3
things that must not be lost — e.g., function signatures, error codes,
dates]. Everything else can be compressed or dropped.
[paste content]
```

**Why it works:** Generic "summarize this" shortens everything evenly — including the one detail you needed.

Naming what must survive directs the compression. The model drops the prose and keeps the error codes, instead of the other way round.

### 6. Determinism-check prompt

**Purpose:** Shows you, on your actual task, whether variance matters.

```
Answer this twice, independently, as if starting fresh each time: [task].
Then compare your two answers — where did they differ, and does that
variance matter for this use case?
```

**Why it works:** "Temperature" is abstract until you see two different answers to your own question side by side. Then it is obvious whether you need low variance or high.

---

## Lab exercise (step-by-step)

The goal here is to make hallucination happen **on purpose**, under controlled conditions. Once you have seen it on command, it stops feeling random.

1. Pick a real file from your codebase, at least 200 lines long.

2. Ask a question about a detail near the **end** of the file, using Prompt #1. Check whether the model confirms it received the whole thing.

3. Now ask a question the file does **not** answer — something genuinely outside its scope. Use Prompt #3's grounding pattern. You should get "Not found in provided context."

4. Ask that same out-of-scope question **without** the grounding constraint. Just ask it plainly.

5. Compare steps 3 and 4.

6. Take a prompt that gave you a wrong answer sometime in the past week. Run Prompt #4 against it. Write down the diagnosis.

---

## Expected outputs

```
Step 3 (grounded):
  "Not found in provided context."

Step 4 (ungrounded):
  A fluent, confident, incorrect answer. Usually it references something
  that sounds plausible but does not exist in your actual file.

Step 5 (the lesson):
  Same model. Same question. Same file. The only difference was one
  sentence of constraint — and that sentence decided whether you got
  an honest "I don't know" or an invented answer.

Step 6 diagnosis example:
  "Prompting issue. I said 'the config' but never said which file.
  There are two. The model picked the more common pattern from its
  training data instead of asking me which one I meant."
```

The point of this lab is **not** to prove the model is bad. It is to show that hallucination is a predictable consequence of missing grounding — something you control — rather than random unreliability you have to live with.

---

## Reflection questions

1. Think of the last wrong answer you got from an LLM. Was it a grounding problem (missing context), an ambiguity problem (unclear ask), or a real capability limit? How would you tell faster next time?
2. Where do you currently rely on the model's memory of a library or framework, instead of pasting your actual version and config? What could go wrong there?
3. Is there a task where you actually *want* high variance? What is it?

---

## Further reading

- Provider documentation on context windows and tokenization *(placeholder link)*
- Research on hallucination causes and mitigation *(placeholder link)*
- Next: [`chapter-03-prompt-design-patterns.md`](./chapter-03-prompt-design-patterns.md) — turning these mental models into repeatable prompt structures

---

## Quiz (5 MCQs)

**1. What is the single highest-leverage way to reduce hallucination?**
- A) Setting temperature to zero
- B) Grounding — pasting the actual source material instead of relying on training memory
- C) Asking the model to double-check itself
- D) Writing a longer prompt

> **Answer: B.**

**2. Why is a token roughly ¾ of a word rather than exactly one word?**
- A) It is a marketing simplification with no technical basis
- B) Tokenization splits on subword pieces, punctuation, and whitespace — not strictly on words
- C) Because only English is supported
- D) Tokens are always exactly 4 characters

> **Answer: B.**

**3. What does "instruction-following" mean here?**
- A) The model always does what you meant, not just what you said
- B) The model does what you literally asked, and resolves ambiguity by guessing rather than asking
- C) The model refuses ambiguous instructions
- D) It is another word for hallucination

> **Answer: B.**

**4. In the lab, what does asking an out-of-scope question *without* the grounding constraint show you?**
- A) That the model always refuses to answer
- B) That hallucination can be triggered reliably by removing a grounding constraint — it is not random bad luck
- C) That context windows do not matter
- D) That temperature has no effect

> **Answer: B.**

**5. When is higher temperature the right choice?**
- A) Never — always use zero
- B) For brainstorming, where varied output is the point
- C) Only for code generation
- D) Only when grounding is unavailable

> **Answer: B.**

---

← [Chapter 1 — Assumptions](./chapter-01-assumptions.md) · [Learning path](./learning-path.md) · Next: [Chapter 3 — Prompt Design Patterns](./chapter-03-prompt-design-patterns.md)
