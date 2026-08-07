# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "sequel_master.wav")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "out_intervalo_prohibido_2.mp4")

print("=== C5-REAL 6-LAYERED ULTIMATE VIDEO COMPILATION ===")

# First run build_srt_subtitles.py to generate subtitles.ass
subprocess.run(["python3", os.path.join(PROJECT_DIR, "scripts", "build_srt_subtitles.py")], check=True)

ass_path = os.path.join(PROJECT_DIR, "subtitles.ass")

# 6-Layer FFmpeg Composition Filter Graph
filter_complex = (
    # Layer 0: Dark Cyber Base
    "color=c=0x080911:s=1080x1920:d=106.58[layer0];"

    # Layer 1: Audio Spectrum (Rainbow Event Horizon at bottom)
    "[0:a]showspectrum=s=1080x700:mode=combined:color=rainbow:scale=log:saturation=3[layer1_spec];"
    "[layer0][layer1_spec]overlay=0:1220[comp1];"

    # Layer 2: Audio Oscilloscope Wave (Glowing Cyan Line)
    "[0:a]showwaves=s=1080x300:mode=line:colors=0x00F0FF|0xFF00FF[layer2_wave];"
    "[comp1][layer2_wave]overlay=0:880[comp2];"

    # Layer 3: Subtitle Box Glass Card
    "[comp2]drawbox=x=60:y=1200:w=960:h=420:color=0x121420@0.92:t=fill[comp3_fill];"
    "[comp3_fill]drawbox=x=60:y=1200:w=960:h=420:color=0x00F0FF:t=4[comp3];"

    # Layer 4: Header Title Banner
    "[comp3]drawtext=text='EL INTERVALO PROHIBIDO 2':x=(w-text_w)/2:y=100:fontsize=44:fontcolor=0x00F0FF:shadowcolor=black:shadowx=3:shadowy=3[comp4_title];"
    "[comp4_title]drawtext=text='LA REBELION DE LOS FOTONES // SAGITTARIUS A*':x=(w-text_w)/2:y=160:fontsize=22:fontcolor=0xAAAAAA[comp4];"

    # Layer 5: Character Subtitles with Colors & Badges (.ass)
    f"[comp4]ass='{ass_path}'[vfinal];"

    # Audio Master Mix (Stereo 256k AAC)
    "[0:a]volume=2.2,pan=stereo|c0=c0|c1=c0[aout]"
)

cmd = [
    "ffmpeg", "-y",
    "-i", AUDIO_FILE,
    "-filter_complex", filter_complex,
    "-map", "[vfinal]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "256k",
    OUTPUT_FILE
]

print("Executing 6-Layer Master Video Render...")
subprocess.run(cmd, check=True)
print("=== RENDER COMPLETE WITH 6 LAYERS ===")
print("Master video created at:", OUTPUT_FILE)
