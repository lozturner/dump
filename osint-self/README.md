# osint-self

Local-only pipeline for turning your own Google Takeout mail export into a
searchable, visualized archive. Nothing leaves your machine. No scraping, no
third-party APIs, no cloud calls.

Purpose: help you (the data subject) find specific moments in your own inbox
that you want to reference — for a solicitor, a DV caseworker, a therapist, or
your own recall — when executive function / stroke recovery / ADHD / autism
make scrolling through ten years of mail impractical.

## What it produces

- A parquet table of every message: sender, recipients, date, subject, body,
  thread id, attachment flag.
- Contact normalization (same person across multiple addresses).
- Thread reconstruction via `In-Reply-To` / `References` headers.
- Per-message signals: VADER sentiment, intensity, time-of-day bucket,
  user-defined regex tags (threats, locations, finance, child-related, etc.).
- Burst detection: 322-messages-in-one-night type patterns, with timestamps.
- Gap detection: long silences followed by resumption.
- Dark-mode HTML dashboard (plotly) with heatmaps, timeline scatter, per-contact
  volume, sentiment over time, and a searchable message table.

## What it does NOT produce

A ranked judgment of named individuals. Sentiment and volume per contact are
measurements, not verdicts. If you want a "who was right" scorecard, build it
by hand with your solicitor — don't let an LLM generate it from one side of an
archive. It will be used against you.

## Phase 0 — Export your data

1. Go to <https://takeout.google.com>.
2. Deselect all, then select **Mail**.
3. Format: `.mbox`. Delivery: download link.
4. Wait for the email, download the `.zip`, extract. You'll get
   `All mail Including Spam and Trash.mbox` (usually big — multi-GB is normal).
5. Copy it to `osint-self/data/mail.mbox` (or pass a custom path with `--mbox`).

## Phase 1..4 — Run the pipeline

```bash
cd osint-self
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/01_ingest_mbox.py --mbox data/mail.mbox --out output/messages.parquet
python scripts/02_normalize.py --in output/messages.parquet --out output/messages_norm.parquet
python scripts/03_signals.py   --in output/messages_norm.parquet --tags config/tags.example.yaml --out output/messages_signals.parquet
python scripts/04_dashboard.py --in output/messages_signals.parquet --out output/dashboard.html
```

Open `output/dashboard.html` in any browser.

## Configuring tags

Copy `config/tags.example.yaml` to `config/tags.yaml` and edit. Each tag is a
regex or keyword list you care about. Example categories: threats, location
mentions, financial, child-related, apologies, denials. These drive the
dashboard filters.

## Data safety

- `data/` and `output/` are gitignored. Do not commit personal data.
- Run on a machine only you access. Full-disk encryption recommended.
- If a solicitor asks for specific messages, export the relevant rows to PDF
  from the dashboard — don't hand them the whole parquet.

## Re-use / extend

Everything is pandas + plotly. You can open the parquet in a notebook and
pivot however you like. The scripts are intentionally short and readable.
