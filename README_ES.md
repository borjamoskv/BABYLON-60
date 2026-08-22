# BABYLON-60

[🌐 Read in English](README.md)

**La "Caja Negra Criptográfica" de registro local para agentes de IA autónomos.**

[![Version](https://img.shields.io/badge/versión-4.0.0-black?style=flat-square)](https://github.com/borjamoskv/BABYLON-60)
[![Licencia](https://img.shields.io/badge/licencia-Soberana_Dual--License-orange?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.10-blue?style=flat-square)](./pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-≥1.77-orange?style=flat-square)](./Cargo.toml)
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Artículos_9--14_Cumplimiento-purple?style=flat-square)](./docs/04_research/eu_ai_act_compliance_whitepaper.md)

---

## ⏱️ Resumen en 10 Segundos

**¿Qué es?**  
Al igual que los aviones utilizan una caja negra para registrar la telemetría de vuelo, **BABYLON-60** es un libro de registro local e inalterable para agentes de IA. Cada decisión, llamada a herramienta y respuesta de prompt que ejecuta tu agente se encadena criptográficamente y se sella en una base de datos local.

**¿Por qué lo necesitas?**  
Cuando un agente autónomo ejecuta acciones en producción (ej. ejecutar código, realizar pedidos, leer archivos), necesitas **pruebas irrefutables de lo que sucedió** que no se puedan alterar retroactivamente. BABYLON-60 te proporciona auditabilidad automatizada y cumplimiento regulatorio (EU AI Act) sin dependencia de servicios en la nube.

---

## 💡 Desmitificando la Jerga (Glosario Pedagógico)

Si es tu primera vez trabajando con ledgers de auditoría o sistemas de bajo nivel, aquí tienes la traducción de los términos clave:

| Término Técnico | Analogía Sencilla | Cómo lo Usa BABYLON-60 |
| :--- | :--- | :--- |
| **Tamper-evident** | **Pegatina de Sello de Garantía:** Puedes abrir un bote, pero el sello roto demuestra que fue manipulado. | Si alguien edita registros pasados del agente en la base de datos, la cadena de hashes se rompe al instante y te alerta. |
| **Hash Chain (Cadena de Hashes)** | **Fila de Dominó:** La posición de cada ficha depende exactamente de la anterior. | Cada evento del agente incluye la huella digital SHA3-256 del evento previo. |
| **Single-writer WAL** | **Ventanilla Única de Registro:** Solo una persona escribe en el libro a la vez para evitar desorden. | Utiliza SQLite Write-Ahead Logging para garantizar cero corrupción de datos en ejecución concurrente. |
| **Reloj de Lamport** | **Ticket de Turno Numerado:** Define objetivamente qué evento ocurrió antes que cuál. | Impone un orden cronológico causal estricto entre las acciones del agente. |
| **Local-First** | **Caja Fuerte Local:** Todos los datos permanecen en tu propia máquina (`$BABYLON_HOME/`). | Sin servidores ni dependencias en la nube, soberanía total de datos. |

---

## ⚡ Inicio Rápido en 3 Pasos

### Paso 1: Instalación y Configuración del Entorno

```bash
git clone https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60

# Configurar el directorio raíz obligatorio para bases de datos
export BABYLON_HOME="$HOME/.babylon60"
mkdir -p "$BABYLON_HOME"

# Instalar dependencias de Python (se recomienda uv)
uv sync

# (Opcional) Verificar el kernel en Rust
cargo test --workspace
```

### Paso 2: Ejecutar la Demo Interactiva

Ejecuta la demo para observar el registro de eventos, la redacción automática de PII y la generación de certificados de cumplimiento:

```bash
PYTHONPATH=packages python3 scripts/c5_demos/run_hero_demo.py
```

### Paso 3: Registrar un Evento (API de Python en 5 Líneas)

Envuelve la lógica de tu agente de IA con 5 líneas de código:

```python
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

# 1. Inicializar el ledger local
ledger = CortexPersistLedger("$BABYLON_HOME/dbs/mi_agente.db")

# 2. Registrar una decisión del agente
event = CortexEvent(
    event_type="AGENT_ACTION",
    payload={"tool": "sql_query", "query": "SELECT * FROM usuarios"},
    cortex_taint="session:abc123"
)
ledger.append(event)

# 3. Verificar que nadie ha alterado el historial
assert ledger.verify_integrity() == True
```

---

## 🎯 ¿Para Quién es BABYLON-60?

### 🤖 Desarrolladores e Ingenieros de IA
- **Problema:** Depurar flujos no deterministas de agentes o demostrar que una alucinación no fue causada por código humano.
- **Solución:** Cada prompt, salida de herramienta y transición de estado queda registrada en una secuencia append-only con validación por `verify_integrity()`.

### 🏛️ Responsables de Cumplimiento y Legal (EU AI Act)
- **Problema:** Los Artículos 9 a 14 del EU AI Act exigen documentación técnica, registros de auditoría y supervisión humana para IA de alto riesgo.
- **Solución:** Exporta certificados de auditoría regulatorios con un solo comando CLI:
  ```bash
  uv run babylon60-compliance --bundle artifact_bundle_v3 --locale es --format html --output cert_auditoria.html
  ```

### 🔒 Equipos de Seguridad y Análisis Forense
- **Problema:** Evitar que ataques de *prompt injection* o procesos maliciosos alteren la memoria histórica del agente.
- **Solución:** Triggers a nivel de motor de base de datos bloquean consultas `UPDATE` y `DELETE`, respaldados por un slot IPC fail-stop en Rust (`SharedManifest`).

---

## 🏗️ Visión General de la Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│    Tu Framework de Agentes (LangChain / AutoGen / CrewAI / Ollama / Custom) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Registrar Evento / Acción
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Capa de Responsabilidad BABYLON-60                      │
│                                                                             │
│   🐍 Núcleo Python (packages/babylon60/)                                    │
│   ├── bft/                 Ledger con Cadena de Hashes (SHA3-256)           │
│   ├── crypto/              AES-256-GCM, Ed25519 y Registro de Hashes        │
│   ├── database/            Conector SQLite/WAL Single-Writer                │
│   ├── attestation/         Anclaje de Estado en Merkle DAG                  │
│   └── compliance_exporter/ Generador de Certificados EU AI Act              │
│                                                                             │
│   🦀 Kernel Rust (src/ + crates/)                                           │
│   ├── SharedManifest       Slot IPC Lock-Free en Memoria Compartida (64 B)   │
│   ├── seqlock              Lectores Concurrentes de Cero Contención        │
│   └── halt                 Interruptor de Parada Segura (Fail-Stop)        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Escritura Cifrada y Encadenada
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│             Base de Datos SQLite WAL Local ($BABYLON_HOME/dbs/)             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Matriz de Seguridad e Integridad

| Característica | Cómo Funciona | Qué Previene / Protege |
| :--- | :--- | :--- |
| **Cadena de Hashes** | Cada entrada almacena `SHA3-256(hash_anterior + datos_actuales)`. | Previene la alteración o reordenamiento retroactivo de logs. |
| **Triggers Inmutables** | Triggers `BEFORE UPDATE` y `BEFORE DELETE` en SQLite lanzan excepciones SQL. | Previene modificaciones accidentales o maliciosas vía consultas SQL directas. |
| **Single-Writer WAL** | Modo estricto `PRAGMA journal_mode=WAL` con `busy_timeout=5000ms`. | Previene corrupción de base de datos o bloqueos bajo alta concurrencia. |
| **Testigos Externos** | Git Sentinel inyecta marcadores `Ledger-Head` y `Ledger-Seq` en los commits. | Permite verificación externa mediante runners de CI/CD. |

---

## 📂 Estructura del Monorepo

```
BABYLON-60/
├── packages/
│   ├── babylon60/         # Motor core en Python (ledger, criptografía, DB, cumplimiento)
│   └── cortex/            # Substrato de memoria cognitiva e integración MCP Server
├── crates/
│   ├── babylon60-kernel/  # Kernel de ejecución de bajo nivel en Rust #![no_std]
│   ├── babylon60-compiler/# Parser DSL .b60 y emisor de demostraciones Lean 4
│   └── strike-rs/         # Bridge nativo PyO3 Rust-Python y memoria compartida
├── apps/
│   ├── babylon60-ide/     # IDE de escritorio en Tauri v2 para desarrolladores
│   ├── web/               # Visualizador de telemetría en React 18
│   └── tonnetz_app/       # Visualizador armónico Neo-Riemanniano (EU AI Act Art. 14)
├── scripts/               # Demos, suites de benchmark y herramientas CLI de verificación
├── docs/                  # Especificaciones, whitepapers y guías regulatorias
└── proof/                 # Demostraciones matemáticas formales en Lean 4
```

---

## ⚙️ Configuración y Variables de Entorno

| Variable | Requerida | Valor por Defecto | Propósito |
| :--- | :---: | :--- | :--- |
| `BABYLON_HOME` | **Sí** | *Ninguno* | Directorio raíz para bases de datos (`$BABYLON_HOME/dbs/`). Debe establecerse explícitamente. |
| `BABYLON60_LICENSE_KEY` | Comercial | *Ninguno* | Clave de licencia criptográfica Enterprise. |
| `BABYLON60_LICENSE_SALT` | Comercial | *Ninguno* | Salt secreto HMAC para verificación de licencias. |

---

## 🧪 Pruebas y Verificación

```bash
# Ejecutar suite de pruebas de Python (377+ tests)
export BABYLON_HOME=/tmp/babylon_test
uv run pytest tests/ -v

# Ejecutar pruebas del workspace de Rust
cargo test --workspace

# Ejecutar verificación completa de calidad (lint + format + typecheck + tests)
make all
```

---

## 📄 Licencia y Soporte Comercial

**Licencia Soberana Dual v4.0:**
- **Nivel Soberano:** Gratuito y Open Core para personas, investigadores y proyectos no comerciales.
- **Nivel Enterprise:** Requerido para despliegues comerciales en producción. Contactar para claves de licencia corporativas.

Ver [LICENSE](./LICENSE) y [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## 🛡️ Reporte de Vulnerabilidades de Seguridad

Reporta problemas de seguridad confidencialmente a **security@babylon60.com**. No abras issues públicos en GitHub para vulnerabilidades.  
*SLA de respuesta: Acuse de recibo < 24 horas, Parche < 72 horas.* Ver [SECURITY.md](./SECURITY.md).

---

<sub>BABYLON-60 v4.0.0 · Ledger Criptográfico para Agentes de IA Autónomos · Borja Moskv</sub>
