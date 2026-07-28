--- filename: roles-and-jobs.md ---

# Roles and Jobs in Prompt Engineering

← [Chapter 8 — Case Study: Dating](./chapter-08-case-study-dating.md) · [Learning path](./learning-path.md) · Next: [Image Prompts](./assets/image-prompts.md)

By the end of the case studies, Asha realizes this isn't just a skill she's picked up — it's become enough of a discipline that her company is starting to hire specifically for it. This chapter maps the roles that have emerged, what each actually does day to day, and what to expect in an interview for two of the most common ones.

---

## 1. Prompt Engineer

**Summary:** The generalist practitioner. Designs, tests, and maintains prompts for a specific product or team, embedded alongside regular engineers rather than in a separate function.

**Responsibilities:**
- Design prompts following the anatomy and pattern discipline from Chapter 3.
- Own a slice of the team's prompt catalog (Chapter 4) — naming, versioning, test cases.
- Debug prompt failures the way you'd debug code: reproduce, isolate, fix, add a regression test.
- Partner with product/design on where prompts fit into user-facing flows.

**Required skills:**
- Strong software engineering fundamentals (this is not an entry-level "just chat with the AI" role).
- Comfort with ambiguity — prompt behavior isn't as deterministic as code, and the role requires reasoning about probabilistic output.
- Testing discipline — writing shape-based test cases, not just eyeballing output.
- Domain literacy in whatever the product actually does (you can't write a good compliance-checking prompt without understanding the compliance requirement).

**Sample interview questions:**
1. Walk me through how you'd debug a prompt that used to work well and started producing worse output after a model update, with no code changes.
2. Design a prompt to extract structured data from unstructured customer support tickets. What's your output schema, and how do you handle a ticket that doesn't match any expected category?
3. What's the difference between a prompting failure and a model capability limit, and how do you tell them apart in practice?

**Career progression:** Software Engineer → Prompt Engineer → Senior Prompt Engineer → Prompt Architect or Engineering Lead (branches based on whether you prefer deep technical design or team/system-level ownership).

---

## 2. Prompt Architect

**Summary:** Senior/staff-level role designing prompt *systems* — orchestration, catalog structure, and standards — across multiple teams, rather than owning one team's prompts directly.

**Responsibilities:**
- Define the prompt anatomy, naming conventions, and versioning standards an organization uses (the Chapter 3/4 material, at org scale).
- Design multi-prompt orchestration patterns (like the wave-based plans in Chapters 6-8) for complex, multi-step AI-assisted workflows.
- Set technical standards for guardrails, review gates, and blast-radius classification (Chapter 5's framework, formalized).
- Mentor Prompt Engineers across teams; run internal reviews of high-risk prompt designs.

**Required skills:**
- Systems design experience — this role is closer to a staff engineer than an individual contributor writing prompts day to day.
- Cross-team influence without direct authority.
- Deep familiarity with failure modes across many domains (the trading and dating case studies' guardrail patterns are the kind of thing a Prompt Architect should have internalized broadly).

**Sample interview questions:**
1. How would you design a prompt catalog and versioning scheme for an organization with 40 engineers and no existing standard? What do you standardize vs. leave flexible per team?
2. Describe a multi-step prompt orchestration you'd design for a workflow with a hard compliance gate partway through. Where do you put the gate and why?
3. A team wants to run an AI-generated summary unattended in a customer-facing email. Walk me through your review process before approving that.

**Career progression:** Senior Prompt Engineer → Prompt Architect → Principal Engineer (AI Systems) or Head of AI Platform.

---

## 3. LLM QA Engineer

**Summary:** Owns testing and evaluation of prompt-driven systems — the Chapter 4/5 testing discipline as a dedicated specialty rather than something every engineer does a little of.

**Responsibilities:**
- Build and maintain automated prompt regression test suites (shape-based validation, banned-phrase checks, schema validation).
- Design evaluation rubrics (precision, recall, safety, latency — see [`appendix-best-practices.md`](./appendix-best-practices.md)) for new prompts before launch.
- Run adversarial/red-team testing (the pattern from the dating case study's Prompt #10) across the org's prompt catalog.
- Track drift over time and flag prompts whose real-world quality is degrading.

**Required skills:**
- Traditional QA/test engineering background, adapted to probabilistic systems.
- Statistical literacy — understanding sample sizes, significance, and what "the model got it right 95% of the time" actually means for a given risk tolerance.
- Adversarial thinking — actively trying to break a system, not just confirming it works on happy-path inputs.

**Sample interview questions:**
1. How do you write a test for a prompt whose output isn't deterministic? Walk through a concrete example.
2. Design an adversarial test suite for a content moderation prompt. What categories of evasion would you specifically target?
3. How would you detect that a previously-reliable prompt has started drifting in quality after a model provider's update, without a human manually reviewing every output?

**Career progression:** QA Engineer → LLM QA Engineer → Senior LLM QA Engineer → QA Lead (AI Systems) or PromptOps Engineer.

---

## 4. Prompt Product Manager

**Summary:** Product management specialized in AI-assisted features — defines what prompt-driven capabilities should exist, for whom, and how success is measured.

**Responsibilities:**
- Translate user needs into prompt-system requirements (the "user stories → prompt inventory" step in the case studies).
- Define success metrics for AI features (the metrics tables in Chapter 6-8) and own the tradeoff decisions between capability and risk.
- Own the go/no-go decision for launching new AI-assisted user-facing features, in partnership with the review gates from Chapter 5.
- Communicate AI feature capabilities and limitations honestly to stakeholders and users (no overpromising what a prompt can reliably do).

**Required skills:**
- Standard PM skills (prioritization, stakeholder management, metrics definition) plus enough technical literacy to have an informed opinion on prompt reliability tradeoffs.
- Comfort saying no to a feature that sounds good but can't be made reliable or safe enough — this is a recurring, real tension in the role.

**Sample interview questions:**
1. A stakeholder wants a feature where the AI auto-generates final customer-facing legal disclaimers with no human review. How do you handle that conversation?
2. How would you define success metrics for an AI-assisted search feature? What would make you kill the feature even if usage numbers look good?
3. Walk me through how you'd prioritize between improving an existing prompt's accuracy vs. shipping a new AI-assisted capability.

**Career progression:** PM → Prompt Product Manager → Senior PM (AI Products) → Director of AI Product.

---

## 5. Prompt Researcher

**Summary:** Investigates prompting techniques, model behavior, and evaluation methodology — closer to applied research than product delivery.

**Responsibilities:**
- Evaluate new prompting techniques (few-shot variants, reasoning patterns, retrieval-augmented approaches) against the org's actual use cases.
- Investigate root causes of systematic failure patterns (e.g., "why does our matching-explanation prompt leak protected attributes 3% of the time?") at a deeper level than day-to-day debugging affords.
- Publish internal findings/playbooks that Prompt Engineers and Architects then operationalize.

**Required skills:**
- Strong experimental methodology — designing a fair comparison between two prompting approaches is genuinely hard to do without bias.
- Comfort with ambiguous, open-ended investigation rather than well-scoped delivery work.
- Ability to translate research findings into practical, adoptable recommendations (a great finding nobody can act on has limited value).

**Sample interview questions:**
1. Design an experiment to determine whether chain-of-thought prompting actually improves accuracy for our specific bug-diagnosis use case, or just makes output longer without being more correct.
2. How would you investigate a systematic bias in an AI system's output that only shows up in aggregate, not in any individual example you've reviewed?
3. What's a prompting technique you've seen recommended that you'd want to rigorously test before trusting, and why?

**Career progression:** Research Engineer → Prompt Researcher → Senior Prompt Researcher → Applied Research Lead.

---

## 6. PromptOps Engineer

**Summary:** The operational counterpart to a Prompt Engineer — owns the infrastructure that runs prompts reliably at scale: CI integration, monitoring, cost/latency management, and incident response for AI-system failures.

**Responsibilities:**
- Build and maintain the CI pipeline that runs prompt regression tests (the Chapter 4 CI pattern, in production).
- Monitor prompt latency, cost, and failure rates in production; own alerting and dashboards.
- Handle incident response when a prompt-driven system fails or degrades (analogous to Chapter 7's on-call/escalation prompts, but as the actual job).
- Manage rollout/rollback of prompt changes, including canary testing new prompt versions against a subset of traffic.

**Required skills:**
- Strong DevOps/SRE background, adapted to a new class of system (prompt-driven, not just service-driven).
- CI/CD pipeline design and observability tooling experience.
- Calm, structured incident response under pressure.

**Sample interview questions:**
1. Design a canary rollout strategy for a new version of a customer-facing prompt. What metrics would make you roll back automatically vs. require a human decision?
2. A prompt-driven feature's latency p99 has tripled overnight with no code changes. Walk me through your investigation.
3. How would you set up alerting for "hallucination rate" in production, given that you can't perfectly automate detecting every hallucination?

**Career progression:** SRE/DevOps Engineer → PromptOps Engineer → Senior PromptOps Engineer → Head of AI Infrastructure/Platform.

---

## 7. Prompt Designer

**Summary:** Focuses specifically on the user-facing language and tone of AI-generated content — closer to a UX writer/content designer with prompt-engineering skill than a backend-focused engineer.

**Responsibilities:**
- Own tone, voice, and inclusivity of user-facing AI-generated copy (the onboarding/explanation prompts from the case studies).
- Partner with legal/compliance/trust & safety on language that carries real risk (financial disclaimers, moderation messaging).
- Run and interpret A/B tests on AI-generated copy variants.
- Maintain a style guide that prompts are checked against (feeding directly into prompts like the "style-guide diff reviewer" pattern).

**Required skills:**
- UX writing / content design background.
- Enough prompt-engineering technical skill to actually write and iterate on the prompts themselves, not just specify requirements for someone else to implement.
- Sensitivity to fairness, inclusivity, and tone — this role owns exactly the kind of review done in the dating case study's inclusive-language and leakage checks.

**Sample interview questions:**
1. Review this onboarding prompt copy for exclusionary assumptions: [sample copy]. What would you change?
2. How do you balance a brand's desired "friendly, enthusiastic" tone against a domain (e.g., financial risk alerts) that requires careful, non-alarmist, non-promissory language?
3. Design an A/B test to compare two tones for a moderation-action notification. What's your primary metric, and what's a guardrail metric you'd also track?

**Career progression:** UX Writer/Content Designer → Prompt Designer → Senior Prompt Designer → Content/AI Design Lead.

---

## 8. Prompt Trainer

**Summary:** Builds internal training programs and enablement material — teaches other engineers, PMs, and support staff the discipline this whole repo covers, at organizational scale.

**Responsibilities:**
- Design and run internal training (workshops, learning paths like this one, office hours) on prompt engineering fundamentals.
- Build and maintain internal documentation, templates, and onboarding material.
- Identify skill gaps across teams and design targeted enablement (e.g., "the support team needs research-prompt skills, the backend team needs bug-fix-prompt skills").
- Measure training effectiveness — not just "did people attend," but "did prompt quality/catalog adoption actually improve."

**Required skills:**
- Instructional design experience.
- Deep, practical prompt-engineering skill (you can't teach a discipline you don't practice).
- Ability to translate technical material for a genuinely broad, mixed-skill audience.

**Sample interview questions:**
1. How would you design a training program to move a team of 15 experienced engineers from "search-first" habits to "prompt-first" habits in one quarter?
2. What would you measure to know if your prompt-engineering training actually worked, beyond attendance and satisfaction surveys?
3. Walk me through how you'd explain grounding and hallucination to a non-technical support team member who needs to use AI-assisted ticket triage.

**Career progression:** Technical Trainer/Instructional Designer → Prompt Trainer → Senior Prompt Trainer → Head of AI Enablement.

---

# Hiring

## Hiring checklist (any prompt-engineering-adjacent role)

- [ ] Does the candidate distinguish between a prompting failure and a model capability limit, or do they treat every bad output the same way?
- [ ] Do they test with shape-based assertions, or do they describe testing in terms of exact-text matching (a red flag for anyone who'll own production prompt quality)?
- [ ] Can they name at least one concrete guardrail pattern (grounding, output schema, banned-phrase check, human review gate) and when they'd use it?
- [ ] Do they ask clarifying questions about blast radius / risk before designing a solution, or do they jump straight to a prompt?
- [ ] For senior/architect-level roles: can they reason about tradeoffs across multiple domains (e.g., explain why the trading case study's guardrails are stricter than the e-commerce case study's)?
- [ ] Do they show awareness of fairness/bias risk as a first-class concern, not an afterthought, when the role touches user-facing or decision-making systems?
- [ ] Reference check specifically for: did their prompts/systems degrade gracefully when they failed, or fail silently and surprise the team later?

## 10 interview questions — Prompt Engineer

1. Walk me through your process for turning a vague feature request into a working prompt. What do you do first?
2. Here's a prompt that's producing inconsistent output shape across runs: [sample]. What's your diagnosis and fix?
3. What's the difference between few-shot prompting and chain-of-thought prompting, and when would you choose one over the other?
4. How do you decide when a prompt needs a human review gate vs. can run unattended?
5. Describe a time (real or hypothetical) when a prompt you wrote produced a confidently wrong answer. How did you catch it, and what did you change?
6. How would you version a prompt change that adds a new optional output field, without breaking existing consumers of the old format?
7. What does "grounding" mean, and give a concrete example of a prompt you'd rewrite to add it.
8. How do you test a prompt whose output legitimately varies between runs (e.g., a creative-writing task) versus one that should be highly consistent (e.g., a data-extraction task)?
9. A teammate says "the AI got it wrong" about a prompt's output. What questions do you ask before agreeing or disagreeing with that framing?
10. Design a prompt to generate a commit message from a diff. Walk through your first draft, then critique it yourself and improve it.

## 10 interview questions — PromptOps Engineer

1. Design a CI pipeline step that runs prompt regression tests on every PR touching a prompt template. What does it check, and what makes it fail the build?
2. How would you monitor for "silent drift" — a prompt's output quality degrading due to a model update, with no code change on your side?
3. Walk me through a canary rollout strategy for a new prompt version. What traffic percentage do you start with, and what automatically triggers a rollback?
4. A production prompt-driven feature's cost has tripled this month with no traffic increase. How do you investigate?
5. What metrics would you put on a dashboard for a team running 20 different prompts in production? Name the top 5.
6. How do you handle a prompt that occasionally times out or returns malformed output in a pipeline — what's your fallback behavior, and how do you decide what "occasionally" is acceptable?
7. Describe how you'd set up alerting thresholds for hallucination rate, given that you likely can't perfectly automate detecting every hallucination.
8. How is on-call/incident response for a prompt-driven system failure different from a traditional service outage, if at all?
9. Walk me through how you'd structure a prompt catalog's storage and access so both humans (browsing) and CI (automated testing) can use it effectively.
10. A prompt template needs to be deprecated because a newer version has a breaking output-format change. Walk me through how you'd manage that transition across multiple downstream consumers without breaking them.

---

← [Chapter 8 — Case Study: Dating](./chapter-08-case-study-dating.md) · [Learning path](./learning-path.md) · Next: [Image Prompts](./assets/image-prompts.md)
