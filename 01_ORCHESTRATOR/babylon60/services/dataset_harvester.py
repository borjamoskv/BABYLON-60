"""
[AX-2] TERMOMETRÍA DE DATASET: XTTS HARVESTER
Pipeline automatizado para segmentar y transcribir audio crudo
hacia el formato LJSpeech para Fine-Tuning.
"""
import os
import sys
from pathlib import Path
import csv

print("==================================================")
print("🎙️ INICIANDO DATA HARVESTER (XTTS DATASET PIPELINE)")
print("==================================================")

try:
    import whisper
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
except ImportError:
    print("[!] Faltan dependencias termodinámicas. Ejecuta:")
    print("    pip install openai-whisper pydub")
    sys.exit(1)

def build_dataset(raw_audio_dir: str, output_dir: str = "dataset_xtts"):
    raw_path = Path(raw_audio_dir).expanduser()
    out_path = Path(output_dir)
    wavs_path = out_path / "wavs"
    wavs_path.mkdir(parents=True, exist_ok=True)
    
    metadata_file = out_path / "metadata.csv"
    
    print(f"[*] Buscando audios en: {raw_path}")
    audio_files = list(raw_path.glob("**/*.wav")) + list(raw_path.glob("**/*.m4a"))
    
    if not audio_files:
        print("[!] No se encontraron archivos de audio. Revisa la ruta.")
        return

    print("[*] Cargando modelo Whisper (Turbo/Base) en memoria...")
    # Usamos base por velocidad en el prototyping. Para producción usar 'turbo'
    model = whisper.load_model("base")

    chunk_id = 0
    with open(metadata_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter='|')
        
        for audio_file in audio_files:
            print(f"\n[>] Procesando: {audio_file.name}")
            try:
                sound = AudioSegment.from_file(str(audio_file))
            except Exception as e:
                print(f"[!] Error leyendo {audio_file.name}: {e}")
                continue
                
            # Forzar a Mono y 22050Hz (Estricto para XTTS)
            sound = sound.set_channels(1).set_frame_rate(22050)
            
            print("  |-- Segmentando por silencios...")
            # split_on_silence requiere calibración fina empírica
            chunks = split_on_silence(sound, min_silence_len=500, silence_thresh=sound.dBFS-14, keep_silence=200)
            
            for chunk in chunks:
                if len(chunk) < 2000 or len(chunk) > 12000:
                    continue # Descartar fragmentos menores de 2s o mayores de 12s
                    
                chunk_filename = f"borja_{chunk_id:04d}.wav"
                chunk_filepath = wavs_path / chunk_filename
                chunk.export(str(chunk_filepath), format="wav")
                
                # Transcribir con Whisper
                result = model.transcribe(str(chunk_filepath), language="es")
                text = result["text"].strip()
                
                if text:
                    # Formato LJSpeech: file_name|text|normalized_text
                    writer.writerow([chunk_filename, text, text])
                    print(f"  [+] {chunk_filename} -> {text}")
                    chunk_id += 1

    print("\n✅ DATASET COMPLETADO.")
    print(f"Generados {chunk_id} fragmentos (Aprox {chunk_id * 5} segundos de exergía).")
    print(f"Ruta: {out_path.absolute()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python dataset_harvester.py <RUTA_DE_TUS_AUDIOS>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    build_dataset(target_dir)

