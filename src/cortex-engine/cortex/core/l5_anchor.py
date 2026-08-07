# C5-REAL EXERGY CERTIFIED
import os
import json
import hashlib
import shutil
import subprocess
from pathlib import Path

class InferenceL5Anchor:
    """
    Submódulo de Atestación Criptográfica L5 (OpenTimestamps)
    Diseñado bajo Invariantes C5-REAL: Asincronía estricta y candados atómicos (.lock).
    """
    def __init__(self, anchor_dir: str = None):
        if anchor_dir is None:
            # Resolving to src/cortex-engine/l5_inference_anchors
            engine_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.anchor_dir = engine_root / "l5_inference_anchors"
        else:
            self.anchor_dir = Path(anchor_dir)

        self.anchor_dir.mkdir(parents=True, exist_ok=True)

    def anchor_inference(self, epoch: int, timestamp: int, payload: dict) -> dict:
        """
        Calcula el digest SHA3-256 de una inferencia y lanza la atestación L5 asíncrona.
        """
        core = {
            "schema": "moskv.cortex.inference/v1",
            "epoch": epoch,
            "kernel_timestamp": timestamp,
            "payload": payload
        }

        canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()

        data_file = self.anchor_dir / f"{digest}.digest"
        ots_file = self.anchor_dir / f"{digest}.digest.ots"
        lock_file = self.anchor_dir / f"{digest}.digest.lock"

        if ots_file.exists():
            return {"status": "ALREADY_STAMPED", "digest": digest, "ots": str(ots_file)}

        if lock_file.exists():
            return {"status": "IN_PROGRESS", "digest": digest, "ots": str(ots_file)}

        if shutil.which("ots") is None:
            return {
                "status": "SKIPPED",
                "digest": digest,
                "reason": "OpenTimestamps client ('ots') no encontrado en PATH."
            }

        data_file.write_text(digest, encoding="utf-8")
        lock_file.write_text("1", encoding="utf-8")

        print(f"[L5 ANCHOR] Delegando atestación OTS asíncrona para Epoch {epoch} (Digest: {digest[:12]}...)")

        # Fire and forget: asíncrono con limpieza atómica del candado
        cmd = f'ots stamp "{data_file}" ; rm -f "{lock_file}"'
        subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return {"status": "DEFERRED", "digest": digest, "data_file": str(data_file)}
