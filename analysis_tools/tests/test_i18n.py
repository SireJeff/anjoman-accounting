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
