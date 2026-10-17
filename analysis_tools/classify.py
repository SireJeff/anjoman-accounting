"""Stage 3: structural rules + lexicon classification + LLM residual machinery."""
import json, re, sys
from .common import ROOT, read_json, write_json, normalize_digits

RULE_ORDER = ["education_courses", "events", "publications_shabahng", "media_outreach",
              "governance_decisions", "finance_operations", "website_tech",
              "community_social", "coordination_logistics", "meta_noise"]
FORM_LINK = re.compile(r"docs\.google\.com/(forms|spreadsheets)")

# --- Task 14 precision fix: corroboration for high-ambiguity lexicon words ---
# Some single lexicon words are too ambiguous to count alone: Persian verb
# forms embed them as substrings ("حساب کردم" I-calculated, "پرسیده" asked →
# رسید; "متریال" material → ریال), and broadcast ads carry stray tokens
# ("API", "تخفیف", "ثبت‌نام" for external camps). A lexicon hit on a risky
# word counts only when a corroborating token for the same category
# co-occurs in the text (short corroborators are word-boundary matched as
# well: هاست inside the enclitic انتقال‌هاست must not corroborate دامنه).
# Multi-word lexicon entries are never risky.
FINANCE_CORROBORATORS = ["تومان", "تومن", "ریال", "حق الزحمه", "حق‌الزحمه", "کارت",
                         "تراکنش", "گردش", "شارژ", "پرداخت شد", "واریز", "واریزی",
                         "برداشت", "فاکتور", "دریافت شد"]
EDUCATION_CORROBORATORS = ["مدرسه", "دوره", "کلاس", "کارگاه", "سمینار", "وبینار",
                           "تابستانه", "instructor", "مدرس"]
WEBSITE_CORROBORATORS = ["دامنه", "سرور", "هاست", "وب سایت", "وب‌سایت", "وبسایت",
                         "alenush", "alenush.com", "vm", "بک‌اند", "فرانت‌اند",
                         "درگاه", "زرین‌پال", "بیلد", "آپلود", "آپدیت"]
COORDINATION_CORROBORATORS = ["رزرو", "اجاره", "اتاق", "سالن", "تجهیزات", "پذیرایی",
                              "مجوز", "پروژکتور", "استند", "پوستر"]
GOVERNANCE_CORROBORATORS = ["هیئت", "انتخابات", "تصمیم", "رأی", "رای گیری",
                            "رای‌گیری", "نشست ماهانه", "نظرسنجی", "تقسیم کار",
                            "plan"]
PUBLICATIONS_CORROBORATORS = ["نشریه", "شماره", "ژورنال", "مجله"]
# the bare word شماره (issue/number) is itself ambiguous (شماره کارت,
# phone numbers), so it corroborates on the journal names it co-occurs with
PUBLICATIONS_NAME_CORROBORATORS = ["نشریه", "شباهنگ", "تکانه", "ژورنال", "مجله"]

RISKY_WORDS = {
    "finance_operations": {**{w: FINANCE_CORROBORATORS
                              for w in ["حساب", "رسید", "مبلغ", "تخفیف", "شارژ",
                                        "قیمت", "هزینه", "پول", "ریال", "پرداخت",
                                        # round 3: sponsor name-drops are
                                        # chatter, and برداشت = physics
                                        # "interpretation"/verb stem
                                        "اسپانسر", "برداشت"]},
                           # physics "circulation/flux" needs a money/bank token
                           "گردش": ["مالی", "کارت", "حساب", "بانک"]},
    "education_courses": {w: EDUCATION_CORROBORATORS
                          for w in ["ثبت‌نام", "ثبت نام"]},
    "website_tech": {**{w: WEBSITE_CORROBORATORS for w in ["سایت", "api"]},
                     # "دامنه" = amplitude in physics; needs a web-infra token
                     "دامنه": ["سرور", "هاست", "alenush", "خرید", "تمدید"]},
    "coordination_logistics": {w: COORDINATION_CORROBORATORS
                               for w in ["چاپ", "سالن", "هماهنگی"]},
    # round 2: polysemous tokens beyond the original risky set
    # round 3: bare تصمیم گرفتیم is announcement prose, not board action
    "governance_decisions": {w: GOVERNANCE_CORROBORATORS
                             for w in ["جلسه", "تصمیم"]},
    # round 3: the journal names/anchors fire on hashtag brand tags
    # (#شباهنگ in astronomy news footers), production credit lines
    # (ویراستاری علمی), and textbook volumes (جلد دوم هالیدی)
    "publications_shabahng": {**{w: PUBLICATIONS_CORROBORATORS
                                 for w in ["تکانه", "شباهنگ", "ویراستاری", "جلد"]},
                              "شماره": PUBLICATIONS_NAME_CORROBORATORS},
}

# bare corroborator tokens per category, reused by the round-3 demotion gate
CATEGORY_CORROBORATORS = {
    "finance_operations": FINANCE_CORROBORATORS,
    "education_courses": EDUCATION_CORROBORATORS,
    "website_tech": WEBSITE_CORROBORATORS,
    "coordination_logistics": COORDINATION_CORROBORATORS,
    "governance_decisions": GOVERNANCE_CORROBORATORS,
    "publications_shabahng": PUBLICATIONS_CORROBORATORS,
}

# --- Task 14 round 2: word-boundary matching for short keywords ---
# Single-word lexicon entries of length <= 5 count only as standalone words:
# the character immediately before and after the occurrence must not be a
# word char (Persian block, ZWNJ, or ASCII letter/digit). This kills
# substring false positives such as لتک inside کلتک (Caltech), اوکی inside
# اوکیه, باشه inside می‌باشه, مدرس inside مدارس, ok inside token/broker.
WORD_CHAR = re.compile("[؀-ۿ‌A-Za-z0-9]")
SHORT_KEYWORD_MAX = 5

def _word_char_at(s, i):
    return 0 <= i < len(s) and WORD_CHAR.match(s[i]) is not None

def contains_standalone(text, kw):
    """True when kw occurs in text at least once with non-word chars (or the
    string edge) on both sides."""
    start = 0
    while True:
        i = text.find(kw, start)
        if i < 0:
            return False
        if not _word_char_at(text, i - 1) and not _word_char_at(text, i + len(kw)):
            return True
        start = i + 1

def remove_standalone(text, kw):
    """Replace every standalone occurrence of kw with a space (long or
    multi-word entries: plain substring replacement)."""
    if " " in kw or len(kw) > SHORT_KEYWORD_MAX:
        return text.replace(kw, " ")
    out, start, i = [], 0, text.find(kw)
    while i >= 0:
        if not _word_char_at(text, i - 1) and not _word_char_at(text, i + len(kw)):
            out.append(text[start:i]); out.append(" ")
            start = i + len(kw)
        i = text.find(kw, max(i + 1, start))
    out.append(text[start:])
    return "".join(out)

def keyword_present(text, nk):
    """Multi-word and long entries match by substring; short single-word
    entries only as standalone words."""
    if " " in nk or len(nk) > SHORT_KEYWORD_MAX:
        return nk in text
    return contains_standalone(text, nk)

def meta_noise_hit(text, keywords):
    """Round-2 gate: a meta_noise lexicon token counts only when the message
    is affirmation-only — after removing every standalone lexicon token,
    nothing word-like remains. A stray آره/باشه/emoji inside a substantive
    message never makes it noise."""
    nks = sorted({normalize_digits(kw).lower() for kw in keywords}, key=len,
                 reverse=True)
    if not any(keyword_present(text, nk) for nk in nks):
        return False
    rem = text
    for nk in nks:
        rem = remove_standalone(rem, nk)
    return WORD_CHAR.search(rem) is None

def firing_keywords(text, category, keywords):
    """Every keyword that counts for the category, in lexicon order: non-risky
    words and multi-word entries always count; risky single words only with a
    corroborator in the text. Short keywords match only on word boundaries.
    meta_noise has its own dominance gate and is not keyword machinery."""
    if category == "meta_noise":
        return []
    risky = RISKY_WORDS.get(category, {})
    fired = []
    for kw in keywords:
        nk = normalize_digits(kw).lower()
        if not keyword_present(text, nk):
            continue
        if " " in nk:
            fired.append(nk)                  # multi-word entries are never risky
            continue
        corroborators = risky.get(nk)
        if corroborators is None:
            fired.append(nk)
        elif any(c != nk and keyword_present(text, normalize_digits(c).lower())
                 for c in corroborators):
            fired.append(nk)
    return fired

def category_hit(text, category, keywords):
    """Does any keyword count for the category? (See firing_keywords; meta_noise
    additionally requires the whole message to be affirmation-only.)"""
    if category == "meta_noise":
        return meta_noise_hit(text, keywords)
    return bool(firing_keywords(text, category, keywords))

# --- Task 14 round 3: multi-label gating on broadcasts ---
# Forwarded posts and channel-origin broadcasts (event ads, journal issues,
# news digests) fire several topical categories at once, and every extra
# label is another precision test. On a broadcast the extra labels are
# usually stray single generic-word hits (a polysemous risky word that
# happened to find a corroborator), so weakly supported topical categories
# are dropped whenever at least one strongly supported topical category
# remains. Rule labels (polls, form links) carry no keyword evidence and are
# never weak; conversation (non-broadcast) keeps every label.

def is_broadcast(rec):
    """Forwarded posts and original channel posts: one-to-many broadcasts
    rather than conversation."""
    return bool(rec.get("forwarded_from")) or rec.get("chat") == "channel"

def weak_broadcast_hit(text, category, keywords):
    """A topical category is weakly supported when its only firing evidence
    is a single risky (polysemous, corroboration-gated) word."""
    fired = firing_keywords(text, category, keywords)
    return len(fired) == 1 and fired[0] in RISKY_WORDS.get(category, {})

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
    # empty text + no media + not forwarded -> fallback category, never topical
    if not text.strip() and not media and not rec.get("forwarded_from"):
        cats.append("meta_noise"); method = method or "rule"

    # Layer 2 - lexicon (multi-label, corroboration-gated for risky words)
    lex_hits = [c for c in RULE_ORDER
                if category_hit(text, c, lexicon.get(c, []))]
    if lex_hits:
        for c in lex_hits:
            if c not in cats:
                cats.append(c)
        method = method or "lexicon"

    # Layer 2b - round 3: broadcast multi-label gating. On forwarded /
    # channel-origin posts carrying more than one topical category, drop the
    # weakly supported ones (single risky-word hits) as long as at least one
    # strongly supported topical category survives.
    if is_broadcast(rec):
        topical = [c for c in cats if c in TOPICAL_CATEGORIES]
        if len(topical) > 1:
            strong = [c for c in topical
                      if not weak_broadcast_hit(text, c, lexicon.get(c, []))]
            if strong and len(strong) < len(topical):
                weak = set(topical) - set(strong)
                cats = [c for c in cats if c not in weak]

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
        print(f"re-applied {apply_llm_labels(out, read_json(labels_path), lex)} llm labels")
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

# Round-2 review: LLM labels on contentless micro-messages (bare numbers,
# phatic fragments, empty voice notes) landed in topical categories at
# confidence 0.5-0.65. Such labels are unverifiable -> demote to the
# content categories deterministically. Only touches llm labels; rule and
# lexicon labels are never demoted.
TOPICAL_CATEGORIES = ["education_courses", "events", "publications_shabahng",
                      "media_outreach", "governance_decisions",
                      "finance_operations", "website_tech",
                      "coordination_logistics"]
MICRO_TEXT_MAX = 15
# round 3: scheduling one-liners and context-free fragments of 16-25 chars
# are equally unverifiable at llm confidence <= 0.65 — unless the text itself
# carries a token of evidence for the label (firing keyword or corroborator)
MICRO_TEXT_MAX_WEAK = 25

def _topical_evidence(text, category, lexicon):
    """Does the text itself carry evidence for the category — a firing
    lexicon keyword, or a bare corroborator token (کلاس for education,
    تومان for finance, ...)?"""
    if category_hit(text, category, lexicon.get(category, [])):
        return True
    return any(keyword_present(text, normalize_digits(c).lower())
               for c in CATEGORY_CORROBORATORS.get(category, []))

def demote_micro_message(r, lexicon=None):
    """llm label + confidence <= 0.65 + micro text + topical category ->
    community_social (text) or meta_noise (no text), confidence 0.5.
    Micro means <= 15 chars (or empty text with a lone voice note); round 3
    extends the window to <= 25 chars when no labeled category has any
    keyword/corroborator evidence in the text. event_ref/is_decision
    untouched; rule and lexicon labels are never demoted.
    Returns True when the record was demoted."""
    if r.get("method") != "llm" or (r.get("confidence") or 0.0) > 0.65:
        return False
    text = (r.get("text_plain") or "").strip()
    media = r.get("media_kinds") or []
    micro = len(text) <= MICRO_TEXT_MAX or (not text and media == ["voice"])
    weak = (not micro and lexicon is not None
            and len(text) <= MICRO_TEXT_MAX_WEAK
            and not any(_topical_evidence(text, c, lexicon)
                        for c in r.get("categories") or []))
    if not (micro or weak) or not any(c in TOPICAL_CATEGORIES
                                      for c in r.get("categories") or []):
        return False
    r["categories"] = ["meta_noise" if not text else "community_social"]
    r["confidence"] = 0.5
    return True


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

def apply_llm_labels(recs, labels, lexicon=None):
    """Merge {"key": {categories, is_decision, event_ref, confidence}} into records."""
    if lexicon is None:
        lexicon = read_json(ROOT / "analysis/lexicon.json")
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
            demote_micro_message(r, lexicon)
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
