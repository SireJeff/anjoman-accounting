# analysis_tools/tests/test_audit_report.py
import pytest
from analysis_tools import build_audit_report as bar

def test_locked_figures():
    rows, log = bar.collect_data()
    bar.run_gates()  # G1-G5, G9 raise on failure

def test_en_render_byte_identical():
    a, b = bar.render("en"), bar.render("en")
    assert a == b

def test_gate_fires(monkeypatch):
    monkeypatch.setitem(bar.LOCKED, "cash_payments", 1.0)
    with pytest.raises(AssertionError, match="gate FAILED"):
        bar.run_gates()

def test_fa_render_byte_identical(pseudo_fa):
    a, b = bar.render("fa"), bar.render("fa")
    assert a == b

def test_number_parity():
    from analysis_tools import i18n
    assert i18n.number_tokens(bar.render("en")) == \
        i18n.number_tokens(bar.render("fa"))

def test_readonly_folders_untouched():
    import subprocess
    from analysis_tools.common import REPORTS, ROOT
    for d in ("2026-10-10", "2026-10-14"):
        p = REPORTS / d
        assert p.is_dir(), p
        subprocess.run(["git", "diff", "--quiet", "--", str(p.relative_to(ROOT))],
                       check=True, cwd=ROOT)

def test_no_pii_in_outputs():
    from pypdf import PdfReader
    from analysis_tools.audit import emit
    from analysis_tools.audit.pii import scan
    for f in emit.OUT_DIR.iterdir():
        if f.suffix == ".pdf":
            # Controller ruling 2026-10-19: PDFs are scanned by EXTRACTED
            # text (what a reader shows a human), not raw bytes -- raw bytes
            # false-positive on reportlab's classic-xref 10-digit offsets
            # and never see inside weasyprint's compressed streams.
            text = "".join(page.extract_text() or ""
                           for page in PdfReader(f).pages)
        else:
            text = f.read_text(encoding="utf-8", errors="ignore")
        hits = scan(text)
        assert hits == [], (f.name, hits)
