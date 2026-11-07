#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ KINETIC REEL BUILDER (KISHAR-60) | DOMAIN: creatives | STATE: C5-REAL
# ============================================================================
"""
Kinetic 1080x1920 (9:16) Reel & Stories Builder.
Uses FFmpeg with VideoToolbox hardware acceleration on Apple Silicon.
Generates vertical videos with terminal animations, title screens, and EBU R128 audio.
"""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import List, Optional, Tuple


REEL_WIDTH = 1080
REEL_HEIGHT = 1920
REEL_FPS = 30


@dataclass
class ReelSpecification:
    """Rigid structural specification for a Reel."""
    title: str
    duration_seconds: int = 15
    audio_path: Optional[Path] = None
    target_lufs: float = -14.0


class ReelBuilder:
    """Builds 1080x1920 vertical MP4 clips for Instagram Reels and Stories."""

    def __init__(self):
        self.ffmpeg_bin = shutil.which("ffmpeg")

    def is_available(self) -> bool:
        """Checks if ffmpeg is available in the current environment."""
        return self.ffmpeg_bin is not None

    def render_static_reel_from_image(
        self,
        image_path: Path,
        output_mp4_path: Path,
        duration: int = 10,
        audio_path: Optional[Path] = None,
    ) -> Path:
        """
        Converts a static 1080x1920 or 1080x1350 image into a valid 9:16 Instagram Reel MP4.
        Pads or centers to 1080x1920 if the input is 1080x1350.
        """
        if not self.is_available():
            raise RuntimeError("ffmpeg no está disponible en el PATH del sistema.")

        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

        # Scale and pad to exactly 1080x1920 with black background
        vf_filter = (
            f"scale={REEL_WIDTH}:{REEL_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={REEL_WIDTH}:{REEL_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
        )

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-t", str(duration),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(REEL_FPS),
        ]

        if audio_path and audio_path.exists():
            cmd.extend([
                "-i", str(audio_path),
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
            ])
        else:
            # Generate silent audio track for Instagram compatibility
            cmd.extend([
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-c:a", "aac",
                "-shortest",
            ])

        cmd.append(str(output_mp4_path))

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Fallo en renderizado de Reel FFmpeg: {res.stderr[-500:]}")

        return output_mp4_path
