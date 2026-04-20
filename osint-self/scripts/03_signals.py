"""Phase 3: per-message signals.

Adds:
- `sentiment` (VADER compound, -1..1)
- `sentiment_pos` / `sentiment_neg` / `sentiment_neu`
- `length_chars`, `length_words`
- `hour_local`, `dow`, `is_night` (22:00-06:00)
- `tags` (list of user-defined regex categories that match)
- Burst flag: >= N messages from one counterparty within a rolling window.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import yaml
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def compile_tags(path: Path) -> dict[str, list[re.Pattern]]:
    data = yaml.safe_load(path.read_text()) or {}
    return {
        category: [re.compile(p, re.IGNORECASE) for p in patterns]
        for category, patterns in data.items()
    }


def tag_row(text: str, tags: dict[str, list[re.Pattern]]) -> list[str]:
    hits = []
    for category, patterns in tags.items():
        if any(p.search(text) for p in patterns):
            hits.append(category)
    return hits


def add_bursts(df: pd.DataFrame, window_minutes: int = 60, threshold: int = 10) -> pd.DataFrame:
    df = df.sort_values("date").copy()
    bucket = df["date"].dt.floor(f"{window_minutes}min")
    counts = df.assign(_b=bucket).groupby(["counterparty", "_b"])["message_id"].transform("size")
    df["burst"] = counts.ge(threshold).fillna(False)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--tags", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--tz", default="Europe/London")
    ap.add_argument("--burst-window-min", type=int, default=60)
    ap.add_argument("--burst-threshold", type=int, default=10)
    args = ap.parse_args()

    df = pd.read_parquet(args.inp)
    tags = compile_tags(args.tags)
    analyzer = SentimentIntensityAnalyzer()

    def score(text: str) -> dict:
        t = (text or "")[:5000]  # cap for speed
        s = analyzer.polarity_scores(t)
        return s

    scores = df["body_text"].fillna("").map(score)
    df["sentiment"] = scores.map(lambda s: s["compound"])
    df["sentiment_pos"] = scores.map(lambda s: s["pos"])
    df["sentiment_neg"] = scores.map(lambda s: s["neg"])
    df["sentiment_neu"] = scores.map(lambda s: s["neu"])

    df["length_chars"] = df["body_text"].fillna("").str.len()
    df["length_words"] = df["body_text"].fillna("").str.split().map(len)

    df["tags"] = df.apply(
        lambda r: tag_row(f"{r.get('subject','')}\n{r.get('body_text','')}", tags),
        axis=1,
    )

    local = df["date"].dt.tz_convert(args.tz)
    df["hour_local"] = local.dt.hour
    df["dow"] = local.dt.day_name()
    df["is_night"] = df["hour_local"].between(22, 23) | df["hour_local"].between(0, 5)

    df = add_bursts(df, window_minutes=args.burst_window_min, threshold=args.burst_threshold)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f"wrote {len(df):,} rows with signals -> {args.out}")


if __name__ == "__main__":
    main()
