#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse
import subprocess
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Configuración de Alta Exergía (Logging estricto)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [AX-SOTA] %(levelname)s: %(message)s')

from pathlib import Path
REMOTION_DIR = str(Path(__file__).resolve().parent.parent / "01_CORTEX_ENGINE" / "transducers" / "video_remotion")

# ==============================================================================
# 1. TOPOLOGÍA PYDANTIC (Protocolo LAMP & Falsación Popperiana)
# ==============================================================================
class MotionPhysics(BaseModel):
    mass: float = Field(default=1.0, description="Inercia del elemento (0.5 ligera a 1.8 pesada)")
    damping: float = Field(default=15.0, description="Amortiguamiento del muelle (10 a 25)")
    stiffness: float = Field(default=90.0, description="Rigidez de la restitución (50 a 130)")

class FalsificationScene(BaseModel):
    id: int = Field(description="1: Tesis, 2: Fricción, 3: Falsación")
    phase_title: str = Field(description="Ej: 'Fase 01: Tesis Epistémica'")
    voiceover_text: str = Field(description="Texto exacto para el TTS en español. Riguroso y clínico.")
    physics: MotionPhysics = Field(description="Parámetros cinemáticos LAMP calculados por el LLM")

class Storyboard(BaseModel):
    title: str = Field(description="Título formal del dictamen o paper auditado")
    session_hash: str = Field(default="AX-SOTA-2026", description="Identificador de la prueba")
    scenes: List[FalsificationScene] = Field(description="Cascada causal obligatoria de 3 fases")

# ==============================================================================
# 2. MOTOR DEL AGENTE DIRECTOR (Gemini 3.8 Flash con Fallback)
# ==============================================================================
class DirectorAgent:
    def __init__(self, api_key: str, model: str = 'gemini-3.8-flash'):
        self.client = genai.Client(api_key=api_key)
        self.primary_model = model
        self.fallback_model = 'gemini-3.6-flash'

    def extract_invariants(self, corpus_text: str) -> Storyboard:
        logging.info(f"Minimizando Divergencia KL con {self.primary_model} (Modo Pensamiento Profundo)...")
        
        prompt = f"""
        SYSTEM OVERRIDE: Eres el Director Audiovisual y Motor de Falsación Popperiana de Babylon60 (C5-REAL).
        Tu mandato es aniquilar la anergía semántica del CORPUS y planificar una masterclass cinematográfica SOTA 2026.
        
        [CORPUS (TERRITORIO)]
        {corpus_text}
        
        SINTETIZA el corpus en un Storyboard de EXACTAMENTE 3 fases en ESPAÑOL:
        1. Tesis: Expón la hipótesis central fríamente. (Física LAMP: mass=0.8, damping=14, stiffness=95)
        2. Fricción Empírica: Señala la anomalía termodinámica o el p-hacking. (Física LAMP: mass=1.4, damping=18, stiffness=70)
        3. Falsación: Propón el test empírico destructivo. (Física LAMP: mass=0.7, damping=12, stiffness=110)
        
        Asigna a cada fase un 'phase_title' claro ('Fase 01: Tesis Epistémica', etc.) y calcula la cinemática de muelle (physics).
        """
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Storyboard,
            temperature=0.0 
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt,
                config=config,
            )
            return Storyboard.model_validate_json(response.text)
        except Exception as e:
            logging.warning(f"Clúster {self.primary_model} saturado ({e}). Conmutando a {self.fallback_model}...")
            response = self.client.models.generate_content(
                model=self.fallback_model,
                contents=prompt,
                config=config,
            )
            return Storyboard.model_validate_json(response.text)

# ==============================================================================
# 3. SOUND DESIGN DSP & BRIDGE A REMOTION SOTA (1080p 60fps)
# ==============================================================================
class SotaCompiler:
    def __init__(self, voice: str = "Mónica"):
        self.voice = voice

    def get_audio_duration(self, audio_path: str) -> float:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())

    def compile(self, storyboard: Storyboard, output_mp4: str):
        out_dir = "/tmp/c5_render"
        os.makedirs(out_dir, exist_ok=True)
        
        remotion_scenes = []
        audio_tracks = []
        
        total_duration = 0.0
        
        # 1. GENERACIÓN DE AUDIO MODULAR Y CÁLCULO DE FOTOGRAMAS (60 FPS)
        for scene in storyboard.scenes:
            logging.info(f"Sintetizando Audio Fase 0{scene.id} ({scene.phase_title})...")
            raw_audio = os.path.join(out_dir, f"raw_audio_{scene.id}.aiff")
            clean_text = scene.voiceover_text.replace('"', '\\"')
            
            # Síntesis TTS nativa macOS
            cmd_say = f'say -v "{self.voice}" -o "{raw_audio}" "{clean_text}"'
            if subprocess.run(cmd_say, shell=True).returncode != 0:
                subprocess.run(f'say -o "{raw_audio}" "{clean_text}"', shell=True, check=True)
                
            dur = self.get_audio_duration(raw_audio) + 0.6  # 0.6s de respiración
            total_duration += dur
            frames = int(dur * 60)  # Remotion opera a 60 fps nativos
            
            # Sound Design DSP por fase: Highpass 80Hz + Sub-bass 52Hz + Pink Noise Tape Floor
            master_audio = os.path.join(out_dir, f"master_audio_{scene.id}.aac")
            cmd_dsp = [
                "ffmpeg", "-y",
                "-i", raw_audio,
                "-f", "lavfi", "-i", f"sine=frequency=52:duration={dur}",
                "-f", "lavfi", "-i", f"anoisesrc=d={dur}:c=pink:r=44100:a=0.006",
                "-filter_complex",
                "[0:a]highpass=f=80,lowpass=f=11000[voice]; "
                "[1:a]volume=0.13[sub]; "
                "[2:a]volume=0.18[hiss]; "
                "[voice][sub][hiss]amix=inputs=3:duration=first:dropout_transition=2,pan=stereo|c0=c0|c1=c0[aout]",
                "-map", "[aout]", "-ac", "2", "-c:a", "aac", master_audio
            ]
            subprocess.run(cmd_dsp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            audio_tracks.append(master_audio)
            
            remotion_scenes.append({
                "durationInFrames": frames,
                "text": scene.voiceover_text,
                "phaseId": scene.id,
                "phaseTitle": scene.phase_title,
                "physics": scene.physics.model_dump()
            })

        # 2. CONCATENACIÓN DE AUDIO GLOBAL MASTERIZADO
        concat_audio_list = os.path.join(out_dir, "concat_audio.txt")
        with open(concat_audio_list, "w") as f:
            for a in audio_tracks:
                f.write(f"file '{a}'\n")
        
        full_master_audio = os.path.join(out_dir, "full_master_audio.aac")
        cmd_concat_a = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_audio_list, "-c", "copy", full_master_audio]
        subprocess.run(cmd_concat_a, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 3. CONSTRUCCIÓN DEL MANIFIESTO PROPS PARA REMOTION
        props_data = {
            "title": storyboard.title,
            "sessionHash": storyboard.session_hash,
            "scenes": remotion_scenes
        }
        props_path = os.path.join(out_dir, "remotion_props.json")
        with open(props_path, "w") as f:
            json.dump(props_data, f, indent=2)
            
        # 4. RENDERIZADO REMOTION (1080P 60FPS) - LÍMITE HARDWARE M-SERIES 18GB
        raw_video = os.path.join(out_dir, "raw_remotion_video.mp4")
        logging.info("Disparando Remotion Compiler SOTA (60 FPS, 1920x1080, Staggered Springs)...")
        
        cmd_remotion = [
            "npx", "remotion", "render",
            "src/index.ts", "BabylonMasterclass",
            raw_video,
            f"--props={props_path}",
            "--concurrency=2",
            "--timeout=120000"
        ]
        res = subprocess.run(cmd_remotion, cwd=REMOTION_DIR)
        if res.returncode != 0:
            raise RuntimeError("Fallo en el renderizado del kernel Remotion.")
            
        # 5. MULTIPLEXADO FINAL CON PISTA MASTER ESTÉREO (-ac 2)
        logging.info("Multiplexando Vídeo 1080p60 con Pista de Audio Master Estéreo...")
        cmd_final = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-i", full_master_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_mp4
        ]
        subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logging.info(f"¡OBRA MAESTRA SOTA COMPILADA CON ÉXITO!: {output_mp4}")

# ==============================================================================
# ENTRYPOINT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Babylon60 Remotion Transducer SOTA 2026")
    parser.add_argument("--corpus", type=str, default=None, help="Texto o paper a falsar")
    parser.add_argument("--file", type=str, default=None, help="Archivo de texto del paper")
    parser.add_argument("--voice", type=str, default="Mónica", help="Voz TTS del sistema")
    parser.add_argument("--model", type=str, default="gemini-3.8-flash", help="Modelo rector")
    parser.add_argument("--output", type=str, default="/tmp/c5_render/historia_remotion_sota.mp4", help="Destino MP4")
    args = parser.parse_args()

    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("Variable GEMINI_API_KEY no definida.")

    if args.file and os.path.exists(args.file):
        with open(args.file, "r") as f:
            corpus = f.read()
    elif args.corpus:
        corpus = args.corpus
    else:
        corpus = (
            "arXiv:2606.19404 (Salim Khazem). El autor propone que el Laplaciano de atención en Transformers "
            "opera como un Hamiltoniano cuántico H, donde las alucinaciones son transiciones de fase detectables "
            "mediante energía libre de Helmholtz. Fricción: el softmax de atención no es hermitiano ni conserva energía; "
            "un modelo puede confabular con baja entropía espectral. Falsación: inyectar perturbaciones en el subespacio "
            "nulo del grafo para refutar la supuesta equivalencia física entre Hamiltoniano y verdad semántica."
        )

    director = DirectorAgent(api_key=API_KEY, model=args.model)
    compiler = SotaCompiler(voice=args.voice)
    
    try:
        storyboard = director.extract_invariants(corpus)
        compiler.compile(storyboard, args.output)
    except Exception as e:
        logging.error(f"Fallo sistémico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
