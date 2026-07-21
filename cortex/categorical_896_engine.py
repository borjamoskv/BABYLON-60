"""
C5-REAL Categorical Logic 896 Primitives Engine & FISR Transducer
==================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Structural AST & Collision Evaluator
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Any
import hashlib
import sqlite3
import yaml
import os
import json


@dataclass(frozen=True)
class CategoricalPrimitive:
    id: int
    code: str
    domain_id: str
    primitive_type: str
    category: str
    description: str
    formal_proof_invariant: str
    blake3_hash: str


class Categorical896Engine:
    """High-exergy C5-REAL transducer for the 896 Categorical Logic Primitives."""

    def __init__(self, yaml_path: str, db_path: Optional[str] = None):
        self.yaml_path = yaml_path
        self.db_path = db_path or os.path.join(os.path.dirname(yaml_path), "categorical_896_ledger.db")
        self.primitives: Dict[int, CategoricalPrimitive] = {}
        self.code_index: Dict[str, CategoricalPrimitive] = {}
        self.domain_index: Dict[str, List[CategoricalPrimitive]] = {}
        
        self._load_yaml()
        self._sync_sqlite_ledger()

    def _load_yaml(self) -> None:
        if not os.path.exists(self.yaml_path):
            raise FileNotFoundError(f"Missing 896 Primitives matrix at {self.yaml_path}")
            
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for p in data.get("primitives", []):
            p_id = int(p["id"])
            p_code = str(p["code"])
            p_dom = str(p["domain_id"])
            p_type = str(p["type"])
            p_cat = str(p["category"])
            p_desc = str(p["description"])
            p_proof = str(p["formal_proof_invariant"])

            # Cryptographic hash per primitive
            raw_payload = f"{p_id}:{p_code}:{p_dom}:{p_type}:{p_proof}".encode("utf-8")
            h_val = hashlib.sha256(raw_payload).hexdigest()

            prim = CategoricalPrimitive(
                id=p_id,
                code=p_code,
                domain_id=p_dom,
                primitive_type=p_type,
                category=p_cat,
                description=p_desc,
                formal_proof_invariant=p_proof,
                blake3_hash=h_val
            )

            self.primitives[p_id] = prim
            self.code_index[p_code] = prim
            self.domain_index.setdefault(p_dom, []).append(prim)

        if len(self.primitives) != 896:
            raise ValueError(f"Incomplete primitive matrix! Expected 896, got {len(self.primitives)}")

    def _sync_sqlite_ledger(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS primitives_896 (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                domain_id TEXT NOT NULL,
                primitive_type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                formal_proof_invariant TEXT NOT NULL,
                blake3_hash TEXT NOT NULL,
                cortex_taint TEXT NOT NULL
            )
        """)

        taint = "CORTEX-TAINT:borjamoskv:896_engine:2026-07-22T01:24:00Z"
        
        for p in self.primitives.values():
            cursor.execute("""
                INSERT INTO primitives_896 
                (id, code, domain_id, primitive_type, category, description, formal_proof_invariant, blake3_hash, cortex_taint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    code=excluded.code,
                    blake3_hash=excluded.blake3_hash,
                    cortex_taint=excluded.cortex_taint
            """, (p.id, p.code, p.domain_id, p.primitive_type, p.category, p.description, p.formal_proof_invariant, p.blake3_hash, taint))

        conn.commit()
        conn.close()

    def evaluate_morphism_cost(self, primitive_ids: List[int], friction_delta: float = 0.0, friction: float = 0.0) -> float:
        """Computes mu(alpha) structural certificate cost over primitive sequence."""
        eff_friction = friction_delta if friction_delta != 0.0 else friction
        if not primitive_ids:
            return float('inf')
        
        valid_ids = [pid for pid in primitive_ids if pid in self.primitives]
        if len(valid_ids) != len(primitive_ids):
            return float('inf')

        # Base cost model: sum of discrete weight per primitive + friction delta
        base_cost = float(len(valid_ids))
        return base_cost + eff_friction

    def detect_diagrammatic_collisions(self, active_primitive_ids: Set[int]) -> List[Dict[str, Any]]:
        """Detects categorical collisions (e.g. D6 collision primitives combined with D7 antipatterns)."""
        collisions = []
        
        # Check collision domain D6 (561..672) against antipattern domain D7 (673..784)
        d6_active = {pid for pid in active_primitive_ids if 561 <= pid <= 672}
        d7_active = {pid for pid in active_primitive_ids if 673 <= pid <= 784}

        if d6_active and d7_active:
            for c_id in d6_active:
                for a_id in d7_active:
                    c_prim = self.primitives[c_id]
                    a_prim = self.primitives[a_id]
                    collisions.append({
                        "collision_type": "NON_COMMUTATIVE_STRUCTURAL_COLLISION",
                        "collision_primitive": c_prim.code,
                        "antipattern_primitive": a_prim.code,
                        "overhead_delta": 1.414,
                        "risk_level": "CRITICAL_C5_VIOLATION"
                    })

        return collisions

    def get_domain_summary(self) -> Dict[str, int]:
        return {dom: len(prims) for dom, prims in self.domain_index.items()}


if __name__ == "__main__":
    yaml_file = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/primitives/896_categorical_logic_primitives.yml"
    engine = Categorical896Engine(yaml_path=yaml_file)
    print(f"ENGINE IGNITION SUCCESS: Loaded {len(engine.primitives)} primitives across {len(engine.domain_index)} domains.")
    
    # Test evaluation
    cost = engine.evaluate_morphism_cost([1, 113, 225, 337, 449])
    print(f"Morphism Cost mu(alpha): {cost}")

    # Test collision detection
    cols = engine.detect_diagrammatic_collisions({561, 673})
    print(f"Detected Collisions ({len(cols)}): {cols}")
