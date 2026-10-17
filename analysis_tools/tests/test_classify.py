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


# --- Task 14 round 2: word-boundary matching for short (<=5 char) keywords ---

BOUNDARY_LEX = {"education_courses": ["لتک", "مدرس"],
                "meta_noise": ["باشه", "آره", "اوکی", "😂", "👍"],
                "community_social": ["ممنون"]}

def test_caltech_word_does_not_match_latex_keyword():
    r = classify_message({"chat": "x",
                          "text_plain": "دکترای خود را در دانشگاه کلتک به پایان رساند",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "education_courses" not in r["categories"]

def test_standalone_latex_keyword_still_matches():
    r = classify_message({"chat": "x", "text_plain": "لتک ابزار اصلی آکادمیک است",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "education_courses" in r["categories"]

def test_okay_suffix_word_does_not_match_oki():
    r = classify_message({"chat": "x",
                          "text_plain": "همینجا هم لایک کنید اوکیه",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "meta_noise" not in r["categories"]

def test_zwnj_compound_does_not_match_bashe():
    # می‌باشه = می + ZWNJ + باشه; ZWNJ is a word char, so باشه is not standalone
    r = classify_message({"chat": "x", "text_plain": "نتیجه قابل توجه می‌باشه",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "meta_noise" not in r["categories"]

def test_schools_word_does_not_match_instructor_keyword():
    r = classify_message({"chat": "x", "text_plain": "مدارس موضوعی انجمن علمی",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "education_courses" not in r["categories"]

def test_affirmation_inside_word_does_not_match_areh():
    r = classify_message({"chat": "x", "text_plain": "این کشور آرهایی بزرگ دارد",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "meta_noise" not in r["categories"]

def test_substantive_message_with_affirmation_not_noise():
    r = classify_message({"chat": "x", "text_plain": "باشه انجامش میدم",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "meta_noise" not in r["categories"]

def test_standalone_affirmation_is_noise():
    r = classify_message({"chat": "x", "text_plain": "باشه", "media_kinds": []},
                         BOUNDARY_LEX)
    assert r["categories"] == ["meta_noise"] and r["method"] == "lexicon"

def test_affirmation_plus_emoji_only_is_noise():
    r = classify_message({"chat": "x", "text_plain": "آره 👍", "media_kinds": []},
                         BOUNDARY_LEX)
    assert "meta_noise" in r["categories"]

def test_emoji_inside_substantive_message_not_noise():
    r = classify_message({"chat": "x",
                          "text_plain": "جلسه فردا ساعت ۵ برگزار می‌شود 😂",
                          "media_kinds": []}, BOUNDARY_LEX)
    assert "meta_noise" not in r["categories"]


# --- Task 14 round 2: extended corroboration for polysemous tokens ---

RISKY2_LEX = {"governance_decisions": ["جلسه"], "website_tech": ["دامنه"],
              "finance_operations": ["گردش", "پرداخت"],
              "publications_shabahng": ["تکانه"]}

def test_jalse_on_course_session_ad_not_governance():
    r = classify_message({"chat": "x",
                          "text_plain": "عنوان جلسه: نمایش اسپینوری گروه لورنتس",
                          "media_kinds": []}, RISKY2_LEX)
    assert "governance_decisions" not in r["categories"]

def test_jalse_with_board_token_is_governance():
    r = classify_message({"chat": "x", "text_plain": "جلسه هیئت مدیره فردا است",
                          "media_kinds": []}, RISKY2_LEX)
    assert "governance_decisions" in r["categories"]

def test_damne_as_amplitude_not_website():
    r = classify_message({"chat": "x", "text_plain": "دامنه موج ذره را حساب کرد",
                          "media_kinds": []}, RISKY2_LEX)
    assert "website_tech" not in r["categories"]

def test_damne_with_server_token_is_website():
    r = classify_message({"chat": "x", "text_plain": "دامنه سرور را تمدید کن",
                          "media_kinds": []}, RISKY2_LEX)
    assert "website_tech" in r["categories"]

def test_gardesh_physics_flux_not_finance():
    r = classify_message({"chat": "x",
                          "text_plain": "جریان گردش تابشی در جو خورشید",
                          "media_kinds": []}, RISKY2_LEX)
    assert "finance_operations" not in r["categories"]

def test_gardesh_with_account_token_is_finance():
    r = classify_message({"chat": "x", "text_plain": "گردش حساب این ماه را بفرست",
                          "media_kinds": []}, RISKY2_LEX)
    assert "finance_operations" in r["categories"]

def test_takkane_chatter_not_publications():
    r = classify_message({"chat": "x", "text_plain": "چیزای تکانه رو گذاشته",
                          "media_kinds": []}, RISKY2_LEX)
    assert "publications_shabahng" not in r["categories"]

def test_takkane_with_journal_token_is_publications():
    r = classify_message({"chat": "x", "text_plain": "شماره جدید نشریه تکانه آمد",
                          "media_kinds": []}, RISKY2_LEX)
    assert "publications_shabahng" in r["categories"]

def test_payment_verb_form_not_finance():
    r = classify_message({"chat": "x",
                          "text_plain": "بچه‌ها حق عضویت را پرداخته‌اند",
                          "media_kinds": []}, RISKY2_LEX)
    assert "finance_operations" not in r["categories"]

def test_confirmed_payment_is_finance():
    r = classify_message({"chat": "x", "text_plain": "حق الزحمه پرداخت شد",
                          "media_kinds": []}, RISKY2_LEX)
    assert "finance_operations" in r["categories"]


# --- Task 14 round 2: deterministic demotion of micro-message LLM labels ---

def test_demote_bare_number_llm_event_label():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="180", media=[])]
    labels = {"a#m1": {"categories": ["events"], "confidence": 0.6}}
    apply_llm_labels(recs, labels)
    assert recs[0]["categories"] == ["community_social"]
    assert recs[0]["method"] == "llm" and recs[0]["confidence"] == 0.5

def test_demote_empty_voice_llm_website_label():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="", media=["voice"])]
    labels = {"a#m1": {"categories": ["website_tech"], "confidence": 0.6}}
    apply_llm_labels(recs, labels)
    assert recs[0]["categories"] == ["meta_noise"]
    assert recs[0]["confidence"] == 0.5

def test_high_confidence_short_topical_label_not_demoted():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="180", media=[])]
    labels = {"a#m1": {"categories": ["events"], "confidence": 0.8}}
    apply_llm_labels(recs, labels)
    assert recs[0]["categories"] == ["events"] and recs[0]["confidence"] == 0.8

def test_low_confidence_short_community_label_unchanged():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="یپ", media=[])]
    labels = {"a#m1": {"categories": ["community_social"], "confidence": 0.6}}
    apply_llm_labels(recs, labels)
    assert recs[0]["categories"] == ["community_social"]
    assert recs[0]["confidence"] == 0.6

def test_demotion_preserves_event_ref_and_decision():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="فقط جناب", media=[])]
    labels = {"a#m1": {"categories": ["coordination_logistics"],
                       "confidence": 0.55, "is_decision": True,
                       "event_ref": "yalda-1404"}}
    apply_llm_labels(recs, labels)
    assert recs[0]["categories"] == ["community_social"]
    assert recs[0]["event_ref"] == "yalda-1404" and recs[0]["is_decision"] is True

def test_demotion_never_touches_rule_or_lexicon_labels():
    from analysis_tools.classify import demote_micro_message
    r = _rec("m1", method="rule", confidence=0.9, text="",
             categories=["governance_decisions"])
    assert demote_micro_message(r) is False
    assert r["categories"] == ["governance_decisions"]
    r2 = _rec("m2", method="lexicon", confidence=0.7, text="180",
              categories=["events"])
    assert demote_micro_message(r2) is False
    assert r2["categories"] == ["events"]


# --- Task 14 round 3: publications/governance lexicon surgery ---

def test_round3_pruned_entries_stay_out_of_lexicon():
    from analysis_tools.common import ROOT, read_json
    lex = read_json(ROOT / "analysis/lexicon.json")
    assert "گروه نجوم" not in lex["publications_shabahng"]
    assert "مقیمی" not in lex["governance_decisions"]
    assert "گزارش" not in lex["governance_decisions"]
    assert "شماره" in lex["publications_shabahng"]   # journal anchor kept

PUB3_LEX = {"publications_shabahng": ["شباهنگ", "تکانه", "شماره", "ویراستاری",
                                      "جلد", "نشریه"]}

def test_shabheng_brand_hashtag_not_publications():
    # channel#message3477/3484 pattern: #شباهنگ hashtag in a news footer
    r = classify_message({"chat": "channel",
                          "text_plain": "تلسکوپ فضایی نانسی گریس رومن #شباهنگ #نجوم #اخترفیزیک",
                          "media_kinds": []}, PUB3_LEX)
    assert "publications_shabahng" not in r["categories"]

def test_journal_issue_with_number_anchor_is_publications():
    # channel#message3324 pattern: شماره‌ی نشریه‌ی #شباهنگ + این شماره
    r = classify_message({"chat": "channel",
                          "text_plain": "بیست و یکمین شماره‌ی نشریه‌ی #شباهنگ منتشر شد! این شماره درباره DESI",
                          "media_kinds": []}, PUB3_LEX)
    assert "publications_shabahng" in r["categories"]

def test_editing_credit_line_not_publications():
    # channel#message3106/3115 pattern: ویراستاری in production credits
    r = classify_message({"chat": "channel",
                          "text_plain": "با تشکر از خانم ملکی جهت کمک در ویراستاری علمی متن #جمعه_های_کوانتومی",
                          "media_kinds": []}, PUB3_LEX)
    assert "publications_shabahng" not in r["categories"]

def test_textbook_volume_not_publications():
    # channel#message3420 pattern: جلد دوم هالیدی is a textbook volume
    r = classify_message({"chat": "channel",
                          "text_plain": "جمع‌وجور حسابی از مطالب فصل‌های ۲۸ تا ۳۳ هالیدی (جلد دوم) آماده شد",
                          "media_kinds": []}, PUB3_LEX)
    assert "publications_shabahng" not in r["categories"]

def test_journal_name_chatter_not_publications():
    # private_group#message9825 pattern: اسم تکانه و شباهنگ نیست اینجا
    r = classify_message({"chat": "private_group",
                          "text_plain": "اسم تکانه و شباهنگ نیست اینجا",
                          "media_kinds": []}, PUB3_LEX)
    assert "publications_shabahng" not in r["categories"]

GOV3_LEX = {"governance_decisions": ["جلسه", "کمیته", "انتخابات", "تصمیم",
                                     "هیئت مدیره"]}

def test_bare_decision_prose_not_governance():
    # channel#message3420 pattern: انجمن تصمیم گرفتیم in an announcement ad
    r = classify_message({"chat": "channel",
                          "text_plain": "ما توی انجمن علمی فیزیک تصمیم گرفتیم یه جمع‌وجور آماده کنیم",
                          "media_kinds": []}, GOV3_LEX)
    assert "governance_decisions" not in r["categories"]

def test_board_decision_is_governance():
    r = classify_message({"chat": "x",
                          "text_plain": "هیئت مدیره تصمیم گرفت جلسات را ادامه دهد",
                          "media_kinds": []}, GOV3_LEX)
    assert "governance_decisions" in r["categories"]

def test_committee_meeting_keeps_governance():
    # private_group#message9875/12513 pattern: جلسه کمیته — کمیته fires,
    # the risky جلسه stays corroborator-gated (TP preserved)
    r = classify_message({"chat": "private_group",
                          "text_plain": "دوستان فردا جلسه کمیته دانشکدست نکته‌ای هست که بپرسید؟",
                          "media_kinds": []}, GOV3_LEX)
    assert "governance_decisions" in r["categories"]

def test_standalone_election_is_governance():
    # private_group#message10342: انتخابات is an unambiguous anchor
    r = classify_message({"chat": "x", "text_plain": "انتخابات رو من اصلا نیستم",
                          "media_kinds": []}, GOV3_LEX)
    assert "governance_decisions" in r["categories"]

FIN3_LEX = {"finance_operations": ["اسپانسر", "برداشت", "تومان", "حساب"]}

def test_bare_sponsor_chatter_not_finance():
    # public_group#message1289/3246/2541 pattern
    r = classify_message({"chat": "public_group",
                          "text_plain": "حالا باید دید اسپانسر چی میشه",
                          "media_kinds": []}, FIN3_LEX)
    assert "finance_operations" not in r["categories"]

def test_sponsor_with_money_token_is_finance():
    r = classify_message({"chat": "x",
                          "text_plain": "اسپانسر قرار شد پنج میلیون تومان واریز کنه",
                          "media_kinds": []}, FIN3_LEX)
    assert "finance_operations" in r["categories"]

def test_interpretation_bardasht_not_finance():
    # channel#message3115 pattern: برداشت = interpretation in a physics essay
    r = classify_message({"chat": "channel",
                          "text_plain": "این برداشت دقیق نیست؛ نتیجه اندازه‌گیری احتمالی است",
                          "media_kinds": []}, FIN3_LEX)
    assert "finance_operations" not in r["categories"]

def test_withdrawal_with_money_token_is_finance():
    r = classify_message({"chat": "x",
                          "text_plain": "برداشت دویست هزار تومان از حساب ثبت شد",
                          "media_kinds": []}, FIN3_LEX)
    assert "finance_operations" in r["categories"]


# --- Task 14 round 3: multi-label gating on broadcasts ---

GATE_LEX = {"events": ["سمینار", "وبینار"],
            "finance_operations": ["پرداخت"],
            "governance_decisions": ["جلسه", "انتخابات"]}

def _broadcast(fwd=True, chat="channel"):
    return {"chat": chat, "text_plain": "سمینار وبینار فیزیک؛ پرداخت حق ثبت نام تومان",
            "media_kinds": [], "forwarded_from": "کانال" if fwd else None}

def test_broadcast_drops_weak_secondary_label():
    # events fires on two keywords (strong); finance only on the risky
    # پرداخت (corroborated by تومان) — dropped on a broadcast
    r = classify_message(_broadcast(), GATE_LEX)
    assert "events" in r["categories"]
    assert "finance_operations" not in r["categories"]

def test_non_broadcast_keeps_weak_secondary_label():
    r = classify_message(_broadcast(fwd=False, chat="private_group"), GATE_LEX)
    assert set(r["categories"]) >= {"events", "finance_operations"}

def test_channel_origin_post_is_gated_even_without_forward():
    r = classify_message(_broadcast(fwd=False, chat="channel"), GATE_LEX)
    assert "events" in r["categories"]
    assert "finance_operations" not in r["categories"]

def test_broadcast_all_weak_keeps_all_labels():
    # no strongly supported category -> drop nothing (never empty the post)
    lex = {"governance_decisions": ["جلسه"],
           "finance_operations": ["پرداخت"]}
    r = classify_message({"chat": "channel",
                          "text_plain": "جلسه انتخابات پرداخت تومان",
                          "media_kinds": [], "forwarded_from": "کانال"}, lex)
    assert set(r["categories"]) == {"governance_decisions", "finance_operations"}

def test_broadcast_rule_labels_never_dropped():
    # poll rule label has no keyword evidence -> never weak -> survives
    r = classify_message({"chat": "channel",
                          "text_plain": "سمینار وبینار فیزیک",
                          "media_kinds": ["poll"]}, GATE_LEX)
    assert "governance_decisions" in r["categories"]
    assert "events" in r["categories"]


# --- Task 14 round 3: demotion window extended to 25 chars without evidence ---

def test_demote_medium_fragment_without_evidence():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="اسمش یادم رفته الان دقیقا", media=[])]  # 24 chars
    labels = {"a#m1": {"categories": ["events"], "confidence": 0.6}}
    apply_llm_labels(recs, labels, lexicon={"events": ["سمینار"]})
    assert recs[0]["categories"] == ["community_social"]
    assert recs[0]["confidence"] == 0.5

def test_medium_fragment_with_corroborator_not_demoted():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="کلاس فرداست حتما بیا", media=[])]  # 19 chars
    labels = {"a#m1": {"categories": ["education_courses"], "confidence": 0.6}}
    apply_llm_labels(recs, labels, lexicon={"education_courses": ["پایتون"]})
    assert recs[0]["categories"] == ["education_courses"]
    assert recs[0]["confidence"] == 0.6

def test_fragment_over_25_chars_not_demoted():
    from analysis_tools.classify import apply_llm_labels
    recs = [_rec("m1", text="فکر نکنم بتونیم الان مکانیزمی دراریم", media=[])]  # 36 chars
    labels = {"a#m1": {"categories": ["website_tech"], "confidence": 0.6}}
    apply_llm_labels(recs, labels, lexicon={"website_tech": ["سرور"]})
    assert recs[0]["categories"] == ["website_tech"]
