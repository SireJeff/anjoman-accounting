# Anjoman Accounting & Telegram Archives (حسابداری و آرشیو انجمن)

Central repository for the Anjoman's accounting records, Telegram chat archives, and the
analysis/audit pipeline that turns them into board reports (English + Persian).

## The three report generations

Every folder in this repo feeds one of three published generations. Each is **frozen** once
published — later work always writes a new dated folder and never edits the old ones.

```
workbooks ──┐
            ├─► reports/2026-10-10/  reconciled financial report  (96-row Transactions.csv)
receipts ───┘            │  (read-only)
                         ▼
5 Telegram exports ──► analysis/ artifacts ──► reports/2026-10-14/  monthly + performance analysis
                         │                         (read-only)
                         ▼
2026-10-10 ledger + evidence (messages, receipt photos, invoice)
                         │
                         ▼
            analysis_tools/audit/  ──► anjoman_accounting_information/reports/2026-10-18/
            38 decisions + 89 fixes  audited re-publication: 97 rows, EN+FA reports, balance sheets
```

- **2026-10-10** — the reconciled ledger produced from the bookkeeping workbooks and receipts.
- **2026-10-14** — analysis of that ledger against all five Telegram exports (financial monthly + performance).
- **2026-10-18** — the audited re-publication: every change to the ledger traced to a numbered
  decision or mechanical fix, per-project balance sheets, reconciliation bridges, EN + FA reports.

## Repository layout

| Directory | Contents |
|---|---|
| `anjoman_accounting_information/` | All accounting material (workbooks, receipts, invoice, accounting-group export, reports) — see below |
| `anjoman_channel_content/` | Telegram **channel** export (2026-10-10) |
| `anjoman_private_group_report/` | Telegram **private group** export (2026-10-13) |
| `anjoman_public_group_export/ChatExport_2026-10-13/` | Telegram **public group** export (2026-10-13) |
| `anjoman_summerschool_channel_content/` | Telegram export of the Physics Summer School channel (@sutschools), 2025-07 → 2026-08 |
| `analysis/` | Parsed/classified Telegram corpus and intermediate artifacts: `classified.jsonl`, event threads, `ecosystem.json`, LLM labeling batches under `labels/` (2026-10-14) |
| `analysis_tools/` | Python pipeline: parsers, report builders, i18n, and the 2026-10-18 audit package |
| `analysis_tools/audit/` | Audit pipeline (`load → rules → apply → balance/bridge → emit`) — pure, deterministic, fully tested |
| `analysis_tools/audit/data/` | The audit's committed inputs: `decisions.json`, `mechanical.json`, `evidence_index.json`, `accounts.json` |
| `analysis_tools/i18n/` | EN/FA string catalogs (`en.json`, `fa.json`, `hashes.json`) and the hand-maintained EN→FA `glossary.json` |
| `reports/2026-10-14/` | Financial and performance report packages (EN + FA, `charts_fa/`) |
| `docs/superpowers/` | Design specs and implementation plans for each work stream (persian-reports, performance-analysis, ledger-audit) |
| `گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx` | Persian performance report as a standalone Word document |

### `anjoman_accounting_information/`

- `Anjoman accounting.xlsx` — original bookkeeping workbook
- `Anjoman accounting - refined.xlsx` — cleaned, reconciled workbook
- `accounting_tools/` — the 2026-10-10 pipeline (see its own README)
- `recipts/` — receipt photos backing the recorded transactions
- `invoice-61150.pdf` — domain expense invoice
- `physics_intro full report.pdf` — event report
- `anjoman_accounting_group_export/` — Telegram export of the accounting group (the audit's primary message evidence)
- `reports/2026-10-10/` — reconciled report package (EN + `fa/`, professional workbook, audit-evidence zip, `Transactions.csv`, validation JSONs, user confirmations) — **read-only**
- `reports/2026-10-18/` — the audited publication (see below)

## How sources and references connect

The **transaction id** (`TX0001`…`TX0096`, plus audit-created `TX0034-B`) is the join key
across the entire corpus. Everything else keys into it:

| File | Keyed by | What it holds |
|---|---|---|
| `reports/2026-10-10/Transactions.csv` | one row per TX | the 96-row source ledger (read-only) |
| `analysis_tools/audit/data/decisions.json` | `rows: [TX…]` | 38 owner decisions; each cites its evidence |
| `analysis_tools/audit/data/mechanical.json` | `tx` | 89 money-neutral fixes (descriptions, tracking ids, evidence refs) |
| `analysis_tools/audit/data/evidence_index.json` | `rows: {TX: […]}` | per-TX evidence refs + the `balance_chain` disclosure block |
| `analysis_tools/audit/data/accounts.json` | cash-account code | holder/type per account, as evidenced |
| `reports/2026-10-18/Audit_Log.csv` | `tx` + `source_id` | 209-entry change log: every field change cites its decision/fix id (or `B-01` status mapping) |
| `reports/2026-10-18/Transactions_Audited.csv/.json` | one row per TX | the 97 audited rows = source + 29 columns incl. audit annotations |

**Evidence refs** (in `evidence_index.json`, and rendered in the reports' Evidence column) point
out to the three evidence corpora:

- `message115`, `message120 (reply to message118)` → Telegram messages in
  `anjoman_accounting_group_export/` (open the export's `messages*.html` to read them)
- `recipts/photo_6_2026-10-10_14-07-27.jpg` → a receipt photo in `recipts/`
- `photos/photo_2@….jpg (message26)` → a photo attached to a specific message
- `invoice-61150.pdf`, workbook/snapshot references → documents in `anjoman_accounting_information/`

Each ref carries a timestamp and a `shows:` statement of what the evidence demonstrates.

**Id namespaces** cited across files: decisions (`D-xx`, `R-xx`, `U-xx`, `P-xx`, `B-01`, `S-01`,
`A-01`), mechanical fixes (`M-xxx`), pending items (`PI-01`), open items (`OI-01`…`OI-18`), cash
accounts (`SHAHR-8966`, `SEPAH-2925`, …). The audited headline is locked and gate-checked:
receipts **112,552,000** / payments **99,393,195** / net **13,158,805** / pending **21,626,064**.

**Translation chain**: `en.json` (source of truth) → `translate.py` (Claude API, VPN required) →
`fa.json` + `hashes.json` (a key re-translates only when its English hash changes). The
`glossary.json` terms are hand-written, never machine-translated. Report builders only read the
committed catalogs — they never call the API.

## Rebuilding the reports

Run from the repository root. Each builder refuses to run with under 1 GB free on C:.

```bash
# 2026-10-14 analysis reports (EN or fa)
python -m analysis_tools.charts --lang fa
python -m analysis_tools.build_financial_report --lang fa
python -m analysis_tools.build_performance_report --lang fa

# 2026-10-18 audited report (en | fa | all) — reruns every gate (G1–G5, G9) before writing
python -m analysis_tools.build_audit_report --lang all

# tests (241) — the suite includes the gate tests; run before any publication
python -m pytest analysis_tools/tests/ -q
```

Outputs are byte-deterministic: rebuilding over an existing report folder produces zero diff.
Re-translate only when `en.json` changed (VPN on; the key is read from the local key file into
the environment, never typed or committed):

```bash
ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" python -m analysis_tools.translate
```

Keys listed in `translate.MANUAL_KEYS` are hand-maintained in `fa.json` and are never
re-translated; if their English changes, update `fa.json` and `hashes.json` by hand.

## Progress log

- **2026-10-10** — Reconciled financial report produced from the workbooks and receipts: `reports/2026-10-10/` (English and Persian versions, professional workbook, audit evidence). Declared domain expense and three-month website VM budget recorded.
- **2026-10-12** — Report package merged to `main` via PR #1. Telegram channel export added (`anjoman_channel_content/`, 4,537 files). Three large media files (>50 MB) tracked with **Git LFS**; remaining content pushed in chunked batches after the initial large push timed out.
- **2026-10-13** — Repository restructured: all accounting material consolidated under `anjoman_accounting_information/` (pure moves, history preserved via rename detection). Added two new group exports: the private group report and the public group export (2026-10-13). This README added.
- **2026-10-14** — Performance & Financial analysis pipeline built (`analysis_tools/`): all five Telegram exports parsed and classified (10-category taxonomy), event threads correlated across chats and joined to the ledger, ecosystem map generated from forwards/mentions. Two new report packages: `reports/2026-10-14/financial_monthly/` and `reports/2026-10-14/performance/`.
- **2026-10-18** — Persian (FA) versions of both 2026-10-14 reports: catalog-driven (`analysis_tools/i18n`, translated once via the Claude API), RTL PDFs via WeasyPrint, Persian charts in `charts_fa/`.
- **2026-10-19** — **Ledger audit published** (`anjoman_accounting_information/reports/2026-10-18/`, merged via PR #4): all 96 source transactions re-decided against evidence (38 decisions, 89 mechanical fixes, 97 audited rows), per-project balance sheets footing to the locked headline, 2026-10-10 → audited reconciliation bridges, cash-custody registry, disclosed balance-chain gaps, 18 open items, EN + FA reports. Ten automated gates (locked figures, log completeness, PII, EN/FA number parity, byte-determinism) run in the test suite.

## Notes for collaborators

- **Read-only generations**: nothing under `reports/2026-10-10/` or `reports/2026-10-14/` (either
  location) is ever modified — the test suite enforces this (`test_readonly_folders_untouched`).
  Corrections land as new dated folders.
- **Privacy**: published outputs never contain national IDs, phone numbers, IBANs, or full card
  numbers (cards appear as last-4 only). The PII gate scans every emitted file, PDFs included.
- Files over 50 MB are stored via **Git LFS** (see `.gitattributes`). Install it (`git lfs install`) before cloning/pulling, or those files will download as pointer stubs.
- Telegram exports are raw HTML exports from Telegram Desktop — open any `messages*.html` in a browser to browse a chat with its media.
- Free GitHub LFS quota used: ~273 MB of 1 GB (bandwidth quota is 1 GB/month).
