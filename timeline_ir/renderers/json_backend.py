# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import json
from abc import ABC, abstractmethod
from ..kernel import SimulationKernel


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, kernel: SimulationKernel, duration: float, fps: int = 60, output_path: str = "output"):
        pass


class RemotionJsonBackend(BaseRenderer):
    """
    Exporta el universo evaluado a 60Hz a un JSON estructurado.
    Un motor externo (como Remotion o un pipeline Three.js) puede consumir esto
    para renderizar el estado del mundo de forma puramente determinista.
    """

    def render(self, kernel: SimulationKernel, duration: float, fps: int = 60, output_path: str = "output.json"):
        frames = []
        total_frames = int(duration * fps)

        for frame_idx in range(total_frames):
            t = frame_idx / fps
            snap = kernel.evaluate_state(t)

            # Serializamos el Snapshot (Isomorfismo)
            frame_data = {
                "t": round(t, 3),
                "frame": frame_idx,
                "world": {
                    "environment": snap.world.environment,
                    "weather": snap.world.weather,
                    "time": snap.world.time,
                },
                "camera": {"track": snap.camera.track, "lens": snap.camera.lens},
                "lighting": snap.lighting_intensity,
                "fx": snap.active_fx,
                "characters": {
                    char_id: {"clothes": char.clothes, "emotion": char.emotion}
                    for char_id, char in snap.characters.items()
                },
            }
            frames.append(frame_data)

        with open(output_path, "w") as f:
            json.dump({"fps": fps, "duration": duration, "frames": frames}, f, indent=2)

        return output_path
