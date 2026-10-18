# analysis_tools/tests/test_audit_mechanical.py
import json
from analysis_tools.common import ROOT

MECH = ROOT / "analysis_tools/audit/data/mechanical.json"
ALLOWED = {"description_en", "description_fa", "tracking_id", "message_ids",
           "notes", "evidence_basis"}

def test_mechanical_schema_and_fields():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    assert len(m) >= 20
    ids = [e["id"] for e in m]
    assert ids == [f"M-{n:03d}" for n in range(1, len(m) + 1)]
    for e in m:
        assert e["field"] in ALLOWED, e
        assert e["tx"] and e["new"] and e["reason"] and e["evidence"]

def test_known_fixes_present():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    by_tx = {}
    for e in m:
        by_tx.setdefault(e["tx"], []).append(e)
    assert any(e["field"] == "tracking_id" and e["new"] == "001873"
               for e in by_tx["TX0075"]), "TX0075 tracking 187300 -> 001873"
    assert any("photo_34" in json.dumps(e) for e in by_tx.get("TX0035", [])), \
        "photo_34 evidence moves to TX0035"
    for tx, course in (("TX0083", "OOP"), ("TX0084", "Manim"), ("TX0087", "Python")):
        assert any(course in e["new"] for e in by_tx[tx]
                   if e["field"] == "description_en"), tx
    assert any("29350" in e["new"] for e in by_tx["TX0038"])
    assert any(e["field"] == "notes" for e in by_tx["TX0002"])
    assert any("shared" in e["new"] for e in by_tx["TX0020"]
               if e["field"] == "description_en"), "P-04 shared-use note"

def test_description_pairs():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    en = {e["tx"] for e in m if e["field"] == "description_en"}
    fa = {e["tx"] for e in m if e["field"] == "description_fa"}
    assert en == fa, "every description rewrite exists in both languages"

def test_no_amount_status_direction_changes():
    m = json.loads(MECH.read_text(encoding="utf-8"))
    assert not ({"amount_toman", "amount_original", "unit_original", "status",
                 "direction", "date_gregorian", "date_jalali", "period_jalali",
                 "project", "category", "duplicate_of", "cash_account"}
                & {e["field"] for e in m})
