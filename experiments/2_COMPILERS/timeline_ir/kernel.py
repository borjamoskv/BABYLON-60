# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# timeline_ir/kernel.py
# El Simulation Kernel: Resuelve State(t)

from typing import List, Dict
from .state_graph import UniverseSnapshot, WorldState, CameraState, CharacterState
import bisect


class Event:
    def __init__(self, time_sec: float, track: str, action: str, params: Dict[str, str]):
        self.time_sec = time_sec
        self.track = track  # 'camera', 'character:ava', 'weather', 'lights'
        self.action = action
        self.params = params

    def __lt__(self, other):
        return self.time_sec < other.time_sec


class SimulationKernel:
    """Máquina de Estados evaluable en tiempo continuo."""

    def __init__(self, initial_snapshot: UniverseSnapshot):
        self.initial_snapshot = initial_snapshot
        self.events: List[Event] = []

    def push_event(self, event: Event):
        bisect.insort(self.events, event)

    def evaluate_state(self, t: float) -> UniverseSnapshot:
        """Computa el estado del universo en el instante t aplicando mutaciones deterministas."""

        # Estado mutacional temporal
        world = WorldState(
            environment=self.initial_snapshot.world.environment,
            weather=self.initial_snapshot.world.weather,
            time=self.initial_snapshot.world.time,
        )
        camera = CameraState(
            name=self.initial_snapshot.camera.name,
            lens=self.initial_snapshot.camera.lens,
            track=self.initial_snapshot.camera.track,
        )
        characters = {
            k: CharacterState(uuid=v.uuid, clothes=v.clothes, emotion=v.emotion)
            for k, v in self.initial_snapshot.characters.items()
        }
        active_fx = list(self.initial_snapshot.active_fx)
        lighting = self.initial_snapshot.lighting_intensity
        music = self.initial_snapshot.music

        # Aplicamos todos los eventos que ocurrieron antes o en el instante t
        for ev in self.events:
            if ev.time_sec > t:
                break

            # Mutaciones BFT
            if ev.track == "weather":
                world = WorldState(world.environment, ev.action, world.time)
            elif ev.track == "camera":
                if ev.action == "PUSH_IN":
                    camera = CameraState(camera.name, camera.lens, "push_in")
                elif ev.action == "SET_TRACK":
                    camera = CameraState(camera.name, camera.lens, ev.params.get("track", camera.track))
            elif ev.track.startswith("character:"):
                char_id = ev.track.split(":")[1]
                if char_id in characters:
                    if ev.action == "ENTER":
                        pass  # Estado lógico de escena, manejado externamente
                    elif ev.action == "CHANGE_EMOTION":
                        characters[char_id] = CharacterState(
                            uuid=char_id,
                            clothes=characters[char_id].clothes,
                            emotion=ev.params.get("emotion", "neutral"),
                        )
            elif ev.track == "fx":
                if ev.action not in active_fx:
                    active_fx.append(ev.action)
            elif ev.track == "lights":
                if ev.action == "FADE":
                    lighting = float(ev.params.get("intensity", lighting))

        return UniverseSnapshot(
            time_sec=t,
            world=world,
            camera=camera,
            music=music,
            characters=characters,
            lighting_intensity=lighting,
            active_fx=active_fx,
        )
