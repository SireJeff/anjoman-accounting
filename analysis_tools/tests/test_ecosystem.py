"""Task 10: ecosystem graph (forwards, mentions, seed validation, joined back-fill)."""
import json

from analysis_tools.common import ROOT
from analysis_tools.ecosystem import backfill_joined_forwards, build


def test_forward_edge_and_seed_node():
    msgs = [{"chat": "channel", "forwarded_from": "نشریه‌ی شباهنگ", "text_plain": ""},
            {"chat": "private_group", "forwarded_from": None, "text_plain": "ببین https://t.me/sharifastronomy"}]
    g = build(msgs)
    ids = {n["id"] for n in g["nodes"]}
    assert "shabahang_sut" in ids and "sharifastronomy" in ids
    edges = {(e["source"], e["target"], e["type"]) for e in g["edges"]}
    assert ("channel_export", "shabahang_sut", "forward") in edges
    assert ("private_group_export", "sharifastronomy", "mention") in edges


def test_external_origin_becomes_node():
    g = build([{"chat": "channel", "forwarded_from": "انجمن بلور شریف", "text_plain": ""}])
    assert any(n["type"] == "external" for n in g["nodes"])


def test_summerschool_export_node_present():
    # controller delta 1: five export chats, summerschool included
    g = build([{"chat": "summerschool_channel", "forwarded_from": None,
                "text_plain": "https://t.me/sutschools"}])
    ids = {n["id"] for n in g["nodes"]}
    assert "summerschool_channel_export" in ids
    edges = {(e["source"], e["target"], e["type"]) for e in g["edges"]}
    assert ("summerschool_channel_export", "sutschools", "mention") in edges


def test_joined_forward_inherits_origin():
    # controller delta 2: a label-less forward (joined block, no sender) directly
    # following a labelled forward in the same chat inherits its origin
    msgs = [{"chat": "channel", "forwarded_from": "نشریه‌ی شباهنگ",
             "sender": "Poster", "text_plain": ""},
            {"chat": "channel", "forwarded_from": None,
             "sender": None, "text_plain": ""}]
    g = build(msgs)
    weights = {(e["source"], e["target"], e["type"]): e["weight"] for e in g["edges"]}
    assert weights[("channel_export", "shabahang_sut", "forward")] == 2


def test_backfill_untouched_by_normal_service_or_chat_boundary():
    msgs = [
        # run head forward (labelled)
        {"chat": "channel", "message_id": "m1", "forwarded_from": "نشریه‌ی شباهنگ",
         "sender": "Poster", "is_service": False, "text_plain": ""},
        # joined label-less forward -> inherits, keeps the run open
        {"chat": "channel", "message_id": "m2", "forwarded_from": None,
         "sender": None, "is_service": False, "text_plain": ""},
        # chained label-less forward -> also inherits
        {"chat": "channel", "message_id": "m3", "forwarded_from": None,
         "sender": None, "is_service": False, "text_plain": ""},
        # normal message with its own run head (sender shown) -> no inherit, closes run
        {"chat": "channel", "message_id": "m4", "forwarded_from": None,
         "sender": "Ali", "is_service": False, "text_plain": "سلام"},
        # sender-less continuation of m4's normal run -> must NOT inherit
        {"chat": "channel", "message_id": "m5", "forwarded_from": None,
         "sender": None, "is_service": False, "text_plain": ""},
        # service message -> never inherits
        {"chat": "channel", "message_id": "m6", "forwarded_from": None,
         "sender": None, "is_service": True, "text_plain": "Ali joined the group"},
        # same shape as a joined forward but in a different chat -> no inherit
        {"chat": "private_group", "message_id": "m7", "forwarded_from": None,
         "sender": None, "is_service": False, "text_plain": ""},
    ]
    filled, stats = backfill_joined_forwards(msgs)
    assert [m["forwarded_from"] for m in filled] == \
        ["نشریه‌ی شباهنگ", "نشریه‌ی شباهنگ", "نشریه‌ی شباهنگ", None, None, None, None]
    assert stats["joined_backfilled"] == 2 and stats["unresolvable"] == 0
    # input records are not mutated
    assert msgs[1]["forwarded_from"] is None and msgs[2]["forwarded_from"] is None


def test_backfill_reduces_nulls_on_real_data():
    # the 40 known label-less joined forwards from the task-4 reconciliation
    # (27 private_group, 11 public_group, 2 accounting_group; 0 elsewhere)
    path = ROOT / "analysis/messages.jsonl"
    msgs = [json.loads(line) for line in open(path, encoding="utf-8")]
    before = sum(1 for m in msgs if m.get("forwarded_from"))
    filled, stats = backfill_joined_forwards(msgs)
    after = sum(1 for m in filled if m.get("forwarded_from"))
    assert before == 1233                       # frozen parse (task 4)
    assert stats["joined_backfilled"] == 40     # exactly the known cases
    assert stats["unresolvable"] == 0
    assert after == 1273                        # 1233 labelled + 40 inherited
