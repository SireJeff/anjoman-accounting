from datetime import datetime
from analysis_tools.parse_exports import enrich

def test_enrich_jalali_and_window():
    rec = {"timestamp": "2025-07-21T14:30:00"}  # 1404/04/30, a Monday
    out = enrich(rec)
    assert out["jalali_month"] == "1404/04"
    assert out["hour"] == 14
    assert out["weekday_en"] == "Monday"
    assert out["in_window"] is True
    assert isinstance(out["jalali_weekday"], str) and out["jalali_weekday"]

def test_enrich_excludes_pre_window():
    rec = {"timestamp": "2025-05-27T10:00:00"}
    assert enrich(rec)["in_window"] is False

def test_enrich_handles_missing_timestamp():
    assert enrich({"timestamp": None})["in_window"] is False
