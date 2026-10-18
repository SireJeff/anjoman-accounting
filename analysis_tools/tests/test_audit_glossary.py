# analysis_tools/tests/test_audit_glossary.py
import json
from analysis_tools import i18n
from analysis_tools.audit import load

def test_existing_terms_unchanged():
    g = i18n.catalog("glossary")
    assert g["status"]["Supported"] == "تأییدشده"
    assert g["status"]["Review"] == "نیازمند بررسی"
    assert g["project"]["Yalda 1404"] == "یلدا ۱۴۰۴"
    assert g["ledger_category"]["Unclassified"] == "طبقه‌بندی‌نشده"

def test_new_status_terms():
    g = i18n.catalog("glossary")
    for s in load.NEW_STATUSES:
        assert g["status"][s], s

def test_every_used_value_has_fa_term():
    from analysis_tools.audit import apply, rules
    g = i18n.catalog("glossary")
    rows, _ = apply.apply()
    for r in rows:
        assert r["status"] in g["status"], r["id"]
        if r["date_basis"]:
            assert r["date_basis"] in g["date_basis"], r["id"]
    acc = load.load_accounts()
    for a in acc.values():
        assert a["type"] in g["account_type"], a
    for r in rows:
        assert r["project"] in g["project"], r["id"]
        assert r["category"] in g["ledger_category"], r["id"]
