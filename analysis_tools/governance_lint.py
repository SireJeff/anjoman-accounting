# -*- coding: utf-8 -*-
"""Content gates for the governance masters.

Enforces the canon of spec §3 plus per-document structure (spec §4-§7).
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
    """Heuristic fix for PyMuPDF lam-alef extraction artifacts.

    Extractions render Persian لا as «ال» mid-word (اطلاعات -> اطالعات).
    Rule: inside a word (previous char is an Arabic-script letter), swap
    the sequence alef+lam to lam+alef. Word-initial alef+lam (definite
    article, e.g. «الحاق») is left untouched.

    This heuristic also rewrites genuine mid-word «ال» occurrences (e.g.
    سال -> سلا, مالی -> ملای, بالا -> بلاا), so its output must be reviewed
    by hand. Never apply it to authored masters — only to raw PDF-extracted
    text that is suspected to carry this artifact. findings_for() and
    cross_doc_findings() deliberately do NOT call this function.
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


def _maddi_numbers(text: str) -> list[int]:
    return [int(n) for n in re.findall(r"^\s*ماده\s+(\d+)", to_en_digits(text), re.M)]


def _block_numbers(text: str) -> dict[int, list[int]]:
    """Map fasl-number -> ordered block numbers from 'N-M.' items."""
    blocks: dict[int, list[int]] = {}
    for fasl, blk in re.findall(r"^([۰-۹]+)-([۰-۹]+)\.", text, re.M):
        blocks.setdefault(int(to_en_digits(fasl)), []).append(int(to_en_digits(blk)))
    return blocks


def findings_for(doc_key: str, text: str) -> list[str]:
    """Run every content gate on the raw master text.

    normalize_fa() is intentionally NOT applied here: it is a heuristic for
    PyMuPDF extraction artifacts and corrupts genuine Persian words
    (سال->سلا, مالی->ملای, بالا->بلاا) when run over authored masters.
    """
    out: list[str] = []
    for b in BANNED:
        if b in text:
            out.append(f"عبارت ممنوع: «{b}»")
    # citation rule: parentheticals naming ماده/تبصره/فصل need a source qualifier
    for m in re.finditer(r"\(([^)]*)\)", text):
        inner = m.group(1)
        if re.search(r"ماده|تبصره|فصل", inner) and not re.search(
                r"آیین‌نامه|اساسنامه|شیوه‌نامه|منشور", inner):
            out.append(f"ارجاع بدون قید منبع: «({inner})» — قالب درست: (آیین‌نامه، ماده …) یا (اساسنامه، ماده …)")
    if re.search(r"اکثریت\s+حاضران", text):
        out.append("قالب رأی: به‌جای «اکثریت حاضران» از «بیش از نیمی از حاضران» یا «رأی X از کل ۷ نفر» استفاده شود")
    if doc_key == "D1":
        nums = _maddi_numbers(text)
        seen = set()
        for n in nums:
            if n in seen:
                out.append(f"ماده {n} تکرار شده است")
            seen.add(n)
        missing = [n for n in range(1, D1_MADDI_COUNT + 1) if n not in seen]
        if missing:
            out.append(f"ماده‌های غایب: {missing}")
        for needle, label in [("اردیبهشت", "بازه انتخابات (۱۰ اردیبهشت تا ۱۰ خرداد)"),
                              ("بیست", "حداقل ۲۰ عضو"), ("هفت", "ترکیب هفت‌نفره شورا (۷ نفر)")]:
            if needle not in text:
                out.append(f"ناکافی/غایب: {label}")
    else:
        expected = {"D2": D2_FASL_COUNT, "D3": D3_FASL_COUNT, "D4": D4_FASL_COUNT}[doc_key]
        fasls = sorted(set(int(to_en_digits(f)) for f in re.findall(r"^## فصل ([۰-۹]+)", text, re.M)))
        miss = [n for n in range(1, expected + 1) if n not in fasls]
        if miss:
            out.append(f"فصل‌های غایب: {miss}")
        for fasl, blocks in _block_numbers(text).items():
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
    """Cross-document checks over raw master text (no normalize_fa)."""
    out: list[str] = []
    d1 = texts.get("D1", "")
    d1_nums = set(_maddi_numbers(d1))
    maddi_ref_re = re.compile(
        r"ماده\s+(\d+)(?:\s+تا\s+(\d+))?\s+اساسنامه"       # ماده N [تا M] اساسنامه
        r"|اساسنامه،?\s*ماده\s+(\d+)(?:\s+تا\s+(\d+))?"     # اساسنامه[،] ماده N [تا M]
        r"|مواد\s+(\d+)\s+تا\s+(\d+)\s+اساسنامه"            # مواد N تا M اساسنامه
        r"|اساسنامه،?\s*مواد\s+(\d+)\s+تا\s+(\d+)"          # اساسنامه[،] مواد N تا M
    )
    for key, text in texts.items():
        if key == "D1":
            continue
        for m in maddi_ref_re.finditer(to_en_digits(text)):
            groups = [g for g in m.groups() if g is not None]
            lo = int(groups[0])
            hi = int(groups[1]) if len(groups) > 1 else lo
            for n in range(lo, hi + 1):
                if n not in d1_nums:
                    out.append(f"{key}: ارجاع به ماده {n} اساسنامه که وجود ندارد")
    d3 = texts.get("D3", "")
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
