# analysis_tools/tests/test_audit_load.py
import pytest
from analysis_tools.audit import load, pii

def test_pii_patterns():
    assert pii.scan("call 09123456789 ok") != []
    assert pii.scan("card 6037991111111111 end") != []
    assert pii.scan("IR062960000000100000000001 hit") != []
    assert pii.scan("id 0012345678 (10 digits)") != []
    assert pii.scan("clean 112,552,000 toman TX0036 2025-07-24") == []

def test_source_rows_and_counters():
    rows = load.load_source()
    assert len(rows) == 96
    from collections import Counter
    assert Counter(r["status"] for r in rows) == {
        "Supported": 66, "Review": 22, "Duplicate": 4,
        "Invoice only": 3, "Summary only": 1}
    assert Counter(r["direction"] for r in rows) == {
        "Payment": 82, "Receipt": 12, "Internal transfer": 1, "Unknown": 1}

def test_source_cols_exact():
    assert load.SOURCE_COLS[:5] == ["id", "date_gregorian", "date_jalali",
                                    "period_jalali", "direction"]
    assert load.SOURCE_COLS[-1] == "sources"
    assert len(load.SOURCE_COLS) == 22
    assert load.AUDIT_COLS == ["source_status", "pending_reason", "parent",
                               "date_basis", "evidence_label", "open_item",
                               "changed_fields"]

def test_input_validators_raise_on_bad_shape():
    with pytest.raises(load.AuditError):
        load._validate_register([])
