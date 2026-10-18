import pytest
from pypdf import PdfReader

from analysis_tools.report_common import md_to_html_rtl, md_to_pdf_rtl

MD = """# گزارش مالی

پاراگراف با `TX0036` و عدد ۱۲٬۰۰۰.

| ماه | دریافت‌ها | پرداخت‌ها |
|---|---:|---:|
| ۱۴۰۴/۰۵ | ۱۲٬۰۰۰ | — |

- مورد اول

![نمودار](charts_fa/x.png)
"""


def test_html_is_rtl_with_numeric_cells():
    import re
    html = md_to_html_rtl(MD, title="گزارش", footer="انجمن علمی فیزیک | گزارش")
    assert '<html lang="fa" dir="rtl">' in html
    assert "Tahoma" in html
    assert "<table>" in html or "<table" in html
    assert 'class="num"' in html               # numeric cells marked LTR-isolated
    assert "<code>TX0036</code>" in html
    assert "counter(page, persian)" in html    # page footer, Persian digits
    assert 'src="charts_fa/x.png"' in html
    # Regression: numeric cells must inherit right-alignment, not override with left
    m = re.search(r"td\.num, th\.num\s*\{[^}]+\}", html)
    assert m, "td.num, th.num rule not found in CSS"
    rule = m.group(0)
    assert "unicode-bidi: isolate" in rule, "unicode-bidi: isolate not found in numeric cell rule"
    assert "text-align:" not in rule, "text-align must not override right-alignment in numeric cell rule"


def test_wide_table_class():
    cols = " | ".join(f"c{i}" for i in range(10))
    md = f"| {cols} |\n|" + "---|" * 10 + "\n| " + " | ".join("۱" for _ in range(10)) + " |\n"
    html = md_to_html_rtl(md, title="t", footer="f")
    assert 'class="wide"' in html


def test_pdf_written(tmp_path):
    md = tmp_path / "r_FA.md"
    md.write_text(MD.replace("![نمودار](charts_fa/x.png)\n", ""), encoding="utf-8")
    pdf = md_to_pdf_rtl(md, tmp_path / "r_FA.pdf", title="گزارش", footer="انجمن")
    assert pdf.exists() and len(PdfReader(str(pdf)).pages) >= 1
    assert (tmp_path / "r_FA.html").exists()


def _fake_usage(free_gb):
    from collections import namedtuple
    U = namedtuple("usage", "total used free")
    return lambda p: U(500 * 1024 ** 3, 0, int(free_gb * 1024 ** 3))


def test_ensure_disk_passes_and_fails(tmp_path, monkeypatch):
    import shutil
    from analysis_tools import report_common
    seen = []
    monkeypatch.setattr(shutil, "disk_usage", lambda p: (seen.append(p), _fake_usage(2.5)(p))[1])
    assert report_common.ensure_disk(tmp_path / "not" / "yet", min_gb=1.0) == 2.5
    assert seen == [tmp_path]                     # walked up to an existing dir
    monkeypatch.setattr(shutil, "disk_usage", _fake_usage(0.4))
    with pytest.raises(RuntimeError, match=r"0\.40 GB free"):
        report_common.ensure_disk(tmp_path, min_gb=1.0)


@pytest.mark.parametrize("call", ["fin", "perf", "charts"])
def test_builders_stop_on_low_disk(call, monkeypatch):
    import shutil
    from analysis_tools import build_financial_report, build_performance_report, charts
    monkeypatch.setattr(shutil, "disk_usage", _fake_usage(0.1))
    fn = {"fin": lambda: build_financial_report.build("fa"),
          "perf": lambda: build_performance_report.build("fa"),
          "charts": lambda: charts.render_all("fa")}[call]
    with pytest.raises(RuntimeError, match="GB free"):
        fn()
