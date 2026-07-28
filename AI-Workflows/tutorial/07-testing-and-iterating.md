# Chapter 7 — Testing and Iterating

← [Chapter 6 — Workflows vs. Other Tools](06-workflows-vs-other-tools.md) · [Learning path](../learning-path.md) · Next: [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md)

---

## Where you left off

Your five-angle review workflow works. You've tested it on the PR that started this whole tutorial, and it correctly caught the real issues while your verification step correctly rejected the line-84 false alarm.

Rahul asks if the whole team can start using it. Before you say yes, you think back to how you tested your skills in AI-Skills — a handful of real tries, in the phrasing that felt natural to you.

That worked for a skill. A workflow has a different kind of thing that can quietly break, and trying it a few times on the same PR won't catch it.

---

## What you'll learn

1. How to test that a workflow's *structure* — not just its output — behaves the way you designed it.
2. How to test a verification stage properly: does it reject bad findings without also rejecting good ones?
3. How to decide, with real evidence, whether a workflow is ready to share.

---

## The lesson

### Two different things to test, again

You did this for skills too, and the same split applies here, adapted.

**Question 1 — Does the output look right, for one input?** This is what you already tested, informally, on the PR that started this tutorial.

**Question 2 — Does the structure actually behave the way you designed it, across different, realistic inputs?** This is the one that's new, and it's the one that actually matters most for a workflow specifically — because a workflow's whole value is in its *shape*, not just what any single `agent()` call produces.

A workflow can pass Question 1 perfectly on your one test PR and still have a real structural bug that only shows up on a bigger PR, or a PR shaped differently than the one you happened to test with.

### Testing the shape, not just the output

Go back to Chapter 4's pipeline vs. barrier lesson. If you built a pipeline believing it would let fast items finish while a slow item was still working, **that's a specific, testable claim** — and you should actually test it, not just assume your code did what you meant.

```
TEST: pipeline behavior with a deliberately slow item

Setup: 4 fast files + 1 file made deliberately slow (very large, or
       complex enough to genuinely take longer)

Expected: the 4 fast files' results should be available well before
          the slow file finishes — NOT all 5 arriving together at
          the same time, which would mean you accidentally built a
          barrier instead of a real pipeline.

Result: [record what actually happened]
```

This single test catches a real, common mistake: writing `pipeline(...)` correctly in syntax, but structuring the stages in a way that accidentally forces everything to wait anyway — for instance, if a later stage secretly depends on a shared resource that serializes everything, even though the code looks like a pipeline. The only way to know your pipeline is a *real* pipeline, and not a barrier wearing a pipeline's syntax, is to test it with a genuinely uneven mix of fast and slow items and watch what actually happens.

### Testing the verification stage properly

You did an informal version of this at the end of Chapter 5. Now formalise it into a real test set you keep, the same way you kept a trigger test set for skills.

```
WORKFLOW: pr-five-angle-review — verification stage

SHOULD BE REJECTED (deliberately planted false findings):
1. "Line 84 stores the token unencrypted" (wrong line — real token
   handling is at line 91)                          → ✅ rejected
2. "No tests were added" (a test file WAS added, under a slightly
   different, easy-to-miss name)                     → ✅ rejected
3. "This function is never called" (it IS called, from a file the
   reviewer didn't look at)                          → ✅ rejected

SHOULD BE CONFIRMED (genuinely real findings):
4. "Line 91 stores the token unencrypted" (actually true)
                                                       → ✅ confirmed
5. "Missing a test for the empty-input case" (genuinely missing)
                                                       → ✅ confirmed
```

Notice this test set has the same two-sided shape as a skill's trigger test from AI-Skills — some things that should be caught, some things that shouldn't. **A verifier that rejects everything would pass the first three tests and fail the last two.** You need both sides to know whether it's actually working, or just being maximally suspicious of everything it sees, which isn't the same thing as being accurate.

### Testing at realistic scale

This is the test most people skip, and it's the one that actually matters for a workflow specifically, because the whole point of a workflow is coordinating *more than one* piece of work — its behaviour at 1 item and its behaviour at 50 items can genuinely differ.

Run your workflow at three sizes:

| Size | What you're checking |
|---|---|
| **1 item** | Does the basic logic work at all? (Your first sanity check, same as any skill.) |
| **A realistic normal size** | Does it behave the way you designed — real parallelism, real pipeline overlap? |
| **A deliberately large size** | Does anything break, slow down disproportionately, or silently start behaving differently? |

That third row catches real problems the first two never will. A workflow that works cleanly on 5 items can behave completely differently on 50 — not because the logic is wrong, but because assumptions that were invisible at small scale (like "there's always exactly one slow item") stop holding.

### Run it more than once, same as before

Same lesson from AI-Skills, still true here: AI output isn't perfectly identical between runs. Run your test inputs two or three times each. You're checking that the **structure and correctness** hold consistently — not that the wording is identical every time. A verification stage that catches your planted false finding 2 times out of 3 is not reliable enough to trust yet, and running it only once would never have told you that.

### Deciding if it's ready

**Ready to share, if:**
- Your structural tests confirm the shape actually behaves as designed — real parallelism where you intended it, real pipeline overlap where you intended it.
- Your verification test set passes on both sides — rejects planted false findings, confirms genuinely real ones — consistently across repeated runs.
- Behaviour holds at a realistic scale, not just on your smallest test case.

**Not ready yet, if:**
- A "pipeline" behaves like a barrier under testing — go back to [Chapter 4](04-parallel-vs-pipeline.md) and check your stages for a hidden shared dependency forcing everything to wait.
- Verification rejects everything, or confirms everything — go back to [Chapter 5](05-fan-out-and-verify.md)'s wording lesson; you likely need "try to find a reason this is wrong," not a softer confirmation-style prompt.
- Something changes meaningfully between your small test and your large-scale test — that's a real bug worth finding now, not after the whole team is relying on it.

**Keep a log**, the same as you did for skills — what you tested, what size, what the result was. The next time you touch this workflow, you'll want to re-run these exact tests and compare, not start from zero.

---

## Try it yourself

1. Take a workflow you've built. Design one structural test — something that checks the *shape* behaves as designed, not just that the output looks reasonable.
2. If it has a verification stage, build a real two-sided test set: planted false findings that should be rejected, real findings that should be confirmed.
3. Run your workflow at three sizes — 1 item, a realistic size, and a deliberately larger size. Note anything that changed in a way you didn't expect.
4. Decide, honestly, using the criteria above: is this ready to share? If not, name the specific thing that needs to change.

---

## What's still missing

You now have real, structural evidence that your workflow works — not just a feeling. Divya has seen it and wants the same "check from several angles, verify what you find" pattern for her own frontend work.

Sharing a workflow properly turns out to raise a question skills never did: **should this even be allowed to run automatically, the way a skill does — or does something that coordinates this much work need a person to actually decide, each time, to run it?**

That's the next chapter.

---

← [Chapter 6 — Workflows vs. Other Tools](06-workflows-vs-other-tools.md) · [Learning path](../learning-path.md) · Next: [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md)
