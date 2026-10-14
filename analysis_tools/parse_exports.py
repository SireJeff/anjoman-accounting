"""Stage 1: parse Telegram Desktop HTML exports into message records.

XPath notes (adapted from the task brief after inspecting real fixtures in
analysis_tools/tests/fixtures/):
- The per-message timestamp div is class="pull_right date details" — two
  tokens, NOT "date_details" as the brief guessed — so we match divs having
  both "date" and "details". The forwarded-original date inside from_name is a
  <span>, never a div, so div-only matching cannot pick it up by accident.
- Forwarded messages carry a <div class="pull_left forwarded userpic_wrap">
  BEFORE the real origin container <div class="forwarded body">. Matching bare
  contains(@class,"forwarded") hits the userpic wrapper first, so we require
  both "forwarded" and "body".
- The origin name sits in from_name INSIDE the forwarded body, with a nested
  <span class="date details">original date</span> whose text must be excluded.
- sender is the OUTER from_name (who posted in this chat); forwarded_from is
  the INNER from_name (original author). The brief's draft made sender equal
  the forwarded origin, which loses the poster.
- No span[class~="user"] fallback: in these exports the only span classes
  starting with "user" are reaction "userpics", which would pollute the origin
  with avatar initials.
- reply_to hrefs look like "#go_to_message802"; we strip the "go_to_" marker so
  the value matches the message_id format ("message802") for joins.
"""
import re
from datetime import datetime
from pathlib import Path
from lxml import html as lhtml

DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2}):(\d{2})(?:\s*(UTC[+-][\d:]+))?")
MEDIA_CLASSES = ["photo_wrap", "video_file_wrap", "voice_player", "animated_wrap",
                 "sticker_wrap", "media_poll", "document_wrap", "media_audio_player"]

def parse_timestamp(title):
    m = DATE_RE.search(title or "")
    if not m:
        return None, None
    d, mo, y, h, mi, s, tz = m.groups()
    return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s)), tz

def iter_message_files(chat_dir: Path):
    return sorted(chat_dir.glob("messages*.html"))

def _media_kinds(node):
    out = []
    for cls in MEDIA_CLASSES:
        xp = f'.//*[contains(@class,"{cls}")]'
        if node.xpath(xp):
            out.append(cls.replace("_wrap", "").replace("media_", "").replace("_player", ""))
    return out

def _clean(texts):
    return re.sub(r"\s+", " ", " ".join(t.strip() for t in texts if t and t.strip())).strip()

# text nodes of a from_name, excluding the nested original-date span
_FROM_NAME_TEXT = ('.//div[contains(@class,"from_name")]'
                   '//text()[not(ancestor::span[contains(@class,"date")])'
                   ' and not(ancestor::span[contains(@class,"details")])]')

def parse_file(path: Path, chat: str):
    doc = lhtml.parse(str(path))
    records = []
    for msg in doc.xpath('//div[contains(@class,"message")]'):
        mid = msg.get("id", "")
        titles = msg.xpath('.//div[contains(@class,"date") and contains(@class,"details")]/@title')
        ts, tz = parse_timestamp(titles[0]) if titles else (None, None)
        is_service = "service" in (msg.get("class") or "")
        rec = {"chat": chat, "message_id": mid or f"nosid-{len(records)}",
               "timestamp": ts.isoformat() if ts else None, "tz": tz,
               "sender": None, "forwarded_from": None, "text_plain": "",
               "media_kinds": _media_kinds(msg), "is_reply": False,
               "reply_to": None, "is_service": is_service}
        if is_service:
            rec["text_plain"] = _clean(msg.xpath("./text() | .//text()"))
            records.append(rec)
            continue
        fwd = msg.xpath('.//div[contains(@class,"forwarded") and contains(@class,"body")]')
        if fwd:
            origin = fwd[0].xpath(_FROM_NAME_TEXT)
            rec["forwarded_from"] = _clean(origin) or None
        names = msg.xpath('.//div[contains(@class,"from_name")]'
                          '[not(ancestor::div[contains(@class,"forwarded")])]'
                          '//text()[not(ancestor::span[contains(@class,"date")])'
                          ' and not(ancestor::span[contains(@class,"details")])]')
        rec["sender"] = _clean(names) or None
        reply = msg.xpath('.//div[contains(@class,"reply_to")]//a/@href')
        if reply:
            rec["is_reply"] = True
            rec["reply_to"] = re.sub(r"^go_to_", "", (reply[0] or "").lstrip("#")) or None
        body_text = msg.xpath('.//div[contains(@class,"text")]')
        rec["text_plain"] = _clean([" ".join(b.itertext()) for b in body_text])
        records.append(rec)
    return records
