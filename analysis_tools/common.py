"""Shared helpers for the anjoman analysis pipeline."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

SOURCES = {
    "private_group":    ROOT / "anjoman_private_group_report",
    "public_group":     ROOT / "anjoman_public_group_export/ChatExport_2026-10-13",
    "channel":          ROOT / "anjoman_channel_content",
    "accounting_group": ROOT / "anjoman_accounting_information/anjoman_accounting_group_export",
    "summerschool_channel": ROOT / "anjoman_summerschool_channel_content/ChatExport_2026-10-14",
}
LEDGER_CSV = ROOT / "anjoman_accounting_information/reports/2026-10-10/Transactions.csv"
LEDGER_DIR = LEDGER_CSV.parent
WINDOW_START, WINDOW_END = "2025-05-28", "2026-10-14"

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def normalize_digits(s: str) -> str:
    return (s or "").translate(FA_DIGITS)

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
