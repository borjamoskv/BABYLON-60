igue  uv run babylon60-compliance --bundle artifact_bundle_v3 --locale es --format html --output cert_auditoria.html
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
