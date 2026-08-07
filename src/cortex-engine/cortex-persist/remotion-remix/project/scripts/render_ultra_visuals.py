# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "sequel_master.wav")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "out_intervalo_prohibido_2.mp4")

print("=== C5-REAL ULTRA-IMMERSIVE CINEMATIC VIDEO RENDER PIPELINE ===")

if not os.path.exists(AUDIO_FILE):
    print("Audio file missing:", AUDIO_FILE)
    exit(1)

# Advanced Multi-Layered FFmpeg Visualizer:
# 1. Top half: Audio-reactive Glowing Cyan Oscilloscope Waveform
# 2. Bottom half: Rainbow High-Density Audio Frequency Spectrum (Sagittarius A* Horizon)
# 3. Dynamic Audio Mastering with 256k Stereo AAC Audio
filter_complex = (
    "[0:a]showwaves=s=1080x960:mode=line:colors=0x00F0FF|0xFF00FF[waves];"
    "[0:a]showspectrum=s=1080x960:mode=combined:color=rainbow:scale=log:saturation=3[spec];"
    "[waves][spec]vstack[v];"
    "[0:a]volume=2.2,pan=stereo|c0=c0|c1=c0[aout]"
)

cmd = [
    "ffmpeg", "-y",
    "-i", AUDIO_FILE,
    "-filter_complex", filter_complex,
    "-map", "[v]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "256k",
    OUTPUT_FILE
]

print("Executing Ultra-Immersive Cinematic Render...")
subprocess.run(cmd, check=True)
print("=== RENDER COMPLETE ===")
print("Master video created at:", OUTPUT_FILE)
