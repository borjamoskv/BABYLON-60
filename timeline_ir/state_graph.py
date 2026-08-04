# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# timeline_ir/ast.py
# Definición Estricta de la Ontología del Estado (Isomorfismo 1-WL)

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CharacterState:
    uuid: str
    clothes: str = "default"
    emotion: str = "neutral"


@dataclass(frozen=True)
class CameraState:
    name: str
    lens: str = "50mm"
    track: str = "static"


@dataclass(frozen=True)
class WorldState:
    environment: str = "void"
    weather: str = "clear"
    time: str = "day"


@dataclass(frozen=True)
class MusicState:
    track: str
    bpm: int = 120


@dataclass(frozen=True)
class UniverseSnapshot:
    """Snapshot inmutable del Universo en el instante T."""

    time_sec: float
    world: WorldState
    camera: CameraState
    music: Optional[MusicState]
    characters: Dict[str, CharacterState]
    lighting_intensity: float = 100.0
    active_fx: List[str] = field(default_factory=list)
