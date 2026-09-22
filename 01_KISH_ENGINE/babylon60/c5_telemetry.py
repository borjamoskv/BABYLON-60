import asyncio
import logging
from typing import Dict
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger("c5_telemetry")


@dataclass
class TelemetryEvent:
    event_type: str
    exergy_delta: float
    metadata: Dict[str, object] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SomaticStatus(str, Enum):
    """
    Estado homeostático de la manta de Markov somática.
    Isomorfo a SomaticStatus en src/fluid_thermo.rs (Ring-0).
    """
    OPTIMAL_THROUGHPUT = "OPTIMAL_THROUGHPUT"
    COOLING_THROTTLE_REQUIRED = "COOLING_THROTTLE_REQUIRED"
    THERMAL_APOPTOSIS = "THERMAL_APOPTOSIS"


@dataclass
class BiometricReading:
    heart_rate_bpm: float
    hrv_sdnn_ms: float
    package_temp_celsius: float
    cognitive_duty_cycles: int
    status: SomaticStatus
    timestamp: float = field(default_factory=time.time)

    @property
    def burnout_risk_score(self) -> float:
        """
        Calcula el índice de riesgo de burnout somático (0.0 a 1.0)
        basado en la variabilidad cardíaca (HRV) y frecuencia sostenida.
        """
        hr_factor = max(0.0, min(1.0, (self.heart_rate_bpm - 60.0) / 60.0))
        hrv_factor = max(0.0, min(1.0, (50.0 - self.hrv_sdnn_ms) / 40.0))
        temp_factor = max(0.0, min(1.0, (self.package_temp_celsius - 60.0) / 40.0))
        return round(0.4 * hr_factor + 0.4 * hrv_factor + 0.2 * temp_factor, 4)


class SomaticMarkovBlanket:
    """
    Manta de Markov Somática (KISH / Ring-1).
    Supervisa la telemetría somática del Operador Biológico (Apple Watch Series 7)
    y el hardware de silicio M-Series, previniendo el agotamiento y la degradación térmica.
    """

    def __init__(self, valve: "ThermodynamicValve | None" = None) -> None:
        self.valve = valve

    def evaluate(
        self,
        heart_rate_bpm: float,
        hrv_sdnn_ms: float,
        package_temp_celsius: float,
        uninterrupted_duty_cycles: int = 0,
    ) -> BiometricReading:
        if (
            package_temp_celsius >= 100.0
            or uninterrupted_duty_cycles >= 100_000_000
            or heart_rate_bpm >= 150.0
            or hrv_sdnn_ms <= 12.0
        ):
            status = SomaticStatus.THERMAL_APOPTOSIS
        elif (
            package_temp_celsius >= 85.0
            or uninterrupted_duty_cycles >= 50_000_000
            or heart_rate_bpm >= 115.0
            or hrv_sdnn_ms <= 25.0
        ):
            status = SomaticStatus.COOLING_THROTTLE_REQUIRED
        else:
            status = SomaticStatus.OPTIMAL_THROUGHPUT

        return BiometricReading(
            heart_rate_bpm=heart_rate_bpm,
            hrv_sdnn_ms=hrv_sdnn_ms,
            package_temp_celsius=package_temp_celsius,
            cognitive_duty_cycles=uninterrupted_duty_cycles,
            status=status,
        )

    async def record_and_ingest(
        self,
        heart_rate_bpm: float,
        hrv_sdnn_ms: float,
        package_temp_celsius: float,
        uninterrupted_duty_cycles: int = 0,
    ) -> BiometricReading:
        reading = self.evaluate(
            heart_rate_bpm, hrv_sdnn_ms, package_temp_celsius, uninterrupted_duty_cycles
        )
        if self.valve:
            exergy_delta = round(1.0 - reading.burnout_risk_score * 2.0, 4)
            await self.valve.ingest(
                event_type="SOMATIC_BIOMETRIC_UPDATE",
                exergy_delta=exergy_delta,
                metadata={
                    "hr_bpm": reading.heart_rate_bpm,
                    "hrv_ms": reading.hrv_sdnn_ms,
                    "temp_c": reading.package_temp_celsius,
                    "status": reading.status.value,
                    "burnout_risk": reading.burnout_risk_score,
                },
            )
        return reading


class ThermodynamicValve:
    """
    Cola asíncrona no bloqueante (Válvula Termodinámica).
    Permite ingerir eventos de telemetría sin acoplar ni bloquear el bucle principal (Zero-Friction).
    """

    def __init__(self, max_size: int = 1000) -> None:
        self.queue: asyncio.Queue[TelemetryEvent] = asyncio.Queue(maxsize=max_size)
        self._worker_task: asyncio.Task[None] | None = None

    async def ingest(self, event_type: str, exergy_delta: float, metadata: Dict[str, object] | None = None) -> None:
        """Ingiere un evento a la válvula. Si está llena, descarta (backpressure)."""
        event = TelemetryEvent(event_type=event_type, exergy_delta=exergy_delta, metadata=metadata or {})
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"[VALVE-FULL] Descartando evento de telemetría: {event_type}. Alta entropía detectada.")

    async def _process_events(self) -> None:
        """Bucle consumidor en background."""
        while True:
            try:
                event = await self.queue.get()
                logger.info(f"[TELEMETRY] Procesado: {event.event_type} | dEx: {event.exergy_delta}")
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[VALVE-ERROR] Error procesando telemetría: {e}")

    def start(self) -> None:
        """Inicia el Worker Asíncrono."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._process_events())

    async def stop(self) -> None:
        """Detiene la válvula y drena la cola."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
