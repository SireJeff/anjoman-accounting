# analysis_tools/tests/test_audit_bridge.py
import pytest
from analysis_tools.audit import apply, bridge
from analysis_tools import build_financial_report as fin

def test_allrows_start_matches_2026_10_14_builder():
    assert (bridge.ALLROWS_START["receipts"], bridge.ALLROWS_START["payments"]) \
        == (fin.ALL_TOTALS["Receipts"], fin.ALL_TOTALS["Payments"])

@pytest.fixture(scope="module")
def br():
    rows, _ = apply.apply()
    return bridge.bridges(rows), bridge.decompose(rows)

def test_supported_bridge_exact(br):
    b, _ = br
    s = b["supported"]
    assert abs(s["end"]["receipts"] - 112552000.0) <= 0.5
    assert abs(s["end"]["payments"] - 99393195.0) <= 0.5
    assert [l["id"] for l in s["lines"]] == ["R-01", "R-02", "D-06"]
    bridge.check(b)

def test_allrows_bridge_exact(br):
    b, _ = br
    a = b["allrows"]
    assert abs(a["end"]["receipts"] - 139787000.0) <= 0.5
    assert abs(a["end"]["payments"] - 133539774.0) <= 0.5
    assert [l["id"] for l in a["lines"]] == ["R-02", "R-06", "R-07"]
    bridge.check(b)

def test_decomposition_sums(br):
    _, d = br
    for side in ("receipts", "payments"):
        total = sum(d[side].values())
        want = 139787000.0 if side == "receipts" else 133539774.0
        assert abs(total - want) <= 0.5
    assert abs(d["receipts"]["cash"] - 112552000.0) <= 0.5
    assert abs(d["payments"]["cash"] - 99393195.0) <= 0.5
