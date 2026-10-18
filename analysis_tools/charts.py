"""All report figures. Palette & mark rules per the dataviz skill."""
import json
import re
import zlib
from datetime import datetime
from pathlib import Path

import jdatetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patheffects as pe
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter, date2num, num2date
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .common import ROOT, read_json
from .i18n import localize, t, term

PERF = ROOT / "reports/2026-10-14/performance/charts"
FIN  = ROOT / "reports/2026-10-14/financial_monthly/charts"

# ---------------------------------------------------------------------------
# dataviz system tokens (light mode) - reference palette instance
# ---------------------------------------------------------------------------
SURFACE  = "#fcfcfb"   # chart surface
INK      = "#0b0b0b"   # primary ink (titles)
INK2     = "#52514e"   # secondary ink (labels, legend text)
MUTED    = "#898781"   # axis ticks, subtitles
GRID     = "#e1e0d9"   # hairline gridlines
BASELINE = "#c3c2b7"   # axis / baseline rules
EXT_DOT  = "#c3c2b7"   # de-emphasis dots (ecosystem externals)

CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
       "#008300", "#4a3aa7", "#e34948"]          # categorical slots 1..8, fixed order
SEQ_LIGHT, SEQ_DARK = "#cde2fb", "#0d366b"       # sequential blue ramp 100 -> 700
BLUE, RED = "#2a78d6", "#e34948"                 # diverging poles (Receipts / Payments)
SEQ_CMAP = LinearSegmentedColormap.from_list("blues100_700", [SEQ_LIGHT, SEQ_DARK])
HALO = [pe.withStroke(linewidth=2.5, foreground=SURFACE)]   # surface ring for text over edges

WEEKDAYS = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنج‌شنبه", "جمعه"]        # Jalali week, Saturday first

# ---------------------------------------------------------------------------
# Persian text: this matplotlib build (3.11.2 / Windows) performs native
# complex-script layout (bidi + contextual joining) itself - verified by
# pixel-IoU against a PIL/libraqm ground-truth renderer using the same
# Tahoma face: raw strings score 0.73-0.89, pre-shaped (arabic_reshaper +
# python-bidi) strings 0.23-0.30 because the two pipelines double-apply
# the reversal.  So Persian strings are passed through UNTOUCHED; fa() is
# kept as the single choke point every label goes through.
# ---------------------------------------------------------------------------
def fa(s):
    """Persian labels pass through; matplotlib handles shaping/bidi natively."""
    return s

def _pick_font():
    """First Arabic-script-capable UI font present on this system."""
    avail = {f.name for f in font_manager.fontManager.ttflist}
    for fam in ("Tahoma", "Segoe UI", "Arial"):
        if fam in avail:
            return fam
    return "sans-serif"

FONT = _pick_font()
plt.rcParams.update({
    "font.family": FONT,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "text.color": INK,
})

def load_timeline(): return read_json(ROOT / "analysis/timeline.json")
def load_ecosystem(): return read_json(ROOT / "analysis/ecosystem.json")

def _months(d):
    """Ordered jalali month keys ('YY/MM' zero-padded -> lexicographic == chronologic)."""
    return sorted(k for k in d if k != "unknown") if d else []

def _trunc(s, n=30):
    s = str(s)
    return s if len(s) <= n else s[:n].rstrip() + "…"

def _new_ax(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    return fig, ax

def _chrome(ax, title, subtitle=None, xlab=None, ylab=None, lang="en"):
    """Recessive hairline chrome + aligned title block (left EN, right FA); solid grid only.
    In fa, every string passed in is localize()d here — a single choke point so a
    catalog template with digits baked into its EN text (not just numeric kwargs)
    can't slip Latin digits through, now or after future catalog edits."""
    if lang == "fa":
        title = localize(title)
        if subtitle:
            subtitle = localize(subtitle)
        if xlab:
            xlab = localize(xlab)
        if ylab:
            ylab = localize(ylab)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(BASELINE)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)
    loc = "right" if lang == "fa" else "left"
    if lang == "fa":
        # Fixed-point offsets (not axes-fraction) so title/subtitle spacing is
        # independent of axes height — on a tall figure (e.g. event_timeline
        # with many threads) an axes-fraction offset like y=1.02 can collapse
        # to a point gap smaller than the title's own pad, colliding the two.
        ax.set_title(title, loc=loc, fontsize=12.5, color=INK, fontweight="bold",
                     pad=28 if subtitle else 10)
        if subtitle:
            ax.annotate(subtitle, xy=(1, 1), xycoords="axes fraction",
                        xytext=(0, 6), textcoords="offset points",
                        fontsize=8.5, color=MUTED, ha="right", va="bottom")
    else:
        ax.set_title(title, loc=loc, fontsize=12.5, color=INK, fontweight="bold",
                     pad=20 if subtitle else 10)
        if subtitle:
            ax.text(0, 1.02, subtitle, transform=ax.transAxes,
                    fontsize=8.5, color=MUTED, ha="left", va="bottom")
    if xlab:
        ax.set_xlabel(xlab, color=INK2, fontsize=9)
    if ylab:
        ax.set_ylabel(ylab, color=INK2, fontsize=9)

def _ygrid(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

def _localize_ticks(fig):
    """FA safety net: localize every auto-generated tick label (main + colorbar axes)
    so no chart can slip Latin digits past the catalog/localize() call sites above.
    Limits are read before and re-applied after, so ranges never shift."""
    fig.canvas.draw()
    for ax in fig.get_axes():
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        ax.set_xticks(ax.get_xticks())
        ax.set_xticklabels([localize(lbl.get_text()) for lbl in ax.get_xticklabels()])
        ax.set_yticks(ax.get_yticks())
        ax.set_yticklabels([localize(lbl.get_text()) for lbl in ax.get_yticklabels()])
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

def _save(fig, path, dpi=120, lang="en"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if lang == "fa":
        _localize_ticks(fig)
    fig.savefig(path, dpi=dpi, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return path

def _mfmt(x, _pos=None, lang="en"):
    """Toman -> millions, e.g. 46.9M."""
    s = f"{x / 1e6:,.1f}M" if abs(x) >= 1e5 else f"{x / 1e6:.2f}M"
    return localize(s) if lang == "fa" else s

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def activity_by_month(tl, path, lang="en"):
    """Stacked bars: message counts per chat over jalali months (5 series)."""
    ma = tl.get("monthly_activity") or {}
    months = _months(ma)
    chats = sorted({c for v in ma.values() for c in v})
    fig, ax = _new_ax(11, 5.5)
    bottom = np.zeros(len(months))
    for i, chat in enumerate(chats):
        vals = np.array([sum((ma[m].get(chat) or {}).values()) for m in months], dtype=float)
        ax.bar(range(len(months)), vals, width=0.62, bottom=bottom,
               color=CAT[i], edgecolor=SURFACE, linewidth=1.2,
               label=term("chat", chat, lang))  # 2px surface gap
        bottom += vals
    if len(chats) >= 2:
        ax.legend(title=t("chart.activity.legend_title", lang), frameon=False, fontsize=8,
                  title_fontsize=8, labelcolor=INK2, loc="upper left")
    xticklabels = [localize(m) if lang == "fa" else m for m in months]
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(xticklabels, rotation=45, ha="right")
    _ygrid(ax)
    _chrome(ax, t("chart.activity.title", lang),
            t("chart.activity.subtitle", lang),
            xlab=t("chart.activity.xlab", lang), ylab=t("chart.activity.ylab", lang),
            lang=lang)
    ax.set_ylim(bottom=0)
    return _save(fig, path, lang=lang)


def category_breakdown(tl, path, lang="en"):
    """Horizontal bars: total messages per category (single series -> slot-1 hue)."""
    ma = tl.get("monthly_activity") or {}
    totals = {}
    for v in ma.values():
        for chat in v.values():
            for cat, n in chat.items():
                totals[cat] = totals.get(cat, 0) + n
    items = sorted(totals.items(), key=lambda kv: kv[1])  # ascending -> largest on top
    labels = [term("category", k, lang, default=k.replace("_", " ").title()) for k, _ in items]
    vals = [n for _, n in items]
    fig, ax = _new_ax(9.5, 5.2)
    ax.barh(range(len(vals)), vals, height=0.62, color=CAT[0],
            edgecolor=SURFACE, linewidth=1.0)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(labels, color=INK2, fontsize=9)
    for y, v in enumerate(vals):                       # bars -> value at the tip
        vtxt = f"{v:,}"
        ax.text(v + max(vals) * 0.012, y, localize(vtxt) if lang == "fa" else vtxt,
                va="center", ha="left", fontsize=8, color=INK2)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    _chrome(ax, t("chart.category.title", lang),
            t("chart.category.subtitle", lang),
            xlab=t("chart.category.xlab", lang), lang=lang)
    ax.set_xlim(0, max(vals) * 1.1 if vals else 1)
    return _save(fig, path, lang=lang)


def weekday_hour_heat(tl, path, lang="en"):
    """Heatmap: jalali weekdays x hour, summed over chats (sequential one-hue ramp)."""
    wh = tl.get("weekday_hour_heat") or {}
    M = np.zeros((7, 24))
    for chat in wh.values():
        for wd, hours in chat.items():
            if wd not in WEEKDAYS:
                continue
            r = WEEKDAYS.index(wd)
            for h, n in hours.items():
                hi = int(h)
                if 0 <= hi < 24:
                    M[r, hi] += n
    masked = np.ma.masked_where(M == 0, M)             # zeros recede to the surface
    cmap = SEQ_CMAP.with_extremes(bad=SURFACE)
    fig, ax = _new_ax(10.5, 4.8)
    im = ax.imshow(masked, aspect="auto", cmap=cmap, interpolation="nearest")
    ax.set_yticks(range(7))
    ax.set_yticklabels([fa(w) for w in WEEKDAYS], color=INK2, fontsize=10)
    hour_ticks = ["0", "3", "6", "9", "12", "15", "18", "21", "23"]
    ax.set_xticks([0, 3, 6, 9, 12, 15, 18, 21, 23])
    ax.set_xticklabels([localize(s) if lang == "fa" else s for s in hour_ticks])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.035)
    cb.set_label(t("chart.heat.colorbar", lang), color=INK2, fontsize=9)
    cb.ax.tick_params(colors=MUTED, labelsize=8)
    cb.outline.set_visible(False)
    if M.max() > 0:
        r, c = np.unravel_index(M.argmax(), M.shape)
        note = t("chart.heat.peak", lang, n=f"{int(M.max()):,}",
                  weekday=WEEKDAYS[r], hour=f"{c:02d}")
        if lang == "fa":
            note = localize(note)
    else:
        note = t("chart.heat.no_data", lang)
    _chrome(ax, t("chart.heat.title", lang), note,
            xlab=t("chart.heat.xlab", lang), lang=lang)
    return _save(fig, path, lang=lang)


def hour_histogram(tl, path, lang="en"):
    """Small multiples: per-chat hour-of-day distribution (2x3, legend in slot 6)."""
    hh = tl.get("hour_histogram") or {}
    chats = sorted(hh)
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2))
    fig.patch.set_facecolor(SURFACE)
    axes = axes.ravel()
    for i, chat in enumerate(chats):
        ax = axes[i]
        counts = np.zeros(24)
        for h, n in hh[chat].items():
            counts[int(h)] += n
        ax.bar(range(24), counts, width=0.8, color=CAT[i],
               edgecolor=SURFACE, linewidth=0.6)
        ax.set_facecolor(SURFACE)
        ax.set_title(term("chat", chat, lang), fontsize=10, color=INK, loc="left")
        ax.set_xticks([0, 6, 12, 18, 23])
        ax.set_xlim(-0.8, 23.8)
        _ygrid(ax)
        ax.tick_params(colors=MUTED, labelsize=7)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("bottom", "left"):
            ax.spines[s].set_color(BASELINE)
        if counts.max() > 0:                            # selective: label the peak only
            ptxt = f"{int(counts.max()):,}"
            ax.text(np.argmax(counts), counts.max(), localize(ptxt) if lang == "fa" else ptxt,
                    ha="center", va="bottom", fontsize=7.5, color=INK2)
        if i >= 3:
            ax.set_xlabel(t("chart.hist.xlab", lang), color=INK2, fontsize=8)
    legend_ax = axes[min(len(chats), 5)]
    legend_ax.axis("off")
    if len(chats) >= 2:
        handles = [Patch(facecolor=CAT[i], edgecolor=SURFACE, label=term("chat", chat, lang))
                   for i, chat in enumerate(chats)]
        legend_ax.legend(handles=handles, title=t("chart.hist.legend_title", lang),
                         frameon=False, fontsize=9, title_fontsize=8, labelcolor=INK2,
                         loc="center")
    for j in range(len(chats) + (1 if len(chats) >= 2 else 0), 6):
        axes[j].axis("off")
    if lang == "fa":
        # right-aligned, and spaced apart so the FA header doesn't overlap
        # itself the way the (pre-existing, pixel-pinned) EN header does.
        fig.suptitle(t("chart.hist.title", lang),
                     x=0.99, y=0.98, ha="right", fontsize=12.5, color=INK, fontweight="bold")
        fig.text(0.99, 0.905, t("chart.hist.subtitle", lang),
                 fontsize=8.5, color=MUTED, ha="right")
        fig.tight_layout(rect=(0, 0, 1, 0.86))
    else:
        fig.suptitle(t("chart.hist.title", lang),
                     x=0.01, ha="left", fontsize=12.5, color=INK, fontweight="bold")
        fig.text(0.01, 0.955, t("chart.hist.subtitle", lang),
                 fontsize=8.5, color=MUTED, ha="left")
        fig.tight_layout(rect=(0, 0, 1, 0.93))
    return _save(fig, path, lang=lang)


def _jalali_month_ticks(ax, lang):
    """FA x-axis for event_timeline (spec S3.5): ticks at Jalali month starts,
    labelled with the Persian month name + Persian-digit year (e.g. «مهر ۱۴۰۴»)
    instead of the Gregorian/English ConciseDateFormatter ticks EN uses. Thins to
    every 2nd month when the span is long, to match EN's ~every-2-months density.
    Returns False (caller falls back to the EN-style locator) if the axes don't
    yet have a real date range (e.g. zero threads)."""
    x0, x1 = ax.get_xlim()
    if not (np.isfinite(x0) and np.isfinite(x1)) or x0 >= x1:
        return False
    j0 = jdatetime.date.fromgregorian(date=num2date(x0).date())
    j1 = jdatetime.date.fromgregorian(date=num2date(x1).date())
    months = []
    y, m = j0.year, j0.month
    while (y, m) <= (j1.year, j1.month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    if not months:
        return False
    step = 2 if len(months) > 6 else 1          # match EN's ~every-2-months density
    ticks, labels = [], []
    for i, (y, m) in enumerate(months):
        if i % step and i != len(months) - 1:   # always keep the last month
            continue
        ticks.append(date2num(jdatetime.date(y, m, 1).togregorian()))
        # fa-only composition (no EN equivalent, so no t() template): month name
        # from the glossary, year in Persian digits, e.g. "مهر 1404" -> "مهر ۱۴۰۴".
        labels.append(f"{term('jalali_month', str(m), lang)} {localize(str(y))}")
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    return True


def event_timeline(tl, path, lang="en"):
    """Horizontal span per thread (first_seen -> last_seen); money-only skipped."""
    from .build_performance_report import thread_title   # local import: avoids import cycle
    threads = [th for th in (tl.get("threads") or []) if th.get("first_seen")]
    threads.sort(key=lambda th: th["first_seen"])
    n = len(threads)
    fig, ax = _new_ax(10.5, max(4.0, 1.6 + 0.24 * n))
    labels = []
    for y, th in enumerate(threads):
        x0 = datetime.fromisoformat(th["first_seen"])
        x1 = datetime.fromisoformat(th["last_seen"] or th["first_seen"])
        ax.barh(y, (x1 - x0).total_seconds() / 86400.0, left=x0, height=0.62,
                color=CAT[0], edgecolor=SURFACE, linewidth=0.8)
        labels.append(fa(_trunc(thread_title(th, lang) or th.get("event_ref") or "", 30)))
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=6.5, color=INK2)
    ax.invert_yaxis()
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if lang != "fa" or not _jalali_month_ticks(ax, lang):
        loc = AutoDateLocator()
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(ConciseDateFormatter(loc))
    skipped = len(tl.get("threads") or []) - n
    if skipped:
        sub = t("chart.timeline.sub_excluded", lang, n=f"{n}", skipped=f"{skipped}")
    else:
        sub = t("chart.timeline.sub_plain", lang, n=f"{n}")
    if lang == "fa":
        sub = localize(sub)
    _chrome(ax, t("chart.timeline.title", lang), sub, ylab="", lang=lang)
    return _save(fig, path, dpi=125, lang=lang)


def ecosystem_map(eco, path, lang="en"):
    """Association center, subgroups inner ring, chat-exports + externals outer.

    Edge width is log-scaled and capped so the 1,793-weight association edge
    cannot dwarf the tail; externals are unlabeled dots except the top 15.
    """
    nodes = eco.get("nodes") or []
    edges = eco.get("edges") or []
    byid = {n["id"]: n for n in nodes}
    assoc = [n for n in nodes if n["type"] == "association"]
    subs = sorted((n for n in nodes if n["type"] == "subgroup"), key=lambda n: n["id"])
    chatsx = sorted((n for n in nodes if n["type"] == "chat-export"), key=lambda n: n["id"])
    ext = [n for n in nodes if n["type"] == "external"]

    # incident weight per node (both directions)
    wsum = {}
    for e in edges:
        for side in ("source", "target"):
            wsum[e[side]] = wsum.get(e[side], 0) + e.get("weight", 0)

    # assign each external to the chat-export it interacts with most
    chat_ids = {n["id"] for n in chatsx}
    partner = {}
    for e in edges:
        for a, b in ((e["source"], e["target"]), (e["target"], e["source"])):
            if a in chat_ids and byid.get(b, {}).get("type") == "external":
                cur = partner.get(b)
                if cur is None or e.get("weight", 0) > cur[1]:
                    partner[b] = (a, e.get("weight", 0))

    fig, ax = _new_ax(11, 11)
    pos = {}
    for n in assoc:
        pos[n["id"]] = (0.0, 0.0)
    for i, n in enumerate(subs):
        a = np.pi / 2 + np.pi / max(len(subs), 1) + i * 2 * np.pi / max(len(subs), 1)
        pos[n["id"]] = (np.cos(a), np.sin(a))
    # chat-export sectors sized by their external count; chat at sector center
    groups = {c["id"]: [] for c in chatsx}
    unassigned = []
    for n in ext:
        pid = partner.get(n["id"], (None,))[0]
        if pid in groups:
            groups[pid].append(n)
        else:
            unassigned.append(n)
    top_ids = {n["id"] for n in sorted(ext, key=lambda n: -wsum.get(n["id"], 0))[:15]}
    groups = {cid: [n for n in m if n["id"] not in top_ids] for cid, m in groups.items()}
    n_ext = max(sum(len(v) for v in groups.values()), 1)
    gap = np.deg2rad(6)
    start = np.pi / 2
    PHI = 0.6180339887498949                     # golden-ratio conjugate
    for cid, members in groups.items():
        members.sort(key=lambda n: -wsum.get(n["id"], 0))
        width = (2 * np.pi - gap * len(chatsx)) * len(members) / n_ext if members else 0.0
        if members:
            ca = start + width / 2
            pos[cid] = (2.1 * np.cos(ca), 2.1 * np.sin(ca))
            for k, m in enumerate(members):
                # low-discrepancy spread: nodes distribute across the whole
                # sector instead of bunching at its start
                frac = ((k + 1) * PHI) % 1.0 if len(members) > 1 else 0.5
                a = start + frac * width
                jitter = (zlib.crc32(m["id"].encode()) % 1000) / 1000.0 * 0.5 - 0.25
                r = 3.15 + jitter
                pos[m["id"]] = (r * np.cos(a), r * np.sin(a))
        start += width + gap
    top_nodes = [n for n in ext if n["id"] in top_ids]
    top_nodes.sort(key=lambda n: -wsum.get(n["id"], 0))
    for k, n in enumerate(top_nodes):
        a = np.pi / 2 + k * 2 * np.pi / max(len(top_nodes), 1)
        jitter = (zlib.crc32(n["id"].encode()) % 1000) / 1000.0 * 0.3 - 0.15
        r = 3.15 + jitter
        pos[n["id"]] = (r * np.cos(a), r * np.sin(a))
    # chats with no externals (and fixture nodes): spread on the ring
    ring_i = 0
    for n in chatsx + unassigned:
        if n["id"] not in pos:
            a = np.pi / 2 + ring_i * 2 * np.pi / max(len(chatsx) + len(unassigned), 1)
            pos[n["id"]] = (2.6 * np.cos(a), 2.6 * np.sin(a))
            ring_i += 1

    # edges: blue=forward, orange=mention; log-scaled, capped width
    wmax = max((e.get("weight", 1) for e in edges), default=1)
    for e in sorted(edges, key=lambda e: e.get("weight", 0)):   # heavy drawn last
        if e["source"] not in pos or e["target"] not in pos:
            continue
        wt = np.log1p(e.get("weight", 1)) / np.log1p(wmax)
        color = CAT[0] if e["type"] == "forward" else CAT[1]
        x0, y0 = pos[e["source"]]
        x1, y1 = pos[e["target"]]
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=0.25 + 2.0 * wt,
                alpha=0.10 + 0.45 * wt, zorder=1, solid_capstyle="round")

    # nodes: grayscale hierarchy, identity carried by shape + legend + labels.
    # Labels carry a surface-colored halo (the text twin of the 2px surface
    # ring) and go through a deterministic declutter pass measured against the
    # REAL rendered text extents: overlapping labels are pushed radially
    # outward, and one that still cannot be separated is dropped, never jammed.
    push = []        # [annotation, ux, uy, weight, x0, y0, r0]

    for n in ext:
        if n["id"] in pos:
            x, y = pos[n["id"]]
            ax.scatter([x], [y], s=5, color=EXT_DOT, zorder=2, linewidths=0)
    for n in subs:
        x, y = pos[n["id"]]
        ax.scatter([x], [y], s=340, color=INK2, zorder=3,
                   edgecolor=SURFACE, linewidth=1.5)
        r = np.hypot(x, y) or 1.0
        ann = ax.annotate(fa(n.get("label") or n["id"]), (x, y),
                          xytext=(x * 1.24, y * 1.24), ha="center", va="center",
                          fontsize=8, color=INK2, zorder=5, path_effects=HALO)
        push.append([ann, x / r, y / r, 1e6 + wsum.get(n["id"], 0), x, y, r])
    for n in chatsx:
        if n["id"] in pos:
            x, y = pos[n["id"]]
            ax.scatter([x], [y], s=300, color=INK2, marker="s", zorder=3,
                       edgecolor=SURFACE, linewidth=1.5)
            r = np.hypot(x, y) or 1.0
            cid = n["id"].removesuffix("_export")
            label = t("chart.ecosystem.chat_export_label", lang, chat=term("chat", cid, lang))
            ann = ax.annotate(label, (x, y), xytext=(x * 1.30, y * 1.30),
                              ha="center", va="center", fontsize=8, color=INK2,
                              zorder=5, path_effects=HALO)
            push.append([ann, x / r, y / r, 1e6 + wsum.get(n["id"], 0), x, y, r])
    for n in assoc:
        ax.scatter([0], [0], s=1500, color=INK, zorder=4,
                   edgecolor=SURFACE, linewidth=2.0)
        ax.annotate(fa(n.get("label") or n["id"]), (0, 0), xytext=(0, 0.17),
                    ha="center", va="bottom", fontsize=11, color=INK,
                    fontweight="bold", zorder=6, path_effects=HALO)

    top_ext = sorted((n for n in ext if n["id"] in pos),
                     key=lambda n: -wsum.get(n["id"], 0))[:15]
    for n in top_ext:
        x, y = pos[n["id"]]
        r = np.hypot(x, y) or 1.0
        ux, uy = x / r, y / r
        text = str(_trunc(n.get("label") or n["id"], 18))
        ann = ax.annotate(fa(text), (x, y), xytext=(x * 1.045, y * 1.045),
                          ha="center", va="center", fontsize=7, color=INK2,
                          zorder=5, path_effects=HALO)
        push.append([ann, ux, uy, wsum.get(n["id"], 0), x, y, r])

    def _declutter():
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for _ in range(8):
            live = [it for it in push if it[0].axes is not None]
            boxes = {id(it[0]): it[0].get_window_extent(renderer) for it in live}
            moved = False
            for i, it_i in enumerate(live):
                for it_j in live[i + 1:]:
                    if boxes[id(it_i[0])].overlaps(boxes[id(it_j[0])]):
                        weak, _ = (it_i, it_j) if it_i[3] < it_j[3] else (it_j, it_i)
                        ann, ux, uy = weak[0], weak[1], weak[2]
                        cx, cy = ann.xyann
                        ann.xyann = (cx + ux * 0.2, cy + uy * 0.2)
                        boxes[id(ann)] = ann.get_window_extent(renderer)
                        moved = True
            if not moved:
                return
        # still overlapping after the push budget: the weaker label is dropped
        live = [it for it in push if it[0].axes is not None]
        for i, it_i in enumerate(live):
            for it_j in live[i + 1:]:
                if it_i[0].axes is None:
                    break
                if it_i[0].get_window_extent(renderer).overlaps(
                        it_j[0].get_window_extent(renderer)):
                    weak = it_i if it_i[3] < it_j[3] else it_j
                    weak[0].remove()

    _declutter()
    labeled = 0
    for ann, ux, uy, w, x0, y0, r0 in push:
        if ann.axes is None:
            continue
        cx, cy = ann.xyann
        if np.hypot(cx, cy) > r0 * 1.06 and w < 1e6:      # displaced -> leader line
            ax.plot([x0, cx], [y0, cy], color=EXT_DOT, linewidth=0.6, zorder=4)
        if w < 1e6:
            labeled += 1

    handles = [
        Line2D([], [], color=CAT[0], lw=2, label=t("chart.ecosystem.legend_forward", lang)),
        Line2D([], [], color=CAT[1], lw=2, label=t("chart.ecosystem.legend_mention", lang)),
        Line2D([], [], color=INK, marker="o", ls="", markersize=10,
               label=t("chart.ecosystem.legend_association", lang)),
        Line2D([], [], color=INK2, marker="o", ls="", markersize=9,
               label=t("chart.ecosystem.legend_subgroup", lang)),
        Line2D([], [], color=INK2, marker="s", ls="", markersize=8,
               label=t("chart.ecosystem.legend_chat_export", lang)),
        Line2D([], [], color=EXT_DOT, marker="o", ls="", markersize=6,
               label=t("chart.ecosystem.legend_external", lang)),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=8.5, labelcolor=INK2,
              loc="lower left", title=t("chart.ecosystem.legend_title", lang),
              title_fontsize=8.5)
    ax.set_xlim(-4.4, 4.4)
    ax.set_ylim(-4.0, 4.4)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    title_txt = t("chart.ecosystem.title", lang, n_nodes=f"{len(nodes)}", n_edges=f"{len(edges)}")
    subtitle_txt = t("chart.ecosystem.subtitle", lang, labeled=f"{labeled}")
    if lang == "fa":
        title_txt = localize(title_txt)
        subtitle_txt = localize(subtitle_txt)
        # Fixed-point offsets as in _chrome: Tahoma bold's Persian descenders
        # collided with the subtitle at pad=14 + axes-fraction placement.
        ax.set_title(title_txt, loc="right", fontsize=12.5, color=INK, fontweight="bold", pad=28)
        ax.annotate(subtitle_txt, xy=(1, 1), xycoords="axes fraction",
                    xytext=(0, 6), textcoords="offset points",
                    fontsize=8.5, color=MUTED, ha="right", va="bottom")
    else:
        ax.set_title(title_txt, loc="left", fontsize=12.5, color=INK, fontweight="bold", pad=14)
        ax.text(0, 1.005, subtitle_txt, transform=ax.transAxes,
                fontsize=8.5, color=MUTED, ha="left", va="bottom")
    return _save(fig, path, dpi=125, lang=lang)


def cashflow_monthly(tl, path, lang="en"):
    """Grouped diverging bars: Receipts up (blue), Payments down (red), per month."""
    mc = tl.get("monthly_cashflow") or {}
    months = _months(mc)
    unk = mc.get("unknown") or {}
    if unk.get("Receipts", 0) + unk.get("Payments", 0) > 0:
        months = months + ["unknown"]                    # non-zero -> include, labeled
    labels = [t("chart.cash.unknown_month", lang) + "*" if m == "unknown" else m
              for m in months]
    if lang == "fa":
        labels = [localize(lbl) for lbl in labels]
    rec = [float(mc[m].get("Receipts", 0) or 0) for m in months]
    pay = [float(mc[m].get("Payments", 0) or 0) for m in months]
    x = np.arange(len(months))
    fig, ax = _new_ax(11, 5.5)
    ax.bar(x - 0.2, rec, width=0.36, color=BLUE, edgecolor=SURFACE,
           linewidth=1.0, label=t("chart.cash.receipts", lang))
    ax.bar(x + 0.2, [-p for p in pay], width=0.36, color=RED, edgecolor=SURFACE,
           linewidth=1.0, label=t("chart.cash.payments", lang))
    if rec:                                             # selective labels: the extremes
        i = int(np.argmax(rec))
        ax.text(x[i] - 0.2, rec[i], _mfmt(rec[i], lang=lang), ha="center", va="bottom",
                fontsize=8, color=INK2)
    if pay:
        j = int(np.argmax(pay))
        ax.text(x[j] + 0.2, -pay[j], _mfmt(pay[j], lang=lang), ha="center", va="top",
                fontsize=8, color=INK2)
    ax.axhline(0, color=BASELINE, linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p=None: _mfmt(v, lang=lang)))
    _ygrid(ax)
    _chrome(ax, t("chart.cash.title", lang),
            t("chart.cash.subtitle", lang),
            xlab=t("chart.cash.xlab", lang), ylab=t("chart.cash.ylab", lang), lang=lang)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower left")
    return _save(fig, path, lang=lang)


def cumulative_cash(tl, path, lang="en"):
    """Line: cumulative net (Receipts - Payments) over months, all-rows basis."""
    mc = tl.get("monthly_cashflow") or {}
    months = _months(mc)
    unk = mc.get("unknown") or {}
    if unk.get("Receipts", 0) + unk.get("Payments", 0) > 0:
        months = months + ["unknown"]
    labels = [t("chart.cash.unknown_month", lang) + "*" if m == "unknown" else m
              for m in months]
    if lang == "fa":
        labels = [localize(lbl) for lbl in labels]
    net = np.cumsum([float(mc[m].get("Receipts", 0) or 0) -
                     float(mc[m].get("Payments", 0) or 0) for m in months])
    x = np.arange(len(months))
    fig, ax = _new_ax(10.5, 5.0)
    ax.fill_between(x, net, 0, color=CAT[0], alpha=0.10, zorder=1)   # ~10% wash
    ax.plot(x, net, color=CAT[0], linewidth=2.0, solid_capstyle="round",
            zorder=3)                                                # 2px line
    if len(x):                                                       # end-dot + ring + label
        ax.plot([x[-1]], [net[-1]], "o", markersize=9, color=CAT[0],
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
        ann_text = t("chart.cumcash.annotation", lang, v=_mfmt(net[-1], lang=lang))
        if lang == "fa":
            # RLM: the label starts with "۱۶٫۵M", whose Latin M would otherwise
            # make the base direction LTR and put «تومان» before the number.
            ann_text = "‏" + localize(ann_text)
        ax.annotate(ann_text, (x[-1], net[-1]),
                    xytext=(-8, 10 if net[-1] >= 0 else -12),
                    textcoords="offset points", ha="right",
                    fontsize=9, color=INK2)
    ax.axhline(0, color=BASELINE, linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p=None: _mfmt(v, lang=lang)))
    _ygrid(ax)
    _chrome(ax, t("chart.cumcash.title", lang, net=t("chart.cash.net", lang)),
            t("chart.cumcash.subtitle", lang,
              receipts=t("chart.cash.receipts", lang), payments=t("chart.cash.payments", lang)),
            xlab=t("chart.cumcash.xlab", lang),
            ylab=t("chart.cumcash.ylab", lang, net=t("chart.cash.net", lang)), lang=lang)
    return _save(fig, path, lang=lang)


def render_all(lang="en"):
    tl, eco = load_timeline(), load_ecosystem()
    perf_dir = PERF.with_name("charts_fa") if lang == "fa" else PERF
    fin_dir = FIN.with_name("charts_fa") if lang == "fa" else FIN
    perf_dir.mkdir(parents=True, exist_ok=True); fin_dir.mkdir(parents=True, exist_ok=True)
    out = {"activity_by_month": activity_by_month(tl, perf_dir / "activity_by_month.png", lang),
           "category_breakdown": category_breakdown(tl, perf_dir / "category_breakdown.png", lang),
           "weekday_hour_heat": weekday_hour_heat(tl, perf_dir / "weekday_hour_heat.png", lang),
           "hour_histogram": hour_histogram(tl, perf_dir / "hour_histogram.png", lang),
           "event_timeline": event_timeline(tl, perf_dir / "event_timeline.png", lang),
           "ecosystem_map": ecosystem_map(eco, perf_dir / "ecosystem_map.png", lang),
           "cashflow_monthly": cashflow_monthly(tl, fin_dir / "cashflow_monthly.png", lang),
           "cumulative_cash": cumulative_cash(tl, fin_dir / "cumulative_cash.png", lang)}
    return out

if __name__ == "__main__":
    print(render_all())
