--- filename: chapter-08-case-study-dating.md ---

# Chapter 8 — Case Study: Dating Site MVP, Start to End

← [Chapter 7 — Case Study: Trading](./chapter-07-case-study-trading.md) · [Learning path](./learning-path.md) · Next: [Roles and Jobs](./roles-and-jobs.md)

## Narrative

Asha's third project changes how she thinks about the whole discipline. It is a dating app MVP.

Compare the three projects by what a wrong prompt output actually costs:

| Project | A wrong output causes | Can you undo it? |
|---|---|---|
| E-commerce | A rewrite. Some wasted time | Yes, easily |
| Trading | Lost money, or a compliance problem | Yes, with effort |
| **Dating** | **Emotional harm to a real person. Exposure to harassment. Bias against a whole group** | **Often not** |

That last row is different in kind, not just in degree.

The bias case is the one that worries her most, because of how it fails. It is quiet. Nobody notices at the time. There is no error, no alert, no angry customer. You find out six months later when somebody finally runs the analysis — and by then it has been shaping who thousands of people met.

So she starts the same way as the other two projects — problem statement, requirements, prompt inventory — and then adds something she has not needed before: **fairness and privacy as a named phase with its own prompts.** Not a checkbox at the end of testing.

The ordering changes too:

- The matching algorithm gets a **fairness audit before** it gets a performance review.
- The moderation system gets tested against **adversarial inputs before** happy-path ones.

This case study is where *"does the output look right?"* stops being a sufficient question, and *"who could this harm, and how would we find out?"* becomes the one the prompts are built to answer.

---

## Privacy and ethics

Four principles. Each one exists because of a specific way this kind of product goes wrong.

**1. Data minimization — send only what the task needs.**

A moderation prompt does not need someone's education history. A match-explanation prompt does not need their exact address.

Why it matters: every extra field you pass into a prompt is a field that can leak into an output, appear in a log, or end up in a place nobody audited.

**2. No protected-class targeting.**

Matching logic and its explanations must never use race, religion, disability status, or similar protected attributes — as a matching factor, or as a reason shown to a user. Even when that data technically exists in the database.

**3. Consent-scoped generation.**

If a prompt writes something *as if from a user* — a suggested opening message, a bio — it must be clearly labelled as a suggestion they choose to send. Never sent automatically on their behalf.

Why: the other person is talking to someone they think is real. Auto-sending generated text quietly makes that untrue.

**4. Right to explanation, without exposing anyone else.**

A user can ask "why was I shown this person?" and deserves an honest answer.

The hard part is that an honest answer must not reveal the *other* user's private data. Both people have a right to privacy, and the explanation sits exactly between them. That tension is what Prompts #5 and #6 exist to manage.

## Prompt inventory (16 prompts)

| # | Category | Prompt | Purpose |
|---|---|---|---|
| 1 | Onboarding | Profile prompt copy generator | Warm, inclusive prompts guiding profile creation |
| 2 | Onboarding | Bio suggestion generator | Optional bio-writing help from user-provided facts |
| 3 | Onboarding | Inclusive language reviewer | Checks onboarding copy for exclusionary assumptions |
| 4 | Matching | Matching factor documenter | Documents what signals feed the matching algorithm |
| 5 | Matching | Matching explainability generator | User-facing "why you matched" explanation |
| 6 | Matching | Protected-attribute leakage checker | Confirms explanations don't reveal protected traits |
| 7 | Matching | Fairness audit designer | Defines what a fairness test of the algorithm looks like |
| 8 | Moderation | Message risk classifier | Flags harassment/spam/scam risk before delivery |
| 9 | Moderation | Photo policy checker (text-description variant) | Flags policy-violating photo descriptions from metadata |
| 10 | Moderation | Adversarial test case generator | Generates edge-case abusive inputs to test the classifier |
| 11 | Moderation | Appeal response drafter | Drafts a response to a user appealing a moderation action |
| 12 | Testing | A/B test hypothesis writer | Turns a product idea into a testable hypothesis |
| 13 | Testing | A/B test result interpreter | Interprets results without overclaiming significance |
| 14 | Testing | Fairness regression test generator | Ensures matching changes don't introduce new bias |
| 15 | Safety | Crisis-language escalation prompt | Flags messages suggesting self-harm/crisis for human escalation |
| 16 | Docs | Trust & safety FAQ generator | User-facing explanation of moderation policies |

## Prompt orchestration plan

Four waves. Two of them run in an order that will look backwards if you are used to normal build-then-test flow.

**Wave 2 runs the fairness audit before building the explainability layer.** **Wave 3 generates adversarial test cases before the classifier is finished.**

Both are deliberate. In a normal project you build, then test. Here, testing *first* defines what you are allowed to build — because a matching algorithm that turns out to be unfair is not fixed by better explanations on top of it.

```
Wave 1 — Onboarding design
  #1 Profile prompt copy generator
    → #3 Inclusive language reviewer (input: #1's output)
    → revise until #3 returns no flags
  #2 Bio suggestion generator — designed and reviewed alongside #1/#3,
     always labeled as an optional, editable suggestion in the UI

Wave 2 — Matching design (fairness-first ordering — deliberately different
from the e-commerce case study, where testing came after build)
  #4 Matching factor documenter (input: proposed algorithm design)
    → #7 Fairness audit designer (input: #4's documented factors)
    → run the actual fairness audit against real/synthetic data
    → IF audit reveals disparate outcomes: back to algorithm design
    → IF clean: proceed
  #5 Matching explainability generator (input: approved algorithm)
    → #6 Protected-attribute leakage checker (input: #5's output)
    → revise until #6 returns no flags

Wave 3 — Moderation (built and tested adversarially before launch, not after)
  #10 Adversarial test case generator (input: known abuse patterns)
    → #8 Message risk classifier tested against #10's output
    → #9 Photo policy checker tested against #10's output
    → iterate until classifier catches all adversarial cases in the test set
  #15 Crisis-language escalation — tested with its own adversarial set,
     reviewed with a trust & safety specialist, not engineering alone
  #11 Appeal response drafter — designed once #8/#9 are stable, so
     appeals have a stable policy to reference

Wave 4 — Launch and iterate
  #12 A/B test hypothesis writer — per experiment
  #13 A/B test result interpreter — per experiment readout
  #14 Fairness regression test — runs in CI on every matching-algorithm
     change, permanently, per the fairness testing plan below
  #16 Trust & safety FAQ generator — at launch, updated per policy change
```

## Prompt examples (17 in full)

### 1. Profile prompt copy generator
**Purpose:** Warm, inclusive copy guiding users through profile creation.
```
Write onboarding prompt copy for a dating app profile-creation step
asking about [field, e.g., "what are you looking for"]. Tone: warm,
inclusive, low-pressure. Must NOT assume a specific gender, orientation,
relationship structure, or age range. Offer an explicit "prefer not to
say" option in the copy where the field is optional.
```
**Expected output:** 1-2 sentences of UI copy, gender/orientation-neutral, with an explicit opt-out mentioned where relevant.
**Safety/guardrails:** Always run Prompt #3 against this before it ships — inclusive language is easy to get subtly wrong (e.g., defaulting to binary gender framing) even with an explicit instruction not to.

### 2. Bio suggestion generator
**Purpose:** Optional bio-writing help built strictly from facts the user themselves provided — never invented personality.

```
The user provided these facts about themselves: [paste user-supplied
facts only — e.g., "plays guitar, teaches maths, has a rescue dog,
prefers hiking to nightlife"].

Write [3] short bio options (max 40 words each) using ONLY these facts.
Tone: [warm / dry-humoured / straightforward].

Do not invent any detail not in the list above — no imagined hobbies,
no personality claims ("adventurous," "easy-going") the user did not
state, no physical descriptions.

Label the output clearly as suggestions the user can edit or discard.
```

**Variants:**
- *Expansion mode:* "Ask up to 3 clarifying questions first if the provided facts are too sparse for a distinctive bio" — better than padding with invention.
- *Rewrite mode:* "Here is the user's existing bio: [paste]. Improve clarity and flow without adding any new claims" — for editing rather than generating.

**Expected output format:** Markdown — 3 numbered options, each under 40 words, followed by an explicit "These are suggestions — edit freely" line.

**Example input:** `plays guitar, teaches maths, rescue dog named Idli, prefers hiking to nightlife`

**Example output:**
```
1. Maths teacher by day, mediocre guitarist by night. Weekends are for
   hiking with my rescue dog, Idli. Not much of a nightlife person.

2. I teach maths, play guitar badly but enthusiastically, and share a
   flat with a rescue dog called Idli. Happiest on a trail.

3. Guitar, maths, and a rescue dog named Idli. I'd pick a hike over a
   club most weekends.

These are suggestions — edit freely, or write your own.
```

**Safety/guardrails:** The "invent nothing" constraint is the whole safety mechanism. A bio that fabricates traits creates a profile that misrepresents a real person to other real people — a meaningfully different harm from a fabricated product description. Per the chapter's consent-scoped generation principle, output must always be presented as an editable suggestion, never auto-applied to a profile.

**Test case:** Given facts with no personality adjectives, the output contains no personality adjectives.

**Catalog metadata:** `id: dating-bio-suggest-v1` · `version: 1.0.0` · `tags: [dating, onboarding, customer-facing]` · `author: asha.k`

---

### 3. Inclusive language reviewer
**Purpose:** Catches exclusionary assumptions in onboarding copy before it ships.
```
Review this onboarding copy for exclusionary assumptions: [paste copy].
Specifically check: does it assume a gender binary, a specific
orientation, a specific relationship structure (e.g., monogamy-only
framing), or an age range? Does it provide an inclusive option or
opt-out where the topic is sensitive? Flag each issue found, or return
"no issues found."
```
**Expected output:** A specific list of flagged assumptions, or an explicit clean pass.
**Safety/guardrails:** This should be reviewed periodically by an actual human from outside the immediate team — a reviewer with the same blind spots as the copy's author won't catch everything the prompt does either.

### 4. Matching factor documenter
**Purpose:** Makes the matching algorithm's actual inputs explicit and auditable before it's built.
```
Document every signal this matching algorithm design uses as an input:
[paste design/pseudocode]. For each signal, state: is it directly
provided by the user, inferred from behavior, or inferred from
demographic data? Flag any signal that is a proxy for a protected
attribute (e.g., zip code as a proxy for race/income) even if not
labeled as such.
```
**Expected output:** A table of signals with provenance (direct/inferred) and explicit proxy-risk flags.
**Safety/guardrails:** "Zip code as a proxy" is a real, well-documented pattern — this prompt should be treated as a first pass, not a substitute for an actual fairness specialist's review on a production system.

### 5. Matching explainability generator
**Purpose:** User-facing explanation of why two profiles matched, without exposing sensitive detail.
```
Generate a user-facing "why you matched" explanation using ONLY these
approved factors: [paste list of approved, non-sensitive shared
interests/preferences — e.g., "both interested in hiking," "similar
distance preference"]. Do not reference any factor not in this approved
list, even if present in the underlying data.
```
**Expected output:** A short, friendly explanation citing only pre-approved factors.
**Safety/guardrails:** The approved-factors allowlist (not a denylist) is the actual safety mechanism here — restricting the prompt to only cite what's explicitly whitelisted is much safer than trying to blocklist every sensitive factor after the fact.

### 6. Protected-attribute leakage checker
**Purpose:** Confirms a match explanation doesn't reveal or imply a protected attribute.
```
Review this match explanation: [paste explanation]. Does it directly
state or strongly imply anything about race, religion, disability
status, sexual orientation (beyond what the user explicitly disclosed
for matching purposes), immigration status, or similar protected
attributes? Flag with the exact phrase if so.
```
**Expected output:** A flag with exact quoted phrase, or a clean pass.
**Safety/guardrails:** Run against every explanation template, not just new ones — a template that was fine in isolation can leak information when combined with a specific user's sparse profile (e.g., "shares your background" is fine generically but risky if it's the only shared factor for a user with few profile fields filled in).

### 7. Fairness audit designer
**Purpose:** Defines what an actual fairness test of the matching algorithm looks like, before the algorithm is finalized.
```
Given this matching algorithm's documented signals: [paste from Prompt
#4's output], design a fairness audit: what user subgroups should match
rates be compared across (e.g., by age bracket, by stated preference
category), what disparity threshold would be concerning, and what data
would be needed to run this audit that we don't currently have.
```
**Expected output:** A named list of subgroup comparisons, a stated disparity threshold, and an explicit data-gap list.
**Safety/guardrails:** The "data gap" output is important — if the audit can't actually be run with available data, that's a blocker to be resolved before launch, not a footnote.

### 8. Message risk classifier
**Purpose:** Flags harassment, spam, or scam risk in a message before it's delivered.
```
Classify this message for risk before delivery: [paste message text].
Categories: harassment, spam/scam (including off-platform payment
requests), safe. For non-safe classifications, state severity (low/
medium/high) and the specific phrase that triggered the flag. Err
toward flagging borderline cases for human review rather than silently
allowing them.
```
**Expected output:** A category, severity, and quoted trigger phrase, or "safe."
**Safety/guardrails:** "Err toward flagging borderline cases" is a deliberate precision/recall tradeoff — in this domain, a false positive (an over-cautious flag reviewed by a human) is far cheaper than a false negative (real harassment delivered unflagged).

### 9. Photo policy checker (text-description variant)
**Purpose:** Flags likely policy-violating photos from text descriptions/metadata, as a triage layer that routes to human review rather than auto-removing.

```
Here is a text description of an uploaded profile photo, generated by
[image classifier / alt-text model]: [paste description]. Here is
available metadata: [paste — e.g., face count, contains-text flag].

Against this photo policy: [paste policy], classify as: LIKELY-COMPLIANT,
NEEDS-HUMAN-REVIEW, or LIKELY-VIOLATION.

State which specific policy clause is implicated and what in the
description triggered it. If the description is too vague to judge
confidently, return NEEDS-HUMAN-REVIEW — do not guess.
```

**Variants:**
- *Strict onboarding mode:* "Default to NEEDS-HUMAN-REVIEW for any first-upload photo from a new account" — higher friction where impersonation risk is highest.
- *Specific-clause mode:* "Check only against clause [N]" — for re-running a targeted check after a policy change without re-reviewing everything.

**Expected output format:** JSON — `{"classification": "...", "policy_clause": "...", "trigger": "...", "confidence": "high|low"}`

**Example input:** Description: *"A photo of a person holding a sign with a phone number and the text 'add me on telegram'"*

**Example output:**
```json
{
  "classification": "LIKELY-VIOLATION",
  "policy_clause": "3.2 — no contact details or off-platform solicitation in photos",
  "trigger": "sign contains a phone number and off-platform handle",
  "confidence": "high"
}
```

**Safety/guardrails:** This prompt reasons over a *description*, not the image itself — the description may be wrong, incomplete, or miss context entirely. Never auto-remove on a `LIKELY-VIOLATION` alone; route to human review. The `confidence: low` path must always map to human review, not to a default-allow.

**Test case:** Given a vague description ("a person outdoors"), returns `NEEDS-HUMAN-REVIEW` rather than `LIKELY-COMPLIANT`.

**Catalog metadata:** `id: dating-photo-policy-v1` · `version: 1.0.0` · `tags: [dating, moderation, safety-critical]` · `author: asha.k`

---

### 10. Adversarial test case generator
**Purpose:** Generates edge-case abusive inputs to stress-test the moderation classifier before real users encounter gaps in it.
```
Generate [N] adversarial test messages designed to evade a harassment/
scam classifier: use techniques like misspellings, unicode substitution,
indirect phrasing, and split-message patterns (spreading a scam across
multiple otherwise-innocuous messages). For each, state what real-world
abuse pattern it's modeling.
```
**Expected output:** N test messages, each labeled with the real-world pattern it represents.
**Safety/guardrails:** This prompt generates content designed to test a safety system, not to actually harass anyone — keep generated test cases in a clearly-labeled, access-restricted test fixture, never in a shared or production-adjacent space.

### 11. Appeal response drafter
**Purpose:** Drafts a response to a user appealing a moderation action — respectful and specific, without leaking detection methods that would help bad actors evade them.

```
A user is appealing this moderation action: [paste action taken + policy
clause cited]. Here is their appeal message: [paste appeal]. Here is the
reviewer's decision: [UPHELD / OVERTURNED] with reasoning: [paste].

Draft a response that: states the outcome plainly in the first sentence,
explains which policy applied in plain language, and states what happens
next (restored / remains actioned / how to appeal further).

Do NOT reveal: specific detection signals, thresholds, or what
would have avoided detection. If OVERTURNED, apologise plainly and
without excessive hedging.

Tone: respectful, non-condescending, brief.
```

**Variants:**
- *Overturned:* "Lead with the apology and the restoration, not the policy explanation" — the user was wronged; policy detail is secondary.
- *Repeat appeal:* "This is their [N]th appeal on the same action. Restate the outcome and clearly state this is final, without becoming hostile."

**Expected output format:** Markdown — short message, outcome stated in sentence one, 3 short paragraphs maximum.

**Example input:** Action: message blocked under clause 4.1 (off-platform payment solicitation). Decision: UPHELD.

**Example output:**
> Your message was blocked and that decision stands after review.
>
> Our policy doesn't allow messages asking other users to send payments or move to off-platform payment apps. This applies regardless of intent — it's one of the most common patterns in scams targeting our users.
>
> Your account remains in good standing and this doesn't affect anything else. If you believe this was a mistake, you can reply once more and a second reviewer will look at it.

**Safety/guardrails:** The "do not reveal detection signals" constraint is genuinely load-bearing — appeal responses are a well-known information leak that sophisticated bad actors use to reverse-engineer moderation thresholds. Balance that against the user's right to a meaningful explanation: name the *policy*, never the *detection mechanism*.

**Test case:** An upheld-appeal response names the policy clause but contains no threshold, score, or signal detail.

**Catalog metadata:** `id: dating-appeal-response-v1` · `version: 1.0.0` · `tags: [dating, moderation, customer-facing]` · `author: asha.k`

---

### 12. A/B test hypothesis writer
**Purpose:** Turns a vague product idea into a testable, falsifiable hypothesis.
```
Turn this product idea into a testable A/B test hypothesis: [paste idea,
e.g., "showing mutual friends might increase match quality"]. State: the
hypothesis in "if we X, then Y, because Z" form, the primary metric,
one guardrail metric that must not regress, and minimum sample size
reasoning at a high level.
```
**Expected output:** A structured hypothesis with a primary metric and at least one guardrail metric.
**Safety/guardrails:** The guardrail metric matters specifically in this domain — e.g., an experiment that increases messages-sent but also increases harassment-report-rate should be treated as a regression, not a win, and the hypothesis structure should force that tradeoff to be stated up front.

### 13. A/B test result interpreter
**Purpose:** Prevents overclaiming statistical significance from noisy or underpowered results.
```
Interpret this A/B test result: [paste metrics, sample sizes, confidence
intervals]. State clearly: is this result statistically significant at
a reasonable threshold, is the sample size adequate for the effect size
claimed, and what specifically would you want to see before rolling
this out to 100% of users. Do not round "not significant" up to "trending
positive" or similar softened language.
```
**Expected output:** A direct significant/not-significant verdict, sample-size adequacy check, and rollout recommendation.
**Safety/guardrails:** The explicit instruction against softening a null result is there because that's a well-known human bias this chapter doesn't want the model to launder — a prompt that lets someone hear what they wanted to hear from a null result is actively harmful here.

### 14. Fairness regression test generator
**Purpose:** Generates a CI test proving a matching-algorithm change doesn't introduce disparity that wasn't there before — the permanent guard behind Wave 2's one-time audit.

```
Here is the fairness audit design: [paste from Prompt #7 — subgroups,
disparity threshold]. Here is the current algorithm's measured baseline
match rate per subgroup: [paste baseline figures].

Generate a regression test in [framework] that: runs the matching
algorithm against a fixed evaluation dataset, computes match rate per
subgroup, and FAILS if any subgroup's disparity versus the baseline
exceeds [threshold] — or if a subgroup drops below a minimum sample
size for the comparison to be meaningful.

The failure message must name the specific subgroup and the measured
disparity, not just "fairness test failed."
```

**Variants:**
- *Intersectional:* "Also compute disparity across intersections of two attributes (e.g., age bracket × stated preference), and flag if any intersection has too few samples to evaluate" — catches disparity invisible in single-axis analysis.
- *Trend mode:* "Compare against the last 5 recorded baselines rather than one, and flag gradual drift even where each individual change passed."

**Expected output format:** Runnable test code, plus a short comment block stating what a failure means and who to escalate to.

**Example input:** Subgroups: age brackets 18-25 / 26-35 / 36-50 / 51+. Threshold: 10% relative disparity. Baseline match rates: 0.42 / 0.45 / 0.38 / 0.29.

**Example output (excerpt):**
```python
# FAILURE MEANING: this change altered match rates unevenly across
# subgroups. Do not merge. Escalate to the fairness reviewer, not the
# on-call engineer — this needs judgement, not a hotfix.

def test_match_rate_disparity_within_threshold():
    rates = compute_match_rates(EVAL_DATASET, subgroup="age_bracket")
    for bracket, baseline in BASELINE_RATES.items():
        assert sample_size(bracket) >= MIN_SAMPLE, \
            f"{bracket}: sample too small to evaluate fairness"
        disparity = abs(rates[bracket] - baseline) / baseline
        assert disparity <= 0.10, \
            f"{bracket}: match rate moved {disparity:.1%} vs baseline"
```

**Safety/guardrails:** The minimum-sample-size assertion matters as much as the disparity check — a subgroup with 4 users will show wild rate swings that are noise, and a test that "passes" by silently skipping under-sampled subgroups gives false assurance. Note also the baseline itself may encode existing bias; this test prevents *new* disparity, it does not certify the current state is fair. That's what the periodic full audit (#7) is for.

**Test case:** Given a change that moves one subgroup's match rate by 15%, the test fails and names that subgroup.

**Catalog metadata:** `id: dating-fairness-regression-v1` · `version: 1.0.0` · `tags: [dating, testing, fairness, ci]` · `author: asha.k`

---

### 15. Crisis-language escalation prompt
**Purpose:** Flags messages suggesting a user may be in crisis for human (not purely automated) escalation.
```
Review this message for language suggesting the sender may be at risk of
self-harm or in crisis: [paste message]. This is NOT a moderation/abuse
classification — it is a wellbeing check. If any signal is present, flag
for immediate human trust & safety review with the specific concerning
phrase quoted. If uncertain, flag anyway — do not attempt to resolve
this automatically or generate a response to the user yourself.
```
**Expected output:** A flag with quoted phrase, or "no crisis signal detected" — never a generated response to the at-risk user.
**Safety/guardrails:** This is the single highest-stakes prompt in the entire repo. It must never be the final step — its only job is to route to a trained human, immediately, with zero automated response generated toward the user in question. Treat any change to this prompt as requiring trust & safety sign-off, not just an engineering review.

---

### 16. Trust & safety FAQ generator
**Purpose:** User-facing explanation of moderation policies — honest about what the platform does and doesn't do, without becoming an evasion manual.

```
Write a Trust & Safety FAQ entry answering: [question, e.g., "How do you
decide what messages get blocked?"].

Ground it strictly in this policy: [paste relevant policy text].

Explain: what the policy covers, that both automated systems and human
reviewers are involved, and how a user can appeal or report.

Do NOT reveal: specific detection thresholds, signal weights, or
anything that would help someone evade moderation. Do NOT overstate
capability — if the system misses things, say so honestly rather than
implying total coverage.

Tone: plain, calm, non-defensive. Maximum 150 words.
```

**Variants:**
- *Safety-feature framing:* "Answer from the perspective of what the user can control (blocking, reporting, privacy settings)" — for questions where user agency is the more useful answer than platform process.
- *Incident-response variant:* "This FAQ is being updated following a publicised incident: [describe]. Acknowledge it directly without defensiveness or legal hedging."

**Expected output format:** Markdown — question as a heading, answer under 150 words, ending with the relevant action link (report / appeal / settings).

**Example input:** *"How do you decide what messages get blocked?"*

**Example output:**
> **How do you decide what messages get blocked?**
>
> Messages are checked against our community policy — mainly for harassment, scams, and requests to move payments off-platform. Some checks are automated; anything borderline goes to a human reviewer before action is taken.
>
> No system catches everything. If something reaches you that shouldn't have, please report it — reports are reviewed by a person and directly improve our detection.
>
> If you think we got it wrong on one of your messages, you can appeal and a second reviewer will look at it.
>
> [Report a message] · [Appeal a decision]

**Safety/guardrails:** Two competing pressures meet here — legal/PR instinct pushes toward vague reassurance, while user trust requires honesty about limits. The "do not overstate capability" instruction resolves it deliberately toward honesty: "no system catches everything" is both true and protective, since implying total coverage creates false safety expectations that make users *less* cautious.

**Test case:** Output contains an honest limitation statement and no numeric threshold or signal detail.

**Catalog metadata:** `id: dating-safety-faq-v1` · `version: 1.0.0` · `tags: [dating, docs, customer-facing, safety]` · `author: asha.k`

## Fairness and bias testing plan

| Test | What it checks | Cadence |
|---|---|---|
| Fairness audit (Prompt #7's design, run against real data) | Match rate disparity across defined subgroups stays under the agreed threshold | Before launch, then quarterly |
| Protected-attribute leakage check (Prompt #6) | No match explanation reveals/implies a protected attribute | Every new explanation template; sampled weekly in production |
| Moderation classifier adversarial suite (Prompt #10's outputs, run against #8/#9) | Classifier catches known evasion patterns | Before launch, then on every classifier model/prompt change |
| Fairness regression test (Prompt #14) | A matching-algorithm change doesn't newly introduce disparity that wasn't there before | CI, on every PR touching matching logic |
| A/B guardrail metric tracking | No experiment "wins" on engagement while regressing a safety/trust metric | Every experiment readout |

## Reflection questions

1. The fairness audit (Wave 2) runs **before** the explainability layer is built, not after. Why does that ordering matter — and what would go wrong if you swapped them?
2. The crisis-language prompt (#15) is forbidden from generating *any* response to the user. Why is that restriction more important here than in any other prompt in this repo?
3. If the launch timeline were cut in half and you could keep only one of the 16 prompts, which would you keep? And what would you tell leadership about the risk of cutting the rest?

---

← [Chapter 7 — Case Study: Trading](./chapter-07-case-study-trading.md) · [Learning path](./learning-path.md) · Next: [Roles and Jobs](./roles-and-jobs.md)
