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
from typing import Any, Dict

logger = logging.getLogger("AGENT-BEEPER")

class AgentPager:
    """
    Sistema de pub/sub ultraligero (Nivel 1300) para orquestación sin polling.
    Utiliza asyncio.Event subyacentes para garantizar la suspensión perfecta
    del hilo en estado C5-REAL hasta el Colapso Cuántico.
    """
    def __init__(self):
        # Mapea un tenant_id a su Event individual
        self._beepers: Dict[int, asyncio.Event] = {}
        # Mapea un tenant_id a su payload recibido en el beep
        self._payloads: Dict[int, Any] = {}
        # Evento global para multicast
        self._global_beep: asyncio.Event = asyncio.Event()
        self._global_payload: Any = None
    
    def register_agent(self, tenant_id: int) -> None:
        """Registra un agente en la centralita de beepers."""
        if tenant_id not in self._beepers:
            self._beepers[tenant_id] = asyncio.Event()
            self._payloads[tenant_id] = None
            
    def deregister_agent(self, tenant_id: int) -> None:
        """Elimina a un agente de la centralita."""
        self._beepers.pop(tenant_id, None)
        self._payloads.pop(tenant_id, None)

    async def wait_for_beep(self, tenant_id: int) -> Any:
        """
        Bloquea (suspende) al agente con latencia/overhead cero
        hasta que recibe un beep unicast o multicast.
        """
        if tenant_id not in self._beepers:
            self.register_agent(tenant_id)
            
        local_event = self._beepers[tenant_id]
        
        global_task = asyncio.create_task(self._global_beep.wait())
        local_task = asyncio.create_task(local_event.wait())
        
        done, pending = await asyncio.wait(
            [local_task, global_task], 
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for p in pending:
            p.cancel()
            
        if local_task in done:
            payload = self._payloads.get(tenant_id)
            local_event.clear()
            self._payloads[tenant_id] = None
            return payload
        else:
            return self._global_payload

    def beep_agent(self, tenant_id: int, payload: Any = None) -> None:
        """Emite un pulso unicast a un agente específico."""
        if tenant_id in self._beepers:
            self._payloads[tenant_id] = payload
            self._beepers[tenant_id].set()
            
    def beep_swarm(self, payload: Any = None) -> None:
        """Colapso cuántico: Emite un pulso multicast a toda la Legión."""
        logger.info(f"📡 [BEEPER] Transmitiendo pulso de Colapso Global... Payload: {payload}")
        self._global_payload = payload
        self._global_beep.set()

    def reset_global_beep(self) -> None:
        self._global_beep.clear()
        self._global_payload = None
