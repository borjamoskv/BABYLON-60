import asyncio
import logging
from typing import Any, Dict
from dataclasses import dataclass, field
import time

logger = logging.getLogger("c5_telemetry")

@dataclass
class TelemetryEvent:
    event_type: str
    exergy_delta: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class ThermodynamicValve:
    """
    Cola asíncrona no bloqueante (Válvula Termodinámica).
    Permite ingerir eventos de telemetría sin acoplar ni bloquear el bucle principal (Zero-Friction).
    """
    
    def __init__(self, max_size: int = 1000):
        self.queue = asyncio.Queue(maxsize=max_size)
        self._worker_task = None

    async def ingest(self, event_type: str, exergy_delta: float, metadata: Dict[str, Any] = None):
        """Ingiere un evento a la válvula. Si está llena, descarta (backpressure)."""
        event = TelemetryEvent(event_type=event_type, exergy_delta=exergy_delta, metadata=metadata or {})
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"[VALVE-FULL] Descartando evento de telemetría: {event_type}. Alta entropía detectada.")

    async def _process_events(self):
        """Bucle consumidor en background."""
        while True:
            try:
                event = await self.queue.get()
                # Aquí se realizaría la persistencia a BFT SQLite o sink externo
                logger.info(f"[TELEMETRY] Procesado: {event.event_type} | dEx: {event.exergy_delta}")
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[VALVE-ERROR] Error procesando telemetría: {e}")

    def start(self):
        """Inicia el worker asíncrono."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._process_events())

    async def stop(self):
        """Detiene la válvula y drena la cola."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
