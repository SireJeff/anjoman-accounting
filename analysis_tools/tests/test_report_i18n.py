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
