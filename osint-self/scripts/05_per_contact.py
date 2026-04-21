"""Phase 5: per-counterparty aggregation.

Rolls per-message signals up to one row per counterparty. Columns are neutral
measurements — rename them however you like for your own review.

Columns:
  counterparty
  first_seen, last_seen, span_days
  n_total, n_in, n_out, ratio_in_out
  avg_sentiment_in, avg_sentiment_out
  pct_negative_in  (compound <= -0.5)
  pct_positive_in  (compound >=  0.5)
  pct_night_in     (messages 22:00-06:00 local)
  n_bursts_in
  longest_silent_gap_days
  <tag>_in_count   (one column per tag from config)
  <tag>_out_count
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["counterparty"] != ""].copy()
    df = df.dropna(subset=["date"])

    all_tags = sorted({t for tags in df["tags"] for t in (tags or [])})
    for t in all_tags:
        df[f"tag_{t}"] = df["tags"].map(lambda lst, t=t: t in (lst or []))

    def per_contact(g: pd.DataFrame) -> pd.Series:
        gin = g[g["direction"] == "in"]
        gout = g[g["direction"] == "out"]
        span = (g["date"].max() - g["date"].min()).days if len(g) else 0
        gaps = g["date"].sort_values().diff().dt.days.dropna()
        out = {
            "first_seen": g["date"].min(),
            "last_seen": g["date"].max(),
            "span_days": span,
            "n_total": len(g),
            "n_in": len(gin),
            "n_out": len(gout),
            "ratio_in_out": (len(gin) / len(gout)) if len(gout) else float("inf"),
            "avg_sentiment_in": gin["sentiment"].mean() if len(gin) else None,
            "avg_sentiment_out": gout["sentiment"].mean() if len(gout) else None,
            "pct_negative_in": (gin["sentiment"] <= -0.5).mean() if len(gin) else None,
            "pct_positive_in": (gin["sentiment"] >= 0.5).mean() if len(gin) else None,
            "pct_night_in": gin["is_night"].mean() if len(gin) else None,
            "n_bursts_in": int(gin["burst"].sum()) if "burst" in gin else 0,
            "longest_silent_gap_days": float(gaps.max()) if len(gaps) else 0.0,
        }
        for t in all_tags:
            col = f"tag_{t}"
            out[f"{t}_in_count"] = int(gin[col].sum()) if len(gin) else 0
            out[f"{t}_out_count"] = int(gout[col].sum()) if len(gout) else 0
        return pd.Series(out)

    return df.groupby("counterparty").apply(per_contact).reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--csv", type=Path, help="also write CSV alongside parquet")
    args = ap.parse_args()

    df = pd.read_parquet(args.inp)
    summary = summarize(df)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_parquet(args.out, index=False)
    if args.csv:
        summary.to_csv(args.csv, index=False)
    print(f"wrote {len(summary)} counterparty rows -> {args.out}")


if __name__ == "__main__":
    main()
