# C5-REAL EXERGY CERTIFIED
from typing import Any

#!/usr/bin/env python3
"""
C5-REAL ULTRATHINK: Physical Thermodynamic Fractal Wallpaper Synthesizer.
(Ω31 Invariant)
Reads system hardware entropy (CPU / RAM load distribution) to calculate Shannon Entropy,
and synthesizes an exclusive 4K fractal/heatmap mapping the exact physical state,
then applies it to the desktop.
"""

import os
import subprocess
import sys
import psutil
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def calculate_hardware_entropy() -> tuple[float, np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Calculates thermodynamic system entropy S = -sum(p * ln(p)) based on CPU per-core loads."""
    cpu_pcts = psutil.cpu_percent(interval=0.5, percpu=True)
    mem = psutil.virtual_memory()

    # Normalize CPU loads as probabilities
    loads = np.array(cpu_pcts) + 1e-3  # Avoid 0
    p_cpu = loads / np.sum(loads)
    s_cpu = -np.sum(p_cpu * np.log(p_cpu))

    mem_frac = mem.percent / 100.0

    # Return entropy score and raw arrays
    return s_cpu, p_cpu, np.array([mem_frac, mem.free / mem.total, mem.active / mem.total])


def generate_thermodynamic_wallpaper(output_path: str) -> None:
    print("[ULTRATHINK] Sampling physical hardware entropy...")
    s_cpu, p_cpu, mem_metrics = calculate_hardware_entropy()

    print(f"[ULTRATHINK] Measured Shannon Entropy (S) = {s_cpu:.4f}")

    # Create a 4K resolution canvas (3840 x 2160)
    width, height = 3840, 2160

    # Fractal parameters influenced by hardware state
    # More CPU load = higher chaos / iteration count
    max_iter = int(50 + 200 * (np.mean(p_cpu) / np.max(p_cpu)))

    # Memory footprint shifts the complex plane view
    x_offset = -0.5 + 0.1 * mem_metrics[0]
    y_offset = 0.0 + 0.1 * mem_metrics[1]
    zoom = 1.0 + mem_metrics[2]

    x = np.linspace(x_offset - 1.5 / zoom, x_offset + 1.5 / zoom, width)
    y = np.linspace(y_offset - 1.0 / zoom, y_offset + 1.0 / zoom, height)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.zeros_like(C)

    fractal = np.zeros(C.shape, dtype=int)

    print("[ULTRATHINK] Synthesizing physical entropy tensor...")
    for i in range(max_iter):
        mask = np.abs(Z) < 2
        Z[mask] = Z[mask] ** 2 + C[mask]
        fractal[mask] += 1

    # Map fractal iterations to thermodynamic colors (YInMn Blue to Decay Red)
    fractal_normalized = fractal / max_iter

    fig, ax = plt.subplots(figsize=(16, 9), dpi=240)
    ax.axis("off")
    fig.patch.set_facecolor("#0A0A0A")

    cmap = plt.cm.magma if s_cpu > 1.5 else plt.cm.YlGnBu_r

    ax.imshow(fractal_normalized, cmap=cmap, aspect="auto")

    # Overlay the measured entropy metric in Industrial Noir Aesthetic
    ax.text(
        0.02,
        0.04,
        f"C5-REAL ULTRATHINK\nHardware Entropy: S={s_cpu:.4f}\nMemory Load: {mem_metrics[0] * 100:.1f}%",
        color="#FFFFFF",
        fontsize=10,
        alpha=0.7,
        transform=ax.transAxes,
        fontfamily="monospace",
    )

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, format="png", facecolor="#0A0A0A", edgecolor="none")
    plt.close()

    print(f"[ULTRATHINK] Synthesis complete. Tensor mapped to: {output_path}")


def set_mac_wallpaper(image_path: str) -> None:
    print("[ULTRATHINK] Assumming control of OS WindowServer via AppleScript...")
    script = f'''
    tell application "System Events"
        set theDesktops to a reference to every desktop
        repeat with aDesktop in theDesktops
            set picture of aDesktop to "{image_path}"
        end repeat
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True)
    print("[ULTRATHINK] Wallpaper physically injected.")


if __name__ == "__main__":
    out_img = os.path.abspath(os.path.expanduser("/tmp/c5_thermo_wallpaper_ultrathink.png"))
    generate_thermodynamic_wallpaper(out_img)
    set_mac_wallpaper(out_img)
    sys.exit(0)
