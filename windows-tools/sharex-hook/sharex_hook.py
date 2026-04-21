"""
sharex-hook — local capture receiver for ShareX on Windows 10.

Runs a small HTTP server that ShareX posts screenshots to via its
"Custom Uploader" feature. When a capture arrives the image is saved
to a local folder and the path is forwarded to content-dialog so you
can annotate and route it immediately.

Setup:
  1. Run this script (or install it as a startup task via install.bat).
  2. In ShareX → Destinations → Custom uploader, import sharex_uploader.json.
  3. Set "Custom uploader" as the image upload destination.
  4. Captures will now appear in the content-dialog automatically.

Config (sharex_config.json next to this script):
    {
        "listen_port": 27183,
        "dialog_port": 27182,
        "save_dir": "~/Pictures/ShareX-captures",
        "open_dialog": true
    }
"""

import json
import os
import pathlib
import shutil
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE    = pathlib.Path(__file__).parent
CFG_FILE = HERE / "sharex_config.json"

DEFAULTS = {
    "listen_port": 27183,
    "dialog_port": 27182,
    "save_dir": str(pathlib.Path.home() / "Pictures" / "ShareX-captures"),
    "open_dialog": True,
}


def _load_cfg():
    cfg = dict(DEFAULTS)
    if CFG_FILE.is_file():
        try:
            cfg.update(json.loads(CFG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def _push_dialog(image_path, dialog_port):
    payload = json.dumps({
        "source": "sharex",
        "text": f"[captured: {pathlib.Path(image_path).name}]",
        "image_path": image_path,
    }).encode()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{dialog_port}/push", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"[sharex-hook] dialog push failed: {e}", file=sys.stderr)


def _make_handler(cfg):
    save_dir    = pathlib.Path(cfg["save_dir"]).expanduser()
    dialog_port = cfg["dialog_port"]
    open_dialog = cfg.get("open_dialog", True)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path not in ("/upload", "/"):
                self.send_response(404); self.end_headers(); return

            ctype   = self.headers.get("Content-Type", "")
            length  = int(self.headers.get("Content-Length", 0))
            body    = self.rfile.read(length)

            # determine extension from Content-Type
            ext_map = {
                "image/png":  ".png",
                "image/jpeg": ".jpg",
                "image/gif":  ".gif",
                "image/webp": ".webp",
            }
            ext = next((v for k, v in ext_map.items() if k in ctype), ".png")

            save_dir.mkdir(parents=True, exist_ok=True)
            ts   = time.strftime("%Y%m%d_%H%M%S")
            dest = save_dir / f"sharex_{ts}{ext}"
            dest.write_bytes(body)

            print(f"[sharex-hook] saved: {dest}", flush=True)

            url = dest.as_posix()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"url": url, "file": str(dest)}).encode())

            if open_dialog:
                threading.Thread(target=_push_dialog,
                                 args=(str(dest), dialog_port),
                                 daemon=True).start()

        def log_message(self, fmt, *args):
            pass  # silence request logs

    return Handler


def main():
    cfg = _load_cfg()
    port = cfg["listen_port"]
    handler = _make_handler(cfg)
    server = HTTPServer(("127.0.0.1", port), handler)
    print(f"[sharex-hook] listening on http://127.0.0.1:{port}/upload", flush=True)
    print(f"[sharex-hook] saving captures to: {cfg['save_dir']}", flush=True)
    print("[sharex-hook] Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[sharex-hook] stopped")


if __name__ == "__main__":
    main()
