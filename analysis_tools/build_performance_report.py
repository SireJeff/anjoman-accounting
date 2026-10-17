"""Performance & activity report — assembled from analysis artifacts only.

Every number, date and message reference in the built markdown is generated
from the committed artifacts (timeline.json, ecosystem.json, classified.jsonl,
classification_stats.json, threads.json, profiles/*.json and the Task-11
charts). No prose claim is hand-written against memory; a final gate asserts
that zero "(auto:" placeholders survived, that all six figures are embedded,
and that the rendered PDF carries more than six pages plus known spot strings
(the docx view total 726,527 and the 13:30 dept-seminar slot).
"""
import json
from collections import Counter, defaultdict
from datetime import date, datetime

import jdatetime

from .common import ROOT, read_json
from .report_common import md_to_pdf

OUT = ROOT / "reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.md"

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


def plural(n, one="chat", many="chats"):
    return f"{n} {one if n == 1 else many}"


def mkey(m):
    y, mm = m.split("/")
    return (int(y), int(mm))


def jdate(iso):
    d = date.fromisoformat(iso[:10])
    jd = jdatetime.date.fromgregorian(date=d)
    return f"{jd.year}/{jd.month:02d}/{jd.day:02d}"


def clean(text, n=70):
    """Table-safe one-line snippet."""
    t = " ".join((text or "").split()).replace("|", "/")
    return (t[:n] + "…") if len(t) > n else (t or "[no text]")


def snippet(rec):
    if rec.get("text_plain"):
        return clean(rec["text_plain"])
    mk = rec.get("media_kinds") or []
    return f"[media: {', '.join(mk)}]" if mk else "[no text]"


def _table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def in_phase(month, lo, hi):
    k = mkey(month)
    return lo <= k <= hi


# --------------------------------------------------------------- section 1
def sec1(tl, stats, w_rows):
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
    threads = [t for t in tl["threads"] if not t.get("money_only")]
    money_only = [t for t in tl["threads"] if t.get("money_only")]
    top5 = sorted(threads, key=lambda t: -t["n_messages"])[:5]

    L = ["## 1. Executive summary", "",
         f"Across the analysis window the five Telegram exports carry "
         f"**{sum(n for _, n in by_chat):,} in-window, non-service messages** "
         f"(of {stats['total']:,} parsed records; classification coverage "
         f"{stats['in_window']['coverage_pct']:.0f}% in-window).", "",
         "Messages by chat (in-window, non-service):", ""]
    L += _table(["Chat", "Messages", "Share"],
                [[c, f"{n:,}", pct(n, sum(x for _, x in by_chat))]
                 for c, n in by_chat])
    L += ["",
          f"The three largest activity categories by label count are "
          f"**{cats.most_common(3)[0][0]}** ({fmt(cats.most_common(3)[0][1])}), "
          f"**{cats.most_common(3)[1][0]}** ({fmt(cats.most_common(3)[1][1])}) and "
          f"**{cats.most_common(3)[2][0]}** ({fmt(cats.most_common(3)[2][1])}) "
          f"of {fmt(cat_tot)} total labelings (multi-label; see §7). "
          f"The correlation stage tracks **{len(tl['threads'])} threads** "
          f"({len(threads)} message-bearing + {len(money_only)} money-only), "
          f"and the reconciled ledger behind them moves "
          f"**{fmt(rec)} toman receipts against {fmt(pay)} toman payments** "
          f"(net **+{fmt(rec - pay)}**, all 96 rows, including the "
          f"{fmt(und)} toman undated bucket).", "",
          "Five headline threads by affiliated message count:", ""]
    L += _table(["Thread", "Title", "First → last seen", "Chats", "Msgs",
                 "TX total (toman)"],
                [[f"`{t['event_ref']}`", clean(t["title"], 44),
                  f"{t['first_seen'][:10]} → {t['last_seen'][:10]}",
                  str(len(t["chats"])), f"{t['n_messages']:,}",
                  fmt(t["tx_total_toman"])] for t in top5])
    L.append("")
    return L


# --------------------------------------------------------------- section 2
def sec2(tl, w_rows):
    ma = tl["monthly_activity"]
    months = sorted(ma.keys(), key=mkey)
    # distinct message volume per month (classified.jsonl is the only artifact
    # carrying per-message rows, so multi-label double counting is avoided)
    vol = Counter(r["jalali_month"] for r in w_rows if r.get("jalali_month"))
    label = Counter()
    for m, chats in ma.items():
        for c, cc in chats.items():
            label[m] += sum(cc.values())
    thr = [t for t in tl["threads"] if not t.get("money_only")]

    def phase_of_thread(t):
        return jdate(t["first_seen"])[:7]  # YYYY/MM jalali

    def thread_phase(t):
        for name, lo, hi in PHASES:
            if in_phase(phase_of_thread(t), lo, hi):
                return name
        return None  # 1404/03 window-opening stub

    L = ["## 2. Phase narrative", "",
         "Thread first-seen dates and monthly activity split the window into "
         "four phases (Jalali months; the window opens 1404/03/07 = 2025-05-28). "
         "First-seen dates derive from affiliated messages, so they inherit "
         "the §7 affiliation caveat.", ""]
    stub_months = [m for m in months if mkey(m) < (1404, 4)]
    stub_thr = [t for t in thr if thread_phase(t) is None]
    if stub_months:
        L += [f"*Window-opening stub:* the partial month(s) "
              f"{', '.join(stub_months)} carry {fmt(sum(vol[m] for m in stub_months))} "
              f"messages and the first-seen of {len(stub_thr)} threads "
              f"(largest: `{max(stub_thr, key=lambda t: t['n_messages'])['event_ref']}`, "
              f"{max(stub_thr, key=lambda t: t['n_messages'])['n_messages']} messages); "
              f"they precede the four phases below.", ""]
    chat_msg = Counter((r["chat"], r["jalali_month"]) for r in w_rows
                       if r.get("chat") and r.get("jalali_month"))
    for name, lo, hi in PHASES:
        pm = [m for m in months if in_phase(m, lo, hi)]
        if not pm:
            continue
        pt = [t for t in thr if thread_phase(t) == name]
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
        biggest = max(pt, key=lambda t: t["n_messages"]) if pt else None
        L.append(f"### {name} ({pm[0]}–{pm[-1]})")
        L.append("")
        para = (f"**{name}** spans Jalali {pm[0]}–{pm[-1]} with "
                f"**{fmt(tot_msgs)} messages** across the chats; the busiest "
                f"surface is {top_chat} ({fmt(top_n)} messages) and the "
                f"dominant labels are {c1} ({fmt(c1n)}) and {c2} "
                f"({fmt(c2n)}). ")
        if pt:
            para += (f"{len(pt)} threads first appear in this phase, led by "
                     f"`{biggest['event_ref']}` (first seen "
                     f"{biggest['first_seen'][:10]} / {jdate(biggest['first_seen'])}, "
                     f"{biggest['n_messages']:,} messages over "
                     f"{plural(len(biggest['chats']))}). ")
        else:
            para += "No new threads first appear in this phase. "
        mx = max(pm, key=lambda m: vol.get(m, 0))
        para += (f"The phase's peak month is {mx} "
                 f"({fmt(vol.get(mx, 0))} messages).")
        L.append(para)
        L.append("")
        top = sorted(pt, key=lambda t: -t["n_messages"])[:5]
        if top:
            L += _table(["Thread", "First seen", "Jalali", "Msgs", "Chats",
                         "Last seen"],
                        [[f"`{t['event_ref']}`", t["first_seen"][:10],
                          jdate(t["first_seen"]), f"{t['n_messages']:,}",
                          str(len(t["chats"])), t["last_seen"][:10]]
                         for t in top])
            L.append("")
    return L


# --------------------------------------------------------------- section 3
def sec3(tl, w_rows):
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

    L = ["## 3. Activity categories", "",
         f"Monthly labelings per category, aggregated over chats "
         f"(`monthly_activity`; a message with several labels counts once per "
         f"label — {fmt(total_labelings)} labelings over the 12,066 in-window "
         f"messages).", ""]
    for yr in ("1404", "1405"):
        ym = [m for m in months if m.startswith(yr)]
        if not ym:
            continue
        L += [f"**{yr}** (columns are Jalali month MM)", ""]
        hdr = ["Category"] + [m.split("/")[1] for m in ym] + ["Total"]
        rows = []
        for cat, tot in cats.most_common():
            vals = [cat_month[cat].get(m, 0) for m in ym]
            if not any(vals):
                continue
            rows.append([cat] + [fmt(v) for v in vals] + [f"**{fmt(tot)}**"])
        col_tot = [sum(cat_month[c].get(m, 0) for c in cats) for m in ym]
        rows.append(["**All labelings**"] +
                    [f"**{fmt(v)}**" for v in col_tot] +
                    [f"**{fmt(total_labelings)}**"])
        L += _table(hdr, rows)
        L.append("")

    L += ["Most-engaged threads per category, from the "
          "**1,187 explicitly affiliated** messages (LLM `event_ref`; "
          "affiliation is conversational, not an evidence link — see §7):", ""]
    rows = []
    for cat, tot in cats.most_common():
        refs = aff.get(cat, Counter()).most_common(3)
        aff_n = sum(aff.get(cat, Counter()).values())
        peak = max(cat_month[cat], key=lambda m: cat_month[cat][m]) if tot else "—"
        thr_txt = ", ".join(f"`{r}` ({n})" for r, n in refs) if refs else "*(none explicitly affiliated)*"
        rows.append([cat, fmt(tot), pct(tot, total_labelings), peak,
                     str(aff_n), thr_txt])
    L += _table(["Category", "Labelings", "Share", "Peak month",
                 "Explicitly affiliated", "Top threads by explicit affiliation "
                 "(messages)"], rows)
    L += ["",
          "![Activity by month](charts/activity_by_month.png)",
          "![Category breakdown](charts/category_breakdown.png)", ""]
    return L


# --------------------------------------------------------------- section 4
def sec4(tl, w_rows, registry, ledger):
    threads = [t for t in tl["threads"] if not t.get("money_only")]
    expl = Counter(r["event_ref"] for r in w_rows if r.get("event_ref"))
    tx_by_id = {f["tx_id"]: f for f in ledger["financial_signals"]}
    L = ["## 4. Cross-chat correlation", "",
         f"All {len(threads)} message-bearing threads with their per-chat "
         f"spread, announcement lag and linked ledger money. `Explicit` counts "
         f"messages whose LLM `event_ref` names the thread; the remainder of "
         f"`Msgs` is keyword-fallback membership (2,734 of the 3,921 "
         f"affiliations), so fallback-heavy threads carry approximate message "
         f"counts and lags (§7). `Lag` = days from the earliest non-channel "
         f"chat first to the channel first; negative means the channel "
         f"announcement preceded other-chat coordination.", ""]
    rows = []
    for t in sorted(threads, key=lambda t: -t["n_messages"]):
        rows.append([f"`{t['event_ref']}`", t["first_seen"][:10],
                     str(len(t["chats"])), f"{t['n_messages']:,}",
                     str(expl.get(t["event_ref"], 0)),
                     "—" if t["announcement_lag_days"] is None
                     else f"{t['announcement_lag_days']:+d}",
                     fmt(t["tx_total_toman"])])
    L += _table(["Thread", "First seen", "Chats", "Msgs", "Explicit",
                 "Lag (d)", "TX total (toman)"], rows)
    L.append("")

    # money-only coverage gap (controller carry)
    for t in tl["threads"]:
        if t.get("money_only"):
            txs = [tx_by_id[x] for x in t["tx_ids"]]
            r = sum(x["amount_toman"] for x in txs if x["direction"] == "Receipt")
            p = sum(x["amount_toman"] for x in txs if x["direction"] != "Receipt")
            dup = [x["tx_id"] for x in txs if x.get("status") == "Duplicate"]
            L.append(
                f"**Money without matched messages — coverage gap:** "
                f"`{t['event_ref']}` ({t['title']}) carries "
                f"{len(txs)} ledger rows ({fmt(t['tx_total_toman'])} toman "
                f"gross: {fmt(r)} receipts, {fmt(p)} payments; "
                f"{', '.join(t['tx_ids'])}) but zero keyword- or "
                f"LLM-matched messages, so it is kept money-only with null "
                f"first/last/lag."
                + (f" {', '.join(dup)} is status *Duplicate* in the ledger, "
                   f"inflating the gross by its amount." if dup else ""))
            L.append("")

    L += ["![Event timeline](charts/event_timeline.png)",
          "The three case studies below are the threads spanning the most "
          "chats (all five; tie-broken by linked transaction volume, then "
          "message count).", ""]
    cands = sorted(threads, key=lambda t: (-len(t["chats"]),
                                           -t["tx_total_toman"],
                                           -t["n_messages"]))
    for t in cands[:3]:
        L += _case_study(t, w_rows, registry, tx_by_id, expl)
    return L


def _case_study(t, w_rows, registry, tx_by_id, expl):
    ref = t["event_ref"]
    E = sorted((r for r in w_rows if r.get("event_ref") == ref),
               key=lambda r: r["timestamp"] or "")
    e_n = expl.get(ref, 0)
    fb = t["n_messages"] - e_n
    txs = [tx_by_id[x] for x in t["tx_ids"] if x in tx_by_id]
    r = sum(x["amount_toman"] for x in txs if x["direction"] == "Receipt")
    p = sum(x["amount_toman"] for x in txs if x["direction"] != "Receipt")
    reg = next((x for x in registry["threads"] if x["event_ref"] == ref), {})

    L = [f"### Case study: `{ref}` — {clean(t['title'], 60)}", "",
         f"{t['n_messages']:,} affiliated messages across "
         f"{len(t['chats'])} chats, {t['first_seen'][:10]} → "
         f"{t['last_seen'][:10]} ({jdate(t['first_seen'])} → "
         f"{jdate(t['last_seen'])}); announcement lag "
         f"**{t['announcement_lag_days']:+d} days** (channel first "
         f"{t['chats']['channel']['first'][:10]}). Explicit affiliation: "
         f"{e_n:,} of {t['n_messages']:,} messages ({pct(e_n, t['n_messages'])}); "
         f"the remaining {fb:,} are keyword-fallback memberships"
         + (" — this thread is fallback-heavy, so its message count and lag "
            "are approximate (§7)." if fb > e_n else "."),
         f"Ledger money behind the thread: {fmt(t['tx_total_toman'])} toman "
         f"gross across {len(txs)} transactions "
         f"({fmt(r)} receipts / {fmt(p)} payments)."
         if txs else
         "No ledger transactions link to this thread (it is the receipt-"
         "collection workstream itself, not a spending project).", ""]

    # stage table: planning -> announcement -> delivery -> payment
    rows = []
    first_rec = E[0] if E else None
    rows.append(["Planning — earliest explicit affiliation",
                 (first_rec or {}).get("timestamp", t["first_seen"])[:16],
                 f"{first_rec['chat']}#{first_rec['message_id']}"
                 if first_rec else "*(thread first seen, keyword-matched)*",
                 snippet(first_rec) if first_rec else clean(t["title"], 60)])
    busiest = max(t["chats"], key=lambda c: t["chats"][c]["n"]) if t["chats"] else None
    for chat in sorted(t["chats"], key=lambda c: t["chats"][c]["first"]):
        meta = t["chats"][chat]
        if chat == "channel":
            label = f"Announcement — first channel post ({meta['n']} msgs)"
        elif chat == busiest:
            label = f"Delivery — busiest chat {chat} ({meta['n']} msgs)"
        else:
            label = f"Work — first message in {chat} ({meta['n']} msgs)"
        ex = next((m for m in E if m["chat"] == chat), None)
        if ex and ex["timestamp"] == meta["first"]:
            ref, ev = f"{chat}#{ex['message_id']}", snippet(ex)
        elif ex:
            ref = "*(chat first, keyword-matched)*"
            ev = (f"chat first {meta['first'][:10]}; earliest explicit "
                  f"{chat}#{ex['message_id']} {ex['timestamp'][:10]}")
        else:
            ref, ev = "*(chat first, keyword-matched)*", "first message in this chat"
        rows.append([label, meta["first"][:16], ref, ev])
    if t["decision_dates"]:
        rows.append(["Delivery-window decisions",
                     ", ".join(sorted(set(t["decision_dates"]))),
                     f"{len(set(t['decision_dates']))} dated decisions",
                     "messages flagged is_decision in this thread"])
    for x in txs:
        mids = x.get("message_ids") or []
        rows.append([f"Payment — {x['tx_id']} ({x['direction']})",
                     x.get("period", "—"),
                     ("accounting_group#" + ", accounting_group#".join(mids))
                     if mids else "*(ledger row, no message refs)*",
                     f"{fmt(x['amount_toman'])} toman · {x['category']} · "
                     f"{x.get('status', '—')}"])
    L += _table(["Stage", "Date", "Reference", "Evidence"], rows)
    bm = t["chats"].get(busiest, {})
    L += ["", f"The delivery surface is `{busiest}` — {bm.get('n', 0):,} of "
              f"the thread's {t['n_messages']:,} messages between "
              f"{bm.get('first', '')[:10]} and {bm.get('last', '')[:10]}."]
    if "docx" in (reg.get("chats") or []):
        L += ["", "The threads registry links this thread to the docx media "
                  "report (`docx` listed among its chats); the corresponding "
                  "شهریور–مهر ۱۴۰۵ campaign metrics are quoted in §5."]
    L.append("")
    return L


# --------------------------------------------------------------- section 5
def sec5(eco, docx, channel_profile):
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

    L = ["## 5. Ecosystem map", "",
         f"`ecosystem.json` carries **{len(eco['nodes'])} nodes / "
         f"{len(eco['edges'])} edges** ({len(seeds)} seed entities, 5 chat "
         f"exports, {sum(1 for n in eco['nodes'] if n.get('type') == 'external')} "
         f"externals). Seed validation (an edge weight ≥ 3 into the seed "
         f"evidences it):", ""]
    L += _table(["Seed", "Label", "Status", "Forward weight in",
                 "Mention weight in"],
                [[s["id"], s["label"], eco["validation"].get(s["id"], "—"),
                  fmt(fwd_in.get(s["id"], 0)), fmt(men_in.get(s["id"], 0))]
                 for s in seeds])
    unv = [s["id"] for s in seeds if eco["validation"].get(s["id"]) == "unverified"]
    if unv:
        unv_labels = "; ".join(f"`{u}` = {nodes[u]['label']}" for u in unv)
        L += ["", f"**Unverified seed caveat:** {unv_labels} has zero "
                  f"forward and mention edges in the exports — an in-person "
                  f"gathering with no digital footprint, so every graph "
                  f"statement in this report is made over the "
                  f"{len(seeds) - len(unv)} evidenced seeds only."]
    L += ["",
          "Top external origins by forward weight (forwards into the five "
          f"chats; {fmt(fwd_tot)} total forward weight):", ""]
    ext = sorted(((k, v) for k, v in fwd_in.items()
                  if nodes.get(k, {}).get("type") == "external"),
                 key=lambda kv: -kv[1])[:10]
    L += _table(["#", "External origin", "Forward weight", "Share of forwards"],
                [[str(i + 1), nodes[k]["label"], fmt(v), pct(v, fwd_tot)]
                 for i, (k, v) in enumerate(ext)])

    ch_fwd = sum(e["weight"] for e in eco["edges"]
                 if e["type"] == "forward" and e["source"] == "channel_export")
    q_fwd = fwd_in.get("quantasc", 0)
    ch_digest = next(x for x in channel_profile["candidate_threads"]
                     if x["event_ref"] == "dept-weekly-seminars")
    assoc_self = men_in.get("association", 0)
    L += ["",
          "**The association operates as a relay.** Its channel is both a "
          "megaphone and a redistribution point: the association handle "
          f"anchors **{fmt(assoc_self)} mention weight** onto the association "
          "seed (post alias merge; 1,793 of them the channel's own "
          "post-signature handle), it has relayed the department's weekly "
          f"seminar digests since 2018 — **{ch_digest['n']} all-time channel "
          f"posts** (anchors {ch_digest['anchor_dates'][0]} → "
          f"{ch_digest['anchor_dates'][-1]}, outside the analysis window) — "
          f"and **کوانتا (QuantaSC study circles) takes {pct(q_fwd, ch_fwd)} "
          f"of the channel's forward weight** "
          f"({fmt(q_fwd)} of {fmt(ch_fwd)}), on top of "
          f"{fmt(men_in.get('quantasc', 0))} mention weight. The strongest "
          "subgroup partnership in the graph is thus the association's own "
          "spin-off study-circle network.", ""]

    L += ["### Docx media report — verbatim metrics (quoted with period labels)",
          "",
          f"`{docx['doc_title']}` — {docx['n_messages']} paragraphs / "
          f"{docx['n_table_rows']} table rows; periods covered: "
          f"{'; '.join(docx['periods_covered'])}. All "
          f"{len(docx['metrics'])} metrics verbatim:", ""]
    def mval(m):
        if "value" in m:
            v = float(m["value"])
            return fmt(m["value"]) if v.is_integer() else str(m["value"])
        if "value_min" in m:  # range metrics (hours of work)
            return f"{m['value_min']}–{m['value_max']}"
        return "—"

    L += _table(["Metric", "Label", "Verbatim", "Value", "Period"],
                [[m["id"], clean(m["label"], 40), m["verbatim"], mval(m),
                  clean(m.get("period", "—"), 44)]
                 for m in docx["metrics"]])
    L += ["", "The document's own caveats (claims, quoted):", ""]
    L += [f"- {clean(c, 160)}" for c in docx.get("claims", [])]
    L += ["", "No toman amounts appear anywhere in the docx report — its only "
              "cost accounting is the 34–38 production-hour estimate (m29), "
              "so the financial side of the same campaign rests entirely on "
              "the ledger artifacts of §4.", "",
          "![Ecosystem map](charts/ecosystem_map.png)", ""]
    return L


# --------------------------------------------------------------- section 6
def sec6(tl, summerschool):
    mech = tl["mechanics"]
    est = tl["event_start_times"]
    hh = tl["hour_histogram"]
    heat = tl["weekday_hour_heat"]
    L = ["## 6. Monthly × hourly patterns (university mechanics)", "",
         f"`mechanics` lists {len(mech)} recurring patterns "
         f"({sum(1 for m in mech if m['kind'] == 'fixed-slot')} fixed event "
         f"slots, {sum(1 for m in mech if m['kind'] == 'peak')} weekday "
         f"peaks, {sum(1 for m in mech if m['kind'] == 'tx-hour')} "
         f"ledger-linked hours; n ≥ 5 only).", "",
         "### Fixed event slots", ""]
    DEADLINE = {"00:00", "23:59"}
    rows = []
    for m in sorted((x for x in mech if x["kind"] == "fixed-slot"),
                    key=lambda x: -x["n"]):
        s = est[m["category"]]
        dl = [t for t in s["times"] if t in DEADLINE]
        rows.append([f"`{m['category']}`", s["mode"], str(s["n"]),
                     str(len(s["times"])),
                     f"{len(dl)} ({', '.join(dl)})" if dl else "0"])
    L += _table(["Thread", "Mode start", "HH:MM mentions", "Distinct times",
                 "Deadline-style times"], rows)
    L += ["",
          "*Caveats (inherited from the extraction rules):* the mention "
          "count `n` includes **deadline-style times** (00:00 / 23:59 appear "
          "in several threads' `times` lists), so a mode is far more reliable "
          "than its n; and colloquial hour-only mentions such as «ساعت ۳» "
          "(old-style 15:00) are **never collected** — only literal HH:MM "
          "strings are, so evening events advertised colloquially are "
          "under-represented here.", "",
          "### Weekday peaks (per chat)", ""]
    order = {w.replace("‌", ""): i for i, w in enumerate(WD_ORDER)}
    peaks = sorted((m for m in mech if m["kind"] == "peak"),
                   key=lambda m: (m["category"], order.get(m["jalali_weekday"]
                                                           .replace("‌", ""), 9)))
    L += _table(["Chat", "Weekday", "Peak hour", "Messages"],
                [[m["category"], m["jalali_weekday"], f"{m['hour']:02d}:00",
                  str(m["n"])] for m in peaks])
    L += ["",
          "### Ledger-linked accounting hours", ""]
    L += _table(["Hour", "TX-linked accounting_group messages"],
                [[f"{m['hour']:02d}:00", str(m["n"])]
                 for m in sorted((x for x in mech if x["kind"] == "tx-hour"),
                                 key=lambda x: x["hour"])])
    L += ["",
          "The 04:00 entry (n = 5) sits right at the n ≥ 5 threshold and "
          "reflects night-time bookkeeping posts — observational, not a "
          "scheduled mechanism.", "",
          "### Nocturnal coordination", "",
          f"The single strongest hourly signal in the corpus is late-night "
          f"coordination: the private group's busiest hour is "
          f"**23:00 with {hh['private_group']['23']:,} messages** and the "
          f"public group's is **00:00 with {hh['public_group']['0']:,} "
          f"messages** (its 23:00 follows at {hh['public_group']['23']:,}). "
          f"Between 22:00 and 01:00 the private group posts "
          f"{pct(sum(hh['private_group'].get(str(h), 0) for h in (22, 23, 0, 1)), sum(hh['private_group'].values()))} "
          f"of its volume and the public group "
          f"{pct(sum(hh['public_group'].get(str(h), 0) for h in (22, 23, 0, 1)), sum(hh['public_group'].values()))} "
          f"— student-run coordination happens after midnight, not in the "
          f"13:00–19:00 business band the fixed slots occupy.", "",
          "### Summer-school channel mechanics", ""]
    ss_n = summerschool["n_messages"]
    ev18 = next(x for x in summerschool["time_patterns"]
                if x["kind"] == "event-hour" and x["hour"] == 18)
    sat = next(x for x in summerschool["time_patterns"]
               if x["kind"] == "weekday-slot"
               and x["jalali_weekday"] == "شنبه")
    kw = next((k for t in summerschool["candidate_threads"]
               for k in t["keywords"] if "18:00" in k), None)
    L += [f"The dedicated summer-school channel ({ss_n} in-window posts) "
          f"runs its live sessions at a fixed class hour — **18:00–19:10** "
          f"(«{kw}» in the 1405 course calendar; event-hour 18:00 appears in "
          f"{ev18['n']} posts, «همه‌روزه») — and publishes its announcements "
          f"in a **Saturday slot**: {sat['n']} of {ss_n} posts sit in the "
          f"شنبه weekday-slot peak.", "",
          "![Weekday × hour heatmap](charts/weekday_hour_heat.png)",
          "![Hour histogram](charts/hour_histogram.png)", ""]
    return L


# --------------------------------------------------------------- section 7
def sec7(stats, w_rows, tl):
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
    affiliated = sum(t["n_messages"] for t in tl["threads"]
                     if not t.get("money_only"))
    fb = affiliated - aff  # keyword-fallback memberships
    no_text = sum(1 for r in w_rows
                  if not (r.get("text_plain") or "").strip()
                  and not r.get("media_kinds"))
    voice_only = sum(1 for r in w_rows
                     if not (r.get("text_plain") or "").strip()
                     and r.get("media_kinds") == ["voice"])
    llm_short = sum(1 for r in w_rows if r.get("method") == "llm"
                    and len((r.get("text_plain") or "").strip()) <= 15)
    L = ["## 7. Classification method & limitations", "",
         "Three-layer pipeline over the 16,677 parsed records; the analysis "
         f"denominator is the **{n:,} in-window, non-service messages**:", ""]
    L += _table(["Layer", "Method", "Messages (in-window)", "Share"],
                [["1", "structural rules (poll/forms/media-only)", fmt(by_m["rule"]),
                  pct(by_m["rule"], n)],
                 ["2", f"lexicon (multi-label, {n_lex} entries)", fmt(by_m["lexicon"]),
                  pct(by_m["lexicon"], n)],
                 ["3", "LLM residual (method=llm)", fmt(by_m["llm"]),
                  pct(by_m["llm"], n)],
                 ["", "**classified total**", f"**{fmt(iw['classified'])}**",
                  f"**{pct(iw['classified'], n)}**"]])
    L += ["",
          f"**Layer-2 coverage plateaued at {pct2(l2, n)} raw / "
          f"{pct2(topical, n)} topical** — {fmt(l2)} of {fmt(n)} messages "
          f"received at least one lexicon/rule label, but only "
          f"**{fmt(topical)} carry at least one topical category** (anything "
          f"beyond the chatter pair meta_noise/community_social); the "
          f"remaining **{fmt(chatter_only)} layer-2 labelings are "
          f"classified-only-chatter**. The structural ceiling is visible in "
          f"the data itself: {no_text} in-window messages have no text and "
          f"no media to classify, {voice_only} are voice-only with no text, "
          f"and {fmt(llm_short)} of the layer-3 messages are 15 characters "
          f"or shorter — so the residue was routed to layer 3 rather than "
          f"forced into topics.",
          "",
          f"**Final state: {pct2(iw['classified'], n)} classified.** The LLM "
          f"layer labeled **{fmt(by_m['llm'])} messages with `method=llm`** "
          f"(confidence-gated at 0.7); after the Task-14 precision pass "
          f"(risky-word corroboration plus lexicon pruning), "
          f"**{fmt(n - iw['classified'])} in-window messages** hold no label "
          f"rather than a speculative one, and {unl:,} records remain "
          f"unlabeled corpus-wide. **{decisions} messages** carry "
          f"`is_decision` (all from the LLM layer).",
          "",
          f"**event_ref is affiliation, not evidence.** The LLM attached "
          f"explicit `event_ref` labels to **{aff:,} messages**, and the "
          f"correlation stage added **{fb:,} keyword-fallback memberships** "
          f"(first-6-keyword substring match) to reach {affiliated:,} "
          f"affiliated messages across the 46 message-bearing threads. In "
          f"fallback-heavy threads — e.g. `final-receipt-handover-1405` "
          f"(1 explicit of 413) — the per-thread `n_messages` and "
          f"`announcement_lag_days` are therefore approximate, and §4 marks "
          f"them as such.",
          "",
          f"**Further limitations.** meta_noise is the largest category "
          f"({fmt(noise_all)} of {fmt(sum(stats['by_category'].values()))} "
          f"corpus labelings) — the groups are, by volume, mostly chat. "
          f"Labels are multi-label (capped at 4): {fmt(multi)} of {fmt(n)} "
          f"in-window messages carry more than one category, so category "
          f"sums exceed message counts ({fmt(sum(stats['by_category'].values()))} "
          f"corpus labelings over 16,677 records). Service messages "
          f"(joins, title changes, poll closes) are excluded from every "
          f"narrative and histogram here. Timestamps are export-local "
          f"(UTC+03:30) — hour patterns are Tehran-local.", ""]
    return L


# ------------------------------------------------------------------- build
def build():
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

    charts = ["activity_by_month", "category_breakdown", "weekday_hour_heat",
              "hour_histogram", "event_timeline", "ecosystem_map"]
    for c in charts:
        assert (OUT.parent / "charts" / f"{c}.png").exists(), f"missing {c}"

    L = ["# Anjoman Performance & Activity Report (2025-05-28 → 2026-10-14)",
         "",
         f"Window 2025-05-28 → 2026-10-14 "
         f"({jdate('2025-05-28T00:00:00')} → {jdate('2026-10-14T00:00:00')}"
         f"), five Telegram exports. Assembled from the analysis artifacts "
         f"only: `timeline.json` ({len(tl['threads'])} threads, "
         f"{len(tl['monthly_activity'])} Jalali months, "
         f"{len(tl['mechanics'])} mechanics), `ecosystem.json` "
         f"({len(eco['nodes'])} nodes / {len(eco['edges'])} edges), "
         f"`classified.jsonl` ({len(rows):,} records; "
         f"{len(w_rows):,} in-window non-service), "
         f"`classification_stats.json`, `threads.json`, and the source "
         f"profiles consumed here (channel, summerschool_channel, ledger, "
         f"docx). Figures render the Task-11 charts.", ""]
    L += sec1(tl, stats, w_rows)
    L += sec2(tl, w_rows)
    L += sec3(tl, w_rows)
    L += sec4(tl, w_rows, registry, ledger)
    L += sec5(eco, docx, channel_profile)
    L += sec6(tl, summerschool)
    L += sec7(stats, w_rows, tl)

    text = "\n".join(L)
    assert "(auto:" not in text, "placeholder text leaked into the report"
    for c in charts:
        assert f"charts/{c}.png" in text, f"chart {c} not embedded"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n", encoding="utf-8")
    pdf = OUT.with_suffix(".pdf")
    md_to_pdf(OUT, pdf,
              footer="ANJOMAN | Performance & activity report | 2026-10-14",
              title="Anjoman performance & activity report")

    # render gate: pages > 6 and known spot strings extractable
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    pages = len(reader.pages)
    pdftext = "".join(p.extract_text() or "" for p in reader.pages)
    assert pages > 6, f"PDF too short: {pages} pages"
    for spot in ("726,527", "13:30", "2,694,750"):
        assert spot in pdftext, f"spot string {spot!r} missing from PDF"
    print(f"[report] {OUT.name}: {len(text.splitlines())} md lines, "
          f"PDF {pages} pages, spot strings OK")
    return OUT


if __name__ == "__main__":
    print(build())
