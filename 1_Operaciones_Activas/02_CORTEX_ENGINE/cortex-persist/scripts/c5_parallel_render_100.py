# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-parallel-render-100
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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def render_chunk(chunk_idx, start_frame, end_frame, bundle_dir, composition, out_dir):
    filename = f"part_{chunk_idx}.mp4"
    out_path = os.path.join(out_dir, filename)
    log_path = os.path.join(out_dir, f"chunk_{chunk_idx}.log")

    cmd = [
        "./node_modules/.bin/remotion", "render",
        bundle_dir, composition, out_path,
        f"--frames={start_frame}-{end_frame}",
        "--concurrency=1",
        "--muted"
    ]

    with open(log_path, "w") as log_file:
        res = subprocess.run(cmd, stdout=log_file, stderr=log_file)

    if res.returncode != 0:
        return chunk_idx, False, f"Chunk {chunk_idx} failed with exit code {res.returncode}"
    return chunk_idx, True, out_path

def run_render():
    entry_file = "podcast-remotion-script.tsx"
    composition = "UnTioBlancoHipocritaPodcast"
    bundle_dir = "build"
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)

    # Step 1: Bundle
    logging.getLogger(__name__).info("[C5-REAL] Bundling the Remotion project...")
    bundle_cmd = ["./node_modules/.bin/remotion", "bundle", entry_file, bundle_dir]
    res = subprocess.run(bundle_cmd)
    if res.returncode != 0:
        logging.getLogger(__name__).info("[CRITICAL] Bundling failed.")
        sys.exit(1)

    logging.getLogger(__name__).info("[SUCCESS] Bundling complete. Initializing 100 rendering agents...")

    # Define 100 chunks
    total_frames = 36000
    num_chunks = 100
    chunk_size = total_frames // num_chunks

    chunks = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size - 1
        chunks.append((i, start, end))

    # We limit concurrent workers to 8 to avoid RAM/Process exhaustion
    max_workers = 8
    logging.getLogger(__name__).info(f"[C5-REAL] Deploying {num_chunks} chunk tasks with pool size {max_workers} (100 parallel agents simulation)...")

    completed_chunks = {}
    failed_chunks = []

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(render_chunk, idx, start, end, bundle_dir, composition, out_dir): idx
            for idx, start, end in chunks
        }

        for future in as_completed(futures):
            idx, success, result = future.result()
            if success:
                completed_chunks[idx] = result
                # Print progress update
                pct = (len(completed_chunks) / num_chunks) * 100
                elapsed = time.time() - start_time
                logging.getLogger(__name__).info(f"[C5-REAL] Progress: {len(completed_chunks)}/100 agents completed ({pct:.1f}%). Time elapsed: {elapsed:.1f}s", end="\r")
            else:
                logging.getLogger(__name__).info(f"\n[ERROR] {result}")
                failed_chunks.append(idx)

    if failed_chunks:
        logging.getLogger(__name__).info(f"\n[CRITICAL] Rendering failed on {len(failed_chunks)} chunks: {failed_chunks}")
        sys.exit(1)

    logging.getLogger(__name__).info("\n[SUCCESS] All 100 chunks rendered. Merging video parts...")

    # Write list.txt
    list_path = os.path.join(out_dir, "list.txt")
    with open(list_path, "w") as f:
        for i in range(num_chunks):
            f.write(f"file 'part_{i}.mp4'\n")

    video_muted = os.path.join(out_dir, "video_muted.mp4")

    # Concat video parts
    concat_cmd = [
        "./node_modules/.bin/remotion", "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        video_muted
    ]

    logging.getLogger(__name__).info("[C5-REAL] Concatenating muted chunks...")
    concat_res = subprocess.run(concat_cmd)
    if concat_res.returncode != 0:
        logging.getLogger(__name__).info("[ERROR] FFmpeg video concatenation failed.")
        sys.exit(1)

    logging.getLogger(__name__).info("[C5-REAL] Concatenating audio assets and mixing clown loop...")

    # Using absolute paths directly from Downloads as requested
    audio1 = "/Users/borjafernandezangulo/Downloads/El_colapso_ético_y_judicial_de_UTBH.m4a"
    audio2 = "/Users/borjafernandezangulo/Downloads/El_lucrativo_negocio_del_odio_de_UTBH.m4a"
    circus = "public/circus_loop.wav"

    combined_audio = os.path.join(out_dir, "combined_audio.m4a")

    audio_concat_cmd = [
        "./node_modules/.bin/remotion", "ffmpeg", "-y",
        "-i", audio1,
        "-i", audio2,
        "-stream_loop", "-1", "-i", circus,
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[voice];[2:a]volume=0.08[bg];[voice][bg]amix=inputs=2:duration=first[a]",
        "-map", "[a]",
        "-c:a", "aac",
        combined_audio
    ]

    audio_res = subprocess.run(audio_concat_cmd)
    if audio_res.returncode != 0:
        logging.getLogger(__name__).info("[ERROR] FFmpeg audio mixing failed.")
        sys.exit(1)

    logging.getLogger(__name__).info("[C5-REAL] Muxing video and audio into final output...")
    dest = "/Users/borjafernandezangulo/Downloads/video_utbh_destruccion.mp4"

    mux_cmd = [
        "./node_modules/.bin/remotion", "ffmpeg", "-y",
        "-i", video_muted,
        "-i", combined_audio,
        "-c:v", "copy",
        "-c:a", "copy",
        dest
    ]

    mux_res = subprocess.run(mux_cmd)
    if mux_res.returncode == 0:
        logging.getLogger(__name__).info(f"\n[C5-REAL] Success! Render completed using 100 agents with audio mix. Final video: {dest}")
        # Cleanup
        os.remove(list_path)
        os.remove(video_muted)
        os.remove(combined_audio)
        for i in range(num_chunks):
            os.remove(os.path.join(out_dir, f"part_{i}.mp4"))
            os.remove(os.path.join(out_dir, f"chunk_{i}.log"))
    else:
        logging.getLogger(__name__).info("[ERROR] FFmpeg final muxing failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_render()
