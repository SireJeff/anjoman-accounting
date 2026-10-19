# analysis_tools/audit/apply.py
"""Apply decision rules + mechanical fixes -> audited rows and audit log.

Deterministic pipeline (no clocks, no randomness):
 1. register patches in register order (rules.RULES, sentinels resolved)
 2. new rows (P-03 split) + non-ledger pending items
 3. B-01 status mapping (internal-transfer direction before STATUS_MAP)
 4. mechanical fixes in M-id order
 5. date-pair / period completion via jdatetime (ruling 4)
 6. finishing (source_status, changed_fields, defaults) + coherence assertion

Change detection (logging, changed_fields, diff_completeness) uses one
comparator: exact equality, or numeric equality within TOL. Source amounts
are strings, patched ones floats, so 17650000.0 vs "17650000.0" is NOT a
change; writes that do not change the value are not logged.
"""
from datetime import date as _date
from functools import lru_cache

import jdatetime

from ..common import ROOT  # noqa: F401
from . import load, rules
from .load import AuditError

TOL = 0.5
STATUS_MAP = {"Supported": "Supported", "Review": "Pending",
              "Invoice only": "Pending", "Summary only": "Memo",
              "Duplicate": "Duplicate"}
PENDING_REASON = {"Review": "Review", "Invoice only": "Invoice only"}

MECHANICAL_FIELDS = {"description_en", "description_fa", "tracking_id",
                     "message_ids", "notes", "evidence_basis"}
_AMOUNT_FIELDS = ("amount_toman", "amount_original")


@lru_cache(maxsize=1)
def _src_by_id():
    """Source rows by id. Shared read-only cache; callers must not mutate."""
    return {r["id"]: r for r in load.load_source()}


@lru_cache(maxsize=1)
def _b01_evidence():
    for e in load.load_register():
        if e["id"] == "B-01":
            return _join(e["evidence"])
    return ""


def _join(evidence):
    if not evidence:
        return ""
    if isinstance(evidence, (list, tuple)):
        return "; ".join(evidence)
    return str(evidence)


def _same(a, b):
    """The change-detection comparator (see module docstring)."""
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) <= TOL
    except (TypeError, ValueError):
        return False


def _coerce_amounts(row):
    """Carry the two amount columns as floats (0.1-toman precision survives:
    float('135799.9') == 135799.9); empty stays empty."""
    for f in _AMOUNT_FIELDS:
        v = str(row.get(f, "") or "").strip()
        if v == "":
            row[f] = ""
            continue
        try:
            row[f] = float(v)
        except ValueError:
            pass


def _resolve_original(row, rid):
    """Sentinel '@original': amount_original from the row's CURRENT
    amount_toman and unit_original."""
    if row.get("amount_toman", "") == "":
        raise AuditError(f"{rid}: '@original' with empty amount_toman")
    mult = 10 if row.get("unit_original", "") == "rial" else 1
    return float(row["amount_toman"]) * mult


def _patch(rows, log, tx, field, value, rid, rationale, evidence):
    if tx not in rows:
        raise AuditError(f"{rid}: unknown row {tx!r}")
    for e in log:
        if (e["tx"] == tx and e["field"] == field
                and e["source_id"] not in (rid, "B-01")):
            raise AuditError(f"{rid}: {tx}.{field} already patched by "
                             f"{e['source_id']}")
    row = rows[tx]
    if value == "@original":
        value = _resolve_original(row, rid)
    elif isinstance(value, str) and value.startswith("@append:"):
        addition = value[len("@append:"):]
        old_text = row.get(field, "") or ""
        value = old_text + " | " + addition if old_text else addition
    if field in _AMOUNT_FIELDS:
        value = float(value)
    old = row.get(field, "")
    row[field] = value
    if not _same(old, value):
        log.append({"tx": tx, "field": field, "old": str(old), "new": value,
                    "source_id": rid, "reason": rationale,
                    "evidence": _join(evidence)})


def _create_new_rows(rows, log, p03):
    # 2a. ledger rows created by a split (rules.NEW_ROWS, decision P-03)
    for nid, spec in rules.NEW_ROWS.items():
        new = dict(rows[spec["copy_from"]])          # post-patch parent values
        for field, value in spec["set"].items():
            if value == "@original":
                value = _resolve_original(new, p03["id"])
            if field in _AMOUNT_FIELDS:
                value = float(value)
            new[field] = value
        new["id"] = nid
        new["duplicate_of"] = ""
        new["tracking_id"] = ""
        new["review_reason"] = ""
        new["source_status"] = _src_by_id()[spec["copy_from"]]["status"]
        rows[nid] = new
        log.append({"tx": nid, "field": "created", "old": "", "new": nid,
                    "source_id": p03["id"], "reason": p03["rationale"],
                    "evidence": _join(p03["evidence"])})
    # 2b. non-ledger pending items (rules.PENDING_ITEMS), cited to the
    # register entry that carries them
    reg_by_id = {e["id"]: e for e in load.load_register()}
    for p in rules.PENDING_ITEMS:
        owner = next((e for e in reg_by_id.values()
                      if e.get("pending_item", {}).get("id") == p["id"]), None)
        if owner is None:
            raise AuditError(f"pending item {p['id']} has no register entry")
        log.append({"tx": p["id"], "field": "created", "old": "",
                    "new": p.get("note", ""), "source_id": owner["id"],
                    "reason": owner["rationale"],
                    "evidence": _join(owner["evidence"])})


def _map_status(r, log):
    tx = r["id"]
    old = r["status"]
    decision_set = any(e["tx"] == tx and e["field"] == "status"
                       and e["source_id"] != "B-01" for e in log)
    if decision_set:
        src_status = _src_by_id().get(tx, {}).get("status", "")
        r["pending_reason"] = (PENDING_REASON.get(src_status, "")
                               if r["status"] == "Pending" else "")
        return
    # not decision-set: internal-transfer direction wins before STATUS_MAP
    if r.get("direction", "") == "Internal transfer":
        new = "Internal transfer"
    elif old in STATUS_MAP:
        new = STATUS_MAP[old]
    else:
        raise AuditError(f"B-01: unmapped source status {old!r} on {tx}")
    if new != old:
        log.append({"tx": tx, "field": "status", "old": str(old), "new": new,
                    "source_id": "B-01", "reason": "status mapping (B-01)",
                    "evidence": _b01_evidence()})
    r["status"] = new
    r["pending_reason"] = PENDING_REASON.get(old, "") if new == "Pending" else ""


def _mechanical(rows, log, m):
    if m["field"] not in MECHANICAL_FIELDS:      # G4: allowed fields only
        raise AuditError(f"{m['id']}: field {m['field']!r} not mechanical")
    if m["tx"] not in rows:
        raise AuditError(f"{m['id']}: unknown row {m['tx']}")
    row = rows[m["tx"]]
    old = row.get(m["field"], "")
    if _same(old, m["new"]):
        return
    row[m["field"]] = m["new"]
    log.append({"tx": m["tx"], "field": m["field"], "old": str(old),
                "new": m["new"], "source_id": m["id"], "reason": m["reason"],
                "evidence": _join(m["evidence"])})


def _jalali_to_gregorian(jal):
    y, m, d = (int(x) for x in jal.split("/"))
    return jdatetime.date(y, m, d).togregorian().isoformat()


def _gregorian_to_jalali(greg):
    y, m, d = (int(x) for x in greg.split("-"))
    return jdatetime.date.fromgregorian(
        date=_date(y, m, d)).strftime("%Y/%m/%d")


def _decider(log, tx, field):
    """Source id that last set tx.field (from the log); 'B-01' when the value
    came from the source row itself."""
    sid = "B-01"
    for e in log:
        if e["tx"] == tx and e["field"] == field:
            sid = e["source_id"]
    return sid


def _fill(r, log, field, value, deciding_field, reg_by_id):
    old = r.get(field, "")
    if _same(old, value):
        return
    r[field] = value
    sid = _decider(log, r["id"], deciding_field)
    entry = reg_by_id.get(sid)
    log.append({"tx": r["id"], "field": field, "old": str(old), "new": value,
                "source_id": sid, "reason": "derived",
                "evidence": _join(entry["evidence"]) if entry else ""})


def _complete_dates(rows, log):
    reg_by_id = {e["id"]: e for e in load.load_register()}
    for r in rows.values():
        g = r.get("date_gregorian", "")
        j = r.get("date_jalali", "")
        if g and not j:
            try:
                j = _gregorian_to_jalali(g)
            except (TypeError, ValueError, OverflowError):
                j = ""
            if j:
                _fill(r, log, "date_jalali", j, "date_gregorian", reg_by_id)
        elif j and not g:
            try:
                g = _jalali_to_gregorian(j)
            except (TypeError, ValueError, OverflowError):
                g = ""
            if g:
                _fill(r, log, "date_gregorian", g, "date_jalali", reg_by_id)
        if not r.get("period_jalali", "") and j:
            y, m = j.split("/")[:2]
            _fill(r, log, "period_jalali", f"{y}/{m}", "date_jalali",
                  reg_by_id)


def _finish_row(r):
    src = _src_by_id().get(r["id"])
    for f in ("parent", "date_basis", "evidence_label", "open_item",
              "pending_reason"):
        r.setdefault(f, "")
    if src is None:                       # created row: no source counterpart
        r["changed_fields"] = "created"
        return
    r["source_status"] = src["status"]
    r["changed_fields"] = ";".join(
        f for f in load.SOURCE_COLS if not _same(r.get(f, ""), src[f]))


def _check_coherence(rows):
    for r in rows:
        toman = str(r.get("amount_toman", "") or "").strip()
        orig = str(r.get("amount_original", "") or "").strip()
        if toman == "" or orig == "":
            continue
        mult = 10 if r.get("unit_original", "") == "rial" else 1
        if abs(float(orig) - float(toman) * mult) > TOL:
            raise AuditError(
                f"{r['id']}: amount_original {orig} inconsistent with "
                f"amount_toman {toman} (unit {r.get('unit_original', '')!r})")


def diff_completeness(rows, log):
    """Gate G3: every source-column difference vs the source row appears in
    the log exactly once, and every source-column log entry is such a
    difference. Audit-column writes (parent, date_basis, ...) and created
    rows/items are outside the bijection; created rows still need their
    'created' entry."""
    src = _src_by_id()
    by_id = {r["id"]: r for r in rows}
    problems = []
    counts = {}
    for e in log:
        if e["field"] not in load.SOURCE_COLS or e["tx"] not in src:
            continue
        counts[(e["tx"], e["field"])] = counts.get((e["tx"], e["field"]), 0) + 1
    for tx, srow in src.items():
        arow = by_id.get(tx)
        if arow is None:
            problems.append(f"{tx}: missing from audited rows")
            continue
        for f in load.SOURCE_COLS:
            if _same(arow.get(f, ""), srow[f]):
                continue
            n = counts.get((tx, f), 0)
            if n != 1:
                problems.append(f"{tx}.{f}: differs from source, {n} log entries")
    for (tx, f), n in sorted(counts.items()):
        arow = by_id.get(tx)
        if arow is not None and _same(arow.get(f, ""), src[tx][f]):
            problems.append(f"{tx}.{f}: {n} log entries but no difference")
    created_logged = {e["tx"] for e in log if e["field"] == "created"}
    for r in rows:
        if r["id"] not in src and r["id"] not in created_logged:
            problems.append(f"{r['id']}: created row without a 'created' entry")
    return problems


def apply():
    src_rows = load.load_source()
    register = load.load_register()
    rules.validate(register)
    mech = load.load_mechanical()
    reg_by_id = {e["id"]: e for e in register}
    rows = {r["id"]: dict(r) for r in src_rows}
    for r in rows.values():
        _coerce_amounts(r)
    log = []
    # 1. register patches, register order
    for e in register:
        for tx, field, value in rules.RULES[e["id"]]:
            _patch(rows, log, tx, field, value, e["id"],
                   e["rationale"], e["evidence"])
    # 2. new rows (P-03 split) + pending items
    _create_new_rows(rows, log, reg_by_id["P-03"])
    # 3. B-01 status mapping
    for r in rows.values():
        _map_status(r, log)
    # 4. mechanical fixes
    for m in mech:
        _mechanical(rows, log, m)
    # 5. date-pair / period completion (ruling 4)
    _complete_dates(rows, log)
    # 6. coherence
    out = []
    for r in src_rows:
        out.append(rows[r["id"]])
        for nid, spec in rules.NEW_ROWS.items():
            if spec["copy_from"] == r["id"]:
                out.append(rows[nid])
    for r in out:
        _finish_row(r)          # source_status, changed_fields, defaults
    _check_coherence(out)
    return out, log
