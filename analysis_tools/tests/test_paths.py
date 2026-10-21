# analysis_tools/tests/test_paths.py
"""Every location the pipeline reads or writes exists in the role-based layout."""
from analysis_tools import common


def test_telegram_exports_exist():
    for name, path in common.SOURCES.items():
        assert path.is_dir(), f"{name}: {path}"
        assert path.is_relative_to(common.TELEGRAM), f"{name} is outside data/telegram"


def test_ledger_and_media_inputs_exist():
    assert common.LEDGER_CSV.is_file(), common.LEDGER_CSV
    assert common.LEDGER_DIR == common.LEDGER_CSV.parent
    assert common.MEDIA_DOCX.is_file(), common.MEDIA_DOCX


def test_report_generations_exist():
    for d in ("2026-10-10", "2026-10-14", "2026-10-18"):
        assert (common.REPORTS / d).is_dir(), d


def test_accounting_inputs_exist():
    acc = common.DATA / "accounting"
    assert (acc / "receipts").is_dir()
    assert len(list((acc / "workbooks").glob("*.xlsx"))) == 2
    assert (acc / "documents" / "invoice-61150.pdf").is_file()


def test_old_top_level_folders_are_gone():
    for old in ("anjoman_channel_content", "anjoman_private_group_report",
                "anjoman_public_group_export", "anjoman_summerschool_channel_content",
                "anjoman_accounting_information"):
        assert not (common.ROOT / old).exists(), old
