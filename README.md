<div dir="rtl">

# آرشیو و تحلیل انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف

این مخزن بایگانی کاری انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف است و پنج بخش را کنار هم نگه می‌دارد: اسناد و دفترهای حسابداری انجمن، بایگانی پنج گفت‌وگوی تلگرامی، زنجیره‌ای پایتونی که این داده‌ها را تحلیل و حسابرسی می‌کند، گزارش‌های منتشرشده در نسل‌های تاریخ‌دار، و مجموعه اسناد حاکمیتی انجمن (اساسنامه، شیوه‌نامه‌ها و منشور مجمع). این راهنما برای شورای مرکزی تازه‌منتخب و همکارانی نوشته شده است که کار را ادامه می‌دهند: هر پوشه چه دارد، هر گزارش از کجا آمده است و چگونه دوباره ساخته می‌شود.

این مخزن روی گیت‌هاب **عمومی** است و هر چیزی را که در آن ثبت شود همه می‌توانند ببینند. قاعده‌های حریم خصوصی در بخش [اصول کار](#اصول-کار) آمده است.

## فهرست مطالب

- [نقشه مخزن](#نقشه-مخزن)
- [محصولات منتشرشده](#محصولات-منتشرشده)
- [زنجیره داده‌ها](#زنجیره-داده‌ها)
- [داده‌های خام](#داده‌های-خام)
- [ابزارها](#ابزارها)
- [بازسازی و آزمون](#بازسازی-و-آزمون)
- [اصول کار](#اصول-کار)
- [جدول تطبیق مسیرها](#جدول-تطبیق-مسیرها)
- [اسناد طراحی](#اسناد-طراحی)
- [وضعیت و کارهای باز](#وضعیت-و-کارهای-باز)

## نقشه مخزن

پوشه‌ها بر پایه نقش چیده شده‌اند: ورودی‌های خام در <span dir="ltr">`data/`</span>، گزارش‌های منتشرشده در <span dir="ltr">`reports/`</span>، اسناد در <span dir="ltr">`docs/`</span>، و ابزارها و خروجی‌های میانی در <span dir="ltr">`analysis_tools/`</span> و <span dir="ltr">`analysis/`</span>. فایل <span dir="ltr">`analysis_tools/common.py`</span> محل ورودی‌های خام، دفتر کل و پوشه‌های گزارش را تعریف می‌کند (ثابت‌های <span dir="ltr">`DATA`</span>، <span dir="ltr">`REPORTS`</span>، <span dir="ltr">`TELEGRAM`</span>، <span dir="ltr">`SOURCES`</span>، <span dir="ltr">`LEDGER_CSV`</span> و <span dir="ltr">`MEDIA_DOCX`</span>)؛ سایر ماژول‌ها مسیرهای <span dir="ltr">`analysis/`</span> و خروجی گزارش خود را جدا تعریف می‌کنند.

<div dir="ltr">

```text
anjoman-accounting/
├── README.md                       همین راهنما
├── data/                           داده‌های خام؛ ابزارها فقط آن را می‌خوانند
│   ├── telegram/                   پنج خروجی تلگرام دسکتاپ
│   │   ├── channel/                کانال انجمن
│   │   ├── private_group/          گروه خصوصی انجمن
│   │   ├── public_group/           گروه عمومی انجمن
│   │   ├── summerschool/           کانال مدرسه تابستانه فیزیک
│   │   └── accounting_group/       گروه حسابداری؛ شواهد پیامی حسابرسی
│   ├── accounting/                 ورودی‌های حسابداری
│   │   ├── workbooks/              دو کارپوشه اکسل دفترداری
│   │   ├── receipts/               عکس رسیدها
│   │   └── documents/              فاکتور دامنه و گزارش رویداد معرفی رشته
│   └── documents/                  گزارش عملکرد رسانه‌ای انجمن
├── reports/                        گزارش‌های منتشرشده؛ هر پوشه یک نسل منجمد
│   ├── 2026-10-10/                 گزارش مالی تطبیق‌شده
│   ├── 2026-10-14/                 گزارش‌های تحلیلی مالی ماهانه و عملکرد
│   └── 2026-10-18/                 گزارش حسابرسی‌شده دفتر کل
├── docs/
│   ├── governance/                 چهار سند حاکمیتی، راهنما و خروجی‌های ساخته‌شده
│   └── superpowers/                اسناد طراحی و برنامه‌های اجرای هر مرحله کار
├── analysis/                       خروجی‌های میانی تحلیل: پیکره پیام‌ها، رده‌بندی، رشته رویدادها
├── analysis_tools/                 بسته پایتون: تجزیه، تحلیل، حسابرسی و ساخت گزارش و سند
│   ├── audit/                      زنجیره حسابرسی دفتر کل و ورودی‌های ثبت‌شده آن
│   ├── i18n/                       کاتالوگ متن انگلیسی و فارسی و واژه‌نامه
│   ├── tests/                      آزمون‌ها و دروازه‌های خودکار
│   └── accounting_2026_10_10/      زنجیره بایگانی‌شده‌ای که نخستین گزارش مالی را ساخت
└── sources/governance/             منابع اسناد حاکمیتی؛ فقط محلی و بیرون از گیت
```

</div>

پوشه <span dir="ltr">`sources/governance/`</span> در <span dir="ltr">`.gitignore`</span> آمده است و فقط روی رایانه کسی وجود دارد که اسناد منبع را در اختیار دارد؛ در نسخه‌ای که از گیت‌هاب کلون می‌شود این پوشه نیست.

## محصولات منتشرشده

هر نسل گزارش پس از انتشار منجمد می‌شود، یعنی دیگر ویرایش نمی‌شود؛ هر اصلاح یا کار تازه در پوشه‌ای با تاریخ تازه می‌آید.

| تاریخ | محصول | محل | زبان | وضعیت |
|---|---|---|---|---|
| ۲۰۲۶-۱۰-۱۰ | گزارش مالی تطبیق‌شده: دفتر کل ۹۶ تراکنشی، کارپوشه حرفه‌ای، بسته شواهد و فایل‌های اعتبارسنجی | پوشه <span dir="ltr">[`reports/2026-10-10/`](reports/2026-10-10/)</span> | انگلیسی و فارسی | منجمد |
| ۲۰۲۶-۱۰-۱۴ | گزارش‌های تحلیلی مالی ماهانه و عملکرد، بر پایه دفتر کل و خروجی‌های تلگرام | پوشه <span dir="ltr">[`reports/2026-10-14/`](reports/2026-10-14/)</span> | انگلیسی و فارسی | منجمد |
| ۲۰۲۶-۱۰-۱۸ | گزارش حسابرسی‌شده دفتر کل: ۹۷ ردیف حسابرسی‌شده، ترازنامه هر پروژه، پل‌های تطبیق و ۱۸ مورد باز | پوشه <span dir="ltr">[`reports/2026-10-18/`](reports/2026-10-18/)</span> | انگلیسی و فارسی | منجمد |
| ۲۰۲۶-۱۰-۲۱ | مجموعه اسناد حاکمیتی: اساسنامه، شیوه‌نامه داخلی شورا، منشور مجمع و شیوه‌نامه اجرایی مجمع | پوشه <span dir="ltr">[`docs/governance/`](docs/governance/)</span> | فارسی | پیش‌نویس نسخه ۱٫۰، در انتظار بررسی و تصویب |

نسخه فارسی گزارش‌های ‎۲۰۲۶-۱۰-۱۴ در ‎۲۰۲۶-۱۰-۱۸ به همان پوشه افزوده شد. گزارش ‎۲۰۲۶-۱۰-۱۰ نسخه فارسی‌اش را در زیرپوشه <span dir="ltr">`reports/2026-10-10/fa/`</span> دارد.

### پیوندهای مستقیم

- **گزارش مالی تطبیق‌شده:** [PDF انگلیسی](reports/2026-10-10/Anjoman_Financial_Report.pdf) · [PDF فارسی](reports/2026-10-10/fa/Anjoman_Financial_Report_FA.pdf) · [کارپوشه انگلیسی](reports/2026-10-10/Anjoman_Accounting_Professional.xlsx) · [کارپوشه فارسی](reports/2026-10-10/fa/Anjoman_Accounting_Professional_FA.xlsx)
- **گزارش مالی ماهانه:** [PDF انگلیسی](reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly.pdf) · [PDF فارسی](reports/2026-10-14/financial_monthly/Anjoman_Financial_Report_Monthly_FA.pdf)
- **گزارش عملکرد و فعالیت:** [PDF انگلیسی](reports/2026-10-14/performance/Anjoman_Performance_Activity_Report.pdf) · [PDF فارسی](reports/2026-10-14/performance/Anjoman_Performance_Activity_Report_FA.pdf)
- **گزارش حسابرسی‌شده دفتر کل:** [PDF انگلیسی](reports/2026-10-18/Anjoman_Ledger_Audit_Report.pdf) · [PDF فارسی](reports/2026-10-18/Anjoman_Ledger_Audit_Report_FA.pdf) · [فهرست موارد باز](reports/2026-10-18/Open_Items.csv)
- **ارقام اصلی گزارش حسابرسی‌شده:** دریافت‌ها ۱۱۲٬۵۵۲٬۰۰۰، پرداخت‌ها ۹۹٬۳۹۳٬۱۹۵، خالص ۱۳٬۱۵۸٬۸۰۵ و در انتظار ۲۱٬۶۲۶٬۰۶۴ تومان.
- **اساسنامه انجمن:** [DOCX](docs/governance/build/asasname.docx) · [PDF](docs/governance/build/asasname.pdf) · [متن اصلی](docs/governance/asasname.md)
- **شیوه‌نامه داخلی شورای مرکزی:** [DOCX](docs/governance/build/shora-shivename.docx) · [PDF](docs/governance/build/shora-shivename.pdf) · [متن اصلی](docs/governance/shora-shivename.md)
- **منشور مجمع:** [DOCX](docs/governance/build/majma-manshoor.docx) · [PDF](docs/governance/build/majma-manshoor.pdf) · [متن اصلی](docs/governance/majma-manshoor.md)
- **شیوه‌نامه اجرایی مجمع:** [DOCX](docs/governance/build/majma-shivename.docx) · [PDF](docs/governance/build/majma-shivename.pdf) · [متن اصلی](docs/governance/majma-shivename.md)
- **راهنمای اسناد حاکمیتی** (ترتیب خواندن، شیوه اصلاح هر سند و پرسش‌های باز): <span dir="ltr">[`docs/governance/README.md`](docs/governance/README.md)</span>

نسخه DOCX اسناد حاکمیتی ویرایش‌پذیر است و نسخه PDF برای چاپ؛ متن اصلی هر سند همان فایل Markdown است و خروجی‌ها از روی آن ساخته می‌شوند.

### شناسه‌ها و شواهد

شناسه تراکنش (<span dir="ltr">`TX0001`</span> تا <span dir="ltr">`TX0096`</span>، به‌علاوه <span dir="ltr">`TX0034-B`</span> که حسابرسی ساخته است) کلید پیوند همه فایل‌های مالی است:

| فایل | کلید | محتوا |
|---|---|---|
| فایل <span dir="ltr">`reports/2026-10-10/Transactions.csv`</span> | هر ردیف یک تراکنش | دفتر کل مبدأ با ۹۶ ردیف (فقط خواندنی) |
| فایل <span dir="ltr">`analysis_tools/audit/data/decisions.json`</span> | فهرست <span dir="ltr">`rows`</span> | ۳۸ تصمیم ثبت‌شده که هر کدام به شواهدش ارجاع می‌دهد |
| فایل <span dir="ltr">`analysis_tools/audit/data/mechanical.json`</span> | ستون <span dir="ltr">`tx`</span> | ۸۹ اصلاح مکانیکی که مبلغی را تغییر نمی‌دهند |
| فایل <span dir="ltr">`analysis_tools/audit/data/evidence_index.json`</span> | بخش <span dir="ltr">`rows`</span> | ارجاع‌های شاهد هر تراکنش و بلوک افشای <span dir="ltr">`balance_chain`</span> |
| فایل <span dir="ltr">`analysis_tools/audit/data/accounts.json`</span> | کد حساب نقد | دارنده و نوع هر حساب، چنان‌که شواهد نشان می‌دهد |
| فایل <span dir="ltr">`reports/2026-10-18/Audit_Log.csv`</span> | ستون‌های <span dir="ltr">`tx`</span> و <span dir="ltr">`source_id`</span> | ۲۰۹ ثبت تغییر؛ هر تغییر به شناسه یک تصمیم یا اصلاح ارجاع می‌دهد |
| فایل <span dir="ltr">`reports/2026-10-18/Transactions_Audited.csv`</span> | هر ردیف یک تراکنش | ۹۷ ردیف حسابرسی‌شده با یادداشت‌های حسابرسی |

ارجاع‌های شاهد به سه پیکره اشاره می‌کنند: پیام‌های گروه حسابداری (مانند <span dir="ltr">`message115`</span>) در <span dir="ltr">`data/telegram/accounting_group/`</span>، عکس رسیدها در <span dir="ltr">`data/accounting/receipts/`</span>، و فاکتور و کارپوشه‌ها در <span dir="ltr">`data/accounting/`</span>. هر ارجاع زمان و توضیحی از آنچه شاهد نشان می‌دهد دارد. ارجاع‌ها مسیرهای پیش از بازآرایی را به کار می‌برند؛ معادل امروزی آن‌ها در [جدول تطبیق مسیرها](#جدول-تطبیق-مسیرها) آمده است.

انواع شناسه‌ها: تصمیم‌ها (<span dir="ltr">`D-xx`</span>، <span dir="ltr">`R-xx`</span>، <span dir="ltr">`U-xx`</span>، <span dir="ltr">`P-xx`</span> و <span dir="ltr">`S-01`</span>، <span dir="ltr">`B-01`</span>، <span dir="ltr">`A-01`</span>)، اصلاح‌های مکانیکی (<span dir="ltr">`M-001`</span> تا <span dir="ltr">`M-089`</span>)، مورد در انتظار (<span dir="ltr">`PI-01`</span>)، موارد باز (<span dir="ltr">`OI-01`</span> تا <span dir="ltr">`OI-18`</span>) و کد حساب‌های نقد. ارقام اصلی گزارش حسابرسی‌شده (در پیوندهای مستقیم بالا) قفل شده‌اند و دروازه‌های خودکار آن‌ها را می‌سنجند.

## زنجیره داده‌ها

<div dir="ltr">

```text
data/accounting/ + data/telegram/accounting_group/
     │
     │ (1) analysis_tools/accounting_2026_10_10/
     ▼
reports/2026-10-10/Transactions.csv ──┬─────────────┐
                                      │             │
data/telegram/ + data/documents/      │             │ (3) analysis_tools/audit/
     │                                │             │     load → rules → apply
     │ (2) parse_exports → classify   │             │     → balance/bridge → emit
     │     → correlate → ecosystem    │             │
     ▼                                │             │
analysis/ ◄───────────────────────────┘             │
     │                                              │
     │ (2) charts                                   │
     │     build_financial_report                   │
     │     build_performance_report                 │
     ▼                                              ▼
reports/2026-10-14/                        reports/2026-10-18/


sources/governance/
     │
     │ (4) extract_governance_sources
     ▼
sources/governance/extracts/
     ┆
     ┆ (4)
     ▼
docs/governance/*.md
     │
     │ (4) governance_lint → governance_build
     ▼
docs/governance/build/
```

</div>

- **(۱) نسل نخست، گزارش مالی تطبیق‌شده:** زنجیره بایگانی‌شده <span dir="ltr">`analysis_tools/accounting_2026_10_10/`</span> از کارپوشه‌ها، رسیدها و پیام‌های گروه حسابداری، دفتر کل <span dir="ltr">`reports/2026-10-10/Transactions.csv`</span> را ساخت. این زنجیره در فضای کاری جداگانه‌ای اجرا شد و دیگر اجرا نمی‌شود؛ خروجی آن ورودی هر دو شاخه بعدی است.
- **(۲) شاخه تحلیل:** پنج خروجی تلگرام و سند Word گزارش عملکرد رسانه‌ای تجزیه، رده‌بندی و به هم پیوند داده می‌شوند و خروجی‌های میانی در <span dir="ltr">`analysis/`</span> ذخیره می‌شوند. سازنده‌های گزارش این خروجی‌ها را با دفتر کل ترکیب می‌کنند و گزارش‌های <span dir="ltr">`reports/2026-10-14/`</span> را می‌سازند.
- **(۳) شاخه حسابرسی:** زنجیره <span dir="ltr">`analysis_tools/audit/`</span> دفتر کل نسل نخست را با چهار فایل تصمیم، اصلاح، شاهد و حساب در <span dir="ltr">`analysis_tools/audit/data/`</span> ترکیب می‌کند و نسخه حسابرسی‌شده را در <span dir="ltr">`reports/2026-10-18/`</span> می‌نویسد. شواهد آن پیام‌های گروه حسابداری، عکس رسیدها و فاکتورند.
- **(۴) اسناد حاکمیتی:** متن اسناد منبع (فقط محلی) استخراج شد و پایه نگارش چهار سند بود؛ خط‌چین یعنی این پیوند مرجع نگارش است، نه گامی خودکار. متن اصلی Markdown هر سند با <span dir="ltr">`governance_lint`</span> بررسی و با <span dir="ltr">`governance_build`</span> به DOCX و PDF ساخته می‌شود.

## داده‌های خام

همه پوشه‌های <span dir="ltr">`data/`</span> ورودی‌اند و ابزارها فقط آن‌ها را می‌خوانند.

### خروجی‌های تلگرام

هر پوشه خروجی HTML تلگرام دسکتاپ است؛ برای مرور یک گفت‌وگو با رسانه‌هایش، فایل <span dir="ltr">`messages.html`</span> آن را در مرورگر باز کنید. گفت‌وگوهای بلند در فایل‌های پیاپی ادامه می‌یابند: کانال تا <span dir="ltr">`messages4.html`</span>، گروه خصوصی تا <span dir="ltr">`messages6.html`</span> و گروه عمومی تا <span dir="ltr">`messages7.html`</span>؛ پیوند <span dir="ltr">`Next messages`</span> در پایان هر فایل به فایل بعدی می‌رود.

| پوشه | گفت‌وگو | بازه (شمسی) | بازه (میلادی) | پیام | فایل ثبت‌شده |
|---|---|---|---|---|---|
| پوشه <span dir="ltr">[`data/telegram/channel/`](data/telegram/channel/)</span> | کانال انجمن | مهر ۱۳۹۴ تا مهر ۱۴۰۵ | ۲۰۱۵-۰۹-۲۸ تا ‎۲۰۲۶-۱۰-۱۰ | ۳٬۰۱۵ | ۴٬۵۳۷ |
| پوشه <span dir="ltr">[`data/telegram/private_group/`](data/telegram/private_group/)</span> | گروه خصوصی انجمن | تیر ۱۴۰۴ تا مهر ۱۴۰۵ | ۲۰۲۵-۰۷-۱۶ تا ‎۲۰۲۶-۱۰-۱۲ | ۵٬۳۰۹ | ۳۶۹ |
| پوشه <span dir="ltr">[`data/telegram/public_group/ChatExport_2026-10-13/`](data/telegram/public_group/ChatExport_2026-10-13/)</span> | گروه عمومی انجمن | مرداد تا مهر ۱۴۰۵ | ۲۰۲۶-۰۸-۱۰ تا ‎۲۰۲۶-۱۰-۱۲ | ۶٬۱۳۶ | ۵۷۶ |
| پوشه <span dir="ltr">[`data/telegram/summerschool/ChatExport_2026-10-14/`](data/telegram/summerschool/ChatExport_2026-10-14/)</span> | کانال مدرسه تابستانه فیزیک | تیر ۱۴۰۴ تا شهریور ۱۴۰۵ | ۲۰۲۵-۰۷-۱۷ تا ‎۲۰۲۶-۰۸-۲۹ | ۳۷ | ۸۱ |
| پوشه <span dir="ltr">[`data/telegram/accounting_group/`](data/telegram/accounting_group/)</span> | گروه حسابداری انجمن؛ منبع اصلی شواهد پیامی حسابرسی | مرداد ۱۴۰۴ تا تیر ۱۴۰۵ | ۲۰۲۵-۰۷-۲۴ تا ‎۲۰۲۶-۰۶-۲۷ | ۱۵۸ | ۱۴۶ |

شمار پیام‌ها از <span dir="ltr">`analysis/profiles/`</span> آمده است و بازه‌ها تاریخ نخستین و آخرین پیام تاریخ‌دار هر گفت‌وگو در <span dir="ltr">`analysis/messages.jsonl`</span> است. ستون آخر شمار فایل‌هایی است که از هر پوشه در گیت ثبت شده است.

سه فایل بزرگ کانال با Git LFS نگهداری می‌شوند و فهرستشان در <span dir="ltr">`.gitattributes`</span> است: شماره ۲۱ نشریه شباهنگ (PDF، ۷۰ مگابایت)، صوت مصاحبه لایه نازک (فایل صوتی، ۱۱۲ مگابایت) و شب دهم وبینارهای شبانه Sharif Frontiers (فایل صوتی، ۱۰۵ مگابایت). پیش از کلون یا دریافت، <span dir="ltr">`git lfs install`</span> را اجرا کنید؛ وگرنه این سه فایل فقط به شکل اشاره‌گرهای متنی کوچک دریافت می‌شوند.

### ورودی‌های حسابداری

- پوشه <span dir="ltr">[`data/accounting/workbooks/`](data/accounting/workbooks/)</span> — دو کارپوشه اکسل: <span dir="ltr">`Anjoman accounting.xlsx`</span>، کارپوشه اصلی دفترداری، و <span dir="ltr">`Anjoman accounting - refined.xlsx`</span>، نسخه پالایش‌شده و تطبیق‌شده. زنجیره ‎۲۰۲۶-۱۰-۱۰ نسخه پالایش‌شده را جایگزین کرد و نسخه پیشین آن در <span dir="ltr">`reports/2026-10-10/source_snapshots/`</span> مانده است.
- پوشه <span dir="ltr">[`data/accounting/receipts/`](data/accounting/receipts/)</span> — ۲۰ عکس رسید، پشتوانه تراکنش‌های ثبت‌شده.
- پوشه <span dir="ltr">[`data/accounting/documents/`](data/accounting/documents/)</span> — [فاکتور خرید دامنه](data/accounting/documents/invoice-61150.pdf) و [گزارش کامل رویداد معرفی رشته](<data/accounting/documents/physics_intro full report.pdf>).

### سند گزارش عملکرد رسانه‌ای

پوشه <span dir="ltr">[`data/documents/`](data/documents/)</span> یک سند Word دارد: [گزارش عملکرد رسانه‌ای انجمن علمی فیزیک](<data/documents/گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx>) درباره شهریور و مهر ۱۴۰۵. این سند هم خواندنی است و هم ورودی زنجیره تحلیل؛ ابزارها مسیر آن را از <span dir="ltr">`MEDIA_DOCX`</span> در <span dir="ltr">`analysis_tools/common.py`</span> می‌گیرند.

## ابزارها

همه ابزارها ماژول‌های بسته پایتون <span dir="ltr">`analysis_tools`</span> هستند و از ریشه مخزن با <span dir="ltr">`python -m analysis_tools.MODULE`</span> اجرا می‌شوند؛ به جای <span dir="ltr">`MODULE`</span> نام ماژول را بگذارید.

| ماژول | کار |
|---|---|
| ماژول <span dir="ltr">`analysis_tools/common.py`</span> | محل تعریف مسیرهای ورودی خام، دفتر کل و پوشه‌های گزارش (<span dir="ltr">`DATA`</span>، <span dir="ltr">`REPORTS`</span>، <span dir="ltr">`TELEGRAM`</span>، <span dir="ltr">`SOURCES`</span>، <span dir="ltr">`LEDGER_CSV`</span>، <span dir="ltr">`MEDIA_DOCX`</span>) و تابع‌های کمکی مشترک؛ سایر ماژول‌ها مسیرهای <span dir="ltr">`analysis/`</span> و خروجی گزارش خود را جدا تعریف می‌کنند |
| ماژول <span dir="ltr">`analysis_tools/parse_exports.py`</span> | تجزیه خروجی‌های HTML تلگرام و سند Word به رکوردهای پیام در <span dir="ltr">`analysis/messages.jsonl`</span> |
| ماژول <span dir="ltr">`analysis_tools/reconcile_parse.py`</span> | دروازه‌ای که شمار پیام‌های تجزیه‌شده را با شمارش خام فایل‌ها می‌سنجد |
| ماژول <span dir="ltr">`analysis_tools/classify.py`</span> | رده‌بندی پیام‌ها با قاعده‌های ساختاری، واژه‌نامه و برچسب‌گذاری مدل زبانی برای پیام‌های باقی‌مانده |
| ماژول <span dir="ltr">`analysis_tools/correlate.py`</span> | ساخت رشته رویدادها، پیوند میان گفت‌وگوها و تحلیل ماهانه و ساعتی |
| ماژول <span dir="ltr">`analysis_tools/ecosystem.py`</span> | نقشه ارتباط انجمن با زیرگروه‌ها و سازمان‌های بیرونی از روی پیام‌های هدایت‌شده و اشاره‌ها |
| ماژول <span dir="ltr">`analysis_tools/fix_profile_ids.py`</span> | اصلاح ارجاع‌هایی در پروفایل گفت‌وگوها که به جداکننده‌های تاریخ اشاره می‌کنند |
| ماژول <span dir="ltr">`analysis_tools/validate.py`</span> | دروازه‌های پایانی تحلیل: نمونه‌برداری برای بازبینی رده‌بندی و تطبیق خروجی‌های میانی با یکدیگر |
| ماژول <span dir="ltr">`analysis_tools/charts.py`</span> | همه نمودارهای گزارش‌ها؛ با گزینه فارسی در پوشه‌های <span dir="ltr">`charts_fa`</span> می‌نویسد |
| ماژول <span dir="ltr">`analysis_tools/build_financial_report.py`</span> | گزارش مالی ماهانه؛ پیش از نوشتن، جمع‌های ماهانه را بر هر دو مبنا (همه ۹۶ ردیف و ردیف‌های تأییدشده) با دفتر کل می‌سنجد |
| ماژول <span dir="ltr">`analysis_tools/build_performance_report.py`</span> | گزارش عملکرد و فعالیت، فقط از روی خروجی‌های میانی ثبت‌شده |
| ماژول <span dir="ltr">`analysis_tools/build_audit_report.py`</span> | گزارش حسابرسی دفتر کل به انگلیسی و فارسی؛ پیش از نوشتن، دروازه‌ها را اجرا می‌کند |
| ماژول <span dir="ltr">`analysis_tools/report_common.py`</span> | تبدیل Markdown به PDF و بررسی فضای آزاد دیسک پیش از ساخت |
| پوشه <span dir="ltr">`analysis_tools/audit/`</span> | زنجیره حسابرسی: <span dir="ltr">`load`</span> (خواندن دفتر کل و چهار فایل داده) ← <span dir="ltr">`rules`</span> (جدول اصلاح هر تصمیم) ← <span dir="ltr">`apply`</span> (ردیف‌های حسابرسی‌شده و دفتر تغییرات) ← <span dir="ltr">`balance`</span> و <span dir="ltr">`bridge`</span> (ترازنامه هر پروژه، حساب‌های نقد و پل‌های تطبیق) ← <span dir="ltr">`emit`</span> (نوشتن قطعی خروجی‌ها)؛ و <span dir="ltr">`pii.py`</span> برای جست‌وجوی اطلاعات شخصی |
| پوشه <span dir="ltr">`analysis_tools/audit/data/`</span> | ورودی‌های ثبت‌شده حسابرسی: <span dir="ltr">`decisions.json`</span>، <span dir="ltr">`mechanical.json`</span>، <span dir="ltr">`evidence_index.json`</span> و <span dir="ltr">`accounts.json`</span> |
| پوشه <span dir="ltr">`analysis_tools/i18n/`</span> | کاتالوگ متن گزارش‌ها: <span dir="ltr">`en.json`</span> (منبع اصلی)، <span dir="ltr">`fa.json`</span> و <span dir="ltr">`hashes.json`</span>، و واژه‌نامه دست‌نویس <span dir="ltr">`glossary.json`</span> |
| ماژول <span dir="ltr">`analysis_tools/translate.py`</span> | در زنجیره فعال، تنها ماژولی است که Claude API را فرا می‌خواند: کلیدهای تازه یا تغییرکرده <span dir="ltr">`en.json`</span> را به فارسی برمی‌گرداند و هر پاسخ را پیش از پذیرش اعتبارسنجی می‌کند |
| ماژول <span dir="ltr">`analysis_tools/governance_lint.py`</span> | دروازه‌های محتوای اسناد حاکمیتی: عبارت‌های ممنوع، شماره‌گذاری مواد و بندها و درستی ارجاع‌ها |
| ماژول <span dir="ltr">`analysis_tools/governance_build.py`</span> | ساخت DOCX و PDF راست‌به‌چپ اسناد حاکمیتی در <span dir="ltr">`docs/governance/build/`</span> |
| ماژول <span dir="ltr">`analysis_tools/extract_governance_sources.py`</span> | استخراج متن اسناد منبع از <span dir="ltr">`sources/governance/`</span> به <span dir="ltr">`sources/governance/extracts/`</span> (فقط محلی) |
| ماژول <span dir="ltr">`analysis_tools/make_fixtures.py`</span> | برداشتن نمونه پیام‌های واقعی برای آزمون‌ها؛ یک‌بار اجرا شده است |
| پوشه <span dir="ltr">`analysis_tools/tests/`</span> | آزمون‌ها، شامل دروازه‌های خودکار گزارش‌ها و اسناد |
| پوشه <span dir="ltr">`analysis_tools/accounting_2026_10_10/`</span> | بایگانی: زنجیره‌ای که <span dir="ltr">`reports/2026-10-10/`</span> را ساخت. در فضای کاری جداگانه اجرا شد؛ <span dir="ltr">`analysis_tools`</span> آن را وارد نمی‌کند و در جای فعلی اجرا نمی‌شود. شرح آن در [راهنمای خودش](analysis_tools/accounting_2026_10_10/README.md) آمده است. |

## بازسازی و آزمون

همه فرمان‌ها از ریشه مخزن اجرا می‌شوند. چهار گروه فرمان زیر به ترتیب این کارها را انجام می‌دهند:

- گروه نخست: آزمون‌ها و دروازه‌ها، که پیش از هر انتشار باید بی‌خطا باشند؛
- گروه دوم: بررسی محتوای اسناد حاکمیتی و سپس ساخت خروجی‌های آن‌ها؛
- گروه سوم: ساخت گزارش حسابرسی دفتر کل؛
- گروه چهارم: ساخت نمودارها و گزارش‌های تحلیلی مالی ماهانه و عملکرد.

<div dir="ltr">

```bash
python -m pytest analysis_tools/tests -q

python -m analysis_tools.governance_lint
python -m analysis_tools.governance_build

python -m analysis_tools.build_audit_report --lang all

python -m analysis_tools.charts --lang fa
python -m analysis_tools.build_financial_report --lang fa
python -m analysis_tools.build_performance_report --lang fa
```

</div>

- آخرین اجرای آزمون‌ها: ۲۷۱ آزمون موفق، با یک هشدار قدیمی از کتابخانه pypdf.
- گزینه <span dir="ltr">`--lang`</span> در سازنده گزارش حسابرسی یکی از <span dir="ltr">`en`</span>، <span dir="ltr">`fa`</span> یا <span dir="ltr">`all`</span> است و در سه فرمان گزارش‌های ‎۲۰۲۶-۱۰-۱۴ یکی از <span dir="ltr">`en`</span> یا <span dir="ltr">`fa`</span>؛ پیش‌فرض همه <span dir="ltr">`en`</span> است.
- سازنده گزارش حسابرسی پیش از نوشتن، دروازه‌های <span dir="ltr">`G1`</span> تا <span dir="ltr">`G5`</span> و <span dir="ltr">`G9`</span> را دوباره اجرا می‌کند.
- سازنده‌ها اگر روی درایوی که <span dir="ltr">`reports/`</span> در آن است کمتر از ۱ گیگابایت جای خالی باشد، اجرا نمی‌شوند.
- ساخت دوباره اسناد حاکمیتی، گزارش حسابرسی در هر دو زبان و نمودارهای فارسی، بایت‌به‌بایت همان فایل‌های ثبت‌شده را می‌سازد (در ‎۲۰۲۶-۱۰-۲۱ آزموده شد).
- **هشدار:** ساخت دوباره گزارش‌های ‎۲۰۲۶-۱۰-۱۴ با <span dir="ltr">`--lang fa`</span> فایل‌های Markdown و HTML و نمودارها را یکسان می‌سازد، اما دو PDF فارسی، با همان متن و همان شمار صفحه، در سطح بایت فرق می‌کنند. این پوشه منجمد است و آزمون <span dir="ltr">`test_readonly_folders_untouched`</span> روی آن <span dir="ltr">`git diff`</span> می‌گیرد؛ پس از چنین بازسازی‌ای فایل‌های ثبت‌شده را با <span dir="ltr">`git checkout -- reports/2026-10-14/`</span> برگردانید.

### ترجمه دوباره کاتالوگ

ترجمه دوباره فقط وقتی لازم است که <span dir="ltr">`analysis_tools/i18n/en.json`</span> تغییر کرده باشد. دسترسی به API بدون VPN مسدود است. کلید از فایل کلید محلی خوانده می‌شود و هرگز تایپ یا ثبت نمی‌شود:

<div dir="ltr">

```bash
ANTHROPIC_API_KEY="$(cat ~/.config/anthropic/anjoman_key)" python -m analysis_tools.translate
```

</div>

هر کلید فقط وقتی دوباره ترجمه می‌شود که چکیده (هش) متن انگلیسی‌اش در <span dir="ltr">`hashes.json`</span> تغییر کرده باشد. کلیدهای فهرست <span dir="ltr">`translate.MANUAL_KEYS`</span> در <span dir="ltr">`fa.json`</span> دستی نگهداری می‌شوند و هرگز دوباره ترجمه نمی‌شوند؛ اگر متن انگلیسی آن‌ها تغییر کند، <span dir="ltr">`fa.json`</span> و <span dir="ltr">`hashes.json`</span> را دستی به‌روز کنید. پاسخ‌های خام در <span dir="ltr">`analysis/claude/i18n/`</span> نگه داشته می‌شوند تا اجرای دوباره با کاتالوگ بی‌تغییر هیچ فراخوانی API نداشته باشد. سازنده‌های گزارش فقط کاتالوگ‌های ثبت‌شده را می‌خوانند و هرگز API را فرا نمی‌خوانند.

### متن‌های استخراج‌شده اسناد منبع

این متن‌ها فقط به‌صورت محلی ساخته می‌شوند: فایل‌های منبع را در <span dir="ltr">`sources/governance/`</span> بگذارید و فرمان زیر را اجرا کنید؛ خروجی در <span dir="ltr">`sources/governance/extracts/`</span> نوشته می‌شود.

<div dir="ltr">

```bash
python -m analysis_tools.extract_governance_sources
```

</div>

## اصول کار

### نسل‌های منجمد

- هر نسل گزارش پس از انتشار ویرایش نمی‌شود؛ هر اصلاح یا کار تازه در پوشه‌ای با تاریخ تازه زیر <span dir="ltr">`reports/`</span> می‌آید.
- آزمون <span dir="ltr">`test_readonly_folders_untouched`</span> در <span dir="ltr">`analysis_tools/tests/test_audit_report.py`</span> با <span dir="ltr">`git diff`</span> بررسی می‌کند که <span dir="ltr">`reports/2026-10-10/`</span> و <span dir="ltr">`reports/2026-10-14/`</span> دست نخورده باشند. پوشه <span dir="ltr">`reports/2026-10-18/`</span> بنا بر قرارداد منجمد است؛ هیچ آزمونی دست‌نخوردگی آن را بررسی نمی‌کند، فقط دروازه <span dir="ltr">`G9`</span> فایل‌های آن را برای یافتن اطلاعات شخصی می‌خواند. یکسانی آن با ساخت دوباره بررسی می‌شود: اجرای <span dir="ltr">`python -m analysis_tools.build_audit_report --lang all`</span> و سپس <span dir="ltr">`git status`</span> که نباید تغییری نشان دهد. دروازه <span dir="ltr">`G7`</span> در مجموعه آزمون‌ها فقط بررسی می‌کند که دو ساخت پیاپی گزارش در هر زبان یکسان باشند.
- اسناد طراحی و برنامه‌ها در <span dir="ltr">`docs/superpowers/`</span> و ارجاع‌های شاهد حسابرسی متن تاریخی‌اند و حتی جایی که مسیرهای قدیم را نام می‌برند بازنویسی نمی‌شوند؛ [جدول تطبیق مسیرها](#جدول-تطبیق-مسیرها) پل میان این دو است.

### ساخت تکرارپذیر

- زنجیره حسابرسی از ساعت و عدد تصادفی استفاده نمی‌کند. در گزارش حسابرسی، دو ساخت پیاپی در هر زبان باید بایت‌به‌بایت یکسان باشند. آزمون قطعیت اسناد حاکمیتی فقط خروجی DOCX را می‌سنجد؛ یکسانی PDFهای آن با ساخت دوباره و <span dir="ltr">`git status`</span> در ‎۲۰۲۶-۱۰-۲۱ به‌صورت دستی بررسی شد.
- ده دروازه خودکار گزارش حسابرسی (<span dir="ltr">`G1`</span> تا <span dir="ltr">`G10`</span>) در مجموعه آزمون‌ها اجرا می‌شوند: ارقام اصلی قفل‌شده، کامل بودن دفتر تغییرات، محدود بودن اصلاح‌های مکانیکی، برابری اعداد گزارش انگلیسی و فارسی، یکسانی بایت‌به‌بایت، دست‌نخوردگی نسل‌های پیشین، نبود اطلاعات شخصی و هماهنگی واژه‌نامه.
- متن اصلی چهار سند حاکمیتی را آزمون <span dir="ltr">`test_masters_clean`</span> با همان بررسی‌های <span dir="ltr">`governance_lint`</span> می‌سنجد.

### حریم خصوصی

- مخزن عمومی است. خروجی‌های منتشرشده هرگز کد ملی، شماره تلفن، شماره شبا یا شماره کامل کارت ندارند و کارت‌ها فقط با چهار رقم آخر می‌آیند. دروازه <span dir="ltr">`G9`</span> همه فایل‌های خروجی، از جمله متن PDFها، را برای این الگوها جست‌وجو می‌کند.
- اسناد منبع حاکمیتی و متن‌های استخراج‌شده از آن‌ها فقط در <span dir="ltr">`sources/governance/`</span> نگه داشته می‌شوند که در <span dir="ltr">`.gitignore`</span> است، چون برخی از آن‌ها اطلاعات شخصی دارند.
- در اسناد و راهنماهای تازه نام اشخاص، شماره تلفن و شناسه شخصی نمی‌آید و فقط نقش‌ها نام برده می‌شوند.
- فایل‌هایی که پیش‌تر ثبت شده‌اند همان وضع را دارند؛ تاریخچه گیت بازنویسی نشده است.

### نکته‌های همکاری

- فایل‌های بزرگ‌تر از ۵۰ مگابایت با Git LFS نگهداری می‌شوند. سه فایل کنونی روی هم ۲۸۷ مگابایت‌اند.
- پیش از هر انتشار، آزمون‌ها و <span dir="ltr">`governance_lint`</span> باید بی‌خطا باشند.
- برای هر مرحله کار تازه، نخست سند طراحی و برنامه اجرا در <span dir="ltr">`docs/superpowers/`</span> نوشته می‌شود؛ [اسناد طراحی](#اسناد-طراحی) را ببینید.

### گزارش پیشرفت

- **۲۰۲۶-۱۰-۱۰** — گزارش مالی تطبیق‌شده از کارپوشه‌ها و رسیدها ساخته شد (<span dir="ltr">`reports/2026-10-10/`</span>: نسخه انگلیسی و فارسی، کارپوشه حرفه‌ای و بسته شواهد). هزینه اعلام‌شده دامنه و بودجه سه‌ماهه ماشین مجازی وب‌سایت ثبت شد.
- **۲۰۲۶-۱۰-۱۲** — بسته گزارش با PR شماره ۱ در شاخه اصلی ادغام شد. خروجی کانال تلگرام افزوده شد (اکنون <span dir="ltr">`data/telegram/channel/`</span>، ۴٬۵۳۷ فایل). سه فایل رسانه‌ای بزرگ‌تر از ۵۰ مگابایت با Git LFS ثبت شد و باقی محتوا، پس از آنکه ارسال یک‌جای نخست با پایان مهلت متوقف شد، در چند دسته فرستاده شد.
- **۲۰۲۶-۱۰-۱۳** — همه مواد حسابداری با جابه‌جایی محض و حفظ تاریخچه در یک پوشه گرد آمد (اکنون در <span dir="ltr">`data/accounting/`</span>، <span dir="ltr">`data/telegram/accounting_group/`</span> و <span dir="ltr">`reports/`</span>). خروجی گروه خصوصی و گروه عمومی افزوده شد (اکنون <span dir="ltr">`data/telegram/private_group/`</span> و <span dir="ltr">`data/telegram/public_group/`</span>). نخستین README نوشته شد.
- **۲۰۲۶-۱۰-۱۴** — زنجیره تحلیل عملکرد و مالی در <span dir="ltr">`analysis_tools/`</span> ساخته شد: هر پنج خروجی تلگرام تجزیه و با رده‌بندی ده‌دسته‌ای طبقه‌بندی شد، رشته رویدادها میان گفت‌وگوها به هم و به دفتر کل پیوند خورد و نقشه ارتباطات از روی پیام‌های هدایت‌شده و اشاره‌ها ساخته شد. دو بسته گزارش تازه: <span dir="ltr">`reports/2026-10-14/financial_monthly/`</span> و <span dir="ltr">`reports/2026-10-14/performance/`</span>. این کار در ‎۲۰۲۶-۱۰-۱۷ با PR شماره ۲ ادغام شد.
- **۲۰۲۶-۱۰-۱۸** — نسخه فارسی هر دو گزارش ‎۲۰۲۶-۱۰-۱۴ ساخته شد: مبتنی بر کاتالوگ <span dir="ltr">`analysis_tools/i18n/`</span> که یک‌بار با Claude API ترجمه شد، PDF راست‌به‌چپ با WeasyPrint و نمودارهای فارسی در پوشه‌های <span dir="ltr">`charts_fa`</span> (PR شماره ۳).
- **۲۰۲۶-۱۰-۱۹** — گزارش حسابرسی دفتر کل منتشر شد (اکنون <span dir="ltr">`reports/2026-10-18/`</span>، PR شماره ۴): هر ۹۶ تراکنش مبدأ بر پایه شواهد دوباره بررسی شد (۳۸ تصمیم، ۸۹ اصلاح مکانیکی، ۹۷ ردیف حسابرسی‌شده)؛ جمع ترازنامه‌های پروژه‌ها با ارقام اصلی قفل‌شده برابر است؛ پل‌های تطبیق از نسل ‎۲۰۲۶-۱۰-۱۰ تا نسخه حسابرسی‌شده، فهرست نگهداری وجه نقد، افشای شکاف‌های زنجیره موجودی، ۱۸ مورد باز و گزارش انگلیسی و فارسی. ده دروازه خودکار در مجموعه آزمون‌ها اجرا می‌شوند.
- **۲۰۲۶-۱۰-۲۱** — مجموعه چهار سند حاکمیتی با ساخت DOCX و PDF و دروازه <span dir="ltr">`governance_lint`</span> افزوده شد (PR شماره ۵). مخزن بر پایه نقش بازآرایی شد (<span dir="ltr">`data/`</span>، <span dir="ltr">`reports/`</span>، <span dir="ltr">`docs/`</span>، <span dir="ltr">`sources/`</span>) و این راهنمای فارسی جای README انگلیسی را گرفت.

## جدول تطبیق مسیرها

مخزن در ‎۲۰۲۶-۱۰-۲۱ بر پایه نقش بازآرایی شد و همه جابه‌جایی‌های فایل‌های ثبت‌شده با <span dir="ltr">`git mv`</span> و با حفظ تاریخچه انجام شد؛ در سه ردیف «فقط محلی» جدول، فایل‌های ثبت‌نشده بیرون از گیت جابه‌جا یا رونوشت شدند. گزارش‌های منجمد، اسناد طراحی و ارجاع‌های شاهد حسابرسی (مانند <span dir="ltr">`recipts/…`</span> یا <span dir="ltr">`anjoman_accounting_group_export/files/…`</span>) هنوز مسیرهای قدیم را به کار می‌برند؛ این ارجاع‌ها با جدول زیر به مسیرهای امروز برگردانده می‌شوند.

| مسیر قدیم | مسیر جدید |
|---|---|
| پوشه <span dir="ltr">`anjoman_channel_content/`</span> | پوشه <span dir="ltr">`data/telegram/channel/`</span> |
| پوشه <span dir="ltr">`anjoman_private_group_report/`</span> | پوشه <span dir="ltr">`data/telegram/private_group/`</span> |
| پوشه <span dir="ltr">`anjoman_public_group_export/`</span> | پوشه <span dir="ltr">`data/telegram/public_group/`</span> (با همان زیرپوشه <span dir="ltr">`ChatExport_2026-10-13`</span>) |
| پوشه <span dir="ltr">`anjoman_summerschool_channel_content/`</span> | پوشه <span dir="ltr">`data/telegram/summerschool/`</span> (با همان زیرپوشه <span dir="ltr">`ChatExport_2026-10-14`</span>) |
| پوشه <span dir="ltr">`anjoman_accounting_information/anjoman_accounting_group_export/`</span> | پوشه <span dir="ltr">`data/telegram/accounting_group/`</span> |
| کارپوشه‌های <span dir="ltr">`anjoman_accounting_information/Anjoman accounting.xlsx`</span> و <span dir="ltr">`Anjoman accounting - refined.xlsx`</span> | پوشه <span dir="ltr">`data/accounting/workbooks/`</span> |
| پوشه <span dir="ltr">`anjoman_accounting_information/recipts/`</span> | پوشه <span dir="ltr">`data/accounting/receipts/`</span> |
| فایل‌های <span dir="ltr">`anjoman_accounting_information/invoice-61150.pdf`</span> و <span dir="ltr">`physics_intro full report.pdf`</span> | پوشه <span dir="ltr">`data/accounting/documents/`</span> |
| فایل <span dir="ltr">`گزارش_عملکرد_رسانه‌ای_انجمن_علمی_فیزیک.docx`</span> در ریشه مخزن | پوشه <span dir="ltr">`data/documents/`</span> |
| پوشه <span dir="ltr">`anjoman_accounting_information/reports/2026-10-10/`</span> | پوشه <span dir="ltr">`reports/2026-10-10/`</span> |
| پوشه <span dir="ltr">`anjoman_accounting_information/reports/2026-10-18/`</span> | پوشه <span dir="ltr">`reports/2026-10-18/`</span> |
| پوشه <span dir="ltr">`anjoman_accounting_information/accounting_tools/`</span> | پوشه <span dir="ltr">`analysis_tools/accounting_2026_10_10/`</span> (بایگانی) |
| ده سند منبع حاکمیتی ثبت‌نشده در ریشه مخزن | پوشه <span dir="ltr">`sources/governance/`</span> (فقط محلی) |
| اساسنامه رسانا (<span dir="ltr">`Asasname.pdf`</span>، بیرون از مخزن) | رونوشت در <span dir="ltr">`sources/governance/`</span> (فقط محلی) |
| پوشه <span dir="ltr">`analysis/claude/governance_sources/`</span> | پوشه <span dir="ltr">`sources/governance/extracts/`</span> (فقط محلی) |

پوشه <span dir="ltr">`anjoman_accounting_information/`</span> دیگر وجود ندارد و <span dir="ltr">`reports/2026-10-14/`</span> سر جای خودش مانده است. ارجاع‌های کوتاه درون گزارش‌ها از پوشه قدیم خود آغاز می‌شوند: <span dir="ltr">`recipts/…`</span> همان <span dir="ltr">`data/accounting/receipts/`</span> است، و <span dir="ltr">`anjoman_accounting_group_export/files/…`</span> و <span dir="ltr">`photos/…`</span> به زیرپوشه‌های هم‌نام در <span dir="ltr">`data/telegram/accounting_group/`</span> اشاره می‌کنند. دو فایل هم در جای خود ماندند و فقط ثبت شدند: <span dir="ltr">`analysis_tools/extract_governance_sources.py`</span> و یک فایل از پاسخ‌های ذخیره‌شده ترجمه در <span dir="ltr">`analysis/claude/i18n/`</span>.

## اسناد طراحی

هر مرحله کار یک سند طراحی و یک برنامه اجرا در <span dir="ltr">`docs/superpowers/`</span> دارد. این اسناد سابقه تاریخی‌اند، به انگلیسی نوشته شده‌اند و جاهایی که مسیرهای قدیم را نام می‌برند بازنویسی نمی‌شوند.

| تاریخ | موضوع | سند طراحی | برنامه اجرا |
|---|---|---|---|
| ۲۰۲۶-۱۰-۱۴ | تحلیل عملکرد و مالی انجمن از روی خروجی‌های تلگرام، دفتر کل و گزارش رسانه‌ای | فایل <span dir="ltr">[`2026-10-14-performance-analysis-design.md`](docs/superpowers/specs/2026-10-14-performance-analysis-design.md)</span> | فایل <span dir="ltr">[`2026-10-14-performance-analysis.md`](docs/superpowers/plans/2026-10-14-performance-analysis.md)</span> |
| ۲۰۲۶-۱۰-۱۸ | نسخه فارسی گزارش‌های تحلیلی ‎۲۰۲۶-۱۰-۱۴ | فایل <span dir="ltr">[`2026-10-18-persian-reports-design.md`](docs/superpowers/specs/2026-10-18-persian-reports-design.md)</span> | فایل <span dir="ltr">[`2026-10-18-persian-reports.md`](docs/superpowers/plans/2026-10-18-persian-reports.md)</span> |
| ۲۰۲۶-۱۰-۱۸ | حسابرسی دفتر کل و ترازنامه هر پروژه | فایل <span dir="ltr">[`2026-10-18-ledger-audit-design.md`](docs/superpowers/specs/2026-10-18-ledger-audit-design.md)</span> | فایل <span dir="ltr">[`2026-10-18-ledger-audit.md`](docs/superpowers/plans/2026-10-18-ledger-audit.md)</span> |
| ۲۰۲۶-۱۰-۲۱ | مجموعه چهار سند حاکمیتی | فایل <span dir="ltr">[`2026-10-21-governance-docs-design.md`](docs/superpowers/specs/2026-10-21-governance-docs-design.md)</span> | فایل <span dir="ltr">[`2026-10-21-governance-docs-suite.md`](docs/superpowers/plans/2026-10-21-governance-docs-suite.md)</span> |
| ۲۰۲۶-۱۰-۲۱ | بازآرایی مخزن بر پایه نقش و همین راهنمای فارسی | فایل <span dir="ltr">[`2026-10-21-repo-reorganization-design.md`](docs/superpowers/specs/2026-10-21-repo-reorganization-design.md)</span> | فایل <span dir="ltr">[`2026-10-21-repo-reorganization.md`](docs/superpowers/plans/2026-10-21-repo-reorganization.md)</span> |

## وضعیت و کارهای باز

### اسناد حاکمیتی

اسناد در وضعیت پیش‌نویس نسخه ۱٫۰ و آماده بررسی شورای فعلی‌اند؛ اساسنامه پس از تصویب برای معاونت فرهنگی و اجتماعی دانشگاه فرستاده می‌شود. پیش از تصویب این تصمیم‌ها باقی است:

- **امکان‌پذیری اصلاح اساسنامه:** جلسه اصلاح اساسنامه فقط با حضور دوسوم همه اعضای انجمن رسمیت می‌یابد و نوبت دوم ندارد، در حالی که دفتر عضویت جز با فراغت از تحصیل یا انصراف کتبی کوچک نمی‌شود. باید یکی از دو راه برگزیده شود: تمدید سالانه عضویت، یا نوبت دوم برای جلسه اصلاح با حد نصابی کمینه.
- **تأیید دو قاعده تازه:** پایان دادن به دبیری با رأی ۵ از کل ۷ نفر شورا (اساسنامه، ماده ۱۷)، و برگزاری جلسه تحویل حداکثر ظرف چهارده روز پس از اعلام رسمی نتیجه انتخابات (اساسنامه، ماده ۲۴).
- **پرسش‌های باز معاونت:** ۲۱ پرسش که باید پیش از تصویب با معاونت فرهنگی و اجتماعی دانشگاه یا استاد مشاور روشن شود، در [راهنمای اسناد حاکمیتی](docs/governance/README.md) فهرست شده‌اند.

کمبودهای جزئی شناخته‌شده:

- ابزار <span dir="ltr">`governance_lint`</span> تبصره‌ای را که درون یک ارجاع ترکیبی آمده است، مانند «(اساسنامه، ماده ۸ و تبصره ۵ ماده ۸)»، هنوز بررسی نمی‌کند.
- چای تابستانی: برگزاری چای در تابستان به محدوده مجوز نیمسالی بسته شده است، اما روشن نیست که مجوز نیمسالی تابستان را هم در بر می‌گیرد.
- نوبت دوم جلسه فوق‌العاده: اساسنامه اعلام زمان نوبت دوم را در دعوت نخست برای جلسه سالانه و فوق‌العاده هر دو لازم می‌داند (اساسنامه، تبصره ۳ ماده ۱۱)، اما یادآوری آن در شیوه‌نامه داخلی شورا فقط برای جلسه عمومی سالانه آمده است.
- زنجیره امضاکننده: اگر دبیر یا مسئول مالی طرف پرداخت باشد یا در دسترس نباشد نائب دبیر امضا می‌کند، اما اگر نائب دبیر هم چنین وضعی داشته باشد، امضاکننده بعدی تعیین نشده است.

### حسابرسی دفتر کل

۱۸ مورد باز حسابرسی (<span dir="ltr">`OI-01`</span> تا <span dir="ltr">`OI-18`</span>) در <span dir="ltr">[`reports/2026-10-18/Open_Items.csv`](reports/2026-10-18/Open_Items.csv)</span> آمده‌اند؛ برای هر مورد پروژه، ردیف‌های مربوط، مبلغ به تومان، پرسش و آنچه آن را حل می‌کند ثبت شده است. پاسخ هر مورد در نسل تازه‌ای با پوشه تاریخ‌دار تازه زیر <span dir="ltr">`reports/`</span> می‌آید، نه با ویرایش <span dir="ltr">`reports/2026-10-18/`</span>.

---

*این راهنما فقط نقش‌ها را نام می‌برد، نه اشخاص را؛ هیچ نام، شماره تلفن یا شناسه شخصی در آن نیامده است.*

</div>
