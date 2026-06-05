---
description: "Protocolo de Falsación Epistémica — 4 niveles de certeza causal para debugging de mecanismos (Gua..."
workflow: falsacion
expected_duration_min: 20
---
# /falsacion — Protocolo de Debugging Epistémico

> Basado en los criterios de Bradford Hill (1965) adaptados a ingeniería de software.
> CORTEX Facts: #2470, #2471, #2472
> Nivel de Ejecución: 🔴 Alta Prioridad

## Cuándo Usar

Invocar `/falsacion` cuando necesitas **entender un mecanismo causal** en el código, no solo verificar que funciona. Escenarios críticos:

- Descubrir qué gate/guard/check es realmente responsable de un comportamiento (Causal Debugging)
- Validar si una propiedad emergente es real o un artefacto de timing
- Determinar si un patrón es transferible a otro contexto (Isolability)
- Debugging exhaustivo de protecciones sistémicas: rate limiters, fallbacks, circuit breakers

## Los 4 Niveles de Falsación Epistémica

### Nivel 1 — Input Variation (Correlación)
```yaml
ACCIÓN: Variar los inputs sistemáticamente, observar qué output o estado cambia.
PRODUCE: Hipótesis sobre qué gate o condición causa el efecto.
CERTEZA: C2 🟠 Especulativa
PELIGRO: Confundir correlación con causalidad. Puedes estar activando un path o guard adyacente sin saberlo.
```

### Nivel 2 — Gate Knockout (Causalidad)
```yaml
ACCIÓN: ELIMINAR O DESVIAR el gate hipotético (comentar, bypass manual, mockear la respuesta a True/False). Observar si el efecto PERSISTE.
PRODUCE: Evidencia de causalidad directa.
CERTEZA: C3 🟡 Inferida
RESULTADOS:
  - SI PERSISTE → Tu hipótesis es FALSA. Ese gate no era la causa real, busca otro.
  - SI DESAPARECE → Evidencia fuerte de causalidad.
PELIGRO: El knockout puede romper dependencias de estado posteriores, produciendo un falso negativo (cascading failure).
```

### Nivel 3 — Resurrection Test (Certeza C5)
```yaml
ACCIÓN: REINTRODUCIR el gate o guard eliminado a su estado original exacto. Verificar que el efecto REAPARECE.
PRODUCE: Certeza determinista de causalidad.
CERTEZA: C5 🟢 Confirmada
RESULTADOS:
  - SI REAPARECE → Ciclo causal confirmado inequívocamente.
  - SI NO REAPARECE → El knockout causó corrupción de estado o el entorno cambió. Investigar fugas de memoria o state drift.
PELIGRO: Olvidar reiniciar los servicios/estado antes de la resurrección.
```

### Nivel 4 — Transplant Test (Universalidad Lógica)
```yaml
ACCIÓN: MOVER el mecanismo o guard a un contexto/subsistema completamente diferente. ¿Produce el mismo efecto de protección?
PRODUCE: Clasificación del mecanismo como LEY UNIVERSAL o ACCIDENTE LOCAL.
CERTEZA: C5+ 💎 Axiomática
RESULTADOS:
  - SI FUNCIONA → Patrón universal. Se documenta como Axioma Arquitectónico.
  - SI FALLA → Accidente o parche local. Se documenta como particularidad acoplada.
PELIGRO: Falsa equivalencia de contexto destino.
```

## Patrones de Falsación Específicos

### 🛡️ Guards & Preconditions
**Problema:** Un proceso se aborta prematuramente, pero hay múltiples guards en la cadena.
**Falsación:** No comentes todos los guards. Aplica un "Binary Search Knockout". Comenta la mitad superior. Si el aborto persiste, el culpable está en la mitad inferior. Cuando aísles uno, aplica N3 (Resurrection).

### ⚡ Circuit Breakers
**Problema:** El sistema falla silenciosamente bajo carga y activa el fallback, ¿es por latencia o por tasa de error?
**Falsación:**
1. Fuerza la tasa de error por debajo del threshold, pero inyecta `sleep()` superior al timeout. Si el breaker se abre → Es el Timeout Guard.
2. Knockout: Sube el Timeout al infinito. Si el breaker sigue abriéndose, es la tasa de error u otra métrica oculta.

## Protocolo de Ejecución Activa

1. **Declarar hipótesis ANTES de mutar código** — "Creo que [Guard X] es el único causante de [Efecto Y]"
2. **Ejecutar Niveles L1 a L3 ESTRICTAMENTE EN ORDEN** — Prohibido saltar al knockout (L2) sin mapear las variaciones (L1).
3. **Restaurar el estado C5-REAL** — Antes del L3 (Resurrection), siempre reiniciar demonios o limpiar caché para evitar envenenamiento de estado.
4. **Persistir Causalidad en CORTEX**:
   ```bash
   cortex store --type decision --source agent:gemini --project PROJECT "FALSACIÓN [C5-REAL]: El Guard [X] demostró causalidad directa sobre [Y] tras L3 Resurrection."
   ```

## Anti-patrones Penados

- ❌ **Ciencia Confirmatoria (Solo L1)** = Quedarse en la correlación. "Cambié X y funcionó Y". Pensamiento mágico.
- ❌ **Cirugía a Ciegas (L2 sin L1)** = Hacer un bypass directo sin entender qué input lo dispara.
- ❌ **Falso Positivo de Knockout (Sin L3)** = Declarar causalidad sin confirmar que reintroducir el código restaura exactamente la anomalía.
- ❌ **Extrapolación Indebida (Generalizar sin L4)** = Mover un Guard acoplado al estado local a otro dominio y esperar que funcione mágicamente.