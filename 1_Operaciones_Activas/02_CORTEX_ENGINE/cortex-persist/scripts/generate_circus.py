# [C5-REAL] Exergy-Maximized
"""
cat_id: generate-circus
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import math
import struct
import wave

SAMPLE_RATE = 44100
AMPLITUDE_MAX = 32767.0

def square_wave(freq, t):
    return 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0

def sine_wave(freq, t):
    return math.sin(2.0 * math.pi * freq * t)

def generate_note(freq, duration, volume=0.3, osc_type='square'):
    num_samples = int(SAMPLE_RATE * duration)
    samples = []

    # Simple linear adsr
    attack = int(num_samples * 0.1)
    release = int(num_samples * 0.2)

    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE

        # Envelope
        if i < attack:
            env = float(i) / attack
        elif i > num_samples - release:
            env = float(num_samples - i) / release
        else:
            env = 1.0

        if osc_type == 'square':
            val = square_wave(freq, t)
        else:
            val = sine_wave(freq, t)

        samples.append(val * env * volume)
    return samples

def make_circus_loop():
    # 120 BPM: 1 beat = 0.5s. 4 beats per bar = 2.0s.
    # We will generate a 16-second loop (8 bars).
    bpm = 130
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4
    total_duration = bar_dur * 8 # 8 bars = ~14.7 seconds

    total_samples = int(SAMPLE_RATE * total_duration)
    master_mix = [0.0] * total_samples

    # Frequencies
    C3, E3, G3, _C4 = 130.81, 164.81, 196.00, 261.63
    G2, _B2, D3, G3_low = 98.00, 123.47, 146.83, 196.00

    # 1. Bass & Chord track (Oom-pah rhythm)
    time_offset = 0.0
    for bar in range(8):
        # Alternating C major and G major bars
        if bar % 2 == 0:
            # C major bar: Bass on 1 & 3, Chord on 2 & 4
            notes = [
                (C3, 0.25, 'sine', 0.5), # Oom
                (E3, 0.25, 'square', 0.15), # Pah (part of chord)
                (G3, 0.25, 'square', 0.15), # Pah
                (G2, 0.25, 'sine', 0.5), # Oom
                (E3, 0.25, 'square', 0.15), # Pah
                (G3, 0.25, 'square', 0.15)  # Pah
            ]
        else:
            # G major bar
            notes = [
                (G2, 0.25, 'sine', 0.5),
                (D3, 0.25, 'square', 0.15),
                (G3_low, 0.25, 'square', 0.15),
                (D3, 0.25, 'sine', 0.5),
                (D3, 0.25, 'square', 0.15),
                (G3_low, 0.25, 'square', 0.15)
            ]

        # Write rhythm notes
        bar_start = bar * bar_dur
        # Beat 1 (0.0), Beat 2 (0.5), Beat 3 (1.0), Beat 4 (1.5) in the bar
        rhythm_schedule = [
            (0.0, notes[0][0], notes[0][1], notes[0][2], notes[0][3]),
            (0.25, notes[1][0], notes[1][1], notes[1][2], notes[1][3]),
            (0.25, notes[2][0], notes[2][1], notes[2][2], notes[2][3]),
            (0.5, notes[3][0], notes[3][1], notes[3][2], notes[3][3]),
            (0.75, notes[4][0], notes[4][1], notes[4][2], notes[4][3]),
            (0.75, notes[5][0], notes[5][1], notes[5][2], notes[5][3]),
        ]

        # Actually oom-pah has 4 beats:
        # Beat 1 (bass): 0.0
        # Beat 2 (chord): 0.5 * beat_dur
        # Beat 3 (bass): 1.0 * beat_dur
        # Beat 4 (chord): 1.5 * beat_dur
        rhythm_schedule = [
            (0.0, notes[0][0], beat_dur * 0.9, 'sine', 0.4), # Bass C
            (beat_dur, notes[1][0], beat_dur * 0.8, 'square', 0.1), # Chord E
            (beat_dur, notes[2][0], beat_dur * 0.8, 'square', 0.1), # Chord G
            (beat_dur * 2, notes[3][0], beat_dur * 0.9, 'sine', 0.4), # Bass G
            (beat_dur * 3, notes[1][0], beat_dur * 0.8, 'square', 0.1), # Chord E
            (beat_dur * 3, notes[2][0], beat_dur * 0.8, 'square', 0.1), # Chord G
        ]

        for offset, freq, dur, osc, vol in rhythm_schedule:
            start_idx = int((bar_start + offset) * SAMPLE_RATE)
            note_s = generate_note(freq, dur, vol, osc)
            for idx, val in enumerate(note_s):
                if start_idx + idx < total_samples:
                    master_mix[start_idx + idx] += val

    # 2. Circus Melody (chromatic runs and jumps)
    # Let's program a funny chromatic melody: "Entry of the Gladiators" simplified
    melody = [
        # Bar 1 (C Major chromatic run up)
        (261.63, 0.25), (277.18, 0.25), (293.66, 0.25), (311.13, 0.25), # C, C#, D, D#
        (329.63, 0.5), (392.00, 0.5), (329.63, 1.0),                  # E, G, E
        # Bar 2 (G Major chromatic run down)
        (392.00, 0.25), (369.99, 0.25), (349.23, 0.25), (329.63, 0.25), # G, F#, F, E
        (293.66, 0.5), (349.23, 0.5), (293.66, 1.0),                  # D, F, D
        # Bar 3
        (261.63, 0.25), (277.18, 0.25), (293.66, 0.25), (311.13, 0.25),
        (329.63, 0.5), (392.00, 0.5), (523.25, 1.0),                  # E, G, C5
        # Bar 4
        (493.88, 0.5), (440.00, 0.5), (392.00, 0.5), (349.23, 0.5),   # B, A, G, F
        # Bar 5
        (329.63, 0.25), (349.23, 0.25), (392.00, 0.25), (440.00, 0.25), # E, F, G, A
        (523.25, 0.5), (392.00, 0.5), (523.25, 1.0),
        # Bar 6
        (493.88, 0.25), (466.16, 0.25), (440.00, 0.25), (415.30, 0.25),
        (392.00, 0.5), (349.23, 0.5), (392.00, 1.0),
        # Bar 7
        (329.63, 0.25), (349.23, 0.25), (392.00, 0.25), (440.00, 0.25),
        (523.25, 0.5), (392.00, 0.5), (523.25, 1.0),
        # Bar 8
        (587.33, 0.5), (493.88, 0.5), (523.25, 1.0)                   # D5, B4, C5
    ]

    time_offset = 0.0
    for note in melody:
        freq, beats = note
        dur = beats * beat_dur
        start_idx = int(time_offset * SAMPLE_RATE)
        # Bouncy square wave for melody
        note_s = generate_note(freq, dur * 0.85, 0.2, 'square') # 0.85 dur creates staccato feel
        for idx, val in enumerate(note_s):
            if start_idx + idx < total_samples:
                master_mix[start_idx + idx] += val
        time_offset += dur

    # Save file
    out_file = "public/circus_loop.wav"
    with wave.open(out_file, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

        for sample in master_mix:
            clipped_sample = max(-32768, min(32767, int(sample * AMPLITUDE_MAX)))
            wav_file.writeframes(struct.pack('h', clipped_sample))

    logging.getLogger(__name__).info(f"[C5-REAL] Generated circus loop at {out_file}")

if __name__ == "__main__":
    make_circus_loop()
