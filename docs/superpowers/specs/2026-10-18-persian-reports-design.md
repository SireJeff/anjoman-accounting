# Persian Versions of the 2026-10-14 Reports — Design Spec

**Date:** 2026-10-18
**Status:** Approved design (brainstormed 2026-10-17/18), pending implementation plan
**Owner:** SireJeff (board) with Claude Code
**Branch:** `feature/persian-reports` → PR → merge commit

## 1. Goal

Produce Persian (FA) versions of both reports merged in PR #2:

- `reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.md/.pdf`
- `reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.md/.pdf`

The FA reports have the same numbers, the same sections, and charts carrying the same data. Persian is generated from the same computation as English (no hand-translated Markdown), so the numbers cannot drift between languages. The English reports must not change.

## 2. Decisions (from brainstorming)

| Topic | Decision |
|---|---|
| Translation method | **Approach A: message catalog.** English prose is extracted into named templates, translated once through the Claude API, cached and committed as `fa.json`. |
| API | Claude API via `ANTHROPIC_API_KEY` from the environment, never stored in the repo. Raw HTTP pattern of `anjoman_accounting_information/accounting_tools/claude_pipeline.py` (no `anthropic` package dependency). Model `claude-opus-5-5`. |
| PDF engine (FA) | Markdown → HTML (`lang="fa" dir="rtl"`) → **WeasyPrint**, the method behind the 2026-10-10 Persian report. WeasyPrint 68.1 is verified working on this Windows machine. The English PDFs stay on reportlab, unchanged. |
| Font | Tahoma, the system font that the charts already use. |
| Charts | **Persian-labeled variants** in `charts_fa/` beside `charts/`: same data and palette, Persian titles, axes, legends and Jalali ticks. |
| Digits | Persian digits (۰–۹) and Persian thousands separator `٬` / decimal `٫` everywhere in FA prose and tables, following the 2026-10-10 precedent. IDs (`TX0036`), file names, code and Latin handles (`@QuantaSC`) stay Latin. |
| Dates | Jalali primary (`۱۴۰۴/۰۷/۱۲`). The Gregorian date appears in parentheses only where the English report shows a Gregorian value. Hours are `۱۳:۳۰`. |

## 3. Components

```
analysis_tools/
  i18n/
    __init__.py      t(key, lang, **kw); num(v, lang, decimals=0); pct(...); digits(s, lang)
    en.json          English templates (verbatim from today's builders)
    fa.json          Persian templates (generated, committed, hand-editable)
    glossary.json    fixed EN→FA term map (categories, projects, statuses, chats,
                     weekdays, months, section names, ledger terms)
    hashes.json      sha1 of each en template at translation time (staleness check)
  translate.py       en.json + glossary → Claude API → fa.json (incremental)
  report_common.py   + md_to_pdf_rtl(md_path, pdf_path, title, footer)
  charts.py          render_all(lang="en"|"fa"); fa → charts_fa/
  build_financial_report.py    build(lang="en"); CLI --lang en|fa
  build_performance_report.py  build(lang="en"); CLI --lang en|fa
```

### 3.1 `i18n` module

- `t(key, lang, **kw)` looks up the template in `en.json` / `fa.json` and runs `str.format(**kw)`. Unknown key → `KeyError`. When `lang == "fa"` and the key is stale (`hashes.json` sha1 ≠ current en sha1) → `RuntimeError("fa.json stale for <key>; run translate.py")`.
- Values reach templates **already formatted**: builders pass `num(v, lang)` output, never raw floats, so templates contain no format specs.
- `num(v, lang)`: `fa` → Persian digits, `٬` thousands, `٫` decimal. `en` → exactly today's `f"{v:,.0f}"` behavior (the `—` for zero/None stays a builder concern, as now).
- `digits(s, lang)` converts digits inside an already-built string (dates, hours, `n=62`). Text inside backticks and anything matching `TX\d{4}`, `@\w+` or a URL/file name is skipped.
- Glossary lookups (`term(name, lang)`) cover table row labels drawn from data keys: category slugs, project names, statuses, chat ids, weekday names. Unknown term in `fa` → returned unchanged and logged once (data-derived Persian text such as thread titles and snippets is already Persian).

### 3.2 Builder refactor

- Every English string literal and f-string in `build_financial_report.py` and `build_performance_report.py` becomes `t("<section>.<name>", lang, ...)`. Computation, ordering, gates and asserts are untouched.
- `fmt`/`pct`/`pct2`/`jdate` and similar helpers gain a `lang` argument and route through `i18n`.
- Markdown structure (headings, table pipes, `![..](charts/x.png)`) stays in code. Only the human text goes into templates. In `fa`, image paths point to `charts_fa/`.
- Outputs: `lang="en"` writes today's paths. `lang="fa"` writes `*_FA.md` and `*_FA.pdf` beside them.
- The reconciliation `_gate` runs in both modes before anything is written.

### 3.3 `translate.py`

- Fails immediately with a clear message if `ANTHROPIC_API_KEY` is unset.
- Selects keys that are missing from `fa.json` or stale per `hashes.json`. They are sent in chunks of at most 60 templates per request, as a JSON object `{key: english}`, together with the glossary.
- Prompt rules: formal written Persian suited to an internal board report. Translate prose only. Keep every `{placeholder}` exactly. Keep backticked spans, IDs, handles, URLs and file names verbatim. Use glossary terms verbatim. Return JSON `{key: persian}` only.
- Validation per key: the placeholder set must equal the English set and backticked spans must be preserved. A failing key is retried, at most 3 attempts in total. After that it is listed in the run's error output and left absent, so the builders fail loudly.
- `stop_reason == "max_tokens"` → the chunk is halved, not repeated.
- Raw responses are cached in `analysis/claude/i18n/<chunk-hash>.json`. Re-runs with an unchanged catalog make no API calls.

### 3.4 RTL PDF (`md_to_pdf_rtl`)

- python-markdown (`tables`, `fenced_code` extensions) → HTML fragment wrapped in `<html lang="fa" dir="rtl">` with an inline stylesheet adapted from `reports/2026-10-10/fa/Anjoman_Financial_Report_FA.html`: Tahoma, A4, right-aligned text and cells, `thead {display: table-header-group}`, `tr {break-inside: avoid}`, images max-width 100%, footer `@bottom-center` «انجمن علمی فیزیک | <report name> | صفحه N».
- Numeric table cells and `code` spans get `direction: ltr; unicode-bidi: isolate` (numbers stay in reading order; IDs do not flip).
- Wide month-schedule tables: the font size steps down (class added when a table has more than 8 columns), as in the English PDF.
- Image `src` is resolved relative to the MD file's directory (`base_url`).

### 3.5 Charts (`lang="fa"`)

- `_chrome` titles, subtitles and axis labels, legend titles and entries, the hour-histogram suptitle, the ecosystem title and legend, and the cashflow legend all come from `t()` / `term()`.
- Month ticks use Jalali month labels with Persian digits. Numeric tick formatter `_mfmt` gains Persian digits in `fa`.
- Text passes through `fa()` unchanged: matplotlib already shapes Persian (measured earlier; reshaper + bidi double-reverses, see `charts.py` comment).
- Output `reports/2026-10-14/{financial_monthly,performance}/charts_fa/<same file names>.png`.

## 4. Testing

New tests in `analysis_tools/tests/test_i18n.py`. The existing 123 tests stay green.

1. **English byte-identity:** `build(lang="en")` for both reports reproduces the MD committed on main byte-for-byte. Proves the refactor changed nothing.
2. **Catalog integrity:** `en.json` and `fa.json` have identical key sets. Each key's `{placeholder}` sets are equal. Every en key is referenced by a builder or by `charts.py` (no orphans), and every referenced key exists.
3. **Number parity:** multiset of number tokens in EN MD == the one in FA MD after Persian→Latin digit and separator normalization. Exclusions are explicit and listed in the test (e.g. section numbers if the FA headings drop them).
4. **Formatting units:** `num(1234567.5, "fa", 1) == "۱٬۲۳۴٬۵۶۷٫۵"`. Jalali date and hour formatting. `digits()` leaves `TX0036`, `@QuantaSC`, backticked spans and file names Latin.
5. **Glossary enforcement:** for each glossary entry whose English term appears in the EN report, its fixed Persian term appears in the FA report.
6. **Translation validator:** unit tests of placeholder and backtick validation on synthetic good/bad translations (no API call).
7. **Gates:** FA build fails exactly as EN does when the ledger reference is corrupted.

### Visual verification (required before done)

- `pdftoppm` rasterizes representative pages of both FA PDFs into the scratchpad: title page, a wide schedule table, a chart page, a bullet list, a page with `TX` IDs and handles. Each is inspected for joined letters, RTL flow, right-aligned tables, unflipped numbers and IDs, and a readable footer. Representative PNGs are shown to the user.
- At least one `charts_fa` PNG per chart type is inspected.

## 5. Error handling

| Condition | Behavior |
|---|---|
| `ANTHROPIC_API_KEY` missing | `translate.py` exits with setup instructions. Builders never call the API. |
| `fa.json` missing/stale key | FA build raises naming the key(s). The EN build is unaffected. |
| Placeholder/backtick mismatch from model | Retried, at most 3 attempts in total, then reported and left absent. |
| Output truncated | Chunk halved. |
| HTTP 429/5xx | Backoff retry (precedent pattern). Other HTTP errors are raised. |
| Low disk (< 1 GB free on C:) | Checked before chart/PDF generation. The build stops with a message. |

## 6. Out of scope

- Any change to English report content or numbers.
- Job 2 (ledger audit + per-event balance sheets). It gets its own spec after this merges.
- Persian versions of other artifacts (spec, plan, README beyond a progress line).
