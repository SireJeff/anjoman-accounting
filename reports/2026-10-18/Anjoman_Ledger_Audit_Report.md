# Anjoman ledger audit - 2026-10-18

| Receipts | Payments | Net | Pending | Excluded |
|---:|---:|---:|---:|---:|
| 112,552,000 | 99,393,195 | 13,158,805 | 21,626,064 | 40,031,098.9 |

Pending: 21,626,064 (rows 21,350,480 + PI-01 275,584)

Basis: cash + pending. Supported rows are cash; open reviews and unpaid invoices are pending; duplicates, supporting detail and memo rows are excluded. Net activity is not closing cash: custody is mixed across personal and association accounts (section 5).

## What changed since 2026-10-10

2026-10-10 supported: receipts 112,552,000 / payments 99,085,195
- R-01 - TX0036: TX0036 direction Unknown → Payment, now Supported (+300,000 toman)
- R-02 - TX0031: TX0031 amount corrected 235,000 → 230,000 (-5,000 toman)
- D-06 - TX0042: TX0042 separate 130,000-rial poster slip, now Supported (+13,000 toman)
Audited supported: receipts 112,552,000 / payments 99,393,195 (net 13,158,805)

2026-10-10 all rows: receipts 139,787,000 / payments 123,265,994
- R-02 - TX0031: TX0031 amount corrected 235,000 → 230,000 (-5,000 toman)
- R-06 - TX0049: TX0049 Sepah withdrawal filled at 10,003,780 toman, stays pending (+10,003,780 toman)
- R-07 - TX0058: TX0058 Yalda spend set to 275,000 toman, payable to Hossein (+275,000 toman)
Audited all rows: receipts 139,787,000 / payments 133,539,773.9 (net 6,247,226.1)

## Consolidated summary (cash basis)

| Project | Receipts | Payments | Net | Pending | Excluded |
|---|---:|---:|---:|---:|---:|
| Association operations | 34,000,000 | 3,597,700 | 30,402,300 | 0 | 0 |
| Association website | 0 | 0 | 0 | 3,000,000 | 0 |
| Booths 1404 | 0 | 1,990,000 | -1,990,000 | 0 | 0 |
| Freshman Party 1404 | 0 | 5,574,000 | -5,574,000 | 0 | 0 |
| Intro Event 1404 | 4,920,000 | 3,155,000 | 1,765,000 | 0 | 0 |
| Intro Event 1405 | 23,000,000 | 15,937,900 | 7,062,100 | 0 | 1 |
| Professors assembly Mehr | 500,000 | 1,142,375 | -642,375 | 0 | 1 |
| Summer School 1404 | 33,642,000 | 12,900,900 | 20,741,100 | 0 | 1 |
| Summer School 1405 | 0 | 11,950,000 | -11,950,000 | 4,257,000 | 0 |
| Tea & Physics society | 0 | 1,702,850 | -1,702,850 | 0 | 1 |
| Unassigned | 0 | 35,075,470 | -35,075,470 | 0 | 0 |
| Unknown (likely 1405 summer school) | 0 | 0 | 0 | 0 | 0 |
| Yalda 1404 | 16,490,000 | 6,367,000 | 10,123,000 | 14,369,064 | 17 |
| **headline totals** | **112,552,000** | **99,393,195** | **13,158,805** | **21,626,064** | **21** |

## Project balance sheets

### Association operations

**Receipts by source** — Former association (Mellat card …7532): 10,000,000; Former association (card …7532): 1,000,000; دکتر مقیمی: 7,000,000; سامان مقیمی عراقی: 16,000,000
**Payments by category** — Equipment: 2,285,000; Printing: 16,600; Supplies: 1,296,100
**Net (cash)** — 30,402,300
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0013 | 1404/05 (month only) | حسن شیری | Copies of association room keys for members, arranged by حسن شیری ('کلید ها که من زدم', message57); amount 750,000 from workbook only — evidence thin (message57; Anjoman accounting.xlsx!مجموع!D11). | 750,000 | Supported | original ledger |
| TX0026 | 2025-10-26 | Former association (Mellat card …7532) | Funds received from previous association board | 10,000,000 | Supported | photos/photo_20@28-10-2025_22-07-57.jpg (message71, forwarded from 'Mŏ̈bina', orig 28.10.2025 10:19:30) |
| TX0027 | 2025-10-27 | Former association (card …7532) | Second handover from previous association | 1,000,000 | Supported | photos/photo_18@28-10-2025_01-53-01.jpg (message67, forwarded from 'Mŏ̈bina', orig 28.10.2025 00:13:04) |
| TX0028 | 2025-10-25 | …پناهی (merchant) | Tissues for association room | 70,000 | Supported | photos/photo_31@27-06-2026_18-24-39.jpg (message144, no caption) |
| TX0029 | 2025-10-27 | Unknown | Projector connectors | 310,000 | Supported | message108 line 1 |
| TX0032 | 2025-10-28 | نیما کوهی | Reimbursement for camera battery (Digikala invoices 696,000+29,000) | 725,000 | Supported | photos/photo_19@28-10-2025_01-58-07.jpg (message69) |
| TX0034-B | 2025-10-29 | T…Mobile (احمدی) | Association operations equipment: 32GB Samsung USB flash drive ('فلش انجمن'), 500,000 toman, bought together with the Freshman Party 1404 prizes from T…Mobile (احمدی) (photo_35, message148). | 500,000 | Supported | — |
| TX0039 | 2025-11-19 | Unknown pharmacy | First-aid medicine | 1,226,100 | Supported | message109 |
| TX0040 | 2025-11-19 | Unknown | Printing room rules | 2,300 | Supported | message110 |
| TX0041 | 2025-11-19 | Unknown | Printing room rules (second line) | 1,300 | Supported | message110 |
| TX0042 | 2025-11-19 | کپی آرام گرافیک | Association poster printing | 13,000 | Supported | photos/photo_32@27-06-2026_18-24-52.jpg (message145) |
| TX0044 | 2025-11-19 | سامان مقیمی عراقی | Moghimi donation for running costs | 10,000,000 | Supported | photos/photo_25@19-11-2025_11-46-31.jpg (message102, forwarded from Saman Moghimi, original 19.11.2025 11:44:07) |
| TX0045 | 1404/09 (month only) | دکتر مقیمی | Donation from Dr. Saman Moghimi to support the association (Azar 1404), per treasurer ledger row مجموع!B39 only; no receipt or Telegram message for this 7,000,000 — evidence thin (Anjoman accounting.xlsx!مجموع!A39:B39). | 7,000,000 | Supported | original ledger |
| TX0046 | 2025-12-19 | سامان مقیمی عراقی | Moghimi donation | 6,000,000 | Supported | photos/photo_26@21-12-2025_05-36-21.jpg (message112) |

**Open items** — OI-04; OI-05

### Association website

**Receipts by source** — —
**Payments by category** — —
**Net (cash)** — 0
**Pending (rows + items)** — 3,000,000
- TX0096 — 3,000,000

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0096 | 1405/04 | Domain registrar not supplied | Purchase of alenush.com for the association website; user-declared expense without receipt | 3,000,000 | Pending | reports/2026-10-10/website_user_confirmation_2026-10-11.json |

### Booths 1404

**Receipts by source** — —
**Payments by category** — Equipment: 1,760,000; Hospitality: 230,000
**Net (cash)** — -1,990,000
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0030 | 2025-10-27 | Unknown | Power protectors and tools for booth projectors | 1,760,000 | Supported | message108 line 2 |
| TX0031 | 2025-10-27 | سوپر مارکت شریف پلاس | Booth refreshments | 230,000 | Supported | photos/photo_40@27-06-2026_18-31-08.jpg (message153) |

### Freshman Party 1404

**Receipts by source** — —
**Payments by category** — Events: 5,274,000; Unclassified: 300,000
**Net (cash)** — -5,574,000
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0033 | 2025-10-29 | رفاه دانشجویی | Freshman party prizes: notebooks and pens | 1,444,000 | Supported | photos/photo_33@27-06-2026_18-25-49.jpg (message146) |
| TX0034 | 2025-10-29 | T…Mobile (احمدی) | Freshman Party 1404 prizes: 8 earphones, 1,000,000 toman, from T…Mobile (احمدی) (photo_35, message107 line 2, message148). | 1,000,000 | Supported | photos/photo_35@27-06-2026_18-26-22.jpg (message148) |
| TX0035 | 2025-10-29 | Unknown | Prizes: bracelets and spinners | 1,400,000 | Supported | message107 line 3 |
| TX0036 | 2025-10-29 | Cash | Cash 'shabash' (cash handed out) at the 1404 freshman party, 300,000 toman; reported by the treasurer in message111 alongside party expense lines; recipient and cash source not shown (accounting_group#message111; Anjoman accounting.xlsx!مجموع!D29). | 300,000 | Supported | message111 |
| TX0037 | 2025-11-14 | اردوان شهبازی | Reimbursement: balloon glue (Shadzi invoice 29449) | 120,000 | Supported | photos/photo_21@09-11-2025_23-16-09.jpg (message90) |
| TX0038 | 2025-11-14 | سیده راحله مختاری | Reimbursement: party decorations (Shadzi invoice 13,100,000 rial) | 1,310,000 | Supported | photos/photo_22@09-11-2025_23-16-15.jpg (message91) |

### Intro Event 1404

**Receipts by source** — Participants, held by محمدامین عزیزی: 4,920,000
**Payments by category** — Events: 3,055,000; Printing: 100,000
**Net (cash)** — 1,765,000
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0014 | 2025-09-06 | Participants, held by محمدامین عزیزی | Major-introduction event receipts (gross) | 4,920,000 | Supported | Anjoman accounting.xlsx!شهریور!B2 and !مجموع!B15 |
| TX0015 | 2025-09-04 | چاپ بهزاد | Poster and barcode printing for intro table | 100,000 | Supported | photos/photo_11@04-09-2025_14-05-56.jpg (message48) |
| TX0016 | 2025-09-06 | محمدامین عزیزی | Intro-event (15 Shahrivar 1404) supplies/refreshments, handled by محمدامین عزیزی from event funds; amount from workbook only (part of 3,055,000 total in شهریور!D4 formula) — evidence thin (Anjoman accounting.xlsx!شهریور!D3 and !مجموع!D16; all chats searched, no message found). | 2,866,000 | Supported | Anjoman accounting.xlsx!شهریور!D3 and !مجموع!D16 |
| TX0017 | 2025-09-06 | ابراهیم خسروانی | Procurement fee to ابراهیم خسروانی for buying intro-event supplies; derived as 3,055,000 - 2,866,000 in the workbook — evidence thin (Anjoman accounting.xlsx!شهریور!D4 / مجموع!D17; all chats searched, no message found). | 189,000 | Supported | Anjoman accounting.xlsx!شهریور!D4 / مجموع!D17 |
| TX0018 | 2025-10-01 | AMIN-EVENT to SHAHR-8966 | Net intro-event proceeds moved to main account | 1,765,000 | Internal transfer | photos/photo_12@01-10-2025_18-02-44.jpg (message51) |

### Intro Event 1405

**Receipts by source** — Event platform / participants: 23,000,000
**Payments by category** — Events: 5,000,000; Hospitality: 9,987,900; Supplies: 950,000
**Net (cash)** — 7,062,100
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0088 | 2026-09-23 | زهرا امیری | Sticker packs for introduction event | 950,000 | Supported | recipts/photo_6_2026-10-10_11-09-04.jpg |
| TX0089 | 2026-09-23 | یاران دریان لوکس گیشا | Catering for Intro Event 1405: 100 Mihan milk drinks (80 cocoa, 20 coffee) and 90 Mazmaz cakes from Yaran Daryan Lux Gisha, invoice 165826 dated 1405/07/01 19:11 in the name of Mohammad-Hassan Shiri, 9,987,900 toman; settlement user-attested (recipts/photo_2026-10-10_12-16-28.jpg). | 9,987,900 | Supported | recipts/photo_2026-10-10_12-16-28.jpg |
| TX0093 | 1405/07 (month only) | Event platform / participants | Intro Event 1405 (1405/07/02) ticket income as entered by the treasurer (مجموع!B45, 'معرفی رشته', block 'مهر 05'); presumably the Evand payout, but no payout statement or bank deposit is in evidence (Anjoman accounting.xlsx!مجموع!A45:B45, physics_intro full report.pdf p1-2). | 23,000,000 | Supported | Anjoman accounting.xlsx!مجموع!A45:B45 |
| TX0094 | 2026-09-24 | Ticket buyers (90) | Platform-reported gross ticket sales | 27,235,000 | Memo | physics_intro full report.pdf p1 |
| TX0095 | 1405/07 (month only) | Unknown | Post-event gathering (after-party) of the Intro Event 1405 organizing team, apparently the evening of 1405/07/02 (public_group message5758); amount per treasurer ledger only (مجموع!D45); payee and receipt not shown (Anjoman accounting.xlsx!مجموع!D45:F45, public_group message5758). | 5,000,000 | Supported | original ledger |

**Excluded rows**

- TX0094 — Memo

**Open items** — OI-03; OI-06

### Professors assembly Mehr

**Receipts by source** — دکتر سامان مقیمی (card 6274…2662): 500,000
**Payments by category** — Hospitality: 1,052,375; Printing: 90,000
**Net (cash)** — -642,375
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0019 | 2025-10-14 | دکتر سامان مقیمی (card 6274…2662) | Donation for 22 Mehr assembly sweets | 500,000 | Supported | photos/photo_15@15-10-2025_14-18-25.jpg (message63) |
| TX0020 | 2025-10-12 | زهرا امیری | Posters for the 22 Mehr professors assembly and the Quanta circles, paid to زهرا امیری; one shared print run covering both events, booked under Professors assembly as a shared cost (photo_13, message61). | 90,000 | Supported | photos/photo_13@12-10-2025_10-24-38.jpg (message61) |
| TX0024 | 2025-10-14 | شیرینی مارژولن (terminal 14594032) | Pastry for professors assembly 22 Mehr | 1,052,375 | Supported | photos/photo_14@15-10-2025_14-18-25.jpg (message62) |
| TX0025 | 1404/07 (month only) | شیرینی مارژولن | Duplicate ledger row for professors pastry | 1,052,375 | Duplicate | Anjoman accounting.xlsx!مجموع!D23 |

**Excluded rows**

- TX0025 — Duplicate (TX0024)

### Summer School 1404

**Receipts by source** — Summer-school students (aggregate): 33,642,000
**Payments by category** — Advertising: 400,000; Bank fees: 900; Teaching: 12,500,000
**Net (cash)** — 20,741,100
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0001 | 2025-07-24 | Summer-school students (aggregate) | Summer School 1404 registration fees, aggregate of 3 courses (Python 81, LaTeX 89, Mathematica 73 students; course reports in message6-8 total 33,643 thousand toman). Collected on members' cards 18-22 Jul 2025 and asked to be consolidated into card …8966 (message6; message7; message8; private_group message3155). | 33,642,000 | Supported | message6; message7; message8 |
| TX0002 | 2025-07-24 | سهراب ملکی | Mathematica instructor fee, full settlement | 3,000,000 | Supported | photos/photo_1@24-07-2025_21-00-16.jpg (message25) |
| TX0003 | 2025-07-24 | امیرمحمد جوشقانی | Python instructor fee | 3,500,000 | Supported | photos/photo_2@24-07-2025_21-00-17.jpg (message26) |
| TX0004 | 2025-07-24 | متین جوکارتنگ کرمی | LaTeX instructor fee, Pol transfer | 3,700,000 | Supported | photos/photo_3@24-07-2025_21-02-51.jpg (message27) |
| TX0005 | 2025-07-25 | ابراهیم خسروانی | TA, forms and sheet fee | 500,000 | Supported | photos/photo_4@25-07-2025_04-04-24.jpg (message29) |
| TX0006 | 2025-07-25 | سپهر طلائی | Registration support and Python TA fee | 600,000 | Supported | photos/photo_5@25-07-2025_04-08-41.jpg (message30) |
| TX0007 | 2025-07-25 | محمدامین عزیزی | Registration, accounting and Python TA fee | 600,000 | Supported | photos/photo_6@25-07-2025_15-53-39.jpg (message31) |
| TX0008 | 2025-07-25 | Bank Shahr | Card transfer fee (SMS debit 6,009,000 minus principal 6,000,000 rial) | 900 | Supported | message32 |
| TX0009 | 2025-07-19 | محمدحسین مشک افشان | Summer school advertising on Mohemat Sharif channel | 400,000 | Supported | photos/photo_8@12-08-2025_09-58-34.jpg (message44, forwarded, original date 19.07.2025 16:42:32) |
| TX0010 | 1404/05 (month only) | حسن شیری | Second Mohemat Sharif ad row attributed to Hassan | 400,000 | Duplicate | Anjoman accounting.xlsx!مجموع!D12 |
| TX0011 | 2025-08-11 | متین جوکارتنگ کرمی | Make-up recording, LaTeX session 3 | 300,000 | Supported | photos/photo_7@11-08-2025_15-51-55.jpg (message42) |
| TX0012 | 2025-08-15 | امیرمحمد جوشقانی | Make-up recording, Python session 4 | 300,000 | Supported | photos/photo_10@15-08-2025_18-28-22.jpg (message47) |

**Excluded rows**

- TX0010 — Duplicate (TX0009)

**Open items** — OI-01

### Summer School 1405

**Receipts by source** — —
**Payments by category** — Advertising: 450,000; Teaching: 11,500,000
**Net (cash)** — -11,950,000
**Pending (rows + items)** — 4,257,000
- TX0082 — 4,257,000

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0080 | 2026-08-27 | محمدحسین مشک افشان | Blu-to-Blu transfer of 450,000 toman to Mohammad-Hossein Moshk-Afshan on 1405/06/05 21:52, very likely for advertising Summer School 1405 on the 'Sharif Admin'/Mohemat Sharif channel (same payee and channel as the 1404 ad TX0009; ad forwarded from 'Sharif Admin' 12 minutes later, public_group message516) (recipts/photo_5_2026-10-10_11-09-04.jpg, public_group message516). | 450,000 | Supported | recipts/photo_5_2026-10-10_11-09-04.jpg |
| TX0082 | 2026-08-29 | مهبانگ فن‌آوری‌های پارس (Skyroom) | Skyroom 1-month licence and 20h recording package | 4,257,000 | Pending | invoice-61150.pdf p1 |
| TX0083 | 2026-09-21 | زهرا صالح کوشالی | Summer School 1405 instructor fee to Zahra Saleh Koushali for the Python OOP course (2 sessions; summerschool_channel message32), 600,000 toman via Pol on 1405/06/30 15:33 (provisional receipt) (recipts/photo_1_2026-10-10_11-09-04.jpg). | 600,000 | Supported | recipts/photo_1_2026-10-10_11-09-04.jpg |
| TX0084 | 2026-09-21 | رضا فرهادی | Summer School 1405 instructor fee to Reza Farhadi for the Manim content-production course (3 sessions; summerschool_channel message33), 1,200,000 toman via Pol on 1405/06/30 15:34 (provisional receipt) (recipts/photo_2_2026-10-10_11-09-04.jpg). | 1,200,000 | Supported | recipts/photo_2_2026-10-10_11-09-04.jpg |
| TX0085 | 2026-09-21 | ابوالفضل احمدی (paid to علیرضا کچویی محقق یعقوبی) | Summer School 1405 instructor fee: LaTeX and API | 2,400,000 | Supported | recipts/photo_3_2026-10-10_11-09-04.jpg |
| TX0086 | 2026-09-23 | بهاره خویش‌خواه | Summer School 1405 instructor fee: Physical simulation with Python | 4,700,000 | Supported | recipts/photo_7_2026-10-10_11-09-04.jpg |
| TX0087 | 2026-09-23 | ایلیا اصغریان دهکردی | Summer School 1405 instructor fee to Ilia Asgharian Dehkordi for the introductory Python course (6 sessions; summerschool_channel message29), 2,600,000 toman Blu-to-Blu on 1405/07/01 01:09 (recipts/photo_8_2026-10-10_11-09-04.jpg). | 2,600,000 | Supported | recipts/photo_8_2026-10-10_11-09-04.jpg |

### Tea & Physics society

**Receipts by source** — —
**Payments by category** — Hospitality: 1,702,850
**Net (cash)** — -1,702,850
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0021 | 2025-10-12 | Merchant terminal 12926362 | Cups, biscuits and tea for Tea society | 790,000 | Supported | photos/photo_16@15-10-2025_14-18-26.jpg (message64) |
| TX0022 | 2025-10-12 | Merchant terminal 12926362 | Re-uploaded copy of the TX0021 receipt | 790,000 | Duplicate | recipts/photo_1_2026-10-10_14-07-27.jpg |
| TX0023 | 2025-10-12 | شیرینی مارژولن (terminal 14594032) | Pastry for Tea society meeting 20 Mehr | 912,850 | Supported | photos/photo_17@15-10-2025_14-18-26.jpg (message65) |

**Excluded rows**

- TX0022 — Duplicate (TX0021)

### Unassigned

**Receipts by source** — —
**Payments by category** — Unclassified: 35,075,470
**Net (cash)** — -35,075,470
**Pending (rows + items)** — 0

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0043 | 2025-11-23 | Merchant terminal 06723260 | Card purchase with association card …8966 at terminal 06723260 on 1404/09/02 13:21, 10,200,000 rial (1,020,000 toman), tracking 406547; purpose not shown in any message — evidence thin (recipts/photo_4_2026-10-10_14-07-27.jpg). | 1,020,000 | Supported | recipts/photo_4_2026-10-10_14-07-27.jpg |
| TX0061 | 2026-02-28 | Card …9676 (owner unknown) | Card-to-card transfer of 1,801,220 toman from the association's Bank Shahr card …8966 to card …9676 (holder not shown) on 1404/12/09 10:10; purpose not shown in any evidence (recipts/photo_6_2026-10-10_14-07-27.jpg). | 1,801,220 | Supported | recipts/photo_6_2026-10-10_14-07-27.jpg |
| TX0075 | 2026-08-12 | Terminal 80957455 | Card purchase of 6,337,000 toman at terminal 80957455 with Bank Shahr card …2167 on the association deposit 400816808774, 1405/05/21 17:43; merchant and purpose not shown (recipts/photo_3_2026-10-10_14-07-27.jpg). | 6,337,000 | Supported | recipts/photo_3_2026-10-10_14-07-27.jpg |
| TX0076 | 2026-08-13 | Terminal 09039608 | Card purchase at terminal 09039608 with Bank Shahr card …2167 on association deposit 400816808774, 1405/05/22 - 15:05; merchant and purpose not shown (recipts/photo_2_2026-10-10_14-07-27.jpg). | 1,100,000 | Supported | recipts/photo_2_2026-10-10_14-07-27.jpg |
| TX0077 | 2026-08-13 | Terminal 09039608 | Card purchase at terminal 09039608 with Bank Shahr card …2167 on association deposit 400816808774, 1405/05/22 - 15:11; merchant and purpose not shown (recipts/photo_5_2026-10-10_14-07-27.jpg). | 1,320,000 | Supported | recipts/photo_5_2026-10-10_14-07-27.jpg |
| TX0078 | 2026-08-13 | Terminal 03202703 | Card purchase at terminal 03202703 with Bank Shahr card …2167 on association deposit 400816808774, 1405/05/22 - 15:31; merchant and purpose not shown (recipts/photo_8_2026-10-10_14-07-27.jpg). | 1,300,000 | Supported | recipts/photo_8_2026-10-10_14-07-27.jpg |
| TX0079 | 2026-08-13 | Terminal 22958772 | Card purchase at terminal 22958772 with Bank Shahr card …2167 on association deposit 400816808774, 1405/05/22 - 15:35; merchant and purpose not shown (recipts/photo_7_2026-10-10_14-07-27.jpg). | 1,160,000 | Supported | recipts/photo_7_2026-10-10_14-07-27.jpg |
| TX0081 | 2026-08-28 | عاطفه نخعی | Card-to-card transfer of 4,500,000 toman from Hassan Shiri's Blu card …5780 to Atefeh Nakhaei (card …3063) on 1405/06/06 01:03; purpose not shown — evidence thin (recipts/photo_4_2026-10-10_11-09-04.jpg). | 4,500,000 | Supported | recipts/photo_4_2026-10-10_11-09-04.jpg |
| TX0090 | 2026-09-24 | پریا هاشمی | Card-to-card transfer of 13,900,000 toman from Hassan Shiri's Blu card …6947 to Paria Hashemi (card …0577) on 1405/07/02 10:03 (the Intro Event 1405 day); purpose not shown — evidence thin (recipts/photo_10_2026-10-10_11-09-04.jpg). | 13,900,000 | Supported | recipts/photo_10_2026-10-10_11-09-04.jpg |
| TX0091 | 2026-09-24 | Merchant 12738006 | Store purchase of 2,332,250 toman at merchant 12738006 from a Blu account (holder not shown) on 1405/07/02 10:17, the Intro Event 1405 day; items not shown (recipts/photo_11_2026-10-10_11-09-04.jpg). | 2,332,250 | Supported | recipts/photo_11_2026-10-10_11-09-04.jpg |
| TX0092 | 2026-10-06 | مژده سلمانی سرشکی | Card-to-card transfer of 305,000 toman from Hassan Shiri's Blu card …6947 to Mozhdeh Salmani Sarshaki (card …6083) on 1405/07/14 18:07; purpose not shown (recipts/photo_12_2026-10-10_11-09-04.jpg). | 305,000 | Supported | recipts/photo_12_2026-10-10_11-09-04.jpg |

**Open items** — OI-08; OI-09; OI-10; OI-11; OI-12; OI-13; OI-14; OI-15; OI-16; OI-17; OI-18

### Unknown (likely 1405 summer school)

No audited rows remain in this project; its rows moved per the decision register (see section 8).

### Yalda 1404

**Receipts by source** — Cash donors: 700,000; Crowd donors: 15,790,000
**Payments by category** — Events: 6,367,000
**Net (cash)** — 10,123,000
**Pending (rows + items)** — 14,369,064
- TX0049 — 10,003,780
- TX0056 — 2,150,000
- TX0058 — 275,000
- TX0060 — 1,664,700
- PI-01 — 275,584 (unreimbursed remainder of TX0050 (decision R-08))

**Transactions**

| ID | Date | Counterparty | Description | Amount (toman) | Status | Evidence |
|---|---|---|---|---:|---|---|
| TX0047 | 1404/10 (month only) | Crowd donors | Yalda donations deposited | 15,790,000 | Supported | message115 |
| TX0048 | 1404/10 (month only) | Cash donors | Yalda cash donations | 700,000 | Supported | message116 |
| TX0049 | 2025-12-22 | Card-to-card payees (unidentified) | Withdrawal of 100,037,800 rial (10,003,780 toman) from Sepah account 3001254062925 on 1404/10/01 10:29, which the treasurer says was used for card-to-card payments of (Yalda) expenses (message120); payees not shown (message115; message118; message120). | 10,003,780 | Pending | message115 |
| TX0050 | 2025-12-29 | سیدبردیا احمدی‌مروست | Reimbursement to Bardia for Yalda prizes and catering | 2,137,000 | Supported | anjoman_accounting_group_export/photos/photo_45@27-06-2026_18-36-09.jpg (message159) |
| TX0051 | 2025-12-29 | سیدبردیا احمدی‌مروست | Re-posted copy of TX0050 receipt | 2,137,000 | Duplicate | anjoman_accounting_group_export/photos/photo_48@27-06-2026_18-43-30.jpg (message165) |
| TX0052 | 2025-12-22 | ساناز بهرامی | Card-to-card 400,000 toman from Bardia's own card (...7195) to Sanaz Bahrami on 1404/10/01 17:50 for Yalda keyrings and a pomegranate earring (message154 '400'); volunteer-paid, reimbursed within TX0050. Purpose matched by amount and by being in Bardia's first photo pair (photo_41/42) which he said were the 400 and 250 receipts (photos/photo_42@27-06-2026_18-36-09.jpg, message154). | 400,000 | Supporting detail | anjoman_accounting_group_export/photos/photo_42@27-06-2026_18-36-09.jpg (message156) |
| TX0053 | 2025-12-22 | پروین حقوردی | Card-to-card 250,000 toman from Bardia's own card (...7195) to Parvin Haghverdi on 1404/10/01 17:55 for Yalda plush keyrings (message154 '250'); volunteer-paid, reimbursed within TX0050 (photos/photo_41@27-06-2026_18-36-09.jpg, message154). | 250,000 | Supporting detail | anjoman_accounting_group_export/photos/photo_41@27-06-2026_18-36-09.jpg (message155) |
| TX0054 | 2025-12-22 | POS Pasargad 00778147 | POS purchase 600,000 toman on Bardia's card (Pasargad terminal 00778147, 1404/10/01 18:41) for small watermelons and pomegranates for Yalda (message154 '600'); volunteer-paid, reimbursed within TX0050. Merchant not shown on slip (photos/photo_43@27-06-2026_18-36-09.jpg, message154). | 600,000 | Supporting detail | anjoman_accounting_group_export/photos/photo_43@27-06-2026_18-36-09.jpg (message157) |
| TX0055 | 2025-12-23 | POS Novin Arian 11304219 | Volunteer purchase: sandwiches 275 + jelly 887 (thousand toman) | 1,162,584 | Supporting detail | anjoman_accounting_group_export/photos/photo_44@27-06-2026_18-36-09.jpg (message158) |
| TX0056 | 2025-12-22 | Canbo Tarasht 1633 | Jelly powder and cherry syrup bought by Hossein | 2,150,000 | Payable | anjoman_accounting_group_export/photos/photo_46@27-06-2026_18-38-52.jpg (message161) |
| TX0057 | 2025-12-22 | Canbo Tarasht 1633 | Duplicate image of TX0056 receipt | 2,150,000 | Duplicate | anjoman_accounting_group_export/photos/photo_47@27-06-2026_18-43-30.jpg (message164) |
| TX0058 | 1404/10 (month only) | حسین | Unreceipted volunteer spend: paper/markers and sweets | 275,000 | Payable | message162 |
| TX0059 | 2025-12-30 | دینا زالی | Thread for Yalda fortune packaging | 180,000 | Supported | photos/photo_39@27-06-2026_18-29-10.jpg (message152) |
| TX0060 | 1404/10 (by event association) | Unknown online grocer | Pomegranates invoice for Yalda | 1,664,700 | Pending | photos/photo_38@27-06-2026_18-27-25.jpg (message151) |
| TX0062 | 2026-05-14 | پرنیان عسگری | Yalda reimbursement installment 1 | 1,550,000 | Supported | anjoman_accounting_group_export/photos/photo_28@17-05-2026_19-45-07.jpg (message126) |
| TX0063 | 2026-05-17 | پرنیان عسگری | Yalda reimbursement installment 2 (total 4,050,000) | 2,500,000 | Supported | anjoman_accounting_group_export/photos/photo_27@17-05-2026_19-45-07.jpg (message125) |
| TX0064 | 2025-12-23 | Canbo Tarasht 1633 | Canbo Tarasht (1633) receipt 1404/10/02 ~18:48: 6 Mazmaz 38g cheese snacks, 107,400 toman; paid by Parnian's card (POS slip 1,074,000 rial, card ...5401, PDF p1); part of the Yalda purchases reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p1, message129). | 107,400 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p1 |
| TX0065 | 2025-12-23 | Canbo Tarasht 1633 | Canbo Tarasht (1633) receipt 1404/10/02 18:47: 10 Mazmaz 38g cheese snacks, 179,000 toman; paid by Parnian (card ...5401); part of the Yalda purchases reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p2, message129). | 179,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p2 |
| TX0066 | 2025-12-23 | Canbo Tarasht 1633 | Canbo Tarasht (1633) receipt 1404/10/02 18:48: 10 Mazmaz 38g cheese snacks, 179,000 toman; paid by Parnian; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p3, message129). | 179,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p3 |
| TX0067 | 2025-12-23 | Canbo Tarasht 1633 | Canbo Tarasht (1633) receipt 1404/10/02 18:46: 10 Mazmaz 38g cheese snacks, 179,000 toman; paid by Parnian; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p4, message129). | 179,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p4 |
| TX0068 | 2025-12-23 | Canbo Tarasht 1633 | Canbo Tarasht (1633) receipt 1404/10/02 18:47: 10 Mazmaz 38g cheese snacks, 179,000 toman; paid by Parnian; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p5, message129). | 179,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p5 |
| TX0069 | 2025-12-23 | Canbo Tarasht 1633 | Canbo Tarasht (1633) receipt 1404/10/02 18:46: 10 Mazmaz 38g cheese snacks, 179,000 toman; a second purchase in the same minute as C4 (separate physical receipt); paid by Parnian; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p6, message129). | 179,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p6 |
| TX0070 | 2025-12-23 | Hyperfamili Tarasht | HyperFamili Tarasht receipt 1404/10/02: 99 Mazmaz 38g cheese snacks, 1,916,640 toman (after 2,613,600-rial discount); bought by Parnian for Yalda; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p7, message129). | 1,916,640 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p7 |
| TX0071 | 2025-12-24 | Ekano | Ekano receipt 1404/10/03 11:36: one Gala milk chocolate tablet item, 1,357,999 rial = 135,799.9 toman, paid with Parnian's card ...5401; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p8, message129). | 135,799.9 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p8 |
| TX0072 | 2025-12-23 | Canbo Tarasht Metro 2224 | Canbo Tarasht Metro (2224) receipt 1404/10/02 18:56: 10 Mazmaz 38g cheese snacks, 179,000 toman; bought by Parnian for Yalda; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p9, message129). | 179,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p9 |
| TX0073 | 2025-12-23 | Canbo Tarasht Metro 2224 | Canbo Tarasht Metro (2224) receipt 1404/10/02 18:56: 7 Mazmaz 38g cheese snacks, 125,300 toman; bought by Parnian; reimbursed via TX0062/63 (CamScanner 13-05-2026 12.43 (1).pdf p10, message129). | 125,300 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p10 |
| TX0074 | 2025-12-24 | RIBAR coffee/fast food | Handwritten RIBAR coffee/fast-food invoice, chocolate cookies, 4,950,000 rial = 495,000 toman, dated 1404/10/03 (or /13); included in Parnian's PDF and matches treasurer's 'Yalda cookies' remark (message128); no payment proof (CamScanner 13-05-2026 12.43 (1).pdf p11, message128). | 495,000 | Supporting detail | anjoman_accounting_group_export/files/CamScanner 13-05-2026 12.43 (1).pdf p11 |

**Excluded rows**

- TX0051 — Duplicate (TX0050)
- TX0052 — Supporting detail (TX0050)
- TX0053 — Supporting detail (TX0050)
- TX0054 — Supporting detail (TX0050)
- TX0055 — Supporting detail (TX0050)
- TX0057 — Duplicate (TX0056)
- TX0064 — Supporting detail (TX0062;TX0063)
- TX0065 — Supporting detail (TX0062;TX0063)
- TX0066 — Supporting detail (TX0062;TX0063)
- TX0067 — Supporting detail (TX0062;TX0063)
- TX0068 — Supporting detail (TX0062;TX0063)
- TX0069 — Supporting detail (TX0062;TX0063)
- TX0070 — Supporting detail (TX0062;TX0063)
- TX0071 — Supporting detail (TX0062;TX0063)
- TX0072 — Supporting detail (TX0062;TX0063)
- TX0073 — Supporting detail (TX0062;TX0063)
- TX0074 — Supporting detail (TX0062;TX0063)

**Open items** — OI-02

## Cash custody

| Account | Holder | Type | Cash in | Cash out | Internal transfers |
|---|---|---|---:|---:|---|
| **cash** |  |  | **700,000** | **300,000** |  |
| CASH | not evidenced | cash | 700,000 | 300,000 |  |
| **event custodian** |  |  | **4,920,000** | **3,155,000** |  |
| AMIN-EVENT | محمدامین عزیزی (Mohammad-Amin Azizi) | event custodian | 4,920,000 | 3,155,000 |  |
| **not evidenced** |  |  | **38,790,000** | **26,954,900** |  |
| SEPAH-2925 | not evidenced | not evidenced | 15,790,000 | 0 |  |
| SHAHR-2167 | not evidenced | not evidenced | 0 | 11,217,000 |  |
| UNKNOWN | not evidenced | not evidenced | 23,000,000 | 15,737,900 |  |
| Unknown funding source | not evidenced | not evidenced | 0 | 0 |  |
| **personal** |  |  | **68,142,000** | **68,983,295** |  |
| BLU-CUSTODIAN | محمدحسن شیری (Mohammad-Hassan Shiri) | personal | 0 | 33,937,250 |  |
| SHAHR-8966 | محمد حسن شیری (Mohammad-Hassan Shiri) | personal | 68,142,000 | 35,046,045 | TX0018 |
| **volunteer** |  |  | **0** | **0** |  |
| VOLUNTEER | سیدبردیا احمدیمروست (card 7195); حسین (Hossein); پرنیان (Parnian, card 5401) | volunteer | 0 | 0 |  |

Holder and type as evidenced; 'not evidenced' means no document identifies them.

## Balance-chain gaps (disclosed, not booked)

Evidenced Bank Shahr balance snapshots vs recorded ledger flows; figures approximate, in toman.

Decision S-01: bank balances implied by the evidenced snapshots do not reconcile with recorded flows. These movements are disclosed, not booked; open item OI-07 asks for the Bank Shahr statement.

| ID | Description | Amount (toman) | Evidence |
|---|---|---:|---|
| BC-1 | 1405/05/21-1405/05/22 (debits): unrecorded debits between TX0075 and TX0076 snapshots | 3,163,000 | recipts/photo_3_2026-10-10_14-07-27.jpg; recipts/photo_2_2026-10-10_14-07-27.jpg |
| BC-2 | 1404/12 - 1405/05 (credits): credits exceeding recorded inflows | 35,200,000 | recipts/photo_6_2026-10-10_14-07-27.jpg; recipts/photo_3_2026-10-10_14-07-27.jpg |
| BC-3 | 1404/09 - 1404/12 (debits): debits exceeding recorded outflows; upper bound 19,800,000 | 12,800,000 | recipts/photo_4_2026-10-10_14-07-27.jpg; recipts/photo_6_2026-10-10_14-07-27.jpg |
| BC-4 | - (inflow anomalies): TX0007 and TX0024 amounts exceed the surrounding balance movement | — | message28; message32; message33; message34; photos/photo_16@15-10-2025_14-18-26.jpg (message64); photos/photo_14@15-10-2025_14-18-25.jpg (message62) |

## Open items

| ID | Description | Amount (toman) | What settles it |
|---|---|---:|---|
| OI-01 (TX0001) | The posted report shows 33,643,000 for this receipt; the ledger has 33,642,000 (1,000 difference). | 1,000 | the original report/workbook page for TX0001 |
| OI-02 (TX0062; TX0063) | 195,860.1 toman of the volunteer-reported purchases (TX0064-74) is not covered by the TX0062/63 reimbursement of 4,050,000. | 195,860.1 | the missing receipt(s) or the volunteer's confirmation of the total |
| OI-03 (TX0093; TX0094) | Intro Event 1405 evidence implies 4,235,000 beyond the recorded net of 23,000,000; the gap is unexplained. | 4,235,000 | bank statement or receipts for the Intro Event 1405 period |
| OI-04 (TX0013) | No evidence outside the original ledger; the row is kept Supported on the original ledger's authority. | — | a source receipt or message for TX0013 |
| OI-05 (TX0045) | No evidence outside the original ledger; the row is kept Supported on the original ledger's authority. | — | a source receipt or message for TX0045 |
| OI-06 (TX0095) | No evidence outside the original ledger; the row is kept Supported on the original ledger's authority. | — | a source receipt or message for TX0095 |
| OI-07 | Implied bank movements are not in the ledger: ~3,163,000 debits around 1405/05/21-22; ~35.2M credits between 1404/12 and 1405/05; ~12.8-19.8M debits between 1404/09 and 1404/12; inflow anomalies at TX0007 and TX0024. | — | the Bank Shahr statement covering 1404/05-1405/06 |
| OI-08 (TX0043) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-09 (TX0061) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-10 (TX0075) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-11 (TX0076) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-12 (TX0077) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-13 (TX0078) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-14 (TX0079) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-15 (TX0081) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-16 (TX0090) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-17 (TX0091) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |
| OI-18 (TX0092) | Purpose unknown - the row could not be assigned to an event/program from evidence. | — | owner identifies the purpose; then reassign project and category |

## Decisions and audit log

38 decisions taken on 2026-10-18; full text in Decisions_Register.json.

- **S-01** — Disclose, don't book
- **B-01** — Cash + pending column
- **A-01** — Decisions first
- **D-01** (TX0022, TX0025, TX0051, TX0057) — Confirm all 4
- **D-02** (TX0010, TX0009) — Duplicate of TX0009
- **D-03** (TX0052, TX0053, TX0054, TX0055, TX0050) — Supporting detail
- **D-04** (TX0064, TX0065, TX0066, TX0067, TX0068, TX0069, TX0070, TX0071, TX0072, TX0073, TX0074, TX0062, TX0063) — Supporting detail
- **D-05** (TX0069, TX0067) — Distinct receipts
- **D-06** (TX0042, TX0040, TX0041) — Separate, Supported
- **R-01** (TX0036) — Payment, Supported
- **R-02** (TX0031) — 230,000
- **R-03** (TX0018) — Rial → 1,765,000, Supported
- **R-04** (TX0001) — Keep 33,642,000
- **R-05** (TX0047) — Toman, keep
- **R-06** (TX0049) — Fill amount, keep pending
- **R-07** (TX0056, TX0058) — Pending payable
- **R-08** (TX0050, TX0055) — Pending payable
- **R-09** (TX0062, TX0063) — Keep paid, open item
- **R-10** (TX0060) — Keep Invoice only
- **R-11** (TX0082) — SS1405, pending payable
- **R-12** (TX0093, TX0094) — Keep 23M net, open item
- **R-13** (TX0096) — Pending, date ≤1405/04
- **R-14** (TX0013) — Keep Supported, flag basis
- **R-15** (TX0045) — Keep Supported, flag basis
- **R-16** (TX0095) — Keep Supported, flag basis
- **U-01** (TX0001) — 2025-07-24, period 1404/05
- **U-02** (TX0014, TX0016, TX0017) — 2025-09-06
- **U-03** (TX0015) — 2025-09-04
- **U-04** (TX0044) — ≤ 2025-11-19, period 1404/08
- **U-05** (TX0036) — 2025-10-29
- **U-06** (TX0074) — 1404/10/03
- **U-07** (TX0060) — Period 1404/10, undated
- **U-08** (TX0013, TX0045, TX0047, TX0048, TX0058, TX0093, TX0095, TX0010, TX0025) — Month only, flagged
- **P-01** (TX0080) — SS1405 / Advertising
- **P-02** (TX0089) — Intro Event 1405 / Hospitality
- **P-03** (TX0034) — Split into two rows
- **P-04** (TX0020) — Keep Professors assembly, note shared
- **P-05** (TX0043, TX0061, TX0075, TX0076, TX0077, TX0078, TX0079, TX0081, TX0090, TX0091, TX0092) — Keep Unassigned + open items

Audit log: 209 field changes (2 created rows/items).

- **B-01** — 6
- **D-02** — 1
- **D-03** — 8
- **D-04** — 22
- **D-05** — 1
- **D-06** — 1
- **M-001** — 1
- **M-002** — 1
- **M-003** — 1
- **M-004** — 1
- **M-005** — 1
- **M-006** — 1
- **M-007** — 1
- **M-008** — 1
- **M-009** — 1
- **M-010** — 1
- **M-011** — 1
- **M-012** — 1
- **M-013** — 1
- **M-014** — 1
- **M-015** — 1
- **M-016** — 1
- **M-017** — 1
- **M-018** — 1
- **M-019** — 1
- **M-020** — 1
- **M-021** — 1
- **M-022** — 1
- **M-023** — 1
- **M-024** — 1
- **M-025** — 1
- **M-026** — 1
- **M-027** — 1
- **M-028** — 1
- **M-029** — 1
- **M-030** — 1
- **M-031** — 1
- **M-032** — 1
- **M-033** — 1
- **M-034** — 1
- **M-035** — 1
- **M-036** — 1
- **M-037** — 1
- **M-038** — 1
- **M-039** — 1
- **M-040** — 1
- **M-041** — 1
- **M-042** — 1
- **M-043** — 1
- **M-044** — 1
- **M-045** — 1
- **M-046** — 1
- **M-047** — 1
- **M-048** — 1
- **M-049** — 1
- **M-050** — 1
- **M-051** — 1
- **M-052** — 1
- **M-053** — 1
- **M-054** — 1
- **M-055** — 1
- **M-056** — 1
- **M-057** — 1
- **M-058** — 1
- **M-059** — 1
- **M-060** — 1
- **M-061** — 1
- **M-062** — 1
- **M-063** — 1
- **M-064** — 1
- **M-065** — 1
- **M-066** — 1
- **M-067** — 1
- **M-068** — 1
- **M-069** — 1
- **M-070** — 1
- **M-071** — 1
- **M-072** — 1
- **M-073** — 1
- **M-074** — 1
- **M-075** — 1
- **M-076** — 1
- **M-077** — 1
- **M-078** — 1
- **M-079** — 1
- **M-080** — 1
- **M-081** — 1
- **M-082** — 1
- **M-083** — 1
- **M-084** — 1
- **M-085** — 1
- **M-086** — 1
- **M-087** — 1
- **M-088** — 1
- **M-089** — 1
- **P-01** — 2
- **P-02** — 1
- **P-03** — 3
- **P-05** — 11
- **R-01** — 2
- **R-02** — 2
- **R-03** — 2
- **R-04** — 1
- **R-06** — 4
- **R-07** — 4
- **R-08** — 1
- **R-09** — 2
- **R-11** — 1
- **R-12** — 2
- **R-13** — 2
- **R-14** — 2
- **R-15** — 2
- **R-16** — 2
- **U-01** — 3
- **U-02** — 9
- **U-03** — 2
- **U-04** — 4
- **U-05** — 3
- **U-06** — 3
- **U-07** — 2
- **U-08** — 9

Mechanical fixes (89) - money-neutral; reviewed by the owner in one pass.

- **M-001** — TX0001 description_en: Dossier A: assessment 'vague'; names the three courses, student counts, totals and the Tir collection window with the …8966 consolidation request.
- **M-002** — TX0001 description_fa: Dossier A: assessment 'vague'; names the three courses, student counts, totals and the Tir collection window with the …8966 consolidation request.
- **M-003** — TX0002 notes: Dossier A discrepancy: old note implied an anomaly (rounding gives 2,900 but 3,000 paid); all three instructor fees were rounded up, so 3,000 is consistent.
- **M-004** — TX0013 description_en: Dossier A: assessment 'vague'; states purpose (room keys, حسن شیری) and that the amount rests on the workbook only.
- **M-005** — TX0013 description_fa: Dossier A: assessment 'vague'; states purpose (room keys, حسن شیری) and that the amount rests on the workbook only.
- **M-006** — TX0016 description_en: Dossier A: assessment 'vague'; states event, handler and workbook-only basis.
- **M-007** — TX0016 description_fa: Dossier A: assessment 'vague'; states event, handler and workbook-only basis.
- **M-008** — TX0017 description_en: Dossier A: assessment 'vague'; states payee and that the amount is a workbook balancing figure only.
- **M-009** — TX0017 description_fa: Dossier A: assessment 'vague'; states payee and that the amount is a workbook balancing figure only.
- **M-010** — TX0020 description_en: Decision P-04 (Dossier A): keep under Professors assembly and append the shared-use note (Quanta circles share the print run; message61).
- **M-011** — TX0020 description_fa: Decision P-04 (Dossier A): keep under Professors assembly and append the shared-use note (Quanta circles share the print run; message61).
- **M-012** — TX0033 notes: Dossier A discrepancy: old note linked photo_34 to TX0033 'uncertainly'; the dossier assigns photo_34 to TX0035 (message107 line 3). TX0033's message_ids carries no photo token, so nothing is removed there.
- **M-013** — TX0034 description_en: Decision P-03 (Dossier A): TX0034 (1,500,000) split into 1,000,000 prizes (this row) + 500,000 association flash drive (TX0034-B); replaces the old combined description.
- **M-014** — TX0034 description_fa: Decision P-03 (Dossier A): TX0034 (1,500,000) split into 1,000,000 prizes (this row) + 500,000 association flash drive (TX0034-B); replaces the old combined description.
- **M-015** — TX0034-B description_en: Decision P-03 (Dossier A): new row TX0034-B (500,000, Association operations / Equipment) carries the flash-drive half of the old combined TX0034.
- **M-016** — TX0034-B description_fa: Decision P-03 (Dossier A): new row TX0034-B (500,000, Association operations / Equipment) carries the flash-drive half of the old combined TX0034.
- **M-017** — TX0035 message_ids: Dossier A: photo_34 (photos/photo_34@27-06-2026_18-26-03.jpg, caption message147) is TX0035's probable invoice (message107 line 3, 'فرفره…'); its caption message is added here. TX0033's message_ids never carried a photo token, so there is nothing to remove on that side (its stale note is corrected separately).
- **M-018** — TX0036 description_en: Dossier B1: assessment 'vague'; states what the cash was for and that recipient and cash source are not shown.
- **M-019** — TX0036 description_fa: Dossier B1: assessment 'vague'; states what the cash was for and that recipient and cash source are not shown.
- **M-020** — TX0038 notes: Dossier B1 discrepancy: ledger note left the invoice number ambiguous ('2935 or 29350'); photo_29 clearly prints 29350.
- **M-021** — TX0043 description_en: Dossier B1: assessment 'vague'; states terminal, date/time, amount and tracking; purpose unknown (card masked to last four digits).
- **M-022** — TX0043 description_fa: Dossier B1: assessment 'vague'; states terminal, date/time, amount and tracking; purpose unknown (card masked to last four digits).
- **M-023** — TX0049 description_en: Dossier B1: assessment 'vague'; states the Sepah withdrawal, treasurer's stated use, and that no payee is shown.
- **M-024** — TX0049 description_fa: Dossier B1: assessment 'vague'; states the Sepah withdrawal, treasurer's stated use, and that no payee is shown.
- **M-025** — TX0052 description_en: Dossier B2: assessment 'vague'; states payer, payee, purpose and the TX0050 reimbursement.
- **M-026** — TX0052 description_fa: Dossier B2: assessment 'vague'; states payer, payee, purpose and the TX0050 reimbursement.
- **M-027** — TX0053 description_en: Dossier B2: assessment 'vague'; states payer, payee, purpose and the TX0050 reimbursement.
- **M-028** — TX0053 description_fa: Dossier B2: assessment 'vague'; states payer, payee, purpose and the TX0050 reimbursement.
- **M-029** — TX0054 description_en: Dossier B2: assessment 'vague'; states terminal, time, purpose and reimbursement; merchant not shown.
- **M-030** — TX0054 description_fa: Dossier B2: assessment 'vague'; states terminal, time, purpose and reimbursement; merchant not shown.
- **M-031** — TX0064 description_en: Dossier B2: assessment 'vague'; states shop, items, amount and payer (POS slip on PDF p1; tracking number on the slip is not legible).
- **M-032** — TX0064 description_fa: Dossier B2: assessment 'vague'; states shop, items, amount and payer (POS slip on PDF p1; tracking number on the slip is not legible).
- **M-033** — TX0065 description_en: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-034** — TX0065 description_fa: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-035** — TX0066 description_en: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-036** — TX0066 description_fa: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-037** — TX0067 description_en: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-038** — TX0067 description_fa: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-039** — TX0068 description_en: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-040** — TX0068 description_fa: Dossier B2: assessment 'vague'; states shop, items, time and payer.
- **M-041** — TX0069 description_en: Dossier B2: assessment 'vague'; states it is a distinct second receipt in the same minute as TX0067 (dossier: evidence indicates a distinct receipt, not a rescan).
- **M-042** — TX0069 description_fa: Dossier B2: assessment 'vague'; states it is a distinct second receipt in the same minute as TX0067 (dossier: evidence indicates a distinct receipt, not a rescan).
- **M-043** — TX0070 description_en: Dossier B2: assessment 'vague'; states shop, items and amount; time not legible and payer inferred from Parnian's PDF only.
- **M-044** — TX0070 description_fa: Dossier B2: assessment 'vague'; states shop, items and amount; time not legible and payer inferred from Parnian's PDF only.
- **M-045** — TX0071 description_en: Dossier B2: assessment 'vague'; states shop, item, exact amount and payer.
- **M-046** — TX0071 description_fa: Dossier B2: assessment 'vague'; states shop, item, exact amount and payer.
- **M-047** — TX0072 description_en: Dossier B2: assessment 'vague'; states shop branch, time and items (printed time 18:56, same minute as TX0073 but different amount).
- **M-048** — TX0072 description_fa: Dossier B2: assessment 'vague'; states shop branch, time and items (printed time 18:56, same minute as TX0073 but different amount).
- **M-049** — TX0073 description_en: Dossier B2: assessment 'vague'; states shop branch, time and items.
- **M-050** — TX0073 description_fa: Dossier B2: assessment 'vague'; states shop branch, time and items.
- **M-051** — TX0074 description_en: Dossier B2: assessment 'vague'; states vendor, item and amount; notes there is no payment proof.
- **M-052** — TX0074 description_fa: Dossier B2: assessment 'vague'; states vendor, item and amount; notes there is no payment proof.
- **M-053** — TX0045 description_en: Dossier C: assessment 'vague'; names donor and purpose; flags the workbook-only basis.
- **M-054** — TX0045 description_fa: Dossier C: assessment 'vague'; names donor and purpose; flags the workbook-only basis.
- **M-055** — TX0061 description_en: Dossier C: assessment 'vague'; states transfer, amount and date; destination cardholder and purpose not shown (destination card masked to last four digits).
- **M-056** — TX0061 description_fa: Dossier C: assessment 'vague'; states transfer, amount and date; destination cardholder and purpose not shown (destination card masked to last four digits).
- **M-057** — TX0075 description_en: Dossier C: assessment 'vague'; states terminal, card, deposit and time; merchant and purpose not shown.
- **M-058** — TX0075 description_fa: Dossier C: assessment 'vague'; states terminal, card, deposit and time; merchant and purpose not shown.
- **M-059** — TX0075 tracking_id: Receipt prints tracking (باکدرهگيري) 001873; ledger had 187300 — digit order, value carried from an earlier OCR (Dossier C discrepancy).
- **M-060** — TX0076 description_en: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-061** — TX0076 description_fa: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-062** — TX0077 description_en: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-063** — TX0077 description_fa: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-064** — TX0078 description_en: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-065** — TX0078 description_fa: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-066** — TX0079 description_en: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-067** — TX0079 description_fa: Dossier C: assessment 'vague'; states terminal, deposit and time; merchant and purpose not shown.
- **M-068** — TX0080 description_en: Dossier C: assessment 'vague'; states payee and the very-likely ad purpose via the 1404 precedent and the forwarded ad post.
- **M-069** — TX0080 description_fa: Dossier C: assessment 'vague'; states payee and the very-likely ad purpose via the 1404 precedent and the forwarded ad post.
- **M-070** — TX0081 description_en: Dossier C: assessment 'vague'; states payer, payee and time; purpose not shown (destination card masked to last four digits).
- **M-071** — TX0081 description_fa: Dossier C: assessment 'vague'; states payer, payee and time; purpose not shown (destination card masked to last four digits).
- **M-072** — TX0083 description_en: Dossier C: assessment 'vague'; names instructor (Zahra Saleh Koushali), course (Python OOP, 2 sessions), amount and channel.
- **M-073** — TX0083 description_fa: Dossier C: assessment 'vague'; names instructor (Zahra Saleh Koushali), course (Python OOP, 2 sessions), amount and channel.
- **M-074** — TX0084 description_en: Dossier C: assessment 'vague'; names instructor (Reza Farhadi), course (Manim content production, 3 sessions), amount and channel.
- **M-075** — TX0084 description_fa: Dossier C: assessment 'vague'; names instructor (Reza Farhadi), course (Manim content production, 3 sessions), amount and channel.
- **M-076** — TX0087 description_en: Dossier C: assessment 'vague'; names instructor (Ilia Asgharian Dehkordi), course (introductory Python, 6 sessions), amount and channel.
- **M-077** — TX0087 description_fa: Dossier C: assessment 'vague'; names instructor (Ilia Asgharian Dehkordi), course (introductory Python, 6 sessions), amount and channel.
- **M-078** — TX0089 description_en: Dossier C: assessment 'vague'; states vendor, items, invoice number/date and that settlement rests on user attestation.
- **M-079** — TX0089 description_fa: Dossier C: assessment 'vague'; states vendor, items, invoice number/date and that settlement rests on user attestation.
- **M-080** — TX0090 description_en: Dossier C: assessment 'vague'; states payer, payee, time and the Intro Event day; purpose not shown (destination card masked to last four digits).
- **M-081** — TX0090 description_fa: Dossier C: assessment 'vague'; states payer, payee, time and the Intro Event day; purpose not shown (destination card masked to last four digits).
- **M-082** — TX0091 description_en: Dossier C: assessment 'vague'; states merchant code, amount and the Intro Event day; items not shown.
- **M-083** — TX0091 description_fa: Dossier C: assessment 'vague'; states merchant code, amount and the Intro Event day; items not shown.
- **M-084** — TX0092 description_en: Dossier C: assessment 'vague'; states payer, payee and time; purpose not shown (destination card masked to last four digits).
- **M-085** — TX0092 description_fa: Dossier C: assessment 'vague'; states payer, payee and time; purpose not shown (destination card masked to last four digits).
- **M-086** — TX0093 description_en: Dossier C: assessment 'vague'; states event and treasurer-ledger basis; no payout statement or deposit in evidence.
- **M-087** — TX0093 description_fa: Dossier C: assessment 'vague'; states event and treasurer-ledger basis; no payout statement or deposit in evidence.
- **M-088** — TX0095 description_en: Dossier C: assessment 'vague'; states the after-party and its workbook-only amount; payee and receipt not shown.
- **M-089** — TX0095 description_fa: Dossier C: assessment 'vague'; states the after-party and its workbook-only amount; payee and receipt not shown.

## Method

Source: reports/2026-10-10/Transactions.csv (96 rows, read-only). Evidence: the accounting Telegram group export (message ids), the receipts folder, invoices and workbooks. Date bases: printed = the date on the document; event-day proxy = the event day; on or before = an upper bound; month only = month precision, flagged; Telegram post time = the post's server timestamp; reports posted = the day the financial report was posted; by event association = period inferred from the event. Amounts are toman (1 toman = 10 rial); totals compare within 0.5 toman. Nothing under reports/2026-10-10 or reports/2026-10-14 was modified.
