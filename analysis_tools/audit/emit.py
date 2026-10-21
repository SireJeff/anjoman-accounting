# analysis_tools/audit/emit.py
"""Deterministic writers for the reports/2026-10-18/ audit folder.

Every writer is a pure function of its arguments (no clock, no randomness);
output order is fixed by sorted/insertion order, never by dict iteration
accident.  Directories are created lazily inside the writer call.

G9 emit-time scrub (controller ruling): every STRING serialized to any
output file passes through _scrub(), which replaces any 16-digit decimal
run with "…" + the last 4 digits (6221061239419676 -> …9676).  The scrub
lives inside the shared serialization path (_cell for CSV, _scrub_obj for
JSON) so no call site can bypass it.  Python's \\d is Unicode-aware, so the
scrub also covers Persian-digit card runs (mirroring pii.scan, which would
flag them too).  Two deliberate exceptions:
  - write_register: byte copy of the already-clean committed decisions
    file (byte fidelity wins);
  - nothing is masked in memory or in committed data - output-time only.

Amounts are written as-is (floats keep 0.1-toman precision; TX0071's
135799.9 survives untouched); display rounding belongs to Task 12.  All
numeric columns hold per-row/per-project toman amounts of at most 9
digits, so no raw 10-digit run can appear in a numeric cell.

Balance_Sheets.csv is long-format (project, section, line_label,
amount_toman, extra) with this fixed per-project section layout, projects
in sorted order:
  receipts        one line per receipt source  (sorted receipt sources)
  payments        one line per payment category (sorted categories)
  totals          lines: receipts, payments, net, pending
  pending_rows    one line per pending/payable row id (ledger order)
  pending_items   one line per non-ledger pending item (id, amount, note)
  open_items      one line per open-item id cited by the project
  excluded        one line per excluded row (id; kind/parent in extra)
  note            the sheet's is_empty_note, when present (extra column)
Per-project totals live in the totals section; the consolidated TOTALS
row (balance.summary) is Task 12's business, not this file's.
"""
import csv
import json
import re
import shutil

from ..common import REPORTS
from . import load, rules

OUT_DIR = REPORTS / "2026-10-18"

LOG_COLS = ["tx", "field", "old", "new", "source_id", "reason", "evidence"]
SHEET_COLS = ["project", "section", "line_label", "amount_toman", "extra"]
OI_COLS = ["id", "project", "rows", "amount_toman", "question", "what_settles"]

# Exactly-16-digit runs, ASCII or Persian digits (\d is Unicode-aware),
# not part of a longer digit run - mirrors pii.scan's card pattern.
_CARD_RUN = re.compile(r"(?<!\d)\d{16}(?!\d)")


def _scrub(text):
    """Mask any 16-digit run down to its last 4 digits (G9, emit-time)."""
    return _CARD_RUN.sub(lambda m: "…" + m.group(0)[-4:], text)


def _cell(value):
    """The single CSV serialization point: stringify, then scrub.  Lists
    are joined with " | " (log evidence); None becomes empty."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = " | ".join("" if v is None else str(v) for v in value)
    elif not isinstance(value, str):
        value = str(value)
    return _scrub(value)


def _csv_string(rows, header, buf):
    """Serialize rows (dicts) under header into a text buffer.  Shared by
    every CSV writer here and by the tests; every cell passes _cell."""
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([_cell(r.get(c, "")) for c in header])


def _scrub_obj(obj):
    """Recursive G9 scrub for JSON output: string values and dict keys."""
    if isinstance(obj, str):
        return _scrub(obj)
    if isinstance(obj, list):
        return [_scrub_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {_scrub_obj(k): _scrub_obj(v) for k, v in obj.items()}
    return obj


def _write_csv(path, rows, header):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        _csv_string(rows, header, f)


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_scrub_obj(obj), f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_ledger(rows, out_dir=OUT_DIR):
    """Transactions_Audited.csv (SOURCE_COLS + AUDIT_COLS) and .json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    header = load.SOURCE_COLS + load.AUDIT_COLS
    _write_csv(out_dir / "Transactions_Audited.csv", rows, header)
    _write_json(out_dir / "Transactions_Audited.json", rows)


def write_log(log, out_dir=OUT_DIR):
    """Audit_Log.csv; evidence lists are " | "-joined inside _cell (apply()
    already emits evidence as a "; "-joined string, which passes through)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "Audit_Log.csv", log, LOG_COLS)


def write_register(register=None, out_dir=OUT_DIR):
    """Decisions_Register.json: byte copy of the committed decisions file
    (never scrubbed - byte fidelity wins; register kept for interface
    stability, the committed file is authoritative)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(load.DATA / "decisions.json",
                    out_dir / "Decisions_Register.json")


def _sheet_lines(p, s):
    """Long-format sheet lines for one project (layout: module docstring)."""
    out = []
    for label in sorted(s["receipts_by_source"]):
        out.append([p, "receipts", label, s["receipts_by_source"][label], ""])
    for label in sorted(s["payments_by_category"]):
        out.append([p, "payments", label, s["payments_by_category"][label], ""])
    for label in ("receipts", "payments", "net", "pending"):
        out.append([p, "totals", label, s[label], ""])
    for tx in s["pending_rows"]:
        out.append([p, "pending_rows", tx, "", ""])
    for item in s["pending_items"]:
        out.append([p, "pending_items", item["id"],
                    item.get("amount_toman"), item.get("note", "")])
    for oi in s["open_items"]:
        out.append([p, "open_items", oi, "", ""])
    for e in s["excluded"]:
        extra = e["kind"] + (f" (parent {e['parent']})"
                             if e.get("parent") else "")
        out.append([p, "excluded", e["id"], "", extra])
    if s.get("is_empty_note"):
        out.append([p, "note", "empty_note", "", s["is_empty_note"]])
    return out


def write_sheets(sheets, pending_items, out_dir=OUT_DIR):
    """Balance_Sheets.json (the sheets dict as computed) and the
    long-format Balance_Sheets.csv (layout in module docstring).
    pending_items is accepted for interface stability; the per-project
    split is already embedded in each sheet by balance.project_sheets."""
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "Balance_Sheets.json", sheets)
    lines = []
    for p in sorted(sheets):
        lines.extend(_sheet_lines(p, sheets[p]))
    _write_csv(out_dir / "Balance_Sheets.csv",
               (dict(zip(SHEET_COLS, ln)) for ln in lines), SHEET_COLS)


def write_open_items(rows, out_dir=OUT_DIR):
    """Open_Items.csv: one line per rules.OPEN_ITEMS entry, in id order.
    project is resolved from the referenced audited rows (distinct
    projects "; "-joined); row-free items fall back to the entry's own
    project key if it carries one (OI-07 carries none -> empty)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = {r["id"]: r for r in rows}
    out = []
    for o in rules.OPEN_ITEMS:
        projects = sorted({by_id[t]["project"] for t in o["txs"]
                           if t in by_id})
        out.append({"id": o["id"],
                    "project": "; ".join(projects) or o.get("project", ""),
                    "rows": ";".join(o["txs"]),
                    "amount_toman": o["amount_toman"],
                    "question": o["question"],
                    "what_settles": o["settles"]})
    _write_csv(out_dir / "Open_Items.csv", out, OI_COLS)
