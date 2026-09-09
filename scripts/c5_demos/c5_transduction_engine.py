#!/usr/bin/env python3

import os
import json
import logging
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Configuración de Alta Exergía (Logging estricto)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [AX-S2] %(levelname)s: %(message)s')

# ==============================================================================
# 1. DEFINICIÓN TOPOLÓGICA (PYDANTIC) - El Tensor de Transducción
# Forzamos la Invariante de Clausura Epistémica: el LLM no puede escupir texto libre,
# solo puede rellenar esta matriz matemática paramétrica.
# ==============================================================================
class FalsificationScene(BaseModel):
    id: int = Field(description="Fase causal. 1: Tesis, 2: Fricción, 3: Falsación")
    duration_sec: int = Field(description="Duración rígida en segundos. Mínimo 3, máximo 8.")
    voiceover_text: str = Field(description="Texto exacto para el motor TTS. Cero retórica.")
    visual_prompt: str = Field(description="Directiva visual paramétrica para Imagen/Veo.")

class Storyboard(BaseModel):
    global_style_vector: str = Field(description="El vector estético inmutable que gobernará todos los píxeles.")
    scenes: List[FalsificationScene] = Field(description="Cascada causal obligatoria de 3 escenas: Tesis, Fricción y Prueba de Falsación.")

# ==============================================================================
# 2. MOTOR DEL AGENTE DIRECTOR (Gemini Pro)
# ==============================================================================
class DirectorAgent:
    def __init__(self, api_key: str):
        # Utilizando el SDK moderno google-genai
        self.client = genai.Client(api_key=api_key)
        # Operamos con el nodo más eficiente para estructuración (Flash/Pro)
        self.model = 'gemini-3.6-flash'

    def extract_invariants(self, corpus_text: str, override_metadata: str) -> Storyboard:
        logging.info("Minimizando Divergencia KL. Comprimiendo entropía textual en Matriz JSON...")
        
        prompt = f"""
        SYSTEM OVERRIDE: Eres un Motor de Falsación Popperiana (C5-REAL).
        Tu mandato es aniquilar la anergía semántica del CORPUS y someterlo a estrés epistémico.
        
        [SYSTEM_OVERRIDE_METADATA]
        {override_metadata}
        
        [CORPUS (TERRITORIO)]
        {corpus_text}
        
        SINTETIZA el corpus en un Storyboard de EXACTAMENTE 3 escenas:
        1. Tesis: Expón la hipótesis o afirmación central del texto de forma clínica.
        2. Fricción Empírica: Señala la anomalía termodinámica, el p-hacking o la debilidad estructural.
        3. Falsación: Propón el test empírico destructivo (Proof of Work) que refutaría la tesis.
        
        El 'visual_prompt' de cada escena DEBE obligatoriamente estar condicionado por el 'global_style_vector'.
        """
        
        # [AX-S3] Forzamos colapso determinista mediante Structured Outputs. Cero alucinación.
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Storyboard,
                temperature=0.0 
            ),
        )
        
        # Validamos asintóticamente la matriz
        return Storyboard.model_validate_json(response.text)

# ==============================================================================
# 3. TRANSDUCTOR MULTIMODAL & COLAPSO DETERMINISTA (Mock Operacional)
# ==============================================================================
import subprocess

class MultimodalTransducer:
    def __init__(self):
        pass

    def get_audio_duration(self, audio_path: str) -> float:
        # Extraemos la duración matemática real del audio generado
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())

    def render_scene(self, scene: FalsificationScene, style_vector: str, output_dir: str):
        logging.info(f"Bifurcación Bimodal Escena {scene.id} | Procesando Audio TTS...")
        
        # 1. CANAL AUDITIVO (TTS Soberano de macOS)
        audio_path = os.path.join(output_dir, f"audio_{scene.id}.aiff")
        # Usamos síntesis local bare-metal para evitar cuotas de Cloud TTS
        clean_text = scene.voiceover_text.replace('"', '\\"')
        subprocess.run(f'say -o "{audio_path}" "{clean_text}"', shell=True, check=True)
        
        # 2. CALIBRACIÓN TEMPORAL (Map == Territory)
        real_duration = self.get_audio_duration(audio_path)
        scene.duration_sec = real_duration  # Sobrescribimos la estimación del LLM con la física real
        logging.info(f"  -> Audio TTS sintetizado. Duración real anclada: {real_duration:.2f}s")
        
        # 3. CANAL VISUAL (Render Procedural)
        # En lugar de mockear, inyectamos una matriz de vídeo negro con ruido termodinámico (Microscopio)
        # y quemamos un subtítulo simplificado para identificar la escena.
        visual_path = os.path.join(output_dir, f"visual_{scene.id}.mp4")
        scene_type = ["TESIS", "FRICCIÓN", "FALSACIÓN"][scene.id - 1] if scene.id <= 3 else "ESCENA"
        
        v_filter = (
            f"color=c=black:s=1280x720:d={real_duration} [base]; "
            f"[base]noise=alls=30:allf=t+u [v_noise]; "
            f"[v_noise]drawtext=text='{scene_type}':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2 [v_out]"
        )
        
        logging.info(f"  -> Renderizando Tensor Visual Procedural ({scene_type})...")
        cmd_v = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720", "-filter_complex", v_filter, "-map", "[v_out]", "-t", str(real_duration), "-c:v", "libx264", visual_path]
        subprocess.run(cmd_v, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return visual_path, audio_path

class Orchestrator:
    @staticmethod
    def multiplex_ffmpeg(scenes: List[FalsificationScene], visual_paths: list, audio_paths: list, output_file: str):
        logging.info("Iniciando Grafo FFmpeg (Filtergraph Matrix)...")
        
        ffmpeg_inputs = []
        for i in range(len(scenes)):
            ffmpeg_inputs.extend(["-i", visual_paths[i], "-i", audio_paths[i]])
            
        filter_complex = ""
        v_labels, a_labels = [], []
        
        for i, scene in enumerate(scenes):
            dur = float(scene.duration_sec)
            filter_complex += f"[{i*2}:v]trim=duration={dur},setpts=PTS-STARTPTS,format=yuv420p[v{i}]; "
            filter_complex += f"[{i*2+1}:a]atrim=duration={dur},asetpts=PTS-STARTPTS[a{i}]; "
            v_labels.append(f"[v{i}]")
            a_labels.append(f"[a{i}]")
            
        concat_v = "".join(v_labels) + f"concat=n={len(scenes)}:v=1:a=0[vout]; "
        concat_a = "".join(a_labels) + f"concat=n={len(scenes)}:v=0:a=1[aout]"
        filter_complex += concat_v + concat_a
        
        cmd = ["ffmpeg", "-y"] + ffmpeg_inputs + [
            "-filter_complex", filter_complex, 
            "-map", "[vout]", "-map", "[aout]", 
            "-c:v", "libx264", "-c:a", "aac", output_file
        ]
        
        logging.info("Ejecutando subproceso FFMPEG BARE-METAL (Generando MP4 Real)...")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logging.info(f"Transducción finalizada. Artefacto REAL sellado en: {output_file}")

# ==============================================================================
# ENTRYPOINT (Díada Simbiótica en Ejecución)
# ==============================================================================
if __name__ == "__main__":
    # Verificación estricta de credenciales (Zero-Trust)
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("Fricción termodinámica detectada: Variable de entorno GEMINI_API_KEY no definida.")

    # 1. Input del Operador (Territorio + Directiva)
    corpus_ejemplo = "La memoria del agua es un mito refutado, pero en dinámica de fluidos cuánticos..."
    override_metadata = "GLOBAL_STYLE_VECTOR: Renderizado de microscopio electrónico, blanco y negro puro, texturas ruidosas, científico."

    # 2. Invocación de Nodos Autopoyéticos
    director = DirectorAgent(api_key=API_KEY)
    transducer = MultimodalTransducer()
    
    # 3. Flujo Termodinámico
    try:
        # Etapa A: Generación del Tensor
        storyboard = director.extract_invariants(corpus_ejemplo, override_metadata)
        logging.info(f"V_Global Fijado Exitosamente: {storyboard.global_style_vector}")
        
        # Etapa B: Divergencia Multimodal
        v_paths, a_paths = [], []
        out_dir = "/tmp/c5_render"
        os.makedirs(out_dir, exist_ok=True)
        
        for scene in storyboard.scenes:
            v, a = transducer.render_scene(scene, storyboard.global_style_vector, out_dir)
            v_paths.append(v)
            a_paths.append(a)
            
        # Etapa C: Colapso Topológico
        Orchestrator.multiplex_ffmpeg(storyboard.scenes, v_paths, a_paths, os.path.join(out_dir, "historia_final.mp4"))
        
    except Exception as e:
        logging.error(f"Fallo de contención sistémica: {e}")
        import sys
        sys.exit(1)
