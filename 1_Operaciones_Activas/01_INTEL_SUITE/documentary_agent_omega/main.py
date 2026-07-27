# C5-REAL EXERGY CERTIFIED
import os
import sys
import json
import asyncio
import subprocess
import time
from pathlib import Path
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from duckduckgo_search import DDGS
from tqdm import tqdm
import urllib.request

# C5-REAL: Documentary Agent using Gemini Omni Flash
# Autor: borjamoskv

class Scene(BaseModel):
    narrator_text: str = Field(description="The exact text the narrator will read.")
    visual_search_query: str = Field(description="A 2-3 word search query to find a relevant image on DuckDuckGo.")

class DocumentaryScript(BaseModel):
    title: str = Field(description="The title of the documentary.")
    scenes: list[Scene] = Field(description="List of scenes. A 20-minute documentary needs around 80-100 scenes (each ~15 seconds).")

def generate_script(topic: str) -> DocumentaryScript:
    """Generates the script using Gemini 2.5 Flash."""
    print(f"[*] Generando guion para: {topic}")
    client = genai.Client() # Requires GEMINI_API_KEY in env

    prompt = f"""
    Eres un guionista de documentales de alto impacto para YouTube.
    Tu objetivo es crear un guion estructurado para un documental sobre: '{topic}'.
    El documental debe durar aproximadamente 20 minutos (alrededor de 2500 a 3000 palabras en total).

    Divide el documental en numerosas escenas breves.
    Para CADA escena, proporciona:
    1. 'narrator_text': El guion narrativo exacto (profundo, épico, y atrapante).
    2. 'visual_search_query': Una consulta de búsqueda visual de 2-3 palabras en inglés (ej: 'ancient rome architecture', 'cyberpunk city night', 'galaxy space').
    """

    retries = 5
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DocumentaryScript,
                    temperature=0.7,
                ),
            )
            return DocumentaryScript.model_validate_json(response.text)
        except Exception as e:
            print(f"[-] Fallo en LLM (intento {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                wait_t = 5 * (2 ** attempt)
                print(f"[*] Reintentando en {wait_t}s...")
                time.sleep(wait_t)
            else:
                raise

async def generate_audio(text: str, output_path: str):
    """Generates TTS using edge-tts."""
    # Using the edge-tts CLI tool directly
    cmd = [
        "edge-tts",
        "--voice", "es-ES-AlvaroNeural", # Spanish voice, or en-US-AriaNeural
        "--text", text,
        "--write-media", output_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

def fetch_image(query: str, output_path: str):
    """Fetches a relevant image using Wikimedia Commons API (C5-REAL Robust)."""
    import urllib.parse
    try:
        safe_query = urllib.parse.quote(query)
        api_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={safe_query}&gsrnamespace=6&gsrlimit=1&prop=imageinfo&iiprop=url&format=json"

        req = urllib.request.Request(api_url, headers={'User-Agent': 'DocumentaryAgentOmega/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        if 'query' in data and 'pages' in data['query']:
            pages = data['query']['pages']
            page = next(iter(pages.values()))
            if 'imageinfo' in page and len(page['imageinfo']) > 0:
                image_url = page['imageinfo'][0]['url']
                # Filtrar SVGs o formatos no compatibles con FFmpeg fácilmente
                if not image_url.lower().endswith('.svg'):
                    req_img = urllib.request.Request(image_url, headers={'User-Agent': 'DocumentaryAgentOmega/1.0'})
                    with urllib.request.urlopen(req_img) as response_img, open(output_path, 'wb') as out_file:
                        out_file.write(response_img.read())
                    return True

        # Fallback to DDG con delay para evitar 403
        time.sleep(2.5)
        results = DDGS().images(query, max_results=1)
        if results and len(results) > 0:
            image_url = results[0]['image']
            req_img = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_img) as response_img, open(output_path, 'wb') as out_file:
                out_file.write(response_img.read())
            return True

    except Exception as e:
        print(f"Error fetching image for '{query}': {e}")
    return False

def create_scene_video(image_path: str, audio_path: str, output_path: str):
    """Creates a video from an image and audio using FFmpeg with a Ken Burns effect."""
    # C5-REAL: Robust FFmpeg execution
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-vf", "zoompan=z='min(zoom+0.0015,1.5)':d=0", # Ken Burns effect
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def concat_videos(video_files: list[str], output_path: str):
    """Concatenates all scene videos into the final documentary."""
    list_path = "concat_list.txt"
    with open(list_path, "w") as f:
        for vid in video_files:
            f.write(f"file '{vid}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(list_path)

async def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("Uso: python main.py [tema_del_documental]")
        print("Genera un documental audiovisual C5-REAL completo usando Gemini Omni Flash, Edge-TTS y FFmpeg.")
        return

    if len(sys.argv) < 2:
        topic = "El Colapso de la Edad de Bronce" # Fallback épico por defecto
    else:
        topic = sys.argv[1]

    # 1. Generate Script
    script = generate_script(topic)

    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    # Save script
    with open(workspace / "script.json", "w", encoding="utf-8") as f:
        f.write(script.model_dump_json(indent=2))

    print(f"[*] Guion generado: {len(script.scenes)} escenas. Título: {script.title}")

    # 2. Process Scenes
    video_files = []

    for i, scene in enumerate(tqdm(script.scenes, desc="Procesando escenas")):
        scene_prefix = workspace / f"scene_{i:03d}"
        audio_path = f"{scene_prefix}.mp3"
        image_path = f"{scene_prefix}.jpg"
        video_path = f"{scene_prefix}.mp4"

        # Audio
        await generate_audio(scene.narrator_text, audio_path)

        # Image
        success = fetch_image(scene.visual_search_query, image_path)
        if not success:
            # Fallback to a solid black image if fetch fails
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1920x1080", "-vframes", "1", image_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Video
        create_scene_video(image_path, audio_path, video_path)
        video_files.append(video_path)

    # 3. Concatenate
    print("[*] Ensamblando documental final...")
    final_output = f"{script.title.replace(' ', '_')}.mp4"
    concat_videos(video_files, final_output)

    print(f"[+] Documental C5-REAL completado: {final_output}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
