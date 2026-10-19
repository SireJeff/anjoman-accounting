# analysis_tools/audit/balance.py
"""Pure aggregation over the audited rows: per-project balance sheets,
cash custody per account, and the consolidated summary with gate G1.

Inclusion rules (spec §5, reproduced by the locked headline figures):
  cash    = Supported rows only. Payable/Pending are not yet cash,
            Internal transfer is custody-only, and Supporting detail /
            Duplicate / Memo rows are excluded from every sum.
  pending = Pending rows + Payable rows + the project's PENDING_ITEMS.
Amounts stay float end-to-end; rounding happens only at display (Task 12).
No value here is masked or scrubbed (faithful-data ruling; scrubbing is a
writer concern).
"""
from . import apply, load, rules
from .load import AuditError

TOL = 0.5
CASH_STATUS = "Supported"
TRANSFER_STATUS = "Internal transfer"
PENDING_STATUSES = ("Pending", "Payable")
EXCLUDED_STATUSES = ("Supporting detail", "Duplicate", "Memo")


def _amount(row):
    v = row.get("amount_toman", "")
    return float(v) if v != "" else 0.0


def _add(bucket, key, amount):
    bucket[key] = bucket.get(key, 0.0) + amount


def _check_open_items(rows):
    oi_ids = {o["id"] for o in rules.OPEN_ITEMS}
    bad = sorted({r.get("open_item", "") for r in rows
                  if r.get("open_item", "") and r["open_item"] not in oi_ids})
    if bad:
        raise AuditError(f"rows reference unknown open items: {bad}")


def _reassignments(log):
    """project -> [(destination project, decision id)] from the audit log's
    project patches, in log order."""
    out = {}
    for e in log:
        if e.get("field") == "project":
            out.setdefault(e["old"], []).append((e["new"], e["source_id"]))
    return out


def _empty_note(sheet, moved):
    """Note for a sheet with no Supported/Pending/Payable rows, naming the
    project(s) its rows were reassigned to (audit-log project patches)."""
    if sheet["receipts"] or sheet["payments"] or sheet["pending_rows"]:
        return None
    if moved:
        dests, decisions = [], []
        for dest, dec in moved:
            if dest not in dests:
                dests.append(dest)
            if dec not in decisions:
                decisions.append(dec)
        return (f"No audited rows remain: transactions reassigned to "
                f"{', '.join(dests)} ({', '.join(decisions)}).")
    if sheet["excluded"]:
        return "No cash or pending activity; only excluded rows remain."
    return None


def project_sheets(rows, pending_items, log=None):
    """Per-project balance sheets keyed by sorted project name. Seeded from
    the 13 source projects so a project emptied by decisions still appears,
    plus any project the audited rows carry."""
    if log is None:
        log = apply.apply()[1]
    _check_open_items(rows)
    projects = ({r["project"] for r in load.load_source()}
                | {r["project"] for r in rows})
    sheets = {}
    for p in sorted(projects):
        sheets[p] = {"receipts": 0.0, "payments": 0.0, "net": 0.0,
                     "pending": 0.0, "pending_rows": [], "pending_items": [],
                     "excluded": [], "receipts_by_source": {},
                     "payments_by_category": {}, "tx_rows": [],
                     "open_items": [], "is_empty_note": None}
    moved = _reassignments(log)
    for r in rows:
        s = sheets[r["project"]]
        s["tx_rows"].append(r["id"])
        status, direction = r["status"], r["direction"]
        amount = _amount(r)
        if status == CASH_STATUS:
            if direction == "Receipt":
                s["receipts"] += amount
                _add(s["receipts_by_source"], r.get("counterparty", "") or "",
                     amount)
            elif direction == "Payment":
                s["payments"] += amount
                _add(s["payments_by_category"], r.get("category", "") or "",
                     amount)
            else:
                raise AuditError(
                    f"{r['id']}: Supported row with direction {direction!r}")
        elif status in PENDING_STATUSES:
            s["pending_rows"].append(r["id"])
            s["pending"] += amount
        elif status in EXCLUDED_STATUSES:
            s["excluded"].append({
                "id": r["id"], "kind": status,
                "parent": (r.get("parent", "")
                           or r.get("duplicate_of", "") or "")})
    for p, s in sheets.items():
        s["net"] = s["receipts"] - s["payments"]
        s["pending_items"] = [dict(item) for item in pending_items
                              if item["project"] == p]
        s["pending"] += sum(float(i["amount_toman"])
                            for i in s["pending_items"])
        s["open_items"] = sorted({r.get("open_item", "") for r in rows
                                  if r["project"] == p
                                  and r.get("open_item", "")} - {""})
        s["is_empty_note"] = _empty_note(s, moved.get(p, []))
    return sheets


def custody(rows, accounts):
    """Per cash_account custody: cash in/out over Supported rows, plus the
    internal-transfer row ids. Sorted by account code."""
    unknown = sorted({r.get("cash_account", "") for r in rows
                      if r["status"] == CASH_STATUS
                      and r.get("cash_account", "") not in accounts})
    if unknown:
        raise AuditError(f"Supported rows in unknown accounts: {unknown}")
    out = []
    for code in sorted(accounts):
        acc = accounts[code]
        c = {"code": code, "holder": acc["holder"], "type": acc["type"],
             "cash_in": 0.0, "cash_out": 0.0, "transfers": []}
        for r in rows:
            if r.get("cash_account", "") != code:
                continue
            if r["status"] == CASH_STATUS:
                if r["direction"] == "Receipt":
                    c["cash_in"] += _amount(r)
                elif r["direction"] == "Payment":
                    c["cash_out"] += _amount(r)
            elif r["status"] == TRANSFER_STATUS:
                c["transfers"].append(r["id"])
        out.append(c)
    return out


def summary(sheets):
    """Consolidated summary: one row per project (sorted as the sheets),
    TOTALS last. Row: project, receipts, payments, net, pending,
    excluded_count."""
    rows = [{"project": p, "receipts": s["receipts"],
             "payments": s["payments"], "net": s["net"],
             "pending": s["pending"], "excluded_count": len(s["excluded"])}
            for p, s in sorted(sheets.items())]
    rows.append({"project": "TOTALS",
                 "receipts": sum(r["receipts"] for r in rows),
                 "payments": sum(r["payments"] for r in rows),
                 "net": sum(r["net"] for r in rows),
                 "pending": sum(r["pending"] for r in rows),
                 "excluded_count": sum(r["excluded_count"] for r in rows)})
    return rows


def check_summary(sheets, cash_receipts, cash_payments, pending):
    """Gate G1: the consolidated per-project totals reconcile with the
    headline cash receipts / payments and pending total."""
    got = {"cash receipts": sum(s["receipts"] for s in sheets.values()),
           "cash payments": sum(s["payments"] for s in sheets.values()),
           "pending": sum(s["pending"] for s in sheets.values())}
    want = {"cash receipts": cash_receipts, "cash payments": cash_payments,
            "pending": pending}
    for name in got:
        if abs(got[name] - float(want[name])) > TOL:
            raise AssertionError(
                f"G1: {name} {got[name]:.1f} does not equal the headline "
                f"{float(want[name]):.1f}")
