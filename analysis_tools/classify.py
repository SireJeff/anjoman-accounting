"""Stage 3: structural rules + lexicon classification + LLM residual machinery."""
import json, re, sys
from .common import ROOT, read_json, write_json, normalize_digits

RULE_ORDER = ["education_courses", "events", "publications_shabahng", "media_outreach",
              "governance_decisions", "finance_operations", "website_tech",
              "community_social", "coordination_logistics", "meta_noise"]
FORM_LINK = re.compile(r"docs\.google\.com/(forms|spreadsheets)")

def classify_message(rec, lexicon):
    text = normalize_digits(rec.get("text_plain") or "").lower()
    media = rec.get("media_kinds") or []
    cats, method = [], None

    # Layer 1 - structural rules
    if "poll" in media:
        cats.append("governance_decisions"); method = "rule"
    if FORM_LINK.search(text):
        cats.append("media_outreach" if "فرم همکاری" not in text else "publications_shabahng")
        if method is None: method = "rule"
    if rec.get("forwarded_from") and not text:
        cats.append("media_outreach"); method = method or "rule"
    if not text and media and set(media) <= {"sticker", "animated"}:
        cats.append("meta_noise"); method = "rule"
    if not text and media and "photo" in media:
        cats.append("community_social"); method = method or "rule"

    # Layer 2 - lexicon (multi-label)
    lex_hits = [c for c in RULE_ORDER
                if any(normalize_digits(k).lower() in text for k in lexicon.get(c, []))]
    if lex_hits:
        for c in lex_hits:
            if c not in cats:
                cats.append(c)
        method = method or "lexicon"

    conf = 0.9 if method == "rule" else (0.7 if method == "lexicon" else 0.0)
    return {"categories": cats[:4], "event_ref": None,
            "is_decision": False, "confidence": conf,
            "method": method if cats else None}

def main():
    lex = read_json(ROOT / "analysis/lexicon.json")
    out = []
    with open(ROOT / "analysis/messages.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            rec.update(classify_message(rec, lex))
            out.append(rec)
    # layer 3: fold in LLM residual labels when the label file exists (idempotent)
    labels_path = ROOT / "analysis/llm_labels.json"
    if labels_path.exists():
        print(f"re-applied {apply_llm_labels(out, read_json(labels_path))} llm labels")
    stats = {"total": 0, "by_method": {}, "by_category": {},
             "in_window": {"total": 0, "by_method": {}}}
    for rec in out:
        method = rec["method"] or "unclassified"
        stats["total"] += 1
        stats["by_method"][method] = stats["by_method"].get(method, 0) + 1
        if rec.get("in_window") and not rec.get("is_service"):
            win = stats["in_window"]
            win["total"] += 1
            win["by_method"][method] = win["by_method"].get(method, 0) + 1
        for c in rec["categories"]:
            stats["by_category"][c] = stats["by_category"].get(c, 0) + 1
    win = stats["in_window"]
    win["classified"] = win["total"] - win["by_method"].get("unclassified", 0)
    win["coverage_pct"] = round(100.0 * win["classified"] / win["total"], 2) if win["total"] else 0.0
    write_classified(out)
    write_json(ROOT / "analysis/classification_stats.json", stats)
    print(json.dumps(stats, indent=1, ensure_ascii=False))


# --- Task 7: LLM residual pass (labels produced by labeling agents) ---

def load_classified():
    with open(ROOT / "analysis/classified.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]

def write_classified(recs):
    with open(ROOT / "analysis/classified.jsonl", "w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

def select_residual(recs):
    """In-window, non-service messages with no method or confidence < 0.7."""
    return [r for r in recs if r.get("in_window") and not r.get("is_service")
            and (r.get("method") is None or (r.get("confidence") or 0.0) < 0.7)]

def build_batches(resid, batch_size=200):
    return [{"batch": bi + 1, "items": [
        {"key": f'{r["chat"]}#{r["message_id"]}', "chat": r["chat"],
         "month": r["jalali_month"], "text": (r["text_plain"] or "")[:500],
         "media": r["media_kinds"]}
        for r in resid[i:i + batch_size]]}
        for bi, i in enumerate(range(0, len(resid), batch_size))]

def emit_residual(batch_size=200):
    resid = select_residual(load_classified())
    batches = build_batches(resid, batch_size)
    write_json(ROOT / "analysis/llm_residual.json",
               {"n_residual": len(resid), "batches": batches})
    print(f"residual: {len(resid)} messages in {len(batches)} batches")

def apply_llm_labels(recs, labels):
    """Merge {"key": {categories, is_decision, event_ref, confidence}} into records."""
    n = 0
    for r in recs:
        lab = labels.get(f'{r["chat"]}#{r["message_id"]}')
        if lab and (r.get("method") is None or (r.get("confidence") or 0.0) < 0.7):
            if lab.get("categories"):
                r["categories"] = lab["categories"]; r["method"] = "llm"
                r["confidence"] = lab.get("confidence", 0.6); n += 1
            r["is_decision"] = r.get("is_decision", False) or bool(lab.get("is_decision"))
            if lab.get("event_ref"):
                r["event_ref"] = lab["event_ref"]
    return n

def apply_llm():
    labels = read_json(ROOT / "analysis/llm_labels.json")
    recs = load_classified()
    n = apply_llm_labels(recs, labels)
    write_classified(recs)
    print(f"applied {n} llm labels")

if __name__ == "__main__":
    if "--emit-residual" in sys.argv:
        emit_residual()
    elif "--apply" in sys.argv:
        apply_llm()
    else:
        main()
