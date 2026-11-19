#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ BIOMETRIC GATE WRAPPER (Ring-(-1)) | DOMAIN: gates | STATE: C5-REAL
# ============================================================================
"""
Biometric Gate Integration (c5_biometric_gate).
Enforces Touch ID attestation via Apple Silicon Secure Enclave before mutating external state.
"""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from typing import Optional


class BiometricGate:
    """Enforces Apple Silicon Touch ID biometric verification before publishing."""

    DEFAULT_GATE_PATH = "/Users/borjafernandezangulo/.local/bin/c5_biometric_gate"

    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = binary_path or shutil.which("c5_biometric_gate") or self.DEFAULT_GATE_PATH

    def is_available(self) -> bool:
        """Checks if the biometric gate binary exists and is executable."""
        p = Path(self.binary_path)
        return p.exists() and os.access(p, os.X_OK) if hasattr(os, "X_OK") else p.exists()

    @classmethod
    def compute_causal_hash(cls, payload: str) -> str:
        """Derives deterministic SHA-256 causal hash for the mutation payload."""
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def request_authorization(
        self,
        action: str,
        scope: str,
        payload_to_sign: str,
        agent: str = "SHAMASH-60",
        preview_only: bool = False,
    ) -> bool:
        """
        Invokes c5_biometric_gate to solicit Touch ID attestation.
        Returns True if authorized (Exit 0), False otherwise.
        """
        if not self.is_available():
            raise FileNotFoundError(f"c5_biometric_gate no encontrado en {self.binary_path}")

        causal_hash = self.compute_causal_hash(payload_to_sign)

        cmd = [
            self.binary_path,
            "--action", action,
            "--agent", agent,
            "--scope", scope,
            "--causal-hash", causal_hash,
            "--no-sound",
        ]

        if preview_only:
            cmd.append("--preview")

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception:
            return False
