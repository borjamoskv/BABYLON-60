# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | UNIFIED SOVEREIGN ENGINE | STATE: C5-REAL
# ============================================================================
"""
Motor Principal AUTODIDACT-Ω.
Orquesta el ciclo completo de investigación epistémica autónoma:
Adquisición -> Formalización Harrop -> Falsación Popperiana -> Compilación de Cristales.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Set

from babylon60.autodidact.crystal_compiler import CrystalCompiler
from babylon60.autodidact.epistemology import derive, hash_statement, verify
from babylon60.autodidact.falsifier import PopperianFalsifier
from babylon60.autodidact.fetchers import ArxivFetcher, LocalCorpusFetcher
from babylon60.autodidact.types import (
    EpistemicCrystal,
    FalsificationVerdict,
    Justification,
    JustifiedStatement,
    Modality,
    Obligation,
    RawEvidence,
    Statement,
    StatementStatus,
)

logger = logging.getLogger("babylon60.autodidact.engine")


class AutodidactOmegaEngine:
    """
    Motor Unificado AUTODIDACT-Ω (v2.0).
    Implementa el pipeline causal de epistemología de sistemas complejos:
    1. Aserción de hipótesis tipadas (Epistémicas vs Deónticas).
    2. Descarga de obligaciones de prueba.
    3. Falsación Popperiana contra silicio y canarios.
    4. Propagación en cascada de contradicciones sobre el DAG de dependencias (B4).
    5. Deducción formal conservativa.
    6. Compilación y sellado Merkle de Cristales Epistémicos.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.falsifier = PopperianFalsifier()
        self.compiler = CrystalCompiler()
        self.statements: List[JustifiedStatement] = []
        self.statement_registry: Dict[str, JustifiedStatement] = {}
        self.dependencies_dag: Dict[str, Set[str]] = {}  # premise_hash -> set(dependent_goal_hashes)
        self.cortex_kernel = None
        self.arxiv_fetcher = ArxivFetcher()
        self.local_fetcher = LocalCorpusFetcher()
        self._init_cortex_bridge(db_path)

    def _init_cortex_bridge(self, db_path: Optional[str]) -> None:
        """Intenta inicializar el puente PyO3 nativo con strike_rs si está disponible."""
        if db_path is None:
            return
        try:
            import strike_rs

            if hasattr(strike_rs, "CortexKernel"):
                self.cortex_kernel = strike_rs.CortexKernel(db_path)
                logger.info(f"Puente nativo strike_rs::CortexKernel activo sobre {db_path}")
        except (ImportError, Exception) as ex:
            logger.debug(f"Puente nativo strike_rs inactivo ({ex}). Operando en fallback determinista puro.")

    def assert_hypothesis(
        self,
        content: str,
        modality: Modality = Modality.EPISTEMIC,
        obligations: Optional[List[Obligation]] = None,
        justification_kind: str = "Observation",
        justification_params: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> JustifiedStatement:
        """
        Crea e instala una hipótesis en el conjunto de conocimiento activo.
        """
        if obligations is None:
            obligations = [Obligation.PROVENANCE, Obligation.REPRODUCIBILITY]

        if justification_params is None:
            justification_params = {}

        stmt = Statement(content=content, modality=modality, obligations=obligations)
        just = Justification(kind=justification_kind, parameters=justification_params, confidence=confidence)

        js = JustifiedStatement(statement=stmt, justification=just)
        js.statement_hash = hash_statement(stmt)
        js.status = StatementStatus.CANDIDATE

        # Si el statement ya estuviese falsado en el oráculo, verify fallará si tiene Obligation.CONTRADICTION
        is_valid = verify(js, nogoods=self.falsifier.nogoods)
        if self.cortex_kernel and is_valid:
            try:
                obs_list = [o.value for o in stmt.obligations]
                if not self.cortex_kernel.verify_statement_content(stmt.content, stmt.modality.value, obs_list):
                    is_valid = False
            except Exception as ex:
                logger.debug(f"Verificación local Harrop activa: {ex}")

        if is_valid:
            js.status = StatementStatus.STABILIZED
        else:
            js.status = StatementStatus.FALSIFIED

        self.statements.append(js)
        self.statement_registry[js.statement_hash] = js

        # Si el kernel nativo está activo, propagar a SQLite WAL
        if self.cortex_kernel and is_valid and modality == Modality.EPISTEMIC:
            try:
                self.cortex_kernel.assert_knowledge(content, justification_kind, "autodidact_omega")
            except Exception as ex:
                logger.warning(f"Error propagando a CortexKernel: {ex}")

        return js

    def falsify_hypothesis(
        self,
        statement: Statement,
        test_fn: Callable[[], Any],
        expected_output: Optional[Any] = None,
    ) -> FalsificationVerdict:
        """
        Somete una hipótesis a una prueba empírica en silicio.
        Si la hipótesis se refuta, propaga la contradicción (B4) a todos sus dependientes.
        """
        s_hash = hash_statement(statement)
        verdict = self.falsifier.falsify_assertion(statement, test_fn, expected_output)

        if verdict.falsified:
            if s_hash in self.statement_registry:
                self.statement_registry[s_hash].status = StatementStatus.FALSIFIED
            # B4: FALSIFICATION => DEPENDENCY REVIEW (propagar en cascada)
            self.propagate_contradiction(s_hash)

            if self.cortex_kernel:
                try:
                    self.cortex_kernel.contradict_knowledge(statement.content, "autodidact_omega")
                except Exception as ex:
                    logger.warning(f"Error registrando contradicción en CortexKernel: {ex}")

        return verdict

    def propagate_contradiction(self, falsified_hash: str) -> List[str]:
        """
        Invariante B4: Falsify(c) => Review(Dependents(c)).
        Paseo en anchura sobre el DAG de dependencias para marcar a todos los descendientes
        que dependían directa o indirectamente de la premisa refutada como DISCREDITED.
        """
        discredited: List[str] = []
        queue = [falsified_hash]
        visited = {falsified_hash}

        while queue:
            curr = queue.pop(0)
            dependents = self.dependencies_dag.get(curr, set())
            for dep_hash in dependents:
                if dep_hash not in visited:
                    visited.add(dep_hash)
                    self.falsifier.nogoods.add(dep_hash)
                    discredited.append(dep_hash)
                    if dep_hash in self.statement_registry:
                        self.statement_registry[dep_hash].status = StatementStatus.DISCREDITED
                    queue.append(dep_hash)

        return discredited

    def derive_theorem(
        self,
        premises: List[JustifiedStatement],
        goal_content: str,
        goal_modality: Modality = Modality.EPISTEMIC,
        goal_obligations: Optional[List[Obligation]] = None,
    ) -> JustifiedStatement:
        """
        Deriva formalmente un nuevo teorema o directiva a partir de premisas verificadas,
        haciendo cumplir estrictamente la Guillotina de Hume y registrando las dependencias en el DAG.
        """
        if goal_obligations is None:
            goal_obligations = [Obligation.PROVENANCE, Obligation.REPRODUCIBILITY, Obligation.CONFIDENCE]

        goal = Statement(content=goal_content, modality=goal_modality, obligations=goal_obligations)
        derived_js = derive(premises, goal, nogoods=self.falsifier.nogoods)
        derived_hash = derived_js.statement_hash or hash_statement(goal)
        derived_js.statement_hash = derived_hash
        derived_js.status = StatementStatus.CANONICAL

        # Registrar dependencias causales
        premise_hashes = [p.statement_hash or hash_statement(p.statement) for p in premises]
        derived_js.dependencies = premise_hashes

        for ph in premise_hashes:
            if ph not in self.dependencies_dag:
                self.dependencies_dag[ph] = set()
            self.dependencies_dag[ph].add(derived_hash)

        self.statements.append(derived_js)
        self.statement_registry[derived_hash] = derived_js
        return derived_js

    def fetch_literature(self, topic: str, max_results: int = 5, query_arxiv: bool = True) -> List[RawEvidence]:
        """
        Adquiere literatura científica primaria viva desde arXiv y el repositorio local.
        """
        evidence: List[RawEvidence] = []
        if query_arxiv:
            arxiv_ev = self.arxiv_fetcher.fetch_papers(topic, max_results=max_results)
            evidence.extend(arxiv_ev)

        local_ev = self.local_fetcher.scan_corpus()
        evidence.extend(local_ev)
        return evidence

    def compile_crystal(self, topic: str, thesis: str) -> EpistemicCrystal:
        """
        Compila todos los statements activos y veredictos en un Cristal Epistémico formal.
        """
        return self.compiler.compile(
            topic=topic,
            thesis=thesis,
            statements=self.statements,
            falsifications=self.falsifier.history,
            nogoods=self.falsifier.nogoods,
        )

    def status(self) -> Dict[str, Any]:
        """Retorna telemetría y estado actual del motor."""
        verified_count = sum(1 for s in self.statements if verify(s, nogoods=self.falsifier.nogoods))
        discredited_count = sum(1 for s in self.statements if s.status == StatementStatus.DISCREDITED)
        has_native_hume = False
        has_native_hasher = False
        try:
            import strike_rs

            has_native_hume = hasattr(strike_rs, "py_enforce_hume_guillotine")
            has_native_hasher = hasattr(strike_rs, "py_hash_statement")
        except ImportError:
            pass

        return {
            "active_statements": len(self.statements),
            "verified_statements": verified_count,
            "discredited_statements": discredited_count,
            "falsified_nogoods": len(self.falsifier.nogoods),
            "falsification_tests_run": len(self.falsifier.history),
            "dependency_edges": sum(len(deps) for deps in self.dependencies_dag.values()),
            "native_cortex_bridge": self.cortex_kernel is not None,
            "native_hume_guillotine": has_native_hume,
            "native_statement_hasher": has_native_hasher,
        }
