# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | POPPERIAN SILICON FALSIFIER | STATE: C5-REAL
# ============================================================================
"""
Motor de Falsación Popperiana en Silicio.
Somete afirmaciones, hipótesis y fragmentos de código a pruebas empíricas falsables,
propagando contradicciones (nogoods) hacia el sistema de mantenimiento de verdad (ATMS).
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Callable, Dict, List, Optional, Set

from babylon60.autodidact.epistemology import hash_statement
from babylon60.autodidact.types import (
    FalsificationVerdict,
    Statement,
)
from babylon60.verifiable_inference import generate_proof, verify_payload


class PopperianFalsifier:
    """
    Oráculo de Falsación Popperiana.
    Aplica el criterio de demarcación: si una afirmación no puede ser sometida
    a una prueba determinista en silicio, se etiqueta como UNTESTABLE.
    Si la prueba física o computacional falla, se emite un veredicto de FALSIFIED
    y se registra el StatementHash en el conjunto activo de nogoods.
    """

    def __init__(self) -> None:
        self.nogoods: Set[str] = set()
        self.history: List[FalsificationVerdict] = []

    def falsify_assertion(
        self,
        statement: Statement,
        test_fn: Callable[[], bool | Any],
        expected_output: Optional[Any] = None,
    ) -> FalsificationVerdict:
        """
        Ejecuta un test empírico en silicio para falsar una afirmación.
        Si la función arroja una excepción o el resultado discrepa de expected_output,
        la hipótesis queda formalmente FALSADA.
        """
        start_ns = time.perf_counter_ns()
        s_hash = hash_statement(statement)
        falsified = False
        verdict = "SUPPORTED"
        telemetry: Dict[str, Any] = {}

        try:
            result = test_fn()
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            telemetry["elapsed_ms"] = elapsed_ms
            telemetry["raw_result"] = str(result)

            if expected_output is not None:
                if result != expected_output:
                    falsified = True
                    verdict = "FALSIFIED"
                    telemetry["discrepancy"] = f"Expected {expected_output}, got {result}"
            else:
                # Si expected_output es None, el test_fn retorna booleano de éxito
                if not bool(result):
                    falsified = True
                    verdict = "FALSIFIED"
                    telemetry["discrepancy"] = "Test function returned False"

        except Exception as ex:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            falsified = True
            verdict = "FALSIFIED"
            telemetry["elapsed_ms"] = elapsed_ms
            telemetry["exception"] = f"{type(ex).__name__}: {str(ex)}"

        if falsified:
            self.nogoods.add(s_hash)

        evidence_digest = hashlib.sha256(
            f"{s_hash}:{verdict}:{telemetry.get('elapsed_ms', 0)}".encode("utf-8")
        ).hexdigest()

        verdict_obj = FalsificationVerdict(
            claim=statement.content,
            falsified=falsified,
            verdict=verdict,
            contradiction_node=s_hash if falsified else None,
            telemetry=telemetry,
            evidence_digest=evidence_digest,
        )
        self.history.append(verdict_obj)
        return verdict_obj

    def verify_computational_proof(
        self,
        statement: Statement,
        payload: bytes,
        nonce: int,
        expected_proof_hex: Optional[bytes] = None,
    ) -> FalsificationVerdict:
        """
        Verifica una prueba de inferencia criptográfica determinista
        utilizando el subsistema FFI de verifiable_inference.
        """
        s_hash = hash_statement(statement)
        if expected_proof_hex is None:
            expected_proof_hex = generate_proof(payload, nonce)

        is_valid = verify_payload(payload, nonce, expected_proof_hex)
        falsified = not is_valid
        verdict = "SUPPORTED" if is_valid else "FALSIFIED"

        if falsified:
            self.nogoods.add(s_hash)

        verdict_obj = FalsificationVerdict(
            claim=statement.content,
            falsified=falsified,
            verdict=verdict,
            contradiction_node=s_hash if falsified else None,
            telemetry={
                "payload_bytes": len(payload),
                "nonce": nonce,
                "proof_hex": expected_proof_hex.decode("utf-8", errors="ignore"),
            },
            evidence_digest=hashlib.sha256(expected_proof_hex).hexdigest(),
        )
        self.history.append(verdict_obj)
        return verdict_obj

    def register_manual_nogood(self, statement: Statement) -> str:
        """Registra manualmente un statement como contradictorio/nogood."""
        s_hash = hash_statement(statement)
        self.nogoods.add(s_hash)
        return s_hash

    def is_falsified(self, statement: Statement) -> bool:
        """Comprueba si un statement se encuentra actualmente falsado."""
        s_hash = hash_statement(statement)
        return s_hash in self.nogoods
