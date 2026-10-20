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
    assert normalize_fa("اطالعات و اعالم") == "اطلاعات و اعلام"
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


def test_cross_doc_maddi_refs():
    # Minimal D1 with مواد ۱..۳۹ fully present (no continuity findings expected to matter here).
    header = "# اساسنامه انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف\n\n"
    fa_digits = "۰۱۲۳۴۵۶۷۸۹"

    def to_fa(n: int) -> str:
        return "".join(fa_digits[int(c)] for c in str(n))

    maddi_lines = "\n".join(
        f"ماده {to_fa(n)} (عنوان): متن." for n in range(1, 40)
    )
    d1 = header + maddi_lines + "\n"
    d2 = (
        "# شیوه‌نامه داخلی شورای مرکزی\n\n"
        "مطابق (اساسنامه، ماده ۴۰) و مواد ۱۰ تا ۱۳ اساسنامه عمل می‌شود.\n"
    )
    out = cross_doc_findings({"D1": d1, "D2": d2})
    forty = [f for f in out if "40" in f]
    ten_to_thirteen = [f for f in out if any(str(n) in f for n in range(10, 14))]
    assert len(forty) == 1
    assert ten_to_thirteen == []
