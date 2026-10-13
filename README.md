# Anjoman Accounting & Telegram Archives (حسابداری و آرشیو انجمن)

Central repository for the Anjoman's accounting records and Telegram chat archives.

## Repository layout

| Directory | Contents |
|---|---|
| `anjoman_accounting_information/` | All accounting material, consolidated 2026-10-13 |
| `anjoman_channel_content/` | Telegram **channel** export (2026-10-10) |
| `anjoman_private_group_report/` | Telegram **private group** export (2026-10-13) |
| `anjoman_public_group_export/ChatExport_2026-10-13/` | Telegram **public group** export (2026-10-13) |

### `anjoman_accounting_information/`

- `Anjoman accounting.xlsx` — original bookkeeping workbook
- `Anjoman accounting - refined.xlsx` — cleaned, reconciled workbook (current source of truth)
- `accounting_tools/` — Python/Node pipeline scripts used to build the reports (normalize, prepare, build_workbook, build_report, claude_pipeline)
- `reports/2026-10-10/` — reconciled financial report package:
  - English + Persian (`fa/`) variants of the report (`.md`, `.pdf`, `.html`), professional workbook, audit evidence zips, transaction CSVs, validation JSONs, and user confirmation records
- `recipts/` — receipt photos backing the recorded transactions
- `invoice-61150.pdf` — domain expense invoice
- `physics_intro full report.pdf` — event report
- `anjoman_accounting_group_export/` — Telegram export of the accounting group (formerly `telegram export/`)

## Progress log

- **2026-10-10** — Reconciled financial report produced from the workbooks and receipts: `reports/2026-10-10/` (English and Persian versions, professional workbook, audit evidence). Declared domain expense and three-month website VM budget recorded.
- **2026-10-12** — Report package merged to `main` via PR #1. Telegram channel export added (`anjoman_channel_content/`, 4,537 files). Three large media files (>50 MB) tracked with **Git LFS**; remaining content pushed in chunked batches after the initial large push timed out.
- **2026-10-13** — Repository restructured: all accounting material consolidated under `anjoman_accounting_information/` (pure moves, history preserved via rename detection). Added two new group exports: the private group report and the public group export (2026-10-13). This README added.

## Notes for collaborators

- Files over 50 MB are stored via **Git LFS** (see `.gitattributes`). Install it (`git lfs install`) before cloning/pulling, or those files will download as pointer stubs.
- Telegram exports are raw HTML exports from Telegram Desktop — open any `messages*.html` in a browser to browse a chat with its media.
- Free GitHub LFS quota used: ~273 MB of 1 GB (bandwidth quota is 1 GB/month).
