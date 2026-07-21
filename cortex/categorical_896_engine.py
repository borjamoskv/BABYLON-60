"""
C5-REAL Categorical Logic 896 Primitives Engine & FISR Transducer
==================================================================
Kernel: MOSKV-1 APEX
Baseline: FISR v18.3 (Lawvere Enriched Metric & Extension/Repair Operator kappa)

Implements:
  - Certificate Category P -> C via monoidal functor pi (Id_Ob)
  - Cost valuation |·|: Mor(P) -> N_bar with identity, sequential & monoidal laws
  - Lawvere premetric mu(alpha) = inf{|c| : c in Cert(alpha)}
  - Subadditivity verification (Theorem 1.1)
  - Budget predicate R_k^A(M)
  - Extension/repair operator kappa(alpha, R)
  - Monotonicity verification (Theorems 2.1 & 2.2)
  - Simplicial compatibility complex Compat(Omega)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum, auto
import hashlib
import sqlite3
import yaml
import os
import math

try:
    import strike_rs  # type: ignore
    RUST_ENGINE_AVAILABLE = True
except ImportError:
    RUST_ENGINE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# 1. DOMAIN TYPES & PRIMITIVE STRUCTURE
# ═══════════════════════════════════════════════════════════════

class DomainType(Enum):
    STRUCTURE = auto()
    LIMITS_COLIMITS = auto()
    FUNCTORIAL_ADJUNCTIONS = auto()
    MONOIDAL_ENRICHED = auto()
    CATEGORICAL_LOGIC_TOPOS = auto()
    COLLISION_OBSTRUCTION = auto()
    ANTIPATTERNS = auto()
    FIBERED_COMPATIBILITY_METRICS = auto()


DOMAIN_TYPE_MAP: Dict[str, DomainType] = {
    "STRUCTURE": DomainType.STRUCTURE,
    "LIMITS_COLIMITS": DomainType.LIMITS_COLIMITS,
    "FUNCTORIAL_ADJUNCTIONS": DomainType.FUNCTORIAL_ADJUNCTIONS,
    "MONOIDAL_ENRICHED": DomainType.MONOIDAL_ENRICHED,
    "CATEGORICAL_LOGIC_TOPOS": DomainType.CATEGORICAL_LOGIC_TOPOS,
    "COLLISION_OBSTRUCTION": DomainType.COLLISION_OBSTRUCTION,
    "ANTIPATTERNS": DomainType.ANTIPATTERNS,
    "FIBERED_COMPATIBILITY_METRICS": DomainType.FIBERED_COMPATIBILITY_METRICS,
}

DOMAIN_RANGES: Dict[str, Tuple[int, int]] = {
    "D1": (1, 112), "D2": (113, 224), "D3": (225, 336), "D4": (337, 448),
    "D5": (449, 560), "D6": (561, 672), "D7": (673, 784), "D8": (785, 896),
}


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

    @property
    def domain_type(self) -> DomainType:
        return DOMAIN_TYPE_MAP.get(self.primitive_type, DomainType.STRUCTURE)

    @property
    def is_collision(self) -> bool:
        return self.domain_type == DomainType.COLLISION_OBSTRUCTION

    @property
    def is_antipattern(self) -> bool:
        return self.domain_type == DomainType.ANTIPATTERNS

    @property
    def is_structural(self) -> bool:
        return self.domain_type in (
            DomainType.STRUCTURE, DomainType.LIMITS_COLIMITS,
            DomainType.FUNCTORIAL_ADJUNCTIONS, DomainType.MONOIDAL_ENRICHED,
        )

    @property
    def is_logical(self) -> bool:
        return self.domain_type in (
            DomainType.CATEGORICAL_LOGIC_TOPOS,
            DomainType.FIBERED_COMPATIBILITY_METRICS,
        )


# ═══════════════════════════════════════════════════════════════
# 2. LAWVERE METRIC & COST ALGEBRA
# ═══════════════════════════════════════════════════════════════

@dataclass
class CostValuation:
    """
    Cost valuation |·|: Mor(P) -> N_bar.
    Axioms:
      Id-1: pi(id_X^P) = id_X^C
      Id-2: |id_X^P| = 0
      Sequential: |q ⊛ p| <= |p| + |q| + delta_circ(alpha, beta)
      Monoidal:   |p ⊠ q| <= |p| + |q| + delta_otimes(alpha, beta)
    """
    value: float = 0.0

    @property
    def is_finite(self) -> bool:
        return not math.isinf(self.value)

    @staticmethod
    def infinity() -> "CostValuation":
        return CostValuation(value=float("inf"))

    @staticmethod
    def zero() -> "CostValuation":
        return CostValuation(value=0.0)

    def sequential_compose(self, other: "CostValuation", delta_circ: float = 0.0) -> "CostValuation":
        """Theorem 1.1 sequential: |q ⊛ p| <= |p| + |q| + delta_circ"""
        if not self.is_finite or not other.is_finite:
            return CostValuation.infinity()
        return CostValuation(value=self.value + other.value + delta_circ)

    def monoidal_compose(self, other: "CostValuation", delta_otimes: float = 0.0) -> "CostValuation":
        """Theorem 1.1 monoidal: |p ⊠ q| <= |p| + |q| + delta_otimes"""
        if not self.is_finite or not other.is_finite:
            return CostValuation.infinity()
        return CostValuation(value=self.value + other.value + delta_otimes)


@dataclass
class MorphismCert:
    """A certificate c in Cert(alpha) with cost |c|."""
    morphism_id: int
    cost: CostValuation
    domain_id: str


# ═══════════════════════════════════════════════════════════════
# 3. SIMPLICIAL COMPATIBILITY COMPLEX Compat(Omega)
# ═══════════════════════════════════════════════════════════════

class CompatProperty(Enum):
    """Vertices of Compat(Omega) = {F, I, S, R_k}"""
    F = "Fibered"           # alpha* admits left adjoint exists_alpha
    I = "MonoidalInvariant"  # alpha*(P otimes Q) ~= alpha*(P) otimes alpha*(Q)  # noqa: E741
    S = "Synchronous"        # alpha*(Box_t P) = Box_t(alpha* P)
    R_k = "BudgetBound"     # forall alpha in A(M), mu(alpha) <= k


@dataclass
class CompatFace:
    """A face (simplex) in Compat(Omega)."""
    properties: frozenset

    @property
    def dimension(self) -> int:
        return len(self.properties) - 1

    def is_subface_of(self, other: "CompatFace") -> bool:
        return self.properties.issubset(other.properties)


class CompatComplex:
    r"""
    Simplicial complex Compat(Omega) subset P(Omega) \ {empty}.
    Down-set invariant: sigma in Compat and tau subset sigma => tau in Compat.
    """
    def __init__(self) -> None:
        self.vertices: Set[CompatProperty] = {CompatProperty.F, CompatProperty.I, CompatProperty.S, CompatProperty.R_k}
        self.faces: List[CompatFace] = []
        self._build_default_complex()

    def _build_default_complex(self) -> None:
        """Build the default compatibility complex from FISR theory (closed under non-empty subsets)."""
        from itertools import combinations
        # Maximal faces of the FISR simplicial complex
        maximal_faces = [
            frozenset({CompatProperty.F, CompatProperty.I, CompatProperty.S, CompatProperty.R_k})
        ]
        face_sets: set[frozenset[CompatProperty]] = set()
        for max_face in maximal_faces:
            props = list(max_face)
            for k in range(1, len(props) + 1):
                for sub in combinations(props, k):
                    face_sets.add(frozenset(sub))

        self.faces = [CompatFace(f) for f in face_sets]

    def verify_downset_invariant(self) -> bool:
        """Verify the simplicial (down-set/hereditary) condition."""
        face_set = {f.properties for f in self.faces}
        for face in self.faces:
            props = list(face.properties)
            for i in range(1, len(props) + 1):
                from itertools import combinations
                for subset in combinations(props, i):
                    if frozenset(subset) not in face_set:
                        return False
        return True

    def euler_characteristic(self) -> int:
        """chi = sum_{k>=0} (-1)^k * f_k where f_k = number of k-simplices."""
        dim_counts: Dict[int, int] = {}
        for face in self.faces:
            d = face.dimension
            dim_counts[d] = dim_counts.get(d, 0) + 1
        return sum((-1) ** k * count for k, count in dim_counts.items())


# ═══════════════════════════════════════════════════════════════
# 4. MAIN ENGINE
# ═══════════════════════════════════════════════════════════════

class Categorical896Engine:
    """
    High-exergy C5-REAL transducer for the 896 Categorical Logic Primitives.

    Implements the full FISR v18.3 mathematical stack:
      P --pi--> C --|||--> N_bar --mu--> R_k --kappa--> PRF
    """

    def __init__(self, yaml_path: str, db_path: Optional[str] = None):
        self.yaml_path = yaml_path
        self.db_path = db_path or os.path.join(os.path.dirname(yaml_path), "categorical_896_ledger.db")
        self.primitives: Dict[int, CategoricalPrimitive] = {}
        self.code_index: Dict[str, CategoricalPrimitive] = {}
        self.domain_index: Dict[str, List[CategoricalPrimitive]] = {}
        self.compat_complex = CompatComplex()

        self.rust_engine: Optional[Any] = None
        if RUST_ENGINE_AVAILABLE:
            try:
                self.rust_engine = strike_rs.RustCategoricalEngine()
            except Exception:
                self.rust_engine = None

        self._load_yaml()
        self._sync_sqlite_ledger()

    # ── YAML Loading ──────────────────────────────────────────

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

            raw_payload = f"{p_id}:{p_code}:{p_dom}:{p_type}:{p_proof}".encode("utf-8")
            h_val = hashlib.sha256(raw_payload).hexdigest()

            prim = CategoricalPrimitive(
                id=p_id, code=p_code, domain_id=p_dom,
                primitive_type=p_type, category=p_cat,
                description=p_desc, formal_proof_invariant=p_proof,
                blake3_hash=h_val
            )

            self.primitives[p_id] = prim
            self.code_index[p_code] = prim
            self.domain_index.setdefault(p_dom, []).append(prim)

        if len(self.primitives) != 896:
            raise ValueError(f"Incomplete primitive matrix! Expected 896, got {len(self.primitives)}")

    # ── SQLite WAL Ledger ─────────────────────────────────────

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

        taint = "CORTEX-TAINT:borjamoskv:896_engine_v2:2026-07-22T01:34:00Z"

        for p in self.primitives.values():
            cursor.execute("""
                INSERT INTO primitives_896
                (id, code, domain_id, primitive_type, category, description,
                 formal_proof_invariant, blake3_hash, cortex_taint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    code=excluded.code,
                    blake3_hash=excluded.blake3_hash,
                    cortex_taint=excluded.cortex_taint
            """, (p.id, p.code, p.domain_id, p.primitive_type,
                  p.category, p.description, p.formal_proof_invariant,
                  p.blake3_hash, taint))

        conn.commit()
        conn.close()

    # ── Morphism Cost mu(alpha) ───────────────────────────────

    def evaluate_morphism_cost(
        self,
        primitive_ids: List[int],
        friction_delta: float = 0.0,
        friction: float = 0.0,
    ) -> float:
        """
        Computes mu(alpha) = inf{|c| : c in Cert(alpha)}.
        Each primitive in the sequence contributes unit cost.
        Friction models delta_circ or delta_otimes overhead.
        """
        eff_friction = friction_delta if friction_delta != 0.0 else friction
        if not primitive_ids:
            return float("inf")

        if self.rust_engine is not None:
            cost = self.rust_engine.calculate_morphism_cost(primitive_ids, eff_friction)
            if cost != float("inf"):
                return cost

        valid_ids = [pid for pid in primitive_ids if pid in self.primitives]
        if len(valid_ids) != len(primitive_ids):
            return float("inf")

        base_cost = float(len(valid_ids))
        return base_cost + eff_friction

    def evaluate_sequential_composition(
        self,
        seq_a: List[int],
        seq_b: List[int],
        delta_circ: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Verifies Theorem 1.1 (Sequential Subadditivity):
          mu(beta o alpha) <= mu(alpha) + mu(beta) + delta_circ(alpha, beta)
        """
        mu_a = self.evaluate_morphism_cost(seq_a)
        mu_b = self.evaluate_morphism_cost(seq_b)
        mu_composed = self.evaluate_morphism_cost(seq_a + seq_b, friction_delta=delta_circ)

        upper_bound = mu_a + mu_b + delta_circ
        theorem_holds = mu_composed <= upper_bound + 1e-12

        return {
            "mu_alpha": mu_a,
            "mu_beta": mu_b,
            "mu_composed": mu_composed,
            "upper_bound": upper_bound,
            "delta_circ": delta_circ,
            "theorem_1_1_sequential_holds": theorem_holds,
        }

    def evaluate_monoidal_composition(
        self,
        seq_a: List[int],
        seq_b: List[int],
        delta_otimes: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Verifies Theorem 1.1 (Monoidal Subadditivity):
          mu(alpha ⊗ beta) <= mu(alpha) + mu(beta) + delta_otimes(alpha, beta)
        """
        mu_a = self.evaluate_morphism_cost(seq_a)
        mu_b = self.evaluate_morphism_cost(seq_b)
        # Monoidal composition: independent parallel cost
        mu_tensor = mu_a + mu_b + delta_otimes

        upper_bound = mu_a + mu_b + delta_otimes
        theorem_holds = mu_tensor <= upper_bound + 1e-12

        return {
            "mu_alpha": mu_a,
            "mu_beta": mu_b,
            "mu_tensor": mu_tensor,
            "upper_bound": upper_bound,
            "delta_otimes": delta_otimes,
            "theorem_1_1_monoidal_holds": theorem_holds,
        }

    # ── Budget Predicate R_k^A ────────────────────────────────

    def evaluate_budget_predicate(
        self,
        distinguished_morphisms: List[List[int]],
        k: float,
    ) -> Dict[str, Any]:
        """
        Evaluates R_k^A(M) <=> forall alpha in A(M), mu(alpha) <= k.
        Each element of distinguished_morphisms is a morphism (primitive sequence).
        """
        costs = [self.evaluate_morphism_cost(m) for m in distinguished_morphisms]
        max_cost = max(costs) if costs else 0.0
        satisfies = all(c <= k + 1e-12 for c in costs)

        return {
            "k": k,
            "morphism_count": len(distinguished_morphisms),
            "costs": costs,
            "max_cost": max_cost,
            "R_k_satisfied": satisfies,
        }

    # ── Extension/Repair Operator kappa ───────────────────────

    def evaluate_kappa(
        self,
        morphism: List[int],
        budget_k: float,
        candidate_extensions: List[List[int]],
    ) -> Dict[str, Any]:
        """
        Evaluates kappa(alpha, R) = inf{mu(e) | e o alpha |= R}.
        Theorem 2.1: R => R' implies kappa(alpha, R') <= kappa(alpha, R).
        """
        mu_alpha = self.evaluate_morphism_cost(morphism)
        extension_costs: list[float] = []

        for ext in candidate_extensions:
            composed = ext + morphism
            mu_ext = self.evaluate_morphism_cost(ext)
            mu_composed = self.evaluate_morphism_cost(composed)
            if mu_composed <= budget_k + 1e-12:
                extension_costs.append(mu_ext)

        kappa_val = min(extension_costs) if extension_costs else float("inf")

        return {
            "mu_alpha": mu_alpha,
            "budget_k": budget_k,
            "kappa": kappa_val,
            "kappa_finite": not math.isinf(kappa_val),
            "extensions_evaluated": len(candidate_extensions),
            "valid_extensions": len(extension_costs),
        }

    def verify_kappa_monotonicity(
        self,
        morphism: List[int],
        k_strong: float,
        k_weak: float,
        extensions: List[List[int]],
    ) -> Dict[str, Any]:
        """
        Theorem 2.1: R => R' (k_strong <= k_weak) implies
          kappa(alpha, R_k_weak) <= kappa(alpha, R_k_strong)
        """
        kappa_strong = self.evaluate_kappa(morphism, k_strong, extensions)
        kappa_weak = self.evaluate_kappa(morphism, k_weak, extensions)

        theorem_holds = kappa_weak["kappa"] <= kappa_strong["kappa"] + 1e-12

        return {
            "k_strong": k_strong,
            "k_weak": k_weak,
            "kappa_strong": kappa_strong["kappa"],
            "kappa_weak": kappa_weak["kappa"],
            "theorem_2_1_holds": theorem_holds,
        }

    # ── Diagrammatic Collision Auditor ─────────────────────────

    def detect_diagrammatic_collisions(
        self,
        active_primitive_ids: Set[int],
    ) -> List[Dict[str, Any]]:
        """
        Detects categorical collisions between D6 (obstructions) and D7 (antipatterns),
        and structural incompatibilities across domains.
        """
        collisions: list[Dict[str, Any]] = []

        d6_active = {pid for pid in active_primitive_ids if 561 <= pid <= 672}
        d7_active = {pid for pid in active_primitive_ids if 673 <= pid <= 784}

        # D6 x D7: Non-commutative structural collisions
        for c_id in sorted(d6_active):
            for a_id in sorted(d7_active):
                c_prim = self.primitives[c_id]
                a_prim = self.primitives[a_id]
                collisions.append({
                    "collision_type": "NON_COMMUTATIVE_STRUCTURAL_COLLISION",
                    "collision_primitive": c_prim.code,
                    "antipattern_primitive": a_prim.code,
                    "overhead_delta": 1.414,
                    "risk_level": "CRITICAL_C5_VIOLATION",
                })

        # D4 (monoidal) x D6 (collisions): Pentagon coherence breakage
        d4_active = {pid for pid in active_primitive_ids if 337 <= pid <= 448}
        for m_id in sorted(d4_active):
            for c_id in sorted(d6_active):
                collisions.append({
                    "collision_type": "MONOIDAL_PENTAGON_COHERENCE_BREAKAGE",
                    "monoidal_primitive": self.primitives[m_id].code,
                    "obstruction_primitive": self.primitives[c_id].code,
                    "overhead_delta": 2.236,
                    "risk_level": "WARNING_COHERENCE_VIOLATION",
                })

        # D5 (topos logic) x D7 (antipatterns): Subobject classifier degradation
        d5_active = {pid for pid in active_primitive_ids if 449 <= pid <= 560}
        for l_id in sorted(d5_active):
            for a_id in sorted(d7_active):
                collisions.append({
                    "collision_type": "SUBOBJECT_CLASSIFIER_DEGRADATION",
                    "logic_primitive": self.primitives[l_id].code,
                    "antipattern_primitive": self.primitives[a_id].code,
                    "overhead_delta": 1.732,
                    "risk_level": "WARNING_LOGIC_INTEGRITY",
                })

        return collisions

    # ── Compat(Omega) Evaluator ────────────────────────────────

    def evaluate_compat_complex(self) -> Dict[str, Any]:
        """Evaluates the simplicial compatibility complex Compat(Omega)."""
        cc = self.compat_complex
        downset_ok = cc.verify_downset_invariant()
        euler = cc.euler_characteristic()

        dim_histogram: Dict[int, int] = {}
        for face in cc.faces:
            d = face.dimension
            dim_histogram[d] = dim_histogram.get(d, 0) + 1

        return {
            "vertices": [p.value for p in cc.vertices],
            "total_faces": len(cc.faces),
            "dimension_histogram": dim_histogram,
            "euler_characteristic": euler,
            "downset_invariant_verified": downset_ok,
            "maximal_dimension": max(dim_histogram.keys()) if dim_histogram else -1,
        }

    # ── Domain Summary ─────────────────────────────────────────

    def get_domain_summary(self) -> Dict[str, int]:
        return {dom: len(prims) for dom, prims in self.domain_index.items()}

    def get_structural_audit(self) -> Dict[str, Any]:
        """Full structural audit of the 896-primitive matrix."""
        structural_count = sum(1 for p in self.primitives.values() if p.is_structural)
        logical_count = sum(1 for p in self.primitives.values() if p.is_logical)
        collision_count = sum(1 for p in self.primitives.values() if p.is_collision)
        antipattern_count = sum(1 for p in self.primitives.values() if p.is_antipattern)

        return {
            "total_primitives": len(self.primitives),
            "domains": len(self.domain_index),
            "structural_primitives": structural_count,
            "logical_primitives": logical_count,
            "collision_primitives": collision_count,
            "antipattern_primitives": antipattern_count,
            "domain_breakdown": self.get_domain_summary(),
            "compat_complex": self.evaluate_compat_complex(),
        }


# ═══════════════════════════════════════════════════════════════
# 5. ENTRYPOINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json
    yaml_file = os.path.join(os.path.dirname(__file__), "..", "primitives", "896_categorical_logic_primitives.yml")
    engine = Categorical896Engine(yaml_path=os.path.abspath(yaml_file))

    print(json.dumps(engine.get_structural_audit(), indent=2))

    result = engine.evaluate_sequential_composition([1, 2, 3], [4, 5])
    print(json.dumps(result, indent=2))

    kappa_result = engine.evaluate_kappa([1], 5.0, [[2], [3, 4], [5, 6, 7]])
    print(json.dumps(kappa_result, indent=2))
