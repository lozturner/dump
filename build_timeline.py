#!/usr/bin/env python3
"""Build a STANDALONE Visual Timeline page — no sidebar, no other pages.
Just: Gantt heatmap on the left, click a cell → email list appears on the
right with one row per individual email, click a row → expands inline
showing full body + Gmail link.

Goal: a minimal, testable, working version of the one thing that's been
broken across multiple attempts.
"""
import html as _html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from build_releaf_csv import records  # 449 records

HERE = Path(__file__).parent

# Load bodies
BODIES = {}
bodies_path = HERE / "email_bodies.json"
if bodies_path.exists():
    raw = json.loads(bodies_path.read_text(encoding="utf-8"))
    BODIES = {mid: {"body": b["body"]} for mid, b in raw.items() if b.get("body")}

def esc(s):
    return _html.escape(str(s), quote=True)

GMAIL = "https://mail.google.com/mail/u/0/#all/{}"

# Sort records oldest → newest for the timeline
records.sort(key=lambda r: r["date"])

# Direction derived from sender
def direction(r):
    return "Outbound" if (r.get("from") or "").lower().startswith("lozturner@") else "Inbound"

# Augment records with direction + url for JS
for r in records:
    r["direction"] = direction(r)
    r["url"] = GMAIL.format(r["id"])

# Build the matrix: category × month → list of emails
def ym(iso): return iso[:7]

months = sorted({ym(r["date"]) for r in records})
cat_count = Counter(r["category"] for r in records)
TOP_N = 14
top_cats = [c for c, _ in cat_count.most_common(TOP_N)]

matrix = defaultdict(lambda: defaultdict(int))
for r in records:
    if r["category"] in top_cats:
        matrix[r["category"]][ym(r["date"])] += 1

max_count = max((max(matrix[c].values(), default=0) for c in top_cats), default=1)

# Category color hint
def cat_class(cat):
    lc = cat.lower()
    if any(k in lc for k in ("fail", "bounce", "miss", "cancel", "complaint")): return "warn"
    if any(k in lc for k in ("ship", "paid", "approved", "ready", "allowance", "deliver")): return "ok"
    if any(k in lc for k in ("marketing", "notice", "external", "calendar")): return "muted"
    if any(k in lc for k in ("support", "escalat", "outbound", "address", "gp", "clinical")): return "info"
    if any(k in lc for k in ("booked", "amended", "reminder", "today", "imminent", "rebook")): return "purple"
    return ""

# Build year and month band
year_to_months = defaultdict(list)
for m in months:
    year_to_months[m[:4]].append(m)
years = sorted(year_to_months.keys())

year_band = "".join(
    f'<div class="g-year" style="grid-column: span {len(year_to_months[y])}">{y}</div>'
    for y in years
)
month_band = "".join(
    f'<div class="g-month">{esc(m[5:7])}</div>'
    for m in months
)

# Cells
def cell_html(cat, m):
    n = matrix[cat].get(m, 0)
    if not n:
        return '<div class="g-cell"></div>'
    o = 0.25 + 0.75 * (n / max_count)
    plural = "s" if n != 1 else ""
    label = m
    return (
        f'<div class="g-cell on" data-cat="{esc(cat)}" data-month="{m}" '
        f'title="{esc(cat)} {label}: {n} email{plural}" '
        f'style="background: rgba(15,118,110,{o:.2f})" tabindex="0" role="button">'
        f'{n}</div>'
    )

body_cells = []
for cat in top_cats:
    body_cells.append(
        f'<div class="g-rowlabel"><span class="tag {cat_class(cat)}">{esc(cat)}</span>'
        f'<span class="g-count">{cat_count[cat]}</span></div>'
    )
    body_cells.extend(cell_html(cat, m) for m in months)

gantt_inner = (
    '<div></div>'                      # blank top-left corner above year band
    + f'{year_band}'
    + '<div></div>'                    # blank corner above month band
    + f'{month_band}'
    + "".join(body_cells)
)

# Strip records to fields the page needs
DATA = [
    {
        "id": r["id"],
        "date": r["date"],
        "from": r["from"],
        "to": r["to"],
        "subject": r["subject"],
        "summary": r["summary"],
        "category": r["category"],
        "direction": r["direction"],
        "url": r["url"],
    }
    for r in records
]

cols = f"220px repeat({len(months)}, minmax(22px, 1fr))"

html_template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Releaf Visual Timeline</title>
<style>
:root {
  --bg: #f3f4f1; --pane: #ffffff; --text: #111827; --muted: #6b7280;
  --soft: #9ca3af; --border: #e5e7eb; --hover: #f8fafc;
  --accent: #0f766e; --accent-soft: #ccfbf1; --accent-text: #134e4a;
  --star: #f59e0b; --star-soft: #fef3c7;
  --flag: #b91c1c; --flag-soft: #fee2e2;
  --ok: #166534; --ok-soft: #dcfce7;
  --info: #1d4ed8; --info-soft: #dbeafe;
  --purple: #6d28d9; --purple-soft: #ede9fe;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; background: var(--bg); color: var(--text);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
a { color: var(--accent); text-decoration: none; } a:hover { text-decoration: underline; }

.page { display: grid; grid-template-rows: 56px 1fr; height: 100vh; }
header.top {
  display: flex; align-items: center; gap: 12px; padding: 0 18px;
  background: var(--pane); border-bottom: 1px solid var(--border);
}
header.top .dot { width: 10px; height: 10px; background: var(--accent); border-radius: 3px; }
header.top h1 { margin: 0; font-size: 16px; font-weight: 600; }
header.top .meta { margin-left: auto; color: var(--muted); font-size: 12px; }

main.split {
  display: grid; grid-template-columns: minmax(0, 1fr) 480px;
  min-height: 0; overflow: hidden;
}
@media (max-width: 900px) {
  main.split { grid-template-columns: minmax(0, 1fr); grid-template-rows: 1fr auto; }
  aside.pane { border-left: none !important; border-top: 1px solid var(--border); max-height: 55vh; }
}

.gantt-scroll { overflow: auto; padding: 16px; min-width: 0; min-height: 0; }

.g-grid { display: grid; gap: 2px; align-items: center; min-width: 720px;
  grid-template-columns: __COLS__; }
.g-year { font-size: 12px; color: var(--muted); text-align: center; padding: 4px 0; font-weight: 600;
  border-bottom: 1px solid var(--border); background: var(--bg); }
.g-month { font-size: 10px; text-align: center; color: var(--soft); padding: 2px 0;
  background: var(--bg); border-bottom: 1px solid var(--border); text-transform: uppercase; }
.g-rowlabel { padding: 4px 8px; font-size: 12px; background: var(--pane); border-radius: 4px;
  display: flex; align-items: center; gap: 6px; min-width: 0; }
.g-count { color: var(--muted); font-size: 11px; margin-left: auto; }
.g-cell { background: #eef2ee; height: 24px; border-radius: 3px; font-size: 10px;
  display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;
  transition: transform .08s, outline .1s; outline: 2px solid transparent; outline-offset: -1px; }
.g-cell.on { cursor: pointer; }
.g-cell.on:hover { outline-color: var(--accent); transform: scale(1.08); position: relative; z-index: 1; }
.g-cell.on.selected { outline: 3px solid var(--star); outline-offset: -2px;
  box-shadow: 0 0 0 4px var(--star-soft); position: relative; z-index: 2; }

.tag { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px;
  font-size: 11px; font-weight: 500; background: var(--accent-soft); color: var(--accent-text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
.tag.warn { background: var(--flag-soft); color: var(--flag); }
.tag.ok { background: var(--ok-soft); color: var(--ok); }
.tag.info { background: var(--info-soft); color: var(--info); }
.tag.purple { background: var(--purple-soft); color: var(--purple); }
.tag.muted { background: #f1f5f9; color: var(--muted); }

aside.pane {
  border-left: 1px solid var(--border); background: var(--pane);
  display: flex; flex-direction: column; min-height: 0; min-width: 0; overflow: hidden;
  box-shadow: -8px 0 24px rgba(0,0,0,.04);
}
.pane-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px;
  padding: 40px 24px; text-align: center; color: var(--muted);
}
.pane-empty .ic { font-size: 38px; opacity: .4; }
.pane-empty h3 { margin: 0; color: var(--text); font-size: 15px; font-weight: 600; }
.pane-empty p { margin: 0; font-size: 12px; }

.pane-header {
  flex: 0 0 auto; padding: 14px 18px; background: #fafbf9;
  border-bottom: 1px solid var(--border);
}
.pane-header h2 { margin: 0; font-size: 15px; font-weight: 600; line-height: 1.2; }
.pane-header .sub { margin-top: 4px; font-size: 12px; color: var(--muted); }

.pane-body { flex: 1 1 0; overflow-y: auto; background: var(--pane); min-height: 0; }

/* INDIVIDUAL EMAIL ROWS */
.row { border-bottom: 1px solid #f1f5f4; }
.row[open] { background: #fafbf9; box-shadow: inset 3px 0 0 var(--accent); }
.row > summary {
  list-style: none; cursor: pointer;
  display: grid;
  grid-template-columns: 50px 70px 1fr 18px;
  gap: 6px 10px;
  padding: 10px 14px;
}
.row > summary::-webkit-details-marker { display: none; }
.row > summary::marker { display: none; }
.row > summary:hover { background: var(--hover); }
.row > summary > .dir {
  font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;
  text-align: center; height: 18px; align-self: center;
}
.row > summary > .dir.Inbound { background: var(--purple-soft); color: var(--purple); }
.row > summary > .dir.Outbound { background: var(--star-soft); color: #92400e; }
.row > summary > .when { font-size: 11px; color: var(--muted); white-space: nowrap; align-self: center; }
.row > summary > .text { min-width: 0; }
.row > summary > .text .subj { font-size: 13px; font-weight: 600; color: var(--text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 2px; }
.row > summary > .text .snip { font-size: 12px; color: var(--muted);
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; }
.row > summary > .chev { color: var(--soft); align-self: center; transition: transform .15s; text-align: center; }
.row[open] > summary > .chev { transform: rotate(90deg); color: var(--accent); }

.row-expanded { padding: 12px 16px 16px; background: white; }
.row-expanded dl.meta-grid { display: grid; grid-template-columns: 70px 1fr; gap: 4px 14px;
  font-size: 12px; margin: 0 0 12px; padding: 10px 12px; background: var(--bg); border-radius: 6px; }
.row-expanded dt { color: var(--muted); }
.row-expanded dd { margin: 0; word-break: break-word; }
.row-expanded dd code { font-size: 11px; color: var(--muted); }
.block-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .06em; color: var(--muted); margin: 12px 0 4px; }
.summary-text { font-size: 13px; line-height: 1.55; margin: 0 0 8px; }
.body-text {
  background: var(--bg); padding: 12px 14px; border-radius: 8px;
  font: 13px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  white-space: pre-wrap; word-wrap: break-word; margin: 0;
  max-height: 360px; overflow-y: auto; border: 1px solid var(--border);
}
.no-body { padding: 10px 12px; background: #fef9e7; border: 1px solid #fde68a;
  border-radius: 6px; color: #92400e; font-size: 12px; }
.row-actions { margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
.gm-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px;
  background: var(--accent); color: white; border: none; border-radius: 8px;
  font-weight: 500; font-size: 13px; text-decoration: none; }
.gm-btn:hover { background: #115e59; text-decoration: none; }
</style>
</head>
<body>
<div class="page">
  <header class="top">
    <span class="dot"></span>
    <h1>Releaf Visual Timeline</h1>
    <span class="meta">__TOTAL__ emails · April 2024 → May 2026 · click any green cell</span>
  </header>
  <main class="split">
    <div class="gantt-scroll" id="ganttScroll">
      <div class="g-grid">__GANTT__</div>
    </div>
    <aside class="pane" id="pane">
      <div class="pane-empty">
        <div class="ic">📨</div>
        <h3>Click a green cell on the left</h3>
        <p>The emails inside that category × month will appear here — one row per email, with the date, sender, subject and snippet. Click a row to expand and read the full body.</p>
      </div>
    </aside>
  </main>
</div>
<script>
const DATA = __DATA__;
const BODIES = __BODIES__;
const BY_ID = Object.fromEntries(DATA.map(r => [r.id, r]));

const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[c]));
const fmtDate = iso => new Date(iso).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
const fmtShort = iso => new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });

function rowHtml(r) {
  const bodyInfo = BODIES[r.id];
  const hasBody = !!(bodyInfo && bodyInfo.body);
  const dirShort = r.direction === "Inbound" ? "IN" : "OUT";
  const bodyBlock = hasBody
    ? `<pre class="body-text">${esc(bodyInfo.body)}</pre>`
    : `<div class="no-body">Only the Gmail snippet is available for this email. Click "Open in Gmail" below to read the original.</div>`;
  return `<details class="row" data-id="${esc(r.id)}">
    <summary>
      <span class="dir ${esc(r.direction)}">${dirShort}</span>
      <span class="when">${esc(fmtShort(r.date))}</span>
      <div class="text">
        <div class="subj">${esc(r.subject)}</div>
        <div class="snip">${esc(r.summary)}</div>
      </div>
      <span class="chev">▸</span>
    </summary>
    <div class="row-expanded">
      <dl class="meta-grid">
        <dt>From</dt><dd>${esc(r.from)}</dd>
        <dt>To</dt><dd>${esc(r.to)}</dd>
        <dt>Date</dt><dd>${esc(fmtDate(r.date))}</dd>
        <dt>Category</dt><dd>${esc(r.category)}</dd>
        <dt>Msg ID</dt><dd><code>${esc(r.id)}</code></dd>
      </dl>
      <div class="block-label">Summary (auto-generated)</div>
      <p class="summary-text">${esc(r.summary)}</p>
      <div class="block-label">Full email body</div>
      ${bodyBlock}
      <div class="row-actions">
        <a class="gm-btn" href="${esc(r.url)}" target="_blank" rel="noopener">↗ Open in Gmail</a>
      </div>
    </div>
  </details>`;
}

let selectedCell = null;

function loadCell(cat, month, cellEl) {
  if (selectedCell) selectedCell.classList.remove("selected");
  cellEl.classList.add("selected");
  selectedCell = cellEl;

  const emails = DATA.filter(r => r.category === cat && r.date.slice(0,7) === month)
                     .sort((a,b) => b.date.localeCompare(a.date));
  const monthLabel = new Date(month + "-01").toLocaleDateString("en-GB", { month: "long", year: "numeric" });

  const pane = document.getElementById("pane");
  pane.innerHTML = `
    <div class="pane-header">
      <h2>${esc(cat)}</h2>
      <div class="sub">${esc(monthLabel)} · ${emails.length} ${emails.length === 1 ? "email" : "emails"} (one row per email, newest first)</div>
    </div>
    <div class="pane-body">${emails.map(rowHtml).join("")}</div>
  `;
}

document.querySelectorAll(".g-cell.on").forEach(c => {
  c.addEventListener("click", () => loadCell(c.dataset.cat, c.dataset.month, c));
  c.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); loadCell(c.dataset.cat, c.dataset.month, c); }
  });
});
</script>
</body>
</html>
"""

out_html = (html_template
    .replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
    .replace("__BODIES__", json.dumps(BODIES, ensure_ascii=False))
    .replace("__GANTT__", gantt_inner)
    .replace("__COLS__", cols)
    .replace("__TOTAL__", str(len(records)))
)

target = HERE / "visual_timeline.html"
target.write_text(out_html, encoding="utf-8")
print(f"Wrote {target} ({len(out_html):,} bytes, {len(records)} records, {len(BODIES)} bodies)")
