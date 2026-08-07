# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess
import json
import wave

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
TEMP_DIR = os.path.join(PROJECT_DIR, "temp_audio")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

VOICE_CONFIGS = {
    "GON": {"voice": "Mónica", "rate": 200, "color": "#00F0FF", "avatar": "⏱️"},
    "CHICOTE": {"voice": "Rocko", "rate": 210, "color": "#FF3333", "avatar": "👨‍🍳"},
    "RASPUTIN": {"voice": "Grandpa", "rate": 150, "color": "#9933FF", "avatar": "🪆"},
    "CHE_JARANA": {"voice": "Eddy", "rate": 190, "color": "#FF9900", "avatar": "🎸"},
    "CARL_COX": {"voice": "Reed", "rate": 200, "color": "#00FF66", "avatar": "🎧"},
    "BLAN_COX": {"voice": "Flo", "rate": 160, "color": "#FF00FF", "avatar": "🌌"},
    "FRUSCIANTE": {"voice": "Reed", "rate": 150, "color": "#FFD700", "avatar": "🎸"},
    "FLEA": {"voice": "Rocko", "rate": 220, "color": "#FF6600", "avatar": "⚡"},
    "RAMONCIN": {"voice": "Jorge", "rate": 200, "color": "#FF0055", "avatar": "🕶️"},
    "HERMENEGILDO": {"voice": "Flo", "rate": 190, "color": "#00FFCC", "avatar": "🎹"},
    "EL_NOTA": {"voice": "Reed", "rate": 140, "color": "#CCCC00", "avatar": "🍹"},
    "ESCOHOTADO": {"voice": "Grandpa", "rate": 145, "color": "#D4AF37", "avatar": "💨"},
    "DR_POPPEL": {"voice": "Paulina", "rate": 180, "color": "#FFFF00", "avatar": "🔬"},
    "DON_SANTIAGO": {"voice": "Grandma", "rate": 140, "color": "#CC9966", "avatar": "🥖"},
    "KIMI_K3": {"voice": "Shelley", "rate": 210, "color": "#33FFFF", "avatar": "🤖"},
    "PAUSA": {"type": "silence", "duration": 2.8, "color": "#FFFFFF", "avatar": "⏳"}
}

# Dialogue Script Part 2 (The Sequel: La Rebelión de los Fotones)
DIALOGUE_SEQUEL = [
    ("GON", "¡Alerta general! ¡El Sindicato de la Hipervelocidad ha bloqueado la pausa de dos coma ocho segundos en toda la galaxia!"),
    ("CHICOTE", "¡Pero bueno! ¡¿Pero qué es esta marranada galáctica?! ¡Nos están metiendo petabytes de spam directamente en la corteza cerebral!"),
    ("KIMI_K3", "¡Chef Chicote! ¡Me he tenido que autodestruir el disco C y conectarme al bajo de Flea para salvar la dignidad!"),
    ("BLAN_COX", "Look at this... The only way to restore the pause is to travel to the supermassive black hole Sagittarius A... Amazing."),
    ("CARL_COX", "¡OH YES, OH YES! ¡Piloto Carl Cox al mando a ciento veintiocho BPM! ¡Rumbo al hoyo negro!"),
    ("FLEA", "¡BOOM! ¡Si el hoyo negro nos intenta tragar, le meto un slap a la constante gravitacional que lo pongo a bailar por funk!"),
    ("RASPUTIN", "¡No temáis al abismo! ¡Un hoyo negro es solo un pozo de agua fría si aplicas la pausa correcta!"),
    ("HERMENEGILDO", "¡Pausa todo el mundo! ¡El hoyo negro no destruye la materia! ¡El hoyo negro está afinado en Do menor armónico!"),
    ("EL_NOTA", "Woah, tíos... Habéis cruzado toda la galaxia con mucho estrés... The Dude abides, man. Tomad un Ruso Blanco de materia oscura."),
    ("DON_SANTIAGO", "El chorizo en gravedad cero sabe más curado."),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción. Mi cuerpo y mi mente son mi fortaleza inexpugnable. El Intervalo Prohibido es el espacio sagrado de la libertad."),
    ("FRUSCIANTE", "¡KA... ME... HA... ME... HAAAAAAAAAAAAAAAAAAAA!"),
    ("CARL_COX", "¡OH YES, OH YES! ¡Drop definitivo de la galaxia!"),
    ("FLEA", "¡Slap, drop and freedom!"),
    ("PAUSA", "PAUSA DE 2.8 SEGUNDOS — DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN"),
    ("BLAN_COX", "We are starstuff enjoying a two point eight second pause across the universe... Wonderful.")
]

def get_audio_duration(file_path):
    try:
        with wave.open(file_path, 'r') as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0.0

def generate_speech(dialogue_list, output_name):
    playlist_files = []
    subtitles = []
    current_time = 0.0
    fps = 30

    print(f"Generating audio tracks for {output_name}...")

    for idx, (speaker, text) in enumerate(dialogue_list):
        cfg = VOICE_CONFIGS[speaker]
        out_file = os.path.join(TEMP_DIR, f"{output_name}_{idx:03d}.wav")

        if speaker == "PAUSA":
            duration = cfg["duration"]
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                "-t", str(duration), "-acodec", "pcm_s16le", out_file
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        else:
            voice = cfg["voice"]
            rate = cfg["rate"]
            aiff_file = os.path.join(TEMP_DIR, f"temp_{output_name}_{idx:03d}.aiff")

            subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", aiff_file, text], check=True)

            cmd = [
                "ffmpeg", "-y", "-i", aiff_file,
                "-ar", "44100", "-ac", "1", "-acodec", "pcm_s16le", out_file
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(aiff_file):
                os.remove(aiff_file)

        duration = get_audio_duration(out_file)
        start_frame = int(round(current_time * fps))
        end_frame = int(round((current_time + duration) * fps))

        subtitles.append({
            "id": idx,
            "speaker": speaker,
            "avatar": cfg["avatar"],
            "color": cfg["color"],
            "text": text,
            "startTime": round(current_time, 2),
            "endTime": round(current_time + duration, 2),
            "startFrame": start_frame,
            "endFrame": end_frame
        })

        playlist_files.append(out_file)
        current_time += duration

    concat_list_path = os.path.join(TEMP_DIR, f"concat_{output_name}.txt")
    with open(concat_list_path, "w") as f:
        for p in playlist_files:
            f.write(f"file '{p}'\n")

    master_wav = os.path.join(PUBLIC_DIR, f"{output_name}_master.wav")
    print(f"Concatenating {output_name} master audio track...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", master_wav
    ], check=True)

    sub_path = os.path.join(PUBLIC_DIR, f"{output_name}_subtitles.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)

    total_frames = int(round(current_time * fps))
    print(f"DONE {output_name}! Duration: {current_time:.2f}s ({total_frames} frames at 30 fps)")

if __name__ == "__main__":
    generate_speech(DIALOGUE_SEQUEL, "sequel")
