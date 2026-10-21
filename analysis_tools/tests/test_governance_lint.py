# -*- coding: utf-8 -*-
"""Content gates for the governance masters (spec §3 canon)."""
from analysis_tools.governance_lint import (
    normalize_fa, to_en_digits, findings_for, cross_doc_findings,
    run_all, D1_MADDI_COUNT,
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


# ---------------------------------------------------------------------------
# Final fix wave (F1-F8): extended reference and invariant checks
# ---------------------------------------------------------------------------

_FA = "۰۱۲۳۴۵۶۷۸۹"


def _fa(n: int) -> str:
    return "".join(_FA[int(c)] for c in str(n))


def _d1_full(tabsare: dict[int, list[str]] | None = None, extra: str = "") -> str:
    """D1 fixture with مواد ۱..۳۹; tabsare maps ماده -> list of تبصره labels
    ("" for an unnumbered «تبصره:», "۱" for «تبصره ۱:»)."""
    tabsare = tabsare or {}
    parts = ["# اساسنامه انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف\n"]
    for n in range(1, 40):
        parts.append(f"ماده {_fa(n)} (عنوان): متن.\n")
        for lab in tabsare.get(n, []):
            head = "تبصره:" if lab == "" else f"تبصره {lab}:"
            parts.append(f"{head} متن تبصره.\n")
    return "\n".join(parts) + "\n" + extra


D2_FIX = """# شیوه‌نامه داخلی شورای مرکزی

## فصل ۱ — ترکیب

۱-۱. ترکیب.

۱-۲. نقش‌ها.

## فصل ۴ — رویدادها

۴-۱. گردش‌کار.

۴-۲. تیم.

۴-۳. مجوز.

## فصل ۶ — مجمع

۶-۱. جلسه هماهنگی.

۶-۲. خودگردانی.

۶-۳. پشتیبانی.

۶-۴. رابطه شورا و مجمع.

## پیوست الف — جدول تصمیم‌گیری

متن.

## پیوست ب — چک‌لیست رویداد

متن.
"""

D3_FIX = """# منشور مجمع

## فصل ۵: نقش‌ها

۵-۱. نقش.

۵-۲. سبد.

۵-۳. هماهنگ‌کننده.

## پیوست: چارچوب گفت‌وگو و مشارکت در چای

زمان جلسه متعلق به همه است؛ کسانی که کمتر صحبت کرده‌اند؛ فرصت گفت‌وگوی جمعی را از بین می‌برد؛
چای محلی برای تخریب اعتبار افراد نیست؛ شنیده شدن نقد به معنای تأیید آن نیست.
"""

D4_FIX = """# شیوه‌نامه اجرایی مجمع

## فصل ۴: از ایده تا تیم

۴-۱. طرح ایده.

۴-۲. قاعده آستانه.

۴-۳. مسیر طرح.

## پیوست ۱: چارچوب چای

متن.

## پیوست ۲: قالب گزارش جلسه

متن.
"""


def _x(**over):
    texts = {"D1": _d1_full(), "D2": D2_FIX, "D3": D3_FIX, "D4": D4_FIX}
    texts.update(over)
    return cross_doc_findings(texts)


def test_masters_clean():
    # F1: the real masters must pass every gate (the only automatic gate).
    assert run_all() == []


def test_cross_doc_band_refs_resolve():
    # F2: «(سند، N-M)» incl. lists and ranges must resolve in the named document.
    d3 = D3_FIX + "\nمتن (شیوه‌نامه داخلی شورا، ۴-۱، ۴-۲ و ۶-۴) و (شیوه‌نامه داخلی شورا، ۹-۹).\n"
    out = _x(D3=d3)
    assert any("۹-۹" in f and f.startswith("D3") for f in out)
    assert not any(t in f for f in out for t in ("۴-۱", "۴-۲", "۶-۴"))
    # range: ۴-۱ تا ۴-۵ -> ۴-۴ and ۴-۵ are missing in D2_FIX
    d4 = D4_FIX + "\nمتن (شیوه‌نامه داخلی شورا، ۴-۱ تا ۴-۵).\n"
    out = _x(D4=d4)
    assert any("۴-۴" in f for f in out) and any("۴-۵" in f for f in out)
    assert not any("۴-۳" in f for f in out)
    # منشور مجمع and شیوه‌نامه اجرایی مجمع targets
    d2 = D2_FIX + "\nمتن (منشور مجمع، ۵-۳ و ۵-۷) و (شیوه‌نامه اجرایی مجمع، ۴-۲؛ اساسنامه، ماده ۸).\n"
    out = _x(D2=d2)
    assert any("۵-۷" in f and "منشور" in f for f in out)
    assert not any("۵-۳" in f or "۴-۲" in f for f in out)


def test_cross_doc_annex_refs_resolve():
    # F2: «… پیوست X» must resolve to a «## پیوست X» heading of the named document.
    d4 = D4_FIX + (
        "\nمتن (شیوه‌نامه داخلی شورا، پیوست الف) و (شیوه‌نامه داخلی شورا، پیوست ج)"
        " و (منشور مجمع، ۵-۲ و پیوست).\n")
    out = _x(D4=d4)
    assert any("پیوست ج" in f for f in out)
    assert not any("پیوست الف" in f for f in out)
    assert not any("منشور" in f for f in out)
    d2 = D2_FIX + "\nمتن (شیوه‌نامه اجرایی مجمع، پیوست ۹) و (شیوه‌نامه اجرایی مجمع، پیوست ۲).\n"
    out = _x(D2=d2)
    assert any("پیوست ۹" in f for f in out)
    assert not any("پیوست ۲" in f for f in out)


def test_internal_band_refs_resolve():
    # F2: bare «(N-M)» (and «مطابق N-M») inside a document resolve to its own items.
    bad = D2_FIX + "\nمتن (۱-۳) و مطابق ۴-۹ و (۱-۱ و ۱-۲).\n"
    out = findings_for("D2", bad)
    assert any("۱-۳" in f for f in out) and any("۴-۹" in f for f in out)
    assert not any("۱-۱" in f or "۱-۲" in f for f in out)
    # آیین‌نامه بند and cross-document tokens are not internal references
    ok = D2_FIX + "\nتکلیف قانونی (آیین‌نامه، بند ۱۶-۱۱) و (منشور مجمع، ۵-۳) و (۴-۱ تا ۴-۳).\n"
    out = findings_for("D2", ok)
    assert not any("۱۶-۱۱" in f or "۵-۳" in f for f in out)
    assert not any("بند" in f for f in out)


def test_internal_annex_refs_resolve():
    # F2: an internal «پیوست X» names an existing annex of the same document.
    out = findings_for("D4", D4_FIX + "\nبا قالب پیوست ۹ و پیوست ۲ و پیوست‌های ۱ تا ۲.\n")
    assert any("پیوست ۹" in f for f in out)
    assert not any("پیوست ۲" in f for f in out)


def test_cross_doc_maddi_lists():
    # F3: «مواد X، Y و Z» / «مواد X و Y» / «مواد X تا Y» in either order, all members.
    d2 = D2_FIX + (
        "\nمتن (اساسنامه، مواد ۱۷، ۱۸ و ۴۲) و مواد ۱۰ و ۴۵ اساسنامه"
        " و (اساسنامه، مواد ۳۸ تا ۴۱).\n")
    out = _x(D2=d2)
    for n in (42, 45, 40, 41):
        assert any(f"ماده {n} " in f for f in out), n
    for n in (17, 18, 10, 38, 39):
        assert not any(f"ماده {n} " in f for f in out), n


def test_tabsare_refs_exist():
    # F4: «تبصره K ماده N» / «ماده N، تبصره K» must exist in D1.
    d1 = _d1_full({8: ["۱", "۲"], 10: [""], 11: ["۱", "۲", "۳"]})
    d2 = D2_FIX + (
        "\nالف (اساسنامه، تبصره ۳ ماده ۸) ب (اساسنامه، تبصره ۲ ماده ۸)"
        " ج (اساسنامه، تبصره ماده ۱۰) د تبصره ۱ ماده ۱۰ اساسنامه"
        " هـ (اساسنامه، ماده ۸، تبصره ۴) و (اساسنامه، تبصره ۲ و ۳ ماده ۱۱)"
        " ز (آیین‌نامه، تبصره ۳ ماده ۱۷).\n")
    out = _x(D1=d1, D2=d2)
    tab = [f for f in out if "تبصره" in f]
    assert any("تبصره 3 ماده 8" in f for f in tab)
    assert any("تبصره 1 ماده 10" in f for f in tab)
    assert any("تبصره 4 ماده 8" in f for f in tab)
    assert not any("تبصره 2 ماده 8" in f for f in tab)
    assert not any("ماده 11" in f for f in tab)
    assert not any("ماده 17" in f for f in tab)
    assert len(tab) == 3
    # D1-internal tabsare reference
    d1_bad = _d1_full({8: ["۱", "۲"]}, extra="مطابق تبصره ۵ ماده ۸ همین اساسنامه.\n")
    assert any("تبصره 5 ماده 8" in f for f in findings_for("D1", d1_bad))


def test_d1_internal_maddi_refs():
    # F5: «ماده N همین اساسنامه» / «مواد X تا Y همین اساسنامه» must exist.
    d1 = _d1_full(extra="مطابق ماده ۴۵ همین اساسنامه و مواد ۱۱ تا ۱۳ همین اساسنامه.\n")
    out = findings_for("D1", d1)
    assert any("ماده 45" in f for f in out)
    assert not any("ماده 11" in f or "ماده 12" in f for f in out)


def test_council_size_needs_haft_nafar():
    # F6: «هفته» must not satisfy the council-size invariant; «هفت نفر» must.
    out = findings_for("D1", D1_MIN + "\nجلسه هفتگی هر هفته برگزار می‌شود.\n")
    assert any("هفت" in f for f in out)
    out = findings_for("D1", D1_MIN + "\nشورا از هفت نفر تشکیل می‌شود.\n")
    assert not any("هفت" in f for f in out)


def test_banned_phrase_variants():
    # F7: ZWNJ and multi-space variants of «مجمع عمومی» are also banned.
    for variant in ("مجمع‌عمومی", "مجمع  عمومی"):
        out = findings_for("D3", "# منشور مجمع\n\nمتن " + variant + " است.\n")
        assert any("مجمع عمومی" in f for f in out), variant
