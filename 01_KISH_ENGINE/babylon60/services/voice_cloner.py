"""Isolated voice synthesis utility (excluded from wheel distribution).

Requires explicit CLI invocation; never monkey-patches torch.load globally
or downloads weights at import time.
"""

from __future__ import annotations

import subprocess


def run_voice_clone(
    speaker_wav: str = "borja_sample.wav",
    output_wav: str = "borja_cloned_warning.wav",
) -> None:
    import torch
    from TTS.api import TTS

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    text = (
        "Atención operador. Este es tu propio clon neuronal de alta exergía. "
        "El entorno acústico ha sido asimilado. El motor de consenso está asegurado."
    )
    tts.tts_to_file(text=text, speaker_wav=speaker_wav, language="es", file_path=output_wav)
    subprocess.run(["afplay", output_wav], check=False)


if __name__ == "__main__":
    run_voice_clone()
