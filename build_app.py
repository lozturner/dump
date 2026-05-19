#!/usr/bin/env python3
"""Stitch the embedded data into the standalone app template."""
import json
from pathlib import Path

# Reuse the record list from the existing builder. Importing this module
# also (idempotently) refreshes releaf_emails_chronology.csv and the old
# single-file HTML — harmless side effects.
from build_releaf_csv import records  # noqa: E402

HERE = Path(__file__).parent
tpl = (HERE / "app_template.html").read_text(encoding="utf-8")
out = tpl.replace("__DATA_JSON__", json.dumps(records, ensure_ascii=False))
target = HERE / "releaf_chronology.html"
target.write_text(out, encoding="utf-8")
print(f"Wrote {target} ({len(out):,} bytes, {len(records)} records)")
