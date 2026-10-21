# Repository Reorganization + Persian README — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the repository to a role-based layout (`data/`, `reports/`, `docs/`, `sources/`, `analysis/`, `analysis_tools/`) with every live path updated and frozen outputs proven byte-identical, then replace the root README with a Persian one that indexes the whole repository.

**Architecture:** `analysis_tools/common.py` becomes the single home of all data/report locations; every other module and test imports from it. A new path test is written first and goes RED→GREEN across the moves. Moves use `git mv` (history kept); the three Git-LFS files get their `.gitattributes` patterns updated before they move. Re-running the audit and governance builds must yield renames only — no content changes.

**Tech Stack:** Python 3.11, pytest, git + git-lfs 3.5, existing `analysis_tools` package.

**Spec:** `docs/superpowers/specs/2026-10-21-repo-reorganization-design.md` — read it together with this plan. Note: the spec calls the export map `EXPORTS`; in the code it is named `SOURCES` (`analysis_tools/common.py`). Use the real name.

## Global Constraints

- Run every command from the repository root `C:\Users\Surface Laptop 3\Downloads\Telegram Desktop\anjoman_acc`, on branch `chore/repo-reorganization`. Python is `python` (3.11).
- Tracked files move only with `git mv` (history preserved). Nothing is deleted. Untracked files move with plain `mv`/`cp`.
- Frozen content must not change, byte for byte: everything under `reports/`, `docs/superpowers/` (except the new plan/spec files), `docs/governance/`, `analysis_tools/audit/data/*.json`, `analysis/profiles/*`, `analysis/*.json[l]`.
- Privacy: the GitHub repo is PUBLIC. `sources/governance/` is git-ignored and nothing from it is ever committed. Never commit personal names, phone numbers or handles.
- Baseline before this plan: `python -m pytest analysis_tools/tests -q` → `266 passed, 1 warning` (the warning is the pre-existing pypdf `CryptographyDeprecationWarning`). Lint: `python -m analysis_tools.governance_lint` → `OK: no findings`.
- Every commit message ends with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The README (Task 3) is written in Persian inside `<div dir="rtl">`; paths, commands and code stay in backtick code spans.

---

### Task 1: Role-based layout for tracked files (path test, moves, code, verification)

All moves and their code changes land in ONE commit so that every commit on the branch has a green suite.

**Files:**
- Create: `analysis_tools/tests/test_paths.py`
- Modify: `analysis_tools/common.py:5-17`
- Modify: `analysis_tools/audit/emit.py:43-46`
- Modify: `analysis_tools/audit/load.py:7-11`
- Modify: `analysis_tools/validate.py:4,20`
- Modify: `analysis_tools/parse_exports.py:108,148-149`
- Modify: `analysis_tools/tests/test_audit_accounts.py:3,10`
- Modify: `analysis_tools/tests/test_audit_evidence.py:3,9`
- Modify: `analysis_tools/tests/test_audit_report.py:27-31`
- Modify: `.gitattributes`
- Move (git mv): see Step 5

**Interfaces:**
- Produces (in `analysis_tools.common`): `DATA: Path` (= ROOT/"data"), `REPORTS: Path` (= ROOT/"reports"), `TELEGRAM: Path` (= DATA/"telegram"), `SOURCES: dict[str, Path]` (same keys as today), `LEDGER_CSV: Path` (= REPORTS/"2026-10-10/Transactions.csv"), `LEDGER_DIR: Path`, `MEDIA_DOCX: Path` (= DATA/"documents/گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx"). Task 2 imports `ROOT` and `MEDIA_DOCX`.

- [ ] **Step 1: Write the failing path test**

Create `analysis_tools/tests/test_paths.py`:

```python
# analysis_tools/tests/test_paths.py
"""Every location the pipeline reads or writes exists in the role-based layout."""
from analysis_tools import common


def test_telegram_exports_exist():
    for name, path in common.SOURCES.items():
        assert path.is_dir(), f"{name}: {path}"
        assert path.is_relative_to(common.TELEGRAM), f"{name} is outside data/telegram"


def test_ledger_and_media_inputs_exist():
    assert common.LEDGER_CSV.is_file(), common.LEDGER_CSV
    assert common.LEDGER_DIR == common.LEDGER_CSV.parent
    assert common.MEDIA_DOCX.is_file(), common.MEDIA_DOCX


def test_report_generations_exist():
    for d in ("2026-10-10", "2026-10-14", "2026-10-18"):
        assert (common.REPORTS / d).is_dir(), d


def test_accounting_inputs_exist():
    acc = common.DATA / "accounting"
    assert (acc / "receipts").is_dir()
    assert len(list((acc / "workbooks").glob("*.xlsx"))) == 2
    assert (acc / "documents" / "invoice-61150.pdf").is_file()


def test_old_top_level_folders_are_gone():
    for old in ("anjoman_channel_content", "anjoman_private_group_report",
                "anjoman_public_group_export", "anjoman_summerschool_channel_content",
                "anjoman_accounting_information"):
        assert not (common.ROOT / old).exists(), old
```

- [ ] **Step 2: Run it — RED**

Run: `python -m pytest analysis_tools/tests/test_paths.py -q`
Expected: FAIL (AttributeError: module 'analysis_tools.common' has no attribute 'TELEGRAM' / 'MEDIA_DOCX' / 'REPORTS', and the old folders still exist). Record the output.

- [ ] **Step 3: Point `common.py` at the new layout**

Replace lines 5-17 of `analysis_tools/common.py` (from `ROOT = ...` through `LEDGER_DIR = ...`) with:

```python
ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

# Role-based layout (2026-10-21): raw inputs under data/, published report
# generations under reports/. Every module and test takes locations from here.
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
TELEGRAM = DATA / "telegram"

SOURCES = {
    "private_group":    TELEGRAM / "private_group",
    "public_group":     TELEGRAM / "public_group/ChatExport_2026-10-13",
    "channel":          TELEGRAM / "channel",
    "accounting_group": TELEGRAM / "accounting_group",
    "summerschool_channel": TELEGRAM / "summerschool/ChatExport_2026-10-14",
}
LEDGER_CSV = REPORTS / "2026-10-10/Transactions.csv"
LEDGER_DIR = LEDGER_CSV.parent
MEDIA_DOCX = DATA / "documents/گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx"
```

Run: `python -m pytest analysis_tools/tests/test_paths.py -q` — still FAIL (paths do not exist yet). Expected.

- [ ] **Step 4: Update `.gitattributes` BEFORE moving the LFS files**

The three LFS files are >50 MB; if they move while their patterns still name the old paths, git would see the real content instead of the LFS pointer. Replace the three pattern lines so the file reads:

```
# Large Telegram-export media stored via Git LFS (over 50 MB each)
"data/telegram/channel/files/شباهنگ شماره‌ی 21 (1).pdf" filter=lfs diff=lfs merge=lfs -text
"data/telegram/channel/files/صوت مصاحبه لایه نازک.m4a" filter=lfs diff=lfs merge=lfs -text
"data/telegram/channel/files/وبینارهای_شبانه_Sharif_Frontiers_شب_دهمه.mp3" filter=lfs diff=lfs merge=lfs -text
```

Then: `git add .gitattributes`

- [ ] **Step 5: Move the tracked folders and files with `git mv`**

```bash
mkdir -p data/telegram data/accounting/workbooks data/accounting/documents data/documents
git mv anjoman_channel_content data/telegram/channel
git mv anjoman_private_group_report data/telegram/private_group
git mv anjoman_public_group_export data/telegram/public_group
git mv anjoman_summerschool_channel_content data/telegram/summerschool
git mv anjoman_accounting_information/anjoman_accounting_group_export data/telegram/accounting_group
git mv "anjoman_accounting_information/Anjoman accounting.xlsx" data/accounting/workbooks/
git mv "anjoman_accounting_information/Anjoman accounting - refined.xlsx" data/accounting/workbooks/
git mv anjoman_accounting_information/recipts data/accounting/receipts
git mv anjoman_accounting_information/invoice-61150.pdf data/accounting/documents/
git mv "anjoman_accounting_information/physics_intro full report.pdf" data/accounting/documents/
git mv "گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx" data/documents/
git mv anjoman_accounting_information/reports/2026-10-10 reports/2026-10-10
git mv anjoman_accounting_information/reports/2026-10-18 reports/2026-10-18
git mv anjoman_accounting_information/accounting_tools analysis_tools/accounting_2026_10_10
```

Then confirm the old folder is empty of tracked files and remove any leftover empty directories (only empty ones):

```bash
git ls-files anjoman_accounting_information | wc -l   # expect 0
find anjoman_accounting_information -type d -empty -delete 2>/dev/null; ls anjoman_accounting_information 2>&1   # expect "No such file or directory"
```

If `ls` shows remaining files, STOP and report them (they would be untracked files not in the spec).

- [ ] **Step 6: Verify LFS survived the move**

Run: `git lfs ls-files`
Expected: exactly three lines, all starting `data/telegram/channel/files/`.
Run: `git status --short -- data/telegram/channel/files | grep -v '^R  '`
Expected: no output (every file there is a pure rename; an `RM`/`M` line on a `.pdf/.m4a/.mp3` would mean LFS lost track of it — STOP and report).

- [ ] **Step 7: Route every other module through `common.py`**

`analysis_tools/audit/emit.py` — change line 43 and line 46:

```python
from ..common import REPORTS
```
```python
OUT_DIR = REPORTS / "2026-10-18"
```

(If `ROOT` is used elsewhere in `emit.py`, keep it in the import: `from ..common import REPORTS, ROOT`. Check with `grep -n "ROOT" analysis_tools/audit/emit.py`.)

`analysis_tools/audit/load.py` — replace lines 7-11:

```python
from ..common import LEDGER_CSV, ROOT

DATA = ROOT / "analysis_tools/audit/data"
SOURCE_CSV = LEDGER_CSV
```

`analysis_tools/validate.py` — line 4 and line 20:

```python
from .common import LEDGER_DIR, ROOT, write_json, read_json
```
```python
    checks = read_json(LEDGER_DIR / "final_checks.json")
```

`analysis_tools/parse_exports.py` — line 108 and lines 148-149:

```python
from .common import MEDIA_DOCX, ROOT, SOURCES, write_json, WINDOW_START, WINDOW_END
```
```python
    write_json(ROOT / "analysis/docx_content.json", parse_docx(MEDIA_DOCX))
```

`analysis_tools/tests/test_audit_accounts.py` — line 3 and line 10:

```python
from analysis_tools.common import LEDGER_CSV, ROOT
```
```python
    src = LEDGER_CSV
```

`analysis_tools/tests/test_audit_evidence.py` — line 3 and line 9:

```python
from analysis_tools.common import LEDGER_CSV, ROOT
```
```python
    src = LEDGER_CSV
```

`analysis_tools/tests/test_audit_report.py` — replace `test_readonly_folders_untouched` (lines 27-31). The old version guarded `anjoman_accounting_information/reports/2026-10-14`, a path that never existed, so half of it was a silent no-op; the new version also asserts the folders exist:

```python
def test_readonly_folders_untouched():
    import subprocess
    from analysis_tools.common import REPORTS, ROOT
    for d in ("2026-10-10", "2026-10-14"):
        p = REPORTS / d
        assert p.is_dir(), p
        subprocess.run(["git", "diff", "--quiet", "--", str(p.relative_to(ROOT))],
                       check=True, cwd=ROOT)
```

- [ ] **Step 8: Prove nothing else names the old paths**

Run:
```bash
grep -rn -E "anjoman_(channel|private|public|summerschool|accounting)|recipts|ROOT / \"گزارش" analysis_tools --include=*.py | grep -v "accounting_2026_10_10/"
```
Expected: no output. (The archived pipeline under `analysis_tools/accounting_2026_10_10/` is a frozen record and is not edited here except its README in Task 2.)

- [ ] **Step 9: Run the path test — GREEN, then the full suite and lint**

Run: `python -m pytest analysis_tools/tests/test_paths.py -q` → `5 passed`.
Run: `python -m pytest analysis_tools/tests -q` → `271 passed, 1 warning` (266 + 5 new; only the pypdf warning).
Run: `python -m analysis_tools.governance_lint` → `OK: no findings`.

- [ ] **Step 10: Byte-identical rebuild proof**

The audit build makes no API calls (it reads the committed `analysis_tools/i18n/fa.json`; translation is a separate command that requires an explicit API key). Run both builds over the moved folders:

```bash
python -m analysis_tools.build_audit_report --lang all
python -m analysis_tools.governance_build
git status --short -- reports docs | grep -v '^R  '
```
Expected: no output — under `reports/` and `docs/` git shows only pure renames (`R  old -> new`); any `RM`, ` M`, or `??` line means a rebuild changed or added content. If any report/docs file shows as modified, STOP: run `git diff --stat` on it, report, and do not commit until resolved (`git checkout -- <file>` restores it).

- [ ] **Step 11: Commit**

```bash
git add .gitattributes analysis_tools/common.py analysis_tools/audit/emit.py analysis_tools/audit/load.py   analysis_tools/validate.py analysis_tools/parse_exports.py analysis_tools/tests/test_paths.py   analysis_tools/tests/test_audit_accounts.py analysis_tools/tests/test_audit_evidence.py   analysis_tools/tests/test_audit_report.py
git status --short | grep -v '^??'   # renames + these modifications only; the untracked extraction script and i18n cache stay out until Task 2
git commit -F - <<'EOF'
refactor(repo): role-based layout — data/ and reports/ with central paths

Raw inputs move under data/ (telegram exports, accounting workbooks,
receipts, documents) and every report generation under reports/<date>/;
anjoman_accounting_information/ is dissolved. analysis_tools/common.py is
the single home of all locations (DATA, REPORTS, TELEGRAM, SOURCES,
LEDGER_CSV, MEDIA_DOCX); audit emit/load, validate, parse_exports and the
audit tests import from it. LFS patterns follow the channel export. A new
path test guards the layout; the read-only guard now checks folders that
actually exist. Audit and governance rebuilds are byte-identical.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 2: Local-only governance sources, extraction script, stray cache, archive label

**Files:**
- Modify: `.gitignore`
- Modify: `analysis_tools/extract_governance_sources.py` (rewrite of the path block, lines 1-35)
- Modify: `analysis_tools/accounting_2026_10_10/README.md` (prepend a note)
- Add to git: `analysis_tools/extract_governance_sources.py`, `analysis/claude/i18n/a79d59906fcd40a21fee8dcaeda0585033ecea5c.json`
- Move (untracked, plain mv): the 10 root documents, `analysis/claude/governance_sources/`
- Copy (untracked): `../Asasname.pdf`

**Interfaces:**
- Consumes: `analysis_tools.common.ROOT`, `analysis_tools.common.MEDIA_DOCX` (Task 1).

- [ ] **Step 1: Ignore rules first**

Append to `.gitignore` (keep the existing two lines):

```
.pytest_cache/
# Governance source documents and their text extracts: local only (repo is public)
sources/governance/
```

- [ ] **Step 2: Move the untracked sources into `sources/governance/`**

```bash
mkdir -p sources/governance
mv "اساس‌نامه انجمن علمی فیزیک.pdf" "تیم چای.pdf" "چارچوب چای.pdf" "دستورجلسه 10مهر.pdf" \
   "راهنمای_حقوقی_و_تکالیف_انجمن_علمی_فیزیک_شریف.docx" "سند_چارچوب_عملیاتی_انجمن_علمی_دانشکده_فیزیک.pdf" \
   "گزارش 15 تیر انجمن.pdf" "گزارش برنامه.docx" "مجمع انجمن علمی دانشکده فیزیک.pdf" \
   Kaveh_Sharif_Physics_Proposal_Revised.docx sources/governance/
cp ../Asasname.pdf sources/governance/
mv analysis/claude/governance_sources sources/governance/extracts
ls sources/governance | wc -l     # expect 12 (10 moved + Asasname.pdf + extracts/)
```

If any `mv` reports "No such file", STOP and report (a file name differs from the spec).

- [ ] **Step 3: Point the extraction script at the new home**

Replace everything from the top of `analysis_tools/extract_governance_sources.py` down to (and including) the end of the `SOURCES = [...]` list with:

```python
# -*- coding: utf-8 -*-
"""Extract text from the governance source documents (Persian PDFs/DOCX).

The sources live in sources/governance/ (git-ignored: the repo is public and
some sources carry personal details). Output: sources/governance/extracts/<slug>.txt

Usage: python -m analysis_tools.extract_governance_sources
"""
import sys

from .common import MEDIA_DOCX, ROOT

sys.stdout.reconfigure(encoding="utf-8")

SRC = ROOT / "sources" / "governance"
OUT = SRC / "extracts"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = [
    # (path, ascii slug)
    (SRC / "اساس‌نامه انجمن علمی فیزیک.pdf", "asasname_physics_current"),
    (SRC / "مجمع انجمن علمی دانشکده فیزیک.pdf", "majma_charter"),
    (SRC / "Asasname.pdf", "asasname_resana_reference"),
    (SRC / "سند_چارچوب_عملیاتی_انجمن_علمی_دانشکده_فیزیک.pdf", "operational_framework"),
    (SRC / "راهنمای_حقوقی_و_تکالیف_انجمن_علمی_فیزیک_شریف.docx", "legal_guide"),
    (SRC / "دستورجلسه 10مهر.pdf", "agenda_10mehr"),
    (SRC / "گزارش 15 تیر انجمن.pdf", "report_15tir"),
    (SRC / "تیم چای.pdf", "tea_team"),
    (SRC / "چارچوب چای.pdf", "tea_framework"),
    (SRC / "گزارش برنامه.docx", "program_report"),
    (SRC / "Kaveh_Sharif_Physics_Proposal_Revised.docx", "kaveh_proposal"),
    (MEDIA_DOCX, "media_performance_report"),
]
```

Keep the rest of the file (`pdf_text`, `docx_text`, the loop) unchanged. Its old `import zipfile`, `import pathlib`, `import re` lines are removed only if unused afterwards (check with `grep -n -E "zipfile|pathlib|re\." analysis_tools/extract_governance_sources.py`).

- [ ] **Step 4: Prove the script reproduces the existing extracts**

```bash
SCR="C:/Users/SURFAC~1/AppData/Local/Temp/claude/C--Users-Surface-Laptop-3-Downloads-Telegram-Desktop-anjoman-acc/784be3c5-ba0a-407d-bf7a-f45bf79d9beb/scratchpad/extracts_before"
rm -rf "$SCR"; cp -r sources/governance/extracts "$SCR"
python -m analysis_tools.extract_governance_sources
diff -r -x png -x critiques_digest.txt "$SCR" sources/governance/extracts && echo IDENTICAL
```
Expected: 12 `OK` lines from the script, then `IDENTICAL`. (`png/` and `critiques_digest.txt` were not produced by the script and are left as they are.)

- [ ] **Step 5: Label the archived 2026-10-10 pipeline**

Prepend these two lines (and a blank line) to `analysis_tools/accounting_2026_10_10/README.md`:

```markdown
> **Archived record (moved here 2026-10-21 from `anjoman_accounting_information/accounting_tools/`).** This is the frozen pipeline that produced `reports/2026-10-10/`. It was run in a separate workspace (`ANJOMAN_WORKSPACE`), is not imported by `analysis_tools`, and is not run in place.
```

- [ ] **Step 6: Commit the script, the cache file, the ignore rules and the label**

```bash
git add .gitignore analysis_tools/extract_governance_sources.py analysis_tools/accounting_2026_10_10/README.md analysis/claude/i18n/a79d59906fcd40a21fee8dcaeda0585033ecea5c.json
git status --short          # expect: no "??" lines at all (everything is tracked or ignored)
git check-ignore sources/governance/Asasname.pdf    # prints the path = ignored
python -m pytest analysis_tools/tests -q   # 271 passed, 1 warning
git commit -F - <<'EOF'
chore(repo): local-only governance sources, extraction script, i18n cache

Governance source documents and their text extracts move to
sources/governance/ (git-ignored: the repo is public). The extraction
script reads from there and reproduces the existing extracts exactly. The
stray i18n cache entry is committed like its siblings; the archived
2026-10-10 accounting pipeline is labelled as a record.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

If `git status --short` still shows `??` lines, STOP and report them.

---

### Task 3: Persian root README

**Files:**
- Rewrite: `README.md`

**Interfaces:**
- Consumes: the final layout from Tasks 1–2; `docs/governance/README.md` (governance index and open questions); the current `README.md` (its progress log and collaborator notes are folded in — read it before overwriting).

- [ ] **Step 1: Gather the facts the README states (record the outputs)**

```bash
for d in data/telegram/*/; do echo "$d $(git ls-files "$d" | wc -l)"; done
git ls-files data/accounting/receipts | wc -l
find reports -maxdepth 2 -type d | sort
ls docs/governance/build
ls docs/superpowers/specs docs/superpowers/plans
python -m pytest analysis_tools/tests -q 2>&1 | tail -1
grep -h "^def main\|argparse\|--lang" analysis_tools/build_*.py analysis_tools/charts.py | head -20
```

Date ranges of each Telegram export: take them from `analysis/profiles/*.json` (`first`/`last` or equivalent keys) or the current README; do not invent them.

- [ ] **Step 2: Write `README.md`**

Structure (all prose in Persian, wrapped in `<div dir="rtl">` … `</div>` with a blank line after the opening tag and before the closing tag so GitHub renders the Markdown inside):

1. `# آرشیو و تحلیل انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف` + one introductory paragraph (what the repo holds: accounting records, Telegram archives, analysis pipeline, published reports, governance documents; that it is public).
2. `## فهرست مطالب` — anchor links to every section below.
3. `## نقشه مخزن` — the layout as a code-block tree (the tree from spec §3, current names) with a one-line Persian explanation per folder.
4. `## محصولات منتشرشده` — table with columns «تاریخ | محصول | محل | زبان | وضعیت»: ۲۰۲۶-۱۰-۱۰ گزارش مالی تطبیق‌شده (`reports/2026-10-10/`), ۲۰۲۶-۱۰-۱۴ گزارش‌های تحلیلی مالی ماهانه و عملکرد (`reports/2026-10-14/`), ۲۰۲۶-۱۰-۱۸ گزارش حسابرسی‌شده دفتر کل (`reports/2026-10-18/`), ۲۰۲۶-۱۰-۲۱ مجموعه اسناد حاکمیتی (`docs/governance/`). Under the table, direct links to each main PDF and DOCX (link syntax with angle brackets for paths containing spaces: `[متن](<path with spaces.pdf>)`).
5. `## زنجیره داده‌ها` — a code-block diagram: data/ → analysis/ → reports/, plus the audit branch and the governance build.
6. `## داده‌های خام` — one bullet per `data/telegram/*` export (what it is, date range, tracked file count) and per `data/accounting/*` subfolder; mention the three Git-LFS media files.
7. `## ابزارها` — index of `analysis_tools/` modules: parse/classify/correlate/ecosystem/charts/report builders, `audit/` pipeline (load → rules → apply → balance/bridge → emit), `governance_lint.py`/`governance_build.py`, `i18n/`, `extract_governance_sources.py`, and `accounting_2026_10_10/` (archived record).
8. `## بازسازی و آزمون` — the exact commands (tests, lint, governance build, audit build `--lang all`, 2026-10-14 builders with `--lang fa`, re-translation command with the key read from the local key file), and the current test count from Step 1.
9. `## اصول کار` — frozen generations (never edited; new work = new dated folder; enforced by `test_readonly_folders_untouched`), byte-reproducible builds, privacy (public repo; PII gate; `sources/governance/` local-only; no names/phones/handles), and the progress log from the old README condensed into a dated list (with paths updated to the new layout).
10. `## جدول تطبیق مسیرها` — table «مسیر قدیم | مسیر جدید» with every row of spec §3 that changed, plus a sentence explaining that citations inside frozen reports (e.g. `recipts/…`, `anjoman_accounting_group_export/files/…`) use the old paths and are resolved through this table.
11. `## اسناد طراحی` — table of every file in `docs/superpowers/specs/` and `docs/superpowers/plans/` with date and one-line Persian subject.
12. `## وضعیت و کارهای باز` — governance: ratification decisions (amendment feasibility; confirm 5-of-7 دبیر replacement and 14-day handover; the open questions list in `docs/governance/README.md`); known minor gaps (compound تبصره citations unchecked by the lint; summer چای vs semester permit; second-call reminder for extraordinary sessions; signer chain beyond نائب دبیر). Audit: point to the open-items file in `reports/2026-10-18/` (find its name with `ls reports/2026-10-18`).

Writing rules: Persian digits in prose; Latin digits stay inside code spans; ZWNJ where standard; no English sentences except inside code spans and proper names; every number in the README comes from Step 1 output or an existing document.

- [ ] **Step 3: Verify every path and link in the README**

```bash
python - <<'EOF'
import pathlib, re, sys
t = pathlib.Path("README.md").read_text(encoding="utf-8")
cands = set(re.findall(r"\]\(<([^>]+)>\)", t)) | set(re.findall(r"\]\(([^)<\s#]+)\)", t))
cands |= {c for c in re.findall(r"`([^`\n]+)`", t) if "/" in c and " " not in c.strip("/")}
bad = []
for c in sorted(cands):
    if c.startswith(("http", "#", "python", "git ", "ANTHROPIC")) or c.startswith("sources/governance"):
        continue
    p = c.split("#")[0].rstrip("/")
    if "…" in p or "*" in p or "<" in p:
        continue
    if not pathlib.Path(p).exists():
        bad.append(c)
print("\n".join(bad) or "ALL PATHS RESOLVE")
sys.exit(1 if bad else 0)
EOF
grep -c 'dir="rtl"' README.md    # expect 1
```
Expected: `ALL PATHS RESOLVE`. Fix any listed path before continuing. (`sources/governance/` is local-only and intentionally skipped.)

- [ ] **Step 4: Full checks and commit**

```bash
python -m pytest analysis_tools/tests -q        # 271 passed, 1 warning
python -m analysis_tools.governance_lint        # OK: no findings
git add README.md
git commit -F - <<'EOF'
docs(readme): Persian root README — map, products, data flow, tools, path concordance

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

## Self-Review (completed during planning)

- **Spec coverage:** §3 moves → Task 1 Step 5 (tracked) + Task 2 Step 2 (untracked); §4 code → Task 1 Steps 3, 7 and Task 2 Steps 3, 5; §4 `.gitattributes` → Task 1 Step 4; §5 verification 1–5 → Task 1 Steps 1-2, 5-6, 9-10; §2.3 frozen records → Global Constraints + Task 1 Step 10; §6 README → Task 3; `.gitignore` → Task 2 Step 1; i18n cache → Task 2 Step 6.
- **Placeholders:** none; every code change is given in full; README prose is specified by section with its facts sourced from Step 1.
- **Name consistency:** `DATA`, `REPORTS`, `TELEGRAM`, `SOURCES`, `LEDGER_CSV`, `LEDGER_DIR`, `MEDIA_DOCX` are defined in Task 1 Step 3 and used with the same names in Task 1 Step 7, Task 2 Step 3 and the tests.
