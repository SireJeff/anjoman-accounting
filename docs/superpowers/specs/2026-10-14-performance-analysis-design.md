# Anjoman Performance & Financial Analysis — Design Spec

**Date:** 2026-10-14
**Status:** Approved design, pending implementation plan
**Owner:** SireJeff (board) with Claude Code

## 1. Goal

Produce two separate, evidence-linked analytical reports covering 2025-05-28 → 2026-10-14 (the current administration's window):

1. **Financial Report (monthly)** — cashflow reorganized into monthly (Jalali) views from the reconciled ledger, with time-of-day patterns where message timestamps exist.
2. **Performance & Activity Report** — a categorized analysis of the association's activities across four Telegram chats, merged on date and concurrency, with an ecosystem map of the association and its subgroups.

Both reports use **monthly classification with detail down to the hour**, and surface the university's operational mechanics (recurring time slots, e.g. "events always start 13:30").

**Audience:** internal board. English primary, Persian names/terms inline. **Not** public-facing; private-group content used candidly.

## 2. Sources (6 inputs)

| # | Source | Location | Volume | Coverage |
|---|---|---|---|---|
| 1 | Private group export | `anjoman_private_group_report/` | ~5,309 msgs | 2025-07-16 → 2026-10-12 |
| 2 | Public group export | `anjoman_public_group_export/ChatExport_2026-10-13/` | ~6,136 msgs | 2026-08-10 → 2026-10-12 |
| 3 | Channel export | `anjoman_channel_content/` | ~3,015 msgs | 2015-09-28 → 2026-10-10 (window-filtered) |
| 4 | Accounting group export | `anjoman_accounting_information/anjoman_accounting_group_export/` | 158 msgs | 2025-07-24 → 2026-06-27 |
| 5 | Reconciled ledger | `anjoman_accounting_information/reports/2026-10-10/` (final_data.json, Transactions.csv) | 96 TX | 1404/05 → 1405/07 |
| 6 | Media performance docx | `گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx` (repo root) | 322 KB | to be parsed |

Messages outside the window are excluded from analytics but retained in the dataset (flagged) for continuity checks.

## 3. Activity taxonomy (approved 2026-10-14)

Multi-label per message; every message also carries `event_ref` (event thread key) where applicable.

| # | Category | Captures |
|---|---|---|
| 1 | Education — Courses | Summer School 1404 & 1405 (Python/LaTeX/Mathematica), instructors, registration |
| 2 | Events | Intro Event 1405, Sharif Frontiers nightly webinars, expert talks, gatherings (دورهمی) |
| 3 | Publications — شباهنگ | Magazine issues, article series (شعر و فیزیک), writer/editor recruitment |
| 4 | Media & Outreach | LinkedIn/Instagram launch, channel announcements, cross-promotions |
| 5 | Governance & Decisions | Board coordination, planning, task assignment, polls; `is_decision` flag on resolved choices |
| 6 | Finance Operations | Payments, receipts, treasury threads; joined to ledger TX ids |
| 7 | Website & Tech | alenush.com domain, VM budget, site build |
| 8 | Community & Social | Member chatter, off-topic — engagement layer, counted not narrated |
| 9 | Coordination & Logistics | Scheduling, rooms, printing (stickers), catering, equipment |
| 10 | Meta / Noise | Slang one-liners, stickers — volume honesty, excluded from narrative |

## 4. Architecture

Four stages, all scripted under `analysis_tools/` (mirroring `accounting_tools/` conventions: reproducible stages, cached LLM JSON, count reconciliation):

### Stage 1 — Parse (deterministic)

`parse_exports.py` → `analysis/messages.jsonl`, one record per message:

```
{chat, message_id, timestamp_utc, jalali_month, hour, weekday,
 sender, forwarded_from, text_plain, media_type[], has_poll,
 is_reply, reply_to, in_window,           // Stage 1 output
 event_ref?, categories[], is_decision?, confidence, method}  // filled in Stage 3
```

- Telegram HTML parsed with lxml (structure: `div.message`, `date_details` title timestamps, `forwarded body` origin spans, media wrappers, polls).
- `forwarded_from` extracted from forwarded-body origin spans (1,271 forwarded messages across sources; Persian labels «ارسال‌شده از»).
- Jalali month via `jdatetime`; hour/weekday from timestamp.
- Docx parsed with python-docx → `analysis/docx_content.json` (paragraphs, tables, embedded numbers preserved).
- **Verification gate:** per-source message counts from the parser must match raw `grep -c 'class="message default'` totals (± boundary messages with non-standard classes, each explained).

### Stage 2 — Parallel source exploration (explicit user requirement)

Dispatch one exploration agent per source (4 chats + ledger + docx = 6 agents, run concurrently). Each returns a **source profile**:

- volume timeline (messages/month), participant list and share, media mix
- forwarded-origin inventory (for the ecosystem graph)
- candidate event threads and their anchor keywords/dates
- observed recurring time patterns (e.g. fixed event hours)
- financial signal list (ledger agent: TX coverage, gaps, unlinked messages in accounting group)

Profiles are cached as `analysis/profiles/<source>.json` and feed Stage 3's lexicons and thread registry. Agents are read-only explorers; all conclusions land as data files, not prose.

### Stage 3 — Classify (layered)

1. **Structural rules** — channel post templates (event announcements with date/time blocks), polls, media-only, form links (docs.google.com/forms), username-tag batches, forwarded items (inherit origin-based hints).
2. **Lexicon pass** — Persian+English keyword/regex lexicon per category, built from Stage 2 profiles (e.g. مدرسه تابستانه, ثبت‌نام, حق‌الزحمه, بلیت, دورهمی, وبینار, شباهنگ, تکانه, دامنه).
3. **LLM residual pass** — unclassified or low-confidence messages batch-classified via cached JSON (pattern of `accounting_tools/claude_pipeline.py`); every LLM label records `method: "llm"` and its cached response file.

Output: `analysis/classified.jsonl` + `analysis/classification_stats.json` (per-category counts, method distribution, confidence histogram).

### Stage 4 — Correlate & build reports

`correlate.py` → `analysis/timeline.json`:

- **Event threads:** each `event_ref` gets start/end dates, chats involved, message counts, linked TX ids, announcement lag (planning → announcement → delivery → payment → public buzz).
- **Monthly matrices (Jalali):** messages by chat × category per month; cashflow by category/project per month (from ledger `period_jalali`).
- **Hour-of-day analytics:** message-hour distributions per chat/category; event start times parsed from announcements; TX timestamps via `message_ids` join; weekday×hour heatmaps; recurring-slot detection (fixed weekday+hour combinations).
- **Ecosystem graph:** nodes = association + subgroups + external orgs; edges from forwarded-from frequency, @mentions, cross-promotions → `analysis/ecosystem.json` (nodes/edges/weights) rendered as a diagram in the performance report.

Seed entities (user-provided map, verified/re-weighted against data):

| Entity | Handle | Type |
|---|---|---|
| Physics Tea announcements | @physics_tea_sessions | Announcement channel |
| Tea in-person chat | (linked group) | Discussion group |
| شباهنگ journal | @shabahang_sut | Student journal |
| Sharif Astronomy Group | @sharifastronomy | Specialized branch |
| تکانه journal | @takaneh_physics_sharif | Scientific journal |
| Physics summer school | @sutschools | School channel |
| Quanta study circles | @QuantaSC | Study circles |

The map is a hypothesis: data confirms, re-weights, or extends it (external orgs like بلور surface from forwards). Unverified claims in the seed map are marked as such.

### Reports

`build_financial_report.py` and `build_performance_report.py` → `reports/2026-10-14/`:

```
reports/2026-10-14/
├── financial_monthly/
│   ├── Anjoman_Financial_Report_Monthly.md / .pdf
│   └── charts/ (monthly cashflow by category/project, cumulative, hour-of-day)
└── performance/
    ├── Anjoman_Performance_Activity_Report.md / .pdf
    └── charts/ (activity timelines, category breakdowns, heatmaps, ecosystem map)
```

**Financial report contents:** monthly cashflow tables (Jalali months, Gregorian inline), category/project schedules, evidence links (TX → messages → receipts), hour-pattern notes on payments/receipts, explicit "derived from reconciled ledger 2026-10-10; Review-status TXs flagged" caveat. **Does not re-audit.**

**Performance report contents:** executive summary; phase narrative (semester-phased: summer 1404 → academic year → summer 1405 → fall 1405); category deep-dives with per-month tables; cross-chat correlation case studies (announcement lags, decision→delivery chains); ecosystem map with roles/relations; monthly × hourly pattern section (university mechanics); limitations.

Charts follow the `dataviz` skill's system when rendered.

## 5. Validation

- Parser counts reconcile per source (Stage 1 gate).
- Ledger totals in financial report reconcile against `reports/2026-10-10` final totals to the toman; any newly surfaced evidence is listed, not silently merged.
- Classification spot-check: 20 random messages per category reviewed; precision target ≥ 85% on the top-5 categories.
- Event threads: each thread's delivery date cross-checked against channel announcement and ledger TX where present.
- Hour patterns: only asserted when n ≥ 5 occurrences.

## 6. Out of scope

- Re-auditing or modifying the reconciled ledger (Review-status items stay flagged)
- Public/member-facing variants, Persian translation of the new reports
- Interactive dashboard
- Pre-window history analysis (2015–2025 channel content), beyond continuity notes

## 7. Execution notes

- Parallel agents (Stage 2) run concurrently; each is read-only and returns JSON-structured profiles.
- LLM calls are cached; re-runs read cache. `ANTHROPIC_API_KEY` in env; never stored in repo.
- Large intermediates (`analysis/`) stay untracked or gitignored except final datasets referenced by reports.
- Python deps: lxml, jdatetime, python-docx, matplotlib, reportlab (PDF), pandas.
