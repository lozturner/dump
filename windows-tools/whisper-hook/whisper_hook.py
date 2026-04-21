"""
whisper-hook — real-time Whisper transcription for Windows 10.

Press and hold the configured hotkey to record, release to transcribe.
The transcript is posted to content-dialog (port 27182) and optionally
also written to the clipboard.

Config (whisper_config.json next to this script):
    {
        "model": "base.en",           # tiny / base / small / medium / large
        "push_to_dialog": true,       # POST transcript to content-dialog
        "copy_to_clipboard": true,    # also put it in the clipboard
        "dialog_port": 27182,
        "hold_key": "ctrl+shift+r",   # hold to record, release to transcribe
        "vad_silence_s": 1.2,         # seconds of silence before auto-stop
        "sample_rate": 16000
    }
"""

import json
import pathlib
import sys
import threading
import time
import urllib.request

import numpy as np
import sounddevice as sd

HERE = pathlib.Path(__file__).parent
CFG_FILE = HERE / "whisper_config.json"

DEFAULTS = {
    "model": "base.en",
    "push_to_dialog": True,
    "copy_to_clipboard": True,
    "dialog_port": 27182,
    "hold_key": "ctrl+shift+r",
    "vad_silence_s": 1.2,
    "sample_rate": 16000,
}


def _load_cfg():
    cfg = dict(DEFAULTS)
    if CFG_FILE.is_file():
        try:
            cfg.update(json.loads(CFG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def _push(text, port):
    payload = json.dumps({"source": "whisper", "text": text, "image_path": ""}).encode()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/push", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"[whisper-hook] push failed: {e}", file=sys.stderr)


def _clip(text):
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        r.clipboard_clear(); r.clipboard_append(text)
        r.update(); r.after(500, r.destroy); r.mainloop()
    except Exception:
        pass


def _beep(freq=880, ms=80):
    try:
        import winsound
        winsound.Beep(freq, ms)
    except Exception:
        pass


class Recorder:
    def __init__(self, sample_rate):
        self._sr = sample_rate
        self._chunks = []
        self._recording = False
        self._stream = None

    def start(self):
        self._chunks = []
        self._recording = True

        def cb(indata, frames, t, status):
            if self._recording:
                self._chunks.append(indata[:, 0].copy())

        self._stream = sd.InputStream(
            samplerate=self._sr, channels=1, dtype="float32", callback=cb)
        self._stream.start()
        _beep(660, 60)
        print("[whisper-hook] recording...", flush=True)

    def stop(self):
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        _beep(440, 80)
        if not self._chunks:
            return None
        return np.concatenate(self._chunks).astype(np.float32)


def _transcribe(audio, model, sr):
    import whisper
    result = model.transcribe(audio, fp16=False, language="en")
    return result.get("text", "").strip()


def main():
    cfg = _load_cfg()

    print("[whisper-hook] loading Whisper model…", flush=True)
    try:
        import whisper as _whisper_mod
        model = _whisper_mod.load_model(cfg["model"])
    except ImportError:
        print("[whisper-hook] openai-whisper not installed.\n"
              "Run: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)
    print(f"[whisper-hook] model '{cfg['model']}' ready. "
          f"Hold {cfg['hold_key']} to record.", flush=True)

    try:
        import keyboard
    except ImportError:
        print("[whisper-hook] 'keyboard' package not installed.\n"
              "Run: pip install keyboard", file=sys.stderr)
        sys.exit(1)

    recorder = Recorder(cfg["sample_rate"])
    _held = threading.Event()

    def on_press():
        if _held.is_set():
            return
        _held.set()
        recorder.start()

    def on_release():
        if not _held.is_set():
            return
        _held.clear()
        audio = recorder.stop()
        if audio is None or len(audio) < cfg["sample_rate"] * 0.3:
            print("[whisper-hook] too short, ignored", flush=True)
            return

        def transcribe_and_route():
            print("[whisper-hook] transcribing…", flush=True)
            text = _transcribe(audio, model, cfg["sample_rate"])
            if not text:
                print("[whisper-hook] empty transcript", flush=True)
                return
            print(f"[whisper-hook] → {text!r}", flush=True)
            if cfg.get("push_to_dialog"):
                _push(text, cfg["dialog_port"])
            if cfg.get("copy_to_clipboard"):
                _clip(text)

        threading.Thread(target=transcribe_and_route, daemon=True).start()

    keyboard.on_press_key(cfg["hold_key"].split("+")[-1], lambda _: on_press())
    keyboard.on_release_key(cfg["hold_key"].split("+")[-1], lambda _: on_release())

    print("[whisper-hook] listening. Ctrl+C to stop.", flush=True)
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\n[whisper-hook] stopped")


if __name__ == "__main__":
    main()
