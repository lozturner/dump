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

# Load full email bodies if the fetcher subagent has produced them.
bodies_path = HERE / "email_bodies.json"
BODIES = {}
if bodies_path.exists():
    try:
        BODIES = json.loads(bodies_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN: could not parse {bodies_path}: {e}")

# Merge in any bodies that don't have a corresponding row in the curated
# records list. These are typically replies inside multi-message threads
# that the original snippet-based pass collapsed into a single row.
GMAIL = "https://mail.google.com/mail/u/0/#all/{}"
existing_ids = {r["id"] for r in records}

def guess_category(b):
    sender = (b.get("from", "") or "").lower()
    subj = (b.get("subject", "") or "").lower()
    is_out = sender.startswith("lozturner@")
    if "bignarstiemedical" in sender or "bignarstiemedical" in subj or "new customer message" in subj:
        return "External/Switch" if not is_out else "Outbound/Switch"
    if is_out and subj.startswith("fwd"):
        return "Outbound/Forward"
    if is_out:
        return "Outbound/Support"
    return "Support"

for mid, b in BODIES.items():
    if mid in existing_ids:
        continue
    sender = b.get("from", "") or ""
    direction = "Outbound" if sender.lower().startswith("lozturner@") else "Inbound"
    body_text = (b.get("body") or "").strip()
    # First non-empty sentence-ish chunk as summary
    summary = (body_text.split("\n\n")[0] or body_text)[:240].replace("\n", " ").strip()
    if len(body_text) > 240:
        summary += "…"
    records.append({
        "id": mid,
        "url": GMAIL.format(mid),
        "date": b.get("date", ""),
        "from": sender,
        "to": b.get("to", "") or "",
        "direction": direction,
        "subject": b.get("subject", "") or "(no subject)",
        "category": guess_category(b),
        "summary": summary or "(body-only message — see expanded view)",
    })
# Re-sort after merging
records.sort(key=lambda r: r["date"])
print(f"Merged {len(records) - len(existing_ids)} orphan-body messages; total records: {len(records)}")

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

def render_body(r):
    """Return the expanded-detail HTML for a single record."""
    body_info = BODIES.get(r["id"])
    if body_info and body_info.get("body"):
        # Preserve line breaks but escape HTML
        body_html = (
            '<div class="body-block"><div class="block-label">Full email body</div>'
            f'<pre class="body-text">{esc(body_info["body"])}</pre></div>'
        )
    else:
        body_html = (
            '<div class="body-block muted-block">'
            '<div class="block-label">Full email body</div>'
            '<p class="muted small">Only the Gmail snippet is available for this message — '
            'open it in Gmail (button below) to read the full content. Manually-written '
            "support replies and Loz's outbound emails have full bodies; automated "
            'notifications (prescription paid, DPD updates, payment receipts) do not.</p>'
            '</div>'
        )
    return f'''
  <div class="row-expanded">
    <dl class="meta-grid">
      <dt>From</dt><dd>{esc(r['from'])}</dd>
      <dt>To</dt><dd>{esc(r['to'])}</dd>
      <dt>Date</dt><dd>{esc(fmt_full(r['date']))}</dd>
      <dt>Direction</dt><dd>{esc(r['direction'])}</dd>
      <dt>Category</dt><dd><span class="tag {cat_class(r['category'])}">{esc(r['category'])}</span></dd>
      <dt>Msg ID</dt><dd><code>{esc(r['id'])}</code></dd>
    </dl>
    <div class="block-label">Summary (auto-generated)</div>
    <p class="summary-text">{esc(r['summary'])}</p>
    {body_html}
    <div class="row-notes" data-notes-for="{esc(r['id'])}">
      <div class="block-label">Your notes <span class="muted small">(saved locally when JS is on)</span></div>
      <textarea class="note-inline" data-id="{esc(r['id'])}" placeholder="Add a private note…"></textarea>
    </div>
    <div class="row-actions">
      <a class="gm-btn" href="{esc(r['url'])}" target="_blank" rel="noopener">↗ Open this email in Gmail</a>
    </div>
  </div>
'''

row_html_parts = []
for r in rows:
    dir_short = "IN" if r["direction"] == "Inbound" else "OUT"
    has_body_dot = '<span class="has-body" title="Full body available">●</span>' if BODIES.get(r["id"]) else ""
    row_html_parts.append(f'''
<details class="row" data-id="{esc(r['id'])}" data-cat="{esc(r['category'])}" data-dir="{esc(r['direction'])}" data-date="{esc(r['date'])}">
  <summary class="row-summary">
    <button class="star" data-act="star" data-id="{esc(r['id'])}" title="Star" type="button">☆</button>
    <button class="flag" data-act="flag" data-id="{esc(r['id'])}" title="Flag" type="button">🚩</button>
    <div class="meta">
      <span class="when">{esc(fmt_short(r['date']))}</span>
      <span class="dir {esc(r['direction'])}">{dir_short}</span>
      <span class="tag {cat_class(r['category'])} cat-tag">{esc(r['category'])}</span>
      {has_body_dot}
    </div>
    <div class="sub">
      <div class="subj">{esc(r['subject'])}</div>
      <div class="snip">{esc(r['summary'])}</div>
    </div>
    <span class="chev-marker">▸</span>
  </summary>{render_body(r)}</details>''')
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

# ─── Methodology / backend transparency page ───
generated_at = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
bodies_count = len(BODIES)
by_cat_sorted = sorted(cat_count.items(), key=lambda kv: -kv[1])
by_sender = Counter(r["from"] for r in records).most_common(15)

methodology_html = f'''
<div class="meth">
  <div class="meth-card">
    <h2>How this report was built</h2>
    <p class="muted">Generated {esc(generated_at)} from the lozturner@gmail.com inbox.</p>
    <ol>
      <li>Gmail was searched for every thread mentioning <code>Releaf</code> (and <code>releaf.co.uk</code>) using the Gmail API
        via the Claude MCP <code>search_threads</code> tool. All result pages were paginated.</li>
      <li>Each matching thread was inspected; every individual message was extracted to a row in this report.
        Surrounding emails — DPD delivery notifications, Stripe payment-failure alerts,
        PayPal/Curve receipts, Google Calendar invites, and Loz's own outbound replies —
        were included so the relationship is visible in context.</li>
      <li>{bodies_count} of the more substantive threads were re-fetched with <code>get_thread</code> in
        <code>FULL_CONTENT</code> mode to capture the full body text (manually-written support
        replies, complaints, GP correspondence, Loz's outbound emails). Automated emails
        kept only their Gmail snippet because the snippet is essentially the whole template.</li>
      <li>Categories were assigned heuristically from subject lines and senders. Summaries
        were written from the Gmail snippet plus any full body that was fetched.</li>
      <li>The whole dataset is embedded in this single HTML file as a JSON literal — see
        the <em>Raw data</em> block at the bottom of this page. The same data is exported
        as <code>releaf_emails_chronology.csv</code> alongside this file.</li>
    </ol>
  </div>

  <div class="meth-card">
    <h3>Numbers</h3>
    <ul class="kv">
      <li><strong>Total messages indexed:</strong> {len(records)}</li>
      <li><strong>Distinct categories:</strong> {len(by_cat_sorted)}</li>
      <li><strong>Full bodies fetched:</strong> {bodies_count}</li>
      <li><strong>Date range:</strong> {esc(records[0]['date'][:10]) if records else '—'} → {esc(records[-1]['date'][:10]) if records else '—'}</li>
      <li><strong>Inbound:</strong> {sum(1 for r in records if r['direction']=='Inbound')}</li>
      <li><strong>Outbound from Loz:</strong> {sum(1 for r in records if r['direction']=='Outbound')}</li>
    </ul>
  </div>

  <div class="meth-card">
    <h3>Top senders</h3>
    <table class="meth-tbl">
      <thead><tr><th>Sender</th><th style="text-align:right">Emails</th></tr></thead>
      <tbody>
        {"".join(f'<tr><td><code>{esc(s)}</code></td><td style="text-align:right">{n}</td></tr>' for s, n in by_sender)}
      </tbody>
    </table>
  </div>

  <div class="meth-card">
    <h3>All categories</h3>
    <table class="meth-tbl">
      <thead><tr><th>Category</th><th style="text-align:right">Count</th></tr></thead>
      <tbody>
        {"".join(f'<tr><td><span class="tag {cat_class(c)}">{esc(c)}</span></td><td style="text-align:right">{n}</td></tr>' for c, n in by_cat_sorted)}
      </tbody>
    </table>
  </div>

  <div class="meth-card">
    <h3>Source code</h3>
    <p>The pipeline that built this report is in the repo on branch
    <code>claude/email-chronology-report-fqunL</code>:</p>
    <ul class="kv">
      <li><code>build_releaf_csv.py</code> — defines the 429-row dataset and writes the CSV</li>
      <li><code>build_app.py</code> — stitches the data + bodies into this HTML</li>
      <li><code>app_template.html</code> — the page template (CSS + JS)</li>
      <li><code>email_bodies.json</code> — full body text for fetched messages</li>
    </ul>
  </div>

  <div class="meth-card">
    <h3>Raw data (JSON)</h3>
    <p class="muted small">All {len(records)} records as embedded in this page. Click to expand.</p>
    <details>
      <summary class="small muted">Show raw JSON ({len(json.dumps(records, ensure_ascii=False)):,} chars)</summary>
      <pre class="raw-json">{esc(json.dumps(records, ensure_ascii=False, indent=2))}</pre>
    </details>
  </div>
</div>
'''
out = (tpl
    .replace("__DATA_JSON__", json.dumps(records, ensure_ascii=False))
    .replace("__INITIAL_LIST__", initial_list)
    .replace("__GANTT_HTML__", gantt_html)
    .replace("__METHODOLOGY_HTML__", methodology_html)
    .replace("__BODIES_COUNT__", str(bodies_count))
    .replace("__TOTAL__", str(len(records)))
    .replace("__FIRST_MONTH__", month_label(months_set[0]))
    .replace("__LAST_MONTH__", month_label(months_set[-1]))
)
target = HERE / "releaf_chronology.html"
target.write_text(out, encoding="utf-8")
print(f"Wrote {target} ({len(out):,} bytes, {len(records)} records, {len(months_set)} months)")
