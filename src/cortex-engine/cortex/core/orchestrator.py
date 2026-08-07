# C5-REAL EXERGY CERTIFIED
import os
import mmap
import tempfile
import time
from typing import Optional

from cortex.ipc.bridge import CortexIPCBridge, EpochState
from cortex.core.l5_anchor import InferenceL5Anchor

class CortexOrchestrator:
    """
    El Causa Eficiente (Orquestador BFT).
    Controla el bucle agéntico, la instanciación de memoria compartida
    y el anclaje determinista con el Kernel de Rust en Ring-0.
    """
    def __init__(self):
        self.bridge = CortexIPCBridge()
        self.epoch_state_ptr = None
        self._shm_file = None
        self._fd = None
        self.is_active = False
        self.l5_anchor = InferenceL5Anchor()

    def boot_kernel_memory(self):
        """
        Inicializa la topología mmap. Delega la validación de memoria a Rust (AXIOMA 3).
        """
        # Crear un archivo de memoria temporal real (backing file para mmap IPC).
        # En producción C5-REAL, podría montarse en /dev/shm.
        self._shm_file = tempfile.NamedTemporaryFile(prefix="c5real_shm_", delete=False)
        self._fd = self._shm_file.fileno()

        # Pre-alojar espacio mínimo (tamaño de EpochState = 24 bytes)
        # Aseguramos un tamaño que encaje en páginas del SO
        os.ftruncate(self._fd, 4096)

        # Iniciar punteros en Rust
        self.epoch_state_ptr = self.bridge.init_shared_memory(self._fd)

        # Inicialización segura
        self.bridge.initialize_epoch_state(self.epoch_state_ptr)
        self.is_active = True

        print("[ORCHESTRATOR] Memoria compartida BFT mapeada y anclada al Kernel Rust.")

    def get_active_epoch(self) -> tuple[int, int]:
        """Lee el estado del manifiesto activo sin fricción ni locks."""
        if not self.is_active:
            raise RuntimeError("Orquestador apagado. No se puede leer epoch.")
        return self.bridge.read_active_epoch_safe(self.epoch_state_ptr)

    def stamp_active_epoch(self, payload: dict) -> dict:
        """Sella criptográficamente la inferencia activa en OpenTimestamps."""
        if not self.is_active:
            raise RuntimeError("Orquestador apagado. No se puede atestar epoch.")

        epoch, ts = self.get_active_epoch()
        return self.l5_anchor.anchor_inference(epoch, ts, payload)

    def shutdown(self):
        """Consume y purga termodinámicamente la conexión."""
        if self.is_active and self.epoch_state_ptr:
            self.bridge.destroy_shared_memory(self.epoch_state_ptr)
        if self._shm_file:
            self._shm_file.close()
            try:
                os.unlink(self._shm_file.name)
            except OSError:
                pass
        self.is_active = False
        print("[ORCHESTRATOR] Memoria desanclada. Purga termodinámica completada.")

    def __enter__(self):
        self.boot_kernel_memory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
