from analysis_tools.correlate import thread_events

def _threads(*specs):
    base = {"chats": [], "anchor_dates": [], "tx_ids": []}
    return {"threads": [{**base, **s} for s in specs]}

def test_thread_summary_and_lag():
    recs = [
        {"chat": "private_group", "message_id": "m1", "timestamp": "2026-08-01T10:00:00",
         "text_plain": "برنامه وبینار شبانه", "event_ref": "nightly-webinars", "in_window": True},
        {"chat": "channel", "message_id": "m2", "timestamp": "2026-08-05T12:00:00",
         "text_plain": "وبینار شبکه شریف", "event_ref": "nightly-webinars", "in_window": True},
        {"chat": "channel", "message_id": "m3", "timestamp": "2026-08-09T18:00:00",
         "text_plain": "برگزار شد", "event_ref": "nightly-webinars", "in_window": True},
    ]
    threads = {"threads": [{"event_ref": "nightly-webinars", "title": "وبینارهای شبانه",
                            "keywords": ["وبینار"], "chats": [], "anchor_dates": [], "tx_ids": []}]}
    out = thread_events(recs, threads, tx_rows=[])
    t = out[0]
    assert t["n_messages"] == 3
    assert t["chats"]["channel"]["n"] == 2
    assert t["announcement_lag_days"] == 4  # private planning → first channel mention

def test_explicit_event_ref_wins_over_keyword_fallback():
    # a message carrying an explicit event_ref must not be double-counted into a
    # keyword-matching thread, even when its ref is unknown to the registry
    recs = [
        {"chat": "private_group", "message_id": "m1", "timestamp": "2026-08-01T10:00:00",
         "text_plain": "برنامه وبینار شبانه", "event_ref": "other-event", "in_window": True},
    ]
    threads = _threads(
        {"event_ref": "nightly-webinars", "title": "وبینارهای شبانه", "keywords": ["وبینار"]},
        {"event_ref": "other-event", "title": "رویداد دیگر", "keywords": []},
    )
    out = thread_events(recs, threads, tx_rows=[])
    assert len(out) == 1
    assert out[0]["event_ref"] == "other-event" and out[0]["n_messages"] == 1

def test_keyword_fallback_applies_to_unlabeled_messages():
    recs = [
        {"chat": "channel", "message_id": "m9", "timestamp": "2026-08-02T09:00:00",
         "text_plain": "وبینار شبکه شریف", "in_window": True},
        {"chat": "channel", "message_id": "m10", "timestamp": "2026-08-03T09:00:00",
         "text_plain": "متن بی‌ربط", "in_window": True},
    ]
    threads = _threads(
        {"event_ref": "nightly-webinars", "title": "وبینارهای شبانه", "keywords": ["وبینار"]},
    )
    out = thread_events(recs, threads, tx_rows=[])
    assert len(out) == 1
    assert out[0]["n_messages"] == 1 and out[0]["chats"]["channel"]["n"] == 1

def test_negative_lag_kept_when_channel_mentions_first():
    recs = [
        {"chat": "channel", "message_id": "m1", "timestamp": "2026-08-01T10:00:00",
         "text_plain": "برنامه وبینار شبانه", "event_ref": "e", "in_window": True},
        {"chat": "private_group", "message_id": "m2", "timestamp": "2026-08-04T10:00:00",
         "text_plain": "هماهنگی وبینار", "event_ref": "e", "in_window": True},
    ]
    threads = _threads({"event_ref": "e", "title": "e", "keywords": ["x"]})
    t = thread_events(recs, threads, tx_rows=[])[0]
    assert t["announcement_lag_days"] == -3  # announcement precedes coordination

def test_tx_project_fallback_for_mapped_refs():
    tx_rows = [
        {"id": "TX1", "project": "Summer School 1404", "amount_toman": 100.0},
        {"id": "TX2", "project": "Other", "amount_toman": 5.0},
    ]
    recs = [
        {"chat": "private_group", "message_id": "m1", "timestamp": "2026-08-01T10:00:00",
         "text_plain": "مدرسه تابستانه", "event_ref": "summer-school-1404", "in_window": True},
    ]
    threads = _threads({"event_ref": "summer-school-1404", "title": "مدرسه تابستانه ۱۴۰۴",
                        "keywords": ["مدرسه تابستانه"]})
    t = thread_events(recs, threads, tx_rows=tx_rows)[0]
    assert t["tx_ids"] == ["TX1"]
    assert t["tx_total_toman"] == 100.0
