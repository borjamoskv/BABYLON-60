#!/usr/bin/env python3
"""
Experimento 2: Síntesis sonora procedural PCM + Cadenas de Markov (C5-REAL).
"""

import math
import struct
import wave


def generate_markov_pcm(filename: str = "cortex/laboratory/segundo_experimento_c5/synth.wav") -> None:
    sample_rate = 44100
    duration = 3.0
    num_samples = int(sample_rate * duration)

    frequencies = [220.0, 277.18, 329.63, 440.0]  # A3, C#4, E4, A4
    transitions = {
        0: [0.1, 0.4, 0.4, 0.1],
        1: [0.3, 0.1, 0.4, 0.2],
        2: [0.2, 0.3, 0.1, 0.4],
        3: [0.4, 0.2, 0.3, 0.1],
    }

    current_state = 0
    phase = 0.0
    pcm_data = bytearray()

    for i in range(num_samples):
        if i % 4410 == 0:  # Cambiar estado cada 100ms
            probs = transitions[current_state]
            r = (i * 17 + 31) % 100 / 100.0
            cum = 0.0
            for idx, p in enumerate(probs):
                cum += p
                if r <= cum:
                    current_state = idx
                    break

        freq = frequencies[current_state]
        phase += 2.0 * math.pi * freq / sample_rate
        value = int(16384.0 * math.sin(phase))
        pcm_data.extend(struct.pack("<h", value))

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)

    print(f"✅ Archivo PCM grabado en: {filename}")


if __name__ == "__main__":
    generate_markov_pcm()
