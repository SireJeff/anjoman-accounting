"""Financial report (monthly) — derived views of the reconciled ledger.

Hard reconciliation gate before anything is written: the timeline.json
monthly aggregates must match a fresh recomputation from Transactions.csv on
BOTH bases — all 96 rows and status-Supported rows — and the supported basis
must reproduce reports/2026-10-10/final_checks.json exactly.
"""
import pandas as pd

from .common import ROOT, LEDGER_CSV, LEDGER_DIR, WINDOW_END, WINDOW_START, read_json
from .correlate import _load_tx
from .report_common import md_to_pdf

TOL = 0.5  # toman

# reference totals (toman). ALL = every ledger row regardless of status (the
# monthly-table basis); SUPPORTED = status 'Supported' only (the headline,
# which must reproduce final_checks.json). TX0036 (300,000, Unknown direction)
# sits in ALL payments alongside the 4 Duplicate-status rows.
ALL_TOTALS = {"Receipts": 139_787_000.0, "Payments": 123_265_994.0}
SUP_TOTALS = {"Receipts": 112_552_000.0, "Payments": 99_085_195.0}
UNDATED_TOTAL = 4_664_700.0  # TX0060 (1,664,700) + TX0096 (3,000,000)

# display labels (tables only; keys are raw CSV values)
CAT_LABELS = {"Course fees": "Course fees", "Teaching": "Teaching", "Events": "Events",
              "Website domain": "Website domain", "Unclassified": "Unclassified"}
PROJ_LABELS = {"Unknown (likely 1405 summer school)": "Unknown (1405 summer school?)"}

# keys are ZWNJ-stripped: ledger data writes یک‌شنبه etc. with U+200C
WEEKDAY_EN = {"شنبه": "Saturday", "یکشنبه": "Sunday", "دوشنبه": "Monday",
              "سهشنبه": "Tuesday", "چهارشنبه": "Wednesday",
              "پنجشنبه": "Thursday", "جمعه": "Friday"}
WD_RANK = {v: i for i, v in enumerate(WEEKDAY_EN.values())}


def _wd_en(fa):
    return WEEKDAY_EN.get((fa or "").replace("‌", ""), fa)

# one grouped row in the flagged list: the December-1404 event payments whose
# review reasons are all volunteer-funded / scan-ambiguity variants
VOLUNTEER_BLOCK = tuple(f"TX{i:04d}" for i in range(64, 74))


def fmt(v):
    return "—" if not v else f"{v:,.0f}"


def _period(r):
    p = r.get("period_jalali")  # undated rows arrive from pandas as NaN
    return p if isinstance(p, str) else "undated"


def _gate(cash, tx, fc):
    """Assert BOTH total bases against recomputation from the CSV."""
    all_r = sum(float(r["amount_toman"] or 0) for r in tx if r["direction"] == "Receipt")
    all_p = sum(float(r["amount_toman"] or 0) for r in tx if r["direction"] != "Receipt")
    sup_r = sum(float(r["amount_toman"] or 0) for r in tx
                if r["direction"] == "Receipt" and r["status"] == "Supported")
    sup_p = sum(float(r["amount_toman"] or 0) for r in tx
                if r["direction"] != "Receipt" and r["status"] == "Supported")
    months = sorted(cash)
    tl_r = sum(cash[m]["Receipts"] for m in months)
    tl_p = sum(cash[m]["Payments"] for m in months)
    checks = [
        ("timeline receipts vs CSV all-rows", tl_r, all_r),
        ("timeline payments vs CSV all-rows", tl_p, all_p),
        ("CSV all-rows receipts vs reference", all_r, ALL_TOTALS["Receipts"]),
        ("CSV all-rows payments vs reference", all_p, ALL_TOTALS["Payments"]),
        ("CSV supported receipts vs reference", sup_r, SUP_TOTALS["Receipts"]),
        ("CSV supported payments vs reference", sup_p, SUP_TOTALS["Payments"]),
        ("supported payments vs final_checks", sup_p, float(fc["new_payments_total"])),
        ("supported net vs final_checks", sup_r - sup_p, float(fc["new_net_activity"])),
        ("undated bucket vs reference", cash.get("unknown", {}).get("Payments", 0.0),
         UNDATED_TOTAL),
    ]
    for name, got, want in checks:
        diff = abs(got - want)
        assert diff < TOL, f"gate FAILED: {name}: {got} vs {want} (diff {diff})"
        print(f"[gate] OK {name}: {got:,.1f} == {want:,.1f}")
    return {"all_r": all_r, "all_p": all_p, "sup_r": sup_r, "sup_p": sup_p}


def _n_msgs(greg):
    def count(s):
        return len([x for x in str(s).split(";") if x.strip()]) if isinstance(s, str) else 0
    greg = greg.copy()
    greg["n_msgs"] = greg["message_ids"].map(count)
    by = greg.groupby(greg["period_jalali"].fillna("unknown"))["n_msgs"].sum()
    return by.to_dict()


def _schedule_tables(title, key, months, cash, label_map):
    """Category/project schedule, split by year so tables stay readable."""
    out = [f"## {title}", "",
           "Gross flow per month (receipts and payments summed, all 96 rows, "
           "all statuses). Month columns are Jalali; 1404 and 1405 split into "
           "two tables for width.", ""]
    names = sorted({n for m in months for n in cash[m][key]},
                   key=lambda n: label_map.get(n, n))
    m04 = [m for m in months if m.startswith("1404/")]
    m05 = [m for m in months if m.startswith("1405/")]
    # the undated bucket gets ONE column (second table) so the two "All rows"
    # totals sum exactly to the grand total
    for label, ms, with_und in (("1404", m04, False), ("1405 (+ undated*)", m05, True)):
        cols = [m.split("/")[1] for m in ms] + (["Und*"] if with_und else [])
        keys = ms + (["unknown"] if with_und else [])
        out += [f"### {label}", "",
                "| " + " | ".join([key.split("_")[1].capitalize()] + cols + ["Total"]) + " |",
                "|" + "---|" * (len(cols) + 2)]
        for n in names:
            vals = [cash[m][key].get(n, 0.0) for m in keys]
            if not any(vals):
                continue
            out.append("| " + label_map.get(n, n) + " | "
                       + " | ".join(fmt(v) for v in vals) + f" | {fmt(sum(vals))} |")
        col_tot = [sum(cash[m][key].get(n, 0.0) for n in names) for m in keys]
        out.append("| **All rows** | " + " | ".join(f"**{fmt(v)}**" for v in col_tot)
                   + f" | **{fmt(sum(col_tot))}** |")
        out.append("")
    out.append("The Und* column is the undated bucket (see the monthly summary "
               "footnote); it appears once, in the second table.")
    out.append("")
    return out


def build():
    tx = _load_tx()
    tl = read_json(ROOT / "analysis/timeline.json")
    cash = tl["monthly_cashflow"]
    fc = read_json(LEDGER_DIR / "final_checks.json")
    tot = _gate(cash, tx, fc)

    greg = pd.read_csv(LEDGER_CSV, encoding="utf-8-sig")
    msgs = _n_msgs(greg)
    gr = (greg.dropna(subset=["date_gregorian"])
          .groupby("period_jalali")["date_gregorian"].agg(["min", "max"]))
    months = sorted(cash)
    gap = [f"1404/{m:02d}" for m in range(4, 13)] + \
          [f"1405/{m:02d}" for m in range(1, 8)]
    gap = [m for m in gap if m not in cash]

    L = ["# Anjoman Financial Report — Monthly View (1404/04 – 1405/07)", "",
         f"**Window:** {WINDOW_START} → {WINDOW_END} · **Source:** reconciled ledger "
         f"of 2026-10-10 ({len(tx)} transactions, `Transactions.csv`). Derived view — "
         "this report does not re-audit; Review-status transactions are flagged in "
         "their own section below.", ""]

    # -- monthly cashflow (ALL-rows basis, stated at the table) --------------
    L += ["## Monthly cashflow summary (toman)", "",
          f"Basis: **all {len(tx)} rows, every status** — including 4 Duplicate "
          "payments, 22 Review items (among them TX0036, direction unknown) and "
          "Invoice-only rows. The headline totals beneath the table are "
          "supported-only.", "",
          "| Jalali month | Gregorian range | Receipts | Payments | Net | Evidence |",
          "|---|---|---:|---:|---:|---:|"]
    for m in months:
        r, p = cash[m]["Receipts"], cash[m]["Payments"]
        g = f'{gr.loc[m, "min"]} → {gr.loc[m, "max"]}' if m in gr.index else "—"
        n = msgs.get(m, 0)
        ev = f"{n} msg" if n == 1 else (f"{n} msgs" if n else "—")
        L.append(f"| {m + '*' if m == 'unknown' else m} | {g} | {fmt(r)} | {fmt(p)} "
                 f"| {fmt(r - p)} | {ev} |")
    L.append(f"| **Total (all rows)** |  | **{fmt(tot['all_r'])}** "
             f"| **{fmt(tot['all_p'])}** | **{fmt(tot['all_r'] - tot['all_p'])}** "
             f"| **{fmt(sum(msgs.values()))} msgs** |")
    L += ["",
          "The unknown* month row holds the two undated transactions — TX0060 "
          "pomegranate/hospitality pre-payment invoice for Yalda (1,664,700) "
          "and TX0096 declared alenush.com domain purchase (3,000,000) — which "
          "carry no `period_jalali` and therefore share one bucket.",
          "",
          f"**Totals — supported only (headline):** receipts {fmt(tot['sup_r'])} · "
          f"payments {fmt(tot['sup_p'])} · net {fmt(tot['sup_r'] - tot['sup_p'])} "
          "toman. Status `Supported` rows only — reproduces the 2026-10-10 "
          "report's final checks exactly "
          f"(`new_payments_total` {fc['new_payments_total']:,}, "
          f"`new_net_activity` {fc['new_net_activity']:,}).",
          "",
          f"**Totals — all rows:** receipts {fmt(tot['all_r'])} · payments "
          f"{fmt(tot['all_p'])} · net {fmt(tot['all_r'] - tot['all_p'])} toman. "
          "The table basis: the headline plus 4 Duplicate payments, 22 Review "
          "items (incl. TX0036 and the declared domain purchase TX0096), 3 "
          "Invoice-only rows and the Summary-only TX0094 gross-sales receipt.",
          "",
          "![Monthly cashflow — receipts, payments and net by Jalali month]"
          "(charts/cashflow_monthly.png)", ""]

    # -- category & project schedules ---------------------------------------
    L += _schedule_tables("Category schedule by month", "by_category", months,
                          cash, CAT_LABELS)
    L += _schedule_tables("Project schedule by month", "by_project", months,
                          cash, PROJ_LABELS)
    L += ["![Cumulative net cash across the ledger period]"
          "(charts/cumulative_cash.png)", ""]

    # -- flagged transactions -------------------------------------------------
    review = [r for r in tx if r["status"] == "Review"]
    block = [r for r in review if r["id"] in VOLUNTEER_BLOCK]
    block_sum = sum(float(r["amount_toman"] or 0) for r in block)
    solo = sorted((r for r in review if r["id"] not in VOLUNTEER_BLOCK),
                  key=lambda r: r["id"])
    dup = [r for r in tx if r["status"] == "Duplicate"]
    inv = [r for r in tx if r["status"] == "Invoice only"]
    summ = [r for r in tx if r["status"] == "Summary only"]
    L += ["## Flagged transactions (Review status)", "",
          f"{len(review)} rows sit in Review — outside the supported headline, "
          "inside the all-rows tables above. The ten December-1404 event "
          "payments whose reasons are all volunteer-funded or scan-ambiguity "
          "variants are grouped; the rest follow individually.", "",
          "| ID / period | Direction | Amount | Why flagged |", "|---|---|---:|---|",
          f"| {'–'.join([VOLUNTEER_BLOCK[0], VOLUNTEER_BLOCK[-1]])} (1404/10) "
          f"| Payment | {fmt(block_sum)} | Grouped: volunteer-funded or "
          "scan-ambiguous event payments (supports TX0050, TX0062/63 and the "
          "Parnian reimbursement; several may be duplicate scans of one slip) |"]
    for r in solo:
        amt = fmt(float(r["amount_toman"] or 0))
        reason = (r.get("review_reason") or r.get("notes") or "unresolved").strip()
        L.append(f"| {r['id']} ({_period(r)}) "
                 f"| {r['direction']} | {amt} | {reason} |")
    L += ["",
          f"Also outside the supported headline: {len(dup)} Duplicate payments "
          f"({fmt(sum(float(r['amount_toman'] or 0) for r in dup))} toman), "
          f"{len(inv)} Invoice-only rows "
          f"({fmt(sum(float(r['amount_toman'] or 0) for r in inv))} toman, incl. "
          "TX0060), and 1 Summary-only receipt "
          f"({fmt(sum(float(r['amount_toman'] or 0) for r in summ))} toman, "
          "TX0094 platform-reported gross ticket sales).", ""]

    # -- evidence & time-of-day ----------------------------------------------
    mech = tl["mechanics"]
    tx_hours = [e for e in mech if e["kind"] == "tx-hour"]
    peaks = sorted((e for e in mech if e["kind"] == "peak"
                    and e["category"] == "accounting_group"),
                   key=lambda e: WD_RANK.get(_wd_en(e["jalali_weekday"]), 99))
    est = tl["event_start_times"].get("association-website", {})
    L += ["## Evidence and time-of-day notes", "",
          "The Evidence column above counts ledger `message_ids` — the "
          "accounting-group messages each month's rows are linked to. Where a "
          "transaction links to messages, timestamps come from the Telegram "
          "export and are **export-local (UTC+03:30)**: they show when the "
          "treasurer posted, not necessarily when cash moved.", "",
          f"Accounting-group hours holding at least 5 TX-linked messages "
          f"(n ≥ 5 only, {len(tx_hours)} hours):", ""]
    for e in sorted(tx_hours, key=lambda e: e["hour"]):
        L.append(f"- {e['hour']:02d}:00 — {e['n']} TX-linked messages")
    L += ["", "Weekday peaks in the accounting group (n ≥ 5): "
          + ", ".join(f"{_wd_en(e['jalali_weekday'])} "
                      f"{e['hour']:02d}:00 (n={e['n']})" for e in peaks) + ".", "",
          "Caveats: these counts are **messages, not transactions**, and "
          "start-time mention counts include deadline times. Example — the "
          "money-linked association-website thread most often mentions start "
          f"{est.get('mode')} (n={est.get('n')}), but its distinct times are "
          f"{', '.join(est.get('times', []))}, so n counts a 23:59 deadline "
          "alongside real starts.", ""]

    # -- caveats ---------------------------------------------------------------
    L += ["## Caveats", "",
          "- **Net activity is not closing cash.** Cash custodianship mixes "
          "personal and association funds; opening cash and bank-reconciled "
          "closing cash remain unavailable (2026-10-10 report, remaining gaps).",
          "- **Monthly tables are all-rows basis** (stated at the table): every "
          "status included. Only the headline totals are supported-only.",
          "- **Review items are flagged, not resolved**: TX0096 (declared "
          "3,000,000 domain purchase) and TX0036 (direction unknown, 300,000) "
          "stay outside supported totals until date, funding and direction are "
          "clarified.",
          f"- **Window**: {WINDOW_START} → {WINDOW_END} fully covers the ledger "
          "period 1404/04 – 1405/07; months with no ledger rows "
          f"({', '.join(gap)}) are omitted from the tables.",
          "- Derived from the reconciled 2026-10-10 ledger; this report does "
          "not re-audit. Message timestamps are export-local (UTC+03:30).", ""]

    text = "\n".join(L)
    assert "(auto:" not in text and "generate identically" not in text, \
        "placeholder text leaked into the report"
    out = ROOT / "reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    md_to_pdf(out, out.with_suffix(".pdf"))
    print(f"[gate] reconciliation passed on both bases; wrote {out}")
    return out


if __name__ == "__main__":
    print(build())
