# Chapter 2 — Anatomy of an Agent

← [Chapter 1 — What Is an Agent?](01-what-is-an-agent.md) · [Learning path](../learning-path.md) · Next: [Chapter 3 — Your First Agent](03-your-first-agent.md)

---

## Where you left off

You understand the idea: a goal and a loop, instead of a fixed plan. Rahul hands you a real agent script and asks you to read it before he explains anything. You get the general shape — there's clearly a goal, and clearly some kind of repeating loop — but you can't yet say, with confidence, what decides what happens on the *second* time through that loop, or what would ever make it stop.

---

## What you'll learn

1. The four parts every agent has: goal, tools, loop, stopping condition.
2. What a "tool" actually is, and how it's different from a workflow's `agent()` call.
3. How to read a real agent script and predict what it will do on two different inputs.

---

## The lesson

### The four parts, plainly

Every agent — no matter what it's investigating — has exactly these four parts.

**1. A goal.** Not a plan — a description of what "done" looks like. "Find out why report totals are sometimes wrong" is a goal. "First check the aggregation code, then check the cache, then check the logs" is a plan, and writing it that specifically defeats the entire point of using an agent instead of a workflow.

**2. A set of tools.** The actual actions the agent is allowed to take — read a file, run a query, search logs, run a test. Each tool has a name and a description, the same way a skill's trigger description matters — the agent picks a tool based on that description, so a vague or misleading one leads to a wrong pick. [Chapter 4](04-tools-and-grounding.md) is entirely about this.

**3. A loop.** On each turn: look at everything learned so far, decide the single most useful next thing to do, do it, and add the result to what's known. Then loop again — with that turn's result now part of what's known, which is exactly why the second turn can do something nobody could have written down before the first turn ran.

**4. A stopping condition.** What tells the loop to stop — reaching the goal, running out of a turn budget, or a real risk that it's going in circles without making progress. Every agent needs one; [Chapter 5](05-stopping-conditions-and-budgets.md) is entirely about why.

### A real agent, as pseudocode

The shape below is the same kind of pseudocode you read in AI-Workflows — meant to be understood, not copy-pasted into a specific tool without adapting the exact syntax.

```javascript
meta = {
  name: "reporting-discrepancy-investigator",
  version: "1.0.0",
  goal: "Find the root cause of intermittent, customer-specific report " +
    "total discrepancies, and confirm it against real log evidence.",
  tools: [
    { name: "read_code", description: "Read a named source file" },
    { name: "search_logs", description: "Search application logs for a " +
      "customer ID and time range" },
    { name: "run_query", description: "Run a read-only query against " +
      "the reporting database" }
  ],
  max_iterations: 8
}

history = []
iteration = 0

while (iteration < meta.max_iterations) {
  // Step 1 — look at everything learned so far
  observation = summarize(history)

  // Step 2 — decide the single most useful next thing to do
  decision = think(meta.goal, observation, meta.tools)

  if (decision.status == "DONE") {
    return decision.conclusion
  }

  // Step 3 — do it, using a real tool
  result = call_tool(decision.tool, decision.args)

  // Step 4 — add it to what's known, then loop again
  history.push({ tool: decision.tool, args: decision.args, result: result })
  iteration++
}

return "Stopped: iteration budget exhausted without reaching the goal"
```

### Reading it the way you'd read a workflow

Compare this shape directly to a workflow's `meta` block. A workflow's `meta.phases` lists every phase that will ever run, in order, before the workflow sees a single real input. This agent's `meta` has no such list — no phases, no fixed sequence. What it has instead is `meta.goal` (what done means) and `meta.tools` (what it's allowed to do), and the actual sequence of actions only exists once you run it, because `think()` decides each one using the result of the one before it.

That's the concrete, code-level version of [Chapter 1](01-what-is-an-agent.md)'s whole point: a workflow's plan exists before the first observation. An agent's plan is built one turn at a time, *because of* each observation.

### What `think()` is actually doing

`think()` is where the agent decides its next move — and it's worth being precise about what that decision is based on. It gets three things: the goal (so it knows what it's working toward), the observation (everything learned in every prior turn, not just the last one), and the list of available tools (so it can only pick from things it's actually allowed to do). It returns either `{status: "DONE", conclusion: ...}` when the goal has genuinely been reached, or `{status: "CONTINUE", tool: ..., args: ...}` naming the next single action to take.

This is the one call in the whole loop that has no fixed answer written anywhere — which is exactly why it's the part that makes this an agent and not a workflow.

### Predicting behavior on two different inputs

Here's the test Rahul actually wanted you to pass. Given the investigator above, on **input A** (a customer whose logs immediately show a stale-cache timestamp) it might reach `DONE` in 2 turns — `search_logs`, see the smoking gun, done. On **input B** (a customer where the first two tool calls come back clean) it might take all 8 turns, trying `read_code` on three different files before anything points anywhere useful, and possibly hit `max_iterations` without a confirmed answer at all.

**Both of those are the same agent, correctly running its own loop.** A workflow given the same two inputs runs the exact same phases, in the exact same order, every time — that predictability is a workflow's whole value. An agent given two different inputs can, correctly, take a genuinely different number of turns and a genuinely different path. That's not a bug to fix. It's the entire reason this tool exists.

---

## Try it yourself

Take the investigator script above. Without running it, write down: what would you expect it to do differently if `search_logs` came back completely empty on turn 1, versus if it immediately found a matching stale-timestamp entry? Then check your prediction against what `think()`'s job description says it should do.

---

## What's still missing

You can read an agent now. You still haven't built one — and Rahul's next question, the same one he asked at the start of AI-Workflows Chapter 3, is going to be "stop reading examples, build one." [Chapter 3](03-your-first-agent.md) is exactly that, including the same honest lesson about building something that turns out not to need the tool you just learned.

---

← [Chapter 1 — What Is an Agent?](01-what-is-an-agent.md) · [Learning path](../learning-path.md) · Next: [Chapter 3 — Your First Agent](03-your-first-agent.md)
