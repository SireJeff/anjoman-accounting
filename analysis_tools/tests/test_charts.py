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


def test_render_all_fa_writes_charts_fa(tmp_path, monkeypatch, pseudo_fa):
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
    monkeypatch.setattr(charts, "PERF", tmp_path / "perf" / "charts")
    monkeypatch.setattr(charts, "FIN", tmp_path / "fin" / "charts")
    out = charts.render_all("fa")
    assert len(out) == 8
    for p in out.values():
        assert Path(p).parent.name == "charts_fa" and Path(p).exists()
    assert not (tmp_path / "perf" / "charts").exists()   # EN dirs untouched


def test_en_chart_unchanged_against_committed(tmp_path):
    """Real data, EN path: re-rendering must reproduce the committed PNG pixels."""
    import numpy as np
    from PIL import Image
    tl = charts.load_timeline()
    for name, fn in (("cashflow_monthly", charts.cashflow_monthly),
                     ("activity_by_month", charts.activity_by_month)):
        new = tmp_path / f"{name}.png"
        fn(tl, new)
        base = (charts.FIN if name == "cashflow_monthly" else charts.PERF) / f"{name}.png"
        a = np.asarray(Image.open(base).convert("RGB"))
        b = np.asarray(Image.open(new).convert("RGB"))
        assert a.shape == b.shape and (a == b).all(), f"{name} EN render drifted"


def test_fa_charts_no_latin_digits(tmp_path, monkeypatch, pseudo_fa):
    """Every chart function, rendered in fa: no ASCII digit may survive in any
    visible Text artist (title, subtitle, legend, tick labels, annotations) once
    protected spans (code/URLs/handles/TX-style ids) are stripped out."""
    import re
    import matplotlib.text
    from analysis_tools import i18n

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
    monkeypatch.setattr(charts, "PERF", tmp_path / "perf" / "charts")
    monkeypatch.setattr(charts, "FIN", tmp_path / "fin" / "charts")

    captured = []
    orig_save = charts._save

    def spy_save(fig, path, dpi=120, lang="en"):
        captured.append(fig)
        return orig_save(fig, path, dpi=dpi, lang=lang)

    monkeypatch.setattr(charts, "_save", spy_save)

    out = charts.render_all("fa")
    assert len(out) == 8
    assert len(captured) == 8

    bad = []
    for fig in captured:
        for txt in fig.findobj(matplotlib.text.Text):
            s = txt.get_text()
            if not s or not txt.get_visible():
                continue
            stripped = i18n._PROTECT.sub("", s)
            if re.search(r"[0-9]", stripped):
                bad.append(s)
    assert not bad, f"Latin digits found in fa chart text: {bad!r}"


def test_event_timeline_fa_jalali_month_ticks(tmp_path, monkeypatch, pseudo_fa):
    """FA event_timeline x-axis must show Jalali month+year ticks (spec S3.5),
    not the Gregorian/English ConciseDateFormatter ticks the EN path uses."""
    import re
    from analysis_tools import i18n

    # Spans Jun 2025 -> Jan 2026: 4 distinct Gregorian months, 8 distinct Jalali
    # months (1404/03 .. 1404/10) -- long enough to exercise the every-2nd-month
    # thinning branch too. event_ref values are real data.thread.* keys so
    # pseudo_fa (derived from en.json) already covers them.
    threads = [
        {"event_ref": "yalda-1404", "title": "Yalda 1404",
         "first_seen": "2025-06-01T10:00:00", "last_seen": "2025-06-15T10:00:00"},
        {"event_ref": "booths-1404", "title": "Booths 1404",
         "first_seen": "2025-08-01T10:00:00", "last_seen": "2025-08-20T10:00:00"},
        {"event_ref": "freshman-party-1404", "title": "Freshman Party 1404",
         "first_seen": "2025-10-01T10:00:00", "last_seen": "2025-10-10T10:00:00"},
        {"event_ref": "summer-school-1405", "title": "Summer School 1405",
         "first_seen": "2026-01-01T10:00:00", "last_seen": "2026-01-15T10:00:00"},
    ]
    tl = {"threads": threads}

    captured = []
    orig_save = charts._save

    def spy_save(fig, path, dpi=120, lang="en"):
        captured.append(fig)
        return orig_save(fig, path, dpi=dpi, lang=lang)

    monkeypatch.setattr(charts, "_save", spy_save)

    out_path = charts.event_timeline(tl, tmp_path / "event_timeline.png", "fa")
    assert Path(out_path).exists()
    assert len(captured) == 1
    ax = captured[0].axes[0]
    tick_labels = [lbl.get_text() for lbl in ax.get_xticklabels() if lbl.get_text()]
    assert tick_labels, "no x tick labels found"

    month_names = set(i18n.catalog("glossary")["jalali_month"].values())
    assert any(any(name in lbl for name in month_names) for lbl in tick_labels), \
        f"no Persian month name found in tick labels: {tick_labels!r}"
    assert not any(re.search(r"[A-Za-z]", lbl) for lbl in tick_labels), \
        f"ASCII letters found in fa month tick labels: {tick_labels!r}"
