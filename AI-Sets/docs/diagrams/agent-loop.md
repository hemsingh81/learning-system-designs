# Diagram: the agent loop, one step at a time

This is what happens inside `src\aisets\agent\loop.py`, in the same shape
as a backend `while` loop with a request/response cycle to an external
system (the model) plus a set of internal calls (the tools).

```
step = 0
history = [ system_prompt, user_question ]

while step < MAX_STEPS:
    step += 1

    # 1. THINK — ask the model: "given everything so far, what next?"
    response = llm.complete(history, tools=available_tools)

    # 2a. Model decided it has enough to answer.
    if response.is_final_answer:
        return response.text

    # 2b. Model decided to call a tool.
    tool_call = response.tool_call
    if seen_before(tool_call):            # loop-detection guard
        return "I'm repeating myself — stopping to avoid a loop."

    # 3. ACT — actually run the tool (this touches the real world:
    #    a database, a log file, a metrics API).
    try:
        result = run_tool(tool_call)
    except ToolError as e:
        result = f"error: {e}"            # the model SEES the error and
                                           # can decide to try something else

    # 4. OBSERVE — put the result back into the conversation so the next
    #    THINK step can use it.
    history.append(tool_call)
    history.append(result)

# Step budget used up without a final answer.
return "I could not finish within the step budget — escalating."
```

**Why the step budget matters:** without it, a confused model can call the
same tool forever, burning time and money with no result. This is the
agent-level version of an infinite retry loop in normal backend code —
same bug class, same fix (a max-attempts counter).
