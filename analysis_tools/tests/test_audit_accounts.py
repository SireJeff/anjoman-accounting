# analysis_tools/tests/test_audit_accounts.py
import csv, json
from analysis_tools.common import ROOT

ACC = ROOT / "analysis_tools/audit/data/accounts.json"
TYPES = {"personal", "association", "volunteer", "event custodian",
         "cash", "not evidenced"}

def _source_accounts():
    src = ROOT / "anjoman_accounting_information/reports/2026-10-10/Transactions.csv"
    with open(src, encoding="utf-8-sig") as f:
        return {r["cash_account"] for r in csv.DictReader(f) if r["cash_account"]}

def test_accounts_cover_source_codes():
    acc = json.loads(ACC.read_text(encoding="utf-8"))["accounts"]
    assert set(acc) == _source_accounts()
    for code, a in acc.items():
        assert a["type"] in TYPES, (code, a["type"])
        assert a["holder"] and a["evidence"]

def test_no_card_or_iban():
    text = ACC.read_text(encoding="utf-8")
    import re
    assert not re.search(r"\b\d{16}\b", text)
    assert not re.search(r"IR\d{24}", text)
