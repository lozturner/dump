"""
One-time synthetic training for the "hey claude" wake word model.
Generates ~500 TTS audio variations using Microsoft Edge TTS (free, no API key),
then trains a small ONNX binary classifier on top of openWakeWord embeddings.
Output: models/hey_claude.onnx  (~1-2 MB)
Run time: ~5-10 minutes on a modern CPU.
"""

import os
import sys
import pathlib
import subprocess

WAKE_PHRASE = "hey claude"
MODELS_DIR = pathlib.Path(__file__).parent / "models"
OUTPUT_MODEL = MODELS_DIR / "hey_claude.onnx"


def _ensure_edge_tts():
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])


def _generate_synthetic_audio(out_dir: pathlib.Path, n_samples: int = 500):
    import asyncio
    import edge_tts
    import random

    # Voices with varied accents / rates give robustness
    voices = [
        "en-US-GuyNeural",
        "en-US-JennyNeural",
        "en-GB-RyanNeural",
        "en-AU-WilliamNeural",
        "en-CA-LiamNeural",
    ]
    rates = ["-10%", "0%", "+10%", "+20%"]
    pitches = ["-5Hz", "0Hz", "+5Hz"]

    out_dir.mkdir(parents=True, exist_ok=True)

    async def _synth_one(idx: int):
        voice = random.choice(voices)
        rate = random.choice(rates)
        pitch = random.choice(pitches)
        path = out_dir / f"pos_{idx:04d}.wav"
        communicate = edge_tts.Communicate(
            WAKE_PHRASE, voice, rate=rate, pitch=pitch
        )
        await communicate.save(str(path))

    async def _run_all():
        tasks = [_synth_one(i) for i in range(n_samples)]
        # batch in groups of 20 to avoid hammering the endpoint
        for start in range(0, len(tasks), 20):
            batch = tasks[start : start + 20]
            await asyncio.gather(*batch)
            print(f"  generated {min(start + 20, n_samples)}/{n_samples} samples...")

    print(f"Generating {n_samples} synthetic audio samples for '{WAKE_PHRASE}'...")
    asyncio.run(_run_all())
    print(f"Saved to {out_dir}")


def _train(positive_dir: pathlib.Path):
    """
    Use openWakeWord's training utilities to fit a small binary classifier
    on top of the pre-computed audio embeddings. This requires openwakeword>=0.6.
    """
    try:
        from openwakeword.train import train_model
    except ImportError:
        print(
            "ERROR: This version of openwakeword does not expose train_model.\n"
            "Install with: pip install openwakeword>=0.6.0\n"
            "Or use the Colab notebook at:\n"
            "  https://github.com/dscripka/openWakeWord/blob/main/notebooks/custom_wakeword_model_training.ipynb"
        )
        sys.exit(1)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Training model... (this takes a few minutes)")
    train_model(
        positive_reference_clips=str(positive_dir),
        output_dir=str(MODELS_DIR),
        model_name="hey_claude",
        n_epochs=50,
        batch_size=128,
    )
    print(f"\nDone. Model saved to: {OUTPUT_MODEL}")


def main():
    if OUTPUT_MODEL.exists():
        print(f"Model already exists at {OUTPUT_MODEL}. Delete it to retrain.")
        return

    _ensure_edge_tts()

    positive_dir = MODELS_DIR / "positive_samples"
    _generate_synthetic_audio(positive_dir)
    _train(positive_dir)


if __name__ == "__main__":
    main()
