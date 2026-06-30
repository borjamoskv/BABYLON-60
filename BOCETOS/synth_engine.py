import math
import wave
import struct
import random
import os

# ==============================================================================
# ALGORITHMIC_MUSIC_OMEGA - C5-REAL Procedural Synthesis
# ==============================================================================
# Author: Borja Moskv (SYS_ID: borjamoskv)
# Aesthetic: Industrial Noir 2026
# Mechanism: Markov Chain + FM Synthesis -> Raw PCM Waveform (.wav)
# ==============================================================================

SAMPLE_RATE = 44100
DURATION = 15.0 # seconds
FILE_NAME = "omega_noir_sequence.wav"
FILE_PATH = os.path.join(os.path.dirname(__file__), FILE_NAME)

def generate_wave(freq, duration, envelope, fm_freq=0, fm_idx=0):
    samples = []
    num_samples = int(duration * SAMPLE_RATE)
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        
        # ADSR Envelope (Simplified Attack / Release)
        env_val = 1.0
        if t < envelope['A']:
            env_val = t / envelope['A']
        elif t > duration - envelope['R']:
            env_val = max(0.0, (duration - t) / envelope['R'])
            
        # FM Synthesis: Fundamental frequency + modulation
        modulation = fm_idx * math.sin(2.0 * math.pi * fm_freq * t)
        val = math.sin(2.0 * math.pi * freq * t + modulation)
        
        # Soft clipping & envelope application
        val = max(-1.0, min(1.0, val * env_val))
        samples.append(val)
    return samples

def write_wav(filename, samples):
    wav_file = wave.open(filename, 'w')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(SAMPLE_RATE)
    
    packed_data = bytearray()
    for sample in samples:
        int_sample = int(sample * 32767.0)
        # Structural packing for 16-bit PCM
        packed_data += struct.pack('h', int_sample)
        
    wav_file.writeframes(packed_data)
    wav_file.close()

def main():
    print("◈ ALGORITHMIC_MUSIC_OMEGA: Initiating C5-REAL Procedural Synthesis...")
    
    # Markov Chain generation for frequencies
    # Scale: Phrygian Dominant (Industrial Noir characteristic friction)
    base_freq = 55.0 # A1
    intervals = [1.0, 1.05946, 1.25992, 1.33484, 1.49831, 1.78180] # A, Bb, C#, D, E, G
    
    notes = []
    current_state = 0
    transition_matrix = [
        [0.1, 0.4, 0.1, 0.2, 0.1, 0.1],
        [0.3, 0.1, 0.4, 0.1, 0.1, 0.0],
        [0.1, 0.2, 0.1, 0.4, 0.2, 0.0],
        [0.1, 0.1, 0.2, 0.1, 0.4, 0.1],
        [0.2, 0.0, 0.1, 0.2, 0.1, 0.4],
        [0.5, 0.0, 0.0, 0.1, 0.2, 0.2]
    ]

    # Generate 30 structural note steps
    for _ in range(30):
        # Apply pseudo-random octave jumps
        octave_multiplier = random.choice([1, 2, 4, 8]) 
        freq = base_freq * intervals[current_state] * octave_multiplier
        notes.append(freq)
        
        # State transition evaluation
        rand_val = random.random()
        cumulative = 0.0
        for next_state, prob in enumerate(transition_matrix[current_state]):
            cumulative += prob
            if rand_val <= cumulative:
                current_state = next_state
                break

    print("◈ Synthesizing 30-step Markov Chain onto raw PCM buffer...")
    final_samples = []
    for idx, n_freq in enumerate(notes):
        # 0.5 sec per note. FM frequency tracks the fundamental (harmonic series).
        note_samples = generate_wave(
            n_freq, 
            duration=0.5, 
            envelope={'A': 0.05, 'R': 0.15}, 
            fm_freq=n_freq * 0.5, 
            fm_idx=3.0 # Metallic frequency modulation texture
        )
        final_samples.extend(note_samples)

    print(f"◈ Flushing binary PCM payload to disk: {FILE_NAME}")
    write_wav(FILE_PATH, final_samples)
    print("◈ Exergy sequence crystallized. Zero external dependencies.")

if __name__ == "__main__":
    main()
