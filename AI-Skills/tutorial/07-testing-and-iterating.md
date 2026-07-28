# Chapter 7 — Testing and Iterating

← [Chapter 6 — Skills vs. Other Tools](06-skills-vs-other-tools.md) · [Learning path](../learning-path.md) · Next: [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md)

---

## Where you left off

Your commit-message skill and your environment-check skill both work. You've tested each of them a handful of times, in the phrasing that feels natural to you.

Rahul asks if he can start using it. Before you say yes, an honest question stops you: you've tested it the way *you'd* ask. Have you tested it the way everyone else on the team actually asks?

You haven't. This chapter is how you actually find out if a skill is ready, instead of just hoping it is.

---

## What you'll learn

1. How to build a proper test set for a skill, not just a few ad-hoc tries.
2. The difference between a false positive and a false negative, and which one is worse for your specific skill.
3. How to decide, with evidence, whether a skill is ready to share.

---

## The lesson

### Two completely different things to test

There are two separate questions, and people often only check one of them.

**Question 1 — Does it trigger correctly?** Does the right request pick the skill, and does the wrong request correctly leave it alone? You started this in Chapter 4, with your 5-should-trigger and 3-should-not-trigger list.

**Question 2 — Once triggered, is the output actually correct?** Even if the skill fires perfectly every time, does it produce the right commit format? Does it actually run the script instead of guessing? Does it follow every rule you wrote?

These need separate testing, because they fail independently. A skill can trigger perfectly and still produce wrong output. A skill can have flawless instructions and never get the chance to run them, because the description never picks it up.

### Building a real trigger test set

You already did the hard thinking for this in Chapter 4. Now formalise it into something you keep, not something you did once and threw away.

```
SKILL: kestrel-commit-message

SHOULD TRIGGER:
1. "write a commit message for this"                          → ✅ triggered
2. "can you commit these changes for me"                       → ✅ triggered
3. "describe what I just changed, for a commit"                → ✅ triggered
4. "help me write a commit message following our format"       → ✅ triggered
5. "commit this with a proper message"                         → ✅ triggered

SHOULD NOT TRIGGER:
6. "what makes a good commit message in general?"              → ✅ correctly ignored
7. "revert my last commit"                                     → ✅ correctly ignored
8. "squash these three commits into one"                       → ✅ correctly ignored
```

Notice this is exactly your Chapter 4 list, now with results recorded next to each line. That's the whole trick — you're not inventing new work, you're **keeping a record** of work you were already doing informally, so you can re-run it later and actually know if something changed.

### False positives and false negatives — and why the difference matters

Borrow two words from testing in general, and apply them here.

**A false positive** is when the skill triggers but shouldn't have — line 6, 7, or 8 above, if any of them had wrongly triggered.

**A false negative** is when the skill should trigger but doesn't — line 1 through 5, if any of them had been missed.

Here's the part that actually matters: **these two mistakes are not equally bad, and which one is worse depends entirely on what the skill does.**

For your commit-message skill, a false negative is mildly annoying — you just type your request again, differently, or write the message yourself. Low cost.

Now imagine a different skill — one that automatically flags a pull request as "safe to merge" based on a review. A false positive there — the skill wrongly saying something is fine when it wasn't checked properly — is a real problem. It could let something genuinely broken through, with a false sense of confidence attached to it.

**The rule:** before you decide a trigger rate is "good enough," ask which mistake your specific skill makes worse — missing it, or wrongly claiming it. Then test harder for whichever one actually costs you something.

### Testing the output, not just the trigger

Once you know it triggers correctly, check what it actually produces. Build a small set of real inputs and check the output against your actual rules, line by line.

```
TEST: commit message for a change to src/auth/login.ts fixing a null check

Rule                                    Pass?
─────────────────────────────────────────────
Format is type(scope): description       ✅
Type is "fix" (correct for a bug fix)     ✅
Scope reflects the actual changed file    ✅  ("auth")
Under 72 characters                       ✅
Imperative mood ("fix", not "fixed")      ✅
No trailing period                        ✅
```

This looks tedious the first time. It takes two minutes. Do it for 3 to 5 real, different inputs — not the same input five times — and you'll find real problems you wouldn't have caught by eye. A skill that gets the format right on a simple one-line change might get the scope wrong on a change that touches three different folders. You won't know until you actually try it.

### Run the same test more than once

Here's something that surprises people the first time. AI assistants don't always give the exact same output for the exact same input — the wording can vary slightly even when nothing about the request changed.

Run your test inputs **two or three times each**, not just once. You're not checking that the wording is identical every time — that's not the bar. You're checking that the *substance* stays correct every time: the format holds, the rules are followed, the facts are right. Small wording differences are fine and expected. A rule that holds sometimes and not other times is not fine, and running the same test once will never catch that — you'll just get lucky or unlucky and think you learned something you didn't.

### Deciding if it's ready

You now have real evidence, not a gut feeling. Use it honestly.

**Ready to share, if:**
- Every "should trigger" test actually triggered, across repeated runs.
- Every "should not trigger" test correctly stayed quiet, across repeated runs.
- Output tests pass your actual rules consistently, not just on the easiest example.

**Not ready yet, if:**
- Any trigger test is inconsistent — sometimes works, sometimes doesn't. Go back to Chapter 4's description work — inconsistency here almost always means the description still isn't specific enough.
- Output is right on simple inputs but wrong on more complex or unusual ones. Go back to Chapter 3's instruction-writing — you likely need a rule for the case you just found.

**Keep a simple log.** Just a plain text file next to your skill, recording what you tested and when. You don't need anything elaborate — but the next time you change the skill, having a record of what already worked means you can check you haven't broken it, instead of starting from zero every time.

---

## Try it yourself

1. Take a skill you built in an earlier chapter.
2. Build a real trigger test set — 5 should-trigger, 3 should-not-trigger — if you don't already have one from Chapter 4.
3. Run each trigger test twice. Note anything inconsistent.
4. Pick 3 different real inputs and test the actual output against your rules, line by line, like the table above.
5. Decide, honestly, using the criteria above: is this ready to share, or not yet? Write down which specific thing would need to change if the answer is "not yet."

---

## What's still missing

You now have real, tested evidence that your skill works. Divya has heard about it and wants to use it for her own team.

Right now, your skill just lives in a folder on your machine. Getting it to Divya — properly, in a way that doesn't quietly break when you update it later — is a different problem than the one you've solved so far.

That's the next chapter.

---

← [Chapter 6 — Skills vs. Other Tools](06-skills-vs-other-tools.md) · [Learning path](../learning-path.md) · Next: [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md)
