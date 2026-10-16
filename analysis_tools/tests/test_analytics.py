"""Task 9: monthly (Jalali) x hourly analytics + mechanics detection."""
from analysis_tools.correlate import (detect_mechanics, event_start_times,
                                      extract_time_mentions, hour_histogram,
                                      monthly_activity, monthly_cashflow,
                                      thread_events)


def test_monthly_activity_buckets():
    recs = [{"chat": "channel", "jalali_month": "1404/05", "in_window": True,
             "is_service": False, "categories": ["events"], "hour": 13},
            {"chat": "channel", "jalali_month": "1404/05", "in_window": False,
             "is_service": False, "categories": ["events"], "hour": 1}]
    ma = monthly_activity(recs)
    assert ma["1404/05"]["channel"]["events"] == 1  # out-of-window excluded


def test_monthly_cashflow_from_ledger_rows():
    tx = [{"period_jalali": "1404/05", "direction": "Receipt", "amount_toman": 33642000.0, "category": "Course fees", "project": "Summer School 1404"},
          {"period_jalali": "1404/05", "direction": "Payment", "amount_toman": 3000000.0, "category": "Teaching", "project": "Summer School 1404"}]
    mc = monthly_cashflow(tx)
    assert mc["1404/05"]["Receipts"] == 33642000.0
    assert mc["1404/05"]["by_category"]["Teaching"] == 3000000.0


def test_monthly_cashflow_shape():
    tx = [{"period_jalali": "1404/07", "direction": "Payment", "amount_toman": 1052375.0,
           "category": "Hospitality", "project": "Professors assembly Mehr"},
          {"period_jalali": "1404/07", "direction": "Receipt", "amount_toman": 500000.0,
           "category": "Donations", "project": "Professors assembly Mehr"}]
    m = monthly_cashflow(tx)["1404/07"]
    assert set(m) == {"Receipts", "Payments", "by_category", "by_project"}
    assert m["Receipts"] == 500000.0 and m["Payments"] == 1052375.0
    # by_category / by_project total both directions
    assert m["by_category"]["Donations"] == 500000.0
    assert m["by_project"]["Professors assembly Mehr"] == 1552375.0


def test_monthly_cashflow_undated_rows_bucketed_as_unknown():
    # TX0060/TX0096 in the real ledger have no period_jalali at all
    tx = [{"period_jalali": None, "direction": "Payment", "amount_toman": 1664700.0,
           "category": "Hospitality", "project": "Yalda 1404"}]
    mc = monthly_cashflow(tx)
    assert mc["unknown"]["Payments"] == 1664700.0
    assert mc["unknown"]["by_project"]["Yalda 1404"] == 1664700.0


def test_hour_histogram():
    hh = hour_histogram([{"chat": "c", "hour": 13, "in_window": True, "is_service": False},
                         {"chat": "c", "hour": 13, "in_window": True, "is_service": False}])
    assert hh["c"][13] == 2


def test_extract_time_mentions_persian_digits():
    assert extract_time_mentions("ساعت ۱۷:۰۰ شروع می‌شود") == ["17:00"]
    assert extract_time_mentions("13:30 و 14:00") == ["13:30", "14:00"]
    assert extract_time_mentions("بدون ساعت") == []
    # colloquial hour without minutes is NOT collected (literal mentions only)
    assert extract_time_mentions("ساعت ۳") == []


def test_event_start_times_channel_or_events_labels_only():
    recs = [
        {"chat": "channel", "timestamp": "2026-08-01T10:00:00",
         "text_plain": "ساعت ۱۷:۰۰", "event_ref": "e", "in_window": True},
        {"chat": "public_group", "timestamp": "2026-08-02T10:00:00",
         "text_plain": "ساعت ۱۳:۳۰", "event_ref": "e", "in_window": True,
         "categories": ["events"]},   # non-channel but events-labelled -> counted
        {"chat": "public_group", "timestamp": "2026-08-03T10:00:00",
         "text_plain": "ساعت ۱۳:۳۰", "event_ref": "e", "in_window": True,
         "categories": []},           # non-channel, no events label -> ignored
        {"chat": "channel", "timestamp": "2026-08-04T10:00:00",
         "text_plain": "۱۳:۳۰", "event_ref": "e", "in_window": True},
    ]
    threads = {"threads": [
        {"event_ref": "e", "title": "e", "keywords": [], "chats": [], "anchor_dates": [], "tx_ids": []},
        {"event_ref": "silent", "title": "s", "keywords": [], "chats": [], "anchor_dates": [], "tx_ids": []},
    ]}
    est = event_start_times(recs, threads)
    assert est == {"e": {"times": ["13:30", "17:00"], "n": 3, "mode": "13:30"}}
    # "silent" has no time mentions -> key absent (n >= 1 only)


def test_money_only_thread_kept_without_messages():
    # real case: professors-assembly-mehr has 4 tx_ids, 2,694,750 toman, no matched messages
    tx_rows = [
        {"id": "TX0019", "project": "Professors assembly Mehr", "amount_toman": 500000.0},
        {"id": "TX0020", "project": "Professors assembly Mehr", "amount_toman": 90000.0},
        {"id": "TX0024", "project": "Professors assembly Mehr", "amount_toman": 1052375.0},
        {"id": "TX0025", "project": "Professors assembly Mehr", "amount_toman": 1052375.0},
    ]
    threads = {"threads": [
        {"event_ref": "professors-assembly-mehr", "title": "Professors assembly Mehr",
         "keywords": ["professors"], "chats": [], "anchor_dates": [],
         "tx_ids": ["TX0019", "TX0020", "TX0024", "TX0025"]},
        {"event_ref": "empty-thread", "title": "no money, no messages",
         "keywords": ["zzz-never-matches"], "chats": [], "anchor_dates": [], "tx_ids": []},
        {"event_ref": "regular", "title": "has messages", "keywords": [],
         "chats": [], "anchor_dates": [], "tx_ids": []},
    ]}
    recs = [{"chat": "channel", "message_id": "m1", "timestamp": "2026-08-01T10:00:00",
             "text_plain": "متن", "event_ref": "regular", "in_window": True}]
    out = {t["event_ref"]: t for t in thread_events(recs, threads, tx_rows)}
    mo = out["professors-assembly-mehr"]
    assert mo["money_only"] is True
    assert mo["first_seen"] is None and mo["last_seen"] is None
    assert mo["n_messages"] == 0 and mo["chats"] == {}
    assert mo["tx_total_toman"] == 2694750.0
    assert mo["announcement_lag_days"] is None and mo["decision_dates"] == []
    assert "empty-thread" not in out            # neither messages nor tx_ids -> dropped
    assert "money_only" not in out["regular"]   # regular threads carry no money_only key
    ordered = thread_events(recs, threads, tx_rows)
    assert ordered[-1]["event_ref"] == "professors-assembly-mehr"  # undated -> last


def test_mechanics_respects_n5_threshold():
    start_times = {"weak": {"times": ["13:30"], "n": 4, "mode": "13:30"},
                   "strong": {"times": ["17:00"], "n": 6, "mode": "17:00"},
                   "nomode": {"times": [], "n": 6, "mode": None}}
    heat = {"chatA": {"شنبه": {13: 4, 14: 1}, "یکشنبه": {9: 5}}}
    mech = detect_mechanics(heat, start_times, tx_rows=[])
    kinds = {(m["kind"], m.get("category")) for m in mech}
    assert ("fixed-slot", "strong") in kinds
    assert ("fixed-slot", "weak") not in kinds     # n=4 < 5
    assert ("fixed-slot", "nomode") not in kinds   # no mode
    peaks = {m["jalali_weekday"]: m for m in mech if m["kind"] == "peak"}
    assert peaks["یکشنبه"]["n"] == 5 and peaks["یکشنبه"]["hour"] == 9
    assert "شنبه" not in peaks                     # max hour there has n=4 < 5


def test_mechanics_tx_hour_from_ledger_message_ids():
    recs = [{"chat": "accounting_group", "message_id": f"message{i}", "hour": 22, "in_window": True}
            for i in range(1, 6)]                   # 5 TX-linked messages at 22:00
    recs += [{"chat": "accounting_group", "message_id": f"message{i}", "hour": 23, "in_window": True}
             for i in range(6, 9)]                  # only 3 at 23:00 -> below threshold
    recs += [{"chat": "channel", "message_id": "message1", "hour": 3, "in_window": True}]
    tx_rows = [{"id": "TX1", "message_ids": "message1; message2; message3"},
               {"id": "TX2", "message_ids": "message4"},
               {"id": "TX3", "message_ids": "message5; message6"},
               {"id": "TX4", "message_ids": "message5; message7; message8"},  # message5 twice: deduped
               {"id": "TX5", "message_ids": ""}]
    mech = detect_mechanics({}, {}, tx_rows, recs)
    tx_hours = [m for m in mech if m["kind"] == "tx-hour"]
    assert len(tx_hours) == 1
    m = tx_hours[0]
    assert m["hour"] == 22 and m["n"] == 5
    assert m["category"] == "accounting_group" and "22:00" in m["note"]
    # channel message1 (hour 3) must never join: only accounting_group resolves
