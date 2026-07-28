# Goal-and-Boundary Worksheet

← [Back to README](../README.md) · See it explained: [Chapter 1 — What Is an Agent?](../tutorial/01-what-is-an-agent.md)

Fill this in **before** writing any agent code. It forces the two decisions that matter most for an agent, specifically — do you actually need one, and what is it allowed to do — before you're deep enough into the loop to stop questioning either one.

---

## Step 1 — Does this genuinely need an agent?

**The task:** _______________________________________________

**Write down what you believe the first 2-3 steps would be:**
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

**The honest test ([Chapter 3](../tutorial/03-your-first-agent.md)):** at each step, could you have written down the next action in advance, the same way every time, regardless of what the previous step found?

`[ ] Yes — every step is knowable in advance. This doesn't need an agent. Build a workflow instead. Stop here.`
`[ ] No — the next step genuinely depends on what the last one reveals. Continue.`

**If no, say specifically why** (this is the sentence you'll want later, when someone asks "why isn't this just a workflow with more phases?"):

_______________________________________________

---

## Step 2 — Define the goal, not a plan

**Write the goal as a description of "done" — not a sequence of steps:**

```
GOAL: _______________________________________________
```

**Check it isn't secretly a plan in disguise.** Does it contain words like "first," "then," "after that"? If so, rewrite it as a destination, not a route.

---

## Step 3 — List every tool, and its access level

| Tool name | What it does | READ_ONLY or ACTION_TAKING | If ACTION_TAKING: reversible? |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

**For every tool, write its description so it rules out anything it could be confused with** ([Chapter 4](../tutorial/04-tools-and-grounding.md)):

```
_______________________________________________
```

---

## Step 4 — For every ACTION_TAKING, non-reversible tool

`[ ] No such tool — skip this step`
`[ ] Yes — this tool needs requires_approval: true (see Chapter 9)`

**What evidence would a human need to approve or reject it in seconds, without re-investigating?**

```
_______________________________________________
```

---

## Step 5 — Set the stopping condition

```
max_iterations:  _____
```

**Write the honest "I couldn't find this" exit message** ([Chapter 5](../tutorial/05-stopping-conditions-and-budgets.md)) — what should the agent say if it genuinely exhausts every tool without reaching the goal?

```
_______________________________________________
```

---

You're ready to write the actual script once every step above has a real, honest answer — not a placeholder you're planning to fill in later.

---

← [Back to README](../README.md) · Full context: [Chapter 1](../tutorial/01-what-is-an-agent.md)
