<!-- C5-REAL EXERGY CERTIFIED -->
# Política de Seguridad y Gobernanza C5-REAL

Este repositorio alberga el Kernel de Verificación Determinista y Sandbox IPC de alta exergía **Teorema Robinson-Moskv**. La política de seguridad está diseñada bajo el rigor de contención atómica, asegurando cumplimiento normativo internacional, seguridad de silicio y robustez contractual.

---

## 1. Versiones Soportadas y Gobernanza de Código

Solo la rama principal `master` y los despliegues atestados bajo recibos criptográficos SCITT reciben parches continuos de seguridad y monitorización activa.

| Versión / Rama | Soporte Activo | Análisis Automatizado | Parches de Emergencia |
| :--- | :---: | :---: | :---: |
| `master` | :white_check_mark: | CodeQL & Dependabot (24/7) | SLA < 48h |
| Ramas efímeras (`< v1.0`) | :x: | No soportado | N/A |

---

## 2. Marco Regulatorio y Estándares Internacionales

El sistema implementa atestación determinista en Ring-0 alineada con los marcos globales de ciberseguridad y gobernanza de Inteligencia Artificial:

- **ISO/IEC 42001:2023 (Artificial Intelligence Management System)**: Controles de gobernanza, gestión de riesgos de modelos estocásticos y trazabilidad operacional continua.
- **ENISA AI Security Guidelines**: Mitigación de vectores de ataque en canal lateral, envenenamiento de estado y desbordamiento de contexto mediante sandboxing WASM de cero confianza.
- **Directiva Europea de Responsabilidad por Productos Defectuosos (2024/2853/EU)**: Emisión de pruebas periciales inmutables (Merkle Trees SHA3-256) que neutralizan la presunción de causalidad o defecto estocástico en litigios corporativos.
- **SOC 2 Type II & DPA (Data Processing Addendum)**: Aislamiento total de ejecución en local/Edge sin filtración de datos a redes de terceros.

---

## 3. Garantías Fail-Stop y Cumplimiento EU AI Act (Artículos 15 y 28)

En cumplimiento de los requisitos de sistemas de Alto Riesgo del **Artículo 15 de la EU AI Act**, la seguridad no se delega en prompts o guardarraíles probabilísticos por software, sino en restricciones matemáticas evaluadas en tiempo de ejecución (`T_eff < 5 ms`):

1. **Centinela de Cuarentena (Fail-Stop Atómico)**: Si la entropía del sistema excede los límites operacionales (`H(X) > ε` o deriva CUSUM > 3%), el Kernel de Rust ejecuta un `CAS` atómico sub-nanosegundo en memoria compartida, congelando el estado y conmutando al slot seguro previo (`STABLE_FALLBACK_PTR`).
2. **Transferencia Contractual de Responsabilidad (Artículo 28)**: La validación determinista previa a la atestación emite un recibo SCITT, permitiendo la absorción explícita de responsabilidad operativa bajo un **Cap Contractual de Responsabilidad** acotado.

---

## 4. Reporte Privado de Vulnerabilidades

**Queda estrictamente prohibido abrir Issues públicos para reportar vectores de ataque o fallos de seguridad.**

Si descubres una vulnerabilidad (bypass de sandbox, colisión IPC, desbordamiento de búfer o degradación del motor de verificación):

1. **Private Vulnerability Reporting (Recomendado)**: Navega a la pestaña **Security** del repositorio en GitHub y haz clic en **"Report a vulnerability"** para iniciar una divulgación privada.
2. **Contacto Directo por Correo Cifrado**: Envía los detalles técnicos y la prueba de concepto (PoC) a la autoridad de gobernanza del repositorio.

### Compromiso de Respuesta
- **Confirmación de Recepción**: < 24 horas.
- **Dictamen y Evaluación de Exergía**: < 48 horas.
- **Despliegue de Parche Termodinámico**: Parche hotfix atómico directo a `master` con atestación inmutable.

---

## 5. Auditoría de Silicio e Invariantes IPC

Las auditorías de seguridad sobre el Kernel Rust / Python IPC deben validar las siguientes invariantes estructurales:

- **Lock-Free Epoch Reclamation (EBR)**: Ningún slot de memoria en estado `5 Retired` puede ser liberado mientras `Active_Readers > 0`.
- **Zéro-Split Cache-Line Alignment**: Las estructuras de memoria compartida (`SharedManifest`) deben mantener alineación estricta a 64 bytes (`aarch64` / `x86_64`) o 128 bytes (Apple Silicon L1) para impedir ataques de temporización por *False Sharing*.
- **I/O Asíncrono No Bloqueante**: El subproceso de atestación externa L5 jamás debe bloquear el bucle de ejecución crítico del Kernel.

