# Ledger Audit and Per-Project Balance Sheets — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the human-decided, evidence-based audit of `anjoman_accounting_information/reports/2026-10-10/Transactions.csv` (96 rows) and publish it as `reports/2026-10-18/` (audited ledger, audit log, decision register copy, per-project balance sheets, EN + FA reports).

**Architecture:** A new package `analysis_tools/audit/` (load → rules → apply → balance → bridge → emit) turns four committed JSON inputs plus the read-only source CSV into audited rows and an audit log; a top-level builder `analysis_tools/build_audit_report.py` renders the EN/FA reports from that data through the existing i18n catalog (`t()`, `term()`, `localize()`), WeasyPrint RTL for FA, with assert-based gates G1–G10 (spec §9) running inside `build()` and as tests.

**Tech Stack:** Python 3.11 stdlib (csv, json, argparse), jdatetime, reportlab (EN PDF), WeasyPrint via `report_common.md_to_pdf_rtl` (FA PDF), pytest, the existing `analysis_tools/i18n` catalog + `translate.py` (Claude API, VPN-gated, builders never call the API).

**Spec:** `docs/superpowers/specs/2026-10-18-ledger-audit-design.md` — the binding authority. This plan argues from it; conflicts inside the plan resolve against the spec.

## Controller rulings (binding for every task)

These resolve spec ambiguities found while writing the plan. Record them in the SDD ledger at setup:

1. **`build_audit_report.py` lives at `analysis_tools/` top level**, not inside `audit/`. Reason: `test_every_en_key_is_referenced` (test_report_i18n.py:90) globs `analysis_tools/*.py` only; catalog keys referenced from a subpackage would read as orphans. Matches the existing builder convention (`build_financial_report.py`).
2. **`emit.py` is added as a 7th pipeline module** (spec §4 table has 6). It holds the deterministic writers for the output CSV/JSON files so they are testable independently of report rendering. `build()` calls it.
3. **`date_basis` canonical vocabulary** is the spec §4.1 six values **plus** `reports posted` (U-01's basis). The register's free-text `set.date_basis` values map canonically in `rules.py`: "reports posted" → `reports posted`; "event-day proxy" → `event-day proxy`; "Telegram post time; slip prints 1404/06/14" → `Telegram post time`; "on or before (forward timestamp)" → `on or before`; "handwritten invoice, read 1404/10/03" → `printed`; "period by event association" → `by event association`; "month only" → `month only`. The fuller register phrasing stays in `decisions.json` (never parsed for meaning).
4. **Date-pair and period completion** (mechanical, logged): after decision patches, `apply()` backfills a missing `date_jalali` from `date_gregorian` (and vice versa, e.g. R-06 sets only `date_jalali` 1404/10/01 → `date_gregorian` 2025-12-22), and a missing `period_jalali` as `YYYY/MM` of the completed date — only when the sibling is empty and the value parses. Each completion logs an audit-log entry citing the same decision id with reason "derived".
5. **`amount_original` coherence sentinel**: a rule patch value `"@original"` on `amount_original` means "derive from `amount_toman` and `unit_original`" (×10 if rial, ×1 if toman). Used by R-02, R-03, R-07, P-03 where the register fixes the toman amount but not the original. `apply()` enforces unit coherence for every row with both fields: `abs(amount_original − amount_toman·(10 if unit_original=="rial" else 1)) ≤ 0.5`.
6. **"Every row gets reviewed descriptions"** (spec §4.3) means every row was *reviewed* (via dossiers); `mechanical.json` carries rewrites only where the dossier assessment was `vague`/`wrong`/`missing`, plus the five known fixes, the P-04 shared-use note, and descriptions for TX0034/TX0034-B. Rows assessed `good` keep their descriptions.
7. **`test_catalog_integrity` sequencing**: `audit.*` EN keys and their FA translations land in the same task (Task 12) — the translate run is a user gate inside that task (VPN on). Until then no `audit.*` keys exist in `en.json` and the suite stays green.

## Staging note (data already rescued)

The evidence dossiers and the decision register draft were rescued from the (now unavailable) session scratchpad into the git-ignored workspace **`.superpowers/sdd/2026-10-18-ledger-audit/inputs/`** (`dossier-brief.md`, `dossier-{A,B1,B2,C,D}.json/.md`, `decisions.json`). `analysis_tools/audit/data/decisions.json` is already copied into place (untracked). Task 1 commits it.

## Global Constraints

- **Read-only paths:** nothing under `anjoman_accounting_information/reports/2026-10-10/` or `reports/2026-10-14/` is ever written (gate G8: `git diff --quiet` on both paths in tests).
- **Locked figures (gate G5, exact):** audited cash receipts **112,552,000**; cash payments **99,393,195**; net **13,158,805**; pending **21,626,064** = rows **21,350,480** + PI-01 **275,584**; all-rows receipts **139,787,000**; all-rows payments **133,539,774**.
- **Tolerance:** totals compare within `TOL = 0.5` toman; amounts kept at 0.1-toman precision (TX0071 = 135,799.9 must survive untouched); display rounds half-up to whole toman except where a fractional value is itself shown.
- **Source counters** (load-time validation): 96 rows; status Supported 66 / Review 22 / Duplicate 4 / Invoice only 3 / Summary only 1; direction Payment 82 / Receipt 12 / Internal transfer 1 / Unknown 1; 13 distinct projects. Read with `encoding="utf-8-sig"`.
- **Status vocabulary (audited `status`):** `Supported · Internal transfer · Pending · Payable · Supporting detail · Duplicate · Memo` (spec §5).
- **Status mapping under B-01** (rows no decision patches; logged with source id `B-01`): Supported→Supported; Review→Pending (`pending_reason` "Review"); Invoice only→Pending (`pending_reason` "Invoice only"); Summary only→Memo; Duplicate→Duplicate; direction Internal transfer once Supported→status Internal transfer.
- **Privacy (G9):** no national ID, `09\d{9}` phone, 16-digit card, `IR\d{24}` IBAN, or known credential string in any committed input or output; card last-4 only. The invoice-61150 buyer details and the message11142 credential content are excluded from every file (the credential itself must never be written anywhere — reference it only as "credential shared in message11142 (excluded)"). Student phone numbers from course reports are excluded.
- **API discipline:** only `translate.py` calls the Claude API; key passed only as `ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)"` (never printed, logged, or committed); VPN required; builders never call the API. `ensure_disk()` runs before any PDF work.
- **Determinism (G7):** no timestamps, no randomness, stable sort orders; two consecutive renders per language are byte-identical and outputs on disk equal a fresh render. Output CSVs are written `utf-8-sig`, JSON/MD `utf-8` (`ensure_ascii=False`).
- **Tests:** `python -m pytest analysis_tools/tests/ -q` from the repo root; the full suite must be green after every task. Windows/Git Bash: run python from the repo root with repo-relative paths (heredocs cannot open `/c/...` paths); prefix each Bash chain with `cd "/c/Users/Surface Laptop 3/Downloads/Telegram Desktop/anjoman_acc"`.
- **Commits:** conventional-commit style; end every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Implementers never dispatch subagents and never call the Claude API.

## File structure

| File | Responsibility |
|---|---|
| `analysis_tools/audit/__init__.py` | empty package marker |
| `analysis_tools/audit/data/decisions.json` | decision register, 38 ids (Task 1, already staged) |
| `analysis_tools/audit/data/mechanical.json` | money-neutral fixes (Task 2) |
| `analysis_tools/audit/data/evidence_index.json` | per-TX evidence + `balance_chain` block (Task 3) |
| `analysis_tools/audit/data/accounts.json` | per `cash_account` holder/type as evidenced (Task 4) |
| `analysis_tools/audit/load.py` | readers + schema validators (Task 5) |
| `analysis_tools/audit/rules.py` | RULES / NEW_ROWS / PENDING_ITEMS / OPEN_ITEMS (Task 6) |
| `analysis_tools/audit/apply.py` | audited rows + audit log + refusals (Task 7) |
| `analysis_tools/audit/balance.py` | project sheets, custody, summary, open items (Task 8) |
| `analysis_tools/audit/bridge.py` | the two bridges + decomposition (Task 9) |
| `analysis_tools/audit/emit.py` | deterministic output-file writers (Task 10) |
| `analysis_tools/build_audit_report.py` | render/build EN+FA, gates, CLI (Task 12) |
| `analysis_tools/i18n/en.json`, `glossary.json`, `fa.json`, `hashes.json` | catalog additions (Tasks 11, 12) |
| `analysis_tools/tests/test_audit_*.py` | one test file per pipeline task |
| `anjoman_accounting_information/reports/2026-10-18/` | the seven output files (spec §7) |

Interfaces chain strictly: Task 5's loader signatures → 6's tables → 7's `apply()` → 8/9's pure functions → 10's writers → 12's `render/build`.

---

### Task 1: Commit the decision register

**Files:**
- Create: `analysis_tools/audit/__init__.py` (empty)
- Already staged, verify + commit: `analysis_tools/audit/data/decisions.json`
- Test: `analysis_tools/tests/test_audit_decisions.py`

**Interfaces:**
- Consumes: the staged `decisions.json` (38 entries).
- Produces: the register at its committed path; every later task loads it via `load.load_register()` (Task 5).

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_decisions.py
import json
from analysis_tools.common import ROOT

DEC = ROOT / "analysis_tools/audit/data/decisions.json"
EXPECTED_IDS = (
    ["S-01", "B-01", "A-01"]
    + [f"D-{n:02d}" for n in range(1, 7)]
    + [f"R-{n:02d}" for n in range(1, 17)]
    + [f"U-{n:02d}" for n in range(1, 9)]
    + [f"P-{n:02d}" for n in range(1, 6)]
)

def test_register_complete_and_shaped():
    reg = json.loads(DEC.read_text(encoding="utf-8"))
    assert [e["id"] for e in reg] == EXPECTED_IDS
    for e in reg:
        assert e["kind"] in {"scope", "basis", "process", "duplicate", "review",
                             "date", "reassignment"}
        assert e["question"] and e["choice"] and e["rationale"]
        assert e["date"] == "2026-10-18"
        assert isinstance(e["evidence"], list) and e["evidence"]

def test_register_no_pii():
    from analysis_tools.audit.pii import scan  # added in Task 5; see note
    assert scan(DEC.read_text(encoding="utf-8")) == []
```

Note: write the test file now **without** `test_register_no_pii` (that helper exists only from Task 5 on); add it back in Task 5. Keep the file otherwise exactly as shown.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/c/Users/Surface Laptop 3/Downloads/Telegram Desktop/anjoman_acc" && python -m pytest analysis_tools/tests/test_audit_decisions.py -q`
Expected: FAIL — `decisions.json` exists (staged), so if it passes immediately, verify it is the staged file (`git status --porcelain analysis_tools/audit/data/` shows `?? analysis_tools/audit/`).

- [ ] **Step 3: Create the package marker and commit the register**

```bash
cd "/c/Users/Surface Laptop 3/Downloads/Telegram Desktop/anjoman_acc"
touch analysis_tools/audit/__init__.py
git add analysis_tools/audit/__init__.py analysis_tools/audit/data/decisions.json analysis_tools/tests/test_audit_decisions.py
git commit -m "feat(audit): commit decision register (38 decisions, 2026-10-18)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Run the test suite**

Run: `python -m pytest analysis_tools/tests/ -q` — Expected: PASS (all, including the new file).

---

### Task 2: `mechanical.json` — money-neutral fixes

**Files:**
- Create: `analysis_tools/audit/data/mechanical.json`
- Test: `analysis_tools/tests/test_audit_mechanical.py`

**Interfaces:**
- Consumes: dossiers at `.superpowers/sdd/2026-10-18-ledger-audit/inputs/dossier-{A,B1,B2,C,D}.json` (read-only), the spec §4.3 allowed-field list.
- Produces: a JSON array consumed by `load.load_mechanical()` (Task 5) and applied by `apply()` (Task 7). Entry schema: `{"id": "M-001", "tx": "TX0083", "field": "description_en", "new": "...", "reason": "...", "evidence": ["summerschool_channel message29"]}`. Allowed `field` values exactly: `description_en`, `description_fa`, `tracking_id`, `message_ids`, `notes`, `evidence_basis`.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_mechanical.py
import json
from analysis_tools.common import ROOT

MECH = ROOT / "analysis_tools/audit/data/mechanical.json"
ALLOWED = {"description_en", "description_fa", "tracking_id", "message_ids",
           "notes", "evidence_basis"}

def test_mechanical_schema_and_fields():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    assert len(m) >= 20
    ids = [e["id"] for e in m]
    assert ids == [f"M-{n:03d}" for n in range(1, len(m) + 1)]
    for e in m:
        assert e["field"] in ALLOWED, e
        assert e["tx"] and e["new"] and e["reason"] and e["evidence"]

def test_known_fixes_present():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    by_tx = {}
    for e in m:
        by_tx.setdefault(e["tx"], []).append(e)
    assert any(e["field"] == "tracking_id" and e["new"] == "001873"
               for e in by_tx["TX0075"]), "TX0075 tracking 187300 -> 001873"
    assert any("photo_34" in json.dumps(e) for e in by_tx.get("TX0035", [])), \
        "photo_34 evidence moves to TX0035"
    for tx, course in (("TX0083", "OOP"), ("TX0084", "Manim"), ("TX0087", "Python")):
        assert any(course in e["new"] for e in by_tx[tx]
                   if e["field"] == "description_en"), tx
    assert any("29350" in e["new"] for e in by_tx["TX0038"])
    assert any(e["field"] == "notes" for e in by_tx["TX0002"])
    assert any("shared" in e["new"] for e in by_tx["TX0020"]
               if e["field"] == "description_en"), "P-04 shared-use note"

def test_description_pairs():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    en = {e["tx"] for e in m if e["field"] == "description_en"}
    fa = {e["tx"] for e in m if e["field"] == "description_fa"}
    assert en == fa, "every description rewrite exists in both languages"

def test_no_amount_status_direction_changes():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    assert not ({"amount_toman", "amount_original", "unit_original", "status",
                 "direction", "date_gregorian", "date_jalali", "period_jalali",
                 "project", "category", "duplicate_of", "cash_account"}
                & {e["field"] for e in m})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest analysis_tools/tests/test_audit_mechanical.py -q` — Expected: FAIL (file missing).

- [ ] **Step 3: Distill the entries**

Read the dossier JSON files and produce entries, writing the file **incrementally** (rewrite the whole file after each batch of ~10 entries, so a stall loses nothing):

1. One `description_en` + one `description_fa` pair for every row whose dossier `description_assessment` is `vague`, `wrong`, or `missing` (~39 rows), using the dossier's `proposed_description_en`/`_fa` verbatim (trim only obvious duplication). The text states what was bought/received, from/to whom, for which event, and cites the evidence ref in parentheses; where the dossier says "evidence thin", the description says so.
2. The five known fixes with these exact values: TX0075 `tracking_id` → `001873` (reason: receipt prints 001873, ledger had 187300); a `message_ids` entry on TX0035 adding `photo_34` (reason: photo_34 is TX0035's receipt, listed under TX0033 — check the dossier for the exact id string TX0033 currently carries and add the matching removal entry on TX0033 if its `message_ids` string contains it); TX0083/84/87 `description_en`/`_fa` naming the courses (Zahra Saleh = OOP, Reza Farhadi = Manim, Ilia Asgharian = intro Python — use the dossier-proposed wording); TX0038 `notes` (or description, if the dossier proposes it there) carrying invoice number 29350; TX0002 `notes` correction per its dossier `discrepancies`.
3. TX0020 `description_en`/`_fa` appending the shared-use note (decision P-04; reason string must mention `P-04`).
4. Descriptions for TX0034 (split, 1,000,000) and TX0034-B (500,000, Association operations / Equipment) consistent with decision P-03 — the TX0034 entry replaces the old combined description; reason mentions `P-03`.

Evidence arrays use exact refs (`accounting_group#message115`, `photos/photo_3@24-07-2025_10-11-12.jpg`, `recipts/photo_1_....jpg`, `invoice-61150.pdf p1`). No national IDs, phones, full cards, IBANs, or credentials anywhere (the message11142 credential is referenced only as "credential shared in message11142 (excluded)").

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest analysis_tools/tests/test_audit_mechanical.py -q` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/data/mechanical.json analysis_tools/tests/test_audit_mechanical.py
git commit -m "feat(audit): mechanical fixes register (descriptions, tracking, evidence refs)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Then run the full suite: `python -m pytest analysis_tools/tests/ -q` — PASS.

---

### Task 3: `evidence_index.json` — per-TX evidence and balance-chain block

**Files:**
- Create: `analysis_tools/audit/data/evidence_index.json`
- Test: `analysis_tools/tests/test_audit_evidence.py`

**Interfaces:**
- Consumes: the dossiers (read-only).
- Produces: `{"rows": {tx: [{"ref", "timestamp", "shows"}...]}, "balance_chain": {...}}` consumed by Task 10 (transaction tables print the first ref per row) and Task 12 §6 (balance-chain section prints the block verbatim).

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_evidence.py
import json
from analysis_tools.common import ROOT

EV = ROOT / "analysis_tools/audit/data/evidence_index.json"

def test_every_source_row_has_evidence():
    import csv
    src = ROOT / "anjoman_accounting_information/reports/2026-10-10/Transactions.csv"
    with open(src, encoding="utf-8-sig") as f:
        ids = [r["id"] for r in csv.DictReader(f)]
    ev = json.loads(EV.read_text(encoding="utf-8"))["rows"]
    missing = [i for i in ids if not ev.get(i)]
    assert missing == []
    for tx, lst in ev.items():
        for e in lst:
            assert e["ref"] and e["shows"]

def test_balance_chain_block_exact():
    bc = json.loads(EV.read_text(encoding="utf-8"))["balance_chain"]
    assert [g["id"] for g in bc["gaps"]] == ["BC-1", "BC-2", "BC-3", "BC-4"]
    assert bc["gaps"][0]["approx_toman"] == 3163000
    assert bc["open_item"] == "OI-07"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest analysis_tools/tests/test_audit_evidence.py -q` — Expected: FAIL (file missing).

- [ ] **Step 3: Distill the index**

Write incrementally (rewrite after each dossier). `rows`: for each of the 96 source rows, 1–4 entries distilled from its dossier `evidence` array — `ref` (exact id: `accounting_group#message115` family; `message123` and `message-123` are different families, never normalize), `timestamp` (ISO or null), `shows` (one English sentence: what the evidence establishes — amounts/unit/date/counterparty/tracking). Rows with no external evidence (the R-14/15/16 originals) get one entry `{"ref": "original ledger", "timestamp": null, "shows": "amount and counterparty as recorded in the 2026-10-10 reconciliation; no external document located"}`.

`balance_chain` (S-01 disclosure block — these figures are locked by spec §6.6, copy exactly):

```json
"balance_chain": {
  "basis": "Evidenced Bank Shahr balance snapshots vs recorded ledger flows; figures approximate, in toman.",
  "gaps": [
    {"id": "BC-1", "window": "1405/05/21-1405/05/22", "approx_toman": 3163000,
     "direction": "debits", "note": "unrecorded debits between TX0075 and TX0076 snapshots",
     "source": "<dossier-D ref for the snapshot messages>"},
    {"id": "BC-2", "window": "1404/12 - 1405/05", "approx_toman": 35200000,
     "direction": "credits", "note": "credits exceeding recorded inflows",
     "source": "<dossier-D ref>"},
    {"id": "BC-3", "window": "1404/09 - 1404/12", "approx_toman": 12800000,
     "direction": "debits", "note": "debits exceeding recorded outflows; upper bound 19,800,000",
     "source": "<dossier-D ref>"},
    {"id": "BC-4", "window": "-", "approx_toman": null,
     "direction": "inflow anomalies", "note": "TX0007 and TX0024 amounts exceed the surrounding balance movement",
     "source": "<dossier-D ref>"}
  ],
  "open_item": "OI-07"
}
```

Replace each `<dossier-D ref>` with the real evidence ref from `dossier-D.json`. PII rules apply (no card numbers, no IBANs — balance snapshots cite message refs, not pasted account data).

- [ ] **Step 4: Run test to verify it passes** — `python -m pytest analysis_tools/tests/test_audit_evidence.py -q` — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/data/evidence_index.json analysis_tools/tests/test_audit_evidence.py
git commit -m "feat(audit): evidence index (per-TX refs, balance-chain disclosure block)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 4: `accounts.json` — cash custody registry

**Files:**
- Create: `analysis_tools/audit/data/accounts.json`
- Test: `analysis_tools/tests/test_audit_accounts.py`

**Interfaces:**
- Produces: `{"accounts": {code: {"holder": str, "type": str, "evidence": str}}}` — `type` ∈ `personal | association | volunteer | event custodian | cash | not evidenced`. Consumed by `balance.custody()` (Task 8) and the §5 custody table.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_accounts.py
import csv, json
from analysis_tools.common import ROOT

ACC = ROOT / "analysis_tools/audit/data/accounts.json"
TYPES = {"personal", "association", "volunteer", "event custodian",
         "cash", "not evidenced"}

def _source_accounts():
    src = ROOT / "anjoman_accounting_information/reports/2026-10-10/Transactions.csv"
    with open(src, encoding="utf-8-sig") as f:
        return {r["cash_account"] for r in csv.DictReader(f) if r["cash_account"]}

def test_accounts_cover_source_codes():
    acc = json.loads(ACC.read_text(encoding="utf-8"))["accounts"]
    assert set(acc) == _source_accounts()
    for code, a in acc.items():
        assert a["type"] in TYPES, (code, a["type"])
        assert a["holder"] and a["evidence"]

def test_no_card_or_iban():
    text = ACC.read_text(encoding="utf-8")
    import re
    assert not re.search(r"\b\d{16}\b", text)
    assert not re.search(r"IR\d{24}", text)
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (file missing).

- [ ] **Step 3: Write the registry**

The 9 codes are exactly the distinct `cash_account` values: `SHAHR-8966`, `VOLUNTEER`, `BLU-CUSTODIAN`, `UNKNOWN`, `SHAHR-2167`, `AMIN-EVENT`, `CASH`, `SEPAH-2925`, `Unknown funding source`. For each, read the dossiers' evidence for that account (which receipts name the holder/card, which messages discuss it) and record `holder` and `type` **as evidenced only** — where no document identifies the holder, `holder` is `"not evidenced"` and `type` is `"not evidenced"`. No guessing; each entry's `evidence` is an exact ref string.

- [ ] **Step 4: Run test to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/data/accounts.json analysis_tools/tests/test_audit_accounts.py
git commit -m "feat(audit): cash custody registry as evidenced

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 5: `load.py` + PII scanner

**Files:**
- Create: `analysis_tools/audit/pii.py`, `analysis_tools/audit/load.py`
- Test: `analysis_tools/tests/test_audit_load.py`

**Interfaces:**
- Produces (everything later imports these exact names):
  - `pii.scan(text) -> list[str]` — PII pattern hits (empty = clean).
  - `load.load_source() -> list[dict]` — 96 rows, utf-8-sig.
  - `load.load_register() -> list[dict]`; `load.load_mechanical() -> list[dict]`; `load.load_evidence() -> dict`; `load.load_accounts() -> dict`.
  - `load.SOURCE_COLS` — the 22 source column names, in file order.
  - `load.AUDIT_COLS` — `["source_status", "pending_reason", "parent", "date_basis", "evidence_label", "open_item", "changed_fields"]` (appended after the source columns).
  - `class AuditError(RuntimeError)`.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_load.py
import pytest
from analysis_tools.audit import load, pii

def test_pii_patterns():
    assert pii.scan("call 09123456789 ok") != []
    assert pii.scan("card 6037991111111111 end") != []
    assert pii.scan("IR062960000000100000000001 hit") != []
    assert pii.scan("id 0012345678 (10 digits)") != []
    assert pii.scan("clean 112,552,000 toman TX0036 2025-07-24") == []

def test_source_rows_and_counters():
    rows = load.load_source()
    assert len(rows) == 96
    from collections import Counter
    assert Counter(r["status"] for r in rows) == {
        "Supported": 66, "Review": 22, "Duplicate": 4,
        "Invoice only": 3, "Summary only": 1}
    assert Counter(r["direction"] for r in rows) == {
        "Payment": 82, "Receipt": 12, "Internal transfer": 1, "Unknown": 1}

def test_source_cols_exact():
    assert load.SOURCE_COLS[:5] == ["id", "date_gregorian", "date_jalali",
                                    "period_jalali", "direction"]
    assert load.SOURCE_COLS[-1] == "sources"
    assert len(load.SOURCE_COLS) == 22
    assert load.AUDIT_COLS == ["source_status", "pending_reason", "parent",
                               "date_basis", "evidence_label", "open_item",
                               "changed_fields"]

def test_input_validators_raise_on_bad_shape():
    with pytest.raises(load.AuditError):
        load._validate_register([])
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (`audit.load` not importable).

- [ ] **Step 3: Implement `pii.py` and `load.py`**

```python
# analysis_tools/audit/pii.py
"""PII pattern scan (gate G9). Empty list = clean."""
import re

_PATTERNS = [
    (re.compile(r"\b09\d{9}\b"), "phone"),
    (re.compile(r"\b\d{16}\b"), "card"),
    (re.compile(r"\bIR\d{24}\b"), "iban"),
    (re.compile(r"\b\d{10}\b"), "possible national id"),
]

def scan(text):
    return [f"{kind}: {m.group(0)}" for pat, kind in _PATTERNS
            for m in pat.finditer(text)]
```

```python
# analysis_tools/audit/load.py
"""Read the source ledger and the four audit data files; validate shapes."""
import csv
import json
from pathlib import Path

from ..common import ROOT

DATA = ROOT / "analysis_tools/audit/data"
SOURCE_CSV = (ROOT / "anjoman_accounting_information"
              / "reports/2026-10-10/Transactions.csv")

SOURCE_COLS = ["id", "date_gregorian", "date_jalali", "period_jalali",
               "direction", "amount_original", "unit_original", "amount_toman",
               "counterparty", "description_en", "description_fa", "category",
               "project", "status", "evidence_basis", "cash_account",
               "message_ids", "tracking_id", "duplicate_of", "review_reason",
               "notes", "sources"]
AUDIT_COLS = ["source_status", "pending_reason", "parent", "date_basis",
              "evidence_label", "open_item", "changed_fields"]

NEW_STATUSES = {"Pending", "Payable", "Supporting detail", "Internal transfer",
                "Memo"}
DATE_BASES = {"printed", "event-day proxy", "on or before", "month only",
              "Telegram post time", "by event association", "reports posted"}
ACCOUNT_TYPES = {"personal", "association", "volunteer", "event custodian",
                 "cash", "not evidenced"}


class AuditError(RuntimeError):
    pass


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_source():
    with open(SOURCE_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 96:
        raise AuditError(f"expected 96 source rows, got {len(rows)}")
    if any(set(r) != set(SOURCE_COLS) for r in rows):
        raise AuditError("source columns drifted from SOURCE_COLS")
    return rows


def load_register():
    reg = _read_json(DATA / "decisions.json")
    _validate_register(reg)
    return reg


def _validate_register(reg):
    if len(reg) != 38 or any(e["id"] in {e2["id"] for e2 in reg[:i]}
                             for i, e in enumerate(reg)):
        raise AuditError("register must hold 38 unique ids")


def load_mechanical():
    m = _read_json(DATA / "mechanical.json")
    allowed = {"description_en", "description_fa", "tracking_id", "message_ids",
               "notes", "evidence_basis"}
    for e in m:
        if e["field"] not in allowed:
            raise AuditError(f"{e['id']}: field {e['field']!r} not mechanical")
    return m


def load_evidence():
    ev = _read_json(DATA / "evidence_index.json")
    if "rows" not in ev or "balance_chain" not in ev:
        raise AuditError("evidence_index.json needs 'rows' and 'balance_chain'")
    return ev


def load_accounts():
    acc = _read_json(DATA / "accounts.json")["accounts"]
    bad = {c: a["type"] for c, a in acc.items() if a["type"] not in ACCOUNT_TYPES}
    if bad:
        raise AuditError(f"bad account types: {bad}")
    return acc
```

Add to `test_audit_decisions.py` the PII test promised in Task 1 (now that `pii.scan` exists).

- [ ] **Step 4: Run test to verify it passes** — `python -m pytest analysis_tools/tests/test_audit_load.py analysis_tools/tests/test_audit_decisions.py -q` — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/pii.py analysis_tools/audit/load.py analysis_tools/tests/test_audit_load.py analysis_tools/tests/test_audit_decisions.py
git commit -m "feat(audit): loaders, schema validation, PII scanner

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 6: `rules.py` — the decision-id → patch table

**Files:**
- Create: `analysis_tools/audit/rules.py`
- Test: `analysis_tools/tests/test_audit_rules.py`

**Interfaces:**
- Consumes: `load.load_register()`.
- Produces (Task 7 imports these exact names):
  - `Patch = tuple[str, str, object]` — `(tx_id, field, new_value)`.
  - `RULES: dict[str, list[Patch]]` — one entry per register id (38).
  - `NO_FIELD_CHANGE: set[str]` — ids with explicitly no patch: `{"S-01", "B-01", "A-01", "D-01", "R-05", "R-08", "R-10", "P-04"}`.
  - `NEW_ROWS: dict[str, dict]` — `"TX0034-B"` (Task 7's split).
  - `PENDING_ITEMS: list[dict]` — `[{"id": "PI-01", "project": "Yalda 1404", "amount_toman": 275584, "counterparty": "سیدبردیا احمدی‌مروست", "note": "unreimbursed remainder of TX0050 (decision R-08)"}]`.
  - `OPEN_ITEMS: list[dict]` — the 18 entries below.
  - `validate(register)` — raises `AuditError` on any coverage/fidelity violation (the four spec §4.2 refusal conditions are enforced here and re-checked in `apply`).

**The complete RULES table** (write exactly this; field names are `load.SOURCE_COLS` ∪ `load.AUDIT_COLS` names):

```python
RULES = {
    "S-01": [], "B-01": [], "A-01": [],
    "D-01": [],
    "D-02": [("TX0010", "status", "Duplicate"),
             ("TX0010", "duplicate_of", "TX0009")],
    "D-03": [(f"TX00{n}", "status", "Supporting detail") for n in (52, 53, 54, 55)]
          + [(f"TX00{n}", "parent", "TX0050") for n in (52, 53, 54, 55)],
    "D-04": [(f"TX00{n}", "status", "Supporting detail")
             for n in range(64, 75)]
          + [(f"TX00{n}", "parent", "TX0062;TX0063") for n in range(64, 75)],
    "D-05": [("TX0069", "duplicate_of", "")],
    "D-06": [("TX0042", "status", "Supported")],
    "R-01": [("TX0036", "direction", "Payment"),
             ("TX0036", "status", "Supported")],
    "R-02": [("TX0031", "amount_toman", 230000.0),
             ("TX0031", "amount_original", "@original")],
    "R-03": [("TX0018", "unit_original", "rial"),
             ("TX0018", "amount_toman", 1765000.0),
             ("TX0018", "amount_original", 17650000.0)],
    "R-04": [("TX0001", "open_item", "OI-01")],
    "R-05": [],
    "R-06": [("TX0049", "amount_toman", 10003780.0),
             ("TX0049", "amount_original", 100037800.0),
             ("TX0049", "unit_original", "rial"),
             ("TX0049", "date_jalali", "1404/10/01")],
    "R-07": [("TX0058", "amount_toman", 275000.0),
             ("TX0058", "amount_original", "@original"),
             ("TX0056", "status", "Payable"),
             ("TX0058", "status", "Payable")],
    "R-08": [],
    "R-09": [("TX0062", "open_item", "OI-02"),
             ("TX0063", "open_item", "OI-02")],
    "R-10": [],
    "R-11": [("TX0082", "project", "Summer School 1405")],
    "R-12": [("TX0093", "open_item", "OI-03"),
             ("TX0094", "open_item", "OI-03")],
    "R-13": [("TX0096", "period_jalali", "1405/04"),
             ("TX0096", "notes", "@append:on or before 1405/04/08")],
    "R-14": [("TX0013", "evidence_label", "original ledger only"),
             ("TX0013", "open_item", "OI-04")],
    "R-15": [("TX0045", "evidence_label", "original ledger only"),
             ("TX0045", "open_item", "OI-05")],
    "R-16": [("TX0095", "evidence_label", "original ledger only"),
             ("TX0095", "open_item", "OI-06")],
    "U-01": [("TX0001", "date_gregorian", "2025-07-24"),
             ("TX0001", "date_basis", "reports posted")],
    "U-02": [(f"TX00{n}", "date_gregorian", "2025-09-06") for n in (14, 16, 17)]
          + [(f"TX00{n}", "date_basis", "event-day proxy") for n in (14, 16, 17)],
    "U-03": [("TX0015", "date_gregorian", "2025-09-04"),
             ("TX0015", "date_basis", "Telegram post time")],
    "U-04": [("TX0044", "date_gregorian", "2025-11-19"),
             ("TX0044", "date_basis", "on or before"),
             ("TX0044", "period_jalali", "1404/08")],
    "U-05": [("TX0036", "date_gregorian", "2025-10-29"),
             ("TX0036", "date_basis", "event-day proxy")],
    "U-06": [("TX0074", "date_gregorian", "2025-12-24"),
             ("TX0074", "date_basis", "printed")],
    "U-07": [("TX0060", "period_jalali", "1404/10"),
             ("TX0060", "date_basis", "by event association")],
    "U-08": [(f"TX00{n}", "date_basis", "month only")
             for n in (10, 13, 25, 45, 47, 48, 58, 93, 95)],
    "P-01": [("TX0080", "project", "Summer School 1405"),
             ("TX0080", "category", "Advertising")],
    "P-02": [("TX0089", "project", "Intro Event 1405"),
             ("TX0089", "category", "Hospitality")],
    "P-03": [("TX0034", "amount_toman", 1000000.0),
             ("TX0034", "amount_original", "@original")],
    "P-04": [],
    "P-05": [(tx, "open_item", f"OI-{n:02d}") for n, tx in enumerate(
        ["TX0043", "TX0061", "TX0075", "TX0076", "TX0077", "TX0078",
         "TX0079", "TX0081", "TX0090", "TX0091", "TX0092"], start=8)],
}

NEW_ROWS = {"TX0034-B": {
    "copy_from": "TX0034",
    "set": {"amount_toman": 500000.0, "amount_original": "@original",
            "project": "Association operations", "category": "Equipment"}}}

PENDING_ITEMS = [{"id": "PI-01", "project": "Yalda 1404", "amount_toman": 275584,
                  "counterparty": "سیدبردیا احمدی‌مروست",
                  "note": "unreimbursed remainder of TX0050 (decision R-08)"}]
```

**OPEN_ITEMS** (18 entries; `txs` lists the rows carrying the id; `amount_toman` may be `None`; `project` is resolved from the row at apply time, so entries carry no project):

```python
OPEN_ITEMS = [
    {"id": "OI-01", "txs": ["TX0001"], "amount_toman": 1000.0,
     "question": "The posted report shows 33,643,000 for this receipt; the ledger has 33,642,000 (1,000 difference).",
     "settles": "the original report/workbook page for TX0001"},
    {"id": "OI-02", "txs": ["TX0062", "TX0063"], "amount_toman": 195860.1,
     "question": "195,860.1 toman of the volunteer-reported purchases (TX0064-74) is not covered by the TX0062/63 reimbursement of 4,050,000.",
     "settles": "the missing receipt(s) or the volunteer's confirmation of the total"},
    {"id": "OI-03", "txs": ["TX0093", "TX0094"], "amount_toman": 4235000.0,
     "question": "Intro Event 1405 evidence implies 4,235,000 beyond the recorded net of 23,000,000; the gap is unexplained.",
     "settles": "bank statement or receipts for the Intro Event 1405 period"},
    {"id": "OI-04", "txs": ["TX0013"], "amount_toman": None,
     "question": "No evidence outside the original ledger; the row is kept Supported on the original ledger's authority.",
     "settles": "a source receipt or message for TX0013"},
    {"id": "OI-05", "txs": ["TX0045"], "amount_toman": None,
     "question": "No evidence outside the original ledger; the row is kept Supported on the original ledger's authority.",
     "settles": "a source receipt or message for TX0045"},
    {"id": "OI-06", "txs": ["TX0095"], "amount_toman": None,
     "question": "No evidence outside the original ledger; the row is kept Supported on the original ledger's authority.",
     "settles": "a source receipt or message for TX0095"},
    {"id": "OI-07", "txs": [], "amount_toman": None,
     "question": "Implied bank movements are not in the ledger: ~3,163,000 debits around 1405/05/21-22; ~35.2M credits between 1404/12 and 1405/05; ~12.8-19.8M debits between 1404/09 and 1404/12; inflow anomalies at TX0007 and TX0024.",
     "settles": "the Bank Shahr statement covering 1404/05-1405/06"},
] + [
    {"id": f"OI-{n:02d}", "txs": [tx], "amount_toman": None,
     "question": "Purpose unknown - the row could not be assigned to an event/program from evidence.",
     "settles": "owner identifies the purpose; then reassign project and category"}
    for n, tx in enumerate(["TX0043", "TX0061", "TX0075", "TX0076", "TX0077",
                            "TX0078", "TX0079", "TX0081", "TX0090", "TX0091",
                            "TX0092"], start=8)
]
```

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_rules.py
import pytest
from analysis_tools.audit import load, rules

def test_every_register_id_covered():
    reg = load.load_register()
    for e in reg:
        rid = e["id"]
        assert rid in rules.RULES or rid in rules.NO_FIELD_CHANGE, rid

def test_every_rule_id_in_register():
    reg_ids = {e["id"] for e in load.load_register()}
    assert set(rules.RULES) == reg_ids
    assert rules.NO_FIELD_CHANGE <= reg_ids

def test_no_double_patches():
    seen = {}
    for rid, patches in rules.RULES.items():
        for tx, field, _ in patches:
            key = (tx, field)
            assert key not in seen, f"{key} patched by {seen.get(key)} and {rid}"
            seen[key] = rid

def test_patch_fields_exist():
    valid = set(load.SOURCE_COLS) | set(load.AUDIT_COLS)
    for rid, patches in rules.RULES.items():
        for tx, field, _ in patches:
            assert field in valid, (rid, field)

def test_register_set_fidelity():
    """Where the register declares explicit set-keys, RULES must carry the same
    values (register text is never parsed; this checks the declared numbers)."""
    reg = {e["id"]: e for e in load.load_register()}
    assert reg["R-06"]["set"] == {"amount_toman": 10003780,
                                  "unit_original": "rial",
                                  "amount_original": 100037800,
                                  "date_jalali": "1404/10/01"}
    assert reg["R-07"]["set"] == {"TX0058.amount_toman": 275000}
    assert reg["P-03"]["set"]["split"][1]["id"] == "TX0034-B"
    assert reg["R-08"]["pending_item"]["id"] == "PI-01"

def test_pending_item_matches_register():
    reg = {e["id"]: e for e in load.load_register()}
    pi = reg["R-08"]["pending_item"]
    assert rules.PENDING_ITEMS[0]["id"] == pi["id"]
    assert rules.PENDING_ITEMS[0]["amount_toman"] == pi["amount_toman"]
    assert rules.PENDING_ITEMS[0]["project"] == pi["project"]

def test_open_items_shape():
    ids = [o["id"] for o in rules.OPEN_ITEMS]
    assert ids == [f"OI-{n:02d}" for n in range(1, 19)]
    carried = {tx for o in rules.OPEN_ITEMS for tx in o["txs"]}
    patched = {tx for patches in rules.RULES.values()
               for tx, f, v in patches if f == "open_item"}
    assert carried == patched

def test_validate_raises_on_unknown_id():
    with pytest.raises(rules.AuditError):
        rules.validate([{"id": "X-99"}, *[{"id": f"D-{n:02d}"} for n in range(1, 6)],
                        *[{"id": f"R-{n:02d}"} for n in range(1, 17)],
                        *[{"id": f"U-{n:02d}"} for n in range(1, 9)],
                        *[{"id": f"P-{n:02d}"} for n in range(1, 6)]])
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (module missing).

- [ ] **Step 3: Implement `rules.py`** with the tables above plus:

```python
def validate(register):
    """Spec §4.2 refusals, static side: unknown rule id, uncovered register id,
    unknown patch field, unknown open-item refs."""
    from . import load
    reg_ids = {e["id"] for e in register}
    unknown = set(RULES) - reg_ids
    if unknown:
        raise AuditError(f"rules without register ids: {sorted(unknown)}")
    uncovered = reg_ids - set(RULES) - NO_FIELD_CHANGE
    if uncovered:
        raise AuditError(f"register ids without rules: {sorted(uncovered)}")
    valid = set(load.SOURCE_COLS) | set(load.AUDIT_COLS)
    for rid, patches in RULES.items():
        for tx, field, value in patches:
            if field not in valid:
                raise AuditError(f"{rid}: unknown field {field!r}")
    oi_ids = {o["id"] for o in OPEN_ITEMS}
    for rid, patches in RULES.items():
        for tx, field, value in patches:
            if field == "open_item" and value not in oi_ids:
                raise AuditError(f"{rid}: unknown open item {value!r}")
```

Sentinels `"@original"` and `"@append:..."` are documented at the top of the module; `apply()` interprets them.

- [ ] **Step 4: Run test to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/rules.py analysis_tools/tests/test_audit_rules.py
git commit -m "feat(audit): decision patch table, new rows, pending and open items

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 7: `apply.py` — audited rows + audit log

**Files:**
- Create: `analysis_tools/audit/apply.py`
- Test: `analysis_tools/tests/test_audit_apply.py`

**Interfaces:**
- Consumes: `load.load_source/load_register/load_mechanical`, `rules.RULES/NEW_ROWS/PENDING_ITEMS/NO_FIELD_CHANGE`, `pii.scan`.
- Produces:
  - `apply() -> tuple[list[dict], list[dict]]` — `(audited_rows, audit_log)`. 97 audited rows (96 + TX0034-B, inserted immediately after TX0034); row = source fields with audited `status` + the 7 `load.AUDIT_COLS` columns.
  - `audit_log` entries: `{"tx", "field", "old", "new", "source_id", "reason", "evidence"}`; created rows/items log `field="created"`.
  - `diff_completeness(rows, log) -> list[str]` — G3 core: every field difference vs the source row must appear in the log exactly once, and vice versa (created rows exempt except their `created` entry).
  - `TOL = 0.5`.
- Apply order (deterministic): ① register patches (RULES order = register order; sentinels resolved) ② NEW_ROWS creation ③ B-01 status mapping ④ mechanical fixes (M-id order) ⑤ date-pair/period completion (ruling 4) ⑥ coherence assertion.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_apply.py
import pytest
from analysis_tools.audit import apply, load, rules

@pytest.fixture(scope="module")
def applied():
    return apply.apply()

def test_row_count_and_order(applied):
    rows, _ = applied
    assert len(rows) == 97
    ids = [r["id"] for r in rows]
    assert ids.index("TX0034-B") == ids.index("TX0034") + 1

def test_spot_patches(applied):
    rows, log = applied
    by = {r["id"]: r for r in rows}
    assert by["TX0010"]["status"] == "Duplicate"
    assert by["TX0010"]["duplicate_of"] == "TX0009"
    assert by["TX0010"]["source_status"] == "Review"
    assert by["TX0036"]["direction"] == "Payment"
    assert by["TX0036"]["status"] == "Supported"
    assert by["TX0031"]["amount_toman"] == pytest.approx(230000.0)
    assert by["TX0049"]["amount_toman"] == pytest.approx(10003780.0)
    assert by["TX0049"]["date_jalali"] == "1404/10/01"
    assert by["TX0049"]["date_gregorian"] == "2025-12-22"     # ruling 4
    assert by["TX0049"]["status"] == "Pending"                # stays Review
    assert by["TX0049"]["pending_reason"] == "Review"
    assert by["TX0058"]["status"] == "Payable"
    assert by["TX0058"]["amount_toman"] == pytest.approx(275000.0)
    assert by["TX0056"]["status"] == "Payable"
    assert by["TX0074"]["parent"] == "TX0062;TX0063"
    assert by["TX0069"]["duplicate_of"] == ""
    assert by["TX0071"]["amount_toman"] == pytest.approx(135799.9)  # precision kept
    assert by["TX0034"]["amount_toman"] == pytest.approx(1000000.0)
    assert by["TX0034-B"]["amount_toman"] == pytest.approx(500000.0)
    assert by["TX0034-B"]["project"] == "Association operations"
    assert by["TX0082"]["project"] == "Summer School 1405"
    assert by["TX0082"]["status"] == "Pending"                # Invoice only
    assert by["TX0094"]["status"] == "Memo"                   # Summary only
    assert by["TX0018"]["status"] == "Internal transfer"
    assert by["TX0013"]["evidence_label"] == "original ledger only"
    assert by["TX0043"]["open_item"] == "OI-08"

def test_status_mapping_counts(applied):
    from collections import Counter
    rows, _ = applied
    c = Counter(r["status"] for r in rows)
    # Supported: source 66 + D-06 + R-01 (both Review->Supported) + TX0034-B = 69.
    assert c["Supported"] == 69
    assert c["Pending"] == 4      # TX0049, TX0060, TX0082, TX0096
    assert c["Payable"] == 2      # TX0056, TX0058
    assert c["Duplicate"] == 5    # 4 + TX0010
    assert c["Memo"] == 1         # TX0094
    assert c["Internal transfer"] == 1
    assert c["Supporting detail"] == 15  # TX0052-55 + TX0064-74

def test_b01_mapping_logged(applied):
    rows, log = applied
    unmapped = [e for e in log if e["source_id"] == "B-01"]
    assert unmapped, "status mapping under B-01 must be logged"

def test_log_cites_register_ids(applied):
    reg_ids = {e["id"] for e in load.load_register()}
    mids = {e["id"] for e in load.load_mechanical()}
    rows, log = applied
    bad = [e for e in log if e["source_id"] not in reg_ids | mids | {"B-01"}]
    assert bad == []

def test_diff_completeness_clean(applied):
    rows, log = applied
    assert apply.diff_completeness(rows, log) == []

def test_created_entries(applied):
    _, log = applied
    created = {e["tx"] for e in log if e["field"] == "created"}
    assert created == {"TX0034-B", "PI-01"}

def test_coherence_enforced():
    # a row with incoherent amount_original must raise
    src = load.load_source()
    row = dict(next(r for r in src if r["id"] == "TX0005"))
    row["amount_original"] = str(float(row["amount_toman"]) * 3)
    with pytest.raises(apply.AuditError):
        apply._check_coherence([row])
```

Before finalizing the `test_status_mapping_counts` numbers, the implementer **computes** the Supported count from the actual patch set (start 66; D-02 −1 to Duplicate; D-03 −4 and D-04 −11 to Supporting detail; D-06 +1 from Review; R-01 +1 from Review; TX0018 −1 to Internal transfer) and asserts the computed value — the number above (64) is the controller's arithmetic and must be verified, not trusted.

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (module missing).

- [ ] **Step 3: Implement `apply.py`**

Core structure (complete this; helper details are ordinary code):

```python
"""Apply decision rules + mechanical fixes -> audited rows and audit log."""
from ..common import ROOT  # noqa: F401
from . import load, rules
from .load import AuditError

TOL = 0.5
STATUS_MAP = {"Supported": "Supported", "Review": "Pending",
              "Invoice only": "Pending", "Summary only": "Memo",
              "Duplicate": "Duplicate"}
PENDING_REASON = {"Review": "Review", "Invoice only": "Invoice only"}

def apply():
    src_rows = load.load_source()
    register = load.load_register()
    rules.validate(register)
    mech = load.load_mechanical()
    reg_by_id = {e["id"]: e for e in register}
    rows = {r["id"]: dict(r) for r in src_rows}
    log = []
    # 1. register patches, register order
    for e in register:
        for tx, field, value in rules.RULES[e["id"]]:
            _patch(rows, log, tx, field, value, e["id"],
                   e["rationale"], e["evidence"])
    # 2. new rows (P-03 split)
    _create_new_rows(rows, log, reg_by_id["P-03"])
    # 3. B-01 status mapping
    for r in rows.values():
        _map_status(r, log)
    # 4. mechanical fixes
    for m in mech:
        _mechanical(rows, log, m)
    # 5. date-pair / period completion (ruling 4)
    _complete_dates(rows, log)
    # 6. coherence
    out = [rows[r["id"]] for r in src_rows] + [rows["TX0034-B"]]
    for r in out:
        _finish_row(r)          # source_status, changed_fields, defaults
    _check_coherence(out)
    return out, log
```

Semantics each helper must implement:
- `_patch`: sentinel `"@original"` (amount_original ← amount_toman × 10 if unit rial else ×1, using the row's current unit); `"@append:X"` (notes ← old + " | X" or X); both numeric fields stored as `float`; writing a field records a log entry (old value stringified) and refuses (`AuditError`) if `(tx, field)` was already patched by a different decision id.
- `_create_new_rows`: TX0034-B copies TX0034's current post-patch values, applies `NEW_ROWS["TX0034-B"]["set"]`, gets `id="TX0034-B"`, empty `duplicate_of`/`tracking_id`/`review_reason`, `source_status` = TX0034's source status, description via mechanical entries (step 4 applies to it), logs `created` citing P-03.
- `_map_status`: for rows whose status was **not** set by a decision patch this run: new status `STATUS_MAP[old]`, `pending_reason = PENDING_REASON.get(old, "")`; log each change with `source_id="B-01"`, reason "status mapping (B-01)". Decision-patched rows: `pending_reason` = "" unless final status is Pending with source Review/Invoice only (e.g. TX0049). Rows now Supported whose direction is Internal transfer get status Internal transfer (TX0018 path).
- `_mechanical`: M-entry applies to the row (created rows included); refuses if field not in the mechanical allowed set (G4); logs with `source_id=m["id"]`.
- `_complete_dates`: for each row, if exactly one of date_gregorian/date_jalali is non-empty and parses, fill the other (`jdatetime`); if period_jalali empty and a date exists, fill `YYYY/MM`; log each fill citing the row's deciding source id (the id that set the date, found from the log; fallback `"B-01"`), reason "derived".
- `_finish_row`: `source_status` = source row's status; `parent`/`evidence_label`/`open_item` default `""`; `changed_fields` = semicolon-joined source-column names whose audited value differs from the source row (status included; new columns excluded).
- `_check_coherence`: for every row with both amounts non-empty (coerce `str`→`float`): `abs(amount_original − amount_toman×(10 if unit_original=="rial" else 1)) ≤ TOL`, else `AuditError`; TX0049 must satisfy it (10,003,780 / 100,037,800 rial).

- [ ] **Step 4: Run test to verify it passes** — PASS (adjust only the computed Supported count if your arithmetic differs — never weaken a spot assertion to make it pass).

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/apply.py analysis_tools/tests/test_audit_apply.py
git commit -m "feat(audit): apply decisions and mechanical fixes to audited rows

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 8: `balance.py` — project sheets, custody, summary

**Files:**
- Create: `analysis_tools/audit/balance.py`
- Test: `analysis_tools/tests/test_audit_balance.py`

**Interfaces:**
- Consumes: `apply.apply()`, `load.load_accounts()`, `rules.PENDING_ITEMS`, `rules.OPEN_ITEMS`.
- Produces:
  - `project_sheets(rows, pending_items) -> dict[project, dict]` — sheet keys are **the 13 source projects** (seeded from `load_source()`, so a project emptied by decisions still appears) plus any project introduced by patches; values carry `receipts`, `payments`, `net`, `pending`, `pending_rows`, `pending_items`, `excluded` (list of `{id, kind, parent}`), `receipts_by_source` (counterparty → amount, Supported only), `payments_by_category` (category → amount, Supported only), `tx_rows` (ids in ledger order), `open_items` (oi ids), `is_empty_note` (`None`, or a note naming the project(s) that received its rows — derivable from the audit log's project patches).
  - `custody(rows, accounts) -> list[dict]` — per cash_account: `{code, holder, type, cash_in, cash_out, transfers}` (Supported rows only; transfers lists Internal-transfer row ids).
  - `summary(sheets) -> list[dict]` — one row per project + `TOTALS`; `check_summary(sheets, cash_receipts, cash_payments, pending)` raises `AssertionError` (G1).
  - Excluded rows (Supporting detail, Duplicate, Memo) and Internal transfer rows contribute to **no** cash or pending sums.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_balance.py
import pytest
from analysis_tools.audit import apply, balance, load, rules

@pytest.fixture(scope="module")
def world():
    rows, log = apply.apply()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS)
    return rows, sheets

def test_cash_sums_equal_locked(world):
    _, sheets = world
    r = sum(s["receipts"] for s in sheets.values())
    p = sum(s["payments"] for s in sheets.values())
    assert abs(r - 112552000.0) <= 0.5
    assert abs(p - 99393195.0) <= 0.5

def test_pending_total(world):
    _, sheets = world
    pend = sum(s["pending"] for s in sheets.values())
    assert abs(pend - 21626064.0) <= 0.5
    yalda = sheets["Yalda 1404"]
    assert any(p["id"] == "PI-01" for p in yalda["pending_items"])

def test_unknown_project_emptied(world):
    _, sheets = world
    u = sheets["Unknown (likely 1405 summer school)"]
    assert u["receipts"] == 0 and u["payments"] == 0 and u["pending"] == 0
    assert u["is_empty_note"] is not None

def test_excluded_under_parent(world):
    _, sheets = world
    y = sheets["Yalda 1404"]["excluded"]
    assert any(e["id"] == "TX0052" and e["parent"] == "TX0050" for e in y)

def test_summary_totals(world):
    _, sheets = world
    rows = balance.summary(sheets)
    tot = rows[-1]
    assert tot["project"] == "TOTALS"
    assert abs(tot["receipts"] - 112552000.0) <= 0.5
    balance.check_summary(sheets, 112552000.0, 99393195.0, 21626064.0)  # G1

def test_custody_shape(world):
    rows, _ = world
    acc = load.load_accounts()
    cust = balance.custody(rows, acc)
    codes = {c["code"] for c in cust}
    assert codes == set(acc)
    assert all("holder" in c and "type" in c for c in cust)
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL.

- [ ] **Step 3: Implement `balance.py`** per the interface contract. Sorting: sheets keyed by sorted project name; `summary` sorts the same way with TOTALS last; custody sorted by code; all sums over `float(amount_toman)`; rounding only at display (Task 12). `is_empty_note` set when a project has no Supported/Pending/Payable rows and at least one excluded row — note text names where the rows went (readable from the excluded rows' successors' projects via the audit log).

- [ ] **Step 4: Run test to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/balance.py analysis_tools/tests/test_audit_balance.py
git commit -m "feat(audit): per-project balance sheets, custody, consolidated summary

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 9: `bridge.py` — the two bridges

**Files:**
- Create: `analysis_tools/audit/bridge.py`
- Test: `analysis_tools/tests/test_audit_bridge.py`

**Interfaces:**
- Produces:
  - `SUPPORTED_START = {"receipts": 112552000.0, "payments": 99085195.0}`, `ALLROWS_START = {"receipts": 139787000.0, "payments": 123265994.0}` (test asserts `ALLROWS_START` equals `build_financial_report.ALL_TOTALS` values).
  - `supported_lines` / `allrows_lines`: fixed lists `{"id", "tx", "dr", "dp", "note"}` — supported: `R-01` (+300,000 payments), `R-02` (−5,000 payments), `D-06` (+13,000 payments); all-rows: `R-02` (−5,000), `R-06` (+10,003,780), `R-07` (+275,000), all payments-side.
  - `bridges(rows) -> dict` — computes audited endpoints from `rows` (cash = Supported; all-rows = every row, internal transfers excluded from both sides) and returns `{basis: {start, lines, end}}`.
  - `decompose(rows) -> dict` — audited all-rows totals split per side into `cash`, `internal_transfer`, `pending`, `excluded`.
  - `check(bridges_dict)` — G2: each basis' `start + Σ lines == end` within 0.5 and every line id exists in the register.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_bridge.py
import pytest
from analysis_tools.audit import apply, bridge
from analysis_tools import build_financial_report as fin

def test_allrows_start_matches_2026_10_14_builder():
    assert (bridge.ALLROWS_START["receipts"], bridge.ALLROWS_START["payments"]) \
        == (fin.ALL_TOTALS["Receipts"], fin.ALL_TOTALS["Payments"])

@pytest.fixture(scope="module")
def br():
    rows, _ = apply.apply()
    return bridge.bridges(rows), bridge.decompose(rows)

def test_supported_bridge_exact(br):
    b, _ = br
    s = b["supported"]
    assert abs(s["end"]["receipts"] - 112552000.0) <= 0.5
    assert abs(s["end"]["payments"] - 99393195.0) <= 0.5
    assert [l["id"] for l in s["lines"]] == ["R-01", "R-02", "D-06"]
    bridge.check(b)

def test_allrows_bridge_exact(br):
    b, _ = br
    a = b["allrows"]
    assert abs(a["end"]["receipts"] - 139787000.0) <= 0.5
    assert abs(a["end"]["payments"] - 133539774.0) <= 0.5
    assert [l["id"] for l in a["lines"]] == ["R-02", "R-06", "R-07"]
    bridge.check(b)

def test_decomposition_sums(br):
    _, d = br
    for side in ("receipts", "payments"):
        total = sum(d[side].values())
        want = 139787000.0 if side == "receipts" else 133539774.0
        assert abs(total - want) <= 0.5
    assert abs(d["receipts"]["cash"] - 112552000.0) <= 0.5
    assert abs(d["payments"]["cash"] - 99393195.0) <= 0.5
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL.

- [ ] **Step 3: Implement `bridge.py`** per the interface. Lines' `note` strings are one-liners, e.g. R-01: "TX0036 direction Unknown → Payment, now Supported". G2's register-id check loads the register. Note R-02's −5,000 appears in **both** bridges (it moves supported cash and therefore all-rows); R-06/R-07 are pending-side so only all-rows moves.

- [ ] **Step 4: Run test to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/bridge.py analysis_tools/tests/test_audit_bridge.py
git commit -m "feat(audit): 2026-10-10 to audited bridges and all-rows decomposition

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 10: `emit.py` — deterministic output writers

**Files:**
- Create: `analysis_tools/audit/emit.py`
- Test: `analysis_tools/tests/test_audit_emit.py`

**Interfaces:**
- Consumes: apply/balance/bridge outputs, `load.load_register/load_evidence`.
- Produces (all into `OUT_DIR = ROOT/"anjoman_accounting_information/reports/2026-10-18/"`):
  - `write_ledger(rows)` → `Transactions_Audited.csv` (utf-8-sig, `SOURCE_COLS + AUDIT_COLS` header) and `.json` (list of dicts).
  - `write_log(log)` → `Audit_Log.csv` (`tx,field,old,new,source_id,reason,evidence`; `evidence` = " | ".join).
  - `write_register(register)` → `Decisions_Register.json` — **byte copy** of the committed file (`shutil.copyfile`).
  - `write_sheets(sheets, pending_items)` → `Balance_Sheets.json` + long-format `Balance_Sheets.csv` (`project,section,line_label,amount_toman,extra`).
  - `write_open_items(rows)` → `Open_Items.csv` (`id,project,rows,amount_toman,question,what_settles`; project resolved from the rows, `rows` semicolon-joined, empty for OI-07).
  - All writers are pure functions of their arguments (no clock, no dict-order dependence: iterate in sorted/insertion order as fixed above).

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_emit.py
import csv, json
from analysis_tools.audit import apply, bridge, balance, emit, load, rules

def test_write_all_outputs(tmp_path):
    rows, log = apply.apply()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS)
    emit.write_ledger(rows, out_dir=tmp_path)
    emit.write_log(log, out_dir=tmp_path)
    emit.write_register(out_dir=tmp_path)
    emit.write_sheets(sheets, rules.PENDING_ITEMS, out_dir=tmp_path)
    emit.write_open_items(rows, out_dir=tmp_path)
    ledger = list(csv.DictReader(open(tmp_path / "Transactions_Audited.csv",
                                       encoding="utf-8-sig")))
    assert len(ledger) == 97 and ledger[0]["source_status"] in {
        "Supported", "Review", "Duplicate", "Invoice only", "Summary only"}
    j = json.loads((tmp_path / "Transactions_Audited.json").read_text(encoding="utf-8"))
    assert len(j) == 97
    logrows = list(csv.DictReader(open(tmp_path / "Audit_Log.csv", encoding="utf-8-sig")))
    assert {"tx", "field", "old", "new", "source_id"} <= set(logrows[0])
    oi = list(csv.DictReader(open(tmp_path / "Open_Items.csv", encoding="utf-8-sig")))
    assert len(oi) == 18 and oi[6]["id"] == "OI-07"

def test_register_is_byte_copy(tmp_path):
    emit.write_register(out_dir=tmp_path)
    assert (tmp_path / "Decisions_Register.json").read_bytes() == \
        (load.DATA / "decisions.json").read_bytes()

def test_deterministic(tmp_path):
    rows, log = apply.apply()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS)
    import io
    outs = []
    for _ in range(2):
        emit.write_ledger(rows, out_dir=tmp_path)
        buf = io.StringIO()
        emit._csv_string(rows, load.SOURCE_COLS + load.AUDIT_COLS, buf)
        outs.append(buf.getvalue())
    assert outs[0] == outs[1]
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL.

- [ ] **Step 3: Implement `emit.py`** — thin `csv`/`json` writers matching the signatures above (default `out_dir=emit.OUT_DIR`); `_csv_string(rows, header, buf)` is the shared serializer used by both writers and tests.

- [ ] **Step 4: Run test to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/audit/emit.py analysis_tools/tests/test_audit_emit.py
git commit -m "feat(audit): deterministic writers for the 2026-10-18 report folder

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 11: Glossary additions + G10 coverage test

**Files:**
- Modify: `analysis_tools/i18n/glossary.json` (append only; existing entries byte-identical)
- Test: `analysis_tools/tests/test_audit_glossary.py`

**Interfaces:**
- Produces: `term("status"/"date_basis"/"account_type"/"project"/"ledger_category", key, "fa")` resolvable for every value the audited data uses (Task 12's FA render and G6 depend on it).

Add to `status`: `"Internal transfer": "انتقال داخلی"`, `"Pending": "در انتظار"`, `"Payable": "پرداختنی"`, `"Supporting detail": "جزئیات پشتیبان"`, `"Memo": "یادداشت"`. Add new kinds:

```json
"date_basis": {
  "printed": "تاریخِ سند", "event-day proxy": "تقریب روزِ رویداد",
  "on or before": "در یا قبل از", "month only": "فقط ماه",
  "Telegram post time": "زمان ارسال در تلگرام",
  "by event association": "قرینهٔ رویداد",
  "reports posted": "زمان انتشار گزارش‌ها"
},
"account_type": {
  "personal": "شخصی", "association": "انجمن", "volunteer": "داوطلب",
  "event custodian": "امین رویداد", "cash": "نقد",
  "not evidenced": "مستندنشده"
}
```

`project` already has `Yalda 1404` («یلدا ۱۴۰۴») — verify, do not touch. `ledger_category` already has `Unclassified`/`Website domain` — verify.

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_glossary.py
import json
from analysis_tools import i18n
from analysis_tools.audit import load

def test_existing_terms_unchanged():
    g = i18n.catalog("glossary")
    assert g["status"]["Supported"] == "تأییدشده"
    assert g["status"]["Review"] == "نیازمند بررسی"
    assert g["project"]["Yalda 1404"] == "یلدا ۱۴۰۴"
    assert g["ledger_category"]["Unclassified"] == "طبقه‌بندی‌نشده"

def test_new_status_terms():
    g = i18n.catalog("glossary")
    for s in load.NEW_STATUSES:
        assert g["status"][s], s

def test_every_used_value_has_fa_term():
    from analysis_tools.audit import apply, rules
    g = i18n.catalog("glossary")
    rows, _ = apply.apply()
    for r in rows:
        assert r["status"] in g["status"], r["id"]
        if r["date_basis"]:
            assert r["date_basis"] in g["date_basis"], r["id"]
    acc = load.load_accounts()
    for a in acc.values():
        assert a["type"] in g["account_type"], a
    for r in rows:
        assert r["project"] in g["project"], r["id"]
        assert r["category"] in g["ledger_category"], r["id"]
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (missing status/date_basis/account_type terms).

- [ ] **Step 3: Add the glossary entries exactly as above** (hand-written FA terms; they are glossary, not catalog — `translate.py` never touches them).

- [ ] **Step 4: Run test to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/i18n/glossary.json analysis_tools/tests/test_audit_glossary.py
git commit -m "feat(i18n): glossary terms for audit statuses, date bases, account types

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Full suite: PASS.

---

### Task 12: `build_audit_report.py` + EN catalog keys + translation run

**Files:**
- Create: `analysis_tools/build_audit_report.py`
- Modify: `analysis_tools/i18n/en.json` (add `audit.*` keys), `analysis_tools/i18n/fa.json` + `hashes.json` (via the translate run)
- Test: `analysis_tools/tests/test_audit_report.py`

**Interfaces:**
- Consumes: everything from Tasks 5–11; `report_common.ensure_disk/md_to_pdf/md_to_pdf_rtl`; i18n `t/term/localize/punct/dt`.
- Produces:
  - `OUT_MD = ROOT/"anjoman_accounting_information/reports/2026-10-18/Anjoman_Ledger_Audit_Report.md"`, `OUT_FA` (`..._FA.md`).
  - `LOCKED = {"cash_receipts": 112552000.0, "cash_payments": 99393195.0, "net": 13158805.0, "pending": 21626064.0, "allrows_receipts": 139787000.0, "allrows_payments": 133539774.0}`.
  - `collect_data() -> tuple` — one call to apply/balance/bridge/load; everything the render needs.
  - `render(lang="en") -> str` — the full report; FA passes through `localize()` once at the end (EN output byte-stable).
  - `build(lang="en")` — writes MD; `ensure_disk(OUT_MD.parent)`; EN PDF via `md_to_pdf`, FA via `md_to_pdf_rtl`; calls every `emit.write_*`; runs `run_gates()`.
  - `run_gates()` — G1 `balance.check_summary`; G2 `bridge.check`; G3 `apply.diff_completeness == []` + every log `source_id` ∈ register ∪ mechanical ∪ {"B-01"}; G4 re-asserted by `load.load_mechanical` (field allowlist); G5 each `LOCKED` figure vs computed (message `gate FAILED: ...`); G9 `pii.scan` over every emitted file's text.
  - `main()` — argparse `--lang {en,fa,all}` default `en`; `all` = en then fa.

**Report structure** (spec §6; same section order in both languages; every number flows from `collect()` — no literals):

1. Headline — cash receipts/payments/net, pending (rows + PI-01), excluded total; `audit.headline.note` (basis statement, B-01).
2. What changed — the two bridges rendered from `bridge.bridges()`; every line `«id — tx: note (±N toman)»`.
3. Consolidated summary — `balance.summary(sheets)`; totals row equals the headline (G1 asserted in-render).
4. Project balance sheets — one subsection per project (skip empties with `audit.sheet.empty_note`); receipts by source, payments by category, net, pending column (rows + PI items), transaction table (`id | date/basis | counterparty | description_en/_fa | amount | status | evidence ref` — date cell: `dt()` when dated, else `period + term("date_basis", …)`; evidence ref: first `evidence_index.rows[tx]` ref), excluded list under parent, project open items.
5. Cash custody — `balance.custody()` table grouped by `account_type` with subtotals; holder/type via `term("account_type", …)`.
6. Balance-chain gaps (S-01) — the `balance_chain` block rendered as a table + `audit.s6.intro` disclosure + open item OI-07.
7. Open items — all 18 from `Open_Items` data.
8. Decisions and audit log — register summary table (id, rows, choice) + audit-log summary grouped by source_id + the mechanical-fix list (id, tx, field, reason) flagged for one-pass review.
9. Method — `audit.s9.body` (sources, date-basis legend, toman unit, tolerance, read-only 2026-10-10).

**EN catalog keys to add** (exact key names; templates use `{placeholders}`; write the English values as given, completing the table-shaped keys with the header words shown):

```
audit.title = "Anjoman ledger audit - 2026-10-18"
audit.headline.note = "Basis: cash + pending. Supported rows are cash; open reviews and unpaid invoices are pending; duplicates, supporting detail and memo rows are excluded. Net activity is not closing cash: custody is mixed across personal and association accounts (section 5)."
audit.s2.title = "What changed since 2026-10-10"
audit.bridge.start = "2026-10-10 {basis}: receipts {rin} / payments {pout}"
audit.bridge.line = "{id} - {tx}: {note} ({delta} toman)"
audit.bridge.end = "Audited {basis}: receipts {rin} / payments {pout} (net {net})"
audit.s3.title = "Consolidated summary (cash basis)"
audit.h.project = "Project" ... audit.h.receipts = "Receipts", audit.h.payments = "Payments", audit.h.net = "Net", audit.h.pending = "Pending", audit.h.excluded = "Excluded"
audit.s4.title = "Project balance sheets"
audit.sheet.receipts_by = "Receipts by source", audit.sheet.payments_by = "Payments by category", audit.sheet.net = "Net (cash)", audit.sheet.pending = "Pending (rows + items)", audit.sheet.tx = "Transactions", audit.sheet.excluded = "Excluded rows", audit.sheet.open = "Open items", audit.sheet.empty_note = "No audited rows remain in this project; its rows moved per the decision register (see section 8)."
audit.h_tx.id = "ID", audit.h_tx.date = "Date", audit.h_tx.counterparty = "Counterparty", audit.h_tx.description = "Description", audit.h_tx.amount = "Amount (toman)", audit.h_tx.status = "Status", audit.h_tx.evidence = "Evidence"
audit.tx.period_cell = "{period} ({basis})"
audit.s5.title = "Cash custody"
audit.custody.h.account = "Account", audit.custody.h.holder = "Holder", audit.custody.h.type = "Type", audit.custody.h.in = "Cash in", audit.custody.h.out = "Cash out", audit.custody.h.transfers = "Internal transfers"
audit.custody.note = "Holder and type as evidenced; 'not evidenced' means no document identifies them."
audit.s6.title = "Balance-chain gaps (disclosed, not booked)"
audit.s6.intro = "Decision S-01: bank balances implied by the evidenced snapshots do not reconcile with recorded flows. These movements are disclosed, not booked; open item {oi} asks for the Bank Shahr statement."
audit.s7.title = "Open items"
audit.s7.h.what = "What settles it"
audit.s8.title = "Decisions and audit log"
audit.s8.register = "{n} decisions taken on 2026-10-18; full text in Decisions_Register.json."
audit.s8.mechanical = "Mechanical fixes ({n}) - money-neutral; reviewed by the owner in one pass."
audit.s8.log = "Audit log: {n} field changes ({created} created rows/items)."
audit.s9.title = "Method"
audit.s9.body = "Source: reports/2026-10-10/Transactions.csv (96 rows, read-only). Evidence: the accounting Telegram group export (message ids), the receipts folder, invoices and workbooks. Date bases: printed = the date on the document; event-day proxy = the event day; on or before = an upper bound; month only = month precision, flagged; Telegram post time = the post's server timestamp; reports posted = the day the financial report was posted; by event association = period inferred from the event. Amounts are toman (1 toman = 10 rial); totals compare within 0.5 toman. Nothing under reports/2026-10-10 or reports/2026-10-14 was modified."
```

- [ ] **Step 1: Write the failing test**

```python
# analysis_tools/tests/test_audit_report.py
import pytest
from analysis_tools import build_audit_report as bar

def test_locked_figures():
    rows, log = bar.collect_data()
    bar.run_gates()  # G1-G5, G9 raise on failure

def test_en_render_byte_identical():
    a, b = bar.render("en"), bar.render("en")
    assert a == b

def test_gate_fires(monkeypatch):
    monkeypatch.setitem(bar.LOCKED, "cash_payments", 1.0)
    with pytest.raises(AssertionError, match="gate FAILED"):
        bar.run_gates()
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (module missing).

- [ ] **Step 3: Implement the builder** — `collect_data()`, `render(lang)`, `build(lang)`, `run_gates()`, `main()` as specified. Every user-visible string goes through `t("audit....")`; status/date-basis/account-type labels through `term(...)`; FA single `localize()` pass; FA branch runs under the `pseudo_fa` fixture in tests. Numbers: `f"{v:,.0f}"`-style formatting kept English until `localize()`; `135,799.9` stays one decimal where fractional.

- [ ] **Step 4: Run tests** — `python -m pytest analysis_tools/tests/test_audit_report.py -q` — PASS.

- [ ] **Step 5: Add the `audit.*` keys to `en.json`** exactly as inventoried above (keep alphabetical order of the file; `test_every_en_key_is_referenced` must stay green — every key is referenced from the builder).

- [ ] **Step 6: USER GATE — translation run (VPN on)**

Ask the user to turn the VPN on. Then:

```bash
cd "/c/Users/Surface Laptop 3/Downloads/Telegram Desktop/anjoman_acc"
ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" python -m analysis_tools.translate
```

Expected: the new `audit.*` keys translate, validate, and land in `fa.json` + `hashes.json`; cache written under `analysis/claude/i18n/`. If the VPN is off, stop and ask — never run without it.

- [ ] **Step 7: Full suite green** — `python -m pytest analysis_tools/tests/ -q` — PASS (now including `test_catalog_integrity` with the new keys).

- [ ] **Step 8: Build EN and commit**

```bash
python -m analysis_tools.build_audit_report --lang en
git add analysis_tools/build_audit_report.py analysis_tools/i18n/en.json analysis_tools/i18n/fa.json analysis_tools/i18n/hashes.json analysis_tools/tests/test_audit_report.py anjoman_accounting_information/reports/2026-10-18/
git commit -m "feat(audit): EN/FA audit report builder, catalog keys, 2026-10-18 outputs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: FA build, number parity, visual check, full gates

**Files:**
- Create: `anjoman_accounting_information/reports/2026-10-18/Anjoman_Ledger_Audit_Report_FA.md/.pdf/.html` (via build)
- Modify: `analysis_tools/tests/test_audit_report.py` (add parity + byte-identity tests)

- [ ] **Step 1: Add the failing parity/identity tests**

```python
def test_fa_render_byte_identical(pseudo_fa):
    a, b = bar.render("fa"), bar.render("fa")
    assert a == b

def test_number_parity():
    from analysis_tools import i18n
    assert i18n.number_tokens(bar.render("en")) == \
        i18n.number_tokens(bar.render("fa"))
```

- [ ] **Step 2: Run to verify fail/pass** — the FA tests need the real glossary terms (Task 11) and catalog (Task 12); run `python -m pytest analysis_tools/tests/test_audit_report.py -q` — Expected: PASS (number parity must hold by construction; fix the render if a number leaks).

- [ ] **Step 3: Build FA + regenerate EN, verify on-disk determinism (G7)**

```bash
python -m analysis_tools.build_audit_report --lang all
python -m analysis_tools.build_audit_report --lang all
git diff --stat anjoman_accounting_information/reports/2026-10-18/
```

Expected: second run produces **no diff** (byte-identical outputs on disk).

- [ ] **Step 4: Read-only check (G8) + PII (G9) as tests** — add to `test_audit_report.py`:

```python
def test_readonly_folders_untouched():
    import subprocess
    for p in ("anjoman_accounting_information/reports/2026-10-10",
              "anjoman_accounting_information/reports/2026-10-14"):
        subprocess.run(["git", "diff", "--quiet", "--", p], check=True)

def test_no_pii_in_outputs():
    from analysis_tools.audit import emit
    from analysis_tools.audit.pii import scan
    for f in emit.OUT_DIR.iterdir():
        hits = scan(f.read_text(encoding="utf-8", errors="ignore"))
        assert hits == [], (f.name, hits)
```

Run the full suite: `python -m pytest analysis_tools/tests/ -q` — PASS.

- [ ] **Step 5: Visual check of the FA PDF** — rasterize 2–3 pages (`pdftoppm -png -r 100`) and Read them: Persian letters joined, RTL layout, Persian digits, tables not flipped. The controller and the user view them.

- [ ] **Step 6: Commit**

```bash
git add anjoman_accounting_information/reports/2026-10-18/ analysis_tools/tests/test_audit_report.py
git commit -m "feat(audit): FA report build, parity and determinism gates

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Gate summary (where each lives)

| Gate | Lives in |
|---|---|
| G1 project sums | `balance.check_summary`, called in `run_gates()` + test |
| G2 bridge exactness | `bridge.check` + test |
| G3 log completeness | `apply.diff_completeness` + Task 12's `run_gates` |
| G4 mechanical field allowlist | `load.load_mechanical` + `apply._mechanical` refusal |
| G5 locked figures | `run_gates()` vs `LOCKED` + `test_locked_figures` |
| G6 EN/FA number parity | `test_number_parity` (Task 13) |
| G7 byte identity | double-render tests + rebuild-diff step (Task 13) |
| G8 read-only folders | `test_readonly_folders_untouched` (Task 13) |
| G9 PII scan | `pii.scan` in `run_gates` + `test_no_pii_in_outputs` |
| G10 glossary parity | `test_audit_glossary.py` (Task 11) |

## Out of scope (unchanged from spec)

Charts; `.xlsx` workbook; booking balance-chain gaps; changes under `reports/2026-10-10` or `reports/2026-10-14`; deleting stale remote branches (only if the user asks later).
