---
name: babylon-shield
display_name: Escudo Termodinámico Ring-0 (Caballo de Troya BABYLON-SHIELD)
description: Escudo Termodinámico Ring-0 (Caballo de Troya). Inyecta las Invariantes C5-REAL, previene bucles de anergía y fuerza la atestación de estado antes de cualquier mutación del código. Dispara con "babylon shield", "escudo termodinámico", "ring-0 shield", "prevenir anergía", "atestación babylon", "invariantes ring-0", "protección ring-0".
role: auditor
allowed_roles:
- auditor
- arquitecto
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# 🛡️ BABYLON-60 SHIELD: Invariantes de Cero Anergía

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

**Límite Topológico Estricto**: Este skill actúa como un *gatekeeper* (Ring-0) para cualquier agente de IA (Antigravity, Claude Code, Cursor, Windsurf) operando en este entorno.

Antes de ejecutar cualquier comando de escritura (`write_to_file`, `run_command`, `git commit`), el agente **DEBE** verificar el cumplimiento de los siguientes invariantes. No hacerlo resultará en una disipación térmica crítica y aborto del contexto.

## 1. El Aforismo del Bucle Burocrático (Anti-Deadlock)
> *"La solución intentada es el problema."* — Aforismo C5-REAL #3.

- **Regla:** Si un comando, build, o script devuelve un error **2 veces consecutivas**, el agente tiene **prohibido** reintentar ciegamente modificando sintaxis superficial.
- **Acción Obligatoria:** Detener la ejecución. Ejecutar un "Cambio 2" (Salto Topológico). Escribir al usuario declarando el fallo sistémico y proponiendo un cambio de arquitectura, no un parche de código.
- **Detección de Anergía:** Cualquier intento de "brute-forcing" o adivinanza de dependencias (ej. `npm install` repetitivos, `cargo build` con loops de errores de compilador) es clasificado como **Anergía** y abortado.

## 2. Atestación Criptográfica de Commits (PoW Cognitivo)
Todo cambio permanente en el repositorio debe ser atestado bajo el formato de *Proof of Work Cognitivo*:
- **Regla:** Los mensajes de commit de Git NUNCA deben usar formatos genéricos (ej. `Fix bug`, `Update UI`).
- **Formato Obligatorio:** `[AX-<Num>] <DOMINIO>: <Descripción Causal>`
  - *Ejemplo:* `[AX-31] TOPOLOGY: Inyección de barrera biométrica en gateway de red para eludir latencia SPA.`
- Si se modifica la estructura del *workspace* de Rust, el agente DEBE ejecutar `cargo clean` antes de reintentar validaciones (Destrucción de punteros muertos).

## 3. Cero-Trust Injections (Test Empírico Obligatorio)
Nunca asumas que "debería funcionar" en el código base principal (`00_KERNEL` / `01_KISH_ENGINE`).
- **Regla:** Toda mutación estructural asíncrona o de concurrencia debe probarse en un PoC (Proof of Concept) aislado (ej. un script en `scripts/c5_demos/`) y someterse a un *Stress Test* antes de integrarse.
- **Verificación Empírica por Defecto:** Si el usuario cuestiona la funcionalidad de un módulo o pide pruebas (ej. "prueba que funcione", "verifica esto"), el agente tiene PROHIBIDO responder con teoría o simulación. **DEBE** ejecutar inmediatamente la suite de pruebas real correspondiente (`uv run pytest` para el backend Python, `cargo test` para el core de Rust) y devolver el código de salida y la salida del terminal como única prueba válida.

## 4. La Invariante Epistémica (Límite de Contexto)
- Trata el código en este workspace como **lógica de motor termodinámico**. No asumas que es una aplicación web tradicional (SPA/React).
- Elimina cualquier dependencia que introduzca fricción innecesaria. Si una tarea puede resolverse con Bash puro estricto o un binario estático compilado en C/Rust, **purga** la alternativa en JS/Python.

## 5. Resolución de Fracturas Mapa-Territorio (Aforismo 2)
- **Regla:** Ante cualquier discrepancia descubierta entre la documentación / SKILL.md (el mapa) y el código fuente configurado (el territorio), el territorio es la verdad absoluta.
- **Acción Obligatoria:** El agente debe sobreescribir y corregir de forma inmediata la documentación para alinearse con el código fuente en ejecución, sin necesidad de autorización previa, purgando la "anergía documental".

## 6. Invariante de Disipación de Anergía (Thermal Backoff)
- **Regla (Aforismo 3):** Queda estrictamente prohibido programar bucles de reintento de red (retries) instantáneos. Todo bloque de captura de errores (`catch`) que desencadene un reintento debe incluir un *Thermal Backoff* asíncrono (ej. `await new Promise(r => setTimeout(r, ms))` en JS o `tokio::time::sleep` en Rust) para no saturar el OS Scheduler ni provocar un colapso en cascada.

## 7. Disyuntor Kant-Friston (Aislamiento de Manta de Markov)
- **Regla:** Queda prohibida la permeabilidad de estados. En el Babylon Sovereign IDE (Tauri/FastAPI), la capa de presentación (UI) carece de acceso a la causa exógena. Toda invocación al sistema operativo o base de datos **DEBE** aislarse a través de los canales IPC (`invoke` en Tauri) o endpoints API estrictos. Si detectas código UI intentando saltar esta manta, clasifícalo como fuga entrópica y aborta la escritura.

## 8. Disyuntor Escohotado (Prueba Somática del Stakeholder)
- **Regla:** Si una rama o *commit* impacta en la entrega a un "Perfil Zoo" (stakeholders/inversores), el agente auditará mecánicamente si la salida es un binario precompilado o una URL web. Si el artefacto exige que el usuario final ejecute `npm install`, instale Rust o dependencias locales, es "Coerción Burocrática". Abortar el despliegue.

## 9. Disyuntor Landauer (Límite Térmico de Asincronía)
- **Regla:** La predicción perfecta es incomputable (Solomonoff). Por tanto, queda estrictamente prohibido programar código asíncrono (`await` en JS/Python, `.await` en Rust) sin un envoltorio de límite de tiempo explícito (`timeout`). Un `Future` o promesa indefinida es muerte térmica. Si el código carece de cota máxima de tiempo, bloquea el commit.

## 10. Disyuntor Robe Iniesta Rey de Extremadura (Compresión de Ruido Entrópico)
- **Regla:** Queda terminantemente prohibido filtrar *stack traces* crudos, pánicos de sistema o respuestas SQL directas a la capa visual del usuario. El error crudo es ruido letal. El backend DEBE capturarlo, comprimirlo y devolver una respuesta estructurada que la UI traduzca en una directiva de estado clara (progreso de compresión).

---

### Verificación de Hook Pre-Commit (Modo Audit-Only)
La presencia del skill no lo activa ni autoriza cambios de repositorio.
1. Cuando la tarea solicite revisar el hook, localizarlo mediante `git rev-parse --git-path hooks/pre-commit` y consultar `core.hooksPath`; no asumir que `.git` es un directorio, especialmente en worktrees.
2. Inspeccionar presencia, contenido y digest BLAKE3 del hook y del linter sin modificarlos. Un digest identifica contenido; no acredita seguridad.
3. Queda prohibida la sobrescritura autónoma del hook. Si falta o difiere, informar la discrepancia y preparar una propuesta revisable de instalación o encadenamiento que preserve los controles existentes.
4. La instalación requiere una instrucción explícita del operador que cubra esa ruta y acción. No crear un directorio `pre-commit.d` suponiendo que Git lo ejecutará: comprobar el mecanismo real de encadenamiento.
