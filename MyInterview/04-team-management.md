# 04 · Team Management (10 questions)

[← System Design](03-system-design.md) · [Home](README.md) · [Next → Client Engagement](05-client-engagement.md)

I lead as an architect, not as a line manager. That means I have influence rather than authority most of the time — I do not usually control salaries or promotions. So my leadership has to come from clarity, from being right often enough to be trusted, and from making other people better. Every answer below is written from that position, because that is the honest one.

**Jump to:** [T1](#t1--tell-me-about-a-time-you-led-a-team-through-a-major-technical-change) · [T2](#t2--how-do-you-onboard-a-new-engineer-onto-a-complex-platform) · [T3](#t3--how-do-you-assess-an-engineer-in-an-interview) · [T4](#t4--two-senior-engineers-disagree-strongly-on-an-architecture-decision-what-do-you-do) · [T5](#t5--how-do-you-mentor-give-me-a-specific-example) · [T6](#t6--scope-changed-mid-sprint-how-did-you-handle-it) · [T7](#t7--you-have-to-tell-a-stakeholder-the-date-is-slipping-walk-me-through-it) · [T8](#t8--how-do-you-keep-a-team-motivated-on-a-long-unglamorous-project) · [T9](#t9--an-engineer-is-underperforming-what-do-you-do) · [T10](#t10--how-do-you-lead-a-distributed-team-across-time-zones)

---

## T1 · Tell me about a time you led a team through a major technical change.

**Situation.** At TCW I introduced AI-assisted development across the engineering team — GitHub Copilot adoption, with usage and review guidelines. On paper this is a tooling rollout. In reality it was a change to how people work, and those always split a team into three groups: the enthusiasts, the sceptics, and the quiet majority waiting to see which side wins.

**Task.** I owned the adoption. Not just the licences — the standards. Because the risk was obvious to me: if engineers used AI assistance to write code faster than they could review it, we would ship more code and understand less of it. In a regulated firm that is a real risk, not a theoretical one.

**Action.** Three things, in this order.

First, **I used it myself, on real work, before I asked anyone else to.** I used it on ETL scripting and test scaffolding — genuinely boring, genuinely repetitive work — and I showed the team the actual output, including where it was wrong. Leading a tooling change without using the tool is how you lose the sceptics on day one.

Second, **I wrote the guidelines before the enthusiasm outran the discipline.** The rules were simple and I kept them short enough to remember: use it freely for boilerplate, test scaffolding and ETL scripting; you own every line you commit, whoever typed it; code review standards do not change; and no proprietary data goes into a prompt.

Third, **I addressed the sceptics' real concern**, which was never "the tool is bad". It was "am I being replaced, and will my judgement stop mattering?" I answered that directly: the tool accelerates typing, not thinking. The work that makes an engineer valuable here — knowing why the reconciliation matters, knowing which query will scan a table — is not what it does.

**Result.** Adoption across the team, with boilerplate, test scaffolding and ETL scripting genuinely faster, and code-review standards held. No drop in review quality, which was the metric I actually watched.

**Lesson.** *"When you introduce a tool that makes people faster, the risk is never the tool. It is the discipline that used to be enforced by things being slow."*

**Follow-ups**

- *"How did you measure success?"* — Not by lines of code. By review throughput staying healthy and defect rates not moving the wrong way. If I measured "acceptance rate", I would be measuring the tool, not the outcome.
- *"What if someone refused to use it?"* — Fine, as long as their output and quality held. I mandated the standards, not the tool.
- *"Biggest surprise?"* — How useful it was for test scaffolding, which is exactly the work people skip when they are under pressure.

---

## T2 · How do you onboard a new engineer onto a complex platform?

**Situation.** The TCW reporting platform has an application tier, a Web API layer, a FastAPI ETL layer, three orchestration tools and two data stores. A new engineer can drown in that for a month. Onboarding badly costs more than the hiring did.

**Task.** Get someone from day one to a merged, meaningful pull request quickly, without them breaking anything and without them being scared to ask.

**Action.** I use the same structure every time.

**Day one is not code, it is the map.** I spend an hour walking the *data*, not the repository. Where does a number on a report actually come from? It comes from the source API, through the ETL, through validation, into the store, out through the Web API, onto the screen. Once someone can trace one number end to end, the repository structure stops being random and starts being obvious.

**Day two to five: a real, small ticket with a safety net.** Not a toy task — people can tell, and it signals you do not trust them. Something small and genuinely useful, paired with a buddy who is *not* me. The buddy is deliberate: a new person will ask a peer the "stupid" question they will not ask the architect.

**Week two: they own something.** A small but real piece with their name on it. Ownership creates engagement far faster than instruction does.

**Throughout: I write down the question, not just the answer.** Every time a new joiner asks something the documentation should have answered, that is a documentation bug. I fix the docs rather than answer the same question for the next person. Onboarding quality compounds — or rots — depending on whether you do this.

**Result.** New engineers reach a meaningful merged contribution in their first fortnight rather than their second month, and the onboarding notes improve with every joiner instead of going stale.

**Lesson.** *"Onboarding is a test of your documentation, not of the new person. If they struggle, look at your material first."*

**Follow-ups**

- *"What do you look for in the first month?"* — Do they ask good questions? Do they read the surrounding code before changing it? Those two predict more than raw speed.
- *"How do you onboard onto a domain like investment reporting?"* — Domain before tech. I explain what a position is, what an as-of date means, why reconciliation matters. An engineer who does not understand the domain writes technically correct, business-wrong code.
- *"Remote onboarding?"* — More structure, not less. Scheduled check-ins rather than assumed availability, and an explicit "ask me anything" slot, because remote joiners under-ask.

---

## T3 · How do you assess an engineer in an interview?

**Situation.** I have interviewed for my teams across several clients, and I have hired people who looked strong and did not work out. That taught me more than the successes.

**Task.** Find out how someone thinks, not what they have memorised.

**Action.** I run three parts.

**Part one — a real problem from our actual system, simplified.** For a data engineer: "This pipeline occasionally loads a portfolio twice. What questions do you ask?" I am not looking for the answer. I am watching whether they ask about idempotency, about keys, about retries — or whether they jump straight to writing code. Jumping to code is the single most common mistake.

**Part two — a deep dive into something on their CV.** I pick a project they claim and I go three levels down. "You said you improved performance — by how much, measured how, and what was the actual root cause?" Anyone who did the work can go three levels. Anyone who watched it happen cannot get past level one. This is the most reliable filter I have.

**Part three — a disagreement.** I state a technical opinion that is defensible but not obviously right, and I see what happens. Do they fold immediately? Do they argue without listening? Or do they ask what constraint led me there and then reason about it? I want the third. An engineer who folds when an architect pushes back will not tell me when I am wrong — and I need people who will.

I also ask one question I weight heavily: **"Tell me about something you built that you would build differently now."** Someone who cannot answer that has either not shipped enough, or has not reflected on what they shipped.

**Result.** I hire more slowly than the pressure would like, and I have far fewer regrets. The people who pass part two and part three are consistently the ones who work out.

**Lesson.** *"CV keywords tell you what someone was near. Three levels of depth tell you what they actually did."*

**Follow-ups**

- *"Do you use algorithm puzzles?"* — Rarely. They test a narrow skill that does not predict how someone designs an ingestion pipeline. I prefer a realistic problem.
- *"How do you assess a junior with no track record?"* — Trajectory and curiosity. What have they learned in the last six months, unprompted? For juniors I hire slope, not intercept.
- *"Have you got it wrong?"* — Yes. I hired for strong technical depth and ignored a clear signal that the person did not listen in the interview. It played out exactly the same way on the team. I now treat that signal as disqualifying, not as a minor concern.

---

## T4 · Two senior engineers disagree strongly on an architecture decision. What do you do?

**Situation.** This happens on every project. A recent version: one engineer wanted a fully event-driven flow between services; the other wanted straightforward synchronous REST calls. Both were experienced. Both had good arguments. And the debate was consuming the team's attention while the decision stayed open.

**Task.** Get a good decision made and keep both engineers engaged afterwards. That second half is the part people forget — winning the argument and losing the engineer is a bad outcome.

**Action.** Three steps.

**One — I separate the argument from the requirement.** I stopped the debate about *solutions* and asked about *constraints*. What actually has to be true? Does this flow need to survive the other service being down? Does the user need a synchronous answer? Ten minutes on constraints usually shrinks the disagreement, because much of it is two people optimising for different unstated requirements.

**Two — I make them argue the other side.** I asked each of them to state the strongest version of the other's position. This is the single most useful technique I know. It stops the debate being about who wins, and it exposes fast whether someone actually understands the alternative or is just defending a preference.

**Three — I decide, in writing, with the reasoning.** If constraints do not settle it — and sometimes they genuinely do not, because both options are viable — then it is my call as architect. I write a short decision record: what we chose, what we rejected, why, and what would make us revisit it. That last part matters enormously. "We chose synchronous REST; if cross-service coupling causes more than X incidents, we revisit" gives the engineer who lost a legitimate path rather than a grudge.

Here it landed on synchronous REST for the user-facing path — because the user needed an immediate answer — and events for the downstream fan-out, where nobody was waiting.

**Result.** Decision made in a day rather than drifting for two weeks. Both engineers stayed engaged, because both got part of their design and both saw their argument written down and taken seriously.

**Lesson.** *"Most architecture arguments are two people solving different problems. Get the constraints on the table and half the disagreement disappears. For the half that remains, decide, write it down, and say what would change your mind."*

**Follow-ups**

- *"What if you are the one who is wrong?"* — Then I change the decision and say so plainly. The fastest way to lose a senior team's respect is to defend a decision after the evidence has moved.
- *"What if one of them keeps re-litigating it?"* — I have a direct one-to-one. Disagree and commit. Re-opening a settled decision without new information is a team problem, and I address it as one.
- *"Do you always decide?"* — No. If the team is aligned and the decision is reversible, I let them run. I spend my authority on decisions that are expensive to undo.

---

## T5 · How do you mentor? Give me a specific example.

**Situation.** At TengizChevroil I mentored engineers on Azure, microservices and API design. Most had strong backgrounds in building single applications and had not designed for a distributed platform before.

**Task.** Move people from "I can build the feature you describe" to "I can decide how the feature should be built".

**Action.** My approach is simple: **I stop giving answers and start giving the question I would ask myself.**

A concrete example. An engineer came to me with a design for a new integration between two of the completion services, and asked me to approve it. Old me would have reviewed it and corrected it. Instead I asked three questions: "What happens if the other service is down when this fires?" "What happens if this message arrives twice?" "How would you know, in production, that this had stopped working?"

He had not considered any of the three. He went away and came back with a design using the outbox pattern, an idempotent consumer, and a specific alert. I did not teach him those patterns in that conversation. I taught him the three questions — and now he asks them himself before he comes to me.

I also do two other things deliberately. I **let people make reversible mistakes**. If a decision is cheap to undo, I let it play out even when I think it is not the best option, because a lesson someone learns from their own code is permanent, and one they learn from my correction lasts a week. I only intervene hard on decisions that are expensive to reverse.

And I **review in public and correct in private**. Design discussions where I ask hard questions are open, because everyone learns from them. Anything that could feel like a personal criticism is one-to-one.

**Result.** Engineers who started needing design approval ended up bringing me designs that already answered the failure-mode questions. Two of them became the people others went to first, which is the real measure — mentoring worked if you are no longer the bottleneck.

**Lesson.** *"Give someone an answer and you have solved one problem. Give them the question you would have asked and you have solved a category of problems."*

**Follow-ups**

- *"How do you mentor someone more senior than you in a specific area?"* — I do not pretend. I learn from them in their area and offer what I have in mine. Mentoring is not a hierarchy.
- *"How much time does this take?"* — Real time, and I protect it. The alternative is being the bottleneck for every design decision forever, which costs far more.
- *"How do you know it worked?"* — People stop asking me for permission and start asking me for a second opinion. That shift is the signal.

---

## T6 · Scope changed mid-sprint. How did you handle it?

**Situation.** On the completion platform, a genuine business change landed mid-sprint: a regulatory requirement meant the approval chain on a certificate needed an extra step. It was not a nice-to-have and it was not negotiable in principle. But the sprint was committed and the team was mid-flight.

**Task.** Absorb a real change without pretending capacity is infinite, and without the team learning that commitments do not mean anything.

**Action.** I refuse to do the thing that everyone does, which is quietly add it and hope. That is how you get a missed sprint, a demoralised team, and a stakeholder who learns that scope is free.

Instead I did three things.

**One — I sized it honestly and quickly.** Half a day of investigation, because a fast rough number beats a slow precise one when someone is waiting on a decision. It was meaningful work — the approval chain touched the audit history and the notification flow, not just a screen.

**Two — I presented it as a trade, not as a problem.** I went to the product owner with a specific choice: "This is roughly this size. We can take it into this sprint if these two items move out, or we can start it next sprint and it lands then. Which do you want?" That framing is the whole technique. It is not resistance and it is not a blank cheque. It puts the decision where it belongs — with the person who owns the priorities — and it makes the cost visible.

**Three — I protected the in-flight work.** Whatever we dropped, we dropped cleanly rather than leaving three things half-done. Half-finished work is the most expensive thing in a sprint, because it carries all the cost and delivers none of the value.

**Result.** The regulatory change went in, in the following sprint with a small piece of groundwork pulled forward, and the sprint that was in flight still delivered. The product owner made an informed choice rather than discovering the cost afterwards.

**Lesson.** *"Never say no to scope, and never say yes for free. Say 'yes, and here is what it costs' — then let the person who owns priorities decide."*

**Follow-ups**

- *"What if the answer is 'we need both'?"* — Then I present what "both" actually costs: a later date, more people (with a ramp-up cost that is not linear), or reduced quality — and I name quality explicitly, because it is the one that gets silently chosen otherwise.
- *"What if the change comes from a senior stakeholder directly to a developer?"* — I redirect it through the product owner, politely but every time. Not to be bureaucratic — because otherwise the team has several backlogs and nobody knows the real priority.
- *"How do you stop this happening every sprint?"* — If scope changes every sprint, the problem is upstream. I raise it as a pattern with evidence: "this is the fourth sprint with a mid-flight change; here is what it has cost us."

---

## T7 · You have to tell a stakeholder the date is slipping. Walk me through it.

**Situation.** This is one of the most important skills an architect has, and the one most people handle badly. The bad version is: say nothing, hope, then deliver the bad news when it is too late for anyone to act.

**Task.** Deliver bad news in a way that preserves trust and gives the stakeholder options.

**Action.** I have a rule: **bad news travels fast, good news can wait.** The moment I am confident a date is at risk — not certain, confident — I say so. Early bad news is a problem you can manage together. Late bad news is a betrayal, and that is how a stakeholder describes it afterwards.

The structure I use is always the same, in this order:

1. **The headline first, in one sentence.** "The reporting release will not make the 15th; I expect the 29th." No preamble. Burying it under context reads as evasion.
2. **The cause, briefly and without blame.** One or two sentences. Not a story, not a defence.
3. **What I have already done about it.** This is what separates a professional from a messenger. I never bring a problem without showing the mitigation I have already attempted.
4. **The options, with real trade-offs.** Usually three: ship the full scope later; ship a reduced scope on the original date and name exactly what is missing; or add capacity, with the honest caveat that people added late rarely make a project faster in the short term.
5. **My recommendation, and why.** Stakeholders want a view, not a menu. Naming my recommendation is what makes me an architect rather than a status reporter.
6. **What I will do to stop it recurring.**

The tone matters as much as the structure. Calm, specific, no defensiveness, no over-apologising. Over-apologising makes it about my feelings when the stakeholder is trying to make a business decision.

**Result.** In my experience, a slip communicated three weeks early with options is a working session. The same slip communicated three days early is an escalation. Same facts, completely different outcome.

**Lesson.** *"Stakeholders can handle a bad date. What they cannot handle is finding out late that you knew."*

**Follow-ups**

- *"What if they push back and demand the original date?"* — I do not argue, and I do not cave. I restate what the original date now costs — specifically which scope goes, or which quality gate we skip — and I make them the decision-maker. If they choose to cut testing, that is their call, and I record it.
- *"How do you know early enough?"* — Progress measured in working software, not in percentage complete. "Ninety percent done" is the most dangerous sentence in delivery.
- *"Have you had to do this badly?"* — Early in my career I waited too long, hoping to recover. We did not recover, and the late notice did more damage than the delay. That is where the rule comes from.

---

## T8 · How do you keep a team motivated on a long, unglamorous project?

**Situation.** Four years on the completion platform at Tengiz. Construction workflow automation is not glamorous work. It is approval chains, certificate states and data validation, in a remote location, for years.

**Task.** Keep good engineers engaged over a long horizon with no shiny technology to hide behind.

**Action.** Four things that actually worked, as opposed to the things that sound good.

**One — connect the work to the visible outcome.** The single most effective thing I did was show the team what their code did in the real world. Not a burndown chart — the actual construction progress. When a commissioning engineer stopped carrying paper because of a screen we built, I made sure the team heard about it. Meaning beats perks, reliably.

**Two — the Power BI dashboards were a motivation tool as much as a leadership tool.** Leadership could see completion status in real time, and the team could see leadership using their system. Being visible to the sponsor changes how people feel about their work.

**Three — I spread the interesting work rather than hoarding it.** There is always some genuinely interesting work — the ETL orchestration, the API design, the performance tuning. The easy path is to give it to whoever will do it fastest. I deliberately rotated it, so nobody spent four years only building forms.

**Four — I protected people from pointless work.** Nothing burns out a team faster than effort that goes nowhere. Reports nobody reads, processes with no purpose. Removing those is a motivation intervention, and it is one that costs nothing.

**Result.** A stable team over a multi-year programme, delivering four applications, with engineers who grew into Azure and microservices skills they did not have when they started.

**Lesson.** *"People do not lose motivation because the work is boring. They lose it when they cannot see that it matters, or when their effort is wasted."*

**Follow-ups**

- *"What about someone who is genuinely bored?"* — I have the direct conversation and try to move them to a different part of the platform. If there is nothing that fits, I say so honestly and help them find their next thing. Keeping a disengaged person in place helps nobody.
- *"How do you handle a death march?"* — I push back on the cause. Sustained overtime is a planning failure, and treating it as a motivation problem is dishonest.
- *"Team-building activities?"* — Less than people think. Fair workload, visible impact and a manager who says the difficult thing out loud beat any social event.

---

## T9 · An engineer is underperforming. What do you do?

**Situation.** I have had this on more than one team. The specific case I use: a capable engineer whose delivery had clearly slowed, with more defects than usual and pull requests sitting unfinished.

**Task.** Find out what is actually happening, and either fix it or be honest about it. Both outcomes are acceptable; drifting is not.

**Action.** The first thing I do is **assume it is a system problem until proven otherwise**, because it usually is. In my experience underperformance is far more often caused by unclear requirements, a blocking dependency, a domain the person never got taught, or something happening outside work — than by someone deciding to try less.

So the first conversation is not a performance conversation. It is one question, asked without an agenda: "How is it going — where are you getting stuck?" Then I stay quiet long enough for a real answer.

In that specific case the cause was domain knowledge. He had been handed work in the completion domain without ever being taught what the workflow actually meant, so he was implementing tickets literally without understanding intent — which produces exactly that pattern of slow delivery and subtle defects. That was an onboarding failure of mine, not a performance failure of his.

The fix was pairing him with someone strong in the domain for two weeks, and having him walk the business process with an actual commissioning engineer. Performance recovered.

**When it is genuinely a performance issue**, I am equally direct, just in a different direction. Specific examples not vague impressions, a clear statement of what "good" looks like, a defined timeframe, and support. And I involve the line manager, because it is their formal process. What I do not do is soften it into ambiguity — that is the unkindest option, because the person keeps failing without knowing they need to change.

**Result.** In this case a recovered engineer and a fixed gap in my onboarding. I made domain walkthroughs a standard part of joining after that.

**Lesson.** *"Before you conclude someone is underperforming, check whether you set them up to fail. Most of the time, part of the answer is yes."*

**Follow-ups**

- *"What if it does not improve?"* — Then it becomes a formal conversation with the line manager, and eventually a role change or an exit. Slow is fine; unclear is not.
- *"How do you protect the rest of the team?"* — Rebalance work quietly, without making the person a topic of team discussion. Nothing damages trust faster than a lead discussing one engineer with another.
- *"What if it is a personal issue outside work?"* — Then it is a human conversation and a manager/HR conversation, not an engineering one. Flexibility now buys years of loyalty later.

---

## T10 · How do you lead a distributed team across time zones?

**Situation.** Most of my career has involved this. Currently I work with a US client from India — that is a large time difference. Earlier I led offshore teams from client sites in London and Kazakhstan.

**Task.** Deliver at the same quality as a co-located team, with only a small overlap window each day.

**Action.** The core insight I work from: **treat the overlap as the scarcest resource on the project, and spend it only on things that genuinely need both sides live.**

That means I am ruthless about what goes into the overlap. Decisions, disagreements, design discussions and anything with emotional content. Status, updates and anything one-directional goes in writing. A status meeting that consumes the only shared hour of the day is a waste of the most expensive resource I have.

**Write things down, properly.** With low overlap, written clarity is not documentation overhead — it is the primary communication channel. Design decisions in a short record with the reasoning. Requirements written so they can be read at 3 a.m. in another country without a follow-up question. Ambiguity that costs ten minutes when someone is at the next desk costs a full day across time zones.

**Design the work to be handover-friendly.** I try to split work so that people are not blocked waiting for an answer overnight. If a task needs three clarifications, that is three days lost. So I front-load the clarification into the overlap window and let the independent work happen offline.

**Deliberately build the relationship.** This is the part that gets skipped. Remote teams default to transactional. I use some overlap time on non-work conversation, and where budget allows I push hard for people to meet in person once — it changes every interaction afterwards. I have been the on-site person and the remote person, and I know the difference in how information reaches you.

**And I watch for the second-class dynamic.** In distributed teams, the group nearest the client hears things first and decides things informally. That is corrosive. So decisions get written down where everyone can see them, and I make sure the remote side is asked directly for input rather than left to volunteer it.

**Result.** Delivery across large time differences with an engaged remote team — including the current TCW engagement, where the platform work spans continents and still lands inside a daily deadline.

**Lesson.** *"Time-zone distance is not the problem. Undocumented decisions are. If a decision only exists in a conversation, half your team does not have it."*

**Follow-ups**

- *"How do you run stand-ups?"* — Written and asynchronous, with the live time reserved for blockers and decisions.
- *"What about incidents outside the overlap?"* — A clear on-call ownership, runbooks written well enough to act on alone, and an explicit escalation path. See [Support & Post-Delivery](07-support-post-delivery.md).
- *"Hardest part?"* — Trust, early on. It builds slowly over a video call and quickly over a delivered commitment. So I make small promises and keep them visibly.

---

## Who decides what — the RACI I use

I bring this to every engagement in the first fortnight, because most delivery friction is not disagreement about the answer; it is disagreement about **who gets to decide**.

![RACI chart mapping decisions such as architecture, non-functional requirements, technology selection, sprint scope, release approval, incident command and cost ownership across the Solution Architect, Product Owner, Engineering Lead, Client Sponsor and Support Lead](assets/raci-chart.svg)

*Figure 4.1 — The decision map I agree up front. Ambiguity here causes more delay than any technical problem.*

**How I use it in an interview:** if asked "how do you work with a product owner", I describe this split — I own the *how* and the non-functional promises, they own the *what* and the priority order, and we jointly own the trade-off conversation. Saying it that crisply signals experience.

---

## Section index

| # | Question | Core message |
|---|---|---|
| T1 | Leading a major technical change | Use the tool yourself first; guard the discipline that speed removes |
| T2 | Onboarding onto a complex platform | Walk the data, not the repo; a new joiner's question is a docs bug |
| T3 | Assessing an engineer | Go three levels deep on one CV claim |
| T4 | Two seniors disagree | Argue constraints, not solutions; decide in writing with a revisit trigger |
| T5 | Mentoring | Give the question, not the answer; allow reversible mistakes |
| T6 | Mid-sprint scope change | "Yes, and here is what it costs" |
| T7 | Telling a stakeholder the date slipped | Bad news fast, with options and a recommendation |
| T8 | Motivation on a long project | Show people the real-world effect of their work |
| T9 | Underperformance | Assume a system problem until proven otherwise |
| T10 | Distributed teams | Spend the overlap only on what needs it live; write everything else down |

---

[← System Design](03-system-design.md) · [Home](README.md) · [Next → Client Engagement](05-client-engagement.md)
