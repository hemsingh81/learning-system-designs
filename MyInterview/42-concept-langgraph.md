# 42 · Concept: LangGraph (30 questions)

[← LangChain](41-concept-langchain.md) · [Home](README.md) · [Next → LangSmith](43-concept-langsmith.md)

This file explains **LangGraph** — building LLM apps and agents as a **stateful graph** you can control, resume and observe — in simple English and real depth. I answer from Project B: it's how I build reliable, production-grade agentic flows on TCW.

> Simple one-liner: *"LangGraph lets me draw my AI app as a graph of nodes and edges with shared state — so I get loops, branches, memory, human approval and recovery, instead of a fragile black-box agent."*

**Jump to:** [LG1 What is LangGraph](#lg1--what-is-langgraph) · [LG2 Why use it](#lg2--why-use-langgraph) · [LG3 vs LangChain](#lg3--langgraph-vs-langchain) · [LG4 State](#lg4--state) · [LG5 Nodes](#lg5--nodes) · [LG6 Edges](#lg6--edges) · [LG7 Conditional edges](#lg7--conditional-edges) · [LG8 Cycles/loops](#lg8--cycles-and-loops) · [LG9 Graph compile](#lg9--building-and-compiling-a-graph) · [LG10 State reducers](#lg10--state-reducers)
> [LG11 Persistence](#lg11--persistence-checkpointers) · [LG12 Threads/memory](#lg12--threads-and-memory) · [LG13 Human-in-the-loop](#lg13--human-in-the-loop) · [LG14 Time travel](#lg14--time-travel) · [LG15 Streaming](#lg15--streaming) · [LG16 Tools/ToolNode](#lg16--tools-and-toolnode) · [LG17 Agent pattern](#lg17--the-react-agent-pattern) · [LG18 Multi-agent](#lg18--multi-agent-graphs) · [LG19 Subgraphs](#lg19--subgraphs) · [LG20 Parallelism](#lg20--parallel-branches)
> [LG21 Errors](#lg21--error-handling) · [LG22 Limits](#lg22--recursion-and-limits) · [LG23 Observability](#lg23--observability-with-langsmith) · [LG24 Testing](#lg24--testing) · [LG25 Deployment](#lg25--deployment) · [LG26 Prebuilt](#lg26--prebuilt-components) · [LG27 Design tips](#lg27--design-tips) · [LG28 Pitfalls](#lg28--pitfalls) · [LG29 When to use](#lg29--when-to-reach-for-langgraph) · [LG30 My use](#lg30--how-i-use-langgraph) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of LangGraph in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. It's my AI app drawn as a graph, not a script.** A plain chain runs A then B then C and stops. LangGraph lets me draw the app as **nodes** (steps that do work) joined by **edges** (what runs next). On Project B I stopped fighting a black-box agent the moment I could see my flow as a picture I control.

**2. Shared state is the thing that flows through.** Every node reads from and writes to one shared **state** object — the messages, the retrieved documents, the tool results, my own flags. Nodes don't pass arguments around; they update the state and the next node sees it. That single idea is what gives me memory and control.

**3. Nodes do the work, edges make the decisions.** A node calls a model, runs a tool, or runs my own Python. An **edge** just says where to go next. A **conditional edge** looks at the current state and branches — "if the model asked for a tool, go run it; otherwise finish." This split keeps logic clean.

**4. Cycles are the point — that's what makes it an agent.** A normal chain can't loop back. LangGraph can. The agent calls a tool, comes back, thinks again, calls another, and only exits when it's done. That loop, expressed as edges that return to an earlier node, is the whole ReAct agent pattern.

**5. Persistence turns a run into something durable.** With a **checkpointer**, the state is saved at every step. So a graph can pause, survive a crash, and resume exactly where it left off. Threads give each conversation its own memory. This is how I get reliability instead of a fragile one-shot script.

**6. Human-in-the-loop is a first-class feature, not a hack.** Because state is saved and the graph can pause, I can stop before a risky step, show a human the proposed action, wait for approval, then continue. For TCW that mattered — some actions must not run without a person saying yes.

**7. Observability is built in through LangSmith.** Every node, every state change, every model call is traceable. When something goes wrong I don't guess — I open the trace and see exactly what each node saw and did.

**The full-stack / architect lens:** the later Q&As go deeper into state reducers, subgraphs, multi-agent graphs, parallel branches, streaming, recursion limits, error handling, testing and deployment. The through-line is always the same: an agent becomes an explicit, inspectable **state machine** instead of an unpredictable loop, which is exactly the discipline production AI needs.

**One rule I never break:** *if a step is risky or expensive, put a checkpoint and a human gate in front of it — never let the graph act on the real world without a way to pause, inspect and resume.*

---

## LG1 · What is LangGraph?

**Simple explanation.** **LangGraph** is a library (from the LangChain team) for building LLM apps as a **graph**: **nodes** do work (call a model, a tool, my code), **edges** decide what runs next, and a shared **state** flows through. It's built for loops, branches, memory and control — exactly what real agents need.

**Architect's view:** It turns an agent from an unpredictable loop into an explicit **state machine** I can see, control, pause and resume — production discipline for agentic AI.

**Follow-ups**
- *"One-line?"* — A framework to build controllable, stateful AI workflows and agents as graphs.
- *"Why a graph?"* — Real AI flows branch and loop — a graph models that far better than a straight chain.

---

## LG2 · Why use LangGraph?

**Simple explanation.** Because plain agents are hard to control. LangGraph gives me **explicit control flow**, **durable state** (checkpointers), **human-in-the-loop**, **time travel** (resume from any step), streaming and tracing. That's the difference between a demo and something I can run in a regulated firm.

*"For anything with loops, approvals or recovery, LangGraph gives me the control and observability I need to put it in production."*

**Follow-ups**
- *"Biggest benefit?"* — Control + durability + human oversight — governable agents.
- *"For a simple chain?"* — Overkill — a LangChain LCEL chain is simpler.

---

## LG3 · LangGraph vs LangChain

**Simple explanation.** **LangChain** ([file 41](41-concept-langchain.md)) gives components and linear chains. **LangGraph** adds **stateful, cyclic control flow** on top — nodes/edges/state, loops, persistence, human-in-the-loop. LangGraph nodes typically *use* LangChain components.

*"Chains for straight pipelines; LangGraph when I need branches, loops, state and recovery."*

**Follow-ups**
- *"Do I choose one?"* — No — use LangChain parts inside a LangGraph graph.
- *"When jump to LangGraph?"* — The moment I need a loop, a branch, durable state, or approval gates.

---

## LG4 · State

**Simple explanation.** The **state** is a shared object (often a `TypedDict`) that flows through the graph — messages, retrieved docs, intermediate results. Each node reads state and returns updates. State is the single source of truth for a run.

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: list
```

**Follow-ups**
- *"Why explicit state?"* — It makes the flow inspectable, persistable and resumable — not hidden in variables.
- *"What goes in state?"* — Only what nodes need to share — keep it lean.

---

## LG5 · Nodes

**Simple explanation.** A **node** is a function (or LangChain runnable) that takes the state and returns an update — e.g. "retrieve", "call model", "call tool", "validate". Each node does one job — the same single-responsibility discipline as good code.

**Follow-ups**
- *"What can a node do?"* — Anything: call an LLM, run a tool, transform data, or run my own logic.
- *"Node output?"* — A partial state update that gets merged in ([LG10](#lg10--state-reducers)).

---

## LG6 · Edges

**Simple explanation.** **Edges** connect nodes and decide the order of execution. A normal edge always goes A → B. There's a special **START** and **END**. Edges are the wiring of the graph.

**Follow-ups**
- *"START/END?"* — Entry and exit points of the graph.
- *"Fixed order only?"* — No — conditional edges branch dynamically ([LG7](#lg7--conditional-edges)).

---

## LG7 · Conditional edges

**Simple explanation.** A **conditional edge** picks the next node based on the state via a function — e.g. "if the model asked for a tool → tool node; else → END". This is how the graph makes decisions and branches.

```python
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
```

**Follow-ups**
- *"How does it decide?"* — My routing function reads state and returns the next node's key.
- *"Use case?"* — Tool vs finish, route by intent, retry vs proceed.

---

## LG8 · Cycles and loops

**Simple explanation.** LangGraph supports **cycles** — edges that go back to an earlier node — which is how agents loop (call model → tool → back to model). Chains can't loop cleanly; graphs can, safely with limits.

**Follow-ups**
- *"Why is looping the key feature?"* — Agents *are* loops — think/act/observe until done ([file 39 AG4](39-concept-ai-agents-agentic.md#ag4--the-agent-loop)).
- *"Infinite loop risk?"* — Bounded by a recursion limit and my stopping logic ([LG22](#lg22--recursion-and-limits)).

---

## LG9 · Building and compiling a graph

**Simple explanation.** I build with a `StateGraph`: add nodes, add edges, set the entry point, then `compile()` into a runnable I can `invoke`/`stream`. Compiling wires it and attaches persistence.

```python
g = StateGraph(State)
g.add_node("agent", call_model); g.add_node("tools", tool_node)
g.add_edge(START, "agent"); g.add_conditional_edges("agent", should_continue)
app = g.compile(checkpointer=checkpointer)
```

**Follow-ups**
- *"Compile step?"* — Validates and builds the executable graph, with checkpointer/interrupts.
- *"Then?"* — `app.invoke(state, config)` runs it; `app.stream(...)` streams progress.

---

## LG10 · State reducers

**Simple explanation.** A **reducer** says how a node's update merges into state — e.g. `add_messages` **appends** to the message list instead of overwriting. Reducers give predictable state updates across nodes.

**Follow-ups**
- *"Default merge?"* — Overwrite the key; use a reducer (like append) when you want to accumulate.
- *"Common one?"* — `add_messages` for chat history.

---

## LG11 · Persistence (checkpointers)

**Simple explanation.** A **checkpointer** saves state after every step to a store (memory, SQLite, Postgres, Redis). This makes runs **durable** — they survive crashes, can pause and resume, and support human approval and time travel.

*"Durable state is what lets me pause for a human to approve, then resume exactly where it stopped — essential for regulated actions."*

**Follow-ups**
- *"Why persist state?"* — Resume after crash/pause, enable human-in-the-loop, and audit the run.
- *"Production store?"* — Postgres/Redis checkpointer, not in-memory.

---

## LG12 · Threads and memory

**Simple explanation.** A **thread** (a config `thread_id`) groups a conversation's state across turns, so the graph remembers context per user/session via the checkpointer. That's durable long-term memory built in.

**Follow-ups**
- *"How does memory work?"* — State keyed by thread_id, restored each turn from the checkpointer.
- *"Multi-user?"* — Each user/session gets its own thread_id — isolated state.

---

## LG13 · Human-in-the-loop

**Simple explanation.** LangGraph can **interrupt** before a node, save state, and wait for a human to approve/edit, then resume ([file 39 AG12](39-concept-ai-agents-agentic.md#ag12--human-in-the-loop)). This is first-class — the graph pauses and continues from the same point.

**Follow-ups**
- *"How?"* — Set an interrupt before the consequential node; the run pauses; a human approves; you resume the thread.
- *"Why is this big?"* — Safe autonomy — the agent works, a human confirms risky actions.

---

## LG14 · Time travel

**Simple explanation.** Because state is checkpointed, I can **rewind** to any earlier step, inspect it, change an input, and re-run from there. Great for debugging and for "what if" corrections.

**Follow-ups**
- *"Use for debugging?"* — Yes — jump to the step that went wrong, tweak, and replay.
- *"Enables recovery?"* — Resume from the last good checkpoint rather than restarting.

---

## LG15 · Streaming

**Simple explanation.** LangGraph streams **progress** — node-by-node updates and LLM tokens — so the UI shows what's happening ("searching…", "drafting…") and the answer as it forms.

**Follow-ups**
- *"What can you stream?"* — State updates per node, and tokens from model nodes.
- *"UX value?"* — Users see live progress on multi-step tasks, not a frozen screen.

---

## LG16 · Tools and ToolNode

**Simple explanation.** A prebuilt **ToolNode** runs the tools the model requested and returns results into state. The model node decides *which* tool; ToolNode executes it — the safe split from file 39 ([AG6](39-concept-ai-agents-agentic.md#ag6--tools-for-agents)).

**Follow-ups**
- *"Why a dedicated tool node?"* — Clean separation: model decides, node executes with auth/limits.
- *"Multiple tools?"* — ToolNode handles the set; conditional edge loops back to the model with results.

---

## LG17 · The ReAct agent pattern

**Simple explanation.** The classic graph: **agent node** (model) → conditional edge → **tool node** → back to agent → … → END when done. LangGraph ships a `create_react_agent` prebuilt for exactly this ([file 39 AG5](39-concept-ai-agents-agentic.md#ag5--react-reason--act)).

**Follow-ups**
- *"Build from scratch?"* — I can, or use the prebuilt and customise — both are common.
- *"Stopping?"* — The model signals "no tool needed" → conditional edge → END, plus a recursion cap.

---

## LG18 · Multi-agent graphs

**Simple explanation.** I can model **multiple agents** as nodes/subgraphs coordinated by a supervisor node that routes work between them ([file 39 AG10](39-concept-ai-agents-agentic.md#ag10--multi-agent-systems)). The graph makes the coordination explicit and debuggable.

**Follow-ups**
- *"Supervisor pattern?"* — A router node decides which specialist agent runs next based on state.
- *"Keep it simple?"* — Yes — fewest agents that work; graphs make the wiring visible.

---

## LG19 · Subgraphs

**Simple explanation.** A **subgraph** is a graph used as a node inside another graph — encapsulating a reusable flow (e.g. a "research" subgraph). It keeps big systems modular and testable.

**Follow-ups**
- *"Why subgraphs?"* — Reuse and modularity — compose complex apps from tested pieces.
- *"State sharing?"* — Map parent state in/out of the subgraph explicitly.

---

## LG20 · Parallel branches

**Simple explanation.** A node can **fan out** to several nodes that run in parallel, then **fan in** to combine results — e.g. query three sources at once, then merge ([file 38 AS12](38-concept-ai-skills-workflow.md#as12--parallelisation)). Cuts latency on independent work.

**Follow-ups**
- *"How merge parallel results?"* — A reducer accumulates them into state at the fan-in node.
- *"When not to parallelise?"* — When steps depend on each other — keep them sequential.

---

## LG21 · Error handling

**Simple explanation.** Nodes can catch errors and route to a recovery/fallback node via conditional edges; combined with checkpointing I can **resume from the last good step** instead of restarting. Retries and fallbacks live in nodes.

**Follow-ups**
- *"Recover mid-run?"* — Yes — resume from the last checkpoint after fixing the cause.
- *"Fallback path?"* — A conditional edge to a safe node (e.g. return best-effort or ask a human).

---

## LG22 · Recursion and limits

**Simple explanation.** LangGraph enforces a **recursion limit** (max steps) so cyclic graphs can't loop forever ([file 39 AG14](39-concept-ai-agents-agentic.md#ag14--stopping-conditions)). I set it plus my own budget/stop logic.

**Follow-ups**
- *"What happens at the limit?"* — It stops with an error I handle — return best effort and log.
- *"Only safeguard?"* — No — add cost/time budgets and progress checks too.

---

## LG23 · Observability with LangSmith

**Simple explanation.** LangGraph runs trace to **LangSmith** ([file 43](43-concept-langsmith.md)) automatically — every node, state change, tool call, token and latency. For an agent, this full replay is how I debug and govern behaviour.

**Follow-ups**
- *"Why essential here?"* — Graph behaviour is emergent — tracing shows the exact path taken.
- *"Plus App Insights?"* — Yes — LangSmith for AI detail, App Insights for service health.

---

## LG24 · Testing

**Simple explanation.** I test **individual nodes** as plain functions (deterministic, mock the model), test **routing functions** directly, and run **scenario evals** on the whole graph via LangSmith. Node-level testing is a big advantage of the graph model.

**Follow-ups**
- *"Why is node testing nice?"* — Each node is a small pure-ish function — easy to unit-test.
- *"Whole-graph tests?"* — Scenario datasets scoring outcome and safety.

---

## LG25 · Deployment

**Simple explanation.** I deploy the compiled graph inside my **FastAPI** service (or LangGraph Platform) with a **Postgres/Redis checkpointer**, secrets in **Key Vault**, models via **Azure OpenAI**, tracing to **LangSmith**, on App Service/Container Apps ([file 37](37-concept-azure-services.md)).

**Follow-ups**
- *"Checkpointer in prod?"* — A durable store (Postgres/Redis) — never in-memory.
- *"Scale?"* — Stateless service + shared checkpointer — scale out horizontally.

---

## LG26 · Prebuilt components

**Simple explanation.** LangGraph ships prebuilts — `create_react_agent`, `ToolNode`, checkpointers, interrupt helpers — so I get common agent patterns fast, then customise. Start prebuilt, drop to low-level graph when I need control.

**Follow-ups**
- *"Prebuilt vs custom graph?"* — Prebuilt for speed; custom for full control of flow and state.
- *"Mix?"* — Yes — wrap a prebuilt agent as a node in a larger graph.

---

## LG27 · Design tips

**Simple explanation.** Keep **state lean**, give each **node one job**, make **edges explicit**, add **limits and human gates** early, and **trace everything**. Design the graph like a clear state machine, not a tangle.

**Follow-ups**
- *"One tip that matters most?"* — Small, single-purpose nodes — they're testable and debuggable.
- *"Avoid?"* — Bloated state and implicit control flow.

---

## LG28 · Pitfalls

**Simple explanation.** Watch for **over-complex graphs**, **bloated state**, **missing limits** (runaway loops), **in-memory checkpointer in prod**, and forgetting **human gates** on risky actions. Simplicity and limits keep it safe.

**Follow-ups**
- *"Most common mistake?"* — No recursion/cost limit — a loop that never ends.
- *"Prod checkpointer mistake?"* — Using in-memory — lose state on restart; use Postgres/Redis.

---

## LG29 · When to reach for LangGraph

**Simple explanation.** Reach for it when I need **loops, branches, durable state, human approval, recovery, or multi-agent coordination**. For a straight prompt → model → parse pipeline, a plain LangChain chain is simpler.

**Follow-ups**
- *"Trigger to switch?"* — The first time the flow must loop, branch, pause, or persist.
- *"Simple RAG Q&A?"* — A LangChain chain — no need for a graph.

---

## LG30 · How I use LangGraph

**How I answer (the whole picture).** *"I use LangGraph for production agentic flows: I model the app as a small state graph — single-purpose nodes (retrieve, call model, run tools, validate), explicit and conditional edges for branching and loops, a lean typed state, and a durable checkpointer so runs are resumable. I add human-in-the-loop interrupts before any consequential action, recursion and cost limits, and stream progress to the UI. Everything traces to LangSmith and runs inside a FastAPI service on Azure with Key Vault and Azure OpenAI. That combination — control, durability, oversight and observability — is what makes agentic AI safe enough for a regulated firm like TCW."*

**Follow-ups**
- *"Why LangGraph over a plain agent?"* — Control, durable state, human gates and recovery — governable, not black-box.
- *"LangChain's role alongside it?"* — Its components live inside my LangGraph nodes.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| LG1 | What is LangGraph | Build AI apps as a stateful graph |
| LG2 | Why use it | Control, durability, human-in-the-loop |
| LG3 | vs LangChain | Adds cyclic, stateful control flow |
| LG4 | State | Shared object flowing through the graph |
| LG5 | Nodes | Single-job functions returning state updates |
| LG6 | Edges | Wiring and order between nodes |
| LG7 | Conditional edges | Branch on state via a routing function |
| LG8 | Cycles/loops | Enables true agent loops |
| LG9 | Compile | Build then compile into a runnable |
| LG10 | Reducers | How updates merge (e.g. append messages) |
| LG11 | Persistence | Checkpointers make runs durable |
| LG12 | Threads | Per-session durable memory |
| LG13 | Human-in-the-loop | Interrupt, approve, resume |
| LG14 | Time travel | Rewind and replay from any step |
| LG15 | Streaming | Live node/token progress |
| LG16 | ToolNode | Executes model-requested tools safely |
| LG17 | ReAct pattern | agent ↔ tools loop; prebuilt available |
| LG18 | Multi-agent | Supervisor routes specialist agents |
| LG19 | Subgraphs | Reusable graphs as nodes |
| LG20 | Parallelism | Fan-out/fan-in for independent work |
| LG21 | Errors | Route to recovery; resume from checkpoint |
| LG22 | Limits | Recursion cap stops runaway loops |
| LG23 | Observability | Full traces to LangSmith |
| LG24 | Testing | Unit-test nodes; scenario-eval graph |
| LG25 | Deployment | FastAPI + durable checkpointer on Azure |
| LG26 | Prebuilt | react agent, ToolNode, checkpointers |
| LG27 | Design tips | Lean state, one-job nodes, limits, tracing |
| LG28 | Pitfalls | Complexity, no limits, in-memory in prod |
| LG29 | When to use | Loops, branches, state, approval, recovery |
| LG30 | My use | Controlled, durable, observable agentic flows |

---

[← LangChain](41-concept-langchain.md) · [Home](README.md) · [Next → LangSmith](43-concept-langsmith.md)
