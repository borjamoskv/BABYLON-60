# Auditoría de Exposición Topológica (Repositorios Públicos vs. Privados)

![Status: C5-REAL](https://img.shields.io/badge/Status-C5--REAL-black?style=flat-square&logo=rust&logoColor=white)


**Fecha de Fijación Causal:** 2026-09-12  
**Marco Epistémico:** C5-REAL v4.3 / Zero-Trust Architecture / Open-Core Sovereignty  
**Objetivo:** Determinar la política estricta de visibilidad (Público/Privado) para el ecosistema de repositorios del usuario, minimizando la superficie de ataque y garantizando la verificabilidad de los axiomas.

---

## 1. Topología Pública (La Superficie de Atestación)

Estos repositorios **DEBEN ser PÚBLICOS**. Constituyen el contrato termodinámico con el exterior, el *Open Core* y la prueba criptográfica de que el sistema opera como se describe. Ocultarlos destruye la confianza y convierte los axiomas en dogma inauditable.

| Repositorio | Función Topológica | Justificación de Alta Exergía |
|---|---|---|
| **`BABYLON-60`** | Motor de Ejecución, Ledger L1 (BFT) y Orquestador | **Obligatorio Público.** Bajo la *Licencia Dual Soberana v4.0*, el código (Rust C-ABI, Python) y los *smart contracts* de atestación deben ser escrutables. Si el motor físico de Ring-0 es cerrado, las atestaciones Merkle carecen de validez epistémica para terceros. |
| **`C5-RESEARCH-FOUNDATIONS`** | Corpus teórico, matemático, de ciencias cognitivas y manifiestos (opcional). | **Recomendado Público.** Separado de BABYLON-60 (Límite Topológico del Workspace). Es la biblioteca del "mapa". Publicarlo facilita la revisión por pares, divulgación académica y citación (preprints/ensayos). |

> [!WARNING]
> **Invariante de Pureza Pública:**  
> Ningún repositorio público puede contener secretos (APIs, `.env`), bases de datos SQLite operativas (`*.db`, `*.db-wal`), documentos de marketing/Go-To-Market (OpSec), borradores de redes sociales, ni perfiles biométricos (`TouchID`). Todo archivo en la rama `main` pública debe tener valor puramente estructural o axiomático.

---

## 2. Topología Privada (Los Enclaves Soberanos)

Estos repositorios y bóvedas **DEBEN ser ESTRICTAMENTE PRIVADOS**. Contienen secretos de estado, infraestructura táctica, claves asimétricas o investigación en fase de incubación que aún no es termodinámicamente estable.

| Repositorio / Bóveda | Función Topológica | Justificación Zero-Trust |
|---|---|---|
| **`Teorema-Robinson-Moskv`** | Enclave de Incubación Matemática | **Privado.** Como se estableció en la revisión `[AX-11]`, es un laboratorio de formalización Lean 4. Las pruebas ya estables se exfiltran y embeben en la carpeta pública `BABYLON-60/proof/` para evitar que el ruido del desarrollo (*WIP*) ensucie la atestación pública. |
| **`20_VAULT/wa-nexus`** | Pasarela WhatsApp de Ring-0 | **Privado (Requerido).** Contiene dependencias directas a SQLite de macOS (CoreData), y su ejecución produce las credenciales asimétricas de Noise Protocol en `cortex_auth_info/`. Publicar este repositorio asume un riesgo crítico de filtración accidental de sesiones o claves privadas. |
| **Bóvedas Criptográficas** (`moskv1_bot_auth/`, `~/.gemini/`) | Identidad, Firmas Ed25519, Telemetría | **Exclusión Git Absoluta.** Nunca deben versionarse ni siquiera en repositorios privados (riesgo de exfiltración por tokens comprometidos). |
| **Repositorios de GTM y OpSec** | Estrategia Comercial, Captación | **Privado / Local.** Conforme a la regla de *Segregación Estricta GTM / OpSec*, todo análisis de algoritmos de captación, *astroturfing* o despliegue comercial se aísla de BABYLON-60 para proteger la soberanía técnica del código de acusaciones de manipulación. |

---

## 3. Topología de Código vs. Topología de Instancia

Para resolver el falso dilema de "si es público me pueden hackear":

1. **El Código es Público (`BABYLON-60`):** Cualquiera puede leer la arquitectura de `SharedManifest`, el puente NAPI-RS o los filtros SQLite.
2. **La Instancia es Privada (Tu Nodo Moskv-1):** Los tokens, las bases de datos `cortex.db` reales con la memoria episódica, y las llaves de WhatsApp viven fuera de control de versiones, protegidos por el cerrojo biométrico (`c5_biometric_gate`) de tu Apple Silicon. 

### Dictamen Final
Mantén **BABYLON-60 público** (como *Open Core* y motor fundacional) y **purga cualquier traza de configuración personal** para que funcione con el estándar corporativo (INV_C5_SHM). Todo lo referente a *wa-nexus* activo, pruebas matemáticas inestables (*Teorema-Robinson-Moskv*) y documentos de captación/negocio debe encapsularse en enclaves privados o bóvedas locales.
