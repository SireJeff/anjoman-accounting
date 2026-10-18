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
    html = md_to_html_rtl(MD, title="گزارش", footer="انجمن علمی فیزیک | گزارش")
    assert '<html lang="fa" dir="rtl">' in html
    assert "Tahoma" in html
    assert "<table>" in html or "<table" in html
    assert 'class="num"' in html               # numeric cells marked LTR-isolated
    assert "<code>TX0036</code>" in html
    assert "counter(page, persian)" in html    # page footer, Persian digits
    assert 'src="charts_fa/x.png"' in html


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
