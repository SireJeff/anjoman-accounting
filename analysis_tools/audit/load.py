# analysis_tools/audit/load.py
"""Read the source ledger and the four audit data files; validate shapes."""
import csv
import json
from pathlib import Path

from ..common import LEDGER_CSV, ROOT

DATA = ROOT / "analysis_tools/audit/data"
SOURCE_CSV = LEDGER_CSV

SOURCE_COLS = ["id", "date_gregorian", "date_jalali", "period_jalali",
               "direction", "amount_original", "unit_original", "amount_toman",
               "counterparty", "description_en", "description_fa", "category",
               "project", "status", "evidence_basis", "cash_account",
               "message_ids", "tracking_id", "duplicate_of", "review_reason",
               "notes", "sources"]
AUDIT_COLS = ["source_status", "pending_reason", "parent", "date_basis",
              "evidence_label", "open_item", "changed_fields"]

NEW_STATUSES = {"Pending", "Payable", "Supporting detail", "Internal transfer",
                "Memo"}
DATE_BASES = {"printed", "event-day proxy", "on or before", "month only",
              "Telegram post time", "by event association", "reports posted"}
ACCOUNT_TYPES = {"personal", "association", "volunteer", "event custodian",
                 "cash", "not evidenced"}


class AuditError(RuntimeError):
    pass


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_source():
    with open(SOURCE_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 96:
        raise AuditError(f"expected 96 source rows, got {len(rows)}")
    if any(set(r) != set(SOURCE_COLS) for r in rows):
        raise AuditError("source columns drifted from SOURCE_COLS")
    return rows


def load_register():
    reg = _read_json(DATA / "decisions.json")
    _validate_register(reg)
    return reg


def _validate_register(reg):
    if len(reg) != 38 or any(e["id"] in {e2["id"] for e2 in reg[:i]}
                             for i, e in enumerate(reg)):
        raise AuditError("register must hold 38 unique ids")


def load_mechanical():
    m = _read_json(DATA / "mechanical.json")
    allowed = {"description_en", "description_fa", "tracking_id", "message_ids",
               "notes", "evidence_basis"}
    for e in m:
        if e["field"] not in allowed:
            raise AuditError(f"{e['id']}: field {e['field']!r} not mechanical")
    return m


def load_evidence():
    ev = _read_json(DATA / "evidence_index.json")
    if "rows" not in ev or "balance_chain" not in ev:
        raise AuditError("evidence_index.json needs 'rows' and 'balance_chain'")
    return ev


def load_accounts():
    acc = _read_json(DATA / "accounts.json")["accounts"]
    bad = {c: a["type"] for c, a in acc.items() if a["type"] not in ACCOUNT_TYPES}
    if bad:
        raise AuditError(f"bad account types: {bad}")
    return acc
