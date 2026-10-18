# analysis_tools/audit/rules.py
"""Decision-id -> patch tables for the audited ledger re-publication.

Two value sentinels appear below and are only documented here: "@original"
(keep the row's existing amount_original) and "@append:..." (append text to
the row's notes). They are interpreted by apply() (Task 7), not by this
module.
"""

from .load import AuditError

Patch = tuple[str, str, object]

RULES = {
    "S-01": [], "B-01": [], "A-01": [],
    "D-01": [],
    "D-02": [("TX0010", "status", "Duplicate"),
             ("TX0010", "duplicate_of", "TX0009")],
    "D-03": [(f"TX00{n}", "status", "Supporting detail") for n in (52, 53, 54, 55)]
          + [(f"TX00{n}", "parent", "TX0050") for n in (52, 53, 54, 55)],
    "D-04": [(f"TX00{n}", "status", "Supporting detail")
             for n in range(64, 75)]
          + [(f"TX00{n}", "parent", "TX0062;TX0063") for n in range(64, 75)],
    "D-05": [("TX0069", "duplicate_of", "")],
    "D-06": [("TX0042", "status", "Supported")],
    "R-01": [("TX0036", "direction", "Payment"),
             ("TX0036", "status", "Supported")],
    "R-02": [("TX0031", "amount_toman", 230000.0),
             ("TX0031", "amount_original", "@original")],
    "R-03": [("TX0018", "unit_original", "rial"),
             ("TX0018", "amount_toman", 1765000.0),
             ("TX0018", "amount_original", 17650000.0)],
    "R-04": [("TX0001", "open_item", "OI-01")],
    "R-05": [],
    "R-06": [("TX0049", "amount_toman", 10003780.0),
             ("TX0049", "amount_original", 100037800.0),
             ("TX0049", "unit_original", "rial"),
             ("TX0049", "date_jalali", "1404/10/01")],
    "R-07": [("TX0058", "amount_toman", 275000.0),
             ("TX0058", "amount_original", "@original"),
             ("TX0056", "status", "Payable"),
             ("TX0058", "status", "Payable")],
    "R-08": [],
    "R-09": [("TX0062", "open_item", "OI-02"),
             ("TX0063", "open_item", "OI-02")],
    "R-10": [],
    "R-11": [("TX0082", "project", "Summer School 1405")],
    "R-12": [("TX0093", "open_item", "OI-03"),
             ("TX0094", "open_item", "OI-03")],
    "R-13": [("TX0096", "period_jalali", "1405/04"),
             ("TX0096", "notes", "@append:on or before 1405/04/08")],
    "R-14": [("TX0013", "evidence_label", "original ledger only"),
             ("TX0013", "open_item", "OI-04")],
    "R-15": [("TX0045", "evidence_label", "original ledger only"),
             ("TX0045", "open_item", "OI-05")],
    "R-16": [("TX0095", "evidence_label", "original ledger only"),
             ("TX0095", "open_item", "OI-06")],
    "U-01": [("TX0001", "date_gregorian", "2025-07-24"),
             ("TX0001", "date_basis", "reports posted")],
    "U-02": [(f"TX00{n}", "date_gregorian", "2025-09-06") for n in (14, 16, 17)]
          + [(f"TX00{n}", "date_basis", "event-day proxy") for n in (14, 16, 17)],
    "U-03": [("TX0015", "date_gregorian", "2025-09-04"),
             ("TX0015", "date_basis", "Telegram post time")],
    "U-04": [("TX0044", "date_gregorian", "2025-11-19"),
             ("TX0044", "date_basis", "on or before"),
             ("TX0044", "period_jalali", "1404/08")],
    "U-05": [("TX0036", "date_gregorian", "2025-10-29"),
             ("TX0036", "date_basis", "event-day proxy")],
    "U-06": [("TX0074", "date_gregorian", "2025-12-24"),
             ("TX0074", "date_basis", "printed")],
    "U-07": [("TX0060", "period_jalali", "1404/10"),
             ("TX0060", "date_basis", "by event association")],
    "U-08": [(f"TX00{n}", "date_basis", "month only")
             for n in (10, 13, 25, 45, 47, 48, 58, 93, 95)],
    "P-01": [("TX0080", "project", "Summer School 1405"),
             ("TX0080", "category", "Advertising")],
    "P-02": [("TX0089", "project", "Intro Event 1405"),
             ("TX0089", "category", "Hospitality")],
    "P-03": [("TX0034", "amount_toman", 1000000.0),
             ("TX0034", "amount_original", "@original")],
    "P-04": [],
    "P-05": [(tx, "open_item", f"OI-{n:02d}") for n, tx in enumerate(
        ["TX0043", "TX0061", "TX0075", "TX0076", "TX0077", "TX0078",
         "TX0079", "TX0081", "TX0090", "TX0091", "TX0092"], start=8)],
}

NO_FIELD_CHANGE = {"S-01", "B-01", "A-01", "D-01", "R-05", "R-08", "R-10",
                   "P-04"}

NEW_ROWS = {"TX0034-B": {
    "copy_from": "TX0034",
    "set": {"amount_toman": 500000.0, "amount_original": "@original",
            "project": "Association operations", "category": "Equipment"}}}

PENDING_ITEMS = [{"id": "PI-01", "project": "Yalda 1404", "amount_toman": 275584,
                  "counterparty": "سیدبردیا احمدی‌مروست",
                  "note": "unreimbursed remainder of TX0050 (decision R-08)"}]

OPEN_ITEMS = [
    {"id": "OI-01", "txs": ["TX0001"], "amount_toman": 1000.0,
     "question": "The posted report shows 33,643,000 for this receipt; the ledger has 33,642,000 (1,000 difference).",
     "settles": "the original report/workbook page for TX0001"},
    {"id": "OI-02", "txs": ["TX0062", "TX0063"], "amount_toman": 195860.1,
     "question": "195,860.1 toman of the volunteer-reported purchases (TX0064-74) is not covered by the TX0062/63 reimbursement of 4,050,000.",
     "settles": "the missing receipt(s) or the volunteer's confirmation of the total"},
    {"id": "OI-03", "txs": ["TX0093", "TX0094"], "amount_toman": 4235000.0,
     "question": "Intro Event 1405 evidence implies 4,235,000 beyond the recorded net of 23,000,000; the gap is unexplained.",
     "settles": "bank statement or receipts for the Intro Event 1405 period"},
    {"id": "OI-04", "txs": ["TX0013"], "amount_toman": None,
     "question": "No evidence outside the original ledger; the row is kept Supported on the original ledger's authority.",
     "settles": "a source receipt or message for TX0013"},
    {"id": "OI-05", "txs": ["TX0045"], "amount_toman": None,
     "question": "No evidence outside the original ledger; the row is kept Supported on the original ledger's authority.",
     "settles": "a source receipt or message for TX0045"},
    {"id": "OI-06", "txs": ["TX0095"], "amount_toman": None,
     "question": "No evidence outside the original ledger; the row is kept Supported on the original ledger's authority.",
     "settles": "a source receipt or message for TX0095"},
    {"id": "OI-07", "txs": [], "amount_toman": None,
     "question": "Implied bank movements are not in the ledger: ~3,163,000 debits around 1405/05/21-22; ~35.2M credits between 1404/12 and 1405/05; ~12.8-19.8M debits between 1404/09 and 1404/12; inflow anomalies at TX0007 and TX0024.",
     "settles": "the Bank Shahr statement covering 1404/05-1405/06"},
] + [
    {"id": f"OI-{n:02d}", "txs": [tx], "amount_toman": None,
     "question": "Purpose unknown - the row could not be assigned to an event/program from evidence.",
     "settles": "owner identifies the purpose; then reassign project and category"}
    for n, tx in enumerate(["TX0043", "TX0061", "TX0075", "TX0076", "TX0077",
                            "TX0078", "TX0079", "TX0081", "TX0090", "TX0091",
                            "TX0092"], start=8)
]


def validate(register):
    """Spec §4.2 refusals, static side: unknown rule id, uncovered register id,
    unknown patch field, unknown open-item refs."""
    from . import load
    reg_ids = {e["id"] for e in register}
    unknown = set(RULES) - reg_ids
    if unknown:
        raise AuditError(f"rules without register ids: {sorted(unknown)}")
    uncovered = reg_ids - set(RULES) - NO_FIELD_CHANGE
    if uncovered:
        raise AuditError(f"register ids without rules: {sorted(uncovered)}")
    valid = set(load.SOURCE_COLS) | set(load.AUDIT_COLS)
    for rid, patches in RULES.items():
        for tx, field, value in patches:
            if field not in valid:
                raise AuditError(f"{rid}: unknown field {field!r}")
    oi_ids = {o["id"] for o in OPEN_ITEMS}
    for rid, patches in RULES.items():
        for tx, field, value in patches:
            if field == "open_item" and value not in oi_ids:
                raise AuditError(f"{rid}: unknown open item {value!r}")
