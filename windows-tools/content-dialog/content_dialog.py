"""
content-dialog — universal content interceptor for Windows 10.

Runs as a system-tray daemon. Global hotkeys open a split-view popup showing
captured content (clipboard, Whisper transcript, ShareX image) alongside an
edit/annotation area. Route the result to MCP, clipboard, Claude Desktop, or a log file.

Other tools push content here via HTTP POST on localhost:27182:
    POST http://localhost:27182/push
    Content-Type: application/json
    {"source": "whisper", "text": "...", "image_path": ""}

Default hotkeys (override in mcp_destinations.json):
    Ctrl+Shift+V   open with clipboard text
    Ctrl+Shift+W   open with latest Whisper transcript
    Ctrl+Shift+S   open with latest ShareX capture
"""

import ctypes
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
import tkinter as tk
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.error

HERE = pathlib.Path(__file__).parent
CONFIG_FILE = HERE / "mcp_destinations.json"

DEFAULTS = {
    "hotkeys": {
        "clipboard": "ctrl+shift+v",
        "whisper":   "ctrl+shift+w",
        "sharex":    "ctrl+shift+s",
    },
    "listen_port": 27182,
    "mcp_url": "http://localhost:3000/ingest",
    "log_file": str(pathlib.Path.home() / "AppData" / "Local" / "loz-tools" / "capture-log.txt"),
    "claude_exe": str(pathlib.Path(os.environ.get("LOCALAPPDATA", "C:\\")) / "AnthropicClaude" / "claude.exe"),
}

BG   = "#0e0f12"
PAN  = "#13151a"
PAN2 = "#1a1c23"
ACC  = "#e84c1e"
INK  = "#e8e6e0"
MUT  = "#6e6b64"
LINE = "#2a2d35"

_lock  = threading.Lock()
_state = {"source": "clipboard", "text": "", "image_path": ""}
_root  = None


def _load_config():
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.is_file():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


# ── HTTP receiver (other tools POST content here) ─────────────────────────

class _PushHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/push":
            self.send_response(404); self.end_headers(); return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            with _lock:
                _state.update(data)
            _root.event_generate("<<ContentPushed>>", when="tail")
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        except Exception as e:
            self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

    def log_message(self, *_):
        pass


def _start_server(port):
    srv = HTTPServer(("127.0.0.1", port), _PushHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()


# ── dialog ────────────────────────────────────────────────────────────────

class ContentDialog(tk.Toplevel):
    def __init__(self, parent, cfg):
        super().__init__(parent)
        self._cfg = cfg
        self.title("Loz Capture")
        self.configure(bg=BG)
        self.attributes("-topmost", True)
        self.geometry("860x540")
        self._center()
        self._build()
        self.bind("<Escape>", lambda _: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._load_content()

    def _center(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"860x540+{(sw-860)//2}+{(sh-540)//2}")

    def _btn(self, parent, text, cmd, primary=False, **kw):
        bg = ACC if primary else PAN2
        fg = INK
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                      relief="flat", cursor="hand2", font=("Consolas", 10, "bold"),
                      padx=14, pady=6, activebackground=LINE, activeforeground=INK, **kw)
        return b

    def _build(self):
        top = tk.Frame(self, bg=PAN, pady=8, padx=12)
        top.pack(fill="x")
        self._src_lbl = tk.Label(top, text="Source: clipboard", bg=PAN,
                                 fg=MUT, font=("Consolas", 10))
        self._src_lbl.pack(side="left")
        self._btn(top, "✕ Close", self.destroy).pack(side="right")

        paned = tk.PanedWindow(self, orient="horizontal", bg=LINE,
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=10, pady=6)

        left = tk.Frame(paned, bg=BG)
        tk.Label(left, text="ORIGINAL", bg=BG, fg=MUT,
                 font=("Consolas", 9), anchor="w").pack(fill="x", padx=6, pady=(6, 2))
        self._orig = tk.Text(left, bg=PAN, fg=INK, insertbackground=ACC,
                             font=("Consolas", 11), relief="flat", wrap="word",
                             state="disabled", selectbackground=ACC + "55")
        self._orig.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        paned.add(left, minsize=320)

        right = tk.Frame(paned, bg=BG)
        tk.Label(right, text="YOUR NOTE", bg=BG, fg=MUT,
                 font=("Consolas", 9), anchor="w").pack(fill="x", padx=6, pady=(6, 2))
        self._note = tk.Text(right, bg=PAN2, fg=INK, insertbackground=ACC,
                             font=("Consolas", 11), relief="flat", wrap="word",
                             selectbackground=ACC + "55")
        self._note.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        paned.add(right, minsize=240)

        bot = tk.Frame(self, bg=PAN, pady=10, padx=12)
        bot.pack(fill="x")
        self._btn(bot, "→ MCP",       self._send_mcp,    primary=True).pack(side="left", padx=(0, 6))
        self._btn(bot, "⎘ Clipboard", self._send_clip).pack(side="left", padx=(0, 6))
        self._btn(bot, "⬡ Claude",    self._send_claude).pack(side="left", padx=(0, 6))
        self._btn(bot, "⊞ Log file",  self._send_file).pack(side="left")
        self._status = tk.Label(bot, text="", bg=PAN, fg=ACC, font=("Consolas", 10))
        self._status.pack(side="right")

    def _load_content(self):
        with _lock:
            src  = _state.get("source", "clipboard")
            text = _state.get("text", "")
            img  = _state.get("image_path", "")

        if src == "clipboard" and not text:
            try:
                text = self.clipboard_get()
            except Exception:
                text = ""

        self._src_lbl.config(text=f"Source: {src}")
        self._orig.config(state="normal")
        self._orig.delete("1.0", "end")
        if img and os.path.isfile(img):
            self._orig.insert("end", f"[image: {img}]\n\n")
        self._orig.insert("end", text or "(no content)")
        self._orig.config(state="disabled")
        self._note.focus_set()

    def _combined(self):
        orig = self._orig.get("1.0", "end").strip()
        note = self._note.get("1.0", "end").strip()
        return f"{orig}\n\n--- note ---\n{note}" if note else orig

    def _flash(self, msg, ms=2200):
        self._status.config(text=msg)
        self.after(ms, lambda: self._status.config(text=""))

    def _send_mcp(self):
        url = self._cfg.get("mcp_url", "")
        if not url:
            self._flash("No mcp_url in mcp_destinations.json"); return
        payload = json.dumps({"content": self._combined(),
                              "source": _state.get("source", "clipboard")}).encode()
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                self._flash(f"Sent to MCP ({r.status})")
        except Exception as e:
            self._flash(f"MCP error: {e}")

    def _send_clip(self):
        self.clipboard_clear()
        self.clipboard_append(self._combined())
        self._flash("Copied to clipboard")

    def _send_claude(self):
        try:
            import win32gui, win32api, win32process
        except ImportError:
            self._flash("pywin32 not installed"); return

        exe = self._cfg.get("claude_exe", "")

        def find_claude():
            found = []
            def cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and "claude" in win32gui.GetWindowText(hwnd).lower():
                    found.append(hwnd)
            win32gui.EnumWindows(cb, None)
            return found[0] if found else None

        hwnd = find_claude()
        if hwnd is None and exe and os.path.isfile(exe):
            subprocess.Popen([exe])
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                hwnd = find_claude()
                if hwnd: break
                time.sleep(0.3)

        if hwnd:
            win32gui.ShowWindow(hwnd, 9)
            fg = win32gui.GetForegroundWindow()
            our = win32api.GetCurrentThreadId()
            their = win32process.GetWindowThreadProcessId(fg)[0]
            ctypes.windll.user32.AttachThreadInput(our, their, True)
            win32gui.SetForegroundWindow(hwnd)
            ctypes.windll.user32.AttachThreadInput(our, their, False)
            self.clipboard_clear()
            self.clipboard_append(self._combined())
            self._flash("Focused Claude Desktop — paste with Ctrl+V")
        else:
            self._flash("Claude Desktop not found")

    def _send_file(self):
        log = pathlib.Path(self._cfg.get("log_file",
                           str(pathlib.Path.home() / "loz-captures.txt")))
        log.parent.mkdir(parents=True, exist_ok=True)
        ts  = time.strftime("%Y-%m-%d %H:%M:%S")
        src = _state.get("source", "clipboard")
        log.open("a", encoding="utf-8").write(
            f"\n── {ts} [{src}] ──\n{self._combined()}\n")
        self._flash(f"Appended to {log.name}")


# ── main ──────────────────────────────────────────────────────────────────

def _open_dialog(cfg, source="clipboard"):
    with _lock:
        _state["source"] = source
    dlg = ContentDialog(_root, cfg)
    dlg.grab_set()
    _root.wait_window(dlg)


def main():
    global _root
    cfg = _load_config()

    _root = tk.Tk()
    _root.withdraw()
    _root.title("Loz Content Dialog")

    _start_server(cfg.get("listen_port", 27182))
    _root.bind("<<ContentPushed>>",
               lambda _: _open_dialog(cfg, _state.get("source", "whisper")))

    try:
        import keyboard
        hk = cfg.get("hotkeys", {})
        keyboard.add_hotkey(hk.get("clipboard", "ctrl+shift+v"),
                            lambda: _root.after(0, lambda: _open_dialog(cfg, "clipboard")))
        keyboard.add_hotkey(hk.get("whisper",   "ctrl+shift+w"),
                            lambda: _root.after(0, lambda: _open_dialog(cfg, "whisper")))
        keyboard.add_hotkey(hk.get("sharex",    "ctrl+shift+s"),
                            lambda: _root.after(0, lambda: _open_dialog(cfg, "sharex")))
    except Exception as e:
        print(f"[content-dialog] hotkeys unavailable: {e}", file=sys.stderr)

    try:
        import pystray
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (64, 64), BG)
        d = ImageDraw.Draw(img)
        d.ellipse([8, 8, 56, 56], fill=ACC)
        d.text((20, 18), "L", fill=INK, font=None)
        icon = pystray.Icon("loz-dialog", img, "Loz Content Dialog",
            menu=pystray.Menu(
                pystray.MenuItem("Open (clipboard)",
                    lambda: _root.after(0, lambda: _open_dialog(cfg, "clipboard"))),
                pystray.MenuItem("Open (whisper)",
                    lambda: _root.after(0, lambda: _open_dialog(cfg, "whisper"))),
                pystray.MenuItem("Exit",
                    lambda: (_root.after(0, _root.destroy), icon.stop())),
            ))
        threading.Thread(target=icon.run, daemon=True).start()
    except Exception as e:
        print(f"[content-dialog] tray icon unavailable: {e}", file=sys.stderr)

    _root.mainloop()


if __name__ == "__main__":
    main()
