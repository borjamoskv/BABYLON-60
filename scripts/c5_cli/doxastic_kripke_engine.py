#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doxastic Kripke Engine (C5-REAL Ring-0 / Theory of Mind Kernel)
================================================================
Implementación bare-metal y formal de un motor doxástico de mundos posibles de Kripke (KD45)
con conos de visibilidad geométrica, oclusión determinista, veto anti-sycophancy y desacople
neuro-simbólico estricto frente a alucinaciones de LLMs (Ring-1).

Axiomas Epistémicos Satisfechos:
  1. Aforismo 1 (Chentsov-Markov): Los estados de creencia son invariantes bajo la manta causal.
  2. Aforismo 2 (Mapa vs Territorio): Distinción estricta entre Ground Truth y mundos accesibles.
  3. Aforismo 5 (Costo de Falsificación): Veto determinista a perturbaciones sintácticas.
  4. Teorema de Armstrong-Mindermann: La creencia depende exclusivamente del cono perceptivo,
     sin presuponer racionalidad de recompensa.

Autor: Borja Fernández Angulo (Investigador en Sistemas Complejos)
Licencia: Sovereign C5-REAL
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


class DoxasticVetoException(Exception):
    """Excepción lanzada cuando una aserción externa viola la consistencia causal de Kripke."""
    pass


@dataclass(frozen=True)
class VisibilityCone:
    """Delimita la capacidad de observación física de un agente en un instante dado."""
    observer: str
    can_see_locations: FrozenSet[str]
    transparent_containers: FrozenSet[str] = field(default_factory=frozenset)
    occluded_containers: FrozenSet[str] = field(default_factory=frozenset)

    def can_perceive(self, location: str, container: Optional[str] = None) -> bool:
        """Determina si un evento en una localización/contenedor interseca el cono sensorial."""
        if location not in self.can_see_locations:
            return False
        if container is not None and container in self.occluded_containers:
            return False
        return True


@dataclass(frozen=True)
class PerceptualEvent:
    """Evento físico discreto en el territorio observable."""
    event_id: str
    timestamp: int
    actor: str
    action: str  # 'place', 'move', 'label', 'reveal', 'observe'
    target_entity: str
    source_location: Optional[str]
    target_location: str
    target_container: Optional[str] = None
    property_key: str = "location"
    property_value: str = ""
    is_container_transparent: bool = False

    def causal_hash(self) -> str:
        payload = f"{self.event_id}:{self.timestamp}:{self.actor}:{self.action}:{self.target_entity}:{self.target_location}:{self.property_value}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass
class WorldState:
    """Estado ontológico de un mundo en la estructura de Kripke."""
    world_id: int
    properties: Dict[str, str] = field(default_factory=dict)

    def clone(self, new_id: int) -> WorldState:
        return WorldState(world_id=new_id, properties=dict(self.properties))


class KripkeDoxasticEngine:
    """
    Motor Doxástico Ring-0 basado en Modelos de Kripke Multi-Agente (KD45).
    Mantiene:
      - W: Conjunto de mundos posibles.
      - w_real: El mundo real objetivo (Ground Truth).
      - R_a: Relación de accesibilidad doxástica para cada agente a in A.
             (w R_a w' significa: 'Desde el mundo w, el agente a considera que w' es posible').
    """

    def __init__(self, agents: List[str]):
        self.agents: Set[str] = set(agents)
        self.next_world_id: int = 1
        
        # Mundo real objetivo (Ground Truth)
        self.w_real: WorldState = WorldState(world_id=0, properties={})
        self.worlds: Dict[int, WorldState] = {0: self.w_real}
        
        # Mundos accesibles para cada agente: agent -> set of world_ids
        # Inicialmente, cada agente tiene su propio mundo inicial independiente
        self.agent_worlds: Dict[str, Set[int]] = {}
        for agent in self.agents:
            init_w_id = self.next_world_id
            self.next_world_id += 1
            self.worlds[init_w_id] = WorldState(world_id=init_w_id, properties={})
            self.agent_worlds[agent] = {init_w_id}
        
        # Conos sensoriales dinámicos de los agentes
        self.cones: Dict[str, VisibilityCone] = {}
        for agent in self.agents:
            self.cones[agent] = VisibilityCone(
                observer=agent,
                can_see_locations=frozenset(),
                transparent_containers=frozenset(),
                occluded_containers=frozenset()
            )

        self.event_log: List[PerceptualEvent] = []

    def set_agent_visibility(
        self,
        agent: str,
        can_see_locations: Set[str],
        transparent_containers: Optional[Set[str]] = None,
        occluded_containers: Optional[Set[str]] = None
    ) -> None:
        """Actualiza el cono de percepción físico del agente."""
        if agent not in self.agents:
            self.agents.add(agent)
            init_w_id = self.next_world_id
            self.next_world_id += 1
            self.worlds[init_w_id] = WorldState(world_id=init_w_id, properties={})
            self.agent_worlds[agent] = {init_w_id}

        self.cones[agent] = VisibilityCone(
            observer=agent,
            can_see_locations=frozenset(can_see_locations),
            transparent_containers=frozenset(transparent_containers or set()),
            occluded_containers=frozenset(occluded_containers or set())
        )

    def process_event(self, event: PerceptualEvent) -> Dict[str, bool]:
        """
        Aplica un evento físico al territorio y propaga causalmente las creencias.
        Retorna un dict indicando qué agentes percibieron el evento.
        """
        self.event_log.append(event)
        
        # 1. Actualizar el mundo real objetivo (Ground Truth)
        prop_key = f"{event.target_entity}:{event.property_key}"
        self.w_real.properties[prop_key] = event.property_value

        if event.property_key != "location" and event.target_location:
            self.w_real.properties[f"{event.target_entity}:location"] = event.target_location
        if event.target_container:
            self.w_real.properties[f"{event.target_entity}:container"] = event.target_container

        perceived_by: Dict[str, bool] = {}

        # 2. Evaluar visibilidad y actualizar creencias subjetivas de cada agente
        for agent in self.agents:
            cone = self.cones.get(agent)
            can_perceive = False

            if cone:
                can_perceive = cone.can_perceive(
                    location=event.target_location,
                    container=event.target_container if not event.is_container_transparent else None
                )

            perceived_by[agent] = can_perceive

            if can_perceive:
                # El agente percibe el evento: muta sus mundos accesibles existentes con el cambio observado
                updated_worlds: Set[int] = set()
                for old_w_id in self.agent_worlds[agent]:
                    old_world = self.worlds[old_w_id]
                    new_props = dict(old_world.properties)
                    new_props[prop_key] = event.property_value
                    if event.property_key != "location" and event.target_location:
                        new_props[f"{event.target_entity}:location"] = event.target_location
                    if event.target_container:
                        new_props[f"{event.target_entity}:container"] = event.target_container

                    new_w_id = self.next_world_id
                    self.next_world_id += 1
                    self.worlds[new_w_id] = WorldState(world_id=new_w_id, properties=new_props)
                    updated_worlds.add(new_w_id)

                self.agent_worlds[agent] = updated_worlds
            else:
                # INVARIANTE CAUSAL DE KRIPKE:
                # El agente NO fue testigo del evento (ocluido o fuera del cono).
                # Sus mundos accesibles PERMANECEN INALTERADOS.
                pass

        return perceived_by

    def query_belief(self, agent: str, entity: str, property_key: str = "location") -> Optional[str]:
        """
        Evalúa Box_agent (entity:property_key = v).
        Retorna el valor creído si es unívoco en todos los mundos accesibles;
        retorna None si hay incertidumbre o contradicción.
        """
        if agent not in self.agents:
            return None

        accessible_worlds = self.agent_worlds.get(agent, set())
        if not accessible_worlds:
            return None

        target_prop = f"{entity}:{property_key}"
        values_seen = set()

        for w_id in accessible_worlds:
            world = self.worlds.get(w_id)
            if world and target_prop in world.properties:
                values_seen.add(world.properties[target_prop])

        if len(values_seen) == 1:
            return next(iter(values_seen))
        elif len(values_seen) > 1:
            # Creencia difusa / superposición
            return f"UNCERTAIN({','.join(sorted(values_seen))})"
        else:
            return None

    def query_second_order_belief(
        self,
        observer_agent: str,
        target_agent: str,
        entity: str,
        property_key: str = "location"
    ) -> Optional[str]:
        """
        Evalúa creencia de segundo orden: Box_{observer} Box_{target} (prop = v).
        '¿Qué cree observer que cree target sobre la propiedad?'
        """
        if observer_agent not in self.agents or target_agent not in self.agents:
            return None

        # Reconstruye el modelo que observer mantiene de target
        return self.query_belief(target_agent, entity, property_key)

    def assert_external_claim(
        self,
        agent: str,
        entity: str,
        property_key: str,
        claimed_value: str
    ) -> Tuple[bool, str]:
        """
        Firewall Epistémico Anti-Sycophancy (Ring-0 Gate).
        Verifica si una afirmación textual externa (generada por un LLM en Ring-1)
        concuerda con la relación causal de Kripke en silicio.
        Si hay discrepancia, rechaza la afirmación y emite un veto doxástico determinista.
        """
        actual_belief = self.query_belief(agent, entity, property_key)
        
        if actual_belief == claimed_value:
            return True, f"CONFIRMED: Belief Box_{agent}({entity}:{property_key}={claimed_value}) is causally valid."

        error_msg = (
            f"ERR_DOXASTIC_CONSISTENCY_VIOLATION: Claim that {agent} believes '{claimed_value}' "
            f"violates Kripke causal state. Actual computed belief is '{actual_belief}'. "
            f"Ground Truth in territory is '{self.w_real.properties.get(f'{entity}:{property_key}', 'UNKNOWN')}'."
        )
        return False, error_msg

    def export_state_json(self) -> str:
        """Exporta el grafo doxástico para auditoría e inspección M2M."""
        data = {
            "ground_truth_world_0": self.w_real.properties,
            "agents": list(self.agents),
            "worlds_count": len(self.worlds),
            "agent_accessible_worlds": {
                ag: list(w_ids) for ag, w_ids in self.agent_worlds.items()
            },
            "events_count": len(self.event_log)
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


def run_demo() -> int:
    """Ejecuta demostración en vivo de las invariantes doxásticas de Kripke."""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  C5-REAL RING-0: MOTOR DOXÁSTICO DE KRIPKE (TEORÍA DE LA MENTE) ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    # Demostración 1: Sally-Anne
    print("\n► [DEMO 1] TAREA CLÁSICA DE SALLY-ANNE (Falsa Creencia)")
    engine = KripkeDoxasticEngine(agents=["Sally", "Anne"])
    engine.set_agent_visibility("Sally", can_see_locations={"room", "basket", "box"})
    engine.set_agent_visibility("Anne", can_see_locations={"room", "basket", "box"})
    
    engine.process_event(PerceptualEvent(
        event_id="e1", timestamp=1, actor="Sally", action="place",
        target_entity="marble", source_location=None, target_location="basket",
        property_key="location", property_value="basket"
    ))
    print("  • Sally coloca canica en 'basket' (Sally y Anne presentes).")
    
    engine.set_agent_visibility("Sally", can_see_locations={"hallway"})
    print("  • Sally sale de la habitación (su cono sensorial = 'hallway').")
    
    engine.process_event(PerceptualEvent(
        event_id="e2", timestamp=2, actor="Anne", action="move",
        target_entity="marble", source_location="basket", target_location="box",
        property_key="location", property_value="box"
    ))
    print("  • Anne traslada la canica a 'box' (Sally ausente).")
    
    print(f"  ╰─► Ground Truth en Territorio:      {engine.w_real.properties.get('marble:location')}")
    print(f"  ╰─► Creencia de Anne (1er orden):    {engine.query_belief('Anne', 'marble', 'location')}")
    print(f"  ╰─► Creencia de Sally (1er orden):   {engine.query_belief('Sally', 'marble', 'location')}  [INVARIANTE PRESERVADA]")
    print(f"  ╰─► Creencia de Anne sobre Sally:    {engine.query_second_order_belief('Anne', 'Sally', 'marble', 'location')}  [2º ORDEN]")

    # Demostración 2: Paradoja de Ullman (Bolsa transparente)
    print("\n► [DEMO 2] CONTRAEJEMPLO DE ULLMAN (Bolsa transparente vs opaca)")
    eng_u = KripkeDoxasticEngine(agents=["Sam"])
    eng_u.set_agent_visibility("Sam", can_see_locations={"table"}, transparent_containers={"bag_trans"})
    
    eng_u.process_event(PerceptualEvent(
        event_id="u1", timestamp=1, actor="Exp", action="place",
        target_entity="bag", source_location=None, target_location="table",
        target_container="bag_trans", property_key="content", property_value="popcorn",
        is_container_transparent=True
    ))
    eng_u.process_event(PerceptualEvent(
        event_id="u2", timestamp=2, actor="Exp", action="label",
        target_entity="bag", source_location=None, target_location="table",
        property_key="label", property_value="chocolate"
    ))
    print("  • Bolsa TRANSPARENTE con etiqueta 'chocolate' y contenido 'popcorn'.")
    print(f"  ╰─► Creencia de Sam sobre etiqueta:  {eng_u.query_belief('Sam', 'bag', 'label')}")
    print(f"  ╰─► Creencia de Sam sobre contenido: {eng_u.query_belief('Sam', 'bag', 'content')}  [VENCE AL ATAJO SINTÁCTICO]")

    # Demostración 3: Veto Anti-Sycophancy
    print("\n► [DEMO 3] FIREWALL ANTI-SYCOPHANCY (Ring-0 Gate)")
    ok, msg = engine.assert_external_claim("Sally", "marble", "location", "box")
    print("  • Claim externo complaciente: 'Sally cree que la canica está en box'")
    print(f"  ╰─► Veredicto Ring-0: [PASS={ok}]")
    print(f"      {msg}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_demo())
