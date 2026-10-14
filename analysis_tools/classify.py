"""Stage 3 layers 1-2: structural rules + lexicon classification."""
import json, re
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
    out, stats = [], {"total": 0, "by_method": {}, "by_category": {},
                      "in_window": {"total": 0, "by_method": {}}}
    with open(ROOT / "analysis/messages.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            cls = classify_message(rec, lex)
            rec.update(cls)
            out.append(rec)
            stats["total"] += 1
            stats["by_method"][cls["method"] or "unclassified"] = \
                stats["by_method"].get(cls["method"] or "unclassified", 0) + 1
            if rec.get("in_window") and not rec.get("is_service"):
                win = stats["in_window"]
                win["total"] += 1
                win["by_method"][cls["method"] or "unclassified"] = \
                    win["by_method"].get(cls["method"] or "unclassified", 0) + 1
            for c in cls["categories"]:
                stats["by_category"][c] = stats["by_category"].get(c, 0) + 1
    win = stats["in_window"]
    win["classified"] = win["total"] - win["by_method"].get("unclassified", 0)
    win["coverage_pct"] = round(100.0 * win["classified"] / win["total"], 2) if win["total"] else 0.0
    with open(ROOT / "analysis/classified.jsonl", "w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_json(ROOT / "analysis/classification_stats.json", stats)
    print(json.dumps(stats, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
