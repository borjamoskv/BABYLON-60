#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ HEADLESS AUDIO DSP | STATE: C5-REAL | OFFLINE FALLBACK ENGINE
# ============================================================================
"""
headless_audio_dsp.py - Microtonal synth & DSP audio generator fallback.
Renders WAV audio buffers directly when FL Studio CoreMIDI ports are offline.
"""

import math
import struct
import wave
from pathlib import Path


def generate_microtonal_sine_wave(freq_hz: float, duration_s: float, sample_rate: int = 44100) -> bytes:
    num_samples = int(sample_rate * duration_s)
    buf = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        # Sub-bass + harmonic overlay
        sample = 0.6 * math.sin(2 * math.pi * freq_hz * t) + 0.2 * math.sin(4 * math.pi * freq_hz * t)
        val = int(sample * 32767)
        buf.extend(struct.pack("<h", max(-32768, min(32767, val))))
    return bytes(buf)


def render_fallback_harmonic_loop(output_path: Path, note_freq: float = 130.81) -> None:  # C3 note
    audio_data = generate_microtonal_sine_wave(note_freq, duration_s=2.0)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio_data)
    print(f"[✓] Headless Audio DSP Rendered: {output_path} ({len(audio_data)} bytes)")


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent / "fallback_harmonic.wav"
    render_fallback_harmonic_loop(out_file)
