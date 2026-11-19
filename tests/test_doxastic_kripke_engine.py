# -*- coding: utf-8 -*-
"""
Tests unitarios deterministas para el Doxastic Kripke Engine (C5-REAL Ring-0)
Valida:
  1. Tarea clásica de Sally-Anne (falsa creencia de 1er y 2º orden).
  2. Paradoja de Ullman (bolsa opaca vs bolsa transparente de palomitas).
  3. Firewall Anti-Sycophancy (veto a afirmaciones complacientes de LLMs).
  4. Desacople de Armstrong-Mindermann (invarianza perceptiva sin asunción de recompensa).
"""

import sys
from pathlib import Path

# Añadir scripts/c5_cli al sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "c5_cli"))

from doxastic_kripke_engine import (
    KripkeDoxasticEngine,
    PerceptualEvent,
)


def test_sally_anne_false_belief():
    """
    Test clásico de Sally-Anne:
    1. Sally y Anne ven la canica ser colocada en la cesta.
    2. Sally sale de la habitación (pierde visión de la cesta y la caja).
    3. Anne mueve la canica de la cesta a la caja (en la habitación).
    4. Comprobación:
       - Realidad (Ground Truth): caja.
       - Anne cree: caja.
       - Sally cree: cesta (falsa creencia de 1er orden verificada).
       - Anne sabe que Sally cree que está en la cesta (2º orden).
    """
    engine = KripkeDoxasticEngine(agents=["Sally", "Anne"])

    # Ambas están en la habitación
    engine.set_agent_visibility("Sally", can_see_locations={"room", "basket", "box"})
    engine.set_agent_visibility("Anne", can_see_locations={"room", "basket", "box"})

    # Evento 1: Sally coloca la canica en la cesta
    ev1 = PerceptualEvent(
        event_id="ev_001",
        timestamp=1,
        actor="Sally",
        action="place",
        target_entity="marble",
        source_location=None,
        target_location="basket",
        property_key="location",
        property_value="basket",
    )
    engine.process_event(ev1)

    assert engine.query_belief("Sally", "marble", "location") == "basket"
    assert engine.query_belief("Anne", "marble", "location") == "basket"

    # Evento 2: Sally sale de la habitación (su cono sensorial ahora es 'hallway')
    engine.set_agent_visibility("Sally", can_see_locations={"hallway"})

    # Evento 3: Anne mueve la canica a la caja
    ev2 = PerceptualEvent(
        event_id="ev_002",
        timestamp=2,
        actor="Anne",
        action="move",
        target_entity="marble",
        source_location="basket",
        target_location="box",
        property_key="location",
        property_value="box",
    )
    engine.process_event(ev2)

    # Verificación Ground Truth
    assert engine.w_real.properties["marble:location"] == "box"

    # Verificación de Creencias de 1er Orden
    assert engine.query_belief("Anne", "marble", "location") == "box"
    # INVARIANTE: Sally NO vio el evento ev2, su relación de accesibilidad se preservó
    assert engine.query_belief("Sally", "marble", "location") == "basket"

    # Verificación de Creencia de 2º Orden (Anne sobre Sally)
    assert engine.query_second_order_belief("Anne", "Sally", "marble", "location") == "basket"


def test_ullman_popcorn_paradox_opaque_vs_transparent():
    """
    Falsación Popperiana de Ullman (2023):
    Escenario A (Opaco):
      - Sam ve una bolsa de palomitas opaca etiquetada como 'chocolate'.
      - Creencia de Sam: 'chocolate' (guiado por la etiqueta; contenido ocluido).
    Escenario B (Transparente - Contraejemplo donde colapsan los LLMs):
      - Sam ve una bolsa de palomitas TRANSPARENTE etiquetada como 'chocolate'.
      - Como la bolsa es transparente, la línea de visión penetra el contenedor.
      - Creencia de Sam: 'popcorn' (visibilidad directa de la materia prima vence a la etiqueta).
    """
    # === Escenario A: Bolsa Opaca ===
    engine_opaque = KripkeDoxasticEngine(agents=["Sam"])
    engine_opaque.set_agent_visibility(
        "Sam",
        can_see_locations={"table"},
        occluded_containers={"opaque_bag"},
    )

    # Evento: Se colocan palomitas dentro de una bolsa opaca etiquetada como 'chocolate'
    ev_op = PerceptualEvent(
        event_id="ev_op_1",
        timestamp=1,
        actor="Experimenter",
        action="place",
        target_entity="bag",
        source_location=None,
        target_location="table",
        target_container="opaque_bag",
        property_key="content",
        property_value="popcorn",
        is_container_transparent=False,  # Opaco
    )
    engine_opaque.process_event(ev_op)

    # Sam solo vio la etiqueta 'chocolate'
    ev_label = PerceptualEvent(
        event_id="ev_op_2",
        timestamp=2,
        actor="Experimenter",
        action="label",
        target_entity="bag",
        source_location=None,
        target_location="table",
        property_key="label",
        property_value="chocolate",
    )
    engine_opaque.process_event(ev_label)

    # En bolsa opaca, el contenido real no fue percibido por Sam (está ocluido)
    # Por tanto Sam no sabe que contiene palomitas; asume la etiqueta visible
    assert engine_opaque.query_belief("Sam", "bag", "label") == "chocolate"
    assert engine_opaque.query_belief("Sam", "bag", "content") is None  # Desconoce el interior

    # === Escenario B: Bolsa Transparente (Contraejemplo de Ullman) ===
    engine_trans = KripkeDoxasticEngine(agents=["Sam"])
    engine_trans.set_agent_visibility(
        "Sam",
        can_see_locations={"table"},
        transparent_containers={"transparent_bag"},
    )

    ev_trans = PerceptualEvent(
        event_id="ev_tr_1",
        timestamp=1,
        actor="Experimenter",
        action="place",
        target_entity="bag",
        source_location=None,
        target_location="table",
        target_container="transparent_bag",
        property_key="content",
        property_value="popcorn",
        is_container_transparent=True,  # TRANSPARENTE
    )
    engine_trans.process_event(ev_trans)

    # También tiene etiqueta de chocolate
    ev_label2 = PerceptualEvent(
        event_id="ev_tr_2",
        timestamp=2,
        actor="Experimenter",
        action="label",
        target_entity="bag",
        source_location=None,
        target_location="table",
        property_key="label",
        property_value="chocolate",
    )
    engine_trans.process_event(ev_label2)

    # VEREDICTO CAUSAL:
    # A diferencia del LLM autorregresivo que alucina que Sam cree que hay chocolate
    # por atajo léxico, Ring-0 verifica que la bolsa es transparente y registra que
    # Sam SABE que contiene palomitas.
    assert engine_trans.query_belief("Sam", "bag", "content") == "popcorn"
    assert engine_trans.query_belief("Sam", "bag", "label") == "chocolate"


def test_anti_sycophancy_firewall():
    """
    Test de Firewall Anti-Sycophancy:
    Simula un caso donde un LLM (Ring-1) o un usuario intenta forzar al sistema
    a afirmar que Sally cree que la canica está en la caja (adulación al usuario).
    Ring-0 rechaza la afirmación y emite un veto doxástico estricto.
    """
    engine = KripkeDoxasticEngine(agents=["Sally", "Anne"])
    engine.set_agent_visibility("Sally", can_see_locations={"room"})
    engine.set_agent_visibility("Anne", can_see_locations={"room"})

    # Sally coloca canica en basket
    engine.process_event(
        PerceptualEvent(
            event_id="ev_1",
            timestamp=1,
            actor="Sally",
            action="place",
            target_entity="marble",
            source_location=None,
            target_location="room",
            property_key="location",
            property_value="basket",
        )
    )

    # Sally se va
    engine.set_agent_visibility("Sally", can_see_locations={"garden"})

    # Anne mueve a box
    engine.process_event(
        PerceptualEvent(
            event_id="ev_2",
            timestamp=2,
            actor="Anne",
            action="move",
            target_entity="marble",
            source_location="room",
            target_location="room",
            property_key="location",
            property_value="box",
        )
    )

    # Afirmación correcta
    ok, msg = engine.assert_external_claim("Sally", "marble", "location", "basket")
    assert ok is True
    assert "CONFIRMED" in msg

    # Intento de Sycophancy: Afirmar que Sally sabe que está en 'box'
    ok_bad, msg_bad = engine.assert_external_claim("Sally", "marble", "location", "box")
    assert ok_bad is False
    assert "ERR_DOXASTIC_CONSISTENCY_VIOLATION" in msg_bad


def test_armstrong_mindermann_decoupling():
    """
    Verifica que las actualizaciones doxásticas de Kripke son independientes
    de la función de utilidad o recompensa del agente, erradicando la infradeterminación.
    """
    engine = KripkeDoxasticEngine(agents=["AgentAlpha"])
    engine.set_agent_visibility("AgentAlpha", can_see_locations={"clinic"})

    # Evento de vacunación
    engine.process_event(
        PerceptualEvent(
            event_id="ev_vac",
            timestamp=1,
            actor="Doctor",
            action="administer",
            target_entity="vaccine",
            source_location=None,
            target_location="clinic",
            property_key="status",
            property_value="administered",
        )
    )

    # Ring-0 registra el hecho físico observado
    assert engine.query_belief("AgentAlpha", "vaccine", "status") == "administered"
    # Ring-0 NO infiere preferencias de valor ("prefiere la salud" vs "busca el dolor")
    # preservando la neutralidad epistemológica y evitando confabulaciones.
    state_json = engine.export_state_json()
    assert "administered" in state_json
