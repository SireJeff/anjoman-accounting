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
