# Ledger audit and per-project balance sheets — design

Date: 2026-10-18 · Branch: `feature/ledger-audit` · Status: approved in brainstorming (decisions taken first, see §3)

## 1. Goal

Produce an evidence-based, human-decided audit of the 2026-10-10 reconciled ledger
(`anjoman_accounting_information/reports/2026-10-10/Transactions.csv`, 96 rows) and publish it as a new
dated report folder `anjoman_accounting_information/reports/2026-10-18/` containing:

- the audited ledger (CSV + JSON),
- a field-level audit log (every change, its reason, its evidence, and the decision or mechanical-fix id it rests on),
- a copy of the decision register,
- per-event/program balance sheets reconciled to the audited totals, with a bridge from the 2026-10-10 totals,
- English and Persian reports (MD + PDF; FA also keeps its `.html`), built from the same data.

Out of scope: modifying anything under `reports/2026-10-10/` or `reports/2026-10-14/`; booking the
balance-chain gaps (they are disclosed, §6.6); charts; an `.xlsx` workbook.

## 2. Inputs

Read-only sources:

| Input | Use |
|---|---|
| `reports/2026-10-10/Transactions.csv` (utf-8-sig) | the 96 source rows; never written |
| `reports/2026-10-10/final_checks.json` | 2026-10-10 supported totals (bridge start) |
| `reports/2026-10-10/fa/Accounting_Data_FA.json` | FA precedent (glossary parity, existing FA descriptions) |
| `analysis_tools/i18n/glossary.json` | EN→FA ledger terms (projects, categories, statuses, directions) |

Committed audit inputs (new, in `analysis_tools/audit/data/`):

| File | Content |
|---|---|
| `decisions.json` | the decision register (§3), the only source of money-affecting changes |
| `mechanical.json` | money-neutral fixes: `description_en`/`description_fa` rewrites with evidence citations, tracking-id and evidence-link corrections (§4.3) |
| `evidence_index.json` | per-TX evidence list distilled from the dossiers (ref, timestamp, what it shows), PII-free (§8) |
| `accounts.json` | per `cash_account` code: holder and type **as evidenced** (`personal`, `association`, `volunteer`, `event custodian`, `cash`, `not evidenced`) with an evidence ref; no guessing |

## 3. Decision register (`decisions.json`)

A JSON array; one object per decision, taken with the owner on 2026-10-18 in batches:

```json
{"id": "R-06", "kind": "scope|basis|process|duplicate|review|date|reassignment",
 "tx": ["TX0049"], "question": "...", "options": ["...", "..."], "choice": "...",
 "rationale": "...", "evidence": ["message115 ...", "..."], "date": "2026-10-18",
 "set": {"...": "..."}, "pending_item": {"...": "..."}}
```

The register holds 38 entries: S-01, B-01, A-01 (design), D-01…D-06, R-01…R-16, U-01…U-08, P-01…P-05.
Interpretation of the human-readable `choice` is fixed by `analysis_tools/audit/rules.py` (§4.2), a single
explicit table mapping each decision id to field patches. The register text is never parsed for meaning.

Outcomes (binding):

| Id | Rows | Outcome |
|---|---|---|
| S-01 | — | Balance-chain flows not in the ledger are disclosed (§6.6), not booked. |
| B-01 | — | Basis: cash headline + pending column + excluded list (§5). |
| D-01 | TX0022, 25, 51, 57 | stay `Duplicate` |
| D-02 | TX0010 | `Review` → `Duplicate`, `duplicate_of` TX0009 |
| D-03 | TX0052–55 | `Review` → `Supporting detail`, `parent` TX0050 |
| D-04 | TX0064–74 | `Review`/`Invoice only` → `Supporting detail`, `parent` TX0062;TX0063 |
| D-05 | TX0069 | clear `duplicate_of` (distinct receipt) |
| D-06 | TX0042 | `Review` → `Supported` |
| R-01 | TX0036 | direction `Unknown` → `Payment`; `Review` → `Supported` |
| R-02 | TX0031 | amount 235,000 → 230,000 (`amount_original` 2,300,000 rial) |
| R-03 | TX0018 | unit rial; amount 1,765,000; `Review` → `Supported` (internal transfer) |
| R-04 | TX0001 | amount unchanged (33,642,000); 1,000 report difference logged |
| R-05 | TX0047 | unchanged (toman) |
| R-06 | TX0049 | unit rial, `amount_original` 100,037,800, amount 10,003,780, date 1404/10/01; stays `Review` (pending) |
| R-07 | TX0056, TX0058 | TX0058 amount 275,000; both → `Payable` (pending, unreimbursed volunteer spend: Hossein) |
| R-08 | — | pending item PI-01: 275,584 payable to Bardia (Yalda 1404) |
| R-09 | TX0062/63 | unchanged; open item (195,860.1 undocumented) |
| R-10 | TX0060 | stays `Invoice only` (pending) |
| R-11 | TX0082 | project → Summer School 1405; stays `Invoice only` (pending payable) |
| R-12 | TX0093/94 | unchanged; 4,235,000 gap shown in Intro Event 1405 sheet + open item |
| R-13 | TX0096 | stays `Review` (pending); period 1405/04, date note "on or before 1405/04/08" |
| R-14…R-16 | TX0013, TX0045, TX0095 | stay `Supported`; evidence-basis label "original ledger only" + open item |
| U-01 | TX0001 | date 2025-07-24 |
| U-02 | TX0014, 16, 17 | date 2025-09-06 (event-day proxy) |
| U-03 | TX0015 | date 2025-09-04 (Telegram post time; slip prints 1404/06/14) |
| U-04 | TX0044 | date 2025-11-19 ("on or before"), period 1404/08 |
| U-05 | TX0036 | date 2025-10-29 (event-day proxy) |
| U-06 | TX0074 | date 2025-12-24 (1404/10/03) |
| U-07 | TX0060 | period 1404/10 (by event association), undated |
| U-08 | TX0010, 13, 25, 45, 47, 48, 58, 93, 95 | month only, flagged |
| P-01 | TX0080 | project Summer School 1405, category Advertising |
| P-02 | TX0089 | project Intro Event 1405, category Hospitality |
| P-03 | TX0034 | split: TX0034 1,000,000 (Freshman Party 1404) + new TX0034-B 500,000 (Association operations / Equipment) |
| P-04 | TX0020 | unchanged; description notes shared use |
| P-05 | 11 Unassigned rows | unchanged; one open item each "purpose unknown" |

Every decision-dependent field change in the audited ledger must cite one of these ids (gate G3).

## 4. Pipeline

New package `analysis_tools/audit/`:

| Module | Responsibility |
|---|---|
| `load.py` | read the source CSV and the four data files; validate their schemas |
| `rules.py` | the explicit decision-id → patch table (§4.2) |
| `apply.py` | source rows + rules + mechanical → audited rows + audit-log entries |
| `balance.py` | per-project sheets, consolidated summary, custody table |
| `bridge.py` | 2026-10-10 → audited bridges (supported basis and all-rows basis) |
| `build_audit_report.py` | `render(lang)` / `build(lang)` for EN and FA; writes every output file; CLI `--lang en|fa|all` |

### 4.1 Audited row schema

The source columns (with `status` holding the audited status, §5), plus: `source_status` (the 2026-10-10
status), `pending_reason` (`Review`, `Invoice only` or empty), `parent` (supporting-detail parent ids), `date_basis`
(`printed`, `event-day proxy`, `on or before`, `month only`, `Telegram post time`, `by event association`, or empty),
`evidence_label` (e.g. "original ledger only"), `open_item` (id or empty), `changed_fields` (semicolon list).

### 4.2 Rules

`rules.py` holds `RULES: dict[str, list[Patch]]` where `Patch = (tx_id, field, new_value)`, plus
`NEW_ROWS` (TX0034-B) and `PENDING_ITEMS` (PI-01). `apply.py` refuses (raises) on: a rule id absent from the
register; a register id with neither a rule nor an explicit "no field change" marker; two patches on the same
field from different decisions; a patch to a field the source row does not have.

### 4.3 Mechanical fixes (`mechanical.json`)

```json
{"id": "M-012", "tx": "TX0083", "field": "description_en", "new": "...", "reason": "...", "evidence": ["summerschool_channel message29"]}
```

Allowed fields: `description_en`, `description_fa`, `tracking_id`, `message_ids`, `notes`, `evidence_basis`.
A mechanical fix may never touch amount, unit, status, direction, date, period, project, category,
`duplicate_of` or `cash_account` (gate G4). Every row gets reviewed descriptions in both languages: what was
bought/received, from or to whom, for which event, citing the evidence ref; where evidence is thin the description
says so. Known mechanical items include: TX0075 tracking id `187300` → `001873`; photo_34 evidence moves from
TX0033 to TX0035; TX0083/84/87 course names; TX0038 invoice number 29350; TX0002 note correction.
The owner reviews all M-entries in one pass after the first build (audit log section "Mechanical fixes").

### 4.4 Audit log

One entry per changed field: `tx, field, old, new, source_id (decision or M- id), reason, evidence`.
Written as `Audit_Log.csv` and summarized in the reports. Rows created (TX0034-B) and pending items log a
`created` entry.

## 5. Basis and status vocabulary (B-01)

| `status` | Meaning | In cash totals | In pending | Listed as excluded |
|---|---|---|---|---|
| Supported | received/paid, evidenced or original-ledger | yes | — | — |
| Internal transfer | between custody accounts (TX0018) | no (custody table only) | — | — |
| Pending | open Review rows and unpaid invoices (TX0049, TX0060, TX0082, TX0096) | no | yes | — |
| Payable | unreimbursed volunteer spend (TX0056, TX0058) | no | yes | — |
| Supporting detail | itemization of a reimbursement (TX0052–55, TX0064–74) | no | no | yes, under its parent |
| Duplicate | second record of the same money (TX0010, 22, 25, 51, 57) | no | no | yes, with `duplicate_of` |
| Memo | non-additive report figure (TX0094) | no | no | yes |

Status mapping where no decision patches the status (applied under B-01 and logged with source id B-01):
Supported → Supported; Review → Pending (`pending_reason` Review); Invoice only → Pending (`pending_reason` Invoice only);
Summary only → Memo; Duplicate → Duplicate; direction Internal transfer → status Internal transfer once Supported.

Pending items (`PI-nn`) are not ledger rows and appear only in the pending column of their project.
Amounts are kept at 0.1-toman precision (TX0071 = 135,799.9); totals compare within 0.5 toman; display rounds
half-up to whole toman except where a fractional value is itself shown.

FA terms for the new statuses are added to `glossary.json` (`status` kind) and to the glossary parity test;
existing terms stay byte-identical. Also added: `ledger_category` `Unclassified`/`Website domain` if absent from FA,
`date_basis` kind, `account_type` kind.

## 6. Report content (EN and FA, same structure)

1. **Headline**: audited cash receipts / payments / net, pending total, excluded total; the statement that net
   activity is not closing cash (mixed custody).
2. **What changed**: two bridges (§6.2).
3. **Consolidated summary**: one row per project: cash receipts, cash payments, net, pending, excluded count;
   totals row equals the headline (gate G1).
4. **Project balance sheets** (12 projects; "Unknown (likely 1405 summer school)" is emptied by R-11 and shown
   as a note): receipts by source, payments by category, net, pending column (rows + PI items), the transaction
   table (id, date or month + basis flag, counterparty, description, amount, status, evidence ref), the
   excluded list (duplicates and supporting detail under their parent), and the project's open items.
5. **Cash custody**: per `cash_account`: holder and type from `accounts.json`, cash in/out, internal transfers.
6. **Balance-chain gaps (S-01)**: the evidenced balance snapshots and the implied unrecorded movements
   (≈3,163,000 debits 1405/05/21–22; ≈35.2M credits 1404/12→1405/05; ≈12.8–19.8M debits 1404/09→12; TX0007 and
   TX0024 inflow anomalies), each with its source, and the open item asking for the Bank Shahr statement. Figures
   come from a committed data block in `evidence_index.json`, not recomputed from images.
7. **Open items for the owner/treasurer**: every unresolved question with its amount and what would settle it.
8. **Decisions and audit log**: register summary (id, rows, choice) and the mechanical-fix list.
9. **Method**: sources, evidence basis labels, read-only treatment of 2026-10-10.

### 6.2 Bridges

- **Supported basis**: 2026-10-10 supported receipts 112,552,000 / payments 99,085,195 → audited cash
  receipts 112,552,000 / payments 99,393,195, one line per decision that moves cash (R-01 +300,000; R-02 −5,000;
  D-06 +13,000), each line citing its id. Net 13,466,805 → 13,158,805.
- **All-rows basis**: 2026-10-10 all-rows receipts 139,787,000 / payments 123,265,994 (as stated in the
  2026-10-14 builder; TX0036 counted as payment) → audited all-rows (every row incl. excluded, internal transfers
  excluded), one line per amount change (R-02 −5,000; R-06 +10,003,780; R-07 +275,000), then a decomposition of
  the audited all-rows totals into cash + pending + excluded (duplicates, supporting detail, memo).
- Pending total 21,626,064 = rows 21,350,480 + PI-01 275,584.

## 7. Outputs (`anjoman_accounting_information/reports/2026-10-18/`)

| File | |
|---|---|
| `Transactions_Audited.csv` / `.json` | audited rows (97: 96 + TX0034-B), §4.1 schema |
| `Audit_Log.csv` | §4.4 |
| `Decisions_Register.json` | byte copy of `analysis_tools/audit/data/decisions.json` |
| `Balance_Sheets.json` / `Balance_Sheets.csv` | per project: sections and lines (long format in CSV) |
| `Open_Items.csv` | id, project, rows, amount, question, what settles it |
| `Anjoman_Ledger_Audit_Report.md` / `.pdf` | EN, reportlab via `report_common.md_to_pdf` |
| `Anjoman_Ledger_Audit_Report_FA.md` / `.pdf` / `.html` | FA, `md_to_pdf_rtl` |

EN text lives in `analysis_tools/i18n/en.json` under prefix `audit.*`; FA comes from `translate.py` (Claude
API, VPN on, key via env only) and is committed. Row descriptions come from `mechanical.json` (both languages),
not from the translator. Builders never call the API. `ensure_disk()` runs before any PDF work.

## 8. Privacy

No national ID, phone number, full card number, IBAN or credential appears in any committed input or output.
Card numbers appear only as last four digits. The invoice-61150 buyer details and the message11142 credential
are excluded. Student phone numbers from the course reports are excluded.

## 9. Gates (assert-based, run inside `build()` and as tests)

- **G1** Σ project cash receipts / payments = audited cash totals, within 0.5 toman; Σ project pending = pending total.
- **G2** Both bridges sum exactly to their end totals; every line cites a register id.
- **G3** Every audited field that differs from the source is in the audit log; every decision-scope field change
  cites an existing register id; every register id is applied or marked "no field change".
- **G4** Mechanical fixes touch only allowed fields.
- **G5** Audited cash totals equal the expected values in §6.2 (regression lock).
- **G6** EN and FA reports carry the same multiset of numbers (dates compared after Jalali conversion), as in
  `test_report_i18n`.
- **G7** Two consecutive renders per language are byte-identical; outputs on disk equal a fresh render.
- **G8** `reports/2026-10-10/` and `reports/2026-10-14/` are unchanged (`git diff --quiet` on those paths in the test).
- **G9** No PII patterns (Iranian national-ID 10-digit, `09\d{9}` phone, 16-digit card, `IR\d{24}` IBAN, known
  credential strings) in any output.
- **G10** Glossary parity: existing ledger terms unchanged; every `status`, project, category and date-basis
  value used has an FA term.

## 10. Testing

`analysis_tools/tests/test_audit_*.py`: unit tests for `apply` (patch application, refusals, split row,
pending items), `balance` (sheet sums, PI placement, empty project note), `bridge` (exact lines), and the gates
above, using the real committed inputs. FA tests use the existing `pseudo_fa` fixture pattern where the real
catalog is not yet translated.
