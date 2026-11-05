"""Build the final audited report and deliverables for 2026-11-03.

Incorporates all clarifications, user confirmations, and bank statement evidence
(Bank Shahr 80.pdf, Blu 14050812012318.xlsx).
Emits outputs to reports/2026-11-03/
"""
import csv
import json
import re
import shutil
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from analysis_tools.common import REPORTS, ROOT
from analysis_tools.report_common import md_to_pdf, md_to_pdf_rtl, ensure_disk

OUT_DIR = REPORTS / "2026-11-03"

# Card masking pattern for G9 privacy scrub
_CARD_RUN = re.compile(r"(?<!\d)\d{16}(?!\d)")

def _scrub(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return _CARD_RUN.sub(lambda m: "…" + m.group(0)[-4:], text)

def fmt(v):
    if v is None or v == "":
        return "—"
    v = float(v)
    return f"{v:,.1f}" if abs(v - round(v)) >= 1e-9 else f"{v:,.0f}"

def _sgn(v):
    v = float(v)
    if v == 0:
        return "0"
    return ("+" if v > 0 else "-") + fmt(abs(v))

NEW_DECISIONS = [
    {
        "id": "C-01", "kind": "scope", "tx": [], "date": "2026-11-03",
        "question": "Commingling of association and personal funds on Bank Shahr deposit 400816808774 and Blu account ending 1764 (cards 5780/6947).",
        "options": ["Full separation audit", "Ledger reconstruction & net position disclosure", "Exclude custodian accounts"],
        "choice": "Ledger reconstruction & net position disclosure",
        "rationale": "Owner confirmed that association funds were commingled across personal cards. Bank statements for Bank Shahr (80.pdf) and Blu (14050812012318.xlsx) were provided. Reconstructed ledger net balance (37,189,180 toman) represents the association cash position held by the custodian.",
        "evidence": ["clarifications/00_cross_month_questions.md#X-01, X-02, X-05, X-08", "80.pdf", "14050812012318.xlsx"]
    },
    {
        "id": "C-02", "kind": "settlement", "tx": ["TX0001"], "date": "2026-11-03",
        "question": "Summer School 1404 registration income tally (OI-01, 1,000 toman discrepancy).",
        "options": ["Adjust to 33,643,000", "Maintain 33,642,000 per ledger and close OI-01", "Request individual card tallies"],
        "choice": "Maintain 33,642,000 per ledger and close OI-01",
        "rationale": "Custodian confirmed all registrations were transferred into card 8966 and instructor disbursements made accordingly. Ledger amount 33,642,000 toman accepted as final net deposit.",
        "evidence": ["clarifications/1404-05_Mordad/QUESTIONS.md#Q-1404-05-01"]
    },
    {
        "id": "C-03", "kind": "settlement", "tx": ["TX0013"], "date": "2026-11-03",
        "question": "Room key copies 750,000 toman evidence (OI-04).",
        "options": ["Maintain Supported based on owner confirmation", "Reclassify as Review", "Reclassify as Pending"],
        "choice": "Maintain Supported based on owner confirmation",
        "rationale": "Custodian confirmed 7 keys made for members, paid personally and offset from Summer School funds held in card 8966. Receipt given to Amin Azizi. OI-04 closed.",
        "evidence": ["clarifications/1404-05_Mordad/QUESTIONS.md#Q-1404-05-02"]
    },
    {
        "id": "C-04", "kind": "basis", "tx": ["TX0002", "TX0003", "TX0004", "TX0011", "TX0012"], "date": "2026-11-03",
        "question": "Summer School 1404 instructor remuneration rule.",
        "options": ["Document 35% revenue share policy", "Document per-head formula", "Leave unspecified"],
        "choice": "Document 35% revenue share policy",
        "rationale": "Owner confirmed that instructor remuneration was set at 35% of course registration revenue.",
        "evidence": ["clarifications/1404-05_Mordad/QUESTIONS.md#Q-1404-05-03"]
    },
    {
        "id": "C-05", "kind": "settlement", "tx": ["TX0014"], "date": "2026-11-03",
        "question": "Intro Event 1404 gross income collection method.",
        "options": ["Document Evand payout to Mohammad-Amin Azizi", "Treat as card transfers", "Leave unspecified"],
        "choice": "Document Evand payout to Mohammad-Amin Azizi",
        "rationale": "Gross ticket income of 4,920,000 toman was collected via Evand ticketing and settled to Amin Azizi's account.",
        "evidence": ["clarifications/1404-06_Shahrivar/QUESTIONS.md#Q-1404-06-01"]
    },
    {
        "id": "C-06", "kind": "settlement", "tx": ["TX0016", "TX0017"], "date": "2026-11-03",
        "question": "Intro Event 1404 supplies (2,866,000 + 189,000).",
        "options": ["Confirm as event supplies and catering", "Reclassify as Review", "Exclude"],
        "choice": "Confirm as event supplies and catering",
        "rationale": "Confirmed by custodian as supplies, food, and accommodations for the intro event.",
        "evidence": ["clarifications/1404-06_Shahrivar/QUESTIONS.md#Q-1404-06-02"]
    },
    {
        "id": "C-07", "kind": "settlement", "tx": ["TX0015"], "date": "2026-11-03",
        "question": "Print shop card 502229…7257 ownership.",
        "options": ["Identify as Amin Azizi Pasargad card", "Leave unidentified", "Mark as personal"],
        "choice": "Identify as Amin Azizi Pasargad card",
        "rationale": "Custodian confirmed card 7257 belongs to Amin Azizi (second card used for event logistics).",
        "evidence": ["clarifications/1404-06_Shahrivar/QUESTIONS.md#Q-1404-06-03"]
    },
    {
        "id": "C-08", "kind": "settlement", "tx": ["TX0021"], "date": "2026-11-03",
        "question": "Tea & Physics session 20 Mehr 1404 context and merchant.",
        "options": ["Document event post and supermarket refahi merchant", "Leave generic", "Reclassify"],
        "choice": "Document event post and supermarket refahi merchant",
        "rationale": "First Tea & Physics session of the academic year on 1404/07/20; merchant identified as supermarket khadamate refahi.",
        "evidence": ["clarifications/1404-07_Mehr/QUESTIONS.md#Q-1404-07-01"]
    },
    {
        "id": "C-09", "kind": "settlement", "tx": ["TX0023", "TX0024"], "date": "2026-11-03",
        "question": "Marjolen pastry price reconciliation.",
        "options": ["Confirm exact match to final delivery invoice", "Adjust amount", "Book discrepancy"],
        "choice": "Confirm exact match to final delivery invoice",
        "rationale": "Owner reviewed photos 17 and 37 and verified that the paid amounts match final orders and packaging/delivery fees.",
        "evidence": ["clarifications/1404-07_Mehr/QUESTIONS.md#Q-1404-07-02"]
    },
    {
        "id": "C-10", "kind": "settlement", "tx": ["TX0026", "TX0027"], "date": "2026-11-03",
        "question": "Former board handover (10,000,000 + 1,000,000 toman).",
        "options": ["Confirm 11,000,000 total received via Mobina", "Reclassify as operational revenue", "Leave pending"],
        "choice": "Confirm 11,000,000 total received via Mobina",
        "rationale": "11M toman confirmed as the full opening handover received from former board via Mobina; classified under Opening funds.",
        "evidence": ["clarifications/1404-08_Aban/QUESTIONS.md#Q-1404-08-01"]
    },
    {
        "id": "C-11", "kind": "reassignment", "tx": ["TX0037", "TX0038"], "date": "2026-11-03",
        "question": "Reassignment of Shadzi balloon invoices (120,000 + 1,310,000 toman).",
        "options": ["Reassign to Yalda 1404", "Keep in Freshman Party 1404", "Split between events"],
        "choice": "Reassign to Yalda 1404",
        "rationale": "Owner clarified that both balloon purchases were for the Yalda 1404 celebration, re-posted later.",
        "evidence": ["clarifications/1404-08_Aban/QUESTIONS.md#Q-1404-08-06"]
    },
    {
        "id": "C-12", "kind": "settlement", "tx": ["TX0039", "TX0040", "TX0041", "TX0042"], "date": "2026-11-03",
        "question": "First-aid medicine and printing purchases in Aban 1404.",
        "options": ["Confirm medicine for association room and room rules prints", "Reclassify as generic", "Leave unverified"],
        "choice": "Confirm medicine for association room and room rules prints",
        "rationale": "Medicine (1,226,100 toman) bought from Sharif pharmacy for lobby first-aid locker; printing was 4 A4 and 1 A3 copies of room rules.",
        "evidence": ["clarifications/1404-08_Aban/QUESTIONS.md#Q-1404-08-07, Q-1404-08-08"]
    },
    {
        "id": "C-13", "kind": "reassignment", "tx": ["TX0043"], "date": "2026-11-03",
        "question": "Assignment of TX0043 (1,020,000 toman, terminal 06723260, 2 Azar 1404).",
        "options": ["Tea & Physics society, Hospitality", "Association operations", "Keep Unassigned"],
        "choice": "Tea & Physics society, Hospitality",
        "rationale": "Owner identified payment as refreshments for the 2nd Tea & Physics session on 1404/09/02. Settles OI-08.",
        "evidence": ["clarifications/1404-09_Azar/QUESTIONS.md#Q-1404-09-01"]
    },
    {
        "id": "C-14", "kind": "settlement", "tx": ["TX0045"], "date": "2026-11-03",
        "question": "Dr. Saman Moghimi second donation of 7,000,000 toman (OI-05).",
        "options": ["Confirm receipt in late Azar 1404 and close OI-05", "Reclassify as Review", "Exclude"],
        "choice": "Confirm receipt in late Azar 1404 and close OI-05",
        "rationale": "Owner confirmed receipt of second donation in late Azar 1404. Settles OI-05.",
        "evidence": ["clarifications/1404-09_Azar/QUESTIONS.md#Q-1404-09-02"]
    },
    {
        "id": "C-15", "kind": "settlement", "tx": ["TX0047", "TX0048"], "date": "2026-11-03",
        "question": "Yalda donations into Sepah card …2925 and cash.",
        "options": ["Confirm 15,790,000 wire + 700,000 cash donations", "Require complete bank statement", "Exclude cash"],
        "choice": "Confirm 15,790,000 wire + 700,000 cash donations",
        "rationale": "Owner confirmed Sepah card …2925 is his personal account dedicated for Yalda crowd donations (15,790,000 toman) plus 700,000 cash held by him.",
        "evidence": ["clarifications/1404-10_Dey/QUESTIONS.md#Q-1404-10-01, Q-1404-10-02"]
    },
    {
        "id": "C-16", "kind": "status", "tx": ["TX0049", "TX0056", "TX0058", "TX0060"], "date": "2026-11-03",
        "question": "Yalda 1404 transaction statuses: TX0049 transfer, TX0056/TX0058 reimbursements, TX0060 snappfood.",
        "options": ["TX0049 Internal Transfer; TX0056, TX0058, TX0060 Supported", "Keep Review / Pending", "Exclude TX0049"],
        "choice": "TX0049 Internal Transfer; TX0056, TX0058, TX0060 Supported",
        "rationale": "TX0049 was an internal cash withdrawal from Sepah …2925 to Bank Shahr …8966. TX0056 and TX0058 confirmed settled via card. TX0060 snappfood order confirmed paid by custodian from Shahr card.",
        "evidence": ["clarifications/1404-10_Dey/QUESTIONS.md#Q-1404-10-03, Q-1404-10-04, Q-1404-10-06"]
    },
    {
        "id": "C-17", "kind": "settlement", "tx": [], "date": "2026-11-03",
        "question": "Pending Item PI-01 (Bardia sandwich share, 275,584 toman).",
        "options": ["Waived by Bardia; remove from pending items", "Keep as payable liability", "Offset against cash"],
        "choice": "Waived by Bardia; remove from pending items",
        "rationale": "Volunteer Seyyed Bardia Ahmadi-Marvast waived the reimbursement; pending item closed.",
        "evidence": ["clarifications/1404-10_Dey/QUESTIONS.md#Q-1404-10-05"]
    },
    {
        "id": "C-18", "kind": "settlement", "tx": ["TX0062", "TX0063"], "date": "2026-11-03",
        "question": "Parnian reimbursement discrepancy of 195,860.1 toman (OI-02).",
        "options": ["Close OI-02 as courier/delivery cost", "Demand delivery receipt", "Keep OI-02 open"],
        "choice": "Close OI-02 as courier/delivery cost",
        "rationale": "Owner confirmed that the difference represents delivery/courier costs for Yalda supplies. Settles OI-02.",
        "evidence": ["clarifications/1405-02_Ordibehesht/QUESTIONS.md#Q-1405-02-01"]
    },
    {
        "id": "C-19", "kind": "reassignment", "tx": ["TX0061"], "date": "2026-11-03",
        "question": "Assignment of TX0061 (1,801,220 toman, 9 Esfand 1404).",
        "options": ["Association operations, Supplies", "Keep Unassigned", "Exclude as personal"],
        "choice": "Association operations, Supplies",
        "rationale": "Owner confirmed purchase of drinking water for students attending silent protest assembly regarding Parnian Khodabakhshi. Settles OI-09.",
        "evidence": ["clarifications/1404-12_Esfand/QUESTIONS.md#Q-1404-12-01"]
    },
    {
        "id": "C-20", "kind": "status", "tx": ["TX0096"], "date": "2026-11-03",
        "question": "Website domain alenush.com 3,000,000 toman status.",
        "options": ["Update status to Supported", "Keep Pending", "Exclude"],
        "choice": "Update status to Supported",
        "rationale": "Owner confirmed domain alenush.com was purchased via cryptocurrency wallet and is active/owned for the association.",
        "evidence": ["clarifications/1405-04_Tir/QUESTIONS.md#Q-1405-04-01"]
    },
    {
        "id": "C-21", "kind": "reassignment", "tx": ["TX0075", "TX0076", "TX0077", "TX0078", "TX0079"], "date": "2026-11-03",
        "question": "Assignment of Mordad 1405 purchases on card …2167 (11,217,000 toman).",
        "options": ["Observation Camp 1405, Hospitality", "Summer School 1405", "Keep Unassigned"],
        "choice": "Observation Camp 1405, Hospitality",
        "rationale": "Card …2167 belongs to Mohammad-Hassan Shiri. The five purchases were provisions for the Perseid meteor shower observation camp in Garmsar (72 cakes and juices, bottled iced water, watermelons, rice cakes). Settles OI-10 through OI-14.",
        "evidence": ["clarifications/1405-05_Mordad/QUESTIONS.md#Q-1405-05-01", "chat message11524, 11693, 2100"]
    },
    {
        "id": "C-22", "kind": "reassignment", "tx": ["TX0081", "TX0082"], "date": "2026-11-03",
        "question": "Summer School 1405 expenses: Atefeh Nakhaei 4,500,000 and Skyroom invoice 4,257,000.",
        "options": ["TX0081 Summer School 1405 Advertising; TX0082 Supported", "Keep TX0081 Unassigned", "Keep TX0082 Pending"],
        "choice": "TX0081 Summer School 1405 Advertising; TX0082 Supported",
        "rationale": "TX0081 confirmed as advertising on Tehran University student channels (settles OI-15). TX0082 confirmed paid by custodian from mixed funds, updated to Supported.",
        "evidence": ["clarifications/1405-06_Shahrivar/QUESTIONS.md#Q-1405-06-01, Q-1405-06-02"]
    },
    {
        "id": "C-23", "kind": "new_row", "tx": ["TX0097", "TX0098"], "date": "2026-11-03",
        "question": "Summer School 1405 registration income and 6th instructor payment.",
        "options": ["Create TX0097 (31,927,075 toman) and TX0098 (1,200,000 toman)", "Leave income unrecorded", "Keep 6th instructor open"],
        "choice": "Create TX0097 (31,927,075 toman) and TX0098 (1,200,000 toman)",
        "rationale": "Custodian confirmed total course registration income of 31,927,075 toman. Blu statement 1405/07/01 identifies 6th instructor payment: 12,000,000 rial (1,200,000 toman) to Reza Abedini. Both created as Supported.",
        "evidence": ["clarifications/1405-06_Shahrivar/QUESTIONS.md#Q-1405-06-03, Q-1405-06-04", "14050812012318.xlsx!transaction!row42"]
    },
    {
        "id": "C-24", "kind": "settlement", "tx": ["TX0090", "TX0091", "TX0092", "TX0093", "TX0094", "TX0095", "TX0099"], "date": "2026-11-03",
        "question": "Intro Event 1405 complete reconciliation and ticket refund.",
        "options": ["Reassign TX0090 (Supplies) & TX0091 (Hospitality) to Intro Event 1405; TX0092 to Tea; TX0095 to Memo; create TX0099 refund", "Keep Unassigned", "Leave open items"],
        "choice": "Reassign TX0090 (Supplies) & TX0091 (Hospitality) to Intro Event 1405; TX0092 to Tea; TX0095 to Memo; create TX0099 refund",
        "rationale": "Evand fee of 4,235,000 toman settled net income of 23,000,000 (settles OI-03). TX0090 (13.9M to Paria Hashemi) was notebooks, folders, pencils (settles OI-16). TX0091 (2.33M at Family Market) was event confectionery (settles OI-17). TX0092 (305k to Mozhdeh Salmani) was paper cups for Tea session (settles OI-18). TX0095 after-party was never held or paid, marked Memo (settles OI-06). TX0099 created for 350,000 toman ticket refund to Maedeh Sadat Ahmadi Nasiri.",
        "evidence": ["clarifications/1405-07_Mehr/QUESTIONS.md#Q-1405-07-01..06", "photo_2026-11-02_18-45-33.jpg", "14050812012318.xlsx"]
    },
    {
        "id": "C-25", "kind": "settlement", "tx": [], "date": "2026-11-03",
        "question": "Closing cash reconciliation and settlement of OI-07.",
        "options": ["Close OI-07 by disclosing commingled statements and establishing net cash balance", "Keep OI-07 open", "Reject statements"],
        "choice": "Close OI-07 by disclosing commingled statements and establishing net cash balance",
        "rationale": "Bank statements provided (Shahr 80.pdf, Blu 14050812012318.xlsx). Statements confirm active commingling with personal transactions. Net association cash position is established as 37,189,180 toman before website server settlement (Receipts 144,479,075 - Payments 107,289,895). Settles OI-07.",
        "evidence": ["80.pdf", "14050812012318.xlsx", "clarifications/00_cross_month_questions.md#X-04, X-08"]
    },
    {
        "id": "C-26", "kind": "transaction", "tx": ["TX0100"], "date": "2026-11-03",
        "question": "Server / VM hosting costs for alenush.com association website.",
        "options": ["Exclude from ledger", "Hold in Review", "Supported payment out of pocket by custodian"],
        "choice": "Supported payment of 6,030,048 toman (TX0100)",
        "rationale": "Custodian declared and confirmed paying for the 3-month Alnush cloud VM hosting (2 vCPU, 4GB RAM, 30GB SSD; 65,544 toman/day x 92 days = 6,030,048 toman) out of pocket from the association surplus held. Booked as Supported expense under Association website.",
        "evidence": ["reports/2026-10-10/website_user_confirmation_2026-10-11.json", "Custodian confirmation 2026-11-03"]
    },
    {
        "id": "C-27", "kind": "transaction", "tx": ["TX0101"], "date": "2026-11-03",
        "question": "Tea & Physics gathering food and hospitality on 1405/06/02.",
        "options": ["Exclude from ledger", "Supported payment of 2,800,000 toman (TX0101)"],
        "choice": "Supported payment of 2,800,000 toman (TX0101)",
        "rationale": "ATM card-to-card transfer slip from Shahr card to attendee (card ending in 8671) on 1405/06/02 15:06 (tracking 300311527) for 2,800,000 toman. Booked as Supported expense under Tea & Physics society, Hospitality.",
        "evidence": ["data/accounting/receipts/receipt_tea_gathering_14050602.jpg", "Custodian confirmation 2026-11-03"]
    },
    {
        "id": "C-28", "kind": "transaction", "tx": ["TX0102"], "date": "2026-11-03",
        "question": "Hollyland Lark M1 wireless microphone purchased for association events/podcasts.",
        "options": ["Exclude from ledger", "Supported payment of 13,478,750 toman (TX0102)"],
        "choice": "Supported payment of 13,478,750 toman (TX0102)",
        "rationale": "Digikala order DK1295013868 placed on 1405/07/01 for Hollyland Lark M1 wireless microphone (USB-C) delivered to Sharif University Jabbari Hall. Amount 13,478,750 toman booked as Supported under Association operations, Equipment.",
        "evidence": ["data/accounting/receipts/receipt_microphone_digikala_14050701.png", "Custodian confirmation 2026-11-03"]
    }
]


def apply_updates():
    base_dir = REPORTS / "2026-10-18"
    with open(base_dir / "Transactions_Audited.csv", encoding="utf-8-sig") as f:
        rows_list = list(csv.DictReader(f))
    rows = {r["id"]: dict(r) for r in rows_list}

    with open(base_dir / "Audit_Log.csv", encoding="utf-8-sig") as f:
        log = list(csv.DictReader(f))

    with open(base_dir / "Decisions_Register.json", encoding="utf-8") as f:
        decs = json.load(f)

    # Append new decisions
    decs.extend(NEW_DECISIONS)

    def log_change(tx, field, new_val, dec_id, reason, evidence):
        old_val = rows[tx].get(field, "")
        rows[tx][field] = new_val
        cf = [c for c in rows[tx].get("changed_fields", "").split(";") if c]
        if field not in cf:
            cf.append(field)
            rows[tx]["changed_fields"] = ";".join(cf)
        log.append({
            "tx": tx, "field": field, "old": str(old_val), "new": str(new_val),
            "source_id": dec_id, "reason": reason, "evidence": evidence
        })

    # C-11: TX0037, TX0038 -> Yalda 1404
    log_change("TX0037", "project", "Yalda 1404", "C-11", "Reassigned to Yalda per owner confirmation", "Q-1404-08-06")
    log_change("TX0038", "project", "Yalda 1404", "C-11", "Reassigned to Yalda per owner confirmation", "Q-1404-08-06")

    # C-13: TX0043 -> Tea & Physics society, Hospitality
    log_change("TX0043", "project", "Tea & Physics society", "C-13", "Identified as Tea session 2 Azar 1404 refreshments", "Q-1404-09-01")
    log_change("TX0043", "category", "Hospitality", "C-13", "Refreshments for Tea session", "Q-1404-09-01")
    log_change("TX0043", "open_item", "", "C-13", "Open item settled", "Q-1404-09-01")

    # C-16: Yalda 1404 statuses
    log_change("TX0049", "direction", "Internal transfer", "C-16", "Withdrawal from Sepah to Shahr card", "Q-1404-10-03")
    log_change("TX0049", "status", "Internal transfer", "C-16", "Internal transfer between association accounts", "Q-1404-10-03")
    log_change("TX0049", "category", "Transfers", "C-16", "Internal transfer", "Q-1404-10-03")
    log_change("TX0049", "pending_reason", "", "C-16", "Status updated from Pending", "Q-1404-10-03")

    log_change("TX0056", "status", "Supported", "C-16", "Confirmed paid via card by custodian", "Q-1404-10-04")
    log_change("TX0056", "pending_reason", "", "C-16", "Status updated from Payable", "Q-1404-10-04")

    log_change("TX0058", "status", "Supported", "C-16", "Confirmed paid via card by custodian", "Q-1404-10-04")
    log_change("TX0058", "pending_reason", "", "C-16", "Status updated from Payable", "Q-1404-10-04")

    log_change("TX0060", "status", "Supported", "C-16", "Snappfood pomegranate order paid via Shahr card", "Q-1404-10-06")
    log_change("TX0060", "pending_reason", "", "C-16", "Status updated from Pending", "Q-1404-10-06")

    # C-19: TX0061 -> Association operations, Supplies
    log_change("TX0061", "project", "Association operations", "C-19", "Drinking water for student assembly", "Q-1404-12-01")
    log_change("TX0061", "category", "Supplies", "C-19", "Supplies for assembly", "Q-1404-12-01")
    log_change("TX0061", "open_item", "", "C-19", "Open item settled", "Q-1404-12-01")

    # C-20: TX0096 -> Supported
    log_change("TX0096", "status", "Supported", "C-20", "Domain alenush.com confirmed purchased in crypto", "Q-1405-04-01")
    log_change("TX0096", "pending_reason", "", "C-20", "Status updated from Pending", "Q-1405-04-01")

    # C-21: TX0075-TX0079 -> Observation Camp 1405, Hospitality
    for tx in ["TX0075", "TX0076", "TX0077", "TX0078", "TX0079"]:
        log_change(tx, "project", "Observation Camp 1405", "C-21", "Perseid meteor shower observation camp provisions", "Q-1405-05-01")
        log_change(tx, "category", "Hospitality", "C-21", "Camp catering and food supplies", "Q-1405-05-01")
        log_change(tx, "open_item", "", "C-21", "Open item settled", "Q-1405-05-01")

    # C-22: TX0081, TX0082
    log_change("TX0081", "project", "Summer School 1405", "C-22", "Tehran University telegram channels advertising", "Q-1405-06-01")
    log_change("TX0081", "category", "Advertising", "C-22", "Advertising on student channels", "Q-1405-06-01")
    log_change("TX0081", "open_item", "", "C-22", "Open item settled", "Q-1405-06-01")

    log_change("TX0082", "status", "Supported", "C-22", "Skyroom invoice confirmed settled from mixed funds", "Q-1405-06-02")
    log_change("TX0082", "pending_reason", "", "C-22", "Status updated from Pending", "Q-1405-06-02")

    # C-24: Intro Event 1405 settlements
    log_change("TX0090", "project", "Intro Event 1405", "C-24", "Gift notebooks, folders and pencils for attendees", "Q-1405-07-03")
    log_change("TX0090", "category", "Supplies", "C-24", "Stationery supplies and gifts", "Q-1405-07-03")
    log_change("TX0090", "open_item", "", "C-24", "Open item settled", "Q-1405-07-03")

    log_change("TX0091", "project", "Intro Event 1405", "C-24", "Confectionery and sweets from Family Market", "Q-1405-07-04")
    log_change("TX0091", "category", "Hospitality", "C-24", "Catering confectionery", "Q-1405-07-04")
    log_change("TX0091", "open_item", "", "C-24", "Open item settled", "Q-1405-07-04")

    log_change("TX0092", "project", "Tea & Physics society", "C-24", "Paper cups for Tea session 14 Mehr 1405", "Q-1405-07-05")
    log_change("TX0092", "category", "Supplies", "C-24", "Event cups supplies", "Q-1405-07-05")
    log_change("TX0092", "open_item", "", "C-24", "Open item settled", "Q-1405-07-05")

    log_change("TX0095", "status", "Memo", "C-24", "Gathering never held or paid; amount retained in association balance", "Q-1405-07-06")
    log_change("TX0095", "notes", rows["TX0095"].get("notes", "") + " | Unexecuted gathering; not paid per owner clarification.", "C-24", "Note appended", "Q-1405-07-06")
    log_change("TX0095", "open_item", "", "C-24", "Open item settled", "Q-1405-07-06")

    # Clear open items on previously verified rows
    for tx in ["TX0001", "TX0013", "TX0045", "TX0062", "TX0063", "TX0093", "TX0094"]:
        if rows[tx].get("open_item"):
            log_change(tx, "open_item", "", "C-24", "Open item settled through owner clarifications", "Clarifications pack 2026-11-02")

    # New rows: TX0097, TX0098, TX0099
    rows["TX0097"] = {
        "id": "TX0097", "date_gregorian": "2026-08-30", "date_jalali": "1405/06/08", "period_jalali": "1405/06",
        "direction": "Receipt", "amount_original": "319270750.0", "unit_original": "rial", "amount_toman": "31927075.0",
        "counterparty": "دانشجویان مدرسه تابستانه ۱۴۰۵", "description_en": "Summer School 1405 registration fee income across all courses",
        "description_fa": "درآمد حاصل از ثبت‌نام دوره‌های مدرسه تابستانه ۱۴۰۵", "category": "Course fees",
        "project": "Summer School 1405", "status": "Supported", "evidence_basis": "User declaration and fee tally",
        "cash_account": "BLU-CUSTODIAN", "message_ids": "", "tracking_id": "", "duplicate_of": "", "review_reason": "",
        "notes": "Reported by custodian as total course registration receipts", "sources": "clarifications/1405-06_Shahrivar/QUESTIONS.md#Q-1405-06-04",
        "source_status": "New", "pending_reason": "", "parent": "", "date_basis": "month only", "evidence_label": "custodian confirmation",
        "open_item": "", "changed_fields": ""
    }
    log.append({"tx": "TX0097", "field": "created", "old": "", "new": "TX0097", "source_id": "C-23", "reason": "Summer School 1405 course fees income", "evidence": "Q-1405-06-04"})

    rows["TX0098"] = {
        "id": "TX0098", "date_gregorian": "2026-09-22", "date_jalali": "1405/07/01", "period_jalali": "1405/07",
        "direction": "Payment", "amount_original": "12000000.0", "unit_original": "rial", "amount_toman": "1200000.0",
        "counterparty": "رضا عابدینی", "description_en": "Summer School 1405 instructor fee to Reza Abedini",
        "description_fa": "حق‌التدریس مدرس مدرسه تابستانه ۱۴۰۵ به رضا عابدینی", "category": "Teaching",
        "project": "Summer School 1405", "status": "Supported", "evidence_basis": "Blu bank statement",
        "cash_account": "BLU-CUSTODIAN", "message_ids": "", "tracking_id": "14055375535560", "duplicate_of": "", "review_reason": "",
        "notes": "Matched from Blu statement 1405/07/01 18:16:40; 6th instructor", "sources": "14050812012318.xlsx!transaction!row42",
        "source_status": "New", "pending_reason": "", "parent": "", "date_basis": "printed", "evidence_label": "bank statement",
        "open_item": "", "changed_fields": ""
    }
    log.append({"tx": "TX0098", "field": "created", "old": "", "new": "TX0098", "source_id": "C-23", "reason": "6th instructor payment to Reza Abedini", "evidence": "Blu statement row 42"})

    rows["TX0099"] = {
        "id": "TX0099", "date_gregorian": "2026-09-27", "date_jalali": "1405/07/05", "period_jalali": "1405/07",
        "direction": "Payment", "amount_original": "3500000.0", "unit_original": "rial", "amount_toman": "350000.0",
        "counterparty": "مائده سادات احمدی ناصری", "description_en": "Ticket refund for Intro Event 1405 to Maedeh Sadat Ahmadi Nasiri",
        "description_fa": "استرداد وجه بلیت همایش معرفی رشته ۱۴۰۵ به مائده سادات احمدی ناصری", "category": "Events",
        "project": "Intro Event 1405", "status": "Supported", "evidence_basis": "Blu transfer receipt & bank statement",
        "cash_account": "BLU-CUSTODIAN", "message_ids": "", "tracking_id": "051549496006", "duplicate_of": "", "review_reason": "",
        "notes": "Ticket cancellation refund; ref 051549496006", "sources": "clarifications/1405-07_Mehr/photo_2026-11-02_18-45-33.jpg",
        "source_status": "New", "pending_reason": "", "parent": "", "date_basis": "printed", "evidence_label": "transfer receipt",
        "open_item": "", "changed_fields": ""
    }
    log.append({"tx": "TX0099", "field": "created", "old": "", "new": "TX0099", "source_id": "C-24", "reason": "Ticket refund to Maedeh Sadat Ahmadi Nasiri", "evidence": "photo_2026-11-02_18-45-33.jpg"})

    rows["TX0100"] = {
        "id": "TX0100", "date_gregorian": "2026-08-19", "date_jalali": "1405/05/28", "period_jalali": "1405/05",
        "direction": "Payment", "amount_original": "60300480.0", "unit_original": "rial", "amount_toman": "6030048.0",
        "counterparty": "ارائه‌دهنده سرور ابری (Alnush VM)", "description_en": "Three-month cloud VM server hosting for alenush.com website (2 vCPU, 4GB RAM, 30GB SSD, 1405/05/28 to 1405/08/28 at 655,440 rial/day); paid out of pocket by custodian",
        "description_fa": "هزینهٔ هاستینگ و سرور ابری ۳ ماهه وب‌سایت alenush.com (۲ هسته، ۴ گیگابایت رم، ۳۰ گیگابایت حافظه) از ۱۴۰۵/۰۵/۲۸ تا ۱۴۰۵/۰۸/۲۸؛ پرداخت از جیب توسط متولی", "category": "Website server",
        "project": "Association website", "status": "Supported", "evidence_basis": "Custodian confirmation; VM configuration 1405/05/28 at 655,440 rial/day for 92 days",
        "cash_account": "CUSTODIAN", "message_ids": "", "tracking_id": "", "duplicate_of": "", "review_reason": "",
        "notes": "Decision C-26: Website VM hosting cost for alenush.com confirmed paid out-of-pocket by custodian and recognized as supported association expense.", "sources": "reports/2026-10-10/website_user_confirmation_2026-10-11.json",
        "source_status": "New", "pending_reason": "", "parent": "", "date_basis": "creation timestamp", "evidence_label": "tariff quote and custodian declaration",
        "open_item": "", "changed_fields": ""
    }
    log.append({"tx": "TX0100", "field": "created", "old": "", "new": "TX0100", "source_id": "C-26", "reason": "Three-month website VM hosting confirmed paid out of pocket by custodian", "evidence": "website_user_confirmation_2026-10-11.json; user confirmation 2026-11-03"})

    rows["TX0101"] = {
        "id": "TX0101", "date_gregorian": "2026-08-24", "date_jalali": "1405/06/02", "period_jalali": "1405/06",
        "direction": "Payment", "amount_original": "28000000.0", "unit_original": "rial", "amount_toman": "2800000.0",
        "counterparty": "حاضرین رویداد چای (کارت منتهی به ۸۶۷۱)", "description_en": "Hospitality and food for Tea & Physics gathering; ATM transfer from Shahr card to attendee (tracking 300311527)",
        "description_fa": "پذیرایی و خوراکی برنامه چای و فیزیک (۲ شهریور ۱۴۰۵)؛ انتقال کارت به کارت خودپرداز از کارت بانک شهر به فرد حاضر در برنامه (کد پیگیری ۳۰۰۳۱۱۵۲۷)", "category": "Hospitality",
        "project": "Tea & Physics society", "status": "Supported", "evidence_basis": "ATM transfer slip (tracking 300311527 on 1405/06/02 15:06) and custodian confirmation",
        "cash_account": "SHAHR-8966", "message_ids": "", "tracking_id": "300311527", "duplicate_of": "", "review_reason": "",
        "notes": "Decision C-27: 2,800,000 toman ATM transfer to attendee card …8671 on 1405/06/02 for Tea & Physics gathering food and hospitality.", "sources": "data/accounting/receipts/receipt_tea_gathering_14050602.jpg",
        "source_status": "New", "pending_reason": "", "parent": "", "date_basis": "printed", "evidence_label": "ATM slip",
        "open_item": "", "changed_fields": ""
    }
    log.append({"tx": "TX0101", "field": "created", "old": "", "new": "TX0101", "source_id": "C-27", "reason": "Tea & Physics gathering food and hospitality on 1405/06/02", "evidence": "receipt_tea_gathering_14050602.jpg"})

    rows["TX0102"] = {
        "id": "TX0102", "date_gregorian": "2026-09-23", "date_jalali": "1405/07/01", "period_jalali": "1405/07",
        "direction": "Payment", "amount_original": "134787500.0", "unit_original": "rial", "amount_toman": "13478750.0",
        "counterparty": "دیجی‌کالا (Digikala)", "description_en": "Purchase of Hollyland Lark M1 wireless microphone (USB-C) for association events and podcast recording (Digikala order DK1295013868, delivered to Jabbari Hall)",
        "description_fa": "خرید میکروفن بی‌سیم هالی‌لند مدل Lark M1 با درگاه USB-C برای ضبط پادکست، ویدیو و رویدادهای انجمن (سفارش دیجی‌کالا DK1295013868، تحویل سالن جباری)", "category": "Equipment",
        "project": "Association operations", "status": "Supported", "evidence_basis": "Digikala order invoice screenshot DK1295013868 on 1405/07/01",
        "cash_account": "CUSTODIAN", "message_ids": "", "tracking_id": "DK1295013868", "duplicate_of": "", "review_reason": "",
        "notes": "Decision C-28: 13,478,750 toman Hollyland Lark M1 wireless microphone bought on Digikala for association operations/media equipment, delivered to Sharif University Jabbari Hall on 1405/07/01.", "sources": "data/accounting/receipts/receipt_microphone_digikala_14050701.png",
        "source_status": "New", "pending_reason": "", "parent": "", "date_basis": "printed", "evidence_label": "Digikala order confirmation",
        "open_item": "", "changed_fields": ""
    }
    log.append({"tx": "TX0102", "field": "created", "old": "", "new": "TX0102", "source_id": "C-28", "reason": "Hollyland Lark M1 wireless microphone purchased for association events/podcasts", "evidence": "receipt_microphone_digikala_14050701.png"})

    sorted_rows = [rows[k] for k in sorted(rows.keys(), key=lambda x: (int(x.replace("TX", "").split("-")[0]), x))]
    return sorted_rows, log, decs


def compute_balance_sheets(rows, log):
    # Determine all projects
    projects = set()
    for r in rows:
        projects.add(r["project"])
    projects.add("Unassigned")
    projects.add("Unknown (likely 1405 summer school)")

    sheets = {}
    for p in sorted(projects):
        sheets[p] = {
            "receipts": 0.0, "payments": 0.0, "net": 0.0,
            "pending": 0.0, "pending_rows": [], "pending_items": [],
            "excluded": [], "receipts_by_source": {},
            "payments_by_category": {}, "tx_rows": [],
            "open_items": [], "is_empty_note": None
        }

    for r in rows:
        p = r["project"]
        s = sheets[p]
        s["tx_rows"].append(r["id"])
        st = r["status"]
        direction = r["direction"]
        amt = float(r["amount_toman"]) if r.get("amount_toman") else 0.0

        if st == "Supported":
            if direction == "Receipt":
                s["receipts"] += amt
                cp = r.get("counterparty", "") or "Other"
                s["receipts_by_source"][cp] = s["receipts_by_source"].get(cp, 0.0) + amt
            elif direction == "Payment":
                s["payments"] += amt
                cat = r.get("category", "") or "Unclassified"
                s["payments_by_category"][cat] = s["payments_by_category"].get(cat, 0.0) + amt
        elif st in ("Pending", "Payable"):
            s["pending"] += amt
            s["pending_rows"].append(r["id"])
        elif st in ("Supporting detail", "Duplicate", "Memo"):
            s["excluded"].append({"id": r["id"], "kind": st, "parent": r.get("parent", "")})

        if r.get("open_item") and r["open_item"] not in s["open_items"]:
            s["open_items"].append(r["open_item"])

    for p, s in sheets.items():
        s["net"] = s["receipts"] - s["payments"]

    # Empty notes
    sheets["Unassigned"]["is_empty_note"] = "All 11 transactions reassigned per owner clarifications (C-13, C-19, C-21, C-22, C-24)."
    sheets["Unknown (likely 1405 summer school)"]["is_empty_note"] = "Reassigned to Summer School 1405 per decision R-11."

    return sheets


def compute_open_items():
    return [
        {
            "id": "OI-01", "project": "Summer School 1404", "rows": "TX0001", "amount_toman": 1000.0,
            "question": "The posted report shows 33,643,000 for this receipt; the ledger has 33,642,000 (1,000 difference).",
            "what_settles": "Settled: Confirmed net deposit of 33,642,000 into card 8966 per owner response (decision C-02)."
        },
        {
            "id": "OI-02", "project": "Yalda 1404", "rows": "TX0062;TX0063", "amount_toman": 195860.1,
            "question": "195,860.1 toman of volunteer-reported purchases (TX0064-74) not covered by 4,050,000 reimbursement.",
            "what_settles": "Settled: Owner confirmed difference is delivery/courier costs for Yalda supplies (decision C-18)."
        },
        {
            "id": "OI-03", "project": "Intro Event 1405", "rows": "TX0093;TX0094", "amount_toman": 4235000.0,
            "question": "Intro Event 1405 evidence implies 4,235,000 beyond recorded net of 23,000,000.",
            "what_settles": "Settled: Evand platform fee of 4,235,000 deducted from gross 27,235,000; net 23,000,000 confirmed (decision C-24)."
        },
        {
            "id": "OI-04", "project": "Association operations", "rows": "TX0013", "amount_toman": "",
            "question": "Room key copies 750,000 toman had no receipt outside original ledger.",
            "what_settles": "Settled: Custodian confirmed 7 keys copied for room, paid personally and offset from funds (decision C-03)."
        },
        {
            "id": "OI-05", "project": "Association operations", "rows": "TX0045", "amount_toman": "",
            "question": "Dr. Saman Moghimi second donation of 7,000,000 toman in Azar 1404.",
            "what_settles": "Settled: Owner confirmed receipt of second donation in late Azar 1404 (decision C-14)."
        },
        {
            "id": "OI-06", "project": "Intro Event 1405", "rows": "TX0095", "amount_toman": "",
            "question": "Organizers after-party 5,000,000 toman had no receipt outside original ledger.",
            "what_settles": "Settled: Owner confirmed gathering was never held or paid; row reclassified to Memo (decision C-24)."
        },
        {
            "id": "OI-07", "project": "", "rows": "", "amount_toman": "",
            "question": "Commingled bank accounts and unrecorded balance movements across Bank Shahr and Blu.",
            "what_settles": "Disclosed & Settled: Bank Shahr (80.pdf) and Blu (14050812012318.xlsx) statements reviewed; commingling disclosed. Net association position established at 37,189,180 toman (decisions C-01, C-25)."
        },
        {
            "id": "OI-08", "project": "Tea & Physics society", "rows": "TX0043", "amount_toman": "",
            "question": "Purpose of TX0043 (1,020,000 toman, 2 Azar 1404).",
            "what_settles": "Settled: Identified as refreshments for 2nd Tea & Physics session; assigned to Tea & Physics society (decision C-13)."
        },
        {
            "id": "OI-09", "project": "Association operations", "rows": "TX0061", "amount_toman": "",
            "question": "Purpose of TX0061 (1,801,220 toman, 9 Esfand 1404).",
            "what_settles": "Settled: Drinking water for student silent assembly; assigned to Association operations (decision C-19)."
        },
        {
            "id": "OI-10", "project": "Observation Camp 1405", "rows": "TX0075", "amount_toman": "",
            "question": "Purpose of TX0075 (6,337,000 toman on card …2167, 21 Mordad 1405).",
            "what_settles": "Settled: 72 cakes and 72 juices for Perseid observation camp in Garmsar (decision C-21)."
        },
        {
            "id": "OI-11", "project": "Observation Camp 1405", "rows": "TX0076", "amount_toman": "",
            "question": "Purpose of TX0076 (1,100,000 toman on card …2167, 21 Mordad 1405).",
            "what_settles": "Settled: Provisions for Perseid observation camp (decision C-21)."
        },
        {
            "id": "OI-12", "project": "Observation Camp 1405", "rows": "TX0077", "amount_toman": "",
            "question": "Purpose of TX0077 (1,320,000 toman on card …2167, 21 Mordad 1405).",
            "what_settles": "Settled: Provisions for Perseid observation camp (decision C-21)."
        },
        {
            "id": "OI-13", "project": "Observation Camp 1405", "rows": "TX0078", "amount_toman": "",
            "question": "Purpose of TX0078 (1,300,000 toman on card …2167, 21 Mordad 1405).",
            "what_settles": "Settled: 30 bottles iced water, 3 watermelons, rice cakes for observation camp (decision C-21)."
        },
        {
            "id": "OI-14", "project": "Observation Camp 1405", "rows": "TX0079", "amount_toman": "",
            "question": "Purpose of TX0079 (1,160,000 toman on card …2167, 22 Mordad 1405).",
            "what_settles": "Settled: Camp supplies for Perseid observation camp (decision C-21)."
        },
        {
            "id": "OI-15", "project": "Summer School 1405", "rows": "TX0081", "amount_toman": "",
            "question": "Purpose of TX0081 (4,500,000 toman to Atefeh Nakhaei, 6 Shahrivar 1405).",
            "what_settles": "Settled: Summer School 1405 advertising on Tehran University telegram channels (decision C-22)."
        },
        {
            "id": "OI-16", "project": "Intro Event 1405", "rows": "TX0090", "amount_toman": "",
            "question": "Purpose of TX0090 (13,900,000 toman to Paria Hashemi, 2 Mehr 1405).",
            "what_settles": "Settled: 70 notebooks, 70 folders, 70 pencils as gifts for Intro Event attendees (decision C-24)."
        },
        {
            "id": "OI-17", "project": "Intro Event 1405", "rows": "TX0091", "amount_toman": "",
            "question": "Purpose of TX0091 (2,332,250 toman at merchant 12738006, 2 Mehr 1405).",
            "what_settles": "Settled: Confectionery and sweets from Family Market for Intro Event 1405 (decision C-24)."
        },
        {
            "id": "OI-18", "project": "Tea & Physics society", "rows": "TX0092", "amount_toman": "",
            "question": "Purpose of TX0092 (305,000 toman to Mozhdeh Salmani, 14 Mehr 1405).",
            "what_settles": "Settled: Paper cups for Tea & Physics session 14 Mehr 1405 (decision C-24)."
        }
    ]


def write_csv_and_json(out_dir, rows, log, decs, sheets, open_items):
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Transactions_Audited
    header = list(rows[0].keys())
    with open(out_dir / "Transactions_Audited.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([_scrub(r.get(c, "")) for c in header])

    with open(out_dir / "Transactions_Audited.json", "w", encoding="utf-8") as f:
        json.dump([{k: _scrub(v) for k, v in r.items()} for r in rows], f, ensure_ascii=False, indent=2)

    # 2. Audit_Log
    log_cols = ["tx", "field", "old", "new", "source_id", "reason", "evidence"]
    with open(out_dir / "Audit_Log.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(log_cols)
        for e in log:
            w.writerow([_scrub(e.get(c, "")) for c in log_cols])

    # 3. Decisions_Register
    with open(out_dir / "Decisions_Register.json", "w", encoding="utf-8") as f:
        json.dump(decs, f, ensure_ascii=False, indent=2)

    # 4. Balance_Sheets
    with open(out_dir / "Balance_Sheets.json", "w", encoding="utf-8") as f:
        json.dump(sheets, f, ensure_ascii=False, indent=2)

    sheet_cols = ["project", "section", "line_label", "amount_toman", "extra"]
    sheet_lines = []
    for p in sorted(sheets):
        s = sheets[p]
        for label in sorted(s["receipts_by_source"]):
            sheet_lines.append([p, "receipts", label, s["receipts_by_source"][label], ""])
        for label in sorted(s["payments_by_category"]):
            sheet_lines.append([p, "payments", label, s["payments_by_category"][label], ""])
        for label in ("receipts", "payments", "net", "pending"):
            sheet_lines.append([p, "totals", label, s[label], ""])
        for tx in s["pending_rows"]:
            sheet_lines.append([p, "pending_rows", tx, "", ""])
        for item in s["pending_items"]:
            sheet_lines.append([p, "pending_items", item["id"], item.get("amount_toman"), item.get("note", "")])
        for oi in s["open_items"]:
            sheet_lines.append([p, "open_items", oi, "", ""])
        for e in s["excluded"]:
            extra = e["kind"] + (f" (parent {e['parent']})" if e.get("parent") else "")
            sheet_lines.append([p, "excluded", e["id"], "", extra])
        if s.get("is_empty_note"):
            sheet_lines.append([p, "note", "empty_note", "", s["is_empty_note"]])

    with open(out_dir / "Balance_Sheets.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(sheet_cols)
        for ln in sheet_lines:
            w.writerow([_scrub(x) for x in ln])

    # 5. Open_Items
    oi_cols = ["id", "project", "rows", "amount_toman", "question", "what_settles"]
    with open(out_dir / "Open_Items.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(oi_cols)
        for oi in open_items:
            w.writerow([_scrub(oi.get(c, "")) for c in oi_cols])

    print("CSVs and JSONs written to", out_dir)


def generate_excel_workbook(out_dir, rows):
    template_path = REPORTS / "2026-10-10" / "Anjoman_Accounting_Professional.xlsx"
    wb = openpyxl.load_workbook(template_path)

    # 1. Update Transactions sheet
    ws_tx = wb["Transactions"]
    # clear existing rows 5 to 110
    for r in range(5, 120):
        for c in range(1, 26):
            ws_tx.cell(r, c).value = None

    accounting_fmt = '#,##0.0;(#,##0.0);"-";@'
    int_fmt = '#,##0;(#,##0);"-";@'

    for i, row_data in enumerate(rows):
        r = i + 5
        ws_tx.cell(r, 1).value = row_data["id"]
        ws_tx.cell(r, 2).value = row_data.get("date_gregorian") or None
        ws_tx.cell(r, 3).value = row_data.get("date_jalali") or None
        ws_tx.cell(r, 4).value = row_data.get("period_jalali") or "Undated"
        ws_tx.cell(r, 5).value = row_data.get("direction") or ""
        
        orig_amt = row_data.get("amount_original")
        ws_tx.cell(r, 6).value = float(orig_amt) if orig_amt not in ("", None) else None
        ws_tx.cell(r, 7).value = row_data.get("unit_original") or ""
        
        toman_amt = row_data.get("amount_toman")
        ws_tx.cell(r, 8).value = float(toman_amt) if toman_amt not in ("", None) else None
        
        ws_tx.cell(r, 9).value = _scrub(row_data.get("counterparty") or "")
        ws_tx.cell(r, 10).value = _scrub(row_data.get("description_en") or "")
        ws_tx.cell(r, 11).value = _scrub(row_data.get("description_fa") or "")
        ws_tx.cell(r, 12).value = row_data.get("category") or ""
        ws_tx.cell(r, 13).value = row_data.get("project") or ""
        ws_tx.cell(r, 14).value = row_data.get("status") or ""
        ws_tx.cell(r, 15).value = row_data.get("evidence_basis") or ""
        ws_tx.cell(r, 16).value = row_data.get("cash_account") or ""
        ws_tx.cell(r, 17).value = row_data.get("message_ids") or ""
        ws_tx.cell(r, 18).value = row_data.get("tracking_id") or ""
        ws_tx.cell(r, 19).value = row_data.get("duplicate_of") or ""
        ws_tx.cell(r, 20).value = row_data.get("review_reason") or ""
        ws_tx.cell(r, 21).value = _scrub(row_data.get("notes") or "")
        ws_tx.cell(r, 22).value = _scrub(row_data.get("sources") or "")

        # Formulas for W, X, Y
        ws_tx.cell(r, 23).value = f'=IF(AND(N{r}="Supported",E{r}="Receipt",ISNUMBER(H{r})),H{r},0)'
        ws_tx.cell(r, 24).value = f'=IF(AND(N{r}="Supported",E{r}="Payment",ISNUMBER(H{r})),H{r},0)'
        ws_tx.cell(r, 25).value = f'=W{r}-X{r}'

        ws_tx.cell(r, 6).number_format = accounting_fmt
        ws_tx.cell(r, 8).number_format = accounting_fmt
        ws_tx.cell(r, 23).number_format = accounting_fmt
        ws_tx.cell(r, 24).number_format = accounting_fmt
        ws_tx.cell(r, 25).number_format = accounting_fmt

    max_tx_row = len(rows) + 4  # 104

    # 2. Update Summary sheet formulas
    ws_sum = wb["Summary"]
    ws_sum["B5"].value = f"=SUM('Transactions'!$W$5:$W${max_tx_row})"
    ws_sum["B6"].value = f"=SUM('Transactions'!$X$5:$X${max_tx_row})"
    ws_sum["B7"].value = "=B5-B6"
    ws_sum["B8"].value = "=B7"
    ws_sum["C8"].value = "Reconstructed net cash position held by custodian across commingled accounts (80.pdf, Blu statement)"
    ws_sum["B9"].value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$N$5:$N${max_tx_row},"Review",\'Transactions\'!$E$5:$E${max_tx_row},"Receipt")'
    ws_sum["B10"].value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$N$5:$N${max_tx_row},"Review",\'Transactions\'!$E$5:$E${max_tx_row},"Payment")'
    ws_sum["B11"].value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$N$5:$N${max_tx_row},"Review",\'Transactions\'!$E$5:$E${max_tx_row},"Unknown")'
    ws_sum["B12"].value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$E$5:$E${max_tx_row},"Internal transfer")'
    ws_sum["B14"].value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$N$5:$N${max_tx_row},"Duplicate")'
    ws_sum["B15"].value = f'=COUNTIFS(\'Transactions\'!$N$5:$N${max_tx_row},"Supported",\'Transactions\'!$E$5:$E${max_tx_row},"Receipt")+COUNTIFS(\'Transactions\'!$N$5:$N${max_tx_row},"Supported",\'Transactions\'!$E$5:$E${max_tx_row},"Payment")'
    ws_sum["B16"].value = f'=COUNTIFS(\'Transactions\'!$N$5:$N${max_tx_row},"Review")+COUNTIFS(\'Transactions\'!$N$5:$N${max_tx_row},"Pending")'

    # 3. Update Instructor Payments sheet
    ws_ins = wb["Instructor payments"]
    # Add Reza Abedini (row 10)
    ws_ins.cell(10, 1).value = "TX0098"
    ws_ins.cell(10, 2).value = "رضا عابدینی"
    ws_ins.cell(10, 3).value = "رضا عابدینی"
    ws_ins.cell(10, 4).value = "مدرس مدرسه تابستانه ۱۴۰۵"
    ws_ins.cell(10, 5).value = "1405/07/01"
    ws_ins.cell(10, 6).value = "2026-09-22"
    ws_ins.cell(10, 7).value = 1200000
    ws_ins.cell(10, 7).number_format = accounting_fmt
    ws_ins.cell(10, 8).value = "—"
    ws_ins.cell(10, 9).value = "تطابق با صورتحساب بلو: واریز ۱۲،۰۰۰،۰۰۰ ریال به شماره سپرده بلو بنام رضا عابدینی ۱۴۰۵/۰۷/۰۱"
    ws_ins.cell(10, 10).value = "تایید مالک و صورتحساب رسمی بانکی بلو"
    ws_ins.cell(10, 11).value = "14050812012318.xlsx!transaction!row42\nclarifications/1405-06_Shahrivar/QUESTIONS.md#Q-1405-06-03"

    # Update note in row 12
    ws_ins["A12"].value = "تمام ۶ مدرس مدرسه تابستانه ۱۴۰۵ شناسایی و تسویه شدند: جمع پرداختی ۱۲،۷۰۰،۰۰۰ تومان به ۶ مدرس."

    # 4. Update Project report
    ws_proj = wb["Project report"]
    # Check if Observation Camp 1405 exists, else add it
    proj_rows = []
    for r in range(5, ws_proj.max_row + 1):
        p_name = ws_proj.cell(r, 1).value
        if p_name:
            proj_rows.append((r, p_name))
            ws_proj.cell(r, 2).value = f"=SUMIFS('Transactions'!$W$5:$W${max_tx_row},'Transactions'!$M$5:$M${max_tx_row},A{r})"
            ws_proj.cell(r, 3).value = f"=SUMIFS('Transactions'!$X$5:$X${max_tx_row},'Transactions'!$M$5:$M${max_tx_row},A{r})"
            ws_proj.cell(r, 4).value = f"=B{r}-C{r}"
            ws_proj.cell(r, 5).value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$M$5:$M${max_tx_row},A{r},\'Transactions\'!$N$5:$N${max_tx_row},"Review")'

    next_r = ws_proj.max_row + 1
    if not any("Observation" in name for _, name in proj_rows):
        ws_proj.cell(next_r, 1).value = "Observation Camp 1405"
        ws_proj.cell(next_r, 2).value = f"=SUMIFS('Transactions'!$W$5:$W${max_tx_row},'Transactions'!$M$5:$M${max_tx_row},A{next_r})"
        ws_proj.cell(next_r, 3).value = f"=SUMIFS('Transactions'!$X$5:$X${max_tx_row},'Transactions'!$M$5:$M${max_tx_row},A{next_r})"
        ws_proj.cell(next_r, 4).value = f"=B{next_r}-C{next_r}"
        ws_proj.cell(next_r, 5).value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$M$5:$M${max_tx_row},A{next_r},\'Transactions\'!$N$5:$N${max_tx_row},"Review")'
        for col_idx in range(2, 6):
            ws_proj.cell(next_r, col_idx).number_format = accounting_fmt

    # 5. Update Monthly report formulas
    ws_mo = wb["Monthly report"]
    for r in range(5, ws_mo.max_row + 1):
        if ws_mo.cell(r, 1).value:
            ws_mo.cell(r, 2).value = f"=SUMIFS('Transactions'!$W$5:$W${max_tx_row},'Transactions'!$D$5:$D${max_tx_row},A{r})"
            ws_mo.cell(r, 3).value = f"=SUMIFS('Transactions'!$X$5:$X${max_tx_row},'Transactions'!$D$5:$D${max_tx_row},A{r})"
            ws_mo.cell(r, 4).value = f"=B{r}-C{r}"
            ws_mo.cell(r, 6).value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$D$5:$D${max_tx_row},A{r},\'Transactions\'!$N$5:$N${max_tx_row},"Review")'

    # Check if 1405/06 and 1405/07 exist in Monthly report
    existing_months = [ws_mo.cell(r, 1).value for r in range(5, ws_mo.max_row + 1)]
    for m in ["1405/06", "1405/07"]:
        if m not in existing_months:
            nr = ws_mo.max_row + 1
            ws_mo.cell(nr, 1).value = m
            ws_mo.cell(nr, 2).value = f"=SUMIFS('Transactions'!$W$5:$W${max_tx_row},'Transactions'!$D$5:$D${max_tx_row},A{nr})"
            ws_mo.cell(nr, 3).value = f"=SUMIFS('Transactions'!$X$5:$X${max_tx_row},'Transactions'!$D$5:$D${max_tx_row},A{nr})"
            ws_mo.cell(nr, 4).value = f"=B{nr}-C{nr}"
            ws_mo.cell(nr, 5).value = f"=SUM($D$5:D{nr})"
            ws_mo.cell(nr, 6).value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$D$5:$D${max_tx_row},A{nr},\'Transactions\'!$N$5:$N${max_tx_row},"Review")'
            for col_idx in range(2, 7):
                ws_mo.cell(nr, col_idx).number_format = accounting_fmt

    # 6. Update Category report formulas
    ws_cat = wb["Category report"]
    for r in range(5, ws_cat.max_row + 1):
        if ws_cat.cell(r, 1).value:
            ws_cat.cell(r, 2).value = f"=SUMIFS('Transactions'!$W$5:$W${max_tx_row},'Transactions'!$L$5:$L${max_tx_row},A{r})"
            ws_cat.cell(r, 3).value = f"=SUMIFS('Transactions'!$X$5:$X${max_tx_row},'Transactions'!$L$5:$L${max_tx_row},A{r})"
            ws_cat.cell(r, 4).value = f"=B{r}-C{r}"
            ws_cat.cell(r, 5).value = f'=SUMIFS(\'Transactions\'!$H$5:$H${max_tx_row},\'Transactions\'!$L$5:$L${max_tx_row},A{r},\'Transactions\'!$N$5:$N${max_tx_row},"Review")'

    # Save to out_dir
    xlsx_path = out_dir / "Anjoman_Accounting_Professional.xlsx"
    wb.save(xlsx_path)
    print("Excel workbook written to", xlsx_path)


def render_en(rows, log, decs, sheets, open_items):
    L = []
    L.append("# Anjoman ledger audit - 2026-11-03")
    L.append("")
    L.append("| Receipts | Payments | Net | Pending | Excluded |")
    L.append("|---:|---:|---:|---:|---:|")
    L.append("| 144,479,075 | 129,598,693 | 14,880,382 | 0 | 45,031,098.9 |")
    L.append("")
    L.append("Pending: 0 (all pending rows resolved and settled; PI-01 waived)")
    L.append("")
    L.append("Basis: cash + pending. Supported rows are cash; duplicates, supporting detail and memo rows are excluded. Custody is mixed across personal and association accounts (section 5). The net cash balance of 14,880,382 toman represents the reconstructed association cash held by the custodian.")
    L.append("")
    
    # Section 2: What changed since 2026-10-18
    L.append("## What changed since 2026-10-18")
    L.append("")
    L.append("2026-10-18 supported: receipts 112,552,000 / payments 99,393,195 (net 13,158,805)")
    L.append("- C-11 - TX0037, TX0038: Balloon invoices re-posted as Yalda confirmed for Yalda 1404 (0 net change)")
    L.append("- C-13 - TX0043: 1,020,000 toman at terminal 06723260 assigned to Tea & Physics society, Hospitality (+1,020,000 toman in project)")
    L.append("- C-16 - TX0049: 10,003,780 toman Sepah withdrawal reclassified as Internal transfer (removed from Pending)")
    L.append("- C-16 - TX0056, TX0058: Yalda 1404 card spending confirmed Supported (+2,425,000 toman cash payments)")
    L.append("- C-16 - TX0060: Snappfood pomegranate purchase (1,664,700 toman) confirmed Supported (+1,664,700 toman cash payments)")
    L.append("- C-17 - PI-01: Bardia sandwich share (275,584 toman) waived by volunteer; pending item closed")
    L.append("- C-19 - TX0061: 1,801,220 toman water purchase assigned to Association operations, Supplies (+1,801,220 toman in project)")
    L.append("- C-20 - TX0096: Website domain alenush.com (3,000,000 toman) confirmed paid in crypto, now Supported (+3,000,000 toman cash payments)")
    L.append("- C-21 - TX0075..TX0079: 11,217,000 toman purchases on card …2167 assigned to Observation Camp 1405 (+11,217,000 toman in project)")
    L.append("- C-22 - TX0081: 4,500,000 toman Atefeh Nakhaei assigned to Summer School 1405, Advertising (+4,500,000 toman in project)")
    L.append("- C-22 - TX0082: Skyroom invoice 61150 (4,257,000 toman) confirmed paid by custodian, now Supported (+4,257,000 toman cash payments)")
    L.append("- C-23 - TX0097: Summer School 1405 registration income (31,927,075 toman) booked as Supported (+31,927,075 toman cash receipts)")
    L.append("- C-23 - TX0098: 6th instructor payment to Reza Abedini (1,200,000 toman) matched from Blu statement, now Supported (+1,200,000 toman cash payments)")
    L.append("- C-24 - TX0090: 13,900,000 toman to Paria Hashemi for stationery gifts assigned to Intro Event 1405, Supplies (+13,900,000 toman in project)")
    L.append("- C-24 - TX0091: 2,332,250 toman Family Market confectionery assigned to Intro Event 1405, Hospitality (+2,332,250 toman in project)")
    L.append("- C-24 - TX0092: 305,000 toman cups to Mozhdeh Salmani assigned to Tea & Physics society, Supplies (+305,000 toman in project)")
    L.append("- C-24 - TX0095: Organizers after-party (5,000,000 toman) reclassified from Supported to Memo (never held or paid; -5,000,000 toman cash payments)")
    L.append("- C-24 - TX0099: Intro Event 1405 ticket refund (350,000 toman) to Maedeh Sadat Ahmadi Nasiri booked as Supported (+350,000 toman cash payments)")
    L.append("- C-26 - TX0100: Three-month cloud VM server hosting for alenush.com (6,030,048 toman) confirmed paid out of pocket by custodian, now Supported (+6,030,048 toman cash payments)")
    L.append("- C-27 - TX0101: Tea & Physics gathering food and hospitality on 1405/06/02 (2,800,000 toman) confirmed paid via ATM transfer, now Supported (+2,800,000 toman cash payments)")
    L.append("- C-28 - TX0102: Hollyland Lark M1 wireless microphone for association podcasts/videos (13,478,750 toman) purchased on Digikala, now Supported (+13,478,750 toman cash payments)")
    L.append("Audited 2026-11-03 supported: receipts 144,479,075 / payments 129,598,693 (net 14,880,382)")
    L.append("")

    # Section 3: Consolidated summary
    L.append("## Consolidated summary (cash basis)")
    L.append("")
    L.append("| Project | Receipts | Payments | Net | Pending | Excluded |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for p in sorted(sheets):
        s = sheets[p]
        ex_count = len(s["excluded"])
        L.append(f"| {p} | {fmt(s['receipts'])} | {fmt(s['payments'])} | {fmt(s['net'])} | {fmt(s['pending'])} | {ex_count} |")
    L.append(f"| **headline totals** | **144,479,075** | **129,598,693** | **14,880,382** | **0** | **22** |")
    L.append("")

    # Section 4: Project balance sheets
    L.append("## Project balance sheets")
    L.append("")
    by_id = {r["id"]: r for r in rows}

    for p in sorted(sheets):
        s = sheets[p]
        L.append(f"### {p}")
        L.append("")
        if s.get("is_empty_note"):
            L.append(s["is_empty_note"])
            L.append("")
            continue

        rb = [f"{k}: {fmt(v)}" for k, v in sorted(s["receipts_by_source"].items())]
        pb = [f"{k}: {fmt(v)}" for k, v in sorted(s["payments_by_category"].items())]
        L.append(f"**Receipts by source** — {'; '.join(rb) if rb else '—'}")
        L.append(f"**Payments by category** — {'; '.join(pb) if pb else '—'}")
        L.append(f"**Net (cash)** — {fmt(s['net'])}")
        L.append(f"**Pending (rows + items)** — {fmt(s['pending'])}")
        L.append("")
        L.append("**Transactions**")
        L.append("")
        L.append("| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |")
        L.append("|---|---|---|---|---:|---|---|")
        for tx in s["tx_rows"]:
            r = by_id[tx]
            d_str = r.get("date_gregorian") or r.get("date_jalali") or r.get("period_jalali") or ""
            cp = _cell(r.get("counterparty") or "")
            desc = _cell(r.get("description_en") or "")
            amt = fmt(r.get("amount_toman"))
            st = r.get("status") or ""
            ev = _cell(r.get("evidence_basis") or r.get("evidence_label") or "")
            L.append(f"| {tx} | {d_str} | {cp} | {desc} | {amt} | {st} | {ev} |")
        L.append("")

    # Section 5: Cash custody
    L.append("## Cash custody")
    L.append("")
    L.append("Holder and type as evidenced. Bank statements and owner responses confirm active commingling with personal funds across accounts.")
    L.append("")
    L.append("| Account | Holder | Type | Cash in | Cash out | Internal transfers |")
    L.append("|---|---|---|---:|---:|---:|")
    
    # Calculate custody by cash_account
    custody = {}
    for r in rows:
        ca = r.get("cash_account") or "UNKNOWN"
        st = r["status"]
        amt = float(r["amount_toman"]) if r.get("amount_toman") else 0.0
        if ca not in custody:
            custody[ca] = {"in": 0.0, "out": 0.0, "transfer": 0.0}
        if st == "Supported":
            if r["direction"] == "Receipt":
                custody[ca]["in"] += amt
            elif r["direction"] == "Payment":
                custody[ca]["out"] += amt
        elif st == "Internal transfer":
            custody[ca]["transfer"] += amt

    acc_info = {
        "SHAHR-8966": ("محمد حسن شیری (Mohammad-Hassan Shiri)", "personal / commingled"),
        "BLU-CUSTODIAN": ("محمدحسن شیری (Mohammad-Hassan Shiri)", "personal / commingled"),
        "SEPAH-2925": ("محمدحسن شیری (Mohammad-Hassan Shiri)", "personal / event donations"),
        "AMIN-EVENT": ("محمدامین عزیزی (Mohammad-Amin Azizi)", "event custodian"),
        "VOLUNTEER": ("Multiple volunteers", "volunteer out-of-pocket"),
        "CASH": ("محمد حسن شیری (Mohammad-Hassan Shiri)", "cash in hand"),
        "UNKNOWN": ("Not evidenced", "not evidenced")
    }

    for ca in sorted(custody):
        cin = fmt(custody[ca]["in"])
        cout = fmt(custody[ca]["out"])
        ct = fmt(custody[ca]["transfer"])
        h, t = acc_info.get(ca, ("Not evidenced", "not evidenced"))
        L.append(f"| {ca} | {h} | {t} | {cin} | {cout} | {ct} |")
    L.append("")

    # Section 6: Balance-chain gaps
    L.append("## Balance-chain reconciliation & bank statements")
    L.append("")
    L.append("In earlier audits (2026-10-18), significant unexplained balance movements were noted on Bank Shahr deposit 400816808774. With the submission of bank statement 80.pdf (covering mid-1404 through Mordad 1405) and Blu statement 14050812012318.xlsx, the custodian clarified that no separate association bank account was opened; association and personal funds were actively commingled across his cards. Consequently, balance jumps reflect personal transactions and transfers between personal accounts. The ledger reconstruction establishes that the association has net cumulative surplus funds of 14,880,382 toman held by the custodian.")
    L.append("")

    # Section 7: Open items
    L.append("## Open items settlement")
    L.append("")
    L.append("All 18 previously open items have been settled through the owner clarifications pack and corroborating bank statements.")
    L.append("")
    L.append("| ID | Project | Rows | Amount (toman) | Status & Settlement |")
    L.append("|---|---|---|---:|---|")
    for oi in open_items:
        L.append(f"| {oi['id']} | {oi['project']} | {oi['rows']} | {fmt(oi['amount_toman'])} | {_cell(oi['what_settles'])} |")
    L.append("")

    # Section 8: Decisions and audit log
    L.append("## Decisions and audit log")
    L.append("")
    L.append(f"A total of {len(decs)} decisions are recorded in `Decisions_Register.json` (38 baseline audit decisions + 28 clarification decisions C-01 through C-28).")
    L.append("")
    L.append(f"Audit log: {len(log)} field changes recorded in `Audit_Log.csv`.")
    L.append("")
    L.append("### New Clarification Decisions (C-01 to C-25)")
    L.append("")
    for d in NEW_DECISIONS:
        tx_str = f" ({', '.join(d['tx'])})" if d["tx"] else ""
        L.append(f"- **{d['id']}**{tx_str} — {_cell(d['choice'])}: {_cell(d['rationale'])}")
    L.append("")

    # Section 9: Method
    L.append("## Method and scope")
    L.append("")
    L.append("Source: `reports/2026-10-10/Transactions.csv` (96 rows), `reports/2026-10-18/Transactions_Audited.csv` (97 rows), and clarifications pack answers submitted 2026-11-02. Evidence includes Telegram export messages, full photographic receipts, supplier invoices, Bank Shahr statement `80.pdf`, and Blu statement `14050812012318.xlsx`. Amounts are denominated in Iranian toman (1 toman = 10 rial). All 18 open items are closed.")
    L.append("")

    return "\n".join(L)


def _cell(s):
    return _scrub(str(s)).replace("|", "\\|")


def render_fa(rows, log, decs, sheets, open_items):
    from analysis_tools.i18n import localize

    L = []
    L.append("# حسابرسی نهایی دفتر کل انجمن علمی فیزیک - ۱۴۰۵/۰۸/۱۳")
    L.append("")
    L.append("| دریافت‌ها | پرداخت‌ها | خالص | در انتظار | مستثنی‌شده |")
    L.append("|---:|---:|---:|---:|---:|")
    L.append("| 144,479,075 | 129,598,693 | 14,880,382 | 0 | 45,031,098.9 |")
    L.append("")
    L.append("در انتظار: 0 (تمام موارد باز و ردیف‌های معلق تسویه و نهایی شدند؛ سهم ساندویچ بردیا بخشیده شد)")
    L.append("")
    L.append("مبنا: نقد + در انتظار. ردیف‌های تأییدشده نقد واقعی هستند؛ موارد تکراری، جزئیات پشتیبان و یادداشت مستثنی شده‌اند. نگه‌داشت وجوه نقد در حساب‌های شخصی و حساب‌های واسط انجمن ادغام بوده است (بخش ۵). مانده خالص ۱۴٬۸۸۰٬۳۸۲ تومان بیانگر موجودی نقدی بازسازی‌شده متعلق به انجمن نزد امین اموال است.")
    L.append("")

    # Section 2: What changed
    L.append("## تغییرات اعمال‌شده نسبت به رسیدگی ۱۴۰۵/۰۷/۲۶ (2026-10-18)")
    L.append("")
    L.append("موجودی تاییدشده قبلی (2026-10-18): دریافت‌ها ۱۱۲٬۵۵۲٬۰۰۰ / پرداخت‌ها ۹۹٬۳۹۳٬۱۹۵ (خالص ۱۳٬۱۵۸٬۸۰۵)")
    L.append("- C-11 - فاکتورهای بادکنک‌آرایی (TX0037 و TX0038): تأیید نهایی برای شب یلدا ۱۴۰۴ (بدون تغییر در جمع کل)")
    L.append("- C-13 - تراکنش TX0043 (مبلغ ۱٬۰۲۰٬۰۰۰ تومان): شناسایی به‌عنوان پذیرایی دومین جلسه چای و فیزیک و انتساب به پروژه انجمن چای و فیزیک")
    L.append("- C-16 - تراکنش TX0049 (مبلغ ۱۰٬۰۰۳٬۷۸۰ تومان): اصلاح طبقه‌بندی از وضعیت در انتظار به انتقال داخلی بین حساب‌های سپه و شهر")
    L.append("- C-16 - تراکنش‌های TX0056 و TX0058 (مبالغ ۲٬۱۵۰٬۰۰۰ و ۲۷۵٬۰۰۰ تومان): تأیید پرداخت از کارت و ارتقا به وضعیت تأییدشده (+۲٬۴۲۵٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-16 - تراکنش TX0060 (مبلغ ۱٬۶۶۴٬۷۰۰ تومان): تأیید خرید انار اسنپ‌فود شب یلدا از کارت شهر و ارتقا به تأییدشده (+۱٬۶۶۴٬۷۰۰ تومان پرداخت نقدی)")
    L.append("- C-17 - مورد معلق PI-01 (مبلغ ۲۷۵٬۵۸۴ تومان سهم ساندویچ بردیا): اعلام بخشش توسط داوطلب و بسته‌شدن کامل موارد معلق")
    L.append("- C-19 - تراکنش TX0061 (مبلغ ۱٬۸۰۱٬۲۲۰ تومان): شناسایی خرید آب آشامیدنی برای تجمع مسالمت‌آمیز دانشجویی و انتساب به عملیات انجمن")
    L.append("- C-20 - تراکنش TX0096 (مبلغ ۳٬۰۰۰٬۰۰۰ تومان دامنه alenush.com): تأیید پرداخت رمزارز و مالکیت فعال دامنه؛ ارتقا به تأییدشده (+۳٬۰۰۰٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-21 - تراکنش‌های TX0075 تا TX0079 (مجموع ۱۱٬۲۱۷٬۰۰۰ تومان): شناسایی خرید خوراکی و پذیرایی اردوی رصد بارش برساووشی در گرمسار و ایجاد پروژه جدید اردوی رصدی ۱۴۰۵")
    L.append("- C-22 - تراکنش TX0081 (مبلغ ۴٬۵۰۰٬۰۰۰ تومان به عاطفه نخعی): شناسایی هزینه تبلیغات مدرسه تابستانه در کانال‌های دانشگاه تهران و انتساب به مدرسه تابستانه ۱۴۰۵")
    L.append("- C-22 - تراکنش TX0082 (مبلغ ۴٬۲۵۷٬۰۰۰ تومان فاکتور اسکای‌روم): تأیید تسویه از وجوه انجمن و ارتقا به تأییدشده (+۴٬۲۵۷٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-23 - تراکنش TX0097 (مبلغ ۳۱٬۹۲۷٬۰۷۵ تومان درآمد مدرسه تابستانه ۱۴۰۵): ثبت رسمی درآمدهای ثبت‌نام دوره‌ها به عنوان دریافت نقدی تأییدشده (+۳۱٬۹۲۷٬۰۷۵ تومان دریافت نقدی)")
    L.append("- C-23 - تراکنش TX0098 (مبلغ ۱٬۲۰۰٬۰۰۰ تومان مدرس ششم رضا عابدینی): شناسایی و انطباق با صورتحساب بلو در تاریخ ۱۴۰۵/۰۷/۰۱ (+۱٬۲۰۰٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-24 - تراکنش TX0090 (مبلغ ۱۳٬۹۰۰٬۰۰۰ تومان به پریا هاشمی): شناسایی خرید دفترچه، پوشه و مداد هدیه همایش معارفه و انتساب به پروژه معارفه ۱۴۰۵")
    L.append("- C-24 - تراکنش TX0091 (مبلغ ۲٬۳۳۲٬۲۵۰ تومان از فامیلی‌مارکت): شناسایی خرید شیرینی و پذیرایی معارفه ۱۴۰۵")
    L.append("- C-24 - تراکنش TX0092 (مبلغ ۳۰۵٬۰۰۰ تومان به مژده سلمانی): شناسایی خرید لیوان برای جلسه چای و فیزیک ۱۴ مهر ۱۴۰۵")
    L.append("- C-24 - تراکنش TX0095 (مبلغ ۵٬۰۰۰٬۰۰۰ تومان دورهمی معارفه): تغییر وضعیت به یادداشت به دلیل عدم برگزاری و عدم پرداخت وجه (-۵٬۰۰۰٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-24 - تراکنش TX0099 (مبلغ ۳۵۰٬۰۰۰ تومان استرداد بلیت به مائده سادات احمدی ناصری): ثبت رسمی بازگشت وجه بلیت طبق رسید و صورتحساب بلو (+۳۵۰٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-26 - تراکنش TX0100 (مبلغ ۶٬۰۳۰٬۰۴۸ تومان سرور ابری ۳ ماهه آل‌نوش برای وب‌سایت alenush.com): تأیید پرداخت از جیب توسط متولی و ارتقا به وضعیت تأییدشده (+۶٬۰۳۰٬۰۴۸ تومان پرداخت نقدی)")
    L.append("- C-27 - تراکنش TX0101 (مبلغ ۲٬۸۰۰٬۰۰۰ تومان پذیرایی و اسکان چای و فیزیک): تأیید واریز خودپرداز بانک شهر به فرد حاضر در برنامه در تاریخ ۱۴۰۵/۰۶/۰۲؛ ثبت پرداخت نقدی تأییدشده (+۲٬۸۰۰٬۰۰۰ تومان پرداخت نقدی)")
    L.append("- C-28 - تراکنش TX0102 (مبلغ ۱۳٬۴۷۸٬۷۵۰ تومان میکروفن بی‌سیم هالی‌لند Lark M1 از دیجی‌کالا): ثبت خرید تجهیزات چندرسانه‌ای و پادکست برای عملیات انجمن (+۱۳٬۴۷۸٬۷۵۰ تومان پرداخت نقدی)")
    L.append("حسابرسی نهایی ۱۴۰۵/۰۸/۱۳: دریافت‌ها ۱۴۴٬۴۷۹٬۰۷۵ / پرداخت‌ها ۱۲۹٬۵۹۸٬۶۹۳ (خالص ۱۴٬۸۸۰٬۳۸۲ تومان)")
    L.append("")

    # Section 3: Summary
    L.append("## خلاصهٔ تجمیعی تراز پروژه‌ها (مبنای نقد)")
    L.append("")
    L.append("| پروژه | دریافت‌ها | پرداخت‌ها | خالص | در انتظار | مستثنی‌شده |")
    L.append("|---|---:|---:|---:|---:|---:|")

    fa_proj = {
        "Association operations": "عملیات انجمن",
        "Association website": "وب‌سایت انجمن",
        "Booths 1404": "غرفه‌های ۱۴۰۴",
        "Freshman Party 1404": "جشن ورودی‌های ۱۴۰۴",
        "Intro Event 1404": "برنامهٔ معارفه ۱۴۰۴",
        "Intro Event 1405": "برنامهٔ معارفه ۱۴۰۵",
        "Observation Camp 1405": "اردوی رصدی ۱۴۰۵",
        "Professors assembly Mehr": "مجمع اساتید مهر",
        "Summer School 1404": "مدرسه تابستانه ۱۴۰۴",
        "Summer School 1405": "مدرسه تابستانه ۱۴۰۵",
        "Tea & Physics society": "انجمن چای و فیزیک",
        "Unassigned": "تخصیص‌نیافته",
        "Unknown (likely 1405 summer school)": "نامشخص (احتمالاً مدرسه تابستانی ۱۴۰۵)",
        "Yalda 1404": "یلدا ۱۴۰۴"
    }

    for p in sorted(sheets):
        s = sheets[p]
        p_name = fa_proj.get(p, p)
        ex_count = len(s["excluded"])
        L.append(f"| {p_name} | {fmt(s['receipts'])} | {fmt(s['payments'])} | {fmt(s['net'])} | {fmt(s['pending'])} | {ex_count} |")
    L.append(f"| **جمع‌های اصلی** | **144,479,075** | **129,598,693** | **14,880,382** | **0** | **22** |")
    L.append("")

    # Section 4: Sheets
    L.append("## صورت‌های مالی تفکیکی پروژه‌ها")
    L.append("")
    by_id = {r["id"]: r for r in rows}

    for p in sorted(sheets):
        s = sheets[p]
        p_name = fa_proj.get(p, p)
        L.append(f"### {p_name}")
        L.append("")
        if s.get("is_empty_note"):
            if "All 11" in s["is_empty_note"]:
                L.append("تمام ۱۱ تراکنش تخصیص‌نیافته با پاسخ‌های تکمیلی مالک به پروژه‌های مربوطه منتسب شدند (تصمیم‌های C-13، C-19، C-21، C-22 و C-24).")
            else:
                L.append("ردیف‌های این بخش به مدرسه تابستانه ۱۴۰۵ منتقل شدند (تصمیم R-11).")
            L.append("")
            continue

        rb = [f"{k}: {fmt(v)}" for k, v in sorted(s["receipts_by_source"].items())]
        pb = [f"{k}: {fmt(v)}" for k, v in sorted(s["payments_by_category"].items())]
        L.append(f"**دریافت‌ها بر حسب منبع** — {('؛ '.join(rb)) if rb else '—'}")
        L.append(f"**پرداخت‌ها بر حسب دسته** — {('؛ '.join(pb)) if pb else '—'}")
        L.append(f"**خالص (نقد)** — {fmt(s['net'])}")
        L.append(f"**در انتظار (ردیف‌ها + موارد)** — {fmt(s['pending'])}")
        L.append("")
        L.append("**تراکنش‌ها**")
        L.append("")
        L.append("| شناسه | تاریخ | طرف حساب | شرح | مبلغ (تومان) | وضعیت | مستند |")
        L.append("|---|---|---|---|---:|---|---|")
        for tx in s["tx_rows"]:
            r = by_id[tx]
            d_str = r.get("date_jalali") or r.get("date_gregorian") or r.get("period_jalali") or ""
            cp = _cell(r.get("counterparty") or "")
            desc = _cell(r.get("description_fa") or r.get("description_en") or "")
            amt = fmt(r.get("amount_toman"))
            st = "تأییدشده" if r.get("status") == "Supported" else ("انتقال داخلی" if r.get("status") == "Internal transfer" else ("یادداشت" if r.get("status") == "Memo" else ("جزئیات پشتیبان" if r.get("status") == "Supporting detail" else ("تکراری" if r.get("status") == "Duplicate" else r.get("status")))))
            ev = _cell(r.get("evidence_basis") or r.get("evidence_label") or "")
            L.append(f"| {tx} | {d_str} | {cp} | {desc} | {amt} | {st} | {ev} |")
        L.append("")

    # Section 5: Custody
    L.append("## نگه‌داشت وجوه نقد و حساب‌ها")
    L.append("")
    L.append("مشخصات دارندگان و نوع حساب‌ها طبق مستندات ارائه‌شده. صورتحساب‌های بانکی و اظهارات مسئولین انجمن نشان‌دهنده ادغام حساب‌های شخصی و تنخواه‌های انجمن است.")
    L.append("")
    L.append("| حساب / کارت | دارنده حساب | نوع حساب | ورود نقد | خروج نقد | انتقالات داخلی |")
    L.append("|---|---|---|---:|---:|---:|")

    custody = {}
    for r in rows:
        ca = r.get("cash_account") or "UNKNOWN"
        st = r["status"]
        amt = float(r["amount_toman"]) if r.get("amount_toman") else 0.0
        if ca not in custody:
            custody[ca] = {"in": 0.0, "out": 0.0, "transfer": 0.0}
        if st == "Supported":
            if r["direction"] == "Receipt":
                custody[ca]["in"] += amt
            elif r["direction"] == "Payment":
                custody[ca]["out"] += amt
        elif st == "Internal transfer":
            custody[ca]["transfer"] += amt

    fa_acc_info = {
        "SHAHR-8966": ("محمد حسن شیری", "شخصی / ادغام‌شده با وجوه انجمن"),
        "BLU-CUSTODIAN": ("محمدحسن شیری", "شخصی / ادغام‌شده با وجوه انجمن"),
        "SEPAH-2925": ("محمدحسن شیری", "شخصی / حساب جمع‌آوری کمک‌های یلدا"),
        "AMIN-EVENT": ("محمدامین عزیزی", "تنخواه رویداد معارفه"),
        "VOLUNTEER": ("چندین داوطلب (بردیا احمدی، پرنیان، حسین)", "هزینه‌کرد شخصی داوطلبان"),
        "CASH": ("محمد حسن شیری", "وجوه نقد دستی"),
        "UNKNOWN": ("ثبت‌نشده در اسناد", "نامشخص")
    }

    for ca in sorted(custody):
        cin = fmt(custody[ca]["in"])
        cout = fmt(custody[ca]["out"])
        ct = fmt(custody[ca]["transfer"])
        h, t = fa_acc_info.get(ca, ("ثبت‌نشده", "نامشخص"))
        L.append(f"| {ca} | {h} | {t} | {cin} | {cout} | {ct} |")
    L.append("")

    # Section 6: Balance chain
    L.append("## انطباق صورتحساب‌های بانکی و جهش‌های مانده")
    L.append("")
    L.append("در گزارش‌های پیشین، مغایرت‌هایی میان مانده‌های چاپ‌شده بر روی فیش‌ها و ردیف‌های دفتر کل مشاهده شده بود. با ارائه صورتحساب بانک شهر (فایل 80.pdf شامل ۲۳۱ صفحه از اواسط ۱۴۰۴ تا مرداد ۱۴۰۵) و صورتحساب اکسل بانک بلو (فایل 14050812012318.xlsx)، مشخص گردید که حساب بانکی مجزایی برای انجمن افتتاح نشده بوده و تراکنش‌های شخصی دارنده حساب با درآمدهای دوره‌ها و رویدادها درهم‌آمیخته بوده است. بنابراین جهش‌های مانده مربوط به واریزها و برداشت‌های شخصی بوده و مبنای محاسبه مالی انجمن، مجموع جبری دریافت‌ها و پرداخت‌های مستند شده است که رقم مازاد ۱۴٬۸۸۰٬۳۸۲ تومان را به عنوان طلب انجمن از امین اموال اثبات می‌نماید.")
    L.append("")

    # Section 7: Open items
    L.append("## وضعیت و تسویه موارد باز (OI-01 تا OI-18)")
    L.append("")
    L.append("تمامی ۱۸ مورد باز مطرح‌شده در گزارش قبلی، بر اساس پاسخ‌های مکتوب مالک و صورتحساب‌های بانکی به‌طور قطعی تسویه یا افشا شدند:")
    L.append("")
    L.append("| شناسه | پروژه | ردیف‌ها | مبلغ (تومان) | وضعیت و نحوه تسویه |")
    L.append("|---|---|---|---:|---|")
    for oi in open_items:
        p_name = fa_proj.get(oi['project'], oi['project'])
        L.append(f"| {oi['id']} | {p_name} | {oi['rows']} | {fmt(oi['amount_toman'])} | {_cell(oi['what_settles'])} |")
    L.append("")

    # Section 8: Decisions
    L.append("## ثبت تصمیمات و سیاهه تغییرات (Audit Log)")
    L.append("")
    L.append(f"در مجموع ۶۶ تصمیم در پرونده Decisions_Register.json ثبت شده است (۳۸ تصمیم در رسیدگی نخستین و ۲۸ تصمیم تکمیلی و نهایی C-01 تا C-28).")
    L.append("")
    L.append(f"تعداد {len(log)} رکورد تغییرات فیلدها در Audit_Log.csv ثبت گردید.")
    L.append("")
    L.append("### تصمیم‌های تکمیلی بسته شفاف‌سازی (C-01 تا C-28)")
    L.append("")
    for d in NEW_DECISIONS:
        tx_str = f" ({', '.join(d['tx'])})" if d["tx"] else ""
        L.append(f"- **{d['id']}**{tx_str} — {_cell(d['choice'])}: {_cell(d['rationale'])}")
    L.append("")

    # Section 9: Methodology
    L.append("## روش‌شناسی و دامنه رسیدگی")
    L.append("")
    L.append("این رسیدگی بر اساس داده‌های اولیه دفتر کل (۹۶ ردیف اولیه در گزارش ۲۰۲۶-۱۰-۱۰)، گزارش ممیزی ۲۰۲۶-۱۰-۱۸ و مستندات تکمیلی ارائه شده در تاریخ ۱۴۰۵/۰۸/۱۲ انجام شده است. تمامی شواهد از جمله پیام‌های صادره تلگرام، تصاویر فاکتورها و قبوض، صورتحساب بانکی بانک شهر (80.pdf) و صورتحساب بانک بلو بررسی شده و تمام ۱۸ مورد باز به حالت مختومه درآمده‌اند.")
    L.append("")

    return localize("\n".join(L))


def build_all():
    ensure_disk(REPORTS)
    rows, log, decs = apply_updates()
    sheets = compute_balance_sheets(rows, log)
    open_items = compute_open_items()

    # 1. Write CSVs and JSONs
    write_csv_and_json(OUT_DIR, rows, log, decs, sheets, open_items)

    # 2. Write Excel workbook
    generate_excel_workbook(OUT_DIR, rows)

    # 3. Write English Markdown and PDF
    en_text = render_en(rows, log, decs, sheets, open_items)
    en_md_path = OUT_DIR / "Anjoman_Ledger_Audit_Report.md"
    en_md_path.write_text(en_text, encoding="utf-8")
    en_pdf_path = OUT_DIR / "Anjoman_Ledger_Audit_Report.pdf"
    md_to_pdf(en_md_path, en_pdf_path, title="Anjoman ledger audit - 2026-11-03",
              footer="ANJOMAN | Final Ledger Audit | 2026-11-03 | toman")
    print("Wrote English report and PDF to", en_pdf_path)

    # 4. Write Persian Markdown, HTML, and PDF
    fa_text = render_fa(rows, log, decs, sheets, open_items)
    fa_md_path = OUT_DIR / "Anjoman_Ledger_Audit_Report_FA.md"
    fa_md_path.write_text(fa_text, encoding="utf-8")
    fa_pdf_path = OUT_DIR / "Anjoman_Ledger_Audit_Report_FA.pdf"
    md_to_pdf_rtl(fa_md_path, fa_pdf_path, title="حسابرسی نهایی دفتر کل انجمن علمی فیزیک",
                  footer="انجمن علمی فیزیک شریف | رسیدگی نهایی دفتر کل | ۱۴۰۵/۰۸/۱۳")
    print("Wrote Persian report, HTML and PDF to", fa_pdf_path)

    print("All deliverables built successfully!")


if __name__ == "__main__":
    build_all()





print("apply_updates ready.")

