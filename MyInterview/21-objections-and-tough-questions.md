# 21 · Objections & Tough Questions (10 rebuttals)

[← AI-Assisted Development](20-ai-assisted-development.md) · [Home](README.md) · [Next → Panic Sheet](22-panic-sheet.md)

These are the hard, sometimes uncomfortable challenges an interviewer throws to test how I hold up. The goal is not to be defensive — it is to answer calmly, honestly, and turn each one into proof of a strength. Every rebuttal here is short on purpose: say it, land one example with a number, stop.

> **My rule for tough questions:** *agree with the fair part, correct the wrong part, then give one piece of evidence.* No arguing, no waffle.

**Jump to:**
[O1 Still hands-on enough?](#o1--youre-an-architect--are-you-still-hands-on-enough) · [O2 Only 7 years as architect](#o2--only-7-years-as-an-architect--wheres-the-depth) · [O3 Jack of all trades](#o3--full-stack-sounds-like-jack-of-all-trades-master-of-none) · [O4 Just Microsoft](#o4--you-only-know-the-microsoft-stack) · [O5 Can you still code fast?](#o5--architects-get-rusty--can-you-still-code-under-pressure) · [O6 Big-picture or details?](#o6--are-you-a-big-picture-person-or-a-details-person) · [O7 Managed vs built](#o7--did-you-actually-build-it-or-just-manage-people-who-did) · [O8 AI will replace this](#o8--wont-ai-just-do-the-architects-job-soon) · [O9 Overqualified](#o9--youre-overqualified-for-this-role) · [O10 Biggest weakness](#o10--whats-your-biggest-weakness) · [Section index](#section-index)

---

## O1 · "You're an architect — are you still hands-on enough?"

**Answer.** Yes — I write production code every week, not just diagrams. On the TCW reporting platform (A) I personally built the FastAPI ETL services that ingest Aladdin, wrote the reusable Web API pattern the team now reuses, and hand-tuned the SQL behind the deadline-critical reports. I design top-down and I still build bottom-up.

That is deliberate. Nineteen years of writing code is exactly why my architecture survives contact with reality — I do not design things my team then cannot build.

**Follow-ups**
- *"When did you last write code?"* — This week. I use GitHub Copilot daily and still open the editor on the hard problems myself.
- *"Prove it in this interview."* — Happy to. Open the hood — I'll write the endpoint, the query, or the React component with you right now.

---

## O2 · "Only 7 years as an architect — where's the depth?"

**Answer.** Agreed on the number, but I have 19 years in software total, and the 12 before the architect title are what give the architecture its depth. I spent those years as a senior engineer and lead — writing code, setting code standards, and running teams. I earned the architecture, I did not jump to it.

And the seven years as architect are heavy ones: I authored TCW's AI/LLM reference architecture and shipped its first production RAG app (B), and I was solution architect for a four-app cloud platform for TengizChevroil (C). Depth is about what you shipped, not the year the title changed.

**Follow-ups**
- *"What's the most complex thing you've owned?"* — The reporting platform end to end (A): app tier, Web API, and a daily pipeline that must land inside the pre-market window — correctness and a hard clock at once.
- *"Ever been in over your head?"* — Yes, the first production RAG app — new ground for the firm. I closed the gap by building evaluation and governance in from day one rather than guessing.

---

## O3 · "Full-stack sounds like jack of all trades, master of none."

**Answer.** Fair worry, so let me be precise. I am not equally deep in everything — I am deepest in the Microsoft/.NET back end and the data layer, which is where the hard problems live. React, Angular and Python are tools I use fluently to deliver the whole slice, not areas where I claim to be the last word.

Being full-stack is what lets me design systems that actually fit together — I have felt the pain at every seam. A back-end-only architect designs an API the front end hates; I have written both, so I don't.

**Follow-ups**
- *"Where are you deepest?"* — .NET/C#, API design, and SQL/data platforms. That's my core; the rest supports it.
- *"Where are you weakest?"* — Deep front-end visual/CSS craft — I build correct, accessible UIs, but for pixel-perfect design systems I lean on a specialist, and I know to.

---

## O4 · "You only know the Microsoft stack."

**Answer.** Microsoft/Azure is my centre of gravity, yes — and that is a strength for a role on that stack. But I am not boxed in: my ETL services are Python/FastAPI, my analytical store is Snowflake (not Microsoft), my orchestration includes Apache Airflow, and my AI work is LangChain/LangGraph on Chroma. I pick the right tool per job, then integrate it cleanly with Azure.

The principles — clean seams, testability, observability, cost control — are platform-independent. The stack is where I'm fluent; the thinking travels.

**Follow-ups**
- *"Could you work on AWS?"* — Yes — the services map across (App Services→ECS/App Runner, Functions→Lambda, Azure SQL→RDS). I'd be productive quickly because the architecture patterns are the same.
- *"Why so much Azure then?"* — Because my last clients were Azure shops and I go deep where I deliver. Depth on one cloud beats shallow on three.

---

## O5 · "Architects get rusty — can you still code under pressure?"

**Answer.** I stay sharp because I never stopped. I still debug production issues in code, tune slow queries live, and review pull requests where I have to read every line and catch the subtle bug. That is coding under real pressure — a broken report with a 6 a.m. deadline concentrates the mind more than any whiteboard.

So test me. I'm comfortable in a live coding round — I'll clarify the problem, state my approach and its complexity, write clean code, and test the edges.

**Follow-ups**
- *"How do you handle a coding round you can't immediately solve?"* — Out loud: restate the problem, start with the brute force, then improve it — interviewers score the thinking, not just the finish.
- *"DSA or feature-building?"* — Both. I prep patterns for algorithm rounds and real feature-building for practical rounds — see [18 Coding-Round Prep](18-coding-round-prep.md).

---

## O6 · "Are you a big-picture person or a details person?"

**Answer.** Both, and switching between them on demand is the actual job. Big picture: I own the reporting platform's whole architecture and how its pieces fit. Details: I hand-tune the one query that threatens the deadline. An architect who can only do one of these is dangerous — grand designs that don't run, or clever code with no shape.

The trick is knowing *which* mode a moment needs. Design review → zoom out. Production incident at 3 a.m. → zoom all the way in.

**Follow-ups**
- *"Give an example of switching."* — A slow report: I zoomed in to fix the query and the N+1, then zoomed out to add the operational/analytical store split so the class of problem couldn't recur.
- *"Which do you enjoy more?"* — Honestly, the moment they meet — when a detail I fixed proves a design decision was right.

---

## O7 · "Did you actually build it, or just manage people who did?"

**Answer.** Both, clearly separated. I led the teams *and* I built the hard parts myself. On A, I personally wrote the FastAPI ingestion services, the reusable Web API pattern, and a DB utility generator that removed repetitive data-access code for the whole team — while also setting the code standards and running the reviews.

I'm careful to say "I" for what I built and "we" for what the team delivered. I won't claim a team's work as my keystrokes, and I won't hide behind the team either.

**Follow-ups**
- *"What did the team do vs you?"* — I built the patterns and the critical path; the team built the many report modules on top of the pattern I created. That's the leverage of a hands-on architect.
- *"How do you stay hands-on while leading?"* — I take the riskiest or most reusable piece myself, so my code sets the bar and unblocks everyone else.

---

## O8 · "Won't AI just do the architect's job soon?"

**Answer.** AI makes me faster, it doesn't make the judgement calls. It can generate code and draft options, but it can't own a trade-off, be accountable to a regulator, or decide what "correct" means for the business. Those are the architect's job, and they're getting *more* valuable as code gets cheaper to produce.

I actually lean into this. I built TCW's AI reference architecture and I have a full playbook for bringing AI into a team safely — roles, guardrails, metrics ([20 AI-Assisted Development](20-ai-assisted-development.md)). The architect who knows how to *govern* AI is the one it can't replace.

**Follow-ups**
- *"So AI writes the code and you review?"* — Often, yes — but I read every line and I'm accountable for it. AI is a fast junior pair, always reviewed.
- *"Where would you never let AI decide?"* — Auth, cryptography, money logic, and anything a regulator will audit. AI can explain; a human writes and owns those.

---

## O9 · "You're overqualified for this role."

**Answer.** I hear that as "will you stay and will you stay engaged?" — both fair. I stay engaged because I still build; the day-to-day of designing and coding hard systems is what I enjoy, not a title. And I'm not looking to sit above the work — I'm looking for exactly this kind of hands-on ownership.

More seniority than the minimum is upside for you, not a risk: I de-risk the hard decisions early and mentor the team as I go, so you get an architect and a force-multiplier in one.

**Follow-ups**
- *"Won't you get bored?"* — I get bored by *not* being hands-on. A role where I own design and still code is the opposite of boring for me.
- *"Why not a bigger title elsewhere?"* — I optimise for the problem and the team, not the title. Interesting, high-ownership work keeps me longer than a grander label.

---

## O10 · "What's your biggest weakness?"

**Answer.** My instinct is to take the hardest or most critical piece myself — which is great for quality but can make me a bottleneck if I'm not careful. I noticed it when a release waited on a component only I understood.

So I actively counter it: I write the reusable pattern rather than the one-off, document the critical path, and deliberately pair a team member on anything only I know. On A, turning my data-access work into a generator the team could use was exactly this fix — my depth became the team's leverage instead of a dependency on me.

**Follow-ups**
- *"A technical weakness, specifically?"* — Deep front-end visual/CSS craft. I build correct, accessible UIs but bring in a specialist for design-system polish — and I know when to.
- *"How do you know you've improved?"* — The bus-factor test: if a component only I understand, that's a smell I now fix before it ships, not after it blocks a release.

---

## Section index

| # | The challenge | My one-line rebuttal |
|---|---|---|
| O1 | Still hands-on? | I write production code every week — open the hood and I'll prove it |
| O2 | Only 7 years as architect | 19 years total; the 12 before earned the depth the title sits on |
| O3 | Jack of all trades | Deepest in .NET/data; full-stack so my systems actually fit together |
| O4 | Only Microsoft | Azure-centred but Python, Snowflake, Airflow, LangChain too; principles travel |
| O5 | Rusty coder | I debug, tune and review in production — test me in a live round |
| O6 | Big-picture or details | Both, on demand — zoom out for design, zoom in for the deadline query |
| O7 | Built or just managed | "I" for what I built, "we" for what the team shipped — I did both |
| O8 | AI replaces architects | AI speeds the code; it can't own the trade-off or the accountability |
| O9 | Overqualified | Seniority is upside — I stay engaged because I still build |
| O10 | Biggest weakness | I over-own the hard part; I fix it by turning depth into reusable leverage |

---

[← AI-Assisted Development](20-ai-assisted-development.md) · [Home](README.md) · [Next → Panic Sheet](22-panic-sheet.md)
