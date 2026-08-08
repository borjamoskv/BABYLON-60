# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import subprocess
import time
import psutil

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "gon_fiction_master.wav")
OUTPUT_VIDEO = os.path.join(PROJECT_DIR, "out_gon_fiction_8bit.mp4")

class CriticalLimitChronometer:
    """
    Monitor de disipación termodinámica (Límite Crítico: η ≈ s).
    Actúa como un Cron en Ring-0, evaluando la carga de entropía y
    aplicando intervenciones ultradianas (SIGSTOP/SIGCONT) para evitar
    el colapso por agotamiento.
    """
    def __init__(self, target_pid: int, threshold_percent: float = 85.0,
                 exhaustion_duration: int = 8, recovery_duration: int = 5):
        self.process = psutil.Process(target_pid)
        self.threshold = threshold_percent
        self.exhaustion_duration = exhaustion_duration
        self.recovery_duration = recovery_duration
        self.consecutive_high_load = 0
        self.is_paused = False

    def monitor(self):
        print(f"[CHRONOMETER] Invariant Observer attached to PID {self.process.pid}. Calibrating η=s boundary...")
        # Warmup
        psutil.cpu_percent(interval=1.0)

        while self.process.is_running() and self.process.status() != psutil.STATUS_ZOMBIE:
            try:
                eta_load = psutil.cpu_percent(interval=1.0)

                if eta_load >= self.threshold:
                    self.consecutive_high_load += 1
                else:
                    self.consecutive_high_load = 0

                print(f"[CHRONOMETER] η_load = {eta_load}% | T_exhaust = {self.consecutive_high_load}/{self.exhaustion_duration} s")

                # Early Warning Signal (EWS): Critical Slowing Down detected
                if self.consecutive_high_load >= self.exhaustion_duration and not self.is_paused:
                    print(f"\n[CHRONOMETER] ⚠️ CRITICAL LIMIT REACHED (η ≈ s). System exhaust imminent.")
                    print(f"[CHRONOMETER] 🛑 Enforcing Epistemic Halt (Ultradian Pause) for {self.recovery_duration} seconds...")

                    self.process.suspend() # Equivalent to SIGSTOP
                    self.is_paused = True

                    time.sleep(self.recovery_duration)

                    print(f"[CHRONOMETER] ♻️ Dissipation capacity recovered. Resuming transition to Acto (SIGCONT)...\n")
                    self.process.resume() # Equivalent to SIGCONT
                    self.is_paused = False
                    self.consecutive_high_load = 0 # Reset counters

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

def render_ultra_reactive_8bit_video():
    print(f"[KINETIC 8-BIT ENGINE] Building hyper-kinetic audio visualization with real-time VU meters & multi-band spectrum...")

    # HIGHLY AUDIO-REACTIVE FFmpeg PIPELINE:
    cmd = [
        "ffmpeg", "-y",
        "-i", AUDIO_FILE,
        "-filter_complex", (
            # CHANANTE STYLE BACKGROUND
            # 1. Base: Test bars that spin through all colors very fast (super tacky)
            "smptebars=s=1080x1920:r=30,hue=h='t*180'[bg]; "

            # Boost audio for visualizers
            "[0:a]volume=3.0[vis_audio]; "

            # 2. A chunky, bright waveform with primary colors
            "[vis_audio]showwaves=s=1080x800:mode=cline:colors=magenta|yellow|cyan:rate=30[waves]; "

            # 3. A cheesy spectrum (rainbow colors, like an old Winamp plugin)
            "[vis_audio]showspectrum=s=1080x500:mode=combined:color=rainbow:scale=cbrt:slide=scroll[spec]; "

            # Combine elements
            "[bg][spec]overlay=0:1200[v1]; "
            "[v1][waves]overlay=0:560[v2]; "

            # 4. Remove drawtext (not supported in this ffmpeg build), just pass v2 to v3
            "[v2]copy[v3]; "

            # 5. Cheap public access TV VHS look (oversaturated, noisy, chromatic aberration)
            "[v3]noise=alls=15:allf=t+u[v4]; "            # Heavy VHS grain
            "[v4]rgbashift=rh=8:bv=-8:gh=4[v5]; "        # Color bleeding
            "[v5]eq=contrast=1.4:saturation=3.0[v6]; "    # Burned retinas (oversaturated)

            # 6. MS Paint / Cheap TV pixelation (half-res, not 135p)
            "[v6]scale=540:960:flags=neighbor,scale=1080:1920:flags=neighbor[vout]; "

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

    # Non-blocking launch (Primum Movens setup)
    proc = subprocess.Popen(cmd)

    # Instantiate and run Chronometer (Ring-0 Observer)
    cron = CriticalLimitChronometer(
        target_pid=proc.pid,
        threshold_percent=85.0, # 85% CPU to trigger pause during rendering
        exhaustion_duration=8,  # wait 8s at >85% CPU
        recovery_duration=5     # pause for 5s
    )

    # Wait for completion while monitoring
    cron.monitor()
    proc.wait()

    if proc.returncode == 0:
        print(f"[KINETIC 8-BIT ENGINE] ✅ RENDER COMPLETE -> {OUTPUT_VIDEO}")
    else:
        print(f"[KINETIC 8-BIT ENGINE] ❌ RENDER FAILED with code {proc.returncode}")

if __name__ == "__main__":
    render_ultra_reactive_8bit_video()
