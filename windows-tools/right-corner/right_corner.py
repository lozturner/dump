"""
right-corner — a slim floating panel anchored to the right edge of the screen.

Shows quick-access buttons that slide in when the mouse approaches the right edge
and retract after a configurable idle period. Each button can open a URL, run a
command, or trigger a content-dialog action.

Config (right_corner_config.json next to this script):
    {
        "trigger_px": 3,       # pixels from right edge that triggers reveal
        "retract_ms": 2500,    # hide after this many ms of no hover
        "panel_width": 52,
        "buttons": [
            {"label": "G",  "title": "Gallery",        "action": "url",     "value": "http://localhost:8765/gallery.html"},
            {"label": "W",  "title": "Whisper",         "action": "dialog",  "value": "whisper"},
            {"label": "S",  "title": "ShareX capture",  "action": "sharex",  "value": "region"},
            {"label": "C",  "title": "Claude Desktop",  "action": "claude",  "value": ""},
            {"label": "⎘",  "title": "Clipboard dialog","action": "dialog",  "value": "clipboard"}
        ],
        "dialog_port": 27182,
        "sharex_exe": "C:\\\\Program Files\\\\ShareX\\\\ShareX.exe",
        "claude_exe": ""
    }
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
import urllib.request
import webbrowser

HERE = pathlib.Path(__file__).parent
CFG_FILE = HERE / "right_corner_config.json"

DEFAULTS = {
    "trigger_px": 3,
    "retract_ms": 2500,
    "panel_width": 52,
    "dialog_port": 27182,
    "sharex_exe": r"C:\Program Files\ShareX\ShareX.exe",
    "claude_exe": str(pathlib.Path(os.environ.get("LOCALAPPDATA", "C:\\"))
                      / "AnthropicClaude" / "claude.exe"),
    "buttons": [
        {"label": "G",  "title": "Gallery",         "action": "url",    "value": "http://localhost:8765/gallery.html"},
        {"label": "W",  "title": "Whisper capture", "action": "dialog", "value": "whisper"},
        {"label": "S",  "title": "ShareX region",   "action": "sharex", "value": "region"},
        {"label": "C",  "title": "Claude Desktop",  "action": "claude", "value": ""},
        {"label": "⎘",  "title": "Clipboard",       "action": "dialog", "value": "clipboard"},
    ],
}

BG   = "#0e0f12"
ACC  = "#e84c1e"
INK  = "#e8e6e0"
MUT  = "#6e6b64"


def _load_cfg():
    cfg = json.loads(json.dumps(DEFAULTS))
    if CFG_FILE.is_file():
        try:
            cfg.update(json.loads(CFG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def _screen():
    return (ctypes.windll.user32.GetSystemMetrics(0),
            ctypes.windll.user32.GetSystemMetrics(1))


def _cursor():
    class PT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = PT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def _push_dialog(source, port):
    payload = json.dumps({"source": source, "text": "", "image_path": ""}).encode()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/push", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        print(f"[right-corner] dialog push failed: {e}", file=sys.stderr)


def _sharex(exe, mode):
    args = {"region": ["-capture", "region"],
            "fullscreen": ["-capture"],
            "window": ["-capture", "window"]}.get(mode, ["-capture", "region"])
    if os.path.isfile(exe):
        subprocess.Popen([exe] + args)


def _bring_claude(exe):
    try:
        import win32gui, win32api, win32process
    except ImportError:
        return
    found = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and "claude" in win32gui.GetWindowText(hwnd).lower():
            found.append(hwnd)
    win32gui.EnumWindows(cb, None)
    hwnd = found[0] if found else None
    if hwnd is None and exe and os.path.isfile(exe):
        subprocess.Popen([exe])
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            found.clear()
            win32gui.EnumWindows(cb, None)
            if found: hwnd = found[0]; break
            time.sleep(0.3)
    if hwnd:
        win32gui.ShowWindow(hwnd, 9)
        fg  = win32gui.GetForegroundWindow()
        our = win32api.GetCurrentThreadId()
        their = win32process.GetWindowThreadProcessId(fg)[0]
        ctypes.windll.user32.AttachThreadInput(our, their, True)
        win32gui.SetForegroundWindow(hwnd)
        ctypes.windll.user32.AttachThreadInput(our, their, False)


class RightCornerPanel:
    def __init__(self, cfg):
        self._cfg  = cfg
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.configure(bg=BG)

        sw, sh = _screen()
        pw = cfg["panel_width"]
        self._sw, self._sh = sw, sh
        self._pw = pw
        self._visible = False
        self._last_hover = 0.0

        # position off-screen right initially
        self._root.geometry(f"{pw}x{sh}+{sw}+0")

        self._build_buttons()

        # mouse-position watcher
        threading.Thread(target=self._watcher, daemon=True).start()
        self._root.after(100, self._tick)
        self._root.mainloop()

    def _build_buttons(self):
        cfg = self._cfg
        frame = tk.Frame(self._root, bg=BG)
        frame.pack(fill="both", expand=True)

        # separator line on left edge
        tk.Frame(frame, bg=ACC, width=2).pack(side="left", fill="y")

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(side="left", fill="both", expand=True, pady=8)

        for b in cfg["buttons"]:
            btn = tk.Button(
                btn_frame, text=b["label"],
                font=("Consolas", 13, "bold"),
                bg=BG, fg=INK, relief="flat", cursor="hand2",
                activebackground=ACC, activeforeground=INK,
                width=2, pady=10,
                command=lambda bc=b: self._fire(bc),
            )
            btn.pack(fill="x", pady=1)
            btn.bind("<Enter>", lambda _: self._on_hover())
            if b.get("title"):
                self._tooltip(btn, b["title"])

    def _tooltip(self, widget, text):
        tip = None
        def show(_):
            nonlocal tip
            tip = tk.Toplevel(widget)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            lbl = tk.Label(tip, text=text, bg="#1a1c23", fg=INK,
                           font=("Consolas", 10), padx=8, pady=4,
                           relief="flat")
            lbl.pack()
            x = widget.winfo_rootx() - lbl.winfo_reqwidth() - 6
            y = widget.winfo_rooty()
            tip.geometry(f"+{x}+{y}")
        def hide(_):
            nonlocal tip
            if tip: tip.destroy(); tip = None
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _fire(self, b):
        action = b.get("action", "none")
        value  = b.get("value", "")
        cfg    = self._cfg
        if action == "url":
            webbrowser.open(value)
        elif action == "command":
            subprocess.Popen(value, shell=True)
        elif action == "dialog":
            threading.Thread(target=_push_dialog,
                             args=(value or "clipboard", cfg["dialog_port"]),
                             daemon=True).start()
        elif action == "sharex":
            _sharex(cfg["sharex_exe"], value or "region")
        elif action == "claude":
            threading.Thread(target=_bring_claude,
                             args=(cfg["claude_exe"],), daemon=True).start()

    def _on_hover(self):
        self._last_hover = time.monotonic()

    def _watcher(self):
        trigger = self._cfg["trigger_px"]
        while True:
            x, _ = _cursor()
            if x >= self._sw - 1 - trigger:
                self._last_hover = time.monotonic()
            time.sleep(0.04)

    def _tick(self):
        retract_s = self._cfg["retract_ms"] / 1000
        idle = time.monotonic() - self._last_hover
        should_show = idle < retract_s

        if should_show and not self._visible:
            self._root.geometry(f"{self._pw}x{self._sh}+{self._sw - self._pw}+0")
            self._visible = True
        elif not should_show and self._visible:
            self._root.geometry(f"{self._pw}x{self._sh}+{self._sw}+0")
            self._visible = False

        self._root.after(80, self._tick)


def main():
    cfg = _load_cfg()
    print("[right-corner] running. Move mouse to the right edge to reveal panel.", flush=True)
    RightCornerPanel(cfg)


if __name__ == "__main__":
    main()
