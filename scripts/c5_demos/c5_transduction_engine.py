#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse
import textwrap
import subprocess
from typing import List
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Configuración de Alta Exergía (Logging estricto)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [AX-S2] %(levelname)s: %(message)s')

# ==============================================================================
# 1. DEFINICIÓN TOPOLÓGICA (PYDANTIC) - El Tensor de Transducción Popperiana
# ==============================================================================
class FalsificationScene(BaseModel):
    id: int = Field(description="Fase causal. 1: Tesis, 2: Fricción, 3: Falsación")
    duration_sec: int = Field(description="Duración rígida en segundos. Mínimo 4, máximo 9.")
    voiceover_text: str = Field(description="Texto exacto para el motor TTS en español. Cero retórica.")
    visual_prompt: str = Field(description="Directiva visual paramétrica para microscopio/cine.")

class Storyboard(BaseModel):
    global_style_vector: str = Field(description="El vector estético inmutable que gobernará todos los píxeles.")
    scenes: List[FalsificationScene] = Field(description="Cascada causal obligatoria de 3 escenas: Tesis, Fricción y Prueba de Falsación.")

# ==============================================================================
# 2. MOTOR DEL AGENTE DIRECTOR (Gemini 3.8 Flash con Fallback)
# ==============================================================================
class DirectorAgent:
    def __init__(self, api_key: str, model: str = 'gemini-3.8-flash'):
        self.client = genai.Client(api_key=api_key)
        self.primary_model = model
        self.fallback_model = 'gemini-3.6-flash'

    def extract_invariants(self, corpus_text: str, override_metadata: str) -> Storyboard:
        logging.info(f"Minimizando Divergencia KL con {self.primary_model} (Modo Pensamiento Profundo)...")
        
        prompt = f"""
        SYSTEM OVERRIDE: Eres un Motor de Falsación Popperiana (C5-REAL).
        Tu mandato es aniquilar la anergía semántica del CORPUS y someterlo a estrés epistémico.
        
        [SYSTEM_OVERRIDE_METADATA]
        {override_metadata}
        
        [CORPUS (TERRITORIO)]
        {corpus_text}
        
        SINTETIZA el corpus en un Storyboard de EXACTAMENTE 3 escenas en ESPAÑOL:
        1. Tesis: Expón la hipótesis o afirmación central del texto de forma clínica y directa.
        2. Fricción Empírica: Señala la anomalía termodinámica, el p-hacking o la debilidad estructural.
        3. Falsación: Propón el test empírico destructivo (Proof of Work) que refutaría la tesis.
        
        El 'visual_prompt' de cada escena DEBE obligatoriamente estar condicionado por el 'global_style_vector'.
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
            logging.warning(f"Clúster {self.primary_model} saturado ({e}). Conmutando al nodo de contención {self.fallback_model}...")
            response = self.client.models.generate_content(
                model=self.fallback_model,
                contents=prompt,
                config=config,
            )
            return Storyboard.model_validate_json(response.text)

# ==============================================================================
# 3. TRANSDUCTOR MULTIMODAL, HUD DINÁMICO & SOUND DESIGN DSP
# ==============================================================================
class MultimodalTransducer:
    def __init__(self, voice: str = "Mónica"):
        self.voice = voice

    def get_audio_duration(self, audio_path: str) -> float:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())

    def render_hud_card(self, scene: FalsificationScene, out_path: str):
        """Genera tarjeta HUD transparente (1280x720) con ventana para osciloscopio en vivo"""
        W, H = 1280, 720
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font_mono_small = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 14)
        font_mono_bold = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 19)
        font_body = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 26)
        
        colors = {
            1: (0, 240, 220),   # Cyan
            2: (255, 180, 40),  # Amber
            3: (255, 75, 75)    # Crimson
        }
        accent = colors.get(scene.id, (200, 200, 200))
        titles = {1: "FASE 01: TESIS EPISTÉMICA", 2: "FASE 02: FRICCIÓN Y ANOMALÍA", 3: "FASE 03: TEST DESTRUCTIVO (FALSACIÓN)"}
        title = titles.get(scene.id, "FASE EXPERIMENTAL")
        
        # Panel Glassmórfico principal
        draw.rounded_rectangle([70, 45, W-70, H-45], radius=16, fill=(8, 11, 16, 225), outline=(45, 55, 70, 255), width=2)
        
        # Top Bar
        draw.text((100, 70), "● C5-REAL // TENSOR DE TRANSDUCCIÓN POPPERIANA", font=font_mono_small, fill=accent)
        draw.text((W-260, 70), "GEMINI 3.8 FLASH SOTA", font=font_mono_small, fill=(150, 165, 180))
        draw.line([100, 100, W-100, 100], fill=(45, 55, 70), width=1)
        
        # Badge Causal
        badge_w = 480 if scene.id == 3 else 390
        draw.rounded_rectangle([100, 120, 100 + badge_w, 165], radius=6, fill=(accent[0]//6, accent[1]//6, accent[2]//6, 255), outline=accent, width=2)
        draw.text((120, 132), title, font=font_mono_bold, fill=accent)
        
        # Texto del oráculo envuelto con tipografía suiza
        wrapped = textwrap.fill(scene.voiceover_text, width=60)
        draw.text((100, 195), wrapped, font=font_body, fill=(245, 250, 255), spacing=10)
        
        # Ventana del Osciloscopio Acústico en Vivo (recuadro de visualización)
        draw.rounded_rectangle([100, 465, W-100, 585], radius=8, fill=(3, 5, 8, 160), outline=(40, 52, 70, 255), width=1)
        draw.text((115, 475), f"OSCILOGRAMA ACÚSTICO EN TIEMPO REAL // DSP MASTER BUS", font=font_mono_small, fill=(100, 120, 140))
        
        # Bottom Telemetry Bar
        draw.line([100, H-105, W-100, H-105], fill=(45, 55, 70), width=1)
        prompt_snippet = scene.visual_prompt[:65] + "..." if len(scene.visual_prompt) > 65 else scene.visual_prompt
        draw.text((100, H-90), f"LATENTE: {prompt_snippet}", font=font_mono_small, fill=(110, 125, 140))
        
        prog_pct = scene.id * 33.33
        draw.text((W-250, H-90), f"COLAPSO D_KL: {prog_pct:.1f}%", font=font_mono_bold, fill=accent)
        
        img.save(out_path)

    def render_scene(self, scene: FalsificationScene, style_vector: str, output_dir: str):
        logging.info(f"Bifurcación Bimodal Escena {scene.id} | Sintetizando Voz, Retícula SEM y Osciloscopio...")
        
        # 1. CANAL AUDITIVO (TTS Soberano macOS)
        raw_audio = os.path.join(output_dir, f"raw_audio_{scene.id}.aiff")
        clean_text = scene.voiceover_text.replace('"', '\\"')
        cmd_say = f'say -v "{self.voice}" -o "{raw_audio}" "{clean_text}"'
        res = subprocess.run(cmd_say, shell=True)
        if res.returncode != 0:
            subprocess.run(f'say -o "{raw_audio}" "{clean_text}"', shell=True, check=True)
        
        # 2. CALIBRACIÓN TEMPORAL (Map == Territory)
        real_duration = self.get_audio_duration(raw_audio) + 0.8
        scene.duration_sec = real_duration
        logging.info(f"  -> Duración anclada al pulso de voz: {real_duration:.2f}s")
        
        # 3. CANAL VISUAL: HUD Card
        hud_card = os.path.join(output_dir, f"hud_card_{scene.id}.png")
        self.render_hud_card(scene, hud_card)
        
        # 4. SOUND DESIGN DSP (Voz + Sub-Bass Drone + Hiss Analógico)
        master_audio = os.path.join(output_dir, f"master_audio_{scene.id}.aac")
        cmd_dsp = [
            "ffmpeg", "-y",
            "-i", raw_audio,
            "-f", "lavfi", "-i", f"sine=frequency=52:duration={real_duration}",
            "-f", "lavfi", "-i", f"anoisesrc=d={real_duration}:c=pink:r=44100:a=0.006",
            "-filter_complex",
            "[0:a]highpass=f=80,lowpass=f=11000[voice]; "
            "[1:a]volume=0.13[sub]; "
            "[2:a]volume=0.18[hiss]; "
            "[voice][sub][hiss]amix=inputs=3:duration=first:dropout_transition=2[aout]",
            "-map", "[aout]", "-c:a", "aac", master_audio
        ]
        subprocess.run(cmd_dsp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 5. RENDER CINEMATOGRÁFICO V3 (Ruido SEM + Retícula + Osciloscopio Reactivo + HUD)
        visual_path = os.path.join(output_dir, f"scene_{scene.id}.mp4")
        wave_colors = {1: "0x00F0DC@0.85", 2: "0xFFB428@0.85", 3: "0xFF4B4B@0.85"}
        wave_col = wave_colors.get(scene.id, "0x00F0DC@0.85")
        
        v_filter = (
            f"color=c=black:s=1280x720:d={real_duration} [base]; "
            f"[base]noise=alls=20:allf=t+u [grain]; "
            f"[grain]drawgrid=width=120:height=120:thickness=1:color=0x203040@0.35 [bg]; "
            f"[1:a]showwaves=s=1060x82:mode=line:colors={wave_col}:scale=cbrt [wave]; "
            f"[bg][wave]overlay=110:492 [bg_wave]; "
            f"[bg_wave][2:v]overlay=0:0:format=auto [vout]"
        )
        
        cmd_v = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={real_duration}",
            "-i", raw_audio,
            "-i", hud_card,
            "-i", master_audio,
            "-filter_complex", v_filter,
            "-map", "[vout]", "-map", "3:a",
            "-t", str(real_duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            visual_path
        ]
        logging.info(f"  -> Compilando Escena {scene.id} con Osciloscopio Reactivo y Retícula...")
        subprocess.run(cmd_v, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        return visual_path

# ==============================================================================
# 4. ORCHESTRATOR (Multiplexado y Ensamblaje Final)
# ==============================================================================
class Orchestrator:
    @staticmethod
    def multiplex_scenes(scene_paths: List[str], output_file: str):
        logging.info("Iniciando Grafo de Ensamblaje Final (Concatenación Sin Anergía)...")
        concat_list = "/tmp/c5_render/concat_list.txt"
        with open(concat_list, "w") as f:
            for p in scene_paths:
                f.write(f"file '{p}'\n")
                
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_file
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logging.info(f"Documental Popperiano sellado con éxito: {output_file}")

# ==============================================================================
# ENTRYPOINT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Tensor de Transducción Popperiana C5-REAL (V3 SOTA)")
    parser.add_argument("--corpus", type=str, default=None, help="Texto o paper para someter a falsación")
    parser.add_argument("--file", type=str, default=None, help="Ruta a archivo de texto con el corpus")
    parser.add_argument("--voice", type=str, default="Mónica", help="Voz del sistema para TTS (ej. Mónica, Paulina, Flo)")
    parser.add_argument("--model", type=str, default="gemini-3.8-flash", help="Modelo rector (default: gemini-3.8-flash)")
    parser.add_argument("--output", type=str, default="/tmp/c5_render/historia_final.mp4", help="Ruta de destino del MP4")
    args = parser.parse_args()

    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("Fricción detectada: Variable de entorno GEMINI_API_KEY no definida.")

    if args.file and os.path.exists(args.file):
        with open(args.file, "r") as f:
            corpus = f.read()
    elif args.corpus:
        corpus = args.corpus
    else:
        corpus = (
            "La hipótesis de la memoria del agua sostiene que el agua retiene una impronta "
            "electromagnética de solutos previamente disueltos incluso tras sucesivas diluciones "
            "que superan el número de Avogadro. Por otro lado, la dinámica de fluidos cuánticos "
            "demuestra que los enlaces de hidrógeno en agua líquida tienen una vida media de picosegundos, "
            "destruyendo cualquier orden molecular coherente a temperatura ambiente."
        )

    override_metadata = "GLOBAL_STYLE_VECTOR: Microscopio electrónico de barrido, blanco y negro puro, alto contraste, grano cuántico, sobriedad matemática."

    director = DirectorAgent(api_key=API_KEY, model=args.model)
    transducer = MultimodalTransducer(voice=args.voice)
    
    try:
        storyboard = director.extract_invariants(corpus, override_metadata)
        logging.info(f"V_Global Fijado: {storyboard.global_style_vector}")
        
        out_dir = "/tmp/c5_render"
        os.makedirs(out_dir, exist_ok=True)
        
        scene_paths = []
        for scene in storyboard.scenes:
            path = transducer.render_scene(scene, storyboard.global_style_vector, out_dir)
            scene_paths.append(path)
            
        Orchestrator.multiplex_scenes(scene_paths, args.output)
        
    except Exception as e:
        logging.error(f"Fallo sistémico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
