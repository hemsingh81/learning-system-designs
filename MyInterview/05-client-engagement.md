# 05 · Client Engagement (8 questions)

[← Team Management](04-team-management.md) · [Home](README.md) · [Next → RFP & Pre-Sales](06-rfp-presales.md)

Most of my career has been consulting into client organisations — Sapient into asset managers and UK enterprises, Novus Bolashak into TengizChevroil, now Publicis Sapient into TCW. So I am rarely the client's employee. I am the person in the room who has to be trusted enough to be believed, without any authority at all.

That shapes everything below.

**Jump to:** [C1](#c1--tell-me-about-a-time-you-proposed-something-the-client-had-not-asked-for) · [C2](#c2--the-client-asks-for-something-that-is-out-of-scope-what-do-you-do) · [C3](#c3--a-client-is-unhappy-with-delivery-how-do-you-recover-it) · [C4](#c4--how-do-you-present-a-proof-of-concept-to-client-stakeholders) · [C5](#c5--how-do-you-say-no-to-a-client) · [C6](#c6--how-do-you-turn-business-requirements-into-a-technical-design) · [C7](#c7--how-do-you-follow-up-after-a-demo-and-keep-momentum) · [C8](#c8--how-do-you-turn-a-conversation-into-funded-delivery-work)

---

## C1 · Tell me about a time you proposed something the client had not asked for.

**Situation.** At TCW, nobody asked me to write an AI/LLM integration framework. The engagement was investment reporting and Aladdin data integration. But I could see what was coming: teams across the firm wanted to use LLMs, and there was no agreed way to do it. Left alone, we would have ended up with several different approaches, different data-handling decisions, and no way to tell whether any of them were accurate. In a regulated asset manager, that is a compliance exposure, not just untidiness.

**Task.** Propose something outside my remit, to a client who had not asked for it, without looking like a consultant selling work.

**Action.** The mistake here would have been to arrive with a slide deck about AI strategy. Nobody buys that from the reporting architect.

Instead I did three things.

**One — I attached it to a problem they already felt.** Not "we should have an AI strategy". Instead: support engineers were spending real time digging through old email threads and Confluence runbooks to answer questions that had already been answered before. That is a pain the business recognised without me explaining it.

**Two — I proposed the framework and the proof together.** I did not ask for approval of an abstract reference architecture. I said: here is a reusable pattern for retrieval, grounding, orchestration and evaluation, and here is the first thing I will build on it to prove it works — a support assistant over our own support history and runbooks. A framework with no implementation is a document; a framework with a working implementation is an asset.

**Three — I led with the controls, not the capability.** With a regulated client, the first question is never "how clever is it?" It is "how do we stop it saying something wrong, and how do we stop it showing someone a document they are not allowed to see?" So my proposal opened with grounding, citations, permission filtering at retrieval, and the evaluation loop. Answering the compliance question before it is asked is what gets an AI proposal approved.

**Result.** Delivered as TCW's first production RAG application, and the framework became the firm's reference pattern for AI/LLM integration. Support engineers now get grounded, cited answers to recurring issues instead of searching mail archives.

**Lesson.** *"An unsolicited proposal works when it is anchored to a pain the client already feels, comes with proof rather than a promise, and answers the risk question before the client has to ask it."*

**Follow-ups**

- *"How did you get the time to build it?"* — I scoped the first version deliberately small, so it fitted alongside the committed work rather than competing with it. A big ask needs a business case; a small proof needs permission.
- *"What if they had said no?"* — Then no. I would have asked what would need to be true for it to be a yes, and revisited when that changed. Pushing a rejected idea is how architects lose credibility.
- *"How do you avoid looking like you are selling?"* — I lead with their outcome and I am honest about the limits. In this case I named clearly what the assistant would *not* do — it answers support and process questions, not investment questions. Naming the boundary builds more trust than claiming range.

---

## C2 · The client asks for something that is out of scope. What do you do?

**Situation.** This happens constantly, and how you handle it is the difference between a healthy account and a resentful one. On the completion platform, mid-delivery, the client asked for an additional integration with a system that was not in the agreed scope. It was a reasonable ask — it would genuinely have made the platform better.

**Task.** Do not say no. Do not say yes for free. And do not let it become an argument about the contract, which is how relationships get damaged.

**Action.** My sequence is always the same.

**First, I understand the need, not the request.** I ask what problem this solves before I discuss whether we can do it. Sometimes the underlying need can be met a much cheaper way than the specific thing they asked for. I would say this is true about a third of the time, and finding it makes you look like a partner rather than a supplier.

**Second, I say yes in principle, immediately.** "Yes, that is worth doing." That sentence costs nothing and it changes the whole conversation. The disagreement is never about whether it is valuable; it is about sequence and cost.

**Third, I make the cost visible and specific.** Not "that's a change request" — that phrasing sounds like a barrier and makes people feel handled. Instead: "That is roughly this much effort. Taking it now means either the date moves by about this much, or these two items move out. Which would you prefer?"

**Fourth, I write it down the same day.** A short note confirming what was asked, what it costs, the options and the decision. Not to build a paper trail against them — to stop a friendly verbal conversation becoming a genuine misunderstanding in six weeks. Both sides benefit from that note.

**Fifth, and this is the part people miss — I record the ones we defer.** Deferred asks are the best-qualified pipeline anyone has. They are needs the client has already told me they have. When the current phase lands, that list is what the next conversation is built from. See [RFP & Pre-Sales](06-rfp-presales.md).

**Result.** On that platform the integration went into a later phase with proper funding, and the in-flight delivery stayed on its date. The client got the thing they wanted, and got it done properly rather than squeezed in.

**Lesson.** *"'No' damages a relationship. 'Yes, and here is what it costs — you choose' protects it. The client is not trying to get free work; they usually just do not know what it costs."*

**Follow-ups**

- *"What if it is small — do you just do it?"* — Sometimes, deliberately, and I say so out loud: "This one is small, we will absorb it." Occasional generosity buys enormous goodwill. But it must be visible, not silent, or it just resets expectations downward.
- *"What if they insist it was always in scope?"* — I go back to the written requirement without arguing about memory. If it genuinely is ambiguous, I say so and we split the difference. Being fair when the wording favours me is worth more than winning that one.
- *"What if the sales team already promised it?"* — Then I honour it and fix the process internally, not in front of the client. Undermining your own account team in a client meeting is unforgivable.

---

## C3 · A client is unhappy with delivery. How do you recover it?

**Situation.** The version I use: a client stakeholder who had lost confidence — reports arriving late, a couple of data discrepancies, and a growing sense that nobody was in control. Individually the issues were small. Together they had become a trust problem, and a trust problem is much harder to fix than a technical one.

**Task.** Recover confidence. And confidence is recovered by predictability, not by heroics.

**Action.** Four steps.

**One — I go and listen, with no defence prepared.** I asked to hear the full list, and I did not explain or contextualise a single item while they were talking. That is very hard to do and it is essential. An unhappy client who feels heard becomes a partner; one who feels managed escalates.

**Two — I separate the symptoms from the cause.** The complaints were "reports were late" and "a number looked wrong". The actual cause was narrower: a fragile step in the chain and no visibility, so problems were discovered by the business rather than by us. That reframing matters — I could not fix "you are unhappy", but I could fix "you find out about problems before we do", which was the real grievance.

**Three — I fix the visibility first, before the engineering.** This is the counter-intuitive bit and it is what actually works. Before the deeper fixes landed, I put in place proactive communication: if something is late or a break is detected, they hear it from me with an assessment, not from a user. Almost immediately, the same underlying issues stopped generating the same anger — because the client was no longer being surprised. Then the engineering fixes followed: the deadline-aware alerting, the reconciliation checks, the structured logging with a shared run id.

**Four — I make the improvement measurable and visible.** A short weekly note with the actual numbers: what ran on time, what broke, what was fixed, what is still open. No spin. Including the bad weeks is what makes the good ones believable.

**Result.** The relationship recovered, and it recovered mostly in the weeks before the technical fixes were finished — because the client's actual complaint was about being surprised, not about the fault rate.

**Lesson.** *"Clients rarely lose trust because something broke. They lose it because they found out from someone else. Fix the surprise first; the engineering fix is necessary but slower."*

**Follow-ups**

- *"What if the complaint is unfair?"* — I still take it seriously, and I separate the feeling from the facts. Often the unfair complaint is a signal about something real that they have not articulated well. Arguing about fairness never once improved a relationship.
- *"What if it is your team's fault?"* — I say so plainly and early. Clients forgive mistakes that are owned. They do not forgive mistakes that are defended.
- *"When do you escalate internally?"* — As soon as I know I cannot fix it with what I have. Escalating late is the same failure as telling the client late.

---

## C4 · How do you present a proof of concept to client stakeholders?

**Situation.** I have been doing this since the Sapient years in London, presenting proofs of concept and technical designs to client stakeholders to shape solution direction before build. The RAG assistant at TCW was the most recent.

**Task.** Get a decision, not applause. A demo that impresses everyone and changes nothing is a failed demo.

**Action.** Five rules I follow every time.

**One — I decide the decision before I build the demo.** What am I asking them to approve at the end? Funding? A direction? A technology choice? If I cannot state it in one sentence, the PoC is not ready to show. Everything in the demo then serves that decision, and anything that does not is cut.

**Two — I show the risky part, not the pretty part.** The instinct is to demo the polished happy path. That is exactly wrong, because the audience's real question is "will this work in our environment?" So I demo the thing everyone doubts. With the RAG assistant, that meant showing what happens when it does not know: it says so, and points to the human escalation path. That single moment did more to build confidence than any correct answer, because it proved the thing they were actually worried about.

**Three — I use their data and their language.** A demo with sample data proves nothing to a stakeholder. A demo answering a real support question from their own runbooks is undeniable. And I use their vocabulary — their process names, their document names. The moment I use my own abstractions, they have to translate, and translation loses people.

**Four — I state the limits myself, before anyone finds them.** "Here is what this does not do yet. Here is what would be needed for production. Here is what I am uncertain about." Every experienced stakeholder is looking for the catch. Naming it yourself converts scepticism into trust — and if you do not, someone finds it in the meeting and you lose control of the room.

**Five — I finish with the decision and the next step, with a date.** Not "let us know what you think". That is how a good PoC dies quietly. Instead: "To take this to production we need these three things. If you agree, the next step is X by this date."

**Result.** PoCs that end in a decision. The AI framework proposal moved from demo to production delivery because the demo answered the risk question and closed with a concrete next step.

**Lesson.** *"Demo the doubt, not the polish. And never end a PoC without naming the decision you are asking for."*

**Follow-ups**

- *"What if the demo breaks live?"* — I stay calm and explain what happened; it is a PoC and everyone knows it. I keep a recorded backup of the core flow. What loses the room is panic, not a bug.
- *"How long should a PoC be?"* — Time-boxed and short — usually two to four weeks — with the success criteria agreed up front. An open-ended PoC becomes an unfunded product.
- *"How do you handle the stakeholder who wants it in production tomorrow?"* — I welcome the enthusiasm and immediately make the gap concrete: security review, evaluation set, monitoring, support model. I turn their urgency into sponsorship for those things rather than fighting it.

---

## C5 · How do you say no to a client?

**Situation.** The hardest version I have faced is a client asking for something technically unwise rather than merely out of scope — where saying yes would produce a system I would not want my name on. For example, being pushed toward a shortcut on data validation to hit a date.

**Task.** Protect the outcome without being the person who blocks things.

**Action.** I almost never say the word no. I say **"yes, and here is the consequence"**, then I make the client the decision-maker.

The distinction I hold onto: **I own the recommendation; the client owns the decision.** It is their system and their money. My job is to make sure the decision is informed, not to make it for them. Architects who treat every technical preference as a hill to die on stop getting invited to the early conversations, which is where they can actually help.

So in the validation example, I did not say "we cannot skip that". I said: "We can hit the date that way. Here is what it means — the errors this catches will reach reports instead, and someone will find them in front of a portfolio manager. Based on what we have seen, I would expect that to happen. My recommendation is to move the date by a fortnight or cut this other feature instead. Your call."

Three things make this work.

**I quantify the consequence** rather than describing it vaguely. "Risky" is dismissible. "The check that catches duplicated positions would not run" is not.

**I always bring an alternative.** Refusing without offering another path makes you an obstacle. Offering a route makes you a partner.

**I record the decision if they overrule me** — briefly, factually, no I-told-you-so tone. Then I commit fully to their choice. Sulking after being overruled is worse than never objecting, and clients remember it.

There is one category where I genuinely will not move: anything that puts data at risk or breaches a regulatory obligation. There I escalate rather than comply, and I say plainly that I cannot sign it off. That has happened rarely, and being known to have a line makes every other recommendation more credible.

**Result.** In that instance the client moved the date. Not because I refused, but because seeing the specific consequence changed their view of the trade.

**Lesson.** *"Do not say no. Show the price, give an alternative, and let them choose. Save your absolute refusals for things that are genuinely unsafe — and then be immovable."*

**Follow-ups**

- *"What if they overrule you and it goes wrong?"* — I help fix it without a single word about having warned them. The record exists if it is ever needed; I never wave it. That restraint is what gets me listened to next time.
- *"Have you ever refused outright?"* — Only on data protection and regulatory grounds. I escalate through my own management rather than quietly complying.
- *"How do you say no to a client's own architect?"* — Peer to peer, on constraints not opinions, and privately first. Never make a client's technical person look wrong in front of their sponsor.

---

## C6 · How do you turn business requirements into a technical design?

**Situation.** At TCW this is a core part of my role — translating business requirements into technical designs with the BAs and stakeholders for the Emerging Markets and Equity reporting platform.

**Task.** Get from what a business person says to a design that will actually hold, including the requirements they did not say out loud.

**Action.** Four steps.

**One — I ask what decision the output supports.** Not "what fields do you want on this report" but "what will you do differently based on what it tells you?" That question reframes everything. A request for a report is rarely a request for a report; it is a request to be able to make a judgement. Once I know the judgement, I often find the requested layout was not the best way to support it.

**Two — I extract the non-functional requirements, because nobody volunteers them.** Business stakeholders describe function. They almost never say "and it must be ready before the market opens" unless asked — they assume it, because to them it is obvious. So I ask directly: When do you need it? What happens if it is late? How wrong can it be before it is useless? How far back do you need to look? Who must not see it? Those five questions produce the requirements that actually drive the architecture.

**Three — I write it back in their language and get it confirmed.** Short, plain sentences, no technical vocabulary: "Every trading day before the market opens, you see positions as of the previous close for the portfolios you are entitled to. If the source data is late, you see the last good figures clearly marked as stale, and you get told." If they can read that and say "yes, that is it", the requirement is real. If I need diagrams to explain it, I have not understood it yet.

**Four — I show them the trade-off early, while it is still cheap.** "Fresher data means a later delivery time. Which matters more?" Business stakeholders are perfectly capable of making that call — they just are not usually given it in time to matter.

The specific habit that has saved me most often: **I ask about the exception, not the normal case.** "What happens on a public holiday?" "What if a portfolio is added mid-month?" "What if the source restates last week's figure?" The normal case is always described accurately. The exceptions are where the real complexity lives, and where a design fails six months later.

**Result.** Designs that survive contact with reality, because the awkward cases were on the table during design rather than discovered in UAT.

**Lesson.** *"Requirements gathering is not writing down what people say. It is asking about the cases they have not thought about, and getting the unstated non-functional promises on paper."*

**Follow-ups**

- *"What if stakeholders disagree with each other?"* — I surface it explicitly rather than averaging it into a compromise nobody wants. Two stakeholders wanting different things is a prioritisation decision, and it belongs to the sponsor.
- *"How do you handle 'just make it like the old system'?"* — I ask which parts of the old system they actually use. There is always a chunk nobody touches, and not rebuilding it is free value.
- *"How do you document it?"* — Plain-language acceptance criteria plus a short decision record for the architectural choices and why. Long specifications go unread; a page that says what and why gets used.

---

## C7 · How do you follow up after a demo and keep momentum?

**Situation.** The most common way good work dies is not rejection. It is silence after a positive meeting. Everyone leaves enthusiastic, nobody owns the next step, and three weeks later the energy is gone.

**Task.** Convert a good meeting into a scheduled next step, without chasing in a way that feels like pestering.

**Action.** Four habits.

**One — I never leave the meeting without a named next step, an owner and a date.** I say it out loud before people stand up: "So the next step is the security review, you are pulling that together, and we meet on the 14th." Getting agreement in the room is ten times easier than getting it by email afterwards.

**Two — I send the follow-up within 24 hours, and it is short.** Long recap emails do not get read. Mine is: what we agreed, what the decision was or what is still open, who does what by when, and one line of value. Under 200 words. There is a full template in [Email Templates](11-email-templates.md).

**Three — every follow-up carries something new.** This is the technique that separates useful follow-up from nagging. I never send "just checking in" — that puts the work on them and gives them nothing. Instead each contact brings a small piece of value: a refined estimate, a relevant example, an answer to something raised in the meeting, a risk I have thought more about. Then the follow-up is a reason to reply, not a request for one.

**Four — I read the silence honestly.** If someone goes quiet after being enthusiastic, something changed: budget, priority, or an internal objection I did not see. Rather than sending a fourth chase, I ask directly and make it easy to say no: "Has this slipped down the list? Genuinely fine if so — I would just rather know than keep chasing." That question gets an honest answer almost every time, and an honest no is worth far more than a polite maybe.

**Result.** Ideas that convert into scheduled work rather than fading. The AI framework moved from proposal to production because each contact after the demo carried something new, and because the next step always had a date on it.

**Lesson.** *"Momentum is not enthusiasm. It is a named owner and a date. Every follow-up should give something, not ask for something."*

**Follow-ups**

- *"How many times do you follow up?"* — Roughly three, each with new value, then a direct question about priority. After that I leave it and come back when circumstances change. Chasing past that damages the relationship.
- *"What if the sponsor is genuinely too busy?"* — I find the person who does have time and cares — often a lead or a manager who feels the pain daily — and let them build the internal case. Bottom-up frequently beats top-down.
- *"How do you keep momentum inside a long delivery?"* — Visible progress on a cadence. Short demos of working software beat any status report.

---

## C8 · How do you turn a conversation into funded delivery work?

**Situation.** The path from "interesting idea" to "funded project" is where most technical proposals die, and it is a large part of what a senior architect is actually paid for.

**Task.** Move something from a conversation to a budget line.

**Action.** I think about it as four gates, and I make sure each one is closed before moving on.

**Gate one — a named pain with a name attached.** Not "this would be better". A specific person who is losing something specific — time, accuracy, sleep. If I cannot name that person, there is no project, and I stop rather than build a proposal nobody sponsors.

**Gate two — proof, at the smallest scale that convinces.** Something working, over their data, showing the risky part. This is the PoC in [C4](#c4--how-do-you-present-a-proof-of-concept-to-client-stakeholders). The purpose is to remove the "will it work here?" doubt, and nothing else.

**Gate three — a credible number.** Effort, cost, and what it buys, with the assumptions written down. I would rather give a range with clear assumptions than a precise-looking single figure I cannot defend — because the first question is always "what is this based on?" and a defensible range survives that question while a false-precision number does not.

**Gate four — a sponsor with a budget, and their internal case.** The most important thing I have learned: **the sponsor has to sell this internally, and I am not in that room.** So my job is to give them the material to win that argument — the one-page summary, the number, the risk position — in a form they can forward without editing. A proposal that only works when I present it will not survive the meeting I am not invited to.

Then I keep it moving with the follow-up discipline in [C7](#c7--how-do-you-follow-up-after-a-demo-and-keep-momentum).

**Result.** The AI framework went through exactly these gates: a real support pain, a working proof on the firm's own content, an honest scope, and a sponsor who could carry it internally. It became production delivery.

**Lesson.** *"You do not win the funding conversation. Your sponsor wins it, in a room you are not in. Write the proposal so it works without you there."*

**Follow-ups**

- *"What if there is no budget this year?"* — Then I get it on the plan for next cycle and keep it warm with evidence. Budget timing is a calendar problem, not a rejection.
- *"How do you price it?"* — See [RFP & Pre-Sales](06-rfp-presales.md) — bottom-up from a work breakdown, cross-checked against a comparable delivery, with the assumptions listed as part of the number.
- *"How do you avoid over-promising to win it?"* — I stay on the account through delivery. That is the strongest discipline there is: whatever I promise in the proposal, I have to run in production.

---

## Section index

| # | Question | Core message |
|---|---|---|
| C1 | Proposing something unasked | Anchor to a felt pain; bring proof; answer the risk question first |
| C2 | Out-of-scope request | "Yes, and here is what it costs — you choose" |
| C3 | Unhappy client | Fix the surprise before the engineering |
| C4 | Presenting a PoC | Demo the doubt, not the polish; close on a decision |
| C5 | Saying no | Show the price, offer an alternative, let them decide |
| C6 | Requirements to design | Ask about exceptions and unstated non-functionals |
| C7 | Follow-up and momentum | Every contact carries new value; always a named date |
| C8 | Conversation to funded work | Write it so the sponsor can win the room you are not in |

---

[← Team Management](04-team-management.md) · [Home](README.md) · [Next → RFP & Pre-Sales](06-rfp-presales.md)
