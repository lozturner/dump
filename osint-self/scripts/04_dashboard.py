"""Phase 4: dark-mode plotly dashboard.

Renders a single self-contained HTML file with:
- Volume over time (by direction)
- Per-counterparty volume (top N)
- Hour-of-day x day-of-week heatmap
- Sentiment over time (rolling mean) per top counterparty
- Burst events (scatter, marker-sized by messages-in-window)
- Tag frequency bar
- Searchable message table (subject + snippet + tags + sentiment)

Nothing in this file produces a per-person judgment. It produces measurements.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0b0d10",
    plot_bgcolor="#0b0d10",
    font=dict(color="#e6e6e6"),
)


def fig_volume(df: pd.DataFrame) -> go.Figure:
    v = df.assign(d=df["date"].dt.date).groupby(["d", "direction"]).size().reset_index(name="n")
    fig = go.Figure()
    for direction in ("in", "out"):
        sub = v[v["direction"] == direction]
        fig.add_trace(go.Scatter(x=sub["d"], y=sub["n"], mode="lines",
                                 name=direction, stackgroup="one"))
    fig.update_layout(title="Volume over time (stacked, in vs out)", **DARK)
    return fig


def fig_top_contacts(df: pd.DataFrame, n: int = 20) -> go.Figure:
    top = (df[df["counterparty"] != ""]
           .groupby(["counterparty", "direction"]).size().unstack(fill_value=0))
    top["total"] = top.sum(axis=1)
    top = top.sort_values("total", ascending=True).tail(n)
    fig = go.Figure()
    for direction in ("in", "out"):
        if direction in top.columns:
            fig.add_trace(go.Bar(y=top.index, x=top[direction], name=direction, orientation="h"))
    fig.update_layout(barmode="stack", title=f"Top {n} counterparties (message count)", **DARK)
    return fig


def fig_heatmap(df: pd.DataFrame) -> go.Figure:
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    piv = (df.groupby(["dow", "hour_local"]).size()
             .unstack(fill_value=0).reindex(dow_order))
    fig = go.Figure(data=go.Heatmap(
        z=piv.values, x=piv.columns, y=piv.index, colorscale="Inferno"))
    fig.update_layout(title="Hour-of-day x day-of-week (all messages)",
                      xaxis_title="hour (local)", yaxis_title="", **DARK)
    return fig


def fig_sentiment(df: pd.DataFrame, top_n: int = 6) -> go.Figure:
    top_contacts = (df[df["counterparty"] != ""]
                    .groupby("counterparty").size()
                    .sort_values(ascending=False).head(top_n).index.tolist())
    fig = go.Figure()
    for cp in top_contacts:
        sub = df[df["counterparty"] == cp].sort_values("date")
        if len(sub) < 10:
            continue
        rolling = sub.set_index("date")["sentiment"].rolling("30D").mean()
        fig.add_trace(go.Scatter(x=rolling.index, y=rolling.values,
                                 mode="lines", name=cp))
    fig.update_layout(title="Sentiment over time (30-day rolling mean, top contacts)",
                      yaxis_range=[-1, 1], **DARK)
    return fig


def fig_bursts(df: pd.DataFrame) -> go.Figure:
    bursts = df[df["burst"]].copy()
    if bursts.empty:
        fig = go.Figure()
        fig.update_layout(title="Bursts (none detected at current threshold)", **DARK)
        return fig
    fig = go.Figure(go.Scatter(
        x=bursts["date"], y=bursts["counterparty"],
        mode="markers",
        marker=dict(size=8, opacity=0.6),
        text=bursts["subject"].fillna(""),
        hovertemplate="%{x}<br>%{y}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(title="Burst events (messages in dense windows)", **DARK)
    return fig


def fig_tags(df: pd.DataFrame) -> go.Figure:
    exploded = df.explode("tags")
    counts = exploded["tags"].dropna().value_counts()
    fig = go.Figure(go.Bar(x=counts.index, y=counts.values))
    fig.update_layout(title="Tag frequency", **DARK)
    return fig


def table_html(df: pd.DataFrame, limit: int = 2000) -> str:
    cols = ["date", "direction", "counterparty", "subject", "sentiment", "burst", "tags"]
    d = df.sort_values("date", ascending=False).head(limit)[cols].copy()
    d["date"] = d["date"].dt.strftime("%Y-%m-%d %H:%M")
    d["subject"] = d["subject"].fillna("").str.slice(0, 120)
    d["tags"] = d["tags"].map(lambda t: ", ".join(t) if isinstance(t, list) else "")
    d["sentiment"] = d["sentiment"].round(2)
    rows = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row) + "</tr>"
        for row in d.itertuples(index=False, name=None)
    )
    header = "".join(f"<th>{c}</th>" for c in cols)
    return f"""
<input id="q" placeholder="filter rows..." oninput="filterRows()" />
<table id="t">
  <thead><tr>{header}</tr></thead>
  <tbody>{rows}</tbody>
</table>
<script>
function filterRows() {{
  const q = document.getElementById('q').value.toLowerCase();
  for (const tr of document.querySelectorAll('#t tbody tr')) {{
    tr.style.display = tr.innerText.toLowerCase().includes(q) ? '' : 'none';
  }}
}}
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    df = pd.read_parquet(args.inp)
    df = df.dropna(subset=["date"]).copy()

    figs = [
        fig_volume(df),
        fig_top_contacts(df),
        fig_heatmap(df),
        fig_sentiment(df),
        fig_bursts(df),
        fig_tags(df),
    ]
    chart_html = "\n".join(f.to_html(include_plotlyjs="cdn" if i == 0 else False,
                                      full_html=False) for i, f in enumerate(figs))
    style = """
    <style>
      body { background: #0b0d10; color: #e6e6e6; font-family: -apple-system, system-ui, sans-serif; margin: 20px; }
      h1 { font-weight: 500; }
      table { border-collapse: collapse; width: 100%; font-size: 12px; }
      th, td { border-bottom: 1px solid #222; padding: 4px 8px; text-align: left; vertical-align: top; }
      thead th { position: sticky; top: 0; background: #111; }
      input#q { background: #111; color: #eee; border: 1px solid #333; padding: 8px; width: 100%; margin: 12px 0; }
      .charts > div { margin-bottom: 32px; }
    </style>
    """
    out_html = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>osint-self dashboard</title>{style}</head>
    <body>
      <h1>osint-self — your archive</h1>
      <p>Local only. {len(df):,} messages. Dates: {df['date'].min().date()} to {df['date'].max().date()}.</p>
      <div class="charts">{chart_html}</div>
      <h2>Messages</h2>
      {table_html(df)}
    </body></html>"""

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_html)
    print(f"wrote dashboard -> {args.out}")


if __name__ == "__main__":
    main()
