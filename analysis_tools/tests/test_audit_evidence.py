# analysis_tools/tests/test_audit_evidence.py
import json
from analysis_tools.common import ROOT

EV = ROOT / "analysis_tools/audit/data/evidence_index.json"

def test_every_source_row_has_evidence():
    import csv
    src = ROOT / "anjoman_accounting_information/reports/2026-10-10/Transactions.csv"
    with open(src, encoding="utf-8-sig") as f:
        ids = [r["id"] for r in csv.DictReader(f)]
    ev = json.loads(EV.read_text(encoding="utf-8"))["rows"]
    missing = [i for i in ids if not ev.get(i)]
    assert missing == []
    for tx, lst in ev.items():
        for e in lst:
            assert e["ref"] and e["shows"]

def test_balance_chain_block_exact():
    bc = json.loads(EV.read_text(encoding="utf-8"))["balance_chain"]
    assert [g["id"] for g in bc["gaps"]] == ["BC-1", "BC-2", "BC-3", "BC-4"]
    assert bc["gaps"][0]["approx_toman"] == 3163000
    assert bc["open_item"] == "OI-07"
