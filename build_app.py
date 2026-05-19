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
      <button class="pin-btn" data-pin-id="{esc(r['id'])}" type="button">📌 Add to my chronology</button>
      <a class="gm-btn" href="{esc(r['url'])}" target="_blank" rel="noopener">↗ Open in Gmail</a>
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

# ─── System chronology: a narrative analysis of the relationship ───
# Phases are derived from the email pattern in the data: onboarding,
# GP friction, first prescription, vape/address issues, the October
# undispatched-order incident, the partial-refund dispute, the
# tech-failed consultation, the formal complaints, then the May 2026
# resolution + Big Narstie alternative.

def ref(*ids):
    """Inline references to messages — JS turns these into clickable links."""
    return " ".join(f'<a class="chron-ref" data-ref-id="{i}">↗</a>' for i in ids if i)

system_chronology_html = f'''
<div class="chron-narrative">
  <div class="chron-header">
    <h2>The Releaf story — generated narrative</h2>
    <p class="muted">An AI-written timeline of what happened, derived from the {len(records)} emails in this dataset. The small ↗ markers link to the specific email they reference; click one to open it.</p>
  </div>

  <section class="chron-phase">
    <header><span class="chron-when">Apr – Jun 2024</span><h3>First contact &amp; recruitment</h3></header>
    <p>Releaf reaches out before you are a patient. On <strong>30 Apr 2024</strong> Graham — described as "one of the team here at Releaf and a registered mental health nurse" — notices you wanted to speak to a doctor about alternative ADHD treatment {ref("18f2f692b01d85f6")}. The next two months are marketing-only: a new website launch in May, the UK-first Glass Pharms cultivars in June {ref("19002d9738a8c6de", "1907870c8417278b")}. Charlene follows up in July with a £50 voucher (code <code>50OFF</code>) for your initial consultation, then a reminder before it expires {ref("19092f8e12be590b", "190a1a8771c8397f")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Nov 2024</span><h3>Onboarding hits the GP wall</h3></header>
    <p>You sign up on <strong>14 Nov 2024</strong>; initial consultation booked, ID verified, health questionnaire submitted {ref("1932b34775460730", "1932bc6f43696d1f")}. Almost immediately Releaf can't get your Summary of Care: on the 15th they say AILSA isn't recognised; on the 21st they try "phl adhd" and that isn't recognised either {ref("1933006f74d74122", "1934e0a4e1e35052")}. You call. By the 25th the GP details have been updated on their system {ref("19363e698cd3027a")}, but a 27 Nov "we need some more information" goes out anyway {ref("1936ed932d216b93")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Dec 2024 – Jan 2025</span><h3>Missed initial consultations</h3></header>
    <p>The 2 Dec consultation is missed; Releaf sends both an automated "we missed you" and a manual rebook offer the same morning {ref("1938688c89661119", "193873747eb631b8")}. On Christmas Eve, support emails Hillview Surgery directly to chase your records and CCs you {ref("193f9657bfb1e1ce", "193f96587f7ac47a")}. You thank them. January is similar — two more missed-you emails on the 24th and 25th {ref("19498d744a2a6d2b", "1949d2a477c14548")}, then on the 28th you finally get into the video appointment after support agents talk you through joining via the patient dashboard {ref("194acef57b7ff666")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Jan – Feb 2025</span><h3>First prescription</h3></header>
    <p>Your first treatment plan lands on <strong>28 Jan 2025</strong> {ref("194ad40459fdbc80")}. The next morning support needs proof of address before they can ship — you provide it the following day; Liberty/Natalie confirms deliveries will go to 5 Nursery Road, Woking GU21 2NN {ref("194b2381369725f0", "194b7fd27176fc7b")}. Your Medical Cannabis Card ships 3 Feb, and the same evening 4C Labs TB-T20 (Tangerine) flower goes out — the first actual medication delivery {ref("194ccddaef3c885b", "194d040331661dd3")}. A second follow-up is booked for the 14th, leading to another prescription and a psychiatrist appointment scheduled for 14 Mar {ref("19504fb1e8ac6e95")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Mar – Jun 2025</span><h3>Steady-state monthly rhythm</h3></header>
    <p>The psychiatrist appointment on 14 Mar is missed {ref("195943f3ae0a78d1")}. You rebook for 25 Mar, attend that one, and from there the cadence stabilises: SOMAÍ T50 oil ships 27 Mar, GK-T25 flower in April, BNB-T26 (Bonne) in May, Pucker Up and Lemonatti in June. Each month follows the same pattern — prescription approved → paid → shipped → DPD delivery (typically by Adrian, Nuradin, or SANAMPREET). A 31 May consult with Dr David Pang completes the second follow-up cycle {ref("1971b608c83dc42a")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Jul 2025</span><h3>Vape battery + urgent address change</h3></header>
    <p>15 Jul becomes the busiest support day. You order a vape; you've also vacated 10 Burriton House and an old card was still pointing there, so you fire an urgent <em>"do not send to my billing address"</em> email {ref("1980e356b5bcc009")}. Over six follow-ups across 16 Jul you double-check the delivery address is the new Woking flat, then ask whether the battery is included with the vape, then ask them to halt delivery if it isn't because you'd "spent all the money I have of my disability to get this" {ref("198125c53369405d", "198125cd30856d38", "19812b98876c37cb")}. Natalie confirms the delivery address; Harvey confirms the first vape order includes the battery and subsequent orders are just cartridges {ref("198122c220eda605", "19812442e80b7445")}. You apologise for the messy thread and accept the answer. Three weeks later the battery is shipped as a separate shop order {ref("19874487d0fba605")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Aug – Sep 2025</span><h3>Missed appointments, resolutions team appears</h3></header>
    <p>You miss the 14 Aug follow-up with Dr Michal Modestowicz and rebook a few hours later {ref("198a9373345117b1")}. The next consultation is missed too — this time the Resolutions team reaches out directly on 21 Aug; agent rebooks you with Dr Imran for 27 Aug 15:00 {ref("198cc1b73a5fc6b2")}. 10 Sep consult lands without incident.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Oct 2025</span><h3>The undispatched-order incident</h3></header>
    <p>The first major service failure. <strong>1 Oct:</strong> you email asking where your order is, attaching the live-chat transcript {ref("199a020eee664297")}. Emily replies the next morning saying she can't see why it's delayed and is escalating as urgent {ref("199a44606def09ea")}. The same afternoon Stripe issues a refund — <code>#3202-8689</code> — and a re-initial consultation has reactivated the script {ref("199a5970a1e83cb2")}. You write back asking for an ETA on the actual medication. By 6 Oct, still nothing has moved; you send a harder follow-up flagging that Emily marked it urgent on Thursday and you'd phoned support that day too {ref("199b962ac8dac981")}. <em>Fifteen minutes after that email</em>, the order goes out the door — and you note the timestamps in your reply, suggesting human pressure was needed {ref("199b997a8ee5ebf2")}. Releaf updates their Patient Terms re: chargebacks and disputes later that month {ref("19a30ed0a0bdd385")}, and the first Stripe failures (£154.98) start hitting at the end of October {ref("19a2b202e608ef55")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Nov 2025</span><h3>The £30.99 partial-refund debate</h3></header>
    <p>On 19 Nov, after a successful consultation with Rachel McCusker {ref("19a9bb3679db5a8b")}, Emily Creighton emails to acknowledge dissatisfaction has been reported and wants to resolve it {ref("19a9ca7b289d859e")}. You reply with the prior thread attached, noting an earlier partial refund had been "a bit odd" {ref("19a9d26c5a060b06")}. Emily comes back on the 24th confirming her colleague Liberty had processed the £30.99 refund on 6/10 {ref("19ab6b53f89bcdb8")}. You forward the chain to your advocate Tasia the same evening {ref("19ab80a122e3d321")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Dec 2025</span><h3>Tech-failed consultation, appointment moved without notice</h3></header>
    <p>18 Dec 14:45 — consultation with Emma Hopkins. You log in on time but hit significant technical issues and can't connect {ref("19b3219a5cd9ce63")}. Rebekah confirms a rebook to 21 Dec 08:30 {ref("19b365511d62f256")}. Then, without telling you, the appointment is cancelled and moved again to <strong>3 Jan 2026 07:30</strong> {ref("19b3ad55a83837ef", "19b3aed59d48ce18")}. You email back with a screenshot: "you've moved the appointment again without telling me… I need you guys to explain what's going on" {ref("19b3ae9973426d8c")}. Releaf's response on the 22nd claims a colleague phoned you on 20 Dec to discuss the change — a claim you dispute {ref("19b46770bc6c68e2")}. Throughout December Stripe is failing repeatedly on the £79.99 and £39.99 charges.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Jan 2026</span><h3>Formal complaints filed</h3></header>
    <p>The 3 Jan 07:30 consultation goes ahead with Dr Haroon Hamid. Two weeks later, on <strong>16 Jan</strong>, you draft two formal complaints {ref("19bc7586a6b76bfd", "19bc759a86c583bc")}. <em>DRAFT 1</em> is the subscription-payment-error refund demand, written with help from advocate Natasha. <em>DRAFT 2</em> escalates the broader pattern — "ongoing pattern of errors affecting my care" — specifically that the 3 Jan consultation notes don't reflect what was agreed and approved. Stripe failures on the £39.99 Releaf+ subscription continue all month {ref("19bd075ea657ae14", "19be76b94ccb6764")}.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Feb 2026</span><h3>GP issue resurfaces</h3></header>
    <p>11 Feb: Releaf says the GP notification letter has been returned undeliverable — the practice records you as no longer registered {ref("19c4de5143aca167")}. Twelve days later they chase again; no update has come back {ref("19c8b07f3e6f543d")}. This is the same problem from Nov 2024, fifteen months later.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">Apr 2026</span><h3>You build a subscription tracker</h3></header>
    <p>RELEAF charges £39.99 again via PayPal on 6 Apr {ref("19d609cdc31695b7")}. Within hours you send yourself two notes: <em>ACTION REQUIRED: build subscription tracking system NOW</em>, and a wrap-up confirming the system is live {ref("19d6385e021e46a9", "19d638c30aa8b4d2")}. April otherwise runs smoothly — Strawberry Cake, Citroli, Wedding Cake Crash, D. Burger all ship.</p>
  </section>

  <section class="chron-phase">
    <header><span class="chron-when">May 2026</span><h3>Looking elsewhere — and a refund</h3></header>
    <p>On <strong>12 May</strong> you contact Big Narstie Medical. You confirm you've completed the eligibility form and ask about transferring from Releaf {ref("19e1bc827239f7e6")}. They request ID, proof of address, and a Brief Summary of Care; you upload documents the same hour {ref("19e1bd01111b9915")}; they reject one because it's not a proper Summary of Care {ref("19e1bd3a29a6a1b7")}.</p>
    <p>Meanwhile Releaf is changing too. On 13 May, Dr Sue Clenton emails about "exciting news about your follow-up care" — a shorter form-based follow-up that doesn't require a doctor {ref("19e227ca5e6bb495")}. The next day the health questionnaire flags that you need a consultation before your reorder can continue {ref("19e2538fdc6f7dc4")}. You raise a concern via the contact form on the 15th — auto-confirmed {ref("19e2b9c35c2c3f3e")}.</p>
    <p>On <strong>18 May</strong> things move fast. Your concern is escalated to the Resolutions Team {ref("19e3aa4a22944a5c")}. Hours later, Natasha Long confirms a <strong>20% refund of £30.99</strong> has been processed — ARN <code>74208475276100096508449</code> — and asks for product/batch/photos {ref("19e3b02d58848147")}. The 22 May consultation is amended to 07:30 {ref("19e38fcfa532e8a6")}, then on the 19th moved one more time to 21 May 13:45 with Renae Carney {ref("19e401d583254f98", "19e40446e3d7052b")}. As of today (the date this report was generated), that's the next appointment on the calendar.</p>
  </section>

  <section class="chron-phase chron-summary">
    <header><h3>What the data shows in aggregate</h3></header>
    <p>Over two years and a month, the Releaf account ran through 449 messages. The medication side worked — prescriptions arrived, allowances renewed monthly. The friction was administrative: GP records that never properly registered (Nov 2024, again Feb 2026), one undispatched order that needed escalation (Oct 2025), one tech-failed consultation that triggered a moved-without-notice rebook (Dec 2025), and a long-running dispute over a subscription charge that ultimately resulted in two partial refunds (Oct 2025 £30.99, May 2026 £30.99). Three formal grievances — Oct 2025 hospital-A&amp;E grievance letter, Jan 2026 DRAFTs 1 &amp; 2, May 2026 contact-form escalation — each produced a Resolutions-team response and a refund, but the underlying pattern (GP records, payment glitches, calendar reschedules) kept recurring. By May 2026 you've reached the point of contacting Big Narstie Medical to evaluate moving the prescription elsewhere.</p>
  </section>
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
    .replace("__SYSTEM_CHRONOLOGY_HTML__", system_chronology_html)
    .replace("__BODIES_COUNT__", str(bodies_count))
    .replace("__TOTAL__", str(len(records)))
    .replace("__FIRST_MONTH__", month_label(months_set[0]))
    .replace("__LAST_MONTH__", month_label(months_set[-1]))
)
target = HERE / "releaf_chronology.html"
target.write_text(out, encoding="utf-8")
print(f"Wrote {target} ({len(out):,} bytes, {len(records)} records, {len(months_set)} months)")
