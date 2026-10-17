"""Ecosystem graph: association <-> subgroups <-> external orgs.

Id discipline: node ids are exact strings — seed-table ids, "<chat>_export",
"ext:<forwarded_from>" and "handle:<lowercased handle>". Nothing is
dash-stripped or otherwise normalized anywhere in this module.

Joined-forward back-fill (adopted from the task-4 review): Telegram Desktop's
export renderer merges the origin label onto the first block of a run of
consecutive forwards, leaving 40 label-less "joined" forward blocks (27
private_group, 11 public_group, 2 accounting_group) that messages.jsonl
carries with forwarded_from=null. Recovery is provably safe on this corpus
(lxml probes over all 19 export files, task-4 report):
- every default message div without a from_name is "joined" (0 exceptions), so
  a sender-less record is always a run continuation, never a run head;
- a joined no-name div directly following a forwarded div is itself a
  label-less forward (0 exceptions), so the jsonl-level rule "non-service,
  sender-less, forwarded_from-null record whose immediately preceding record
  is in the same chat and is a forward (labelled or back-filled)" recovers
  exactly the 40 and nothing else (verified against the HTML ground truth:
  40/40 matched, 0 false positives, 0 unresolvable).
"""
import json
import re
from collections import Counter

from .common import ROOT, write_json

SEEDS = [
    ("association",     "انجمن علمی فیزیک شریف", "association"),
    ("physics_tea",     "چای فیزیک (@physics_tea_sessions)", "subgroup"),
    ("tea_chat",        "چای - حضوری", "subgroup"),
    ("shabahang_sut",   "نشریه شباهنگ (@shabahang_sut)", "subgroup"),
    ("sharifastronomy", "گروه نجوم شریف (@sharifastronomy)", "subgroup"),
    ("takaneh",         "نشریه تکانه (@takaneh_physics_sharif)", "subgroup"),
    ("sutschools",      "مدرسه تابستانی فیزیک (@sutschools)", "subgroup"),
    ("quantasc",        "حلقه‌های کوانتا (@QuantaSC)", "subgroup"),
]
SEED_MATCH = {"شباهنگ": "shabahang_sut", "نجوم": "sharifastronomy", "آسترونومی": "sharifastronomy",
              "تکانه": "takaneh", "کوانتا": "quantasc", "چای": "physics_tea",
              "تابستانه": "sutschools", "school": "sutschools",
              "summer school": "sutschools",  # English form of the summerschool entity
              "انجمن علمی فیزیک": "association"}
# Curated alias (task-10 review fix): the association's own handle and its
# r-typo variant are the association itself, so mentions of them land on the
# seed node instead of separate handle: externals. SEED_MATCH cannot do this:
# mentions carry bare handles and bypass _map_origin. Deliberately excludes the
# ambiguous family variants (anjoman_elmi_phys_su, elmi_physics, anjomansut, ...)
# which stay external.
HANDLE_ALIAS = {"anjoman_elmi_phys_sut": "association", "rnjoman_elmi_phys_sut": "association"}
HANDLE_RE = re.compile(r"(?:t\.me/|@)([A-Za-z0-9_]{4,})")
EXPORT_NODE = {"private_group": "private_group_export", "public_group": "public_group_export",
               "channel": "channel_export", "accounting_group": "accounting_group_export",
               "summerschool_channel": "summerschool_channel_export"}


def _map_origin(name):
    for k, sid in SEED_MATCH.items():
        if k in (name or ""):
            return sid, None
    return None, name  # external/unknown


def backfill_joined_forwards(messages):
    """First pass per chat, file order: label-less joined forwards inherit the
    forwarded_from of the nearest preceding same-chat forward.

    Returns (new list of records, stats); the input records are not mutated.
    """
    out = []
    stats = {"joined_backfilled": 0, "unresolvable": 0}
    prev_chat, prev_is_forward, origin = None, False, None
    for m in messages:
        rec = dict(m)
        if rec.get("chat") != prev_chat:
            prev_chat, prev_is_forward, origin = rec.get("chat"), False, None
        labelled = rec.get("forwarded_from")
        if labelled:
            origin, prev_is_forward = labelled, True
        elif (prev_is_forward and not rec.get("is_service")
              and not rec.get("sender") and origin):
            rec["forwarded_from"] = origin   # joined block continuing the forward run
            stats["joined_backfilled"] += 1
            prev_is_forward = True
        else:
            prev_is_forward = False          # run head, service or new chat closes the run
        out.append(rec)
    return out, stats


def build(messages, backfill=True):
    if backfill:
        messages, _ = backfill_joined_forwards(messages)
    fwd, men = Counter(), Counter()
    externals = {}
    for m in messages:
        src = EXPORT_NODE.get(m["chat"])
        if m.get("forwarded_from"):
            sid, raw = _map_origin(m["forwarded_from"])
            if sid:
                fwd[(src, sid)] += 1
            elif raw:
                externals[raw] = externals.get(raw, 0) + 1
                fwd[(src, f"ext:{raw}")] += 1
        for h in HANDLE_RE.findall(m.get("text_plain") or ""):
            hl = HANDLE_ALIAS.get(h.lower(), h.lower())
            sid = hl if hl in {s[0] for s in SEEDS} else f"handle:{hl}"
            men[(src, sid)] += 1
    nodes = [{"id": sid, "label": lab, "type": typ, "seed": True}
             for sid, lab, typ in SEEDS]
    nodes += [{"id": EXPORT_NODE[k], "label": k.replace("_", " "), "type": "chat-export", "seed": False}
              for k in EXPORT_NODE]
    nodes += [{"id": f"ext:{n}", "label": n, "type": "external", "seed": False}
              for n in externals]
    seen_handles = {e[1] for e in list(fwd) + list(men)} - {n["id"] for n in nodes}
    nodes += [{"id": h, "label": h.split(":", 1)[1], "type": "external", "seed": False}
              for h in seen_handles if h.startswith(("ext:", "handle:"))]
    edges = ([{"source": s, "target": t, "type": "forward", "weight": c} for (s, t), c in fwd.items()] +
             [{"source": s, "target": t, "type": "mention", "weight": c} for (s, t), c in men.items()])
    return {"nodes": nodes, "edges": edges}


def main():
    msgs = [json.loads(l) for l in open(ROOT / "analysis/messages.jsonl", encoding="utf-8")]
    g = build(msgs)
    raw = build(msgs, backfill=False)
    filled, bf_stats = backfill_joined_forwards(msgs)
    fw = lambda gr: [e for e in gr["edges"] if e["type"] == "forward"]  # noqa: E731
    meta = {
        "backfill": bf_stats,
        "forward_origin_messages_before": sum(1 for m in msgs if m.get("forwarded_from")),
        "forward_origin_messages_after": sum(1 for m in filled if m.get("forwarded_from")),
        "forward_edges_before": len(fw(raw)),
        "forward_edges_after": len(fw(g)),
        "forward_weight_before": sum(e["weight"] for e in fw(raw)),
        "forward_weight_after": sum(e["weight"] for e in fw(g)),
    }
    g["meta"] = meta
    g["validation"] = {sid: ("evidenced" if any(e["target"] == sid and e["weight"] >= 3
                                                for e in g["edges"]) else "unverified")
                       for sid, _, _ in SEEDS}
    write_json(ROOT / "analysis/ecosystem.json", g)
    unverified = [sid for sid, v in g["validation"].items() if v == "unverified"]
    print(f"{len(g['nodes'])} nodes, {len(g['edges'])} edges")
    print(f"back-fill: {meta['forward_origin_messages_before']} -> "
          f"{meta['forward_origin_messages_after']} forward-origin messages "
          f"(+{meta['backfill']['joined_backfilled']} joined inherited, "
          f"{meta['backfill']['unresolvable']} unresolvable)")
    print(f"forward edges before/after back-fill: {meta['forward_edges_before']}/"
          f"{meta['forward_edges_after']} (total weight {meta['forward_weight_before']} -> "
          f"{meta['forward_weight_after']})")
    print(f"validation: {g['validation']}")
    print(f"unverified seeds: {unverified if unverified else 'none'}")


if __name__ == "__main__":
    main()
