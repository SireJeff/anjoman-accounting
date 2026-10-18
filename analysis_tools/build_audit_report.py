"""Ledger-audit report builder — 2026-10-18 (spec §6).

Consumes the whole audit pipeline (Tasks 5-11): apply() for the audited
rows and log, balance for sheets/custody/summary, bridge for the two
bridges, load for register/mechanical/evidence/accounts, rules for the
pending/open items, emit for the deterministic data writers (and its G9
scrub), pii for the privacy scan.  Every user-visible string flows
through t("audit....") or term(...) so fa.json can translate it; every
number flows from collect_data() — no literal figures in render().
EN output is byte-stable; the FA branch passes the whole report through
localize() exactly once at the end.
"""
import argparse
import tempfile
from pathlib import Path

from .audit import apply, balance, bridge, emit, load, pii, rules
from .i18n import dt, localize, punct, t, term
from .report_common import ensure_disk, md_to_pdf, md_to_pdf_rtl

TOL = 0.5  # toman

OUT_DIR = emit.OUT_DIR
OUT_MD = OUT_DIR / "Anjoman_Ledger_Audit_Report.md"
OUT_FA = OUT_MD.with_name("Anjoman_Ledger_Audit_Report_FA.md")

# Headline figures locked by the spec (gate G5 compares each within TOL;
# allrows payments carry TX0071's 0.1 fraction, hence the .9 vs .0 gap).
LOCKED = {"cash_receipts": 112552000.0, "cash_payments": 99393195.0,
          "net": 13158805.0, "pending": 21626064.0,
          "allrows_receipts": 139787000.0, "allrows_payments": 133539774.0}

_PENDING = ("Pending", "Payable")
_EXCLUDED = ("Supporting detail", "Duplicate", "Memo")


def collect_data():
    """One pass over the pipeline: the audited rows and the audit log.
    Sheets, custody, bridges and summaries are pure functions over these
    two (the log is passed on to balance so apply() never re-runs)."""
    return apply.apply()


def _amount(row):
    v = row.get("amount_toman", "")
    return float(v) if v != "" else 0.0


def _figures(rows, log):
    """Every headline figure, computed — never taken from LOCKED.  Cash
    receipts/payments come from the row-side bridge endpoint (not the
    sheets), so G1's sheets-vs-headline check is a real cross-check."""
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS, log=log)
    bridges = bridge.bridges(rows)
    pend_rows = sum(_amount(r) for r in rows if r["status"] in _PENDING)
    pend_items = sum(float(i["amount_toman"]) for i in rules.PENDING_ITEMS)
    excluded = sum(_amount(r) for r in rows if r["status"] in _EXCLUDED)
    cash_r = bridges["supported"]["end"]["receipts"]
    cash_p = bridges["supported"]["end"]["payments"]
    return {"sheets": sheets, "bridges": bridges,
            "cash_receipts": cash_r, "cash_payments": cash_p,
            "net": cash_r - cash_p,
            "pending": pend_rows + pend_items,
            "pending_rows": pend_rows, "pending_items": pend_items,
            "excluded": excluded}


def fmt(v):
    """Toman display: whole amounts comma-separated; a fractional value is
    itself shown with one decimal (TX0071's 135,799.9).  "—" means NO DATA
    (None/empty) only — a genuine zero renders as "0"."""
    if v is None or v == "":
        return "—"
    v = float(v)
    return f"{v:,.1f}" if abs(v - round(v)) >= 1e-9 else f"{v:,.0f}"


def _sgn(v):
    """Signed toman for bridge line deltas (+300,000 / -5,000; 0 → "0")."""
    v = float(v)
    if v == 0:
        return "0"
    return ("+" if v > 0 else "-") + fmt(abs(v))


def _cell(s):
    """Dossier-faithful data text for report cells: the same G9 card scrub
    the data writers apply (16-digit run -> last 4, controller ruling) plus
    markdown pipe escaping."""
    return emit._scrub(str(s)).replace("|", "\\|")


def _labeled(label, items, lang):
    """**label** — item; item; item (em dash when there is nothing)."""
    joined = punct("semi", lang).join(items) if items else "—"
    return f"**{label}** — {joined}"


def _date_cell(r, lang):
    """dt() when the row is dated; else period + date-basis term (period
    alone when no basis is on record, e.g. TX0096)."""
    if r["date_gregorian"]:
        return dt(r["date_gregorian"], lang)
    if r["date_basis"]:
        return t("audit.tx.period_cell", lang, period=r["period_jalali"],
                 basis=term("date_basis", r["date_basis"], lang))
    return r["period_jalali"]


def _first_ref(evidence_rows, tx):
    entries = evidence_rows.get(tx) or []
    return entries[0]["ref"] if entries else ""


def _headline(L, fig, lang):
    L += ["| " + " | ".join(t(k, lang) for k in (
              "audit.h.receipts", "audit.h.payments", "audit.h.net",
              "audit.h.pending", "audit.h.excluded")) + " |",
          "|---:|---:|---:|---:|---:|",
          f"| {fmt(fig['cash_receipts'])} | {fmt(fig['cash_payments'])} "
          f"| {fmt(fig['net'])} | {fmt(fig['pending'])} "
          f"| {fmt(fig['excluded'])} |",
          "",
          t("audit.headline.pending", lang, total=fmt(fig["pending"]),
            rows=fmt(fig["pending_rows"]), pi=fmt(fig["pending_items"])),
          "",
          t("audit.headline.note", lang),
          ""]


def _bridges_section(L, fig, lang):
    L.append("## " + t("audit.s2.title", lang))
    L.append("")
    basis_of = {"supported": term("terms", "supported", lang),
                "allrows": term("terms", "all rows", lang)}
    for basis in ("supported", "allrows"):
        b = fig["bridges"][basis]
        L.append(t("audit.bridge.start", lang, basis=basis_of[basis],
                   rin=fmt(b["start"]["receipts"]),
                   pout=fmt(b["start"]["payments"])))
        for line in b["lines"]:
            L.append("- " + t("audit.bridge.line", lang, id=line["id"],
                              tx=line["tx"], note=_cell(line["note"]),
                              delta=_sgn(line["dr"] + line["dp"])))
        L.append(t("audit.bridge.end", lang, basis=basis_of[basis],
                   rin=fmt(b["end"]["receipts"]),
                   pout=fmt(b["end"]["payments"]),
                   net=fmt(b["end"]["receipts"] - b["end"]["payments"])))
        L.append("")


def _summary_section(L, fig, lang):
    L.append("## " + t("audit.s3.title", lang))
    L.append("")
    L += ["| " + " | ".join(t(k, lang) for k in (
              "audit.h.project", "audit.h.receipts", "audit.h.payments",
              "audit.h.net", "audit.h.pending", "audit.h.excluded")) + " |",
          "|---|---:|---:|---:|---:|---:|"]
    for row in balance.summary(fig["sheets"]):
        totals = row["project"] == "TOTALS"
        label = (term("terms", "headline totals", lang) if totals
                 else term("project", row["project"], lang))
        cells = [label, fmt(row["receipts"]), fmt(row["payments"]),
                 fmt(row["net"]), fmt(row["pending"]),
                 f"{row['excluded_count']}"]
        if totals:
            cells = [f"**{c}**" for c in cells]
        L.append("| " + " | ".join(cells) + " |")
    L.append("")


def _project_section(L, fig, rows, lang, evidence_rows):
    by_id = {r["id"]: r for r in rows}
    L.append("## " + t("audit.s4.title", lang))
    L.append("")
    for p, s in fig["sheets"].items():          # sheets: sorted projects
        L.append("### " + term("project", p, lang))
        L.append("")
        if s["is_empty_note"]:
            L += [t("audit.sheet.empty_note", lang), ""]
            continue
        L.append(_labeled(t("audit.sheet.receipts_by", lang),
                          [f"{_cell(k)}: {fmt(v)}" for k, v
                           in sorted(s["receipts_by_source"].items())], lang))
        L.append(_labeled(t("audit.sheet.payments_by", lang),
                          [f"{term('ledger_category', k, lang)}: {fmt(v)}"
                           for k, v
                           in sorted(s["payments_by_category"].items())],
                          lang))
        L.append(_labeled(t("audit.sheet.net", lang), [fmt(s["net"])], lang))
        L.append(_labeled(t("audit.sheet.pending", lang),
                          [fmt(s["pending"])], lang))
        for tx in s["pending_rows"]:
            L.append(f"- {tx} — {fmt(_amount(by_id[tx]))}")
        for item in s["pending_items"]:
            note = _cell(item.get("note", ""))
            L.append(f"- {item['id']} — {fmt(item['amount_toman'])} ({note})")
        L.append("")
        L.append("**" + t("audit.sheet.tx", lang) + "**")
        L.append("")
        L += ["| " + " | ".join(t(k, lang) for k in (
                  "audit.h_tx.id", "audit.h_tx.date", "audit.h_tx.counterparty",
                  "audit.h_tx.description", "audit.h_tx.amount",
                  "audit.h_tx.status", "audit.h_tx.evidence")) + " |",
              "|---|---|---|---|---:|---|---|"]
        for tx in s["tx_rows"]:
            r = by_id[tx]
            desc = (r["description_en"] if lang == "en"
                    else (r["description_fa"] or r["description_en"]))
            ref = _first_ref(evidence_rows, tx)
            L.append(f"| {tx} | {_date_cell(r, lang)} "
                     f"| {_cell(r['counterparty'])} | {_cell(desc)} "
                     f"| {fmt(r['amount_toman'])} "
                     f"| {term('status', r['status'], lang)} "
                     f"| {_cell(ref) if ref else '—'} |")
        L.append("")
        if s["excluded"]:
            L.append("**" + t("audit.sheet.excluded", lang) + "**")
            L.append("")
            for e in s["excluded"]:
                kind = term("status", e["kind"], lang)
                parent = f" ({e['parent']})" if e.get("parent") else ""
                L.append(f"- {e['id']} — {kind}{parent}")
            L.append("")
        if s["open_items"]:
            L.append(_labeled(t("audit.sheet.open", lang),
                              s["open_items"], lang))
            L.append("")


def _custody_section(L, rows, lang):
    accounts = load.load_accounts()
    L.append("## " + t("audit.s5.title", lang))
    L.append("")
    L += ["| " + " | ".join(t(k, lang) for k in (
              "audit.custody.h.account", "audit.custody.h.holder",
              "audit.custody.h.type", "audit.custody.h.in",
              "audit.custody.h.out", "audit.custody.h.transfers")) + " |",
          "|---|---|---|---:|---:|---|"]
    by_type = {}
    for c in balance.custody(rows, accounts):
        by_type.setdefault(c["type"], []).append(c)
    for ty in sorted(by_type):
        group = by_type[ty]
        sub_in = sum(c["cash_in"] for c in group)
        sub_out = sum(c["cash_out"] for c in group)
        L.append(f"| **{term('account_type', ty, lang)}** |  |  | "
                 f"**{fmt(sub_in)}** | **{fmt(sub_out)}** |  |")
        for c in group:
            holder = c["holder"]
            if holder == "not evidenced":
                holder = term("account_type", "not evidenced", lang)
            L.append(f"| {_cell(c['code'])} | {_cell(holder)} "
                     f"| {term('account_type', c['type'], lang)} "
                     f"| {fmt(c['cash_in'])} | {fmt(c['cash_out'])} "
                     f"| {punct('comma', lang).join(c['transfers'])} |")
    L += ["", t("audit.custody.note", lang), ""]


def _chain_section(L, evidence_rows, lang):
    bc = evidence_rows["balance_chain"]
    L.append("## " + t("audit.s6.title", lang))
    L.append("")
    L.append(_cell(bc["basis"]))
    L.append("")
    L.append(t("audit.s6.intro", lang, oi=bc["open_item"]))
    L.append("")
    L += ["| " + " | ".join(t(k, lang) for k in (
              "audit.h_tx.id", "audit.h_tx.description", "audit.h_tx.amount",
              "audit.h_tx.evidence")) + " |",
          "|---|---|---:|---|"]
    for g in bc["gaps"]:
        desc = f"{g['window']} ({g['direction']}): {g['note']}"
        L.append(f"| {g['id']} | {_cell(desc)} | {fmt(g['approx_toman'])} "
                 f"| {_cell(g['source'])} |")
    L.append("")


def _open_items_section(L, lang):
    L.append("## " + t("audit.s7.title", lang))
    L.append("")
    L += ["| " + " | ".join(t(k, lang) for k in (
              "audit.h_tx.id", "audit.h_tx.description", "audit.h_tx.amount",
              "audit.s7.h.what")) + " |",
          "|---|---|---:|---|"]
    for o in rules.OPEN_ITEMS:
        oid = o["id"]
        if o["txs"]:
            oid += " (" + punct("semi", lang).join(o["txs"]) + ")"
        L.append(f"| {oid} | {_cell(o['question'])} "
                 f"| {fmt(o['amount_toman'])} | {_cell(o['settles'])} |")
    L.append("")


def _log_section(L, log, lang):
    register = load.load_register()
    mechanical = load.load_mechanical()
    L.append("## " + t("audit.s8.title", lang))
    L.append("")
    L.append(t("audit.s8.register", lang, n=f"{len(register)}"))
    L.append("")
    for e in register:
        line = f"- **{e['id']}**"
        if e["tx"]:
            line += " (" + punct("comma", lang).join(e["tx"]) + ")"
        L.append(line + f" — {_cell(e['choice'])}")
    created = sum(1 for e in log if e["field"] == "created")
    L += ["", t("audit.s8.log", lang, n=f"{len(log)}", created=f"{created}"),
          ""]
    counts = {}
    for e in log:
        counts[e["source_id"]] = counts.get(e["source_id"], 0) + 1
    for sid in sorted(counts):
        L.append(f"- **{sid}** — {counts[sid]}")
    L += ["", t("audit.s8.mechanical", lang, n=f"{len(mechanical)}"), ""]
    for m in mechanical:
        L.append(f"- **{m['id']}** — {m['tx']} {m['field']}: "
                 f"{_cell(m['reason'])}")
    L.append("")


def render(lang="en"):
    """The full report (spec §6 section order).  G1 is asserted in-render:
    the consolidated per-project totals must equal the row-side headline."""
    rows, log = collect_data()
    fig = _figures(rows, log)
    balance.check_summary(fig["sheets"], fig["cash_receipts"],
                          fig["cash_payments"], fig["pending"])
    evidence_rows = load.load_evidence()["rows"]

    L = ["# " + t("audit.title", lang), ""]
    _headline(L, fig, lang)                      # 1. headline
    _bridges_section(L, fig, lang)               # 2. what changed
    _summary_section(L, fig, lang)               # 3. consolidated summary
    _project_section(L, fig, rows, lang, evidence_rows)   # 4. balance sheets
    _custody_section(L, rows, lang)              # 5. cash custody
    _chain_section(L, load.load_evidence(), lang)        # 6. balance chain
    _open_items_section(L, lang)                 # 7. open items
    _log_section(L, log, lang)                   # 8. decisions and log
    L += ["## " + t("audit.s9.title", lang), "",   # 9. method
          t("audit.s9.body", lang), ""]

    text = "\n".join(L)
    return localize(text) if lang == "fa" else text


def run_gates():
    """G1-G5 and G9, self-contained: needs neither the real report folder
    nor writes it.  G9 scans every emitted file's text (written into a
    temp dir via the emit writers, which also run their own scrub) plus
    the EN report text itself (a published output)."""
    rows, log = collect_data()
    fig = _figures(rows, log)
    sheets = fig["sheets"]
    # G1 — consolidated sheets reconcile with the row-side headline
    balance.check_summary(sheets, fig["cash_receipts"], fig["cash_payments"],
                          fig["pending"])
    # G2 — bridges reach the audited ends; every line id is in the register
    bridge.check(fig["bridges"])
    # G3 — source-column differences <-> log bijection ...
    problems = apply.diff_completeness(rows, log)
    assert problems == [], f"gate FAILED: G3 diff completeness: {problems}"
    # ... and every log source_id is a register id, a mechanical id or B-01
    # (load_mechanical re-runs the G4 field allowlist)
    valid = ({e["id"] for e in load.load_register()}
             | {m["id"] for m in load.load_mechanical()}
             | {"B-01"})
    unknown = sorted({e["source_id"] for e in log} - valid)
    assert not unknown, f"gate FAILED: G3 unknown source ids: {unknown}"
    # G5 — locked headline figures vs computed, within TOL
    computed = {k: fig[k] for k in
                ("cash_receipts", "cash_payments", "net", "pending")}
    computed["allrows_receipts"] = fig["bridges"]["allrows"]["end"]["receipts"]
    computed["allrows_payments"] = fig["bridges"]["allrows"]["end"]["payments"]
    for name in sorted(LOCKED):
        assert abs(computed[name] - LOCKED[name]) <= TOL, (
            f"gate FAILED: G5 {name}: computed {computed[name]:,.1f} "
            f"vs locked {LOCKED[name]:,.1f}")
    # G9 — privacy scan over every emitted file and the report text
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        emit.write_ledger(rows, out_dir=out_dir)
        emit.write_log(log, out_dir=out_dir)
        emit.write_register(out_dir=out_dir)
        emit.write_sheets(sheets, rules.PENDING_ITEMS, out_dir=out_dir)
        emit.write_open_items(rows, out_dir=out_dir)
        for f in sorted(out_dir.iterdir()):
            findings = pii.scan(f.read_text(encoding="utf-8-sig"))
            assert not findings, f"gate FAILED: G9 {f.name}: {findings}"
    findings = pii.scan(render("en"))
    assert not findings, f"gate FAILED: G9 report text: {findings}"


def build(lang="en"):
    """Gates first, then the data folder, the markdown and the PDF."""
    ensure_disk(OUT_MD.parent)
    run_gates()
    rows, log = collect_data()
    sheets = balance.project_sheets(rows, rules.PENDING_ITEMS, log=log)
    emit.write_ledger(rows, out_dir=OUT_DIR)
    emit.write_log(log, out_dir=OUT_DIR)
    emit.write_register(out_dir=OUT_DIR)
    emit.write_sheets(sheets, rules.PENDING_ITEMS, out_dir=OUT_DIR)
    emit.write_open_items(rows, out_dir=OUT_DIR)
    text = render(lang)
    findings = pii.scan(text)
    assert not findings, f"gate FAILED: G9 report text: {findings}"
    out = OUT_MD if lang == "en" else OUT_FA
    out.write_text(text, encoding="utf-8")
    if lang == "en":
        md_to_pdf(out, out.with_suffix(".pdf"),
                  footer="ANJOMAN | Ledger audit | 2026-10-18 | toman",
                  title=t("audit.title", lang))
    else:
        md_to_pdf_rtl(out, out.with_suffix(".pdf"),
                      title=t("audit.title", lang),
                      footer="انجمان علمی فیزیک | رسیدگی دفتر کل | ۱۴۰۵/۰۷/۲۶")
    print(f"[gates] G1-G5, G9 passed; wrote {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("en", "fa", "all"), default="en")
    lang = ap.parse_args().lang
    for l in ("en", "fa") if lang == "all" else (lang,):
        build(l)


if __name__ == "__main__":
    main()
