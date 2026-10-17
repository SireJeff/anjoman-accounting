# analysis_tools/tests/test_charts.py
import json
from pathlib import Path
from analysis_tools import charts

def test_render_all_produces_pngs(tmp_path, monkeypatch):
    tl = {"monthly_activity": {"1404/05": {"channel": {"events": 3}}},
          "monthly_cashflow": {"1404/05": {"Receipts": 1.0, "Payments": 0.5,
                                           "by_category": {"Events": 1.0}, "by_project": {}}},
          "hour_histogram": {"channel": {"13": 2}},
          "weekday_hour_heat": {"channel": {"شنبه": {"13": 2}}},
          "threads": [], "mechanics": [], "event_start_times": {}}
    eco = {"nodes": [{"id": "association", "label": "A", "type": "association", "seed": True},
                     {"id": "shabahang_sut", "label": "S", "type": "subgroup", "seed": True}],
           "edges": [{"source": "channel_export", "target": "shabahang_sut",
                      "type": "forward", "weight": 5}]}
    monkeypatch.setattr(charts, "load_timeline", lambda: tl)
    monkeypatch.setattr(charts, "load_ecosystem", lambda: eco)
    # fixture renders must not overwrite the production chart directories
    monkeypatch.setattr(charts, "PERF", tmp_path / "perf")
    monkeypatch.setattr(charts, "FIN", tmp_path / "fin")
    out = charts.render_all()
    assert set(out) == {"activity_by_month", "category_breakdown", "weekday_hour_heat",
                        "hour_histogram", "event_timeline", "ecosystem_map",
                        "cashflow_monthly", "cumulative_cash"}
    for p in out.values():
        assert Path(p).exists() and Path(p).suffix == ".png"
