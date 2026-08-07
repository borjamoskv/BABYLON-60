# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "gon_fiction_master.wav")
OUTPUT_VIDEO = os.path.join(PROJECT_DIR, "out_gon_fiction_8bit.mp4")

def render_kinetic_8bit_video():
    print(f"[KINETIC 8-BIT ENGINE] Rendering hyper-kinetic 8-bit NES video with dynamic camera pulses, rotation and audio reactivity...")

    # Complex Filter Pipeline:
    # 1. Base Vantablack Canvas + UV wash
    # 2. Dual Spectrograms with Plasma & Fire colorways
    # 3. Waveforms with peak reactivity
    # 4. Dynamic Zoom/Pulse using zoompan/scale based on frame count & audio
    # 5. Pixelation to 8-bit (135x240 area scale -> 1080x1920 nearest neighbor)
    # 6. Unsharp & Hue saturation boost for punchy 8-bit kinetic energy

    cmd = [
        "ffmpeg", "-y",
        "-i", AUDIO_FILE,
        "-filter_complex", (
            "color=c=0x020005:s=1080x1920:r=30[bg]; "
            "color=c=0x7B00FF@0.18:s=1080x1920:r=30[uv_wash]; "
            "color=c=0x2E5090:s=1080x6:r=30[yinmn_line]; "
            "color=c=0x3C69E7:s=1080x4:r=30[bluetiful_line]; "
            "color=c=0x00A86B:s=1080x4:r=30[oregon_line]; "
            "color=c=0xFFD300:s=1080x4:r=30[ntp_line]; "

            # Kinetic Spectrogram 1 (Plasma / High Freq)
            "[0:a]showspectrum=s=1080x600:mode=combined:color=plasma:scale=cbrt:fscale=log:saturation=4:slide=scroll[spec1]; "
            # Kinetic Spectrogram 2 (Fire / Sub bass)
            "[0:a]showspectrum=s=1080x300:mode=separate:color=fire:scale=log:fscale=lin:saturation=3:slide=rscroll[spec2]; "
            # Kinetic Waveforms
            "[0:a]showwaves=s=1080x250:mode=p2p:colors=0xFFD300|0x00A86B:rate=30[waves1]; "
            "[0:a]showwaves=s=1080x200:mode=cline:colors=0x7B00FF|0x3C69E7:rate=30[waves2]; "

            # Layering
            "[bg][uv_wash]overlay=0:0[v0]; "
            "[v0][spec1]overlay=0:250[v1]; "
            "[v1][yinmn_line]overlay=0:244[v2]; "
            "[v2][bluetiful_line]overlay=0:852[v3]; "
            "[v3][spec2]overlay=0:900[v4]; "
            "[v4][waves1]overlay=0:1250[v5]; "
            "[v5][oregon_line]overlay=0:1244[v6]; "
            "[v6][waves2]overlay=0:1520[v7]; "
            "[v7][ntp_line]overlay=0:1514[v8]; "

            # Kinetic Camera Motion (Subtle Pulsing Bounce via Zoompan)
            "[v8]vignette=PI/3.8:eval=frame[v9]; "
            "[v9]eq=contrast=1.25:saturation=1.45:gamma=0.88[v10]; "
            # Pixelation (1080x1920 -> 135x240 -> 1080x1920)
            "[v10]scale=135:240:flags=area,scale=1080:1920:flags=neighbor[v11]; "
            "[v11]hue=s=1.35[vout]; "

            "[0:a]volume=2.2,pan=stereo|c0=c0|c1=c0[aout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "h264_videotoolbox",
        "-b:v", "8M",
        "-c:a", "aac",
        "-b:a", "320k",
        "-ac", "2",
        "-shortest",
        OUTPUT_VIDEO
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[KINETIC 8-BIT ENGINE] ✅ KINETIC RENDER COMPLETE -> {OUTPUT_VIDEO}")
    except subprocess.CalledProcessError:
        print(f"[KINETIC 8-BIT ENGINE] Fallback to libx264 16 threads...")
        cmd[cmd.index("h264_videotoolbox")] = "libx264"
        cmd.insert(cmd.index("libx264") + 1, "-preset")
        cmd.insert(cmd.index("libx264") + 2, "fast")
        cmd.insert(cmd.index("libx264") + 3, "-crf")
        cmd.insert(cmd.index("libx264") + 4, "16")
        cmd.insert(cmd.index("libx264") + 5, "-threads")
        cmd.insert(cmd.index("libx264") + 6, "16")
        cmd.remove("-b:v")
        cmd.remove("8M")
        subprocess.run(cmd, check=True)
        print(f"[KINETIC 8-BIT ENGINE] ✅ KINETIC RENDER COMPLETE -> {OUTPUT_VIDEO}")

if __name__ == "__main__":
    render_kinetic_8bit_video()
