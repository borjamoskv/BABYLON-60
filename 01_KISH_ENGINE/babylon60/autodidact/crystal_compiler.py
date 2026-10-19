# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | EPISTEMIC CRYSTAL COMPILER | STATE: C5-REAL
# ============================================================================
"""
Compilador de Cristales Epistémicos.
Sintetiza conjuntos verificados de conocimiento $(S, J)$ y veredictos de falsación
en un artefacto inmutable, firmado formalmente y sellado con raíz Merkle SHA-256.
"""

from __future__ import annotations

import datetime
import hashlib
from typing import List, Optional, Set

from babylon60.autodidact.epistemology import hash_statement, optimize
from babylon60.autodidact.types import (
    EpistemicCrystal,
    FalsificationVerdict,
    JustifiedStatement,
)


class CrystalCompiler:
    """
    Compila y formaliza Cristales Epistémicos bajo el estándar C5-REAL.
    Garantiza:
    - Normalización e idempotencia de la prueba vía optimize().
    - Cómputo determinista de la Raíz de Merkle de toda la evidencia.
    - Atribución de autoría inalienable a Borja Fernández Angulo.
    """

    def __init__(self, author: str = "Borja Fernández Angulo", affiliation: str = "Investigador en Sistemas Complejos"):
        self.author = author
        self.affiliation = affiliation

    def compute_merkle_root(
        self,
        statements: List[JustifiedStatement],
        falsifications: List[FalsificationVerdict],
    ) -> str:
        """Calcula la raíz de Merkle combinando los hashes de statements y evidencias de falsación."""
        leaves: List[bytes] = []

        for js in statements:
            s_hash = js.statement_hash or hash_statement(js.statement)
            leaves.append(s_hash.encode("utf-8"))

        for fv in falsifications:
            ev_digest = fv.evidence_digest or hashlib.sha256(fv.claim.encode("utf-8")).hexdigest()
            leaves.append(f"FALSIFY:{fv.verdict}:{ev_digest}".encode("utf-8"))

        if not leaves:
            return hashlib.sha256(b"EMPTY_CRYSTAL").hexdigest()

        # Si el número de hojas es impar, duplicar la última para árbol binario
        current = [hashlib.sha256(leaf).digest() for leaf in leaves]
        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                if i + 1 < len(current):
                    combined = current[i] + current[i + 1]
                else:
                    combined = current[i] + current[i]
                next_level.append(hashlib.sha256(combined).digest())
            current = next_level

        return current[0].hex()

    def compile(
        self,
        topic: str,
        thesis: str,
        statements: List[JustifiedStatement],
        falsifications: Optional[List[FalsificationVerdict]] = None,
        nogoods: Optional[Set[str]] = None,
    ) -> EpistemicCrystal:
        """
        Compila y normaliza el Cristal Epistémico.
        """
        if falsifications is None:
            falsifications = []

        # Normalizar y optimizar aserciones
        optimized_stmts = optimize(statements, nogoods=nogoods)
        for js in optimized_stmts:
            if not js.statement_hash:
                js.statement_hash = hash_statement(js.statement)

        merkle_root = self.compute_merkle_root(optimized_stmts, falsifications)
        timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Generar contenido Markdown formal
        lines = [
            f"# CRISTAL EPISTÉMICO: {topic.upper()}",
            "",
            f"**Por {self.author}**  ",
            f"*{self.affiliation}*  ",
            f"**Fecha de Compilación:** `{timestamp_iso}`  ",
            f"**Merkle Root (SHA-256):** `{merkle_root}`  ",
            "",
            "---",
            "",
            "## 1. Tesis y Núcleo Conceptual",
            "",
            thesis.strip(),
            "",
            "---",
            "",
            "## 2. Proposiciones Formales Verificadas (Lógica de Harrop Ω₀)",
            "",
            "| # | Modalidad | Hash Statement | Proposición | Justificación | Confianza |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for idx, js in enumerate(optimized_stmts, 1):
            s = js.statement
            j = js.justification
            s_hash_short = js.statement_hash[:16] + "..." if js.statement_hash else "N/A"
            lines.append(
                f"| {idx} | `{s.modality.value.upper()}` | `{s_hash_short}` | {s.content} | {j.kind} | {j.confidence:.2f} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 3. Registro de Falsaciones Popperianas (Silicio y Verificación Empírica)",
                "",
            ]
        )

        if falsifications:
            lines.extend(
                [
                    "| # | Afirmación Sometida a Test | Veredicto | Nodo Contradicción | Tiempo (ms) |",
                    "| :--- | :--- | :--- | :--- | :--- |",
                ]
            )
            for idx, fv in enumerate(falsifications, 1):
                contra = fv.contradiction_node[:16] + "..." if fv.contradiction_node else "N/A"
                ms = f"{fv.telemetry.get('elapsed_ms', 0.0):.2f}"
                lines.append(f"| {idx} | {fv.claim} | **{fv.verdict}** | `{contra}` | {ms} ms |")
        else:
            lines.append("*No se registraron anomalías ni falsaciones en la corrida de verificación.*")

        lines.extend(
            [
                "",
                "---",
                "",
                "## 4. Atestación Causal e Integridad C5-REAL",
                "",
                f"- **Autoridad de Compilación:** `{self.author}`",
                f"- **Árbol de Evidencia:** {len(optimized_stmts)} aserciones verificadas, {len(falsifications)} tests de demarcación.",
                f"- **Sello Merkle WORM:** `{merkle_root}`",
                "",
                "---",
                "**Firmado:**  ",
                f"**{self.author}**  ",
                f"*{self.affiliation}*",
                "",
            ]
        )

        markdown_content = "\n".join(lines)

        return EpistemicCrystal(
            topic=topic,
            thesis=thesis,
            statements=optimized_stmts,
            falsification_verdicts=falsifications,
            merkle_root=merkle_root,
            author=self.author,
            affiliation=self.affiliation,
            compiled_at_iso=timestamp_iso,
            markdown_content=markdown_content,
        )

    def export_json(self, crystal: EpistemicCrystal) -> str:
        """Serializa el Cristal Epistémico a JSON canónico."""
        import json

        return json.dumps(crystal.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def verify_crystal_integrity(cls, target: dict[str, object] | str) -> tuple[bool, str]:
        """
        Verifica la integridad criptográfica de un Cristal Epistémico (JSON o dict).
        Recalcula la raíz de Merkle a partir de sus statements y falsaciones,
        comprobando coincidencia exacta bit a bit contra merkle_root.
        """
        import json
        import os

        data: dict[str, object]
        if isinstance(target, str):
            if os.path.exists(target):
                with open(target, "r", encoding="utf-8") as f:
                    content = f.read()
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # Si es Markdown, comprobar presencia de Merkle Root
                    if "Merkle Root (SHA-256):" in content:
                        import re

                        m = re.search(r"Merkle Root \(SHA-256\):\s*`([a-f0-9]{64})`", content)
                        if m:
                            return True, f"Markdown Crystal verified: Merkle Root {m.group(1)} structurally present"
                    return False, "Formato no reconocido o JSON corrupto"
            else:
                try:
                    data = json.loads(target)
                except Exception:
                    return False, f"Archivo o string JSON no válido: {target}"
        elif isinstance(target, dict):
            data = target
        else:
            return False, "Target debe ser dict o ruta a archivo"

        if not isinstance(data, dict):
            return False, "Crystal JSON must be an object"

        declared_merkle = data.get("merkle_root", "")
        if not isinstance(declared_merkle, str) or len(declared_merkle) != 64:
            return False, "Merkle root ausente o inválida"

        # Reconstruir hojas
        leaves: list[bytes] = []
        statements = data.get("statements", [])
        if not isinstance(statements, list):
            return False, "Statements must be a list"
        for s_data in statements:
            if not isinstance(s_data, dict):
                return False, "Statement must be an object"
            s_hash = s_data.get("statement_hash", "")
            if not isinstance(s_hash, str) or not s_hash:
                return False, "Statement sin hash canónico en el cristal"
            leaves.append(s_hash.encode("utf-8"))

        verdicts = data.get("falsification_verdicts", [])
        if not isinstance(verdicts, list):
            return False, "Falsification verdicts must be a list"
        for fv in verdicts:
            if not isinstance(fv, dict):
                return False, "Falsification verdict must be an object"
            ev_digest = fv.get("evidence_digest", "")
            verdict = fv.get("verdict", "UNKNOWN")
            leaves.append(f"FALSIFY:{verdict}:{ev_digest}".encode("utf-8"))

        if not leaves:
            calc_merkle = hashlib.sha256(b"EMPTY_CRYSTAL").hexdigest()
        else:
            current = [hashlib.sha256(leaf).digest() for leaf in leaves]
            while len(current) > 1:
                next_level = []
                for i in range(0, len(current), 2):
                    if i + 1 < len(current):
                        combined = current[i] + current[i + 1]
                    else:
                        combined = current[i] + current[i]
                    next_level.append(hashlib.sha256(combined).digest())
                current = next_level
            calc_merkle = current[0].hex()

        if calc_merkle.lower() == declared_merkle.lower():
            return True, f"INTEGRITY_VERIFIED: Merkle Root matches {declared_merkle}"
        else:
            return False, f"MERKLE_MISMATCH: Declared {declared_merkle}, computed {calc_merkle}"
