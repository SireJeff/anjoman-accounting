# Repository Reorganization + Persian README — Design Spec

**Date:** 2026-10-21 · **Status:** Approved in chat (layout, code/verification, README outline); spec pending user review
**Branch:** `chore/repo-reorganization`

## 1. Goal

Turn the repository from "raw exports, tools, reports and loose documents side by side at the top level" into a role-based layout, without changing any frozen output, and then replace the stale English root README with a Persian one that indexes and explains the whole repository as it now stands.

## 2. Decisions (user-approved)

1. **Scope: group by role** — top level = `data/`, `reports/`, `docs/`, `sources/`, `analysis/`, `analysis_tools/`. The Python package keeps the name `analysis_tools` (no import churn).
2. **Privacy:** the GitHub repo stays **public**. Governance source documents and their text extracts live in `sources/governance/` and are **git-ignored** (local only). No new personal details are committed. Already-tracked files keep their current tracked status (they are already public; this work does not rewrite history).
3. **Frozen records are moved, never edited:** report packages keep byte-identical contents; `docs/superpowers/` specs and plans keep their historical text even where it names old paths; the audit's evidence citations (paths inside `analysis_tools/audit/data/*.json` and `analysis/profiles/ledger.json`, quoted verbatim in the 2026-10-18 report) are not rewritten — the README carries an old→new path concordance instead.

## 3. Target layout and complete move list

| Old path | New path | Tracked? |
|---|---|---|
| `anjoman_channel_content/` | `data/telegram/channel/` | yes (incl. 3 LFS files) |
| `anjoman_private_group_report/` | `data/telegram/private_group/` | yes |
| `anjoman_public_group_export/` | `data/telegram/public_group/` (keeps inner `ChatExport_2026-10-13/`) | yes |
| `anjoman_summerschool_channel_content/` | `data/telegram/summerschool/` (keeps inner `ChatExport_2026-10-14/`) | yes |
| `anjoman_accounting_information/anjoman_accounting_group_export/` | `data/telegram/accounting_group/` | yes |
| `anjoman_accounting_information/Anjoman accounting.xlsx`, `… - refined.xlsx` | `data/accounting/workbooks/` | yes |
| `anjoman_accounting_information/recipts/` | `data/accounting/receipts/` | yes |
| `anjoman_accounting_information/invoice-61150.pdf`, `physics_intro full report.pdf` | `data/accounting/documents/` | yes |
| `گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx` (root, tracked, pipeline input) | `data/documents/` | yes |
| `anjoman_accounting_information/reports/2026-10-10/` | `reports/2026-10-10/` | yes |
| `anjoman_accounting_information/reports/2026-10-18/` | `reports/2026-10-18/` | yes |
| `reports/2026-10-14/` | (stays) | yes |
| `anjoman_accounting_information/accounting_tools/` | `analysis_tools/accounting_2026_10_10/` (archived; not imported, not run in place — it ran in a separate workspace) | yes |
| 10 untracked root documents (9 Persian governance sources + `Kaveh_Sharif_Physics_Proposal_Revised.docx`) | `sources/governance/` | **ignored** |
| `../Asasname.pdf` (Resana constitution, outside the repo) | copied to `sources/governance/` | **ignored** |
| `analysis/claude/governance_sources/` (untracked extracts + PNGs) | `sources/governance/extracts/` | **ignored** |
| `analysis_tools/extract_governance_sources.py` (untracked) | stays; paths updated; **committed** | yes |
| `analysis/claude/i18n/a79d59906fcd40a21fee8dcaeda0585033ecea5c.json` (untracked cache) | stays; **committed** like its siblings | yes |
| `docs/governance/`, `docs/superpowers/`, `analysis/`, `analysis_tools/` | (stay) | yes |

`anjoman_accounting_information/` ceases to exist. `.gitignore` gains `sources/governance/` and `.pytest_cache/`.

## 4. Code changes (live paths only)

- `analysis_tools/common.py` is the single home for locations: add `DATA = ROOT / "data"`, `REPORTS = ROOT / "reports"`; `EXPORTS` and `LEDGER_CSV` point to the new locations.
- `analysis_tools/audit/emit.py` (`OUT_DIR` → `reports/2026-10-18`), `analysis_tools/audit/load.py` (`SOURCE_CSV` → `common.LEDGER_CSV`), `analysis_tools/validate.py` (`final_checks.json` under `reports/2026-10-10`), `analysis_tools/parse_exports.py` (docx under `data/documents/`) import their locations from `common.py` instead of hard-coding them.
- `analysis_tools/tests/test_audit_accounts.py`, `test_audit_evidence.py`, `test_audit_report.py`: same.
- `analysis_tools/extract_governance_sources.py`: inputs from `sources/governance/`, outputs to `sources/governance/extracts/`.
- `.gitattributes`: the three LFS patterns move to `data/telegram/channel/files/…`.
- `analysis_tools/accounting_2026_10_10/README.md` gets a one-line note that this is the archived 2026-10-10 pipeline, run in a separate workspace.

## 5. Verification

1. **Test first:** a new test asserts that every location defined in `common.py` (each `EXPORTS` entry, `LEDGER_CSV`, the media docx, the three report folders) exists. It is written and run RED against the new constants before any move.
2. Moves via `git mv` (history preserved); the test turns GREEN.
3. Full suite green (baseline 266 passed + the new test; only the pre-existing pypdf warning); `python -m analysis_tools.governance_lint` → OK.
4. **Byte-identical rebuilds:** re-run the governance build and the 2026-10-18 audit build (only if fully cache-backed — any build that could make a live API call is skipped and reported); `git status` must show renames only, no content modifications under `reports/` and `docs/`.
5. The three LFS files are still LFS pointers after the move (`git lfs ls-files`).

## 6. Persian README

`README.md` is rewritten in Persian inside `<div dir="rtl">` (paths, commands and code in LTR code spans). Sections, in order:

1. عنوان و معرفی
2. فهرست مطالب (anchor links)
3. نقشه مخزن (the §3 layout as a tree with one-line explanations)
4. محصولات منتشرشده — table of the four generations (۲۰۲۶-۱۰-۱۰ reconciled financial report; ۲۰۲۶-۱۰-۱۴ analytical reports; ۲۰۲۶-۱۰-۱۸ audited report; ۲۰۲۶-۱۰-۲۱ governance suite): what, where, languages, status, direct links to PDF/DOCX
5. زنجیره داده‌ها (raw data → analysis → reports diagram)
6. داده‌های خام (each export and accounting input: contents, date range)
7. ابزارها (index of `analysis_tools/` modules incl. audit pipeline, governance lint/build, i18n, archived 2026-10-10 pipeline)
8. بازسازی و آزمون (exact commands)
9. اصول کار (frozen reports + dated folders, byte-reproducible builds, privacy rule)
10. جدول تطبیق مسیرها (old → new, for citations inside frozen reports)
11. اسناد طراحی (index of `docs/superpowers/` specs and plans)
12. وضعیت و کارهای باز (governance ratification decisions, known minor gaps)

Content from the current English README (progress log, collaborator notes) is folded into §4 and §9. Every fact stated in the README is checked against the repository (counts, dates, file names, commands run).

## 7. Out of scope

Renaming the `analysis_tools` package; rewriting git history; changing any report, spec, plan or audit-data content; making the repo private.
