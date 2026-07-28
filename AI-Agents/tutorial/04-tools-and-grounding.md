# Chapter 4 — Tools and Grounding

← [Chapter 3 — Your First Agent](03-your-first-agent.md) · [Learning path](../learning-path.md) · Next: [Chapter 5 — Stopping Conditions and Budgets](05-stopping-conditions-and-budgets.md)

This is the most important chapter in this tutorial — the same way parallel-vs-pipeline was the most important chapter in AI-Workflows. Everything else here assumes you've internalized this one.

---

## Where you left off

Your config-discrepancy agent from [Chapter 3](03-your-first-agent.md) works — on the cases you tried it on. Rahul asks you to run it against a new case, one where two of the tools overlap in a way you hadn't noticed. It picks the wrong one. Confidently. It doesn't say "I'm not sure" — it reports a root cause, clearly and completely, and the root cause is wrong.

---

## What you'll learn

1. What actually makes an agent choose one tool over another — and why that choice is only as good as the tool descriptions.
2. What "grounding" means, and the specific failure mode where an agent answers from a guess instead of real evidence.
3. How to write tool descriptions and require evidence so both failures become visible instead of silent.

---

## The lesson

### What a tool actually is

A tool is not just a function. It's three things together: a **name**, a **description** the agent uses to decide *when* to reach for it, and a real action that produces a real result the agent didn't already know. `read_config_files` isn't useful because it exists — it's useful because its description tells `think()` exactly when picking it is the right move, and because calling it returns something genuinely new, not something the agent could have guessed.

This should feel familiar. It's the exact same idea as a skill's trigger description from AI-Skills — the part that decides *whether* a skill gets used at all. A tool's description does the same job, but one level deeper: instead of deciding whether to use an entire capability, it decides which *one* of several available capabilities to reach for, on every single turn of the loop.

### The overlap that broke Rahul's test case

Here's what Rahul's new case actually looked like. Your config-discrepancy agent had two tools:

```javascript
tools: [
  { name: "check_env_vars", description: "List environment variables set " +
    "for a named environment" },
  { name: "check_feature_flags", description: "Check feature flag state " +
    "for a named environment" }
]
```

The new case: `DISCOUNT_CAP` was controlled by a feature flag *named* `discount_cap_override` — but that flag's own description, stored wherever feature flags live, happened to describe it as "an environment-level override for discount behaviour." The agent, reading its own tool list, saw `check_env_vars`'s description — "list environment variables" — and reasonably (from its perspective) decided that sounded like the right tool for something described as an "environment-level override." It called `check_env_vars`, found nothing relevant, and — without a third option pointing anywhere else — reported "no discrepancy found in environment configuration" as its conclusion.

Nothing was broken. `think()` did exactly what it's supposed to do: pick the tool whose description sounds most like the right match for what it's looking for. **The problem was that both tools plausibly matched, and nothing in either description told the agent how to tell them apart.**

### The fix: descriptions that draw the line

The fix isn't a smarter agent. It's a clearer set of tool descriptions — the direct equivalent of AI-Skills' lesson that a vague trigger description is the actual bug, not the thing that failed to trigger correctly.

```javascript
tools: [
  { name: "check_env_vars", description: "List OS-level environment " +
    "variables (things like DATABASE_URL, API_KEY) set for a named " +
    "environment. Does NOT include feature flags, even ones with " +
    "'environment' in their own description — use check_feature_flags " +
    "for those." },
  { name: "check_feature_flags", description: "Check feature flag " +
    "state for a named environment, including flags whose OWN " +
    "description mentions 'environment' or 'override' — flags are a " +
    "separate system from OS environment variables." }
]
```

Notice what changed: each description now explicitly rules out the thing it's most likely to be confused with, by name. That's the general pattern — whenever two tools could plausibly both sound right for the same situation, the fix is to name the confusion directly in both descriptions, not to hope the agent infers the boundary on its own.

### The other failure: grounding

Overlapping tools produce a *wrong* answer. There's a second, quieter failure that produces an *ungrounded* one — a conclusion that was never actually checked against a real tool result at all.

Here's what that looks like. Suppose `think()`, on some turn, reasons: "Discount caps are usually controlled by feature flags in systems like this, so it's probably the `discount_cap_override` flag" — and returns `DONE` with that as the conclusion, **without ever having called `check_feature_flags` to confirm it.** That sentence might even be right. But it was never actually checked. It's a plausible guess wearing the shape of a finding.

**Grounding** means every claim in an agent's conclusion has to trace back to a real tool call that actually happened, with a real result the agent can point to — not a plausible inference dressed up as one. This is the direct cousin of AI-Workflows Chapter 5's lesson about verification: there, the risk was a *reviewer* sounding confident about something wrong. Here, the risk is the agent's own reasoning sounding confident about something it never actually looked up.

### How to enforce grounding structurally

Don't rely on asking the agent nicely to "only report things you've checked." Structure the conclusion so an ungrounded claim is visible on inspection:

```javascript
if (decision.status == "DONE") {
  if (!decision.evidence || decision.evidence.length == 0) {
    // A conclusion with no cited tool-call evidence is a red flag —
    // reject it and force another turn, exactly like verification
    // rejects an unconfirmed finding in AI-Workflows Chapter 5.
    history.push({ note: "Conclusion rejected: no evidence cited. " +
      "Continue investigating." })
    iteration++
    continue
  }
  return decision.conclusion + "\n\nEvidence: " + decision.evidence
}
```

`decision.evidence` here means specific prior tool calls and their actual results — "turn 2, `check_feature_flags`, found `discount_cap_override = true` for staging only" — not a restatement of the conclusion in different words. If `think()` can't point to real evidence for its own claim, that's the signal something was guessed instead of checked, and the loop should keep going instead of accepting it.

### Grounding and tool descriptions are the same underlying lesson

Both failures come from the same root cause: **an agent's reasoning is only as trustworthy as what it's actually built on** — either the description it used to choose a tool, or the tool result it used to reach a conclusion. Get either one wrong, and the agent produces something that looks exactly as confident as a correct answer. That's what makes both failures dangerous: there's no visible difference between a right answer and a wrong one unless you specifically design for evidence and disambiguation.

---

## Try it yourself

Take an agent with at least two tools. Deliberately make their descriptions overlap — the way `check_env_vars` and `check_feature_flags` did before the fix — and run it on a case where the correct tool is the less obvious one. Confirm it picks wrong. Then fix the descriptions the way this chapter did, and confirm it now picks correctly. Separately: add the evidence check above, and confirm a `DONE` result with no cited evidence gets rejected and forces another turn.

---

## What's still missing

You can now build an agent that picks the right tool and grounds its conclusions in real evidence. What you haven't built yet is anything that stops it from running forever — or from confidently going in circles, making no real progress, burning cost the whole time. That's [Chapter 5](05-stopping-conditions-and-budgets.md).

---

← [Chapter 3 — Your First Agent](03-your-first-agent.md) · [Learning path](../learning-path.md) · Next: [Chapter 5 — Stopping Conditions and Budgets](05-stopping-conditions-and-budgets.md)
