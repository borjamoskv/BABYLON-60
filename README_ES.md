# BABYLON-60 v4.0 (Sovereign Hardened)

**Infraestructura de Capa 0 para Agentes de IA Verificables & Cumplimiento Regulatorio del EU AI Act**

[![Version](https://img.shields.io/badge/Version-4.0.0--Sovereign--Hardened-black?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)
[![Security Rating](https://img.shields.io/badge/Security_Rating-A%2B-brightgreen?style=for-the-badge)](./docs/02_ontology/security_threat_model_v4.md)
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Articles_9--14_Compliant-purple?style=for-the-badge)](./docs/04_research/eu_ai_act_compliance_whitepaper.md)
[![Formal Verification](https://img.shields.io/badge/Lean_4-Verified-green?style=for-the-badge)](./BabylonTrace.lean)
[![Governance](https://img.shields.io/badge/Governance-C5--REAL-blue?style=for-the-badge)](./SECURITY.md)
[![License](https://img.shields.io/badge/License-Sovereign_Exclusion_v1.0-orange?style=for-the-badge)](./LICENSE.md)

> *"La mayoría de los sistemas de IA pueden generar texto. Pocos pueden justificar su historial."*

---

## ⚡ Demo Ejecutable en Vivo (5 Segundos)

Prueba el kernel en vivo, la sanitización criptográfica, la fallback por caída de red y la generación automática de certificados para la **AESIA (España)**, **BSI (Alemania)** y **Oficina de IA de la UE** ejecutando:

```bash
python3 scripts/run_hero_demo.py
```

---

## 🎯 El Problema: Por qué las Bases de Datos Vectoriales no son la Solución

En 2026, desplegar agentes de IA en banca, salud o defensa con bases de datos vectoriales (Pinecone, Milvus, Weaviate) crea un **pasivo legal inaceptable**:

| Lo que hace un Vector DB / Guardrail | Lo que exige un Auditor del EU AI Act | Consecuencia Legal |
| :--- | :--- | :--- |
| Encuentra texto semánticamente parecido | Prueba de fecha/hora de almacenamiento | Rechazado bajo Art. 10 (Gobernanza) |
| Devuelve los $K$ vecinos más cercanos | Cadena causal: qué datos produjeron esta decisión | Rechazado bajo Art. 9 (Gestión de Riesgos) |
| Filtra prompts probabilísticamente | Garantía inalterable de que el log no fue manipulado | Multas de hasta **€35M o 7% facturación** (Art. 12) |

**La similitud no es linaje.** Sin linaje causal verificable, los agentes sufren de *entropía generativa*: se desvían (*drift*) y dejan registros inútiles en un tribunal.

---

## 🛡️ La Solución: Substrato BABYLON-60 v4.0

BABYLON-60 es una **capa de gobernanza y ejecución "local-first" en Rust y Lean 4** que encapsula cualquier stack de agentes (LangChain, AutoGen, CrewAI, Ollama) bajo restricciones termodinámicas y criptográficas:

```
┌─────────────────────────────────────────────────────────────┐
│    Agentes & Orquestadores (LangChain / AutoGen / CrewAI)   │
├─────────────────────────────────────────────────────────────┤
│    LLMs Latentes (OpenAI / Claude / Mamba / Ollama)         │
├─────────────────────────────────────────────────────────────┤
│  ██ BABYLON-60 v4.0 SOVEREIGN HARDENED ██                   │
│  - Scheduler Sexagesimal Exacto F60 (0;20 exact)            │
│  - Ledger Merkle-Causal DAG (Tamper-Evident)                │
│  - Cuarentena Forense WORM (Write Once Read Many)           │
│  - Exporter EU AI Act i18n (AESIA / BSI / CNIL)             │
├─────────────────────────────────────────────────────────────┤
│  Enclave Seguro Hardware (TPM 2.0 / TEE / GPU bf16 Native)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💎 Fosos Tecnológicos (Moats)

### 1. Aritmética Sexagesimal Exacta (`F60`)
En `f64`, $1/3$ de hora es `0.33333...` — acumula *drift* catastrófico. En `F60`, es exactamente `0;20` (20 minutos exactos, cero *drift*). `F60` se aplica al **Scheduler y Ledger**, mientras los tensores GPU corren a velocidad nativa `bf16`.

### 2. Congelación Forense WORM (Write Once Read Many)
Las IA tradicionales alucinan o purgan logs al fallar. BABYLON-60 aplica un **Congelamiento Criptográfico Inmutable**: ante cualquier anomalía, el motor dispara `CRITICAL HALT` y congela el estado en `artifact_bundle_v3/quarantine/` firmado por hardware TPM 2.0. **Cero destrucción de evidencia.**

### 3. Verificación Formal con Lean 4
Teoremas matemáticos estáticos (`proof.ir` $\to$ `BabylonTrace.lean`) que demuestran que el kernel es matemáticamente incapaz de violar invariantes causales.

### 4. Certificación Multilingüe Automática (`compliance_exporter`)
Exportador integrado que genera certificados auditables para las autoridades de supervisión nacionales (AESIA en España, BSI en Alemania, CNIL en Francia, NIST en EE. UU.).

---

## 📚 Matriz Directoria de Documentación

| Dominio | Documento | Descripción |
| :--- | :--- | :--- |
| **Visión** | [Manifiesto Fundacional v4.0](./docs/00_MANIFESTO.md) | Tesis central, los 4 pilares del foso tecnológico, el ROI comercial y el Juramento del Ingeniero |
| **Investigación** | [EU AI Act Compliance Whitepaper](./docs/04_research/eu_ai_act_compliance_whitepaper.md) | Mapeo detallado para los Artículos 9, 10, 11, 12, 13 y 14 del Reglamento UE 2024/1689 |
| **Investigación** | [Technical Whitepaper v1.0](./docs/WHITEPAPER.md) | Paper formal: F60, Ledger Merkle DAG, Self-Falsification Engine, Proof IR |
| **Guías** | [Quickstart Enterprise](./docs/03_guides/QUICKSTART_ENTERPRISE.md) | Guía de onboarding DevOps en 5 mins para Docker Compose y Kubernetes/Helm |
| **Guías** | [Tutorial: Hola Mundo Causal](./docs/03_guides/tutorial_hello_causal.md) | Guía paso a paso contrastando BABYLON-60 vs Python/asyncio |
| **Guías** | [Guía Auditoría Armónica Tonnetz](./docs/03_guides/tonnetz_audit_guide.md) | Supervisión humana (Art. 14) vía red armónica espacial Neo-Riemanniana |
| **Seguridad** | [Threat Model & Mitigations v4.0](./docs/02_ontology/security_threat_model_v4.md) | Modelo de amenazas Fase II: Redacción criptográfica, Grace Period y Bounds |
| **Especificación**| [Especificación Formal v4.0](./SPECIFICATION.md) | Semántica operacional completa, ISA B60, Proof IR, Topology P2P |

---

## 🕹️ Integración de Agentes y Consola de Mando (Antigravity & WA-Nexus)

BABYLON-60 no es solo un kernel pasivo; se acopla directamente a tu stack de IA favorito para dotarlo de autonomía determinista, "Deep Research" (AUTODIDACT-Ω) y ejecución forzada a cero fricción (ULTRATHINK).

### 1. Inyección en LLMs (Model Context Protocol)
El kernel es agnóstico y expone su arsenal de herramientas locales mediante el estándar MCP (`cortex_mcp_server.py`):
- **Para Claude Code (Anthropic) y Cursor/Codex (OpenAI):** Soporte MCP nativo. Añade el servidor local en los *settings* (o usa `claude mcp add`) y tu IA heredará instantáneamente el escudo WORM Quarantine y la capacidad de ejecutar acciones físicas en tu máquina.
- **Para ChatGPT (Web):** Exporta el arsenal de BABYLON-60 en formato JSON *OpenAPI*, crea un Custom GPT e inyéctale el esquema para operar el kernel desde la web.

### 2. Pasarela de Intervención (WA-Nexus)
Controla tus enjambres desde WhatsApp sin necesidad de estar frente al PC.
- **Mensajes Privados (DMs):** Intervención *Event-Driven* instantánea. Escribe a la IA y responderá sin fricción.
- **Grupos:** Requiere el disparador `Moskv-1` al inicio del mensaje para forzar una interrupción de hardware y saltar el polling defensivo de 5 minutos.
- **Asistencia del Kernel:** Escribe `Moskv-tips` para recibir píldoras de sabiduría arquitectónica y buenas prácticas operativas.

### 3. Cheat Sheet: Directivas Termodinámicas y Slash Commands
Comandos ejecutables desde la interfaz del agente (Antigravity) para gobernar el enjambre:

- **⚡ Slash Commands:**
  - `/goal [tarea]` $\to$ Activa la ejecución masiva. El agente refactoriza o investiga sin descanso hasta cumplir el objetivo.
  - `/learn` $\to$ Cristaliza el contexto actual en memoria permanente. La IA lo integrará en su ADN para futuros despliegues.
  - `/schedule` $\to$ Programa un Cron Job agéntico (ej. auditar la red cada hora).
  - `/grill-me` $\to$ Modo Inquisidor. Entrevista iterativa para validar arquitecturas antes de escribir código.

- **🔥 Triggers Termodinámicos (Zero-Friction):**
  - `ULTRATHINK` $\to$ Obliga al modelo a colapsar su inferencia en código físico. Elimina la entropía generativa ("parloteo").
  - `purga anergia` $\to$ Protocolo de limpieza determinista para erradicar archivos zombie o código muerto.
  - `deep research` $\to$ Dispara el motor AUTODIDACT-Ω para investigación web ultra-profunda.

### 4. Setup *Zero-Friction* en Windows 10
Si no dispones de un entorno UNIX nativo (macOS/Linux), BABYLON-60 se despliega en Windows sin tocar variables de entorno:
1. Instala **Python 3.12** desde la **Microsoft Store** (autoconfigura el PATH).
2. Abre PowerShell / cmd y ejecuta: `pip install cortex-persist`.
3. Lanza la demo interactiva: `python -m babylon60.run_hero_demo`.

---

## 🗂️ Mapa del Monorepo

```
BABYLON-60/
├── babylon60.rs              # Kernel Causal-Determinist (bin: b60_kernel)
├── kernel/                   # Crate Rust: motor de bajo nivel y Cuarentena WORM
├── attestation/              # Crate Rust: anclaje PCR TPM 2.0 y notariado P2P
├── compiler/                 # Crate Rust: compilador B60 → IR + Lean 4 backend
├── runtime/                  # Crate Rust: runtime de corrutinas
├── proof_ir/                 # Crate Rust: representación intermedia de pruebas
├── strike_rs/                # Crate Rust: GIL bypass y extracción de exergía (PyO3)
├── fuzz/                     # Crate Rust: fuzzing diferencial
│
├── babylon60/                # Paquete Python principal (cortex-persist)
│   ├── compliance_exporter/  # Generador i18n de certificados EU AI Act (ES, EN, DE, FR, IT)
│   ├── attestation/          # Anclaje Merkle PCR Quote TPM 2.0 y notariado P2P
│   └── primitives/           # Serialization Boundary F60 → GPU bf16 con checksum SHA-256
│
├── causal_isomorphism/       # Transpilador F# → Rust/Solidity
├── timeline_ir/              # Backend de renderizado de IR temporal
│
├── web/                      # Interfaz web React + WASM
├── tonnetz_app/              # Visualizador espacial armónico Neo-Riemanniano (Art. 14)
├── babylon60-ide/            # IDE Soberano dedicado en Tauri v2 (macOS, Windows, Android, iOS, Linux)
│   ├── backend/              # Puente FastAPI (OpenRouter Nativo + Clasificador AUTO_SOTA + Arena de Comparación)
│   ├── frontend/             # Interfaz Industrial Noir React/Vite con Ruteador SOTA y Telemetría en Vivo
│   ├── src-tauri/            # Núcleo IPC Rust Multiplataforma con Iceoryx2 zero-copy
│   └── scripts/              # Pipeline de compilación ejecutable (`build_multiplatform.sh`)
│
├── hello_causal.b60          # Programa ejecutable de demostración DSL
├── BabylonTrace.lean         # Teoremas de causalidad verificados en Lean 4
├── tests/                    # 301 tests automatizados (pytest + cargo test)
├── scripts/                  # Herramientas CLI (run_hero_demo.py, export_country_compliance.py)
│
├── docs/                     # Portal completo de documentación y GTM (01-05)
│   ├── 01_spec/              # ESPECIFICACIÓN Y ARQUITECTURA
│   ├── 02_ontology/          # ONTOLOGÍA Y MODELO DE AMENAZAS V4
│   ├── 03_guides/            # TUTORIALES Y QUICKSTART ENTERPRISE
│   ├── 04_research/          # WHITEPAPERS TÉCNICOS Y NORMATIVOS
│   ├── 05_gtm/               # PLAYBOOK DE VENTAS, PITCH DECK Y VC DATA ROOM
│   └── audits/               # MUESTRAS DE CERTIFICADOS DE CUMPLIMIENTO (ES, EN, DE, FR, IT)
│
├── Cargo.toml                # Workspace Rust v4.0.0
├── pyproject.toml            # cortex-persist v4.0.0
├── SPECIFICATION.md          # Especificación formal v4.0
├── LICENSE.md                # Sovereign Exclusion License v1.0
└── SECURITY.md               # Política de seguridad soberana
```

---

## 🛠️ Quick Start

```bash
# 1. Ejecutar Demo Interactiva Hero en Vivo
python3 scripts/run_hero_demo.py

# 2. Generar Certificado de Cumplimiento para España (AESIA)
python3 scripts/export_country_compliance.py --locale es --output docs/audits/CERTIFICADO_ES.md

# 3. Ejecutar Suite de Tests (301 Tests)
uv run pytest tests/ -v

# 4. Compilar Workspace Rust
cargo test --workspace

# 5. BABYLON IDE v0.4.0 (Instalables Multiplataforma Escritorio y Móvil)
cd babylon60-ide
npm run dev           # Iniciar IDE en Desarrollo
npm run build:mac     # Compilar ejecutable macOS (.dmg / .app)
npm run build:win     # Compilar instalador Windows (.msi / .exe NSIS)
npm run build:android # Compilar paquete Android (.apk / .aab)
npm run build:ios     # Compilar aplicación iOS (.app / .ipa)

lean BabylonTrace.lean
```


---

## 📜 Licencia

**Sovereign Exclusion License v1.0** — Modelo de Licencia Dual:

| Tier | Acceso | Requisito |
| :--- | :--- | :--- |
| **Sovereign** | Individuos, investigadores, uso no comercial | Libre — 100% Open Core |
| **Enterprise** | Corporaciones, uso comercial, producción | `CORTEX_LICENSE_KEY` criptográfica |

Ver detalles en [LICENSE.md](./LICENSE.md) y [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## 🔒 Seguridad

Para reportar vulnerabilidades: **security@babylon60.com** (No usar GitHub Issues públicos).  
Compromiso de respuesta: confirmación < 24h, remediación < 72h.  
Ver [SECURITY.md](./SECURITY.md) y [Threat Model v4.0](./docs/02_ontology/security_threat_model_v4.md).

---

<sub>BABYLON-60 v4.0.0 Sovereign Hardened · Infraestructura de Capa 0 para Agentes de IA Verificables · Borja Moskv</sub>
