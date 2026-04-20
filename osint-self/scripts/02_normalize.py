"""Phase 2: contact normalization + thread reconstruction.

- Groups aliases into a single `contact_id` using config/contacts.yaml if
  present; otherwise falls back to the raw address.
- Reconstructs threads from Message-ID / In-Reply-To / References.
- Classifies each message as sent (`direction=out`) or received (`direction=in`)
  based on a --me argument (your own address(es)).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml


def load_contact_map(path: Path) -> dict[str, str]:
    if not path or not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    out = {}
    for label, addrs in data.items():
        for a in addrs or []:
            out[a.lower().strip()] = label
    return out


def resolve_threads(df: pd.DataFrame) -> pd.Series:
    # Union-find over message_id / in_reply_to / references
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for mid in df["message_id"]:
        parent.setdefault(mid, mid)

    for _, row in df.iterrows():
        mid = row["message_id"]
        irt = row.get("in_reply_to") or ""
        if irt:
            parent.setdefault(irt, irt)
            union(mid, irt)
        for ref in row.get("references") or []:
            parent.setdefault(ref, ref)
            union(mid, ref)

    return df["message_id"].map(lambda m: find(m))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--contacts", type=Path, default=Path("config/contacts.yaml"))
    ap.add_argument("--me", nargs="+", required=True,
                    help="Your own email address(es), lowercase")
    args = ap.parse_args()

    df = pd.read_parquet(args.inp)
    alias_map = load_contact_map(args.contacts)
    me = {a.lower() for a in args.me}

    def contact_for(addr: str) -> str:
        if not addr:
            return ""
        a = addr.lower()
        return alias_map.get(a, a)

    df["from_contact"] = df["from"].map(contact_for)
    df["to_contacts"] = df["to"].map(lambda lst: [contact_for(a) for a in (lst or [])])
    df["cc_contacts"] = df["cc"].map(lambda lst: [contact_for(a) for a in (lst or [])])

    df["direction"] = df["from"].map(lambda a: "out" if a in me else "in")

    def counterparty(row):
        if row["direction"] == "out":
            parties = [c for c in (row["to_contacts"] + row["cc_contacts"])
                       if c and c not in {alias_map.get(m, m) for m in me}]
        else:
            parties = [row["from_contact"]] if row["from_contact"] else []
        return parties[0] if parties else ""

    df["counterparty"] = df.apply(counterparty, axis=1)
    df["thread_id"] = resolve_threads(df)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f"wrote {len(df):,} rows, {df['thread_id'].nunique():,} threads -> {args.out}")


if __name__ == "__main__":
    main()
