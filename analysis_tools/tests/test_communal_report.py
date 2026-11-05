# analysis_tools/tests/test_communal_report.py
"""Test suite for the publishable Persian Communal Performance & Accountability Report."""
from pathlib import Path
from pypdf import PdfReader
from analysis_tools import common
from analysis_tools.audit import pii


REPORT_DIR = common.REPORTS / "2026-11-03"
MD_PATH = REPORT_DIR / "Anjoman_Communal_Performance_Report_FA.md"
HTML_PATH = REPORT_DIR / "Anjoman_Communal_Performance_Report_FA.html"
PDF_PATH = REPORT_DIR / "Anjoman_Communal_Performance_Report_FA.pdf"


def test_communal_report_files_exist():
    assert MD_PATH.is_file(), f"Missing {MD_PATH}"
    assert HTML_PATH.is_file(), f"Missing {HTML_PATH}"
    assert PDF_PATH.is_file(), f"Missing {PDF_PATH}"


def test_communal_report_content_and_scale():
    text = MD_PATH.read_text(encoding="utf-8")
    words = text.split()
    assert len(words) >= 2000, f"Expected comprehensive report (>=2000 words), got {len(words)}"
    
    # Must contain essential chapter headings / concepts
    required_concepts = [
        "پیش‌گفتار",
        "داشبورد",
        "مدرسه تابستانه",
        "معارفه",
        "شب یلدا",
        "چای و فیزیک",
        "اردوی رصدی",
        "بهره‌وری",
        "آسیب‌شناسی",
        "تراز مالی",
        "توصیه‌ها"
    ]
    for c in required_concepts:
        assert c in text, f"Missing concept in communal report: {c}"


def test_communal_report_financial_concordance():
    text = MD_PATH.read_text(encoding="utf-8")
    
    # Key verified financial and performance metrics (in Persian or ASCII digits)
    assert "۳۱٬۱۵۹٬۱۳۲" in text or "31,159,132" in text, "Missing closing surplus figure"
    assert "۱۴۴٬۴۷۹٬۰۷۵" in text or "144,479,075" in text, "Missing receipts figure"
    assert "۱۱۳٬۳۱۹٬۹۴۳" in text or "113,319,943" in text, "Missing payments figure"
    assert "۷۲۶٬۵۲۷" in text or "726,527" in text, "Missing Instagram impressions figure"
    assert "۶٬۰۲۹" in text or "6,029" in text, "Missing follower growth figure"


def test_communal_report_pii_clean():
    for path in (MD_PATH, HTML_PATH):
        findings = pii.scan(path.read_text(encoding="utf-8"))
        assert not findings, f"PII found in {path.name}: {findings}"
    
    pdf_text = "".join(p.extract_text() or "" for p in PdfReader(PDF_PATH).pages)
    pdf_findings = pii.scan(pdf_text)
    assert not pdf_findings, f"PII found in {PDF_PATH.name}: {pdf_findings}"


def test_communal_report_pdf_validity():
    reader = PdfReader(PDF_PATH)
    assert len(reader.pages) >= 5, f"Expected detailed multi-page PDF, got {len(reader.pages)} pages"
    assert PDF_PATH.stat().st_size > 50_000, f"PDF seems too small: {PDF_PATH.stat().st_size} bytes"
