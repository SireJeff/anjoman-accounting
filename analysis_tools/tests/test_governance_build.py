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
    doc = md_to_docx_rtl(MD, title="آزمون")
    a, b = tmp_path / "a.docx", tmp_path / "b.docx"
    doc.save(str(a)); doc.save(str(b))
    from analysis_tools.governance_build import _rezip_deterministic
    _rezip_deterministic(a); _rezip_deterministic(b)
    assert a.read_bytes() == b.read_bytes()
