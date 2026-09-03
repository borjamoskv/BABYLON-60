# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
CORTEX / BABYLON-60 — Vector Symbolic Architecture (VSA / HDC) Oncology Engine.

Implementa la formalización ejecutable de la Ontología de 300 Primitivas:
1. Proyección Hiperdimensional (D = 10,000 bits / vectores bipolares {-1, +1}).
2. Operadores VSA: Binding O(1) vía XOR/Hadamard, Bundling por regla de mayoría.
3. Taxonomía BFO (Continuants, Occurrents, Informational Entities).
4. Simulación de Dinámica de Langevin sobre el Paisaje de Waddington U(x).
"""

from __future__ import annotations

import json
import math
import hashlib
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class BFOCategory(str, Enum):
    CONTINUANT = "Continuant"               # Genes, Moléculas, Fármacos
    OCCURRENT = "Occurrent"                 # Vías, Checkpoints, Procesos
    INFORMATIONAL = "InformationalEntity"   # Biomarcadores, Hipótesis


DIMENSION = 10_000  # Espacio hiperdimensional estándar


class HyperVector:
    """Vector bipolar {-1, +1} en R^D optimizado para operaciones VSA."""

    __slots__ = ("data",)

    def __init__(self, data: Optional[List[int]] = None):
        if data is None:
            self.data = [1] * DIMENSION
        else:
            self.data = data

    @classmethod
    def from_seed(cls, seed_str: str) -> HyperVector:
        """Genera un vector hiperdimensional determinista e insesgado mediante Keccak SHAKE-256."""
        raw_bytes = hashlib.shake_256(seed_str.encode("utf-8")).digest((DIMENSION + 7) // 8)
        vec = []
        for b in raw_bytes:
            for i in range(8):
                if len(vec) < DIMENSION:
                    vec.append(1 if (b & (1 << i)) != 0 else -1)
        return cls(vec)

    def bind(self, other: HyperVector) -> HyperVector:
        """Binding O(1): Multiplicación componente a componente (Isomorfo a XOR)."""
        return HyperVector([a * b for a, b in zip(self.data, other.data)])

    def similarity(self, other: HyperVector) -> float:
        """Similitud cosenoidal normalizada en [-1.0, 1.0]."""
        dot = sum(a * b for a, b in zip(self.data, other.data))
        return dot / float(DIMENSION)

    @classmethod
    def bundle(cls, vectors: List[HyperVector]) -> HyperVector:
        """Bundling: Superposición por regla de la mayoría (consenso)."""
        if not vectors:
            return cls()
        accum = [0] * DIMENSION
        for v in vectors:
            for i, val in enumerate(v.data):
                accum[i] += val
        return cls([1 if a >= 0 else -1 for a in accum])


class OncologyOntologyVSA:
    """Motor ontológico VSA para las 300 primitivas oncológicas."""

    def __init__(self, json_path: Optional[Path] = None):
        if json_path is None:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            json_path = repo_root / "data" / "oncology_300.json"
        
        self.json_path = json_path
        self.primitives: Dict[str, Dict[str, Any]] = {}
        self.vectors: Dict[str, HyperVector] = {}
        self._load_primitives()

    def _load_primitives(self) -> None:
        if not self.json_path.exists():
            raise FileNotFoundError(f"No se encuentra el catálogo ontológico en: {self.json_path}")
        
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_list = data.get("primitives", [])
            for item in raw_list:
                p_id = item["id"]
                self.primitives[p_id] = item
                self.vectors[p_id] = HyperVector.from_seed(f"C5_ONC_{p_id}_{item['name']}")

    def classify_bfo(self, p_id: str) -> BFOCategory:
        """Clasifica la primitiva en la taxonomía BFO formal."""
        item = self.primitives[p_id]
        role = item.get("role", "").lower()
        if role in ["oncogen", "supresor", "diana", "farmaco->diana"]:
            return BFOCategory.CONTINUANT
        elif role == "biomarcador" or "hypothesis" in item.get("name", "").lower():
            return BFOCategory.INFORMATIONAL
        else:
            return BFOCategory.OCCURRENT

    def compute_drug_target_affinity(self, drug_name: str, target_id: str) -> float:
        """Calcula la resonancia hiperdimensional entre intervención y diana."""
        if target_id not in self.vectors:
            raise KeyError(f"Diana {target_id} no registrada.")
        v_drug = HyperVector.from_seed(f"C5_DRUG_{drug_name}")
        v_target = self.vectors[target_id]
        bound = v_drug.bind(v_target)
        return bound.similarity(v_target)

    def simulate_waddington_trajectory(
        self,
        oncogene_id: str,
        inhibited: bool = False,
        steps: int = 100,
        dt: float = 0.05
    ) -> List[Tuple[float, float]]:
        """
        Simula la evolución temporal sobre el paisaje de Waddington U(x).
        x(t) representa la trayectoria del estado celular hacia la cuenca diferenciada (x < 0)
        o cuenca maligna tumoral (x > 0).
        """
        if oncogene_id not in self.primitives:
            raise KeyError(f"Primitiva {oncogene_id} no encontrada.")

        f_onc = 0.8 if not inhibited else -0.5
        x = 0.1
        trajectory = []

        for _ in range(steps):
            grad = 4.0 * (x ** 3) - 4.0 * x - f_onc
            x = x - grad * dt
            x = max(-2.0, min(2.0, x))
            u_x = (x ** 4) - 2.0 * (x ** 2) - f_onc * x
            trajectory.append((x, u_x))

        return trajectory
