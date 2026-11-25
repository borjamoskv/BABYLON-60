#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
agent_beeper.py - C5-REAL Zero-Friction Agent Pager

Notificaciones asíncronas para agentes de un mismo event loop, sin polling.
"""

import asyncio
import logging
from threading import RLock
from typing import Dict, Generic, Optional, TypeVar, cast

logger = logging.getLogger("AGENT-BEEPER")

T = TypeVar("T")


class AgentPager(Generic[T]):
    """
    Notificaciones unicast y barrera global en un único event loop.
    No crea sub-tareas para combinar eventos. La difusión recorre los N
    registros y despierta sus W esperas actuales: O(N + W). Unicast señala
    un único evento y su coste depende de las esperas de ese destinatario.

    La difusión global es una barrera de una sola emisión por instancia.
    El pulso queda retenido para agentes tardíos; nuevas esperas lo reciben
    inmediatamente. Para otra ronda de difusión se crea otra instancia.
    No ofrece una cola global ni espera por la siguiente generación de mensajes.
    Una segunda difusión lanza RuntimeError y conserva el primer pulso.
    Las llamadas deben realizarse en el hilo del event loop; el bloqueo protege
    las transiciones internas, no convierte asyncio.Event en thread-safe.
    """

    def __init__(self) -> None:
        self._unicast_events: Dict[int, asyncio.Event] = {}
        self._unicast_payloads: Dict[int, T] = {}
        self._global_payload: Optional[T] = None
        self._emitted = False
        self._lock = RLock()
        self._registered_count: int = 0

    def register_agent(self, tenant_id: int) -> None:
        """Registra un agente en la matriz de la centralita."""
        with self._lock:
            if tenant_id not in self._unicast_events:
                self._unicast_events[tenant_id] = asyncio.Event()
                self._registered_count += 1

    def deregister_agent(self, tenant_id: int) -> None:
        """Elimina a un agente de la matriz."""
        with self._lock:
            event = self._unicast_events.pop(tenant_id, None)
            if event is not None:
                self._unicast_payloads.pop(tenant_id, None)
                self._registered_count -= 1
                event.set()

    async def wait_for_beep(self, tenant_id: int) -> T:
        """
        Espera el evento del destinatario, activado por unicast o difusión.
        Tras la difusión, devuelve el pulso retenido si no hay unicast pendiente.
        Otra espera no inicia una nueva ronda de difusión.
        """
        with self._lock:
            self.register_agent(tenant_id)
            event = self._unicast_events[tenant_id]

        # INV_C5_19: la espera solo continúa mientras este evento siga registrado;
        # la baja del agente es la condición de parada explícita.
        while self._is_current_waiter(tenant_id, event):
            with self._lock:
                if self._unicast_events.get(tenant_id) is not event:
                    break
                if tenant_id in self._unicast_payloads:
                    payload = self._unicast_payloads.pop(tenant_id)
                    event.clear()
                    return payload
                if self._emitted:
                    return cast(T, self._global_payload)
                event.clear()
            # Nunca mantener el bloqueo durante una suspensión.
            await event.wait()
        raise RuntimeError("Agent deregistered while waiting")

    def _is_current_waiter(self, tenant_id: int, event: asyncio.Event) -> bool:
        """Indica si ``event`` sigue siendo el evento registrado para ``tenant_id``."""
        with self._lock:
            return self._unicast_events.get(tenant_id) is event

    def beep_agent(self, tenant_id: int, payload: T) -> None:
        """Señala el evento unicast de un agente específico."""
        with self._lock:
            if tenant_id in self._unicast_events:
                self._unicast_payloads[tenant_id] = payload
                self._unicast_events[tenant_id].set()

    def beep_swarm(self, payload: T) -> None:
        """Emite la única difusión de esta instancia y la retiene para agentes tardíos.

        Rechaza cualquier segunda emisión antes de modificar el estado.
        El llamante debe crear otro AgentPager para una nueva ronda global.
        """
        with self._lock:
            if self._emitted:
                raise RuntimeError("Global broadcast already emitted; create a new AgentPager")
            self._global_payload = payload
            self._emitted = True
            for event in self._unicast_events.values():
                event.set()
            registered = self._registered_count
        logger.info("[BEEPER] Global broadcast for %d registered agents", registered)
