"""Performance & activity report — assembled from analysis artifacts only.

Every number, date and message reference in the built markdown is generated
from the committed artifacts (timeline.json, ecosystem.json, classified.jsonl,
classification_stats.json, threads.json, profiles/*.json and the Task-11
charts). No prose claim is hand-written against memory; a final gate asserts
that zero "(auto:" placeholders survived, that all six figures are embedded,
and that the rendered PDF carries more than six pages plus known spot strings
(the docx view total 726,527 and the 13:30 dept-seminar slot).
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime

import jdatetime

from . import i18n
from .common import ROOT, read_json
from .i18n import t, term
from .report_common import md_to_pdf, md_to_pdf_rtl

OUT = ROOT / "reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.md"
OUT_FA = OUT.with_name("Anjoman_Performance_Activity_Report_FA.md")
CHARTS = ["activity_by_month", "category_breakdown", "weekday_hour_heat",
          "hour_histogram", "event_timeline", "ecosystem_map"]

# ZWNJ-stripped Persian weekday -> English (same convention as the financial
# report; timeline weekday keys carry U+200C in یک‌شنبه etc.)
WEEKDAY_EN = {"شنبه": "Saturday", "یکشنبه": "Sunday", "دوشنبه": "Monday",
              "سهشنبه": "Tuesday", "چهارشنبه": "Wednesday",
              "پنجشنبه": "Thursday", "جمعه": "Friday"}
WD_ORDER = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]

CHATTER = {"meta_noise", "community_social"}

# controller-mandated phase buckets (jalali months); the window opens
# 1404/03/07 so a 1404/03 stub precedes the first phase and is reported apart
PHASES = [
    ("Summer 1404", (1404, 4), (1404, 6)),
    ("Academic 1404-05", (1404, 7), (1405, 3)),
    ("Summer 1405", (1405, 4), (1405, 6)),
    ("Fall 1405", (1405, 7), (1405, 12)),
]


def fmt(v):
    return "—" if not v else f"{v:,.0f}"


def pct(part, whole):
    return f"{100.0 * part / whole:.1f}%" if whole else "—"


def pct2(part, whole):
    return f"{100.0 * part / whole:.2f}%" if whole else "—"


def plural(n, lang):
    return t("common.chat_one" if n == 1 else "common.chat_many", lang, n=f"{n}")


def mkey(m):
    y, mm = m.split("/")
    return (int(y), int(mm))


def jdate(iso):
    d = date.fromisoformat(iso[:10])
    jd = jdatetime.date.fromgregorian(date=d)
    return f"{jd.year}/{jd.month:02d}/{jd.day:02d}"


def clean(text, lang, n=70):
    """Table-safe one-line snippet."""
    s = " ".join((text or "").split()).replace("|", "/")
    return (s[:n] + "…") if len(s) > n else (s or t("common.no_text", lang))


def snippet(rec, lang):
    if rec.get("text_plain"):
        return clean(rec["text_plain"], lang)
    mk = rec.get("media_kinds") or []
    return (t("common.media", lang, kinds=", ".join(term("media", k, lang) for k in mk))
            if mk else t("common.no_text", lang))


def img(alt_key, name, lang):
    return f"![{t(alt_key, lang)}]({'charts' if lang == 'en' else 'charts_fa'}/{name}.png)"


def collect_data_strings():
    tl = read_json(ROOT / "analysis/timeline.json")
    return {f"data.thread.{x['event_ref']}": x["title"] for x in tl["threads"]}


def thread_title(th, lang):
    return th["title"] if lang == "en" else t(f"data.thread.{th['event_ref']}", lang)


def _table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def in_phase(month, lo, hi):
    k = mkey(month)
    return lo <= k <= hi


# --------------------------------------------------------------- section 1
def sec1(tl, stats, w_rows, lang):
    hh = tl["hour_histogram"]
    by_chat = sorted(((c, sum(v.values())) for c, v in hh.items()),
                     key=lambda kv: -kv[1])
    cats = Counter()
    for m, chats in tl["monthly_activity"].items():
        for c, cc in chats.items():
            cats.update(cc)
    cat_tot = sum(cats.values())
    cash = tl["monthly_cashflow"]
    rec = sum(v["Receipts"] for v in cash.values())
    pay = sum(v["Payments"] for v in cash.values())
    und = cash.get("unknown", {}).get("Payments", 0.0)
    threads = [th for th in tl["threads"] if not th.get("money_only")]
    money_only = [th for th in tl["threads"] if th.get("money_only")]
    top5 = sorted(threads, key=lambda th: -th["n_messages"])[:5]

    top3 = cats.most_common(3)
    L = ["## " + t("perf.s1.h_title", lang), "",
         t("perf.s1.intro", lang, n=f"{sum(n for _, n in by_chat):,}",
           total=f"{stats['total']:,}",
           cov=f"{stats['in_window']['coverage_pct']:.0f}"), "",
         t("perf.s1.by_chat_intro", lang), ""]
    L += _table([t(k, lang) for k in ("perf.s1.tbl_chats.h_chat",
                                       "perf.s1.tbl_chats.h_messages",
                                       "perf.s1.tbl_chats.h_share")],
                [[term("chat", c, lang), f"{n:,}", pct(n, sum(x for _, x in by_chat))]
                 for c, n in by_chat])
    L += ["",
          t("perf.s1.summary", lang,
            c1=term("category", top3[0][0], lang), c1n=fmt(top3[0][1]),
            c2=term("category", top3[1][0], lang), c2n=fmt(top3[1][1]),
            c3=term("category", top3[2][0], lang), c3n=fmt(top3[2][1]),
            cat_tot=fmt(cat_tot), n_threads=f"{len(tl['threads'])}",
            n_msg=f"{len(threads)}", n_money=f"{len(money_only)}",
            rec=fmt(rec), pay=fmt(pay), net=fmt(rec - pay), und=fmt(und)), "",
          t("perf.s1.top5_intro", lang), ""]
    L += _table([t(k, lang) for k in ("perf.s1.tbl_top5.h_thread",
                                       "perf.s1.tbl_top5.h_title",
                                       "perf.s1.tbl_top5.h_seen",
                                       "perf.s1.tbl_top5.h_chats",
                                       "perf.s1.tbl_top5.h_msgs",
                                       "perf.s1.tbl_top5.h_tx_total")],
                [[f"`{th['event_ref']}`", clean(thread_title(th, lang), lang, 44),
                  f"{i18n.dt(th['first_seen'], lang)} → {i18n.dt(th['last_seen'], lang)}",
                  str(len(th["chats"])), f"{th['n_messages']:,}",
                  fmt(th["tx_total_toman"])] for th in top5])
    L.append("")
    return L


# --------------------------------------------------------------- section 2
def sec2(tl, w_rows, lang):
    ma = tl["monthly_activity"]
    months = sorted(ma.keys(), key=mkey)
    # distinct message volume per month (classified.jsonl is the only artifact
    # carrying per-message rows, so multi-label double counting is avoided)
    vol = Counter(r["jalali_month"] for r in w_rows if r.get("jalali_month"))
    label = Counter()
    for m, chats in ma.items():
        for c, cc in chats.items():
            label[m] += sum(cc.values())
    thr = [th for th in tl["threads"] if not th.get("money_only")]

    def phase_of_thread(th):
        return jdate(th["first_seen"])[:7]  # YYYY/MM jalali

    def thread_phase(th):
        for name, lo, hi in PHASES:
            if in_phase(phase_of_thread(th), lo, hi):
                return name
        return None  # 1404/03 window-opening stub

    L = ["## " + t("perf.s2.h_title", lang), "",
         t("perf.s2.intro", lang), ""]
    stub_months = [m for m in months if mkey(m) < (1404, 4)]
    stub_thr = [th for th in thr if thread_phase(th) is None]
    if stub_months:
        L += [t("perf.s2.stub", lang, months=", ".join(stub_months),
                n_msgs=fmt(sum(vol[m] for m in stub_months)),
                n_thr=f"{len(stub_thr)}",
                ref=f"{max(stub_thr, key=lambda th: th['n_messages'])['event_ref']}",
                n_big=f"{max(stub_thr, key=lambda th: th['n_messages'])['n_messages']}"), ""]
    chat_msg = Counter((r["chat"], r["jalali_month"]) for r in w_rows
                       if r.get("chat") and r.get("jalali_month"))
    for name, lo, hi in PHASES:
        pm = [m for m in months if in_phase(m, lo, hi)]
        if not pm:
            continue
        pt = [th for th in thr if thread_phase(th) == name]
        chat_vol = Counter()
        cat_lab = Counter()
        for m in pm:
            for c in chat_msg:
                if c[1] == m:
                    chat_vol[c[0]] += chat_msg[c]
            for cc in ma[m].values():
                cat_lab.update(cc)
        tot_msgs = sum(vol[m] for m in pm)
        top_chat, top_n = (chat_vol.most_common(1)[0] if chat_vol
                           else ("—", 0))
        (c1, c1n), (c2, c2n) = cat_lab.most_common(2)[:2]
        biggest = max(pt, key=lambda th: th["n_messages"]) if pt else None
        pname = term("phase", name, lang)
        L.append(f"### {pname} ({pm[0]}–{pm[-1]})")
        L.append("")
        para = t("perf.s2.phase_para", lang, name=pname, m0=pm[0], m1=pm[-1],
                 n_msgs=fmt(tot_msgs),
                 top_chat=term("chat", top_chat, lang) if chat_vol else top_chat,
                 top_n=fmt(top_n),
                 c1=term("category", c1, lang), c1n=fmt(c1n),
                 c2=term("category", c2, lang), c2n=fmt(c2n))
        if pt:
            para += t("perf.s2.phase_new", lang, n=f"{len(pt)}",
                      ref=f"{biggest['event_ref']}",
                      g=f"{biggest['first_seen'][:10]}",
                      j=f"{jdate(biggest['first_seen'])}",
                      n_big=f"{biggest['n_messages']:,}",
                      chats=f"{plural(len(biggest['chats']), lang)}")
        else:
            para += t("perf.s2.phase_none", lang)
        mx = max(pm, key=lambda m: vol.get(m, 0))
        para += t("perf.s2.phase_peak", lang, month=f"{mx}",
                  n=fmt(vol.get(mx, 0)))
        L.append(para)
        L.append("")
        top = sorted(pt, key=lambda th: -th["n_messages"])[:5]
        if top:
            L += _table([t(k, lang) for k in ("perf.s2.tbl.h_thread",
                                               "perf.s2.tbl.h_first",
                                               "perf.s2.tbl.h_jalali",
                                               "perf.s2.tbl.h_msgs",
                                               "perf.s2.tbl.h_chats",
                                               "perf.s2.tbl.h_last")],
                        [[f"`{th['event_ref']}`", th["first_seen"][:10],
                          jdate(th["first_seen"]), f"{th['n_messages']:,}",
                          str(len(th["chats"])), th["last_seen"][:10]]
                         for th in top])
            L.append("")
    return L


# --------------------------------------------------------------- section 3
def sec3(tl, w_rows, lang):
    ma = tl["monthly_activity"]
    months = sorted(ma.keys(), key=mkey)
    cat_month = defaultdict(lambda: defaultdict(int))
    cats = Counter()
    for m, chats in ma.items():
        for c, cc in chats.items():
            for k, n in cc.items():
                cat_month[k][m] += n
                cats[k] += n
    total_labelings = sum(cats.values())
    # explicit event_ref affiliation per category (thread engagement view)
    aff = defaultdict(Counter)
    for r in w_rows:
        if r.get("event_ref"):
            for c in r["categories"]:
                aff[c][r["event_ref"]] += 1
    # total explicit event_ref affiliations — same basis as §7's `aff`
    expl_total = sum(1 for r in w_rows if r.get("event_ref"))

    L = ["## " + t("perf.s3.h_title", lang), "",
         t("perf.s3.intro", lang, n_lab=fmt(total_labelings), n=f"{len(w_rows):,}"), ""]
    for yr in ("1404", "1405"):
        ym = [m for m in months if m.startswith(yr)]
        if not ym:
            continue
        L += [t("perf.s3.year_note", lang, yr=yr), ""]
        hdr = ([t("perf.s3.tbl_month.h_category", lang)] + [m.split("/")[1] for m in ym]
               + [t("perf.s3.tbl_month.h_total", lang)])
        rows = []
        for cat, tot in cats.most_common():
            vals = [cat_month[cat].get(m, 0) for m in ym]
            if not any(vals):
                continue
            rows.append([term("category", cat, lang)] + [fmt(v) for v in vals]
                        + [f"**{fmt(tot)}**"])
        col_tot = [sum(cat_month[c].get(m, 0) for c in cats) for m in ym]
        rows.append([f"**{t('perf.s3.tbl_month.all_labelings', lang)}**"] +
                    [f"**{fmt(v)}**" for v in col_tot] +
                    [f"**{fmt(total_labelings)}**"])
        L += _table(hdr, rows)
        L.append("")

    L += [t("perf.s3.engaged_intro", lang, n=f"{expl_total:,}"), ""]
    rows = []
    for cat, tot in cats.most_common():
        refs = aff.get(cat, Counter()).most_common(3)
        aff_n = sum(aff.get(cat, Counter()).values())
        peak = max(cat_month[cat], key=lambda m: cat_month[cat][m]) if tot else "—"
        thr_txt = (", ".join(f"`{r}` ({n})" for r, n in refs) if refs
                   else t("perf.s3.tbl_engaged.none", lang))
        rows.append([term("category", cat, lang), fmt(tot), pct(tot, total_labelings), peak,
                     str(aff_n), thr_txt])
    L += _table([t(k, lang) for k in ("perf.s3.tbl_engaged.h_category",
                                       "perf.s3.tbl_engaged.h_labelings",
                                       "perf.s3.tbl_engaged.h_share",
                                       "perf.s3.tbl_engaged.h_peak",
                                       "perf.s3.tbl_engaged.h_explicit",
                                       "perf.s3.tbl_engaged.h_top")], rows)
    L += ["",
          img("perf.s3.chart_activity_alt", "activity_by_month", lang),
          img("perf.s3.chart_category_alt", "category_breakdown", lang), ""]
    return L


# --------------------------------------------------------------- section 4
def sec4(tl, w_rows, registry, ledger, lang):
    threads = [th for th in tl["threads"] if not th.get("money_only")]
    expl = Counter(r["event_ref"] for r in w_rows if r.get("event_ref"))
    tx_by_id = {f["tx_id"]: f for f in ledger["financial_signals"]}
    # same basis as §7: explicit event_ref affiliations vs. total thread
    # membership (explicit + keyword-fallback), so the two sections agree
    expl_total = sum(expl.values())
    affiliated_total = sum(th["n_messages"] for th in threads)
    fb_total = affiliated_total - expl_total
    L = ["## " + t("perf.s4.h_title", lang), "",
         t("perf.s4.intro", lang, n=f"{len(threads)}", fb=f"{fb_total:,}",
           aff=f"{affiliated_total:,}"), ""]
    rows = []
    for th in sorted(threads, key=lambda th: -th["n_messages"]):
        rows.append([f"`{th['event_ref']}`", i18n.dt(th["first_seen"], lang),
                     str(len(th["chats"])), f"{th['n_messages']:,}",
                     str(expl.get(th["event_ref"], 0)),
                     "—" if th["announcement_lag_days"] is None
                     else f"{th['announcement_lag_days']:+d}",
                     fmt(th["tx_total_toman"])])
    L += _table([t(k, lang) for k in ("perf.s4.tbl.h_thread", "perf.s4.tbl.h_first",
                                       "perf.s4.tbl.h_chats", "perf.s4.tbl.h_msgs",
                                       "perf.s4.tbl.h_explicit", "perf.s4.tbl.h_lag",
                                       "perf.s4.tbl.h_tx_total")], rows)
    L.append("")

    # money-only coverage gap (controller carry)
    for th in tl["threads"]:
        if th.get("money_only"):
            txs = [tx_by_id[x] for x in th["tx_ids"]]
            r = sum(x["amount_toman"] for x in txs if x["direction"] == "Receipt")
            p = sum(x["amount_toman"] for x in txs if x["direction"] != "Receipt")
            dup = [x["tx_id"] for x in txs if x.get("status") == "Duplicate"]
            L.append(
                t("perf.s4.money_gap", lang, ref=th["event_ref"],
                  title=thread_title(th, lang), n=f"{len(txs)}",
                  gross=fmt(th["tx_total_toman"]), rec=fmt(r), pay=fmt(p),
                  ids=", ".join(th["tx_ids"]))
                + (t("perf.s4.money_gap_dup", lang, ids=", ".join(dup)) if dup else ""))
            L.append("")

    L += [img("perf.s4.chart_timeline_alt", "event_timeline", lang),
          t("perf.s4.case_intro", lang), ""]
    cands = sorted(threads, key=lambda th: (-len(th["chats"]),
                                           -th["tx_total_toman"],
                                           -th["n_messages"]))
    for th in cands[:3]:
        L += _case_study(th, w_rows, registry, tx_by_id, expl, lang)
    return L


def _case_study(th, w_rows, registry, tx_by_id, expl, lang):
    ref = th["event_ref"]
    E = sorted((r for r in w_rows if r.get("event_ref") == ref),
               key=lambda r: r["timestamp"] or "")
    e_n = expl.get(ref, 0)
    fb = th["n_messages"] - e_n
    txs = [tx_by_id[x] for x in th["tx_ids"] if x in tx_by_id]
    r = sum(x["amount_toman"] for x in txs if x["direction"] == "Receipt")
    p = sum(x["amount_toman"] for x in txs if x["direction"] != "Receipt")
    reg = next((x for x in registry["threads"] if x["event_ref"] == ref), {})

    L = ["### " + t("perf.case.h_title", lang, ref=ref,
                    title=clean(thread_title(th, lang), lang, 60)), "",
         t("perf.case.intro", lang, n=f"{th['n_messages']:,}",
           n_chats=f"{len(th['chats'])}", g0=th["first_seen"][:10],
           g1=th["last_seen"][:10], j0=jdate(th["first_seen"]),
           j1=jdate(th["last_seen"]), lag=f"{th['announcement_lag_days']:+d}",
           ch_first=i18n.dt(th["chats"]["channel"]["first"], lang),
           e_n=f"{e_n:,}", pct=pct(e_n, th["n_messages"]), fb=f"{fb:,}")
         + (t("perf.case.fallback_heavy", lang) if fb > e_n else "."),
         t("perf.case.money", lang, gross=fmt(th["tx_total_toman"]),
           n=f"{len(txs)}", rec=fmt(r), pay=fmt(p))
         if txs else
         t("perf.case.no_money", lang), ""]

    # stage table: planning -> announcement -> delivery -> payment
    rows = []
    first_rec = E[0] if E else None
    rows.append([t("perf.case.stage_planning", lang),
                 i18n.dt((first_rec or {}).get("timestamp", th["first_seen"]), lang, 16),
                 f"{first_rec['chat']}#{first_rec['message_id']}"
                 if first_rec else t("perf.case.ref_thread_first", lang),
                 snippet(first_rec, lang) if first_rec else clean(thread_title(th, lang), lang, 60)])
    busiest = max(th["chats"], key=lambda c: th["chats"][c]["n"]) if th["chats"] else None
    for chat in sorted(th["chats"], key=lambda c: th["chats"][c]["first"]):
        meta = th["chats"][chat]
        if chat == "channel":
            label = t("perf.case.stage_announce", lang, n=f"{meta['n']}")
        elif chat == busiest:
            label = t("perf.case.stage_delivery", lang, chat=term("chat", chat, lang),
                      n=f"{meta['n']}")
        else:
            label = t("perf.case.stage_work", lang, chat=term("chat", chat, lang),
                      n=f"{meta['n']}")
        ex = next((m for m in E if m["chat"] == chat), None)
        if ex and ex["timestamp"] == meta["first"]:
            ref, ev = f"{chat}#{ex['message_id']}", snippet(ex, lang)
        elif ex:
            ref = t("perf.case.ref_chat_first", lang)
            ev = t("perf.case.ev_chat_first", lang, d0=i18n.dt(meta["first"], lang),
                   ref=f"{chat}#{ex['message_id']}", d1=i18n.dt(ex["timestamp"], lang))
        else:
            ref, ev = (t("perf.case.ref_chat_first", lang),
                       t("perf.case.ev_first_in_chat", lang))
        rows.append([label, i18n.dt(meta["first"], lang, 16), ref, ev])
    if th["decision_dates"]:
        rows.append([t("perf.case.stage_decisions", lang),
                     ", ".join(i18n.dt(d, lang) for d in sorted(set(th["decision_dates"]))),
                     t("perf.case.ref_decisions", lang,
                       n=f"{len(set(th['decision_dates']))}"),
                     t("perf.case.ev_decisions", lang)])
    for x in txs:
        mids = x.get("message_ids") or []
        status = x.get("status", "—")
        rows.append([t("perf.case.stage_payment", lang, tx=x["tx_id"],
                       direction=term("direction", x["direction"], lang)),
                     x.get("period", "—"),
                     ("accounting_group#" + ", accounting_group#".join(mids))
                     if mids else t("perf.case.ref_ledger_row", lang),
                     t("perf.case.ev_payment", lang, amount=fmt(x["amount_toman"]),
                       category=term("ledger_category", x["category"], lang),
                       status=term("status", status, lang) if status != "—" else status)])
    L += _table([t(k, lang) for k in ("perf.case.tbl.h_stage", "perf.case.tbl.h_date",
                                       "perf.case.tbl.h_reference",
                                       "perf.case.tbl.h_evidence")], rows)
    bm = th["chats"].get(busiest, {})
    L += ["", t("perf.case.surface", lang, chat=f"{busiest}", n=f"{bm.get('n', 0):,}",
                total=f"{th['n_messages']:,}", d0=i18n.dt(bm.get("first", ""), lang),
                d1=i18n.dt(bm.get("last", ""), lang))]
    if "docx" in (reg.get("chats") or []):
        L += ["", t("perf.case.docx", lang)]
    L.append("")
    return L


# --------------------------------------------------------------- section 5
def sec5(eco, docx, channel_profile, lang):
    nodes = {n["id"]: n for n in eco["nodes"]}
    seeds = [n for n in eco["nodes"] if n.get("seed")]
    seed_ids = {s["id"] for s in seeds}
    fwd_in, men_in = defaultdict(int), defaultdict(int)
    fwd_tot = 0
    for e in eco["edges"]:
        if e["type"] == "forward":
            fwd_tot += e["weight"]
            fwd_in[e["target"]] += e["weight"]
        else:
            men_in[e["target"]] += e["weight"]

    def seed_status(sid):
        v = eco["validation"].get(sid, "—")
        return term("validation", v, lang) if v != "—" else v

    L = ["## " + t("perf.s5.h_title", lang), "",
         t("perf.s5.intro", lang, n_nodes=f"{len(eco['nodes'])}",
           n_edges=f"{len(eco['edges'])}", n_seeds=f"{len(seeds)}",
           n_ext=f"{sum(1 for n in eco['nodes'] if n.get('type') == 'external')}"), ""]
    L += _table([t(k, lang) for k in ("perf.s5.tbl_seeds.h_seed",
                                       "perf.s5.tbl_seeds.h_label",
                                       "perf.s5.tbl_seeds.h_status",
                                       "perf.s5.tbl_seeds.h_fwd",
                                       "perf.s5.tbl_seeds.h_men")],
                [[s["id"], s["label"], seed_status(s["id"]),
                  fmt(fwd_in.get(s["id"], 0)), fmt(men_in.get(s["id"], 0))]
                 for s in seeds])
    unv = [s["id"] for s in seeds if eco["validation"].get(s["id"]) == "unverified"]
    if unv:
        unv_labels = "; ".join(f"`{u}` = {nodes[u]['label']}" for u in unv)
        L += ["", t("perf.s5.unverified", lang, labels=unv_labels,
                    n=f"{len(seeds) - len(unv)}")]
    L += ["",
          t("perf.s5.ext_intro", lang, total=fmt(fwd_tot)), ""]
    ext = sorted(((k, v) for k, v in fwd_in.items()
                  if nodes.get(k, {}).get("type") == "external"),
                 key=lambda kv: -kv[1])[:10]
    L += _table(["#"] + [t(k, lang) for k in ("perf.s5.tbl_ext.h_origin",
                                               "perf.s5.tbl_ext.h_weight",
                                               "perf.s5.tbl_ext.h_share")],
                [[str(i + 1), nodes[k]["label"], fmt(v), pct(v, fwd_tot)]
                 for i, (k, v) in enumerate(ext)])

    ch_fwd = sum(e["weight"] for e in eco["edges"]
                 if e["type"] == "forward" and e["source"] == "channel_export")
    q_fwd = fwd_in.get("quantasc", 0)
    ch_digest = next(x for x in channel_profile["candidate_threads"]
                     if x["event_ref"] == "dept-weekly-seminars")
    assoc_self = men_in.get("association", 0)
    L += ["",
          t("perf.s5.relay", lang, assoc=fmt(assoc_self), n_posts=f"{ch_digest['n']}",
            d0=i18n.dt(ch_digest["anchor_dates"][0], lang),
            d1=i18n.dt(ch_digest["anchor_dates"][-1], lang),
            q_pct=pct(q_fwd, ch_fwd), q_fwd=fmt(q_fwd), ch_fwd=fmt(ch_fwd),
            q_men=fmt(men_in.get("quantasc", 0))), ""]

    L += ["### " + t("perf.s5.docx.h_title", lang),
          "",
          t("perf.s5.docx.intro", lang, title=docx["doc_title"],
            n_par=f"{docx['n_messages']}", n_rows=f"{docx['n_table_rows']}",
            periods="; ".join(docx["periods_covered"]),
            n_metrics=f"{len(docx['metrics'])}"), ""]
    def mval(m):
        if "value" in m:
            v = float(m["value"])
            return fmt(m["value"]) if v.is_integer() else str(m["value"])
        if "value_min" in m:  # range metrics (hours of work)
            return f"{m['value_min']}–{m['value_max']}"
        return "—"

    L += _table([t(k, lang) for k in ("perf.s5.tbl_metrics.h_metric",
                                       "perf.s5.tbl_metrics.h_label",
                                       "perf.s5.tbl_metrics.h_verbatim",
                                       "perf.s5.tbl_metrics.h_value",
                                       "perf.s5.tbl_metrics.h_period")],
                [[m["id"], clean(m["label"], lang, 40), m["verbatim"], mval(m),
                  clean(m.get("period", "—"), lang, 44)]
                 for m in docx["metrics"]])
    L += ["", t("perf.s5.docx.claims_intro", lang), ""]
    L += [f"- {clean(c, lang, 160)}" for c in docx.get("claims", [])]
    L += ["", t("perf.s5.docx.no_toman", lang), "",
          img("perf.s5.chart_ecosystem_alt", "ecosystem_map", lang), ""]
    return L


# --------------------------------------------------------------- section 6
def sec6(tl, summerschool, lang):
    mech = tl["mechanics"]
    est = tl["event_start_times"]
    hh = tl["hour_histogram"]
    heat = tl["weekday_hour_heat"]
    L = ["## " + t("perf.s6.h_title", lang), "",
         t("perf.s6.intro", lang, n=f"{len(mech)}",
           n_fixed=f"{sum(1 for m in mech if m['kind'] == 'fixed-slot')}",
           n_peak=f"{sum(1 for m in mech if m['kind'] == 'peak')}",
           n_tx=f"{sum(1 for m in mech if m['kind'] == 'tx-hour')}"), "",
         "### " + t("perf.s6.fixed.h_title", lang), ""]
    DEADLINE = {"00:00", "23:59"}
    rows = []
    for m in sorted((x for x in mech if x["kind"] == "fixed-slot"),
                    key=lambda x: -x["n"]):
        s = est[m["category"]]
        dl = [x for x in s["times"] if x in DEADLINE]
        rows.append([f"`{m['category']}`", s["mode"], str(s["n"]),
                     str(len(s["times"])),
                     f"{len(dl)} ({', '.join(dl)})" if dl else "0"])
    L += _table([t(k, lang) for k in ("perf.s6.fixed.h_thread", "perf.s6.fixed.h_mode",
                                       "perf.s6.fixed.h_mentions",
                                       "perf.s6.fixed.h_distinct",
                                       "perf.s6.fixed.h_deadline")], rows)
    L += ["",
          t("perf.s6.fixed.caveat", lang), "",
          "### " + t("perf.s6.peaks.h_title", lang), ""]
    order = {w.replace("‌", ""): i for i, w in enumerate(WD_ORDER)}
    peaks = sorted((m for m in mech if m["kind"] == "peak"),
                   key=lambda m: (m["category"], order.get(m["jalali_weekday"]
                                                           .replace("‌", ""), 9)))
    L += _table([t(k, lang) for k in ("perf.s6.peaks.h_chat", "perf.s6.peaks.h_weekday",
                                       "perf.s6.peaks.h_hour", "perf.s6.peaks.h_messages")],
                [[term("chat", m["category"], lang), m["jalali_weekday"],
                  f"{m['hour']:02d}:00", str(m["n"])] for m in peaks])
    L += ["",
          "### " + t("perf.s6.tx.h_title", lang), ""]
    L += _table([t("perf.s6.tx.h_hour", lang), t("perf.s6.tx.h_messages", lang)],
                [[f"{m['hour']:02d}:00", str(m["n"])]
                 for m in sorted((x for x in mech if x["kind"] == "tx-hour"),
                                 key=lambda x: x["hour"])])
    L += ["",
          t("perf.s6.tx.note", lang), "",
          "### " + t("perf.s6.night.h_title", lang), "",
          t("perf.s6.night.para", lang,
            priv23=f"{hh['private_group']['23']:,}",
            pub0=f"{hh['public_group']['0']:,}",
            pub23=f"{hh['public_group']['23']:,}",
            priv_pct=pct(sum(hh['private_group'].get(str(h), 0) for h in (22, 23, 0, 1)),
                         sum(hh['private_group'].values())),
            pub_pct=pct(sum(hh['public_group'].get(str(h), 0) for h in (22, 23, 0, 1)),
                        sum(hh['public_group'].values()))), "",
          "### " + t("perf.s6.ss.h_title", lang), ""]
    ss_n = summerschool["n_messages"]
    ev18 = next(x for x in summerschool["time_patterns"]
                if x["kind"] == "event-hour" and x["hour"] == 18)
    sat = next(x for x in summerschool["time_patterns"]
               if x["kind"] == "weekday-slot"
               and x["jalali_weekday"] == "شنبه")
    kw = next((k for th in summerschool["candidate_threads"]
               for k in th["keywords"] if "18:00" in k), None)
    L += [t("perf.s6.ss.para", lang, n=f"{ss_n}", kw=f"{kw}", n_ev=f"{ev18['n']}",
            n_sat=f"{sat['n']}"), "",
          img("perf.s6.chart_heat_alt", "weekday_hour_heat", lang),
          img("perf.s6.chart_hist_alt", "hour_histogram", lang), ""]
    return L


# --------------------------------------------------------------- section 7
def sec7(stats, w_rows, tl, lang):
    iw = stats["in_window"]
    n = iw["total"]
    by_m = iw["by_method"]
    l2 = by_m["lexicon"] + by_m["rule"]
    l2_rows = [r for r in w_rows if r["in_window"] and not r["is_service"]
               and r["method"] in ("lexicon", "rule")]
    topical = sum(1 for r in l2_rows
                  if any(c not in CHATTER for c in r["categories"]))
    chatter_only = l2 - topical
    n_labels = Counter(len(r["categories"]) for r in w_rows)
    multi = sum(v for k, v in n_labels.items() if k > 1)
    unl = stats["by_method"]["unclassified"]
    noise_all = stats["by_category"]["meta_noise"]
    n_lex = sum(len(v) for v in
                read_json(ROOT / "analysis/lexicon.json").values())
    decisions = sum(1 for r in w_rows if r.get("is_decision"))
    aff = sum(1 for r in w_rows if r.get("event_ref"))
    affiliated = sum(th["n_messages"] for th in tl["threads"]
                     if not th.get("money_only"))
    fb = affiliated - aff  # keyword-fallback memberships
    no_text = sum(1 for r in w_rows
                  if not (r.get("text_plain") or "").strip()
                  and not r.get("media_kinds"))
    voice_only = sum(1 for r in w_rows
                     if not (r.get("text_plain") or "").strip()
                     and r.get("media_kinds") == ["voice"])
    llm_short = sum(1 for r in w_rows if r.get("method") == "llm"
                    and len((r.get("text_plain") or "").strip()) <= 15)
    n_corpus_lab = fmt(sum(stats['by_category'].values()))
    L = ["## " + t("perf.s7.h_title", lang), "",
         t("perf.s7.intro", lang, total=f"{stats['total']:,}", n=f"{n:,}"), ""]
    L += _table([t(k, lang) for k in ("perf.s7.tbl.h_layer", "perf.s7.tbl.h_method",
                                       "perf.s7.tbl.h_messages", "perf.s7.tbl.h_share")],
                [["1", t("perf.s7.tbl.rule", lang), fmt(by_m["rule"]),
                  pct(by_m["rule"], n)],
                 ["2", t("perf.s7.tbl.lexicon", lang, n=f"{n_lex}"), fmt(by_m["lexicon"]),
                  pct(by_m["lexicon"], n)],
                 ["3", t("perf.s7.tbl.llm", lang), fmt(by_m["llm"]),
                  pct(by_m["llm"], n)],
                 ["", f"**{t('perf.s7.tbl.total', lang)}**", f"**{fmt(iw['classified'])}**",
                  f"**{pct(iw['classified'], n)}**"]])
    L += ["",
          t("perf.s7.layer2", lang, raw_pct=pct2(l2, n), top_pct=pct2(topical, n),
            l2=fmt(l2), n=fmt(n), topical=fmt(topical), chatter=fmt(chatter_only),
            no_text=f"{no_text}", voice=f"{voice_only}", short=fmt(llm_short)),
          "",
          t("perf.s7.final", lang, cls_pct=pct2(iw['classified'], n),
            llm=fmt(by_m['llm']), unlabeled=fmt(n - iw['classified']),
            unl=f"{unl:,}", decisions=f"{decisions}"),
          "",
          t("perf.s7.event_ref", lang, aff=f"{aff:,}", fb=f"{fb:,}",
            affiliated=f"{affiliated:,}"),
          "",
          t("perf.s7.further", lang, noise=fmt(noise_all), corpus=n_corpus_lab,
            multi=fmt(multi), n=fmt(n), total=f"{stats['total']:,}"), ""]
    return L


# ------------------------------------------------------------------- build
def render(lang="en"):
    tl = read_json(ROOT / "analysis/timeline.json")
    eco = read_json(ROOT / "analysis/ecosystem.json")
    stats = read_json(ROOT / "analysis/classification_stats.json")
    registry = read_json(ROOT / "analysis/threads.json")
    ledger = read_json(ROOT / "analysis/profiles/ledger.json")
    docx = read_json(ROOT / "analysis/profiles/docx.json")
    summerschool = read_json(ROOT / "analysis/profiles/summerschool_channel.json")
    channel_profile = read_json(ROOT / "analysis/profiles/channel.json")
    rows = [json.loads(l) for l in
            open(ROOT / "analysis/classified.jsonl", encoding="utf-8")]
    w_rows = [r for r in rows if r["in_window"] and not r["is_service"]]
    assert len(w_rows) == stats["in_window"]["total"], "window mismatch"

    L = ["# " + t("perf.title", lang),
         "",
         t("perf.intro", lang, j0=jdate('2025-05-28T00:00:00'),
           j1=jdate('2026-10-14T00:00:00'), n_threads=f"{len(tl['threads'])}",
           n_months=f"{len(tl['monthly_activity'])}", n_mech=f"{len(tl['mechanics'])}",
           n_nodes=f"{len(eco['nodes'])}", n_edges=f"{len(eco['edges'])}",
           n_rows=f"{len(rows):,}", n_win=f"{len(w_rows):,}"), ""]
    L += sec1(tl, stats, w_rows, lang)
    L += sec2(tl, w_rows, lang)
    L += sec3(tl, w_rows, lang)
    L += sec4(tl, w_rows, registry, ledger, lang)
    L += sec5(eco, docx, channel_profile, lang)
    L += sec6(tl, summerschool, lang)
    L += sec7(stats, w_rows, tl, lang)

    text = "\n".join(L)
    assert "(auto:" not in text, "placeholder text leaked into the report"
    chart_dir = "charts" if lang == "en" else "charts_fa"
    for c in CHARTS:
        assert f"{chart_dir}/{c}.png" in text, f"chart {c} not embedded"
    if lang == "fa":
        text = i18n.localize(text)
    return text + "\n"


def build(lang="en"):
    out = OUT if lang == "en" else OUT_FA
    chart_dir = "charts" if lang == "en" else "charts_fa"
    for c in CHARTS:
        assert (out.parent / chart_dir / f"{c}.png").exists(), f"missing {chart_dir}/{c}"
    text = render(lang)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    pdf = out.with_suffix(".pdf")
    from pypdf import PdfReader
    if lang == "en":
        md_to_pdf(out, pdf,
                  footer="ANJOMAN | Performance & activity report | 2026-10-14",
                  title="Anjoman performance & activity report")

        # render gate: pages > 6 and known spot strings extractable
        reader = PdfReader(str(pdf))
        pages = len(reader.pages)
        pdftext = "".join(p.extract_text() or "" for p in reader.pages)
        assert pages > 6, f"PDF too short: {pages} pages"
        for spot in ("726,527", "13:30", "2,694,750"):
            assert spot in pdftext, f"spot string {spot!r} missing from PDF"
    else:
        md_to_pdf_rtl(out, pdf,
                      title="گزارش عملکرد و فعالیت انجمن علمی فیزیک",
                      footer="انجمن علمی فیزیک | گزارش عملکرد و فعالیت | ۱۴۰۵/۰۷/۲۲")
        # pypdf extracts RTL runs in visual order, so FA spot strings are
        # checked in the sibling .html; the page count still comes from the PDF
        pages = len(PdfReader(str(pdf)).pages)
        assert pages > 6, f"PDF too short: {pages} pages"
        html = out.with_suffix(".html").read_text(encoding="utf-8")
        for spot in ("۷۲۶٬۵۲۷", "۱۳:۳۰", "۲٬۶۹۴٬۷۵۰"):
            assert spot in html, f"FA spot string {spot} missing"
    print(f"[report] {out.name}: {len(text.splitlines())} md lines, "
          f"PDF {pages} pages, spot strings OK")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("en", "fa"), default="en")
    print(build(ap.parse_args().lang))
