# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "gon_fiction_master.wav")
OUTPUT_VIDEO = os.path.join(PROJECT_DIR, "out_gon_fiction_8bit.mp4")

def render_8bit_video():
    print(f"[8-BIT NES RENDER ENGINE] Starting parallel multi-threaded FFmpeg 8-Bit NES render for GON FICTION...")

    cmd = [
        "ffmpeg", "-y",
        "-i", AUDIO_FILE,
        "-filter_complex", (
            "color=c=0x020005:s=1080x1920:r=30[bg]; "
            "color=c=0x7B00FF@0.15:s=1080x1920:r=30[uv_wash]; "
            "color=c=0x2E5090:s=1080x4:r=30[yinmn_line]; "
            "color=c=0x3C69E7:s=1080x2:r=30[bluetiful_line]; "
            "color=c=0x00A86B:s=1080x2:r=30[oregon_line]; "
            "color=c=0xFFD300:s=1080x2:r=30[ntp_line]; "
            "[0:a]showspectrum=s=1080x550:mode=combined:color=plasma:scale=cbrt:fscale=log:saturation=4:slide=scroll[spec]; "
            "[0:a]showwaves=s=1080x200:mode=p2p:colors=0xFFD300|0x00A86B:rate=30[waves]; "
            "[0:a]showwaves=s=1080x150:mode=cline:colors=0x7B00FF|0x3C69E7:rate=30[waves_uv]; "
            "[bg][uv_wash]overlay=0:0[v0]; "
            "[v0][spec]overlay=0:300[v1]; "
            "[v1][yinmn_line]overlay=0:296[v2]; "
            "[v2][bluetiful_line]overlay=0:852[v3]; "
            "[v3][waves]overlay=0:1250[v4]; "
            "[v4][oregon_line]overlay=0:1246[v5]; "
            "[v5][waves_uv]overlay=0:1500[v6]; "
            "[v6][ntp_line]overlay=0:1496[v7]; "
            "[v7]vignette=PI/4[v8]; "
            "[v8]eq=contrast=1.2:saturation=1.4:gamma=0.9[v9]; "
            "[v9]scale=135:240:flags=area,scale=1080:1920:flags=neighbor[v10]; "
            "[v10]hue=s=1.3[vout]; "
            "[0:a]volume=2.2,pan=stereo|c0=c0|c1=c0[aout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "h264_videotoolbox",
        "-b:v", "6M",
        "-c:a", "aac",
        "-b:a", "320k",
        "-ac", "2",
        "-shortest",
        OUTPUT_VIDEO
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[8-BIT NES RENDER ENGINE] ✅ SUCCESS! Rendered GON FICTION 8-bit to {OUTPUT_VIDEO}")
    except subprocess.CalledProcessError:
        print(f"[8-BIT NES RENDER ENGINE] h264_videotoolbox failed, falling back to libx264 with 16 threads...")
        cmd[cmd.index("h264_videotoolbox")] = "libx264"
        cmd.insert(cmd.index("libx264") + 1, "-preset")
        cmd.insert(cmd.index("libx264") + 2, "fast")
        cmd.insert(cmd.index("libx264") + 3, "-crf")
        cmd.insert(cmd.index("libx264") + 4, "18")
        cmd.insert(cmd.index("libx264") + 5, "-threads")
        cmd.insert(cmd.index("libx264") + 6, "16")
        cmd.remove("-b:v")
        cmd.remove("6M")
        subprocess.run(cmd, check=True)
        print(f"[8-BIT NES RENDER ENGINE] ✅ SUCCESS! Rendered GON FICTION 8-bit to {OUTPUT_VIDEO}")

if __name__ == "__main__":
    render_8bit_video()
