"""Phase 6: review & oversight HTML.

Generates a self-contained page with:
- Top bar of external quick-links (Gmail, Takeout, Account activity, etc.)
- Review checklist (areas to cover) with localStorage-persisted checkboxes
- Per-counterparty section with per-contact progress + summary numbers
- Message table with [open in Gmail] deep links and a "reviewed" checkbox
  per row — state persists in localStorage keyed by message_id

Uses Gmail's rfc822msgid: search operator to jump straight to a message by
Message-ID. Only works while signed into the right Google account in the
browser.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path
from urllib.parse import quote

import pandas as pd


EXTERNAL_LINKS = [
    ("Gmail inbox",            "https://mail.google.com/mail/u/0/#inbox"),
    ("Gmail — sent",           "https://mail.google.com/mail/u/0/#sent"),
    ("Gmail — all mail",       "https://mail.google.com/mail/u/0/#all"),
    ("Gmail — advanced search","https://mail.google.com/mail/u/0/#advanced-search"),
    ("Google Takeout",         "https://takeout.google.com/"),
    ("Account activity",       "https://myaccount.google.com/security"),
    ("Recent security events", "https://myaccount.google.com/notifications"),
    ("Data & privacy",         "https://myaccount.google.com/data-and-privacy"),
]


DEFAULT_CHECKLIST = [
    ("Export", [
        "Takeout export downloaded and extracted",
        "mbox copied to data/mail.mbox",
        "SHA256 of mbox recorded for chain-of-custody",
    ]),
    ("Ingest", [
        "Phase 1 parsed without parse errors",
        "Row count matches expected order of magnitude",
        "Date range covers the period of interest",
    ]),
    ("Normalize", [
        "Own addresses listed via --me",
        "Alias map reviewed (config/contacts.yaml)",
        "Spot-checked 5 random threads for correct reconstruction",
    ]),
    ("Signals", [
        "Tag YAML customised for personal vocabulary and locations",
        "Burst threshold calibrated (review a known event)",
        "Sentiment spot-checked on 10 random messages",
    ]),
    ("Review per contact", [
        "Timeline sanity-checked against memory",
        "Night-message rate reviewed",
        "Burst windows opened in Gmail for context",
        "Relevant attachments exported separately",
    ]),
    ("Handover", [
        "Solicitor brief written (anonymised P1..Pn)",
        "Source message IDs cross-referenced in brief",
        "Backup of output/ kept on encrypted drive",
    ]),
]


def gmail_search_url(message_id: str) -> str:
    mid = message_id.strip("<> ")
    if not mid:
        return ""
    q = quote(f"rfc822msgid:{mid}", safe="")
    return f"https://mail.google.com/mail/u/0/#search/{q}"


def gmail_from_search(addr: str) -> str:
    q = quote(f"from:{addr}", safe="")
    return f"https://mail.google.com/mail/u/0/#search/{q}"


def render(df_msgs: pd.DataFrame, df_contacts: pd.DataFrame | None) -> str:
    df = df_msgs.dropna(subset=["date"]).sort_values("date", ascending=False).copy()

    ext_links_html = "\n".join(
        f'<a class="chip" href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(n)}</a>'
        for n, u in EXTERNAL_LINKS
    )

    checklist_html = ""
    for section, items in DEFAULT_CHECKLIST:
        lis = "\n".join(
            f'<li><label><input type="checkbox" data-key="cl:{html.escape(section)}:{i}">'
            f' {html.escape(item)}</label></li>'
            for i, item in enumerate(items)
        )
        checklist_html += f'<section><h3>{html.escape(section)}</h3><ul>{lis}</ul></section>'

    if df_contacts is not None and not df_contacts.empty:
        cols = [c for c in [
            "counterparty", "n_total", "n_in", "n_out",
            "avg_sentiment_in", "pct_negative_in", "pct_night_in",
            "n_bursts_in", "longest_silent_gap_days",
            "first_seen", "last_seen",
        ] if c in df_contacts.columns]
        contact_rows = []
        for _, r in df_contacts.sort_values("n_total", ascending=False).iterrows():
            cp = r["counterparty"]
            tds = []
            for c in cols:
                v = r[c]
                if isinstance(v, float):
                    v = f"{v:.2f}"
                elif isinstance(v, pd.Timestamp):
                    v = v.strftime("%Y-%m-%d")
                tds.append(f"<td>{html.escape(str(v))}</td>")
            tds.append(
                f'<td><a class="mini" target="_blank" rel="noopener" '
                f'href="{html.escape(gmail_from_search(cp))}">open in gmail</a></td>'
            )
            tds.append(
                f'<td><input type="checkbox" data-key="cp:{html.escape(cp)}"></td>'
            )
            contact_rows.append("<tr>" + "".join(tds) + "</tr>")
        header = "".join(f"<th>{c}</th>" for c in cols) + "<th>link</th><th>done</th>"
        contacts_html = (
            f"<table><thead><tr>{header}</tr></thead>"
            f"<tbody>{''.join(contact_rows)}</tbody></table>"
        )
    else:
        contacts_html = "<p><em>No per-contact summary found. Run Phase 5.</em></p>"

    rows = []
    for _, r in df.head(3000).iterrows():
        mid = r.get("message_id", "")
        link = gmail_search_url(mid)
        subject = (r.get("subject") or "")[:140]
        tags = ", ".join(r.get("tags") or []) if isinstance(r.get("tags"), list) else ""
        sent = r.get("sentiment")
        sent_s = f"{sent:.2f}" if isinstance(sent, (int, float)) and sent == sent else ""
        date_s = r["date"].strftime("%Y-%m-%d %H:%M")
        link_html = (
            f'<a class="mini" target="_blank" rel="noopener" href="{html.escape(link)}">open</a>'
            if link else ""
        )
        rows.append(
            "<tr>"
            f'<td>{html.escape(date_s)}</td>'
            f'<td>{html.escape(str(r.get("direction","")))}</td>'
            f'<td>{html.escape(str(r.get("counterparty","")))}</td>'
            f'<td>{html.escape(subject)}</td>'
            f'<td>{html.escape(sent_s)}</td>'
            f'<td>{html.escape(tags)}</td>'
            f'<td>{link_html}</td>'
            f'<td><input type="checkbox" data-key="msg:{html.escape(mid)}"></td>'
            "</tr>"
        )
    msg_table_header = "".join(
        f"<th>{c}</th>" for c in
        ["date", "dir", "counterparty", "subject", "sent", "tags", "gmail", "reviewed"]
    )
    msg_table_html = (
        f'<input id="q" placeholder="filter rows..." oninput="filterRows()"/>'
        f"<table id=\"t\"><thead><tr>{msg_table_header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )

    counts = {
        "messages": int(len(df)),
        "contacts": int(df["counterparty"].replace("", pd.NA).dropna().nunique()),
        "date_min": str(df["date"].min().date()) if len(df) else "",
        "date_max": str(df["date"].max().date()) if len(df) else "",
    }

    style = """
    <style>
      :root { color-scheme: dark; }
      body { background: #0b0d10; color: #e6e6e6;
             font-family: -apple-system, system-ui, sans-serif; margin: 16px; }
      h1, h2, h3 { font-weight: 500; }
      .chip { display: inline-block; padding: 6px 10px; margin: 4px 6px 4px 0;
              border: 1px solid #333; border-radius: 20px; color: #e6e6e6;
              text-decoration: none; background: #14181c; font-size: 13px; }
      .chip:hover { background: #1e252b; }
      section { border: 1px solid #1d2125; border-radius: 10px;
                padding: 12px 16px; margin: 12px 0; background: #0f1215; }
      ul { list-style: none; padding: 0; }
      ul li { margin: 4px 0; }
      input[type=checkbox] { accent-color: #4a9eff; }
      table { border-collapse: collapse; width: 100%; font-size: 12px; margin-top: 8px; }
      th, td { border-bottom: 1px solid #222; padding: 4px 8px; text-align: left; vertical-align: top; }
      thead th { position: sticky; top: 0; background: #111; }
      input#q { background: #111; color: #eee; border: 1px solid #333; padding: 8px;
                width: 100%; margin: 12px 0; }
      a.mini { color: #4a9eff; text-decoration: none; }
      a.mini:hover { text-decoration: underline; }
      .stats { display: flex; gap: 16px; flex-wrap: wrap; margin: 8px 0; }
      .stat { background: #14181c; padding: 8px 12px; border-radius: 8px;
              border: 1px solid #222; font-size: 13px; }
    </style>
    """

    script = """
    <script>
      // Persist checkbox state in localStorage keyed by data-key.
      const STORAGE_KEY = 'osint-self-review';
      function loadState() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
        catch (e) { return {}; }
      }
      function saveState(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
      const state = loadState();
      document.addEventListener('DOMContentLoaded', () => {
        for (const box of document.querySelectorAll('input[type=checkbox][data-key]')) {
          const k = box.dataset.key;
          if (state[k]) box.checked = true;
          box.addEventListener('change', () => {
            state[k] = box.checked;
            if (!box.checked) delete state[k];
            saveState(state);
            updateProgress();
          });
        }
        updateProgress();
      });
      function updateProgress() {
        const all = document.querySelectorAll('input[type=checkbox][data-key^="cl:"]');
        const done = [...all].filter(b => b.checked).length;
        const el = document.getElementById('progress');
        if (el) el.textContent = `${done} / ${all.length} checklist items done`;
      }
      function filterRows() {
        const q = document.getElementById('q').value.toLowerCase();
        for (const tr of document.querySelectorAll('#t tbody tr')) {
          tr.style.display = tr.innerText.toLowerCase().includes(q) ? '' : 'none';
        }
      }
      function exportState() {
        const blob = new Blob([JSON.stringify(loadState(), null, 2)],
                              {type: 'application/json'});
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'review-state.json';
        a.click();
      }
      function clearState() {
        if (confirm('Clear all checkbox state?')) {
          localStorage.removeItem(STORAGE_KEY);
          location.reload();
        }
      }
    </script>
    """

    stats_html = "".join(
        f'<div class="stat"><b>{html.escape(str(v))}</b> {html.escape(k)}</div>'
        for k, v in counts.items()
    )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>osint-self — review & oversight</title>{style}</head>
<body>
  <h1>osint-self — review & oversight</h1>
  <div class="stats">{stats_html}
    <div class="stat" id="progress">0 / 0</div>
    <div class="stat"><a class="mini" href="#" onclick="exportState();return false;">export state</a></div>
    <div class="stat"><a class="mini" href="#" onclick="clearState();return false;">clear state</a></div>
  </div>

  <section><h2>External tools</h2>{ext_links_html}</section>

  <h2>Review checklist</h2>
  {checklist_html}

  <h2>Per counterparty</h2>
  {contacts_html}

  <h2>Messages (latest {min(len(df),3000):,})</h2>
  <p><em>"open" opens the message in Gmail via rfc822msgid search. You must be
  signed into the right Google account.</em></p>
  {msg_table_html}

  {script}
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--messages", required=True, type=Path,
                    help="parquet from Phase 3 (messages_signals)")
    ap.add_argument("--contacts", type=Path,
                    help="optional parquet from Phase 5 (per_contact)")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    df_msgs = pd.read_parquet(args.messages)
    df_contacts = pd.read_parquet(args.contacts) if args.contacts and args.contacts.exists() else None

    out_html = render(df_msgs, df_contacts)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_html, encoding="utf-8")
    print(f"wrote review page -> {args.out}")


if __name__ == "__main__":
    main()
