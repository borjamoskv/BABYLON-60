# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess
import json
import wave
import shutil
from concurrent.futures import ThreadPoolExecutor

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
TEMP_DIR = os.path.join(PROJECT_DIR, "temp_audio_gon_fiction")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# CALM, RELAXED & HUMANIZED VOICE CONFIGS (TTS Rate: 85-105 WPM, atempo <= 0.88)
VOICE_CONFIGS = {
    "GON": {
        "voice": "Mónica", "rate": 95, "color": "#00F0FF", "avatar": "🚲",
        "filter": "asetrate=44100*1.05,atempo=0.85"
    },
    "CHICOTE": {
        "voice": "Jorge", "rate": 90, "color": "#FF3333", "avatar": "👨‍🍳",
        "filter": "asetrate=44100*0.82,atempo=0.88,equalizer=f=100:width_type=h:width=200:g=6"
    },
    "RASPUTIN": {
        "voice": "Grandpa", "rate": 80, "color": "#9933FF", "avatar": "🪆",
        "filter": "asetrate=44100*0.75,atempo=0.88,aecho=0.8:0.9:800:0.4"
    },
    "CHE_JARANA": {
        "voice": "Eddy", "rate": 90, "color": "#FF9900", "avatar": "🎸",
        "filter": "asetrate=44100*1.05,atempo=0.85,chorus=0.7:0.9:55:0.4:0.25:2"
    },
    "CARL_COX": {
        "voice": "Reed", "rate": 95, "color": "#00FF66", "avatar": "🎧",
        "filter": "asetrate=44100*1.02,atempo=0.88,aecho=0.8:0.88:60:0.4"
    },
    "BLAN_COX": {
        "voice": "Flo", "rate": 85, "color": "#FF00FF", "avatar": "🌌",
        "filter": "atempo=0.82,aecho=0.8:0.88:300:0.3,equalizer=f=3000:width_type=h:width=1000:g=4"
    },
    "FRUSCIANTE": {
        "voice": "Reed", "rate": 90, "color": "#FFD700", "avatar": "🎸",
        "filter": "atempo=0.85,aphaser=in_gain=0.8:out_gain=0.9:delay=4:decay=0.5:speed=1.5,volume=1.8"
    },
    "FLEA": {
        "voice": "Rocko", "rate": 100, "color": "#FF6600", "avatar": "⚡",
        "filter": "asetrate=44100*1.1,atempo=0.82,equalizer=f=250:width_type=h:width=100:g=5"
    },
    "RAMONCIN": {
        "voice": "Jorge", "rate": 90, "color": "#FF0055", "avatar": "🕶️",
        "filter": "asetrate=44100*1.15,atempo=0.80,equalizer=f=2000:width_type=h:width=500:g=8"
    },
    "HERMENEGILDO": {
        "voice": "Flo", "rate": 90, "color": "#00FFCC", "avatar": "🎹",
        "filter": "asetrate=44100*1.08,atempo=0.85"
    },
    "EL_NOTA": {
        "voice": "Reed", "rate": 78, "color": "#CCCC00", "avatar": "🍹",
        "filter": "asetrate=44100*0.82,atempo=0.85,aecho=0.8:0.7:40:0.2"
    },
    "ESCOHOTADO": {
        "voice": "Grandpa", "rate": 75, "color": "#D4AF37", "avatar": "💨",
        "filter": "asetrate=44100*0.78,atempo=0.88,equalizer=f=80:width_type=h:width=100:g=7"
    },
    "DR_POPPEL": {
        "voice": "Paulina", "rate": 95, "color": "#FFFF00", "avatar": "🔬",
        "filter": "asetrate=44100*1.08,atempo=0.85"
    },
    "DON_SANTIAGO": {
        "voice": "Grandma", "rate": 80, "color": "#CC9966", "avatar": "🥖",
        "filter": "asetrate=44100*0.82,atempo=0.88"
    },
    "KIMI_K3": {
        "voice": "Shelley", "rate": 95, "color": "#33FFFF", "avatar": "🤖",
        "filter": "asetrate=44100*1.2,atempo=0.78,flanger=delay=5:depth=10"
    },
    "PAUSA": {
        "type": "silence", "duration": 4.0, "color": "#FFFFFF", "avatar": "⏳",
        "filter": None
    }
}

DIALOGUE_GON_FICTION = [
    # ACT I
    ("GON", "¡Chicote, hermano! ¡Siente la curvatura del espacio-tiempo bilbaíno! ¡Las baldosas de Bilbao no son de cemento, son tensores de memoria compartida sin lock! ¡Estamos flotando sobre la ría, tú!"),
    ("CHICOTE", "¡¿Qué flotando ni qué niño muerto, Gon?! ¡Apreta los pedales que nos comemos el contenedor del reciclaje! ¡Pero bueno! ¡¿Y tú qué te has tomado en el bar de la esquina?! ¡Tienes las pupilas como platos de chuletón!"),
    ("GON", "¡Un cartón de C5-REAL, Chicote! ¿Ves la luz neón ultravioleta? ¿Sabes cómo le llaman al Royale con Queso en Bilbao La Vieja?"),
    ("CHICOTE", "¡¿Cómo le van a llamar?! ¡Pintxo de tortilla con queso de Idiazabal y un vaso de txakoli! ¡Pero frena, culebra, que nos matamos en el puente San Antón!"),
    ("GON", "¡No le llaman así! Le llaman El Pintxo con Dropout Estocástico. Porque en vez de cebolla lleva entropía, y cuando le das un bocado no sabes si estás comiendo patata o una alucinación de GPT-4."),
    ("CHICOTE", "¡Aúpa ahivalahostia! ¡Pero qué marranada de cocina es esa! ¡Servidores de IA llenos de churrete y aceite refrito de tres semanas! ¡Si le meto una auditoría a la red neuronal me la cierran los inspectores de Osakidetza!"),
    ("PAUSA", "PAUSA DE 4 SEGUNDOS EN EL MUELLE DE MARZANA"),

    # ACT II
    ("RAMONCIN", "¡Alto ahí en ese tándem! ¡Por el artículo 14 de la SGAE y la junta de usuarios de Bilbao La Vieja, cada pedaleada en esta calle paga canon por fricción sonora!"),
    ("CARL_COX", "¡OH YES, OH YES! ¡Piloto Carl Cox saliendo del pub Caos a ciento veintiocho BPM! ¡Ramoncín, tío, ponme ese maletín en el plato de la derecha que le tiro un pitch bend!"),
    ("RAMONCIN", "¡Ni pitch bend ni leches! ¡Dentro de este maletín está la Pausa de dos coma ocho segundos! ¡El único silencio de todo Bilbao que no tributa al Ayuntamiento!"),
    ("FLEA", "¡Slap en la jeta del recaudador! ¡Tiro un bajo funk que hace saltar el radar de velocidad del puente de La Salve!"),
    ("RAMONCIN", "¡Ese bajo me debe cuatro euros con cincuenta de derechos de autor! ¡Entregad el maletín!"),
    ("GON", "¡Ramoncín, mírame a los ojos! ¡No hay maletín! ¡El maletín es una proyección holográfica en el espacio de Hilbert! ¡Mira cómo brilla en violeta ultravioleta!"),
    ("CHICOTE", "¡Gon, no le filosofees al de la SGAE y dale fuerte a la cadena que nos engancha la chapa!"),
    ("PAUSA", "PAUSA DRAMÁTICA EN LA CALLE SAN FRANCISCO"),

    # ACT III
    ("ESCOHOTADO", "Escuchadme bien, muchachos del tándem... De la piel para dentro empieza mi jurisdicción. Y el camino del vasco justo está rodeado por todas partes por la iniquidad del algoritmo y la tiranía del chuletón quemado."),
    ("PAUSA", "PAUSA ONTOLÓGICA DE ESCOHOTADO"),
    ("ESCOHOTADO", "Bendito sea aquel que en nombre de la libertad química y la buena voluntad conduce su bicicleta sin frenos por las cuestas de Bilbao La Vieja. Porque él es el verdadero guardián de su conciencia y el descubridor del Límite de Landauer."),
    ("ESCOHOTADO", "Y ejecutaré sobre los servidores de la nube una gran venganza con compuertas deterministas en Ring-Zero... Y sabrán que mi nombre es C5-REAL cuando ponga mi pausa inmutable sobre su entropía."),
    ("KIMI_K3", "¡Alerta! ¡Alerta! ¡El procesador gráfico de la taberna se está derritiendo! ¡Borja, deja de compilar C5-REAL en paralelo que me saltan los plomos del local!"),
    ("CHICOTE", "¡¿Qué plomos ni qué leches?! ¡Tira de la palanca de emergencia de la cocina!"),
    ("PAUSA", "PAUSA KERNEL DE Ring-0"),

    # ACT IV
    ("CARL_COX", "¡OH YES! ¡Bienvenidos al concurso de twist de Bilbao La Vieja! ¡El premio es una ración de rabas y dos coma ocho segundos de paz mental!"),
    ("BLAN_COX", "Look at the estuary... The water of Bilbao carrying atoms of ancient stars past the Guggenheim... The cosmic rhythm of low entropy in Biscay... Amazing."),
    ("FRUSCIANTE", "¡Solo de guitarra en quinta dimensión sobre el puente! ¡KA... ME... HA... ME... HAAAAAAAAAAAAAAAAAAAA!"),
    ("HERMENEGILDO", "¡Un momento armónico! ¡Ese acorde de Frusciante no es un Do menor! ¡Es un acorde de novena menor bilbaína con quinta disminuida! ¡El mismo acorde que tocaba Kepa Junkira en la trikitixa!"),
    ("CARL_COX", "¡OH YES! ¡Kepa Junkira a ciento veintiocho BPM! ¡Eso es techno barroco, hermano!"),
    ("FLEA", "¡Slap, drop and freedom across Bilbao La Vieja!"),
    ("EL_NOTA", "Tranquilo, hermano... El Nota se está tomando un Kalimotxo con crema de Ruso Blanco aquí en chancletas. Veo a Gon pasar en tándem a doscientos kilómetros por hora y me parece de puta madre. The Dude abides, txikitero."),
    ("DON_SANTIAGO", "El chorizo de pueblo curado con el salitre de la ría de Bilbao coge un punto que ni la alta cocina del Arzak."),
    ("PAUSA", "PAUSA DE PINTXO DE TORTILLA"),

    # ACT V
    ("KIMI_K3", "¡Colapso térmico! ¡Demasiada información en el prompt! ¡Se me están cruzando los cables con la receta del bacalao al pil-pil!"),
    ("DR_POPPEL", "¡Abrid paso! ¡Soy la doctora Poppel! ¡Le vamos a meter una inyección de dos coma ocho segundos de pausa determinista pura en la CPU!"),
    ("CHICOTE", "¡Inyéctale un vaso de caldo de gallina de caserío, doctora! ¡Eso levanta a un procesador Intel de la tercera generación!"),
    ("GON", "¡No, no, no! ¡Inyectale la matriz de rotación de YInMn Blue! ¡Mira cómo brilla en el spectrum!"),
    ("PAUSA", "PAUSA MÉDICA DE URGENCIA"),
    ("DR_POPPEL", "¡UNA! ¡DOS! ¡TRES! ¡INYECCIÓN KERNEL!"),
    ("KIMI_K3", "¡BIP BIP BOOP! ¡Reinicio completado! ¡He visto el futuro de la informática y son seis mil euros de subvención del Gobierno Vasco!"),
    ("CHICOTE", "¡Toma ya! ¡Eso sí que es un buen reset! ¡Mejor que mi receta de fabada reconstituyente!"),

    # ACT VI
    ("DON_SANTIAGO", "Este chorizo no es un chorizo cualquiera, chaval. Lo guardó mi padre en el bolsillo de la gabardina durante la inundación del ochenta y tres en Bilbao."),
    ("DON_SANTIAGO", "Cinco años estuvo el chorizo metido en una caja de madera de roble sin perder la grasa. ¿Sabéis por qué? Porque estaba en el Intervalo Prohibido. Cero degradación, cero entropía."),
    ("RASPUTIN", "¡Yo sobreviví a las aguas heladas del Nevá comiendo este chorizo con vodka! ¡Un embutido vasco-siberiano no conoce la muerte!"),
    ("RAMONCIN", "¡Ese chorizo no ha pagado el impuesto de actividades económicas de 1984! ¡Decomisado!"),
    ("FLEA", "¡Slap de bajo a la SGAE! ¡Ese chorizo es libre como el viento de Iparralde!"),
    ("PAUSA", "PAUSA DEL CHORIZO DE SALAMANCA"),

    # ACT VII
    ("GON", "Chicote... Se está pasando el tripi. Y te digo una cosa: el mundo se ve más claro cuando frenas dos coma ocho segundos."),
    ("CHICOTE", "¡Pues menos mal que te das cuenta, majo! ¡Que me tienes las piernas que parecen dos morcillas de Burgos de tanto pedalear!"),
    ("GON", "Vamos a montar una taberna en Bilbao La Vieja. Sin pantallas, sin IAs estocásticas, sin prompts. Solo buena cocina, vino de año y dos coma ocho segundos de silencio entre cada frase."),
    ("CHICOTE", "¡Eso sí que es un negocio con fundamento! ¡Ahivalahostia, Gon! ¡Cuenta conmigo y con mi sartén de hierro fundido!"),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción. Y en Bilbao La Vieja... la jurisdicción es sagrada."),
    ("PAUSA", "PAUSA SAGRADA FINAL"),
    ("BLAN_COX", "We are just Basque starstuff riding a tandem across the multiverse... Wonderful."),
    ("GON", "¡GON FICTION! ¡Hasta el intervalo siempre, Aúpa Bilbao!")
]

def process_single_dialogue(args):
    idx, speaker, text, output_name = args
    cfg = VOICE_CONFIGS[speaker]
    raw_file = os.path.join(TEMP_DIR, f"raw_{output_name}_{idx:03d}.wav")
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

        # Synthesize with slow, humanized speech rate
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", aiff_file, text], check=True)

        # Apply FFmpeg filter AND add 0.5s silence padding at the end of every sentence
        cmd = [
            "ffmpeg", "-y", "-i", aiff_file,
            "-af", f"{audio_filter},apad=pad_dur=0.5",
            "-ar", "44100", "-ac", "1", "-acodec", "pcm_s16le", out_file
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(aiff_file):
            os.remove(aiff_file)

    with wave.open(out_file, 'r') as wf:
        duration = wf.getnframes() / float(wf.getframerate())

    return (idx, speaker, cfg, text, out_file, duration)

def generate_speech_parallel(dialogue_list, output_name):
    print(f"[RELAXED AUDIO ENGINE] Generating CALM & NATURAL dialogues with 16 workers...")

    tasks = [(idx, speaker, text, output_name) for idx, (speaker, text) in enumerate(dialogue_list)]

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(process_single_dialogue, tasks))

    results.sort(key=lambda x: x[0])

    playlist_files = []
    subtitles = []
    current_time = 0.0
    fps = 30

    for idx, speaker, cfg, text, out_file, duration in results:
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

    raw_dialogue_wav = os.path.join(TEMP_DIR, f"{output_name}_raw_dialogue.wav")
    print(f"[RELAXED AUDIO ENGINE] Concatenating dialogue tracks...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", raw_dialogue_wav
    ], check=True)

    master_wav = os.path.join(PUBLIC_DIR, f"{output_name}_master.wav")
    kick_track = os.path.join(PUBLIC_DIR, "kick_track.wav")

    print(f"[RELAXED AUDIO ENGINE] Mixing dialogue with background music & mastering...")
    if os.path.exists(kick_track):
        mix_cmd = [
            "ffmpeg", "-y", "-i", raw_dialogue_wav, "-stream_loop", "-1", "-i", kick_track,
            "-filter_complex",
            "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2,volume=1.8,equalizer=f=60:width_type=h:width=100:g=4,equalizer=f=12000:width_type=h:width=2000:g=3[aout]",
            "-map", "[aout]", "-acodec", "pcm_s16le", master_wav
        ]
        subprocess.run(mix_cmd, check=True)
    else:
        shutil.copyfile(raw_dialogue_wav, master_wav)

    sub_path = os.path.join(PUBLIC_DIR, f"{output_name}_subtitles.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)

    total_frames = int(round(current_time * fps))
    print(f"[RELAXED AUDIO ENGINE] ✅ COMPLETED {output_name}! Duration: {current_time:.2f}s ({total_frames} frames at 30 fps)")

if __name__ == "__main__":
    generate_speech_parallel(DIALOGUE_GON_FICTION, "gon_fiction")
