# Chapter 5 — Stopping Conditions and Budgets

← [Chapter 4 — Tools and Grounding](04-tools-and-grounding.md) · [Learning path](../learning-path.md) · Next: [Chapter 6 — Agents vs. Other Tools](06-agents-vs-other-tools.md)

---

## Where you left off

Your config-discrepancy agent picks the right tool now, and grounds its conclusions in real evidence. Rahul gives you one more case to run it against — a genuinely unsolvable one, on purpose, where the real cause turns out to be a third-party vendor's outage that none of the agent's tools can see.

The agent doesn't say "I can't find this." It keeps going. Turn 4 checks feature flags again. Turn 6 checks environment variables again — the same ones it already checked on turn 1. By turn 8, it's re-reading the same config file for the third time, still hoping the next look will reveal something the last two didn't.

---

## What you'll learn

1. Why an agent, unlike a workflow, doesn't naturally know when to stop.
2. How to set a real iteration and cost budget that catches this before it's expensive.
3. How to detect the specific failure of going in circles, not just running long.

---

## The lesson

### Why this is the risk that's unique to agents

A workflow can't do this. Its phases are a fixed list — it runs each one once, in order, and then it's done, by construction. There's no version of a workflow that "keeps going" past its last phase, because there's no mechanism for it to decide to add another one.

An agent's whole value, as you learned in [Chapter 1](01-what-is-an-agent.md), is deciding its own next step based on what it finds. That's exactly the feature that makes "just keep trying" a genuinely available option on every single turn — and nothing about the loop itself tells it when trying again has stopped being useful. **The same freedom that makes an agent powerful is the one that makes it capable of never stopping on its own.** This isn't a bug you can design away by writing a smarter `think()`. It's a direct consequence of what an agent is for — the same way AI-Workflows' nested-cost risk was a direct consequence of what a workflow is for.

### The two ways an agent fails to stop

**Running long without looping** — genuinely making slow progress, trying new things each turn, just needing more turns than expected. This isn't actually a failure; it's a hard problem taking a hard number of turns.

**Going in circles** — re-trying something already tried, with an already-known result, hoping for a different outcome. This *is* a failure, and it's the one your CI-log-style story above shows: turn 6 re-checked exactly what turn 1 already checked, and got exactly the same answer, because nothing about the world had changed between them.

Telling these apart matters, because the fix for each is different.

### Fix 1 — a hard iteration budget

The simplest, non-negotiable limit: a maximum number of turns, checked every single time, no exceptions.

```javascript
meta = {
  name: "config-discrepancy-investigator",
  goal: "...",
  tools: [ ... ],
  max_iterations: 8   // a real, explicit, checkable number
}

while (iteration < meta.max_iterations) {
  // ... the loop from Chapter 2 ...
  iteration++
}

// Falls through here if the budget runs out without reaching DONE —
// never silently continues past this point.
return "Stopped: reached the " + meta.max_iterations + "-iteration " +
  "budget without confirming a root cause. Investigated: " +
  summarize_attempts(history)
```

This alone stops the *worst* case — genuinely unbounded running — but it doesn't catch the circling failure early. An 8-turn budget still lets an agent spend turns 3 through 8 re-checking the same three things it already ruled out on turns 1 and 2.

### Fix 2 — loop detection

Catch the circling failure directly, by noticing when a turn is about to repeat a tool call it already made, with the same arguments, that already returned a result:

```javascript
function is_repeat(decision, history) {
  return history.some(h =>
    h.tool == decision.tool && deep_equal(h.args, decision.args)
  )
}

// Inside the loop, after think() decides the next action:
if (decision.status == "CONTINUE" && is_repeat(decision, history)) {
  // Don't silently allow it — force the decision to account for
  // the fact that this exact check already happened.
  decision = think(meta.goal, observation, meta.tools,
    "Note: you already tried " + decision.tool + " with these exact " +
    "arguments, on turn " + find_turn(decision, history) + ", and got: " +
    find_result(decision, history) + ". Trying it again won't produce a " +
    "new result. Pick something genuinely different, or report that " +
    "you've exhausted what your tools can determine.")
}
```

This doesn't ban repeating a tool — sometimes checking the same thing after time has passed is legitimate (a flag that might have since changed, a log that might have new entries). It bans repeating it **without acknowledging it's a repeat**, which is exactly what turned Rahul's unsolvable test case into eight turns of quiet, expensive circling instead of a fast, honest "I've checked everything my tools can see, and none of it explains this."

### Fix 3 — an honest "I don't know" is a valid stop

The other half of this fix is cultural, not just structural: **a stopping condition needs a real, acceptable outcome for "the goal wasn't reached," not just "the goal was reached" or "ran out of budget."** An agent whose only two exits are "found it" and "silently exhausted its budget" has a real incentive to keep trying rather than admit it can't find an answer with the tools it has. That incentive is baked into how it was built, not into anything it wants.

Here's the fix Rahul's third case actually needed. The unsolvable one — a real third-party outage none of the tools could see — should stop at turn 3 or 4, having established it exhausted everything its tools *could* check. The report should say exactly that: not a report that pretends to have found something, and not eight turns of unexplained repetition either.

```javascript
if (decision.status == "EXHAUSTED") {
  return "Investigated using every available tool: " +
    summarize_attempts(history) +
    ". No root cause found within what these tools can see. This may " +
    "require checking something outside this agent's current tools " +
    "(for example, a third-party vendor's status page)."
}
```

This is the agent equivalent of a workflow's explicit cap-and-fallback from AI-Workflows Chapter 9 — instead of silently scaling past a sensible limit, it fails loudly, with an honest explanation of what was tried and why it stopped.

### The three questions for any agent, before it ships

**1. What is the hard iteration (and cost) budget, and is it a real checked number, not a hope?**

**2. Does the loop detect exact repeats, and force an honest acknowledgment instead of silently trying the same thing again?**

**3. Is there a real, honest "I couldn't find this with what I have" exit — separate from both success and silently running out of budget?**

---

## Try it yourself

Take an agent you've built. Deliberately give it a goal it genuinely cannot reach with its current tools — the way Rahul's third-party-outage case did. Confirm, without the fixes above, how many turns it takes before stopping, and whether it repeats any tool call along the way. Add the iteration budget, the repeat check, and the honest "EXHAUSTED" exit. Re-run it, and confirm it now stops early, with an honest explanation, instead of quietly circling.

---

## What's still missing

You can now build an agent that picks correctly, grounds its answers, and stops honestly. What you haven't done yet is compare it, side by side, against every other tool you know — skill, workflow, subagent, hook — to make sure you're reaching for the right one each time. [Chapter 6](06-agents-vs-other-tools.md) is that comparison.

---

← [Chapter 4 — Tools and Grounding](04-tools-and-grounding.md) · [Learning path](../learning-path.md) · Next: [Chapter 6 — Agents vs. Other Tools](06-agents-vs-other-tools.md)
