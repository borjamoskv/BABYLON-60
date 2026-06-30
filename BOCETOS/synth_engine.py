import math
import wave
import struct
import random
import os

# ==============================================================================
# ALGORITHMIC_MUSIC_OMEGA - V2.0 (Structural Improvement)
# ==============================================================================
# Author: Borja Moskv (SYS_ID: borjamoskv)
# Enhancements: Polyphony, Stereo Space, Native Delay Buffer, Exp. Envelopes
# ==============================================================================

SAMPLE_RATE = 44100
DURATION = 20.0
FILE_NAME = "omega_noir_v2.wav"
FILE_PATH = os.path.join(os.path.dirname(__file__), FILE_NAME)

def exp_envelope(t, duration, attack, release):
    if t < attack:
        return (math.exp(t / attack * 5.0) - 1.0) / (math.exp(5.0) - 1.0)
    elif t > duration - release:
        rem = duration - t
        return (math.exp(rem / release * 5.0) - 1.0) / (math.exp(5.0) - 1.0)
    return 1.0

def generate_poly_wave(frequencies, duration, envelopes, fm_params, pan=0.5):
    # pan: 0.0=left, 1.0=right
    num_samples = int(duration * SAMPLE_RATE)
    samples_L = []
    samples_R = []
    
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        val = 0.0
        
        for idx, freq in enumerate(frequencies):
            env_val = exp_envelope(t, duration, envelopes[idx]['A'], envelopes[idx]['R'])
            fm_freq, fm_idx = fm_params[idx]
            modulation = fm_idx * math.sin(2.0 * math.pi * fm_freq * t)
            osc = math.sin(2.0 * math.pi * freq * t + modulation)
            val += osc * env_val
        
        # Soft clip and average
        val = max(-1.0, min(1.0, val / len(frequencies)))
        
        samples_L.append(val * (1.0 - pan))
        samples_R.append(val * pan)
        
    return samples_L, samples_R

def apply_delay(samples, delay_time=0.375, feedback=0.4):
    delay_samples = int(delay_time * SAMPLE_RATE)
    out = list(samples)
    for i in range(delay_samples, len(samples)):
        out[i] += out[i - delay_samples] * feedback
        # Hard Clip to avoid digital distortion accumulation
        out[i] = max(-1.0, min(1.0, out[i]))
    return out

def write_wav_stereo(filename, samples_L, samples_R):
    wav_file = wave.open(filename, 'w')
    wav_file.setnchannels(2)
    wav_file.setsampwidth(2)
    wav_file.setframerate(SAMPLE_RATE)
    
    packed_data = bytearray()
    for l, r in zip(samples_L, samples_R):
        int_l = int(l * 32767.0)
        int_r = int(r * 32767.0)
        packed_data += struct.pack('h', int_l)
        packed_data += struct.pack('h', int_r)
        
    wav_file.writeframes(packed_data)
    wav_file.close()

def main():
    print("◈ ALGORITHMIC_MUSIC_OMEGA V2: Deep Structural Generation...")
    
    base_freq = 55.0 # A1
    intervals = [1.0, 1.05946, 1.25992, 1.33484, 1.49831, 1.78180] 
    
    transition_matrix = [
        [0.1, 0.4, 0.1, 0.2, 0.1, 0.1],
        [0.3, 0.1, 0.4, 0.1, 0.1, 0.0],
        [0.1, 0.2, 0.1, 0.4, 0.2, 0.0],
        [0.1, 0.1, 0.2, 0.1, 0.4, 0.1],
        [0.2, 0.0, 0.1, 0.2, 0.1, 0.4],
        [0.5, 0.0, 0.0, 0.1, 0.2, 0.2]
    ]

    current_state = 0
    buffer_L = []
    buffer_R = []
    
    print("◈ Multiplexing Drone & Arpeggio with Markov state machine...")
    for step in range(40):
        # Drone (Pedal Point A1) stays fixed for atmospheric depth
        drone_freq = base_freq
        
        # Arpeggio logic
        octave_multiplier = random.choice([2, 4, 8]) 
        arp_freq = base_freq * intervals[current_state] * octave_multiplier
        
        # Spatial placement logic (sine pan modulation)
        pan = 0.5 + 0.4 * math.sin(step * 0.5)
        
        s_L, s_R = generate_poly_wave(
            frequencies=[drone_freq, arp_freq],
            duration=0.5,
            envelopes=[{'A': 0.1, 'R': 0.4}, {'A': 0.02, 'R': 0.2}],
            fm_params=[(drone_freq*2, 1.5), (arp_freq*0.5, 2.0)],
            pan=pan
        )
        
        buffer_L.extend(s_L)
        buffer_R.extend(s_R)
        
        rand_val = random.random()
        cumulative = 0.0
        for next_state, prob in enumerate(transition_matrix[current_state]):
            cumulative += prob
            if rand_val <= cumulative:
                current_state = next_state
                break

    print("◈ Applying Native DSP: Ping-Pong Delay Echoes...")
    # Asymmetric delays for structural stereo width
    buffer_L = apply_delay(buffer_L, delay_time=0.375, feedback=0.45)
    buffer_R = apply_delay(buffer_R, delay_time=0.500, feedback=0.40)

    print(f"◈ Flushing Stereo binary PCM payload to disk: {FILE_NAME}")
    write_wav_stereo(FILE_PATH, buffer_L, buffer_R)
    print("◈ C5-REAL Exergy crystallized.")

if __name__ == "__main__":
    main()
