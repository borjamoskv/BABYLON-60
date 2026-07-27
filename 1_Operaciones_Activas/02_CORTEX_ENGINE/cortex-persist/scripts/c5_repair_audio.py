# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-repair-audio
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import subprocess
import sys


def repair():
    out_dir = "out"
    audio1 = "/Users/borjafernandezangulo/Downloads/El_colapso_ético_y_judicial_de_UTBH.m4a"
    audio2 = "/Users/borjafernandezangulo/Downloads/El_lucrativo_negocio_del_odio_de_UTBH.m4a"
    circus = "public/circus_loop.wav"

    video_muted = os.path.join(out_dir, "video_muted.mp4")
    combined_audio_wav = os.path.join(out_dir, "combined_audio.wav")
    list_path = os.path.join(out_dir, "list.txt")

    logging.getLogger(__name__).info("[C5-REAL] Mixing voice audios with clown loop into WAV...")

    # We output to a standard WAV container to bypass the M4A/iPod muxer limitation
    audio_concat_cmd = [
        "./node_modules/.bin/remotion", "ffmpeg", "-y",
        "-i", audio1,
        "-i", audio2,
        "-stream_loop", "-1", "-i", circus,
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[voice];[2:a]volume=0.08[bg];[voice][bg]amix=inputs=2:duration=first[a]",
        "-map", "[a]",
        combined_audio_wav
    ]

    res = subprocess.run(audio_concat_cmd)
    if res.returncode != 0:
        logging.getLogger(__name__).info("[ERROR] FFmpeg audio mixing failed.")
        sys.exit(1)

    logging.getLogger(__name__).info("[C5-REAL] Muxing muted video with WAV audio into final MP4...")
    dest = "/Users/borjafernandezangulo/Downloads/video_utbh_destruccion.mp4"

    mux_cmd = [
        "./node_modules/.bin/remotion", "ffmpeg", "-y",
        "-i", video_muted,
        "-i", combined_audio_wav,
        "-c:v", "copy",
        "-c:a", "aac", # Encode to standard AAC in the output container
        dest
    ]

    mux_res = subprocess.run(mux_cmd)
    if mux_res.returncode == 0:
        logging.getLogger(__name__).info(f"\n[C5-REAL] Success! Final video successfully created at: {dest}")
        # Clean up
        try:
            if os.path.exists(list_path):
                os.remove(list_path)
            if os.path.exists(video_muted):
                os.remove(video_muted)
            if os.path.exists(combined_audio_wav):
                os.remove(combined_audio_wav)
            for i in range(100):
                part_path = os.path.join(out_dir, f"part_{i}.mp4")
                log_path = os.path.join(out_dir, f"chunk_{i}.log")
                if os.path.exists(part_path):
                    os.remove(part_path)
                if os.path.exists(log_path):
                    os.remove(log_path)
            logging.getLogger(__name__).info("[C5-REAL] Cleanup complete.")
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).info(f"[WARNING] Cleanup encountered an error: {e}")
    else:
        logging.getLogger(__name__).info("[ERROR] Final muxing failed.")
        sys.exit(1)

if __name__ == "__main__":
    repair()
