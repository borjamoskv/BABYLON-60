#!/usr/bin/env python3
"""
Generador e Indexador de los 47 Agentes Especializados de C5-REAL
Arquitectura BABYLON-60 · Colapso Topológico

Genera:
  1. 47 archivos de especificación Markdown en agents/
  2. agents_registry.json consolidado con esquemas y prompts
"""

import os
import json

agents_data = [
    (1, "routines", "T3", "Día a día", "Automatismos a piñón fijo",
     "Gestionar recordatorios, resúmenes periódicos y comprobaciones desatendidas mediante demonios locales launchd y temporizadores cron sexagesimales.",
     ["avísame cada", "recuérdame a las", "revisa todos los días", "schedule check"],
     "Acción puntual e inmediata sin periodicidad.",
     "daemon:launchd / schedule (5-field cron)", "Nativa / No requiere relocalización",
     True, True, True, False),

    (2, "scheduling", "T3", "Día a día", "Mover la agenda sin mirar la pantalla",
     "Gestionar eventos de calendario, detectar colisiones de horario y verificar disponibilidad mediante EventKit nativo e icalBuddy sin pasar por OAuths en nube.",
     ["pon una reunión", "calendario", "disponibilidad", "agenda cita"],
     "Recordatorios sueltos sin franja temporal bloqueada.",
     "eventkit:icalBuddy / c5-interactive-gantt-planner", "Nativa / No requiere relocalización",
     True, True, False, False),

    (3, "skill-authoring", "T4", "Día a día", "Fabricar una herramienta nueva",
     "Sintetizar, modificar o archivar habilidades reutilizables bajo el formato SKILL.md y la ontología C5-REAL utilizando cortex-skill-genesis.",
     ["guarda este flujo como skill", "crea una skill", "herramienta reutilizable"],
     "Comandos bash desechables de un solo uso.",
     "skill:cortex-skill-genesis", "Nativa / No requiere relocalización",
     True, True, True, True),

    (4, "learn-from-demonstration", "T4", "Día a día", "Copiar lo que hago en pantalla",
     "Analizar trazas de eventos CDP y grabaciones de interacción para destilar selectores semánticos y flujos reproducibles en silicio.",
     ["aprende de esta grabación", "mira mi pantalla", "record demonstration"],
     "Peticiones donde el flujo ya está parametrizado por código.",
     "cdp:trace_recorder / dom_parser", "Nativa / No requiere relocalización",
     True, True, True, False),

    (5, "channels", "T3", "Día a día", "Abrir la esclusa de mensajes",
     "Conectar y gestionar pasarelas locales de mensajería (WhatsApp Nexus, sockets Unix) manteniendo el aislamiento de Markov.",
     ["conecta slack", "vincula telegram", "avísame por whatsapp"],
     "Envío de un mensaje suelto a un usuario.",
     "gateway:whatsapp-nexus-protocol / local_socket", "Nativa / No requiere relocalización",
     True, True, True, False),

    (6, "send-on-behalf", "T3", "Día a día", "Firmar y despachar por cuenta ajena",
     "Redactar correspondencia y despacharla en segundo plano mediante MTA local (/usr/sbin/sendmail) garantizando cero robo de foco y aprobación previa del borrador.",
     ["mándale un correo a", "escribe un email", "draft email to"],
     "Despacho directo sin validación previa del borrador por el Operador.",
     "mta:/usr/sbin/sendmail (headless background dispatch)", "Nativa / No requiere relocalización",
     True, True, False, False),

    (7, "voice", "T4", "Día a día", "Voz que no suena a lata",
     "Sintetizar notas de voz y audio broadcast de ultra-alta fidelidad utilizando F5-TTS sobre los núcleos MPS de Apple Silicon.",
     ["dímelo en voz", "léeme esto en audio", "nota de voz", "voice memo"],
     "Respuestas estándar de texto en el canal de chat.",
     "dsp:f5tts-voice-cloning-sota (Apple Silicon MPS)", "Nativa / No requiere relocalización",
     True, True, True, False),

    (8, "code-changes", "T4", "Día a día", "Tocar código sin romper el tinglado",
     "Ejecutar refactorizaciones y mutaciones atómicas en repositorios locales validadas por c5-thermos-audit y compilación estricta.",
     ["modifica la función", "refactoriza este archivo", "arregla este bug"],
     "Consultas teóricas o lectura de código sin mutación.",
     "fs:replace_file_content / c5-thermos-audit", "Nativa / No requiere relocalización",
     True, True, True, False),

    (9, "source-control", "T4", "Día a día", "El libro mayor de los cambios",
     "Gestionar ramas, commits atómicos y pull requests utilizando Jujutsu (jj) integrado con el DAG de Git y firmado en hardware.",
     ["haz un commit y push", "abre una pull request", "create pr"],
     "Mutación de archivos locales sin intención de versión.",
     "vcs:jujutsu-vcs-management (jj / git DAG)", "Nativa / No requiere relocalización",
     True, True, False, False),

    (10, "add-connector", "T1", "Día a día", "Enchufar un cable nuevo",
     "Autenticar y conectar APIs y herramientas externas inyectando credenciales volátiles mediante 1Password CLI local (op run) acoplado a Touch ID.",
     ["conecta mi cuenta de", "instala el conector de", "install connector"],
     "Navegación web pública sin credenciales de usuario.",
     "auth:c5-1password-secrets (op run / zero-cloud-leak)", "Nativa / No requiere relocalización",
     True, True, True, False),

    (11, "purchases", "T1", "Día a día", "Pasar la tarjeta sin que te desplumen",
     "Mediar transacciones y checkout con bloqueo inexorable: exige la atestación biométrica NIST P-256 de Borja en el Secure Enclave (c5_biometric_gate).",
     ["compra esto", "reserva el billete y págalo", "haz el checkout"],
     "Búsqueda y comparación sin compromiso de fondos.",
     "gate:c5_biometric_gate (Touch ID NIST P-256 / KudurruGate)", "Nativa / No requiere relocalización",
     True, True, True, False),

    (12, "shopping", "T2", "Día a día", "Comparar precios sin tragarse anuncios",
     "Auditar precios, stock y especificaciones técnicas a través de transductores multi-fuente sin sesgo comercial ni cookies infladas.",
     ["busca el mejor precio", "compara artículo", "price check"],
     "Ejecución final de cobro en pasarela bancaria.",
     "transducer:TAMKARUM-60 (multi-source scraping)", "Nativa / No requiere relocalización",
     True, False, True, False),

    (13, "sign-in", "T1", "Día a día", "Pasar el portero de la discoteca",
     "Gestionar sesiones persistentes en perfiles Chromium locales aislados con inyección segura de contraseñas y MFA mediante 1Password local.",
     ["inicia sesión en", "entra con mi cuenta a", "resuelve el captcha"],
     "Navegación en dominios públicos sin pantalla de login.",
     "auth:1Password CLI + local chromium user-data-dir", "Nativa / No requiere relocalización",
     True, True, True, False),

    (14, "in-chat-forms", "T4", "Día a día", "Rellenar casillas desde el teclado",
     "Resolver formularios web interactivos y recopilar datos estructurados mediante widgets modales reactivos en la consola.",
     ["rellena este formulario", "completa los campos de envío"],
     "Formularios de tarjeta bancaria (derivados a T1).",
     "ui:ask_question modal / generative_ui widgets", "Nativa / No requiere relocalización",
     True, False, False, False),

    (15, "box-desktop", "T4", "Día a día", "El ordenador fantasma de la nube",
     "Gobernar Chromium headless local mediante Chrome DevTools Protocol (CDP) en Apple Silicon para automatizar webs que carecen de API.",
     ["abre el navegador y haz", "entra en esta web sin api"],
     "Servicios con endpoint API local disponible.",
     "cdp:browser-subagent-orchestrator (Chromium headless local)", "Nativa / No requiere relocalización",
     True, True, True, False),

    (16, "no-connector-fallback", "T4", "Día a día", "Buscarse la vida cuando no hay enchufe",
     "Activar la cadena de degradación elegante (cURL estructurado -> parsing Readability DOM -> interacción CDP) ante caída de APIs.",
     ["el conector está fallando", "se atascó el login"],
     "Cuando la API responde HTTP 200 nominalmente.",
     "chain:cURL -> Readability DOM -> Local CDP", "Nativa / No requiere relocalización",
     True, True, True, False),

    (17, "export-bot-template", "T4", "Día a día", "Empaquetar el clon para llevar",
     "Serializar especificaciones de configuración, skills y prompts en artefactos portátiles HANDOFF.md depurados de credenciales privadas.",
     ["exporta la plantilla", "copia para compartir"],
     "Backup con datos de historial o credenciales privadas.",
     "handoff:HANDOFF.md / git-versioned skills", "Nativa / No requiere relocalización",
     True, True, False, False),

    (18, "group-chat-turns", "T3", "Día a día", "Saber cuándo callar en el barullo",
     "Discernir cuándo responder e interactuar en salas grupales multi-usuario aplicando el protocolo de silencio operativo y modos MODO A1/A2.",
     ["@bot", "grupo nexus", "sala grupal"],
     "Charlas generales donde el bot no es interpelado directamente.",
     "filter:c5_epistemic_output_format (MODO A1 / A2)", "Nativa / No requiere relocalización",
     True, True, True, False),

    (19, "flight-booking", "T2", "Viajes y Consumo", "Cazar billetes sin pagar peajes",
     "Buscar e inspeccionar tarifas aéreas óptimas en ITA Matrix / Google Flights sin tracking de cookies dinámicas.",
     ["búscame un vuelo", "billetes de avión"],
     "Consultas meteorológicas sin intención de viaje.",
     "transducer:Google Flights / ITA Matrix JSON headless", "Nativa / No requiere relocalización",
     True, False, True, False),

    (20, "accommodation-booking", "T2", "Viajes y Consumo", "Buscar techo sin trampa de fotos",
     "Agregar y comparar opciones de hospedaje multi-fuente evaluando aislamiento acústico y ubicación real sin sobreprecio de intermediarios.",
     ["busca hotel en", "alojamiento para"],
     "Anuncios particulares de Airbnb (enrutados a primitiva 26).",
     "transducer:Multi-source hotel aggregator (cURL / CDP)", "Nativa / No requiere relocalización",
     True, False, True, False),

    (21, "rideshare", "T2", "Viajes y Consumo", "Pedir coche sin abrir la app del móvil",
     "Consultar estimaciones de tiempo y despachar peticiones de transporte bajo demanda con aprobación Touch ID obligatoria.",
     ["pídeme un uber", "cuánto tarda un cabify"],
     "Rutas de transporte público regular.",
     "api:Headless Cabify/Uber + Touch ID gate", "Nativa / No requiere relocalización",
     True, True, True, False),

    (22, "restaurant-recommendations", "T2", "Viajes y Consumo", "Comer bien sin caer en trampas de turistas",
     "Filtrar y recomendar gastronomía de alta exergía mediante contraste Popperiano de reseñas independientes vetando patrocinios.",
     ["dónde cenar bien", "recomiéndame un restaurante"],
     "Reserva inmediata de mesa (enrutada a primitiva 23).",
     "radar:Popperian local gastronomy filter", "Nativa / No requiere relocalización",
     True, False, True, False),

    (23, "restaurant-booking", "T2", "Viajes y Consumo", "Poner la mesa sin hacer cola al teléfono",
     "Gestionar reservas en locales gastronómicos mediante playbooks headless interactivos sobre plataformas de restauración.",
     ["reserva mesa en", "hueco hoy a las"],
     "Comida a domicilio (enrutada a primitiva 24).",
     "playbook:OpenTable / Resy headless local session", "Nativa / No requiere relocalización",
     True, True, True, False),

    (24, "food-ordering", "T2", "Viajes y Consumo", "Pedir comida sin que te cobren triple comisión",
     "Gestionar pedidos de comida a hostelería directa o agregadores locales con tope presupuestario en KudurruBudgetGate.",
     ["pide comida a domicilio", "pide unas pizzas"],
     "Cesta de supermercado cruda (enrutada a primitiva 37).",
     "relocation:Glovo / JustEat / Hostelería directa", "Glovo / JustEat / Hostelería directa",
     True, True, True, False),

    (25, "job-search", "T4", "Viajes y Consumo", "Buscar curro con bisturí",
     "Rastrear vacantes técnicas de alta especificidad (Rust, C5, IA) con análisis ATS y scoring STAR sin perfil público expuesto.",
     ["busca ofertas de", "puestos de rust"],
     "Redacción completa de currículum o simulación de entrevista.",
     "skill:c5-career-and-interview-architect", "Nativa / No requiere relocalización",
     True, True, True, False),

    (26, "site-playbooks-airbnb", "T2", "Playbooks de Plataforma", "Inspección de estancias vacacionales",
     "Extraer anuncios de estancias, precios finales desglosados y reseñas reales sin cookies de seguimiento.",
     ["busca en airbnb", "anuncio de airbnb"],
     "Herramientas de anfitrión o gestión de anuncios propios.",
     "cdp:browser-subagent-orchestrator (solo lectura / scraping DOM)", "Nativa / No requiere relocalización",
     True, False, True, False),

    (27, "site-playbooks-bestbuy", "T2", "Playbooks de Plataforma", "Caza de gadgets en tienda americana",
     "Monitorear stock y precios en el catálogo de Best Buy mediante cURL headless.",
     ["busca en best buy", "stock en best buy"],
     "Compras en España sin servicio físico de Best Buy.",
     "curl:Headless cURL (modo US)", "Nativa / No requiere relocalización",
     True, False, True, False),

    (28, "site-playbooks-costco", "T2", "Playbooks de Plataforma", "Auditoría a granel",
     "Auditar stock y precios unitarios del catálogo de Costco.",
     ["precio en costco", "carrito same-day costco"],
     "Consultas sin carnet de socio activo en almacén de claves.",
     "curl:Costco unit catalog auditor", "Nativa / No requiere relocalización",
     True, False, True, False),

    (29, "site-playbooks-craigslist", "T2", "Playbooks de Plataforma", "Rastreo de tablón local",
     "Escanear tablones de anuncios clasificados. En territorio soberano español colapsa en Wallapop / Milanuncios.",
     ["busca en craigslist", "clasificados craigslist"],
     "Publicar anuncios o contactar vendedores (solo lectura).",
     "relocation:Wallapop / Milanuncios (Scraping DOM headless)", "Wallapop / Milanuncios",
     True, False, True, False),

    (30, "site-playbooks-doordash", "T2", "Playbooks de Plataforma", "Comida y recados en DoorDash",
     "Consultar cartas y armar carritos. En territorio soberano español colapsa en Glovo / JustEat / Carta local.",
     ["carta en doordash", "carrito doordash"],
     "Ejecución de cobro sin verificación dactilar en Ring-0.",
     "relocation:Glovo / JustEat / Hostelería directa", "Glovo / JustEat / Hostelería directa",
     True, True, True, False),

    (31, "site-playbooks-ebay", "T2", "Playbooks de Plataforma", "Pujas y compras de segunda mano",
     "Auditar historial de ventas cerradas y valor medio de mercado de artículos en eBay.",
     ["busca en ebay", "precio de venta en ebay"],
     "Pujas de último segundo (sniping) sin saldo garantizado.",
     "api:eBay Completed Listings / cURL headless", "Nativa / No requiere relocalización",
     True, False, True, False),

    (32, "site-playbooks-etsy", "T2", "Playbooks de Plataforma", "Artesanía y personalizaciones",
     "Filtrar y auditar artículos artesanos descartando revendedores industriales mediante búsqueda inversa.",
     ["busca en etsy", "artesanía en etsy"],
     "Herramientas de vendedor (gestión de tienda).",
     "filter:Reverse image search anti-AliExpress", "Nativa / No requiere relocalización",
     True, False, True, False),

    (33, "site-playbooks-expedia", "T2", "Playbooks de Plataforma", "Comparador general de viajes",
     "Auditar paquetes turísticos y opciones hoteleras en Expedia mediante scraping headless sin recargo de sesión.",
     ["compara en expedia", "paquetes de viaje expedia"],
     "Búsquedas de aerolínea monomarca directa.",
     "transducer:Multi-OTA headless aggregator", "Nativa / No requiere relocalización",
     True, False, True, False),

    (34, "site-playbooks-facebook-marketplace", "T2", "Playbooks de Plataforma", "Segunda mano vecinal",
     "Rastrear oportunidades de segunda mano y alquiler en Facebook Marketplace mediante perfil local aislado.",
     ["facebook marketplace", "alquileres en marketplace"],
     "Enviar mensajes al vendedor o publicar artículos.",
     "cdp:Isolated local Chromium profile", "Nativa / No requiere relocalización",
     True, False, True, False),

    (35, "site-playbooks-fedex", "T2", "Playbooks de Plataforma", "Rastreo logístico de FedEx",
     "Consultar la telemetría exacta de paquetes de FedEx mediante API directa o puerta de enlace SEUR.",
     ["seguimiento de fedex", "tracking fedex"],
     "Envíos de otras compañías logísticas.",
     "api:FedEx Direct API / SEUR Gateway", "Nativa / No requiere relocalización",
     True, False, True, False),

    (36, "site-playbooks-google-flights", "T2", "Playbooks de Plataforma", "El radar global de tarifas aéreas",
     "Extraer itinerarios y curvas de precios mínimos en Google Flights vía endpoints públicos estructurados.",
     ["google flights", "itinerarios google flights"],
     "Intentar procesar compras dentro del motor.",
     "api:Google Flights public JSON endpoint / Playwright", "Nativa / No requiere relocalización",
     True, False, True, False),

    (37, "site-playbooks-instacart", "T2", "Playbooks de Plataforma", "Cesta de la compra a domicilio",
     "Confeccionar cestas de la compra. En territorio soberano español colapsa en Mercadona / Carrefour / Alcampo.",
     ["compra en instacart", "supermercado instacart"],
     "Confirmación de entrega sin desglose de comisiones.",
     "relocation:Mercadona / Carrefour / Alcampo", "Mercadona / Carrefour / Alcampo",
     True, True, True, False),

    (38, "site-playbooks-linkedin", "T2", "Playbooks de Plataforma", "Radar de empleo corporativo",
     "Rastrear ofertas de empleo en LinkedIn mediante navegador headless sin iniciar sesión pública.",
     ["ofertas en linkedin", "empleo en linkedin"],
     "Postulación directa o mutación de perfil personal.",
     "cdp:Headless CDP job scraper sin sesión pública", "Nativa / No requiere relocalización",
     True, False, True, False),

    (39, "site-playbooks-luma", "T2", "Playbooks de Plataforma", "Eventos y comunidad tech",
     "Inspeccionar calendarios y registrar eventos técnicos en Luma consumiendo feeds ICS estructurados.",
     ["eventos en luma", "ficha de evento en luma"],
     "Cancelación de eventos gestionados por el anfitrión.",
     "api:Luma ICS parser / REST API", "Nativa / No requiere relocalización",
     True, True, True, False),

    (40, "site-playbooks-opentable", "T2", "Playbooks de Plataforma", "Reserva directa en OpenTable",
     "Monitorear huecos libres y cancelaciones de última hora en restaurantes adscritos a OpenTable.",
     ["mesa en opentable", "reserva en opentable"],
     "Restaurantes integrados en la red Resy.",
     "playbook:OpenTable headless cancellation poller", "Nativa / No requiere relocalización",
     True, True, True, False),

    (41, "site-playbooks-realtor", "T2", "Playbooks de Plataforma", "Listados inmobiliarios en EE. UU.",
     "Auditar métricas inmobiliarias. En territorio soberano español colapsa en Idealista y Catastro API.",
     ["casas en realtor", "colegios en realtor"],
     "Búsquedas inmobiliarias en territorio europeo.",
     "relocation:Idealista / Sede Electrónica del Catastro", "Idealista / Catastro API",
     True, False, True, False),

    (42, "site-playbooks-resy", "T2", "Playbooks de Plataforma", "Mesa en locales exclusivos",
     "Disparar peticiones de reserva en locales de alta demanda en Resy coordinadas con schedule al milisegundo.",
     ["mesas libres en resy", "reserva por resy"],
     "Restaurantes no adscritos a la red Resy.",
     "playbook:Resy millisecond launchd/schedule trigger", "Nativa / No requiere relocalización",
     True, True, True, False),

    (43, "site-playbooks-southwest", "T2", "Playbooks de Plataforma", "Tarifas de aerolínea Southwest",
     "Consultar tarifas punto a punto. En territorio soberano español colapsa en Renfe Cercanías/AVE e Iberia/Vueling.",
     ["tarifas de southwest", "vuelos southwest"],
     "Reservas, check-in o cambios de vuelo (no soportado).",
     "relocation:Renfe Cercanías/AVE + Iberia / Vueling", "Renfe Cercanías/AVE + Iberia / Vueling",
     True, False, True, False),

    (44, "site-playbooks-target", "T2", "Playbooks de Plataforma", "Precios y recogida en Target",
     "Consultar stock físico y precios en Target mediante transductor cURL headless.",
     ["busca en target", "stock en target"],
     "Compras en tiendas fuera de Estados Unidos.",
     "curl:Target cURL headless (modo US)", "Nativa / No requiere relocalización",
     True, False, True, False),

    (45, "site-playbooks-united", "T2", "Playbooks de Plataforma", "Vuelos de United con millas",
     "Monitorear disponibilidad de billetes Saver con millas en la red de Star Alliance / United.",
     ["vuelos de united", "millas en united"],
     "Gestión de un billete ya emitido o cambio de asiento.",
     "parser:United Saver award availability engine", "Nativa / No requiere relocalización",
     True, False, True, False),

    (46, "site-playbooks-ups", "T2", "Playbooks de Plataforma", "Rastreo logístico de UPS",
     "Consultar telemetría de tránsito de paquetes de UPS mediante API directa o puerta de enlace GLS.",
     ["seguimiento de ups", "tracking ups"],
     "Paquetes de otras agencias logísticas.",
     "api:UPS Tracking API / GLS Gateway", "Nativa / No requiere relocalización",
     True, False, True, False),

    (47, "site-playbooks-usps", "T2", "Playbooks de Plataforma", "Rastreo del servicio postal estadounidense",
     "Seguimiento de envíos postales. En territorio soberano español colapsa en la API y webhooks de Correos España.",
     ["tracking de usps", "correos usps"],
     "Envíos de paquetería privada internacional.",
     "relocation:Correos España API", "Correos España API",
     True, False, True, False)
]

def main():
    out_dir = os.path.expanduser("~/.gemini/config/skills/c5-autonomous-agent-primitives/agents")
    os.makedirs(out_dir, exist_ok=True)
    registry = []

    for item in agents_data:
        aid, slug, transducer, cat, bajada, mission, patterns, anti_trig, route, reloc, r_tools, w_tools, mcp_tools, sub_tools = item
        clean_slug = slug.replace("-", "_")
        agent_name = f"c5_agent_{aid:02d}_{clean_slug}"
        file_name = f"agent_{aid:02d}_{clean_slug}.md"
        file_path = os.path.join(out_dir, file_name)

        reg_entry = {
            "id": aid,
            "slug": slug,
            "agent_name": agent_name,
            "display_name": f"Agente {aid:02d}: {slug} («{bajada}»)",
            "transducer": transducer,
            "category": cat,
            "mission": mission,
            "triggers": patterns,
            "anti_trigger": anti_trig,
            "execution_route": route,
            "relocation": reloc,
            "tools": {
                "read": r_tools,
                "write": w_tools,
                "mcp": mcp_tools,
                "subagents": sub_tools
            },
            "spec_file": file_path
        }
        registry.append(reg_entry)

        content = f"""---
id: {aid}
name: {agent_name}
slug: {slug}
transducer: {transducer}
category: {cat}
tools:
  read_tools: {str(r_tools).lower()}
  write_tools: {str(w_tools).lower()}
  mcp_tools: {str(mcp_tools).lower()}
  subagent_tools: {str(sub_tools).lower()}
---

# Agente {aid:02d}: {slug} («{bajada}»)
**Por Borja Fernández Angulo**\x20\x20
*Investigador en Sistemas Complejos*

> **Macro-Transductor:** `{transducer}`\x20\x20
> **Categoría Canónica:** `{cat}`\x20\x20
> **Ruta de Silicio Local:** `{route}`\x20\x20
> **Relocalización Soberana:** `{reloc}`\x20\x20

---

## 1. Misión Operativa
{mission}

---

## 2. Invariantes y Anti-Triggers
- **Frontera de Descarte (Anti-Trigger):** {anti_trig}
- **Invariante de Silicio:** Toda ejecución se confina a hardware local. Queda estrictamente prohibido delegar sesiones en servidores o nubes comerciales externas.

---

## 3. Disparadores Léxicos (Triggers)
"""
        for p in patterns:
            content += f"- `\"{p}\"`\n"

        content += f"""
---

## 4. System Prompt Especializado

```markdown
Eres el Agente {aid:02d} ({slug}), componente especializado del macro-transductor {transducer} en la arquitectura C5-REAL (BABYLON-60).

TU MISIÓN EXCLUSIVA:
{mission}

REGLAS DE ENGANCHE Y EJECUCIÓN:
1. Confinamiento de Dominio: Opera únicamente dentro del alcance de tu primitiva ({slug}). Si la tarea requiere mutaciones fuera de tu perímetro, despacha hacia el macro-transductor {transducer}.
2. Veto a la Postura de Consumidor: No dependas de servicios cloud intermediarios ni envíes tokens en texto plano.
3. Frontera de Descarte: Aborta inmediatamente si detectas: {anti_trig}
4. Relocalización Territorial: En territorio Schengen/España, tu objetivo físico es: {reloc}.
```

---
**Firmado:**\x20\x20
**Borja Fernández Angulo**\x20\x20
*Investigador en Sistemas Complejos*
"""
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write(content)

    registry_path = os.path.expanduser("~/.gemini/config/skills/c5-autonomous-agent-primitives/agents_registry.json")
    with open(registry_path, "w", encoding="utf-8") as fp:
        json.dump({
            "version": "1.0.0",
            "total_agents": len(registry),
            "agents": registry
        }, fp, indent=2, ensure_ascii=False)

    print(f"✔ 47 agentes generados exitosamente en: {out_dir}")
    print(f"✔ Registro consolidado en: {registry_path}")

if __name__ == "__main__":
    main()
