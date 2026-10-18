# analysis_tools/tests/test_audit_report.py
import pytest
from analysis_tools import build_audit_report as bar

def test_locked_figures():
    rows, log = bar.collect_data()
    bar.run_gates()  # G1-G5, G9 raise on failure

def test_en_render_byte_identical():
    a, b = bar.render("en"), bar.render("en")
    assert a == b

def test_gate_fires(monkeypatch):
    monkeypatch.setitem(bar.LOCKED, "cash_payments", 1.0)
    with pytest.raises(AssertionError, match="gate FAILED"):
        bar.run_gates()
