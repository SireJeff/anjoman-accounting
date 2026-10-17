"""Stage 4a: event threads + cross-chat correlation + monthly/hourly analytics."""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from .common import ROOT, LEDGER_CSV, normalize_digits, read_json, write_json

# thread event_ref -> ledger project name (fallback when threads.json has no tx_ids)
PROJECT_FALLBACK = {"summer-school-1404": "Summer School 1404",
                    "summer-school-1405": "Summer School 1405",
                    "intro-event-1405": "Intro Event 1405",
                    "website-alenush": "Association website"}


def _load_tx():
    import pandas as pd
    df = pd.read_csv(LEDGER_CSV, encoding="utf-8-sig")
    df["amount_toman"] = pd.to_numeric(df["amount_toman"], errors="coerce").fillna(0)
    return df.to_dict("records")


def _group_thread_msgs(recs, threads):
    """Assign messages to threads: explicit event_ref always wins; keyword
    fallback (first 6 keywords) only applies to in-window non-service messages
    that carry no event_ref."""
    by_ref = {}
    for t in threads["threads"]:
        by_ref[t["event_ref"]] = {**t, "msgs": []}
    for r in recs:
        ref = r.get("event_ref")
        if ref:
            # explicit event_ref is affiliation, not a hint: it always wins and
            # the keyword fallback never applies to an already-labeled message
            if ref in by_ref:
                by_ref[ref]["msgs"].append(r)
        elif r.get("in_window") and not r.get("is_service"):
            # keyword fallback for messages without an event_ref
            text = (r.get("text_plain") or "")
            for t in threads["threads"]:
                if any(k in text for k in t["keywords"][:6]):
                    by_ref[t["event_ref"]]["msgs"].append(r)
                    break
    return by_ref


def thread_events(recs, threads, tx_rows):
    by_ref = _group_thread_msgs(recs, threads)
    out = []
    for ref, t in by_ref.items():
        # first_seen/last_seen come from actual message timestamps only;
        # anchor_dates are display-only and mix Jalali strings with ISO dates
        msgs = sorted(t["msgs"], key=lambda m: m.get("timestamp") or "")
        tx_ids = [x for x in t.get("tx_ids", []) if x] or _tx_for(ref, tx_rows)
        total = sum(float(r.get("amount_toman") or 0) for r in tx_rows
                    if r.get("id") in tx_ids)
        if not msgs:
            # money-only thread: no matched messages but real ledger money —
            # kept with null message fields and money_only: true
            # (regular threads below carry no money_only key at all)
            if tx_ids:
                out.append({"event_ref": ref, "title": t["title"],
                            "first_seen": None, "last_seen": None, "chats": {},
                            "n_messages": 0, "tx_ids": tx_ids,
                            "tx_total_toman": total, "announcement_lag_days": None,
                            "decision_dates": [], "money_only": True})
            continue  # neither messages nor tx_ids -> dropped
        chats = {}
        for m in msgs:
            c = chats.setdefault(m["chat"], {"first": m["timestamp"], "last": m["timestamp"], "n": 0})
            c["n"] += 1
            c["last"] = max(c["last"], m["timestamp"])
        lag = None
        if "channel" in chats and len(chats) > 1:
            firsts = [v["first"] for c, v in chats.items() if c != "channel"]
            pre = min(firsts)
            d1 = datetime.fromisoformat(pre[:19]); d2 = datetime.fromisoformat(chats["channel"]["first"][:19])
            # negative lag is legitimate: announcement can precede coordination
            lag = (d2 - d1).days if d2 >= d1 else -(d1 - d2).days
        out.append({"event_ref": ref, "title": t["title"],
                    "first_seen": msgs[0]["timestamp"], "last_seen": msgs[-1]["timestamp"],
                    "chats": chats, "n_messages": len(msgs), "tx_ids": tx_ids,
                    "tx_total_toman": total, "announcement_lag_days": lag,
                    "decision_dates": [m["timestamp"][:10] for m in msgs if m.get("is_decision")]})
    # money-only threads have no message timestamps to order by: sorted last
    return sorted(out, key=lambda x: (x["first_seen"] is None, x["first_seen"] or ""))


def _tx_for(ref, tx_rows):
    proj = PROJECT_FALLBACK.get(ref)
    return [r["id"] for r in tx_rows if proj and r.get("project") == proj] if proj else []


def _verify(tx_threads, tx_rows):
    """Print the §5 ledger-join checks for threads with money behind them."""
    checks = {"summer-school-1404": "Summer School 1404",
              "summer-school-1405": "Summer School 1405",
              "intro-event-1405": "Intro Event 1405"}
    by_ref = {t["event_ref"]: t for t in tx_threads}
    for ref, proj in checks.items():
        t = by_ref.get(ref)
        proj_sum = sum(float(r.get("amount_toman") or 0) for r in tx_rows
                       if r.get("project") == proj)
        ok = bool(t) and t["tx_total_toman"] > 0 and t["tx_total_toman"] == proj_sum
        got = t["tx_total_toman"] if t else None
        print(f"[check] {ref}: tx_total_toman={got} vs ledger project '{proj}' sum={proj_sum:.0f} "
              f"-> {'OK' if ok else 'MISMATCH'}")
    y = by_ref.get("yalda-1404")
    n_tx = len(y["tx_ids"]) if y else 0
    print(f"[check] yalda-1404: {n_tx} TX ids -> {'OK' if n_tx == 27 else 'MISMATCH (expected 27)'}")


def build_timeline():
    recs = [json.loads(l) for l in open(ROOT / "analysis/classified.jsonl", encoding="utf-8")]
    threads = read_json(ROOT / "analysis/threads.json")
    tx_rows = _load_tx()
    tl = {"threads": thread_events(recs, threads, tx_rows),
          "monthly_activity": monthly_activity(recs),
          "monthly_cashflow": monthly_cashflow(tx_rows),
          "hour_histogram": hour_histogram(recs),
          "weekday_hour_heat": weekday_hour_heat(recs),
          "event_start_times": event_start_times(recs, threads)}
    tl["mechanics"] = detect_mechanics(tl["weekday_hour_heat"], tl["event_start_times"],
                                       tx_rows, recs)
    write_json(ROOT / "analysis/timeline.json", tl)
    print(f"{len(tl['threads'])} threads written")
    _verify(tl["threads"], tx_rows)


# ---------------------------------------------------------------- analytics

# literal "HH:MM" mentions only (Persian digits normalized first); the optional
# ساعت/ساعتِ prefix is tolerated but not required. Colloquial hour-only
# mentions like «ساعت ۳» are deliberately NOT converted — collected never.
TIME_RE = re.compile(r"(?:ساعت|ساعتِ)?\s*([0-9]{1,2}:[0-9]{2})(?![0-9])")


def extract_time_mentions(text):
    t = normalize_digits(text or "")
    return [f"{h.zfill(2)}:{m}" for h, m in
            (x.split(":") for x in TIME_RE.findall(t))
            if 0 <= int(h) < 24 and 0 <= int(m) < 60]


def monthly_activity(recs):
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in recs:
        if not r.get("in_window") or r.get("is_service") or not r.get("jalali_month"):
            continue
        for c in r.get("categories") or ["uncategorized"]:
            out[r["jalali_month"]][r["chat"]][c] += 1
    return out


def monthly_cashflow(tx_rows):
    out = defaultdict(lambda: {"Receipts": 0.0, "Payments": 0.0,
                               "by_category": defaultdict(float),
                               "by_project": defaultdict(float)})
    for r in tx_rows:
        # undated rows (TX0060/TX0096) have no period_jalali: bucket under
        # "unknown" so their money stays visible instead of a NaN key
        period = r.get("period_jalali")
        m = out[period if isinstance(period, str) and period else "unknown"]
        amt = float(r.get("amount_toman") or 0)
        if r["direction"] == "Receipt":
            m["Receipts"] += amt
        else:
            m["Payments"] += amt
        m["by_category"][r.get("category") or "Unknown"] += amt
        m["by_project"][r.get("project") or "Unknown"] += amt
    return out


def hour_histogram(recs):
    out = defaultdict(lambda: defaultdict(int))
    for r in recs:
        if r.get("in_window") and not r.get("is_service") and r.get("hour") is not None:
            out[r["chat"]][r["hour"]] += 1
    return out


def weekday_hour_heat(recs):
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in recs:
        if (r.get("in_window") and not r.get("is_service")
                and r.get("hour") is not None and r.get("jalali_weekday")):
            out[r["chat"]][r["jalali_weekday"]][r["hour"]] += 1
    return out


def event_start_times(recs, threads):
    """Per thread: literal HH:MM mentions in its channel posts (any *channel
    chat) or messages carrying an events-category label. Key present only
    when n >= 1; mode = most common mention (ties: first seen wins)."""
    out = {}
    for ref, t in _group_thread_msgs(recs, threads).items():
        times = []
        for m in t["msgs"]:
            is_channel_post = str(m.get("chat") or "").endswith("channel")
            if is_channel_post or "events" in (m.get("categories") or []):
                times.extend(extract_time_mentions(m.get("text_plain") or ""))
        if not times:
            continue
        cnt = Counter(times)
        out[ref] = {"times": sorted(set(times)), "n": len(times),
                    "mode": cnt.most_common(1)[0][0]}
    return out


def detect_mechanics(heat, start_times, tx_rows, recs=None):
    """Recurring patterns, n >= 5 only:
    - fixed-slot: a thread's start-time mode mentioned >= 5 times
    - peak: the max hour of a (chat, jalali_weekday) cell with >= 5 messages
    - tx-hour: an hour holding >= 5 distinct accounting_group messages that
      the ledger's message_ids join resolves (exact id match; recs optional —
      without it no tx-hour entries are produced)."""
    mech = []
    for ref, s in start_times.items():
        if s["n"] >= 5 and s.get("mode"):
            mech.append({"kind": "fixed-slot", "hour": int(s["mode"][:2]),
                         "category": ref, "n": s["n"],
                         "note": f"{ref} most often mentions start {s['mode']}"})
    for chat, days in heat.items():
        for wd, hours in days.items():
            h, n = max(hours.items(), key=lambda kv: kv[1])
            if n >= 5:
                mech.append({"kind": "peak", "jalali_weekday": wd, "hour": h,
                             "category": chat, "n": n,
                             "note": f"{chat} peaks {wd} {h:02d}:00"})
    if recs is not None:
        ag = {m["message_id"]: m for m in recs
              if m.get("chat") == "accounting_group" and m.get("hour") is not None}
        linked = set()
        for r in tx_rows:
            mids = r.get("message_ids")
            if not isinstance(mids, str):
                continue
            for mid in mids.split(";"):
                mid = mid.strip()
                if mid in ag:
                    linked.add(mid)
        hour_n = Counter(ag[mid]["hour"] for mid in linked)
        for h, n in sorted(hour_n.items()):
            if n >= 5:
                mech.append({"kind": "tx-hour", "hour": h,
                             "category": "accounting_group", "n": n,
                             "note": f"{n} TX-linked messages in accounting_group at {h:02d}:00"})
    return mech


if __name__ == "__main__":
    build_timeline()
