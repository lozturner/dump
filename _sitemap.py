#!/usr/bin/env python3
"""Scan every .html in this directory, extract title + outgoing links,
compute incoming links, and write sitemap.json. Also prints the map."""

import datetime
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

files = sorted(f for f in glob.glob("*.html") if not f.startswith("_"))
pages = []
for f in files:
    with open(f, encoding="utf-8") as fh:
        html = fh.read()
    title_match = re.search(r"<title>([^<]*)</title>", html, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else f
    links = sorted(set(re.findall(r'href="([^"#?]+\.html)(?:[#?][^"]*)?"', html)))
    pages.append({"file": f, "title": title, "links": links, "incoming": []})

by_file = {p["file"]: p for p in pages}
for p in pages:
    for l in p["links"]:
        if l in by_file:
            by_file[l]["incoming"].append(p["file"])
for p in pages:
    p["incoming"] = sorted(set(p["incoming"]))

out = {
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "count": len(pages),
    "pages": pages,
}
with open("sitemap.json", "w", encoding="utf-8") as w:
    json.dump(out, w, indent=2)

# Mirror to docs/ if present
docs_dir = os.path.join(HERE, "docs")
if os.path.isdir(docs_dir):
    with open(os.path.join(docs_dir, "sitemap.json"), "w", encoding="utf-8") as w:
        json.dump(out, w, indent=2)

# Human-readable print
print(f"Sitemap generated at {out['generated']} — {out['count']} pages")
print("=" * 56)
for p in pages:
    print(f"\n{p['file']:<24}  {p['title']}")
    if p["links"]:
        for l in p["links"]:
            print(f"    → {l}")
    if p["incoming"]:
        for l in p["incoming"]:
            print(f"    ← {l}")
