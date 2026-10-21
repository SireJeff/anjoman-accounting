"""Shared helpers for the anjoman analysis pipeline."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

# Role-based layout (2026-10-21): raw inputs under data/, published report
# generations under reports/. Every module and test takes locations from here.
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
TELEGRAM = DATA / "telegram"

SOURCES = {
    "private_group":    TELEGRAM / "private_group",
    "public_group":     TELEGRAM / "public_group/ChatExport_2026-10-13",
    "channel":          TELEGRAM / "channel",
    "accounting_group": TELEGRAM / "accounting_group",
    "summerschool_channel": TELEGRAM / "summerschool/ChatExport_2026-10-14",
}
LEDGER_CSV = REPORTS / "2026-10-10/Transactions.csv"
LEDGER_DIR = LEDGER_CSV.parent
MEDIA_DOCX = DATA / "documents/گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx"
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
