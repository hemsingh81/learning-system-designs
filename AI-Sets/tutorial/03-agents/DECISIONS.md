# Decision log — AI Agent (Milestone 5)

### D-301: The agent handles exactly ONE tool call per turn
Options:
  A) Handle every tool call in a model turn that requests multiple at once
     (parallel tool calls).
     — pros: can be faster (multiple lookups in one round trip). cons:
       harder to trace step-by-step in a teaching example; harder to
       apply loop-detection cleanly (which call counts as "the" call?).
  B) Only ever act on the FIRST tool call in a turn, ignore any others the
     model might have requested in the same response.
Chosen: B
Why: this project's whole teaching goal is a loop you can read and trace
one step at a time (see docs/diagrams/agent-loop.md). One call per turn
keeps `AgentStepLog` exactly one tool call per log entry, which makes the
printed trace in every example directly readable.
Revisit if: latency actually matters for your use case and the model
regularly asks for genuinely independent parallel lookups — then extend
the loop to fan out multiple tool calls per turn (see the async appendix
for the concurrency mechanics you'd need).

### D-302: Loop detection is exact-match, not "similar enough"
Options:
  A) Detect a loop by fuzzy-matching similar-looking calls.
     — pros: catches more subtle loops. cons: much harder to reason
       about, could false-positive on two genuinely different lookups
       that happen to look similar.
  B) Detect a loop only when the tool NAME and the exact serialized
     ARGUMENTS match a previous call, byte for byte.
Chosen: B
Why: an exact repeat is unambiguous evidence the model isn't making
progress — trying the SAME thing again with the SAME inputs cannot
produce new information. A near-repeat might genuinely be a different,
useful investigation step (e.g. `query_orders(order_id="9002")` then
`query_orders(order_id="9003")` are NOT a loop).
Revisit if: you observe models "loop" via near-identical-but-not-exact
calls in practice (e.g. re-ordering dict keys before we serialize them —
note we already sort keys for this reason, see `loop.py`'s `call_key`).

### D-303: A tool ERROR is fed back to the model, never raised out of the loop
Options:
  A) Let a tool exception propagate up and crash the whole agent run.
     — pros: simplest code. cons: one flaky tool call (e.g. a transient
       DB lock) kills an otherwise-successful investigation.
  B) Catch `ToolError`/`ToolPermissionError`, turn it into an "error: ..."
     observation, and let the model see it and decide what to do next —
     exactly like a human investigator whose command failed and who
     tries something else.
Chosen: B
Why: an agent's whole value proposition is adapting to what it finds —
that has to include adapting to failures, not just successes. See
`test_tool_error_is_fed_back_not_raised`.
Revisit if: certain tool errors should be UNRECOVERABLE and stop the run
immediately (e.g. a security violation) — those should raise a distinct
exception type the loop explicitly does NOT catch, rather than reusing
`ToolError` for both "retryable" and "fatal" cases.

### D-304: Write tools are simply not OFFERED to a read-only agent
Options:
  A) Register write tools normally; rely on `ToolRegistry.invoke`'s
     `allow_write` gate to refuse them at call time.
     — pros: one registry serves both read-only and write-allowed agents.
       cons: the model can still SEE the tool exists (it's in the spec
       list sent to it) and may try to call it, wasting a step on a
       call that was always going to be refused.
  B) `ToolRegistry.specs(allow_write=False)` doesn't even include write
     tools in the list handed to the model — see `AgentLoop.run`'s
     `tool_specs = self.registry.specs(allow_write=self.allow_write)`.
Chosen: B (with A's gate kept too, as defense in depth)
Why: the model can't ask for what it doesn't know exists. This also
means a read-only agent's step budget is never wasted on an attempted
(and refused) write call. The `allow_write` check inside `invoke()` stays
as a second layer, in case a caller ever builds `tool_specs` incorrectly.
Revisit if: never — defense in depth here is cheap and worth keeping.

### D-305: Short-term memory trims by character count, not real tokenization
Options:
  A) Use a real tokenizer to count tokens precisely before trimming.
     — pros: accurate. cons: adds a dependency, and precision doesn't
       change the TEACHING point (there is SOME budget, and SOMETHING
       has to be evicted).
  B) Approximate with character count (`ConversationMemory.max_chars`).
Chosen: B
Why: the lesson here is "the context window is finite, decide an
eviction policy" — the exact conversion ratio doesn't change that
lesson. A real system integrating with a specific model's SDK would use
that SDK's token counter instead.
Revisit if: you're building something real — swap the character count
for the model's actual token counter before trusting this in production.
