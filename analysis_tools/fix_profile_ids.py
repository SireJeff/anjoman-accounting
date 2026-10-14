"""Remap profile evidence ids that point at service separators.

In the raw exports the DOM holds two id families: content messages
(``id="message123"``) and service rows such as date separators
(``id="message-123"``).  They are DIFFERENT DOM nodes that only collide once
non-alphanumerics are stripped, so resolution here is exact-string-match
first, dash-stripped normalization only as a fallback.  A cited id that
exact-matches a content record is never a separator citation, no matter how
many same-numbered separators exist.

For every ``candidate_threads[].evidence_message_ids`` and
``time_patterns[].evidence_message_ids`` in analysis/profiles/ (docx.json
excluded: its para-NN/table-row-NN ids do not reference messages):

* if the referenced record is a service message (or the id is unresolvable
  in the profile's chat), replace it with the next non-service message id in
  that chat's messages.jsonl order -- the content message sits immediately
  after each separator;
* if no following non-service message exists, drop the id;
* never leave a list empty: if every id would drop, keep the single closest
  following non-service message in the chat;
* event-hour / weekday-slot patterns whose evidence ends up with zero
  hour-bearing ids are dropped (an hour claim needs hour evidence).

Prints a proof table (ids_before, service_ids_found, ids_remapped,
ids_dropped, patterns_dropped per profile) and asserts that afterwards ZERO
evidence ids resolve to service messages.  Files are rewritten (UTF-8,
indent=1, same structure) only when something actually changed.
"""
import json, sys
from .common import ANALYSIS

PROFILES_DIR = ANALYSIS / "profiles"
MSGS = ANALYSIS / "messages.jsonl"

# profile -> chat whose messages its evidence ids reference
# (ledger threads cite accounting-group message ids; docx cites none)
PROFILE_CHAT = {
    "channel": "channel",
    "accounting_group": "accounting_group",
    "summerschool_channel": "summerschool_channel",
    "public_group": "public_group",
    "private_group": "private_group",
    "ledger": "accounting_group",
}
SKIP = {"docx"}  # para-NN / table-row-NN ids -- not message references

_norm = lambda mid: "".join(ch for ch in (mid or "") if ch.isalnum())


def load_chats():
    """chat -> ordered [(message_id, norm_id, is_service, hour)] plus indexes."""
    chats = {}
    with open(MSGS, encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            chats.setdefault(m["chat"], []).append(
                (m["message_id"], _norm(m["message_id"]),
                 bool(m["is_service"]), m["hour"])
            )
    for chat, rows in chats.items():
        exact, norm = {}, {}
        for r in rows:
            exact.setdefault(r[0], r)
            norm.setdefault(r[1], []).append(r)
        chats[chat] = {"rows": rows, "exact": exact, "norm": norm}
    return chats


def resolve(chats, chat, cited):
    """-> (record, how) where how in exact/norm/dash-twin/unresolved.

    record is None when unresolved.  ``dash-twin``: no exact match, several
    normalized rows -- resolves to the content twin when one exists (the
    dash-form rows are unrelated separators sharing the number), else to the
    first service row so the caller remaps it.
    """
    c = chats.get(chat)
    if not c:
        return None, "unresolved"
    if cited in c["exact"]:
        return c["exact"][cited], "exact"
    cands = c["norm"].get(_norm(cited), [])
    if len(cands) == 1:
        return cands[0], "norm"
    if len(cands) > 1:
        content = [r for r in cands if not r[2]]
        return (content[0] if content else cands[0]), "dash-twin"
    return None, "unresolved"


def next_non_service(chats, chat, record):
    """Closest following non-service row id after `record` in chat order."""
    rows = chats[chat]["rows"]
    start = rows.index(record) + 1 if record is not None else 0
    for r in rows[start:]:
        if not r[2]:
            return r
    return None


def any_non_service(chats, chat):
    for r in chats.get(chat, {"rows": []})["rows"]:
        if not r[2]:
            return r
    return None


def fix_ids(chats, chat, ids, stats, reasons, where):
    """Remap/drop service or unresolvable ids in one evidence list."""
    out = []
    for cited in ids:
        record, how = resolve(chats, chat, cited)
        if record is not None and not record[2]:          # good content ref
            out.append(cited)
            if how == "dash-twin":
                stats["dash_twins"] += 1
            continue
        stats["service_found"] += 1
        if record is None:
            reasons.append(f"{where}: {cited} unresolvable in chat '{chat}' -> dropped")
            stats["dropped"] += 1
            continue
        nxt = next_non_service(chats, chat, record)
        if nxt is None:
            reasons.append(f"{where}: {cited} service with no following non-service in '{chat}' -> dropped")
            stats["dropped"] += 1
        else:
            out.append(nxt[0])
            stats["remapped"] += 1
            reasons.append(f"{where}: {cited} service separator -> {nxt[0]}")
    # never leave the list empty
    if not out and ids:
        keeper = next_non_service(chats, chat, None) or any_non_service(chats, chat)
        if keeper is not None:
            out = [keeper[0]]
            stats["remapped"] += 1
            reasons.append(f"{where}: all ids dropped -> kept closest non-service {keeper[0]}")
        else:
            reasons.append(f"{where}: chat '{chat}' has no non-service messages; left empty")
    seen, dedup = set(), []
    for i in out:
        if i not in seen:
            seen.add(i)
            dedup.append(i)
        else:
            stats["dropped"] += 1
            reasons.append(f"{where}: duplicate id {i} after remap -> deduped")
    return dedup


def hour_bearing(chats, chat, ids):
    n = 0
    for cited in ids:
        record, _ = resolve(chats, chat, cited)
        if record is not None and not record[2] and record[3] is not None:
            n += 1
    return n


def process(name, chats):
    profile = json.loads((PROFILES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    chat = PROFILE_CHAT[name]
    stats = {"ids_before": 0, "service_found": 0, "remapped": 0,
             "dropped": 0, "patterns_dropped": 0, "dash_twins": 0}
    reasons = []
    for t in profile.get("candidate_threads", []):
        ids = t.get("evidence_message_ids", [])
        stats["ids_before"] += len(ids)
        t["evidence_message_ids"] = fix_ids(chats, chat, ids, stats, reasons,
                                            f"thread {t.get('event_ref')}")
    patterns = []
    for tp in profile.get("time_patterns", []):
        ids = tp.get("evidence_message_ids", [])
        stats["ids_before"] += len(ids)
        tp["evidence_message_ids"] = fix_ids(chats, chat, ids, stats, reasons,
                                             f"pattern {tp.get('kind')}/{tp.get('hour') or tp.get('jalali_weekday')}")
        if tp.get("kind") in ("event-hour", "weekday-slot") \
                and hour_bearing(chats, chat, tp["evidence_message_ids"]) == 0:
            stats["patterns_dropped"] += 1
            print(f"  DROPPED pattern {name}: {tp.get('kind')} "
                  f"hour={tp.get('hour')} weekday={tp.get('jalali_weekday')} "
                  f"(no hour-bearing evidence left)")
            continue
        patterns.append(tp)
    if "time_patterns" in profile:   # never introduce the key (ledger lacks it)
        profile["time_patterns"] = patterns
    return profile, stats, reasons


def audit(chats):
    """Post-fix assertion: zero evidence ids resolve to service messages."""
    bad, total = [], 0
    for name, chat in PROFILE_CHAT.items():
        profile = json.loads((PROFILES_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for t in profile.get("candidate_threads", []):
            for cited in t.get("evidence_message_ids", []):
                total += 1
                record, _ = resolve(chats, chat, cited)
                if record is None or record[2]:
                    bad.append(f"{name}/thread {t.get('event_ref')}: {cited}")
        for tp in profile.get("time_patterns", []):
            for cited in tp.get("evidence_message_ids", []):
                total += 1
                record, _ = resolve(chats, chat, cited)
                if record is None or record[2]:
                    bad.append(f"{name}/pattern {tp.get('kind')}: {cited}")
    return total, bad


def main():
    chats = load_chats()
    header = (f"{'profile':<22}{'ids_before':>11}{'service_ids_found':>19}"
              f"{'ids_remapped':>14}{'ids_dropped':>13}{'patterns_dropped':>17}")
    print(header)
    print("-" * len(header))
    for name in sorted(PROFILE_CHAT):
        profile, stats, reasons = process(name, chats)
        print(f"{name:<22}{stats['ids_before']:>11}{stats['service_found']:>19}"
              f"{stats['remapped']:>14}{stats['dropped']:>13}{stats['patterns_dropped']:>17}")
        if stats["dash_twins"]:
            print(f"  note: {stats['dash_twins']} citations exact-match a content "
                  f"message that has a same-numbered separator twin "
                  f"(left on the content message)")
        for r in reasons:
            print(f"  {r}")
        target = PROFILES_DIR / f"{name}.json"
        if stats["remapped"] or stats["dropped"] or stats["patterns_dropped"]:
            target.write_text(
                json.dumps(profile, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8")
            print(f"  rewritten: {target.name}")
        else:
            print(f"  unchanged: {target.name}")

    total, bad = audit(chats)
    print("-" * len(header))
    print(f"ASSERTION: {len(bad)}/{total} evidence ids resolve to service messages"
          f"{' -- PASS' if not bad else ' -- FAIL'}")
    for b in bad:
        print(f"  STILL SERVICE: {b}")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
