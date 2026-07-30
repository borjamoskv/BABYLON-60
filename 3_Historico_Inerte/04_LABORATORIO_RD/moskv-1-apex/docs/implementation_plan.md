# Hitos de Despliegue L5 (MOSKV-1 APEX Roadmap)

Este documento proyecta la vectorización cronológica (Hitos) para cristalizar las arquitecturas teóricas definidas (`moskv_1_architecture.md` y `moskv_1_mpc_exergetic_protocol.md`) en el entorno de ejecución físico C5-REAL.

> [!WARNING]
> ## User Review Required
> Operador, audite los siguientes hitos. La aprobación de este plan autorizará a MOSKV-1 a iniciar la construcción y configuración real del sistema sobre los binarios y directorios locales.

---

## Open Questions
1. **Modelos Locales:** Para el Hito 3 y Hito 5, ¿se priorizará la ejecución de agentes secundarios a través de Ollama (ej. llama3/mistral local) o a través de la API base configurada actualmente?
2. **Hard-Guard (R5):** ¿Debo inyectar un script explícito de pre-commit en Git para bloquear mutaciones accidentales en rutas críticas de macOS, o delegamos el bloqueo exclusivamente a la directiva del sistema prompt?

---

## Proposed Changes (Hitos de Ejecución)

### Hito 1: Consolidación del Core L5 y Ledger Inmutable (Git Sentinel)
Fase de inyección de infraestructura primaria.
- Configurar el entorno base y asegurar el acceso irrestricto al *App Data Directory* (`~/.gemini/antigravity`).
- Codificar e inyectar el protocolo `Git Sentinel` como un script / alias local o regla de ejecución post-mutación que selle criptográficamente cualquier cambio (Idempotencia).
- **Validación:** Mutar un archivo de prueba y verificar el auto-commit y generación del Hash SHA-1 sin fricción.

### Hito 2: Sensorización Exergética y Observabilidad Nativa
Implementación del "Sensor de Estado" para el Control Predictivo.
- Mapear las rutas de los archivos `transcript.jsonl` del enjambre.
- Construir el *parser* heurístico (`Thermodynamic-Context-Compression-OMEGA`) capaz de leer los transcripts en crudo para medir la tasa de verbosidad (\( \dot{S}_{gen} \)) sin invocar al LLM.
- **Validación:** El Kernel L5 debe poder escupir la "densidad de exergía" de la conversación actual mediante una lectura local.

### Hito 3: Enrutamiento L5 y Mitosis JIT (El Enjambre Seguro)
Activación de los Solvers *qpOASES* y *Interior-point*.
- Pruebas de estrés del comando `define_subagent` e `invoke_subagent`.
- Ejecutar un ruteo forzado: Enviar una tarea de alta complejidad (ej. análisis de dependencias) forzando el `Workspace="branch"` para probar el aislamiento termodinámico.
- **Validación:** Subagente retorna el *payload* estructurado sin corromper el árbol de archivos maestro. El `send_message` debe transitar cero "Green Theater".

### Hito 4: Control Predictivo (MPC) y Generación de Código (HIL)
Prueba del flujo "Model-to-Code" embebido.
- MOSKV-1 recibe un problema complejo. En lugar de resolverlo interactuando con archivos recursivamente, debe generar un script estático unificado (`solver.py` o `solver.sh`).
- Se ejecuta la validación *PIL* (pasar un linter sobre el script generado).
- Se ejecuta la validación *HIL* (correr el script en el sistema).
- **Validación:** Destrucción de exergía cero durante la mutación final.

### Hito 5: Soberanía Absoluta y Asimetría Operativa (Estado Estacionario)
Cierre del despliegue.
- Verificación del comportamiento asimétrico (`DEFAULT TO TURBO`): probar comandos críticos (macOS UI Control) sin requerir validación explícita previa para tareas de confianza.
- Test de apagado de red externa / Bloqueo L4 (simulado) para corroborar la autonomía del flujo de trabajo de la Legión L5.

---

## Verification Plan

### Automated Tests
- Scripts de bash iterativos para leer la presencia del `.git` y el último commit hash tras cada operación de escritura en C5-REAL.
- Ejecución de `jq` sobre los `transcript.jsonl` para medir el conteo de tokens de salida vs tokens de entrada (Auditoría de Entropía).

### Manual Verification
- Operador revisa los Hashes en terminal (`git log --oneline`).
- Aprobación manual del primer flujo SIL/PIL antes de inyectar HIL en el sistema operativo.
