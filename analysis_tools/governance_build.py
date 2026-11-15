# -*- coding: utf-8 -*-
"""Render governance markdown masters to RTL DOCX (+ PDF via report_common).

OOXML notes (Persian is a complex script):
  - A bidi paragraph (<w:bidi/> in pPr) is right-aligned/start-aligned by
    default, so paragraphs here do NOT also set jc; setting both is
    redundant and the brief's original draft appended bidi after jc,
    which violates CT_PPr's defined child order.
  - Word distinguishes "Western" run properties (w:b, w:sz, w:rFonts/@ascii)
    from "complex-script" run properties (w:bCs, w:szCs, w:rFonts/@cs). A
    run flagged rtl (w:rtl, exposed by python-docx as Font.rtl) is shaped
    with the complex-script properties, so bold/size must be mirrored onto
    w:bCs/w:szCs or headings render plain in Word.
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from bs4 import NavigableString, Tag

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Mm
from docx.opc.constants import RELATIONSHIP_TYPE as RT

from . import governance_lint as gl
from .report_common import _pin_font_stamps
from .governance_layout import FONT, DRAFT, COMPANIONS, parsed_markdown, governance_html

def _rtl_paragraph(p):
    """Mark a paragraph bidi (RTL). Do not also set jc/alignment: a bidi
    paragraph's default alignment is already right/start, and CT_PPr
    requires its children in schema order (bidi after jc would be invalid)."""
    pPr = p._p.get_or_add_pPr()
    if pPr.find(qn("w:bidi")) is None:
        pPr.append(OxmlElement("w:bidi"))
    return p


def _rtl_run(r, bold=False, size=None, rtl=True):
    r.font.name = FONT
    r.font.rtl = rtl
    if bold:
        r.bold = True
        r.font.cs_bold = True
    if size:
        r.font.size = Pt(size)
    rPr = r._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:cs"), FONT)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "fa-IR")
    lang.set(qn("w:bidi"), "fa-IR")
    rPr.append(lang)
    if size:
        # python-docx has no Font property for szCs; w:sz/w:szCs share the
        # same half-point value and CT_RPr requires szCs immediately after
        # sz, so insert it by hand right after the sz element python-docx
        # just wrote via r.font.size.
        sz = rPr.find(qn("w:sz"))
        szCs = OxmlElement("w:szCs")
        if sz is not None:
            szCs.set(qn("w:val"), sz.get(qn("w:val")))
            sz.addnext(szCs)
        else:
            rPr.append(szCs)
    return r


_LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_./:@%+?=&~#\-]*")


def _text(p, text, bold=False, italic=False, code=False):
    parts = [text] if code else re.split(f"({_LATIN.pattern})", text)
    for part in parts:
        if not part:
            continue
        run = _rtl_run(p.add_run(part), bold=bold, rtl=not (code or _LATIN.fullmatch(part)))
        run.italic = italic
        run.font.cs_italic = italic
        if code:
            run.font.name = "Consolas"


def _link(p, label, target, anchor=False):
    element = OxmlElement("w:hyperlink")
    if anchor:
        element.set(qn("w:anchor"), target)
    else:
        element.set(qn("r:id"), p.part.relate_to(target, RT.HYPERLINK, is_external=True))
    run = _rtl_run(p.add_run(label), rtl=not bool(_LATIN.fullmatch(label)))
    element.append(run._r)
    p._p.append(element)


def _inline(p, node, bold=False, italic=False, code=False):
    if isinstance(node, NavigableString):
        _text(p, str(node), bold, italic, code)
        return
    if not isinstance(node, Tag) or node.name in ("ul", "ol"):
        return
    if node.name == "a":
        href = node.get("href", "")
        _link(p, node.get_text(), href[1:] if href.startswith("#") else href,
              anchor=href.startswith("#"))
        return
    if node.name == "br":
        p.add_run().add_break()
        return
    for child in node.children:
        _inline(p, child, bold or node.name in ("b", "strong"),
                italic or node.name in ("em", "i"), code or node.name == "code")


def _field(p, instruction, cached=""):
    for tag, value in (("begin", None), ("instruction", instruction), ("separate", None)):
        if tag == "instruction":
            element = OxmlElement("w:instrText")
            element.set(qn("xml:space"), "preserve")
            element.text = f" {value} "
        else:
            element = OxmlElement("w:fldChar")
            element.set(qn("w:fldCharType"), tag)
        _rtl_run(p.add_run(), size=8)._r.append(element)
    if cached:
        _rtl_run(p.add_run(cached), size=8)
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    _rtl_run(p.add_run(), size=8)._r.append(end)


def _bookmark(p, name, number):
    start, end = OxmlElement("w:bookmarkStart"), OxmlElement("w:bookmarkEnd")
    start.set(qn("w:id"), str(number))
    start.set(qn("w:name"), name)
    end.set(qn("w:id"), str(number))
    p._p.insert(1, start)
    p._p.append(end)


def _numbering(doc, ordered, start=1, level=0):
    numbering = doc.part.numbering_part.element
    ids = [int(n.get(qn("w:abstractNumId"))) for n in numbering.findall(qn("w:abstractNum"))]
    abstract_id = max(ids, default=-1) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    for ilvl in range(9):
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(ilvl))
        for tag, val in (("start", "1"), ("numFmt", "decimal" if ordered else "bullet"),
                         ("lvlText", f"%{ilvl + 1}." if ordered else "•"), ("lvlJc", "right")):
            item = OxmlElement(f"w:{tag}")
            item.set(qn("w:val"), val)
            lvl.append(item)
        abstract.append(lvl)
    # abstractNum elements must precede num elements in CT_Numbering.
    nums = numbering.findall(qn("w:num"))
    if nums:
        nums[0].addprevious(abstract)
    else:
        numbering.append(abstract)
    num = numbering.add_num(abstract_id)
    if ordered:
        override = OxmlElement("w:lvlOverride")
        override.set(qn("w:ilvl"), str(min(level, 8)))
        start_override = OxmlElement("w:startOverride")
        start_override.set(qn("w:val"), str(start))
        override.append(start_override)
        num.append(override)
    return num.numId


def _list(doc, node, level=0):
    num_id = _numbering(doc, node.name == "ol", int(node.get("start", 1)), level)
    for li in node.find_all("li", recursive=False):
        p = _rtl_paragraph(doc.add_paragraph())
        p.paragraph_format.right_indent = Mm(5 * (level + 1))
        props = p._p.get_or_add_pPr().get_or_add_numPr()
        props.get_or_add_ilvl().val = min(level, 8)
        props.get_or_add_numId().val = num_id
        _inline(p, li)
        for child in li.find_all(["ul", "ol"], recursive=False):
            _list(doc, child, level + 1)


def _table(doc, node):
    rows = node.find_all("tr")
    if not rows:
        return
    columns = max(len(r.find_all(["td", "th"], recursive=False)) for r in rows)
    table = doc.add_table(rows=0, cols=columns)
    table.style = "Table Grid"
    bidi = OxmlElement("w:bidiVisual")
    # CT_TblPr places bidiVisual before tblW; Word tolerates the wrong
    # order, but stricter Office readers need schema-ordered properties.
    table._tbl.tblPr.insert_element_before(bidi, "w:tblW", "w:tblLook")
    for row in rows:
        cells = table.add_row().cells
        for cell, source in zip(cells, row.find_all(["td", "th"], recursive=False)):
            p = _rtl_paragraph(cell.paragraphs[0])
            _inline(p, source, bold=source.name == "th")
            for r in p.runs:
                r.font.size = Pt(10)
            cell.width = Mm(172 / columns)
        if row.find("th"):
            repeat = OxmlElement("w:tblHeader")
            table.rows[-1]._tr.get_or_add_trPr().append(repeat)


def _blocks(doc, parent):
    for node in parent.children:
        if not isinstance(node, Tag):
            continue
        if node.name == "h1":
            continue  # title is on the cover
        if re.fullmatch(r"h[2-6]", node.name):
            level = min(int(node.name[1]) - 1, 3)
            p = _rtl_paragraph(doc.add_paragraph(style=f"Heading {level}"))
            _inline(p, node)
            _bookmark(p, node.get("id", "heading"), len(doc.paragraphs))
        elif node.name in ("ul", "ol"):
            _list(doc, node)
        elif node.name == "table":
            _table(doc, node)
        elif node.name == "blockquote":
            for child in node.find_all("p", recursive=False):
                p = _rtl_paragraph(doc.add_paragraph(style="Quote"))
                _inline(p, child)
        elif node.name in ("p", "pre"):
            p = _rtl_paragraph(doc.add_paragraph())
            _inline(p, node)
            if "unit-meta" in node.get("class", []):
                p.paragraph_format.keep_with_next = True
        elif node.name != "hr":
            _blocks(doc, node)


def md_to_docx_rtl(md_text: str, title: str) -> Document:
    doc = Document()
    doc.core_properties.title = title
    doc.core_properties.author = "انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف"
    doc.core_properties.subject = DRAFT
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin, section.bottom_margin = Mm(21), Mm(22)
    section.left_margin = section.right_margin = Mm(19)
    for name, size in (("Normal", 11), ("Title", 20), ("Heading 1", 15),
                       ("Heading 2", 13), ("Heading 3", 12), ("Quote", 11)):
        style = doc.styles[name]
        style.font.name, style.font.size = FONT, Pt(size)
        props = style.element.get_or_add_rPr()
        props.get_or_add_rFonts().set(qn("w:cs"), FONT)
        szcs = OxmlElement("w:szCs")
        szcs.set(qn("w:val"), str(size * 2))
        props.append(szcs)
        if name.startswith("Heading"):
            style.font.cs_bold = True
            style.paragraph_format.keep_with_next = True
        style.paragraph_format.line_spacing = 1.65
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.widow_control = True
    header = _rtl_paragraph(section.header.paragraphs[0])
    _rtl_run(header.add_run(title), size=8)
    footer = _rtl_paragraph(section.footer.paragraphs[0])
    _rtl_run(footer.add_run("پیشنهادی ـ تصویب‌نشده | صفحه "), size=8)
    _field(footer, "PAGE", "۱")
    _rtl_run(footer.add_run(" از "), size=8)
    _field(footer, "NUMPAGES", "۱")
    cover = _rtl_paragraph(doc.add_paragraph(style="Title"))
    cover.paragraph_format.space_before = Pt(65)
    _rtl_run(cover.add_run(title), bold=True, size=20)
    _rtl_run(_rtl_paragraph(doc.add_paragraph()).add_run(DRAFT), size=13)
    _rtl_run(_rtl_paragraph(doc.add_paragraph()).add_run(
        "بسته پیشنهادی برای هفت عضو شورای مرکزی دوره آینده؛ این نسخه تصویب یا تأیید نشده است."))
    soup = parsed_markdown(md_text)
    headings = soup.find_all("h2")
    if headings:
        doc.add_page_break()
        toc_title = _rtl_paragraph(doc.add_paragraph(style="Title"))
        _rtl_run(toc_title.add_run("فهرست مطالب"), bold=True, size=17)
        # The cached TOC consists of working bookmark links. Word may replace it
        # with a paginated TOC when the user updates fields; no stale page claims.
        p = _rtl_paragraph(doc.add_paragraph())
        for kind in ("begin", "separate"):
            field = OxmlElement("w:fldChar")
            field.set(qn("w:fldCharType"), kind)
            p.add_run()._r.append(field)
            if kind == "begin":
                instruction = OxmlElement("w:instrText")
                instruction.text = ' TOC \\o "1-1" \\h \\z \\u '
                p.add_run()._r.append(instruction)
        for heading in headings:
            p = _rtl_paragraph(doc.add_paragraph())
            if heading.name == "h3":
                p.paragraph_format.right_indent = Mm(5)
            _link(p, heading.get_text(" ", strip=True), heading["id"], anchor=True)
        field = OxmlElement("w:fldChar")
        field.set(qn("w:fldCharType"), "end")
        p.add_run()._r.append(field)
        doc.add_page_break()
    _blocks(doc, soup)
    return doc


def md_to_governance_pdf(md_path: Path, pdf_path: Path, title: str) -> Path:
    from weasyprint import HTML
    document = governance_html(md_path.read_text(encoding="utf-8"), title)
    pdf_path.with_suffix(".html").write_text(document, encoding="utf-8")
    HTML(string=document, base_url=str(md_path.parent)).write_pdf(
        str(pdf_path), finisher=_pin_font_stamps)
    return pdf_path


def _rezip_deterministic(path: Path) -> None:
    """Rewrite the docx zip with fixed entry timestamps -> byte-stable output."""
    fixed = (1980, 1, 1, 0, 0, 0)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "rezip.docx"
        with zipfile.ZipFile(path) as zin, \
             zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                info.date_time = fixed
                zout.writestr(info, data)
        shutil.move(str(tmp), str(path))


def _bundle(out: Path, written: list[Path]) -> Path:
    """Only explicitly generated delivery files enter the portable package."""
    bundle = out / "governance-proposed-v1.1.zip"
    note = (
        "بسته پیشنهادی حاکمیت و تحویل دوره انجمن علمی فیزیک — نسخه ۱٫۱\n\n"
        "این اسناد تصویب یا تأیید نشده‌اند. نخست handover-guide.pdf و سپس "
        "review-adoption.pdf را بخوانید. فایل‌های DOCX قابل ویرایش‌اند؛ "
        "PDFها برای خواندن و چاپ A4 تهیه شده‌اند.\n"
        "همه چهار متن اصلی، راهنمای شروع، فرم‌های عملیاتی و همراه بررسی "
        "در نسخه کامل بسته قرار دارند. پرسش‌های اختیار و ضوابط دانشگاه "
        "پیش از تصویب باید تعیین تکلیف شوند.\n"
        "منابع خصوصی، اطلاعات اشخاص و رمزها در این بسته نیستند.\n"
    )
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        entries = {p.name: p.read_bytes() for p in written}
        entries["START-HERE.txt"] = note.encode("utf-8")
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return bundle


def build_all(out_dir: Path | None = None) -> list[Path]:
    out = Path(out_dir) if out_dir else gl.GOV / "build"
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    masters = list(gl.MASTER_FILES.values())
    parents = {p.parent for p in masters}
    for parent in sorted(parents):
        masters += [parent / f"{stem}.md" for stem in COMPANIONS
                    if (parent / f"{stem}.md").exists()]
    for md in masters:
        if not md.exists():
            print(f"skip {md}: missing", file=sys.stderr)
            continue
        text = md.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        stem = md.stem
        docx_path = out / f"{stem}.docx"
        pdf_path = out / f"{stem}.pdf"
        d = md_to_docx_rtl(text, title=title)
        d.save(str(docx_path))
        _rezip_deterministic(docx_path)
        md_to_governance_pdf(md, pdf_path, title=title)
        written += [docx_path, pdf_path]
    _bundle(out, written)
    return written


if __name__ == "__main__":
    for f in build_all():
        print(f)
