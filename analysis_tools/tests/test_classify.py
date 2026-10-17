from analysis_tools.classify import classify_message

LEX = {"education_courses": ["مدرسه تابستانه"], "events": ["وبینار"],
       "publications_shabahang": ["شباهنگ"], "finance_operations": ["تومان"],
       "meta_noise": ["ok"]}

def test_lexicon_hit():
    r = classify_message({"chat": "x", "text_plain": "ثبت‌نام مدرسه تابستانه شروع شد", "media_kinds": []}, LEX)
    assert r["categories"] == ["education_courses"] and r["method"] == "lexicon"

def test_structural_poll_is_governance():
    r = classify_message({"chat": "x", "text_plain": "", "media_kinds": ["poll"]}, LEX)
    assert "governance_decisions" in r["categories"] and r["method"] == "rule"

def test_form_link_is_outreach_or_education():
    r = classify_message({"chat": "x", "text_plain": "فرم همکاری https://docs.google.com/forms/d/e/xyz", "media_kinds": []}, LEX)
    assert r["categories"] and r["method"] == "rule"

def test_unclassified():
    r = classify_message({"chat": "x", "text_plain": "hghk ldhn", "media_kinds": []}, LEX)
    assert r["method"] is None and r["categories"] == []

def test_multilabel():
    r = classify_message({"chat": "x", "text_plain": "هزینه بلیت وبینار چند تومان شد", "media_kinds": []}, LEX)
    assert set(r["categories"]) >= {"events", "finance_operations"}


# --- Task 14: corroboration rules for high-ambiguity (risky) lexicon words ---

RISKY_LEX = {"finance_operations": ["حساب", "رسید", "تخفیف", "حق‌الزحمه", "تومان"],
             "education_courses": ["ثبت‌نام", "کارگاه", "دوره api"],
             "website_tech": ["سایت", "alenush"]}

def test_risky_hesab_verb_form_not_finance():
    r = classify_message({"chat": "x", "text_plain": "حساب کردم ساعت ها رو",
                          "media_kinds": []}, RISKY_LEX)
    assert "finance_operations" not in r["categories"]

def test_corroborated_resid_is_finance():
    r = classify_message({"chat": "x", "text_plain": "حق‌الزحمه رسید",
                          "media_kinds": []}, RISKY_LEX)
    assert "finance_operations" in r["categories"]

def test_registration_with_workshop_is_education():
    r = classify_message({"chat": "x", "text_plain": "ثبت‌نام کارگاه پایتون",
                          "media_kinds": []}, RISKY_LEX)
    assert "education_courses" in r["categories"]

def test_risky_site_without_corroborator_not_website():
    r = classify_message({"chat": "x", "text_plain": "سایت تلگرام خرابه",
                          "media_kinds": []}, RISKY_LEX)
    assert "website_tech" not in r["categories"]

def test_corroborated_hesab_is_finance():
    r = classify_message({"chat": "x", "text_plain": "حساب ۲۰۰ تومن شارژ شد",
                          "media_kinds": []}, RISKY_LEX)
    assert "finance_operations" in r["categories"]

def test_risky_takhfif_ad_without_money_not_finance():
    r = classify_message({"chat": "x", "text_plain": "۱۵٪ تخفیف ویژه دانشجویان",
                          "media_kinds": []}, RISKY_LEX)
    assert "finance_operations" not in r["categories"]

def test_multiword_entry_containing_risky_word_still_counts():
    # "دوره api" is a multi-word entry -> never risky, fires on its own
    r = classify_message({"chat": "x", "text_plain": "دوره api شروع شد",
                          "media_kinds": []}, RISKY_LEX)
    assert "education_courses" in r["categories"]

def test_empty_no_media_not_forwarded_is_meta_noise():
    r = classify_message({"chat": "x", "text_plain": "", "media_kinds": []}, RISKY_LEX)
    assert r["categories"] == ["meta_noise"] and r["method"] == "rule"

def test_empty_forwarded_stays_media_outreach_not_meta_noise():
    r = classify_message({"chat": "x", "text_plain": "", "media_kinds": [],
                          "forwarded_from": "some_channel"}, RISKY_LEX)
    assert "media_outreach" in r["categories"]
    assert "meta_noise" not in r["categories"]


# --- Task 7: LLM residual emission and label application ---

def _rec(mid, chat="a", in_window=True, is_service=False, method=None,
         confidence=0.0, text="تست", media=None, month="1404/05",
         is_decision=False, categories=None, event_ref=None):
    return {"chat": chat, "message_id": mid, "in_window": in_window,
            "is_service": is_service, "method": method, "confidence": confidence,
            "text_plain": text, "media_kinds": media or [],
            "jalali_month": month, "categories": categories or [],
            "event_ref": event_ref, "is_decision": is_decision}

def test_select_residual_picks_unclassified_and_low_confidence():
    from analysis_tools.classify import select_residual
    recs = [
        _rec("m1"),                                        # unclassified -> residual
        _rec("m2", method="lexicon", confidence=0.7),      # conf == 0.7 -> kept out
        _rec("m3", method="lexicon", confidence=0.55),     # low confidence -> residual
        _rec("m4", method="rule", confidence=0.9),         # confident -> kept out
        _rec("m5", in_window=False),                       # out of window -> kept out
        _rec("m6", is_service=True),                       # service message -> kept out
    ]
    assert [r["message_id"] for r in select_residual(recs)] == ["m1", "m3"]

def test_build_batches_shapes_items_and_truncates_text():
    from analysis_tools.classify import build_batches
    recs = [_rec(f"m{i}", chat="c", text="ع" * 600, media=["photo"]) for i in range(5)]
    batches = build_batches(recs, batch_size=2)
    assert [b["batch"] for b in batches] == [1, 2, 3]
    assert [len(b["items"]) for b in batches] == [2, 2, 1]
    item = batches[0]["items"][0]
    assert item["key"] == "c#m0" and item["chat"] == "c"
    assert item["month"] == "1404/05" and item["media"] == ["photo"]
    assert len(item["text"]) == 500          # truncated to 500 chars
    assert item["text"] == "ع" * 500

def test_apply_llm_labels_merges_and_respects_confidence_gate():
    from analysis_tools.classify import apply_llm_labels
    recs = [
        _rec("m1"),                                                    # unclassified
        _rec("m2", method="lexicon", confidence=0.55, categories=["events"],
             is_decision=True),                                        # low confidence
        _rec("m3", method="lexicon", confidence=0.7, categories=["events"]),  # at gate
        _rec("m4"),                                                    # empty-categories label
        _rec("m5"),                                                    # no label at all
    ]
    labels = {
        "a#m1": {"categories": ["finance_operations"], "is_decision": True,
                 "event_ref": "yalda-1404", "confidence": 0.8},
        "a#m2": {"categories": ["meta_noise"], "is_decision": False,
                 "event_ref": "summer-school-1404", "confidence": 0.75},
        "a#m3": {"categories": ["meta_noise"], "is_decision": True,
                 "event_ref": "booths-1404", "confidence": 0.9},
        "a#m4": {"categories": [], "is_decision": True,
                 "event_ref": "intro-event-1405", "confidence": 0.6},
    }
    n = apply_llm_labels(recs, labels)
    assert n == 2                                       # only m1 and m2 got categories
    # unclassified record fully relabeled
    assert recs[0]["categories"] == ["finance_operations"]
    assert recs[0]["method"] == "llm" and recs[0]["confidence"] == 0.8
    assert recs[0]["event_ref"] == "yalda-1404" and recs[0]["is_decision"] is True
    # low-confidence record overwritten
    assert recs[1]["categories"] == ["meta_noise"] and recs[1]["method"] == "llm"
    assert recs[1]["event_ref"] == "summer-school-1404"
    assert recs[1]["is_decision"] is True               # sticky true
    # record already at confidence 0.7 untouched
    assert recs[2]["categories"] == ["events"] and recs[2]["method"] == "lexicon"
    assert recs[2]["event_ref"] is None and recs[2]["is_decision"] is False
    # empty categories: no method bump / count, but decision + event_ref applied
    assert recs[3]["method"] is None and recs[3]["categories"] == []
    assert recs[3]["event_ref"] == "intro-event-1405" and recs[3]["is_decision"] is True
    # unlabeled record untouched
    assert recs[4]["method"] is None and recs[4]["event_ref"] is None
