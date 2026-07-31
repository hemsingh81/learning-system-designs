# 01 — Sprint 0: Foundations

← [00 — The brief](00-the-brief.md) · [Case study index](README.md) · Next: [02 — Sprint 1: Discovery](02-sprint-1-discovery.md)

> **One line:** Rahul spends two weeks producing nothing a client can see, and it is the highest-return fortnight of the project.

---

## 1. Monday, 09:40

The repository has eleven files in it and nine of them are empty.

Seven people are in a room in Kestrel's office with a whiteboard that says **SPRINT 0 — FOUNDATIONS** and, underneath it, in Farhan's handwriting, **Demo: the setup.** Amara raised an eyebrow at that when he wrote it and has not said anything yet.

Tomas Vargas, who has been on the project for forty minutes and would like to feel useful, opens his AI assistant and types something entirely reasonable:

> *"Write me a function that inserts extracted positions into Azure SQL."*

Ten seconds later he has a function. It is clean. It has type annotations, a docstring, sensible error handling and a name that fits the project. It opens a connection using a connection string, and the connection string contains a password read from an environment variable called `SQL_PASSWORD`.

That is a completely normal way to connect to SQL Server. It is also, on this project, a hard no. Northwind's security review has exactly one non-negotiable line in it, and that line is **no API keys, no passwords, anywhere.**

The assistant had no way of knowing that. Nobody had told it.

Rahul Nair, who has done this on three previous engagements, closes Tomas's laptop lid about two inches — which is his version of shouting — and says the sentence that starts Sprint 0:

> "Before anyone generates another line, we generate the context file."

---

## 2. What Sprint 0 is, and why it has a number

**Sprint 0 is a sprint in which nothing ships.**

That's the whole idea and it's uncomfortable enough that it needs defending, which is what most of this chapter is.

Its purpose is to make the environment safe to work in before anybody works in it. Concretely, at Kestrel it produces five things:

| What | Why | Prompt |
|---|---|---|
| A project context file | So every AI session starts knowing the rules it could not have inferred | [P01](../../AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md) |
| Working database access | So the first person who needs to write a row isn't inventing an auth pattern under time pressure | [P02](../../AI-Prompts-Library/phase-0-foundation/P02-connect-the-database.md) |
| An MCP server | So the assistant can read the real schema instead of guessing from a `.sql` file | [P03](../../AI-Prompts-Library/phase-0-foundation/P03-wire-up-an-mcp-server.md) |
| Hooks | So the rules that can be checked mechanically are checked mechanically | [P04](../../AI-Prompts-Library/phase-0-foundation/P04-hooks-as-guardrails.md) |
| One team skill | So the nine-step ritual everybody will do forty times is one command | [P05](../../AI-Prompts-Library/phase-0-foundation/P05-turn-a-repeated-task-into-a-skill.md) |

None of those is a feature. All five of them are the reason the features get built without incident.

**The thing that makes Sprint 0 different in an AI-assisted team is speed.** On a project where humans write every line, a missing convention costs you a slow afternoon and a code review comment. On a project where an assistant writes four files in nine minutes, a missing convention costs you four files, a config schema, a passing test suite and a README, all of them wrong in the same consistent way, all of them looking exactly as good as the correct version would have looked.

That asymmetry is the entire argument, and it is the argument Farhan is about to lose twice.

---

## 3. Farhan asks the first time

Tuesday, 08:55, five minutes before standup. Farhan Qureshi finds Rahul at the coffee machine.

"Can we do this in three days?"

Rahul asks which three days he has in mind.

"The context file, the database and the hooks. Skip the MCP thing and the skill. We're a fortnight into a ten-week engagement and the client's seen nothing."

It is a fair question, asked by somebody whose job is to worry about exactly this, and Rahul does not dismiss it. What he says is:

> "Ask me on the Wednesday of Sprint 2 and I'll tell you whether it was worth it. If I'm wrong you'll be able to point at the day."

Farhan writes it down, which is a thing he does, and which becomes relevant on the Wednesday of Sprint 2.

There's a second reason Rahul holds the line and he doesn't say it out loud at the coffee machine. Sprint 0 is the only sprint where nobody is under delivery pressure. Every rule that gets written down here gets written down calmly. The same rules written in Sprint 2, in the middle of a build, get written as reactions to something that already went wrong, and reactive rules are always narrower than they should be.

---

## 4. P01 — the project context file

Rahul runs [P01](../../AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md) at 09:55 on the Monday, in the repository root.

### What the problem actually is

An AI coding assistant starts every conversation knowing nothing about your project. Everybody nods at that sentence and then forgets it four minutes later, which is why Tomas got a password in a connection string.

Two different things go by the name "context" and it's worth separating them.

> **The context window** is how much text the model can hold at once. Short-term working memory. When the session ends, it empties. Tomorrow morning the assistant is a brand new colleague who has never seen your code.
>
> **The project context file** is the fix for that emptiness. A plain Markdown file at the root of the repository, conventionally called `CLAUDE.md`, that the tool loads automatically at the start of every session before you type anything.

The analogy that holds: you've hired a genuinely excellent contract developer who is extremely fast, knows every library you use, and has total amnesia every night at midnight. You would not re-brief them verbally each morning. You'd write a one-page onboarding note, pin it to their desk, and update it when something changed.

### What Rahul actually asked for

The prompt does one thing that matters more than the rest: **it makes the assistant read the repository before it writes anything, and then tag every claim as either observed or supplied.**

- `(observed)` — found in the repo, and it can name the file that proves it.
- `(supplied)` — came from Rahul's brief and is not visible in the code.

That split is what makes the output reviewable rather than merely plausible. You can verify every `(observed)` line in thirty seconds. Every `(supplied)` line is your own claim reflected back at you, so if it's wrong, that's on the brief.

He supplies eight invariants. Here they are, because they are the spine of everything in this book:

```text
1. A wrong number is worse than no number. Every extracted field carries a
   confidence score and low confidence never silently enters the warehouse.
2. One failing field sends the whole document to review. Never partially
   ingest a statement.
3. Bronze is immutable and is written before any parsing happens.
4. Idempotency is by SHA-256 of file content, never by filename.
5. Redaction fails closed — if the PII call errors, raw text is not persisted,
   a marker is.
6. No API keys anywhere. Managed identity via DefaultAzureCredential for all
   Azure services; Snowflake uses key-pair (JWT) auth.
7. The confidence gate sits upstream of reconciliation, never downstream.
8. Adding a counterparty is a YAML change plus a trained model — never a
   code change.
```

Some of those need unpacking, and the file itself unpacks them for anybody who reads it later:

> **Managed identity.** An identity the cloud platform hands to your running code automatically. Instead of your code carrying a password to prove who it is, the platform vouches for it. In Python you get it through `DefaultAzureCredential`, a helper from the Azure SDK that tries several ways of proving identity in order and uses the first that works — your developer login on your laptop, the platform-assigned identity in production. The roles this project uses are `Cognitive Services User`, `Storage Blob Data Contributor` and `Key Vault Secrets User`.

> **Key-pair (JWT) auth.** Snowflake isn't on Azure's identity system, so managed identity doesn't apply. Instead of a password you register a public key with Snowflake and hold the private key; the client signs a short-lived token — a **JWT**, a JSON Web Token, a small signed blob proving who you are and when it expires — and sends that. No shared secret travels over the wire and nothing long-lived sits in a config file.

> **SHA-256.** A function that turns any file into a fixed 64-character fingerprint. Change one byte and the fingerprint changes completely. Invariant 4 says the pipeline decides "have I seen this document before?" by fingerprinting the *contents*, not by looking at the filename — because counterparties resend the same statement under a new name constantly, and Priya has the `_v2.pdf` files to prove it.

### What came back

Abridged; the full file is at [`artifacts/CLAUDE.md`](artifacts/CLAUDE.md).

```markdown
# CLAUDE.md — Northwind Counterparty Document Ingestion

## What this project is

An Azure Functions service that receives counterparty statements and trade
confirmations as PDFs, extracts positions and trades with Azure AI Document
Intelligence, gates every extracted field on its confidence score, and loads
what passes into Azure SQL and Snowflake. Anything failing the gate goes to a
human review queue instead. The purpose is to remove manual keying so that
reconciliation breaks against the Aladdin feed surface at T+1 rather than T+2.

## Repository map

| Folder | Single responsibility |
|---|---|
| `config/` | (observed) `sources.yaml` holds one block per counterparty;
             `settings.py` holds environment-derived configuration. No logic. |
| `core/`   | (observed) Pure logic. Classification, extraction orchestration,
             the confidence gate, the rules engine, transform, redaction,
             translation, idempotency. No direct I/O to storage or databases. |
| `sources/`| (observed) Inbound integrations. Today only `aladdin_api.py`. |
| `sinks/`  | (observed) The only place that writes anywhere. |
| `recon/`  | (observed) `reconcile.py` — full outer join, break classification. |
| `sql/`    | (observed) `schema.sql` — the Azure SQL silver schema. |
| `tests/`  | (observed) pytest suite mirroring `core/`. |
| `function_app.py` | (observed) Azure Functions entry point. Bindings only. |

## Conventions

- (supplied) Raw parameterised SQL only. No ORM. Every query is readable in the
  source file that runs it.
- (observed) Type annotations on every public function. `mypy` strict over
  `core`, `sources`, `sinks`, `recon`.
- (supplied) Logging is structured. One event per document carrying
  `document_sha256`, `counterparty` and `min_confidence`. Never log field values.
- (supplied) Errors a human must act on become rows in `etl.extraction_exception`,
  not log lines. Log lines are for engineers; the exception queue is for Priya.
- (observed) Tests are named `test_<behaviour>_<condition>`, e.g.
  `test_gate_rejects_currency_below_threshold`.
- (supplied) `core/` may not import from `sinks/` or `sources/`.

## Unknowns

1. What is the retention policy on `bronze/`? Indefinite, or a lifecycle rule?
2. Is there a staging Snowflake account, or does everything below production go
   to Azure SQL only?
3. Which Azure region are the Document Intelligence resources in? Affects both
   latency and whether EM documents can be processed under data residency rules.
4. Who owns `sql/schema.sql` in production — us, or Northwind's DBA team?
5. Is there an existing Application Insights workspace, or do we create one?
```

### The three things worth noticing

**The last convention is the one that gets quoted most.** *"Errors a human must act on become rows in `etl.extraction_exception`, not log lines. Log lines are for engineers; the exception queue is for Priya."* Rahul wrote that in Sprint 0, before there was a PRD, before the exception queue existed as a story, before anybody had said the word. It comes straight out of the brief and it is the earliest appearance in this book of the idea that will nearly evaporate in Chapter 3.

**The Unknowns section did real work.** Question 4 — who owns `schema.sql` in production — got asked on the Wednesday call with Northwind. The answer was "our DBA team, and they will not accept an automated migration from a vendor." That single answer changed the deployment design, added a manual approval step to the runbook, and is the direct reason `sql/schema.sql` sits behind a blocking hook by Friday.

**A generated context file with an empty Unknowns section has failed.** It means the assistant filled gaps with guesses. Rahul's had five and two of them turned into real project decisions.

### The thing Rahul got wrong the first time

His first run produced the invariants in the wrong order. Managed identity was invariant 6, near the bottom, below four rules about confidence scoring. That felt right at the time, because confidence scoring is what the project is *about*.

Two days later, mid-way through a long session building out the Snowflake sink, the assistant produced a `snowflake.connector.connect()` call with a password parameter — while cheerfully citing the confidence invariants at the top of the file.

Rahul's read: **rules at the top of a long file get applied, rules at the bottom get skimmed.** He reordered so the two security invariants sit at positions 1 and 2. That ordering survived the rest of the project.

---

## 5. P02 — connect the database

Tomas runs [P02](../../AI-Prompts-Library/phase-0-foundation/P02-connect-the-database.md) on the Monday afternoon, which is the same task he failed at 09:40, now with the context file loaded.

He does not mention managed identity in the prompt. He doesn't have to; invariant 1 is loaded before he types a word. **That is the entire return on P01, and it shows up within six hours.**

What comes back is [`core/clients.py`](code/doc_ingestion/core/clients.py) — one module that owns every outbound connection the project makes:

```python
"""Every outbound client, in one place, with no secrets anywhere.

Northwind security review: no API keys, no passwords, no connection strings
carrying credentials. Azure services use managed identity; Snowflake uses
key-pair (JWT) auth with the private key held in Key Vault.
"""

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.storage.blob import BlobServiceClient

from config.settings import settings


@lru_cache(maxsize=1)
def _credential() -> DefaultAzureCredential:
    """One credential for the whole process.

    DefaultAzureCredential tries several identity sources in order and uses the
    first that works: the developer's az-cli login locally, the function app's
    assigned managed identity in Azure. Cached because token acquisition is not
    free and a cold start is already slow enough.
    """
    return DefaultAzureCredential()


@lru_cache(maxsize=1)
def document_intelligence() -> DocumentIntelligenceClient:
    return DocumentIntelligenceClient(
        endpoint=settings.doc_intelligence_endpoint,
        credential=_credential(),
    )


@lru_cache(maxsize=1)
def blob_service() -> BlobServiceClient:
    return BlobServiceClient(
        account_url=settings.storage_account_url,
        credential=_credential(),
    )
```

Two details in there are load-bearing and they're the kind of thing that only gets right when somebody has thought about the runtime.

**`lru_cache` rather than module-level globals.** Azure Functions on a consumption plan is serverless — the code runs in a container the platform spins up on demand and throws away when it's idle. That means **cold starts**: the first request after a quiet period pays the cost of starting the whole process. A module-level client built at import time makes every cold start slower and, worse, holds a credential that may have expired by the time the function is invoked. Caching on first call moves the cost to where it belongs.

**No connection string anywhere.** The Azure SQL sink uses the same credential path; Snowflake pulls its private key from Key Vault at call time. There is no environment variable in this project whose name contains the word `PASSWORD`, and by Friday there is a hook that makes sure of it.

---

## 6. P03 — the MCP server

Wednesday. This is the one Farhan wanted to cut.

### What an MCP server is, plainly

> **MCP** stands for Model Context Protocol. It is a standard way of giving an AI assistant access to a live system — a database, a ticket tracker, a file store — so that instead of you pasting information in, the assistant can go and ask.
>
> **An MCP server** is a small program that sits in front of one of those systems and exposes a fixed set of things the assistant is allowed to do. Not "run any SQL." Specifically: list tables, describe a table's columns and types, show indexes. Read-only, enumerated, and you decide what's on the list.

The distinction that matters: without it, the assistant knows what `sql/schema.sql` says. With it, the assistant knows what the database **is**. Those diverge the first time somebody applies a change by hand, and on this project they diverge permanently, because Northwind's DBA team owns production schema and Kestrel's file is a proposal rather than a record.

### What Rahul wires up

Two servers, both read-only:

| Server | What it exposes | Why |
|---|---|---|
| Azure SQL | `list_tables`, `describe_table`, `list_indexes` on the `etl` schema | So a session writing an insert can check the real column types instead of inferring from a file that may be stale |
| Snowflake | `describe_table` on the gold layer only | So the merge statement is written against the real target |

Neither can write. Neither can drop. Neither can see anything outside the named schemas. Rahul's rule, stated in the setup note and repeated at standup: **an MCP server is a way of letting the assistant read your reality, not a way of letting it change your reality.**

### The moment it pays for itself

Sprint 2, day six. Tomas asks the assistant to write the insert into the exception table. Without the MCP server, the assistant would have read `sql/schema.sql`, seen `FIELD_CONFIDENCE decimal(5,4)`, and written code passing a Python `float` straight in.

With the server, the assistant runs `describe_table('etl', 'extraction_exception')` first, sees that the deployed column is `decimal(5,4)`, and notes in its own output that a Python float will be rounded on insert and the round-trip won't be exact. That's a one-line difference in the code and it's the difference between a confidence of `0.9123456` being stored as `0.9123` deliberately and being stored as `0.9123` by accident.

Small. Genuinely small. Rahul's point is that Sprint 0 is made of about nine of those, and none of them individually justifies a fortnight.

---

## 7. Farhan asks the second time

Wednesday, 16:20. This time it's in the room and Amara is there.

"We're three days in. I could have the whole team on the PRD tomorrow morning."

Rahul's answer is different from Monday's, because Farhan is asking a different question — Monday was "is this worth it," Wednesday is "can we overlap it."

What he says is that overlapping is fine for the PRD, because Amara doesn't need any of this. She needs the client's email and a room. What isn't fine is anybody generating *code* before the hooks exist, because the hooks are the only part of Sprint 0 that stops something rather than merely informing it.

Amara sides with Rahul, for a reason nobody expected: she wants the PRD written **without** engineering in the room, because a PRD written with engineers present acquires technology names in paragraph two and stops being a business document.

So the compromise is: Amara starts discovery on Thursday, Rahul finishes Sprint 0, and nobody writes production code until Monday. Farhan writes that down too.

**It is worth noticing that the argument was settled by the product owner wanting the same thing for a completely different reason.** Farhan's summary in the retro is that Sprint 0 survived on a coincidence, and he is not entirely joking.

---

## 8. P04 — hooks as guardrails

Thursday. This is the part of Sprint 0 that everybody agrees about afterwards.

### The difference between documentation and enforcement

The context file from P01 is **advisory**. The assistant reads it, agrees with it, and then, three hours into a long session under a lot of context pressure, forgets it. That is not a moral failing of the tool; it's what happens when a rule is one line among a hundred and fifty.

> **A hook** is a script the harness runs automatically at a fixed point in the assistant's loop, whether the assistant likes it or not. It is not advice. It's machinery.
>
> **A `PreToolUse` hook** runs *before* the assistant is allowed to use a tool — before a file edit lands, before a command runs. It gets told what's about to happen and it can allow it, or refuse it and say why. Refusal is the whole point: the edit does not happen.
>
> **A `PostToolUse` hook** runs *after*. You use it for things that should happen every time regardless: formatting, linting, a type check.

Rahul's line, which ends up in the team's setup notes:

> **"Documentation persuades. Hooks enforce. Know which one your problem needs."**

### The four hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command",
                    "command": ".claude/hooks/protect_owned_files.py" }]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command",
                    "command": ".claude/hooks/no_secrets.py" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command",
                    "command": "ruff check --fix $CLAUDE_FILE_PATHS" }]
      }
    ]
  }
}
```

| Hook | When | What it does |
|---|---|---|
| `protect_owned_files.py` | Before any edit or write | Blocks edits to a small list of files that a human must change deliberately, with a message saying who owns each one |
| `no_secrets.py` | Before any edit or write | Refuses any content matching a password, key or connection-string pattern, and names the invariant it's enforcing |
| `ruff check --fix` | After any edit or write | Formats and lints the changed file so no diff ever contains a style argument |
| `pytest -q` | On session end | Runs the suite so nobody discovers on Monday that Friday's last edit broke it |

The protected list starts at two entries and grows to four:

```python
# .claude/hooks/protect_owned_files.py  (excerpt)

PROTECTED = {
    "sql/schema.sql": (
        "Production schema is owned by Northwind's DBA team. They do not accept "
        "automated migrations from a vendor. Propose the change in "
        "artifacts/data-contract-counterparty-position.md and raise it with "
        "Sofia — do not edit this file."
    ),
    "config/sources.yaml": (
        "A counterparty block or a threshold is a business decision, not a code "
        "change. Thresholds are agreed with Amara and recorded in "
        "artifacts/spec-confidence-gate.md. Adding a counterparty runs the "
        "onboard-counterparty skill, which includes the steps you will otherwise "
        "forget. Do not hand-edit this file."
    ),
}
```

Read the second message carefully, because it is doing something a blanket ban wouldn't.

**It doesn't say no. It says no, and here is the thing to do instead, and here is the person who decides.** A hook that only refuses gets worked around within a week — somebody disables it, or edits the file outside the assistant, or gives up and does something worse. A hook that refuses and routes is a hook that survives.

---

## 9. P05 — one team skill

Friday. The last piece, and the one Farhan most wanted to cut, and the one with the smallest immediate return.

Onboarding a new counterparty is a nine-step ritual:

```text
1.  Collect 50 labelled sample documents for the layout family
2.  Train a custom extraction model in Document Intelligence Studio
3.  Record the resulting model id
4.  Add a counterparty block to config/sources.yaml with model_id, language,
    thresholds and any field overrides
5.  Decide whether the documents need translation (EM: usually yes)
6.  Add the intake folder convention to the blob container
7.  Run five held-out documents through the pipeline in dev
8.  Check the confidence distribution and adjust thresholds if the counterparty
    has poor scan quality
9.  Record the onboarding in artifacts/ with the held-out results
```

Nine steps, and Northwind adds a counterparty roughly once a quarter, which means everybody does it rarely enough to forget step 8 every single time. Step 8 is the one that catches `broker_alpha`-shaped problems — the ones where the scans are bad enough that the default threshold lets marginal reads through.

> **A skill** is a packaged procedure the assistant can invoke by name. Not a prompt you paste. A named, versioned set of instructions that lives in the repo, so when anybody says "onboard a counterparty" the assistant runs the same nine steps in the same order with the same checks, whoever asked and whenever they asked.

The skill lives at `.claude/skills/onboard-counterparty/SKILL.md` and it does one thing the checklist above cannot: it **stops** between step 7 and step 8 and shows the confidence distribution to a human, because deciding whether a threshold needs raising is a judgement about the counterparty's scan quality and not a thing to automate.

**The test for whether something should be a skill:** you've done it three times, it has more than five steps, and at least one step is skipped when people are busy. Onboarding hits all three.

The return arrives in Sprint 4, when Northwind adds a counterparty and it takes forty minutes with no deployment. Rahul does not claim that Sprint 0 paid for itself on that one. He does claim that the alternative — the previous vendor's design, where onboarding was a Python module and three weeks — is the thing the skill exists to make impossible.

---

## 10. The payoff, part one: Tomas's first session

**Sprint 2, Monday morning, 09:15.** Three weeks after Sprint 0 ended.

Tomas opens a fresh session to start NWD-101 and types:

> *"Implement NWD-101. Land counterparty PDFs immutably in the raw zone. Implementation plan is in `artifacts/implementation-plan-NWD-103.md` for the general shape; story is at `artifacts/stories/NWD-101.md`."*

That's it. No preamble about managed identity. No note about where sinks live. No explanation of the naming convention for tests.

The first thing that comes back, before any code:

```text
Before writing anything, from CLAUDE.md:

- I will not use a connection string or an environment variable containing a
  secret. Blob access goes through core/clients.py, which already wires
  DefaultAzureCredential (invariant 1).
- All writes go in sinks/. core/ may not import from sinks/, so the landing
  logic will be split: sinks/blob_sink.py does the write, core/idempotency.py
  computes the content hash.
- Idempotency is by SHA-256 of file content, not filename (invariant 4). I will
  key the blob path on the hash and treat a repeat hash as a no-op, not an error.
- Tests will be named test_<behaviour>_<condition>, in tests/, mirroring core/.

One question the context file does not answer: is a re-arrival of the same
content under a different filename something we log, or something we ignore
silently? The convention about the exception queue suggests it is neither an
engineer's log line nor Priya's problem. Please confirm.
```

Read that last paragraph again. **It asked a good question, and the question came out of a convention that was written down three weeks earlier for a completely different reason.**

Tomas's answer is "log it at info, don't queue it," which he checks with Rahul in about forty seconds, and it becomes a line in the runbook in Sprint 4.

What did not happen: a connection string. A `sinks` import inside `core`. Tests named `test_1`, `test_2`. A helpful new `utils.py`. An argument in code review about any of the above.

Farhan is at his desk when Tomas mentions this at standup. He looks at his notebook, finds the entry from three weeks earlier, and says nothing, which from Farhan is a considerable concession.

---

## 11. The payoff, part two: the hook fires

**Sprint 2, Tuesday. Day two of the build.**

Tomas is on NWD-102 — classify an incoming PDF to its counterparty layout. He's testing against a Broker Alpha statement and the classifier is coming back at 0.71, which is below the 0.75 minimum, which means the document routes to review instead of being extracted.

He is fairly sure this is a threshold problem rather than a model problem, because the same document classified fine yesterday. He asks the assistant to nudge the classifier minimum for `broker_alpha` down to 0.70 so he can carry on testing.

The assistant agrees that's reasonable, opens `config/sources.yaml`, and the edit does not happen:

```text
PreToolUse hook blocked this edit.

  File: config/sources.yaml
  Reason: A counterparty block or a threshold is a business decision, not a code
  change. Thresholds are agreed with Amara and recorded in
  artifacts/spec-confidence-gate.md. Adding a counterparty runs the
  onboard-counterparty skill, which includes the steps you will otherwise
  forget. Do not hand-edit this file.

No changes were made.
```

Tomas's first reaction is mild irritation, because he wants to get on with it and this is obviously a temporary change he was going to revert.

His second reaction, about ninety seconds later, is the useful one. He goes and looks at *why* the classifier dropped, and it dropped because he was testing against a statement from a **different month** whose header block had a different layout — an early sign of exactly the thing constraint C2 exists for. Lowering the threshold would have made the symptom go away and hidden the signal.

He raises it at standup. Sofia's response is the one line that gets quoted for the rest of the project:

> "That's not a threshold problem, that's the system telling you the truth."

### What everybody agrees afterwards

At the Sprint 2 retro, the team is asked what would have happened without the hook, and the answers are unanimous and specific.

**Tomas:** he'd have made the change, carried on, and reverted it at the end of the day. Probably. He is honest about the "probably."

**Rahul:** the change would have shipped. Not because Tomas is careless, but because a one-line YAML edit made to unblock yourself on a Tuesday afternoon does not feel like a change, and it would have arrived in a diff alongside 300 lines of classifier code where nobody reviews the YAML.

**Amara:** she would not have been told, because from her side nothing observable would have changed. The threshold that protects against misclassification would just have been slightly lower, permanently, for the counterparty with the worst scan quality.

**Farhan:** "That's the fortnight, isn't it."

That sentence is the closest Sprint 0 gets to being vindicated, and it lands on the Tuesday of Sprint 2 rather than the Wednesday, so Rahul's promise at the coffee machine was a day pessimistic.

---

## 12. What Sprint 0 actually cost

Honest arithmetic, because "two weeks of nothing" is a real cost and pretending otherwise helps nobody.

| Item | Time |
|---|---|
| P01 — context file, generate, argue, trim, reorder | 1.0 day |
| P02 — database access, both sinks, Key Vault wiring | 1.5 days |
| P03 — two MCP servers, read-only, scoped | 1.0 day |
| P04 — four hooks plus the protected-file list | 1.0 day |
| P05 — onboard-counterparty skill | 1.0 day |
| Repo skeleton, CI, pre-commit, dev environment for two engineers | 2.5 days |
| Northwind access, roles, subscriptions, the Key Vault argument | 2.0 days |
| **Total** | **10 days — one full sprint of one person** |

Rahul was the only person on it full time. Tomas was on it about half time. Everybody else was doing something else, which is the part of the deal that made Farhan's second question answerable.

**What it bought, measurably, by the end of Sprint 2:**

- Zero code-review comments about secrets, imports or naming across roughly 900 lines of generated Python. On the previous engagement, before the team did this, those three categories were about 40% of review comments.
- One blocked config change that everybody agreed would otherwise have shipped.
- One correctly-typed decimal insert nobody had to debug.
- A counterparty onboarded in forty minutes in Sprint 4, against three weeks for the previous vendor.

**What it did not buy:** anything the client could see at the end of the fortnight. Farhan showed Northwind a repository, a diagram and a context file. That demo was, in his own words, "the worst fifteen minutes of the project," and he did it anyway.

---

## 13. What this cost, honestly

The thing that nearly went wrong in Sprint 0 was the context file itself, and it wasn't the ordering problem in §4.

An early draft of the repository map used a real Northwind account number in a sample blob path. The assistant hadn't invented it — it had read one of the test PDFs sitting in the fixtures folder and, being helpful, used a realistic example rather than a placeholder.

The context file is a normal file in a normal repository. It gets committed, pushed, cloned onto laptops, and read by every tool anybody points at the repo. That account number would have been in git history permanently, and removing something from git history is a conversation with a security team rather than a commit.

Sofia caught it, on a Thursday, while reading the file for a completely different reason — she was looking for informally-made decisions that ought to be ADRs, and the sample path caught her eye because it looked too specific.

Two things came out of it. The first is a line in `CLAUDE.md` saying no secrets, no client data, no real identifiers, which is now the first thing in the file. The second is a fixtures policy: every test PDF in the repository is a synthetic document generated from a template, with invented instrument names and account numbers that fail a checksum on purpose.

**The uncomfortable part is that nothing in Sprint 0 would have caught it.** The `no_secrets.py` hook looks for credential patterns, and an account number isn't one. The context file's own review checklist doesn't mention client data. It was caught by one person reading carefully for an unrelated reason, which is not a control, it's luck.

That gap stays open until Sprint 3, when [P24 — Find Security Gaps](../../AI-Prompts-Library/phase-5-verify/P24-find-security-gaps.md) checks the repository properly and finds two more instances of the same class of thing. Sofia's note in the retro is short: *"We built machinery for the rule we'd already been bitten by and none for the one we hadn't."*

---

**Next:** [Chapter 2 — Sprint 1: Discovery](02-sprint-1-discovery.md). Amara turns a rambling two-page email into a PRD, slices it into eight stories, and asks the four-word question that creates the exception queue.

---

← [00 — The brief](00-the-brief.md) · [Case study index](README.md) · Next: [02 — Sprint 1: Discovery](02-sprint-1-discovery.md)
