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
