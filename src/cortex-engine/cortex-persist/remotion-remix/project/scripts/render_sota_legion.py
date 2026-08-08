# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "legion_master.wav")
OUTPUT_VIDEO = os.path.join(PROJECT_DIR, "out_sota_legion.mp4")

def render_sota_legion_video():
    print(f"[SOTA KINETIC ENGINE] Rendering premium 1080p60fps glassmorphic background...")

    cmd = [
        "ffmpeg", "-y",
        "-i", AUDIO_FILE,
        "-filter_complex", (
            # 1. Premium Glassmorphic Deep Gradient Background (Dark Blue/Purple)
            "color=c=0x080A15:s=1080x1920:r=60[bg]; "

            # Subtle moving radial gradient overlay using a slow rotating hue
            "color=c=0x1E0D35@0.6:s=1080x1920:r=60,hue=h='t*15'[uv_wash]; "

            "[0:a]volume=2.5[vis_audio]; "

            # 2. Sleek, high-res audio spectrum (Smooth curves, minimal colors: Cyan & Purple)
            "[vis_audio]showspectrum=s=1080x600:mode=combined:color=cool:scale=cbrt:fscale=log:saturation=2:slide=scroll[spec]; "

            # 3. Crisp Audio Waveform (Neon Cyan)
            "[vis_audio]showwaves=s=1080x400:mode=cline:colors=0x00F0FF:rate=60[waves]; "

            # 4. Avectorscope for center geometric elegance (Lissajous curves with high opacity)
            "[vis_audio]avectorscope=s=800x800:m=lissajous:r=60,colorkey=black:0.1:0.0,format=rgba,colorchannelmixer=aa=0.8[vector]; "

            # Layering with additive blending (screen) for glassmorphic glow
            "[bg][uv_wash]overlay=0:0[v0]; "

            # Blend the spectrum softly at the bottom
            "[v0][spec]overlay=0:1320:format=auto[v1]; "

            # Blend the waveform in the middle
            "[v1][waves]overlay=0:1000[v2]; "

            # Blend the lissajous vector at the top center
            "[v2][vector]overlay=140:100[v3]; "

            # 5. Cinematic post-processing (very subtle vignette, high contrast, clean)
            "[v3]vignette=PI/4:eval=frame[v4]; "
            "[v4]eq=contrast=1.1:saturation=1.2[vout]; "

            "[0:a]volume=1.0[aout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-threads", "16",
        "-c:a", "aac",
        "-b:a", "320k",
        "-ac", "2",
        "-shortest",
        OUTPUT_VIDEO
    ]

    proc = subprocess.Popen(cmd)
    proc.wait()

    if proc.returncode == 0:
        print(f"[SOTA KINETIC ENGINE] ✅ RENDER COMPLETE -> {OUTPUT_VIDEO}")
    else:
        print(f"[SOTA KINETIC ENGINE] ❌ RENDER FAILED with code {proc.returncode}")

if __name__ == "__main__":
    if not os.path.exists(AUDIO_FILE):
        print(f"[SOTA KINETIC ENGINE] ❌ Audio file not found: {AUDIO_FILE}. Please generate it first.")
        exit(1)
    render_sota_legion_video()
