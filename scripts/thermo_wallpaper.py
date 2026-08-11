#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

METRICS_DIR = Path(__file__).resolve().parents[1] / "babylon60" / "metrics"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "wallpapers"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_metrics():
    data = []
    if not METRICS_DIR.exists():
        print("Metrics directory not found, using dummy data")
        return [{"exergy": np.random.random()} for _ in range(10)]
    for file in METRICS_DIR.glob("*.json"):
        try:
            with open(file) as f:
                obj = json.load(f)
                data.append(obj)
        except Exception as e:
            print(f"Failed to load {file}: {e}")
    return data


def compute_entropy(metrics):
    exergies = np.array([m.get("exergy", 0) for m in metrics])
    if exergies.sum() == 0:
        return 0
    probs = exergies / exergies.sum()
    return -np.sum(probs * np.log2(probs + 1e-12))


def generate_wallpaper(entropy):
    # Create a gradient based on entropy value (0-1 normalized)
    norm_entropy = min(max(entropy / 10.0, 0), 1)  # assume max entropy ~10
    cmap = plt.get_cmap("coolwarm")
    colors = cmap(np.linspace(0, 1, 256))
    gradient = np.tile(colors, (1080, 1, 1))
    # Modulate brightness by entropy
    gradient = gradient * (0.5 + 0.5 * norm_entropy)
    plt.figure(figsize=(19.2, 10.8), dpi=100)
    plt.imshow(gradient)
    plt.axis("off")
    out_path = OUTPUT_DIR / f"wallpaper_entropy_{entropy:.2f}.png"
    plt.savefig(out_path, bbox_inches="tight", pad_inches=0)
    plt.close()
    print(f"Wallpaper saved to {out_path}")


def main():
    metrics = load_metrics()
    entropy = compute_entropy(metrics)
    print(f"Computed entropy: {entropy:.4f}")
    generate_wallpaper(entropy)


if __name__ == "__main__":
    main()
