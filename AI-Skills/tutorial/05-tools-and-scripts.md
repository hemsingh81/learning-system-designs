# Chapter 5 — Tools and Scripts

← [Chapter 4 — Writing Trigger Descriptions](04-writing-trigger-descriptions.md) · [Learning path](../learning-path.md) · Next: [Chapter 6 — Skills vs. Other Tools](06-skills-vs-other-tools.md)

---

## Where you left off

Your commit-message skill triggers reliably now. Vikram sees it and asks for something harder: a skill that checks whether every environment variable a new hire needs is actually set up on their machine, and tells them exactly which ones are missing.

You try writing it the same way — plain instructions, no different from your commit-message skill:

```markdown
Check if the required environment variables are set. Required
variables: DATABASE_URL, API_KEY, REDIS_URL. Tell the user which
ones are missing.
```

It doesn't work reliably. Sometimes it guesses instead of actually checking. This chapter explains why, and what to do differently.

---

## What you'll learn

1. When a skill needs a real, bundled script — not just instructions.
2. How to reference a script correctly from inside a skill.
3. The real risk a script-running skill introduces, and why it matters.

---

## The lesson

### Why instructions alone failed here

Go back to your commit-message skill for a second. What did it actually need to do? Read some code, apply a format, produce text. All of that is exactly the kind of task your assistant is naturally good at — reading, reasoning, writing.

Now look at the environment-variable check. What does it actually need? To look at *your specific machine*, right now, and report a true or false fact about it — is this variable actually set, or not.

That's a fundamentally different kind of task. It's not about reasoning or writing well. It's about **checking a real, current fact about a real system.** Your assistant can't reliably "reason its way" to knowing what's in your environment variables — it has to actually go look.

**The rule:** if a task requires checking a real, current fact — reading a real file, running a real command, calling a real API — plain instructions aren't enough on their own. You need the skill to actually run something.

### The two kinds of skill content

You've been building skills with one kind of content so far: instructions the assistant reads and follows using its own judgement. There's a second kind: **things the skill can actually execute** — scripts, commands, small programs.

```
your-skill-name/
├── SKILL.md              ← name, description, instructions
└── scripts/
    └── check-env.sh       ← a real script the skill can run
```

The instructions inside `SKILL.md` now do something new — they tell your assistant *when* and *how* to run the bundled script, instead of trying to describe the whole check in prose.

### Rewriting the environment-variable skill

Here's the script itself. Simple, plain, does exactly one job:

```bash
#!/bin/bash
# scripts/check-env.sh
# Checks that required environment variables are set. Prints any
# that are missing, one per line. Exits with code 1 if any are missing.

REQUIRED_VARS=("DATABASE_URL" "API_KEY" "REDIS_URL")
MISSING=()

for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    MISSING+=("$VAR")
  fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
  echo "All required environment variables are set."
  exit 0
else
  echo "Missing environment variables:"
  printf '  - %s\n' "${MISSING[@]}"
  exit 1
fi
```

And here's the skill file that wraps it:

```markdown
---
name: kestrel-env-check
description: Checks whether a developer's local environment has all
  required variables set (DATABASE_URL, API_KEY, REDIS_URL). Use when
  the user asks to check, verify, or set up their local environment,
  or reports something isn't working and might be a missing config
  issue.
---

Run the bundled script `scripts/check-env.sh` to check the current
environment.

Do NOT guess or assume which variables are set. Always run the
script and report its actual output.

If variables are missing, tell the user which ones, and point them
to the setup doc at docs/local-setup.md for how to obtain each value.

If all variables are set, confirm that clearly and briefly — do not
add unnecessary detail.
```

Notice the instruction **"Do NOT guess or assume which variables are set. Always run the script."** This line exists for the exact reason your first attempt failed. Without it, your assistant might reason about what's *probably* set, based on the conversation so far, instead of actually checking. Being explicit about *never guessing, always checking* is what makes this reliable.

### The real risk: a skill that can act, not just talk

Here's the part of this chapter that matters most, and it's worth slowing down for.

Your commit-message skill could only produce text. If it got something wrong, the worst outcome was a badly worded commit message — annoying, but harmless. Nothing it did was permanent until a human chose to use the output.

A skill that runs a real script is different. It can read files. Depending on what you allow it to do, it could write files, delete things, or call external services. **The moment a skill can act instead of just talk, a mistake stops being merely annoying and starts being potentially real.**

This isn't a reason to avoid scripts — plenty of real, valuable tasks genuinely need them, exactly like the environment check above. It's a reason to be deliberate about *what* you let a skill's script actually do.

A few concrete habits, starting now, that you'll expand on properly in [Chapter 9](09-governance-and-capstone.md):

**Keep scripts narrow.** `check-env.sh` does exactly one job — reads variables, reports them. It doesn't modify anything. A script that only reads is far safer than one that writes or deletes.

**Make destructive actions require a real confirmation**, not just "the assistant decided this was fine." If a script could delete something or send something externally, that's a different category of skill from the one you just built, and it deserves the safety review covered in Chapter 9 — not just a plain instruction telling it to "be careful."

**Never bundle a script that reads secrets and sends them anywhere.** `check-env.sh` correctly checks *whether* a variable is set — it never prints the *value*. That distinction matters. Reporting "DATABASE_URL is missing" is safe. Reporting "DATABASE_URL is set to `postgres://user:hunter2@...`" is not, even though it might feel like it's being more helpful.

### When you don't need a script at all

Not every check needs one. Before reaching for a script, ask: **can the assistant get what it needs just by reading files that are already visible to it in the conversation?**

If you're checking something in a file the assistant can already read directly — a config file, a piece of code, a document — plain instructions describing what to look for are often enough, the same way your commit-message skill worked. Reach for a script specifically when the check needs to *run something* — execute a command, query a live system, compute something that reading alone can't answer.

---

## Try it yourself

1. Take a real, small check your team does by hand — something that has an actual true/false or pass/fail answer, not something that needs judgement.
2. Write the smallest possible script that performs that check.
3. Wrap it in a skill file, using the pattern above. Include the "do NOT guess, always run the script" instruction.
4. Ask yourself the safety question from this chapter: does this script only read, or does it also write or delete something? Write down your honest answer.

---

## What's still missing

You can now build skills that check real things, not just produce text. Rahul, watching all this, asks a fair question: "Why is this a skill and not just a subagent? Or a hook that runs the check automatically?"

You don't have a confident answer yet. Neither did anyone, the first time they were asked.

That's the next chapter.

---

← [Chapter 4 — Writing Trigger Descriptions](04-writing-trigger-descriptions.md) · [Learning path](../learning-path.md) · Next: [Chapter 6 — Skills vs. Other Tools](06-skills-vs-other-tools.md)
