"""
hot-corners — mouse-corner triggers for Windows 10.

Monitors the cursor position. When the cursor dwells in a screen corner for
`dwell_ms` milliseconds the configured action fires. Each corner is independent
and has its own cooldown.

Actions available per corner:
    "none"     — do nothing
    "url"      — open value in the default browser
    "command"  — run value as a shell command
    "dialog"   — POST to content-dialog (value = source: clipboard/whisper/sharex)
    "hey_claude" — bring Claude Desktop to the foreground (same trick as hey_claude.py)
    "sharex"   — launch ShareX capture (value = region / fullscreen / window)

Config lives in config.json next to this script.
"""

import ctypes
import json
import os
import pathlib
import subprocess
import sys
import time
import threading
import urllib.request
import webbrowser

HERE = pathlib.Path(__file__).parent
CFG_FILE = HERE / "config.json"

DEFAULTS = {
    "corner_px": 4,
    "dwell_ms": 300,
    "cooldown_s": 2.0,
    "dialog_port": 27182,
    "sharex_exe": r"C:\Program Files\ShareX\ShareX.exe",
    "claude_exe": str(pathlib.Path(os.environ.get("LOCALAPPDATA", "C:\\"))
                      / "AnthropicClaude" / "claude.exe"),
    "corners": {
        "top_left":     {"action": "url",      "value": "http://localhost:8765/gallery.html"},
        "top_right":    {"action": "hey_claude","value": ""},
        "bottom_left":  {"action": "none",      "value": ""},
        "bottom_right": {"action": "dialog",    "value": "clipboard"},
    },
}

_last_fire: dict[str, float] = {k: 0.0 for k in
                                 ("top_left", "top_right", "bottom_left", "bottom_right")}
_dwell_start: dict[str, float] = {k: 0.0 for k in _last_fire}


def _load_cfg():
    cfg = json.loads(json.dumps(DEFAULTS))
    if CFG_FILE.is_file():
        try:
            cfg.update(json.loads(CFG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def _cursor_pos():
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def _screen_size():
    return (ctypes.windll.user32.GetSystemMetrics(0),
            ctypes.windll.user32.GetSystemMetrics(1))


def _which_corner(x, y, w, h, px):
    if x <= px and y <= px:           return "top_left"
    if x >= w - 1 - px and y <= px:  return "top_right"
    if x <= px and y >= h - 1 - px:  return "bottom_left"
    if x >= w - 1 - px and y >= h - 1 - px: return "bottom_right"
    return None


def _find_claude_hwnd():
    import win32gui
    found = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and "claude" in win32gui.GetWindowText(hwnd).lower():
            found.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


def _bring_claude(claude_exe):
    try:
        import win32gui, win32api, win32process
    except ImportError:
        print("[hot-corners] pywin32 not installed", file=sys.stderr)
        return

    hwnd = _find_claude_hwnd()
    if hwnd is None and claude_exe and os.path.isfile(claude_exe):
        subprocess.Popen([claude_exe])
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            hwnd = _find_claude_hwnd()
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
        try:
            import winsound; winsound.Beep(440, 100)
        except Exception:
            pass


def _push_dialog(source, port):
    payload = json.dumps({"source": source, "text": "", "image_path": ""}).encode()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/push", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        print(f"[hot-corners] dialog push failed: {e}", file=sys.stderr)


def _sharex(exe, mode):
    modes = {"region": "-capture region", "fullscreen": "-capture", "window": "-capture window"}
    args = modes.get(mode, "-capture region").split()
    if os.path.isfile(exe):
        subprocess.Popen([exe] + args)
    else:
        print(f"[hot-corners] ShareX not found at {exe}", file=sys.stderr)


def _fire(corner, cfg):
    action_cfg = cfg["corners"].get(corner, {})
    action = action_cfg.get("action", "none")
    value  = action_cfg.get("value", "")

    if action == "none":
        return
    if action == "url":
        webbrowser.open(value)
    elif action == "command":
        subprocess.Popen(value, shell=True)
    elif action == "dialog":
        threading.Thread(target=_push_dialog,
                         args=(value or "clipboard", cfg["dialog_port"]),
                         daemon=True).start()
    elif action == "hey_claude":
        threading.Thread(target=_bring_claude,
                         args=(cfg["claude_exe"],), daemon=True).start()
    elif action == "sharex":
        _sharex(cfg["sharex_exe"], value or "region")

    print(f"[hot-corners] fired {corner} → {action}", flush=True)


def main():
    cfg = _load_cfg()
    px        = cfg["corner_px"]
    dwell_ms  = cfg["dwell_ms"]
    cooldown  = cfg["cooldown_s"]
    poll_s    = 0.04  # 40 ms

    print("[hot-corners] running. Ctrl+C to stop.", flush=True)

    try:
        while True:
            x, y = _cursor_pos()
            w, h = _screen_size()
            corner = _which_corner(x, y, w, h, px)
            now = time.monotonic()

            for c in _dwell_start:
                if c == corner:
                    if _dwell_start[c] == 0.0:
                        _dwell_start[c] = now
                    elif (now - _dwell_start[c]) * 1000 >= dwell_ms:
                        if now - _last_fire[c] >= cooldown:
                            _last_fire[c] = now
                            _fire(c, cfg)
                        _dwell_start[c] = now  # reset so it doesn't spam
                else:
                    _dwell_start[c] = 0.0

            time.sleep(poll_s)
    except KeyboardInterrupt:
        print("\n[hot-corners] stopped")


if __name__ == "__main__":
    main()
