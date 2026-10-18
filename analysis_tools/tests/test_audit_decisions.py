# analysis_tools/tests/test_audit_decisions.py
import json
from analysis_tools.common import ROOT

DEC = ROOT / "analysis_tools/audit/data/decisions.json"
EXPECTED_IDS = (
    ["S-01", "B-01", "A-01"]
    + [f"D-{n:02d}" for n in range(1, 7)]
    + [f"R-{n:02d}" for n in range(1, 17)]
    + [f"U-{n:02d}" for n in range(1, 9)]
    + [f"P-{n:02d}" for n in range(1, 6)]
)

def test_register_complete_and_shaped():
    reg = json.loads(DEC.read_text(encoding="utf-8"))
    assert [e["id"] for e in reg] == EXPECTED_IDS
    for e in reg:
        assert e["kind"] in {"scope", "basis", "process", "duplicate", "review",
                             "date", "reassignment"}
        assert e["question"] and e["choice"] and e["rationale"]
        assert e["date"] == "2026-10-18"
        assert isinstance(e["evidence"], list) and e["evidence"]
