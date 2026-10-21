> **Archived record (moved here 2026-10-21 from `anjoman_accounting_information/accounting_tools/`).** This is the frozen pipeline that produced `reports/2026-10-10/`. It was run in a separate workspace (`ANJOMAN_WORKSPACE`), is not imported by `analysis_tools`, and is not run in place.

# Accounting evidence workflow

The report is a reconstructed cash-activity report, not an audit or a complete accrual balance sheet. The workbook retains Persian descriptions and the original evidence. Review items are excluded from supported totals. Original-ledger-only records remain included with an explicit evidence label; they are not bank-confirmed. The 10–11 October user confirmation establishes all recipts/ items as association expenses. Five Summer School 1405 instructor payments and intro-event sticker packs are specifically allocated; a sixth instructor payment remains unmatched. Provisional screens and the photographed invoice remain explicitly user-attested.

## Final outputs

`reports/2026-10-10/` contains the professional workbook, detailed PDF/Markdown report, canonical JSON ledger, CSV, source inventory, validation and extraction audit package. The root refined workbook is replaced; its predecessor is preserved in `source_snapshots/`. Original financial evidence remains untouched.

## Models and credentials

Extraction/context: Claude Sonnet 5.5 (`claude-sonnet-5-5`). Independent scan review, reconciliation and final review: Claude Opus 5.5 (`claude-opus-5-5`). API access was verified during preparation. Credentials are never stored here. Set `ANTHROPIC_API_KEY` in the environment. Calls are billable; cached extraction JSON prevents duplicate calls. Model availability should be checked before later runs.

## Reproduction

Python dependencies: lxml, pypdf, reportlab. Workbook authoring uses Node `@oai/artifact-tool`. Runtime/library versions affect visual output. Scripts resolve the repository root as the parent of `accounting_tools/`; the workbook also accepts `ANJOMAN_WORKSPACE`.

1. Create `sources/` and `analysis/claude/`. Stage the source files listed in the pinned manifest from the original commit; for the original refined workbook use the archived predecessor, not the replacement. This staging is important to avoid analyzing the revised report as source evidence.
2. Copy the saved manifest/inventory and audit-package extraction JSON to `analysis/` and `analysis/claude/` respectively. Copy `final_data.json` to `analysis/claude/reconciled.json`, then run `python accounting_tools/normalize.py`.
3. Run `node accounting_tools/build_workbook.mjs`; run `python accounting_tools/build_report.py` after restoring `report_narrative.json` from the audit package.
4. For new evidence, parse messages/workbooks with `prepare.py`, then run `claude_pipeline.py context`, `extract`, `scan`, `scan_review`, and `reconcile`. Large reconciliation responses must be partitioned to avoid output truncation; do not accept incomplete JSON. Resolve proposed corrections against the evidence before producing final outputs.

Formula-linked monthly/project/category schedules recalculate when current transactions are edited. When appending new rows, extend the bounded formula ranges or regenerate the workbook. Original formula text is retained as text, including defects, for traceability.

## Remaining gaps

Five unavailable-media notices were present in the Telegram export. No complete bank statements or verified opening association cash were supplied. The custodian has mixed personal and association funds. The report lists the documentation required to resolve outstanding transactions, invoices and settlement differences. Do not substitute the net activity figure for closing cash.

## Website addendum (11 October 2026)

TX0096 records the user-declared 3,000,000 toman alenush.com purchase under Review. Purchase date, funding source and reimbursement are not supplied; supported cutoff cash totals are unchanged. The Website budget tab models the 92-day VM period 1405/05/28 to 1405/08/28 at 655,440 rial/day (65,544 toman/day). The VM forecast is 6,030,048 toman; domain plus VM budget is 9,030,048 toman, not an actual paid total. Restore website_user_confirmation_2026-10-11.json and use the current final_data.json (including website_budget) when reproducing outputs. Daily-rate changes and missing-rate inputs were checked.
