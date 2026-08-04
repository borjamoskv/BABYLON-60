#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os

# Agregamos la ruta base para que Python encuentre el módulo timeline_ir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from timeline_ir import Movie
from timeline_ir.renderers.json_backend import RemotionJsonBackend


def test_compiler():
    print("[TimelineIR] Compilando test.tlir...")
    with open("timeline_ir/test.tlir", "r") as f:
        source = f.read()

    movie = Movie(source)

    print("\n--- TEST: SNAPSHOT EN T = 0.0s ---")
    snap0 = movie.evaluate_at(0.0)
    print(f"World: {snap0.world}")
    print(f"Camera Track: {snap0.camera.track}")
    print(f"Lights: {snap0.lighting_intensity}%")
    print(f"Weather: {snap0.world.weather}")
    print(f"FX: {snap0.active_fx}")

    print("\n--- TEST: SNAPSHOT EN T = 50.0s ---")
    # En 50.0, la cámara debe ser PUSH_IN, las luces al 30%, y debe llover.
    snap50 = movie.evaluate_at(50.0)
    print(f"World: {snap50.world}")
    print(f"Camera Track: {snap50.camera.track}")
    print(f"Lights: {snap50.lighting_intensity}%")
    print(f"Weather: {snap50.world.weather}")
    print(f"FX: {snap50.active_fx}")

    print("\n--- TEST: SNAPSHOT EN T = 70.0s ---")
    # En 70.0, ocurre la explosión de chispas en 65s (01:05)
    snap70 = movie.evaluate_at(70.0)
    print(f"FX: {snap70.active_fx}")

    print("\n[TimelineIR] Exportando a Render Backend (Remotion JSON)...")
    renderer = RemotionJsonBackend()
    out_path = renderer.render(movie.kernel, duration=70.0, fps=10, output_path="timeline_ir/render_out.json")
    print(f"[TimelineIR] Cristalización completa en {out_path}.")


if __name__ == "__main__":
    test_compiler()
