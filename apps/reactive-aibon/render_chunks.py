#!/usr/bin/env python3
import os
import subprocess
import sys

# No purgamos los chunks anteriores porque ya están listos (1, 2, 3)
# NO ELIMINAMOS los chunks anteriores porque el bucle de supervivencia los necesita
# os.system("rm -rf out/chunks")
os.system("mkdir -p out/chunks")

CONCURRENCY = 4
CHUNK_SIZE = 1000
TOTAL_FRAMES = 12506

print("[*] Iniciando renderizado fraccionado (Slideshow Mode)")
print(f"[*] Concurrencia Térmica: {CONCURRENCY}x")
print(f"[*] Tamaño de Fragmento: {CHUNK_SIZE} frames")

chunk_files = []

for i in range(0, TOTAL_FRAMES, CHUNK_SIZE):
    start = i
    end = min(i + CHUNK_SIZE - 1, TOTAL_FRAMES - 1)
    chunk_idx = i // CHUNK_SIZE + 1
    
    file_name = f"chunk_{chunk_idx}.mp4"
    chunk_path = f"out/chunks/{file_name}"
    chunk_files.append(file_name)
    
    # Skip already rendered chunks
    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 1000000:
        print(f"[+] Fragmento {chunk_idx} ya existe, omitiendo...")
        continue

    cmd = [
        "npx", "remotion", "render", "src/index.ts", "AibonReactive",
        chunk_path,
        f"--frames={start}-{end}",
        f"--concurrency={CONCURRENCY}",
        "--scale=0.25",
        "--gl=angle",
        "--crf=30",
        "--preset=ultrafast"
    ]
    
    print(f"\n[+] Renderizando fragmento {chunk_idx}: frames {start}-{end}...")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"[-] ERROR crítico en el motor V8 durante el fragmento {chunk_idx}.")
        sys.exit(1)

print("\n[*] Fusión Termodinámica (Muxing Audio/Video)...")
with open("out/chunks/list.txt", "w") as f:
    for file_name in chunk_files:
        f.write(f"file '{file_name}'\n")

print("[*] Concatenando vídeo mudo...")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "out/chunks/list.txt", "-c:v", "copy", "-an", "out/temp.mp4"])

print("[*] Inyectando pista de audio maestra...")
subprocess.run(["ffmpeg", "-y", "-i", "out/temp.mp4", "-i", "public/audio.mp3", "-c:v", "copy", "-c:a", "aac", "-shortest", "out/video.mp4"])

print("\n[*] Cristalización de Silicio completada: out/video.mp4")
