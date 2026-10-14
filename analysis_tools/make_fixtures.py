"""Extract real message blocks into test fixtures. Run once from repo root.

Adapted from the task brief after grepping the real exports:
- private_group/messages.html has no message10/message11; real ids there start at
  message803, so verified ids are used instead (service + reply + plain text).
- forwarded messages do NOT carry a "forwarded" class on the message div (the
  brief's class regex never matches); the marker is an inner
  <div class="forwarded body">, and it sits ~800 chars into the block (beyond
  the brief's 400-char window). We therefore split into message blocks and keep
  the ones containing 'forwarded body'.
"""
import re
from pathlib import Path
from analysis_tools.common import SOURCES

FIX = Path(__file__).parent / "tests/fixtures"
HEAD = """<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>"""
TAIL = "</body></html>"

def grab(html_path: Path, want_ids: list[str]) -> str:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    blocks = []
    for mid in want_ids:
        m = re.search(rf'<div class="message[^"]*" id="{mid}".*?(?=<div class="message |$)', text, re.S)
        if m:
            blocks.append(m.group(0))
    return HEAD + "\n".join(blocks) + TAIL

def forwarded_ids(html_path: Path, count: int = 2) -> list[str]:
    """Ids of the first `count` message blocks containing a 'forwarded body'."""
    text = html_path.read_text(encoding="utf-8", errors="replace")
    ids = []
    for m in re.finditer(r'<div class="message[^"]*" id="(message[-\d]+)".*?(?=<div class="message |$)', text, re.S):
        if "forwarded body" in m.group(0):
            ids.append(m.group(1))
            if len(ids) >= count:
                break
    return ids

if __name__ == "__main__":
    FIX.mkdir(parents=True, exist_ok=True)
    # service + reply + plain-text messages from the private group (ids verified by grep)
    (FIX / "plain.html").write_text(
        grab(SOURCES["private_group"] / "messages.html",
             ["message803", "message804", "message806"]),
        encoding="utf-8")
    # forwarded messages, from the channel (found by scanning for 'forwarded body')
    chan_file = SOURCES["channel"] / "messages3.html"
    ids = forwarded_ids(chan_file)
    (FIX / "forwarded.html").write_text(grab(chan_file, ids), encoding="utf-8")
    print("fixtures written; inspect them and adjust test expectations if needed")
