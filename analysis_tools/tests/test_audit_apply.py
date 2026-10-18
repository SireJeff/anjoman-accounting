# analysis_tools/tests/test_audit_apply.py
import pytest
from analysis_tools.audit import apply, load, rules

@pytest.fixture(scope="module")
def applied():
    return apply.apply()

def test_row_count_and_order(applied):
    rows, _ = applied
    assert len(rows) == 97
    ids = [r["id"] for r in rows]
    assert ids.index("TX0034-B") == ids.index("TX0034") + 1

def test_spot_patches(applied):
    rows, log = applied
    by = {r["id"]: r for r in rows}
    assert by["TX0010"]["status"] == "Duplicate"
    assert by["TX0010"]["duplicate_of"] == "TX0009"
    assert by["TX0010"]["source_status"] == "Review"
    assert by["TX0036"]["direction"] == "Payment"
    assert by["TX0036"]["status"] == "Supported"
    assert by["TX0031"]["amount_toman"] == pytest.approx(230000.0)
    assert by["TX0049"]["amount_toman"] == pytest.approx(10003780.0)
    assert by["TX0049"]["date_jalali"] == "1404/10/01"
    assert by["TX0049"]["date_gregorian"] == "2025-12-22"     # ruling 4
    assert by["TX0049"]["status"] == "Pending"                # stays Review
    assert by["TX0049"]["pending_reason"] == "Review"
    assert by["TX0058"]["status"] == "Payable"
    assert by["TX0058"]["amount_toman"] == pytest.approx(275000.0)
    assert by["TX0056"]["status"] == "Payable"
    assert by["TX0074"]["parent"] == "TX0062;TX0063"
    assert by["TX0069"]["duplicate_of"] == ""
    assert by["TX0071"]["amount_toman"] == pytest.approx(135799.9)  # precision kept
    assert by["TX0034"]["amount_toman"] == pytest.approx(1000000.0)
    assert by["TX0034-B"]["amount_toman"] == pytest.approx(500000.0)
    assert by["TX0034-B"]["project"] == "Association operations"
    assert by["TX0082"]["project"] == "Summer School 1405"
    assert by["TX0082"]["status"] == "Pending"                # Invoice only
    assert by["TX0094"]["status"] == "Memo"                   # Summary only
    assert by["TX0018"]["status"] == "Internal transfer"
    assert by["TX0013"]["evidence_label"] == "original ledger only"
    assert by["TX0043"]["open_item"] == "OI-08"

def test_status_mapping_counts(applied):
    from collections import Counter
    rows, _ = applied
    c = Counter(r["status"] for r in rows)
    # Supported: source 66 + D-06 + R-01 (both Review->Supported) + TX0034-B = 69.
    assert c["Supported"] == 69
    assert c["Pending"] == 4      # TX0049, TX0060, TX0082, TX0096
    assert c["Payable"] == 2      # TX0056, TX0058
    assert c["Duplicate"] == 5    # 4 + TX0010
    assert c["Memo"] == 1         # TX0094
    assert c["Internal transfer"] == 1
    assert c["Supporting detail"] == 15  # TX0052-55 + TX0064-74

def test_b01_mapping_logged(applied):
    rows, log = applied
    unmapped = [e for e in log if e["source_id"] == "B-01"]
    assert unmapped, "status mapping under B-01 must be logged"

def test_log_cites_register_ids(applied):
    reg_ids = {e["id"] for e in load.load_register()}
    mids = {e["id"] for e in load.load_mechanical()}
    rows, log = applied
    bad = [e for e in log if e["source_id"] not in reg_ids | mids | {"B-01"}]
    assert bad == []

def test_diff_completeness_clean(applied):
    rows, log = applied
    assert apply.diff_completeness(rows, log) == []

def test_created_entries(applied):
    _, log = applied
    created = {e["tx"] for e in log if e["field"] == "created"}
    assert created == {"TX0034-B", "PI-01"}

def test_coherence_enforced():
    # a row with incoherent amount_original must raise
    src = load.load_source()
    row = dict(next(r for r in src if r["id"] == "TX0005"))
    row["amount_original"] = str(float(row["amount_toman"]) * 3)
    with pytest.raises(apply.AuditError):
        apply._check_coherence([row])
