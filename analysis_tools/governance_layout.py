# -*- coding: utf-8 -*-
"""Governance-only HTML layout; financial report rendering is intentionally unchanged."""
from __future__ import annotations

import html
import re

import markdown
from bs4 import BeautifulSoup


FONT = "Tahoma"
DRAFT = "پیش‌نویس پیشنهادی برای بررسی و تصویب"
COMPANIONS = ("handover-guide", "operations-forms", "review-adoption")

CSS = """
@page {
  size: A4; margin: 21mm 19mm 22mm;
  @top-right { content: 'انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف';
    font: 8pt Tahoma; color: #52606d; }
  @bottom-right { content: 'صفحه ' counter(page, persian) ' از ' counter(pages, persian);
    font: 8pt Tahoma; color: #52606d; }
  @bottom-left { content: 'پیشنهادی ـ تصویب‌نشده'; font: 8pt Tahoma; color: #52606d; }
}
html { direction: rtl; }
body { font: 11pt Tahoma, sans-serif; line-height: 1.85; color: #202f3e; }
h1 { font-size: 21pt; line-height: 1.8; color: #133b55; bookmark-level: none; }
h2 { font-size: 15pt; line-height: 1.75; margin: 9mm 0 3mm; padding-bottom: 2mm;
  border-bottom: 1pt solid #b4c6d0; break-after: avoid; bookmark-level: 1; }
h3 { font-size: 12.5pt; line-height: 1.8; margin: 6mm 0 2mm;
  break-after: avoid; bookmark-level: 2; }
h4 { font-size: 11.5pt; break-after: avoid; bookmark-level: 3; }
p { margin: 0 0 3mm; orphans: 3; widows: 3; }
p.unit-meta { font-size: 9pt; color: #52606d; break-after: avoid; }
li { margin-bottom: 2mm; orphans: 2; widows: 2; }
ul, ol { padding-right: 6mm; padding-left: 0; }
a { color: #174d6c; text-decoration: none; overflow-wrap: break-word; }
code, .latin { direction: ltr; unicode-bidi: embed; font-size: 0.92em; }
code { font-family: Consolas, Tahoma, monospace; background: #f0f3f5; }
pre { direction: ltr; white-space: pre-wrap; overflow-wrap: break-word; }
blockquote { border-right: 2pt solid #567c90; background: #f1f5f7;
  margin: 4mm 0; padding: 3mm 4mm; }
table { width: 100%; border-collapse: collapse; direction: rtl;
  margin: 4mm 0; font-size: 9.5pt; line-height: 1.75; }
th { background: #e1ebf0; color: #153c54; }
th, td { text-align: right; vertical-align: top; border: 0.5pt solid #b7c6ce;
  padding: 2mm; overflow-wrap: break-word; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
hr { border: 0; border-top: 0.5pt solid #b7c6ce; margin: 5mm 0; }
.cover { min-height: 205mm; padding-top: 25mm; break-after: page; }
.cover .status { font-size: 13pt; color: #52606d; }
.cover .identity { margin-top: 10mm; font-size: 11pt; }
nav { break-after: page; }
nav h2 { bookmark-level: none; }
nav ul { list-style: none; padding: 0; }
nav li { margin-bottom: 2mm; }
nav a::after { content: leader('.') target-counter(attr(href), page, persian); }
nav .sub { padding-right: 5mm; font-size: 10pt; }
"""


def parsed_markdown(text: str) -> BeautifulSoup:
    """One Markdown parse feeds both editions; stable IDs power their contents."""
    soup = BeautifulSoup(markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]), "html.parser")
    for i, heading in enumerate(soup.find_all(["h2", "h3", "h4"]), 1):
        heading["id"] = f"gov-{i}"
    for code in soup.find_all("code"):
        code["dir"] = "ltr"
    label = re.compile(r"^(?:ماده\s+[۰-۹0-9]+(?:\s+\([^)]*\))?|[۰-۹]+-[۰-۹]+\.\s*[^:]{1,100}|تبصره(?:\s+[۰-۹]+)?):")
    for p in soup.find_all("p"):
        if p.get_text().startswith("نسخه"):
            p["class"] = "unit-meta"
        if p.contents and isinstance(p.contents[0], str):
            first = p.contents[0]
            match = label.match(first)
            if match:
                strong = soup.new_tag("strong")
                strong.string = match.group(0)
                first.replace_with(strong)
                strong.insert_after(str(first)[match.end():])
    return soup


def governance_html(text: str, title: str) -> str:
    soup = parsed_markdown(text)
    first = soup.find("h1")
    if first:
        first.decompose()
    items = []
    for heading in soup.find_all("h2"):
        items.append(f'<li><a href="#{heading["id"]}">'
                     f'{html.escape(heading.get_text(" ", strip=True))}</a></li>')
    contents = ('<nav aria-label="فهرست مطالب"><h2>فهرست مطالب</h2><ul>'
                + "".join(items) + "</ul></nav>") if items else ""
    return ('<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
            f'<title>{html.escape(title)}</title><meta name="author" '
            'content="انجمن علمی دانشکده فیزیک دانشگاه صنعتی شریف">'
            f'<style>{CSS}</style></head><body><section class="cover">'
            f'<h1>{html.escape(title)}</h1><p class="status">{DRAFT}</p>'
            '<p class="identity">بسته پیشنهادی برای هفت عضو شورای مرکزی دوره آینده</p>'
            '<p>این نسخه به معنای تصویب، تأیید دانشگاه یا آغاز اجرای قواعد پیشنهادی نیست.</p>'
            '</section>' + contents + f'<main>{soup}</main></body></html>')
