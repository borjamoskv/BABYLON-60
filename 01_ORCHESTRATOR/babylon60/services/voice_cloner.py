import torch

# [BYPASS] PyTorch 2.6 weights_only security patch para Coqui TTS
original_load = torch.load
def bypass_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = bypass_load

from TTS.api import TTS
import os

print("==================================================")
print("🔥 INICIALIZANDO TENSOR XTTS-v2 EN APPLE SILICON")
print("==================================================")
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"[*] Aceleración por hardware detectada: {device.upper()}")

print("[*] Levantando pesos neuronales...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

print("\n🎙️ Cargando firma acústica desde 'borja_sample.wav'...")
text = "Atención operador. Este es tu propio clon neuronal de alta exergía. El entorno acústico ha sido asimilado. El motor de consenso está asegurado."

tts.tts_to_file(
    text=text,
    speaker_wav="borja_sample.wav", 
    language="es", 
    file_path="borja_cloned_warning.wav"
)

print("\n✅ Síntesis termodinámica completa. Reproduciendo clon...")
os.system("afplay borja_cloned_warning.wav")
