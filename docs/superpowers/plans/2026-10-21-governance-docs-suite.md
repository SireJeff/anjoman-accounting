# Governance Documents Suite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Draft the four Persian governance documents (اساسنامه، شیوه‌نامه شورا، منشور مجمع، شیوه‌نامه مجمع) as markdown masters and build editable DOCX + deterministic PDF outputs from them.

**Architecture:** Markdown masters in `docs/governance/` are the single source of truth. A lint module enforces the spec's content canon (banned phrases, numbering, citations, cross-references, canonical tea text) as executable gates; a build module renders masters to PDF via the existing tested RTL pipeline (`analysis_tools/report_common.py`) and to DOCX via a new python-docx RTL writer. Drafting tasks run the linter as their test cycle.

**Tech Stack:** Python 3.11, python-docx, reportlab/pypdf (already in repo), pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-21-governance-docs-design.md` — the plan argues from it; executors read **both**. Spec section references below are to that file.

## Global Constraints

- **Language:** All four documents are in Persian. Masters are markdown, UTF-8, LF line endings.
- **Banned phrases** (spec §3): «مجمع عمومی», «پرتفوی», «ضرفضا», «ماده‌گونه», «هم‌آماده‌سازی» — none may appear in any master.
- **Terminology canon** (spec §3): «جلسه عمومی» (سالانه/فوق‌العاده) never «مجمع عمومی»؛ «حوزه» not «پرتفوی»؛ named bodies exactly «کمیته انتخابات», «رابط مجمع», «استاد مشاور», «کارگروه پشتیبانی و نظارت»؛ voting formulas «بیش از نیمی از حاضران» or «رأی X از کل ۷ نفر» (never bare «اکثریت حاضران»).
- **Citation rule** (spec §3): every parenthetical citing مواد/تبصره/فصل must carry a qualifier («آیین‌نامه، ماده …» / «اساسنامه، ماده …» / «شیوه‌نامه … فصل …»). Bare numeric refs like «(۳-۱۱)» (internal بند refs) are allowed.
- **Roles not persons** (spec §1): no current-member names in normative text.
- **Markdown subset for masters:** `#` title, `##` بخش/فصل, `###` sub-units, paragraphs, `-` bullets, `**bold**`. **No tables, no images, no code fences** in masters (keeps DOCX writer simple; tabular content is written as bullet lists).
- **Version headers:** every master starts with a one-line version block: `نسخه ۱٫۰ — پیش‌نویس` plus fields «تاریخ تصویب: —» / «تاریخ تأیید: —» (left blank for the ratifying bodies; D1 also «جلسه عمومی: —»).
- **Drafting order:** D1 → D2 → D3 → D4 → cross-doc pass → build (spec §9).
- **Test command** (from repo root): `python -m pytest analysis_tools/tests/test_governance_lint.py -v` (etc.). Python 3.11 via `python`.
- **Source extracts** (read-only inputs) live in `analysis/claude/governance_sources/*.txt`; `operational_framework.txt` and `agenda_10mehr.txt` are FONT-BROKEN — never read them; their substance is inlined in spec §1/§4-§7 context and the CTX of the design workflow.

---

### Task 1: Lint harness — content gates as code (TDD)

**Files:**
- Create: `analysis_tools/governance_lint.py`
- Test: `analysis_tools/tests/test_governance_lint.py`

**Interfaces:**
- Consumes: nothing (pure functions over text).
- Produces (later tasks call these):
  - `normalize_fa(text: str) -> str` — lam-alef artifact fix + digit/whitespace normalization
  - `FA_DIGITS: dict`, `to_en_digits(s: str) -> str`
  - `findings_for(doc_key: str, text: str) -> list[str]` — all checks for one document; doc_key in {"D1","D2","D3","D4"}; returns human-readable violation strings (empty = pass)
  - `cross_doc_findings(texts: dict[str, str]) -> list[str]` — cross-document checks (D1 ماده count vs references, tea canon across D3)
  - `BANNED: list[str]`, `D1_MADDI_COUNT = 39`

- [ ] **Step 1: Write failing tests**

Create `analysis_tools/tests/test_governance_lint.py`:

```python
# -*- coding: utf-8 -*-
"""Content gates for the governance masters (spec §3 canon)."""
from analysis_tools.governance_lint import (
    normalize_fa, to_en_digits, findings_for, cross_doc_findings,
    D1_MADDI_COUNT,
)

D1_MIN = """# اساسنامه انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف

نسخه ۱٫۰ — پیش‌نویس | تاریخ تصویب: — | تاریخ تأیید: —

## بخش اول: کلیات و تعاریف

ماده ۱ (نام و قلمرو): نام تشکل «انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف» است.

ماده ۲ (تعاریف): در این اساسنامه، «جلسه عمومی» یعنی جلسه قانونی مجمع.
"""


def test_to_en_digits():
    assert to_en_digits("ماده ۱۲ و ۳") == "ماده 12 و 3"


def test_normalize_fa_fixes_lam_alef_artifacts():
    # PyMuPDF extractions render لا as «ال» mid-word (اطلاعات -> اطالعات)
    assert normalize_fa("اطالعات و اعالم و الزم") == "اطلاعات و اعلام و لازم"
    # word-initial definite article must survive untouched
    assert normalize_fa("الحاق") == "الحاق"


def test_banned_phrases_flagged():
    text = D1_MIN + "\nماده ۳ (تست): جلسه مجمع عمومی برگزار می‌شود و پرتفوی‌ها تقسیم می‌شود.\n"
    out = findings_for("D1", text)
    assert any("مجمع عمومی" in f for f in out)
    assert any("پرتفوی" in f for f in out)


def test_d1_maddi_continuity():
    # D1_MIN has مواد 1..2 only -> must flag missing 3..39
    out = findings_for("D1", D1_MIN)
    assert any("ماده" in f and "3" in f for f in out)
    # duplicate ماده flagged
    dup = D1_MIN + "\nماده ۲ (دوباره): تکراری است.\n"
    out = findings_for("D1", dup)
    assert any("تکرار" in f or "duplicate" in f for f in out)


def test_citation_rule():
    bad = D1_MIN + "\nماده ۳ (الف): مطابق (ماده ۱۶) عمل می‌شود.\n"
    out = findings_for("D1", bad)
    assert any("ارجاع" in f for f in out)
    ok = D1_MIN + "\nماده ۳ (الف): مطابق (آیین‌نامه، ماده ۱۶) و بند (۳-۱۱) عمل می‌شود.\n"
    out = findings_for("D1", ok)
    assert not any("ارجاع" in f for f in out)


def test_majority_formula():
    bad = D1_MIN + "\nماده ۳ (الف): مصوبات با اکثریت حاضران تصویب می‌شود.\n"
    out = findings_for("D1", bad)
    assert any("اکثریت حاضران" in f for f in out)


def test_d1_invariants_present():
    out = findings_for("D1", D1_MIN)  # missing window, member floor, council size
    assert any("اردیبهشت" in f for f in out)
    assert any("بیست" in f or "۲۰" in f for f in out)
    assert any("هفت" in f for f in out)


def test_block_numbering_d2():
    bad = """# شیوه‌نامه داخلی شورای مرکزی

## فصل ۱ — ترکیب، نقش‌ها و حوزه‌ها

۱-۱. ترکیب.

۱-۳. پرش باعث خطا شود.
"""
    out = findings_for("D2", bad)
    assert any("۱-۲" in f or "1-2" in f for f in out)


def test_fasl_structure_d3_d4():
    bad = """# منشور مجمع

## فصل ۱: هویت

۱-۱. مجمع چیست.
"""
    out = findings_for("D3", bad)  # D3 needs 9 فصل + دیباچه
    assert any("فصل" in f for f in out)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_governance_lint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'analysis_tools.governance_lint'`

- [ ] **Step 3: Implement `analysis_tools/governance_lint.py`**

```python
# -*- coding: utf-8 -*-
"""Content gates for the governance masters.

Enforces the canon of spec §3 plus per-document structure (spec §4–§7).
Pure functions over text so tests need no files on disk; the integration
entry point is run_all() which reads the masters.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOV = ROOT / "docs" / "governance"

MASTER_FILES = {
    "D1": GOV / "asasname.md",
    "D2": GOV / "shora-shivename.md",
    "D3": GOV / "majma-manshoor.md",
    "D4": GOV / "majma-shivename.md",
}

D1_MADDI_COUNT = 39
D2_FASL_COUNT = 7   # فصل ۱..۷ (پیش‌درآمد is ۰)
D3_FASL_COUNT = 9
D4_FASL_COUNT = 8

BANNED = ["مجمع عمومی", "پرتفوی", "ضرفضا", "ماده‌گونه", "هم‌آماده‌سازی"]

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_EN = "0123456789"
_TRANS = str.maketrans(FA_DIGITS, _EN)


def to_en_digits(s: str) -> str:
    return s.translate(_TRANS)


def normalize_fa(text: str) -> str:
    """Fix PyMuPDF lam-alef extraction artifacts.

    Extractions render Persian لا as «ال» mid-word (اطلاعات -> اطالعات).
    Rule: inside a word (previous char is an Arabic-script letter), swap
    the sequence alef+lam to lam+alef. Word-initial alef+lam (definite
    article, e.g. «الحاق») is left untouched.
    """
    letters = set("ابجدهوزحطيكلمنسعفصقرشتثخذضظغءأةؤپچژکگی")
    out, i = [], 0
    while i < len(text):
        if (text[i] == "ا" and i + 1 < len(text) and text[i + 1] == "ل"
                and i > 0 and text[i - 1] in letters):
            out.append("لا")
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)
```

Then the checks:

```python
def _maddi_numbers(text: str) -> list[int]:
    return [int(n) for n in re.findall(r"^\s*ماده\s+(\d+)", to_en_digits(text), re.M)]


def _block_numbers(text: str) -> dict[int, list[int]]:
    """Map fasl-number -> ordered block numbers from 'N-M.' items."""
    blocks: dict[int, list[int]] = {}
    for fasl, blk in re.findall(r"^([\u06f0-\u06f9]+)-([\u06f0-\u06f9]+)\.", text, re.M):
        blocks.setdefault(int(to_en_digits(fasl)), []).append(int(to_en_digits(blk)))
    return blocks


def findings_for(doc_key: str, text: str) -> list[str]:
    out: list[str] = []
    norm = normalize_fa(text)
    for b in BANNED:
        if b in norm:
            out.append(f"عبارت ممنوع: «{b}»")
    # citation rule: parentheticals naming ماده/تبصره need a source qualifier
    for m in re.finditer(r"\(([^)]*)\)", norm):
        inner = m.group(1)
        if re.search(r"ماده|تبصره|فصل", inner) and not re.search(
                r"آیین‌نامه|اساسنامه|شیوه‌نامه|منشور", inner):
            out.append(f"ارجاع بدون قید منبع: «({inner})» — قالب درست: (آیین‌نامه، ماده …) یا (اساسنامه، ماده …)")
    if re.search(r"اکثریت\s+حاضران", norm) and "اکثریت مطلق اعضای حاضر" not in norm:
        out.append("قالب رأی: به‌جای «اکثریت حاضران» از «بیش از نیمی از حاضران» یا «رأی X از کل ۷ نفر» استفاده شود")
    if doc_key == "D1":
        nums = _maddi_numbers(norm)
        seen = set()
        for n in nums:
            if n in seen:
                out.append(f"ماده {n} تکرار شده است")
            seen.add(n)
        missing = [n for n in range(1, D1_MADDI_COUNT + 1) if n not in seen]
        if missing:
            out.append(f"مواد غایب: {missing}")
        for needle, label in [("اردیبهشت", "بازه انتخابات (۱۰ اردیبهشت تا ۱۰ خرداد)"),
                              ("بیست", "حداقل ۲۰ عضو"), ("هفت", "ترکیب ۷ نفره شورا")]:
            if needle not in norm:
                out.append(f"ناکافی/غایب: {label}")
    else:
        expected = {"D2": D2_FASL_COUNT, "D3": D3_FASL_COUNT, "D4": D4_FASL_COUNT}[doc_key]
        fasls = sorted(set(int(to_en_digits(f)) for f in re.findall(r"^## فصل ([\u06f0-\u06f9]+)", text, re.M)))
        miss = [n for n in range(1, expected + 1) if n not in fasls]
        if miss:
            out.append(f"فصل‌های غایب: {miss}")
        for fasl, blocks in _block_numbers(norm).items():
            for i in range(1, max(blocks) + 1):
                if i not in blocks:
                    out.append(f"بند {fasl}-{i} غایب (پرش شماره در فصل {fasl})")
    return out


# Canonical tea-framework sentences that must survive verbatim inside D3's
# پیوست (chosen to avoid mid-word line breaks in the PDF extraction).
TEA_CANON = [
    "زمان جلسه متعلق به همه است",
    "کسانی که کمتر صحبت کرده",
    "جمعی را از بین می",
    "چای محلی برای تخریب اعتبار افراد",
    "شنیده شدن نقد به معنای تأیید آن نیست",
]


def cross_doc_findings(texts: dict[str, str]) -> list[str]:
    out: list[str] = []
    d1 = normalize_fa(texts.get("D1", ""))
    d1_nums = set(_maddi_numbers(d1))
    for key, text in texts.items():
        if key == "D1":
            continue
        norm = normalize_fa(text)
        for m in re.finditer(r"ماده\s+(\d+)(?:\s+تا\s+(\d+))?\s+اساسنامه", to_en_digits(norm)):
            lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
            for n in range(lo, hi + 1):
                if n not in d1_nums:
                    out.append(f"{key}: ارجاع به ماده {n} اساسنامه که وجود ندارد")
    d3 = normalize_fa(texts.get("D3", ""))
    for sent in TEA_CANON:
        if sent not in d3:
            out.append(f"D3: جمله قالبی چارچوب چای غایب/تغییر یافته: «{sent}»")
    return out


def run_all() -> list[str]:
    texts = {k: p.read_text(encoding="utf-8") for k, p in MASTER_FILES.items() if p.exists()}
    out: list[str] = []
    for k, t in texts.items():
        out += [f"[{k}] {f}" for f in findings_for(k, t)]
    if len(texts) == len(MASTER_FILES):
        out += [f"[X] {f}" for f in cross_doc_findings(texts)]
    return out


if __name__ == "__main__":
    problems = run_all()
    print("\n".join(problems) if problems else "OK: no findings")
    raise SystemExit(1 if problems else 0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_governance_lint.py -v`
Expected: all PASS. (If `test_normalize_fa_fixes_lam_alef_artifacts` fails, tune the letters set — «پ چ ژ ک گ ی» and ZWNJ must be members; verify «اطالعات»→«اطلاعات», «الزام»-type words are NOT mangled because their لام-الف is genuinely ordered — only swap when the pair follows an Arabic letter.)

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/governance_lint.py analysis_tools/tests/test_governance_lint.py
git commit -m "feat(governance): lint harness — canon gates as executable checks"
```

---

### Task 2: Build pipeline — RTL DOCX + PDF from masters (TDD)

**Files:**
- Create: `analysis_tools/governance_build.py`
- Test: `analysis_tools/tests/test_governance_build.py`

**Interfaces:**
- Consumes: `analysis_tools.report_common.md_to_pdf_rtl(md_path, pdf_path, title, footer)` (existing, tested).
- Produces:
  - `md_to_docx_rtl(md_text: str, title: str) -> docx.document.Document`
  - `_rezip_deterministic(path: Path) -> None` (fixed zip timestamps)
  - `build_all(out_dir: Path | None = None) -> list[Path]` — builds every master in `governance_lint.MASTER_FILES` to `<name>.docx` + `<name>.pdf`
  - CLI: `python -m analysis_tools.governance_build`

- [ ] **Step 1: Write failing tests**

Create `analysis_tools/tests/test_governance_build.py`:

```python
# -*- coding: utf-8 -*-
import io
import zipfile
from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfReader

from analysis_tools.governance_build import md_to_docx_rtl, build_all

MD = """# اساسنامه آزمون

## بخش اول

ماده ۱ (تست): این یک **پاراگراف آزمون** است.

- بند اول
- بند دوم
"""


def test_docx_rtl_and_font(tmp_path):
    doc = md_to_docx_rtl(MD, title="آزمون")
    out = tmp_path / "t.docx"
    doc.save(str(out))
    xml = out.read_bytes().decode("utf-8", "ignore")
    assert "<w:bidi/>" in xml                     # RTL paragraphs
    assert "Tahoma" in xml                        # Persian-capable font
    d2 = Document(str(out))
    joined = "\n".join(p.text for p in d2.paragraphs)
    assert "پاراگراف آزمون" in joined
    assert "بند اول" in joined


def test_pdf_build(tmp_path):
    md = tmp_path / "m.md"
    md.write_text(MD, encoding="utf-8")
    from analysis_tools.report_common import md_to_pdf_rtl
    pdf = tmp_path / "m.pdf"
    md_to_pdf_rtl(md, str(pdf), title="آزمون", footer="آزمون")
    assert len(PdfReader(str(pdf)).pages) >= 1


def test_build_all_smoke(tmp_path, monkeypatch):
    from analysis_tools import governance_lint as gl
    # point MASTER_FILES at a temp master so we do not need D1..D4 yet
    fake = tmp_path / "x.md"
    fake.write_text(MD, encoding="utf-8")
    monkeypatch.setattr(gl, "MASTER_FILES", {"D1": fake})
    outs = build_all(tmp_path / "build")
    assert (tmp_path / "build" / "x.docx").exists()
    assert (tmp_path / "build" / "x.pdf").exists()
    assert len(outs) == 2


def test_docx_deterministic(tmp_path):
    doc = md_to_docx_rtl(MD, title="آزمون")
    a, b = tmp_path / "a.docx", tmp_path / "b.docx"
    doc.save(str(a)); doc.save(str(b))
    from analysis_tools.governance_build import _rezip_deterministic
    _rezip_deterministic(a); _rezip_deterministic(b)
    assert a.read_bytes() == b.read_bytes()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_governance_build.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'analysis_tools.governance_build'`

- [ ] **Step 3: Implement `analysis_tools/governance_build.py`**

```python
# -*- coding: utf-8 -*-
"""Render governance markdown masters to RTL DOCX (+ PDF via report_common)."""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt

from . import governance_lint as gl
from .report_common import md_to_pdf_rtl

FONT = "Tahoma"


def _rtl_paragraph(p):
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pPr = p._p.get_or_add_pPr()
    pPr.append(OxmlElement("w:bidi"))
    return p


def _rtl_run(r, bold=False, size=None):
    r.font.name = FONT
    r.bold = bold
    if size:
        r.font.size = Pt(size)
    rPr = r._r.get_or_add_rPr()
    rPr.append(OxmlElement("w:rtl"))
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:cs"), FONT)
    return r


_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _add_rich(p, text, bold=False, size=None):
    pos = 0
    for m in _BOLD.finditer(text):
        if m.start() > pos:
            _rtl_run(p.add_run(text[pos:m.start()]), bold=bold, size=size)
        _rtl_run(p.add_run(m.group(1)), bold=True, size=size)
        pos = m.end()
    if pos < len(text):
        _rtl_run(p.add_run(text[pos:]), bold=bold, size=size)


def md_to_docx_rtl(md_text: str, title: str) -> Document:
    doc = Document()
    for line in md_text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# ") and not s.startswith("## "):
            p = _rtl_paragraph(doc.add_paragraph())
            _add_rich(p, s[2:], bold=True, size=16)
        elif s.startswith("## "):
            p = _rtl_paragraph(doc.add_paragraph())
            _add_rich(p, s[3:], bold=True, size=13)
        elif s.startswith("### "):
            p = _rtl_paragraph(doc.add_paragraph())
            _add_rich(p, s[4:], bold=True, size=12)
        elif s.startswith("- "):
            p = _rtl_paragraph(doc.add_paragraph())
            _rtl_run(p.add_run("•  "))
            _add_rich(p, s[2:])
        else:
            p = _rtl_paragraph(doc.add_paragraph())
            _add_rich(p, s)
    return doc


def _rezip_deterministic(path: Path) -> None:
    """Rewrite the docx zip with fixed entry timestamps -> byte-stable output."""
    fixed = (1980, 1, 1, 0, 0, 0)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "rezip.docx"
        with zipfile.ZipFile(path) as zin, \
             zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                info.date_time = fixed
                zout.writestr(info, data)
        shutil.move(str(tmp), str(path))


def build_all(out_dir: Path | None = None) -> list[Path]:
    out = Path(out_dir) if out_dir else gl.GOV / "build"
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for key, md in gl.MASTER_FILES.items():
        if not md.exists():
            print(f"skip {key}: {md} missing", file=sys.stderr)
            continue
        text = md.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        stem = md.stem
        docx_path = out / f"{stem}.docx"
        pdf_path = out / f"{stem}.pdf"
        d = md_to_docx_rtl(text, title=title)
        d.save(str(docx_path))
        _rezip_deterministic(docx_path)
        md_to_pdf_rtl(md, str(pdf_path), title=title,
                      footer="انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف")
        written += [docx_path, pdf_path]
    return written


if __name__ == "__main__":
    for f in build_all():
        print(f)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_governance_build.py -v`
Expected: all PASS. If `test_build_all_smoke` fails on `md_to_pdf_rtl` fonts, confirm Windows Tahoma exists at `C:/Windows/Fonts/tahoma.ttf` (it does on this machine — `report_common._pick_font()` prefers it).

- [ ] **Step 5: Commit**

```bash
git add analysis_tools/governance_build.py analysis_tools/tests/test_governance_build.py
git commit -m "feat(governance): RTL DOCX writer + build_all (PDF via report_common)"
```

---

### Task 3: Draft D1 — اساسنامه (۳۹ ماده)

**Files:**
- Create: `docs/governance/asasname.md`

**Interfaces:**
- Consumes: spec §2 (locked decisions), §3 (canon), §4 (the 39 ماده one-liners); sources `analysis/claude/governance_sources/asasname_resana_reference.txt` (tone/register for ماده‌بندی) and `legal_guide.txt` (statutory language).
- Produces: `docs/governance/asasname.md` — later tasks reference its ماده numbers verbatim (۱..۳۹ as numbered in spec §4).

**Reading list (executor must read before drafting):** spec §2–§4 fully; `asasname_resana_reference.txt` pages 1–2 and 11–13 (register of formal مواد); `legal_guide.txt` sections «تکالیف دبیر و شورای مرکزی», «امور مالی», «مقررات حاکم».

- [ ] **Step 1: Create the master with header and all ۷ بخش**

Structure skeleton (fill every ماده from spec §4 — each spec bullet becomes one full ماده paragraph; تبصره‌ها as indented «تبصره …» lines below their ماده):

```markdown
# اساسنامه انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف

نسخه ۱٫۰ — پیش‌نویس | تاریخ تصویب: — | تاریخ تأیید: — | جلسه عمومی: —

## بخش اول: کلیات و تعاریف

ماده ۱ (نام و قلمرو): نام تشکل «انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف» است که به‌عنوان تشکل دانشجویی علمی–فرهنگی وابسته به دانشکده فیزیک دانشگاه صنعتی شریف فعالیت می‌کند.

[…مواد ۲ تا ۳۹ مطابق spec §4…]

## بخش هفتم: انضباط، اصلاح اساسنامه و احکام پایانی

[…]

- این اساسنامه در … جلسه عمومی به تصویب و توسط معاونت فرهنگی و اجتماعی دانشگاه به تأیید می‌رسد.
```

Drafting rules (verbatim from spec):
- ماده ۱۰ is the two-mode مجمع ماده — draft exactly per spec §4 بخش سوم text.
- ماده ۱۱ تبصره ۱ must contain: «رسمیت جلسه با حضور بیش از نیمی از اعضای انجمن است و مصوبات با اکثریت مطلق اعضای حاضر تصویب می‌شود؛ حضور دانشجویان غیرعضو آزاد و بدون حق رأی است.»
- ماده ۸ تبصره (threshold carve-out) mirrors spec wording exactly (D4 ۴-۲ depends on it).
- ماده ۳۴ written as six numbered بنده (الف تا و) inside the ماده.
- Every ماده is 1–4 sentences, plain formal Persian; no bullet lists inside مواد except ماده ۱۵ (12 numbered duties) and ماده ۳۴.

- [ ] **Step 2: Run the lint gate**

Run: `python -m analysis_tools.governance_lint`
Expected: `[D1]` findings only about D2/D3/D4 being absent are fine (lint skips missing files); zero `عبارت ممنوع`, zero `مواد غایب`, zero `ارجاع بدون قید منبع` for D1. Fix until clean.

- [ ] **Step 3: Full test suite**

Run: `python -m pytest analysis_tools/tests/test_governance_lint.py analysis_tools/tests/test_governance_build.py -v`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/governance/asasname.md
git commit -m "docs(governance): D1 اساسنامه — ۳۹ ماده در ۷ بخش (پیش‌نویس)"
```

---

### Task 4: Draft D2 — شیوه‌نامه داخلی شورای مرکزی

**Files:**
- Create: `docs/governance/shora-shivename.md`

**Interfaces:**
- Consumes: spec §5 (پیش‌درآمد ۰-۱..۰-۷, فصل‌های ۱–۷ with all بند one-liners incl. new ۱-۱۳ and ۷-۱۱, ۳ پیوست); D1 ماده numbers (from Task 3 file); `legal_guide.txt` checklists (پیش/حین/پس/سالانه) for پیوست ب.
- Produces: master whose فصل/بند numbering D4's cross-references point at («فصل ۶» answer-duty block, «۴-۲» team minimums, «۳-۱۱»/«۳-۱۲»).

**Reading list:** spec §5 fully; `legal_guide.txt` sections «چک‌لیست‌های عملیاتی», «امور مالی», «مجوز رویدادها»; D1 master (for exact ماده numbers to cite).

- [ ] **Step 1: Create the master**

Skeleton: title + version block → `## پیش‌درآمد` (۰-۱..۰-۷) → `## فصل ۱ — ترکیب شورا، نقش‌ها و حوزه‌ها` (۱-۱..۱-۱۳, ordered) → فصل ۲ (۲-۱..۲-۱۱) → `## فصل ۳ — امور مالی` (۳-۱..۳-۱۲) → فصل ۴ (۴-۱..۴-۹) → فصل ۵ (۵-۱..۵-۱۰) → فصل ۶ (۶-۱..۶-۸) → فصل ۷ (۷-۱..۷-۱۱) → `## پیوست الف/ب/ج` (each a bullet-list one-pager: الف decision table as bullets «عادی: … / مهم: … / حساس: …»; ب the three checklists; ج the annual calendar month-by-month bullets).

Each بند is written as `۱-۱.` followed by 1–5 sentences; numbers/dates exactly as spec (۴۸ ساعت، ۷۲ ساعت، ۱۰ روز، ۱۴ روز، ۵ و ۲۰ میلیون تومان، نصاب ۴ از ۷، رأی ۵ از ۷، ۵ از ۶ در تعلیق). Word «حوزه» everywhere (never پرتفوی). The three canonical texts live here: تعهدنامه five principles (۱-۱۱), the 10-day answer duty (۶-۴), کمیته انتخابات definition (۷-۱).

- [ ] **Step 2: Run the lint gate**

Run: `python -m analysis_tools.governance_lint`
Expected: zero D2 findings (فصل ۱..۷ present, no بند gaps, no banned phrases, citations qualified).

- [ ] **Step 3: Run tests + commit**

```bash
python -m pytest analysis_tools/tests/ -k governance -v
git add docs/governance/shora-shivename.md
git commit -m "docs(governance): D2 شیوه‌نامه شورا — پیش‌درآمد + ۷ فصل + ۳ پیوست"
```

---

### Task 5: Draft D3 — منشور مجمع (+ canonical چای پیوست)

**Files:**
- Create: `docs/governance/majma-manshoor.md`

**Interfaces:**
- Consumes: spec §6; `analysis/claude/governance_sources/majma_charter.txt` (preamble + جمع‌بندی carried near-verbatim; 11 groups; role basket); `analysis/claude/governance_sources/tea_framework.txt` (پیوست body); `normalize_fa` from Task 1 for artifact cleanup.
- Produces: the canonical چارچوب چای text (D4 پیوست ۱ points here; lint `TEA_CANON` checks this file).

**Reading list:** spec §6; `majma_charter.txt` fully; `tea_framework.txt` fully.

- [ ] **Step 1: Create the master**

Skeleton: `# منشور مجمع…` + version block → دیباچه (no-number paragraphs, 150–200 words, preserving the charter's three soul-sentences and «به بیان ساده» sentence verbatim from `majma_charter.txt` page 1, and its جمع‌بندی from page 15) → `## فصل ۱: هویت و هدف` (۱-۱..۱-۴) → فصل ۲ (رابطه با شورا؛ ۲-۱..۲-۵ — ۲-۴ decouples انتخابات per spec) → فصل ۳ (عضویت؛ ۳-۱..۳-۵ with the مدرسه‌تابستانه/یلدا/پست example verbatim) → فصل ۴ (گروه‌های کاری؛ ۴-۱..۴-۵, 11 groups one line each, sleep/wake, content clause) → فصل ۵ (نقش‌های پروژه‌ای؛ ۵-۱..۵-۴) → فصل ۶ (چای؛ ۶-۱..۶-۴) → فصل ۷ (یادگیری؛ ۷-۱..۷-۳) → فصل ۸ (مستندسازی؛ ۸-۱..۸-۵) → فصل ۹ (اصلاح؛ ۹-۱..۹-۳ with the announce-then-next-session beat) → `## پیوست: چارچوب گفت‌وگو و مشارکت در چای`.

- [ ] **Step 2: Reproduce the tea framework clean**

Re-typeset `tea_framework.txt` as the پیوست: reflow line-broken sentences (the extraction splits words across lines), apply lam-alef fixes (اطالعات→اطلاعات، اعالم→اعلام، الزم→لازم، سؤاالت→سؤالات، بالمانع→بلامانع، مصاحبه‌کننده‌گان artifacts), keep its ۶ sections and all normative content **verbatim in substance** — no rewriting, no summarizing. The five `TEA_CANON` sentences must appear character-for-character.

- [ ] **Step 3: Lint + tests + commit**

```bash
python -m analysis_tools.governance_lint   # D3 clean incl. فصل ۱..۹; TEA_CANON only checked in cross-doc (Task 7) — still verify the 5 sentences by grep:
grep -c "زمان جلسه متعلق به همه است" docs/governance/majma-manshoor.md   # expect 1
python -m pytest analysis_tools/tests/ -k governance -v
git add docs/governance/majma-manshoor.md
git commit -m "docs(governance): D3 منشور مجمع + پیوست چارچوب چای (canonical)"
```

---

### Task 6: Draft D4 — شیوه‌نامه اجرایی مجمع

**Files:**
- Create: `docs/governance/majma-shivename.md`

**Interfaces:**
- Consumes: spec §7 (فصل‌های ۱–۸ with fixes); D2 فصل ۶ block (cite, don't restate, for the 10-day duty); D3 پیوست (pointer only — never re-embed the tea text); `tea_framework.txt` and `majma_charter.txt` for template wording.
- Produces: the بسته انتقال canonical checklist (۵-۸) that D3 ۸-۴ references.

**Reading list:** spec §7; `majma_charter.txt` فصل نقش‌ها; `tea_framework.txt` (for consistency of گرداننده wording).

- [ ] **Step 1: Create the master**

Skeleton: title + version block → `## فصل ۱: کلیات و اصول` (۱-۱..۱-۴ — ۱-۱ hierarchy per spec including منشور مجمع in the chain) → فصل ۲ اداره جلسات چای (۲-۱..۲-۸; ۲-۱ points to D3 پیوست as canonical) → فصل ۳ چرخه جلسات (۳-۱..۳-۷; «منظم و معمولاً هفتگی») → فصل ۴ از ایده تا تیم (۴-۱..۴-۱۰; three-threshold + content clause; tiered صفحه همراهی) → فصل ۵ مستندسازی (۵-۱..۵-۸; canonical بسته انتقال list) → فصل ۶ چرخه سالانه (۶-۱..۶-۹) → فصل ۷ هماهنگی با شورا (۷-۱..۷-۷; cite D2 فصل ۶ for the answer duty) → فصل ۸ ابزارها (۸-۱..۸-۷) → `## پیوست‌های ۱ تا ۸` (each ۳–۸ bullet lines, ≤ one printed page; پیوست ۱ is the pointer + D4-only addenda: گرداننده/یادداشت‌گیر split, rotation rule, برگه گرداننده contents).

- [ ] **Step 2: Lint + tests + commit**

```bash
python -m analysis_tools.governance_lint
python -m pytest analysis_tools/tests/ -k governance -v
git add docs/governance/majma-shivename.md
git commit -m "docs(governance): D4 شیوه‌نامه اجرایی مجمع — ۸ فصل + ۸ پیوست"
```

---

### Task 7: Cross-document consistency pass

**Files:**
- Modify (as needed): all four masters.

**Interfaces:**
- Consumes: all four masters; `governance_lint.cross_doc_findings`.
- Produces: a suite-green state where `python -m analysis_tools.governance_lint` exits 0 with all four masters present.

- [ ] **Step 1: Run the full gate**

```bash
python -m analysis_tools.governance_lint
```
Expected: exit 0. Typical residues to fix: D2/D3/D4 citing ماده numbers that shifted during drafting; TEA_CANON sentence drift in D3's پیوست; unqualified citations.

- [ ] **Step 2: Manual spot-audit (checklist)**

Verify by reading (grep each phrase, expect hits in the right docs):
- «کمیته انتخابات» defined in D2 ۷-۱, named in D1 ماده ۲۳ and D4 ۶-۷ — and nowhere as «هیئت نظارت مجمع».
- «رابط مجمع» defined in D2 فصل ۶; D4 ۷-۱ states expectations only; D2 ۱-۶ assigns it to حوزه ارتباطات.
- «جلسه عمومی سالانه» in D2 ۳-۶ and ۷-۲ (not «مجمع عمومی»).
- The 10-day answer duty text appears in D2 ۶-۴; D4 ۷-۴ cites it.
- «بدون رسید، ثبت نمی‌شود» in D2 ۳-۳; «تسویه» precondition in D2 ۷-۳; «هیچ کار مادی به‌تنهایی» in D2 ۱-۸.
- ماده ۸ تبصره in D1 and ۴-۲ threshold in D4 use matching wording («اعلام عمومی، ثبت‌نام، پرداخت، میهمان بیرونی یا استفاده از نام و نشان انجمن»).

- [ ] **Step 3: Full tests + commit**

```bash
python -m pytest analysis_tools/tests/ -k governance -v
git add -A docs/governance && git commit -m "docs(governance): cross-document consistency pass — suite green"
```

---

### Task 8: Final builds + index README

**Files:**
- Create: `docs/governance/README.md`
- Create (build outputs, committed): `docs/governance/build/asasname.{docx,pdf}`, `shora-shivename.{docx,pdf}`, `majma-manshoor.{docx,pdf}`, `majma-shivename.{docx,pdf}`

**Interfaces:**
- Consumes: `build_all()` from Task 2; `governance_lint.run_all()`.
- Produces: the handover-ready artifacts.

- [ ] **Step 1: Write `docs/governance/README.md`**

Content (Persian): جدول چهار سند (نام، فایل، مرجع تصویب/اصلاح)؛ how-to-amend per document (D1: جلسه عمومی دو‌سوم + معاونت؛ D2: مصوبه شورا طبق ۰-۴؛ D3: سازوکار فصل ۹؛ D4: توافق جلسه مجمع طبق ۱-۴)؛ build instructions (`python -m analysis_tools.governance_build`)؛ lint instructions (`python -m analysis_tools.governance_lint`)؛ pointer to spec + open-questions list (spec §8) for the معاونت verification items.

- [ ] **Step 2: Build + verify determinism**

```bash
python -m analysis_tools.governance_build
sha1=$(git hash-object docs/governance/build/asasname.pdf)
python -m analysis_tools.governance_build
[ "$sha1" = "$(git hash-object docs/governance/build/asasname.pdf)" ] && echo PDF-DETERMINISTIC
```
Expected: 8 files written; `PDF-DETERMINISTIC` printed.

- [ ] **Step 3: Final gate + tests + commit**

```bash
python -m analysis_tools.governance_lint
python -m pytest analysis_tools/tests/ -k governance -v
git add docs/governance
git commit -m "docs(governance): final builds (DOCX+PDF) + index README — suite complete"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** D1→Task 3 (§4), D2→Task 4 (§5), D3→Task 5 (§6), D4→Task 6 (§7), canon→Tasks 1+7 (§3), production notes→Tasks 2+8 (§9), locked decisions embedded in drafting instructions (§2). Open questions (§8) surface in README (Task 8) — not tasks, they are external verifications.
- **Placeholders:** none — drafting tasks carry full skeletons, exact thresholds, and verbatim anchor sentences from the spec; `[…مواد ۲ تا ۳۹…]` markers point at spec §4 bullets which ARE the content list (the spec travels with the plan).
- **Type consistency:** `findings_for`/`cross_doc_findings`/`run_all`/`MASTER_FILES` names identical in Tasks 1–8; `md_to_docx_rtl`/`build_all`/`_rezip_deterministic` identical in Tasks 2 and 8; master filenames identical everywhere (`asasname.md`, `shora-shivename.md`, `majma-manshoor.md`, `majma-shivename.md`).
