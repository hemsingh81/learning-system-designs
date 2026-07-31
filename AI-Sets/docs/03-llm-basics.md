# 03 — LLM basics: tokens, prompts, temperature, context window, cost

You don't need a deep AI background to use an LLM correctly — you need to
understand five things. This page covers all five, with backend-engineer
analogies.

## 1. What an LLM actually does

A large language model (LLM) reads text and predicts the next chunk of
text, one piece at a time, based on everything before it. That's it.
There is no database of facts it "looks up" — it generates text based on
patterns learned during training. This is WHY it can confidently say
something false (a **hallucination**) — it's not "lying", it's predicting
plausible-sounding text, and plausible isn't always true.

**Backend takeaway:** never trust raw LLM output the way you'd trust a
database read. Treat it like **untrusted user input** — validate it (see
`docs/04-prompting-guide.md` and the `Skill` base class in Milestone 2).

## 2. Tokens

A **token** is roughly a word or word-piece. "unbelievable" might be one
token or split into "un" + "believable" — you don't control this exactly,
but you can estimate: **~4 characters per token** in English is a
reasonable rule of thumb.

**Why you care:** every model call costs money based on tokens IN
(your prompt + conversation history) and tokens OUT (the response). See
`src/aisets/llm/usage.py` for how this project tracks that.

## 3. The context window

The **context window** is the maximum number of tokens a model can see at
once — your whole conversation history, plus the current prompt, plus
whatever it's about to generate. Claude models today support very large
context windows (hundreds of thousands of tokens), but "large" is not
"infinite", and every extra token costs money and (a little) latency.

**Backend analogy:** think of it like a fixed-size request payload limit,
except it's shared between your input AND the model's output, and it also
grows as a conversation goes on (each turn adds to the total). This is
exactly why the Agent's Memory module (Milestone 5) has to decide what to
keep and what to drop, the same way you'd design a bounded in-memory cache.

## 4. Temperature

**Temperature** controls how "creative" vs. "consistent" the output is.
- Low temperature (near 0) → the model tends to pick its most likely next
  token every time → more consistent, more predictable output.
- Higher temperature → more variety, more surprising word choices.

**This project defaults to low temperature everywhere** (see every skill
in Milestone 2), because we want reliable, testable behavior — not
creative writing. If you were building a marketing-copy generator, you'd
want it higher; for "classify this ticket into one of 5 categories", you
want it low.

## 5. Prompts are contracts

A **prompt** is the text you send the model: instructions + context + the
actual question. Think of a prompt exactly like an API request body —
the clearer and more constrained it is, the more reliable the response.
See [docs/04-prompting-guide.md](04-prompting-guide.md) for the full
technique this project uses (a fixed template + a required output schema).

## Cost, concretely

See [docs/07-cost-and-latency.md](07-cost-and-latency.md) for real numbers
from this project's examples. The short version: `FakeLLM` costs $0 always.
`ClaudeLLM` with a small/cheap model on a short prompt typically costs a
small fraction of a cent per call — but it adds up across an agent's many
tool-call turns, which is exactly why Milestone 6 builds a hard budget cap.

## Try it yourself

```powershell
.\scripts\run-example.ps1 01_skill_hello
```

Open `examples\01_skill_hello.py` (Milestone 2) side by side and watch how
the printed output changes when you switch `.env`'s `LLM_BACKEND` from
`fake` to `claude` — same code, different backend, real tokens now being
spent.
