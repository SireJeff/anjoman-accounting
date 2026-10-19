# analysis_tools/audit/bridge.py
"""Bridges from the 2026-10-10 published totals to the audited totals, plus
the audited all-rows decomposition.

Two bases:
  supported — the published supported-cash figures to the audited Supported
              cash (G5: 112,552,000 receipts / 99,393,195 payments);
  allrows   — the 2026-10-14 builder's all-rows totals to the audited
              all-rows totals (G5: 139,787,000 / 133,539,774).
Sides are direction-based: Receipt rows feed receipts, Payment rows feed
payments, Internal-transfer direction feeds neither side (custody-only).
R-02's -5,000 moves supported cash and therefore appears in both bridges;
R-06/R-07 are pending-side so only all-rows moves. Amounts stay float
end-to-end; rounding happens only at display (Task 12). No value here is
masked or scrubbed (faithful-data ruling).
"""
from . import load
from .load import AuditError

TOL = 0.5
CASH_STATUS = "Supported"
TRANSFER_STATUS = "Internal transfer"
PENDING_STATUSES = ("Pending", "Payable")
EXCLUDED_STATUSES = ("Supporting detail", "Duplicate", "Memo")

# 2026-10-10 published starting points (G5-locked endpoints audited below).
SUPPORTED_START = {"receipts": 112552000.0, "payments": 99085195.0}
ALLROWS_START = {"receipts": 139787000.0, "payments": 123265994.0}

# dr / dp are the line deltas on the receipts / payments side.
supported_lines = [
    {"id": "R-01", "tx": "TX0036", "dr": 0.0, "dp": 300000.0,
     "note": "TX0036 direction Unknown → Payment, now Supported"},
    {"id": "R-02", "tx": "TX0031", "dr": 0.0, "dp": -5000.0,
     "note": "TX0031 amount corrected 235,000 → 230,000"},
    {"id": "D-06", "tx": "TX0042", "dr": 0.0, "dp": 13000.0,
     "note": "TX0042 separate 130,000-rial poster slip, now Supported"},
]

allrows_lines = [
    {"id": "R-02", "tx": "TX0031", "dr": 0.0, "dp": -5000.0,
     "note": "TX0031 amount corrected 235,000 → 230,000"},
    {"id": "R-06", "tx": "TX0049", "dr": 0.0, "dp": 10003780.0,
     "note": "TX0049 Sepah withdrawal filled at 10,003,780 toman, "
             "stays pending"},
    {"id": "R-07", "tx": "TX0058", "dr": 0.0, "dp": 275000.0,
     "note": "TX0058 Yalda spend set to 275,000 toman, payable to Hossein"},
]


def _amount(row):
    v = row.get("amount_toman", "")
    return float(v) if v != "" else 0.0


def _side(direction):
    """Direction -> side bucket; None feeds neither side (internal
    transfers are custody-only, so they move no total here)."""
    if direction == "Receipt":
        return "receipts"
    if direction == "Payment":
        return "payments"
    return None


def _cash_end(rows):
    """Audited cash endpoint: Supported rows only, per direction side."""
    end = {"receipts": 0.0, "payments": 0.0}
    for r in rows:
        if r["status"] != CASH_STATUS:
            continue
        side = _side(r["direction"])
        if side is None:
            raise AuditError(
                f"{r['id']}: Supported row with direction {r['direction']!r}")
        end[side] += _amount(r)
    return end


def _allrows_end(rows):
    """Audited all-rows endpoint: every row on its direction side."""
    end = {"receipts": 0.0, "payments": 0.0}
    for r in rows:
        side = _side(r["direction"])
        if side is not None:
            end[side] += _amount(r)
    return end


def bridges(rows):
    """The two bridges as {basis: {start, lines, end}}: start from the
    2026-10-10 constants, lines fixed per the decisions, end computed from
    the audited rows."""
    return {
        "supported": {"start": dict(SUPPORTED_START),
                      "lines": [dict(l) for l in supported_lines],
                      "end": _cash_end(rows)},
        "allrows": {"start": dict(ALLROWS_START),
                    "lines": [dict(l) for l in allrows_lines],
                    "end": _allrows_end(rows)},
    }


def decompose(rows):
    """Audited all-rows totals split per side into the four buckets:
    cash (Supported), internal_transfer (Internal-transfer status on that
    side), pending (Pending + Payable), excluded (Supporting detail,
    Duplicate, Memo). Sums per side equal the all-rows endpoints."""
    out = {side: {"cash": 0.0, "internal_transfer": 0.0, "pending": 0.0,
                  "excluded": 0.0}
           for side in ("receipts", "payments")}
    for r in rows:
        side = _side(r["direction"])
        if side is None:
            continue
        status = r["status"]
        if status == CASH_STATUS:
            key = "cash"
        elif status == TRANSFER_STATUS:
            key = "internal_transfer"
        elif status in PENDING_STATUSES:
            key = "pending"
        elif status in EXCLUDED_STATUSES:
            key = "excluded"
        else:
            raise AuditError(f"{r['id']}: unknown audit status {status!r}")
        out[side][key] += _amount(r)
    return out


def check(bridges_dict):
    """Gate G2: on each basis and side, start plus the line deltas reaches
    the audited end within TOL, and every line id exists in the decision
    register."""
    register_ids = {e["id"] for e in load.load_register()}
    for basis, b in bridges_dict.items():
        for side, key in (("receipts", "dr"), ("payments", "dp")):
            delta = sum(l[key] for l in b["lines"])
            if abs(b["start"][side] + delta - b["end"][side]) > TOL:
                raise AssertionError(
                    f"G2 {basis}/{side}: start {b['start'][side]:,.1f} plus "
                    f"lines {delta:,.1f} does not reach the audited end "
                    f"{b['end'][side]:,.1f}")
    missing = sorted({l["id"] for b in bridges_dict.values()
                      for l in b["lines"] if l["id"] not in register_ids})
    if missing:
        raise AssertionError(
            f"G2: bridge lines missing from the register: {missing}")
