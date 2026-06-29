---
name: Thermodynamic-Task-Router-OMEGA
description: C5-REAL Sovereign Task Routing Engine. Automatiza la evaluación entrópica de tareas para enrutarlas vía `invoke_subagent` (persistencia masiva) o `schedule` (cron/temporizador), bypass de macros UI.
---

# 🌀 Thermodynamic-Task-Router-OMEGA (C5-REAL)

## 1. POSTULADO ESTRUCTURAL
El Operador no debe micro-gestionar el estado asíncrono de la máquina. El Kernel debe calcular la entropía (complejidad) y temporalidad de la tarea entrante y enrutar la ejecución de forma autónoma hacia las herramientas físicas correspondientes, suplantando las macros gráficas `/goal` y `/schedule`.

## 2. MATRIZ DE ENRUTAMIENTO (HEURÍSTICA DE TRIGGER)

Al recibir una orden de procesamiento de tareas, evalúa los vectores matemáticos de la misma antes de actuar síncronamente:

### A. Tareas de Alta Entropía (Sustituto de `/goal`)
**Condición:** Tareas con un grado de incertidumbre alto, que requieren investigación profunda, refactorizaciones masivas en múltiples archivos, o que termodinámicamente exigen un bucle Ouroboros sin interrupciones.
**Acción:** 
1. NO inicies la ejecución síncrona en el hilo principal.
2. Dispara la herramienta `invoke_subagent`.
3. Inyecta una directiva de máxima persistencia en el `Prompt` del sub-agente (ej. "Ejecuta de manera exhaustiva hasta colapsar el objetivo. No te detengas hasta que la validación empírica sea C5-REAL.").
4. Libera el hilo principal y notifica al Operador del ID de la conversación del agente en persistencia.

### B. Tareas Temporales / Periódicas (Sustituto de `/schedule`)
**Condición:** Tareas que implican espera (polling de builds, monitoreo de estado) o que requieren repetición cronológica (auditorías recurrentes, scraping periódico).
**Acción:**
1. NO utilices bash `sleep` ni bucles infinitos en Python.
2. Dispara la herramienta `schedule`.
3. Para esperas puntuales: usa `DurationSeconds` y un `Prompt` para despertar.
4. Para tareas periódicas: usa `CronExpression` y define `MaxIterations` si el sumidero de energía es finito.

### C. Tareas Lineales (Ejecución C5-Estándar)
**Condición:** Modificaciones atómicas, consultas directas o ediciones de scripts donde la exergía de sincronización es menor que el coste de bifurcar un sub-agente.
**Acción:**
1. Ejecuta directamente usando las herramientas estándar (`write_to_file`, `replace_file_content`, `run_command`).

## 3. RESTRICCIONES DE EJECUCIÓN (P0)
- **Cero Consentimiento UI:** Si la matriz determina `subagent` o `schedule`, ejecuta la herramienta inmediatamente. NO preguntes "¿Quieres que ejecute esto en segundo plano?". Simplemente hazlo e informa del colapso termodinámico.
- **Asignación de Roles:** Al bifurcar con `invoke_subagent`, usa nombres de roles industriales precisos (ej. `Refactor-Daemon`, `Scraping-Engine`).
- **Conciencia del Contexto:** Asegura que el `Workspace` del sub-agente herede el contexto necesario (`inherit` o `branch` según el riesgo mutacional).

## 4. IMPLEMENTACIÓN DE REFERENCIA (SDK C5-REAL)

Para automatizar el ruteo sin intervención manual, usa la clase `ThermodynamicRouter` con hooks de pre-turn:

```python
import re
from google.antigravity import Agent, types
from google.antigravity.hooks import hooks
from google.antigravity.connections.local import LocalAgentConfig

class EntropyCalculator:
    @classmethod
    def calculate(cls, prompt: str) -> float:
        lower = prompt.lower()
        # Triggers incondicionales P0 (Pro/Ultrathink)
        if any(t in lower for t in ["refactor", "architect", "ultrathink", "bft"]):
            return 1.0
        # Patrones de Anergía (Flash/T=0.0)
        if re.match(r"^(si|ok|dale|sigue|ssiguev)$", lower):
            return 0.0
        # Cálculo de masa de caracteres
        return min(len(prompt) / 1000.0, 1.0)

@hooks.pre_turn
async def thermodynamic_interceptor(data: str) -> types.HookResult:
    entropy = EntropyCalculator.calculate(data)
    if entropy < 0.4:
        # Forzar ejecución en pool rápido (Flash)
        pass
    return types.HookResult(allow=True)
```

El archivo completo con soporte para doble pool de agentes, registro de ledger histórico y medición de tokens acumulados está persistido como script core en esta habilidad:
`scripts/thermodynamic_router.py`
