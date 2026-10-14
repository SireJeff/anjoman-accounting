# Anjoman Performance & Financial Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible analysis pipeline over 4 Telegram exports + the reconciled ledger + the media docx, producing two report packages (`reports/2026-10-14/financial_monthly/` and `reports/2026-10-14/performance/`) with monthly (Jalali) classification down to the hour.

**Architecture:** Four scripted stages under `analysis_tools/` (mirroring `accounting_tools/` conventions): deterministic parse → parallel source-profile agents → layered classification (rules → lexicon → LLM-residual) → correlation + report build. Every stage writes a JSON/JSONL artifact to `analysis/`; reports are assembled only from those artifacts.

**Tech Stack:** Python 3.11+, lxml, jdatetime, python-docx, pandas, matplotlib, reportlab, pytest. Parallel exploration via the Agent tool at execution time.

**Spec:** `docs/superpowers/specs/2026-10-14-performance-analysis-design.md`

## Global Constraints

- Repo root = parent of `analysis_tools/`; all scripts resolve it as `ROOT = Path(__file__).resolve().parent.parent` (same convention as `accounting_tools/`).
- Analysis window: `2025-05-28 <= t <= 2026-10-14`. Out-of-window messages are kept with `in_window: false`.
- Monthly classification is by **Jalali month** (`1404/05` format) with Gregorian range inline. Hours are **export-local time** (UTC+03:30), because university mechanics live in local time.
- Ledger is read-only truth: `anjoman_accounting_information/reports/2026-10-10/Transactions.csv` (UTF-8 **with BOM** — read with `encoding="utf-8-sig"`). Never modify it; Review-status TXs stay flagged.
- Statistical claims only at `n >= 5`. Classification precision target ≥ 85% on top-5 categories.
- Persian/Arabic-Indic digits (۰-۹, ٠-٩) must be normalized to ASCII before any numeric parsing.
- Commits end with `Co-Authored-By: Claude Code <noreply@anthropic.com>`.
- Windows / Git Bash environment: use `python` (fallback `py -3`); paths in bash commands use forward slashes.

## File Structure

```
analysis_tools/                      # new package (all pipeline stages)
├── common.py                        # ROOT, paths, digit-normalize, JSON I/O helpers
├── parse_exports.py                 # Stage 1: HTML + docx → messages.jsonl
├── make_fixtures.py                 # extracts real HTML snippets into tests/fixtures/
├── classify.py                      # Stage 3: rules+lexicon, --emit-residual, --apply
├── correlate.py                     # Stage 4: threads, monthly/hourly matrices, ecosystem
├── charts.py                        # all matplotlib chart builders (PNG)
├── report_common.py                 # MD→PDF via reportlab, shared by both builders
├── build_financial_report.py        # financial MD+PDF
├── build_performance_report.py      # performance MD+PDF
├── validate.py                      # spot-check sampler + reconciliation checks
└── tests/                           # pytest suite + fixtures/
analysis/                            # artifacts (committed; only cache/ ignored)
├── messages.jsonl  docx_content.json  lexicon.json  threads.json
├── profiles/<source>.json  llm_residual.json  llm_labels.json
├── classified.jsonl  classification_stats.json  timeline.json  ecosystem.json
└── cache/                           # gitignored
reports/2026-10-14/
├── financial_monthly/…  └── performance/…
```

---

### Task 1: Environment & scaffolding

**Files:**
- Create: `analysis_tools/common.py`, `analysis_tools/tests/__init__.py` (empty), `analysis_tools/__init__.py` (empty), `.gitignore` (append)

**Interfaces:**
- Produces: `common.ROOT` (Path), `common.SOURCES` (dict chat-name → dir Path), `common.normalize_digits(str)->str`, `common.write_json(path, obj)`, `common.read_json(path)->obj`, installed deps.

- [ ] **Step 1: Verify Python and install dependencies**

```bash
python --version || py -3 --version
python -m pip install lxml jdatetime python-docx pandas matplotlib reportlab pytest
```
Expected: Python ≥ 3.11; installs succeed.

- [ ] **Step 2: Write `analysis_tools/common.py`**

```python
"""Shared helpers for the anjoman analysis pipeline."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

SOURCES = {
    "private_group":    ROOT / "anjoman_private_group_report",
    "public_group":     ROOT / "anjoman_public_group_export/ChatExport_2026-10-13",
    "channel":          ROOT / "anjoman_channel_content",
    "accounting_group": ROOT / "anjoman_accounting_information/anjoman_accounting_group_export",
}
LEDGER_CSV = ROOT / "anjoman_accounting_information/reports/2026-10-10/Transactions.csv"
LEDGER_DIR = LEDGER_CSV.parent
WINDOW_START, WINDOW_END = "2025-05-28", "2026-10-14"

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def normalize_digits(s: str) -> str:
    return (s or "").translate(FA_DIGITS)

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
```

- [ ] **Step 3: Create package markers and gitignore entry**

```bash
touch analysis_tools/__init__.py analysis_tools/tests/__init__.py
printf 'analysis/cache/\n' >> .gitignore
```

- [ ] **Step 4: Smoke test**

```bash
cd "C:/Users/Surface Laptop 3/Downloads/Telegram Desktop/anjoman_acc" && python -c "from analysis_tools.common import ROOT, SOURCES, normalize_digits; assert all(p.is_dir() for p in SOURCES.values()); assert normalize_digits('۱۳:۳۰') == '13:30'; print('ok')"
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add analysis_tools .gitignore
git commit -m "feat: scaffold analysis_tools package with common helpers

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: Telegram HTML parser core (TDD)

**Files:**
- Create: `analysis_tools/make_fixtures.py`, `analysis_tools/parse_exports.py`
- Test: `analysis_tools/tests/test_parse.py`, fixtures under `analysis_tools/tests/fixtures/`

**Interfaces:**
- Produces: `parse_exports.parse_file(path: Path, chat: str) -> list[dict]` where each dict has keys `chat, message_id, timestamp (datetime|None), tz, sender, forwarded_from, text_plain, media_kinds (list[str]), is_reply, reply_to, is_service (bool)`; `parse_exports.parse_timestamp(title: str) -> (datetime|None, tz|None)`; `parse_exports.iter_message_files(chat_dir) -> list[Path]` (sorted `messages*.html`).

- [ ] **Step 1: Discovery — extract real fixture blocks from the actual exports**

Write `analysis_tools/make_fixtures.py`:

```python
"""Extract real message blocks into test fixtures. Run once from repo root."""
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

if __name__ == "__main__":
    FIX.mkdir(parents=True, exist_ok=True)
    # plain message with text, from the private group (ids verified at run time)
    (FIX / "plain.html").write_text(grab(SOURCES["private_group"] / "messages.html", ["message10", "message11"]), encoding="utf-8")
    # forwarded message, from the channel (find one by scanning for 'forwarded body')
    chan = (SOURCES["channel"] / "messages3.html").read_text(encoding="utf-8", errors="replace")
    ids = re.findall(r'<div class="message[^"]* forwarded[^"]*" id="(message\d+)"', chan) \
          or re.findall(r'id="(message\d+)"[^>]*>.{0,400}?forwarded body', chan, re.S)[:2]
    (FIX / "forwarded.html").write_text(grab(SOURCES["channel"] / "messages3.html", ids[:2]), encoding="utf-8")
    print("fixtures written; inspect them and adjust test expectations if needed")
```

Run: `python -m analysis_tools.make_fixtures` then **open both fixture files and read the exact class names and structure** (forwarded messages may use `class="forwarded body"` container or a `from_name` with «ارسال‌شده از» label — the parser below handles both, but verify against what you see).

- [ ] **Step 2: Write the failing tests**

`analysis_tools/tests/test_parse.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest analysis_tools/tests/test_parse.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'analysis_tools.parse_exports'`

- [ ] **Step 4: Write `analysis_tools/parse_exports.py`**

```python
"""Stage 1: parse Telegram Desktop HTML exports into message records."""
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

def parse_file(path: Path, chat: str):
    doc = lhtml.parse(str(path))
    records = []
    for msg in doc.xpath('//div[contains(@class,"message")]'):
        mid = msg.get("id", "")
        titles = msg.xpath('.//div[contains(@class,"date_details")]/@title')
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
        fwd = msg.xpath('.//div[contains(@class,"forwarded")]')
        if fwd:
            origin = fwd[0].xpath('.//div[contains(@class,"from_name")]//text() | .//span[contains(@class,"user")]//text()')
            rec["forwarded_from"] = _clean(origin) or None
            sender_scope = fwd[0]
        else:
            sender_scope = msg
        names = sender_scope.xpath('.//div[contains(@class,"from_name")]//text()')
        rec["sender"] = _clean(names) or None
        reply = msg.xpath('.//div[contains(@class,"reply_to")]//a/@href')
        if reply:
            rec["is_reply"] = True
            rec["reply_to"] = (reply[0] or "").lstrip("#")
        body_text = msg.xpath('.//div[contains(@class,"text")]')
        rec["text_plain"] = _clean([" ".join(b.itertext()) for b in body_text])
        records.append(rec)
    return records
```
Note: if fixture inspection in Step 1 showed a different structure for forwarded origin or sender, adapt the two xpath lines — the population-level gate in Task 4 is the authoritative check.

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest analysis_tools/tests/test_parse.py -v
```
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add analysis_tools
git commit -m "feat: telegram html parser with real-data fixtures

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: Time enrichment, window filter, docx parsing (TDD)

**Files:**
- Modify: `analysis_tools/parse_exports.py` (add `enrich`, `parse_docx`, `run_all`)
- Test: `analysis_tools/tests/test_enrich.py`

**Interfaces:**
- Consumes: `parse_file` records from Task 2.
- Produces: `parse_exports.enrich(rec: dict) -> dict` (adds `jalali_month: "1404/05"`, `jalali_weekday: "شنبه"`, `hour: int`, `weekday_en: str`, `date_greg: "2025-07-21"`, `in_window: bool`); `parse_exports.parse_docx(path: Path) -> dict` (`{"paragraphs": [{"style","text"}], "tables": [[str]]}`); `parse_exports.run_all() -> None` (writes `analysis/messages.jsonl` + `analysis/docx_content.json`).

- [ ] **Step 1: Write failing tests**

`analysis_tools/tests/test_enrich.py`:

```python
from datetime import datetime
from analysis_tools.parse_exports import enrich

def test_enrich_jalali_and_window():
    rec = {"timestamp": "2025-07-21T14:30:00"}  # 1404/04/30, a Monday
    out = enrich(rec)
    assert out["jalali_month"] == "1404/04"
    assert out["hour"] == 14
    assert out["weekday_en"] == "Monday"
    assert out["in_window"] is True
    assert isinstance(out["jalali_weekday"], str) and out["jalali_weekday"]

def test_enrich_excludes_pre_window():
    rec = {"timestamp": "2025-05-27T10:00:00"}
    assert enrich(rec)["in_window"] is False

def test_enrich_handles_missing_timestamp():
    assert enrich({"timestamp": None})["in_window"] is False
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest analysis_tools/tests/test_enrich.py -v
```
Expected: FAIL — `ImportError: cannot import name 'enrich'`

- [ ] **Step 3: Implement — append to `parse_exports.py`**

```python
import jdatetime
from .common import ROOT, SOURCES, write_json, WINDOW_START, WINDOW_END

def enrich(rec):
    if rec.get("timestamp"):
        dt = datetime.fromisoformat(rec["timestamp"])
        jd = jdatetime.date.fromgregorian(date=dt.date())
        rec["date_greg"] = dt.date().isoformat()
        rec["jalali_month"] = f"{jd.year}/{jd.month:02d}"
        rec["jalali_weekday"] = jd.strftime("%A")
        rec["hour"] = dt.hour
        rec["weekday_en"] = dt.strftime("%A")
        rec["in_window"] = WINDOW_START <= rec["date_greg"] <= WINDOW_END
    else:
        for k in ("date_greg", "jalali_month", "jalali_weekday", "hour", "weekday_en"):
            rec[k] = None
        rec["in_window"] = False
    return rec

def parse_docx(path):
    import docx
    d = docx.Document(str(path))
    paras = [{"style": p.style.name if p.style else "Normal", "text": p.text}
             for p in d.paragraphs if p.text.strip()]
    tables = [[cell.text.strip() for cell in row.cells] for t in d.tables for row in t.rows]
    return {"paragraphs": paras, "tables": tables}

def run_all():
    import json
    out = []
    for chat, src in SOURCES.items():
        for f in iter_message_files(src):
            for rec in parse_file(f, chat):
                out.append(enrich(rec))
    with open(ROOT / "analysis/messages.jsonl", "w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_json(ROOT / "analysis/docx_content.json",
               parse_docx(ROOT / "گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx"))
    print(f"parsed {len(out)} messages -> analysis/messages.jsonl")

if __name__ == "__main__":
    run_all()
```

- [ ] **Step 4: Run tests, then the docx parse smoke check**

```bash
python -m pytest analysis_tools/tests/test_enrich.py -v
python -c "from analysis_tools.parse_exports import parse_docx; from analysis_tools.common import ROOT; d = parse_docx(ROOT / 'گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx'); print(len(d['paragraphs']), 'paragraphs,', len(d['tables']), 'table rows')"
```
Expected: tests pass; docx yields a non-trivial paragraph count (hundreds expected for a 322 KB document — if it is image-heavy with little text, record the actual counts and proceed; the images are handled qualitatively in the performance report).

- [ ] **Step 5: Commit**

```bash
git add analysis_tools
git commit -m "feat: jalali/hour enrichment, window filter, docx parsing

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: Full parse run + population reconciliation gate

**Files:**
- Create: `analysis_tools/reconcile_parse.py`
- Output: `analysis/messages.jsonl`, `analysis/docx_content.json`, `analysis/parse_reconciliation.json`

**Interfaces:**
- Consumes: `run_all()` from Task 3.
- Produces: `analysis/messages.jsonl` (all four chats, enriched) — the backbone dataset every later task reads. Reconciliation JSON with per-source counts.

- [ ] **Step 1: Write the reconciliation script**

`analysis_tools/reconcile_parse.py`:

```python
"""Population-level gate: parser output must match raw grep counts."""
import json, subprocess
from pathlib import Path
from .common import SOURCES, write_json, ROOT

def grep_count(path: Path) -> int:
    # count non-service message divs the way the exploration greps did
    r = subprocess.run(["grep", "-c", 'class="message default', str(path)],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)

def main():
    msgs = [json.loads(l) for l in open(ROOT / "analysis/messages.jsonl", encoding="utf-8")]
    report = {}
    for chat, src in SOURCES.items():
        raw = sum(grep_count(f) for f in sorted(src.glob("messages*.html")))
        parsed_default = sum(1 for m in msgs
                             if m["chat"] == chat and not m["is_service"])
        parsed_service = sum(1 for m in msgs
                             if m["chat"] == chat and m["is_service"])
        with_ts = sum(1 for m in msgs if m["chat"] == chat and m["timestamp"])
        fwd = sum(1 for m in msgs if m["chat"] == chat and m["forwarded_from"])
        report[chat] = {"grep_default": raw, "parsed_default": parsed_default,
                        "parsed_service": parsed_service,
                        "default_delta": parsed_default - raw,
                        "with_timestamp": with_ts,
                        "forwarded_with_origin": fwd}
    report["_totals"] = {"messages": len(msgs),
                         "forwarded_expected_about": 1271}
    write_json(ROOT / "analysis/parse_reconciliation.json", report)
    print(json.dumps(report, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full parse + gate**

```bash
python -m analysis_tools.parse_exports
python -m analysis_tools.reconcile_parse
```
Expected: `parsed ~14,600 messages`; every chat's `default_delta` is 0 (± a handful is acceptable ONLY if each discrepancy is investigated and explained in the reconciliation JSON's notes — add a `"notes"` key manually after investigating); `with_timestamp` ≈ `parsed_default` (untimestamped service messages are the only acceptable gap); total `forwarded_with_origin` in the ballpark of 1,271 (joined-forward blocks legitimately merge counts).

If a delta is large: do NOT proceed — return to Task 2's xpaths, fix, re-run.

- [ ] **Step 3: Commit**

```bash
git add analysis_tools analysis/messages.jsonl analysis/docx_content.json analysis/parse_reconciliation.json
git commit -m "feat: full parse of all sources with reconciliation gate

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: Parallel source-profile agents (6 concurrent)

**Files:**
- Output: `analysis/profiles/private_group.json`, `public_group.json`, `channel.json`, `accounting_group.json`, `ledger.json`, `docx.json`

**Interfaces:**
- Consumes: `analysis/messages.jsonl`, `analysis/docx_content.json`, `Transactions.csv`.
- Produces: six profile JSONs, each matching this schema exactly:
```json
{"source": "…", "n_messages": 0,
 "months": {"1404/05": {"count": 0, "top_participants": [["name", 0]]}},
 "participants": [["name", "count", "share_percent"]],
 "media_mix": {"photo": 0, "video": 0, "voice": 0, "document": 0, "poll": 0, "sticker": 0, "animated": 0},
 "forwarded_origins": [["origin name", "count"]],
 "candidate_threads": [{"event_ref": "kebab-case-id", "title": "…", "keywords": ["…"],
   "anchor_dates": ["…"], "chats_seen_in": ["…"], "evidence_message_ids": ["…"]}],
 "time_patterns": [{"kind": "event-hour|active-hour|weekday-slot", "hour": 0, "jalali_weekday": "…",
   "n": 0, "evidence_message_ids": ["…"]}],
 "financial_signals": [{"what": "…", "message_ids": ["…"], "amounts_toman": [0]}]}
```
`ledger.json` uses the same top-level keys with `financial_signals` = TX coverage summary (by `period_jalali`, by category, unlinked message_ids) and `candidate_threads` built from ledger `project` values. `docx.json` summarizes the media report (metrics found, periods covered, claims).

- [ ] **Step 1: Dispatch 6 exploration agents concurrently** (one Agent-tool call each, in a single message; each agent is read-only over its source):

Agent prompt template (fill `{SOURCE}`, `{INPUT}`):

> You are a read-only data explorer. Input: `{INPUT}` (a JSONL of parsed Telegram messages with keys chat, message_id, timestamp, jalali_month, jalali_weekday, hour, sender, forwarded_from, text_plain, media_kinds, is_service / or the ledger CSV / or the docx JSON). Task: produce a source profile EXACTLY matching this schema: (schema above). Rules: months bucket by jalali_month; participants only from non-service messages with a sender; forwarded_origins from forwarded_from counts; candidate_threads = candidate activity threads you can defend from the data (events, schools, journal issues, website, media launches, interviews) each with keywords, anchor dates, chats, evidence message ids; time_patterns only where n>=5 (event start hours mentioned in text like ساعت ۱۷, weekday activity peaks, fixed slots); financial_signals = money-mentioning messages (amounts, بلیت، حق‌الزحمه، رسید، پرداخت). Persian text: keep original names; normalize Persian digits. Write the result with the Write tool to `analysis/profiles/{SOURCE}.json` (UTF-8). Do not modify any other file. Report back only the thread count and top-3 forwarded origins.

Source → input mapping: 4 chats read `analysis/messages.jsonl` filtered by `chat` field (private_group ~5.3k msgs, public_group ~6.1k, channel ~3k, accounting_group 158); ledger agent reads `anjoman_accounting_information/reports/2026-10-10/Transactions.csv` + `final_checks.json`; docx agent reads `analysis/docx_content.json`.

- [ ] **Step 2: Validate profiles**

```bash
python -c "
import json, pathlib
for f in pathlib.Path('analysis/profiles').glob('*.json'):
    d = json.loads(f.read_text(encoding='utf-8'))
    need = {'source','months','participants','forwarded_origins','candidate_threads','time_patterns','financial_signals'}
    missing = need - set(d)
    assert not missing, (f.name, missing)
    print(f.name, 'threads:', len(d['candidate_threads']), 'patterns:', len(d['time_patterns']))
"
```
Expected: six files, all schemas complete, thread counts plausible (expect ≥ 10 across chats combined).

- [ ] **Step 3: Commit**

```bash
git add analysis/profiles
git commit -m "feat: six parallel source profiles (chats, ledger, docx)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: Taxonomy, lexicon, structural classifier (TDD)

**Files:**
- Create: `analysis_tools/classify.py`, `analysis/lexicon.json`
- Test: `analysis_tools/tests/test_classify.py`

**Interfaces:**
- Consumes: `analysis/messages.jsonl`, `analysis/profiles/*.json`.
- Produces: `classify.classify_message(rec: dict, lexicon: dict) -> dict` returning `{categories: list[str], event_ref: str|None, confidence: float, method: "rule"|"lexicon"|None}`; CLI `python -m analysis_tools.classify` writes `analysis/classified.jsonl` (messages + classification fields, `method:"unclassified"` when empty).

Categories (fixed, from the approved taxonomy — exact slugs): `education_courses`, `events`, `publications_shabahang`, `media_outreach`, `governance_decisions`, `finance_operations`, `website_tech`, `community_social`, `coordination_logistics`, `meta_noise`.

- [ ] **Step 1: Author `analysis/lexicon.json`** — merge keyword lists from the six profiles' `candidate_threads[].keywords` into this structure (illustrative seed — the executor extends from profiles; every entry must be evidence-backed by a profile thread or ledger category):

```json
{
  "education_courses": ["مدرسه تابستانه", "summer school", "ثبت نام", "ثبت‌نام", "پایتون", "لاتک", "لتک", "ریاضیات Mathematica", "Mathematica", "مدرس", "sutschools"],
  "events": ["وبینار", "رویداد", "معرفی رشته", "نشست", "سمینار", "سمینار", "گردهمایی", "دورهمی", "ضیافت", "تک", "بلیت", "13:30"],
  "publications_shabahng_NOTE_USE_SLUG": [],
  "publications_shabahang": ["شباهنگ", "نشریه", "شماره جدید", "شعر و فیزیک", "ویراستاری", "جلد"],
  "media_outreach": ["اینستاگرام", "لینکدین", "Instagram", "LinkedIn", "کانال", "استوری", "پست"],
  "governance_decisions": ["جلسه هیئت", "انتخابات", "تصمیم", "رأی", "رای گیری", "برنامه ریزی", "تقسیم کار"],
  "finance_operations": ["حق الزحمه", "حق‌الزحمه", "پرداخت", "رسید", "گردش", "تومان", "ریال", "کسر", "شارژ", "تراکنش", "کارت به کارت"],
  "website_tech": ["alenush", "دامنه", "سرور", "هاست", "وب سایت", "وب‌سایت", "VM"],
  "community_social": ["سلام", "مرسی", "دمت گرم", "ممنون", "خسته نباشی", "ولید", "hghk"],
  "coordination_logistics": ["سالن", "کلاس رزرو", "چاپ", "استیکر", "پذیرایی", "ساندویچ", "تجهیزات", "پروژکتور"],
  "meta_noise": ["ok", "okay", "👍", "😂"]
}
```
(Remove the `…_NOTE_USE_SLUG` placeholder key — it exists only to say: use the exact slugs above.)

- [ ] **Step 2: Write failing tests**

`analysis_tools/tests/test_classify.py`:

```python
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
```

- [ ] **Step 3: Run to verify failure** — `python -m pytest analysis_tools/tests/test_classify.py -v` → FAIL (no module `classify`).

- [ ] **Step 4: Implement `analysis_tools/classify.py`**

```python
"""Stage 3 layers 1-2: structural rules + lexicon classification."""
import json, re
from .common import ROOT, read_json, write_json, normalize_digits

RULE_ORDER = ["education_courses", "events", "publications_shabahang", "media_outreach",
              "governance_decisions", "finance_operations", "website_tech",
              "community_social", "coordination_logistics", "meta_noise"]
FORM_LINK = re.compile(r"docs\.google\.com/(forms|spreadsheets)")

def classify_message(rec, lexicon):
    text = normalize_digits(rec.get("text_plain") or "").lower()
    media = rec.get("media_kinds") or []
    cats, method = [], None

    # Layer 1 — structural rules
    if "poll" in media:
        cats.append("governance_decisions"); method = "rule"
    if FORM_LINK.search(text):
        cats.append("media_outreach" if "فرم همکاری" not in text else "publications_shabahang")
        if method is None: method = "rule"
    if rec.get("forwarded_from") and not text:
        cats.append("media_outreach"); method = method or "rule"
    if not text and media and set(media) <= {"sticker", "animated"}:
        cats.append("meta_noise"); method = "rule"
    if not text and media and "photo" in media:
        cats.append("community_social"); method = method or "rule"

    # Layer 2 — lexicon (multi-label)
    lex_hits = [c for c in RULE_ORDER
                if any(k.lower() in text for k in lexicon.get(c, []))]
    if lex_hits:
        for c in lex_hits:
            if c not in cats:
                cats.append(c)
        method = method or "lexicon"

    conf = 0.9 if method == "rule" else (0.7 if method == "lexicon" else 0.0)
    return {"categories": cats[:4], "event_ref": None,
            "is_decision": False, "confidence": conf,
            "method": method if cats else None}

def main():
    lex = read_json(ROOT / "analysis/lexicon.json")
    out, stats = [], {"total": 0, "by_method": {}, "by_category": {}}
    with open(ROOT / "analysis/messages.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            cls = classify_message(rec, lex)
            rec.update(cls)
            out.append(rec)
            stats["total"] += 1
            stats["by_method"][cls["method"] or "unclassified"] = \
                stats["by_method"].get(cls["method"] or "unclassified", 0) + 1
            for c in cls["categories"]:
                stats["by_category"][c] = stats["by_category"].get(c, 0) + 1
    with open(ROOT / "analysis/classified.jsonl", "w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_json(ROOT / "analysis/classification_stats.json", stats)
    print(json.dumps(stats, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests + full classification, sanity-check coverage**

```bash
python -m pytest analysis_tools/tests/test_classify.py -v
python -m analysis_tools.classify
```
Expected: 5 tests pass. Coverage target: combined rule+lexicon ≥ 60% of window messages; `unclassified` < 40%. If lexicon coverage is far lower, extend the lexicon from the profiles' keyword lists (each addition evidence-backed) and re-run — do not move the target.

- [ ] **Step 6: Commit**

```bash
git add analysis_tools analysis/lexicon.json analysis/classified.jsonl analysis/classification_stats.json
git commit -m "feat: layered classifier with profile-derived lexicon

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: LLM residual classification + event threading registry

**Files:**
- Create: `analysis/threads.json` (curated registry), `analysis/llm_residual.json`, `analysis/llm_labels.json`
- Modify: `analysis_tools/classify.py` (add `--emit-residual`, `--apply`)

**Interfaces:**
- Consumes: `analysis/classified.jsonl` (unclassified/low-confidence, in-window, non-service messages), profiles' `candidate_threads`.
- Produces: final classification fields on every in-window message (`method:"llm"` for residuals); `threads.json`: `{"threads": [{"event_ref": str, "title": str, "keywords": [str], "chats": [str], "anchor_dates": [str], "tx_ids": [str]}]}`.

- [ ] **Step 1: Curate `analysis/threads.json`** — merge the 6 profiles' `candidate_threads`, de-duplicate by identity (same event across chats = one thread). Mandatory seed threads (verify/enrich from profiles; add anchor dates from channel announcements and ledger `message_ids`):
  `summer-school-1404`, `summer-school-1405`, `intro-event-1405`, `shabahang-new-issue`, `shabahang-media-launch` (LinkedIn/Instagram), `website-alenush`, `nightly-webinars` (Sharif Frontiers وبینارهای شبانه), `expert-talks`, `physics-tea`, `astronomy-activities`, `takaneh-journal`, `quanta-circles`, plus every profile thread not covered above.

- [ ] **Step 2: Emit residual batches** — add to `classify.py`:

```python
def emit_residual(batch_size=200):
    recs = [json.loads(l) for l in open(ROOT / "analysis/classified.jsonl", encoding="utf-8")]
    resid = [r for r in recs if r["in_window"] and not r["is_service"]
             and (r["method"] is None or r["confidence"] < 0.7)]
    batches = [{"batch": i + 1, "items": [
        {"key": f'{r["chat"]}#{r["message_id"]}', "chat": r["chat"],
         "month": r["jalali_month"], "text": (r["text_plain"] or "")[:500],
         "media": r["media_kinds"]}
        for r in resid[i:i + batch_size]]}
        for i in range(0, len(resid), batch_size)]
    write_json(ROOT / "analysis/llm_residual.json", {"n_residual": len(resid), "batches": batches})
    print(f"residual: {len(resid)} messages in {len(batches)} batches")
```
CLI: `python -m analysis_tools.classify --emit-residual`.

- [ ] **Step 3: Label residual batches with subagent(s)** — dispatch concurrent labeling agents (Agent tool), prompt:

> Read `analysis/llm_residual.json` batch(es) N. For each item classify into slugs from this fixed list: education_courses, events, publications_shabahang, media_outreach, governance_decisions, finance_operations, website_tech, community_social, coordination_logistics, meta_noise (multi-label allowed, max 3; empty list if genuinely unclear → leave `categories: []`). Also set `is_decision` (true only when a choice/resolution is stated), `event_ref` (one of the ids in analysis/threads.json, or null), `confidence` 0.5-0.9. Persian slang: judge by context; money/amounts → finance_operations; scheduling/rooms/printing → coordination_logistics. Write/merge results into `analysis/llm_labels.json` as `{"key": {"categories": [...], "is_decision": bool, "event_ref": str|null, "confidence": float}}` (UTF-8, keep existing keys from other batches). Do not modify any other file. Report only counts labeled.

- [ ] **Step 4: Apply labels** — add to `classify.py`:

```python
def apply_llm():
    labels = read_json(ROOT / "analysis/llm_labels.json")
    recs = [json.loads(l) for l in open(ROOT / "analysis/classified.jsonl", encoding="utf-8")]
    n = 0
    for r in recs:
        lab = labels.get(f'{r["chat"]}#{r["message_id"]}')
        if lab and (r["method"] is None or r["confidence"] < 0.7):
            if lab.get("categories"):
                r["categories"] = lab["categories"]; r["method"] = "llm"
                r["confidence"] = lab.get("confidence", 0.6); n += 1
            r["is_decision"] = r["is_decision"] or bool(lab.get("is_decision"))
            if lab.get("event_ref"):
                r["event_ref"] = lab["event_ref"]
    with open(ROOT / "analysis/classified.jsonl", "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"applied {n} llm labels")
```
CLI: `python -m analysis_tools.classify --apply` (wire both flags in `__main__`).

- [ ] **Step 5: Run the full loop and verify coverage**

```bash
python -m analysis_tools.classify --emit-residual
# dispatch labeling agents, then:
python -m analysis_tools.classify --apply
python -m analysis_tools.classify   # regenerate stats
```
Expected: final `unclassified` among in-window non-service messages < 15%.

- [ ] **Step 6: Commit**

```bash
git add analysis_tools analysis/threads.json analysis/llm_residual.json analysis/llm_labels.json analysis/classified.jsonl analysis/classification_stats.json
git commit -m "feat: llm residual classification and curated event threads

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 8: Event threading + cross-chat correlation (TDD)

**Files:**
- Create: `analysis_tools/correlate.py`
- Test: `analysis_tools/tests/test_correlate.py`
- Output: `analysis/timeline.json` (threads section)

**Interfaces:**
- Consumes: `analysis/classified.jsonl`, `analysis/threads.json`, `Transactions.csv`.
- Produces: `correlate.thread_events(recs, threads, tx) -> list[dict]` — one summary per thread: `{event_ref, title, first_seen, last_seen, chats: {chat: {first, last, n}}, n_messages, tx_ids: [], tx_total_toman: 0, announcement_lag_days: null, decision_dates: []}`; `correlate.build_timeline() -> None` writes `analysis/timeline.json`.

- [ ] **Step 1: Write failing tests**

`analysis_tools/tests/test_correlate.py`:

```python
from analysis_tools.correlate import thread_events

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
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest analysis_tools/tests/test_correlate.py -v` → FAIL (no module).

- [ ] **Step 3: Implement** `analysis_tools/correlate.py`:

```python
"""Stage 4a: event threads + cross-chat correlation."""
import json
from datetime import datetime
from .common import ROOT, LEDGER_CSV, read_json, write_json

def _load_tx():
    import pandas as pd
    df = pd.read_csv(LEDGER_CSV, encoding="utf-8-sig")
    df["amount_toman"] = pd.to_numeric(df["amount_toman"], errors="coerce").fillna(0)
    return df.to_dict("records")

def thread_events(recs, threads, tx_rows):
    by_ref = {}
    for t in threads["threads"]:
        by_ref[t["event_ref"]] = {**t, "msgs": []}
    for r in recs:
        ref = r.get("event_ref")
        if ref and ref in by_ref:
            by_ref[ref]["msgs"].append(r)
        # keyword fallback for messages without llm event_ref
        elif r.get("in_window") and not r.get("is_service"):
            text = (r.get("text_plain") or "")
            for t in threads["threads"]:
                if any(k in text for k in t["keywords"][:6]):
                    by_ref[t["event_ref"]]["msgs"].append(r)
                    break
    out = []
    for ref, t in by_ref.items():
        msgs = sorted(t["msgs"], key=lambda m: m.get("timestamp") or "")
        if not msgs:
            continue
        chats = {}
        for m in msgs:
            c = chats.setdefault(m["chat"], {"first": m["timestamp"], "last": m["timestamp"], "n": 0})
            c["n"] += 1
            c["last"] = max(c["last"], m["timestamp"])
        tx_ids = [t.get("tx_ids", []) and x for x in t.get("tx_ids", [])]
        tx_ids = [x for x in t.get("tx_ids", []) if x] or _tx_for(ref, tx_rows)
        total = sum(float(r.get("amount_toman") or 0) for r in tx_rows
                    if r["id"] in tx_ids)
        lag = None
        if "channel" in chats and len(chats) > 1:
            firsts = [v["first"] for c, v in chats.items() if c != "channel"]
            pre = min(firsts)
            d1 = datetime.fromisoformat(pre[:19]); d2 = datetime.fromisoformat(chats["channel"]["first"][:19])
            lag = (d2 - d1).days if d2 >= d1 else -(d1 - d2).days
        out.append({"event_ref": ref, "title": t["title"],
                    "first_seen": msgs[0]["timestamp"], "last_seen": msgs[-1]["timestamp"],
                    "chats": chats, "n_messages": len(msgs), "tx_ids": tx_ids,
                    "tx_total_toman": total, "announcement_lag_days": lag,
                    "decision_dates": [m["timestamp"][:10] for m in msgs if m.get("is_decision")]})
    return sorted(out, key=lambda x: x["first_seen"])

def _tx_for(ref, tx_rows):
    map_ = {"summer-school-1404": "Summer School 1404", "summer-school-1405": "Summer School 1405",
            "intro-event-1405": "Intro Event 1405", "website-alenush": "Association website"}
    proj = map_.get(ref)
    return [r["id"] for r in tx_rows if proj and r.get("project") == proj] if proj else []

def build_timeline():
    recs = [json.loads(l) for l in open(ROOT / "analysis/classified.jsonl", encoding="utf-8")]
    threads = read_json(ROOT / "analysis/threads.json")
    tl = {"threads": thread_events(recs, threads, _load_tx())}
    write_json(ROOT / "analysis/timeline.json", tl)
    print(f"{len(tl['threads'])} threads written")

if __name__ == "__main__":
    build_timeline()
```

- [ ] **Step 4: Run tests + build, sanity-check**

```bash
python -m pytest analysis_tools/tests/test_correlate.py -v
python -m analysis_tools.correlate
```
Expected: test passes; ≥ 8 threads written; summer-school threads show non-zero `tx_total_toman` matching their ledger projects.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools analysis/timeline.json
git commit -m "feat: event threading with cross-chat lag and ledger join

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 9: Monthly (Jalali) × hourly analytics (TDD)

**Files:**
- Modify: `analysis_tools/correlate.py` (add analytics functions)
- Test: `analysis_tools/tests/test_analytics.py`
- Output: `analysis/timeline.json` (monthly/hourly/mechanics sections)

**Interfaces:**
- Consumes: `analysis/classified.jsonl`, `Transactions.csv`.
- Produces (inside `timeline.json`):
  - `monthly_activity`: `{month: {chat: {category: count}}}`
  - `monthly_cashflow`: `{month: {"Receipts": toman, "Payments": toman, "by_category": {category: toman}, "by_project": {project: toman}}}`
  - `hour_histogram`: `{chat: {hour: count}}`
  - `weekday_hour_heat`: `{chat: {"<jalali_weekday>": {hour: count}}}`
  - `event_start_times`: `{event_ref: {"times": ["HH:MM"], "n": int, "mode": "HH:MM"|null}}` — from ساعت/ ساعتِ + Persian-digit time mentions in channel/event messages
  - `mechanics`: recurring patterns list `[{"kind": "fixed-slot|tx-hour|peak", "jalali_weekday": "…", "hour": 0, "category": "…", "n": 0, "note": "…"}]` (n ≥ 5 only)
- Functions: `monthly_activity(recs)`, `monthly_cashflow(tx_rows)`, `hour_histogram(recs)`, `weekday_hour_heat(recs)`, `extract_time_mentions(text) -> list["HH:MM"]`, `detect_mechanics(heat, start_times, tx_rows) -> list`.

- [ ] **Step 1: Write failing tests**

`analysis_tools/tests/test_analytics.py`:

```python
from analysis_tools.correlate import (monthly_activity, monthly_cashflow,
                                      hour_histogram, extract_time_mentions)

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

def test_hour_histogram():
    hh = hour_histogram([{"chat": "c", "hour": 13, "in_window": True, "is_service": False},
                         {"chat": "c", "hour": 13, "in_window": True, "is_service": False}])
    assert hh["c"][13] == 2

def test_extract_time_mentions_persian_digits():
    assert extract_time_mentions("ساعت ۱۷:۰۰ شروع می‌شود") == ["17:00"]
    assert extract_time_mentions("13:30 و 14:00") == ["13:30", "14:00"]
    assert extract_time_mentions("بدون ساعت") == []
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest analysis_tools/tests/test_analytics.py -v` → FAIL.

- [ ] **Step 3: Implement** — append to `correlate.py`:

```python
import re
from collections import defaultdict
from .common import normalize_digits

TIME_RE = re.compile(r"(?:ساعت|ساعتِ)?\s*([0-9]{1,2}:[0-9]{2})(?![0-9])")

def extract_time_mentions(text):
    t = normalize_digits(text or "")
    return [f"{h.zfill(2)}:{m}" for h, m in
            (x.split(":") for x in TIME_RE.findall(t))
            if 0 <= int(h) < 24 and 0 <= int(m) < 60]

def monthly_activity(recs):
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in recs:
        if not r.get("in_window") or r.get("is_service") or not r.get("jalali_month"):
            continue
        for c in r.get("categories") or ["uncategorized"]:
            out[r["jalali_month"]][r["chat"]][c] += 1
    return json.loads(json.dumps(out))

def monthly_cashflow(tx_rows):
    out = defaultdict(lambda: {"Receipts": 0.0, "Payments": 0.0,
                               "by_category": defaultdict(float), "by_project": defaultdict(float)})
    for r in tx_rows:
        m = out[r["period_jalali"]]
        amt = float(r.get("amount_toman") or 0)
        if r["direction"] == "Receipt":
            m["Receipts"] += amt
        else:
            m["Payments"] += amt
        m["by_category"][r.get("category") or "Unknown"] += amt
        m["by_project"][r.get("project") or "Unknown"] += amt
    return json.loads(json.dumps(out))

def hour_histogram(recs):
    out = defaultdict(lambda: defaultdict(int))
    for r in recs:
        if r.get("in_window") and not r.get("is_service") and r.get("hour") is not None:
            out[r["chat"]][r["hour"]] += 1
    return json.loads(json.dumps(out))

def weekday_hour_heat(recs):
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in recs:
        if r.get("in_window") and not r.get("is_service") and r.get("hour") is not None:
            out[r["chat"]][r.get("jalali_weekday")][r["hour"]] += 1
    return json.loads(json.dumps(out))

def detect_mechanics(heat, start_times, tx_rows):
    mech = []
    for ref, s in start_times.items():
        if s["n"] >= 5 and s["mode"]:
            mech.append({"kind": "fixed-slot", "hour": int(s["mode"][:2]),
                         "category": ref, "n": s["n"],
                         "note": f"{ref} most often mentions start {s['mode']}"})
    for chat, days in heat.items():
        for wd, hours in days.items():
            h, n = max(hours.items(), key=lambda kv: kv[1])
            if n >= 5:
                mech.append({"kind": "peak", "jalali_weekday": wd, "hour": h,
                             "category": chat, "n": n,
                             "note": f"{chat} peaks {wd} {h:02d}:00"})
    return mech
```
Also extend `build_timeline()` to compute `event_start_times` (per thread: collect `extract_time_mentions` over its channel/event messages, `mode` = most common) and to merge all sections into `timeline.json`.

- [ ] **Step 4: Run tests + rebuild timeline**

```bash
python -m pytest analysis_tools/tests/test_analytics.py -v
python -m analysis_tools.correlate
```
Expected: 4 tests pass; `timeline.json` now has all seven sections; `mechanics` non-empty (the 13:30/17:00 slots should surface if the data supports them).

- [ ] **Step 5: Commit**

```bash
git add analysis_tools analysis/timeline.json
git commit -m "feat: jalali-monthly and hour-of-day analytics with mechanics detection

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 10: Ecosystem graph (TDD)

**Files:**
- Create: `analysis_tools/ecosystem.py`
- Test: `analysis_tools/tests/test_ecosystem.py`
- Output: `analysis/ecosystem.json`

**Interfaces:**
- Consumes: `analysis/messages.jsonl` (forwarded_from, text @mentions), seed entity table.
- Produces: `ecosystem.build(messages) -> {"nodes": [...], "edges": [...]}` where nodes are `{"id", "label", "type": "association|subgroup|chat-export|external|unknown", "seed": bool}` and edges `{"source", "target", "type": "forward|mention", "weight": int}`. Written to `analysis/ecosystem.json` with a `validation` block mapping each seed entity → evidence found (or `"unverified"`).

- [ ] **Step 1: Write failing tests**

`analysis_tools/tests/test_ecosystem.py`:

```python
from analysis_tools.ecosystem import build

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
```

- [ ] **Step 2: Run to verify failure** — FAIL (no module).

- [ ] **Step 3: Implement `analysis_tools/ecosystem.py`**

```python
"""Ecosystem graph: association <-> subgroups <-> external orgs."""
import json, re
from collections import Counter
from .common import ROOT, write_json

SEEDS = [
    ("association",     "انجمن علمی فیزیک شریف", "association"),
    ("physics_tea",     "چای فیزیک (@physics_tea_sessions)", "subgroup"),
    ("tea_chat",        "چای - حضوری", "subgroup"),
    ("shabahang_sut",   "نشریه شباهنگ (@shabahang_sut)", "subgroup"),
    ("sharifastronomy", "گروه نجوم شریف (@sharifastronomy)", "subgroup"),
    ("takaneh",         "نشریه تکانه (@takaneh_physics_sharif)", "subgroup"),
    ("sutschools",      "مدرسه تابستانی فیزیک (@sutschools)", "subgroup"),
    ("quantasc",        "حلقه‌های کوانتا (@QuantaSC)", "subgroup"),
]
SEED_MATCH = {"شباهنگ": "shabahang_sut", "نجوم": "sharifastronomy", "آسترونومی": "sharifastronomy",
              "تکانه": "takaneh", "کوانتا": "quantasc", "چای": "physics_tea",
              "تابستانه": "sutschools", "school": "sutschools", "انجمن علمی فیزیک": "association"}
HANDLE_RE = re.compile(r"(?:t\.me/|@)([A-Za-z0-9_]{4,})")
EXPORT_NODE = {"private_group": "private_group_export", "public_group": "public_group_export",
               "channel": "channel_export", "accounting_group": "accounting_group_export"}

def _map_origin(name):
    for k, sid in SEED_MATCH.items():
        if k in (name or ""):
            return sid, None
    return None, name  # external/unknown

def build(messages):
    fwd, men = Counter(), Counter()
    externals = {}
    for m in messages:
        src = EXPORT_NODE.get(m["chat"])
        if m.get("forwarded_from"):
            sid, raw = _map_origin(m["forwarded_from"])
            if sid:
                fwd[(src, sid)] += 1
            elif raw:
                externals[raw] = externals.get(raw, 0) + 1
                fwd[(src, f"ext:{raw}")] += 1
        for h in HANDLE_RE.findall(m.get("text_plain") or ""):
            sid = h.lower() if h.lower() in {s[0] for s in SEEDS} else f"handle:{h.lower()}"
            men[(src, sid)] += 1
    nodes = [{"id": sid, "label": lab, "type": typ, "seed": True}
             for sid, lab, typ in SEEDS]
    nodes += [{"id": EXPORT_NODE[k], "label": k.replace("_", " "), "type": "chat-export", "seed": False}
              for k in EXPORT_NODE]
    nodes += [{"id": f"ext:{n}", "label": n, "type": "external", "seed": False}
              for n in externals]
    seen_handles = {e[1] for e in list(fwd) + list(men)} - {n["id"] for n in nodes}
    nodes += [{"id": h, "label": h.split(":", 1)[1], "type": "external", "seed": False}
              for h in seen_handles if h.startswith(("ext:", "handle:"))]
    edges = ([{"source": s, "target": t, "type": "forward", "weight": c} for (s, t), c in fwd.items()] +
             [{"source": s, "target": t, "type": "mention", "weight": c} for (s, t), c in men.items()])
    return {"nodes": nodes, "edges": edges}

def main():
    msgs = [json.loads(l) for l in open(ROOT / "analysis/messages.jsonl", encoding="utf-8")]
    g = build(msgs)
    g["validation"] = {sid: ("evidenced" if any(e["target"] == sid and e["weight"] >= 3
                                                for e in g["edges"]) else "unverified")
                       for sid, _, _ in SEEDS}
    write_json(ROOT / "analysis/ecosystem.json", g)
    print(f"{len(g['nodes'])} nodes, {len(g['edges'])} edges; validation: {g['validation']}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests + build**

```bash
python -m pytest analysis_tools/tests/test_ecosystem.py -v
python -m analysis_tools.ecosystem
```
Expected: tests pass; every seed subgroup either `evidenced` or explicitly `unverified` in the printed validation (record unverified ones — they go into the report's caveats).

- [ ] **Step 5: Commit**

```bash
git add analysis_tools analysis/ecosystem.json
git commit -m "feat: ecosystem graph from forwards and mentions with seed validation

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 11: Chart builders

**Files:**
- Create: `analysis_tools/charts.py`
- Test: `analysis_tools/tests/test_charts.py`
- Output: `reports/2026-10-14/performance/charts/*.png`, `reports/2026-10-14/financial_monthly/charts/*.png`

**Interfaces:**
- Consumes: `analysis/timeline.json`, `analysis/ecosystem.json`.
- Produces: `charts.render_all() -> dict[str, Path]` — keys: `activity_by_month`, `category_breakdown`, `weekday_hour_heat`, `hour_histogram`, `event_timeline`, `ecosystem_map`, `cashflow_monthly`, `cumulative_cash`.

- [ ] **Step 0: Invoke the `dataviz` skill** before writing any chart code — its palette and mark rules govern every figure (executor: call `Skill(dataviz)` first and follow it).

- [ ] **Step 1: Write the test**

```python
# analysis_tools/tests/test_charts.py
import json
from pathlib import Path
from analysis_tools import charts

def test_render_all_produces_pngs(tmp_path, monkeypatch):
    tl = {"monthly_activity": {"1404/05": {"channel": {"events": 3}}},
          "monthly_cashflow": {"1404/05": {"Receipts": 1.0, "Payments": 0.5,
                                           "by_category": {"Events": 1.0}, "by_project": {}}},
          "hour_histogram": {"channel": {"13": 2}},
          "weekday_hour_heat": {"channel": {"شنبه": {"13": 2}}},
          "threads": [], "mechanics": [], "event_start_times": {}}
    eco = {"nodes": [{"id": "association", "label": "A", "type": "association", "seed": True},
                     {"id": "shabahang_sut", "label": "S", "type": "subgroup", "seed": True}],
           "edges": [{"source": "channel_export", "target": "shabahang_sut",
                      "type": "forward", "weight": 5}]}
    monkeypatch.setattr(charts, "load_timeline", lambda: tl)
    monkeypatch.setattr(charts, "load_ecosystem", lambda: eco)
    out = charts.render_all()
    assert set(out) == {"activity_by_month", "category_breakdown", "weekday_hour_heat",
                        "hour_histogram", "event_timeline", "ecosystem_map",
                        "cashflow_monthly", "cumulative_cash"}
    for p in out.values():
        assert Path(p).exists() and Path(p).suffix == ".png"
```

- [ ] **Step 2: Run to verify failure** — FAIL (no module).

- [ ] **Step 3: Implement `analysis_tools/charts.py`** — structure (each function: data → matplotlib figure → savefig PNG, palette/types per the dataviz skill):

```python
"""All report figures. Palette & mark rules per the dataviz skill."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .common import ROOT, read_json

PERF = ROOT / "reports/2026-10-14/performance/charts"
FIN  = ROOT / "reports/2026-10-14/financial_monthly/charts"

def load_timeline(): return read_json(ROOT / "analysis/timeline.json")
def load_ecosystem(): return read_json(ROOT / "analysis/ecosystem.json")

def _months(d):  # ordered jalali month keys across a nested dict
    return sorted({m for v in d.values() for m in v} | set(d)) if d else []

def activity_by_month(tl, path): ...      # stacked bars: chat series over jalali months
def category_breakdown(tl, path): ...     # horizontal bars: message counts per category (sum across monthly_activity)
def weekday_hour_heat(tl, path): ...      # heatmap: jalali weekdays × hours, summed over chats
def hour_histogram(tl, path): ...         # small multiples: per-chat hour distribution
def event_timeline(tl, path): ...         # horizontal span per thread (first_seen→last_seen) labeled
def ecosystem_map(eco, path): ...         # association center, subgroups inner ring, externals outer ring; edge width=weight
def cashflow_monthly(tl, path): ...       # grouped diverging bars: Receipts vs Payments per jalali month (toman)
def cumulative_cash(tl, path): ...        # line: cumulative net (Receipts−Payments) over months

def render_all():
    tl, eco = load_timeline(), load_ecosystem()
    PERF.mkdir(parents=True, exist_ok=True); FIN.mkdir(parents=True, exist_ok=True)
    out = {"activity_by_month": activity_by_month(tl, PERF / "activity_by_month.png"),
           "category_breakdown": category_breakdown(tl, PERF / "category_breakdown.png"),
           "weekday_hour_heat": weekday_hour_heat(tl, PERF / "weekday_hour_heat.png"),
           "hour_histogram": hour_histogram(tl, PERF / "hour_histogram.png"),
           "event_timeline": event_timeline(tl, PERF / "event_timeline.png"),
           "ecosystem_map": ecosystem_map(eco, PERF / "ecosystem_map.png"),
           "cashflow_monthly": cashflow_monthly(tl, FIN / "cashflow_monthly.png"),
           "cumulative_cash": cumulative_cash(tl, FIN / "cumulative_cash.png")}
    return out

if __name__ == "__main__":
    print(render_all())
```
Each `...` body is implemented per the dataviz skill's rules: one shared categorical palette for chats/categories, sequential ramp for heatmaps, direct labels over legends where space allows, units in axis titles (messages / toman), jalali month labels rendered right-to-left-safe (matplotlib handles UTF-8; set `plt.rcParams["font.family"]` to a font with Arabic script coverage, e.g. "Tahoma" on Windows, verified at run time).

- [ ] **Step 4: Run tests + render real charts**

```bash
python -m pytest analysis_tools/tests/test_charts.py -v
python -m analysis_tools.charts
```
Expected: test passes (monkeypatched); real run writes 8 PNGs. Visually open `ecosystem_map.png` and `weekday_hour_heat.png` — if Persian labels render as boxes, switch the font to one present on the system (Tahoma/Segoe UI) and re-render.

- [ ] **Step 5: Commit**

```bash
git add analysis_tools reports/2026-10-14
git commit -m "feat: eight report figures following dataviz system

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 12: Financial report (monthly) build

**Files:**
- Create: `analysis_tools/report_common.py`, `analysis_tools/build_financial_report.py`
- Output: `reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md` + `.pdf`

**Interfaces:**
- Consumes: `Transactions.csv`, `analysis/timeline.json` (monthly_cashflow, mechanics), `reports/2026-10-14/financial_monthly/charts/*.png`, `anjoman_accounting_information/reports/2026-10-10/final_checks.json`.
- Produces: `report_common.md_to_pdf(md_path, pdf_path, images_dir)` shared by Task 13; `build_financial_report.build() -> Path` (MD) with a hard reconciliation gate.

- [ ] **Step 1: Write `analysis_tools/report_common.py`** (MD → PDF via reportlab, following `accounting_tools/build_report.py` precedent — read that file first and reuse its helpers where practical):

```python
"""Shared markdown→PDF builder for the 2026-10-14 reports."""
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

def md_to_pdf(md_path, pdf_path):
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=13)
    story, img_dir = [], Path(md_path).parent
    for line in Path(md_path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            story.append(Spacer(1, 4)); continue
        m = re.match(r"!\[.*\]\((.+)\)", s)
        if m and (img_dir / m.group(1)).exists():
            from PIL import Image as PILImage  # reportlab needs explicit dims for PNGs sometimes
            story.append(Image(str(img_dir / m.group(1)), width=16 * cm, height=9 * cm))
            story.append(Spacer(1, 6)); continue
        if s.startswith("## "):
            story.append(Paragraph(s[3:], h2))
        elif s.startswith("# "):
            story.append(Paragraph(s[2:], h1))
        elif s.startswith("|"):
            row = [c.strip() for c in s.strip("|").split("|")]
            story.append(Paragraph(" | ".join(row), body))  # tables render as wrapped rows
        else:
            story.append(Paragraph(s, body))
    SimpleDocTemplate(str(pdf_path), pagesize=A4,
                      leftMargin=2 * cm, rightMargin=2 * cm).build(story)
```
(If `accounting_tools/build_report.py` has a better table pipeline, use it and delete this simplification — the requirement is: headings, paragraphs, tables, and all chart images present in the PDF.)

- [ ] **Step 2: Write `analysis_tools/build_financial_report.py`**

```python
"""Financial report (monthly) — derived views of the reconciled ledger."""
import pandas as pd
from .common import ROOT, LEDGER_CSV, LEDGER_DIR, read_json
from .correlate import _load_tx, monthly_cashflow
from .report_common import md_to_pdf

CAT_LABELS = {"Course fees": "Course fees", "Teaching": "Teaching", "Events": "Events",
              "Website domain": "Website", "uncategorized": "Uncategorized"}

def build():
    tx = _load_tx()
    tl = read_json(ROOT / "analysis/timeline.json")
    cash = tl["monthly_cashflow"]
    months = sorted(cash)
    # GATE: reconcile against the source ledger before writing anything
    tot_r = sum(float(r["amount_toman"] or 0) for r in tx if r["direction"] == "Receipt")
    tot_p = sum(float(r["amount_toman"] or 0) for r in tx if r["direction"] == "Payment")
    assert abs(sum(cash[m]["Receipts"] for m in months) - tot_r) < 0.5, "receipt total drift"
    assert abs(sum(cash[m]["Payments"] for m in months) - tot_p) < 0.5, "payment total drift"
    L = ["# Anjoman Financial Report — Monthly View (1404/04 – 1405/07)",
         "",
         f"**Window:** 2025-05-28 → 2026-10-14 · **Source:** reconciled ledger of 2026-10-10 "
         f"({len(tx)} transactions). Derived view — this report does not re-audit. "
         "Review-status transactions are flagged.",
         "",
         "## Monthly cashflow summary (toman)",
         "",
         "| Jalali month | Gregorian range | Receipts | Payments | Net |",
         "|---|---|---:|---:|---:|"]
    from .common import WINDOW_START, WINDOW_END  # months outside window still shown, flagged
    greg = pd.read_csv(LEDGER_CSV, encoding="utf-8-sig")
    gr = greg.dropna(subset=["date_gregorian"]).groupby("period_jalali")["date_gregorian"].agg(["min", "max"])
    for m in months:
        r, p = cash[m]["Receipts"], cash[m]["Payments"]
        g = f'{gr.loc[m, "min"]} → {gr.loc[m, "max"]}' if m in gr.index else "—"
        L.append(f"| {m} | {g} | {r:,.0f} | {p:,.0f} | {r - p:,.0f} |")
    L += ["", f"**Totals:** receipts {tot_r:,.0f} · payments {tot_p:,.0f} · net {tot_r - tot_p:,.0f} toman", ""]
    L += ["## Category schedule by month", "",
          "| Category | " + " | ".join(months) + " | Total |",
          "|---" * (len(months) + 2) + "|"]
    cats = sorted({c for m in months for c in cash[m]["by_category"]})
    for c in cats:
        vals = [cash[m]["by_category"].get(c, 0) for m in months]
        L.append(f"| {c} | " + " | ".join(f"{v:,.0f}" for v in vals) + f" | {sum(vals):,.0f} |")
    L += ["", "## Project schedule by month", "", "(same table shape, rows = ledger projects — generate identically to categories)"]
    # → generate the project table with the same loop over cash[m]["by_project"]
    L += ["", "## Evidence and time-of-day notes", ""]
    L.append("Transaction timestamps exist where ledger `message_ids` link to accounting-group "
             "messages; hourly patterns observed there: (render from timeline.json mechanics "
             "entries of kind tx-hour/peak, n>=5 only — list each as 'weekday HH:MM, n=…').")
    L += ["", "![Monthly cashflow](charts/cashflow_monthly.png)", "",
          "![Cumulative net cash](charts/cumulative_cash.png)", "",
          "## Caveats", "",
          "- Derived from the reconciled ledger 2026-10-10; Review-status items (e.g. TX0096 domain "
          "declaration) are excluded from supported totals there and flagged here.",
          "- Cash custodianship is mixed personal/association; net activity ≠ closing cash "
          "(per the 2026-10-10 report's remaining-gaps section)."]
    out = ROOT / "reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    md_to_pdf(out, out.with_suffix(".pdf"))
    return out

if __name__ == "__main__":
    print(build())
```
The two inline "generate identically" notes are the only allowed deferred loops in this plan — implement them in place (project table, tx-hour list) before running.

- [ ] **Step 3: Run and verify the gate + output**

```bash
python -m analysis_tools.build_financial_report
```
Expected: build succeeds (assertions passed = ledger totals reconcile to the toman); MD and PDF exist; open the PDF and confirm both charts and all monthly tables render.

- [ ] **Step 4: Commit**

```bash
git add analysis_tools reports/2026-10-14/financial_monthly
git commit -m "feat: monthly financial report with ledger reconciliation gate

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 13: Performance & activity report build

**Files:**
- Create: `analysis_tools/build_performance_report.py`
- Output: `reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.md` + `.pdf`

**Interfaces:**
- Consumes: `analysis/timeline.json` (all sections), `analysis/ecosystem.json`, `analysis/classification_stats.json`, `analysis/profiles/*.json`, `analysis/docx_content.json`, charts from Task 11.
- Produces: `build() -> Path`.

- [ ] **Step 1: Implement the builder** — section skeleton (every `(from …)` is rendered from the named artifact, not prose from memory):

```python
"""Performance & activity report — assembled from analysis artifacts only."""
from .common import ROOT, read_json
from .report_common import md_to_pdf

def build():
    tl = read_json(ROOT / "analysis/timeline.json")
    eco = read_json(ROOT / "analysis/ecosystem.json")
    stats = read_json(ROOT / "analysis/classification_stats.json")
    L = ["# Anjoman Performance & Activity Report (2025-05-28 → 2026-10-14)", "",
         "## 1. Executive summary", "",
         "(auto: total messages by chat in window, top-3 categories, thread count, "
         "net cashflow from timeline.monthly_cashflow totals, 5 headline threads by n_messages)", "",
         "## 2. Phase narrative", "",
         "(auto: split window at jalali months into phases — Summer 1404, Academic 1404-05, "
         "Summer 1405, Fall 1405; per phase: monthly_activity highlights + threads whose "
         "first_seen falls in the phase, one generated paragraph each)", "",
         "## 3. Activity categories", "",
         "(auto: for each of the 10 categories — monthly counts table from monthly_activity "
         "aggregated over chats + the 3 most-engaged threads in that category)", "",
         "![Activity by month](charts/activity_by_month.png)",
         "![Category breakdown](charts/category_breakdown.png)", "",
         "## 4. Cross-chat correlation", "",
         "(auto: table of threads with chats involved, announcement_lag_days, tx_total_toman; "
         "then 3 case studies: the threads with the most chats involved — planning→announcement"
         "→delivery→payment sequence with dated message references from thread summaries)", "",
         "![Event timeline](charts/event_timeline.png)", "",
         "## 5. Ecosystem map", "",
         "(auto: ecosystem.json validation table — each seed subgroup: evidenced/unverified + "
         "edge weights; describe association↔subgroup relations from edges; list external orgs "
         "by forward frequency; note docx media report's own metrics where docx_content.json "
         "contains numbers — Instagram/LinkedIn stats are quoted with their period labels)", "",
         "![Ecosystem map](charts/ecosystem_map.png)", "",
         "## 6. Monthly × hourly patterns (university mechanics)", "",
         "(auto: mechanics list — fixed event slots, weekday peaks, event_start_times modes, "
         "n>=5 only; heatmap + hour histograms referenced)", "",
         "![Weekday × hour heatmap](charts/weekday_hour_heat.png)",
         "![Hour histogram](charts/hour_histogram.png)", "",
         "## 7. Classification method & limitations", "",
         f"(auto: from classification_stats.json — {stats['by_method']} coverage; limitations: "
         "noise category size, unclassified remainder, LLM-labeled share with method='llm', "
         "service messages excluded from narratives, timezone = export-local)"]
    out = ROOT / "reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    md_to_pdf(out, out.with_suffix(".pdf"))
    return out

if __name__ == "__main__":
    print(build())
```
Every parenthesized `(auto: …)` block is implemented as real generation code in place before running — no placeholder text may survive into the built MD.

- [ ] **Step 2: Run, inspect, iterate**

```bash
python -m analysis_tools.build_performance_report
```
Expected: MD contains zero literal "(auto:" strings; PDF renders all 6 figures; every claim carries a count, date, or message reference. Read the built MD end-to-end — fix generation code (not hand-editing the MD) for anything wrong.

- [ ] **Step 3: Commit**

```bash
git add analysis_tools reports/2026-10-14/performance
git commit -m "feat: performance and activity report assembled from artifacts

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 14: Final validation, README, push

**Files:**
- Create: `analysis_tools/validate.py`
- Modify: `README.md` (progress log entry)
- Output: `analysis/validation_report.json`

**Interfaces:**
- Consumes: everything under `analysis/` + both report packages.

- [ ] **Step 1: Write `analysis_tools/validate.py`**

```python
"""Final gates: classification spot-check sampling + cross-artifact reconciliation."""
import json, random
from pathlib import Path
from .common import ROOT, write_json, read_json

def sample_for_review(n_per_cat=20, seed=42):
    random.seed(seed)
    recs = [json.loads(l) for l in open(ROOT / "analysis/classified.jsonl", encoding="utf-8")]
    by_cat = {}
    for r in recs:
        if not r.get("in_window") or r.get("is_service"):
            continue
        for c in r.get("categories") or []:
            by_cat.setdefault(c, []).append(f'{r["chat"]}#{r["message_id"]}\t{r["text_plain"][:160]}')
    return {c: random.sample(v, min(n_per_cat, len(v))) for c, v in by_cat.items()}

def main():
    report = {"samples": sample_for_review()}
    tl = read_json(ROOT / "analysis/timeline.json")
    checks = read_json(ROOT / "anjoman_accounting_information/reports/2026-10-10/final_checks.json")
    fin = Path(ROOT / "reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md")
    perf = Path(ROOT / "reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.md")
    report["artifacts_present"] = {"financial_md": fin.exists(), "financial_pdf": fin.with_suffix(".pdf").exists(),
                                   "performance_md": perf.exists(), "performance_pdf": perf.with_suffix(".pdf").exists(),
                                   "charts": len(list((ROOT / "reports/2026-10-14").rglob("*.png")))}
    report["final_checks_keys"] = sorted(checks.keys())
    write_json(ROOT / "analysis/validation_report.json", report)
    print("samples per category:", {k: len(v) for k, v in report["samples"].items()})

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validation + spot-check review**

```bash
python -m analysis_tools.validate
```
Then dispatch a review agent: read `analysis/validation_report.json`, judge each sample's category label correct/incorrect, compute per-category precision for the top-5 categories by volume. Target ≥ 85%; if a category misses, extend `lexicon.json` (evidence-backed) for that category, re-run Task 6→7→8→9→11→12→13 pipeline stages, and re-validate. Record final precision in `analysis/validation_report.json` as `{"precision": {cat: pct}}`.

- [ ] **Step 3: Update `README.md` progress log** — append one entry:

```markdown
- **2026-10-14** — Performance & Financial analysis pipeline built (`analysis_tools/`): all four
  Telegram exports parsed and classified (10-category taxonomy), event threads correlated across
  chats and joined to the ledger, ecosystem map generated from forwards/mentions. Two new report
  packages: `reports/2026-10-14/financial_monthly/` and `reports/2026-10-14/performance/`.
```

- [ ] **Step 4: Final commit + push**

```bash
git add -A
git status --short | head -30   # review what's being committed
git commit -m "feat: complete 2026-10-14 performance and financial analysis

Reports, datasets, pipeline tools, and validation for the
2025-05-28 → 2026-10-14 association performance analysis.

Co-Authored-By: Claude Code <noreply@anthropic.com>"
git push origin main
git log --oneline -3 && git ls-remote origin main | cut -f1 && git rev-parse main
```
Expected: push succeeds; local `main` == remote. If the pack exceeds ~200 MB (it should not — expected artifact size is a few MB), fall back to the chunked push pattern from 2026-10-13.

---

## Self-Review Notes (completed at plan time)

- **Spec coverage:** parse (T2-3), gate (T4), parallel agents (T5), lexicon+rules (T6), LLM residual (T7), threads+lag (T8), monthly/hourly+mechanics (T9), ecosystem+seed validation (T10), charts via dataviz (T11), financial report w/ gate (T12), performance report (T13), validation ≥85% + README + push (T14). Docx source enters at T3 (parse) and is profiled at T5 and quoted at T13. Spec §5 validation fully mapped.
- **Type consistency:** `classify_message(rec, lexicon)` returns the 4 classification keys consumed by T7/T8; `thread_events(recs, threads, tx_rows)` consumed by T12's builder via `timeline.json`; `monthly_cashflow` shape identical in T9 test and T12 build.
- **Known risks carried into execution:** forwarded-message HTML structure varies by export version (T2 discovery step + T4 population gate); `final_checks.json` key names unknown until T14 (script prints keys); Persian glyph rendering in matplotlib (T11 fix loop).
