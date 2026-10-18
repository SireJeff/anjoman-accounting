# Persian Report Versions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce Persian (FA) Markdown + PDF versions of both 2026-10-14 reports, plus Persian-labelled charts, generated from the same computation as the English reports so numbers cannot drift.

**Architecture:** An `analysis_tools/i18n` message catalog. Builders call `t(key, lang, **values)` instead of holding English literals. `en.json` is extracted verbatim from today's builders. `fa.json` is produced once by `translate.py` through the Claude API and committed. Builders keep their English number formatting, and FA output passes through one `localize()` step (Persian digits and separators). FA Markdown is rendered to PDF via HTML (`dir="rtl"`) + WeasyPrint. The English pipeline and its outputs stay byte-identical.

**Tech Stack:** Python 3.11, jdatetime, pandas, matplotlib, python-markdown 3.9, WeasyPrint 68.1, anthropic SDK 1.15 + pydantic 2.4, pytest, pypdf, `pdftoppm` (MiKTeX) for visual checks.

**Spec:** `docs/superpowers/specs/2026-10-18-persian-reports-design.md`

## Global Constraints

- Branch `feature/persian-reports`. Commit after each task. Every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- English outputs must not change: `reports/2026-10-14/**/Anjoman_*_Report*.md` (EN) must rebuild byte-identically. Never re-run `charts.render_all()` for `en` (it would rewrite committed PNGs).
- FA outputs sit next to the EN files: `Anjoman_Financial_Report_Monthly_FA.md/.pdf`, `Anjoman_Performance_Activity_Report_FA.md/.pdf`, `charts_fa/<same names>.png`.
- Persian digits `۰۱۲۳۴۵۶۷۸۹`, thousands separator `٬` (U+066C), decimal `٫` (U+066B), percent `٪` (U+066A). IDs (`TX0036`), backtick code, file names, URLs, `@handles` and `chat#id` references stay Latin.
- Jalali dates are primary in FA. Hours `HH:MM` are kept (digits localized).
- Builders never call the API. Only `python -m analysis_tools.translate` does, and it needs `ANTHROPIC_API_KEY` in the environment plus the user's VPN (the API returns HTTP 403 from this machine without it). Run it as `ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" python -m analysis_tools.translate`. Never print, log or commit the key.
- Model `claude-opus-5-5`. Default effort (do not pass `thinking` or `effort`).
- Before chart or PDF generation, check free space on C: (`df -h /c`). Stop if < 1 GB.
- Run tests with `python -m pytest analysis_tools/tests/ -q`. The 123 existing tests must stay green.
- Reading the ledger CSV always uses `encoding="utf-8-sig"`.

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `analysis_tools/i18n/__init__.py` | create | `t`, `template`, `term`, `dt`, `localize`, `delocalize`, `number_tokens`, `CatalogError`, catalog loading + staleness |
| `analysis_tools/i18n/en.json` | create | EN templates (keys `fin.*`, `perf.*`, `chart.*`, `common.*`) |
| `analysis_tools/i18n/fa.json` | create (Task 6) | FA templates, same keys |
| `analysis_tools/i18n/hashes.json` | create (Task 6) | sha1 of each EN template when its FA was produced |
| `analysis_tools/i18n/glossary.json` | create | closed EN→FA vocabularies + free `term` list for the translator |
| `analysis_tools/report_common.py` | modify | add `md_to_html_rtl`, `md_to_pdf_rtl` (EN `md_to_pdf` untouched) |
| `analysis_tools/build_financial_report.py` | modify | `render(lang)` + `build(lang)`; CLI `--lang` |
| `analysis_tools/build_performance_report.py` | modify | `render(lang)` + `build(lang)`; CLI `--lang` |
| `analysis_tools/charts.py` | modify | `lang` parameter; FA → `charts_fa/` |
| `analysis_tools/translate.py` | create | pending-key selection, validation, chunked SDK calls, cache, write `fa.json` + `hashes.json` |
| `analysis_tools/tests/test_i18n.py` | create | i18n units, glossary checks |
| `analysis_tools/tests/test_rtl_render.py` | create | HTML/PDF RTL renderer |
| `analysis_tools/tests/test_translate.py` | create | validator, chunking, cache, fake client |
| `analysis_tools/tests/test_report_i18n.py` | create | EN byte-identity, catalog integrity, number parity, glossary enforcement, FA gates |
| `analysis_tools/tests/conftest.py` | create | `pseudo_fa` fixture (FA catalog = EN with marker, used before real translation exists) |

**Pseudo-FA catalog (used in Tasks 3–5 before the real `fa.json` exists).** The `pseudo_fa` fixture points the catalog loader at a temp directory with `fa.json = {k: "«FA» " + v}` and matching `hashes.json`. This lets builder and chart FA paths be tested end to end without the API. The number-parity and glossary tests in Task 7 run against the real `fa.json`.

---

### Task 1: i18n core module + glossary

**Files:**
- Create: `analysis_tools/i18n/__init__.py`, `analysis_tools/i18n/glossary.json`, `analysis_tools/i18n/en.json` (initially `{}`)
- Create: `analysis_tools/tests/test_i18n.py`, `analysis_tools/tests/conftest.py`

**Interfaces:**
- Produces (used by every later task):
  - `class CatalogError(RuntimeError)`
  - `set_catalog_dir(path: Path | None) -> None` (None restores the package dir) and `reload() -> None`
  - `sha(s: str) -> str` (sha1 hex of UTF-8)
  - `template(key: str, lang: str) -> str` and `t(key: str, lang: str, **kw) -> str`
  - `term(kind: str, key: str, lang: str, default: str | None = None) -> str`
  - `dt(iso: str, lang: str, n: int = 10) -> str`
  - `localize(text: str) -> str` (ASCII digits/separators → Persian, protected spans untouched)
  - `delocalize(text: str) -> str` (Persian digits/separators → ASCII; for tests)
  - `number_tokens(text: str) -> collections.Counter` (ISO dates → Jalali first, then `\d+(?:[.,]\d+)*` tokens)
  - `catalog(name: str) -> dict` (`"en" | "fa" | "hashes" | "glossary"`)

- [ ] **Step 1: Write the failing tests** — `analysis_tools/tests/test_i18n.py`

```python
import json
from collections import Counter

import pytest

from analysis_tools import i18n


@pytest.fixture
def cat(tmp_path):
    (tmp_path / "en.json").write_text(json.dumps(
        {"x.hello": "Hello {name}, {n} rows", "x.plain": "Plain text"}), encoding="utf-8")
    (tmp_path / "fa.json").write_text(json.dumps(
        {"x.hello": "سلام {name}، {n} ردیف", "x.plain": "متن ساده"}, ensure_ascii=False),
        encoding="utf-8")
    (tmp_path / "hashes.json").write_text(json.dumps(
        {"x.hello": i18n.sha("Hello {name}, {n} rows"), "x.plain": "stale"}), encoding="utf-8")
    (tmp_path / "glossary.json").write_text(json.dumps(
        {"chat": {"channel": "کانال"}}, ensure_ascii=False), encoding="utf-8")
    i18n.set_catalog_dir(tmp_path)
    yield tmp_path
    i18n.set_catalog_dir(None)


def test_t_en_and_fa(cat):
    assert i18n.t("x.hello", "en", name="A", n="3") == "Hello A, 3 rows"
    assert i18n.t("x.hello", "fa", name="A", n="3") == "سلام A، 3 ردیف"


def test_unknown_key_raises(cat):
    with pytest.raises(KeyError):
        i18n.t("nope", "en")


def test_stale_fa_raises(cat):
    with pytest.raises(i18n.CatalogError, match="stale"):
        i18n.t("x.plain", "fa")


def test_missing_fa_raises(cat):
    (cat / "en.json").write_text(json.dumps({"x.new": "New"}), encoding="utf-8")
    i18n.reload()
    with pytest.raises(i18n.CatalogError, match="missing"):
        i18n.t("x.new", "fa")


def test_term(cat):
    assert i18n.term("chat", "channel", "en") == "channel"
    assert i18n.term("chat", "channel", "en", default="Channel") == "Channel"
    assert i18n.term("chat", "channel", "fa") == "کانال"
    with pytest.raises(i18n.CatalogError):
        i18n.term("chat", "unknown_chat", "fa")


def test_dt():
    assert i18n.dt("2025-10-04T13:30:00", "en") == "2025-10-04"
    assert i18n.dt("2025-10-04T13:30:00", "en", 16) == "2025-10-04T13:30"
    assert i18n.dt("2025-10-04T13:30:00", "fa") == "1404/07/12"
    assert i18n.dt("2025-10-04T13:30:00", "fa", 16) == "1404/07/12 13:30"
    assert i18n.dt("2025-05-28", "fa") == "1404/03/07"


def test_localize_numbers():
    assert i18n.localize("1,234,567.5 and 12.5%") == "۱٬۲۳۴٬۵۶۷٫۵ and ۱۲٫۵٪"
    assert i18n.localize("1404/07 at 13:30, n=62") == "۱۴۰۴/۰۷ at ۱۳:۳۰, n=۶۲"


def test_localize_protects_identifiers():
    s = ("TX0036 `analysis/timeline.json` @QuantaSC accounting_group#123 m29 "
         "Task-11 ![a](charts_fa/x1.png) https://a.b/c1 and 5")
    out = i18n.localize(s)
    for keep in ("TX0036", "`analysis/timeline.json`", "@QuantaSC",
                 "accounting_group#123", "m29", "Task-11", "![a](charts_fa/x1.png)",
                 "https://a.b/c1"):
        assert keep in out
    assert out.endswith("and ۵")


def test_delocalize_roundtrip():
    assert i18n.delocalize("۱٬۲۳۴٫۵٪") == "1,234.5%"


def test_number_tokens_normalizes_dates():
    en = "first seen 2025-10-04, total 1,234 (12.5%)"
    fa = i18n.localize("اولین ۱۴۰۴/۰۷/۱۲، مجموع 1,234 (12.5%)")
    assert i18n.number_tokens(en) == i18n.number_tokens(fa)
    assert i18n.number_tokens("2025-10-04T13:30") == Counter({"1404": 1, "07": 1, "12": 1,
                                                               "13": 1, "30": 1})


def test_glossary_digit_tokens_preserved():
    g = i18n.catalog("glossary")
    for kind, m in g.items():
        if kind == "terms":
            continue
        for en, fa in m.items():
            assert i18n.number_tokens(en) == i18n.number_tokens(fa), (kind, en, fa)


def test_glossary_covers_ledger_vocab():
    import pandas as pd
    from analysis_tools.common import LEDGER_CSV
    df = pd.read_csv(LEDGER_CSV, encoding="utf-8-sig")
    g = i18n.catalog("glossary")
    for col, kind in (("category", "ledger_category"), ("project", "project"),
                      ("status", "status"), ("direction", "direction")):
        missing = set(df[col].dropna().unique()) - set(g[kind])
        assert not missing, (kind, missing)


def test_glossary_covers_classifier_categories_and_chats():
    from analysis_tools.common import SOURCES
    g = i18n.catalog("glossary")
    lex = json.loads((i18n.ROOT / "analysis/lexicon.json").read_text(encoding="utf-8"))
    assert set(lex) <= set(g["category"]), set(lex) - set(g["category"])
    assert set(SOURCES) | {"docx"} <= set(g["chat"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_i18n.py -q`
Expected: FAIL (`ImportError: cannot import name 'i18n'`)

- [ ] **Step 3: Implement `analysis_tools/i18n/__init__.py`**

```python
"""Message catalog for EN/FA report generation.

Builders call t(key, lang, **values) instead of holding English literals;
en.json is the source of truth, fa.json is produced by analysis_tools.translate
and committed. Numbers keep their English formatting inside the builders and
FA output is passed once through localize(), so EN output stays byte-identical
and both languages share one computation path.
"""
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import jdatetime

from ..common import ROOT  # noqa: F401  (re-exported for tests)

PKG_DIR = Path(__file__).parent
_dir = PKG_DIR
_cache = {}


class CatalogError(RuntimeError):
    pass


def set_catalog_dir(path):
    global _dir
    _dir = Path(path) if path else PKG_DIR
    reload()


def reload():
    _cache.clear()


def catalog(name):
    if name not in _cache:
        p = _dir / f"{name}.json"
        _cache[name] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _cache[name]


def sha(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def template(key, lang):
    en = catalog("en")
    if key not in en:
        raise KeyError(f"no en template {key!r}")
    if lang == "en":
        return en[key]
    fa = catalog("fa")
    if key not in fa:
        raise CatalogError(f"fa.json missing {key!r}; run python -m analysis_tools.translate")
    if catalog("hashes").get(key) != sha(en[key]):
        raise CatalogError(f"fa.json stale for {key!r}; run python -m analysis_tools.translate")
    return fa[key]


def t(key, lang, **kw):
    return template(key, lang).format(**kw)


def term(kind, key, lang, default=None):
    if lang == "en":
        return key if default is None else default
    try:
        return catalog("glossary")[kind][key]
    except KeyError:
        raise CatalogError(f"glossary missing {kind}/{key!r}") from None


def dt(iso, lang, n=10):
    if lang == "en":
        return iso[:n]
    d = date.fromisoformat(iso[:10])
    jd = jdatetime.date.fromgregorian(date=d)
    out = f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
    if n == 16 and len(iso) >= 16:
        out += " " + iso[11:16]
    return out


# ------------------------------------------------------------ digit handling
_FA = "۰۱۲۳۴۵۶۷۸۹"
_TO_FA = str.maketrans("0123456789", _FA)
_TO_EN = str.maketrans(_FA + "٬٫٪", "0123456789,.%")
_PROTECT = re.compile(
    r"`[^`]*`"                       # inline code
    r"|!\[[^\]]*\]\([^)]*\)"         # markdown image
    r"|https?://\S+"                 # URL
    r"|@\w+"                         # handle
    r"|\w+#\d+"                      # chat#message reference
    r"|[A-Za-z_][A-Za-z0-9_\-]*\d[A-Za-z0-9_\-]*"  # TX0036, m29, Task-11
)


def _fa_span(s):
    s = re.sub(r"(?<=\d),(?=\d)", "٬", s)
    s = re.sub(r"(?<=\d)\.(?=\d)", "٫", s)
    s = re.sub(r"(?<=\d)%", "٪", s)
    return s.translate(_TO_FA)


def localize(text):
    out, pos = [], 0
    for m in _PROTECT.finditer(text):
        out.append(_fa_span(text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_fa_span(text[pos:]))
    return "".join(out)


def delocalize(text):
    return text.translate(_TO_EN)


_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}:\d{2}))?")


def _iso_to_jalali(m):
    jd = jdatetime.date.fromgregorian(
        date=date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    s = f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
    return s + (" " + m.group(4) if m.group(4) else "")


def number_tokens(text):
    s = _ISO.sub(_iso_to_jalali, delocalize(text))
    return Counter(re.findall(r"\d+(?:[.,]\d+)*", s))
```

- [ ] **Step 4: Write `analysis_tools/i18n/glossary.json`**

Persian ledger terms are copied from the 2026-10-10 precedent (`anjoman_accounting_information/reports/2026-10-10/fa/Accounting_Data_FA.json`) so both Persian reports agree. Write exactly:

```json
{
  "category": {
    "education_courses": "آموزش و دوره‌ها",
    "events": "رویدادها",
    "publications_shabahng": "نشریات (شباهنگ)",
    "media_outreach": "رسانه و اطلاع‌رسانی",
    "governance_decisions": "اداره و تصمیم‌گیری",
    "finance_operations": "امور مالی",
    "website_tech": "وب‌سایت و فناوری",
    "community_social": "اجتماعی و گفت‌وگوی اعضا",
    "coordination_logistics": "هماهنگی و پشتیبانی",
    "meta_noise": "پیام‌های حاشیه‌ای"
  },
  "chat": {
    "private_group": "گروه خصوصی",
    "public_group": "گروه عمومی",
    "channel": "کانال",
    "accounting_group": "گروه حسابداری",
    "summerschool_channel": "کانال مدرسهٔ تابستانه",
    "docx": "گزارش رسانه‌ای (docx)"
  },
  "ledger_category": {
    "Advertising": "تبلیغات", "Bank fees": "کارمزدهای بانکی",
    "Course fees": "شهریه دوره‌ها", "Donations": "کمک‌های مالی",
    "Equipment": "تجهیزات", "Events": "رویدادها", "Hospitality": "پذیرایی",
    "Opening funds": "وجوه ابتدای دوره", "Printing": "چاپ", "Supplies": "ملزومات",
    "Teaching": "تدریس", "Transfers": "انتقال‌ها", "Unclassified": "طبقه‌بندی‌نشده",
    "Website domain": "دامنهٔ وب‌سایت"
  },
  "project": {
    "Association operations": "عملیات انجمن",
    "Association website": "وب‌سایت انجمن",
    "Booths 1404": "غرفه‌های ۱۴۰۴",
    "Freshman Party 1404": "جشن ورودی‌های ۱۴۰۴",
    "Intro Event 1404": "برنامهٔ معارفه ۱۴۰۴",
    "Intro Event 1405": "برنامهٔ معارفه ۱۴۰۵",
    "Professors assembly Mehr": "مجمع اساتید مهر",
    "Summer School 1404": "مدرسهٔ تابستانه ۱۴۰۴",
    "Summer School 1405": "مدرسهٔ تابستانه ۱۴۰۵",
    "Tea & Physics society": "انجمن چای و فیزیک",
    "Unassigned": "تخصیص‌نیافته",
    "Unknown (likely 1405 summer school)": "نامشخص (احتمالاً مدرسهٔ تابستانه ۱۴۰۵)",
    "Yalda 1404": "یلدا ۱۴۰۴"
  },
  "status": {
    "Supported": "تأییدشده", "Review": "نیازمند بررسی", "Duplicate": "تکراری",
    "Invoice only": "صرفاً صورتحساب", "Summary only": "صرفاً گزارش تجمیعی"
  },
  "direction": {
    "Receipt": "دریافت", "Payment": "پرداخت", "Unknown": "نامشخص",
    "Internal transfer": "انتقال داخلی"
  },
  "weekday": {
    "Saturday": "شنبه", "Sunday": "یک‌شنبه", "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه", "Wednesday": "چهارشنبه", "Thursday": "پنج‌شنبه",
    "Friday": "جمعه"
  },
  "phase": {
    "Summer 1404": "تابستان ۱۴۰۴",
    "Academic 1404-05": "سال تحصیلی ۱۴۰۴–۱۴۰۵",
    "Summer 1405": "تابستان ۱۴۰۵",
    "Fall 1405": "پاییز ۱۴۰۵"
  },
  "terms": {
    "thread": "رشته (موضوع)", "event thread": "رشتهٔ رویداد",
    "in-window": "درون بازه", "non-service": "غیرخدماتی",
    "labeling": "برچسب‌گذاری", "affiliation": "انتساب",
    "keyword-fallback": "انتساب جایگزین کلیدواژه‌ای",
    "explicit affiliation": "انتساب صریح", "announcement lag": "تأخیر اعلان",
    "ledger": "دفتر کل", "reconciled ledger": "دفتر کل تطبیق‌شده",
    "supported": "تأییدشده", "review": "نیازمند بررسی",
    "receipts": "دریافت‌ها", "payments": "پرداخت‌ها", "net": "خالص",
    "toman": "تومان", "undated": "بدون تاریخ",
    "headline totals": "جمع‌های اصلی", "all rows": "همهٔ ردیف‌ها",
    "seed": "نهاد پایه", "forward weight": "وزن بازارسال",
    "mention weight": "وزن اشاره", "relay": "بازپخش‌کننده",
    "fixed slot": "نوبت ثابت", "weekday peak": "اوج روز هفته",
    "mechanics": "سازوکارها", "coverage": "پوشش", "precision": "دقت",
    "caveat": "ملاحظه", "case study": "مطالعهٔ موردی",
    "export-local": "به وقت محلی خروجی"
  }
}
```

Also create `analysis_tools/i18n/en.json` containing `{}`.

- [ ] **Step 5: Write `analysis_tools/tests/conftest.py`** (the shared `pseudo_fa` fixture used by Tasks 3–5)

```python
import json
import shutil

import pytest

from analysis_tools import i18n


@pytest.fixture
def pseudo_fa(tmp_path):
    """FA catalog = EN templates prefixed with «FA», hashes current. Lets FA
    code paths run before the real fa.json exists (Task 6)."""
    en = json.loads((i18n.PKG_DIR / "en.json").read_text(encoding="utf-8"))
    (tmp_path / "en.json").write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "fa.json").write_text(json.dumps(
        {k: "«FA» " + v for k, v in en.items()}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "hashes.json").write_text(json.dumps(
        {k: i18n.sha(v) for k, v in en.items()}), encoding="utf-8")
    shutil.copy(i18n.PKG_DIR / "glossary.json", tmp_path / "glossary.json")
    i18n.set_catalog_dir(tmp_path)
    yield tmp_path
    i18n.set_catalog_dir(None)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_i18n.py -q`
Expected: all PASS. If `test_glossary_covers_classifier_categories_and_chats` fails, the lexicon may hold a slug that is not among the 10 categories. Print the set difference and add the slug with a Persian name. Do not drop the assertion.

Run: `python -m pytest analysis_tools/tests/ -q`
Expected: 123 + new tests pass.

- [ ] **Step 7: Commit**

```bash
git add analysis_tools/i18n analysis_tools/tests/test_i18n.py analysis_tools/tests/conftest.py
git commit -m "feat(i18n): message catalog core, digit localization, glossary

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: RTL Markdown → HTML → PDF renderer

**Files:**
- Modify: `analysis_tools/report_common.py` (append; do not touch `md_to_pdf`)
- Test: `analysis_tools/tests/test_rtl_render.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - `md_to_html_rtl(md_text: str, title: str, footer: str) -> str` (a complete HTML document)
  - `md_to_pdf_rtl(md_path, pdf_path, title: str, footer: str) -> Path` (writes the PDF and a sibling `.html` file next to the PDF, for inspection and the spot-string gate)

- [ ] **Step 1: Write the failing tests** — `analysis_tools/tests/test_rtl_render.py`

```python
from pypdf import PdfReader

from analysis_tools.report_common import md_to_html_rtl, md_to_pdf_rtl

MD = """# گزارش مالی

پاراگراف با `TX0036` و عدد ۱۲٬۰۰۰.

| ماه | دریافت‌ها | پرداخت‌ها |
|---|---:|---:|
| ۱۴۰۴/۰۵ | ۱۲٬۰۰۰ | — |

- مورد اول

![نمودار](charts_fa/x.png)
"""


def test_html_is_rtl_with_numeric_cells():
    html = md_to_html_rtl(MD, title="گزارش", footer="انجمن علمی فیزیک | گزارش")
    assert '<html lang="fa" dir="rtl">' in html
    assert "Tahoma" in html
    assert "<table>" in html or "<table" in html
    assert 'class="num"' in html               # numeric cells marked LTR-isolated
    assert "<code>TX0036</code>" in html
    assert "counter(page, persian)" in html    # page footer, Persian digits
    assert 'src="charts_fa/x.png"' in html


def test_wide_table_class():
    cols = " | ".join(f"c{i}" for i in range(10))
    md = f"| {cols} |\n|" + "---|" * 10 + "\n| " + " | ".join("۱" for _ in range(10)) + " |\n"
    html = md_to_html_rtl(md, title="t", footer="f")
    assert 'class="wide"' in html


def test_pdf_written(tmp_path):
    md = tmp_path / "r_FA.md"
    md.write_text(MD.replace("![نمودار](charts_fa/x.png)\n", ""), encoding="utf-8")
    pdf = md_to_pdf_rtl(md, tmp_path / "r_FA.pdf", title="گزارش", footer="انجمن")
    assert pdf.exists() and len(PdfReader(str(pdf)).pages) >= 1
    assert (tmp_path / "r_FA.html").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_rtl_render.py -q`
Expected: FAIL (`ImportError: cannot import name 'md_to_html_rtl'`)

- [ ] **Step 3: Implement** (append to `analysis_tools/report_common.py`)

```python
# --------------------------------------------------------------------------
# Persian (RTL) path: markdown -> HTML (dir=rtl) -> WeasyPrint. Follows the
# 2026-10-10 precedent (reports/2026-10-10/fa/Anjoman_Financial_Report_FA.html);
# reportlab cannot shape Arabic script, WeasyPrint (Pango/HarfBuzz) can.
# --------------------------------------------------------------------------
_RTL_NUM = re.compile(r"^[\s\-−+*—]*[۰-۹0-9][۰-۹0-9٬٫,.%٪:/\s→–\-+*()]*$")

_RTL_CSS = """
@page { size: A4; margin: 16mm 14mm 18mm;
  @bottom-center { content: "%(footer)s | صفحه " counter(page, persian);
    font-family: Tahoma; font-size: 7.5pt; color: %(muted)s; } }
html { direction: rtl; }
body { font-family: Tahoma, "DejaVu Sans", sans-serif; font-size: 9pt;
  line-height: 1.75; color: %(ink2)s; }
h1 { font-size: 17pt; color: %(ink)s; margin: 0 0 4mm; }
h2 { font-size: 12.5pt; color: %(accent)s; border-bottom: 0.6pt solid %(grid)s;
  padding-bottom: 1.5mm; margin-top: 7mm; break-after: avoid; }
h3 { font-size: 10.5pt; color: %(ink)s; break-after: avoid; }
p, li { text-align: right; overflow-wrap: anywhere; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.92em;
  direction: ltr; unicode-bidi: isolate; }
table { width: 100%%; border-collapse: collapse; margin: 2mm 0 5mm;
  font-size: 7.4pt; line-height: 1.55; direction: rtl; }
table.wide { font-size: 6.2pt; }
th { background: %(accent)s; color: white; text-align: right; padding: 1.6mm 1.4mm; }
td { padding: 1.3mm 1.4mm; vertical-align: top; overflow-wrap: anywhere;
  border-bottom: 0.4pt solid %(grid)s; text-align: right; }
td.num, th.num { direction: ltr; unicode-bidi: isolate; text-align: left;
  white-space: nowrap; }
tr:nth-child(even) td { background: %(zebra)s; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
img { max-width: 100%%; display: block; margin: 3mm auto; }
"""


def _mark_tables(html_body):
    """Tag numeric cells (class=num) and wide tables (class=wide)."""
    def table(m):
        t = m.group(0)
        ncols = len(re.findall(r"<th[ >]", t.split("</tr>", 1)[0]))
        t = re.sub(r"<td([^>]*)>(.*?)</td>",
                   lambda c: (f'<td{c.group(1)} class="num">{c.group(2)}</td>'
                              if _RTL_NUM.match(re.sub(r"<[^>]+>", "", c.group(2)))
                              else c.group(0)),
                   t, flags=re.S)
        if ncols > 8:
            t = t.replace("<table>", '<table class="wide">', 1)
        return t
    return re.sub(r"<table>.*?</table>", table, html_body, flags=re.S)


def md_to_html_rtl(md_text, title, footer):
    import markdown
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    body = _mark_tables(body)
    css = _RTL_CSS % {"footer": footer.replace('"', "'"), "muted": MUTED, "ink": INK,
                      "ink2": INK2, "accent": ACCENT, "grid": GRID, "zebra": ZEBRA}
    return (f'<!DOCTYPE html>\n<html lang="fa" dir="rtl"><head><meta charset="utf-8">'
            f"<title>{html.escape(title)}</title><style>{css}</style></head>"
            f"<body>{body}</body></html>\n")


def md_to_pdf_rtl(md_path, pdf_path, title, footer):
    from weasyprint import HTML
    md_path, pdf_path = Path(md_path), Path(pdf_path)
    doc = md_to_html_rtl(md_path.read_text(encoding="utf-8"), title, footer)
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(doc, encoding="utf-8")
    HTML(string=doc, base_url=str(md_path.parent)).write_pdf(str(pdf_path))
    return pdf_path
```

Note for the implementer: python-markdown emits `<td style="text-align: right;">` for `---:` columns. The `_mark_tables` regex keeps existing attributes (`c.group(1)`) and adds `class="num"`. The `class="num"` CSS rule overrides the inline alignment only for direction; that is intended. Inline `text-align: right` still wins for alignment, which is fine in RTL.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_rtl_render.py -q`
Expected: 3 PASS (WeasyPrint may print font-fallback warnings; those are fine).

- [ ] **Step 5: Visual smoke check**

Run:
```bash
python - <<'EOF'
from pathlib import Path
from analysis_tools.tests.test_rtl_render import MD
from analysis_tools.report_common import md_to_pdf_rtl
d = Path(r"C:/Users/SURFAC~1/AppData/Local/Temp/claude/C--Users-Surface-Laptop-3-Downloads-Telegram-Desktop-anjoman-acc/4e5b9bc6-84eb-4765-8e18-8406d048ec03/scratchpad/rtl")
d.mkdir(parents=True, exist_ok=True)
(d / "s.md").write_text(MD.replace("![نمودار](charts_fa/x.png)\n", ""), encoding="utf-8")
md_to_pdf_rtl(d / "s.md", d / "s.pdf", "گزارش", "انجمن علمی فیزیک | آزمایش")
EOF
pdftoppm -r 70 -png -f 1 -l 1 "<scratchpad>/rtl/s.pdf" "<scratchpad>/rtl/s"
```
Open `s-1.png` with the Read tool. Check that the heading sits at the right edge, the letters are joined, the table's first column is on the right, `۱۲٬۰۰۰` reads correctly (not `۰۰۰٬۲۱`), `TX0036` is not mirrored, and the footer shows «صفحه ۱» in Persian digits. Report what you saw in the task report.

- [ ] **Step 6: Commit**

```bash
git add analysis_tools/report_common.py analysis_tools/tests/test_rtl_render.py
git commit -m "feat(report): RTL markdown->HTML->WeasyPrint renderer for Persian reports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Shared refactor rules (Tasks 3 and 4)

Both builders are converted by the same mechanical rules. The **objective gate** is the EN byte-identity test: `render("en")` must equal the committed EN Markdown exactly. If the test fails, the refactor changed something. Fix the refactor, never the baseline file.

- **R1 Split.** `render(lang="en") -> str` does all loading, gating, computation and assembly, and returns exactly the text the EN file holds today (financial: `"\n".join(L)`; performance: `"\n".join(L) + "\n"`). It writes nothing. `build(lang="en")` calls `render`, writes `OUT` (en) or `OUT_FA` (fa), renders the PDF, and runs the PDF gates. `__main__` uses argparse `--lang {en,fa}`, default `en`.
- **R2 Literals → templates.** Every human-language string literal or f-string becomes `t("<prefix>.<section>.<name>", lang, **kw)`. The template is the literal's text with each `{expression}` replaced by `{name}`. Each `kw` value is a string formatted exactly as the f-string formatted it (`n=f"{len(tx)}"`, `total=fmt(v)`, `pct=pct(a, b)`). Templates contain **no format specs** (`{n:,}` is not allowed; pass `n=f"{n:,}"`).
- **R3 Markup stays in code.** Line prefixes (`## `, `### `, `- `), table pipes and separator rows, and image syntax are built in code. Inline emphasis (`**…**`, backticked identifiers) stays inside templates, so the translator can position it.
- **R4 Granularity.** One key per sentence or paragraph as the code assembles it today. Each branch of a conditional (`if fb > e_n` …) is its own key. One key per table header cell (`perf.s1.tbl_chats.h_chat`). Static header lists are built as `[t(k, lang) for k in (...)]`.
- **R5 Closed vocabularies** go through `term(kind, raw, lang, default=<today's EN display>)`: kinds `category`, `chat`, `ledger_category`, `project`, `status`, `direction`, `weekday` (pass the **English** weekday name), `phase`, `validation`. Add `"validation": {"evidenced": "مستند", "unverified": "تأییدنشده"}` to `glossary.json` in Task 4.
- **R6 Dates.** Where the EN shows a Gregorian date with **no Jalali beside it**, use `i18n.dt(iso, lang, n)` (n = today's slice length, 10 or 16). Where EN already pairs Gregorian with Jalali (`first_seen[:10] / jdate(...)`, `(... → ...) (jdate → jdate)`, the §2 thread table that has both a "First seen" and a "Jalali" column), keep the Gregorian slice unchanged.
- **R7 Localize once.** `text = "\n".join(L)`, then `if lang == "fa": text = i18n.localize(text)`. Never localize piecemeal.
- **R8 Images.** `img(alt_key, name, lang)` returns `f"![{t(alt_key, lang)}]({'charts' if lang == 'en' else 'charts_fa'}/{name}.png)"`.
- **R9 Keys** are stable snake_case identifiers (`fin.cash.basis`, `perf.s4.money_gap`) and never contain English sentences. Every key used must exist in `en.json`. Add keys to `en.json` as you extract them, sorted, with `ensure_ascii=False, indent=1`.
- **R10 No logic changes.** Computation, ordering, rounding, asserts and gates stay identical. FA runs the same `_gate` before writing.
- **R11 Data strings.** English free text that comes from data:
  - **Ledger review reasons** (financial flagged table): in FA, read `review_reason` (fallback `notes`) for the same TX id from `LEDGER_DIR / "fa/Accounting_Data_FA.json"` (`["ledger"]`, list of dicts with `id`). This is the board-approved Persian of the 2026-10-10 report. A missing id → `CatalogError`.
  - **Thread titles** (performance + event-timeline chart): in FA use `t(f"data.thread.{event_ref}", lang)`. EN keeps the raw `title` (byte identity). `en.json` must hold `data.thread.<ref>` = raw title for **every** thread in `timeline.json`. Task 4 adds `collect_data_strings() -> dict` in `build_performance_report.py`, plus a test asserting `en.json` contains exactly those `data.*` entries.
  - Everything else data-derived (snippets, docx labels and claims, seed/external labels, Persian weekday values) passes through unchanged.

### Task 3: Financial report builder → `render(lang)` / `build(lang)`

**Files:**
- Modify: `analysis_tools/build_financial_report.py`
- Modify: `analysis_tools/i18n/en.json` (add `fin.*` keys)
- Create: `analysis_tools/tests/test_report_i18n.py`

**Interfaces:**
- Consumes: `i18n.t`, `i18n.term`, `i18n.dt`, `i18n.localize`, `i18n.CatalogError` (Task 1); `report_common.md_to_pdf_rtl(md_path, pdf_path, title, footer)` (Task 2); `conftest.pseudo_fa` fixture.
- Produces: `build_financial_report.render(lang="en") -> str`, `build_financial_report.build(lang="en") -> Path`, `OUT`, `OUT_FA` module constants; `img(alt_key, name, lang)` helper.

- [ ] **Step 1: Write the failing tests** — `analysis_tools/tests/test_report_i18n.py`

```python
import re

import pytest

from analysis_tools import build_financial_report as fin
from analysis_tools import i18n


def _unprotected(text):
    return i18n._PROTECT.sub("", text)


def test_fin_en_byte_identical():
    assert fin.render("en") == fin.OUT.read_text(encoding="utf-8")


def test_fin_fa_pseudo(pseudo_fa):
    text = fin.render("fa")
    assert "«FA»" in text
    assert "charts_fa/cashflow_monthly.png" in text
    assert "](charts/" not in text
    assert not re.search(r"[0-9]", _unprotected(text)), "ASCII digit left unlocalized"
    assert "یلدا ۱۴۰۴" in text            # project label via glossary


def test_fin_fa_needs_catalog(tmp_path):
    import shutil
    shutil.copy(i18n.PKG_DIR / "en.json", tmp_path / "en.json")
    shutil.copy(i18n.PKG_DIR / "glossary.json", tmp_path / "glossary.json")
    i18n.set_catalog_dir(tmp_path)
    try:
        with pytest.raises(i18n.CatalogError):
            fin.render("fa")
    finally:
        i18n.set_catalog_dir(None)


def test_fin_gate_still_fires(monkeypatch, pseudo_fa):
    monkeypatch.setitem(fin.SUP_TOTALS, "Receipts", 1.0)
    with pytest.raises(AssertionError, match="gate FAILED"):
        fin.render("fa")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_report_i18n.py -q`
Expected: FAIL (`AttributeError: module ... has no attribute 'render'`)

- [ ] **Step 3: Restructure the module skeleton**

Apply this structure to `analysis_tools/build_financial_report.py`. The section bodies are converted in Step 4.

```python
import argparse

from . import i18n
from .i18n import t, term
from .report_common import md_to_pdf, md_to_pdf_rtl

OUT = ROOT / "reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md"
OUT_FA = OUT.with_name("Anjoman_Financial_Report_Monthly_FA.md")
FA_LEDGER = LEDGER_DIR / "fa/Accounting_Data_FA.json"


def img(alt_key, name, lang):
    return f"![{t(alt_key, lang)}]({'charts' if lang == 'en' else 'charts_fa'}/{name}.png)"


def _reason(r, lang, fa_rows):
    """Review reason in the report language (R11)."""
    if lang == "en":
        return (r.get("review_reason") or r.get("notes") or "unresolved").strip()
    row = fa_rows.get(r["id"])
    if row is None:
        raise i18n.CatalogError(f"{r['id']} missing from {FA_LEDGER.name}")
    return (row.get("review_reason") or row.get("notes")
            or t("fin.flag.unresolved", lang)).strip()


def render(lang="en"):
    tx = _load_tx()
    # ... today's build() body up to `text = "\n".join(L)`, converted per R1-R11
    text = "\n".join(L)
    assert "(auto:" not in text and "generate identically" not in text, \
        "placeholder text leaked into the report"
    return i18n.localize(text) if lang == "fa" else text


def build(lang="en"):
    text = render(lang)
    out = OUT if lang == "en" else OUT_FA
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if lang == "en":
        md_to_pdf(out, out.with_suffix(".pdf"))
    else:
        for c in ("cashflow_monthly", "cumulative_cash"):
            assert (out.parent / "charts_fa" / f"{c}.png").exists(), f"missing charts_fa/{c}.png"
        md_to_pdf_rtl(out, out.with_suffix(".pdf"),
                      title="گزارش مالی ماهانهٔ انجمن علمی فیزیک",
                      footer="انجمن علمی فیزیک | گزارش مالی ماهانه | ۱۴۰۵/۰۷/۲۲")
        html = out.with_suffix(".html").read_text(encoding="utf-8")
        for spot in ("۱۱۲٬۵۵۲٬۰۰۰", "۹۹٬۰۸۵٬۱۹۵", "۱۳٬۴۶۶٬۸۰۵"):
            assert spot in html, f"FA spot string {spot} missing"
    print(f"[gate] reconciliation passed on both bases; wrote {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("en", "fa"), default="en")
    print(build(ap.parse_args().lang))
```

(The `# ...` line above marks where the existing body goes. It is not a placeholder for new logic. Step 4 specifies the conversion.)

`_schedule_tables(title, key, months, cash, label_map)` gains `lang` and `kind` parameters (`kind="ledger_category"` for `by_category`, `"project"` for `by_project`). Row labels become `term(kind, n, lang, default=label_map.get(n, n))`. The header's first cell (`key.split("_")[1].capitalize()`) becomes `t("fin.sched.h_category", lang)` / `t("fin.sched.h_project", lang)`. **Sorting keeps today's EN key** (`label_map.get(n, n)`) in both languages, so row order is identical.

`fa_rows = {x["id"]: x for x in read_json(FA_LEDGER)["ledger"]}` is loaded only when `lang == "fa"`. Otherwise it is `{}`.

- [ ] **Step 4: Convert every literal (R2–R11)**

Worked examples. Every other literal in the module follows the same pattern.

```python
# before
L = ["# Anjoman Financial Report — Monthly View (1404/04 – 1405/07)", "",
     f"**Window:** {WINDOW_START} → {WINDOW_END} · **Source:** reconciled ledger "
     f"of 2026-10-10 ({len(tx)} transactions, `Transactions.csv`). Derived view — "
     "this report does not re-audit; Review-status transactions are flagged in "
     "their own section below.", ""]
# after
L = ["# " + t("fin.title", lang), "",
     t("fin.intro", lang, start=i18n.dt(WINDOW_START, lang), end=i18n.dt(WINDOW_END, lang),
       n=f"{len(tx)}"), ""]
# en.json
#  "fin.title": "Anjoman Financial Report — Monthly View (1404/04 – 1405/07)",
#  "fin.intro": "**Window:** {start} → {end} · **Source:** reconciled ledger of 2026-10-10 ({n} transactions, `Transactions.csv`). Derived view — this report does not re-audit; Review-status transactions are flagged in their own section below.",
```

The window bounds are ISO dates with no Jalali beside them (R6). In EN, `dt` returns the same string, so identity holds. The literal `2026-10-10` inside the template is a report **name** (the reconciliation's folder date). Leave it as text: `localize` turns it into `۲۰۲۶-۱۰-۱۰`, and the parity normalization converts both sides identically.

```python
# month evidence cell: three branches → three keys
ev = (t("fin.cash.ev_one", lang, n=f"{n}") if n == 1 else
      (t("fin.cash.ev_many", lang, n=f"{n}") if n else "—"))
# Gregorian range column (no Jalali in that cell; the row label is the Jalali month)
g = (f'{i18n.dt(gr.loc[m, "min"], lang)} → {i18n.dt(gr.loc[m, "max"], lang)}'
     if m in gr.index else "—")
# 'unknown*' row label
label = (t("fin.cash.unknown_row", lang) + "*") if m == "unknown" else m
```

For `label`, EN must still print `unknown*`, so `fin.cash.unknown_row` = `"unknown"`.

Weekday peaks: `term("weekday", _wd_en(e["jalali_weekday"]), lang)`. Flagged-table direction: `term("direction", r["direction"], lang)`. Flagged-table reason: `_reason(r, lang, fa_rows)`. Status words inside prose stay in the templates (the translator renders them with the glossary).

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_report_i18n.py -q`
Expected: 4 PASS. If `test_fin_en_byte_identical` fails, diff the two:
```bash
python -c "from analysis_tools import build_financial_report as f; open('/tmp/fin_en.md','w',encoding='utf-8',newline='\n').write(f.render('en'))"
git diff --no-index --word-diff reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md /tmp/fin_en.md
```

Run: `python -m pytest analysis_tools/tests/ -q`. All green.

- [ ] **Step 6: Commit**

```bash
git add analysis_tools/build_financial_report.py analysis_tools/i18n/en.json analysis_tools/tests/test_report_i18n.py
git commit -m "refactor(financial-report): catalog-driven render(lang); EN byte-identical

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Performance report builder → `render(lang)` / `build(lang)`

**Files:**
- Modify: `analysis_tools/build_performance_report.py`
- Modify: `analysis_tools/i18n/en.json` (add `perf.*`, `common.*`, `data.thread.*` keys); `analysis_tools/i18n/glossary.json` (add `validation`)
- Modify: `analysis_tools/tests/test_report_i18n.py` (append)

**Interfaces:**
- Consumes: same as Task 3. Copy the 3-line `img` helper into this module.
- Produces: `build_performance_report.render(lang="en") -> str`, `build(lang="en") -> Path`, `OUT`, `OUT_FA`, `collect_data_strings() -> dict[str, str]` (`{"data.thread.<ref>": title}` for every thread in `timeline.json`), `thread_title(th: dict, lang: str) -> str` (EN: raw title; FA: `t(f"data.thread.{ref}")`). Task 5 imports `thread_title`.

- [ ] **Step 1: Append failing tests** to `analysis_tools/tests/test_report_i18n.py`

```python
from analysis_tools import build_performance_report as perf


def test_perf_en_byte_identical():
    assert perf.render("en") == perf.OUT.read_text(encoding="utf-8")


def test_perf_fa_pseudo(pseudo_fa):
    text = perf.render("fa")
    assert "«FA»" in text
    for c in ("activity_by_month", "category_breakdown", "weekday_hour_heat",
              "hour_histogram", "event_timeline", "ecosystem_map"):
        assert f"charts_fa/{c}.png" in text
    assert "](charts/" not in text
    assert not re.search(r"[0-9]", _unprotected(text)), "ASCII digit left unlocalized"
    assert "۷۲۶٬۵۲۷" in text and "۱۳:۳۰" in text and "۲٬۶۹۴٬۷۵۰" in text
    assert "گروه خصوصی" in text              # chat label via glossary


def test_data_strings_in_sync():
    en = i18n.catalog("en")
    want = perf.collect_data_strings()
    have = {k: v for k, v in en.items() if k.startswith("data.")}
    assert have == want
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_report_i18n.py -q -k "perf or data_strings"`
Expected: FAIL (`no attribute 'render'`)

- [ ] **Step 3: Restructure**

- `sec1 … sec7` and `_case_study` each gain a trailing `lang` parameter. `render(lang)` holds today's `build()` body up to `text = "\n".join(L)` and returns `text + "\n"`, localized when `lang == "fa"` (localize the joined text, then append `"\n"`).
- `build(lang)` writes the file. EN keeps today's `md_to_pdf(...)` call and pypdf spot gate, unchanged. FA asserts the six `charts_fa/*.png` exist, runs `md_to_pdf_rtl(out, pdf, title="گزارش عملکرد و فعالیت انجمن علمی فیزیک", footer="انجمن علمی فیزیک | گزارش عملکرد و فعالیت | ۱۴۰۵/۰۷/۲۲")`, and gates on pypdf page count `> 6` plus `۷۲۶٬۵۲۷`, `۱۳:۳۰`, `۲٬۶۹۴٬۷۵۰` in the sibling `.html`. Do **not** gate FA on pypdf text: pypdf extracts RTL runs in visual order (`۰۰۰٬۲۱`), which is not a rendering defect.
- The chart-existence assert (today at the top of `build()`, for `charts/`) moves into `build()` for each language's own chart directory, so `render("fa")` works under test before `charts_fa/` exists. The `charts/{c}.png` embedded-check after assembly becomes `f"{'charts' if lang == 'en' else 'charts_fa'}/{c}.png"`.
- Helpers: `plural(n, one, many)` becomes `plural(n, lang)` using keys `common.chat_one` = `"{n} chat"` and `common.chat_many` = `"{n} chats"` (picked by `n == 1`, with `n=f"{n}"`). `clean()` keeps its logic, but its `"[no text]"` literal becomes `t("common.no_text", lang)`, so `clean` and `snippet` gain `lang`. `snippet`'s `"[media: …]"` uses `t("common.media", lang, kinds=", ".join(mk))`.
- `PHASES` names → `term("phase", name, lang)` at render time. Keep the tuple as-is.
- Add, and use `thread_title` wherever the code prints `t['title']` (§1 top-5 table, §4 money-only paragraph, case-study heading, the `clean(t["title"], 60)` fallback):

```python
def collect_data_strings():
    tl = read_json(ROOT / "analysis/timeline.json")
    return {f"data.thread.{x['event_ref']}": x["title"] for x in tl["threads"]}


def thread_title(th, lang):
    return th["title"] if lang == "en" else t(f"data.thread.{th['event_ref']}", lang)
```

  Merge those entries into `en.json` with a one-off script (`json.loads` → `update(collect_data_strings())` → sorted dump).
- Vocabulary sites (R5): §1 chat column and the top-3 category names; §2 `top_chat`, `c1`, `c2`, phase names; §3 category rows (both tables); §4 case-study stage labels (the `{chat}` inside "busiest chat …" / "first message in …"), while `{chat}#{message_id}` references stay raw; ledger `x['direction']` (`direction`), `x['category']` (`ledger_category`), `x.get('status')` (`status`); §5 seed `Status` column (`validation`); §6 peaks `Chat` column. The §6 weekday column is already Persian: keep it raw.
- Dates (R6): §1 top-5 `first_seen[:10] → last_seen[:10]` → `dt`; §4 table `First seen` → `dt`; case-study stage `Date` cells `[:16]` → `dt(..., lang, 16)`, and `chat first {..[:10]}` / `{ex['timestamp'][:10]}` → `dt`; delivery-surface sentence dates → `dt`; `decision_dates` → `", ".join(dt(d, lang) for d in sorted(set(...)))`. Keep Gregorian at the pair sites: the §2 phase sentence (`first seen {g} / {jalali}`), the §2 thread table (`First seen` + `Jalali` columns), and the case-study header `(g → g) (j → j)`. The window header line already pairs both: keep it.
- `x.get("period", "—")` in the payment stage rows is a Jalali month: keep it raw.

- [ ] **Step 4: Convert every literal (R2–R11)** with the same patterns as Task 3. Example for a conditional tail:

```python
# before
f"the remaining {fb:,} are keyword-fallback memberships"
+ (" — this thread is fallback-heavy, so its message count and lag "
   "are approximate (§7)." if fb > e_n else "."),
# after
t("perf.case.fallback", lang, fb=f"{fb:,}")
+ (t("perf.case.fallback_heavy", lang) if fb > e_n else "."),
```

Watch for leading and trailing spaces inside fragments that are concatenated (e.g. the §2 `para += (...)` pieces). They belong inside the template text, so the EN output stays identical.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_report_i18n.py -q`. All pass.
Run: `python -m pytest analysis_tools/tests/ -q`. All green.

- [ ] **Step 6: Commit**

```bash
git add analysis_tools/build_performance_report.py analysis_tools/i18n/en.json analysis_tools/i18n/glossary.json analysis_tools/tests/test_report_i18n.py
git commit -m "refactor(performance-report): catalog-driven render(lang); EN byte-identical

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Persian chart variants (`charts.py`, `lang`)

**Files:**
- Modify: `analysis_tools/charts.py`
- Modify: `analysis_tools/i18n/en.json` (add `chart.*` keys)
- Modify: `analysis_tools/tests/test_charts.py` (append)

**Interfaces:**
- Consumes: `i18n.t`, `i18n.term`, `i18n.localize`; `build_performance_report.thread_title(th, lang)` (Task 4); `conftest.pseudo_fa`.
- Produces: `charts.render_all(lang="en") -> dict[str, Path]`. For `fa` it writes to `PERF.with_name("charts_fa")` and `FIN.with_name("charts_fa")`, same file names. Every chart function gains a trailing `lang="en"` parameter.

- [ ] **Step 1: Append failing tests** to `analysis_tools/tests/test_charts.py`

```python
def test_render_all_fa_writes_charts_fa(tmp_path, monkeypatch, pseudo_fa):
    tl = {"monthly_activity": {"1404/05": {"channel": {"events": 3}}},
          "monthly_cashflow": {"1404/05": {"Receipts": 1.0, "Payments": 0.5,
                                           "by_category": {"Events": 1.0}, "by_project": {}}},
          "hour_histogram": {"channel": {"13": 2}},
          "weekday_hour_heat": {"channel": {"شنبه": {"13": 2}}},
          "threads": [], "mechanics": [], "event_start_times": {}}
    eco = {"nodes": [{"id": "association", "label": "A", "type": "association", "seed": True},
                     {"id": "shabahang_sut", "label": "S", "type": "subgroup", "seed": True}],
           "edges": [{"source": "channel_export", "target": "shabahang_sut",
                      "type": "forward", "weight": 5}]}
    monkeypatch.setattr(charts, "load_timeline", lambda: tl)
    monkeypatch.setattr(charts, "load_ecosystem", lambda: eco)
    monkeypatch.setattr(charts, "PERF", tmp_path / "perf" / "charts")
    monkeypatch.setattr(charts, "FIN", tmp_path / "fin" / "charts")
    out = charts.render_all("fa")
    assert len(out) == 8
    for p in out.values():
        assert Path(p).parent.name == "charts_fa" and Path(p).exists()
    assert not (tmp_path / "perf" / "charts").exists()   # EN dirs untouched


def test_en_chart_unchanged_against_committed(tmp_path):
    """Real data, EN path: re-rendering must reproduce the committed PNG pixels."""
    import numpy as np
    from PIL import Image
    tl = charts.load_timeline()
    for name, fn in (("cashflow_monthly", charts.cashflow_monthly),
                     ("activity_by_month", charts.activity_by_month)):
        new = tmp_path / f"{name}.png"
        fn(tl, new)
        base = (charts.FIN if name == "cashflow_monthly" else charts.PERF) / f"{name}.png"
        a = np.asarray(Image.open(base).convert("RGB"))
        b = np.asarray(Image.open(new).convert("RGB"))
        assert a.shape == b.shape and (a == b).all(), f"{name} EN render drifted"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_charts.py -q`
Expected: `test_render_all_fa_writes_charts_fa` FAILS (`render_all() takes 0 positional arguments`). `test_en_chart_unchanged_against_committed` should already PASS. It is the baseline guard, and must keep passing after the change.

- [ ] **Step 3: Implement**

- `render_all(lang="en")`: for `fa`, `perf_dir = PERF.with_name("charts_fa")` and `fin_dir = FIN.with_name("charts_fa")`. For `en` keep `PERF` / `FIN`. Pass `lang` to every chart function.
- `_chrome(ax, title, subtitle=None, xlab=None, ylab=None, lang="en")`: for `fa` put the title at `loc="right"` and the subtitle at `x=1, ha="right"`, so the Persian text block is right-aligned. EN keeps today's left alignment.
- Every literal title, subtitle, axis label, legend title and legend entry → `t("chart.<chart>.<name>", lang, **kw)`, with counts passed pre-formatted (`n=f"{len(nodes)}"`). `chart.cash.receipts`, `chart.cash.payments` and `chart.cash.net` are the legend entries.
- Chat names (legend entries, small-multiple titles) → `term("chat", chat, lang)`. Category labels in `category_breakdown`: EN keeps `k.replace("_", " ").title()`; FA uses `term("category", k, lang)`.
- Thread labels in `event_timeline`: `_trunc(thread_title(t, lang) or t.get("event_ref") or "", 30)`, importing `thread_title` from `.build_performance_report` inside the function body (avoids import cycles at module import).
- Numbers drawn as text (bar value labels `f"{v:,}"`, peak labels, the `_mfmt` tick formatter) and month tick labels: wrap the final string with `localize()` when `lang == "fa"`. The weekday tick labels are already Persian: keep them.
- Matplotlib already shapes Persian (see the comment above `fa()`). **Do not** add arabic_reshaper or python-bidi.
- Before rendering real charts, check disk: `df -h /c` (stop if < 1 GB).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_charts.py -q`. All PASS, including the EN pixel guard.
Run: `python -m pytest analysis_tools/tests/ -q`. All green.

- [ ] **Step 5: Visual check with the pseudo catalog** (sanity only: real Persian arrives in Task 6)

```bash
python - <<'EOF'
import json, shutil, tempfile
from pathlib import Path
from analysis_tools import i18n, charts
d = Path(tempfile.mkdtemp())
en = json.loads((i18n.PKG_DIR / "en.json").read_text(encoding="utf-8"))
(d / "en.json").write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
(d / "fa.json").write_text(json.dumps({k: "آزمایش " + v for k, v in en.items()}, ensure_ascii=False), encoding="utf-8")
(d / "hashes.json").write_text(json.dumps({k: i18n.sha(v) for k, v in en.items()}), encoding="utf-8")
shutil.copy(i18n.PKG_DIR / "glossary.json", d / "glossary.json")
i18n.set_catalog_dir(d)
out = Path(r"C:/Users/SURFAC~1/AppData/Local/Temp/claude/C--Users-Surface-Laptop-3-Downloads-Telegram-Desktop-anjoman-acc/4e5b9bc6-84eb-4765-8e18-8406d048ec03/scratchpad/charts_check")
out.mkdir(parents=True, exist_ok=True)
tl = charts.load_timeline()
charts.cashflow_monthly(tl, out / "cash.png", "fa")
charts.hour_histogram(tl, out / "hour.png", "fa")
EOF
```
Read `cash.png` and `hour.png` with the Read tool. Check that the Persian is joined, the title is right-aligned, the digits are Persian and the chat names are Persian. Report what you saw. Do **not** write into `reports/` in this task.

- [ ] **Step 6: Commit**

```bash
git add analysis_tools/charts.py analysis_tools/i18n/en.json analysis_tools/tests/test_charts.py
git commit -m "feat(charts): Persian chart variants (render_all(lang='fa') -> charts_fa/)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: `translate.py` + produce `fa.json`

**Files:**
- Create: `analysis_tools/translate.py`
- Create: `analysis_tools/tests/test_translate.py`
- Create (by running it): `analysis_tools/i18n/fa.json`, `analysis_tools/i18n/hashes.json`, `analysis/claude/i18n/*.json`

**Interfaces:**
- Consumes: `i18n.catalog`, `i18n.sha`, `i18n.number_tokens`, `i18n.set_catalog_dir`, `i18n.PKG_DIR`, `i18n.reload`; the complete `en.json` from Tasks 3–5.
- Produces: `translate.validate(en: str, fa: str) -> list[str]`, `translate.pending(en, fa, hashes) -> list[str]`, `translate.run(client, size=CHUNK, out_dir=None) -> dict` (`{"translated": int, "failed": {key: [problems]}}`), CLI `python -m analysis_tools.translate`.

- [ ] **Step 1: Write the failing tests** — `analysis_tools/tests/test_translate.py`

```python
import json
from types import SimpleNamespace

import pytest

from analysis_tools import i18n, translate


def test_validate_ok():
    assert translate.validate("Total {n} rows in `x.csv` (**12**)",
                              "مجموع {n} ردیف در `x.csv` (**12**)") == []


@pytest.mark.parametrize("fa,needle", [
    ("مجموع ردیف", "placeholders"),
    ("مجموع {n} {m} ردیف در `x.csv` (**12**)", "placeholders"),
    ("مجموع {n} ردیف در x.csv (**12**)", "code spans"),
    ("مجموع {n} ردیف در `x.csv` (**۱۳**)", "number tokens"),
    ("مجموع {n} ردیف در `x.csv` (12)", "bold"),
])
def test_validate_rejects(fa, needle):
    probs = translate.validate("Total {n} rows in `x.csv` (**12**)", fa)
    assert any(needle in p for p in probs), probs


def test_validate_edge_whitespace():
    assert any("whitespace" in p for p in translate.validate(" and more", "و بیشتر"))


def test_pending():
    en = {"a": "A", "b": "B", "c": "C"}
    fa = {"a": "الف", "b": "ب"}
    hashes = {"a": i18n.sha("A"), "b": "old"}
    assert translate.pending(en, fa, hashes) == ["b", "c"]


class FakeMessages:
    def __init__(self, script):
        self.script, self.calls = script, []

    def parse(self, **kw):
        payload = json.loads(kw["messages"][0]["content"])
        self.calls.append(payload)
        return self.script(payload)


def _resp(items, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, stop_details=None,
                           parsed_output=translate.Batch(items=[
                               translate.Item(key=k, fa=v) for k, v in items.items()]))


@pytest.fixture
def catdir(tmp_path, monkeypatch):
    (tmp_path / "en.json").write_text(json.dumps(
        {"k1": "One {n}", "k2": "Two `c` 5", "k3": "Three"}), encoding="utf-8")
    (tmp_path / "glossary.json").write_text("{}", encoding="utf-8")
    i18n.set_catalog_dir(tmp_path)
    monkeypatch.setattr(translate, "CACHE", tmp_path / "cache")
    yield tmp_path
    i18n.set_catalog_dir(None)


GOOD = {"k1": "یک {n}", "k2": "دو `c` 5", "k3": "سه"}


def test_run_happy_path_and_cache(catdir):
    msgs = FakeMessages(lambda p: _resp({k: GOOD[k] for k in p["items"]}))
    res = translate.run(SimpleNamespace(messages=msgs), size=2, out_dir=catdir)
    assert res["failed"] == {} and res["translated"] == 3
    fa = json.loads((catdir / "fa.json").read_text(encoding="utf-8"))
    hashes = json.loads((catdir / "hashes.json").read_text(encoding="utf-8"))
    assert fa == GOOD and hashes["k1"] == i18n.sha("One {n}")
    # second run: nothing pending, no API calls
    n_calls = len(msgs.calls)
    i18n.reload()
    translate.run(SimpleNamespace(messages=msgs), size=2, out_dir=catdir)
    assert len(msgs.calls) == n_calls


def test_run_splits_on_truncation(catdir):
    def script(p):
        if len(p["items"]) > 1:
            return _resp({}, stop="max_tokens")
        return _resp({k: GOOD[k] for k in p["items"]})
    msgs = FakeMessages(script)
    res = translate.run(SimpleNamespace(messages=msgs), size=3, out_dir=catdir)
    assert res["failed"] == {}
    assert [len(c["items"]) for c in msgs.calls] == [3, 1, 2, 1, 1]


def test_run_retries_with_notes_then_gives_up(catdir):
    def script(p):
        return _resp({k: ("یک" if k == "k1" else GOOD[k]) for k in p["items"]})
    msgs = FakeMessages(script)
    res = translate.run(SimpleNamespace(messages=msgs), size=3, out_dir=catdir)
    assert list(res["failed"]) == ["k1"]
    assert any("notes" in c and "k1" in c["notes"] for c in msgs.calls)
    assert len([c for c in msgs.calls if "k1" in c["items"]]) == translate.MAX_ATTEMPTS
    fa = json.loads((catdir / "fa.json").read_text(encoding="utf-8"))
    assert "k1" not in fa and fa["k3"] == "سه"


def test_run_drops_orphans(catdir):
    (catdir / "fa.json").write_text(json.dumps({"gone": "x"}), encoding="utf-8")
    (catdir / "hashes.json").write_text(json.dumps({"gone": "h"}), encoding="utf-8")
    i18n.reload()
    msgs = FakeMessages(lambda p: _resp({k: GOOD[k] for k in p["items"]}))
    translate.run(SimpleNamespace(messages=msgs), size=3, out_dir=catdir)
    fa = json.loads((catdir / "fa.json").read_text(encoding="utf-8"))
    assert "gone" not in fa


def test_main_requires_key(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as e:
        translate.main([])
    assert e.value.code == 2 and "ANTHROPIC_API_KEY" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest analysis_tools/tests/test_translate.py -q`
Expected: FAIL (`ImportError: cannot import name 'translate'`)

- [ ] **Step 3: Implement `analysis_tools/translate.py`**

```python
"""Translate the EN report catalog to Persian through the Claude API.

Only this module calls the API; builders read the committed fa.json. Keys
whose English changed since translation (hashes.json) or that are missing are
re-translated in chunks; every result is validated (placeholders, backtick
spans, number tokens, bold markers, edge whitespace) before it is accepted.
Raw chunk responses are cached under analysis/claude/i18n/ so re-runs with an
unchanged catalog make no API calls.

Run (VPN on; the API is geo-blocked from this machine otherwise):
    ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" \
        python -m analysis_tools.translate
"""
import argparse
import json
import os
import re
import sys

from pydantic import BaseModel

from . import i18n
from .common import ROOT

MODEL = "claude-opus-5-5"
CHUNK = 60
MAX_ATTEMPTS = 3
CACHE = ROOT / "analysis/claude/i18n"

SYSTEM = """You translate fragments of an internal board report of the Sharif \
University of Technology physics student association (انجمن علمی فیزیک) from \
English into formal written Persian suited to a board document.

Input: JSON with "glossary" (fixed English→Persian terms), "items" (key → English \
fragment) and optionally "notes" (key → problems found in your previous attempt).
Output: one item per input key, with the Persian translation in "fa".

Rules for every fragment:
1. Keep every {placeholder} exactly (same names, same count). Move it where Persian grammar needs it.
2. Copy every `backtick span` verbatim, backticks included.
3. Keep every number exactly as written, in ASCII digits. Never turn numbers into words or words into numbers. Never convert Gregorian dates to Jalali. Keep ranges like 1404/04 – 1405/07 as written.
4. Keep **bold** markers around the corresponding Persian words (same number of ** pairs).
5. Keep IDs (TX0036), @handles, URLs, file names, slugs (dept-weekly-seminars) and Latin proper names verbatim.
6. Whenever a glossary concept occurs, use its glossary Persian term.
7. Use Persian punctuation (، ؛ ؟) and standard ZWNJ spellings (می‌شود، داده‌ها).
8. Fragments can begin or end mid-sentence. Preserve leading and trailing spaces exactly.
9. Keys starting with "data.thread." are event-thread titles. Translate their English words and keep their Persian words as they are.
10. If "notes" lists problems for a key, fix exactly those problems."""


class Item(BaseModel):
    key: str
    fa: str


class Batch(BaseModel):
    items: list[Item]


class Truncated(Exception):
    pass


_PH = re.compile(r"\{(\w+)\}")
_CODE = re.compile(r"`[^`]*`")


def validate(en, fa):
    probs = []
    if sorted(_PH.findall(en)) != sorted(_PH.findall(fa)):
        probs.append(f"placeholders {sorted(_PH.findall(en))} != {sorted(_PH.findall(fa))}")
    if sorted(_CODE.findall(en)) != sorted(_CODE.findall(fa)):
        probs.append("code spans changed (copy every `...` span verbatim)")
    if i18n.number_tokens(_PH.sub("", en)) != i18n.number_tokens(_PH.sub("", fa)):
        probs.append("number tokens changed (keep every number exactly, ASCII digits)")
    if en.count("**") != fa.count("**"):
        probs.append("bold markers changed")
    if en[:1].isspace() != fa[:1].isspace() or en[-1:].isspace() != fa[-1:].isspace():
        probs.append("edge whitespace changed (preserve leading/trailing spaces)")
    try:
        fa.format(**{p: "x" for p in _PH.findall(en)})
    except (KeyError, IndexError, ValueError) as e:
        probs.append(f"str.format fails: {e!r}")
    return probs


def pending(en, fa, hashes):
    return [k for k in sorted(en) if k not in fa or hashes.get(k) != i18n.sha(en[k])]


def call_model(client, items, glossary, notes=None, attempt=0):
    body = {"glossary": glossary, "items": items}
    if notes:
        body["notes"] = notes
    if attempt:
        body["attempt"] = attempt  # retries must not be served from the cache
    payload = json.dumps(body, ensure_ascii=False, sort_keys=True)
    cache = CACHE / f"{i18n.sha(MODEL + SYSTEM + payload)}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    resp = client.messages.parse(model=MODEL, max_tokens=16000, system=SYSTEM,
                                 messages=[{"role": "user", "content": payload}],
                                 output_format=Batch)
    if resp.stop_reason == "max_tokens":
        raise Truncated()
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"model refused chunk: {resp.stop_details}")
    out = {it.key: it.fa for it in resp.parsed_output.items}
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _write(out_dir, fa, hashes):
    (out_dir / "fa.json").write_text(
        json.dumps(dict(sorted(fa.items())), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    (out_dir / "hashes.json").write_text(
        json.dumps(dict(sorted(hashes.items())), indent=1) + "\n", encoding="utf-8")


def run(client, size=CHUNK, out_dir=None):
    out_dir = out_dir or i18n.PKG_DIR
    en = i18n.catalog("en")
    fa = {k: v for k, v in i18n.catalog("fa").items() if k in en}
    hashes = {k: v for k, v in i18n.catalog("hashes").items() if k in en}
    glossary = i18n.catalog("glossary")
    todo, failed, done = pending(en, fa, hashes), {}, 0
    for attempt in range(MAX_ATTEMPTS):
        if not todo:
            break
        queue = [todo[i:i + size] for i in range(0, len(todo), size)]
        retry = []
        while queue:
            keys = queue.pop(0)
            notes = {k: failed[k] for k in keys if k in failed} or None
            try:
                got = call_model(client, {k: en[k] for k in keys}, glossary, notes, attempt)
            except Truncated:
                if len(keys) == 1:
                    failed[keys[0]] = ["output truncated"]
                    retry.append(keys[0])
                    continue
                mid = len(keys) // 2
                queue[:0] = [keys[:mid], keys[mid:]]
                continue
            for k in keys:
                probs = ["missing from response"] if k not in got else validate(en[k], got[k])
                if probs:
                    failed[k] = probs
                    retry.append(k)
                else:
                    fa[k], hashes[k] = got[k], i18n.sha(en[k])
                    failed.pop(k, None)
                    done += 1
        _write(out_dir, fa, hashes)
        todo = retry
    _write(out_dir, fa, hashes)
    i18n.reload()
    return {"translated": done, "failed": failed}


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set. Run:\n  ANTHROPIC_API_KEY=\"$(cat "
              "~/.config/anthropic/anjoman_key)\" python -m analysis_tools.translate",
              file=sys.stderr)
        sys.exit(2)
    import anthropic
    res = run(anthropic.Anthropic(max_retries=4))
    print(f"translated {res['translated']} keys; {len(res['failed'])} failed")
    for k, p in res["failed"].items():
        print(f"  FAILED {k}: {'; '.join(p)}", file=sys.stderr)
    sys.exit(1 if res["failed"] else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest analysis_tools/tests/test_translate.py -q`. All PASS.
Run: `python -m pytest analysis_tools/tests/ -q`. All green.

- [ ] **Step 5: Commit the tool** (before any API call)

```bash
git add analysis_tools/translate.py analysis_tools/tests/test_translate.py
git commit -m "feat(i18n): Claude API catalog translator with validation and cache

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Connectivity check** (the user turns on their VPN first)

```bash
ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" python -c "import anthropic; print([m.id for m in anthropic.Anthropic().models.list(limit=5)])"
```
Expected: a list of model ids. If you get `PermissionDeniedError` / 403 `Request not allowed`, the network is still blocked. **Stop and report BLOCKED** (the user must enable the VPN). Do not retry in a loop. A 401 means the key itself is rejected: report BLOCKED with that status.

- [ ] **Step 7: Translate**

```bash
ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" python -m analysis_tools.translate
```
Expected: `translated N keys; 0 failed`. If some keys failed after 3 attempts, hand-write their Persian in `fa.json`, following the same rules, and set their `hashes.json` entry to `i18n.sha(en[key])`. Then re-run `translate` (which must report 0 pending) and list those keys in your report.

- [ ] **Step 8: Spot-read the translation.** Open `fa.json` and read at least 25 entries across `fin.*`, `perf.*`, `chart.*`, `data.thread.*`. Check register (formal), glossary terms and meaning. Fix wrong renderings by editing `fa.json` directly (re-validate with `python -c "from analysis_tools import i18n, translate; en=i18n.catalog('en'); fa=i18n.catalog('fa'); print({k: p for k in fa if (p := translate.validate(en[k], fa[k]))})"`, which must print `{}`).

- [ ] **Step 9: Commit**

```bash
git add analysis_tools/i18n/fa.json analysis_tools/i18n/hashes.json analysis/claude/i18n
git commit -m "feat(i18n): Persian catalog translated via Claude API (validated, cached)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Build the Persian reports, parity tests, visual verification

**Files:**
- Modify: `analysis_tools/tests/test_report_i18n.py` (append)
- Create (by building): `reports/2026-10-14/financial_monthly/{Anjoman_Financial_Report_Monthly_FA.md,.pdf,.html}`, `reports/2026-10-14/financial_monthly/charts_fa/*.png`, `reports/2026-10-14/performance/{Anjoman_Performance_Activity_Report_FA.md,.pdf,.html}`, `reports/2026-10-14/performance/charts_fa/*.png`
- Modify: `README.md` (progress line + layout rows)

**Interfaces:**
- Consumes: everything above, with the real `fa.json`.
- Produces: the deliverables, plus tests that pin them.

- [ ] **Step 1: Append the integrity and parity tests**

```python
import glob
from analysis_tools import translate
from analysis_tools.common import ROOT, LEDGER_DIR


def test_catalog_integrity():
    en, fa, hashes = i18n.catalog("en"), i18n.catalog("fa"), i18n.catalog("hashes")
    assert set(en) == set(fa) == set(hashes)
    assert all(hashes[k] == i18n.sha(en[k]) for k in en)
    bad = {k: p for k in en if (p := translate.validate(en[k], fa[k]))}
    assert bad == {}


def test_every_en_key_is_referenced():
    code = "".join(open(p, encoding="utf-8").read()
                   for p in glob.glob(str(ROOT / "analysis_tools/*.py")))
    orphans = [k for k in i18n.catalog("en")
               if not k.startswith("data.") and f'"{k}"' not in code]
    assert orphans == []


def _reason_tokens(lang):
    """Number tokens of the flagged-table review reasons. The EN ledger and the
    precedent FA ledger are different source texts, so these are excluded from
    parity. Reuses the builder's own _reason() so the exclusion matches it exactly."""
    import json
    from collections import Counter
    from analysis_tools.correlate import _load_tx
    fa_rows = ({x["id"]: x for x in json.loads(fin.FA_LEDGER.read_text(encoding="utf-8"))["ledger"]}
               if lang == "fa" else {})
    tok = Counter()
    for r in _load_tx():
        if r["status"] == "Review" and r["id"] not in fin.VOLUNTEER_BLOCK:
            tok += i18n.number_tokens(fin._reason(r, lang, fa_rows))
    return tok


@pytest.mark.parametrize("mod", ["fin", "perf"])
def test_number_parity(mod):
    m = fin if mod == "fin" else perf
    en_tok = i18n.number_tokens(m.render("en"))
    fa_tok = i18n.number_tokens(m.render("fa"))
    if mod == "fin":
        en_tok -= _reason_tokens("en")
        fa_tok -= _reason_tokens("fa")
    assert en_tok == fa_tok, (en_tok - fa_tok, fa_tok - en_tok)


@pytest.mark.parametrize("mod,kinds", [("fin", ("project", "ledger_category")),
                                       ("perf", ("chat", "category", "phase"))])
def test_glossary_enforced(mod, kinds):
    m = fin if mod == "fin" else perf
    en_text, fa_text = m.render("en"), m.render("fa")
    g = i18n.catalog("glossary")
    for kind in kinds:
        for en_term, fa_term in g[kind].items():
            if any(f in en_text for f in (f"| {en_term} |", f"### {en_term} ")):
                assert i18n.localize(fa_term) in fa_text, (kind, en_term)


def test_fa_outputs_current():
    """Committed FA markdown equals a fresh render (no stale deliverables)."""
    assert fin.OUT_FA.read_text(encoding="utf-8") == fin.render("fa")
    assert perf.OUT_FA.read_text(encoding="utf-8") == perf.render("fa")
```

- [ ] **Step 2: Run the new tests.** `test_fa_outputs_current` fails because the files don't exist yet. Everything else must pass. If `test_number_parity` fails, print the two difference Counters, find the template or `term` value that changed a number, and fix it at the source (`fa.json` entry or glossary). Then re-run.

- [ ] **Step 3: Build** (check disk first: `df -h /c`, stop if < 1 GB)

```bash
python -c "from analysis_tools import charts; print(charts.render_all('fa'))"
python -m analysis_tools.build_financial_report --lang fa
python -m analysis_tools.build_performance_report --lang fa
```
Expected: 8 PNGs under the two `charts_fa/` dirs; both builds print their gate lines with no assertion errors.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest analysis_tools/tests/ -q`. All green, including `test_fa_outputs_current`. Confirm the EN reports are untouched: `git status --short reports/` must list only new `_FA.*` files and `charts_fa/` dirs.

- [ ] **Step 5: Visual verification (required)**

```bash
S="C:/Users/SURFAC~1/AppData/Local/Temp/claude/C--Users-Surface-Laptop-3-Downloads-Telegram-Desktop-anjoman-acc/4e5b9bc6-84eb-4765-8e18-8406d048ec03/scratchpad/visual"
mkdir -p "$S"
pdftoppm -r 70 -png reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly_FA.pdf "$S/fin"
pdftoppm -r 70 -png -f 1 -l 6 reports/2026-10-14/performance/Anjoman_Performance_Activity_Report_FA.pdf "$S/perf"
ls "$S"
```
Read with the Read tool: financial pages 1, 2 and 3 (the title, the monthly cashflow table, and a wide 1404/1405 schedule table) and the page holding the flagged table; performance pages 1, 3, 5 and 6 (with a chart and the case-study stage table); and each `charts_fa/*.png`. For each, check that letters are joined, text flows right to left, the table's first column is at the right, numbers are not reversed (`۱۱۲٬۵۵۲٬۰۰۰`, `۱۳:۳۰`), Latin IDs (`TX0036`, `dept-weekly-seminars`) are intact, nothing is clipped or overflowing, and the footer reads «صفحه ۱…» in Persian digits. Fix any defect in `report_common` CSS or the builders, rebuild, and re-check. In the task report, list each page you inspected and what you saw.

- [ ] **Step 6: README.** Under the 2026-10-14 progress entry, add: `- 2026-10-18 — Persian (FA) versions of both 2026-10-14 reports: catalog-driven (analysis_tools/i18n, translated once via the Claude API), RTL PDFs via WeasyPrint, Persian charts in charts_fa/.` Add layout rows for `analysis_tools/i18n/` and the `_FA` files, following the existing table format.

- [ ] **Step 7: Commit**

```bash
git add reports/2026-10-14 README.md analysis_tools/tests/test_report_i18n.py
git commit -m "feat(reports): Persian versions of the 2026-10-14 financial and performance reports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Spec coverage map

| Spec section | Task |
|---|---|
| §2 decisions (catalog, SDK, WeasyPrint, Tahoma, charts_fa, digits, dates) | 1, 2, 5, 6 |
| §3.1 i18n module (`t`, `term`, `dt`, `localize`, staleness) | 1 |
| §3.2 builder refactor (render/build, outputs, gates in both modes) | 3, 4 |
| §3.3 translate.py (key check, chunks, validation, retries, truncation, cache, number preservation) | 6 |
| §3.4 RTL PDF (markdown→HTML, CSS, numeric cells, wide tables, base_url) | 2 |
| §3.5 Persian charts | 5 |
| §4 tests 1–7 (byte-identity, catalog integrity, number parity, formatting units, glossary, validator, gates) | 3, 4, 1, 7, 6, 3 |
| §4 visual verification | 2 (smoke), 5 (charts), 7 (full) |
| §5 error handling (missing key, stale catalog, mismatch retries, truncation, HTTP, disk) | 1, 6, 5, 7 |
