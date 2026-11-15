# Proposed Persian Governance Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to implement task-by-task. Checkboxes track deliverables; human prose is reviewed, not tested through exact-copy assertions.

**Goal:** Deliver a coherent, traceable proposed Persian governance and handover suite for seven incoming members.
**Architecture:** Four canonical Markdown documents plus guide, operations/forms and adoption/coverage companion. A governance-only renderer produces A4 DOCX/PDF without changing frozen reports.
**Tech Stack:** Python, python-docx, Markdown, WeasyPrint, PyMuPDF, pytest.
**Spec:** `docs/superpowers/specs/2026-11-15-governance-finalization-design.md`.

## Global Constraints

All rules proposed, not adopted. Raw sources/private evidence remain outside git. Preserve historical reports, article identifiers and user files. No guessed legal approvals or credentials. Sponsor: گروه صنعتی شیشه کاوه. No merge/push/publication.

## Review Focus

- Lossy PDF extraction cannot establish complete source coverage; explicitly review original page images and preserve limitations.
- Seven-person voting with vacancies/recusal cannot create a smaller group's power to remove elected members.
- Missing financial documents must not cause actual cash movements to disappear.
- Mixed-direction links, nested lists and tables must preserve text and reading order in DOCX/PDF.
- A proposed rule cannot gain authority from a guide, historical report or generated approval field.

## Tasks

### Task 1: Source coverage and authority register
Files: create `docs/governance/review-adoption.md`; read original `sources/governance/` from primary checkout.
Consumes: reference originals/extracts and existing D1–D4. Produces: safe source IDs, source/provision dispositions, authority and decision register, experience-to-rule mapping.
- [x] Inventory every available source and classify extraction quality/authority.
- [x] Review unreadable source pages and account for Resana provisions; mark unresolved number/date readings honestly.
- [x] Record substantive recommendations and institution-only confirmations; keep original evidence local.
- [x] Review every row for unsupported completeness or legal claims; explicitly distinguish 56 article rows from independent enumeration of 69 provisos.

### Task 2: Harden canonical rules and handover operations
Files: modify four `docs/governance/*.md` masters; create `handover-guide.md` and `operations-forms.md`; update README.
Consumes: Task 1 recommendations. Produces: internally consistent version 1.1 proposed suite, canonical operational references and clear adoption blockers.
- [x] Revise proposed status and qualified authority, finance/voting edge cases without inventing approval.
- [x] Add practical forms and tea-organizer layer while preserving volunteer participation rights.
- [x] Review source mapping destinations and scenario outcomes; run governance lint.

### Task 3: Structured Persian delivery pipeline
Files: modify `analysis_tools/governance_build.py`; create `analysis_tools/governance_layout.py`; extend `analysis_tools/tests/test_governance_build.py`.
Interfaces: preserve `md_to_docx_rtl(md_text: str, title: str) -> Document` and `build_all(out_dir: Path | None = None) -> list[Path]`; extra companions are included when present beside canonical masters. Keep two returned document paths per master for compatibility.
- [x] Write failing tests for A4/semantic headings/linked contents, real lists and tables, links/code/mixed text, governance-only PDF contents and companion builds.
- [x] Run focused tests and confirm expected failures.
- [x] Implement minimal semantic renderer and isolated PDF styling; keep byte-stable DOCX output.
- [x] Run focused tests and full suite; inspect output parity.

### Task 4: Validation, visual review and proposed release
Files: generated `docs/governance/build/*`; create `docs/governance/validation.md`; update root README governance links only.
Consumes: seven authored documents. Produces: verified proposed package with honest limitations.
- [x] Build all documents and run structural lint, text/PII checks, font/page metadata and full tests.
- [x] Render PDF pages to private scratch, inspect contact sheets and problem pages; render Word with explicit user authorization.
- [x] Conduct explicit scenario walkthrough, record outcomes and unresolved institutional gates.
- [x] Request independent whole-change review; provider quota exhausted, so record weaker author self-review instead of claiming independence.
- [x] Fix important findings with regression tests for code, rebuild and reverify; package prepared for local checkpoint without merging/pushing. Missing-master regression was RED→GREEN; final suite 292 passed. See `docs/governance/validation.md` for evidence and limitations.

## Execution rulings and limitations

- Native worktree started detached; a local named branch was created with main unchanged.
- Independent renderer work proceeded while read-only source-review jobs were pending; those jobs failed due provider quota, so the author reviewed sources directly.
- Recommendations remain proposed and require explicit council/institutional decisions; no legal approval was inferred.
- Frozen reports were preserved; their historical 'approved' wording is corrected by an explicit note in the companion, not by rewriting history.
- The crosswalk uses safe source IDs and 56 individual Resana article rows; no database was introduced, and independent enumeration of all 69 source provisos remains outstanding.
- A portable allowlisted ZIP was added without changing build_all's return contract; it includes only generated Word/PDF files and the start note.
- Native Word numbering may follow local Office numeral settings; the distributed PDF uses Persian page numbering.
- Independent institutional/legal review and actual newcomer testing remain future adoption gates, not technical release claims.
