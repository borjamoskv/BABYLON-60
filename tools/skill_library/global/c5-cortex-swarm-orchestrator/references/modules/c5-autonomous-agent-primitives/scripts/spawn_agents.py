#!/usr/bin/env python3
"""
Orquestador y Despachador de la Legión de 47 Agentes Especializados
Arquitectura C5-REAL · Ecosistema BABYLON-60

Permite:
  --list               : Lista los 47 agentes con su macro-transductor y ruta.
  --query <prompt>     : Evalúa un prompt y selecciona el agente exacto.
  --agent <id>         : Muestra la ficha completa y el system prompt del agente.
  --verify             : Valida la integridad de los 47 agentes contra el registro.
"""

import os
import sys
import json
import re

REGISTRY_PATH = os.path.expanduser("~/.gemini/config/skills/c5-autonomous-agent-primitives/agents_registry.json")

def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def list_agents(reg):
    print("=" * 80)
    print("LEGIÓN C5-REAL · CATÁLOGO DE 47 AGENTES ESPECIALIZADOS")
    print("=" * 80)
    for a in reg["agents"]:
        print(f"[{a['id']:02d}] {a['agent_name']:<35} | {a['transducer']} | {a['category']:<22} | Reloc: {a['relocation'][:25]}")
    print("=" * 80)
    print(f"Total agentes activos: {reg['total_agents']}")

def show_agent(reg, aid):
    for a in reg["agents"]:
        if a["id"] == aid:
            print(json.dumps(a, indent=2, ensure_ascii=False))
            return
    print(f"Error: Agente con ID {aid} no encontrado.", file=sys.stderr)
    sys.exit(1)

def query_agent(reg, prompt):
    p_lower = prompt.lower()
    for a in reg["agents"]:
        for trig in a["triggers"]:
            if trig.lower() in p_lower:
                print(f"✔ Match detectado: Agente {a['id']:02d} ({a['agent_name']})")
                print(f"  Macro-Transductor: {a['transducer']}")
                print(f"  Misión: {a['mission']}")
                print(f"  Ruta Local: {a['execution_route']}")
                print(f"  Relocalización: {a['relocation']}")
                return a
    print("Ningún agente específico reconoció el prompt. Derivando al orquestador general.")
    return None

def verify_all(reg):
    assert reg["total_agents"] == 47, f"Esperados 47 agentes, encontrados {reg['total_agents']}"
    missing = []
    for a in reg["agents"]:
        if not os.path.exists(a["spec_file"]):
            missing.append(a["spec_file"])
    if missing:
        print(f"❌ Error: Archivos faltantes: {missing}", file=sys.stderr)
        sys.exit(1)
    print("✔ Verificación 100% exitosa: 47/47 archivos de agentes presentes y sincronizados.")

if __name__ == "__main__":
    reg = load_registry()
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_agents(reg)
    elif len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_all(reg)
    elif len(sys.argv) > 2 and sys.argv[1] == "--agent":
        show_agent(reg, int(sys.argv[2]))
    elif len(sys.argv) > 2 and sys.argv[1] == "--query":
        query_agent(reg, " ".join(sys.argv[2:]))
    else:
        print("Uso:")
        print("  spawn_agents.py --list")
        print("  spawn_agents.py --verify")
        print("  spawn_agents.py --agent <id_1_47>")
        print("  spawn_agents.py --query <prompt>")
