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


# --- reference resolution (final fix wave F2-F5) ----------------------------
#
# A «بند» reference is a Persian-digit token «N-M»; an annex reference is
# «پیوست» optionally followed by a label (الف/ب/ج or Persian digits). Lists use
# «،» and «و», ranges use «تا». Cross-document references name the target
# document right before a «،»; everything else in D2-D4 that is not an
# آیین‌نامه «بند» citation is an internal reference to the same document.

_BAND =r"[۰-۹]+-[۰-۹]+"
_ANNEX = r"پیوست(?:\s+(?:الف|ب|ج|[۰-۹]+))?(?![\w‌])"
_SEP = r"\s*(?:،|و|تا)\s*"
_REF = rf"(?:{_BAND}|{_ANNEX})"
_SRC_NAMES = {
    "D2": "شیوه‌نامه داخلی شورا",
    "D3": "منشور مجمع",
    "D4": "شیوه‌نامه اجرایی مجمع",
}
_XREF_RE = re.compile(
    r"(?P<src>شیوه‌نامه داخلی شورا(?:ی مرکزی)?|منشور مجمع|شیوه‌نامه اجرایی مجمع)"
    rf"،\s*(?P<refs>{_REF}(?:{_SEP}{_REF})*)")
_AIIN_BAND_RE = re.compile(
    rf"آیین‌نامه،?\s*بند\s+{_BAND}(?:{_SEP}{_BAND})*|بند\s+{_BAND}\s+آیین‌نامه")
_BAND_LIST_RE = re.compile(rf"{_BAND}(?:{_SEP}{_BAND})*")
_ANNEX_HEAD_RE = re.compile(r"^##\s+پیوست(?:\s+([^\s:—]+))?", re.M)


def _src_key(src: str) -> str:
    if src.startswith("منشور"):
        return "D3"
    return "D4" if "اجرایی" in src else "D2"


def _band_set(text: str) -> set[tuple[int, int]]:
    return {(f, b) for f, bs in _block_numbers(text).items() for b in bs}


def _annex_labels(text: str) -> list[str]:
    """Labels of «## پیوست X» headings ("" for an unlabelled «## پیوست:»)."""
    return [to_en_digits(lab) for lab in _ANNEX_HEAD_RE.findall(text)]


def _expand_refs(refs: str) -> list[str]:
    """Split a reference list into tokens; «N-M تا N-K» expands within one فصل."""
    toks = re.findall(rf"{_BAND}|{_ANNEX}|(?<![\w‌])تا(?![\w‌])", refs)
    out: list[str] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if (t == "تا" and out and i + 1 < len(toks)
                and re.fullmatch(_BAND, out[-1]) and re.fullmatch(_BAND, toks[i + 1])):
            f1, b1 = (int(x) for x in to_en_digits(out[-1]).split("-"))
            f2, b2 = (int(x) for x in to_en_digits(toks[i + 1]).split("-"))
            if f1 == f2:
                fa = str.maketrans(_EN, FA_DIGITS)
                out += [f"{f1}-{b}".translate(fa) for b in range(b1 + 1, b2)]
            out.append(toks[i + 1])
            i += 2
            continue
        if t != "تا":
            out.append(t)
        i += 1
    return out


def _resolve(tok: str, bands: set[tuple[int, int]], annexes: list[str]) -> bool:
    if re.fullmatch(_BAND, tok):
        f, b = (int(x) for x in to_en_digits(tok).split("-"))
        return (f, b) in bands
    label = to_en_digits(tok[len("پیوست"):].strip())
    if label:
        return label in annexes
    return len(annexes) == 1   # unlabelled «پیوست» is only unambiguous with one annex


def _internal_ref_findings(text: str) -> list[str]:
    """F2: bare «N-M» and «پیوست X» references resolve inside the same document."""
    skip = [m.span() for m in _XREF_RE.finditer(text)]
    skip += [m.span() for m in _AIIN_BAND_RE.finditer(text)]

    def skipped(span: tuple[int, int]) -> bool:
        return any(a <= span[0] < b for a, b in skip)

    bands, annexes = _band_set(text), _annex_labels(text)
    out: list[str] = []
    for m in _BAND_LIST_RE.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        is_item_label = m.start() == line_start and text[m.end():m.end() + 1] == "."
        if skipped(m.span()) or is_item_label:
            continue
        for tok in _expand_refs(m.group(0)):
            if not _resolve(tok, bands, annexes):
                out.append(f"ارجاع درون‌سندی به بند {tok} که وجود ندارد")
    for m in re.finditer(_ANNEX, text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        tok = m.group(0)
        if skipped(m.span()) or tok == "پیوست" or text[line_start:m.start()].startswith("#"):
            continue
        if not _resolve(tok, bands, annexes):
            out.append(f"ارجاع درون‌سندی به {tok} که وجود ندارد")
    return out


def _xref_findings(key: str, text: str, texts: dict[str, str]) -> list[str]:
    """F2: «(سند، N-M …)» / «(سند، پیوست X)» resolve in the named document."""
    out: list[str] = []
    for m in _XREF_RE.finditer(text):
        target = _src_key(m.group("src"))
        if target not in texts:
            continue
        bands, annexes = _band_set(texts[target]), _annex_labels(texts[target])
        for tok in _expand_refs(m.group("refs")):
            if not _resolve(tok, bands, annexes):
                what = tok if tok.startswith("پیوست") else f"بند {tok}"
                out.append(f"{key}: ارجاع به {what} {_SRC_NAMES[target]} که وجود ندارد")
    return out


# ماده / تبصره references to the اساسنامه (F3-F5); run on Latin-digit text.
_NUM = r"\d+(?![\d\-])"
_NUMLIST = rf"{_NUM}(?:\s*(?:،|و|تا)\s*{_NUM})*"
_ASAS = r"(?:همین\s+)?اساسنامه"
_MADDI_RES = [
    re.compile(rf"اساسنامه،?\s*(?:ماده|مواد)\s+(?P<n>{_NUMLIST})"),
    re.compile(rf"(?:ماده|مواد)\s+(?P<n>{_NUMLIST})\s+{_ASAS}"),
]
_TAB = r"تبصره(?P<pl>‌های|‌ها)?"
_TABSARE_RES = [
    re.compile(rf"اساسنامه،?\s*{_TAB}(?:\s+(?P<k>{_NUMLIST}))?\s+ماده\s+(?P<n>{_NUM})"),
    re.compile(rf"{_TAB}(?:\s+(?P<k>{_NUMLIST}))?\s+ماده\s+(?P<n>{_NUM})\s+{_ASAS}"),
    re.compile(rf"اساسنامه،?\s*ماده\s+(?P<n>{_NUM})،?\s*{_TAB}\s+(?P<k>{_NUMLIST})"),
    re.compile(rf"ماده\s+(?P<n>{_NUM})،\s*{_TAB}\s+(?P<k>{_NUMLIST})\s+{_ASAS}"),
]


def _num_list(s: str) -> list[int]:
    toks = re.findall(r"\d+|تا", s)
    out: list[int] = []
    i = 0
    while i < len(toks):
        if toks[i] == "تا" and out and i + 1 < len(toks) and toks[i + 1] != "تا":
            out += list(range(out[-1] + 1, int(toks[i + 1]) + 1))
            i += 2
            continue
        if toks[i] != "تا":
            out.append(int(toks[i]))
        i += 1
    return out


def _d1_tabsare_index(d1: str) -> dict[int, dict]:
    """ماده -> {"numbered": {K, …}, "plain": bool} from D1's «تبصره[ K]:» lines."""
    idx: dict[int, dict] = {}
    cur = None
    for line in to_en_digits(d1).splitlines():
        m = re.match(r"\s*ماده\s+(\d+)", line)
        if m:
            cur = int(m.group(1))
            idx.setdefault(cur, {"numbered": set(), "plain": False})
            continue
        t = re.match(r"\s*تبصره(?:\s+(\d+))?\s*:", line)
        if t and cur is not None:
            if t.group(1):
                idx[cur]["numbered"].add(int(t.group(1)))
            else:
                idx[cur]["plain"] = True
    return idx


def _asasname_ref_findings(text: str, d1: str, prefix: str, own: bool) -> list[str]:
    """F3-F5: every ماده (lists and ranges) and تبصره cited from the اساسنامه exists."""
    en = to_en_digits(text)
    nums = set(_maddi_numbers(d1))
    idx = _d1_tabsare_index(d1)
    where = "همین اساسنامه" if own else "اساسنامه"
    out: list[str] = []
    seen: set[int] = set()
    for rx in _MADDI_RES:
        for m in rx.finditer(en):
            for n in _num_list(m.group("n")):
                if n not in nums and n not in seen:
                    seen.add(n)
                    out.append(f"{prefix}ارجاع به ماده {n} {where} که وجود ندارد")
    tab_seen: set[tuple] = set()
    for rx in _TABSARE_RES:
        for m in rx.finditer(en):
            n = int(m.group("n"))
            info = idx.get(n)
            ks = _num_list(m.group("k")) if m.group("k") else []
            if ks:
                for k in ks:
                    if (info is None or k not in info["numbered"]) and (n, k) not in tab_seen:
                        tab_seen.add((n, k))
                        out.append(f"{prefix}ارجاع به تبصره {k} ماده {n} {where} که وجود ندارد")
            else:
                ok = info is not None and (
                    (info["plain"] or info["numbered"]) if m.group("pl") else info["plain"])
                if not ok and (n, None) not in tab_seen:
                    tab_seen.add((n, None))
                    out.append(f"{prefix}ارجاع به تبصره ماده {n} {where} که وجود ندارد یا مبهم است")
    return out


def findings_for(doc_key: str, text: str) -> list[str]:
    """Run every content gate on the raw master text.

    normalize_fa() is intentionally NOT applied here: it is a heuristic for
    PyMuPDF extraction artifacts and corrupts genuine Persian words
    (سال->سلا, مالی->ملای, بالا->بلاا) when run over authored masters.
    """
    out: list[str] = []
    for b in BANNED:
        if _banned_re(b).search(text):
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
        # «هفت نفر» as whole words: the bare substring «هفت» also matches «هفته».
        for pattern, label in [(r"اردیبهشت", "بازه انتخابات (۱۰ اردیبهشت تا ۱۰ خرداد)"),
                               (r"بیست", "حداقل ۲۰ عضو"),
                               (r"(?<![\w‌])هفت\s+نفر(?![\w‌])",
                                "ترکیب هفت‌نفره شورا (۷ نفر)")]:
            if not re.search(pattern, text):
                out.append(f"ناکافی/غایب: {label}")
        out += _asasname_ref_findings(text, text, prefix="", own=True)
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
        # D1 has no N-M items, so bare بند references are checked in D2-D4 only.
        out += _internal_ref_findings(text)
    return out


def _banned_re(phrase: str) -> re.Pattern:
    """Banned phrase with any run of spaces/ZWNJ between its words (F7):
    «مجمع عمومی» also catches «مجمع‌عمومی» and «مجمع  عمومی»."""
    parts = re.split(r"[ ‌]+", phrase)
    return re.compile(r"[ \t ‌]*".join(re.escape(p) for p in parts))


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
    for key, text in texts.items():
        # F3/F4: ماده lists/ranges and تبصره cited from the اساسنامه exist in D1
        # (D1's own «همین اساسنامه» references are checked in findings_for).
        if key != "D1":
            out += _asasname_ref_findings(text, d1, prefix=f"{key}: ", own=False)
        # F2: «(سند، N-M …)» and «(سند، پیوست X)» resolve in the named document.
        out += _xref_findings(key, text, texts)
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
