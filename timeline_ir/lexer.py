# timeline_ir/lexer.py
# Parseador Determinista del DSL (.tlir) - Sin Python ast.parse()

import re
from .state_graph import UniverseSnapshot, WorldState, CameraState, MusicState, CharacterState
from .kernel import SimulationKernel, Event

class DslParser:
    """Compilador de Intención -> TimelineIR"""
    
    def __init__(self, source: str):
        self.source = source
        self.lines = [line.strip() for line in source.splitlines() if line.strip() and not line.startswith("#")]
        
    def compile(self) -> SimulationKernel:
        world = WorldState()
        camera = CameraState(name="Main")
        music = None
        characters = {}
        
        events = []
        current_time = 0.0
        
        # Pasada 1: Extracción del Estado Inicial (Invariante 0)
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            if line.startswith("WORLD"):
                parts = line.split(" ")[1:]
                world = WorldState(
                    environment=parts[0] if len(parts) > 0 else "void",
                    time=parts[1] if len(parts) > 1 else "day",
                    weather=parts[2] if len(parts) > 2 else "clear"
                )
            elif line.startswith("MUSIC"):
                # Ej: MUSIC "cathedral.wav" BPM 128
                match = re.search(r'MUSIC\s+"([^"]+)"(?:\s+BPM\s+(\d+))?', line)
                if match:
                    music = MusicState(track=match.group(1), bpm=int(match.group(2) or 120))
            elif line.startswith("CHARACTER"):
                char_id = line.split(" ")[1].lower()
                # Parsear atributos en líneas siguientes anidadas
                clothes = "default"
                emotion = "neutral"
                while i + 1 < len(self.lines) and self.lines[i+1].startswith(("CLOTHES", "EMOTION")):
                    i += 1
                    subline = self.lines[i]
                    if subline.startswith("CLOTHES"):
                        clothes = subline.split(" ")[1]
                    elif subline.startswith("EMOTION"):
                        emotion = subline.split(" ")[1]
                characters[char_id] = CharacterState(uuid=char_id, clothes=clothes, emotion=emotion)
            elif line.startswith("CAMERA"):
                # Si no está en un bloque temporal, define cámara inicial
                if current_time == 0.0 and not any(l.startswith("AT ") for l in self.lines[:i]):
                    parts = line.split(" ")
                    camera = CameraState(name=parts[1] if len(parts) > 1 else "Main")
            
            # Pasada 2: Extracción de Eventos Lineales
            elif line.startswith("AT "):
                time_str = line.split(" ")[1] # format MM:SS
                if ":" in time_str:
                    m, s = time_str.split(":")
                    current_time = int(m) * 60 + int(s)
                else:
                    current_time = float(time_str)
                    
            elif current_time >= 0.0:
                # Estamos dentro de un bloque AT
                parts = line.split(" ")
                subject = parts[0]
                action = parts[1] if len(parts) > 1 else ""
                
                if subject == "CAMERA":
                    events.append(Event(current_time, "camera", action, {}))
                elif subject == "WEATHER":
                    events.append(Event(current_time, "weather", action, {}))
                elif subject == "LIGHTS":
                    if action == "FADE":
                        intensity = parts[2].replace("%", "")
                        events.append(Event(current_time, "lights", "FADE", {"intensity": intensity}))
                elif subject == "EXPLOSION":
                    events.append(Event(current_time, "fx", action, {}))
                elif subject.lower() in characters:
                    char_id = subject.lower()
                    events.append(Event(current_time, f"character:{char_id}", action, {}))

            i += 1
            
        initial_snap = UniverseSnapshot(
            time_sec=0.0,
            world=world,
            camera=camera,
            music=music,
            characters=characters
        )
        
        kernel = SimulationKernel(initial_snap)
        for ev in events:
            kernel.push_event(ev)
            
        return kernel
