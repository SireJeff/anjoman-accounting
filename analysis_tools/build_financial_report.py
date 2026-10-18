"""Financial report (monthly) — derived views of the reconciled ledger.

Hard reconciliation gate before anything is written: the timeline.json
monthly aggregates must match a fresh recomputation from Transactions.csv on
BOTH bases — all 96 rows and status-Supported rows — and the supported basis
must reproduce reports/2026-10-10/final_checks.json exactly.
"""
import argparse

import pandas as pd

from . import i18n
from .common import ROOT, LEDGER_CSV, LEDGER_DIR, WINDOW_END, WINDOW_START, read_json
from .correlate import _load_tx
from .i18n import t, term
from .report_common import md_to_pdf, md_to_pdf_rtl

TOL = 0.5  # toman

OUT = ROOT / "reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md"
OUT_FA = OUT.with_name("Anjoman_Financial_Report_Monthly_FA.md")
FA_LEDGER = LEDGER_DIR / "fa/Accounting_Data_FA.json"

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


def img(alt_key, name, lang):
    return f"![{t(alt_key, lang)}]({'charts' if lang == 'en' else 'charts_fa'}/{name}.png)"


def _reason(r, lang, fa_rows):
    """Review reason in the report language (R11)."""
    if lang == "en":
        return (r.get("review_reason") or r.get("notes") or "unresolved").strip()
    row = fa_rows.get(r["id"])
    if row is None:
        raise i18n.CatalogError(f"{r['id']} missing from {FA_LEDGER.name}")
    return (row.get("review_reason") or row.get("notes")
            or t("fin.flag.unresolved", lang)).strip()


def _schedule_tables(title, key, months, cash, label_map, lang, kind):
    """Category/project schedule, split by year so tables stay readable."""
    out = [f"## {title}", "",
           t("fin.sched.gross_note", lang), ""]
    names = sorted({n for m in months for n in cash[m][key]},
                   key=lambda n: label_map.get(n, n))
    m04 = [m for m in months if m.startswith("1404/")]
    m05 = [m for m in months if m.startswith("1405/")]
    # the undated bucket gets ONE column (second table) so the two "All rows"
    # totals sum exactly to the grand total
    und_suffix = t("fin.sched.und_suffix", lang)
    h0 = t("fin.sched.h_category", lang) if key == "by_category" else t("fin.sched.h_project", lang)
    und_col = t("fin.sched.und_col", lang)
    h_total = t("fin.sched.h_total", lang)
    all_rows_label = t("fin.sched.all_rows", lang)
    for label, ms, with_und in (("1404", m04, False), ("1405" + und_suffix, m05, True)):
        cols = [m.split("/")[1] for m in ms] + ([und_col] if with_und else [])
        keys = ms + (["unknown"] if with_und else [])
        out += [f"### {label}", "",
                "| " + " | ".join([h0] + cols + [h_total]) + " |",
                "|" + "---|" * (len(cols) + 2)]
        for n in names:
            vals = [cash[m][key].get(n, 0.0) for m in keys]
            if not any(vals):
                continue
            row_label = term(kind, n, lang, default=label_map.get(n, n))
            out.append("| " + row_label + " | "
                       + " | ".join(fmt(v) for v in vals) + f" | {fmt(sum(vals))} |")
        col_tot = [sum(cash[m][key].get(n, 0.0) for n in names) for m in keys]
        out.append(f"| **{all_rows_label}** | " + " | ".join(f"**{fmt(v)}**" for v in col_tot)
                   + f" | **{fmt(sum(col_tot))}** |")
        out.append("")
    out.append(t("fin.sched.und_footnote", lang))
    out.append("")
    return out


def render(lang="en"):
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

    L = ["# " + t("fin.title", lang), "",
         t("fin.intro", lang, start=i18n.dt(WINDOW_START, lang), end=i18n.dt(WINDOW_END, lang),
           n=f"{len(tx)}"), ""]

    # -- monthly cashflow (ALL-rows basis, stated at the table) --------------
    L += ["## " + t("fin.cash.h_title", lang), "",
          t("fin.cash.basis", lang, n=f"{len(tx)}"), "",
          "| " + " | ".join(t(k, lang) for k in (
              "fin.cash.h_month", "fin.cash.h_greg", "fin.cash.h_receipts",
              "fin.cash.h_payments", "fin.cash.h_net", "fin.cash.h_evidence")) + " |",
          "|---|---|---:|---:|---:|---:|"]
    for m in months:
        r, p = cash[m]["Receipts"], cash[m]["Payments"]
        g = (f'{i18n.dt(gr.loc[m, "min"], lang)} {i18n.punct("arrow", lang)} '
             f'{i18n.dt(gr.loc[m, "max"], lang)}'
             if m in gr.index else "—")
        n = msgs.get(m, 0)
        ev = (t("fin.cash.ev_one", lang, n=f"{n}") if n == 1 else
              (t("fin.cash.ev_many", lang, n=f"{n}") if n else "—"))
        label = (t("fin.cash.unknown_row", lang) + "*") if m == "unknown" else m
        L.append(f"| {label} | {g} | {fmt(r)} | {fmt(p)} "
                 f"| {fmt(r - p)} | {ev} |")
    L.append(f"| **{t('fin.cash.total_row', lang)}** |  | **{fmt(tot['all_r'])}** "
             f"| **{fmt(tot['all_p'])}** | **{fmt(tot['all_r'] - tot['all_p'])}** "
             f"| **{t('fin.cash.total_msgs', lang, n=fmt(sum(msgs.values())))}** |")
    L += ["",
          t("fin.cash.unknown_note", lang),
          "",
          t("fin.cash.totals_supported", lang, sup_r=fmt(tot['sup_r']), sup_p=fmt(tot['sup_p']),
            net=fmt(tot['sup_r'] - tot['sup_p']), pay_total=f"{fc['new_payments_total']:,}",
            net_activity=f"{fc['new_net_activity']:,}"),
          "",
          t("fin.cash.totals_all", lang, all_r=fmt(tot['all_r']), all_p=fmt(tot['all_p']),
            net=fmt(tot['all_r'] - tot['all_p'])),
          "",
          img("fin.cash.chart_alt", "cashflow_monthly", lang), ""]

    # -- category & project schedules ---------------------------------------
    L += _schedule_tables(t("fin.sched.title_category", lang), "by_category", months,
                          cash, CAT_LABELS, lang, "ledger_category")
    L += _schedule_tables(t("fin.sched.title_project", lang), "by_project", months,
                          cash, PROJ_LABELS, lang, "project")
    L += [img("fin.cash.cum_chart_alt", "cumulative_cash", lang), ""]

    # -- flagged transactions -------------------------------------------------
    fa_rows = {x["id"]: x for x in read_json(FA_LEDGER)["ledger"]} if lang == "fa" else {}
    review = [r for r in tx if r["status"] == "Review"]
    block = [r for r in review if r["id"] in VOLUNTEER_BLOCK]
    block_sum = sum(float(r["amount_toman"] or 0) for r in block)
    solo = sorted((r for r in review if r["id"] not in VOLUNTEER_BLOCK),
                  key=lambda r: r["id"])
    dup = [r for r in tx if r["status"] == "Duplicate"]
    inv = [r for r in tx if r["status"] == "Invoice only"]
    summ = [r for r in tx if r["status"] == "Summary only"]
    L += ["## " + t("fin.flag.h_title", lang), "",
          t("fin.flag.intro", lang, n=f"{len(review)}"), "",
          "| " + " | ".join(t(k, lang) for k in (
              "fin.flag.h_id", "fin.flag.h_direction", "fin.flag.h_amount",
              "fin.flag.h_reason")) + " |",
          "|---|---|---:|---|",
          f"| {'–'.join([VOLUNTEER_BLOCK[0], VOLUNTEER_BLOCK[-1]])} (1404/10) "
          f"| {term('direction', 'Payment', lang)} | {fmt(block_sum)} | "
          + t("fin.flag.block_reason", lang) + " |"]
    for r in solo:
        amt = fmt(float(r["amount_toman"] or 0))
        reason = _reason(r, lang, fa_rows)
        period = _period(r)
        period = t("fin.flag.period_undated", lang) if period == "undated" else period
        direction = term("direction", r["direction"], lang)
        L.append(f"| {r['id']} ({period}) "
                 f"| {direction} | {amt} | {reason} |")
    L += ["",
          t("fin.flag.other_statuses", lang,
            n_dup=f"{len(dup)}", dup_amt=fmt(sum(float(r['amount_toman'] or 0) for r in dup)),
            n_inv=f"{len(inv)}", inv_amt=fmt(sum(float(r['amount_toman'] or 0) for r in inv)),
            summ_amt=fmt(sum(float(r['amount_toman'] or 0) for r in summ))), ""]

    # -- evidence & time-of-day ----------------------------------------------
    mech = tl["mechanics"]
    tx_hours = [e for e in mech if e["kind"] == "tx-hour"]
    peaks = sorted((e for e in mech if e["kind"] == "peak"
                    and e["category"] == "accounting_group"),
                   key=lambda e: WD_RANK.get(_wd_en(e["jalali_weekday"]), 99))
    est = tl["event_start_times"].get("association-website", {})
    L += ["## " + t("fin.ev.h_title", lang), "",
          t("fin.ev.intro", lang), "",
          t("fin.ev.hours_intro", lang, n=f"{len(tx_hours)}"), ""]
    for e in sorted(tx_hours, key=lambda e: e["hour"]):
        L.append("- " + t("fin.ev.hour_line", lang, hour=f"{e['hour']:02d}", n=f"{e['n']}"))
    items = i18n.punct("comma", lang).join(
        f"{term('weekday', _wd_en(e['jalali_weekday']), lang)} "
        f"{e['hour']:02d}:00 (n={e['n']})" for e in peaks)
    L += ["", t("fin.ev.peaks_line", lang, items=items), "",
          t("fin.ev.caveat", lang, mode=f"{est.get('mode')}", n=f"{est.get('n')}",
            times=i18n.punct("comma", lang).join(est.get('times', []))), ""]

    # -- caveats ---------------------------------------------------------------
    L += ["## " + t("fin.cav.h_title", lang), "",
          "- " + t("fin.cav.b1", lang),
          "- " + t("fin.cav.b2", lang),
          "- " + t("fin.cav.b3", lang),
          "- " + t("fin.cav.b4", lang, start=i18n.dt(WINDOW_START, lang),
                   end=i18n.dt(WINDOW_END, lang), gap=i18n.punct("comma", lang).join(gap)),
          "- " + t("fin.cav.b5", lang), ""]

    text = "\n".join(L)
    assert "(auto:" not in text and "generate identically" not in text, \
        "placeholder text leaked into the report"
    return i18n.localize(text) if lang == "fa" else text


def build(lang="en"):
    text = render(lang)
    out = OUT if lang == "en" else OUT_FA
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if lang == "en":
        md_to_pdf(out, out.with_suffix(".pdf"))
    else:
        for c in ("cashflow_monthly", "cumulative_cash"):
            assert (out.parent / "charts_fa" / f"{c}.png").exists(), f"missing charts_fa/{c}.png"
        md_to_pdf_rtl(out, out.with_suffix(".pdf"),
                      title="گزارش مالی ماهانهٔ انجمن علمی فیزیک",
                      footer="انجمن علمی فیزیک | گزارش مالی ماهانه | ۱۴۰۵/۰۷/۲۲")
        html = out.with_suffix(".html").read_text(encoding="utf-8")
        for spot in ("۱۱۲٬۵۵۲٬۰۰۰", "۹۹٬۰۸۵٬۱۹۵", "۱۳٬۴۶۶٬۸۰۵"):
            assert spot in html, f"FA spot string {spot} missing"
    print(f"[gate] reconciliation passed on both bases; wrote {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("en", "fa"), default="en")
    print(build(ap.parse_args().lang))
