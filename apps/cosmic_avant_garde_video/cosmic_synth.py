import numpy as np
import wave
import struct
import math
import os

def generate_cosmic_suite(output_wav_path, duration_sec=240, sr=48000):
    print(f"Generating Cosmic Avant-Garde Audio Suite ({duration_sec}s @ {sr}Hz)...")
    total_samples = duration_sec * sr
    time = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    # Pre-allocate stereo audio channels
    left = np.zeros(total_samples, dtype=np.float64)
    right = np.zeros(total_samples, dtype=np.float64)
    
    # -------------------------------------------------------------
    # MOVEMENT I: Singularity & Microtonal Vacuum [0s - 60s]
    # -------------------------------------------------------------
    print("Synthesizing Movement I: Singularity & Microtonal Vacuum...")
    m1_mask = (time >= 0) & (time < 65)
    t1 = time[m1_mask]
    
    # Sub-bass drone (32.7 Hz - C1, 65.4 Hz - C2) with slow pitch modulation
    f0 = 32.7 + 0.5 * np.sin(2 * np.pi * 0.05 * t1)
    sub_drone_l = 0.35 * np.sin(2 * np.pi * f0 * t1) + 0.15 * np.sin(2 * np.pi * f0 * 2.01 * t1)
    sub_drone_r = 0.35 * np.sin(2 * np.pi * f0 * 1.005 * t1) + 0.15 * np.sin(2 * np.pi * f0 * 1.995 * t1)
    
    # Microtonal Xenharmonic Cluster (24-TET micro-intervals: 100, 150, 225, 337.5 Hz)
    cluster_freqs = [100.0, 105.95, 141.42, 178.18, 224.5, 336.7]
    cluster_l = np.zeros_like(t1)
    cluster_r = np.zeros_like(t1)
    for idx, f in enumerate(cluster_freqs):
        pan = (idx / len(cluster_freqs))
        lfo = 0.1 * np.sin(2 * np.pi * (0.1 + idx * 0.03) * t1)
        sig = 0.08 * np.sin(2 * np.pi * (f + lfo) * t1)
        cluster_l += sig * (1.0 - pan)
        cluster_r += sig * pan

    # Filtered Cosmic Wind Noise
    noise = np.random.normal(0, 0.05, len(t1))
    wind_envelope = np.clip(t1 / 10.0, 0, 1) * np.clip((65.0 - t1) / 5.0, 0, 1)
    wind_lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t1)
    cosmic_wind = noise * wind_envelope * wind_lfo
    
    # Combine M1 with smooth fade in
    m1_env = np.clip(t1 / 3.0, 0, 1)
    left[m1_mask] += (sub_drone_l + cluster_l + cosmic_wind) * m1_env
    right[m1_mask] += (sub_drone_r + cluster_r + cosmic_wind) * m1_env
    
    # -------------------------------------------------------------
    # MOVEMENT II: Quantum Pulsar & Granular Starlight [60s - 135s]
    # -------------------------------------------------------------
    print("Synthesizing Movement II: Quantum Pulsar & Granular Starlight...")
    m2_mask = (time >= 55) & (time < 140)
    t2 = time[m2_mask]
    
    # Pulsar rhythm: 120 BPM = 0.5s per beat
    beat_period = 0.5
    beat_phase = (t2 % beat_period) / beat_period
    pulsar_click = np.exp(-40.0 * beat_phase) * np.sin(2 * np.pi * 880.0 * beat_phase) * 0.15
    pulsar_kick = np.exp(-15.0 * beat_phase) * np.sin(2 * np.pi * (55.0 - 30.0 * beat_phase) * beat_phase) * 0.35
    
    # Shepard-Risset ascending continuous tone
    shepard_l = np.zeros_like(t2)
    shepard_r = np.zeros_like(t2)
    for octave in range(1, 6):
        base_f = 55.0 * (2 ** octave)
        # pitch glissando over M2
        gliss = (t2 - 55.0) / 80.0
        freq = base_f * (2 ** (gliss % 1.0))
        # Gaussian amplitude bell curve centered around octave 3
        amp = np.exp(-0.5 * ((octave + (gliss % 1.0) - 3.5) / 1.2) ** 2) * 0.1
        shepard_l += amp * np.sin(2 * np.pi * freq * t2)
        shepard_r += amp * np.sin(2 * np.pi * freq * 1.003 * t2)
        
    m2_env = np.clip((t2 - 55.0) / 8.0, 0, 1) * np.clip((140.0 - t2) / 8.0, 0, 1)
    left[m2_mask] += (pulsar_kick + pulsar_click + shepard_l) * m2_env
    right[m2_mask] += (pulsar_kick + pulsar_click + shepard_r) * m2_env
    
    # -------------------------------------------------------------
    # MOVEMENT III: Event Horizon Bifurcation [135s - 195s]
    # -------------------------------------------------------------
    print("Synthesizing Movement III: Event Horizon Bifurcation...")
    m3_mask = (time >= 130) & (time < 200)
    t3 = time[m3_mask]
    
    # High energy FM synthesis (carrier & modulator)
    fc = 144.0  # Carrier frequency (D2)
    fm = 216.0  # Modulator frequency (3:2 ratio)
    mod_index = 3.5 + 2.5 * np.sin(2 * np.pi * 0.25 * t3)
    modulator = np.sin(2 * np.pi * fm * t3)
    fm_synth_l = 0.3 * np.sin(2 * np.pi * fc * t3 + mod_index * modulator)
    fm_synth_r = 0.3 * np.sin(2 * np.pi * (fc * 1.004) * t3 + mod_index * modulator)
    
    # Polyrhythmic cosmic percussion drops (every 1.5s and 0.75s)
    drop_phase = ((t3 - 130.0) % 1.5) / 1.5
    drop_kick = np.exp(-12.0 * drop_phase) * np.sin(2 * np.pi * (110.0 * (1.0 - drop_phase) + 35.0) * drop_phase) * 0.45
    
    # Metallic resonance ring mod
    metal_ring = 0.15 * np.sin(2 * np.pi * 1760.0 * t3) * np.sin(2 * np.pi * 110.0 * t3)
    
    m3_env = np.clip((t3 - 130.0) / 5.0, 0, 1) * np.clip((200.0 - t3) / 5.0, 0, 1)
    left[m3_mask] += (fm_synth_l + drop_kick + metal_ring) * m3_env
    right[m3_mask] += (fm_synth_r + drop_kick + metal_ring) * m3_env
    
    # -------------------------------------------------------------
    # MOVEMENT IV: Entropic Drift & Zero Exergy Return [195s - 240s]
    # -------------------------------------------------------------
    print("Synthesizing Movement IV: Entropic Drift & Zero Exergy Return...")
    m4_mask = (time >= 190) & (time <= 240)
    t4 = time[m4_mask]
    
    # Gentle decaying harmonic chord (C minor / microtonal shimmer)
    chord_freqs = [65.41, 130.81, 155.56, 196.00, 293.66, 392.00]
    decay_env = np.clip((240.0 - t4) / 50.0, 0, 1) ** 1.5
    chord_l = np.zeros_like(t4)
    chord_r = np.zeros_like(t4)
    
    for idx, cf in enumerate(chord_freqs):
        lfo = 0.05 * np.sin(2 * np.pi * (0.04 + idx * 0.01) * t4)
        sig = 0.08 * np.sin(2 * np.pi * (cf + lfo) * t4)
        pan = idx / len(chord_freqs)
        chord_l += sig * (1.0 - pan)
        chord_r += sig * pan

    m4_env = np.clip((t4 - 190.0) / 5.0, 0, 1) * decay_env
    left[m4_mask] += chord_l * m4_env
    right[m4_mask] += chord_r * m4_env

    # -------------------------------------------------------------
    # Master Limiter & Normalization (-1.0 dB FS peak)
    # -------------------------------------------------------------
    max_peak = max(np.max(np.abs(left)), np.max(np.abs(right)))
    if max_peak > 0:
        norm_factor = 0.90 / max_peak
        left *= norm_factor
        right *= norm_factor
        
    print(f"Master normalization applied. Peak level: {20 * np.log10(np.max(np.abs(left))):.2f} dBFS")

    # Write WAV file
    os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
    with wave.open(output_wav_path, 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sr)
        
        # Interleave channels
        audio_int16 = np.zeros((total_samples * 2,), dtype=np.int16)
        audio_int16[0::2] = (left * 32767.0).astype(np.int16)
        audio_int16[1::2] = (right * 32767.0).astype(np.int16)
        
        wav_file.writeframes(audio_int16.tobytes())

    print(f"WAV audio generated successfully: {output_wav_path}")

if __name__ == '__main__':
    out_path = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/apps/cosmic_avant_garde_video/assets/cosmic_avant_garde_suite.wav"
    generate_cosmic_suite(out_path, duration_sec=240, sr=48000)
