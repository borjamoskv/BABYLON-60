# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-parallel-render
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


def run_render():
    entry_file = "podcast-remotion-script.tsx"
    composition = "UnTioBlancoHipocritaPodcast"
    bundle_dir = "build"
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)

    # Step 1: Bundle the project to avoid redundant compilation
    logging.getLogger(__name__).info("[C5-REAL] Bundling the Remotion project...")
    bundle_cmd = ["./node_modules/.bin/remotion", "bundle", entry_file, bundle_dir]

    # Overwrite if exists
    res = subprocess.run(bundle_cmd)
    if res.returncode != 0:
        logging.getLogger(__name__).info("[CRITICAL] Bundling failed. Aborting.")
        sys.exit(1)

    logging.getLogger(__name__).info("[SUCCESS] Bundling complete. Launching parallel rendering agents...")

    chunks = [
        ("0-8999", "part1.mp4", "chunk_1.log"),
        ("9000-17999", "part2.mp4", "chunk_2.log"),
        ("18000-26999", "part3.mp4", "chunk_3.log"),
        ("27000-35999", "part4.mp4", "chunk_4.log")
    ]

    processes = []

    for frames, filename, logname in chunks:
        out_path = os.path.join(out_dir, filename)
        log_path = os.path.join(out_dir, logname)

        # Open log file for stdout/stderr redirection
        log_file = open(log_path, "w")

        cmd = [
            "./node_modules/.bin/remotion", "render",
            bundle_dir, composition, out_path,
            f"--frames={frames}",
            "--concurrency=3"
        ]
        logging.getLogger(__name__).info(f" -> Agent rendering {frames} (writing to {logname})")
        p = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        processes.append((p, out_path, log_file))

    # Monitor progress from the log files
    start_time = time.time()
    while True:
        alive = False
        finished_count = 0
        for p, _out_path, _log_file in processes:
            if p.poll() is None:
                alive = True
            else:
                finished_count += 1

        # Simple progress update
        elapsed = time.time() - start_time
        logging.getLogger(__name__).info(f"[C5-REAL] Rendering: {finished_count}/4 agents finished. Time elapsed: {elapsed:.1f}s", end="\r")

        if not alive:
            break
        time.sleep(2)

    logging.getLogger(__name__).info("\n[SUCCESS] Parallel rendering complete. Closing logs...")
    for _, _, log_file in processes:
        log_file.close()

    # Check for exit codes
    failed = False
    for p, out_path, _ in processes:
        if p.returncode != 0:
            logging.getLogger(__name__).info(f"[ERROR] Process rendering {out_path} failed with code {p.returncode}")
            failed = True

    if failed:
        logging.getLogger(__name__).info("[CRITICAL] One or more parallel rendering agents failed. Aborting merge.")
        sys.exit(1)

    logging.getLogger(__name__).info("[C5-REAL] Stitching chunks via FFmpeg...")

    # Create list.txt
    list_path = os.path.join(out_dir, "list.txt")
    with open(list_path, "w") as f:
        for _, filename, _ in chunks:
            f.write(f"file '{filename}'\n")

    final_output = os.path.join(out_dir, "video_utbh_destruccion.mp4")

    merge_cmd = [
        "./node_modules/.bin/remotion", "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        final_output
    ]

    merge_res = subprocess.run(merge_cmd)

    if merge_res.returncode == 0:
        logging.getLogger(__name__).info(f"[C5-REAL] Success! Final video: {final_output}")
        import shutil
        dest = "/Users/borjafernandezangulo/Downloads/video_utbh_destruccion.mp4"
        shutil.copy(final_output, dest)
        logging.getLogger(__name__).info(f"[C5-REAL] Copied final video to: {dest}")
        # Clean up parts
        os.remove(list_path)
        for _, filename, logname in chunks:
            os.remove(os.path.join(out_dir, filename))
            os.remove(os.path.join(out_dir, logname))
    else:
        logging.getLogger(__name__).info("[ERROR] FFmpeg merge failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_render()
