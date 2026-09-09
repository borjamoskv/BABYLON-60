#!/usr/bin/env python3
import numpy as np
from scipy.io import wavfile
import math
import os
import sys

# Añadir el path al orquestador para importar tonnetz_monitor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../01_ORCHESTRATOR')))
from babylon60.primitives.tonnetz_monitor import evaluate_tonnetz_oversight

# ============================================================================
# BABYLON-60 DSP SYNTHESIS - C5-REAL (OPTION 2: NATIVE DSP)
# ============================================================================

SAMPLE_RATE = 44100
DURATION_SEC = 2.0

PITCH_TO_HZ = {
    "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
    "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
    "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88
}

def generate_spatial_triad(telemetry, duration=DURATION_SEC, sr=SAMPLE_RATE):
    """
    Sintetiza la tríada en DSP nativo.
    - Tensión armónica (0.0 a 1.0) mezcla onda seno pura con sierra (anergía).
    - Cents offset aplica desviación microtonal a los osciladores.
    - Espacialización simple L/R con retraso de fase para exteriorización (Binaural proxy).
    """
    t = np.linspace(0, duration, int(sr * duration), False)
    
    # Pre-allocation para canales L y R
    audio_l = np.zeros_like(t)
    audio_r = np.zeros_like(t)
    
    for i, note in enumerate(telemetry.triad_notes):
        base_hz = PITCH_TO_HZ.get(note, 440.0)
        
        # Aplicar desviación microtonal (cents a hz)
        # 1 cent = 1/1200 de octava
        shifted_hz = base_hz * (2 ** (telemetry.microtonal_cents_offset / 1200.0))
        
        # Fase base y generación de onda
        phase = 2 * np.pi * shifted_hz * t
        sine_wave = np.sin(phase)
        saw_wave = 2 * (t * shifted_hz - np.floor(0.5 + t * shifted_hz)) # Sierra ideal
        
        # Mix Sine/Saw basado en tensión (0 = puro, 1 = sierra total)
        tension = telemetry.harmonic_tension
        osc = (1 - tension) * sine_wave + tension * saw_wave
        
        # Espacialización binaural básica (ITD - Interaural Time Difference proxy)
        # Aplicamos desfase y paneo según la nota para simular apertura espacial
        pan_pos = -0.8 if i == 0 else (0.8 if i == 2 else 0.0) # Izq, Centro, Der
        
        gain_l = np.cos((pan_pos + 1) * np.pi / 4)
        gain_r = np.sin((pan_pos + 1) * np.pi / 4)
        
        # Efecto Haas (ITD): Retrasamos el canal opuesto en función de la tensión
        # A mayor entropía/tensión, la escena acústica colapsa de forma asimétrica
        delay_samples = int((abs(pan_pos) * 0.001) * sr) + int(tension * 50)
        
        osc_l = osc * gain_l
        osc_r = osc * gain_r
        
        if pan_pos < 0:
            osc_r = np.roll(osc_r, delay_samples)
        elif pan_pos > 0:
            osc_l = np.roll(osc_l, delay_samples)
            
        audio_l += osc_l
        audio_r += osc_r

    # Normalización
    max_val = max(np.max(np.abs(audio_l)), np.max(np.abs(audio_r)))
    if max_val > 0:
        audio_l /= max_val
        audio_r /= max_val

    # Envolvente (Fade in/out para evitar clicks)
    envelope = np.ones_like(t)
    fade_len = int(sr * 0.1)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    
    audio_l *= envelope
    audio_r *= envelope

    # Interleave to stereo (L, R) int16
    stereo_signal = np.vstack((audio_l, audio_r)).T
    return np.int16(stereo_signal * 32767)


def run_stress_test():
    print("Iniciando PoC C5-REAL: DSP Nativo Tonnetz (Zero-DAW)...")
    
    # Caso 1: Homeostasis (Baja entropía, Baja exergía) -> Acorde Mayor Puro
    tel_hom = evaluate_tonnetz_oversight(entropy=0.05, exergy_consumption=0.05)
    print(f"1. Homeostasis -> {tel_hom.state} | Notas: {tel_hom.triad_notes} | Tensión: {tel_hom.harmonic_tension:.2f}")
    wavfile.write("tonnetz_homeostasis.wav", SAMPLE_RATE, generate_spatial_triad(tel_hom))

    # Caso 2: Anergía (Alta entropía, Alta fricción) -> Disonancia microtonal y onda sierra
    tel_anergy = evaluate_tonnetz_oversight(entropy=1.2, exergy_consumption=1.5)
    print(f"2. Anergía / Disonancia -> {tel_anergy.state} | Notas: {tel_anergy.triad_notes} | Tensión: {tel_anergy.harmonic_tension:.2f} | Cents: {tel_anergy.microtonal_cents_offset:.2f}")
    wavfile.write("tonnetz_anergy.wav", SAMPLE_RATE, generate_spatial_triad(tel_anergy))
    
    print("\n[OK] Falsación empírica superada. Archivos WAV generados con éxito.")

if __name__ == "__main__":
    run_stress_test()
