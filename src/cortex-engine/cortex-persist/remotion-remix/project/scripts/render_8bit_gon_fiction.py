# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "gon_fiction_master.wav")
OUTPUT_VIDEO = os.path.join(PROJECT_DIR, "out_gon_fiction_8bit.mp4")

def render_ultra_reactive_8bit_video():
    print(f"[AUDIO-REACTIVE 8-BIT ENGINE] Building hyper-reactive audio visualization with real-time VU meters & multi-band spectrum...")

    # HIGHLY AUDIO-REACTIVE FFmpeg PIPELINE:
    # 1. Base Dark Vantablack Canvas
    # 2. showspectrum (top): Plasma color scale, log frequency, reacting to vocal formants
    # 3. showspectrum (middle): Fire color scale, sub-bass reactivity
    # 4. showwaves (bottom 1): Peak-to-peak amplitude waveform (NTP Yellow & Oregon Green)
    # 5. showwaves (bottom 2): Vector line waveform (UV Blacklight & Bluetiful)
    # 6. showvolume (left & right borders): Stereo audio VU meters pulsing with every spoken word
    # 7. Pixelation scaling: 1080x1920 -> 135x240 -> 1080x1920 (nearest neighbor)

    cmd = [
        "ffmpeg", "-y",
        "-i", AUDIO_FILE,
        "-filter_complex", (
            "color=c=0x020005:s=1080x1920:r=30[bg]; "
            "color=c=0x7B00FF@0.15:s=1080x1920:r=30[uv_wash]; "

            # 1. Main Vocal Formant Spectrum (Plasma)
            "[0:a]showspectrum=s=1080x550:mode=combined:color=plasma:scale=cbrt:fscale=log:saturation=4:slide=scroll[spec1]; "

            # 2. Sub-bass & Transients Spectrum (Fire)
            "[0:a]showspectrum=s=1080x300:mode=separate:color=fire:scale=log:fscale=lin:saturation=3:slide=rscroll[spec2]; "

            # 3. Peak Audio Waveform
            "[0:a]showwaves=s=1080x220:mode=p2p:colors=0xFFD300|0x00A86B:rate=30[waves1]; "

            # 4. Vector Line Waveform
            "[0:a]showwaves=s=1080x180:mode=cline:colors=0x7B00FF|0x3C69E7:rate=30[waves2]; "

            # 5. Real-time Stereo VU Volume Meters (Side Audio Bars)
            "[0:a]showvolume=s=60x1920:b=4:c=0x00F0FF:v=1:f=0.95[vu_left]; "
            "[0:a]showvolume=s=60x1920:b=4:c=0xFF00FF:v=1:f=0.95[vu_right]; "

            # Color Accent Lines
            "color=c=0x2E5090:s=1080x6:r=30[yinmn_line]; "
            "color=c=0x3C69E7:s=1080x4:r=30[bluetiful_line]; "
            "color=c=0x00A86B:s=1080x4:r=30[oregon_line]; "
            "color=c=0xFFD300:s=1080x4:r=30[ntp_line]; "

            # Layering Complex
            "[bg][uv_wash]overlay=0:0[v0]; "
            "[v0][spec1]overlay=0:250[v1]; "
            "[v1][yinmn_line]overlay=0:244[v2]; "
            "[v2][bluetiful_line]overlay=0:852[v3]; "
            "[v3][spec2]overlay=0:900[v4]; "
            "[v4][waves1]overlay=0:1250[v5]; "
            "[v5][oregon_line]overlay=0:1244[v6]; "
            "[v6][waves2]overlay=0:1520[v7]; "
            "[v7][ntp_line]overlay=0:1514[v8]; "
            "[v8][vu_left]overlay=0:0[v9]; "
            "[v9][vu_right]overlay=1020:0[v10]; "

            # Post-Processing & 8-Bit Pixelation
            "[v10]vignette=PI/4:eval=frame[v11]; "
            "[v11]eq=contrast=1.3:saturation=1.5:gamma=0.88[v12]; "
            "[v12]scale=135:240:flags=area,scale=1080:1920:flags=neighbor[v13]; "
            "[v13]hue=s=1.4[vout]; "

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
        print(f"[AUDIO-REACTIVE 8-BIT ENGINE] ✅ RENDER COMPLETE -> {OUTPUT_VIDEO}")
    except subprocess.CalledProcessError:
        print(f"[AUDIO-REACTIVE 8-BIT ENGINE] Fallback to libx264 16 threads...")
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
        print(f"[AUDIO-REACTIVE 8-BIT ENGINE] ✅ RENDER COMPLETE -> {OUTPUT_VIDEO}")

if __name__ == "__main__":
    render_ultra_reactive_8bit_video()
