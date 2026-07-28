# Phase-Planning Checklist

← [Back to README](../README.md) · See it explained: [Chapter 4 — Parallel vs. Pipeline](../tutorial/04-parallel-vs-pipeline.md)

Fill this in **before** writing any workflow code. It forces the two decisions that matter most. Do you need this at all? What shape should it be? Answer both before you're deep enough into the syntax to stop questioning either one.

---

## Step 1 — Does this genuinely need a workflow?

**The task:** _______________________________________________

**List the separate pieces of work, if any:**
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

**The honest test ([Chapter 3](../tutorial/03-your-first-workflow.md)):** would ONE focused piece of work, given all the same information, do just as good a job as the pieces above, done separately?

`[ ] Yes — this doesn't need a workflow. Build a skill instead. Stop here.`
`[ ] No — the pieces genuinely need different context, different focus, or a real second opinion. Continue.`

**If no, say specifically why** (this is the sentence you'll want later, when someone asks "why isn't this just one request?"):

_______________________________________________

---

## Step 2 — For each pair of stages, parallel or pipeline?

For every two stages that could theoretically run at the same time, ask this question honestly.

| Stage A | Stage B | Does B need ALL of A's results together before it can start? | Choice |
|---|---|---|---|
| | | Yes / No | Parallel (barrier) / Pipeline |
| | | Yes / No | Parallel (barrier) / Pipeline |
| | | Yes / No | Parallel (barrier) / Pipeline |

**Default is pipeline.** Only mark "Parallel (barrier)" if you wrote a real "Yes." You also need to be able to name the specific reason — deduplication across everything, an early-exit decision, or a genuine comparison across all items. See [Chapter 4](../tutorial/04-parallel-vs-pipeline.md) if you're not sure.

**Named reason for any barrier above:**
```
_______________________________________________
```

---

## Step 3 — Does anything here need verification?

**Does any stage produce a "finding" or claim that would be acted on, trusted, or shown to someone as fact?**

`[ ] Yes — plan a verification stage (see Chapter 5)`
`[ ] No — skip this step`

**If yes, write the verification instruction now, using the "look for a reason this is WRONG" wording — not "confirm this is right":**

```
_______________________________________________
```

---

## Step 4 — Is there any nested orchestration?

**Does any stage itself contain a parallel() or pipeline() call — orchestration inside orchestration?**

`[ ] No — skip this step`
`[ ] Yes — do the real multiplication arithmetic below`

```
Outer stage runs across:     _____ items
Inner orchestration spawns:  _____ pieces of work per item
Real total:                  _____ × _____ = _____ pieces of work
```

**Is that real total genuinely acceptable?** If not, what's your explicit cap, and what happens when an input exceeds it? (See [Chapter 9](../tutorial/09-governance-and-capstone.md) for the pattern.)

```
Cap: _______   Fallback behaviour when exceeded: _______________________
```

---

## Step 5 — Sketch the phases

Now, and only now, sketch the actual `meta.phases` list:

```
phase("_______________")   — [what happens here]
phase("_______________")   — [what happens here]
```

You're ready to write the actual script once every step above has a real, honest answer — not a placeholder you're planning to fill in later.

---

← [Back to README](../README.md) · Full context: [Chapter 4](../tutorial/04-parallel-vs-pipeline.md)
