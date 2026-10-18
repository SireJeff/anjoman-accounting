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


# Punctuation that builders emit in code (list joins, date ranges). In RTL text
# "→" points from the end back to the start, and Latin ", " / "; " are not
# Persian punctuation, so fa gets its own marks; en is unchanged.
_PUNCT = {"en": {"comma": ", ", "semi": "; ", "arrow": "→"},
          "fa": {"comma": "، ", "semi": "؛ ", "arrow": "←"}}


def punct(name, lang):
    return _PUNCT[lang][name]


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
