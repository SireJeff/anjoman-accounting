# -*- coding: utf-8 -*-
import zipfile

from docx import Document
from pypdf import PdfReader

from analysis_tools.governance_build import md_to_docx_rtl

MD = """# اساسنامه آزمون

## بخش اول

ماده ۱ (تست): این یک **پاراگراف آزمون** است.

- بند اول
- بند دوم
"""


def test_docx_rtl_and_font(tmp_path):
    doc = md_to_docx_rtl(MD, title="آزمون")
    out = tmp_path / "t.docx"
    doc.save(str(out))
    # A .docx is a deflate-compressed zip: read word/document.xml from the
    # archive, not the raw file bytes (which can never contain readable XML).
    xml = zipfile.ZipFile(out).read("word/document.xml").decode("utf-8")
    assert "<w:bidi/>" in xml                     # RTL paragraphs
    assert "Tahoma" in xml                        # Persian-capable font
    assert "<w:bCs/>" in xml                      # bold applied to complex-script run
    assert "w:szCs" in xml                        # complex-script size set alongside sz
    assert "<w:jc " not in xml                    # bidi paragraphs: no explicit alignment
    d2 = Document(str(out))
    joined = "\n".join(p.text for p in d2.paragraphs)
    assert "پاراگراف آزمون" in joined
    assert "بند اول" in joined


def test_pdf_build(tmp_path):
    md = tmp_path / "m.md"
    md.write_text(MD, encoding="utf-8")
    from analysis_tools.report_common import md_to_pdf_rtl
    pdf = tmp_path / "m.pdf"
    md_to_pdf_rtl(md, str(pdf), title="آزمون", footer="آزمون")
    assert len(PdfReader(str(pdf)).pages) >= 1


def test_build_all_smoke(tmp_path, monkeypatch):
    from analysis_tools import governance_lint as gl
    from analysis_tools.governance_build import build_all
    # point MASTER_FILES at a temp master so we do not need D1..D4 yet
    fake = tmp_path / "x.md"
    fake.write_text(MD, encoding="utf-8")
    monkeypatch.setattr(gl, "MASTER_FILES", {"D1": fake})
    outs = build_all(tmp_path / "build")
    assert (tmp_path / "build" / "x.docx").exists()
    assert (tmp_path / "build" / "x.pdf").exists()
    assert len(outs) == 2


def test_docx_deterministic(tmp_path):
    # Two independent builds (separate Document objects from separate
    # md_to_docx_rtl calls, a tick apart) must still produce byte-identical
    # output -- the real G7 scenario is two independent build runs, not one
    # Document saved twice, so a regression that stamps a live
    # modified/revision field onto a *new* Document would slip past a
    # same-object save/save test.
    import time
    doc_a = md_to_docx_rtl(MD, title="آزمون")
    time.sleep(1.1)  # exceeds OOXML/zip's 1s (DOS) / 1s (dcterms) resolution
    doc_b = md_to_docx_rtl(MD, title="آزمون")
    a, b = tmp_path / "a.docx", tmp_path / "b.docx"
    doc_a.save(str(a)); doc_b.save(str(b))
    from analysis_tools.governance_build import _rezip_deterministic
    _rezip_deterministic(a); _rezip_deterministic(b)
    assert a.read_bytes() == b.read_bytes()


def test_docx_has_a4_semantic_headings_and_working_contents():
    """A visual bold paragraph is not a navigable document heading."""
    doc = md_to_docx_rtl(MD, title="آزمون")
    section = doc.sections[0]
    assert abs(section.page_width / 914400 - 8.2677) < 0.01
    assert abs(section.page_height / 914400 - 11.6929) < 0.01
    assert any(p.style.name == "Heading 1" and p.text == "بخش اول" for p in doc.paragraphs)
    xml = doc._element.xml
    assert 'w:bookmarkStart' in xml
    assert 'w:anchor="gov-1"' in xml
    assert any("TOC" in t.text for t in doc._element.iter() if t.tag.endswith("instrText"))
    assert "فهرست مطالب" in "\n".join(p.text for p in doc.paragraphs)


def test_docx_renders_tables_real_lists_and_inline_links():
    """Pipe tables, code and links must not leak as Markdown text."""
    md = """# راهنما

## بخش اول

متن **پررنگ** و `TX0103` و [راهنما](https://example.org/guide).

1. مرحله نخست
2. مرحله دوم

- کار اصلی
    - کار فرعی

| نقش | کار |
|---|---|
| دبیر | هماهنگی |
"""
    doc = md_to_docx_rtl(md, title="راهنما")
    assert len(doc.tables) == 1
    assert [[c.text for c in r.cells] for r in doc.tables[0].rows] == [
        ["نقش", "کار"], ["دبیر", "هماهنگی"]]
    xml = doc._element.xml
    assert "w:bidiVisual" in xml
    assert "w:numPr" in xml
    assert "کار فرعی" in xml
    assert "`TX0103`" not in xml
    assert "[راهنما]" not in xml
    assert any(rel.target_ref == "https://example.org/guide" for rel in doc.part.rels.values())
    code = next(r for p in doc.paragraphs for r in p.runs if r.text == "TX0103")
    assert code.font.rtl is False
    assert all("•" not in p.text for p in doc.paragraphs)
    assert 'w:lang w:val="fa-IR"' in xml


def test_docx_has_running_identity_and_page_fields():
    doc = md_to_docx_rtl(MD, title="آزمون")
    assert "آزمون" in "\n".join(p.text for p in doc.sections[0].header.paragraphs)
    footer = doc.sections[0].footer._element.xml
    assert "PAGE" in footer
    assert "NUMPAGES" in footer
    assert "python-docx" not in doc.core_properties.author


def test_word_cover_uses_persian_complex_script_font_not_theme_fallback():
    """The installed Word theme otherwise renders a Persian cover in Calibri."""
    doc = md_to_docx_rtl(MD, title="آزمون")
    title = next(p for p in doc.paragraphs if p.style.name == "Title")
    assert title.runs[0].font.rtl is True
    assert title.runs[0].font.name == "Tahoma"
    assert title.runs[0].font.cs_bold is True


def test_governance_pdf_is_navigable_and_does_not_change_shared_style(tmp_path):
    from analysis_tools import report_common
    from analysis_tools import governance_build as gb
    before = report_common._RTL_CSS
    render = getattr(gb, "md_to_governance_pdf", None)
    assert callable(render), "governance needs its own renderer, not global report CSS mutation"
    master = tmp_path / "test.md"
    master.write_text(MD + "\n## بخش دوم\n\nپایان.\n", encoding="utf-8")
    pdf = tmp_path / "test.pdf"
    render(master, pdf, title="آزمون")
    reader = PdfReader(pdf)
    assert len(reader.outline) >= 2
    assert any(page.get("/Annots") for page in reader.pages)
    assert report_common._RTL_CSS == before
    html = pdf.with_suffix(".html").read_text(encoding="utf-8")
    assert 'href="#gov-1"' in html
    assert 'lang="fa"' in html
    assert "target-counter" in html


def test_build_all_includes_companions_beside_masters(tmp_path, monkeypatch):
    from analysis_tools import governance_lint as gl
    from analysis_tools.governance_build import build_all
    master = tmp_path / "asasname.md"
    master.write_text(MD, encoding="utf-8")
    companion = tmp_path / "handover-guide.md"
    companion.write_text("# راهنمای آغاز\n\n## هفته نخست\n\nآغاز کار.", encoding="utf-8")
    monkeypatch.setattr(gl, "MASTER_FILES", {"D1": master})
    outs = build_all(tmp_path / "build")
    assert {p.name for p in outs} == {
        "asasname.docx", "asasname.pdf", "handover-guide.docx", "handover-guide.pdf"}


def test_docx_preserves_blockquotes_and_multiline_paragraphs():
    doc = md_to_docx_rtl("# راهنما\n\n> یادداشت **مهم**\n\nیک جمله\nدر دو خط.\n", title="راهنما")
    text = "\n".join(p.text for p in doc.paragraphs)
    assert ">" not in text
    assert "یادداشت مهم" in text
    assert "یک جمله\nدر دو خط." in text or "یک جمله در دو خط." in text


def test_clause_label_is_emphasized_and_version_stays_with_content():
    md = "# متن\n\n## فصل یک\n\nنسخه ۱٫۱ — پیش‌نویس\n\n۱-۱. موضوع: متن ساده.\n"
    doc = md_to_docx_rtl(md, title="متن")
    version = next(p for p in doc.paragraphs if p.text.startswith("نسخه"))
    assert version.paragraph_format.keep_with_next is True
    clause = next(p for p in doc.paragraphs if p.text.startswith("۱-۱."))
    assert clause.runs[0].font.cs_bold is True
    assert clause.text == "۱-۱. موضوع: متن ساده."


def test_pdf_contents_indexes_chapters_without_repeating_all_subheadings():
    from bs4 import BeautifulSoup
    from analysis_tools.governance_layout import governance_html
    doc = BeautifulSoup(governance_html("# متن\n\n## فصل\n\n### بخش کوچک\n\nمتن.", "متن"), "html.parser")
    assert [a.get_text() for a in doc.select("nav a")] == ["فصل"]
    assert doc.select_one('main h3[id]') is not None  # still a PDF bookmark target


def test_word_table_direction_uses_schema_order():
    from docx.oxml.ns import qn
    doc = md_to_docx_rtl("# متن\n\n| نقش | کار |\n|---|---|\n| دبیر | هماهنگی |", "متن")
    tags = [child.tag for child in doc.tables[0]._tbl.tblPr]
    assert tags.index(qn("w:bidiVisual")) < tags.index(qn("w:tblW"))


def test_word_keeps_explicit_ordered_list_start_and_paragraphs_in_list_item():
    doc = md_to_docx_rtl("# متن\n\n3. سوم\n4. چهارم\n\n- نخست\n\n    توضیح دوم همان کار.\n", "متن")
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "توضیح دوم همان کار." in text
    from docx.oxml.ns import qn
    numbers = doc.part.numbering_part.element
    assert any(e.get(qn("w:val")) == "3" for e in numbers.iter(qn("w:startOverride")))


def test_build_all_writes_portable_bundle_without_private_inputs(tmp_path, monkeypatch):
    from analysis_tools import governance_lint as gl
    from analysis_tools.governance_build import build_all
    master = tmp_path / "asasname.md"
    master.write_text(MD, encoding="utf-8")
    (tmp_path / "private.txt").write_text("private source", encoding="utf-8")
    monkeypatch.setattr(gl, "MASTER_FILES", {"D1": master})
    out = tmp_path / "build"
    build_all(out)
    bundle = out / "governance-proposed-v1.1.zip"
    assert bundle.exists()
    with zipfile.ZipFile(bundle) as z:
        assert set(z.namelist()) == {"asasname.docx", "asasname.pdf", "START-HERE.txt"}
        assert "تصویب" in z.read("START-HERE.txt").decode("utf-8")
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in z.infolist())
