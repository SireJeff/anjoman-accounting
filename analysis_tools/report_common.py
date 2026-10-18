"""Shared markdown->PDF builder for the 2026-10-14 reports.

Render pipeline follows the accounting_tools/build_report.py precedent (real
Table flowables with Paragraph cells, repeating header rows) rather than the
brief's wrapped-rows simplification: the month-schedule tables are too wide to
stay readable as joined text lines. Dataviz tokens mirror analysis_tools/
charts.py so figures and tables read as one system.
"""
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# dataviz tokens (see charts.py)
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
ACCENT = "#0d366b"      # sequential dark blue -> table headers
ZEBRA = "#f4f3ef"

# first Arabic-script-capable pair wins (Windows Tahoma / Linux DejaVu);
# falls back to Helvetica (no Persian coverage) when neither is present
_FONT_PAIRS = [
    ("Tahoma", "C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/tahomabd.ttf"),
    ("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def _pick_font():
    for name, normal, bold in _FONT_PAIRS:
        try:
            if Path(normal).exists() and Path(bold).exists():
                pdfmetrics.registerFont(TTFont(name, normal))
                pdfmetrics.registerFont(TTFont(name + "Bold", bold))
                pdfmetrics.registerFontFamily(name, normal=name, bold=name + "Bold",
                                              italic=name, boldItalic=name + "Bold")
                return name, name + "Bold"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = _pick_font()

_NUM = re.compile(r"^[−-]?[\d,\s]+(\.\d+)?[‰%]?$")
_IMAGE = re.compile(r"!\[.*\]\((.+?)\)")
_SEP_ROW = re.compile(r"^\|?\s*:?-{2,}.*\|")  # |---|---| separator line


def _inline(s):
    """Minimal inline markdown -> reportlab intra-paragraph markup."""
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", s)
    return s


def _styles():
    base = getSampleStyleSheet()
    mk = lambda n, **kw: ParagraphStyle(n, fontName=FONT, textColor=colors.HexColor(INK2), **kw)
    return {
        "h1": ParagraphStyle("Rh1", parent=base["Heading1"], fontName=FONT_BOLD,
                             fontSize=17, leading=21, spaceAfter=8,
                             textColor=colors.HexColor(INK)),
        "h2": ParagraphStyle("Rh2", parent=base["Heading2"], fontName=FONT_BOLD,
                             fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=5,
                             textColor=colors.HexColor(ACCENT)),
        "h3": ParagraphStyle("Rh3", parent=base["Heading3"], fontName=FONT_BOLD,
                             fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4,
                             textColor=colors.HexColor(INK)),
        "body": mk("Rbody", fontSize=9, leading=12.6, spaceAfter=5),
        "bullet": mk("Rbullet", fontSize=9, leading=12.6, spaceAfter=3,
                     leftIndent=11, bulletIndent=2),
    }


def _col_widths(rows, usable_cm):
    """Damped proportional widths: wide free-text columns share, never own."""
    ncols = len(rows[0])
    lens = [max(len(r[c]) for r in rows) for c in range(ncols)]
    w = [max(4.0, min(l, 34.0)) ** 0.62 for l in lens]
    tot = sum(w)
    widths = [usable_cm * x / tot for x in w]
    floor = 0.85
    deficit = sum(max(0.0, floor - x) for x in widths)
    if deficit > 0:
        give = [x - floor if x > floor else 0.0 for x in widths]
        gtot = sum(give)
        widths = [max(floor, x - deficit * g / gtot) if gtot else x
                  for x, g in zip(widths, give)]
    return [x * cm for x in widths]


def _table(lines, st, usable_cm):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines
            if not _SEP_ROW.match(ln)]
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    size = 6.2 if ncols >= 9 else (6.8 if ncols >= 6 else 7.4)
    cell = ParagraphStyle("c", fontName=FONT, fontSize=size, leading=size + 2.6,
                          textColor=colors.HexColor(INK2))
    cell_r = ParagraphStyle("cr", parent=cell, alignment=TA_RIGHT)
    head = ParagraphStyle("ch", parent=cell, fontName=FONT_BOLD,
                          textColor=colors.white)
    head_r = ParagraphStyle("chr", parent=head, alignment=TA_RIGHT)
    numeric = []
    for c in range(ncols):
        body = [r[c] for r in rows[1:]]
        ok = sum(1 for v in body if v and (_NUM.match(v) or v in {"—", "-"}))
        numeric.append(ok >= len(body) * 0.6)
    grid = [[Paragraph(_inline(v), head_r if numeric[c] else head)
             for c, v in enumerate(rows[0])]]
    for r in rows[1:]:
        grid.append([Paragraph(_inline(v), cell_r if numeric[c] else cell)
                     for c, v in enumerate(r)])
    t = Table(grid, colWidths=_col_widths(rows, usable_cm), repeatRows=1,
              hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ACCENT)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(ZEBRA)]),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor(GRID)),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(ACCENT)),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.HexColor(GRID)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def _image(path, usable_cm):
    from PIL import Image as PILImage  # sizing only: keep the chart aspect true
    with PILImage.open(path) as im:
        w, h = im.size
    width = min(16.4, usable_cm) * cm
    return Image(str(path), width=width, height=width * h / w)


DEFAULT_FOOTER = "ANJOMAN | Financial report (monthly) | 2026-10-14 | toman"
DEFAULT_TITLE = "Anjoman financial report (monthly view)"


def md_to_pdf(md_path, pdf_path, images_dir=None, footer=None, title=None):
    """Render a markdown file (headings, paragraphs, bullets, pipe tables,
    ![](rel.png) images) to a readable A4 PDF. footer/title override the
    financial-report defaults for other report families (performance report)."""
    footer_text = footer if footer is not None else DEFAULT_FOOTER
    title = title if title is not None else DEFAULT_TITLE
    md_path, pdf_path = Path(md_path), Path(pdf_path)
    images_dir = Path(images_dir) if images_dir else md_path.parent
    st = _styles()
    usable = (A4[0] - 2 * 1.6 * cm) / cm
    story, table_buf = [], []

    def flush_table():
        if table_buf:
            story.append(_table(table_buf, st, usable))
            story.append(Spacer(1, 7))
            table_buf.clear()

    for line in md_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            flush_table()
            story.append(Spacer(1, 4))
            continue
        if s.startswith("|"):
            table_buf.append(s)  # separator rows are dropped inside _table()
            continue
        flush_table()
        m = _IMAGE.match(s)
        if m and (images_dir / m.group(1)).exists():
            story.append(_image(images_dir / m.group(1), usable))
            story.append(Spacer(1, 7))
        elif s.startswith("### "):
            story.append(Paragraph(_inline(s[4:]), st["h3"]))
        elif s.startswith("## "):
            story.append(Paragraph(_inline(s[3:]), st["h2"]))
        elif s.startswith("# "):
            story.append(Paragraph(_inline(s[2:]), st["h1"]))
        elif s.startswith(("- ", "* ")) and len(s) > 2:
            story.append(Paragraph(_inline(s[2:]), st["bullet"], bulletText="•"))
        else:
            story.append(Paragraph(_inline(s), st["body"]))
    flush_table()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor(GRID))
        canvas.line(1.6 * cm, 1.15 * cm, A4[0] - 1.6 * cm, 1.15 * cm)
        canvas.setFont(FONT, 7)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(1.6 * cm, 0.78 * cm, footer_text)
        canvas.drawRightString(A4[0] - 1.6 * cm, 0.78 * cm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.5 * cm, bottomMargin=1.7 * cm,
        title=title, author="Anjoman")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return pdf_path


# --------------------------------------------------------------------------
# Persian (RTL) path: markdown -> HTML (dir=rtl) -> WeasyPrint. Follows the
# 2026-10-10 precedent (reports/2026-10-10/fa/Anjoman_Financial_Report_FA.html);
# reportlab cannot shape Arabic script, WeasyPrint (Pango/HarfBuzz) can.
# --------------------------------------------------------------------------
_RTL_NUM = re.compile(r"^[\s\-−+*—]*[۰-۹0-9][۰-۹0-9٬٫,.%٪:/\s→–\-+*()]*$")

_RTL_CSS = """
@page { size: A4; margin: 16mm 14mm 18mm;
  @bottom-center { content: "%(footer)s | صفحه " counter(page, persian);
    font-family: Tahoma; font-size: 7.5pt; color: %(muted)s; } }
html { direction: rtl; }
body { font-family: Tahoma, "DejaVu Sans", sans-serif; font-size: 9pt;
  line-height: 1.75; color: %(ink2)s; }
h1 { font-size: 17pt; color: %(ink)s; margin: 0 0 4mm; }
h2 { font-size: 12.5pt; color: %(accent)s; border-bottom: 0.6pt solid %(grid)s;
  padding-bottom: 1.5mm; margin-top: 7mm; break-after: avoid; }
h3 { font-size: 10.5pt; color: %(ink)s; break-after: avoid; }
p, li { text-align: right; overflow-wrap: anywhere; }
code { font-family: Consolas, Tahoma, monospace; font-size: 0.92em;
  direction: ltr; unicode-bidi: isolate; }
table { width: 100%%; border-collapse: collapse; margin: 2mm 0 5mm;
  font-size: 7.4pt; line-height: 1.55; direction: rtl; }
table.wide { font-size: 6.2pt; }
th { background: %(accent)s; color: white; text-align: right; padding: 1.6mm 1.4mm; }
td { padding: 1.3mm 1.4mm; vertical-align: top; overflow-wrap: break-word;
  border-bottom: 0.4pt solid %(grid)s; text-align: right; }
td.num, th.num { direction: ltr; unicode-bidi: isolate;
  white-space: nowrap; }
tr:nth-child(even) td { background: %(zebra)s; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
img { max-width: 100%%; display: block; margin: 3mm auto; }
"""


def _mark_tables(html_body):
    """Tag numeric cells (class=num) and wide tables (class=wide)."""
    def table(m):
        t = m.group(0)
        ncols = len(re.findall(r"<th[ >]", t.split("</tr>", 1)[0]))
        t = re.sub(r"<td([^>]*)>(.*?)</td>",
                   lambda c: (f'<td{c.group(1)} class="num">{c.group(2)}</td>'
                              if _RTL_NUM.match(re.sub(r"<[^>]+>", "", c.group(2)))
                              else c.group(0)),
                   t, flags=re.S)
        if ncols > 8:
            t = t.replace("<table>", '<table class="wide">', 1)
        return t
    return re.sub(r"<table>.*?</table>", table, html_body, flags=re.S)


def md_to_html_rtl(md_text, title, footer):
    import markdown
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    body = _mark_tables(body)
    css = _RTL_CSS % {"footer": footer.replace('"', "'"), "muted": MUTED, "ink": INK,
                      "ink2": INK2, "accent": ACCENT, "grid": GRID, "zebra": ZEBRA}
    return (f'<!DOCTYPE html>\n<html lang="fa" dir="rtl"><head><meta charset="utf-8">'
            f"<title>{html.escape(title)}</title><style>{css}</style></head>"
            f"<body>{body}</body></html>\n")


def md_to_pdf_rtl(md_path, pdf_path, title, footer):
    from weasyprint import HTML
    md_path, pdf_path = Path(md_path), Path(pdf_path)
    doc = md_to_html_rtl(md_path.read_text(encoding="utf-8"), title, footer)
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(doc, encoding="utf-8")
    HTML(string=doc, base_url=str(md_path.parent)).write_pdf(str(pdf_path))
    return pdf_path
