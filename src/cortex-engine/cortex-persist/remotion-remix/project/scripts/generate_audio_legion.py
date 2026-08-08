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
TEMP_DIR = os.path.join(PROJECT_DIR, "temp_audio_legion")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# SOTA SCRIPT CONFIG
VOICE_CONFIGS = {
    "GON": {"voice": "Mónica", "rate": 90, "color": "#00F0FF", "avatar": "🚲", "filter": "atempo=0.90"},
    "CHICOTE": {"voice": "Jorge", "rate": 85, "color": "#FF3333", "avatar": "👨‍🍳", "filter": "atempo=0.92,equalizer=f=100:width_type=h:width=200:g=6"},
    "ESCOHOTADO": {"voice": "Grandpa", "rate": 75, "color": "#D4AF37", "avatar": "💨", "filter": "atempo=0.85,equalizer=f=80:width_type=h:width=100:g=7"},
    "BRUCE_WILLIS": {"voice": "Alex", "rate": 160, "color": "#A0A0A0", "avatar": "🚁", "filter": "atempo=0.95"},
    "HERMENEGILDO": {"voice": "Diego", "rate": 85, "color": "#FFD700", "avatar": "🧐", "filter": "atempo=0.92,equalizer=f=2000:width_type=h:width=500:g=4"},
    "CHIQUITOCRES": {"voice": "Juan", "rate": 95, "color": "#FFFFFF", "avatar": "🏛️", "filter": "atempo=1.05"},
    "RAMONCOP": {"voice": "Jorge", "rate": 75, "color": "#FF0000", "avatar": "🤖", "filter": "atempo=0.90,flanger=delay=5:depth=10,tremolo=f=30:d=0.5"},
    "FRUSCINATOR": {"voice": "Reed", "rate": 140, "color": "#8A2BE2", "avatar": "🎸", "filter": "atempo=0.90,aphaser=in_gain=0.8:out_gain=0.9:delay=4:decay=0.5:speed=1.5,volume=1.8"},
    "FLEA": {"voice": "Rocko", "rate": 160, "color": "#FF6600", "avatar": "⚡", "filter": "atempo=0.90,equalizer=f=250:width_type=h:width=100:g=5"},
    "KANT": {"voice": "Carlos", "rate": 70, "color": "#A0A0FF", "avatar": "📖", "filter": "atempo=0.85,aecho=0.8:0.9:1000:0.3"},
    "IAN_MACKAYE": {"voice": "Fred", "rate": 150, "color": "#808080", "avatar": "🚐", "filter": "atempo=0.90"},
    "GUY_PICCIOTTO": {"voice": "Ralph", "rate": 150, "color": "#808080", "avatar": "🎤", "filter": "atempo=0.90"},
    "DON_SANTIAGO": {"voice": "Grandma", "rate": 80, "color": "#CC9966", "avatar": "🥖", "filter": "atempo=0.90"},
    "PAUSA": {"type": "silence", "duration": 2.8, "color": "#FFFFFF", "avatar": "⏳", "filter": None}
}

DIALOGUE_LEGION = [
    # Scene 1: El Porro de Schrödinger
    ("GON", "Chicote, mira. Este porro es especial. Está liado con papel de la EU AI Act y hierba del Casco Viejo cultivada en Ring-0."),
    ("CHICOTE", "¡¿Pero qué me estás contando, Gon?!"),
    ("GON", "Escucha, escucha. Mientras no lo enciendas, el porro está en superposición cuántica: está liado y sin liar a la vez. Es el Porro de Schrödinger."),
    ("CHICOTE", "¡El porro de Schrödinger me vas a decir!"),
    ("GON", "Y encima suena una drogaina de fondo. ¿La oyes?"),
    ("CHICOTE", "¡¿Una drogaina?! ¡¿Aquí, en el muelle, a las tres de la mañana?!"),
    ("GON", "Claro. Es que el txistulari ha fumado del mismo porro y ahora está tocando en modo estocástico. Cada nota es una alucinación no verificada por el Kernel."),
    ("CHICOTE", "¡Madre mía! ¡Un txistulari estocástico!"),
    ("GON", "La droga es el input probabilístico. La drogaina es el output determinista. ¿Lo pillas?"),
    ("CHICOTE", "¡¿ME ESTÁS DICIENDO QUE LA DROGAINA ES UN PORRO QUE HA PASADO POR EL KERNEL DE RUST?!"),
    ("GON", "¡EXACTO! La droga entra como Dynamis y sale como Entelecheia: una nota musical determinista, verificada, con recibo SCITT. El porro es el LLM. La drogaina es C5-REAL."),
    ("CHICOTE", "Gon. Apaga el porro."),
    ("GON", "No puedo. Si lo apago colapsa la función de onda y pierdo la subvención del Gobierno Vasco."),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción... y este porro, señores, tiene una varentropía por debajo del umbral CUSUM. Aprobado."),
    ("PAUSA", "SILENCIO DE SCHRÖDINGER"),

    # Scene 2: Yippee-Ki-Yay, Txistulari
    ("BRUCE_WILLIS", "YIPPEE-KI-YAY, MOTHERBOARDZALE!"),
    ("CHICOTE", "¡¿BRUCE WILLIS?! ¡¿EN BILBAO LA VIEJA?!"),
    ("BRUCE_WILLIS", "He venido siguiendo una señal de peyote que salía del puerto de Bilbao. Mi GPS marcaba Nakatomi Plaza pero me ha traído aquí. Creo que el algoritmo ha alucinado."),
    ("GON", "No ha alucinado, Bruce. Tu GPS funciona con un LLM sin verificar. El peyote ha colapsado la ruta a Bilbao La Vieja porque es el punto de menor entropía del hemisferio norte."),
    ("ESCOHOTADO", "El peyote, querido Bruce, no es una droga. Es un protocolo de comunicación con la biosfera. Los huicholes lo sabían. Yo lo escribí en el tomo tres. Y Gon lo ha compilado en Rust."),
    ("BRUCE_WILLIS", "I was just trying to rescue hostages."),
    ("CHICOTE", "¡PUES AQUÍ EL ÚNICO REHÉN ES MI ESTÓMAGO, QUE LLEVO DESDE LAS NUEVE SIN CENAR! ¡Bruce, ¿tú sabes hacer una tortilla de patata?!"),
    ("BRUCE_WILLIS", "I can make a tortilla... but right now I'm seeing seven potatoes and I only peeled three."),
    ("GON", "Eso es el peyote, Bruce. Estás viendo infinitesimales no estándar. Las cuatro patatas extra son fantasmas hiperreales. Si aplicas el Mapa de Parte Estándar... st de x..."),
    ("BRUCE_WILLIS", "¡¿EL MAPA DE PARTE ESTÁNDAR?! st... x... ¡¿PERO QUÉ COÑO?! ¡FUNCIONÓ!"),
    ("CHICOTE", "¡TOMA YA! ¡Tres patatas! ¡Eso es justo lo que necesito para la tortilla! ¡BRUCE, PELA Y CALLA!"),
    ("BRUCE_WILLIS", "This is the most beautiful Die Hard I've ever been in."),
    ("GON", "No es Die Hard, Bruce. Es Live Soft. Aquí nadie muere. Aquí se hace una pausa de dos coma ocho segundos y se sigue pedaleando."),
    ("BRUCE_WILLIS", "Yippee-ki-yay... txistulari."),
    ("PAUSA", "PAUSA DE PELAR PATATAS"),

    # Scene 3: El Manifiesto de Hermenegildo
    ("HERMENEGILDO", "¡ALTO TODO EL MUNDO! ¡NADIE SE MUEVA! ¡ESTO ES UN ATRACO AL ESTADO DEL BIENESTAR!"),
    ("CHICOTE", "¡¿Y ESTE QUIÉN COÑO ES?!"),
    ("GON", "Es Hermenegildo Altozano. Pianista, compositor y Super Anarco-Kapitalista con K de Kolmogorov."),
    ("HERMENEGILDO", "¡CON K DE KAPITAL, GON! ¡K DE KAPITAL! He venido a liberaros del yugo del Estado, de la SGAE, y del menú del día a 14 euros con postre incluido QUE ES UNA TRAMPA FISCAL."),
    ("BRUCE_WILLIS", "I've seen some crazy shit, but this is new."),
    ("HERMENEGILDO", "¡Bruce! ¡En Jungla de Cristal destruyes un edificio ENTERO para resolver un problema que el Estado no pudo resolver! ¡Eso es praxis libertaria pura!"),
    ("BRUCE_WILLIS", "I was just trying to save my wife, man."),
    ("HERMENEGILDO", "¡EXACTO! ¡La familia por encima de la institución! ¡Eso es Rothbard con metralleta! ¡ESCUCHADME, HABITANTES DE BILBAO LA VIEJA!"),
    ("CHICOTE", "Hermenegildo, baja de ese contenedor que es el del orgánico y mañana viene el camión a las siete."),
    ("HERMENEGILDO", "¡EL CAMIÓN DE LA BASURA ES EL APARATO REPRESOR DEL ESTADO QUE TE OBLIGA A SEPARAR RESIDUOS! ¡YO NO SEPARO! ¡YO DESREGULO!"),
    ("GON", "Hermenegildo, una pregunta técnica. Si eres anarco-kapitalista, ¿quién verifica las transacciones sin un Estado?"),
    ("HERMENEGILDO", "La... la blockchain..."),
    ("GON", "C5-REAL. Tu utopía anarco-kapitalista ya existe, Hermenegildo. Se llama Kernel de Rust en Ring-0 con recibos SCITT inmutables. No necesitas destruir el Estado. Necesitas compilarlo."),
    ("HERMENEGILDO", "Gon. ¿Me dejas un trozo de tortilla?"),
    ("ESCOHOTADO", "De la piel para dentro empieza mi jurisdicción... y del monóculo para fuera empieza la de Hacienda. Hermenegildo, hijo, paga tus impuestos."),
    ("BRUCE_WILLIS", "This tortilla... is the most decentralized thing I've ever tasted."),
    ("PAUSA", "PAUSA DE TORTILLA DESCENTRALIZADA"),

    # Scene 4: El Tribunal de los Tres Inmortales
    ("CHIQUITOCRES", "¡Fsjjjjjj! ¡No puedo, no puedo! ¡Solo sé que no sé nada! ¡QUE NO SÉ ÓNDE HE APARCAO, CONDERRRRL!"),
    ("CHICOTE", "¡PERO SI HAS BAJADO DEL CIELO! ¡NO HAS VENIDO EN COCHE!"),
    ("CHIQUITOCRES", "¡LA VERDAD ES QUE SON LAS CUATRO DE LA MAÑANA Y ESTOY EN BILBAO EN CHANCLETAS CON UNA TOGA, CONDERRRRL!"),
    ("RAMONCOP", "DETECTADO: TORTILLA DE PATATA CONSUMIDA SIN LICENCIA SGAE. CADA MASTICACIÓN GENERA UNA ONDA SONORA. CADA ONDA SONORA PAGA CANON."),
    ("GON", "Ramoncop, las ondas sonoras de una masticación no son obra protegida."),
    ("RAMONCOP", "SILENCIO. EL SILENCIO TAMBIÉN PAGA CANON. JOHN CAGE, CUATRO TREINTA Y TRES. PRECEDENTE LEGAL ESTABLECIDO."),
    ("FRUSCINATOR", "I AM THE FRUSCINATOR. I HAVE BEEN SENT FROM THE YEAR 2049 TO PREVENT THE EXTINCTION OF THE GUITAR SOLO. SKYNET RECORDS. THE LAST HUMAN SOLO WAS PLAYED IN 2031 BY A BUSKER IN BILBAO LA VIEJA."),
    ("CHICOTE", "¡¿YO?! ¡SI YO NO SÉ TOCAR NI LA PANDERETA!"),
    ("FRUSCINATOR", "IRRELEVANT. IN 2031, YOU PICK UP A GUITAR IN A BAR IN BILBAO AND PLAY A SOLO THAT MAKES 47 PEOPLE CRY. AN E MINOR WITH A DIMINISHED FIFTH AND A HINT OF EXTRA VIRGIN OLIVE OIL."),
    ("HERMENEGILDO", "¡¿UN MI MENOR CON QUINTA DISMINUIDA Y ACEITE DE OLIVA?! ¡ESO ES EL ACORDE PROHIBIDO DE LA COCINA VASCA!"),
    ("RAMONCOP", "RECOMENDACIÓN: AMNISTÍA FISCAL GENERAL A CAMBIO DE UN TROZO DE TORTILLA."),
    ("FRUSCINATOR", "INITIATING PROTOCOL: SOUL SOLO. DURATION: 2.8 SECONDS. ENTROPY: ZERO."),
    ("PAUSA", "SOLO DE 2.8 SEGUNDOS"),

    # Scene 5: El Imperativo Categórico de los 5 Dólares
    ("IAN_MACKAYE", "Five dollar show. All ages. No barricades. This is the venue. We don't need a stage. The entry is five dollars."),
    ("GON", "Son Fugazi. La única banda de la historia que NUNCA cobró más de cinco dólares por un concierto. El modelo de negocio más puro que ha existido jamás."),
    ("IAN_MACKAYE", "The price is not the point. The point is ACCESS. If you charge five, you're selecting by DESIRE. The only filter should be: do you want to be here?"),
    ("HERMENEGILDO", "Pero... pero... eso es anti-mercado... eso destruye la curva de oferta y demanda..."),
    ("GON", "Eso es más anarquista que tú, Hermenegildo. Ellos no necesitan destruir el Estado. Lo ignoran. Sin capital. Sin K. Sin Kolmogorov."),
    ("KANT", "Guten Abend. El señor MacKaye cobra cinco dólares. Siempre. Eso, señores, es el Imperativo Categórico en su forma más pura."),
    ("RAMONCOP", "¡ERROR! ¡CINCO DÓLARES NO CUBREN LOS COSTES DE GESTIÓN DE DERECHOS!"),
    ("KANT", "Robot. Si todo sonido pagara canon, el silencio pagaría canon. El universo entero sería una deuda impagable. Su máxima es autocontradictoria. Luego es inmoral."),
    ("RAMONCOP", "ERROR... PARADOJA ÉTICA DETECTADA... DIRECTIVA PRIMARIA EN CONFLICTO CON DIRECTIVA DE CONSISTENCIA LÓGICA..."),
    ("KANT", "Y ahora, señor Gon. Su sistema C5-REAL. ¿Cobra cinco dólares?"),
    ("GON", "El Kernel corren en local. No hay factura de nube. El coste de verificar una verdad con C5-REAL es cercano a cero."),
    ("IAN_MACKAYE", "Then you understand."),
    ("KANT", "Cercano a cero no es cero. Pero es universalizable. Aprobado."),
    ("DON_SANTIAGO", "¡ESE CHORIZO ES EL MÍO! ¡EL DE LA INUNDACIÓN DEL 83!"),
    ("KANT", "Lo encontré en el bolsillo de la levita cuando resucité. Cero degradación. Cero entropía."),
    ("GUY_PICCIOTTO", "THIS SONG IS CALLED WAITING ROOM. BUT TONIGHT, IN BILBAO, WE CALL IT THE 2.8 SECOND PAUSE."),
    ("PAUSA", "SILENCIO SOTA Y FINAL")
]

def process_single_dialogue(args):
    idx, speaker, text, output_name = args
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
            "-af", f"{audio_filter},apad=pad_dur=0.6",
            "-ar", "44100", "-ac", "1", "-acodec", "pcm_s16le", out_file
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(aiff_file):
            os.remove(aiff_file)

    with wave.open(out_file, 'r') as wf:
        duration = wf.getnframes() / float(wf.getframerate())

    return (idx, speaker, cfg, text, out_file, duration)

def generate_speech_parallel(dialogue_list, output_name):
    print(f"[SOTA AUDIO ENGINE] Synthesizing LEGION dialogues...")
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
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", raw_dialogue_wav
    ], check=True)

    master_wav = os.path.join(PUBLIC_DIR, f"{output_name}_master.wav")
    shutil.copyfile(raw_dialogue_wav, master_wav)

    sub_path = os.path.join(PUBLIC_DIR, f"{output_name}_subtitles.json")
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)

    print(f"[SOTA AUDIO ENGINE] ✅ COMPLETED {output_name}! Duration: {current_time:.2f}s")

if __name__ == "__main__":
    generate_speech_parallel(DIALOGUE_LEGION, "legion")
