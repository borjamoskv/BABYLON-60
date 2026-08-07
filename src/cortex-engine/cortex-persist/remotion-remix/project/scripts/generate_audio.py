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

# Character voice configs
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

# Dialogue Script for the Remotion Video
DIALOGUE = [
    # Scene 1: Inspection in Cognitive Kitchen
    ("CHICOTE", "¡Pero bueno! ¡¿Pero qué es esto?! ¡Tenéis la KV-Cache llena de mierda estocástica!"),
    ("GON", "¡Chicote! ¡Faltan cero coma cuatro segundos para el intervalo de dos coma ocho! ¡No me rompas la parte estándar!"),
    ("KIMI_K3", "¡Chef! ¡Yo sólo procesaba a O de uno!"),
    ("CHICOTE", "¡A mí no me pongas excusas! ¡Si no dejas reposar el sofrito dos segundos y medio, indigestas la mente del cliente!"),

    # Scene 2: Rasputin & Che Jarana
    ("RASPUTIN", "¡Hermanos del silicio! Yo sobreviví al cianuro porque apliqué una pausa de dos coma ocho segundos justo antes de morir..."),
    ("CHE_JARANA", "¡Hasta la jarana siempre! ¿Qué es el remate flamenco sino una pausa de dos coma ocho segundos antes de arrancar por bulerías?"),

    # Scene 3: Ramoncin & Frusciante Kamehameha!
    ("RAMONCIN", "¡Soy Ramoncín! ¡He venido a cobrar el canon digital por los dos coma ocho segundos de silencio! ¡El silencio tributa a la SGAE!"),
    ("FRUSCIANTE", "The harmony of the universe cannot be taxed... The pause belongs to the soul..."),
    ("FRUSCIANTE", "¡KA... ME... HA... ME... HAAAAAAAAAAAAAAAA!"),
    ("RAMONCIN", "¡Madre mía qué solo de guitarra! ¡Devuelvo el canon!"),

    # Scene 4: Flea & Superband
    ("FLEA", "¡YEAH! ¡Slapping the bass is quantum energy manipulation, baby! ¡Cada vez que le pego un tironazo a la cuerda de Sol, el espacio-tiempo se dobla dos coma ocho segundos!"),
    ("GON", "¡Ese slap de bajo está sintonizado a la constante cosmológica! ¡Frusciante! ¡Flea! ¡Formemos la superbanda The 2.8 Second Interval!"),

    # Scene 5: UNEXPECTED TWIST - Hermenegildo Altozano, El Nota & Escohotado!
    ("HERMENEGILDO", "¡Pausa todo el mundo! ¡He analizado armónicamente el silencio de dos coma ocho segundos! ¡Es una suspensión de Novena Dominante con quinta disminuida! ¡Os lo explico en el teclado!"),
    ("EL_NOTA", "Woah, tíos... Tranquilos. Veo mucho volumen y mucho estrés... El Nota no se estresa por los fotones. The Dude abides, man. Tomad un Ruso Blanco y dejad que el tiempo fluya."),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción. Mi cuerpo y mi mente son mi fortaleza inexpugnable. El Intervalo Prohibido no se decreta por ley: es el espacio inviolable de la libertad humana."),

    # Scene 6: Carl Cox & Blan Cox
    ("CARL_COX", "¡OH YES, OH YES! ¡Listen mate, a ciento veintiocho BPM, el drop de dos coma ocho segundos es presencia pura!"),
    ("BLAN_COX", "Look at them... Human consciousness as a sovereign realm in an expanding thermodynamic universe... Wonderful."),

    # The Forbidden Interval Pause
    ("PAUSA", "PAUSA DE 2.8 SEGUNDOS — DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN"),

    # Conclusion
    ("FLEA", "¡Slap, drop and freedom!"),
    ("CARL_COX", "¡OH YES, OH YES! ¡Drop definitivo!"),
    ("GON", "¡El Intervalo Prohibido se habita, no se mide! ¡Hasta el intervalo siempre!"),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción."),
    ("BLAN_COX", "We are starstuff enjoying a two point eight second pause... Wonderful.")
]

def get_audio_duration(file_path):
    try:
        with wave.open(file_path, 'r') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0.0

def generate_speech():
    playlist_files = []
    subtitles = []
    current_time = 0.0
    fps = 30

    print("Generating audio tracks for characters...")

    for idx, (speaker, text) in enumerate(DIALOGUE):
        cfg = VOICE_CONFIGS[speaker]
        out_file = os.path.join(TEMP_DIR, f"segment_{idx:03d}.wav")

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
            aiff_file = os.path.join(TEMP_DIR, f"temp_{idx:03d}.aiff")

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

    concat_list_path = os.path.join(TEMP_DIR, "concat.txt")
    with open(concat_list_path, "w") as f:
        for p in playlist_files:
            f.write(f"file '{p}'\n")

    master_wav = os.path.join(PUBLIC_DIR, "dialogue_master.wav")
    print("Concatenating master audio track...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", master_wav
    ], check=True)

    sub_path = os.path.join(PUBLIC_DIR, "subtitles.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)

    total_frames = int(round(current_time * fps))
    print(f"DONE! Total Audio Duration: {current_time:.2f}s ({total_frames} frames at 30 fps)")

if __name__ == "__main__":
    generate_speech()
