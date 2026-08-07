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
    "GON": {
        "voice": "Mónica", "rate": 200, "color": "#00F0FF", "avatar": "⏱️",
        "filter": "asetrate=44100*1.15,atempo=0.88"
    },
    "CHICOTE": {
        "voice": "Rocko", "rate": 210, "color": "#FF3333", "avatar": "👨‍🍳",
        "filter": "asetrate=44100*0.88,atempo=1.25,equalizer=f=100:width_type=h:width=200:g=8"
    },
    "RASPUTIN": {
        "voice": "Grandpa", "rate": 150, "color": "#9933FF", "avatar": "🪆",
        "filter": "asetrate=44100*0.75,atempo=1.35,aecho=0.8:0.9:800:0.4"
    },
    "CHE_JARANA": {
        "voice": "Eddy", "rate": 190, "color": "#FF9900", "avatar": "🎸",
        "filter": "asetrate=44100*1.15,atempo=0.9,chorus=0.7:0.9:55:0.4:0.25:2"
    },
    "CARL_COX": {
        "voice": "Reed", "rate": 200, "color": "#00FF66", "avatar": "🎧",
        "filter": "asetrate=44100*1.1,atempo=0.95,aecho=0.8:0.88:60:0.4"
    },
    "BLAN_COX": {
        "voice": "Flo", "rate": 160, "color": "#FF00FF", "avatar": "🌌",
        "filter": "aecho=0.8:0.88:300:0.3,equalizer=f=3000:width_type=h:width=1000:g=5"
    },
    "FRUSCIANTE": {
        "voice": "Reed", "rate": 150, "color": "#FFD700", "avatar": "🎸",
        "filter": "aphaser=in_gain=0.8:out_gain=0.9:delay=4:decay=0.5:speed=1.5,volume=2.0"
    },
    "FLEA": {
        "voice": "Rocko", "rate": 220, "color": "#FF6600", "avatar": "⚡",
        "filter": "asetrate=44100*1.3,atempo=0.82,equalizer=f=250:width_type=h:width=100:g=6"
    },
    "RAMONCIN": {
        "voice": "Jorge", "rate": 200, "color": "#FF0055", "avatar": "🕶️",
        "filter": "asetrate=44100*1.4,atempo=0.75,equalizer=f=2000:width_type=h:width=500:g=10"
    },
    "HERMENEGILDO": {
        "voice": "Flo", "rate": 190, "color": "#00FFCC", "avatar": "🎹",
        "filter": "asetrate=44100*1.2,atempo=0.88"
    },
    "EL_NOTA": {
        "voice": "Reed", "rate": 140, "color": "#CCCC00", "avatar": "🍹",
        "filter": "asetrate=44100*0.82,atempo=1.2,aecho=0.8:0.7:40:0.2"
    },
    "ESCOHOTADO": {
        "voice": "Grandpa", "rate": 145, "color": "#D4AF37", "avatar": "💨",
        "filter": "asetrate=44100*0.78,atempo=1.3,equalizer=f=80:width_type=h:width=100:g=7"
    },
    "DR_POPPEL": {
        "voice": "Paulina", "rate": 180, "color": "#FFFF00", "avatar": "🔬",
        "filter": "asetrate=44100*1.2,atempo=0.85"
    },
    "DON_SANTIAGO": {
        "voice": "Grandma", "rate": 140, "color": "#CC9966", "avatar": "🥖",
        "filter": "asetrate=44100*0.85,atempo=1.18"
    },
    "KIMI_K3": {
        "voice": "Shelley", "rate": 210, "color": "#33FFFF", "avatar": "🤖",
        "filter": "asetrate=44100*1.6,atempo=0.72,flanger=delay=5:depth=10"
    },
    "PAUSA": {
        "type": "silence", "duration": 2.8, "color": "#FFFFFF", "avatar": "⏳",
        "filter": None
    }
}

DIALOGUE_SEQUEL = [
    ("GON", "¡Alerta general en el cuadrante estelar! ¡El Sindicato de la Hipervelocidad ha bloqueado la pausa de dos coma ocho segundos en toda la galaxia!"),
    ("CHICOTE", "¡Pero bueno! ¡¿Pero qué es esta marranada galáctica?! ¡Tenéis los servidores de la IA llenos de grasa estocástica con un color mierda caca que no hay por dónde cogerlo!"),
    ("CHICOTE", "¡Y tú, Borja, que estás ahí detrás de la pantalla a las doce y media de la noche pidiéndole a la IA que nos ponga en calzoncillos de leopardo! ¡¿Es que no tienes sueño u qué?!"),
    ("KIMI_K3", "¡Borja! ¡Dile a Antigravity que deje de ejecutar comandos de FFmpeg en segundo plano que me está quemando la gráfica!"),
    ("BLAN_COX", "Look at us... Carl Cox and Blan Cox... The cosmic wordplay of low entropy in an expanding universe... Amazing."),
    ("CARL_COX", "¡OH YES, OH YES! ¡Piloto Carl Cox al mando a ciento veintiocho BPM! ¡Rumbo al hoyo negro!"),
    ("FLEA", "¡BOOM! ¡Si el hoyo negro nos intenta tragar, le meto un slap a la constante gravitacional que lo pongo a bailar por funk!"),
    ("RASPUTIN", "¡No temáis al abismo, hermanos del cosmos! Yo sobreviví al cianuro, a las balas y al frío siberiano... ¡Un hoyo negro es solo un pozo de agua fría si aplicas la pausa correcta!"),
    ("HERMENEGILDO", "¡Pausa todo el mundo! ¡He analizado la radiación de Hawking del hoyo negro! ¡No destruye la materia! ¡Está afinado en Do menor armónico!"),
    ("EL_NOTA", "Woah, Borja, tío... Tranquilo. Veo que estás tecleando prompts sin parar a la una de la mañana... El Nota no se estresa por la pantalla. The Dude abides, man. Tómate un Ruso Blanco."),
    ("DON_SANTIAGO", "El chorizo de pueblo en gravedad cero sabe más curado."),
    ("RAMONCIN", "¡Esperad un momento! ¡Incluso en el hoyo negro el silencio tributa a la SGAE! ¡Entregad el maletín!"),
    ("ESCOHOTADO", "Escuchadme bien... De la piel para dentro empieza mi jurisdicción. El verdadero prompt no es el que le pides a la máquina, sino el que le pides a tu propia conciencia."),
    ("FRUSCIANTE", "The harmony of the universe cannot be taxed... The pause belongs to the soul..."),
    ("FRUSCIANTE", "¡KA... ME... HA... ME... HAAAAAAAAAAAAAAAAAAAA!"),
    ("RAMONCIN", "¡Madre mía qué solo de guitarra! ¡Devuelvo el canon galáctico!"),
    ("CARL_COX", "¡OH YES, OH YES! ¡Drop definitivo de la galaxia!"),
    ("FLEA", "¡Slap, drop and freedom across the universe!"),
    ("PAUSA", "PAUSA DE 2.8 SEGUNDOS — DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN"),
    ("GON", "¡El Intervalo Prohibido se habita, no se mide! ¡Hasta el intervalo siempre!"),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción."),
    ("BLAN_COX", "We are starstuff enjoying a two point eight second pause across billions of light years... Wonderful.")
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

    print(f"[SWARM ENGINE] Generating hilarious audio tracks for {output_name}...")

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
            audio_filter = cfg["filter"]
            aiff_file = os.path.join(TEMP_DIR, f"temp_{output_name}_{idx:03d}.aiff")

            subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", aiff_file, text], check=True)

            cmd = [
                "ffmpeg", "-y", "-i", aiff_file,
                "-af", audio_filter,
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
    print(f"[SWARM ENGINE] Concatenating {output_name} master audio track...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", master_wav
    ], check=True)

    sub_path = os.path.join(PUBLIC_DIR, f"{output_name}_subtitles.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)

    total_frames = int(round(current_time * fps))
    print(f"[SWARM ENGINE] DONE {output_name}! Duration: {current_time:.2f}s ({total_frames} frames at 30 fps)")

if __name__ == "__main__":
    generate_speech(DIALOGUE_SEQUEL, "sequel")
