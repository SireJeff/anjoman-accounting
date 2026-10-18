"""Translate the EN report catalog to Persian through the Claude API.

Only this module calls the API; builders read the committed fa.json. Keys
whose English changed since translation (hashes.json) or that are missing are
re-translated in chunks; every result is validated (placeholders, backtick
spans, number tokens, bold markers, edge whitespace) before it is accepted.
Raw chunk responses are cached under analysis/claude/i18n/ so re-runs with an
unchanged catalog make no API calls.

Run (VPN on; the API is geo-blocked from this machine otherwise):
    ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" \
        python -m analysis_tools.translate
"""
import argparse
import json
import os
import re
import sys

from pydantic import BaseModel

from . import i18n
from .common import ROOT

MODEL = "claude-opus-5-5"
CHUNK = 60
MAX_ATTEMPTS = 3
CACHE = ROOT / "analysis/claude/i18n"

SYSTEM = """You translate fragments of an internal board report of the Sharif \
University of Technology physics student association (انجمن علمی فیزیک) from \
English into formal written Persian suited to a board document.

Input: JSON with "glossary" (fixed English→Persian terms), "items" (key → English \
fragment) and optionally "notes" (key → problems found in your previous attempt).
Output: one item per input key, with the Persian translation in "fa".

Rules for every fragment:
1. Keep every {placeholder} exactly (same names, same count). Move it where Persian grammar needs it.
2. Copy every `backtick span` verbatim, backticks included.
3. Keep every number exactly as written, in ASCII digits. Never turn numbers into words or words into numbers. Never convert Gregorian dates to Jalali. Keep ranges like 1404/04 – 1405/07 as written.
4. Keep **bold** markers around the corresponding Persian words (same number of ** pairs).
5. Keep IDs (TX0036), @handles, URLs, file names, slugs (dept-weekly-seminars) and Latin proper names verbatim.
6. Whenever a glossary concept occurs, use its glossary Persian term.
7. Use Persian punctuation (، ؛ ؟) and standard ZWNJ spellings (می‌شود، داده‌ها). In ranges write «←» instead of "→" (RTL reading order). Never use « · » as a separator; use «؛» or «،».
8. Fragments can begin or end mid-sentence. Preserve leading and trailing spaces exactly.
9. Keys starting with "data.thread." are event-thread titles. Translate their English words and keep their Persian words as they are.
10. If "notes" lists problems for a key, fix exactly those problems."""


# Keys whose Persian wording is deliberately hand-maintained in fa.json (not a
# mechanical punctuation fix): run() never re-translates them while an fa entry
# exists, even if their English changed; it reports them as "manual_stale"
# instead, and fa.json + hashes.json must then be updated by hand.
MANUAL_KEYS = (
    "chart.ecosystem.legend_title",   # LaTeX \propto replaced by words
    "fin.cash.h_greg",                # column holds Jalali dates in fa
    "fin.ev.peak_item",               # added by hand ("n=" -> "پیام")
    "fin.flag.block_reason",          # Parnian -> پرنیان
    "perf.s7.final",                  # terminology fixes
    "perf.title",                     # title uses Jalali dates (catalog convention)
)


class Item(BaseModel):
    key: str
    fa: str


class Batch(BaseModel):
    items: list[Item]


class Truncated(Exception):
    pass


_PH = re.compile(r"\{(\w+)\}")
_CODE = re.compile(r"`[^`]*`")


def validate(en, fa):
    probs = []
    if sorted(_PH.findall(en)) != sorted(_PH.findall(fa)):
        probs.append(f"placeholders {sorted(_PH.findall(en))} != {sorted(_PH.findall(fa))}")
    if sorted(_CODE.findall(en)) != sorted(_CODE.findall(fa)):
        probs.append("code spans changed (copy every `...` span verbatim)")
    if i18n.number_tokens(_PH.sub("", en)) != i18n.number_tokens(_PH.sub("", fa)):
        probs.append("number tokens changed (keep every number exactly, ASCII digits)")
    if en.count("**") != fa.count("**"):
        probs.append("bold markers changed")
    if en[:1].isspace() != fa[:1].isspace() or en[-1:].isspace() != fa[-1:].isspace():
        probs.append("edge whitespace changed (preserve leading/trailing spaces)")
    try:
        fa.format(**{p: "x" for p in _PH.findall(en)})
    except (KeyError, IndexError, ValueError) as e:
        probs.append(f"str.format fails: {e!r}")
    return probs


def pending(en, fa, hashes):
    return [k for k in sorted(en)
            if k not in fa or (k not in MANUAL_KEYS and hashes.get(k) != i18n.sha(en[k]))]


def manual_stale(en, fa, hashes):
    """Hand-maintained keys whose English changed since their fa was written."""
    return [k for k in MANUAL_KEYS
            if k in en and k in fa and hashes.get(k) != i18n.sha(en[k])]


def call_model(client, items, glossary, notes=None, attempt=0):
    body = {"glossary": glossary, "items": items}
    if notes:
        body["notes"] = notes
    if attempt:
        body["attempt"] = attempt  # retries must not be served from the cache
    payload = json.dumps(body, ensure_ascii=False, sort_keys=True)
    cache = CACHE / f"{i18n.sha(MODEL + SYSTEM + payload)}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    resp = client.messages.parse(model=MODEL, max_tokens=16000, system=SYSTEM,
                                 messages=[{"role": "user", "content": payload}],
                                 output_format=Batch)
    if resp.stop_reason == "max_tokens":
        raise Truncated()
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"model refused chunk: {resp.stop_details}")
    out = {it.key: it.fa for it in resp.parsed_output.items}
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _write(out_dir, fa, hashes):
    (out_dir / "fa.json").write_text(
        json.dumps(dict(sorted(fa.items())), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    (out_dir / "hashes.json").write_text(
        json.dumps(dict(sorted(hashes.items())), indent=1) + "\n", encoding="utf-8")


def run(client, size=CHUNK, out_dir=None):
    out_dir = out_dir or i18n.PKG_DIR
    en = i18n.catalog("en")
    fa = {k: v for k, v in i18n.catalog("fa").items() if k in en}
    hashes = {k: v for k, v in i18n.catalog("hashes").items() if k in en}
    glossary = i18n.catalog("glossary")
    todo, failed, done = pending(en, fa, hashes), {}, 0
    for attempt in range(MAX_ATTEMPTS):
        if not todo:
            break
        queue = [todo[i:i + size] for i in range(0, len(todo), size)]
        retry = []
        while queue:
            keys = queue.pop(0)
            notes = {k: failed[k] for k in keys if k in failed} or None
            try:
                got = call_model(client, {k: en[k] for k in keys}, glossary, notes, attempt)
            except Truncated:
                if len(keys) == 1:
                    failed[keys[0]] = ["output truncated"]
                    retry.append(keys[0])
                    continue
                mid = len(keys) // 2
                queue[:0] = [keys[:mid], keys[mid:]]
                continue
            for k in keys:
                probs = ["missing from response"] if k not in got else validate(en[k], got[k])
                if probs:
                    failed[k] = probs
                    retry.append(k)
                else:
                    fa[k], hashes[k] = got[k], i18n.sha(en[k])
                    failed.pop(k, None)
                    done += 1
        _write(out_dir, fa, hashes)
        todo = retry
    _write(out_dir, fa, hashes)
    i18n.reload()
    return {"translated": done, "failed": failed,
            "manual_stale": manual_stale(en, fa, hashes)}


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set. Run:\n  ANTHROPIC_API_KEY=\"$(cat "
              "~/.config/anthropic/anjoman_key)\" python -m analysis_tools.translate",
              file=sys.stderr)
        sys.exit(2)
    import anthropic
    # accept-encoding: identity works around a local httpx2 decompression bug
    # (TypeError: process() takes no keyword arguments) seen on this machine
    # with the SDK's default compressed responses; unrelated to auth/network.
    client = anthropic.Anthropic(max_retries=4, default_headers={"accept-encoding": "identity"})
    res = run(client)
    print(f"translated {res['translated']} keys; {len(res['failed'])} failed")
    for k, p in res["failed"].items():
        print(f"  FAILED {k}: {'; '.join(p)}", file=sys.stderr)
    for k in res["manual_stale"]:
        print(f"  MANUAL {k}: English changed; update fa.json and hashes.json by hand",
              file=sys.stderr)
    sys.exit(1 if res["failed"] else 0)


if __name__ == "__main__":
    main()
