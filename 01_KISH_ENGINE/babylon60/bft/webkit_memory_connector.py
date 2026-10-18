# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized WebKit Memory Audit Connector
"""webkit_memory_connector.py - Triaje forense de memoria WebKit/JSC (Vector 21).

Conecta la cola DOMAIN_NATIVE del despachador con los diagnósticos de memoria
C++ de macOS (Gigacage, IsoMalloc, bmalloc, DFG/FTL JIT).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import logging
import shutil
import subprocess
from typing import Dict, List, Optional, Sequence

from babylon60.transducers.bounty_feed_transducer import BountyAdvisory, BountyDomain

logger = logging.getLogger("babylon60.bft.webkit_connector")


@dataclass
class WebKitTriageResult:
    """Resultado del triaje estático y forense de una anomalía en WebKit/JSC."""

    advisory_id: str
    affected_subsystems: List[str]
    vulnerability_class: str
    gigacage_bypass_risk: bool
    recommended_probe: str
    risk_score: float
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serializa el resultado a formato de diccionario."""
        return asdict(self)


class WebKitMemoryConnector:
    """Conector soberano para el análisis de subsistemas de memoria en WebKit."""

    @staticmethod
    def identify_subsystems(text: str) -> List[str]:
        """Identifica los subsistemas de memoria involucrados a partir de la firma causal."""
        subsystems: List[str] = []
        lower = text.lower()

        if "gigacage" in lower or "caged" in lower or "cage" in lower:
            subsystems.append("Gigacage")
        if "isomalloc" in lower or "isoheap" in lower:
            subsystems.append("IsoMalloc")
        if "bmalloc" in lower or "scavenger" in lower:
            subsystems.append("bmalloc")
        if "dfg" in lower or "ftl" in lower or "jit" in lower:
            subsystems.append("JIT_Compiler")
        if "webcore" in lower or "dom" in lower or "wrapper" in lower:
            subsystems.append("DOM_Bindings")

        if not subsystems:
            subsystems.append("Native_Silicon_General")

        return subsystems

    @staticmethod
    def classify_vuln_type(text: str) -> str:
        """Clasifica el modo de fallo de memoria."""
        lower = text.lower()
        if "use-after-free" in lower or "uaf" in lower:
            return "Use-After-Free"
        if "out-of-bounds" in lower or "oob" in lower or "heap overflow" in lower:
            return "Out-Of-Bounds-Access"
        if "type confusion" in lower:
            return "Type-Confusion"
        if "uninitialized" in lower:
            return "Uninitialized-Memory-Read"
        if "sandbox" in lower or "escape" in lower:
            return "Sandbox-Escape"
        return "Memory-Corruption-Generic"

    def triage_advisory(self, advisory: BountyAdvisory) -> WebKitTriageResult:
        """Realiza el triaje formal de una vulnerabilidad en el dominio nativo."""
        corpus = f"{advisory.title} {advisory.payload_summary} {advisory.target_ecosystem}"
        subsystems = self.identify_subsystems(corpus)
        vuln_class = self.classify_vuln_type(corpus)

        # Evaluación de riesgo sobre la jaula de 32 GB (Gigacage)
        gigacage_risk = "Gigacage" in subsystems or (
            vuln_class in ("Out-Of-Bounds-Access", "Type-Confusion") and "JIT_Compiler" in subsystems
        )

        risk_score = 0.5
        if gigacage_risk:
            risk_score += 0.4
        if "IsoMalloc" in subsystems and vuln_class == "Use-After-Free":
            risk_score += 0.3

        notes: List[str] = []
        if gigacage_risk:
            notes.append("Alerta C5: Posible evasión del Fast-Crash Protocol en Gigacage (Vector 21)")
            recommended_probe = "vmmap -summary <pid> | grep -E 'Gigacage|IsoHeap'"
        elif "bmalloc" in subsystems:
            notes.append("Monitoreo de scavenger thread de bmalloc recomendado")
            recommended_probe = "sample <pid> 1 100"
        else:
            recommended_probe = "leaks <pid>"

        return WebKitTriageResult(
            advisory_id=advisory.advisory_id,
            affected_subsystems=subsystems,
            vulnerability_class=vuln_class,
            gigacage_bypass_risk=gigacage_risk,
            recommended_probe=recommended_probe,
            risk_score=min(1.0, risk_score),
            notes=notes,
        )

    def process_advisories(self, advisories: Sequence[BountyAdvisory]) -> List[WebKitTriageResult]:
        """Procesa el lote de advisories del dominio nativo drenados del despachador."""
        results: List[WebKitTriageResult] = []
        for adv in advisories:
            if adv.domain == BountyDomain.DOMAIN_NATIVE:
                results.append(self.triage_advisory(adv))
        return results

    @staticmethod
    def query_jscore_exports() -> Optional[str]:
        """Consulta segura de símbolos exportados en JavaScriptCore de macOS (Zero-Trust)."""
        dyld_bin = shutil.which("dyld_info")
        jscore_path = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/JavaScriptCore"
        if not dyld_bin:
            return None

        try:
            result = subprocess.run(
                [dyld_bin, "-exports", jscore_path],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                # Retorna las primeras 20 líneas como muestreo de símbolos
                return "\n".join(lines[:20])
        except Exception as exc:  # noqa: BLE001
            logger.warning("No fue posible invocar dyld_info: %s", exc)
        return None
