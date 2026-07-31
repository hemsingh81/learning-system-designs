# NWD-138 — Translation is applied to identifier fields, so translated security names break the match

| | |
|---|---|
| **Raised by** | Ananya Iyer, QA Engineer |
| **Date raised** | 2026-06-22 |
| **Severity** | **High** |
| **Priority** | P2 — blocks the EM book, not the EQ book |
| **Component** | `core/translate.py` — counterparty document ingestion |
| **Affects story** | [NWD-104](stories/NWD-104.md) (translate EM documents), [NWD-106](stories/NWD-106.md) (transform) |
| **Environment** | `dev`, pipeline build `2026.06.21-b`, Document Intelligence model `broker-beta-confirm-v1`, Azure AI Translator `es` → `en` |
| **Status** | Open → Fixed 2026-06-24 → Verified 2026-06-25 |

---

## 1. Summary

Broker Beta EM trade confirmations arrive in Spanish and are normalised to English before matching, per [NWD-104](stories/NWD-104.md). The translation step is applied to **every string field in the document**, including the fields reconciliation keys on.

On confirmation `BB-CONF-20260619.pdf` the security name `TELEFONICA BRASIL SA PREFERENCIAL` is translated to `TELEFONICA BRAZIL SA PREFERRED`. Aladdin holds the untranslated name. The rows do not match on name, and one of them does not match at all, because the `security_id` field on this layout is alphanumeric and one of its components was translated too.

Everything passes. Confidence is high — the model read the Spanish correctly and Translator translated it correctly. The failure is that we asked it to.

---

## 2. Expected vs actual

Test document: `broker_beta/2026-06-19/BB-CONF-20260619.pdf` — 6 trades, Spanish, account `ACC-40211`.

| Field | Source value (es) | Expected after pipeline | Actual |
|---|---|---|---|
| `security_name` | `TELEFONICA BRASIL SA PREFERENCIAL` | `TELEFONICA BRAZIL SA PREFERRED` | `TELEFONICA BRAZIL SA PREFERRED` ✓ |
| `security_id` | `VIVT3` | `VIVT3` | `VIVT3` ✓ |
| `security_id` | `BBAS3 ON` | `BBAS3 ON` | **`BBAS3 ACTIVATED`** |
| `side` | `COMPRA` | `BUY` (via `map_values`) | `PURCHASE` — then unmapped |
| `currency` | `BRL` | `BRL` | `BRL` ✓ |
| Breaks raised | | 0 | **2 × `MISSING_EXTERNAL`, 2 × `MISSING_INTERNAL`** |

`ON` is a Brazilian share-class suffix meaning *ordinária* — ordinary shares. Translator renders it as `ACTIVATED`, which is a defensible translation of the Spanish word `on` in isolation and a catastrophic one for an identifier.

`COMPRA` becoming `PURCHASE` then falls through the `side_vocabulary` rule in `config/sources.yaml`, which maps `COMPRA` → `BUY`. It never sees `COMPRA`, so `side` arrives as `PURCHASE` and is not a value the data contract permits.

---

## 3. Steps to reproduce

1. Upload the fixture:
   ```bash
   az storage blob upload \
     --container-name raw \
     --name "broker_beta/2026-06-19/BB-CONF-20260619.pdf" \
     --file ./fixtures/BB-CONF-20260619.pdf \
     --auth-mode login
   ```
2. Wait for the worker (~35s), then read what landed:
   ```sql
   SELECT line_no, security_id, security_name, side, quantity
   FROM   silver.counterparty_position
   WHERE  content_hash = 'c41e…7b09'
   ORDER  BY line_no;
   ```

**Result:**

```
LINE_NO  SECURITY_ID       SECURITY_NAME                     SIDE      QUANTITY
-------  ----------------  --------------------------------  --------  --------
      0  VIVT3             TELEFONICA BRAZIL SA PREFERRED     PURCHASE     4000
      1  BBAS3 ACTIVATED   BANCO DO BRAZIL SA ORDINARY        PURCHASE     1500
      2  PETR4             PETROBRAS PREFERRED                SALE         2200
```

Row 1's identifier has been rewritten by a translation service. There is no path by which that value can ever match Aladdin.

---

## 4. Evidence

### 4.1 The document is translated wholesale before mapping

`core/translate.py` builds the translation payload from every string-valued field on the extraction result, before `field_map` has been applied. At that point the code does not know which fields are identifiers and which are prose — the canonical names do not exist yet.

### 4.2 The bronze response has the correct values

`bronze/broker_beta/2026-06-19/c41e…7b09.json` holds `"SecurityId": {"content": "BBAS3 ON", "confidence": 0.968}`. The correct value was extracted, at high confidence, and then modified downstream. This is recoverable without re-paying for extraction — [ADR-0002](adr/0002-persist-bronze-before-parsing.md) earning its keep.

### 4.3 Reconciliation cannot tell this from a real break

```sql
SELECT break_type, COUNT(*)
FROM   recon.break_report
WHERE  as_of_date = '2026-06-19' AND account_number = 'ACC-40211'
GROUP  BY break_type;
```

```
BREAK_TYPE          COUNT
-----------------   -----
MISSING_EXTERNAL        2
MISSING_INTERNAL        2
```

Four breaks from two positions. The same holding appears twice — once as absent from the counterparty side under its real identifier, once as an unrecognised extra under its translated one. An analyst reading the break report sees two problems where there are none, and the pairing is not obvious unless you already know to look for it.

---

## 5. Business impact

1. **The entire EM book is affected**, not one document. Every Spanish and Portuguese confirmation carries share-class suffixes and side vocabulary. On last month's volume that is roughly 40% of `broker_beta_em` line items with a translated identifier component.
2. **Breaks come in pairs and look worse than they are.** Four fabricated breaks per two positions. Priya works them individually.
3. **The data is wrong in the warehouse, not merely rejected.** These rows loaded. They carry a high `min_confidence` and a valid `bronze_path`, and the identifier in the row is a value that was never on the document.
4. **`side` arrives outside the permitted vocabulary**, which the data contract says cannot happen. Nothing rejected it, so either the contract is not enforced at this point or the rule ran before translation. Both are worth someone's attention.

---

## 6. What I ruled out

| Hypothesis | Ruled out because |
|---|---|
| The extraction misread the identifier | Bronze holds `BBAS3 ON` at confidence 0.968 |
| Translator is faulty | `ON` → `ACTIVATED` is a correct translation of a Spanish word. The service did what it was asked |
| The `side_vocabulary` rule is wrong | The mapping table is right. It is being handed `PURCHASE`, a value it was never written to see |
| Aladdin holds a different identifier | Checked three of them by hand against the Aladdin REST response. Aladdin has `BBAS3 ON` |
| Only `security_id` is affected | `side` is affected too, and any string field the matching logic touches is exposed |
| The EQ book is affected | No. `broker_alpha` is English and never enters the translation path |

---

## 7. Suggested area to investigate

`core/translate.py`, the field-selection step. Translation runs before `field_map` is applied, so it is choosing fields by the counterparty's own names, at a point in the pipeline where nothing knows which of those names is an identifier.

Two things I would want out of the fix, beyond it working:
- The list of fields never to translate should be **configuration**, in `config/sources.yaml`, using canonical post-`field_map` names. A new counterparty will have an identifier field named something we have not seen, and that must not be a code change — the whole design says onboarding a counterparty is YAML plus a trained model.
- Consider gating by field *type* as well as by name. Translator should only ever see `string` fields that are descriptive. An identifier that happens to be typed `string` still needs the name-based exclusion, so both, not either.

---

## 8. Note for whoever picks this up

The test that should have caught this does not exist, and its absence is a pattern. Every EM fixture in `tests/` is a hand-built Spanish document with security names like `ACCIONES ORDINARIAS` — descriptive text that translates harmlessly. None of them carries a real Brazilian ticker with a share-class suffix, because when I wrote them I was testing that translation *happened*, not that it happened to the right fields.

A fixture built to prove a feature works is not a fixture that can find out where it does harm.

I would also check the reverse direction. If translation can corrupt a value on the way in, the exception queue may be showing Priya a translated value while the underlying record holds a different one. Worth a look at what NWD-108 renders.

— Ananya

---

## 9. Resolution

**Fixed** 2026-07-24 by Tomas Vargas. Two commits:

1. `test: reproduce NWD-138 identifier corruption on EM confirmations`
2. `fix(translate): restrict translation to descriptive fields by config`

**Root cause:** `core/translate.py` translated every string-valued field on the raw extraction result, before `field_map` ran. Identifier and vocabulary fields were indistinguishable from prose at that point.

**Fix:**
- Translation now runs **after** `field_map`, on canonical names.
- `config/sources.yaml` gains `no_translate_fields` in `defaults` — `account_number`, `security_id`, `isin`, `cusip`, `sedol`, `ticker`, `currency`, `trade_id` — and `translate_field_types: [string]`. Both are defaults, deep-merged, so a source states only what differs.
- `side` is normalised by the existing `side_vocabulary` rule against the untranslated value, as it was always meant to be.

**Regression tests added:** 5, including one asserting `BBAS3 ON` survives the pipeline byte-identical, and one asserting a new counterparty with an unlisted identifier field is caught by the type gate.

**Fixture set extended:** `tests/fixtures/broker_beta_em_tickers.json` carries four real share-class suffixes. Ananya's point in §8 stands as a general lesson — [`retrospective-sprint-3.md`](retrospective-sprint-3.md).

**Verified** 2026-06-25 by Ananya Iyer. Six trades in, six matched, zero breaks.

---

> **Artifact contract — `artifacts/bug-NWD-138.md`**
>
> Produced by: Ananya Iyer (QA Engineer), using the bug-report standard in [P22](../../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md)
> Approved by: Rahul Nair, 2026-06-22
>
> Anyone fixing from this report can rely on finding:
> - Exact reproduction steps, including the fixture and the commands to run it
> - Expected vs actual as **values**, field by field, not descriptions
> - Raw evidence — the bronze response, the SQL and its real output
> - A ruled-out table, so no one repeats an investigation already done
> - Business impact stated in operational terms, with scope
> - Whether the reporter believes configuration, not code, is the right home for the fix
>
> This report does **not** contain: a diagnosis of the root cause, or a proposed fix.
> Those are the engineer's job — see [P27](../../../AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md).
>
> **If any guarantee above is missing, this report is not ready to prompt with.** Send it back.
>
> Changing this file: QA only, until Resolution is filled in; then it is closed.
