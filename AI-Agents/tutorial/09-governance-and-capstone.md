# Chapter 9 — Governance and Capstone

← [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md) · [Learning path](../learning-path.md) · Next: [Chapter 10 — The Execution Lifecycle →](10-lifecycle-of-execution.md)

---

## Where you left off

Ananya asks you to sit in on a review, again — same as your last chapter in AI-Skills, and your last chapter in AI-Workflows, but this time it's an agent.

Her exploratory-testing agent got a new tool a few weeks back: `quarantine_flaky_test`, which marks a test as skipped when the agent's investigation concludes it's flaky rather than a real failure. It's a genuinely useful capability — flaky tests waste real engineering time, and Ananya's agent had gotten good at spotting the pattern.

Last Tuesday, it quarantined a test in the checkout flow. The agent's reasoning wasn't unreasonable — the test had an intermittent failure pattern that looked exactly like every other flaky test it had correctly identified before. It wasn't flaky. It was catching a real, new regression, introduced two days earlier, that nobody had caught yet. The regression sat live for two more days, silently, because the one thing that would have caught it had been quietly turned off — by an agent, acting entirely within its own tool access, doing exactly what its goal told it to do.

Nobody noticed until a customer did.

---

## What you'll learn

1. Why an agent with action-taking tools can do something no skill or workflow ever could: take a real, irreversible action nobody explicitly approved.
2. How to build a real human-approval gate around irreversible actions, without making the agent useless.
3. The complete checklist — thought process to sharing — tying together everything from Chapters 1 through 8.

---

## The lesson

### Why this is the risk unique to agents

A skill can't do this — it does one focused thing, in one flow of reasoning, and its output is a response, not an action taken on the world. A workflow can't do this either, not because a workflow can't call action-taking tools, but because every action a workflow will ever take is decided **before it runs**, which means a human reviewing the workflow's script *already* reviewed and approved every action it could possibly take, before the first run.

An agent's actions are decided **during** the run, using information that didn't exist until that point. That's the entire value of the loop — and it's exactly what makes it possible for an agent to take a real action that nobody, at any point, specifically looked at and approved. **The same freedom that makes an agent able to investigate something genuinely unknown is the freedom that makes an unapproved, irreversible action possible.** This isn't a coincidence you can design around — it's the direct cost of what an agent is for, the same way AI-Workflows' cost-multiplication risk was the direct cost of what a workflow is for.

### Why Ananya's mistake is easy to miss

Look at each piece on its own. A tool that quarantines a flaky test — reasonable, saves real time, exactly [Chapter 4](04-tools-and-grounding.md)'s idea of giving an agent a useful action to take. A `think()` loop that concludes "this matches the flaky pattern" based on real evidence — reasonable, exactly the grounding [Chapter 4](04-tools-and-grounding.md) asked for. The agent wasn't hallucinating, wasn't confused about which tool to use, wasn't circling. **Every individual piece worked correctly.**

**The problem only exists at the point where a genuinely irreversible action — turning off a test that might be the only thing watching for a specific regression — was allowed to happen automatically, based on the agent's own conclusion, with nobody checking it first.** This is worth stating plainly, because it generalises past this one example: **whenever an agent's tool set includes an action that is hard or impossible to undo — deleting something, disabling a safeguard, sending something externally, changing production state — the risk isn't that the agent will reason badly. It's that even correct-sounding reasoning can be wrong, and an irreversible action doesn't leave room to notice that before the cost lands.**

### The fix: a real human-approval gate

The honest fix isn't "make the agent smarter" — you already learned in Chapter 4 that even grounded, evidence-based conclusions can be wrong. The fix is a real gate that exists in the agent's own structure, not in a hope that its reasoning will always be right.

```javascript
meta = {
  name: "flaky-test-triage-agent",
  goal: "Investigate failing tests and correctly identify genuinely " +
    "flaky ones for quarantine.",
  tools: [
    { name: "read_test_history", access: "READ_ONLY" },
    { name: "run_test_n_times", access: "READ_ONLY" },
    { name: "quarantine_flaky_test", access: "ACTION_TAKING",
      reversible: false,     // an explicit, visible flag
      requires_approval: true }
  ]
}

if (decision.status == "DONE" && decision.action) {
  tool_definition = find_tool(meta.tools, decision.action.tool)

  if (tool_definition.requires_approval) {
    // The agent stops here. It does NOT call the tool itself.
    return {
      status: "PENDING_APPROVAL",
      proposed_action: decision.action,
      evidence: decision.evidence,
      message: "This agent has concluded '" + decision.conclusion +
        "' and proposes calling " + decision.action.tool + ". This is " +
        "an irreversible action. Review the evidence above and approve " +
        "or reject before it runs."
    }
  }

  // Only reversible, non-gated actions execute without stopping first.
  result = call_tool(decision.action.tool, decision.action.args)
  return result
}
```

Three things worth noticing about this fix.

**The flag lives on the tool, not on the agent as a whole.** `read_test_history` and `run_test_n_times` still run freely — they're read-only, nothing about them needs a human in the loop. Only `quarantine_flaky_test` — the one action that's genuinely hard to undo — carries `requires_approval: true`. A gate applied to the whole agent, instead of the specific dangerous action, would make the useful, safe parts of the agent slower for no reason.

**The agent still does the hard part.** It still investigates, still reaches a grounded conclusion, still cites its evidence. What changes is the very last step — instead of *acting* on its own conclusion, it *proposes* the action and stops, with everything a human needs to make a fast, informed call already assembled. This is the agent equivalent of AI-Workflows' loud, explained fallback: the gate doesn't silently block the action, it explains exactly what's about to happen and why, so a human can approve in seconds rather than having to re-investigate from scratch.

**Reversible actions don't need this overhead.** A tool that leaves a comment, creates a draft PR, or writes a report can run freely — undoing a wrong comment costs nothing. The line isn't "does this agent take actions." It's specifically: **can this particular action be undone without real cost if the agent's conclusion turns out to be wrong?**

### The three questions for any agent, before it ships

**1. Does this agent have any action-taking tools?** If every tool is read-only, per [Chapter 8](08-packaging-and-sharing.md), this chapter's specific risk doesn't apply — skip to the checklist below.

**2. For each action-taking tool: is it genuinely, cheaply reversible?** A draft comment is. A quarantined test that might be the only thing watching for a real regression is not. Be honest here — "probably fine" is not the same as "cheaply reversible."

**3. Does every non-reversible action require a real human approval step before it executes — one that shows the evidence, not just asks "proceed?"** A gate that just asks yes/no, with no evidence attached, forces the human to either blindly approve or re-do the whole investigation themselves — neither is a real safeguard.

### The pre-distribution safety review, extended

Everything from AI-Workflows' checklist still applies — is this genuinely needed, is the tool selection tested, are conclusions grounded, is there a real stopping condition. Add these, specific to what's new about an agent with real tool access:

- [ ] **Is every tool labeled `READ_ONLY` or `ACTION_TAKING`**, visibly, in the agent's own definition?
- [ ] **Does every `ACTION_TAKING` tool have an honest `reversible` flag** — not assumed, actually thought through?
- [ ] **Does every non-reversible action require human approval before it executes**, with the evidence attached, not just a yes/no prompt?
- [ ] **Has the approval gate been tested** — confirmed the agent actually stops and waits, rather than proceeding past it?
- [ ] **Is the agent's tool access documented somewhere visible**, so a teammate can answer "what can this do without asking me" without reading the source?

### The full journey, in one checklist

**Thought process (Chapters 1, 3, 6)**
- [ ] Does the right next step genuinely depend on what gets discovered — not knowable in advance? (Chapter 1)
- [ ] Would a fixed plan (a workflow) do just as well? If so, this doesn't need to be an agent. (Chapter 3)
- [ ] Checked against the full decision framework — agent, or actually a skill, workflow, subagent, or hook? (Chapter 6)

**Writing (Chapters 2, 4)**
- [ ] Does it follow the standard shape — goal, tools, loop, stopping condition? (Chapter 2)
- [ ] Do tool descriptions disambiguate from anything they could plausibly be confused with? (Chapter 4)
- [ ] Does every conclusion require real cited evidence, not an ungrounded guess? (Chapter 4)

**Stopping (Chapter 5)**
- [ ] Is there a real, checked iteration and cost budget?
- [ ] Does the loop detect and refuse silent exact repeats?
- [ ] Is there an honest "couldn't find this" exit, separate from silently exhausting the budget?

**Testing (Chapter 7)**
- [ ] Tested for goal-reached across multiple real, genuinely different paths — not one lucky run?
- [ ] Tested the planted-overlap, planted-ungrounded, planted-unsolvable, and planted-repeat cases?

**Sharing (Chapter 8)**
- [ ] Are all tools labeled `READ_ONLY` / `ACTION_TAKING`, and is that visible without reading the code?
- [ ] Does it have a real version number, and does adding any tool bump it correctly?

**Governance (Chapter 9)**
- [ ] Run the extended pre-distribution safety review above, every time any action-taking tool is involved.

### Closing the loop

Go back to [`00-the-story.md`](../00-the-story.md) for a second, to "what done looks like."

You've built an agent from nothing, watched it fail to earn its own overhead on a task that had a fixed plan the whole time, learned the one thing that decides whether an agent is even the right tool, built one that picks correctly and grounds its answers, taught it to stop honestly instead of circling forever, and now know exactly what stops it from quietly turning off the one thing that would have caught a real regression. Rahul's original skill became a stage inside a workflow. That workflow's fixed five angles are about to become one agent's adaptive choice, in [Case Study 4](../case-studies/04-code-review-agent/README.md) — the last piece of this whole three-part story.

### Where this leaves you

You now have three tools, and — more importantly — you know exactly when each one is the right one. A skill for one focused, recognisable, repeated request. A workflow for a fixed plan that coordinates several. An agent for a goal where the right steps can't be known until you start looking, with a real gate around anything it does that can't be undone.

None of these replaced the others. Rahul's `/code-review` skill is still running, unchanged, inside the five-angle workflow. That workflow is still running, unchanged, as one option a review agent can reach for. Nothing in this three-part story got thrown away — each tool became a trusted piece inside the next one up.

---

## Try it yourself

Run your own agent — the one you've been building since Chapter 3 — through the complete checklist above, honestly, top to bottom. If it has any action-taking tool at all, write down, specifically, whether it's genuinely reversible, even if you're confident it's fine. Confidence isn't the same as a written-down answer, and this whole chapter exists because that gap is exactly where Ananya's mistake lived.

---

## What's still missing

Nothing, for this one agent. Same as your last two capstones — you've done the whole thing, start to end.

Before the case studies, one bonus chapter worth reading: [Chapter 10 — The Execution Lifecycle](10-lifecycle-of-execution.md) traces a real agent's run turn by turn, including exactly what happens at its repeat guard, grounding gate, and approval gate.

Read the [case studies](../case-studies/README.md) next — four different teams, four genuinely different investigations, including the one where Rahul's five-angle workflow becomes one agent's adaptive choice.

**Then, when you're ready:** see [`docs/how-the-three-connect.md`](../../docs/how-the-three-connect.md) — how Skills, Workflows, and Agents fit together as one continuous ladder, start to finish.

---

← [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md) · [Learning path](../learning-path.md) · Next: [Chapter 10 — The Execution Lifecycle →](10-lifecycle-of-execution.md)
