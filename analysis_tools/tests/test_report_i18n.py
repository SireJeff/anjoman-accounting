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
    # Keys used inside f-strings are single-quoted (Python 3.11 cannot nest
    # double quotes there), so accept either quote style.
    orphans = [k for k in i18n.catalog("en")
               if not k.startswith("data.")
               and f'"{k}"' not in code and f"'{k}'" not in code]
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
