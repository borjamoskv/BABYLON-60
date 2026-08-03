import subprocess

# Queremos 417 segundos de fotos (7 minutos) a 1.5s por foto = 278 fotos
TOTAL_PHOTOS_NEEDED = 280
SECONDS_PER_PHOTO = 1.5

with open("out/fast_images.txt", "w") as f:
    for i in range(TOTAL_PHOTOS_NEEDED):
        idx = i % 53
        # FFmpeg concat format
        f.write(f"file '../public/media/batch_{idx}.jpg'\n")
        f.write(f"duration {SECONDS_PER_PHOTO}\n")
    
    # Needs to end with the last file again for ffmpeg concat quirk
    f.write(f"file '../public/media/batch_{(TOTAL_PHOTOS_NEEDED-1)%53}.jpg'\n")

print("[*] Generando slideshow a hiper-velocidad con FFmpeg puro...")

cmd = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "out/fast_images.txt",
    "-i", "public/audio.mp3",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    "out/aibon_fast.mp4"
]

subprocess.run(cmd)
print("[*] Slideshow generado: out/aibon_fast.mp4")
