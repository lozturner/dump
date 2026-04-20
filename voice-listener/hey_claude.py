"""
Hey Claude — wake word listener for Windows 10.
Listens continuously for "hey claude", then brings the Claude Desktop app
to the foreground with the cursor focused in the input box.

Usage: run hey_claude.exe (or python hey_claude.py) at startup — no console shown.
Config: edit the constants below to match your setup.
"""

import os
import sys
import time
import pathlib
import subprocess
import threading
import numpy as np

# ── config ──────────────────────────────────────────────────────────────────

WAKE_THRESHOLD = 0.5          # confidence to trigger (0–1); raise if too many false alarms
AUDIO_SAMPLE_RATE = 16_000    # Hz — required by openWakeWord
CHUNK_MS = 80                 # audio chunk size in milliseconds
MODEL_PATH = str(pathlib.Path(__file__).parent / "models" / "hey_claude.onnx")

# Default Claude Desktop install location; update if yours differs
CLAUDE_EXE = os.path.expandvars(
    r"%LOCALAPPDATA%\AnthropicClaude\claude.exe"
)

# Seconds to wait for Claude window to appear after launching
LAUNCH_WAIT_S = 8

# ── internals ────────────────────────────────────────────────────────────────

_COOLDOWN_S = 3   # ignore re-triggers for this many seconds after activation
_last_trigger = 0.0


def _play_beep():
    """Short 440 Hz confirmation chirp via Windows Beep (no extra deps)."""
    try:
        import winsound
        winsound.Beep(440, 120)
    except Exception:
        pass


def _find_claude_window():
    """Return the first window handle whose title contains 'Claude', or None."""
    import win32gui

    result = []

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "claude" in title.lower():
                result.append(hwnd)

    win32gui.EnumWindows(_cb, None)
    return result[0] if result else None


def _force_foreground(hwnd):
    """Bring hwnd to the foreground, bypassing Windows focus-steal protection."""
    import ctypes
    import win32api
    import win32gui
    import win32con
    import win32process

    SW_RESTORE = 9

    # Restore if minimised
    win32gui.ShowWindow(hwnd, SW_RESTORE)

    # AttachThreadInput trick — attach our thread to the foreground thread
    # so SetForegroundWindow is allowed
    fg_hwnd = win32gui.GetForegroundWindow()
    if fg_hwnd and fg_hwnd != hwnd:
        our_tid = win32api.GetCurrentThreadId()
        fg_tid = win32process.GetWindowThreadProcessId(fg_hwnd)[0]
        attached = False
        try:
            ctypes.windll.user32.AttachThreadInput(our_tid, fg_tid, True)
            attached = True
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
        finally:
            if attached:
                ctypes.windll.user32.AttachThreadInput(our_tid, fg_tid, False)
    else:
        win32gui.SetForegroundWindow(hwnd)


def _focus_input_box():
    """
    Find the text input inside the Claude Desktop (Electron/Chromium) window
    and click it. Uses pywinauto's UIA backend which works with Electron apps.

    If the control tree changes in future Claude versions, run this to re-map:
        from pywinauto.application import Application
        app = Application(backend="uia").connect(title_re=".*[Cc]laude.*")
        app.top_window().print_control_identifiers()
    """
    try:
        from pywinauto.application import Application
        from pywinauto.findwindows import ElementNotFoundError

        app = Application(backend="uia").connect(
            title_re=".*[Cc]laude.*", timeout=5
        )
        win = app.top_window()

        # Try the first Edit control (the composer textarea)
        try:
            edit = win.child_window(control_type="Edit", found_index=0)
            edit.click_input()
            return
        except ElementNotFoundError:
            pass

        # Fallback: click the window centre and hope the textarea gets focus
        rect = win.rectangle()
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
        import pyautogui
        pyautogui.click(cx, cy)

    except Exception as e:
        # Non-fatal — Claude is foregrounded; user can click manually
        print(f"[hey_claude] could not auto-focus input: {e}", file=sys.stderr)


def _activate_claude():
    global _last_trigger

    now = time.monotonic()
    if now - _last_trigger < _COOLDOWN_S:
        return
    _last_trigger = now

    print("[hey_claude] triggered")

    hwnd = _find_claude_window()

    if hwnd is None:
        if not os.path.isfile(CLAUDE_EXE):
            print(
                f"[hey_claude] Claude not found at {CLAUDE_EXE}\n"
                "Edit CLAUDE_EXE in hey_claude.py to point to your installation.",
                file=sys.stderr,
            )
            return
        subprocess.Popen([CLAUDE_EXE])
        # Poll for the window to appear
        deadline = time.monotonic() + LAUNCH_WAIT_S
        while time.monotonic() < deadline:
            hwnd = _find_claude_window()
            if hwnd:
                break
            time.sleep(0.3)

    if hwnd is None:
        print("[hey_claude] window never appeared", file=sys.stderr)
        return

    _play_beep()
    _force_foreground(hwnd)
    time.sleep(0.15)   # let the window paint before we poke at it
    _focus_input_box()


def _load_model():
    """Load the custom hey_claude ONNX model, or fall back to any pre-trained model."""
    from openwakeword.model import Model

    if os.path.isfile(MODEL_PATH):
        return Model(wakeword_models=[MODEL_PATH], inference_framework="onnx")

    # No custom model yet — use a built-in model as a placeholder so the
    # service at least starts. Run train_model.py for accurate "hey claude" detection.
    print(
        "[hey_claude] WARNING: custom model not found at:\n"
        f"  {MODEL_PATH}\n"
        "Run train_model.py first for accurate detection.\n"
        "Starting with built-in placeholder model...",
        file=sys.stderr,
    )
    return Model(inference_framework="onnx")


def main():
    import sounddevice as sd

    model = _load_model()
    chunk_samples = int(AUDIO_SAMPLE_RATE * CHUNK_MS / 1000)

    print("[hey_claude] listening...")

    def _audio_callback(indata, frames, time_info, status):
        # indata shape: (frames, 1) — flatten to 1-D int16
        audio_chunk = (indata[:, 0] * 32767).astype(np.int16)
        predictions = model.predict(audio_chunk)

        for ww_name, score in predictions.items():
            if score >= WAKE_THRESHOLD:
                # Run activation in a separate thread so the audio callback
                # returns immediately and the stream stays healthy
                threading.Thread(target=_activate_claude, daemon=True).start()
                break

    with sd.InputStream(
        samplerate=AUDIO_SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=chunk_samples,
        callback=_audio_callback,
    ):
        # Block forever; Ctrl-C or task kill to stop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[hey_claude] stopped")


if __name__ == "__main__":
    main()
