# analysis_tools/tests/test_paths.py
"""Every location the pipeline reads or writes exists in the role-based layout."""
from analysis_tools import common


def test_telegram_exports_exist():
    for name, path in common.SOURCES.items():
        assert path.is_dir(), f"{name}: {path}"
        assert path.is_relative_to(common.TELEGRAM), f"{name} is outside data/telegram"


def test_ledger_and_media_inputs_exist():
    assert common.LEDGER_CSV.is_file(), common.LEDGER_CSV
    assert (common.LEDGER_DIR / "final_checks.json").is_file()
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


def test_governance_sources_are_git_ignored():
    import subprocess
    r = subprocess.run(["git", "check-ignore", "-q", "sources/governance/x.pdf"],
                       cwd=common.ROOT)
    assert r.returncode == 0, "sources/governance/ must stay git-ignored (public repo)"


def test_lfs_media_keep_lfs_filter():
    import subprocess
    files = subprocess.run(["git", "lfs", "ls-files", "--name-only"], cwd=common.ROOT,
                           capture_output=True, text=True, encoding="utf-8", check=True).stdout.split("\n")
    files = [f for f in files if f.strip()]
    assert len(files) == 3
    for f in files:
        assert f.startswith("data/telegram/channel/files/"), f
        attr = subprocess.run(["git", "check-attr", "filter", "--", f], cwd=common.ROOT,
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout
        assert attr.strip().endswith("filter: lfs"), attr
