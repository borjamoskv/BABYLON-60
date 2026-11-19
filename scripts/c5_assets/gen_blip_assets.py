#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import wave
import struct
import math
import os


def generate_square_wave(freq, duration, sample_rate=44100, volume=0.5):
    num_samples = int(sample_rate * duration)
    wave_data = bytearray()

    for i in range(num_samples):
        t = i / sample_rate
        # Onda cuadrada
        value = volume if math.sin(2 * math.pi * freq * t) > 0 else -volume

        # Envelope para evitar el 'clic' seco al final del audio
        envelope = 1.0
        if i > num_samples - 200:
            envelope = (num_samples - i) / 200.0

        sample = int(value * envelope * 32767)
        wave_data.extend(struct.pack("<h", sample))

    return wave_data


def save_wav(filename, wave_data, sample_rate=44100) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(wave_data)


if __name__ == "__main__":
    # Generar un blip clásico de 8-bits, 800Hz, cortísimo (0.04 segs) para repetirlo
    wave_data = generate_square_wave(800, 0.04, volume=0.2)
    output_path = "web/public/audio/blip.wav"
    save_wav(output_path, wave_data)
    print(f"Onda cuadrada generada y guardada en {output_path}")
