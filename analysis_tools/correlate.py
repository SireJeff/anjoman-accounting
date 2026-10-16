"""Stage 4a: event threads + cross-chat correlation."""
import json
from datetime import datetime
from .common import ROOT, LEDGER_CSV, read_json, write_json

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


def thread_events(recs, threads, tx_rows):
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
    out = []
    for ref, t in by_ref.items():
        # first_seen/last_seen come from actual message timestamps only;
        # anchor_dates are display-only and mix Jalali strings with ISO dates
        msgs = sorted(t["msgs"], key=lambda m: m.get("timestamp") or "")
        if not msgs:
            continue
        chats = {}
        for m in msgs:
            c = chats.setdefault(m["chat"], {"first": m["timestamp"], "last": m["timestamp"], "n": 0})
            c["n"] += 1
            c["last"] = max(c["last"], m["timestamp"])
        tx_ids = [x for x in t.get("tx_ids", []) if x] or _tx_for(ref, tx_rows)
        total = sum(float(r.get("amount_toman") or 0) for r in tx_rows
                    if r.get("id") in tx_ids)
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
    return sorted(out, key=lambda x: x["first_seen"])


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
    tl = {"threads": thread_events(recs, threads, tx_rows)}
    write_json(ROOT / "analysis/timeline.json", tl)
    print(f"{len(tl['threads'])} threads written")
    _verify(tl["threads"], tx_rows)


if __name__ == "__main__":
    build_timeline()
