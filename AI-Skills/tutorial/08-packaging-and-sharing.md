# Chapter 8 — Packaging and Sharing

← [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md) · [Learning path](../learning-path.md) · Next: [Chapter 9 — Governance and Capstone](09-governance-and-capstone.md)

---

## Where you left off

Your skill is tested and working. Divya wants to use it for her own team. Rahul mentions the platform team might want it too, eventually, across every repo at Kestrel.

Right now your skill is one folder on your laptop. "Send me the folder" works exactly once. It falls apart the moment you improve the skill next month and Divya is still running the old version, with no way to know that's even happened.

This chapter is how you actually share something people can depend on.

---

## What you'll learn

1. How to version a skill, so a change never surprises the people using it.
2. The three real levels of sharing — just you, your project, your whole company — and when each one fits.
3. How to write a changelog entry that actually tells people what they need to know.

---

## The lesson

### Why "just send the folder" breaks down

Imagine this timeline:

```
Week 1:  You give Divya the folder. It works great.
Week 3:  You improve the skill — you make the output format stricter,
         because you found a real problem with the old one.
Week 4:  Divya asks why her commit messages suddenly look different
         from yours. You realise she never got the update.
Week 6:  Someone on the platform team copies Divya's OLD version into
         a different repo. Now there are two different versions of
         the same skill, quietly drifting apart, and nobody can say
         which one is "correct" anymore.
```

Nothing about this is unusual. It's exactly what happens to any shared thing — code, a config file, a document — with no version and no single source of truth. Skills are no different, and the fix is the one you already know from software: **version it, and give it one real home.**

### Versioning a skill

You don't need anything complicated. Borrow the same idea you already use for code: a version number that goes up in a way that tells people something real about the change.

```
MAJOR.MINOR.PATCH

PATCH  →  Wording fix, no real change in behaviour
MINOR  →  New capability, but old requests still work the same way
MAJOR  →  Behaviour changed enough that someone relying on the old
          version would notice, and might need to adjust
```

Apply it to your commit-message skill's real history:

| Version | What changed | Why that category |
|---|---|---|
| 1.0.0 | First working version | — |
| 1.0.1 | Fixed a typo in the instructions | Wording only — **PATCH** |
| 1.1.0 | Added support for a `BREAKING CHANGE:` footer, when relevant | New capability, old behaviour unchanged — **MINOR** |
| 2.0.0 | Changed the scope field to always be lowercase, where it used to match the folder name's exact casing | Anyone whose tooling expected the old casing would now see different output — **MAJOR** |

Put the version directly in the skill file:

```markdown
---
name: kestrel-commit-message
version: 2.0.0
description: Writes a commit message following Kestrel's format...
---
```

**Why bother, for something this small?** Because the moment more than one person depends on a skill, "I changed something" stops being enough information. "I made a MAJOR change" tells Divya, at a glance, that she should actually look at what changed before she keeps relying on it. "I made a PATCH" tells her she doesn't need to think about it at all. That distinction is the entire value of a version number.

### Writing a changelog entry that's actually useful

Keep a plain file next to your skill — `CHANGELOG.md` is a fine, ordinary name — and add one short entry every time you change something real.

```markdown
# Changelog — kestrel-commit-message

## 2.0.0
Scope is now always lowercase, to match how our CI already
normalises branch names. Previously it matched the folder's exact
casing, which sometimes produced `Auth` instead of `auth`.

## 1.1.0
Added support for a BREAKING CHANGE footer when the change actually
breaks something. Optional — normal commits are unaffected.

## 1.0.1
Fixed a typo in the format description.

## 1.0.0
First version.
```

Notice each entry says **what changed and why**, not just what changed. "Scope is now lowercase" is a fact. "To match how our CI already normalises branch names" is the reason — and it's the reason that actually helps Divya decide whether this affects her.

### The three levels of sharing

This is the real answer to "how do I give this to Divya, and later, the whole company." Think of it as a ladder — you climb it as more people genuinely need what you built, not all at once, and not before it's ready.

**Level 1 — Personal.** The skill lives somewhere only you can see it. This is where every skill in this tutorial has lived so far. It's the right level for anything you're still actively changing, testing, or aren't sure is even useful yet. Nobody else is affected by your experiments.

**Level 2 — Project (shared through your repo).** The skill is checked into your team's actual git repository. Often in a dedicated folder, the same way your CI config already lives there. Once it's in the repo, **everyone who clones it gets the skill automatically.** No separate install step. No "did you get my email." It travels with the codebase, the same way a linter config does.

This is the right level once you've tested a skill properly (Chapter 7) and it's specific to how your team, and only your team, actually works. Divya's request fits here — if she's working in the same repo, checking your skill in gives it to her and everyone else on the project, permanently, without you doing anything else.

**Level 3 — Company-wide (a proper package, distributed like a library).** For a skill genuinely useful across many teams — not just yours — the honest answer is that this needs real packaging. Think of publishing a shared internal library, instead of copy-pasting the same function into ten repos. It's typically distributed as an installable package with its own name. A team pulls in "the commit-message skill" the same deliberate way they'd add any other internal dependency, and gets told when a new version is available — instead of silently drifting out of date.

**The exact mechanics of Level 3 differ between tools, and change over time.** This is one case where you genuinely should check your own tool's current documentation, rather than trust a fixed set of steps written down once. What stays true regardless of the exact mechanism: something used company-wide needs a real update path. A hundred people should never end up running a hundred slightly different, silently drifted copies of the same thing.

### Choosing the right level, honestly

| Question | If yes |
|---|---|
| Are you still actively changing or testing this? | **Level 1.** Don't share it yet. |
| Is it specific to your team's own conventions, and tested (Chapter 7)? | **Level 2.** Check it into your repo. |
| Would three or more genuinely separate teams want this, unmodified? | **Level 3.** It needs real packaging — this is also exactly when [Chapter 9](09-governance-and-capstone.md)'s safety review stops being optional. |

Notice the honest version of this table: **most skills should stop at Level 2, and that's a completely fine, successful outcome.** Not everything needs to become a company-wide package. A skill that makes your specific team faster, living in your specific repo, is a real win on its own — don't feel pressure to "graduate" it further than it actually needs to go.

---

## Try it yourself

1. Take your tested skill from Chapter 7. Give it a real version number — start at `1.0.0` if you haven't already.
2. Write its first changelog entry, in the "what changed, and why" shape shown above — even if the entry is just "first version."
3. Using the honest table above, decide which level it genuinely belongs at right now. Not where you'd *like* it to be — where the evidence actually puts it.
4. If it lands on Level 2, write down the one concrete step you'd take to check it into your team's actual repo.

---

## What's still missing

You know how to version, changelog, and share a skill properly. There's one thing you haven't been forced to think about yet: **what could go wrong if a skill like this ends up somewhere it shouldn't, or does something nobody meant for it to do.**

Rahul is about to show you exactly that — a real near-miss from another team's skill. That's the last chapter.

---

← [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md) · [Learning path](../learning-path.md) · Next: [Chapter 9 — Governance and Capstone](09-governance-and-capstone.md)
