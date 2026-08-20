import numpy as np
import scipy.io.wavfile as wavfile
import os

class XenarmoniaEngine:
    """
    Motor DSP C5-REAL para síntesis xenarmónica y microtonal.
    """
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.base_freq = 440.0 # A4
        # C4 (MIDI 60) calculado desde A4 (MIDI 69)
        self.c4_freq = 440.0 * (2.0 ** (-9.0 / 12.0))

    def cents_to_ratio(self, cents):
        return 2.0 ** (cents / 1200.0)

    def generate_scl(self, name, description, cents_array, output_path):
        """
        Genera archivo Scala (.scl) compatible con FL Studio (Fruity Keyboard Controller, Harmor)
        y sintetizadores VST compatibles (Serum, Vital, Omnisphere).
        """
        with open(output_path, 'w') as f:
            f.write(f"! {name}.scl\n")
            f.write(f"! Generado por C5-REAL Xenarmonia DSP Engine\n")
            f.write(f"!\n")
            f.write(f"{description}\n")
            f.write(f"{len(cents_array)}\n")
            f.write(f"!\n")
            for cents in cents_array:
                f.write(f"{cents:.5f}\n")
        print(f"[*] Escala Scala exportada: {output_path}")

    def synthesize_tone(self, freq, duration=0.5, volume=0.5, waveform='sawtooth'):
        """Sintetiza un oscilador básico con envolvente ADSR para evitar clicks."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        if waveform == 'sine':
            signal = np.sin(freq * t * 2 * np.pi)
        elif waveform == 'sawtooth':
            signal = 2 * (freq * t - np.floor(0.5 + freq * t))
        else:
            signal = np.sin(freq * t * 2 * np.pi)
            
        # Envolvente suave
        attack = 0.05
        release = 0.1
        env = np.ones_like(t)
        
        attack_samples = int(attack * self.sample_rate)
        if attack_samples > 0:
            env[:attack_samples] = np.linspace(0, 1, attack_samples)
            
        release_samples = int(release * self.sample_rate)
        if release_samples > 0:
            env[-release_samples:] = np.linspace(1, 0, release_samples)
            
        return signal * env * volume

    def synthesize_sequence(self, freqs, duration_per_note=0.4):
        """Secuencia una lista de frecuencias en un único array de audio."""
        sequence = []
        for f in freqs:
            tone = self.synthesize_tone(f, duration=duration_per_note, waveform='sawtooth')
            sequence.append(tone)
            # Silencio entre notas
            rest = np.zeros(int(self.sample_rate * 0.1))
            sequence.append(rest)
            
        return np.concatenate(sequence)

    def save_wav(self, signal, filepath):
        """Exporta array a archivo WAV 16-bit PCM."""
        # Normalización a 16-bit
        signal = np.int16(signal / np.max(np.abs(signal)) * 32767)
        wavfile.write(filepath, self.sample_rate, signal)
        print(f"[*] Audio generado: {filepath}")

def main():
    engine = XenarmoniaEngine()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n--- INICIANDO MOTOR XENARMÓNICO C5-REAL ---\n")
    
    # 1. Escala Mayor 12-TET (Jónico Estándar)
    # C D E F G A B C
    major_12tet_cents = [200.0, 400.0, 500.0, 700.0, 900.0, 1100.0, 1200.0]
    
    # 2. Makam Rast (Aproximación Microtonal)
    # El Makam Rast disminuye el 3er y 7mo grado (E y B) en aproximadamente 1 coma (aprox ~50 cents)
    makam_rast_cents = [200.0, 350.0, 500.0, 700.0, 900.0, 1050.0, 1200.0]
    
    # 3. Escala Pelog (Gamelán Indonesio - 7 Notas Xenarmónicas)
    # No coincide con ninguna nota del piano estándar.
    pelog_cents = [120.0, 275.0, 540.0, 670.0, 785.0, 950.0, 1200.0]
    
    # Exportar formatos .scl para producción externa (FL Studio, Serum)
    engine.generate_scl("12TET_Major", "Escala Mayor 12-TET de Referencia", major_12tet_cents, os.path.join(out_dir, "12TET_Major.scl"))
    engine.generate_scl("Makam_Rast", "Makam Rast (E y B -50c microtonal)", makam_rast_cents, os.path.join(out_dir, "Makam_Rast.scl"))
    engine.generate_scl("Pelog_Gamelan", "Afinacion Pelog (Indonesia)", pelog_cents, os.path.join(out_dir, "Pelog.scl"))
    
    # Cálculo vectorial de Frecuencias Reales (Hz)
    c4 = engine.c4_freq
    freqs_12tet = [c4 * engine.cents_to_ratio(c) for c in [0] + major_12tet_cents]
    freqs_rast  = [c4 * engine.cents_to_ratio(c) for c in [0] + makam_rast_cents]
    freqs_pelog = [c4 * engine.cents_to_ratio(c) for c in [0] + pelog_cents]
    
    print("\n--- INICIANDO SÍNTESIS DSP ---")
    
    # Generar audios
    audio_12tet = engine.synthesize_sequence(freqs_12tet)
    engine.save_wav(audio_12tet, os.path.join(out_dir, "1_demo_12TET.wav"))
    
    audio_rast = engine.synthesize_sequence(freqs_rast)
    engine.save_wav(audio_rast, os.path.join(out_dir, "2_demo_Makam_Rast.wav"))
    
    audio_pelog = engine.synthesize_sequence(freqs_pelog)
    engine.save_wav(audio_pelog, os.path.join(out_dir, "3_demo_Pelog.wav"))
    
    # Generar pista A/B Comparativa (Alta fricción cognitiva por disonancia de memoria)
    comparativa = np.concatenate([
        audio_12tet, np.zeros(engine.sample_rate), 
        audio_rast, np.zeros(engine.sample_rate),
        audio_pelog
    ])
    engine.save_wav(comparativa, os.path.join(out_dir, "4_demo_Comparativa_A_B_C.wav"))
    
    print("\n[+] Bucle de síntesis completado. Archivos listos para auditoría sónica.")

if __name__ == "__main__":
    main()
