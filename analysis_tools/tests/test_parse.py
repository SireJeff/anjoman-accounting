from pathlib import Path
from analysis_tools.parse_exports import parse_file, parse_timestamp

FIX = Path(__file__).parent / "fixtures"

def test_parse_timestamp():
    ts, tz = parse_timestamp('title="21.07.2025 14:30:05 UTC+03:30"')
    assert (ts.year, ts.month, ts.day, ts.hour, ts.minute) == (2025, 7, 21, 14, 30)
    assert tz == "UTC+03:30"

def test_plain_fixture_parses():
    msgs = parse_file(FIX / "plain.html", "test")
    assert len(msgs) >= 1
    m = [x for x in msgs if not x["is_service"]][0]
    assert m["message_id"].startswith("message")
    assert m["timestamp"] is not None
    assert isinstance(m["text_plain"], str)

def test_forwarded_fixture_has_origin():
    msgs = parse_file(FIX / "forwarded.html", "test")
    fwd = [x for x in msgs if x["forwarded_from"]]
    assert fwd, "expected at least one forwarded message with a non-empty origin"

def test_service_messages_flagged():
    # service messages (joins, pins) must be flagged, not crash the parser
    msgs = parse_file(FIX / "plain.html", "test")
    assert all(isinstance(m["is_service"], bool) for m in msgs)
