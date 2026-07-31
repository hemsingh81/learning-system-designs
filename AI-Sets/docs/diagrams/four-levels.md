# Diagram: the four levels

```
LEVEL 1 — SKILL
  One small unit of AI work. Input in, output out. No memory. No decisions.

      input ──► [ SKILL ] ──► output

  Analogy: a pure function, or a single REST endpoint.


           + fixed order, wired by a HUMAN at design time
                          │
                          ▼
LEVEL 2 — WORKFLOW
  Several skills chained in an order YOU decided. The path is the same
  every run. Retries, fallbacks, and branching live here.

      input ──► [classify] ──► [extract] ──► [score] ──► [draft reply] ──► output
                    │
                    └─ if category == "outage" ──► [escalate branch]

  Analogy: a CI/CD pipeline, or a queue-consumer chain.


           + the MODEL decides the order, and can call tools
                          │
                          ▼
LEVEL 3 — AGENT
  A loop: think → choose a tool → run it → look at the result → repeat.
  The path is DIFFERENT every run, because the model is choosing it.

      ┌─────────────────────────────────────────────┐
      │                                              │
      ▼                                              │
   [ THINK ] ──► [ CHOOSE TOOL ] ──► [ RUN TOOL ] ──► [ OBSERVE ] ──┘
      │
      └─ when the model decides it has enough info ──► [ FINAL ANSWER ]

  Analogy: a junior engineer with a runbook and shell access, figuring
  out which command to run next based on what the last one showed.


           + a GOAL over time, memory, planning, self-checks, many
             agents, and a human escalation path
                          │
                          ▼
LEVEL 4 — AGENTIC AI
  A system that owns a goal, not just a single question. It plans, it
  remembers across steps, it checks its own work, it has hard limits
  (budget/time/risk), and it knows when to STOP and ask a human.

      [ GOAL ] ──► [ PLAN ] ──► [ AGENT LOOP x N steps ] ──► [ CRITIC ]
                       ▲                                         │
                       │                 re-plan if the world     │
                       └─────────────── surprised us ◄────────────┘
                                                                    │
                                                    goal met? ──────┤
                                                        │           │
                                                       yes          no, but
                                                        │           risk is high
                                                        ▼           │
                                                   [ DONE ]         ▼
                                                              [ ASK A HUMAN ]

  Analogy: an on-call team following an incident runbook, with a clear
  escalation policy for when to page a human instead of guessing.
```

**The one sentence to remember:**
A *skill* does one thing. A *workflow* is a path **you** chose. An *agent* is a
path the **model** chooses. *Agentic AI* is an agent that owns a **goal**, with
memory, safety limits, and an escape hatch to a human.
