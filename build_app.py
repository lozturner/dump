#!/usr/bin/env python3
"""Stitch embedded data + pre-rendered HTML into the standalone app template.

We pre-render the full list AND a Gantt-style visual timeline as static
HTML so the page works even when the viewer blocks JavaScript (e.g.
mobile file previews). JS enhances on top when available.
"""
import html as _html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from build_releaf_csv import records  # noqa: E402

HERE = Path(__file__).parent
tpl = (HERE / "app_template.html").read_text(encoding="utf-8")

def esc(s):
    return _html.escape(str(s), quote=True)

def cat_class(cat: str) -> str:
    lc = cat.lower()
    if any(k in lc for k in ("fail", "bounce", "miss", "cancel", "complaint")):
        return "warn"
    if any(k in lc for k in ("ship", "paid", "approved", "ready", "allowance", "deliver")):
        return "ok"
    if any(k in lc for k in ("marketing", "notice", "external", "calendar")):
        return "muted"
    if any(k in lc for k in ("support", "escalat", "outbound", "address", "gp", "clinical")):
        return "info"
    if any(k in lc for k in ("booked", "amended", "reminder", "today", "imminent", "rebook")):
        return "purple"
    return ""

def fmt_short(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%-d %b %y")

def fmt_full(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%-d %b %Y, %H:%M")

# ─── Pre-render list (newest first) ───
rows = sorted(records, key=lambda r: r["date"], reverse=True)
row_html_parts = []
for r in rows:
    dir_short = "IN" if r["direction"] == "Inbound" else "OUT"
    row_html_parts.append(f'''
<div class="row" data-id="{esc(r['id'])}" data-cat="{esc(r['category'])}" data-dir="{esc(r['direction'])}" data-date="{esc(r['date'])}">
  <button class="star" data-act="star" data-id="{esc(r['id'])}" title="Star">☆</button>
  <button class="flag" data-act="flag" data-id="{esc(r['id'])}" title="Flag">🚩</button>
  <div class="meta">
    <span class="when">{esc(fmt_short(r['date']))}</span>
    <span class="dir {esc(r['direction'])}">{dir_short}</span>
    <span class="tag {cat_class(r['category'])} cat-tag">{esc(r['category'])}</span>
  </div>
  <div class="sub">
    <div class="subj">{esc(r['subject'])}</div>
    <div class="snip">{esc(r['summary'])}</div>
  </div>
  <a class="chev" href="{esc(r['url'])}" target="_blank" rel="noopener" title="Open in Gmail">↗</a>
</div>''')
initial_list = '<div class="list" id="listInner">' + "".join(row_html_parts) + "</div>"

# ─── Pre-render Gantt-style visual timeline ───
# Build a month-by-category matrix
def ym(iso: str) -> str:
    return iso[:7]  # YYYY-MM

months_set = sorted({ym(r["date"]) for r in records})
cat_count = Counter(r["category"] for r in records)
top_cats = [c for c, _ in cat_count.most_common(14)]
matrix = defaultdict(lambda: defaultdict(int))
for r in records:
    if r["category"] in top_cats:
        matrix[r["category"]][ym(r["date"])] += 1

# Generate Gantt: header row of months, then one row per category
def month_label(m: str) -> str:
    d = datetime.strptime(m, "%Y-%m")
    return d.strftime("%b %y")

# Group months by year for top header band
year_to_months: dict[str, list[str]] = defaultdict(list)
for m in months_set:
    year_to_months[m[:4]].append(m)
years_sorted = sorted(year_to_months.keys())

gantt_header_year = "".join(
    f'<div class="g-year" style="grid-column: span {len(year_to_months[y])}">{y}</div>'
    for y in years_sorted
)
gantt_header_months = "".join(
    f'<div class="g-month" title="{esc(month_label(m))}">{esc(m[5:7])}</div>'
    for m in months_set
)
gantt_rows_html = []
max_count = max((max(matrix[c].values(), default=0) for c in top_cats), default=1)
for cat in top_cats:
    cells = []
    for m in months_set:
        n = matrix[cat].get(m, 0)
        if n:
            # opacity scales with intensity
            o = 0.25 + 0.75 * (n / max_count)
            cells.append(
                f'<div class="g-cell on" data-cat="{esc(cat)}" data-month="{m}" '
                f'title="{esc(cat)} — {month_label(m)}: {n} email{"s" if n!=1 else ""}" '
                f'style="background: rgba(15,118,110,{o:.2f})">{n if n > 1 else ""}</div>'
            )
        else:
            cells.append('<div class="g-cell"></div>')
    gantt_rows_html.append(
        f'<div class="g-rowlabel"><span class="tag {cat_class(cat)}">{esc(cat)}</span> '
        f'<span class="g-count">{cat_count[cat]}</span></div>'
        f'<div class="g-rowcells">{"".join(cells)}</div>'
    )

def cell_html(cat: str, m: str) -> str:
    n = matrix[cat].get(m, 0)
    if not n:
        return '<div class="g-cell"></div>'
    o = 0.25 + 0.75 * (n / max_count)
    plural = "s" if n != 1 else ""
    return (
        f'<div class="g-cell on" data-cat="{esc(cat)}" data-month="{m}" '
        f'title="{esc(cat)} — {month_label(m)}: {n} email{plural}" '
        f'style="background: rgba(15,118,110,{o:.2f})">{n if n > 1 else ""}</div>'
    )

# Build rows as a single sequence so every cell is a direct child of g-grid
gantt_body_cells = []
for cat in top_cats:
    gantt_body_cells.append(
        f'<div class="g-rowlabel"><span class="tag {cat_class(cat)}">{esc(cat)}</span>'
        f'<span class="g-count">{cat_count[cat]}</span></div>'
    )
    gantt_body_cells.extend(cell_html(cat, m) for m in months_set)

gantt_html = f'''
<div class="gantt">
  <div class="g-grid" style="grid-template-columns: 220px repeat({len(months_set)}, minmax(22px, 1fr));">
    <div></div>
    {gantt_header_year}
    <div></div>
    {gantt_header_months}
    {"".join(gantt_body_cells)}
  </div>
  <div class="g-legend">
    <span><span class="g-swatch" style="background: rgba(15,118,110,0.25)"></span>1 email</span>
    <span><span class="g-swatch" style="background: rgba(15,118,110,0.6)"></span>a few</span>
    <span><span class="g-swatch" style="background: rgba(15,118,110,1)"></span>many</span>
    <span style="margin-left:auto;color:var(--muted);font-size:12px">{len(records)} events across {len(months_set)} months · click any cell to filter</span>
  </div>
</div>
'''

# ─── Stitch ───
out = (tpl
    .replace("__DATA_JSON__", json.dumps(records, ensure_ascii=False))
    .replace("__INITIAL_LIST__", initial_list)
    .replace("__GANTT_HTML__", gantt_html)
    .replace("__TOTAL__", str(len(records)))
    .replace("__FIRST_MONTH__", month_label(months_set[0]))
    .replace("__LAST_MONTH__", month_label(months_set[-1]))
)
target = HERE / "releaf_chronology.html"
target.write_text(out, encoding="utf-8")
print(f"Wrote {target} ({len(out):,} bytes, {len(records)} records, {len(months_set)} months)")
