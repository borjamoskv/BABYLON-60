"""
C5-REAL Vibe Code IDE Engine
Motor físico determinista que implementa la arquitectura Vibe Code de 10 principios.
"""

import os
import hashlib
import time
from typing import Dict, Tuple

from cortex.swarm.memory_store import AgentMemory
from cortex.swarm.sanitizer import ZeroTrustSanitizer
from cortex.swarm.sandbox import VesicularSandbox


class VibeIDEEngine:
    """Motor C5-REAL para IDE Agéntico con degradación de agencia 4 -> 0 y memoria Dual-Tier."""

    def __init__(self) -> None:
        self.agency_level: int = (
            4  # 4: Full Auto, 3: Confirm, 2: Preview, 1: Lint, 0: Halt
        )
        self.memory = AgentMemory()
        self.sanitizer = ZeroTrustSanitizer()
        self.sandbox = VesicularSandbox(execution_timeout_ms=5000)
        self.tier_0: Dict[str, str] = {}  # Ground Truth (Humano / Compilado)
        self.tier_1: Dict[
            str, Tuple[str, float]
        ] = {}  # Sintético en Cuarentena (Payload, Timestamp)
        self.tier_1_ttl_seconds: float = 3600.0

    def check_kill_switch(self) -> bool:
        """Principio P8: Hardware / Hotkey Kill Switch."""
        if os.getenv("SWARM_KILL_SWITCH") == "1" or os.path.exists("kill_switch.lock"):
            self.agency_level = 0
            self.memory.log(0, "vibe_ide", "kill_switch_active", "HALTED")
            return True
        return False

    def degrade_agency(self, reason: str) -> None:
        """Principio P1: Graceful Degradation of Agency (4 -> 0)."""
        old_level = self.agency_level
        if self.agency_level > 0:
            self.agency_level -= 1
        self.memory.log(
            0,
            "vibe_ide",
            "agency_degraded",
            f"Level={old_level}->{self.agency_level}|Reason={reason}",
        )

    def purge_tier_1(self) -> int:
        """Principio P3: Weaponized Forgetting de TIER_1 expirable."""
        now = time.time()
        expired = [
            k
            for k, (_, ts) in self.tier_1.items()
            if now - ts > self.tier_1_ttl_seconds
        ]
        for k in expired:
            del self.tier_1[k]
        if expired:
            self.memory.log(0, "vibe_ide", "tier_1_purged", f"Count={len(expired)}")
        return len(expired)

    def process_intent(
        self, user_intent: str, file_path: str, proposed_code: str
    ) -> Tuple[bool, str]:
        """Procesa una intención Vibe Code de forma determinista (Principio P1-P10)."""
        if self.check_kill_switch():
            return False, "HALTED_BY_KILL_SWITCH"

        # P9: Zero-Trust Sanitizer
        is_clean, reason = self.sanitizer.validate(user_intent)
        if not is_clean:
            self.degrade_agency(f"PromptInjectionDetected:{reason}")
            return False, f"REJECTED:{reason}"

        # P7: Idempotency Lock (Ahorro de ATP)
        payload_hash = hashlib.sha256(proposed_code.encode("utf-8")).hexdigest()
        existing_code = self.tier_0.get(file_path, "")
        existing_hash = hashlib.sha256(existing_code.encode("utf-8")).hexdigest()

        if payload_hash == existing_hash:
            self.memory.log(
                0, "vibe_ide", "idempotency_lock_hit", f"File={file_path}|ATP_Saved=1"
            )
            return True, "IDEMPOTENT_NO_CHANGE"

        # P3: TIER_1 Quarantine
        self.tier_1[file_path] = (proposed_code, time.time())
        self.memory.log(
            0,
            "vibe_ide",
            "tier_1_quarantine",
            f"File={file_path}|Hash={payload_hash[:8]}",
        )

        # P4: Local Deterministic Compiler Check
        sandbox_res = self.sandbox.execute_safely(proposed_code)
        if sandbox_res["status"] != "PASS":
            self.degrade_agency("SandboxCompilationFail")
            return False, "COMPILATION_FAIL"

        # P3 Promotion: TIER_1 ➔ TIER_0
        self.tier_0[file_path] = proposed_code
        del self.tier_1[file_path]
        self.memory.log(
            0,
            "vibe_ide",
            "tier_0_promoted",
            f"File={file_path}|Hash={payload_hash[:8]}",
        )

        return True, "SUCCESS_C5_REAL"
