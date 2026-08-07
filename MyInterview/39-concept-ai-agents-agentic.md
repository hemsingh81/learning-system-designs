# 39 · Concept: AI Agents & Agentic AI (30 questions)

[← AI Skills & Workflow](38-concept-ai-skills-workflow.md) · [Home](README.md) · [Next → RAG](40-concept-rag.md)

This file explains **AI agents** and **agentic AI** — systems where the model decides what to do next — in simple English and real depth. I answer as an architect who ships governed AI, from Project B (TCW's AI/LLM reference architecture and first production RAG assistant).

> Simple one-liner: *"An agent is an LLM that runs in a loop: it thinks, picks a tool, acts, observes the result, and repeats until the goal is met. Agentic AI is powerful — so I wrap it in tight guardrails, limits and human oversight."*

**Jump to:** [AG1 What is an AI agent](#ag1--what-is-an-ai-agent) · [AG2 Agentic AI](#ag2--what-is-agentic-ai) · [AG3 Agent vs workflow](#ag3--agent-vs-workflow) · [AG4 The agent loop](#ag4--the-agent-loop) · [AG5 ReAct](#ag5--react-reason--act) · [AG6 Tools](#ag6--tools-for-agents) · [AG7 Planning](#ag7--planning) · [AG8 Memory](#ag8--agent-memory) · [AG9 Reflection](#ag9--reflection-and-self-critique) · [AG10 Multi-agent](#ag10--multi-agent-systems)
> [AG11 Roles](#ag11--agent-roles) · [AG12 Human-in-the-loop](#ag12--human-in-the-loop) · [AG13 Autonomy levels](#ag13--levels-of-autonomy) · [AG14 Stopping](#ag14--stopping-conditions) · [AG15 Cost/latency](#ag15--cost-and-latency) · [AG16 Errors](#ag16--error-handling) · [AG17 Security](#ag17--agent-security) · [AG18 Guardrails](#ag18--guardrails-for-agents) · [AG19 Evaluation](#ag19--evaluating-agents) · [AG20 Observability](#ag20--observability)
> [AG21 Frameworks](#ag21--frameworks) · [AG22 MCP](#ag22--model-context-protocol-mcp) · [AG23 RAG agent](#ag23--agentic-rag) · [AG24 Coding agents](#ag24--coding-agents) · [AG25 When to use](#ag25--when-to-use-an-agent) · [AG26 When not to](#ag26--when-not-to-use-an-agent) · [AG27 Failure modes](#ag27--common-failure-modes) · [AG28 Testing](#ag28--testing-agents) · [AG29 Deployment](#ag29--deploying-agents) · [AG30 My stance](#ag30--my-architects-stance) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of AI agents and agentic AI in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. An agent is an LLM running in a loop.** Give the model a goal, a set of tools, and a loop: it thinks, picks a tool, acts, reads the result, and repeats until the goal is met or a limit is hit. "Agentic" simply means the model — not my hard-coded path — decides the next step at runtime.

**2. Agent = model + tools + memory + a control loop.** Those four parts are the whole thing. Tools are how it acts on the world (search, call an API, run code); memory is how it remembers across steps; the control loop is the fence I put around it. Take away the loop and it's just a single call.

**3. The trade is flexibility for predictability.** A workflow follows my fixed steps and is easy to reason about. An agent chooses its own steps and handles messy, open-ended tasks — but it's less predictable, costs more and can wander. I use an agent deliberately, not because it's fashionable.

**4. ReAct is the common loop: reason, then act.** The model reasons about what to do, acts by calling a tool, observes the result, and reasons again. Planning and reflection (self-critique) make this smarter for harder tasks, at the cost of more model calls.

**5. Multi-agent means splitting work across specialists.** Instead of one do-everything agent, I can use several with clear roles coordinated by an orchestrator. It's powerful but adds cost and coordination complexity, so I only reach for it when a single agent genuinely can't cope.

**6. Autonomy is a dial, not a switch.** I choose how much freedom to give — from a tightly scripted assistant to a highly autonomous agent — and I set stopping conditions (step limits, budgets, timeouts) so it can never loop forever or burn unbounded cost.

**7. Guardrails and human-in-the-loop are mandatory, not optional.** Tool permissions, input/output validation, sandboxing, approvals for risky actions, and human review on anything sensitive. On Project B I ship *governed* AI — the guardrails are as much of the design as the agent itself.

**8. If I can't observe and evaluate it, I don't run it.** Tracing every step, evaluating outcomes, and handling errors turn an impressive demo into something safe for production. Cost, latency and failure modes get designed for up front.

**The full-stack / architect lens:** the later Q&As go deeper — frameworks, MCP, agentic RAG, coding agents, when to use an agent and when not to, common failure modes, testing, and deployment. They all trace back to the same core: a fenced loop of model-plus-tools, given only as much autonomy as the task truly needs.

**One rule I never break:** *never give an agent an unbounded loop or an unfenced tool — always cap the steps and constrain what it's allowed to do.*

---

## AG1 · What is an AI agent?

**Simple explanation.** An **AI agent** is an LLM given a goal, a set of **tools**, and a **loop**. It decides the next action, uses a tool, reads the result, and repeats until it reaches the goal or hits a limit. The model — not my hard-coded path — drives the steps.

**Architect's view:** An agent = model + tools + memory + a control loop. It's flexible but less predictable, so I use it deliberately and fence it in.

**Follow-ups**
- *"Simplest definition?"* — An LLM that can take actions in a loop to achieve a goal.
- *"What makes it 'agentic'?"* — The model decides what to do next at runtime, instead of following my fixed script.

---

## AG2 · What is agentic AI?

**Simple explanation.** **Agentic AI** is the broader idea of AI systems that act with autonomy — they plan, use tools, adapt to results, and pursue multi-step goals with limited human input. Agents are the building block; agentic AI is the pattern.

**Follow-ups**
- *"Is it hype?"* — Partly — it's powerful for open-ended tasks but oversold for simple ones a workflow handles better.
- *"What changed recently?"* — Better tool calling, bigger context, and frameworks make reliable agents practical, not just demos.

---

## AG3 · Agent vs workflow

**Simple explanation.** In a **workflow** I fix the steps in code; in an **agent** the model chooses steps dynamically ([file 38 AS4](38-concept-ai-skills-workflow.md#as4--workflow-vs-agent)). Workflow = predictable, cheap, testable. Agent = flexible, but costlier and harder to control.

*"My rule: use the simplest thing that works. Start with a workflow; reach for an agent only when the path can't be known in advance."*

**Follow-ups**
- *"Why not always use agents?"* — Cost, latency, and unpredictability — most enterprise tasks are better as workflows.
- *"Can you combine them?"* — Yes — a workflow calls an agent for one open-ended step and stays in control elsewhere.

---

## AG4 · The agent loop

**Simple explanation.** The core loop: **Think** (plan next step) → **Act** (call a tool) → **Observe** (read result) → repeat, until the goal is met or a limit is hit. Each turn adds to the context so the model reasons with what it has learned.

**Follow-ups**
- *"What ends the loop?"* — A success signal, a max-step cap, a time/cost budget, or an error — always bounded.
- *"Where does it go wrong?"* — Looping without progress — which is why limits and reflection matter.

---

## AG5 · ReAct (Reason + Act)

**Simple explanation.** **ReAct** is a common agent pattern where the model interleaves **reasoning** ("I should search for X") and **acting** (calls the search tool), using each observation to reason again. It makes the agent's thinking explicit and tool use grounded.

**Follow-ups**
- *"Why is ReAct useful?"* — The visible reasoning makes behaviour easier to debug and steer.
- *"Downside?"* — More tokens; the reasoning text costs money and can leak internal logic if exposed.

---

## AG6 · Tools for agents

**Simple explanation.** **Tools** are the actions an agent can take — search a KB, query a DB, call an API, run code, send an email. I describe each tool (name, purpose, argument schema); the agent picks and fills arguments; **my code** runs it with proper auth.

*"The tools define what the agent *can* do — so I keep them minimal and least-privilege. No tool = no capability = no risk."*

**Follow-ups**
- *"How many tools?"* — Few and well-described — too many confuse the model and widen the attack surface.
- *"Dangerous tools?"* — Gate destructive actions behind confirmation or human approval.

---

## AG7 · Planning

**Simple explanation.** **Planning** is the agent breaking a goal into an ordered set of steps before (or while) acting. Some agents plan up front, some plan step-by-step. Planning helps on complex, multi-part tasks.

**Follow-ups**
- *"Plan-first vs step-by-step?"* — Plan-first is structured but rigid; step-by-step adapts but can wander — I pick by task.
- *"Risk with planning?"* — A bad plan cascades — I add re-planning and checks between steps.

---

## AG8 · Agent memory

**Simple explanation.** Agents use **short-term memory** (the running loop context) and **long-term memory** (facts stored and retrieved later, often in a vector store). Memory lets an agent stay coherent over a long task and across sessions.

**Follow-ups**
- *"Why not keep everything in context?"* — Context is limited and costly — store and retrieve only what's relevant.
- *"Privacy?"* — Control what's persisted; redact PII and honour retention rules.

---

## AG9 · Reflection and self-critique

**Simple explanation.** **Reflection** is the agent reviewing its own work — "did that step succeed? is this answer right?" — and correcting course. It's the evaluator-optimiser idea ([file 38 AS14](38-concept-ai-skills-workflow.md#as14--evaluator-optimiser-loop)) inside an agent.

**Follow-ups**
- *"Does reflection help?"* — Yes on complex tasks — catching its own errors improves quality, at extra cost.
- *"Limit?"* — It can over-think — cap reflection iterations.

---

## AG10 · Multi-agent systems

**Simple explanation.** A **multi-agent system** uses several specialised agents that collaborate — e.g. a planner, a researcher, a coder, a reviewer. One orchestrator coordinates; each agent focuses on its role. Good for large tasks, but more complex and costly.

*"I keep it to the fewest agents that do the job — more agents means more coordination bugs and cost."*

**Follow-ups**
- *"Why split into multiple agents?"* — Focus and clearer prompts per role — like a small team with defined jobs.
- *"Biggest risk?"* — Coordination overhead and compounding errors — start single-agent, split only if needed.

---

## AG11 · Agent roles

**Simple explanation.** In multi-agent designs I give each agent a **role** with its own system prompt and tools — e.g. Orchestrator (splits work), Worker (does a subtask), Critic (reviews). Clear roles keep behaviour predictable.

**Follow-ups**
- *"Common roles?"* — Planner/orchestrator, worker/specialist, critic/reviewer, and a tool-runner.
- *"How do they talk?"* — Structured messages the orchestrator routes — not free-for-all chatter.

---

## AG12 · Human-in-the-loop

**Simple explanation.** For anything risky, the agent **pauses for human approval** before acting — e.g. before sending an email or changing data. It keeps autonomy useful and safe.

*"In a regulated firm I put approval gates on any action that's irreversible, customer-facing, or touches money."*

**Follow-ups**
- *"Where do you put the gate?"* — Right before the consequential tool call — the agent proposes, a human confirms.
- *"Does it kill the value?"* — No — the agent still does the heavy lifting; the human just approves the last step.

---

## AG13 · Levels of autonomy

**Simple explanation.** Autonomy is a dial: **assist** (suggests, human does it) → **approve** (acts after sign-off) → **auto** (acts alone within limits). I start low and raise it only as evals and monitoring earn trust.

**Follow-ups**
- *"Where do you start?"* — Assist or approve — never full auto on day one for consequential actions.
- *"How do you raise autonomy?"* — Evidence: strong eval scores, clean monitoring, low error rate.

---

## AG14 · Stopping conditions

**Simple explanation.** Every agent needs hard limits: **max steps**, **time budget**, **cost budget**, and a clear **success/failure signal**. Without them an agent can loop forever and burn money.

**Follow-ups**
- *"What if it hits the cap without finishing?"* — Return best effort + a clear "couldn't complete" and log it for review.
- *"Why cost caps?"* — A runaway loop is a real bill — budgets are a safety control, not just tuning.

---

## AG15 · Cost and latency

**Simple explanation.** Agents make **many** model calls, so they're slower and pricier than a single call. I control it with step caps, cheaper models for sub-steps, caching, parallel tools, and preferring a workflow when the path is known.

**Follow-ups**
- *"Why are agents expensive?"* — The loop + reasoning tokens + multiple tool round-trips add up fast.
- *"How do you cut it?"* — Fewer steps, smaller models per sub-task, caching, and tight tool descriptions.

---

## AG16 · Error handling

**Simple explanation.** Tools fail and models mis-step. I return clear error messages to the agent so it can adapt, add **retries with backoff**, keep tools **idempotent**, and fall back gracefully after N failures.

**Follow-ups**
- *"Feed errors back to the agent?"* — Yes — a good error message lets it correct itself; a silent failure derails it.
- *"When do you stop retrying?"* — After a small cap — then fail cleanly rather than loop.

---

## AG17 · Agent security

**Simple explanation.** Agents are riskier because they **act**. Threats: **prompt injection** turning tools against you, **excessive permissions**, and **data exfiltration**. I mitigate with least-privilege tools, input/output filtering, no direct execution of model output, and approval gates on sensitive actions.

*"An agent with a database-write tool and no guardrails is a liability. I design the blast radius to be small."*

**Follow-ups**
- *"Scariest risk?"* — Prompt injection via retrieved/user content triggering a powerful tool — hence least privilege + gates.
- *"Golden rule?"* — The agent can only do what its tools allow — so restrict the tools.

---

## AG18 · Guardrails for agents

**Simple explanation.** Guardrails wrap the loop: allow-listed tools, argument validation, content-safety on inputs/outputs, budget/step limits, and approval gates. They turn a free-roaming agent into a controlled one.

**Follow-ups**
- *"Where do guardrails live?"* — In my code around the loop — not in the prompt alone, which can be bypassed.
- *"Tooling on Azure?"* — Content Safety + my validators + managed identity for least-privilege tool auth.

---

## AG19 · Evaluating agents

**Simple explanation.** I evaluate agents on **task success rate**, **steps/cost to complete**, **safety** (no bad actions), and **groundedness** of answers — measured over a fixed set of scenarios, including adversarial ones.

**Follow-ups**
- *"Hardest part of agent eval?"* — Many valid paths — so I score the outcome and the safety, not the exact steps.
- *"Include attacks?"* — Yes — injection and edge cases in the eval set to prove the guardrails hold.

---

## AG20 · Observability

**Simple explanation.** I **trace the whole loop** — every thought, tool call, argument, observation, token and cost — so I can replay why an agent did what it did. Agents without tracing are impossible to debug or trust.

*"LangSmith-style tracing ([file 43](43-concept-langsmith.md)) plus App Insights gives me a full replay of each run."*

**Follow-ups**
- *"What do you capture?"* — The full step-by-step trace: prompts, tool I/O, decisions, tokens, latency, outcome.
- *"Why essential for agents?"* — Behaviour is emergent — you can only govern what you can see.

---

## AG21 · Frameworks

**Simple explanation.** Frameworks speed up building agents: **LangChain** ([file 41](41-concept-langchain.md)) for components, **LangGraph** ([file 42](42-concept-langgraph.md)) for stateful graph-based control, plus others (AutoGen, CrewAI, Semantic Kernel). They handle the loop, tools and memory so I focus on the task.

**Follow-ups**
- *"LangChain vs LangGraph for agents?"* — LangChain for quick chains; LangGraph when I need explicit state, branches and control — which agents need.
- *"Do you need a framework?"* — No, but it saves boilerplate and gives tracing/patterns for free.

---

## AG22 · Model Context Protocol (MCP)

**Simple explanation.** **MCP** is an open standard for connecting AI models to tools and data sources in a consistent way — a common "USB port" for tools. It lets an agent use standard servers (files, DBs, APIs) without custom glue for each.

**Follow-ups**
- *"Why does MCP matter?"* — Standard tool integration — less bespoke code, reusable across agents and vendors.
- *"Security with MCP?"* — Still least-privilege — a standard connector doesn't remove the need for auth and limits.

---

## AG23 · Agentic RAG

**Simple explanation.** **Agentic RAG** lets the agent decide *how* to retrieve — reformulate the query, search multiple sources, judge if results are enough, and retrieve again — instead of a single fixed retrieval ([file 40](40-concept-rag.md)). Better for hard, multi-hop questions.

*"For complex support questions the agent can search, realise it needs more, refine the query, and retrieve again — closer to how a human researches."*

**Follow-ups**
- *"Agentic RAG vs plain RAG?"* — Plain RAG retrieves once; agentic RAG retrieves iteratively and adaptively — more power, more cost.
- *"When worth it?"* — Multi-hop or ambiguous questions; overkill for simple lookups.

---

## AG24 · Coding agents

**Simple explanation.** **Coding agents** (like the ones in modern IDEs) plan, edit files, run tests, read errors, and fix — in a loop. I use them under my rules from Project B's AI-assisted development playbook ([file 20](20-ai-assisted-development.md)): human ownership, repo rules, and automated gates.

**Follow-ups**
- *"Do you trust a coding agent's output?"* — I review everything — the human owns the merge; the agent accelerates, it doesn't approve.
- *"Guardrails for coding agents?"* — Tests, linters, CI gates, and code review — the same gates as any change.

---

## AG25 · When to use an agent

**Simple explanation.** Use an agent when the task is **open-ended**, the **steps can't be predetermined**, and it needs to **use tools and adapt** — e.g. research across sources, triage with dynamic lookups, or multi-step problem solving.

**Follow-ups**
- *"Give a good fit."* — "Investigate this alert": the path depends on findings — an agent adapts; a fixed workflow can't.
- *"First question you ask?"* — "Can I predetermine the steps?" If yes, use a workflow.

---

## AG26 · When not to use an agent

**Simple explanation.** Avoid agents for **known, repeatable** tasks (use a workflow), **high-stakes actions without oversight**, or where **cost/latency** matter and a single call would do. Simpler is safer and cheaper.

*"Most 'agent' demos are really workflows. I don't pay the agent tax unless the task truly needs it."*

**Follow-ups**
- *"Cheapest correct option first?"* — Yes — single call → workflow → agent, in that order of preference.
- *"Red flag for over-engineering?"* — An agent used where the steps never change.

---

## AG27 · Common failure modes

**Simple explanation.** Agents fail by **looping** without progress, **hallucinating** tool arguments, **misusing tools**, **ignoring the goal**, or **runaway cost**. I counter with step/cost caps, argument validation, clear tool descriptions, reflection, and tracing.

**Follow-ups**
- *"Most common in practice?"* — Getting stuck in a loop — fixed with progress checks and hard caps.
- *"How do you catch these?"* — Tracing + evals with adversarial cases surface them before production.

---

## AG28 · Testing agents

**Simple explanation.** I test tools and guardrails deterministically (unit tests), and the agent behaviour with **scenario evals**: does it complete the task, stay safe, and stay within budget across many runs? I assert on outcomes and safety, not exact paths.

**Follow-ups**
- *"Why scenario-based?"* — Non-determinism means multiple valid paths — score the result and behaviour over many runs.
- *"Regression?"* — Re-run the scenario suite on every change; block if success/safety drops.

---

## AG29 · Deploying agents

**Simple explanation.** Deploy like any service, with extra care: strict tool permissions (managed identity, least privilege), budget/rate limits, full tracing, approval gates on sensitive actions, and evals in CI. Pin model and prompt versions.

*"On Azure: Azure OpenAI/AI Foundry for the model, my service for the loop and tools, Key Vault for secrets, App Insights + LangSmith for traces."*

**Follow-ups**
- *"Biggest deployment risk?"* — An over-privileged tool + injection — so I lock permissions and gate actions.
- *"Rollout?"* — Canary with low autonomy, monitor, then widen — never full auto on day one.

---

## AG30 · My architect's stance

**How I answer (the whole picture).** *"I'm pragmatic about agents. I start with the simplest thing — a single call, then a workflow — and only reach for an agent when the steps genuinely can't be known in advance. When I do, I give it the fewest, least-privileged tools, hard step/cost caps, guardrails and content safety, full tracing, and a human-in-the-loop on anything consequential. I raise autonomy only as evals and monitoring earn trust. That's how I'd take agentic features to production in a regulated firm — the same discipline I used for TCW's first production RAG app."*

**Follow-ups**
- *"One-line philosophy?"* — Give the model as much freedom as the task needs and not one bit more.
- *"Where have you applied this?"* — The AI/LLM reference architecture and RAG assistant on Project B — grounded, governed, observable.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| AG1 | AI agent | LLM + tools + loop pursuing a goal |
| AG2 | Agentic AI | The pattern of autonomous, tool-using AI |
| AG3 | Agent vs workflow | Model decides vs I decide the steps |
| AG4 | Agent loop | Think → Act → Observe → repeat, bounded |
| AG5 | ReAct | Interleave reasoning and tool actions |
| AG6 | Tools | Least-privilege actions; my code runs them |
| AG7 | Planning | Break goal into steps; re-plan as needed |
| AG8 | Memory | Short-term loop + long-term retrieved facts |
| AG9 | Reflection | Self-critique to catch and fix errors |
| AG10 | Multi-agent | Specialised agents collaborate under an orchestrator |
| AG11 | Roles | Planner/worker/critic with own prompts & tools |
| AG12 | Human-in-the-loop | Approve consequential actions |
| AG13 | Autonomy levels | Assist → approve → auto; earn trust to raise |
| AG14 | Stopping | Step/time/cost caps + success signal |
| AG15 | Cost/latency | Many calls; cap steps, cache, smaller models |
| AG16 | Errors | Feed back, retry, idempotent, fail cleanly |
| AG17 | Security | Injection, over-privilege, exfiltration — mitigate |
| AG18 | Guardrails | Allow-list tools, validate, budgets, gates |
| AG19 | Evaluation | Success rate, cost, safety over scenarios |
| AG20 | Observability | Trace the whole loop for replay |
| AG21 | Frameworks | LangChain/LangGraph/AutoGen/Semantic Kernel |
| AG22 | MCP | Standard connector for tools and data |
| AG23 | Agentic RAG | Iterative, adaptive retrieval |
| AG24 | Coding agents | Plan-edit-test-fix under human ownership |
| AG25 | When to use | Open-ended, unknown steps, needs tools |
| AG26 | When not to | Known/repeatable tasks — use a workflow |
| AG27 | Failure modes | Loops, bad args, tool misuse, runaway cost |
| AG28 | Testing | Unit-test tools; scenario-eval behaviour |
| AG29 | Deployment | Least privilege, caps, tracing, gates, evals |
| AG30 | My stance | Simplest thing first; freedom only as needed |

---

[← AI Skills & Workflow](38-concept-ai-skills-workflow.md) · [Home](README.md) · [Next → RAG](40-concept-rag.md)
