import json
from types import SimpleNamespace

import pytest

from analysis_tools import i18n, translate


def test_validate_ok():
    assert translate.validate("Total {n} rows in `x.csv` (**12**)",
                              "مجموع {n} ردیف در `x.csv` (**12**)") == []


@pytest.mark.parametrize("fa,needle", [
    ("مجموع ردیف", "placeholders"),
    ("مجموع {n} {m} ردیف در `x.csv` (**12**)", "placeholders"),
    ("مجموع {n} ردیف در x.csv (**12**)", "code spans"),
    ("مجموع {n} ردیف در `x.csv` (**۱۳**)", "number tokens"),
    ("مجموع {n} ردیف در `x.csv` (12)", "bold"),
])
def test_validate_rejects(fa, needle):
    probs = translate.validate("Total {n} rows in `x.csv` (**12**)", fa)
    assert any(needle in p for p in probs), probs


def test_validate_edge_whitespace():
    assert any("whitespace" in p for p in translate.validate(" and more", "و بیشتر"))


def test_pending():
    en = {"a": "A", "b": "B", "c": "C"}
    fa = {"a": "الف", "b": "ب"}
    hashes = {"a": i18n.sha("A"), "b": "old"}
    assert translate.pending(en, fa, hashes) == ["b", "c"]


class FakeMessages:
    def __init__(self, script):
        self.script, self.calls = script, []

    def parse(self, **kw):
        payload = json.loads(kw["messages"][0]["content"])
        self.calls.append(payload)
        return self.script(payload)


def _resp(items, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, stop_details=None,
                           parsed_output=translate.Batch(items=[
                               translate.Item(key=k, fa=v) for k, v in items.items()]))


@pytest.fixture
def catdir(tmp_path, monkeypatch):
    (tmp_path / "en.json").write_text(json.dumps(
        {"k1": "One {n}", "k2": "Two `c` 5", "k3": "Three"}), encoding="utf-8")
    (tmp_path / "glossary.json").write_text("{}", encoding="utf-8")
    i18n.set_catalog_dir(tmp_path)
    monkeypatch.setattr(translate, "CACHE", tmp_path / "cache")
    yield tmp_path
    i18n.set_catalog_dir(None)


GOOD = {"k1": "یک {n}", "k2": "دو `c` 5", "k3": "سه"}


def test_run_happy_path_and_cache(catdir):
    msgs = FakeMessages(lambda p: _resp({k: GOOD[k] for k in p["items"]}))
    res = translate.run(SimpleNamespace(messages=msgs), size=2, out_dir=catdir)
    assert res["failed"] == {} and res["translated"] == 3
    fa = json.loads((catdir / "fa.json").read_text(encoding="utf-8"))
    hashes = json.loads((catdir / "hashes.json").read_text(encoding="utf-8"))
    assert fa == GOOD and hashes["k1"] == i18n.sha("One {n}")
    # second run: nothing pending, no API calls
    n_calls = len(msgs.calls)
    i18n.reload()
    translate.run(SimpleNamespace(messages=msgs), size=2, out_dir=catdir)
    assert len(msgs.calls) == n_calls


def test_run_splits_on_truncation(catdir):
    def script(p):
        if len(p["items"]) > 1:
            return _resp({}, stop="max_tokens")
        return _resp({k: GOOD[k] for k in p["items"]})
    msgs = FakeMessages(script)
    res = translate.run(SimpleNamespace(messages=msgs), size=3, out_dir=catdir)
    assert res["failed"] == {}
    assert [len(c["items"]) for c in msgs.calls] == [3, 1, 2, 1, 1]


def test_run_retries_with_notes_then_gives_up(catdir):
    def script(p):
        return _resp({k: ("یک" if k == "k1" else GOOD[k]) for k in p["items"]})
    msgs = FakeMessages(script)
    res = translate.run(SimpleNamespace(messages=msgs), size=3, out_dir=catdir)
    assert list(res["failed"]) == ["k1"]
    assert any("notes" in c and "k1" in c["notes"] for c in msgs.calls)
    assert len([c for c in msgs.calls if "k1" in c["items"]]) == translate.MAX_ATTEMPTS
    fa = json.loads((catdir / "fa.json").read_text(encoding="utf-8"))
    assert "k1" not in fa and fa["k3"] == "سه"


def test_run_drops_orphans(catdir):
    (catdir / "fa.json").write_text(json.dumps({"gone": "x"}), encoding="utf-8")
    (catdir / "hashes.json").write_text(json.dumps({"gone": "h"}), encoding="utf-8")
    i18n.reload()
    msgs = FakeMessages(lambda p: _resp({k: GOOD[k] for k in p["items"]}))
    translate.run(SimpleNamespace(messages=msgs), size=3, out_dir=catdir)
    fa = json.loads((catdir / "fa.json").read_text(encoding="utf-8"))
    assert "gone" not in fa


def test_main_requires_key(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as e:
        translate.main([])
    assert e.value.code == 2 and "ANTHROPIC_API_KEY" in capsys.readouterr().err
