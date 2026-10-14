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
