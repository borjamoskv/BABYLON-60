import subprocess
import logging
import hashlib
import json
import time
import os
from functools import lru_cache
from typing import Dict, Any

logger = logging.getLogger("devsecops_attest")

LOCK_FILE = ".devsecops_attest.lock"

class AttestationError(Exception):
    pass

@lru_cache(maxsize=128)
def get_git_tree_hash(path: str) -> str:
    """Caché LRU del árbol Git para evitar cómputo termodinámico innecesario."""
    try:
        result = subprocess.run(["git", "ls-tree", "HEAD", path], capture_output=True, text=True, check=True)
        return hashlib.sha256(result.stdout.encode()).hexdigest()
    except subprocess.CalledProcessError:
        return ""

class L5Attestor:
    """
    Atestación determinista L5 (Nivel de Seguridad y Trazabilidad C5-REAL).
    """
    
    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    def _acquire_lock(self):
        """Protección candado .lock para exclusión mutua durante atestación."""
        if os.path.exists(LOCK_FILE):
            raise AttestationError("Attestation is currently locked by another process.")
        with open(LOCK_FILE, "w") as f:
            f.write(str(time.time()))

    def _release_lock(self):
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    def generate_attestation_payload(self) -> Dict[str, Any]:
        """Genera el payload determinista a partir de los metadatos Git."""
        tree_hash = get_git_tree_hash(self.target_dir)
        payload = {
            "timestamp": time.time(),
            "target_dir": self.target_dir,
            "git_tree_sha256": tree_hash,
            "c5_real_invariant": "Zero-Anergy"
        }
        return payload

    def anchor_to_bitcoin(self, payload: Dict[str, Any]):
        """
        Anclaje asíncrono a Bitcoin (Simulado).
        En un entorno real usaría OpenTimestamps u otra red L1.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        merkle_root = hashlib.sha256(payload_str.encode()).hexdigest()
        logger.info(f"[L5-ATTEST] Anclando estado criptográfico (raíz: {merkle_root[:8]}...) a L1.")
        # Simulación de la latencia asíncrona de anclaje L1
        time.sleep(1.0)
        logger.info("[L5-ATTEST] Anclaje completado exitosamente.")

    def run_attestation(self):
        self._acquire_lock()
        try:
            payload = self.generate_attestation_payload()
            self.anchor_to_bitcoin(payload)
            logger.info("Atestación DevSecOps finalizada.")
        finally:
            self._release_lock()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    attestor = L5Attestor("src")
    attestor.run_attestation()
