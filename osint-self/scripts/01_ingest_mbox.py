"""Phase 1: parse a Google Takeout .mbox into a parquet table.

Reads messages with the stdlib `mailbox` module, strips HTML from bodies,
decodes headers, and writes a tidy DataFrame.
"""
from __future__ import annotations

import argparse
import mailbox
import re
from email.header import decode_header, make_header
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


def _decode(value):
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _addrs(msg, header):
    raw = msg.get_all(header, [])
    return [addr.lower().strip() for _, addr in getaddresses(raw) if addr]


def _get_body(msg):
    text_parts, html_parts = [], []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp.lower():
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain":
                text_parts.append(decoded)
            elif ctype == "text/html":
                html_parts.append(decoded)
    else:
        payload = msg.get_payload(decode=True)
        if payload is not None:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            (text_parts if msg.get_content_type() == "text/plain" else html_parts).append(decoded)

    text = "\n".join(text_parts).strip()
    if not text and html_parts:
        soup = BeautifulSoup("\n".join(html_parts), "lxml")
        text = soup.get_text(separator="\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _has_attachment(msg) -> bool:
    if not msg.is_multipart():
        return False
    for part in msg.walk():
        disp = str(part.get("Content-Disposition") or "")
        if "attachment" in disp.lower():
            return True
    return False


def _refs(msg):
    raw = msg.get("References", "") or ""
    return [r.strip("<> \t") for r in raw.split() if r.strip()]


def ingest(mbox_path: Path) -> pd.DataFrame:
    box = mailbox.mbox(str(mbox_path))
    rows = []
    for key, msg in tqdm(box.iteritems(), desc="parsing mbox"):
        try:
            date_raw = msg.get("Date")
            date = parsedate_to_datetime(date_raw) if date_raw else None
        except Exception:
            date = None
        rows.append({
            "message_id": (msg.get("Message-ID") or f"no-id-{key}").strip("<> "),
            "date": date,
            "from": (_addrs(msg, "From") or [""])[0],
            "from_name": _decode(msg.get("From")),
            "to": _addrs(msg, "To"),
            "cc": _addrs(msg, "Cc"),
            "bcc": _addrs(msg, "Bcc"),
            "subject": _decode(msg.get("Subject")),
            "in_reply_to": (msg.get("In-Reply-To") or "").strip("<> "),
            "references": _refs(msg),
            "gmail_labels": [s.strip() for s in (msg.get("X-Gmail-Labels") or "").split(",") if s.strip()],
            "body_text": _get_body(msg),
            "has_attachment": _has_attachment(msg),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mbox", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if not args.mbox.exists():
        raise SystemExit(f"mbox not found: {args.mbox}")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    df = ingest(args.mbox)
    df.to_parquet(args.out, index=False)
    print(f"wrote {len(df):,} messages -> {args.out}")


if __name__ == "__main__":
    main()
