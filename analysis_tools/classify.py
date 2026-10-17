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
    "education_courses": {**{w: EDUCATION_CORROBORATORS
                             for w in ["ثبت‌نام", "ثبت نام"]},
                          # round 4: شبیه‌سازی is generic science prose
                          # (channel#message3506 essay) and پایتون appears in
                          # sponsor-prospectus company blurbs
                          # (public_group#message764); both need a course token
                          "شبیه‌سازی": EDUCATION_CORROBORATORS,
                          "پایتون": EDUCATION_CORROBORATORS},
    "website_tech": {**{w: WEBSITE_CORROBORATORS for w in ["سایت", "api"]},
                     # "دامنه" = amplitude in physics; needs a web-infra token
                     "دامنه": ["سرور", "هاست", "alenush", "خرید", "تمدید"]},
    "coordination_logistics": {**{w: COORDINATION_CORROBORATORS
                                  for w in ["چاپ", "سالن", "هماهنگی"]},
                               # round 4: bare مجوز fires on external news
                               # forwards (private_group#message11577 library
                               # entry permit); استیکر alone is Telegram
                               # sticker chatter (public_group#message2756),
                               # printing needs چاپ/طراحی/سفارش
                               "مجوز": COORDINATION_CORROBORATORS,
                               "استیکر": ["چاپ", "طراحی", "سفارش"]},
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

# round 4: multi-word entries that are themselves risky — "اتاق انجمن" in an
# event announcement is a bare venue line (channel#message3223 "مکان: اتاق
# انجمن..."), not logistics work; it counts only with a logistics verb.
MULTIWORD_RISKY = {
    "coordination_logistics": {
        "اتاق انجمن": ["رزرو", "ببرید", "بگذارید", "آماده کنید", "بگیرید"],
    }
}

# round 4: category-level blockers — a marker token that switches the whole
# category off unless an unblocking token co-occurs.
# Macro-economy editorials cite تومان/ریال/صندوق/هزینه but describe the
# national economy, not org money ops (channel#message3359); external
# journal forwards (تابش, Isfahan student physics journal) hit نشریه in
# their credit lines (channel#message3479, private_group#message11417).
MACRO_ECON_MARKERS = ["تورم", "دلار", "بیکاری", "اقتصاد", "بانک جهانی"]
MONEY_OPS_TOKENS = ["درگاه", "واریز", "واریزی", "فاکتور", "اسپانسر",
                    "حق الزحمه", "حق‌الزحمه", "پرداخت شد", "دریافت شد",
                    "تسویه", "شهریه", "کارت به کارت", "کارت‌به‌کارت"]
EXTERNAL_JOURNAL_NAMES = ["تابش"]
OWN_JOURNAL_ANCHORS = ["شباهنگ", "تکانه"]
CATEGORY_BLOCKERS = {
    "finance_operations": (MACRO_ECON_MARKERS, MONEY_OPS_TOKENS),
    "publications_shabahng": (EXTERNAL_JOURNAL_NAMES, OWN_JOURNAL_ANCHORS),
}

# round 4: generic greeting/address words. Inside a substantive (>100 char)
# text they must not add community_social when another category already
# fired (private_group#message10074 بچه‌ها inside a course proposal,
# public_group#message6227 سلام/بچه‌ها inside a governance report).
GENERIC_SOCIAL_WORDS = {"سلام", "بچه‌ها", "بچه ها", "خوبی", "چطوری",
                        "چه خبر", "لطفا", "زحمت"}
SUBSTANTIVE_TEXT_MIN = 100

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
WORD_TOKEN = re.compile("[؀-ۿ‌A-Za-z0-9]+")
# Arabic punctuation lives inside the ؀-ۿ block but is not part of words:
# "تابش،" must count as the standalone word تابش (and not as a substring of
# کتابش). Treated as separators everywhere word boundaries matter.
ARABIC_PUNCT = "،؛؟"
SHORT_KEYWORD_MAX = 5

# --- Task 14 round 4: Persian verb-conjugation suffix boundary ---
# A keyword that is a past-tense verb stem must not match inside a
# conjugated form: پرداخت fired inside پرداختید / پرداختند / پرداخته‌ام
# (public_group#message6227 "به این موضوع پرداختید" = attention you paid).
# Only multi-char personal endings are blocked; the single-char clitics
# م/ی are also possessive on nouns (واریزم = my deposit) and stay matches,
# and the participle in "پرداخت شد" is a separate multi-word entry.
VERB_ENDINGS = ("ید", "یم", "ند", "اند", "ه‌ام", "ه‌ای", "ه‌است", "ه‌ایم",
                "ه‌اید", "ه‌اند")

def _is_word_char(ch):
    return bool(WORD_CHAR.match(ch)) and ch not in ARABIC_PUNCT

def _word_char_at(s, i):
    return 0 <= i < len(s) and _is_word_char(s[i])

def _verb_ending_after(text, end):
    """Does a conjugation suffix start right at text[end]?"""
    return any(text[end:].startswith(s) for s in VERB_ENDINGS)

def contains_standalone(text, kw):
    """True when kw occurs in text at least once with non-word chars (or the
    string edge) on both sides and no verb-conjugation suffix glued on."""
    start = 0
    while True:
        i = text.find(kw, start)
        if i < 0:
            return False
        if (not _word_char_at(text, i - 1)
                and not _word_char_at(text, i + len(kw))
                and not _verb_ending_after(text, i + len(kw))):
            return True
        start = i + 1

def _has_unsuffixed_occurrence(text, nk):
    """Substring match that ignores occurrences glued to a verb ending."""
    start = 0
    while True:
        i = text.find(nk, start)
        if i < 0:
            return False
        if not _verb_ending_after(text, i + len(nk)):
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
    """Multi-word and long entries match by substring (verb-suffixed
    occurrences excluded); short single-word entries only as standalone,
    unsuffixed words."""
    if " " in nk or len(nk) > SHORT_KEYWORD_MAX:
        return _has_unsuffixed_occurrence(text, nk)
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
    return not any(_is_word_char(c) for c in rem)

# --- Task 14 round 4: affirmation-only texts resolve to meta_noise ---
# "وای😭😭" (public_group#message552) and "عالی و قوی" (public_group#message508)
# fire community_social lexicon words, but the stripped text (minus
# emoji/punctuation) is pure affirmation: phatic reaction, not social content.
AFFIRMATION_GLUE = {"و", "هم", "یا", "نه", "خوب", "خیلی", "واقعا", "قوی",
                    "بود", "هست", "است", "ست", "شد"}

def word_tokens(text):
    """Word tokens with Arabic punctuation treated as separators."""
    return WORD_TOKEN.findall(text.translate(str.maketrans(ARABIC_PUNCT,
                                                           "   ")))

def _lexicon_tokens(keywords):
    """Every word token of the (possibly multi-word) lexicon entries."""
    toks = set()
    for kw in keywords:
        toks.update(word_tokens(normalize_digits(kw).lower()))
    return toks

def affirmation_only_text(text, community_keywords, noise_keywords):
    """True when every word token of the text is a social/noise lexicon token
    or glue word, and at least one is a community_social lexicon token."""
    tokens = word_tokens(text)
    if not tokens:
        return False
    social = _lexicon_tokens(community_keywords)
    allowed = social | _lexicon_tokens(noise_keywords) | AFFIRMATION_GLUE
    return all(t in allowed for t in tokens) and any(t in social
                                                     for t in tokens)

def firing_keywords(text, category, keywords):
    """Every keyword that counts for the category, in lexicon order: non-risky
    words and multi-word entries always count (risky multi-word entries and
    category-blocked categories excepted); risky single words only with a
    corroborator in the text. Short keywords match only on word boundaries.
    meta_noise has its own dominance gate and is not keyword machinery."""
    if category == "meta_noise":
        return []
    # round-4 category blockers: a marker token switches the whole category
    # off unless an unblocking token co-occurs (keyword_present rules apply,
    # so تابش matches "#تابش" / "تابش،" but not the inside of کتابش)
    blockers, unblockers = CATEGORY_BLOCKERS.get(category, ((), ()))
    if (blockers
            and any(keyword_present(text, normalize_digits(b).lower())
                    for b in blockers)
            and not any(keyword_present(text, normalize_digits(u).lower())
                        for u in unblockers)):
        return []
    risky = RISKY_WORDS.get(category, {})
    multiword_risky = MULTIWORD_RISKY.get(category, {})
    fired = []
    for kw in keywords:
        nk = normalize_digits(kw).lower()
        if not keyword_present(text, nk):
            continue
        if " " in nk:
            # multi-word entries are never single-word risky, but a few are
            # risky as entries (bare venue lines) and need their own anchor
            corroborators = multiword_risky.get(nk)
            if corroborators is None or any(
                    c != nk and keyword_present(text, normalize_digits(c).lower())
                    for c in corroborators):
                fired.append(nk)
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
    # round 4: a forwarded photo with no text is a rebroadcast, not a member
    # sharing a picture — keep it media_outreach alone (message10410)
    if not text and media and "photo" in media and not rec.get("forwarded_from"):
        cats.append("community_social"); method = method or "rule"
    # empty text + no media + not forwarded -> fallback category, never topical
    if not text.strip() and not media and not rec.get("forwarded_from"):
        cats.append("meta_noise"); method = method or "rule"

    # Layer 2 - lexicon (multi-label, corroboration-gated for risky words)
    lex_hits = [c for c in RULE_ORDER
                if category_hit(text, c, lexicon.get(c, []))]
    # round 4: affirmation-only texts (lexicon social word + emoji/glue only)
    # are phatic reactions -> meta_noise, not community_social
    if "community_social" in lex_hits and affirmation_only_text(
            text, lexicon.get("community_social", []),
            lexicon.get("meta_noise", [])):
        lex_hits.remove("community_social")
        if "meta_noise" not in lex_hits:
            lex_hits.append("meta_noise")
    # round 4: generic greeting words must not append community_social onto
    # substantive (>100 char) texts that already carry another category
    elif "community_social" in lex_hits and len(text) > SUBSTANTIVE_TEXT_MIN:
        fired = firing_keywords(text, "community_social",
                                lexicon.get("community_social", []))
        others = [c for c in cats + lex_hits if c != "community_social"]
        if fired and set(fired) <= GENERIC_SOCIAL_WORDS and others:
            lex_hits.remove("community_social")
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
