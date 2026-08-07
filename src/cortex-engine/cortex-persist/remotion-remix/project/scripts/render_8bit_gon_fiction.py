# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "gon_fiction_master.wav")
OUTPUT_VIDEO = os.path.join(PROJECT_DIR, "out_gon_fiction_8bit.mp4")

def render_ultra_reactive_8bit_video():
    print(f"[KINETIC 8-BIT ENGINE] Building hyper-kinetic audio visualization with real-time VU meters & multi-band spectrum...")

    # HIGHLY AUDIO-REACTIVE FFmpeg PIPELINE:
    cmd = [
        "ffmpeg", "-y",
        "-i", AUDIO_FILE,
        "-filter_complex", (
            # Backgrounds
            "color=c=0x020005:s=1080x1920:r=30[bg]; "
            "color=c=0x7B00FF@0.35:s=1080x1920:r=30,hue=h='t*45'[uv_wash]; " # Hue cycling for dynamic background

            # Boost audio for visualizers to make them more kinetic
            "[0:a]volume=4.0[vis_audio]; "

            # 1. Main Vocal Formant Spectrum (Plasma)
            "[vis_audio]showspectrum=s=1080x600:mode=combined:color=plasma:scale=cbrt:fscale=log:saturation=5:slide=scroll,hue=h='t*20'[spec1]; "

            # 2. Sub-bass & Transients Spectrum (Fire)
            "[vis_audio]showspectrum=s=1080x350:mode=separate:color=fire:scale=log:fscale=lin:saturation=5:slide=rscroll[spec2]; "

            # 3. Peak Audio Waveform
            "[vis_audio]showwaves=s=1080x300:mode=p2p:colors=0xFFD300|0x00A86B:rate=30[waves1]; "

            # 4. Vector Line Waveform
            "[vis_audio]showwaves=s=1080x250:mode=cline:colors=0x7B00FF|0x3C69E7:rate=30[waves2]; "

            # 4b. NEW: Avectorscope (Lissajous curves) for organic center geometry
            "[vis_audio]avectorscope=s=800x800:m=lissajous:r=30,colorkey=black:0.1:0.0,format=rgba,colorchannelmixer=aa=0.7[vector]; "

            # 5. Real-time Stereo VU Volume Meters (Side Audio Bars)
            "[vis_audio]showvolume=w=80:h=900:b=5:c=0x00F0FF:v=1:f=0.9,scale=80:1920[vu_left]; "
            "[vis_audio]showvolume=w=80:h=900:b=5:c=0xFF00FF:v=1:f=0.9,scale=80:1920[vu_right]; "

            # Color Accent Lines (Neon)
            "color=c=0x2E5090:s=1080x8:r=30[yinmn_line]; "
            "color=c=0x3C69E7:s=1080x8:r=30[bluetiful_line]; "
            "color=c=0x00A86B:s=1080x8:r=30[oregon_line]; "
            "color=c=0xFFD300:s=1080x8:r=30[ntp_line]; "

            # CRT Scanlines
            "color=c=black@0.4:s=1080x1920:r=30,drawgrid=w=1080:h=6:t=3:c=black@0.8[scanlines]; "

            # Layering Complex
            "[bg][uv_wash]overlay=0:0[v0]; "
            "[v0][spec1]overlay=0:200[v1]; "
            "[v1][yinmn_line]overlay=0:192[v2]; "
            "[v2][bluetiful_line]overlay=0:800[v3]; "
            "[v3][spec2]overlay=0:850[v4]; "
            "[v4][waves1]overlay=0:1200[v5]; "
            "[v5][oregon_line]overlay=0:1192[v6]; "
            "[v6][vector]overlay=140:560[v7]; " # Center the Lissajous vectorscope
            "[v7][waves2]overlay=0:1500[v8]; "
            "[v8][ntp_line]overlay=0:1492[v9]; "
            "[v9][vu_left]overlay=0:0[v10]; "
            "[v10][vu_right]overlay=1000:0[v11]; "
            "[v11][scanlines]overlay=0:0[v12]; "

            # Post-Processing: Glitch, CRT distortion, Pixelation
            "[v12]noise=alls=12:allf=t+u[v13]; " # Dynamic film grain
            "[v13]vignette=PI/3:eval=frame[v14]; "
            "[v14]lenscorrection=cx=0.5:cy=0.5:k1=0.15:k2=0.15[v15]; " # CRT bulge
            "[v15]rgbashift=rh=4:bv=-4:gh=-2[v16]; " # Chromatic aberration (Glitch intensified)
            "[v16]eq=contrast=1.7:saturation=2.2:gamma=0.75[v17]; "

            # 8-Bit Pixelation (Nes style)
            "[v17]scale=135:240:flags=area,scale=1080:1920:flags=neighbor[v18]; "

            # Final touch: Vibrance and pop
            "[v18]colorlevels=rimin=0.03:gimin=0.03:bimin=0.03:rimax=0.97:gimax=0.97:bimax=0.97[vout]; "

            "[0:a]volume=2.2,pan=stereo|c0=c0|c1=c0[aout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-threads", "16",
        "-c:a", "aac",
        "-b:a", "320k",
        "-ac", "2",
        "-shortest",
        OUTPUT_VIDEO
    ]

    subprocess.run(cmd, check=True)
    print(f"[KINETIC 8-BIT ENGINE] ✅ RENDER COMPLETE -> {OUTPUT_VIDEO}")

if __name__ == "__main__":
    render_ultra_reactive_8bit_video()
