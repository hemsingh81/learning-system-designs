# Chapter 4 — Writing Trigger Descriptions

← [Chapter 3 — Your First Skill](03-your-first-skill.md) · [Learning path](../learning-path.md) · Next: [Chapter 5 — Tools and Scripts](05-tools-and-scripts.md)

---

## Where you left off

Your commit-message skill worked — sometimes. It fired correctly on your main test phrase. It fired when it shouldn't have, once. It missed a slightly different phrasing of a request it should have caught.

You know the description is the problem. You don't yet know the actual rule for fixing it.

This chapter is that rule. If you only remember one chapter from this whole tutorial, make it this one — this is where almost every real skill problem actually lives.

---

## What you'll learn

1. Exactly why a skill triggers on some requests and not others.
2. How to spot a vague description, and say precisely why it's vague.
3. How to rewrite a bad description into a good one, using a repeatable method.

---

## The lesson

### Go back to the company directory

In Chapter 1, you compared a skill's description to a one-line job title in a company directory. Hold onto that picture — it explains almost everything in this chapter.

Imagine a directory with two entries:

```
Priya — "helps with stuff"
Karan — "handles payroll questions: salary, tax deductions, and payslip access"
```

If someone has a payroll question, who do they go to? Obviously Karan — his one-liner tells them exactly when he's the right person. Priya's entry is technically true. It's also useless, because it doesn't tell anyone *when* to pick her over anyone else.

A skill's description works exactly like this. Your assistant is scanning a list of one-liners, deciding which skill — if any — matches the current request. **A vague description is Priya. A good description is Karan.**

### The two failure modes, properly explained

You saw both of these happen in Chapter 3. Now let's name them precisely.

**Too broad — false triggers.** The description is written so loosely that it matches requests it shouldn't. "Helps with commits" matches almost anything commit-related: writing one, explaining one, reverting one, squashing several. Your skill fires on requests it has no business handling, and produces output nobody asked for.

**Too narrow — missed triggers.** The description is tied so tightly to one exact phrasing that a request has to almost quote it back to trigger correctly. If your description only mentions "commit message" and someone says "help me commit these changes," it might not connect the two.

Here's the important part: **these are opposite problems, but they come from the same mistake** — writing the description the way it feels natural to write it, instead of testing it against the real range of ways people actually ask for things.

### The two-sentence shape, properly explained

You saw this shape in Chapter 2's example. Now here's why it works, not just what it looks like.

```
[WHAT it does]. Use when [WHEN to reach for it, described broadly enough
to cover real variation, narrowly enough to exclude what it's not for].
```

**The "what" sentence** exists so a human skimming a list of skills can understand what this one produces, at a glance.

**The "when" sentence** is doing the actual triggering work. This is where broad-enough-but-not-too-broad lives. Notice it's not one exact phrase — it's a *description of a category of request*.

Compare:

```
❌ Use when the user says "write a commit message"
```

versus

```
✅ Use when the user asks for a commit message, or asks to commit
   their changes, or asks how to describe a set of code changes
```

The first only matches one phrasing. The second describes the actual *category* — several different ways a person might really ask for the same underlying thing. That's the difference between narrow and correctly broad.

### The method: write it, then attack it

Here's a repeatable process. Use this every time you write a description, not just this once.

**Step 1 — Write the two-sentence shape.** What it does, then when to use it.

**Step 2 — List 5 real phrasings that SHOULD trigger it.** Not one. Five. Write them the way different real people actually talk — some terse, some detailed, some using different words for the same idea.

```
1. "write a commit message for this"
2. "can you commit these changes for me"
3. "describe what I just changed, for a commit"
4. "help me write a commit message following our format"
5. "commit this with a proper message"
```

**Step 3 — List 3 real phrasings that should NOT trigger it, but are close enough to be a real risk.** This step is the one people skip, and it's the one that actually catches over-broad descriptions.

```
1. "what makes a good commit message in general?" (asking for advice,
   not asking you to write one for real changes)
2. "revert my last commit" (a different action entirely, just shares
   the word "commit")
3. "squash these three commits into one" (also different — shares
   the word, not the task)
```

**Step 4 — Read your description against all 8, one at a time.** For each one, honestly ask: based only on this one-line description — not the full instructions — would this get picked correctly?

**Step 5 — If any fail, fix the description, not the instructions.** This is the part people get backwards. If a good request doesn't trigger, or a bad one does, the fix almost always belongs in the description, not in the detailed instructions underneath it. The instructions never even get read if the description doesn't get picked in the first place.

### Applying it to your commit-message skill

Let's run your actual skill from Chapter 3 through this process.

**Original:**
```
Writes a commit message following Kestrel's format
  (type(scope): description). Use when the user asks for a commit
  message, or asks to commit their changes.
```

Run it against the 8 test phrasings above. Sentences 1, 2, 4, and 5 clearly pass — they're close to the exact wording already in the description. Sentence 3, "describe what I just changed, for a commit," is shakier — nothing in the description hints that *describing changes* counts as the same request.

And check the "should not trigger" list: "revert my last commit" and "squash these three commits" both share the word "commit" but are clearly different actions — nothing in the description accidentally invites those in, which is good.

**Improved:**
```
Writes a commit message following Kestrel's format
  (type(scope): description), based on the actual code changes. Use
  when the user asks you to write, draft, or describe a commit
  message, or asks to commit their changes. Does NOT cover reverting,
  squashing, or amending existing commits.
```

Two changes, both earned by the test:

- **"write, draft, or describe"** widens the "when" sentence just enough to catch phrasing 3, without becoming so broad it catches things it shouldn't.
- **The explicit "does NOT cover" sentence** is a new, deliberate technique — an exclusion. You don't always need one, but when a skill's name or topic sits close to other actions (commit vs. revert vs. squash, all in the same neighbourhood), spelling out the boundary prevents the wrong skill from ever getting confused for the right one.

### When to add an explicit exclusion

Not every skill needs a "does NOT cover" line. Add one when:

- Your skill's topic sits near other, different tasks that share vocabulary (commit vs. revert, deploy vs. rollback, review vs. approve).
- You've actually observed a false trigger during testing — don't guess at exclusions preemptively, add them when the 8-phrase test in Step 3 turns one up for real.

Skip it when the skill is already narrow and distinctive enough that nothing realistically overlaps. Adding exclusions you don't need just makes the description longer and harder to skim.

---

## Try it yourself

1. Take your own skill's description from Chapter 3.
2. Write your own 5 "should trigger" phrasings and 3 "should not trigger" phrasings, based on how your actual teammates talk — not how you'd phrase it.
3. Run the description against all 8, honestly.
4. Rewrite it, fixing whatever failed. If nothing failed, try to break it — write a ninth phrasing designed specifically to confuse it, and see if it holds up.

---

## What's still missing

Your description is solid now. Your instructions still only cover what to *say* — writing text in the right format.

Some tasks need more than that. They need your skill to actually *do* something: run a real check, call a real script, look something up in a real file. Plain instructions can't do that on their own.

That's the next chapter.

---

← [Chapter 3 — Your First Skill](03-your-first-skill.md) · [Learning path](../learning-path.md) · Next: [Chapter 5 — Tools and Scripts](05-tools-and-scripts.md)
