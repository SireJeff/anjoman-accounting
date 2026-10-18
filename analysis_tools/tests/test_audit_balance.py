# analysis_tools/tests/test_audit_balance.py
import pytest
from analysis_tools.audit import apply, balance, load, rules

@pytest.fixture(scope="module")
def world():
    rows, log = apply.apply()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS)
    return rows, sheets

def test_cash_sums_equal_locked(world):
    _, sheets = world
    r = sum(s["receipts"] for s in sheets.values())
    p = sum(s["payments"] for s in sheets.values())
    assert abs(r - 112552000.0) <= 0.5
    assert abs(p - 99393195.0) <= 0.5

def test_pending_total(world):
    _, sheets = world
    pend = sum(s["pending"] for s in sheets.values())
    assert abs(pend - 21626064.0) <= 0.5
    yalda = sheets["Yalda 1404"]
    assert any(p["id"] == "PI-01" for p in yalda["pending_items"])

def test_unknown_project_emptied(world):
    _, sheets = world
    u = sheets["Unknown (likely 1405 summer school)"]
    assert u["receipts"] == 0 and u["payments"] == 0 and u["pending"] == 0
    assert u["is_empty_note"] is not None

def test_excluded_under_parent(world):
    _, sheets = world
    y = sheets["Yalda 1404"]["excluded"]
    assert any(e["id"] == "TX0052" and e["parent"] == "TX0050" for e in y)

def test_summary_totals(world):
    _, sheets = world
    rows = balance.summary(sheets)
    tot = rows[-1]
    assert tot["project"] == "TOTALS"
    assert abs(tot["receipts"] - 112552000.0) <= 0.5
    balance.check_summary(sheets, 112552000.0, 99393195.0, 21626064.0)  # G1

def test_custody_shape(world):
    rows, _ = world
    acc = load.load_accounts()
    cust = balance.custody(rows, acc)
    codes = {c["code"] for c in cust}
    assert codes == set(acc)
    assert all("holder" in c and "type" in c for c in cust)
