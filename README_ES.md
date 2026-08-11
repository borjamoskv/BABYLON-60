# BABYLON-60 v4.0 (Sovereign Hardened)

[🌐 Read in English](README.md)

**Infraestructura de Capa 0 para Agentes de IA Verificables & Cumplimiento Regulatorio del EU AI Act**

[![Version](https://img.shields.io/badge/Version-4.0.0--Sovereign--Hardened-black?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

[![Governance](https://img.shields.io/badge/Governance-C5--REAL-blue?style=for-the-badge)](./SECURITY.md)
[![License](https://img.shields.io/badge/License-Sovereign_Exclusion_v1.0-orange?style=for-the-badge)](./LICENSE)

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

## 📚 Arquitectura del Monorepo e Índice de Subproyectos

| Módulo del Subproyecto | Documentación README | Enfoque / Tecnología |
| :--- | :--- | :--- |
| **Rust Kernel** | [`kernel/`](./kernel/README.md) | Motor de ejecución `#![no_std]`, scheduler $F_{60}$, cuarentena WORM. |
| **Cortex Substrate** | [`cortex/`](./cortex/README.md) | Memoria cognitiva Python (`cortex-persist`), SQLite WAL, Servidor MCP. |
| **Sovereign IDE** | [`babylon60-ide/`](./babylon60-ide/README.md) | IDE Tauri v2 Escritorio/Móvil, backend FastAPI OpenRouter, IPC Iceoryx2. |
| **Web Telemetry UI** | [`web/`](./web/README.md) | Visualizador de telemetría React 18 + WASM y montado local via FSA API. |
| **Tonnetz Human Oversight**| [`tonnetz_app/`](./tonnetz_app/README.md) | Visualizador armónico tórico Neo-Riemanniano (EU AI Act Art. 14). |
| **Causal Attestation** | [`attestation/`](./attestation/README.md) | Notariado hardware TPM 2.0 PCR Quote y anclaje de raíz Merkle. |
| **DSL Compiler** | [`compiler/`](./compiler/README.md) | Lexer/Parser `.b60`, Bytecode IR B60, emisor de teoremas Lean 4. |
| **Strike RS Acceleration**| [`strike_rs/`](./strike_rs/README.md) | Bypass nativo del GIL PyO3, memoria compartida Iceoryx2, motor BLAKE3. |
| **Master Ledger BFT** | [`babylon60/bft/`](./babylon60/bft/README.md) | Log Tamper-Evident Escalón 3 con testigo externo Git Sentinel. |
| **EVM On-Chain Notary** | [`anvil_yung/`](./anvil_yung/README.md) | Smart contracts Foundry para notariado de raíz Merkle en EVM. |
| **Causal Transpiler** | [`causal_isomorphism/`](./causal_isomorphism/README.md)| Transpilador funcional F# y verificador de tipos lineales. |
| **Continuous Timeline IR** | [`timeline_ir/`](./timeline_ir/README.md) | Kernel de simulación de grafos de estado en tiempo continuo ($State(t)$). |
| **APEX Clinical Copilot** | [`docs/06_theory/`](./docs/06_theory/README_APEX.md) | Copiloto determinista de riesgo de enmiendas en ensayos clínicos. |
| **Documentation Hub** | [`docs/`](./docs/README.md) | Índice central de especificaciones, whitepapers y playbooks GTM. |

---

## 🕹️ Integración de Agentes y Consola de Mando (Antigravity & WA-Nexus)

BABYLON-60 se acopla directamente a tu stack de IA favorito para dotarlo de autonomía determinista, "Deep Research" (AUTODIDACT-Ω) y ejecución forzada a cero fricción (ULTRATHINK).

### 1. Inyección en LLMs (Model Context Protocol)
El kernel expone su arsenal de herramientas locales mediante el estándar MCP (`cortex_mcp_server.py`):
- **Para Claude Code y Cursor/Codex:** Soporte MCP nativo. Añade el servidor local en los settings para heredar la protección WORM.
- **Para ChatGPT (Web):** Exporta el arsenal de BABYLON-60 en formato JSON *OpenAPI* para operar el kernel desde la web.

### 2. Pasarela de Intervención (WA-Nexus)
Controla tus enjambres desde WhatsApp sin necesidad de estar frente al PC.
- **Mensajes Privados (DMs):** Intervención *Event-Driven* instantánea.
- **Grupos:** Requiere el disparador `Moskv-1` al inicio del mensaje para forzar una interrupción de hardware.
- **Asistencia del Kernel:** Escribe `Moskv-tips` para recibir consejos arquitectónicos.

### 3. Cheat Sheet: Directivas Termodinámicas y Slash Commands

- **⚡ Slash Commands:**
  - `/goal [tarea]` $\to$ Activa la ejecución masiva continua hasta cumplir el objetivo.
  - `/learn` $\to$ Cristaliza el contexto actual en memoria permanente.
  - `/schedule` $\to$ Programa un Cron Job agéntico (ej. auditar la red cada hora).
  - `/grill-me` $\to$ Modo Inquisidor. Entrevista iterativa para validar arquitecturas antes de programar.

- **🔥 Triggers Termodinámicos (Zero-Friction):**
  - `ULTRATHINK` $\to$ Obliga al modelo a colapsar su inferencia en código físico, eliminando la entropía generativa.
  - `purga anergia` $\to$ Protocolo de limpieza determinista para erradicar archivos zombie y código muerto.
  - `deep research` $\to$ Dispara el motor AUTODIDACT-Ω para investigación web ultra-profunda.

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

# 6. Verificar Teoremas Formales en Lean 4
lean BabylonTrace.lean
```

---

## 📜 Licencia

**Sovereign Exclusion License v1.0** — Modelo de Licencia Dual:

| Tier | Acceso | Requisito |
| :--- | :--- | :--- |
| **Sovereign** | Individuos, investigadores, uso no comercial | Libre — 100% Open Core |
| **Enterprise** | Corporaciones, uso comercial, producción | `CORTEX_LICENSE_KEY` criptográfica |

Ver detalles en [LICENSE](./LICENSE) y [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## 🔒 Seguridad

Para reportar vulnerabilidades: **security@babylon60.com** (No usar GitHub Issues públicos).  
Compromiso de respuesta: confirmación < 24h, remediación < 72h.  
Ver [SECURITY.md](./SECURITY.md) y [Threat Model v4.0](./docs/02_ontology/security_threat_model_v4.md).

---

<sub>BABYLON-60 v4.0.0 Sovereign Hardened · Infraestructura de Capa 0 para Agentes de IA Verificables · Borja Moskv</sub>
