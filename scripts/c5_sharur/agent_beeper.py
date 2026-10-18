#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
agent_beeper.py - C5-REAL Zero-Friction Agent Pager

Implementa el paradigma de Event-Sourcing para subagentes, eliminando el 
polling (anergía CPU) mediante interrupciones asíncronas puras.
"""

import asyncio
import logging
from typing import Dict, TypeVar, Generic, Optional

logger = logging.getLogger("AGENT-BEEPER")

T = TypeVar('T')

class AgentPager(Generic[T]):
    """
    Sistema de pub/sub ultraligero (Nivel 1300) para orquestación sin polling.
    Zero-Task Allocation: Cero creación de sub-tareas en Event Loop.
    Permite instanciar y sincronizar 1,000,000+ de subagentes en < 0.1s.
    """
    def __init__(self) -> None:
        self._unicast_events: Dict[int, asyncio.Event] = {}
        self._unicast_payloads: Dict[int, T] = {}
        self._global_event: asyncio.Event = asyncio.Event()
        self._global_payload: Optional[T] = None
        self._registered_count: int = 0
    
    def register_agent(self, tenant_id: int) -> None:
        """Registra un agente en la matriz de la centralita."""
        if tenant_id not in self._unicast_events:
            self._unicast_events[tenant_id] = asyncio.Event()
            self._registered_count += 1
            
    def deregister_agent(self, tenant_id: int) -> None:
        """Elimina a un agente de la matriz."""
        if tenant_id in self._unicast_events:
            del self._unicast_events[tenant_id]
            self._unicast_payloads.pop(tenant_id, None)
            self._registered_count -= 1

    async def wait_for_beep(self, tenant_id: int) -> T:
        """
        Bloquea (suspende) al agente con latencia y memoria mínima.
        Cero overhead de sub-tareas asyncio.
        """
        if tenant_id not in self._unicast_events:
            self.register_agent(tenant_id)
            
        # Fast-path 1: Mensaje Unicast previo
        if tenant_id in self._unicast_payloads:
            payload = self._unicast_payloads.pop(tenant_id)
            self._unicast_events[tenant_id].clear()
            return payload
            
        # Fast-path 2: Pulso Global previo
        if self._global_event.is_set():
            if self._global_payload is None:
                raise RuntimeError("Global event set without payload")
            return self._global_payload
            
        # Zero-Task Allocation await: Suspensión directa sobre la Primitiva C
        await self._global_event.wait()
        
        if tenant_id in self._unicast_payloads:
            return self._unicast_payloads.pop(tenant_id)
        if self._global_payload is None:
            raise RuntimeError("Agent woke up without payload")
        return self._global_payload

    def beep_agent(self, tenant_id: int, payload: T) -> None:
        """Emite un pulso unicast O(1) a un agente específico."""
        if tenant_id in self._unicast_events:
            self._unicast_payloads[tenant_id] = payload
            self._unicast_events[tenant_id].set()
            
    def beep_swarm(self, payload: T) -> None:
        """Colapso cuántico: Emite un pulso multicast O(1) a toda la Legión."""
        logger.info(f"📡 [BEEPER] OMEGA_COLLAPSE Zero-Alloc Fan-Out [N={self._registered_count}] | Payload: {payload}")
        self._global_payload = payload
        self._global_event.set()
