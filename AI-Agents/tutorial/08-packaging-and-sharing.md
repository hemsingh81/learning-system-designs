# Chapter 8 — Packaging and Sharing

← [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md) · [Learning path](../learning-path.md) · Next: [Chapter 9 — Governance and Capstone](09-governance-and-capstone.md)

---

## Where you left off

Your config-discrepancy agent is tested and reliable. Vikram wants it — he's got his own flaky-test triage problem, and your investigator's shape looks like exactly what he needs. But before he'll actually run it against his team's systems, he asks a question nobody asked about your workflow: **"What is it actually allowed to do, on its own, without asking me first?"**

You realize you don't have a crisp answer. Your agent reads files, reads logs, runs queries. All read-only, as it happens — but you never wrote that down anywhere, and Vikram has no way to know it without reading your entire tool list and reasoning it out himself.

---

## What you'll learn

1. Why sharing an agent is a bigger trust ask than sharing a workflow, even a well-tested one.
2. How to version and document an agent so a teammate can trust its boundary without reading the source.
3. The extra step, specific to agents, that belongs in every shared agent's documentation.

---

## The lesson

### Why the trust ask is genuinely bigger

A shared workflow is auditable before anyone runs it — its phases are a fixed list, so reading the script *is* knowing exactly what it will do. A shared agent's exact path can't be read in advance, by design — that's the entire point of Chapters 1 through 3. What a teammate *can* know in advance, and what they absolutely need to, is the **boundary**: the full set of tools it has, and specifically, whether any of them can change something instead of just looking at it.

Your config-discrepancy agent happens to be entirely read-only — every one of its three tools only looks at things, never changes them. That's a genuinely different, much safer thing to hand someone than an agent with even one tool that can write, delete, deploy, or notify someone. **Vikram's question wasn't paranoid. It was the exact right question, and it should be answerable from the agent's own documentation, not from reading its code.**

### Read-only vs. action-taking tools — the line that matters most

Before packaging any agent for someone else, sort every one of its tools into one of two categories:

**Read-only** — looks at something, changes nothing. `read_code`, `search_logs`, `run_query` (if the query is genuinely read-only), `check_feature_flags` (checking state, not setting it).

**Action-taking** — changes something in the real world. Writing a file, running a database migration, posting a message, triggering a deploy, closing a ticket.

This distinction should be visible immediately, not something a teammate has to reconstruct by reading every tool's implementation:

```javascript
meta = {
  name: "config-discrepancy-investigator",
  version: "1.0.0",
  goal: "Find why config value DISCOUNT_CAP behaves differently in " +
    "staging vs. production, and confirm the real cause.",
  tools: [
    { name: "read_config_files", access: "READ_ONLY", ... },
    { name: "check_env_vars", access: "READ_ONLY", ... },
    { name: "check_feature_flags", access: "READ_ONLY", ... }
  ],
  // A teammate can answer Vikram's exact question by reading this one
  // line, without reading a single line of the actual tool code.
  can_take_action_without_approval: false
}
```

An agent with even one action-taking tool needs its own, separate answer — which [Chapter 9](09-governance-and-capstone.md) covers in full, because it's genuinely the risk unique to agents.

### Versioning an agent

The same semantic-versioning habit from AI-Skills and AI-Workflows, with the axis that actually matters for an agent:

- **MAJOR** — the goal changed in a way that changes what "done" means, or the tool set changed (especially: a tool was added, particularly an action-taking one). Either of these changes what the agent is trusted to do.
- **MINOR** — a tool's description was clarified or disambiguated (like the Chapter 4 fix), or the stopping condition's budget changed, without changing what the agent is fundamentally allowed to do.
- **PATCH** — wording, prompt phrasing, or internal logic changed, with no change to goal or tool access.

**The one rule that matters most:** adding a new tool is *always* at least a MINOR bump, and adding an action-taking tool is *always* MAJOR — because that's the exact moment the trust boundary Vikram asked about actually changes.

### The changelog entry that actually matters

```
## [2.0.0] — Added deploy-log-restart tool

BREAKING: This agent can now restart a deployment when it identifies a
stuck rollout as the root cause. This is a NEW action-taking capability —
previous versions were entirely read-only. Requires human approval per
restart (see Chapter 9). Do not upgrade shared instances without
re-reviewing the approval gate.
```

Compare this to a vague "improved investigation logic" entry, which is exactly the kind of changelog message AI-Workflows Chapter 8 already taught you to distrust — it hides the one fact anyone re-running this agent actually needs before they upgrade.

### The same three-level sharing ladder

**Level 1 — Personal.** Still testing, still changing. Nobody else runs it.

**Level 2 — Project.** Checked into the repo, documented with its tool list and access levels, ready for a teammate to read and trust without asking you directly. Most agents — like most skills and most workflows — should stop here.

**Level 3 — Company-wide.** Genuinely useful across teams, with real versioning discipline and, if it has any action-taking tools at all, a documented and tested approval gate — covered in [Chapter 9](09-governance-and-capstone.md), which is a harder bar than either Level 3 gate you've cleared before.

Your config-discrepancy agent, entirely read-only, is a clean Level 2 once it has the `access: "READ_ONLY"` labels and a real version number. Vikram's flaky-test triage agent, if it ever gets a tool that can retry or quarantine a test automatically, will need to clear Chapter 9's bar first.

---

## Try it yourself

Take an agent you've built in this tutorial. Label every tool `READ_ONLY` or `ACTION_TAKING`, honestly. Add a real version number. Write one changelog entry that would tell a teammate, in one sentence, exactly what changed about what it's allowed to do — not just what it does better.

---

## What's still missing

You can package and share a read-only agent safely. What you haven't built yet is the thing that makes it safe to hand *any* agent a tool that can actually change something — the human-approval gate around irreversible actions, and the full governance checklist that ties this entire tutorial together. [Chapter 9](09-governance-and-capstone.md) is that, and it's the capstone.

---

← [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md) · [Learning path](../learning-path.md) · Next: [Chapter 9 — Governance and Capstone](09-governance-and-capstone.md)
