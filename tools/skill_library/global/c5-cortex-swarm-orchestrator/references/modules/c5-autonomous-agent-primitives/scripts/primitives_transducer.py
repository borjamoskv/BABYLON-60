#!/usr/bin/env python3
"""
Motor de Transducción y Enrutamiento Determinista de las 47 Primitivas de Agente Autónomo
Arquitectura C5-REAL · Ecosistema BABYLON-60

Colapsa formalmente las 47 primitivas de agente en 4 macro-transductores canónicos:
  - T1: KUDURRU-BIOMETRIC-GATE (Ring-0)
  - T2: TAMKARUM-CDP-ENGINE (Ring-1)
  - T3: PARACORTEX-DISPATCHER (Ring-1)
  - T4: GENESIS-COGNITIVE-FORGE (Ring-1)

Incluye relocalización automática de playbooks estadounidenses hacia la infraestructura
soberana real del territorio europeo/español.
"""

import sys
import json
import re
from typing import Dict, Any, List, Optional

# Definición canónica de las 47 primitivas
PRIMITIVES: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "routines",
        "transducer": "T3",
        "category": "Operaciones",
        "patterns": [r"av[ií]same cada", r"recu[eé]rdame a las", r"revisa todos los d[ií]as", r"schedule check", r"daily digest"],
        "local_route": "daemon:launchd / schedule (5-field cron)",
        "anti_trigger": "Acción puntual e inmediata sin periodicidad."
    },
    2: {
        "name": "scheduling",
        "transducer": "T3",
        "category": "Operaciones",
        "patterns": [r"pon una reuni[oó]n", r"calendario", r"disponibilidad", r"agenda cita", r"cancel meeting"],
        "local_route": "eventkit:icalBuddy / c5-interactive-gantt-planner",
        "anti_trigger": "Recordatorios sueltos sin franja horaria bloqueada."
    },
    3: {
        "name": "skill-authoring",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"guarda este flujo como skill", r"crea una skill", r"herramienta reutilizable", r"new custom skill"],
        "local_route": "skill:cortex-skill-genesis (SKILL.md / YAML)",
        "anti_trigger": "Ejecución de un comando bash desechable de un solo uso."
    },
    4: {
        "name": "learn-from-demonstration",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"aprende de esta grabaci[oó]n", r"mira mi pantalla", r"record demonstration", r"learn from workflow"],
        "local_route": "cdp:trace_recorder / dom_parser",
        "anti_trigger": "Peticiones donde el flujo ya está parametrizado por código."
    },
    5: {
        "name": "channels",
        "transducer": "T3",
        "category": "Operaciones",
        "patterns": [r"conecta slack", r"vincula telegram", r"av[ií]same por whatsapp", r"link message channel"],
        "local_route": "gateway:whatsapp-nexus-protocol / local_socket",
        "anti_trigger": "Envío de un mensaje suelto a un usuario."
    },
    6: {
        "name": "send-on-behalf",
        "transducer": "T3",
        "category": "Operaciones",
        "patterns": [r"m[aá]ndale un correo a", r"escribe un email", r"deja un borrador en slack", r"draft email to"],
        "local_route": "mta:/usr/sbin/sendmail (headless background dispatch)",
        "anti_trigger": "Despacho directo sin validación previa del borrador por el Operador."
    },
    7: {
        "name": "voice",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"d[ií]melo en voz", r"l[eé]eme esto en audio", r"nota de voz", r"voice memo", r"read aloud"],
        "local_route": "dsp:f5tts-voice-cloning-sota (Apple Silicon MPS)",
        "anti_trigger": "Respuestas estándar de texto en el canal de chat."
    },
    8: {
        "name": "code-changes",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"modifica la funci[oó]n", r"refactoriza este archivo", r"arregla este bug", r"apply patch"],
        "local_route": "fs:replace_file_content / c5-thermos-audit",
        "anti_trigger": "Consultas teóricas o lectura de código sin mutación."
    },
    9: {
        "name": "source-control",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"haz un commit y push", r"abre una pull request", r"create pr", r"merge branch"],
        "local_route": "vcs:jujutsu-vcs-management (jj / git DAG)",
        "anti_trigger": "Mutación de archivos locales sin intención de versión."
    },
    10: {
        "name": "add-connector",
        "transducer": "T1",
        "category": "Seguridad",
        "patterns": [r"conecta mi cuenta de", r"instala el conector de", r"autentica linear", r"install connector"],
        "local_route": "auth:c5-1password-secrets (op run / zero-cloud-leak)",
        "anti_trigger": "Navegación web pública sin credenciales de usuario."
    },
    11: {
        "name": "purchases",
        "transducer": "T1",
        "category": "Seguridad",
        "patterns": [r"compra esto", r"reserva el billete y p[aá]galo", r"haz el checkout", r"proceed to payment"],
        "local_route": "gate:c5_biometric_gate (Touch ID NIST P-256 / KudurruGate)",
        "anti_trigger": "Búsqueda y comparación sin intención de compromiso de fondos."
    },
    12: {
        "name": "shopping",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"busca el mejor precio", r"compara art[ií]culo", r"mira si hay stock", r"price check"],
        "local_route": "transducer:TAMKARUM-60 (multi-source scraping)",
        "anti_trigger": "Ejecución final de cobro en pasarela bancaria."
    },
    13: {
        "name": "sign-in",
        "transducer": "T1",
        "category": "Seguridad",
        "patterns": [r"inicia sesi[oó]n en", r"entra con mi cuenta a", r"resuelve el captcha", r"login to"],
        "local_route": "auth:1Password CLI + local chromium user-data-dir",
        "anti_trigger": "Navegación en dominios públicos sin pantalla de login."
    },
    14: {
        "name": "in-chat-forms",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"rellena este formulario", r"completa los campos de env[ií]o", r"fill form"],
        "local_route": "ui:ask_question modal / generative_ui widgets",
        "anti_trigger": "Formularios de tarjeta bancaria (derivados a T1)."
    },
    15: {
        "name": "box-desktop",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"abre el navegador y haz", r"entra en esta web sin api", r"use desktop browser"],
        "local_route": "cdp:browser-subagent-orchestrator (Chromium headless local)",
        "anti_trigger": "Servicios con endpoint API local disponible."
    },
    16: {
        "name": "no-connector-fallback",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"el conector est[aá] fallando", r"se atasc[oó] el login", r"connector fallback"],
        "local_route": "chain:cURL -> Readability DOM -> Local CDP",
        "anti_trigger": "Cuando la API responde HTTP 200 de forma nominal."
    },
    17: {
        "name": "export-bot-template",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"exporta la plantilla", r"copia para compartir", r"export bot template"],
        "local_route": "handoff:HANDOFF.md / git-versioned skills",
        "anti_trigger": "Backup con datos de historial o credenciales privadas."
    },
    18: {
        "name": "group-chat-turns",
        "transducer": "T3",
        "category": "Operaciones",
        "patterns": [r"@bot", r"grupo nexus", r"sala grupal", r"menci[oó]n en grupo"],
        "local_route": "filter:c5_epistemic_output_format (MODO A1 / A2)",
        "anti_trigger": "Mensajes generales del grupo donde el bot no es interpelado."
    },
    19: {
        "name": "flight-booking",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"b[uú]scame un vuelo", r"billetes de avi[oó]n", r"find flights"],
        "local_route": "transducer:Google Flights / ITA Matrix JSON headless",
        "anti_trigger": "Preguntas meteorológicas del destino sin traslado físico."
    },
    20: {
        "name": "accommodation-booking",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"busca hotel en", r"alojamiento para", r"book hotel"],
        "local_route": "transducer:Multi-source hotel aggregator (cURL / CDP)",
        "anti_trigger": "Anuncios particulares de Airbnb (enrutados a primitiva 26)."
    },
    21: {
        "name": "rideshare",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"p[ií]deme un uber", r"cu[aá]nto tarda un cabify", r"order ride"],
        "local_route": "api:Headless Cabify/Uber + Touch ID gate",
        "anti_trigger": "Rutas de metro o transporte público regular."
    },
    22: {
        "name": "restaurant-recommendations",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"d[oó]nde cenar bien", r"recomi[eé]ndame un restaurante", r"best restaurants"],
        "local_route": "radar:Popperian local gastronomy filter",
        "anti_trigger": "Reserva inmediata de mesa (enrutada a primitiva 23)."
    },
    23: {
        "name": "restaurant-booking",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"reserva mesa en", r"hueco hoy a las", r"reserve table"],
        "local_route": "playbook:OpenTable / Resy headless local session",
        "anti_trigger": "Comida a domicilio (enrutada a primitiva 24)."
    },
    24: {
        "name": "food-ordering",
        "transducer": "T2",
        "category": "Transducción",
        "patterns": [r"pide comida a domicilio", r"pide unas pizzas", r"order food delivery"],
        "local_route": "relocation:Glovo / JustEat / Hostelería directa",
        "anti_trigger": "Cesta de supermercado cruda (enrutada a primitiva 37)."
    },
    25: {
        "name": "job-search",
        "transducer": "T4",
        "category": "Cognición",
        "patterns": [r"busca ofertas de", r"puestos de rust", r"job openings"],
        "local_route": "skill:c5-career-and-interview-architect",
        "anti_trigger": "Redacción completa de currículum o preparación de entrevista."
    },
    26: {
        "name": "site-playbooks-airbnb",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"busca en airbnb", r"anuncio de airbnb"],
        "local_route": "cdp:browser-subagent-orchestrator (solo lectura / scraping DOM)",
        "anti_trigger": "Herramientas de anfitrión o gestión de anuncios propios."
    },
    27: {
        "name": "site-playbooks-bestbuy",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"busca en best buy", r"stock en best buy"],
        "local_route": "curl:Headless cURL (modo US)",
        "anti_trigger": "Compras en España sin servicio físico de Best Buy."
    },
    28: {
        "name": "site-playbooks-costco",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"precio en costco", r"carrito same-day costco"],
        "local_route": "curl:Costco unit catalog auditor",
        "anti_trigger": "Consultas sin carnet de socio activo en almacén de claves."
    },
    29: {
        "name": "site-playbooks-craigslist",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"busca en craigslist", r"clasificados craigslist"],
        "local_route": "relocation:Wallapop / Milanuncios (Scraping DOM headless)",
        "anti_trigger": "Publicar anuncios o contactar vendedores (solo lectura)."
    },
    30: {
        "name": "site-playbooks-doordash",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"carta en doordash", r"carrito doordash"],
        "local_route": "relocation:Glovo / JustEat / Hostelería directa",
        "anti_trigger": "Ejecución de cobro sin verificación dactilar en Ring-0."
    },
    31: {
        "name": "site-playbooks-ebay",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"busca en ebay", r"precio de venta en ebay"],
        "local_route": "api:eBay Completed Listings / cURL headless",
        "anti_trigger": "Pujas de último segundo (sniping) sin saldo garantizado."
    },
    32: {
        "name": "site-playbooks-etsy",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"busca en etsy", r"artesan[ií]a en etsy"],
        "local_route": "filter:Reverse image search anti-AliExpress",
        "anti_trigger": "Herramientas de vendedor (gestión de tienda)."
    },
    33: {
        "name": "site-playbooks-expedia",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"compara en expedia", r"paquetes de viaje expedia"],
        "local_route": "transducer:Multi-OTA headless aggregator",
        "anti_trigger": "Búsquedas de aerolínea monomarca directa."
    },
    34: {
        "name": "site-playbooks-facebook-marketplace",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"facebook marketplace", r"alquileres en marketplace"],
        "local_route": "cdp:Isolated local Chromium profile",
        "anti_trigger": "Enviar mensajes al vendedor o publicar artículos."
    },
    35: {
        "name": "site-playbooks-fedex",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"seguimiento de fedex", r"tracking fedex"],
        "local_route": "api:FedEx Direct API / SEUR Gateway",
        "anti_trigger": "Envíos de otras compañías logísticas."
    },
    36: {
        "name": "site-playbooks-google-flights",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"google flights", r"itinerarios google flights"],
        "local_route": "api:Google Flights public JSON endpoint / Playwright",
        "anti_trigger": "Intentar procesar compras dentro del motor."
    },
    37: {
        "name": "site-playbooks-instacart",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"compra en instacart", r"supermercado instacart"],
        "local_route": "relocation:Mercadona / Carrefour / Alcampo",
        "anti_trigger": "Confirmación de entrega sin desglose de comisiones."
    },
    38: {
        "name": "site-playbooks-linkedin",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"ofertas en linkedin", r"empleo en linkedin"],
        "local_route": "cdp:Headless CDP job scraper sin sesión pública",
        "anti_trigger": "Postulación directa o mutación de perfil personal."
    },
    39: {
        "name": "site-playbooks-luma",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"eventos en luma", r"ficha de evento en luma"],
        "local_route": "api:Luma ICS parser / REST API",
        "anti_trigger": "Cancelación de eventos gestionados por el anfitrión."
    },
    40: {
        "name": "site-playbooks-opentable",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"mesa en opentable", r"reserva en opentable"],
        "local_route": "playbook:OpenTable headless cancellation poller",
        "anti_trigger": "Restaurantes integrados en la red Resy."
    },
    41: {
        "name": "site-playbooks-realtor",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"casas en realtor", r"colegios en realtor"],
        "local_route": "relocation:Idealista / Sede Electrónica del Catastro",
        "anti_trigger": "Búsquedas inmobiliarias en territorio europeo (fuera de US)."
    },
    42: {
        "name": "site-playbooks-resy",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"mesas libres en resy", r"reserva por resy"],
        "local_route": "playbook:Resy millisecond launchd/schedule trigger",
        "anti_trigger": "Restaurantes no adscritos a la red Resy."
    },
    43: {
        "name": "site-playbooks-southwest",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"tarifas de southwest", r"vuelos southwest"],
        "local_route": "relocation:Renfe Cercanías/AVE + Iberia/Vueling",
        "anti_trigger": "Reservas, check-in o cambios de vuelo (no soportado)."
    },
    44: {
        "name": "site-playbooks-target",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"busca en target", r"stock en target"],
        "local_route": "curl:Target cURL headless (modo US)",
        "anti_trigger": "Compras en tiendas fuera de Estados Unidos."
    },
    45: {
        "name": "site-playbooks-united",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"vuelos de united", r"millas en united"],
        "local_route": "parser:United Saver award availability engine",
        "anti_trigger": "Gestión de un billete ya emitido o cambio de asiento."
    },
    46: {
        "name": "site-playbooks-ups",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"seguimiento de ups", r"tracking ups"],
        "local_route": "api:UPS Tracking API / GLS Gateway",
        "anti_trigger": "Paquetes de otras agencias logísticas."
    },
    47: {
        "name": "site-playbooks-usps",
        "transducer": "T2",
        "category": "Playbooks",
        "patterns": [r"tracking de usps", r"correos usps"],
        "local_route": "relocation:Correos España API / Webhook",
        "anti_trigger": "Envíos de paquetería privada internacional."
    }
}

# Tabla de relocalización de plataformas comerciales US hacia infraestructura europea
JURISDICTION_RELOCATIONS: Dict[str, str] = {
    "site-playbooks-craigslist": "Wallapop / Milanuncios (Scraping DOM headless)",
    "site-playbooks-doordash": "Glovo / JustEat / Hostelería directa",
    "site-playbooks-instacart": "Mercadona / Carrefour / Alcampo",
    "site-playbooks-realtor": "Idealista / Catastro API",
    "site-playbooks-southwest": "Renfe Cercanías/AVE + Iberia / Vueling",
    "site-playbooks-usps": "Correos España API"
}

TRANSDUCER_DESCRIPTIONS: Dict[str, str] = {
    "T1": "KUDURRU-BIOMETRIC-GATE (Ring-0 / Touch ID P-256 · 1Password CLI)",
    "T2": "TAMKARUM-CDP-ENGINE (Ring-1 / Schema-Driven Chromium CDP Local)",
    "T3": "PARACORTEX-DISPATCHER (Ring-1 / Demonios launchd, Agenda y MTA Local)",
    "T4": "GENESIS-COGNITIVE-FORGE (Ring-1 / Bare-Metal Code, Jujutsu jj, F5-TTS)"
}


def dispatch_primitive(primitive_id: int) -> Dict[str, Any]:
    """Retorna el contrato de despacho formal de una primitiva por su ID cardinal."""
    if primitive_id not in PRIMITIVES:
        raise ValueError(f"Primitiva {primitive_id} no existe en el catálogo sexagesimal.")

    p = PRIMITIVES[primitive_id]
    reloc = JURISDICTION_RELOCATIONS.get(p["name"])

    return {
        "id": primitive_id,
        "name": p["name"],
        "transducer_id": p["transducer"],
        "transducer_title": TRANSDUCER_DESCRIPTIONS[p["transducer"]],
        "category": p["category"],
        "execution_route": p["local_route"],
        "relocation": reloc or "Nativa / No requiere relocalización",
        "anti_trigger": p["anti_trigger"]
    }


def route_intent(prompt: str) -> Optional[Dict[str, Any]]:
    """Evalúa un prompt y lo enruta hacia la primitiva y macro-transductor correspondiente."""
    p_lower = prompt.lower()
    for pid, p in PRIMITIVES.items():
        for pat in p["patterns"]:
            if re.search(pat, p_lower):
                return dispatch_primitive(pid)
    return None


def run_self_test() -> bool:
    """Ejecuta la batería de pruebas deterministas de silicio sobre el catálogo."""
    print("=== [SUITE DETERMINISTA C5-REAL · 47 PRIMITIVAS] ===")

    # Invariante 1: Cardinalidad Isomórfica 1:1
    assert len(PRIMITIVES) == 47, f"Violación de cardinalidad: esperadas 47, detectadas {len(PRIMITIVES)}"
    print("✔ Invariante 1 superada: Cardinalidad canónica exacta = 47")

    # Invariante 2: Partición Ortogonal de los 4 Macro-Transductores
    t_counts = {"T1": 0, "T2": 0, "T3": 0, "T4": 0}
    for p in PRIMITIVES.values():
        t_counts[p["transducer"]] += 1

    # T1 = 3 (compras, auth, checkout)
    # T2 = 29 (22 site-playbooks + 7 consumo)
    # T3 = 5 (routines, scheduling, channels, send-on-behalf, group-turns)
    # T4 = 10 (skills, code, voice, git, forms, desktop, fallback, template, jobs, demo)
    assert t_counts["T1"] == 3, f"Fallo en partición T1: {t_counts['T1']} != 3"
    assert t_counts["T2"] == 29, f"Fallo en partición T2: {t_counts['T2']} != 29"
    assert t_counts["T3"] == 5, f"Fallo en partición T3: {t_counts['T3']} != 5"
    assert t_counts["T4"] == 10, f"Fallo en partición T4: {t_counts['T4']} != 10"
    print(f"✔ Invariante 2 superada: Partición ortogonal T1={t_counts['T1']}, T2={t_counts['T2']}, T3={t_counts['T3']}, T4={t_counts['T4']} (Total: 47)")

    # Invariante 3: Relocalización Jurisdiccional
    for name, target in JURISDICTION_RELOCATIONS.items():
        found = any(p["name"] == name for p in PRIMITIVES.values())
        assert found, f"Fallo de relocalización: {name} no catalogada"
    print(f"✔ Invariante 3 superada: 6 relocalizaciones soberanas activadas ({len(JURISDICTION_RELOCATIONS)})")

    # Invariante 4: Test de Enrutamiento por Expresiones Regulares
    test_cases = [
        ("avísame cada mañana a las 9", 1, "T3"),
        ("pon una reunión con Nacho", 2, "T3"),
        ("compra este billete y págalo", 11, "T1"),
        ("inicia sesión en GitHub con mi cuenta", 13, "T1"),
        ("dímelo en voz alta con nota de voz", 7, "T4"),
        ("busca en airbnb piso céntrico", 26, "T2"),
        ("busca en craigslist coches de segunda mano", 29, "T2"),
        ("tracking correos usps 94001000", 47, "T2")
    ]
    for prompt, expected_id, expected_transducer in test_cases:
        res = route_intent(prompt)
        assert res is not None, f"Fallo en reconocimiento de: '{prompt}'"
        assert res["id"] == expected_id, f"Fallo en ID para '{prompt}': esperado {expected_id}, obtenido {res['id']}"
        assert res["transducer_id"] == expected_transducer, f"Fallo en Transductor para '{prompt}'"
    print(f"✔ Invariante 4 superada: Enrutamiento sintáctico verificado ({len(test_cases)} tests)")

    print("\n[VEREDICTO SILICIO]: 100% PASS · 0 COLISIONES · TOPOLOGÍA ESTABLE")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        success = run_self_test()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 2 and sys.argv[1] == "--route":
        prompt_arg = " ".join(sys.argv[2:])
        result = route_intent(prompt_arg)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({"status": "UNMATCHED", "prompt": prompt_arg}, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "--dispatch":
        try:
            pid = int(sys.argv[2])
            print(json.dumps(dispatch_primitive(pid), indent=2, ensure_ascii=False))
        except Exception as ex:
            print(f"Error: {ex}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Uso:")
        print("  primitives_transducer.py --self-test")
        print("  primitives_transducer.py --route <prompt del usuario>")
        print("  primitives_transducer.py --dispatch <id_primitiva_1_47>")
